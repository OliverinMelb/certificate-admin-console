import sqlite3
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
import uvicorn

from fastapi.testclient import TestClient

from app.main import create_app


ALICE = {"X-Actor-Id": "alice", "Idempotency-Key": "operation-one"}
ISSUE = "/api/courses/east-safety/issue"


def test_retries_replay_first_result_after_restart(tmp_path):
    database = tmp_path / "idempotency.sqlite3"
    with TestClient(create_app(database)) as client:
        first = client.post(ISSUE, headers=ALICE)
        assert first.status_code == 200
        assert client.post(ISSUE, headers=ALICE, json={}).json() == first.json()
    with TestClient(create_app(database)) as client:
        assert client.post(ISSUE, headers=ALICE).json() == first.json()
        issued = next(row for row in first.json()["outcomes"] if row["outcome"] == "issued")
        events = client.get(f"/api/certificates/{issued['certificate_id']}/audit", headers=ALICE).json()["items"]
        assert [event["event_type"] for event in events] == ["ISSUED"]


def test_same_key_changed_course_conflicts_without_overwriting(tmp_path):
    database = tmp_path / "conflict.sqlite3"
    with TestClient(create_app(database)) as client:
        with sqlite3.connect(database) as db:
            db.execute("INSERT INTO course VALUES ('east-second', 'east', 'Second')")
        first = client.post(ISSUE, headers=ALICE)
        conflict = client.post("/api/courses/east-second/issue", headers=ALICE)
        assert conflict.status_code == 409
        assert client.post(ISSUE, headers=ALICE).json() == first.json()
        assert client.post("/api/courses/west-safety/issue", headers=ALICE).status_code == 404


def test_failed_commit_rolls_back_issuance_and_key_can_retry(tmp_path):
    database = tmp_path / "failure.sqlite3"
    with TestClient(create_app(database), raise_server_exceptions=False) as client:
        with sqlite3.connect(database) as db:
            db.execute("""CREATE TRIGGER reject_result BEFORE INSERT ON bulk_operation
                BEGIN SELECT RAISE(ABORT, 'test persistence failure'); END""")
        failed = client.post(ISSUE, headers=ALICE)
        assert failed.status_code == 503
        assert "Retry-After" not in failed.headers
        assert client.get("/api/certificates", headers=ALICE).json()["total"] == 12
        with sqlite3.connect(database) as db:
            db.execute("DROP TRIGGER reject_result")
        recovered = client.post(ISSUE, headers=ALICE)
        assert recovered.status_code == 200
        issued = next(row for row in recovered.json()["outcomes"] if row["outcome"] == "issued")
        assert len(client.get(f"/api/certificates/{issued['certificate_id']}/audit", headers=ALICE).json()["items"]) == 1
        assert client.post(ISSUE, headers=ALICE).json() == recovered.json()


@pytest.fixture
def live_server(tmp_path):
    database = tmp_path / "live.sqlite3"
    app = create_app(database)
    arrivals = threading.Condition()
    arrived = []

    @app.middleware("http")
    async def observe_requests(request, call_next):
        if request.url.path.endswith("/issue"):
            with arrivals:
                arrived.append(request.headers.get("Idempotency-Key"))
                arrivals.notify_all()
        return await call_next(request)

    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    server = uvicorn.Server(uvicorn.Config(app, log_level="error"))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not server.started and thread.is_alive() and time.monotonic() < deadline:
        time.sleep(.01)
    assert server.started
    try:
        with httpx.Client(base_url=f"http://127.0.0.1:{listener.getsockname()[1]}", trust_env=False, timeout=15) as client:
            yield database, client, arrivals, arrived
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        listener.close()
        assert not thread.is_alive()


def test_busy_lock_returns_retry_after_and_same_key_recovers(live_server):
    database, client, arrivals, arrived = live_server
    with sqlite3.connect(database) as lock:
        lock.execute("BEGIN IMMEDIATE")
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(client.post, ISSUE, headers=ALICE)
            with arrivals:
                assert arrivals.wait_for(lambda: len(arrived) == 1, timeout=5)
            assert not future.done()
            failed = future.result(timeout=10)
        assert failed.status_code == 503
        assert failed.headers.get("Retry-After") == "1"
    recovered = client.post(ISSUE, headers=ALICE)
    assert recovered.status_code == 200
    assert client.post(ISSUE, headers=ALICE).json() == recovered.json()


