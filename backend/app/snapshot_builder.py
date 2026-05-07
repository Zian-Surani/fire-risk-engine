from __future__ import annotations

"""Background refresh loop + page-snapshot builders.

Runs every `settings.refresh_interval_seconds` seconds, fetches the latest
Gold/Silver data from Databricks (or returns mock data if Databricks is
unavailable), builds per-page response envelopes, and stores them in the
in-memory SnapshotCache.

The refresh loop also calls the AI service for the decision brief and pushes
`snapshot_updated` events to all connected WebSocket clients.
"""

import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import Any

from app.clients.databricks import DatabricksClient
from app.clients.gemini_client import GeminiClient
from app.core.config import Settings
from app.core.runtime_metrics import collect_runtime_metrics
from app.core.snapshot_cache import SnapshotCache
from app.core.websocket_hub import WebSocketHub
from app.repositories import FireRiskRepository
from app.services.ai_service import AIService
from app.services.risk_intelligence import build_risk_dataset
from app.services.roadmap_service import RoadmapService
from app.services.utils import now_iso, to_float, to_int

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Databricks row normalization (Gold schemas → dashboard contract)
# ---------------------------------------------------------------------------


def normalize_executive_metrics_row(row: dict[str, Any]) -> dict[str, Any]:
    """Gold `gold_executive_metrics` uses numeric current_value; UI/report expect strings."""
    out = dict(row)
    cv = row.get("current_value")
    if cv is not None and not isinstance(cv, str):
        out["current_value"] = str(cv)
    if not out.get("status"):
        out["status"] = "stable"
    if not out.get("unit") and row.get("unit"):
        out["unit"] = str(row["unit"])
    return out


def normalize_simulation_row(row: dict[str, Any]) -> dict[str, Any]:
    """Map `gold_impact_simulation` columns to the shapes used by the dashboard + /api/simulations/run."""
    gold_shape = row.get("incident_reduction_pct") is not None or (
        "intervention_cost" in row and "projected_annual_incidents" in row
    )
    if not gold_shape:
        return dict(row)
    inc = to_float(row.get("incident_reduction_pct"), 0.0)
    priority = str(row.get("recommendation_priority") or "").upper()
    if "HIGHLY" in priority or priority == "RECOMMENDED":
        feasibility = "HIGH"
    elif "CONSIDER" in priority:
        feasibility = "MEDIUM"
    else:
        feasibility = "LOW"
    merged = dict(row)
    merged["scenario_name"] = str(row.get("scenario_name") or "Scenario")
    merged["risk_reduction_pct"] = inc
    merged["net_benefit"] = to_float(row.get("net_benefit"), 0.0)
    merged["feasibility"] = feasibility
    return merged


