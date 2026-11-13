"""Exercise the documented command and real HTTP, never launcher internals."""

import os
from pathlib import Path
import re
import shutil
import signal
import socket
import subprocess
import time

import httpx


ROOT = Path(__file__).resolve().parents[1]


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def copy_project(target):
    target.mkdir()
    for name in ("frontend", "backend", "scripts"):
        if (ROOT / name).exists():
            shutil.copytree(
                ROOT / name, target / name,
                ignore=shutil.ignore_patterns("node_modules", "dist", ".venv", "__pycache__", ".pytest_cache"),
            )
    for name in (".python-version", ".node-version"):
        shutil.copy2(ROOT / name, target / name)


def launch(project, port, log):
    return subprocess.Popen(
        ["node", str(project / "scripts" / "start.mjs"), "--port", str(port)],
        cwd=project.parent, stdout=log, stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
    )


def await_ready(process, base_url, log_path):
    deadline = time.monotonic() + 180
    with httpx.Client(base_url=base_url, trust_env=False, timeout=1) as client:
        while time.monotonic() < deadline:
            assert process.poll() is None, log_path.read_text(encoding="utf-8", errors="replace")
            try:
                response = client.get("/api/health")
                if response.status_code == 200:
                    assert response.json() == {"status": "ok"}
                    return
            except httpx.TransportError:
                pass
            time.sleep(0.2)
    raise AssertionError(log_path.read_text(encoding="utf-8", errors="replace"))


def stop(process):
    if process.poll() is None:
        process.send_signal(signal.CTRL_BREAK_EVENT if os.name == "nt" else signal.SIGINT)
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
            else:
                process.kill()
            raise AssertionError("Launcher failed to stop within 15 seconds")


def await_port_closed(port):
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return
        time.sleep(0.1)
    raise AssertionError("Application still listens after launcher stopped")


def test_clean_copy_starts_from_documented_command(tmp_path):
    project = tmp_path / "certificate admin 空间"
    copy_project(project)
    locks = {name: (project / name).read_bytes() for name in ("frontend/package-lock.json", "backend/uv.lock")}
    port = free_port()
    url = f"http://127.0.0.1:{port}"
    log_path = tmp_path / "startup.log"
    with log_path.open("w", encoding="utf-8") as log:
        process = launch(project, port, log)
        try:
            await_ready(process, url, log_path)
            with httpx.Client(base_url=url, trust_env=False) as client:
                page = client.get("/")
                assert page.status_code == 200
                scripts = re.findall(r'<script[^>]+src="([^"]+)"', page.text)
                assert scripts
                for source in scripts:
                    asset = client.get(source)
                    assert asset.status_code == 200
                    assert "javascript" in asset.headers["content-type"]
                assert client.get("/api/unknown").status_code == 404
            for name, original in locks.items():
                assert (project / name).read_bytes() == original
        finally:
            stop(process)
        await_port_closed(port)
        process = launch(project, port, log)
        try:
            await_ready(process, url, log_path)
            for name, original in locks.items():
                assert (project / name).read_bytes() == original
        finally:
            stop(process)
        await_port_closed(port)


def test_server_exits_if_launcher_is_terminated(tmp_path):
    project = tmp_path / "project"
    copy_project(project)
    port = free_port()
    log_path = tmp_path / "terminated.log"
    server_pid = None
    with log_path.open("w", encoding="utf-8") as log:
        process = launch(project, port, log)
        try:
            await_ready(process, f"http://127.0.0.1:{port}", log_path)
            server_pid = int(re.search(r"Started server process \[(\d+)\]", log_path.read_text(encoding="utf-8")).group(1))
            process.kill()
            process.wait(timeout=5)
            await_port_closed(port)
        finally:
            stop(process)
            # Clean up only this test's known server process if the assertion fails.
            if server_pid:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(server_pid), "/T", "/F"], capture_output=True)
                else:
                    try:
                        os.kill(server_pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass


def test_occupied_port_is_preserved_and_startup_fails(tmp_path):
    project = tmp_path / "project"
    copy_project(project)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        with (tmp_path / "occupied.log").open("w", encoding="utf-8") as log:
            process = launch(project, port, log)
            try:
                assert process.wait(timeout=180) != 0
                with socket.create_connection(("127.0.0.1", port), timeout=1):
                    connection, _ = listener.accept()
                    connection.close()
            finally:
                stop(process)


def test_outdated_lock_fails_without_starting_service(tmp_path):
    project = tmp_path / "project"
    copy_project(project)
    pyproject = project / "backend/pyproject.toml"
    pyproject.write_text(pyproject.read_text().replace('version = "0.1.0"', 'version = "0.2.0"'))
    lock = (project / "backend/uv.lock").read_bytes()
    port = free_port()
    log_path = tmp_path / "lock-error.log"
    with log_path.open("w", encoding="utf-8") as log:
        process = launch(project, port, log)
        try:
            assert process.wait(timeout=60) != 0
            assert "Sync Python dependencies failed" in log_path.read_text(encoding="utf-8")
            assert (project / "backend/uv.lock").read_bytes() == lock
            await_port_closed(port)
        finally:
            stop(process)
