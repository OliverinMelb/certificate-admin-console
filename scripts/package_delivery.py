"""Build a local source ZIP and verify its byte manifest; no network or exports."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "DELIVERY-MANIFEST.json"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def allowed(name):
    path = PurePosixPath(name)
    excluded = {".git", ".venv", "node_modules", "dist", "__pycache__", ".pytest_cache", ".smoke", "data"}
    return ("\\" not in name and ":" not in name and not path.is_absolute() and ".." not in path.parts
            and not excluded.intersection(path.parts)
            and not any(part == ".env" or part.startswith(".env.") for part in path.parts)
            and path.suffix not in {".pyc", ".sqlite", ".sqlite3", ".db", ".jsonl"})


def verify(path, *, check_sidecar=True):
    if check_sidecar:
        expected_checksum = path.with_suffix(path.suffix + ".sha256").read_text(encoding="utf-8").strip()
        if expected_checksum != f"{digest(path.read_bytes())}  {path.name}":
            raise ValueError("ZIP sidecar SHA256 mismatch")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate ZIP entries")
        manifest = json.loads(archive.read(MANIFEST))
        expected = manifest["files"]
        if set(names) != set(expected) | {MANIFEST}:
            raise ValueError("Archive/manifest file set mismatch")
        for name, entry in expected.items():
            data = archive.read(name)
            if not allowed(name) or len(data) != entry["bytes"] or digest(data) != entry["sha256"]:
                raise ValueError(f"Invalid archive member: {name}")
    return manifest


def build(path, working_tree):
    if path.exists():
        raise ValueError("Output exists; use a new filename")
    dirty = bool(git("status", "--porcelain"))
    if dirty and not working_tree:
        raise ValueError("Clean committed tree required; --working-tree is only for precommit validation")
    names = sorted(set(git("ls-files", "-z", "--cached", "--others", "--exclude-standard").decode().split("\0")) - {""})
    files = {}
    for name in names:
        source = ROOT / name
        if not allowed(name):
            raise ValueError(f"Excluded file is tracked or unignored: {name}")
        if source.is_symlink() or not source.is_file() or not source.resolve().is_relative_to(ROOT):
            raise ValueError(f"Not an ordinary repository file: {name}")
        files[name] = source.read_bytes()
    manifest = {
        "schema": 1, "base_commit": git("rev-parse", "HEAD").decode().strip(),
        "working_tree_snapshot": dirty,
        "original_ai_export_complete": False,
        "files": {name: {"bytes": len(data), "sha256": digest(data)} for name, data in files.items()},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
        archive.writestr(MANIFEST, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    verify(path, check_sidecar=False)
    checksum = digest(path.read_bytes())
    path.with_suffix(path.suffix + ".sha256").write_text(f"{checksum}  {path.name}\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["build", "verify"])
    parser.add_argument("archive", type=Path)
    parser.add_argument("--working-tree", action="store_true")
    args = parser.parse_args()
    result = build(args.archive, args.working_tree) if args.action == "build" else verify(args.archive)
    print(json.dumps({"files": len(result["files"]), "base_commit": result["base_commit"],
                      "working_tree_snapshot": result["working_tree_snapshot"],
                      "sha256": digest(args.archive.read_bytes())}, indent=2))
