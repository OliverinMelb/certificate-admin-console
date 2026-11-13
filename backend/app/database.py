"""File-backed demo data; initialization never replaces existing rows."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def connect(path: Path):
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    try:
        yield connection
    finally:
        connection.close()


def initialize(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as db:
        db.execute("PRAGMA journal_mode = WAL")
    with connect(path) as db, db:
        db.execute("BEGIN")
        db.execute("""CREATE TABLE IF NOT EXISTS tenant (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, timezone TEXT NOT NULL)""")
        db.execute("""CREATE TABLE IF NOT EXISTS admin (
            id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenant(id),
            email TEXT NOT NULL, UNIQUE(tenant_id, id))""")
        db.execute("""CREATE TABLE IF NOT EXISTS course (
            id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenant(id),
            title TEXT NOT NULL, UNIQUE(tenant_id, id))""")
        db.execute("""CREATE TABLE IF NOT EXISTS learner (
            id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenant(id),
            name TEXT NOT NULL, UNIQUE(tenant_id, id))""")
        db.execute("""CREATE TABLE IF NOT EXISTS enrollment (
            id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenant(id),
            course_id TEXT NOT NULL, learner_id TEXT NOT NULL,
            completed INTEGER NOT NULL CHECK(completed IN (0, 1)),
            UNIQUE(tenant_id, course_id, learner_id),
            FOREIGN KEY(tenant_id, course_id) REFERENCES course(tenant_id, id),
            FOREIGN KEY(tenant_id, learner_id) REFERENCES learner(tenant_id, id))""")
        db.execute("""CREATE TABLE IF NOT EXISTS certificate (
            id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenant(id),
            serial_number TEXT NOT NULL, course_id TEXT NOT NULL, learner_id TEXT NOT NULL,
            issued_at TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('ACTIVE', 'REVOKED')),
            UNIQUE(tenant_id, serial_number),
            FOREIGN KEY(tenant_id, course_id, learner_id)
                REFERENCES enrollment(tenant_id, course_id, learner_id))""")
        db.execute("CREATE INDEX IF NOT EXISTS certificate_tenant_serial ON certificate(tenant_id, serial_number, id)")
        db.execute("CREATE INDEX IF NOT EXISTS certificate_enrollment ON certificate(tenant_id, course_id, learner_id)")
        for tenant, name, timezone, actor in [
            ("east", "East", "Australia/Sydney", "alice"),
            ("west", "West", "Australia/Perth", "bob"),
        ]:
            db.execute("INSERT INTO tenant VALUES (?, ?, ?) ON CONFLICT DO NOTHING",
                       (tenant, name, timezone))
            db.execute("INSERT INTO admin VALUES (?, ?, ?) ON CONFLICT DO NOTHING",
                       (actor, tenant, f"{actor}@{tenant}.test"))
            db.execute("INSERT INTO course VALUES (?, ?, ?) ON CONFLICT DO NOTHING",
                       (f"{tenant}-safety", tenant, "Safety 101"))
            count = 12 if tenant == "east" else 4
            for number in range(1, count + 3):
                learner = f"{tenant}-learner-{number:03}"
                name = "Alex Lee" if number <= 2 else f"Learner {number:03}"
                if number == 3:
                    name = "Case 100%_\\ Complete"
                db.execute("INSERT INTO learner VALUES (?, ?, ?) ON CONFLICT DO NOTHING",
                           (learner, tenant, name))
                db.execute("INSERT INTO enrollment VALUES (?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
                           (f"{tenant}-enrollment-{number:03}", tenant, f"{tenant}-safety",
                            learner, int(number != count + 2)))
                if number <= count:
                    db.execute("INSERT INTO certificate VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
                               (f"{tenant}-cert-{number:03}", tenant, f"{tenant.upper()}-{number:03}",
                                f"{tenant}-safety", learner, "2026-01-10T13:30:00Z", "ACTIVE"))