@pytest.mark.parametrize("same_key", [True, False])
def test_real_overlapping_requests_issue_once(live_server, same_key):
    database, client, arrivals, arrived = live_server
    second_headers = ALICE if same_key else {**ALICE, "Idempotency-Key": "operation-two"}
    with ThreadPoolExecutor(max_workers=2) as pool:
        with sqlite3.connect(database) as lock:
            lock.execute("BEGIN IMMEDIATE")
            first = pool.submit(client.post, ISSUE, headers=ALICE)
            second = pool.submit(client.post, ISSUE, headers=second_headers)
            with arrivals:
                assert arrivals.wait_for(lambda: len(arrived) == 2, timeout=5)
            assert not first.done() and not second.done()
        responses = [first.result(timeout=10), second.result(timeout=10)]
    assert [response.status_code for response in responses] == [200, 200]
    results = [response.json() for response in responses]
    if same_key:
        assert results[0] == results[1]
    else:
        assert sorted(sum(row["outcome"] == "issued" for row in result["outcomes"]) for result in results) == [0, 1]
    issued = next(row for result in results for row in result["outcomes"] if row["outcome"] == "issued")
    assert client.get("/api/certificates", headers=ALICE).json()["total"] == 13
    events = client.get(f"/api/certificates/{issued['certificate_id']}/audit", headers=ALICE).json()["items"]
    assert [event["event_type"] for event in events] == ["ISSUED"]


def test_key_validation_unknown_payload_and_tenant_actor_scope(tmp_path):
    database = tmp_path / "validation.sqlite3"
    with TestClient(create_app(database)) as client:
        for key in (None, "", " ", "a" * 129):
            headers = {"X-Actor-Id": "alice"}
            if key is not None:
                headers["Idempotency-Key"] = key
            assert client.post(ISSUE, headers=headers).status_code == 422
        assert client.post(ISSUE, headers=ALICE, json={"unexpected": True}).status_code == 422
        assert client.get("/api/certificates", headers=ALICE).json()["total"] == 12
        first = client.post(ISSUE, headers=ALICE).json()
        with sqlite3.connect(database) as db:
            db.execute("INSERT INTO admin VALUES ('alice-two', 'east', 'alice-two@east.test')")
        other = client.post(ISSUE, headers={**ALICE, "X-Actor-Id": "alice-two"})
        assert other.status_code == 200
        assert all(row["outcome"] == "skipped" for row in other.json()["outcomes"])
        west = client.post("/api/courses/west-safety/issue", headers={**ALICE, "X-Actor-Id": "bob"})
        assert west.status_code == 200
        assert any(row["outcome"] == "issued" for row in west.json()["outcomes"])
        assert client.post(ISSUE, headers=ALICE).json() == first


def test_partial_failed_result_is_preserved_even_after_cause_removed(tmp_path):
    database = tmp_path / "partial.sqlite3"
    with TestClient(create_app(database)) as client:
        with sqlite3.connect(database) as db:
            db.execute("""CREATE TRIGGER serial_collision BEFORE INSERT ON certificate
                WHEN NEW.learner_id = 'east-learner-013'
                BEGIN INSERT INTO certificate VALUES ('collision', 'east', 'EAST-001',
                    'east-safety', 'east-learner-014', '2026-01-10T13:30:00Z', 'ACTIVE'); END""")
        first = client.post(ISSUE, headers=ALICE)
        assert first.status_code == 200
        assert any(row["outcome"] == "failed" for row in first.json()["outcomes"])
        with sqlite3.connect(database) as db:
            db.execute("DROP TRIGGER serial_collision")
        assert client.post(ISSUE, headers=ALICE).json() == first.json()
        assert client.get("/api/certificates", headers=ALICE).json()["total"] == 12
        fresh = client.post(ISSUE, headers={**ALICE, "Idempotency-Key": "fresh"})
        assert any(row["outcome"] == "issued" for row in fresh.json()["outcomes"])