def pick_best_simulation_scenario(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    if not scenarios:
        return {}
    non_baseline = [s for s in scenarios if "BASELINE" not in str(s.get("scenario_name", "")).upper()]
    pool = non_baseline or scenarios
    return max(
        pool,
        key=lambda s: (to_float(s.get("risk_reduction_pct"), 0.0), to_float(s.get("net_benefit"), 0.0)),
    )


# ---------------------------------------------------------------------------
# Mock data helpers (used when Databricks is not configured / offline)
# ---------------------------------------------------------------------------

def _mock_silver_rows() -> list[dict[str, Any]]:
    districts = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"]
    rows: list[dict[str, Any]] = []
    for i in range(60):
        d = districts[i % len(districts)]
        rows.append({
            "address": f"{100 + i * 7} Market St, SF",
            "district": d,
            "risk_score": round(20 + (i * 1.1) % 78, 2),
            "risk_category": "HIGH" if i % 5 == 0 else ("MEDIUM" if i % 3 == 0 else "LOW"),
            "recency_score": round(30 + (i * 2.3) % 65, 2),
            "violation_count": i % 4,
            "incident_count": 2 + (i % 6),
            "avg_response_time_min": round(5 + (i * 0.7) % 14, 2),
            "compliance_score": round(60 + (i * 1.5) % 38, 2),
            "human_impact_score": round(10 + (i * 2.1) % 80, 2),
        })
    return rows


def _mock_executive_metrics() -> list[dict[str, Any]]:
    return [
        {"metric_name": "Total Properties", "current_value": "23,634", "unit": "", "status": "stable"},
        {"metric_name": "High Risk Zones", "current_value": "12", "unit": "zones", "status": "elevated"},
        {"metric_name": "Avg Response Time", "current_value": "9.4", "unit": "min", "status": "degraded"},
        {"metric_name": "Compliance Rate", "current_value": "82.3", "unit": "%", "status": "stable"},
        {"metric_name": "Active Violations", "current_value": "47", "unit": "", "status": "elevated"},
        {"metric_name": "AI Confidence", "current_value": "74.1", "unit": "%", "status": "stable"},
    ]


def _mock_recommendations() -> list[dict[str, Any]]:
    return [
        {
            "action_type": "DEPLOY",
            "priority": "CRITICAL",
            "description": "Shift rapid-response coverage to District 7 and schedule targeted inspection sweep.",
            "estimated_impact": "Reduces response time by ~3.2 min",
            "district": "7",
        },
        {
            "action_type": "INSPECT",
            "priority": "HIGH",
            "description": "Conduct compliance audit at top-10 repeat offender addresses.",
            "estimated_impact": "Mitigates 5 active violations",
            "district": "3",
        },
        {
            "action_type": "REROUTE",
            "priority": "MEDIUM",
            "description": "Reroute Tanker-09 from District 4 to District 9 redundancy zone.",
            "estimated_impact": "Frees 1 resource, improves coverage by 7%",
            "district": "9",
        },
    ]


def _mock_repeat_offenders() -> list[dict[str, Any]]:
    return [
        {"address": "2145 Mission St", "violation_count": 8, "enforcement_priority": 4, "enforcement_action": "Formal Notice"},
        {"address": "880 Pacific Ave", "violation_count": 6, "enforcement_priority": 3, "enforcement_action": "Inspection"},
        {"address": "1402 Fillmore St", "violation_count": 5, "enforcement_priority": 3, "enforcement_action": "Re-inspection"},
        {"address": "345 Polk St", "violation_count": 4, "enforcement_priority": 2, "enforcement_action": "Warning Issued"},
        {"address": "762 Haight St", "violation_count": 3, "enforcement_priority": 2, "enforcement_action": "Pending Review"},
    ]


def _mock_simulation_scenarios() -> list[dict[str, Any]]:
    return [
        {"scenario_name": "Accelerated Inspection", "risk_reduction_pct": 18.4, "net_benefit": 340000, "feasibility": "HIGH"},
        {"scenario_name": "Resource Reallocation", "risk_reduction_pct": 12.1, "net_benefit": 210000, "feasibility": "HIGH"},
        {"scenario_name": "Aerial Patrol Expansion", "risk_reduction_pct": 9.7, "net_benefit": 145000, "feasibility": "MEDIUM"},
    ]


def _mock_district_intelligence() -> list[dict[str, Any]]:
    return [
        {"district": str(i), "resource_gap_score": round(0.1 + (i * 0.08) % 0.9, 3), "avg_response_time_min": round(5 + i * 0.7, 2)}
        for i in range(1, 12)
    ]


def _mock_time_risk() -> list[dict[str, Any]]:
    return [
        {"hour_of_day": h, "avg_risk_score": round(30 + abs(h - 14) * 2.3, 2), "incident_count": max(1, 6 - abs(h - 14))}
        for h in range(0, 24, 3)
    ]


# ---------------------------------------------------------------------------
# Snapshot builders
# ---------------------------------------------------------------------------

def _envelope(
    data: Any,
    *,
    query_latency_ms: float,
    ai_latency_ms: float = 0.0,
    source_status: str,
    alerts: list[str],
    runtime: dict[str, float] | None = None,
    last_optimization: dict[str, Any] | None = None,
    last_simulation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now = datetime.now(UTC)
    env: dict[str, Any] = {
        "generated_at": now.isoformat(),
        "stale_after": (now.timestamp() + 30),
        "query_latency_ms": round(query_latency_ms, 2),
        "ai_latency_ms": round(ai_latency_ms, 2),
        "source_status": source_status,
        "data": data,
        "alerts": alerts,
    }
    if runtime is not None:
        env["runtime"] = runtime
    if last_optimization is not None:
        env["last_optimization"] = last_optimization
    if last_simulation is not None:
        env["last_simulation"] = last_simulation
    return env


def build_command_center_snapshot(
    *,
    risk_dataset: dict[str, Any],
    recommendations: list[dict[str, Any]],
    exec_metrics: list[dict[str, Any]],
    decision_brief: str,
    query_latency_ms: float,
    ai_latency_ms: float,
    source_status: str,
    alerts: list[str],
    runtime: dict[str, float] | None = None,
    last_optimization: dict[str, Any] | None = None,
    last_simulation: dict[str, Any] | None = None,
    markers: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    top = risk_dataset.get("top_markers", [])[:6]
    districts: dict[str, dict[str, Any]] = {}
    for marker in risk_dataset.get("markers", []):
        d = str(marker.get("district", ""))
        if d and d not in districts:
            districts[d] = {
                "district": d,
                "display_district": marker.get("display_district", f"District {d}"),
                "adjusted_risk_score": round(marker.get("adjusted_risk_score", 0.0), 2),
                "adjusted_risk_band": marker.get("adjusted_risk_band", "LOW"),
                "marker_color": marker.get("marker_color", "#71d7cd"),
                "latitude": marker.get("latitude"),
                "longitude": marker.get("longitude"),
            }

    ai_confidence = round(
        62 + len(risk_dataset.get("top_markers", [])) * 0.8,
        1,
    )

    metric_map = {m.get("metric_name", ""): m for m in exec_metrics}
    avg_response_raw = to_float(metric_map.get("Avg Response Time", {}).get("current_value"))
    response_latency_status = "DEGRADED" if avg_response_raw > 10 else "NOMINAL"

    return _envelope(
        {
            "global_risk_index": risk_dataset.get("global_risk_index", 0.0),
            "high_risk_zones": risk_dataset.get("high_risk_zones", 0),
            "average_adjusted_risk": risk_dataset.get("average_adjusted_risk", 0.0),
            "markers": top,
            "districts": list(districts.values())[:12],
            "recommendations": recommendations[:3],
            "executive_metrics": exec_metrics[:6],
            "decision_brief": decision_brief,
            "ai_confidence": ai_confidence,
            "response_latency_status": response_latency_status,
            "avg_response_time_min": avg_response_raw or 9.4,
            "markers": markers or top,
        },
        query_latency_ms=query_latency_ms,
        ai_latency_ms=ai_latency_ms,
        source_status=source_status,
        alerts=alerts,
        runtime=runtime,
        last_optimization=last_optimization,
        last_simulation=last_simulation,
    )


def build_operations_snapshot(
    *,
    district_rows: list[dict[str, Any]],
    response_rows: list[dict[str, Any]],
    recommendations: list[dict[str, Any]],
    runtime_cpu: float,
    runtime_mem: float,
    runtime_mem_mb: float,
    query_latency_ms: float,
    source_status: str,
    alerts: list[str],
    last_optimization: dict[str, Any] | None = None,
    last_simulation: dict[str, Any] | None = None,
    markers: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    api_latency = round(query_latency_ms, 2)
    avg_resp = round(
        sum(to_float(r.get("avg_response_time_min")) for r in response_rows) / max(len(response_rows), 1),
        2,
    )
    # Resource load
    total_units = 32
    active_units = min(total_units, max(1, int(total_units * (1 - runtime_cpu / 200))))
    ground_pct = round(active_units / total_units * 100, 1)

    dispatch_items = [
        {
            "title": rec.get("description", "Deploy unit to high-risk zone"),
            "subtitle": rec.get("estimated_impact", ""),
            "priority": rec.get("priority", "MEDIUM"),
            "district": rec.get("district", ""),
            "action_type": rec.get("action_type", "DEPLOY"),
        }
        for rec in recommendations[:3]
    ]

    runtime_payload = {
        "cpu_percent": runtime_cpu,
        "memory_percent": runtime_mem,
        "memory_used_mb": runtime_mem_mb,
    }
    return _envelope(
        {
            "ground_units_active": active_units,
            "ground_units_total": total_units,
            "ground_units_pct": ground_pct,
            "aerial_active": 4,
            "aerial_total": 6,
            "aerial_pct": round(4 / 6 * 100, 1),
            "personnel_active": 12,
            "personnel_total": 12,
            "personnel_pct": 100.0,
            "avg_response_time_min": avg_resp,
            "api_latency_ms": api_latency,
            "cpu_percent": runtime_cpu,
            "memory_percent": runtime_mem,
            "memory_mb": runtime_mem_mb,
            "system_health_pct": round(100 - runtime_cpu * 0.5, 1),
            "dispatch_items": dispatch_items,
            "district_intelligence": district_rows[:6],
            "bottlenecks": [
                {"label": "Hwy 101 Congestion", "detail": "+12m delay for North Sector units."},
            ] if avg_resp > 10 else [],
            "refresh_healthy": source_status == "live",
            "markers": markers or [],
        },
        query_latency_ms=query_latency_ms,
        source_status=source_status,
        alerts=alerts,
        runtime=runtime_payload,
        last_optimization=last_optimization,
        last_simulation=last_simulation,
    )


def build_simulation_snapshot(
    *,
    scenarios: list[dict[str, Any]],
    time_risk: list[dict[str, Any]],
    repeat_offenders: list[dict[str, Any]],
    sentinel_brief: str,
    query_latency_ms: float,
    ai_latency_ms: float,
    source_status: str,
    alerts: list[str],
    iteration_current: int | None = None,
    iteration_total: int | None = None,
    runtime: dict[str, float] | None = None,
    last_optimization: dict[str, Any] | None = None,
    last_simulation: dict[str, Any] | None = None,
    markers: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    best = pick_best_simulation_scenario(scenarios)
    risk_reduction = to_float(best.get("risk_reduction_pct"), -18.4)
    net_benefit = to_float(best.get("net_benefit"), 340000)

    spread_bars = [
        {"label": f"H{r.get('hour_of_day', 0)}", "value": round(to_float(r.get("avg_risk_score", 50)) / 100, 3)}
        for r in time_risk[:6]
    ] if time_risk else [
        {"label": "00h", "value": 0.4},
        {"label": "04h", "value": 0.6},
        {"label": "08h", "value": 0.3},
        {"label": "12h", "value": 0.8},
        {"label": "16h", "value": 0.95},
        {"label": "20h", "value": 0.5},
    ]

    # Efficiency ring (% of scenarios meeting HIGH feasibility)
    high_feasibility = sum(1 for s in scenarios if str(s.get("feasibility", "")) == "HIGH")
    efficiency_pct = round(high_feasibility / max(len(scenarios), 1) * 100, 1) if scenarios else 72.0

    iter_total = iteration_total if iteration_total is not None else 5000
    iter_cur = iteration_current if iteration_current is not None else 1402
    return _envelope(
        {
            "scenarios": scenarios[:5],
            "best_scenario": best,
            "risk_reduction_pct": risk_reduction,
            "net_benefit": net_benefit,
            "spread_bars": spread_bars,
            "efficiency_pct": efficiency_pct,
            "time_risk": time_risk[:8],
            "repeat_offenders": repeat_offenders[:5],
            "sentinel_brief": sentinel_brief,
            "iteration_current": iter_cur,
            "iteration_total": iter_total,
            "markers": markers or [],
        },
        query_latency_ms=query_latency_ms,
        ai_latency_ms=ai_latency_ms,
        source_status=source_status,
        alerts=alerts,
        runtime=runtime,
        last_optimization=last_optimization,
        last_simulation=last_simulation,
    )


def build_compliance_snapshot(
    *,
    repeat_offenders: list[dict[str, Any]],
    exec_metrics: list[dict[str, Any]],
    query_latency_ms: float,
    source_status: str,
    alerts: list[str],
    runtime: dict[str, float] | None = None,
    last_optimization: dict[str, Any] | None = None,
    last_simulation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metric_map = {m.get("metric_name", ""): m for m in exec_metrics}
    active_violations = to_int(str(metric_map.get("Active Violations", {}).get("current_value", "0")).replace(",", ""))
    compliance_rate = to_float(str(metric_map.get("Compliance Rate", {}).get("current_value", "82.3")).replace(",", ""))

    kpis = [
        {"label": "Compliance Rate", "value": f"{compliance_rate:.1f}%", "status": "stable" if compliance_rate > 80 else "elevated"},
        {"label": "Active Violations", "value": str(active_violations), "status": "elevated" if active_violations > 20 else "stable"},
        {"label": "Repeat Offenders", "value": str(len(repeat_offenders)), "status": "elevated" if len(repeat_offenders) > 3 else "stable"},
        {"label": "Audits This Quarter", "value": "6", "status": "stable"},
    ]

    return _envelope(
        {
            "repeat_offenders": repeat_offenders[:10],
            "executive_metrics": exec_metrics[:6],
            "kpis": kpis,
            "policy_violations_30d": active_violations,
            "compliance_rate": compliance_rate,
            "frameworks": [
                {"name": "ISO 31000 Standard", "status": "compliant"},
                {"name": "OSHA Sect. 5(a)", "status": "compliant"},
                {"name": "NFPA 1 Fire Code", "status": "compliant"},
            ],
        },
        query_latency_ms=query_latency_ms,
        source_status=source_status,
        alerts=alerts,
        runtime=runtime,
        last_optimization=last_optimization,
        last_simulation=last_simulation,
    )


# ---------------------------------------------------------------------------
# Main refresh orchestrator
# ---------------------------------------------------------------------------

class RefreshOrchestrator:
    def __init__(
        self,
        *,
        settings: Settings,
        db_client: DatabricksClient,
        ai_client: GeminiClient,
        cache: SnapshotCache,
        hub: WebSocketHub,
    ) -> None:
        self._settings = settings
        self._repo = FireRiskRepository(db_client, settings)
        self._ai = AIService(ai_client)
        self._cache = cache
        self._hub = hub
        self._roadmap = RoadmapService()
        self._db_available: bool = False
        self._startup_checked = False
        self._roadmap_seeded = False

    async def startup_check(self) -> None:
        """Detect Databricks connectivity once at startup."""
        if self._startup_checked:
            return
        if self._settings.databricks_enabled:
            from app.clients.databricks import DatabricksClient  # noqa: F401
            try:
                self._db_available = await self._repo._db.is_available()
            except Exception:
                self._db_available = False
        self._startup_checked = True
        logger.info("Databricks available: %s", self._db_available)

    async def _seed_roadmap_snapshot(self) -> None:
        if self._roadmap_seeded:
            return
        await self._cache.set_snapshot("roadmap", _envelope(
            self._roadmap.build_snapshot(),
            query_latency_ms=0.0,
            source_status="static",
            alerts=[],
        ))
        self._roadmap_seeded = True

    async def ensure_ready(self) -> None:
        await self.startup_check()
        await self._seed_roadmap_snapshot()

    async def warm_start(self) -> bool:
        """Prime cache before the app starts serving requests."""
        await self.ensure_ready()
        await self._refresh_once()
        command_center_snapshot = await self._cache.get_snapshot("command-center")
        return command_center_snapshot is not None

    async def run_refresh_loop(self, *, skip_initial_refresh: bool = False) -> None:
        """Background task: refresh loop."""
        await self.ensure_ready()
        if skip_initial_refresh:
            await asyncio.sleep(self._settings.refresh_interval_seconds)
        while True:
            try:
                await self._refresh_once()
            except Exception as exc:
                logger.exception("Refresh loop error: %s", exc)
            await asyncio.sleep(self._settings.refresh_interval_seconds)

    async def _refresh_once(self) -> None:
        await self.ensure_ready()
        await self._cache.mark_refresh_started()
        t0 = time.perf_counter()
        alerts: list[str] = []
        source_status = "live" if self._db_available else "mock"

        try:
            if self._db_available:
                (
                    (silver_rows, q1),
                    (recs_rows, q2),
                    (exec_rows, q3),
                    (district_rows, q4),
                    (response_rows, q5),
                    (offenders_rows, q6),
                    (sim_rows, q7),
                    (time_risk_rows, q8),
                ) = await asyncio.gather(
                    self._repo.fetch_silver_risk_base(),
                    self._repo.fetch_structured_recommendations(),
                    self._repo.fetch_executive_metrics(),
                    self._repo.fetch_district_intelligence(),
                    self._repo.fetch_response_optimization(),
                    self._repo.fetch_repeat_offenders(),
                    self._repo.fetch_impact_simulation(),
                    self._repo.fetch_time_risk_analysis(),
                )
                query_latency = (q1 + q2 + q3 + q4 + q5 + q6 + q7 + q8) / 8
                exec_rows = [normalize_executive_metrics_row(r) for r in exec_rows]
                sim_rows = [normalize_simulation_row(r) for r in sim_rows]
            else:
                silver_rows = _mock_silver_rows()
                recs_rows = _mock_recommendations()
                exec_rows = _mock_executive_metrics()
                district_rows = _mock_district_intelligence()
                response_rows = []
                offenders_rows = _mock_repeat_offenders()
                sim_rows = _mock_simulation_scenarios()
                time_risk_rows = _mock_time_risk()
                query_latency = 0.0

            # Build enriched risk dataset
            risk_dataset = build_risk_dataset(silver_rows)

            if risk_dataset.get("high_risk_zones", 0) > 8:
                alerts.append(f"High risk zone count elevated: {risk_dataset['high_risk_zones']} zones")

            # AI decision brief (throttled via cache in GeminiClient)
            ai_t0 = time.perf_counter()
            top_marker = (risk_dataset.get("top_markers") or [None])[0]
            best_scenario = sim_rows[0] if sim_rows else None
            decision_brief = await self._ai.build_decision_brief(
                top_marker=top_marker,
                best_scenario=best_scenario,
            )
            sentinel_brief = decision_brief
            ai_latency = (time.perf_counter() - ai_t0) * 1000

            runtime = collect_runtime_metrics()
            runtime_payload = {
                "cpu_percent": runtime.cpu_percent,
                "memory_percent": runtime.memory_percent,
                "memory_used_mb": runtime.memory_used_mb,
            }
            last_opt = await self._cache.get_runtime_artifact("optimization")
            last_sim = await self._cache.get_runtime_artifact("simulation")

            # Build snapshots
            cc = build_command_center_snapshot(
                risk_dataset=risk_dataset,
                recommendations=recs_rows,
                exec_metrics=exec_rows,
                decision_brief=decision_brief,
                query_latency_ms=query_latency,
                ai_latency_ms=ai_latency,
                source_status=source_status,
                alerts=alerts,
                runtime=runtime_payload,
                last_optimization=last_opt,
                last_simulation=last_sim,
                markers=risk_dataset.get("markers", []),
            )
            ops = build_operations_snapshot(
                district_rows=district_rows,
                response_rows=response_rows,
                recommendations=recs_rows,
                runtime_cpu=runtime.cpu_percent,
                runtime_mem=runtime.memory_percent,
                runtime_mem_mb=runtime.memory_used_mb,
                query_latency_ms=query_latency,
                source_status=source_status,
                alerts=alerts,
                last_optimization=last_opt,
                last_simulation=last_sim,
                markers=risk_dataset.get("markers", []),
            )
            sim = build_simulation_snapshot(
                scenarios=sim_rows,
                time_risk=time_risk_rows,
                repeat_offenders=offenders_rows,
                sentinel_brief=sentinel_brief,
                query_latency_ms=query_latency,
                ai_latency_ms=ai_latency,
                source_status=source_status,
                alerts=alerts,
                runtime=runtime_payload,
                last_optimization=last_opt,
                last_simulation=last_sim,
                markers=risk_dataset.get("markers", []),
            )
            comp = build_compliance_snapshot(
                repeat_offenders=offenders_rows,
                exec_metrics=exec_rows,
                query_latency_ms=query_latency,
                source_status=source_status,
                alerts=alerts,
                runtime=runtime_payload,
                last_optimization=last_opt,
                last_simulation=last_sim,
            )

            for name, snap in [
                ("command-center", cc),
                ("operations", ops),
                ("simulation", sim),
                ("compliance", comp),
            ]:
                await self._cache.set_snapshot(name, snap)

            total_latency = (time.perf_counter() - t0) * 1000
            await self._cache.mark_refresh_completed(
                success=True,
                source_status=source_status,
                query_latency_ms=query_latency,
                ai_latency_ms=ai_latency,
                alerts=alerts,
            )

            await self._hub.broadcast({
                "type": "snapshot_updated",
                "pages": ["command-center", "operations", "simulation", "compliance"],
                "source_status": source_status,
                "query_latency_ms": round(query_latency, 2),
                "ai_latency_ms": round(ai_latency, 2),
                "total_latency_ms": round(total_latency, 2),
                "generated_at": now_iso(),
                "alerts": alerts,
            })

            await self._hub.broadcast({
                "type": "system_metrics",
                "cpu_percent": runtime.cpu_percent,
                "memory_percent": runtime.memory_percent,
                "memory_mb": runtime.memory_used_mb,
                "generated_at": now_iso(),
            })

        except Exception as exc:
            logger.exception("Snapshot refresh failed: %s", exc)
            err_text = str(exc)
            if "UC_HIVE_METASTORE_DISABLED" in err_text or "Hive Metastore" in err_text:
                logger.warning(
                    "Databricks rejected hive_metastore / legacy HMS. Set DATABRICKS_CATALOG and "
                    "DATABRICKS_SCHEMA to your Unity Catalog location (often main.<schema>)."
                )
            alerts.append(f"Refresh error: {exc}")
            await self._cache.mark_refresh_completed(
                success=False,
                source_status="error",
                query_latency_ms=0.0,
                ai_latency_ms=0.0,
                alerts=alerts,
            )
            await self._hub.broadcast({
                "type": "pipeline_alert",
                "message": str(exc),
                "generated_at": now_iso(),
            })
