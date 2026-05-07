from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any


class SnapshotCache:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._snapshots: dict[str, dict[str, Any]] = {}
        self._meta: dict[str, Any] = {
            "last_refresh_started_at": None,
            "last_refresh_completed_at": None,
            "last_refresh_success": False,
            "source_status": "initializing",
            "query_latency_ms": 0.0,
            "ai_latency_ms": 0.0,
            "alerts": [],
            "optimization": None,
            "simulation": None,
        }

    async def set_snapshot(self, name: str, snapshot: dict[str, Any]) -> None:
        async with self._lock:
            self._snapshots[name] = deepcopy(snapshot)

    async def get_snapshot(self, name: str) -> dict[str, Any] | None:
        async with self._lock:
            snapshot = self._snapshots.get(name)
            return deepcopy(snapshot) if snapshot else None

    async def get_all(self) -> dict[str, dict[str, Any]]:
        async with self._lock:
            return deepcopy(self._snapshots)

    async def mark_refresh_started(self) -> None:
        async with self._lock:
            self._meta["last_refresh_started_at"] = datetime.now(UTC).isoformat()

    async def mark_refresh_completed(
        self,
        *,
        success: bool,
        source_status: str,
        query_latency_ms: float,
        ai_latency_ms: float,
        alerts: list[str],
    ) -> None:
        async with self._lock:
            self._meta["last_refresh_completed_at"] = datetime.now(UTC).isoformat()
            self._meta["last_refresh_success"] = success
            self._meta["source_status"] = source_status
            self._meta["query_latency_ms"] = round(query_latency_ms, 2)
            self._meta["ai_latency_ms"] = round(ai_latency_ms, 2)
            self._meta["alerts"] = alerts

    async def set_runtime_artifact(self, name: str, artifact: dict[str, Any] | None) -> None:
        async with self._lock:
            self._meta[name] = deepcopy(artifact)

    async def get_runtime_artifact(self, name: str) -> dict[str, Any] | None:
        async with self._lock:
            value = self._meta.get(name)
            return deepcopy(value) if isinstance(value, dict) else value

    async def meta(self) -> dict[str, Any]:
        async with self._lock:
            return deepcopy(self._meta)
