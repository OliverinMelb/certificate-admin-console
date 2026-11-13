"""Durable results committed together with the issuance they describe."""

import json
import sqlite3

from fastapi import HTTPException

from app.issuance import issue_course_in_transaction


def initialize_idempotency(db):
    db.execute("""CREATE TABLE IF NOT EXISTS bulk_operation (
        tenant_id TEXT NOT NULL, actor_id TEXT NOT NULL,
        operation_type TEXT NOT NULL, key TEXT NOT NULL,
        request_json TEXT NOT NULL, status_code INTEGER NOT NULL,
        result_json TEXT NOT NULL,
        PRIMARY KEY(tenant_id, actor_id, operation_type, key),
        FOREIGN KEY(tenant_id, actor_id) REFERENCES admin(tenant_id, id))""")


def issue_idempotent(db, tenant_id, actor_id, course_id, key):
    try:
        return _issue_idempotent(db, tenant_id, actor_id, course_id, key)
    except sqlite3.Error as error:
        if getattr(error, "sqlite_errorcode", 0) & 0xFF == sqlite3.SQLITE_BUSY:
            raise HTTPException(status_code=503, detail="Database busy; retry with the same key",
                                headers={"Retry-After": "1"}) from error
        raise HTTPException(status_code=503, detail="Issuance storage unavailable; batch rolled back") from error


def _issue_idempotent(db, tenant_id, actor_id, course_id, key):
    request = json.dumps({"version": 1, "course_id": course_id}, sort_keys=True)
    identity = (tenant_id, actor_id, "issue_course", key)
    with db:
        db.execute("BEGIN IMMEDIATE")
        if db.execute("SELECT 1 FROM course WHERE tenant_id=? AND id=?", (tenant_id, course_id)).fetchone() is None:
            raise HTTPException(status_code=404, detail="Not Found")
        previous = db.execute("""SELECT request_json, result_json FROM bulk_operation
            WHERE tenant_id=? AND actor_id=? AND operation_type=? AND key=?""", identity).fetchone()
        if previous:
            if previous["request_json"] != request:
                raise HTTPException(status_code=409, detail="Idempotency key already used for a different request")
            return json.loads(previous["result_json"])
        result = issue_course_in_transaction(db, tenant_id, actor_id, course_id)
        db.execute("INSERT INTO bulk_operation VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (*identity, request, 200, json.dumps(result)))
    return result
