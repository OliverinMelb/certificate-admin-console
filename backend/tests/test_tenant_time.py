import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def api(tmp_path):
    path = tmp_path / "dates.sqlite3"
    with TestClient(create_app(database_path=path)) as client:
        yield client, path


def test_list_and_detail_preserve_utc_and_use_server_tenant_timezone(api):
    client, _ = api
    for actor, tenant, local_date, local_datetime, zone in [
        ("alice", "east", "2026-01-11", "2026-01-11T00:30:00+11:00", "Australia/Sydney"),
        ("bob", "west", "2026-01-10", "2026-01-10T21:30:00+08:00", "Australia/Perth"),
    ]:
        headers = {"X-Actor-Id": actor}
        response = client.get("/api/certificates?timezone=UTC", headers=headers)
        assert response.status_code == 200
        item = response.json()["items"][0]
        assert item["issued_at"] == "2026-01-10T13:30:00Z"
        assert item["issued_local_date"] == local_date
        assert item["issued_local_datetime"] == local_datetime
        assert item["timezone"] == zone
        detail = client.get(f"/api/certificates/{tenant}-cert-001", headers=headers)
        assert detail.status_code == 200
        assert detail.json() == item


def test_local_day_sort_precedes_pagination_and_uses_id_within_each_day(api):
    client, path = api
    # Same local day deliberately has UTC times opposite to the ID order.
    with sqlite3.connect(path) as db:
        db.executemany("UPDATE certificate SET issued_at = ? WHERE id = ?", [
            ("2026-01-10T12:59:00Z", "east-cert-001"),
            ("2026-01-10T13:01:00Z", "east-cert-002"),
            ("2026-01-10T01:00:00Z", "east-cert-003"),
            ("2026-01-11T13:00:00Z", "east-cert-004"),
        ])
    headers = {"X-Actor-Id": "alice"}
    for order, expected in [
        ("asc", ["east-cert-001", "east-cert-003", "east-cert-002",
                 "east-cert-005", "east-cert-006", "east-cert-007", "east-cert-008",
                 "east-cert-009", "east-cert-010", "east-cert-011", "east-cert-012", "east-cert-004"]),
        ("desc", ["east-cert-004", "east-cert-002", "east-cert-005", "east-cert-006",
                  "east-cert-007", "east-cert-008", "east-cert-009", "east-cert-010",
                  "east-cert-011", "east-cert-012", "east-cert-001", "east-cert-003"]),
    ]:
        actual = []
        for page in range(1, 5):
            response = client.get("/api/certificates", headers=headers,
                                  params={"sort": "issue_date", "order": order,
                                          "page": page, "page_size": 3})
            assert response.status_code == 200
            assert response.json()["total"] == 12
            actual.extend(item["id"] for item in response.json()["items"])
        assert actual == expected


def test_invalid_timezone_is_an_explicit_server_error_without_fallback(api):
    client, path = api
    with sqlite3.connect(path) as db:
        db.execute("UPDATE tenant SET timezone = 'Unknown/Zone' WHERE id = 'east'")
    for route in ("/api/certificates", "/api/certificates/east-cert-001"):
        response = client.get(route, headers={"X-Actor-Id": "alice"})
        assert response.status_code == 500
        assert response.json() == {"detail": "Invalid tenant timezone"}
    assert client.get("/api/certificates", headers={"X-Actor-Id": "bob"}).status_code == 200


def test_naive_or_malformed_stored_time_never_uses_host_timezone(api):
    client, path = api
    for value in ("2026-01-10T13:30:00", "not-a-timestamp"):
        with sqlite3.connect(path) as db:
            db.execute("UPDATE certificate SET issued_at = ? WHERE id = 'east-cert-001'", (value,))
        for route in ("/api/certificates", "/api/certificates?sort=issue_date",
                      "/api/certificates/east-cert-001"):
            response = client.get(route, headers={"X-Actor-Id": "alice"})
            assert response.status_code == 500
            assert response.json() == {"detail": "Invalid certificate timestamp"}


@pytest.mark.parametrize("utc, local", [
    ("2026-07-01T13:30:00Z", "2026-07-01T23:30:00+10:00"),
    ("2026-04-04T15:59:00Z", "2026-04-05T02:59:00+11:00"),
    ("2026-04-04T16:00:00Z", "2026-04-05T02:00:00+10:00"),
    ("2026-10-03T15:59:00Z", "2026-10-04T01:59:00+10:00"),
    ("2026-10-03T16:00:00Z", "2026-10-04T03:00:00+11:00"),
])
def test_sydney_standard_time_and_both_dst_transitions(api, utc, local):
    client, path = api
    with sqlite3.connect(path) as db:
        db.execute("UPDATE certificate SET issued_at = ? WHERE id = 'east-cert-001'", (utc,))
    headers = {"X-Actor-Id": "alice"}
    item = client.get("/api/certificates/east-cert-001", headers=headers).json()
    assert item["issued_at"] == utc
    assert item["issued_local_datetime"] == local
    assert item["issued_local_date"] == local[:10]
    assert client.get("/api/certificates?q=EAST-001&sort=issue_date", headers=headers).json()["items"] == [item]
