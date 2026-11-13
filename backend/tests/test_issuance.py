import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def database(tmp_path):
    return tmp_path / "issuance.sqlite3"


@pytest.fixture
def client(database):
    with TestClient(create_app(database_path=database)) as client:
        yield client


ALICE = {"X-Actor-Id": "alice", "Idempotency-Key": "initial"}
BOB = {"X-Actor-Id": "bob", "Idempotency-Key": "initial"}


def test_issue_only_completed_never_certified_enrollments(client):
    response = client.post("/api/courses/east-safety/issue", headers=ALICE)
    assert response.status_code == 200
    result = response.json()
    assert result["course_id"] == "east-safety"
    assert len(result["outcomes"]) == 14
    outcomes = {item["learner_id"]: item for item in result["outcomes"]}
    assert outcomes["east-learner-001"] == {
        "learner_id": "east-learner-001", "outcome": "skipped",
        "reason": "already_certified", "certificate_id": "east-cert-001",
    }
    assert outcomes["east-learner-014"] == {
        "learner_id": "east-learner-014", "outcome": "skipped",
        "reason": "not_completed", "certificate_id": None,
    }
    issued = outcomes["east-learner-013"]
    assert issued["outcome"] == "issued"
    detail = client.get(f"/api/certificates/{issued['certificate_id']}", headers=ALICE)
    assert detail.status_code == 200
    assert detail.json()["learner_id"] == "east-learner-013"
    assert detail.json()["status"] == "ACTIVE"
    assert client.get("/api/certificates", headers=ALICE).json()["total"] == 13


def test_issue_audit_is_single_and_repeated_issue_skips(client):
    result = client.post("/api/courses/east-safety/issue", headers=ALICE).json()
    issued = next(item for item in result["outcomes"] if item["outcome"] == "issued")
    certificate_id = issued["certificate_id"]
    audit = client.get(f"/api/certificates/{certificate_id}/audit", headers=ALICE)
    assert audit.status_code == 200
    events = audit.json()["items"]
    assert len(events) == 1
    assert events[0]["event_type"] == "ISSUED"
    assert events[0]["actor_id"] == "alice"
    assert events[0]["certificate_id"] == certificate_id
    repeated = client.post("/api/courses/east-safety/issue", headers={**ALICE, "Idempotency-Key": "new-operation"})
    assert repeated.status_code == 200
    assert all(item["outcome"] == "skipped" for item in repeated.json()["outcomes"])
    assert client.get(f"/api/certificates/{certificate_id}/audit", headers=ALICE).json()["items"] == events
    assert client.get("/api/certificates", headers=ALICE).json()["total"] == 13


def test_audit_failure_rolls_back_entire_batch_and_recovers(client, database):
    with sqlite3.connect(database) as db:
        db.execute("UPDATE enrollment SET completed = 1 WHERE id = 'east-enrollment-014'")
        db.execute("""CREATE TRIGGER reject_second_audit BEFORE INSERT ON audit_event
            WHEN (SELECT learner_id FROM certificate WHERE id = NEW.certificate_id) = 'east-learner-014'
            BEGIN SELECT RAISE(ABORT, 'test audit storage failure'); END""")
    response = client.post("/api/courses/east-safety/issue", headers=ALICE)
    assert response.status_code == 503
    assert client.get("/api/certificates", headers=ALICE).json()["total"] == 12
    with sqlite3.connect(database) as db:
        db.execute("DROP TRIGGER reject_second_audit")
    recovered = client.post("/api/courses/east-safety/issue", headers=ALICE)
    assert recovered.status_code == 200
    issued = [item for item in recovered.json()["outcomes"] if item["outcome"] == "issued"]
    assert [item["learner_id"] for item in issued] == ["east-learner-013", "east-learner-014"]
    for item in issued:
        events = client.get(f"/api/certificates/{item['certificate_id']}/audit", headers=ALICE).json()["items"]
        assert len(events) == 1


def test_identity_and_cross_tenant_writes_and_audit_are_isolated(client):
    for headers in ({}, {"X-Actor-Id": "unknown"}):
        assert client.post("/api/courses/east-safety/issue", headers=headers).status_code == 401
        assert client.get("/api/certificates/east-cert-001/audit", headers=headers).status_code == 401
    for course in ("east-safety", "missing"):
        assert client.post(f"/api/courses/{course}/issue", headers=BOB).status_code == 404
    for certificate in ("east-cert-001", "missing"):
        assert client.get(f"/api/certificates/{certificate}/audit", headers=BOB).status_code == 404
    assert client.get("/api/certificates", headers=ALICE).json()["total"] == 12
    assert client.get("/api/certificates/east-cert-001/audit", headers=ALICE).json() == {"items": []}
    assert client.get("/api/certificates", headers=BOB).json()["total"] == 4


def test_revoked_certificate_is_never_reissued(client, database):
    with sqlite3.connect(database) as db:
        db.execute("UPDATE certificate SET status = 'REVOKED' WHERE id = 'east-cert-001'")
    result = client.post("/api/courses/east-safety/issue", headers=ALICE).json()
    first = next(item for item in result["outcomes"] if item["learner_id"] == "east-learner-001")
    assert first["outcome"] == "skipped"
    assert first["reason"] == "already_certified"
    assert first["certificate_id"] == "east-cert-001"
    assert client.get("/api/certificates/east-cert-001", headers=ALICE).json()["status"] == "REVOKED"
    assert client.get("/api/certificates/east-cert-001/audit", headers=ALICE).json() == {"items": []}


def test_serial_conflict_fails_one_learner_and_continues(client, database):
    with sqlite3.connect(database) as db:
        db.execute("UPDATE enrollment SET completed = 1 WHERE id = 'east-enrollment-014'")
        db.execute("""CREATE TRIGGER serial_collision BEFORE INSERT ON certificate
            WHEN NEW.learner_id = 'east-learner-013'
            BEGIN INSERT INTO certificate VALUES ('collision', 'east', 'EAST-001',
                'east-safety', 'east-learner-014', '2026-01-10T13:30:00Z', 'ACTIVE'); END""")
    response = client.post("/api/courses/east-safety/issue", headers=ALICE)
    assert response.status_code == 200
    outcomes = {item["learner_id"]: item for item in response.json()["outcomes"]}
    assert outcomes["east-learner-013"] == {
        "learner_id": "east-learner-013", "outcome": "failed",
        "reason": "serial_conflict", "certificate_id": None,
    }
    issued = outcomes["east-learner-014"]
    assert issued["outcome"] == "issued"
    assert client.get("/api/certificates", headers=ALICE).json()["total"] == 13
    assert len(client.get(f"/api/certificates/{issued['certificate_id']}/audit", headers=ALICE).json()["items"]) == 1
