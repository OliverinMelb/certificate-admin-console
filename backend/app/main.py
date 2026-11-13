from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


def create_app() -> FastAPI:
    app = FastAPI(title="Certificate Admin Console")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    frontend = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    app.mount("/", StaticFiles(directory=frontend, html=True, check_dir=False))
    return app
