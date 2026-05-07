from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


PRIORITY_WEIGHT = {
    "CRITICAL": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
}


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def to_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def priority_score(priority: str) -> int:
    return PRIORITY_WEIGHT.get((priority or "").upper(), 0)


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))
