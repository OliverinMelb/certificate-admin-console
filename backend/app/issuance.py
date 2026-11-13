"""Tenant-scoped batch issuance and its audit trail."""

from datetime import datetime, timezone
import sqlite3
from uuid import uuid4

from fastapi import HTTPException


def initialize_issuance(db):
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS certificate_once ON certificate(tenant_id, course_id, learner_id)")
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS certificate_tenant_id ON certificate(tenant_id, id)")
    db.execute("""CREATE TABLE IF NOT EXISTS audit_event (
        id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, certificate_id TEXT NOT NULL,
        actor_id TEXT NOT NULL, event_type TEXT NOT NULL CHECK(event_type IN ('ISSUED', 'REVOKED')),
        occurred_at TEXT NOT NULL, UNIQUE(certificate_id, event_type),
        FOREIGN KEY(tenant_id, certificate_id) REFERENCES certificate(tenant_id, id),
        FOREIGN KEY(tenant_id, actor_id) REFERENCES admin(tenant_id, id))""")


def issue_course(db, tenant_id, actor_id, course_id):
    try:
        return _issue_course(db, tenant_id, actor_id, course_id)
    except sqlite3.Error as error:
        raise HTTPException(status_code=503, detail="Issuance unavailable; batch rolled back") from error


def _issue_course(db, tenant_id, actor_id, course_id):
    with db:
        db.execute("BEGIN IMMEDIATE")
        return issue_course_in_transaction(db, tenant_id, actor_id, course_id)


def issue_course_in_transaction(db, tenant_id, actor_id, course_id):
    if db.execute("SELECT 1 FROM course WHERE tenant_id = ? AND id = ?",
                  (tenant_id, course_id)).fetchone() is None:
        raise HTTPException(status_code=404, detail="Not Found")
    outcomes = []
    for enrollment in db.execute(
        "SELECT learner_id, completed FROM enrollment WHERE tenant_id = ? AND course_id = ? ORDER BY learner_id",
        (tenant_id, course_id),
    ).fetchall():
        learner_id = enrollment["learner_id"]
        existing = db.execute(
            "SELECT id FROM certificate WHERE tenant_id = ? AND course_id = ? AND learner_id = ?",
            (tenant_id, course_id, learner_id),
        ).fetchone()
        if existing is not None:
            outcome, reason, certificate_id = "skipped", "already_certified", existing["id"]
        elif not enrollment["completed"]:
            outcome, reason, certificate_id = "skipped", "not_completed", None
        else:
            db.execute("SAVEPOINT learner_issue")
            certificate_id = str(uuid4())
            issued_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            try:
                db.execute("INSERT INTO certificate VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (certificate_id, tenant_id, str(uuid4()), course_id, learner_id, issued_at, "ACTIVE"))
                db.execute("INSERT INTO audit_event VALUES (?, ?, ?, ?, ?, ?)",
                           (str(uuid4()), tenant_id, certificate_id, actor_id, "ISSUED", issued_at))
                outcome, reason = "issued", "issued"
            except sqlite3.IntegrityError as error:
                # SQLite does not expose constraint names; require both the extended
                # result code and this exact column set, never a broad integrity catch.
                if (error.sqlite_errorcode != sqlite3.SQLITE_CONSTRAINT_UNIQUE or
                        str(error) != "UNIQUE constraint failed: certificate.tenant_id, certificate.serial_number"):
                    raise
                db.execute("ROLLBACK TO learner_issue")
                outcome, reason, certificate_id = "failed", "serial_conflict", None
            db.execute("RELEASE learner_issue")
        outcomes.append({"learner_id": learner_id, "outcome": outcome, "reason": reason,
                         "certificate_id": certificate_id})
    return {"course_id": course_id, "outcomes": outcomes}


def certificate_audit(db, tenant_id, certificate_id):
    if db.execute("SELECT 1 FROM certificate WHERE tenant_id = ? AND id = ?",
                  (tenant_id, certificate_id)).fetchone() is None:
        raise HTTPException(status_code=404, detail="Not Found")
    return {"items": [dict(row) for row in db.execute(
        """SELECT id, certificate_id, actor_id, event_type, occurred_at FROM audit_event
           WHERE tenant_id = ? AND certificate_id = ? ORDER BY occurred_at, id""",
        (tenant_id, certificate_id),
    )]}
