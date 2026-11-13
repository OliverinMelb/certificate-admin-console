import csv
import io
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def api(tmp_path):
    path = tmp_path / 'export.sqlite3'
    with TestClient(create_app(database_path=path)) as client:
        yield client, path


def rows(response):
    return list(csv.reader(io.StringIO(response.content.decode('utf-8-sig'), newline='')))


def test_csv_has_four_columns_bom_crlf_and_tenant_local_dates(api):
    client, _ = api
    response = client.get('/api/certificates/export.csv', headers={'X-Actor-Id': 'alice'})
    assert response.status_code == 200
    assert response.content.startswith(b'\xef\xbb\xbf')
    assert response.headers['content-type'] == 'text/csv; charset=utf-8'
    assert 'attachment;' in response.headers['content-disposition']
    data = rows(response)
    assert data[0] == ['learner_name', 'course_title', 'serial_number', 'issued_local_date']
    assert len(data) == 13
    assert data[1] == ['Alex Lee', 'Safety 101', 'EAST-001', '2026-01-11']
    assert response.content.endswith(b'\r\n')


def test_csv_quotes_text_and_neutralizes_formula_prefixes_without_changing_records(api):
    client, path = api
    names = ['中文,"换行\n学员', ' =1+1', '\ttext', '\x01@SUM(A1)', '+42', '-42']
    with sqlite3.connect(path) as db:
        db.executemany('UPDATE learner SET name=? WHERE id=?',
                       [(name, f'east-learner-{i:03}') for i, name in enumerate(names, 1)])
    data = rows(client.get('/api/certificates/export.csv', headers={'X-Actor-Id': 'alice'}))
    assert [row[0] for row in data[1:7]] == [names[0], *["'" + name for name in names[1:]]]
    detail = client.get('/api/certificates/east-cert-002', headers={'X-Actor-Id': 'alice'})
    assert detail.json()['learner_name'] == ' =1+1'


def test_csv_is_tenant_scoped_filtered_stable_and_not_limited_to_one_page(api):
    client, path = api
    with sqlite3.connect(path) as db:
        db.execute("UPDATE certificate SET status='REVOKED' WHERE id='east-cert-001'")
        db.execute("UPDATE certificate SET issued_at='2026-01-09T13:30:00Z' WHERE id='east-cert-002'")
    for sort in ['learner_name', 'serial_number', 'issue_date']:
        for order in ['asc', 'desc']:
            params = {'sort': sort, 'order': order}
            response = client.get('/api/certificates/export.csv', params=params, headers={'X-Actor-Id': 'alice'})
            expected = client.get('/api/certificates', params={**params, 'page_size': 100},
                                  headers={'X-Actor-Id': 'alice'}).json()['items']
            assert [r[2] for r in rows(response)[1:]] == [r['serial_number'] for r in expected]
            assert len(rows(response)) == 13
            assert rows(response) == rows(client.get('/api/certificates/export.csv', params=params,
                                                     headers={'X-Actor-Id': 'alice'}))
    west = rows(client.get('/api/certificates/export.csv', headers={'X-Actor-Id': 'bob'}))
    assert len(west) == 5 and all(r[2].startswith('WEST-') for r in west[1:])
    assert west[1][3] == '2026-01-10'
    literal = rows(client.get('/api/certificates/export.csv?q=100%25_', headers={'X-Actor-Id': 'alice'}))
    assert [r[2] for r in literal[1:]] == ['EAST-003']
    empty = rows(client.get('/api/certificates/export.csv?q=no-such-person', headers={'X-Actor-Id': 'alice'}))
    assert len(empty) == 1
    for params in [{'page': 1}, {'page_size': 100}, {'sort': 'bad'}, {'order': 'bad'}]:
        assert client.get('/api/certificates/export.csv', params=params,
                          headers={'X-Actor-Id': 'alice'}).status_code == 422
    assert client.get('/api/certificates/export.csv').status_code == 401


def test_invalid_timezone_or_timestamp_fails_before_csv_headers(api):
    client, path = api
    with sqlite3.connect(path) as db:
        db.execute("UPDATE tenant SET timezone='Invalid/Zone' WHERE id='east'")
    assert client.get('/api/certificates/export.csv', headers={'X-Actor-Id': 'alice'}).status_code == 500
    with sqlite3.connect(path) as db:
        db.execute("UPDATE tenant SET timezone='Australia/Sydney' WHERE id='east'")
        db.execute("UPDATE certificate SET issued_at='invalid' WHERE id='east-cert-001'")
    response = client.get('/api/certificates/export.csv?sort=issue_date', headers={'X-Actor-Id': 'alice'})
    assert response.status_code == 500 and response.headers['content-type'] == 'application/json'
