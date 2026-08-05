"""Timestamp helpers for Olist values, without timezone conversion."""

from datetime import datetime
from typing import Any, Optional


def parse_olist_timestamp(value: Any, field_name: str) -> Optional[datetime]:
    if value is None or str(value).strip() == "":
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(f"Invalid {field_name} timestamp: {value!r}") from exc
