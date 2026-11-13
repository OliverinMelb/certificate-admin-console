"""Export source-linked visible Codex records, excluding internal model/runtime data."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

PROTECTED = {"encrypted_content", "internal_chat_message_metadata_passthrough", "reasoning", "analysis", "system", "developer"}
FIELDS = {
    "message": ("type", "role", "content", "phase"),
    "function_call": ("type", "name", "namespace", "arguments", "call_id"),
    "custom_tool_call": ("type", "name", "input", "call_id"),
    "function_call_output": ("type", "name", "namespace", "output", "call_id"),
    "custom_tool_call_output": ("type", "output", "call_id"),
}
SECRET_PATTERNS = [
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+=*"),
    re.compile(r"\b(?:sk-proj-|ghp_)[A-Za-z0-9_-]{12,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r'''(?i)\b(?:password|api[_-]?key|access[_-]?token|refresh[_-]?token|cookie)\s*["']?\s*[:=]\s*["']?[^\s"';,}]+'''),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def clean(value, omitted, path=""):
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            child_path = f"{path}.{key}" if path else key
            if key in PROTECTED:
                omitted.append(child_path)
            else:
                result[key] = clean(item, omitted, child_path)
        return result
    if isinstance(value, list):
        result = []
        for index, item in enumerate(value):
            child_path = f"{path}[{index}]"
            if isinstance(item, dict) and item.get("type") in PROTECTED:
                omitted.append(child_path)
            else:
                result.append(clean(item, omitted, child_path))
        return result
    return value


def redact(value, counts):
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if re.fullmatch(r"password|api[_-]?key|access[_-]?token|refresh[_-]?token|cookie|authorization", key, re.I):
                result[key] = "[REDACTED]"
                counts["credentials"] += 1
            else:
                result[key] = redact(item, counts)
        return result
    if isinstance(value, list):
        return [redact(item, counts) for item in value]
    if isinstance(value, str):
        for pattern in SECRET_PATTERNS:
            value, count = pattern.subn("[REDACTED]", value)
            counts["credentials"] += count
    return value


def visible(row, omitted):
    payload = row.get("payload", {})
    kind = payload.get("type")
    if row.get("type") != "response_item" or kind not in FIELDS:
        return None
    if kind == "message" and (payload.get("role") not in {"user", "assistant"}
                              or payload.get("channel") == "analysis" or payload.get("phase") == "analysis"):
        return None
    omitted.extend(sorted(set(payload) - set(FIELDS[kind])))
    return clean({key: payload[key] for key in FIELDS[kind] if key in payload}, omitted)


def transform(rows):
    transcript, ledger = [], []
    for number, row in enumerate(rows, 1):
        omitted = []
        payload = visible(row, omitted)
        redactions = Counter()
        if payload is not None:
            payload = redact(payload, redactions)
            transcript.append({"source_line": number, "timestamp": row.get("timestamp"), "payload": payload})
        ledger.append({"source_line": number, "disposition": "exported" if payload is not None else "excluded",
                       "source_type": row.get("type"), "payload_type": row.get("payload", {}).get("type"),
                       "redactions": sum(redactions.values()), "omitted_fields": sorted(omitted)})
    return transcript, ledger


def inventory(directory):
    result = {}
    for path in directory.rglob("*.jsonl"):
        try:
            with path.open(encoding="utf-8") as stream:
                first = json.loads(next(stream))
                metadata = {**first.get("payload", {}), "_record_timestamp": first.get("timestamp")}
        except (ValueError, StopIteration):
            continue
        identity = metadata.get("id")
        if identity and re.fullmatch(r"[A-Za-z0-9_-]+", identity):
            if identity in result:
                raise ValueError(f"Duplicate session id: {identity}")
            result[identity] = (path, metadata)
    return result


def lineage(metadata):
    source = metadata.get("source")
    spawn = source.get("subagent", {}).get("thread_spawn", {}) if isinstance(source, dict) else {}
    return {"parent": spawn.get("parent_thread_id"), "fork": metadata.get("forked_from_id"),
            "agent_path": spawn.get("agent_path")}


def related(sources, root, cutoff=None):
    if root not in sources:
        raise ValueError("Root session not found")
    selected = {root}
    while True:
        children = {identity for identity, (_, metadata) in sources.items()
                    if (lineage(metadata)["parent"] in selected or lineage(metadata)["fork"] in selected)
                    and (not cutoff or not metadata.get("_record_timestamp")
                         or datetime.fromisoformat(metadata["_record_timestamp"]) <= datetime.fromisoformat(cutoff))}
        if children <= selected:
            return selected
        selected |= children


def source_fields(identity, path, metadata, rows, transcript, ledger):
    return {"id": identity, **lineage(metadata), "source_file": path.name,
            "source_lines": len(rows), "exported_records": len(transcript),
            "excluded_records": len(rows) - len(transcript),
            "credential_redactions": sum(item["redactions"] for item in ledger),
            "first_timestamp": rows[0].get("timestamp"), "last_timestamp": rows[-1].get("timestamp")}


def export(directory, root, output):
    sources = inventory(directory)
    selected = related(sources, root)
    output.mkdir(parents=True, exist_ok=False)
    (output / "transcripts").mkdir()
    (output / "dispositions").mkdir()
    entries = []
    for identity in sorted(selected):
        path, metadata = sources[identity]
        captured = path.read_bytes()
        boundary = captured.rfind(b"\n") + 1
        data = captured[:boundary]
        rows = [json.loads(line) for line in data.splitlines()]
        transcript, ledger = transform(rows)
        (output / f"transcripts/{identity}.jsonl").write_text(
            "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in transcript), encoding="utf-8")
        (output / f"dispositions/{identity}.json").write_bytes(encode(ledger))
        entries.append({**source_fields(identity, path, metadata, rows, transcript, ledger),
                        "source_prefix_bytes": len(data), "source_prefix_sha256": sha(data),
                        "incomplete_tail_bytes": len(captured) - boundary})
    files = {p.relative_to(output).as_posix(): {"bytes": p.stat().st_size, "sha256": sha(p.read_bytes())}
             for p in output.rglob("*") if p.is_file()}
    manifest = {"schema": 1, "root": root, "captured_at": datetime.now(timezone.utc).isoformat(),
                "format": "source-linked visible records; internal data excluded; not byte-for-byte raw logs",
                "raw_internal_export": False, "sessions": entries, "files": files}
    manifest_data = encode(manifest)
    (output / "manifest.json").write_bytes(manifest_data)
    (output / "manifest.sha256").write_text(sha(manifest_data) + "\n", encoding="utf-8")
    return manifest


def verify(output, sessions=None):
    data = (output / "manifest.json").read_bytes()
    if sha(data) != (output / "manifest.sha256").read_text(encoding="utf-8").strip():
        raise ValueError("Manifest checksum mismatch")
    manifest = json.loads(data)
    actual = {p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()}
    if actual != set(manifest["files"]) | {"manifest.json", "manifest.sha256"}:
        raise ValueError("File set mismatch")
    for name, entry in manifest["files"].items():
        path = (output / name).resolve()
        if not path.is_relative_to(output.resolve()) or path.is_symlink():
            raise ValueError("Unsafe member")
        content = path.read_bytes()
        if sha(content) != entry["sha256"] or len(content) != entry["bytes"]:
            raise ValueError("Member checksum mismatch")
    sources = inventory(sessions) if sessions else None
    identities = {entry["id"] for entry in manifest["sessions"]}
    if len(identities) != len(manifest["sessions"]):
        raise ValueError("Duplicate manifest session")
    if sources is not None and identities != related(sources, manifest["root"], manifest["captured_at"]):
        raise ValueError("Session relationship coverage mismatch")
    for entry in manifest["sessions"]:
        identity = entry["id"]
        if not re.fullmatch(r"[A-Za-z0-9_-]+", identity):
            raise ValueError("Unsafe session id")
        transcript = [json.loads(line) for line in (output / f"transcripts/{identity}.jsonl").read_text(encoding="utf-8").splitlines()]
        ledger = json.loads((output / f"dispositions/{identity}.json").read_text(encoding="utf-8"))
        if [item["source_line"] for item in ledger] != list(range(1, entry["source_lines"] + 1)):
            raise ValueError("Disposition ledger is incomplete")
        if [item["source_line"] for item in transcript] != [item["source_line"] for item in ledger if item["disposition"] == "exported"]:
            raise ValueError("Transcript coverage mismatch")
        if len(transcript) != entry["exported_records"]:
            raise ValueError("Record count mismatch")
        if sources is not None:
            with sources[identity][0].open("rb") as stream:
                prefix = stream.read(entry["source_prefix_bytes"])
            if len(prefix) != entry["source_prefix_bytes"] or sha(prefix) != entry["source_prefix_sha256"]:
                raise ValueError("Original source prefix changed")
            rows = [json.loads(line) for line in prefix.splitlines()]
            replay, expected_ledger = transform(rows)
            if replay != transcript or expected_ledger != ledger:
                raise ValueError("Transcript or ledger does not match original source")
            expected_fields = source_fields(identity, *sources[identity], rows, replay, expected_ledger)
            if any(entry[key] != value for key, value in expected_fields.items()):
                raise ValueError("Source metadata mismatch")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["export", "verify"])
    parser.add_argument("--sessions", type=Path)
    parser.add_argument("--root")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "export" and (not args.sessions or not args.root):
        parser.error("export requires --sessions and --root")
    result = export(args.sessions, args.root, args.output) if args.action == "export" else verify(args.output, args.sessions)
    print(json.dumps({"sessions": len(result["sessions"]), "records": sum(s["exported_records"] for s in result["sessions"])}))
