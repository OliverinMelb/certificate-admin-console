import asyncio
import httpx

from app.main import create_app


def get(path: str, tmp_path) -> httpx.Response:
    async def request():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=create_app(database_path=tmp_path / "certificates.sqlite3")), base_url="http://test"
        ) as client:
            return await client.get(path)
    return asyncio.run(request())


def test_health_reports_process_ready(tmp_path):
    response = get("/api/health", tmp_path)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_serves_the_built_frontend(tmp_path):
    response = get("/", tmp_path)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert '<div id="app">' in response.text


def test_unknown_api_is_a_404_not_the_frontend(tmp_path):
    response = get("/api/unknown", tmp_path)
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}
