from pathlib import Path
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.staticfiles import StaticFiles
from app.database import connect, initialize


CERTIFICATE_SELECT = """
    SELECT c.id, c.serial_number, c.learner_id, l.name AS learner_name,
           c.course_id, co.title AS course_title, c.issued_at, c.status
    FROM certificate c
    JOIN learner l ON l.tenant_id = c.tenant_id AND l.id = c.learner_id
    JOIN course co ON co.tenant_id = c.tenant_id AND co.id = c.course_id
"""


def create_app(database_path: str | Path | None = None) -> FastAPI:
    database = Path(database_path) if database_path is not None else (
        Path(__file__).resolve().parents[2] / "data" / "certificates.sqlite3"
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        initialize(database)
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
                     sort: Literal["learner_name", "serial_number"] = "serial_number",
                     order: Literal["asc", "desc"] = "asc",
                     x_actor_id: str | None = Header(default=None)):
        with connect(database) as db:
            tenant = tenant_for(db, x_actor_id)
            escaped = q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            pattern = f"%{escaped}%"
            where = """ WHERE c.tenant_id = ?
                AND (l.name LIKE ? ESCAPE '\\' OR c.serial_number LIKE ? ESCAPE '\\')"""
            parameters = (tenant, pattern, pattern)
            column = "l.name" if sort == "learner_name" else "c.serial_number"
            direction = "DESC" if order == "desc" else "ASC"
            total = db.execute("SELECT COUNT(*) FROM (" + CERTIFICATE_SELECT + where + ")",
                               parameters).fetchone()[0]
            offset = (page - 1) * page_size
            if offset >= total:
                return {"items": [], "total": total, "page": page, "page_size": page_size}
            items = [dict(row) for row in db.execute(
                CERTIFICATE_SELECT + where + f" ORDER BY {column} {direction}, c.id ASC LIMIT ? OFFSET ?",
                (*parameters, page_size, offset)
            )]
            return {"items": items, "total": total, "page": page, "page_size": page_size}

    @app.get("/api/certificates/{certificate_id}")
    def certificate_detail(certificate_id: str, x_actor_id: str | None = Header(default=None)):
        with connect(database) as db:
            tenant = tenant_for(db, x_actor_id)
            row = db.execute(CERTIFICATE_SELECT + " WHERE c.tenant_id = ? AND c.id = ?",
                             (tenant, certificate_id)).fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Not Found")
            return dict(row)

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
