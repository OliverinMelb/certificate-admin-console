"""The delivery CLI exports visible source records, not internal model state."""
import json
import hashlib
from pathlib import Path
import subprocess
import sys

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/export_ai_evidence.py"


def record(kind, payload):
    return {"timestamp": "2026-11-13T00:00:00Z", "type": kind, "payload": payload}


def source(directory, identity, parent=None, fork=None, items=()):
    metadata = {"id": identity, "forked_from_id": fork}
    if parent:
        metadata["source"] = {"subagent": {"thread_spawn": {"parent_thread_id": parent, "agent_path": "/root/worker"}}}
    records = [record("session_meta", metadata), *items]
    (directory / f"{identity}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)


def test_export_preserves_visible_messages_and_excludes_internal_state(tmp_path):
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    source(sessions, "root", items=[
        record("response_item", {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "original request"}]}),
        record("response_item", {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "original answer"}], "internal_chat_message_metadata_passthrough": {"private": "INTERNAL_MARKER"}}),
        record("response_item", {"type": "message", "role": "system", "content": "SYSTEM_MARKER"}),
        record("response_item", {"type": "reasoning", "summary": "REASONING_MARKER"}),
        record("response_item", {"type": "function_call", "name": "test", "arguments": "{}", "call_id": "c1", "encrypted_content": "ENCRYPTED_MARKER"}),
        record("response_item", {"type": "function_call_output", "output": "failed as observed", "call_id": "c1"}),
        record("response_item", {"type": "agent_message", "content": "INTERNAL_AGENT_MARKER"}),
    ])
    output = tmp_path / "export"
    result = run("export", "--sessions", sessions, "--root", "root", "--output", output)
    assert result.returncode == 0, result.stderr
    transcript = (output / "transcripts/root.jsonl").read_text(encoding="utf-8")
    assert "original request" in transcript and "original answer" in transcript
    assert "failed as observed" in transcript
    assert all(marker not in transcript for marker in ["INTERNAL_MARKER", "SYSTEM_MARKER", "REASONING_MARKER", "ENCRYPTED_MARKER", "INTERNAL_AGENT_MARKER"])
    assert [json.loads(line)["source_line"] for line in transcript.splitlines()] == [2, 3, 6, 7]
    assert run("verify", "--output", output).returncode == 0


def test_export_follows_fork_and_nested_agents_without_unrelated_sessions(tmp_path):
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    source(sessions, "root")
    source(sessions, "fork", fork="root")
    source(sessions, "child", parent="fork")
    source(sessions, "grandchild", parent="child")
    source(sessions, "unrelated")
    before = {p.name: p.read_bytes() for p in sessions.iterdir()}
    output = tmp_path / "export"
    result = run("export", "--sessions", sessions, "--root", "root", "--output", output)
    assert result.returncode == 0, result.stderr
    manifest = json.loads((output / "manifest.json").read_text())
    assert {item["id"] for item in manifest["sessions"]} == {"root", "fork", "child", "grandchild"}
    assert {p.name: p.read_bytes() for p in sessions.iterdir()} == before
    assert run("export", "--sessions", sessions, "--root", "root", "--output", output).returncode != 0


def test_export_redacts_credentials_and_detects_changed_transcript(tmp_path):
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    source(sessions, "root", items=[record("response_item", {
        "type": "function_call_output", "call_id": "c1",
        "output": 'HTTP failed Authorization: Bearer synthetic-private-value; password="synthetic-password"',
    })])
    output = tmp_path / "export"
    assert run("export", "--sessions", sessions, "--root", "root", "--output", output).returncode == 0
    transcript = output / "transcripts/root.jsonl"
    content = transcript.read_text(encoding="utf-8")
    assert "synthetic-private-value" not in content and "synthetic-password" not in content
    assert "HTTP failed" in content and "[REDACTED]" in content
    ledger = json.loads((output / "dispositions/root.json").read_text())
    assert ledger[1]["redactions"] >= 2
    transcript.write_text(content + "changed", encoding="utf-8")
    assert run("verify", "--output", output).returncode != 0


def test_source_verification_allows_append_but_rejects_modified_prefix(tmp_path):
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    source(sessions, "root", items=[record("response_item", {"type": "message", "role": "user", "content": "original"})])
    output = tmp_path / "export"
    assert run("export", "--sessions", sessions, "--root", "root", "--output", output).returncode == 0
    path = sessions / "root.jsonl"
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record("event_msg", {"type": "later"})) + "\n")
    assert run("verify", "--sessions", sessions, "--output", output).returncode == 0
    path.write_text(path.read_text().replace("original", "modified"), encoding="utf-8")
    assert run("verify", "--sessions", sessions, "--output", output).returncode != 0


def test_structured_credentials_are_redacted_without_erasing_failure(tmp_path):
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    source(sessions, "root", items=[record("response_item", {
        "type": "function_call_output", "output": {"password": "fixture-secret", "status": "failure"},
    })])
    output = tmp_path / "export"
    assert run("export", "--sessions", sessions, "--root", "root", "--output", output).returncode == 0
    text = (output / "transcripts/root.jsonl").read_text(encoding="utf-8")
    assert "fixture-secret" not in text and "failure" in text


def test_source_verifier_rejects_rehashed_ledger_or_lineage_and_records_nested_filters(tmp_path):
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    source(sessions, "root", items=[record("response_item", {
        "type": "function_call_output", "output": {"data": "failure", "details": {"encrypted_content": "hidden"}},
    })])
    source(sessions, "child", parent="root")
    output = tmp_path / "export"
    assert run("export", "--sessions", sessions, "--root", "root", "--output", output).returncode == 0
    ledger_path = output / "dispositions/root.json"
    ledger = json.loads(ledger_path.read_text())
    assert "output.details.encrypted_content" in ledger[1]["omitted_fields"]
    original = {p: p.read_bytes() for p in output.rglob('*') if p.is_file()}
    for mutation in ("ledger", "lineage", "root", "missing_child"):
        for path, data in original.items(): path.write_bytes(data)
        manifest = json.loads((output / "manifest.json").read_text())
        if mutation == "ledger":
            ledger[1]["redactions"] = 999
            data = json.dumps(ledger).encode()
            ledger_path.write_bytes(data)
            manifest["files"]["dispositions/root.json"] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        elif mutation == "lineage":
            next(item for item in manifest["sessions"] if item["id"] == "child")["parent"] = "fake-parent"
        elif mutation == "root":
            manifest["root"] = "child"
        else:
            manifest["sessions"] = [item for item in manifest["sessions"] if item["id"] != "child"]
        data = json.dumps(manifest).encode()
        (output / "manifest.json").write_bytes(data)
        (output / "manifest.sha256").write_text(hashlib.sha256(data).hexdigest() + "\n")
        assert run("verify", "--sessions", sessions, "--output", output).returncode != 0, mutation
