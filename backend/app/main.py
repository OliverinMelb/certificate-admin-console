from pathlib import Path
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException, Header, Query, Body, Request
from pydantic import BaseModel, ConfigDict
from fastapi.staticfiles import StaticFiles
from app.database import connect, initialize


class EmptyOperation(BaseModel):
    model_config = ConfigDict(extra="forbid")


def create_app(database_path: str | Path | None = None) -> FastAPI:
    database = Path(database_path) if database_path is not None else (
        Path(__file__).resolve().parents[2] / "data" / "certificates.sqlite3"
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        initialize(database)
        from app.issuance import initialize_issuance
        from app.idempotency import initialize_idempotency
        with connect(database) as db, db:
            db.execute("BEGIN")
            initialize_issuance(db)
            initialize_idempotency(db)
        yield

    app = FastAPI(title="Certificate Admin Console", lifespan=lifespan)

    def tenant_for(db, actor_id: str | None) -> str:
        actor = db.execute("SELECT tenant_id FROM admin WHERE id = ?", (actor_id,)).fetchone()
        if actor is None:
            raise HTTPException(status_code=401, detail="Unknown or missing actor")
        return actor["tenant_id"]

    @app.get("/api/courses")
    def courses(x_actor_id: str | None = Header(default=None)):
        with connect(database) as db:
            tenant = tenant_for(db, x_actor_id)
            return {"items": [dict(row) for row in db.execute(
                "SELECT id, title FROM course WHERE tenant_id = ? ORDER BY id", (tenant,)
            )]}

    @app.get("/api/certificates")
    def certificates(q: str = "", page: int = Query(default=1, ge=1),
                     page_size: int = Query(default=50, ge=1, le=100),
                     sort: Literal["learner_name", "serial_number", "issue_date"] = "serial_number",
                     order: Literal["asc", "desc"] = "asc",
                     x_actor_id: str | None = Header(default=None)):
        from app.certificate_query import list_certificates
        with connect(database) as db:
            tenant = tenant_for(db, x_actor_id)
            return list_certificates(db, tenant, q, page, page_size, sort, order)

    @app.get("/api/certificates/export.csv")
    def export(request: Request, q: str = "",
               sort: Literal["learner_name", "serial_number", "issue_date"] = "serial_number",
               order: Literal["asc", "desc"] = "asc",
               x_actor_id: str | None = Header(default=None)):
        from app.csv_export import export_csv
        with connect(database) as db:
            tenant = tenant_for(db, x_actor_id)
        if "page" in request.query_params or "page_size" in request.query_params:
            raise HTTPException(status_code=422, detail="CSV export does not accept pagination")
        return export_csv(database, tenant, q, sort, order)

    @app.get("/api/certificates/{certificate_id}")
    def certificate_detail(certificate_id: str, x_actor_id: str | None = Header(default=None)):
        from app.certificate_query import get_certificate
        with connect(database) as db:
            tenant = tenant_for(db, x_actor_id)
            return get_certificate(db, tenant, certificate_id)

    @app.post("/api/courses/{course_id}/issue")
    def issue(course_id: str, x_actor_id: str | None = Header(default=None),
              idempotency_key: str | None = Header(default=None),
              body: EmptyOperation | None = Body(default=None)):
        from app.idempotency import issue_idempotent
        with connect(database) as db:
            tenant = tenant_for(db, x_actor_id)
            if (not idempotency_key or not idempotency_key.strip() or len(idempotency_key) > 128
                    or any(ord(c) < 32 or ord(c) > 126 for c in idempotency_key)):
                raise HTTPException(status_code=422, detail="Idempotency-Key must be 1-128 printable ASCII characters")
            return issue_idempotent(db, tenant, x_actor_id, course_id, idempotency_key)

    @app.post("/api/certificates/{certificate_id}/revoke")
    def revoke(certificate_id: str, x_actor_id: str | None = Header(default=None),
               body: EmptyOperation | None = Body(default=None)):
        from app.revocation import revoke_certificate
        with connect(database) as db:
            tenant = tenant_for(db, x_actor_id)
            return revoke_certificate(db, tenant, x_actor_id, certificate_id)

    @app.get("/api/certificates/{certificate_id}/audit")
    def audit(certificate_id: str, x_actor_id: str | None = Header(default=None)):
        from app.issuance import certificate_audit
        with connect(database) as db:
            tenant = tenant_for(db, x_actor_id)
            return certificate_audit(db, tenant, certificate_id)

    @app.get("/api/actors")
    def actors():
        with connect(database) as db:
            return {"items": [dict(row) for row in db.execute("""
                SELECT a.id, a.email, a.tenant_id, t.name AS tenant_name, t.timezone
                FROM admin a JOIN tenant t ON t.id = a.tenant_id ORDER BY a.id
            """)]}

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/{path:path}")
    def unknown_api(path: str):
        raise HTTPException(status_code=404, detail="Not Found")

    frontend = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    app.mount("/", StaticFiles(directory=frontend, html=True, check_dir=False))
    return app
