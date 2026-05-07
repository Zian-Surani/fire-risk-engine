from __future__ import annotations

"""Databricks repository layer.

All SQL queries against Gold / Silver tables are centralised here.
Each method returns raw row-dicts; no business logic lives here.
"""

import time
from typing import Any

from app.clients.databricks import DatabricksClient
from app.core.config import Settings


class FireRiskRepository:
    def __init__(self, client: DatabricksClient, settings: Settings) -> None:
        self._db = client
        self._cfg = settings

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------

    async def _query(self, sql: str) -> tuple[list[dict[str, Any]], float]:
        started = time.perf_counter()
        result = await self._db.fetch_rows(sql)
        return result.rows, result.duration_ms

    def _tbl(self, key: str) -> str:
        return self._cfg.fq_table(key)

    # ------------------------------------------------------------------
    # Silver
    # ------------------------------------------------------------------

    async def fetch_silver_risk_base(self, limit: int = 500) -> tuple[list[dict[str, Any]], float]:
        sql = f"""
        SELECT
            address,
            district,
            risk_score,
            risk_category,
            recency_score,
            violation_count,
            incident_count,
            avg_response_time_min,
            compliance_score,
            human_impact_score
        FROM {self._tbl('silver_fire_risk_base')}
        WHERE risk_score IS NOT NULL
        ORDER BY risk_score DESC
        LIMIT {limit}
        """
        return await self._query(sql)

    # ------------------------------------------------------------------
    # Gold
    # ------------------------------------------------------------------

    async def fetch_top_critical(self, limit: int = 100) -> tuple[list[dict[str, Any]], float]:
        sql = f"""
        SELECT *
        FROM {self._tbl('gold_top_100_critical_properties')}
        ORDER BY risk_score DESC
        LIMIT {limit}
        """
        return await self._query(sql)

    async def fetch_risk_heatmap(self, limit: int = 300) -> tuple[list[dict[str, Any]], float]:
        sql = f"""
        SELECT *
        FROM {self._tbl('gold_risk_heatmap_data')}
        LIMIT {limit}
        """
        return await self._query(sql)

    async def fetch_district_intelligence(self) -> tuple[list[dict[str, Any]], float]:
        sql = f"""
        SELECT *
        FROM {self._tbl('gold_district_intelligence')}
        """
        return await self._query(sql)

    async def fetch_response_optimization(self, limit: int = 50) -> tuple[list[dict[str, Any]], float]:
        sql = f"""
        SELECT *
        FROM {self._tbl('gold_response_optimization')}
        ORDER BY avg_response_time_min DESC
        LIMIT {limit}
        """
        return await self._query(sql)

    async def fetch_structured_recommendations(self, limit: int = 20) -> tuple[list[dict[str, Any]], float]:
        # Notebook schema uses string `priority` (CRITICAL/HIGH/MEDIUM/LOW), not `priority_score`.
        sql = f"""
        SELECT *
        FROM {self._tbl('gold_structured_recommendations')}
        ORDER BY
          CASE UPPER(COALESCE(priority, ''))
            WHEN 'CRITICAL' THEN 4
            WHEN 'HIGH' THEN 3
            WHEN 'MEDIUM' THEN 2
            WHEN 'LOW' THEN 1
            ELSE 0
          END DESC,
          created_date DESC NULLS LAST
        LIMIT {limit}
        """
        return await self._query(sql)

    async def fetch_executive_metrics(self) -> tuple[list[dict[str, Any]], float]:
        sql = f"""
        SELECT *
        FROM {self._tbl('gold_executive_metrics')}
        """
        return await self._query(sql)

    async def fetch_repeat_offenders(self, limit: int = 50) -> tuple[list[dict[str, Any]], float]:
        sql = f"""
        SELECT *
        FROM {self._tbl('gold_repeat_offenders')}
        ORDER BY enforcement_priority DESC
        LIMIT {limit}
        """
        return await self._query(sql)

    async def fetch_impact_simulation(self, limit: int = 20) -> tuple[list[dict[str, Any]], float]:
        sql = f"""
        SELECT *
        FROM {self._tbl('gold_impact_simulation')}
        LIMIT {limit}
        """
        return await self._query(sql)

    async def fetch_time_risk_analysis(self) -> tuple[list[dict[str, Any]], float]:
        sql = f"""
        SELECT *
        FROM {self._tbl('gold_time_risk_analysis')}
        """
        return await self._query(sql)

    async def fetch_action_playbook(self, limit: int = 10) -> tuple[list[dict[str, Any]], float]:
        sql = f"""
        SELECT *
        FROM {self._tbl('gold_action_playbook')}
        LIMIT {limit}
        """
        return await self._query(sql)
