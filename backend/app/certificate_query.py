"""Tenant-scoped certificate reads and local calendar-day ordering."""

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException

from app.tenant_time import local_fields


CERTIFICATE_SELECT = """
    SELECT c.id, c.serial_number, c.learner_id, l.name AS learner_name,
           c.course_id, co.title AS course_title, c.issued_at, c.status
    FROM certificate c
    JOIN learner l ON l.tenant_id = c.tenant_id AND l.id = c.learner_id
    JOIN course co ON co.tenant_id = c.tenant_id AND co.id = c.course_id
"""


def tenant_zone(db, tenant_id: str) -> ZoneInfo:
    row = db.execute("SELECT timezone FROM tenant WHERE id = ?", (tenant_id,)).fetchone()
    try:
        return ZoneInfo(row["timezone"])
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=500, detail="Invalid tenant timezone") from exc


def project(row, zone: ZoneInfo):
    try:
        return {**dict(row), **local_fields(row["issued_at"], zone)}
    except ValueError as exc:
        raise HTTPException(status_code=500, detail="Invalid certificate timestamp") from exc


def list_certificates(db, tenant_id: str, q: str, page: int, page_size: int,
                      sort: str, order: str):
    zone = tenant_zone(db, tenant_id)
    escaped = q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped}%"
    where = """ WHERE c.tenant_id = ?
        AND (l.name LIKE ? ESCAPE '\\' OR c.serial_number LIKE ? ESCAPE '\\')"""
    parameters = (tenant_id, pattern, pattern)
    columns = {"learner_name": "l.name", "serial_number": "c.serial_number",
               "issue_date": "tenant_local_date(c.issued_at)"}
    column = columns[sort]
    invalid_timestamp = False
    if sort == "issue_date":
        def local_date(value):
            nonlocal invalid_timestamp
            try:
                return local_fields(value, zone)["issued_local_date"]
            except ValueError:
                invalid_timestamp = True
                return None

        db.create_function("tenant_local_date", 1,
                           local_date, deterministic=True)
    direction = "DESC" if order == "desc" else "ASC"
    total = db.execute("SELECT COUNT(*) FROM (" + CERTIFICATE_SELECT + where + ")",
                       parameters).fetchone()[0]
    offset = (page - 1) * page_size
    if offset >= total:
        return {"items": [], "total": total, "page": page, "page_size": page_size}
    items = [project(row, zone) for row in db.execute(
        CERTIFICATE_SELECT + where + f" ORDER BY {column} {direction}, c.id ASC LIMIT ? OFFSET ?",
        (*parameters, page_size, offset)
    )]
    if invalid_timestamp:
        raise HTTPException(status_code=500, detail="Invalid certificate timestamp")
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def get_certificate(db, tenant_id: str, certificate_id: str):
    row = db.execute(CERTIFICATE_SELECT + " WHERE c.tenant_id = ? AND c.id = ?",
                     (tenant_id, certificate_id)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Not Found")
    return project(row, tenant_zone(db, tenant_id))
