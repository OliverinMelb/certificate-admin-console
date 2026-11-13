import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(database_path=tmp_path / "certificates.sqlite3")) as client:
        yield client


def test_demo_actors_are_available_without_identity(client):
    response = client.get("/api/actors")
    assert response.status_code == 200
    assert response.json() == {"items": [
        {"id": "alice", "email": "alice@east.test", "tenant_id": "east",
         "tenant_name": "East", "timezone": "Australia/Sydney"},
        {"id": "bob", "email": "bob@west.test", "tenant_id": "west",
         "tenant_name": "West", "timezone": "Australia/Perth"},
    ]}


def test_courses_require_known_actor_and_ignore_client_tenant(client):
    for headers in ({}, {"X-Actor-Id": "unknown"}):
        assert client.get("/api/courses", headers=headers).status_code == 401
    for actor, course in [("alice", "east-safety"), ("bob", "west-safety")]:
        response = client.get("/api/courses?tenant_id=east", headers={"X-Actor-Id": actor})
        assert response.status_code == 200
        assert response.json() == {"items": [{"id": course, "title": "Safety 101"}]}


def test_certificate_lists_are_tenant_scoped_with_fixed_samples(client):
    for headers in ({}, {"X-Actor-Id": "unknown"}):
        assert client.get("/api/certificates", headers=headers).status_code == 401
    for actor, tenant, count in [("alice", "east", 12), ("bob", "west", 4)]:
        response = client.get("/api/certificates?tenant_id=east", headers={"X-Actor-Id": actor})
        assert response.status_code == 200
        data = response.json()
        assert (data["total"], data["page"], data["page_size"]) == (count, 1, 50)
        assert len(data["items"]) == count
        assert all(item["course_id"] == f"{tenant}-safety" for item in data["items"])
        assert data["items"][0] == {
            "id": f"{tenant}-cert-001", "serial_number": f"{tenant.upper()}-001",
            "learner_id": f"{tenant}-learner-001", "learner_name": "Alex Lee",
            "course_id": f"{tenant}-safety", "course_title": "Safety 101",
            "issued_at": "2026-01-10T13:30:00Z", "status": "ACTIVE",
            "issued_local_date": "2026-01-11" if tenant == "east" else "2026-01-10",
            "issued_local_datetime": "2026-01-11T00:30:00+11:00" if tenant == "east" else "2026-01-10T21:30:00+08:00",
            "timezone": "Australia/Sydney" if tenant == "east" else "Australia/Perth",
        }


def test_detail_requires_identity_and_hides_other_tenants(client):
    for headers in ({}, {"X-Actor-Id": "unknown"}):
        assert client.get("/api/certificates/east-cert-001", headers=headers).status_code == 401
    for actor, own, other in [("alice", "east", "west"), ("bob", "west", "east")]:
        headers = {"X-Actor-Id": actor}
        expected = client.get("/api/certificates", headers=headers).json()["items"][0]
        response = client.get(f"/api/certificates/{own}-cert-001", headers=headers)
        assert response.status_code == 200
        assert response.json() == expected
        forbidden = client.get(f"/api/certificates/{other}-cert-001?tenant_id={other}", headers=headers)
        missing = client.get("/api/certificates/missing", headers=headers)
        assert forbidden.status_code == missing.status_code == 404
        assert forbidden.json() == missing.json() == {"detail": "Not Found"}


def test_search_trims_and_matches_literal_names_or_serials(client):
    for query, expected in [
        ("  alex LEE  ", ["east-cert-001", "east-cert-002"]),
        (" east-012 ", ["east-cert-012"]),
        ("%", ["east-cert-003"]), ("_", ["east-cert-003"]),
        ("\\", ["east-cert-003"]), ("100%_\\", ["east-cert-003"]),
        ("' OR 1=1 --", []), ("absent", []),
    ]:
        response = client.get("/api/certificates", params={"q": query}, headers={"X-Actor-Id": "alice"})
        assert response.status_code == 200
        assert [item["id"] for item in response.json()["items"]] == expected
        assert response.json()["total"] == len(expected)


def test_pagination_preserves_totals_and_stable_sort_ties(client):
    headers = {"X-Actor-Id": "alice"}
    response = client.get("/api/certificates", headers=headers,
                          params={"page": 2, "page_size": 5, "order": "desc"})
    assert response.status_code == 200
    assert response.json() == {
        "items": client.get("/api/certificates", headers=headers).json()["items"][2:7][::-1],
        "total": 12, "page": 2, "page_size": 5,
    }
    assert client.get("/api/certificates?page=4&page_size=5", headers=headers).json() == {
        "items": [], "total": 12, "page": 4, "page_size": 5,
    }
    for order in ("asc", "desc"):
        ids = []
        for page in (1, 2):
            result = client.get("/api/certificates", headers=headers, params={
                "q": "Alex", "sort": "learner_name", "order": order, "page_size": 1, "page": page,
            }).json()
            assert result["total"] == 2
            ids.append(result["items"][0]["id"])
        assert ids == ["east-cert-001", "east-cert-002"]


def test_invalid_query_parameters_are_rejected(client):
    for parameters in [{"page": 0}, {"page": -1}, {"page": "x"},
                       {"page_size": 0}, {"page_size": 101}, {"page_size": "1.5"},
                       {"sort": "issued_at"}, {"sort": "serial_number; DROP TABLE certificate"},
                       {"order": "sideways"}]:
        assert client.get("/api/certificates", params=parameters,
                          headers={"X-Actor-Id": "alice"}).status_code == 422


def test_very_large_positive_page_returns_empty_with_real_total(client):
    response = client.get("/api/certificates?page=9223372036854775807",
                          headers={"X-Actor-Id": "alice"})
    assert response.status_code == 200
    assert response.json() == {
        "items": [], "total": 12, "page": 9223372036854775807, "page_size": 50,
    }


def test_restart_preserves_existing_certificate_data_and_seed_counts(tmp_path):
    database = tmp_path / "nested" / "certificates.sqlite3"
    headers = {"X-Actor-Id": "alice"}
    with TestClient(create_app(database_path=database)) as first:
        before = first.get("/api/certificates", headers=headers).json()
        assert before["total"] == 12
    assert database.is_file()
    # Arrange existing persisted data, then observe exclusively through HTTP.
    with sqlite3.connect(database) as setup:
        setup.execute("UPDATE certificate SET status = 'REVOKED' WHERE id = 'east-cert-001'")
    for _ in range(2):
        with TestClient(create_app(database_path=database)) as restarted:
            after = restarted.get("/api/certificates", headers=headers).json()
            assert after["total"] == 12
            assert after["items"][0]["status"] == "REVOKED"
            assert after["items"][1:] == before["items"][1:]
            assert restarted.get("/api/certificates", headers={"X-Actor-Id": "bob"}).json()["total"] == 4
