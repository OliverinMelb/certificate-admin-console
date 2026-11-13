"""Public cross-ticket contract: revocation must not be undone by replay."""

import csv
import io

from fastapi.testclient import TestClient
from app.main import create_app


def test_replay_after_revocation_preserves_status_audit_and_csv(tmp_path):
    headers = {"X-Actor-Id": "alice", "Idempotency-Key": "original-operation"}
    with TestClient(create_app(tmp_path / "integration.sqlite3")) as client:
        first = client.post("/api/courses/east-safety/issue", headers=headers)
        assert first.status_code == 200
        issued = next(x for x in first.json()["outcomes"] if x["outcome"] == "issued")
        certificate_id = issued["certificate_id"]
        revoked = client.post(f"/api/certificates/{certificate_id}/revoke", headers=headers)
        assert revoked.status_code == 200
        replay = client.post("/api/courses/east-safety/issue", headers=headers)
        assert replay.json() == first.json()
        detail = client.get(f"/api/certificates/{certificate_id}", headers=headers).json()
        assert detail["status"] == "REVOKED"
        audit = client.get(f"/api/certificates/{certificate_id}/audit", headers=headers).json()
        assert sorted(x["event_type"] for x in audit["items"]) == ["ISSUED", "REVOKED"]
        fresh = client.post("/api/courses/east-safety/issue",
                            headers={**headers, "Idempotency-Key": "new-operation"}).json()
        learner = next(x for x in fresh["outcomes"] if x["learner_id"] == issued["learner_id"])
        assert learner["outcome"] == "skipped"
        assert learner["reason"] == "already_certified"
        exported = client.get("/api/certificates/export.csv",
                              params={"q": detail["serial_number"], "sort": "issue_date"}, headers=headers)
        assert exported.status_code == 200
        rows = list(csv.DictReader(io.StringIO(exported.content.decode("utf-8-sig"))))
        assert len(rows) == 1
        assert rows[0]["serial_number"] == detail["serial_number"]
        assert rows[0]["issued_local_date"] == detail["issued_local_date"]
