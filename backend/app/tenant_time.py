"""Tenant-local projections of stored UTC instants, shared by reads and export."""

from datetime import datetime
from zoneinfo import ZoneInfo


def local_fields(issued_at: str, zone: ZoneInfo) -> dict[str, str]:
    instant = datetime.fromisoformat(issued_at)
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("Certificate timestamps must include an offset")
    local = instant.astimezone(zone)
    return {
        "issued_local_date": local.date().isoformat(),
        "issued_local_datetime": local.isoformat(),
        "timezone": zone.key,
    }
