from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class QueryResult:
    rows: list[dict[str, Any]]
    columns: list[str]
    duration_ms: float
