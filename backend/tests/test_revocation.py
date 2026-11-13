import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Event, Lock

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

ALICE = {"X-Actor-Id": "alice"}
BOB = {"X-Actor-Id": "bob"}


@pytest.fixture
def database(tmp_path):
    return tmp_path / "revocation.sqlite3"


@pytest.fixture
def client(database):
    with TestClient(create_app(database_path=database)) as client:
        yield client


def test_revoke_changes_status_and_adds_one_audit_without_changing_issue_time(client):
    certificate = "east-cert-001"
    before = client.get(f"/api/certificates/{certificate}", headers=ALICE).json()
    response = client.post(f"/api/certificates/{certificate}/revoke", headers=ALICE)
    assert response.status_code == 200
    assert response.json() == {"certificate_id": certificate, "status": "revoked", "changed": True}
    after = client.get(f"/api/certificates/{certificate}", headers=ALICE).json()
    assert after["status"] == "REVOKED"
    assert after["issued_at"] == before["issued_at"]
    events = client.get(f"/api/certificates/{certificate}/audit", headers=ALICE).json()["items"]
    assert len(events) == 1
    assert events[0]["event_type"] == "REVOKED"
    assert events[0]["actor_id"] == "alice"


def test_repeated_revoke_and_restart_preserve_original_event(client, database):
    url = "/api/certificates/east-cert-001"
    assert client.post(url + "/revoke", headers=ALICE).status_code == 200
    original = client.get(url + "/audit", headers=ALICE).json()
    repeated = client.post(url + "/revoke", headers=ALICE)
    assert repeated.status_code == 200
    assert repeated.json()["changed"] is False
    assert client.get(url + "/audit", headers=ALICE).json() == original
    with TestClient(create_app(database_path=database)) as restarted:
        assert restarted.post(url + "/revoke", headers=ALICE).json()["changed"] is False
        assert restarted.get(url + "/audit", headers=ALICE).json() == original


def test_cross_tenant_missing_and_invalid_identity_cannot_revoke(client):
    url = "/api/certificates/east-cert-001"
    for headers in ({}, {"X-Actor-Id": "unknown"}):
        assert client.post(url + "/revoke", headers=headers).status_code == 401
    for certificate in ("east-cert-001", "missing"):
        response = client.post(f"/api/certificates/{certificate}/revoke", headers=BOB)
        assert response.status_code == 404
        assert response.json() == {"detail": "Not Found"}
    assert client.get(url, headers=ALICE).json()["status"] == "ACTIVE"
    assert client.get(url + "/audit", headers=ALICE).json() == {"items": []}


def test_audit_failure_rolls_back_status_and_can_be_retried(database):
    with TestClient(create_app(database_path=database), raise_server_exceptions=False) as client:
        with sqlite3.connect(database) as db:
            db.execute("""CREATE TRIGGER reject_revocation BEFORE INSERT ON audit_event
                WHEN NEW.event_type = 'REVOKED'
                BEGIN SELECT RAISE(ABORT, 'test audit failure'); END""")
        url = "/api/certificates/east-cert-001"
        response = client.post(url + "/revoke", headers=ALICE)
        assert response.status_code == 500
        assert client.get(url, headers=ALICE).json()["status"] == "ACTIVE"
        assert client.get(url + "/audit", headers=ALICE).json() == {"items": []}
        with sqlite3.connect(database) as db:
            db.execute("DROP TRIGGER reject_revocation")
        assert client.post(url + "/revoke", headers=ALICE).json()["changed"] is True


def test_overlapping_revoke_requests_create_only_one_event(database):
    app = create_app(database_path=database)
    entered = Event()
    counter_lock = Lock()
    arrivals = 0

    @app.middleware("http")
    async def observe_http_arrivals(request, call_next):
        nonlocal arrivals
        if request.url.path.endswith("/revoke"):
            with counter_lock:
                arrivals += 1
                if arrivals == 2:
                    entered.set()
        return await call_next(request)

    with TestClient(app) as client, sqlite3.connect(database) as blocker:
        blocker.execute("BEGIN IMMEDIATE")
        with ThreadPoolExecutor(max_workers=2) as workers:
            futures = [workers.submit(client.post, "/api/certificates/east-cert-001/revoke",
                                      headers=ALICE) for _ in range(2)]
            try:
                assert entered.wait(3), "Both requests must enter HTTP before lock release"
                assert not any(future.done() for future in futures)
            finally:
                blocker.rollback()
            responses = [future.result(timeout=10) for future in futures]
        assert [response.status_code for response in responses] == [200, 200]
        assert sorted(response.json()["changed"] for response in responses) == [False, True]
        events = client.get("/api/certificates/east-cert-001/audit", headers=ALICE).json()["items"]
        assert len(events) == 1
        assert events[0]["event_type"] == "REVOKED"


def test_busy_write_returns_retryable_503_without_changing_status(database):
    with TestClient(create_app(database_path=database), raise_server_exceptions=False) as client:
        with sqlite3.connect(database) as blocker:
            blocker.execute("BEGIN IMMEDIATE")
            response = client.post("/api/certificates/east-cert-001/revoke", headers=ALICE)
            assert response.status_code == 503
            assert response.headers["Retry-After"] == "1"
            blocker.rollback()
        assert client.get("/api/certificates/east-cert-001", headers=ALICE).json()["status"] == "ACTIVE"
        assert client.get("/api/certificates/east-cert-001/audit", headers=ALICE).json() == {"items": []}


def test_revoke_preserves_issued_audit_and_rejects_unknown_body(client):
    result = client.post("/api/courses/east-safety/issue",
                         headers={**ALICE, "Idempotency-Key": "t4-issue"}).json()
    certificate = next(item["certificate_id"] for item in result["outcomes"] if item["outcome"] == "issued")
    url = f"/api/certificates/{certificate}"
    original = client.get(url + "/audit", headers=ALICE).json()["items"]
    assert client.post(url + "/revoke", headers=ALICE, json={"reason": "unsupported"}).status_code == 422
    assert client.get(url, headers=ALICE).json()["status"] == "ACTIVE"
    assert client.post(url + "/revoke", headers=ALICE, json={}).status_code == 200
    events = client.get(url + "/audit", headers=ALICE).json()["items"]
    assert len(events) == 2
    assert [event for event in events if event["event_type"] == "ISSUED"] == original
