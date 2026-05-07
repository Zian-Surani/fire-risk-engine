"""Tests for settings and Databricks table FQN resolution."""

from __future__ import annotations

from pathlib import Path

from app.core.config import DEFAULT_TABLE_NAMES, Settings


def test_fq_table_joins_catalog_schema_and_logical_name() -> None:
    settings = Settings(
        project_root=Path("."),
        host="127.0.0.1",
        port=8000,
        frontend_origin="http://localhost:3000",
        databricks_host=None,
        databricks_auth_type=None,
        databricks_metadata_service_url=None,
        databricks_token=None,
        databricks_warehouse_id=None,
        databricks_catalog="main",
        databricks_schema="default",
        refresh_interval_seconds=5,
        risk_refresh_interval_seconds=60,
        ai_refresh_interval_seconds=60,
        websocket_ping_interval_seconds=15,
        gemini_api_key=None,
        gemini_model="gemini-2.0-flash",
        gemini_enabled=True,
        gemini_cache_ttl_seconds=900,
        gemini_rate_limit_cooldown_seconds=300,
        tables=dict(DEFAULT_TABLE_NAMES),
    )
    fq = settings.fq_table("gold_impact_simulation")
    assert fq == "main.default.gold_impact_simulation"


def test_repository_logical_keys_resolve_to_notebook_table_names() -> None:
    """FireRiskRepository keys must map to the same names used in saveAsTable()."""
    repo_keys = {
        "silver_fire_risk_base",
        "gold_top_100_critical_properties",
        "gold_district_intelligence",
        "gold_response_optimization",
        "gold_structured_recommendations",
        "gold_executive_metrics",
        "gold_repeat_offenders",
        "gold_impact_simulation",
        "gold_risk_heatmap_data",
        "gold_time_risk_analysis",
        "gold_action_playbook",
    }
    for key in repo_keys:
        assert key in DEFAULT_TABLE_NAMES
        assert DEFAULT_TABLE_NAMES[key] == key
