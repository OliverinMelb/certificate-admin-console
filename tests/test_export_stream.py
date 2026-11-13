"""Real TCP tests: buffered TestClient is deliberately not used for streaming."""

import csv
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import time

import httpx
import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def live_export(tmp_path):
    path = tmp_path / 'network.sqlite3'
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    env = {**os.environ, 'PYTHONPATH': str(ROOT / 'backend'), 'PYTHONUTF8': '1'}
    code = '''import os,sys,threading,uvicorn
from app.main import create_app
server = uvicorn.Server(uvicorn.Config(create_app(sys.argv[1]),host="127.0.0.1",port=int(sys.argv[2]),log_level="error"))
threading.Thread(target=lambda: (os.read(sys.stdin.fileno(),1),setattr(server,"should_exit",True)),daemon=True).start()
server.run()
'''
    process = subprocess.Popen([sys.executable, '-c', code, str(path), str(port)], env=env,
                               stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    base = f'http://127.0.0.1:{port}'
    with httpx.Client(base_url=base, timeout=15, trust_env=False) as client:
        try:
            deadline = time.monotonic() + 15
            while True:
                try:
                    if client.get('/api/health').status_code == 200:
                        break
                except httpx.TransportError:
                    pass
                if time.monotonic() > deadline:
                    raise AssertionError('network server did not start')
                time.sleep(.05)
            # > socket buffers: paused consumption must retain an active read snapshot.
            with sqlite3.connect(path) as db:
                db.execute('PRAGMA foreign_keys=ON')
                db.executemany('INSERT INTO learner VALUES (?, ?, ?)',
                               [(f'large-{i:05}', 'east', f'{i:05}-' + 'x' * 4096) for i in range(6000)])
                db.executemany('INSERT INTO enrollment VALUES (?, ?, ?, ?, ?)',
                               [(f'large-enrollment-{i:05}', 'east', 'east-safety', f'large-{i:05}', 1)
                                for i in range(6000)])
                db.executemany('INSERT INTO certificate VALUES (?, ?, ?, ?, ?, ?, ?)',
                               [(f'large-{i:05}', 'east', f'LARGE-{i:05}', 'east-safety', f'large-{i:05}',
                                 '2026-01-10T13:30:00Z', 'ACTIVE') for i in range(6000)])
            yield client, path
        finally:
            process.stdin.close()
            process.wait(timeout=10)
            process.stderr.close()


def test_stream_snapshot_allows_list_and_releases_reader_after_disconnect(live_export):
    client, path = live_export
    headers = {'X-Actor-Id': 'alice'}
    with client.stream('GET', '/api/certificates/export.csv', headers=headers) as response:
        assert response.status_code == 200
        assert response.headers.get('transfer-encoding') == 'chunked'
        chunks = response.iter_bytes()
        assert next(chunks).startswith(b'\xef\xbb\xbf')
        assert client.get('/api/certificates', headers=headers).status_code == 200
        with sqlite3.connect(path) as db:
            db.execute("UPDATE learner SET name='changed after snapshot' WHERE id='large-05999'")
        with sqlite3.connect(path, timeout=.05) as db:
            assert db.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()[0] == 1
    deadline = time.monotonic() + 5
    while True:
        with sqlite3.connect(path, timeout=.05) as db:
            released = db.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()[0] == 0
        if released:
            break
        assert time.monotonic() < deadline, 'disconnected export retained its snapshot'
        time.sleep(.05)
    assert client.get('/api/certificates', headers=headers).status_code == 200


def test_stream_keeps_snapshot_while_new_export_sees_committed_change(live_export):
    client, _ = live_export
    headers = {'X-Actor-Id': 'alice'}
    with client.stream('GET', '/api/certificates/export.csv', headers=headers) as response:
        lines = response.iter_lines()
        assert next(lines).startswith('\ufefflearner_name,')
        # A real business write after the CSV snapshot starts.
        revoke = client.post('/api/courses/east-safety/issue',
                             headers={**headers, 'Idempotency-Key': 'snapshot-issuance'})
        assert revoke.status_code == 200
        issued = [o for o in revoke.json()['outcomes'] if o['outcome'] == 'issued']
        assert len(issued) == 1
        content = list(csv.reader(lines))
        assert len(content) == 6012
    with client.stream('GET', '/api/certificates/export.csv', headers=headers) as response:
        assert sum(1 for _ in response.iter_lines()) == 6014


def test_generator_cli_requires_new_path_and_preserves_existing_file(tmp_path):
    target = tmp_path / 'performance.sqlite3'
    command = [sys.executable, str(ROOT / 'scripts/generate_export_fixture.py'),
               '--database', str(target), '--rows', '1005']
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    original = target.read_bytes()
    repeated = subprocess.run(command, capture_output=True, text=True)
    assert repeated.returncode != 0
    assert target.read_bytes() == original


def test_disconnect_before_first_response_does_not_leave_reader(live_export):
    client, path = live_export
    host, port = client.base_url.host, client.base_url.port
    with socket.create_connection((host, port), timeout=5) as peer:
        peer.sendall(b'GET /api/certificates/export.csv?sort=issue_date HTTP/1.1\r\n'
                     b'Host: localhost\r\nX-Actor-Id: alice\r\n\r\n')
        # Disconnect without reading headers, including the initial query/sort interval.
    assert client.get('/api/certificates', headers={'X-Actor-Id': 'alice'}).status_code == 200
    deadline = time.monotonic() + 5
    while True:
        with sqlite3.connect(path, timeout=.05) as db:
            db.execute("UPDATE learner SET name='after early disconnect' WHERE id='east-learner-001'")
        with sqlite3.connect(path, timeout=.05) as db:
            released = db.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()[0] == 0
        if released:
            break
        assert time.monotonic() < deadline
        time.sleep(.05)
