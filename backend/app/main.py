from pathlib import Path
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.staticfiles import StaticFiles
from app.database import connect, initialize


def create_app(database_path: str | Path | None = None) -> FastAPI:
    database = Path(database_path) if database_path is not None else (
        Path(__file__).resolve().parents[2] / "data" / "certificates.sqlite3"
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        initialize(database)
        from app.issuance import initialize_issuance
        with connect(database) as db, db:
            db.execute("BEGIN")
            initialize_issuance(db)
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

    @app.get("/api/certificates/{certificate_id}")
    def certificate_detail(certificate_id: str, x_actor_id: str | None = Header(default=None)):
        from app.certificate_query import get_certificate
        with connect(database) as db:
            tenant = tenant_for(db, x_actor_id)
            return get_certificate(db, tenant, certificate_id)

    @app.post("/api/courses/{course_id}/issue")
    def issue(course_id: str, x_actor_id: str | None = Header(default=None)):
        from app.issuance import issue_course
        with connect(database) as db:
            tenant = tenant_for(db, x_actor_id)
            return issue_course(db, tenant, x_actor_id, course_id)

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
