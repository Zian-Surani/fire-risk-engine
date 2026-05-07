from __future__ import annotations

import asyncio
from pathlib import Path

import app.clients.gemini_client as gemini_module
from app.clients.gemini_client import GeminiClient
from app.core.config import DEFAULT_TABLE_NAMES, Settings
from app.core.snapshot_cache import SnapshotCache
from app.core.websocket_hub import WebSocketHub
from app.snapshot_builder import RefreshOrchestrator


class DummyDatabricksClient:
    pass


def make_settings(**overrides: object) -> Settings:
    defaults: dict[str, object] = {
        "project_root": Path("."),
        "host": "127.0.0.1",
        "port": 8000,
        "frontend_origin": "http://localhost:3000",
        "databricks_host": None,
        "databricks_auth_type": None,
        "databricks_metadata_service_url": None,
        "databricks_token": None,
        "databricks_warehouse_id": None,
        "databricks_catalog": "workspace",
        "databricks_schema": "default",
        "refresh_interval_seconds": 5,
        "risk_refresh_interval_seconds": 60,
        "ai_refresh_interval_seconds": 60,
        "websocket_ping_interval_seconds": 15,
        "gemini_api_key": None,
        "gemini_model": "gemini-2.0-flash",
        "gemini_enabled": True,
        "gemini_cache_ttl_seconds": 900,
        "gemini_rate_limit_cooldown_seconds": 300,
        "tables": dict(DEFAULT_TABLE_NAMES),
    }
    defaults.update(overrides)
    return Settings(**defaults)


def test_warm_start_primes_dashboard_snapshots_using_mock_data() -> None:
    async def scenario() -> tuple[bool, dict[str, object], dict[str, object] | None, dict[str, object] | None]:
        settings = make_settings()
        cache = SnapshotCache()
        orchestrator = RefreshOrchestrator(
            settings=settings,
            db_client=DummyDatabricksClient(),
            ai_client=GeminiClient(settings),
            cache=cache,
            hub=WebSocketHub(),
        )
        warmed = await orchestrator.warm_start()
        meta = await cache.meta()
        command_center = await cache.get_snapshot("command-center")
        roadmap = await cache.get_snapshot("roadmap")
        return warmed, meta, command_center, roadmap

    warmed, meta, command_center, roadmap = asyncio.run(scenario())
    assert warmed is True
    assert command_center is not None
    assert roadmap is not None
    assert meta["last_refresh_success"] is True
    assert meta["source_status"] == "mock"


def test_refresh_once_seeds_roadmap_even_without_full_run_loop() -> None:
    async def scenario() -> tuple[dict[str, object] | None, dict[str, object] | None]:
        settings = make_settings()
        cache = SnapshotCache()
        orchestrator = RefreshOrchestrator(
            settings=settings,
            db_client=DummyDatabricksClient(),
            ai_client=GeminiClient(settings),
            cache=cache,
            hub=WebSocketHub(),
        )
        await orchestrator._refresh_once()
        return await cache.get_snapshot("roadmap"), await cache.get_snapshot("simulation")

    roadmap, simulation = asyncio.run(scenario())
    assert roadmap is not None
    assert simulation is not None


def test_gemini_client_falls_back_cleanly_when_sdk_missing(monkeypatch) -> None:
    settings = make_settings(gemini_api_key="test-key")
    monkeypatch.setattr(gemini_module, "genai", None)
    client = GeminiClient(settings)

    assert client._client is None
    assert asyncio.run(client.generate("decision-brief", "hello")) is None
