"""Atomic tenant-scoped certificate revocation."""

from datetime import datetime, timezone
import sqlite3
from uuid import uuid4

from fastapi import HTTPException


def revoke_certificate(db, tenant_id, actor_id, certificate_id):
    try:
        return _revoke_in_transaction(db, tenant_id, actor_id, certificate_id)
    except sqlite3.OperationalError as error:
        if getattr(error, "sqlite_errorcode", 0) & 0xFF == sqlite3.SQLITE_BUSY:
            raise HTTPException(status_code=503, detail="Database busy; retry revocation",
                                headers={"Retry-After": "1"}) from error
        raise


def _revoke_in_transaction(db, tenant_id, actor_id, certificate_id):
    with db:
        db.execute("BEGIN IMMEDIATE")
        certificate = db.execute("SELECT status FROM certificate WHERE tenant_id = ? AND id = ?",
                                 (tenant_id, certificate_id)).fetchone()
        if certificate is None:
            raise HTTPException(status_code=404, detail="Not Found")
        if certificate["status"] == "REVOKED":
            return {"certificate_id": certificate_id, "status": "revoked", "changed": False}
        db.execute("UPDATE certificate SET status = 'REVOKED' WHERE tenant_id = ? AND id = ? AND status = 'ACTIVE'",
                   (tenant_id, certificate_id))
        db.execute("INSERT INTO audit_event VALUES (?, ?, ?, ?, ?, ?)",
                   (str(uuid4()), tenant_id, certificate_id, actor_id, "REVOKED",
                    datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")))
    return {"certificate_id": certificate_id, "status": "revoked", "changed": True}
