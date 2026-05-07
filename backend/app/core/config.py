from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# Logical keys → unqualified Delta table names produced by the Databricks notebooks
# (see databricks/03_gold_layer*.py saveAsTable calls). Override with env TABLE_<KEY>.
DEFAULT_TABLE_NAMES = {
    "silver_fire_risk_base": "silver_fire_risk_base",
    "gold_top_100_critical_properties": "gold_top_100_critical_properties",
    "gold_district_intelligence": "gold_district_intelligence",
    "gold_response_optimization": "gold_response_optimization",
    "gold_structured_recommendations": "gold_structured_recommendations",
    "gold_executive_metrics": "gold_executive_metrics",
    "gold_repeat_offenders": "gold_repeat_offenders",
    "gold_impact_simulation": "gold_impact_simulation",
    "gold_risk_heatmap_data": "gold_risk_heatmap_data",
    "gold_time_risk_analysis": "gold_time_risk_analysis",
    "gold_action_playbook": "gold_action_playbook",
}


def _load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


@dataclass(slots=True)
class Settings:
    project_root: Path
    host: str
    port: int
    frontend_origin: str
    databricks_host: str | None
    databricks_auth_type: str | None
    databricks_metadata_service_url: str | None
    databricks_token: str | None
    databricks_warehouse_id: str | None
    databricks_catalog: str
    databricks_schema: str
    refresh_interval_seconds: int
    risk_refresh_interval_seconds: int
    ai_refresh_interval_seconds: int
    websocket_ping_interval_seconds: int
    gemini_api_key: str | None
    gemini_api_keys: str | None
    gemini_model: str
    gemini_enabled: bool
    # Seconds to cache successful Gemini responses (reduces quota use vs fast snapshot refresh).
    gemini_cache_ttl_seconds: int
    # After a 429 / RESOURCE_EXHAUSTED, skip API calls for this many seconds.
    gemini_rate_limit_cooldown_seconds: int
    openai_api_key: str | None
    openai_api_keys: str | None
    openai_model: str
    openai_enabled: bool
    deepseek_api_key: str | None
    deepseek_model: str
    groq_api_key: str | None
    groq_model: str
    anthropic_api_key: str | None
    anthropic_model: str
    openrouter_api_key: str | None
    tables: dict[str, str] = field(default_factory=dict)

    @property
    def get_gemini_keys_list(self) -> list[str]:
        keys = []
        if self.gemini_api_key:
            keys.append(self.gemini_api_key)
        if self.gemini_api_keys:
            keys.extend([k.strip() for k in self.gemini_api_keys.split(",") if k.strip()])
        # De-duplicate while preserving order
        return list(dict.fromkeys(keys))

    @property
    def get_openai_keys_list(self) -> list[str]:
        keys = []
        if self.openai_api_key:
            keys.append(self.openai_api_key)
        if self.openai_api_keys:
            keys.extend([k.strip() for k in self.openai_api_keys.split(",") if k.strip()])
        return list(dict.fromkeys(keys))

    @property
    def databricks_enabled(self) -> bool:
        return bool(
            self.databricks_host
            and (
                self.databricks_token
                or (
                    self.databricks_auth_type == "metadata-service"
                    and self.databricks_metadata_service_url
                )
            )
        )

    @property
    def ai_enabled(self) -> bool:
        return self.gemini_enabled

    def fq_table(self, key: str) -> str:
        table_name = self.tables[key]
        return f"{self.databricks_catalog}.{self.databricks_schema}.{table_name}"


def load_settings() -> Settings:
    backend_root = Path(__file__).resolve().parents[2]
    project_root = backend_root.parent
    env_values: dict[str, str] = {}
    env_values.update(_load_env_file(project_root / ".databricks" / ".databricks.env"))
    env_values.update(_load_env_file(backend_root / ".env"))
    env_values.update({key: value for key, value in os.environ.items() if value})

    # CRITICAL FIX: Ensure os.environ is updated so os.getenv() works in other services (like Twilio)
    os.environ.update(env_values)

    def env(key: str, default: Any = None) -> Any:
        return env_values.get(key, default)

    tables = {
        key: env(f"TABLE_{key.upper()}", default)
        for key, default in DEFAULT_TABLE_NAMES.items()
    }

    return Settings(
        project_root=project_root,
        host=str(env("BACKEND_HOST", "127.0.0.1")),
        port=int(env("BACKEND_PORT", "8000")),
        frontend_origin=str(env("FRONTEND_ORIGIN", "http://localhost:3000")),
        databricks_host=env("DATABRICKS_HOST"),
        databricks_auth_type=env("DATABRICKS_AUTH_TYPE"),
        databricks_metadata_service_url=env("DATABRICKS_METADATA_SERVICE_URL"),
        databricks_token=env("DATABRICKS_TOKEN"),
        databricks_warehouse_id=env("DATABRICKS_WAREHOUSE_ID"),
        # Unity Catalog: default to `main` (typical workspace catalog). Legacy Hive Metastore
        # (`hive_metastore`) is disabled on many accounts; set DATABRICKS_CATALOG explicitly if
        # your tables live elsewhere (e.g. a shared UC catalog or HMS federation).
        databricks_catalog=str(env("DATABRICKS_CATALOG", "main")),
        databricks_schema=str(env("DATABRICKS_SCHEMA", "default")),
        refresh_interval_seconds=int(env("REFRESH_INTERVAL_SECONDS", "5")),
        risk_refresh_interval_seconds=int(env("RISK_REFRESH_INTERVAL_SECONDS", "60")),
        ai_refresh_interval_seconds=int(env("AI_REFRESH_INTERVAL_SECONDS", "60")),
        websocket_ping_interval_seconds=int(env("WEBSOCKET_PING_INTERVAL_SECONDS", "15")),
        gemini_api_key=env("GEMINI_API_KEY"),
        gemini_api_keys=env("GEMINI_API_KEYS"),
        # Use a current Gemini API id (see https://ai.google.dev/gemini-api/docs/models)
        gemini_model=str(env("GEMINI_MODEL", "gemini-2.0-flash")),
        gemini_enabled=str(env("GEMINI_ENABLED", "true")).lower() != "false",
        gemini_cache_ttl_seconds=int(env("GEMINI_CACHE_TTL_SECONDS", "900")),
        gemini_rate_limit_cooldown_seconds=int(
            env("GEMINI_RATE_LIMIT_COOLDOWN_SECONDS", "300")
        ),
        openai_api_key=env("OPENAI_API_KEY"),
        openai_api_keys=env("OPENAI_API_KEYS"),
        openai_model=str(env("OPENAI_MODEL", "gpt-4.5-preview")),
        openai_enabled=str(env("OPENAI_ENABLED", "false")).lower() != "false",
        deepseek_api_key=env("DEEPSEEK_API_KEY"),
        deepseek_model=str(env("DEEPSEEK_MODEL", "deepseek-chat")),
        groq_api_key=env("GROQ_API_KEY"),
        groq_model=str(env("GROQ_MODEL", "llama3-70b-8192")),
        anthropic_api_key=env("ANTHROPIC_API_KEY"),
        anthropic_model=str(env("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")),
        openrouter_api_key=env("OPENROUTER_API_KEY"),
        tables=tables,
    )
