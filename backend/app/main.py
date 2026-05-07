from __future__ import annotations

"""FastAPI application entry-point.

REST routes:
  GET  /api/health
  GET  /api/dashboard/command-center
  GET  /api/dashboard/operations
  GET  /api/dashboard/simulation
  GET  /api/dashboard/compliance
  GET  /api/dashboard/roadmap
  POST /api/optimize
  POST /api/simulations/run
  GET  /api/reports/compliance?format=pdf|csv

WebSocket:
  GET  /ws/live
"""

import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from typing import Any

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.clients.databricks import DatabricksClient
from app.clients.universal_ai_client import UniversalAIClient
from app.core.config import load_settings
from app.core.runtime_metrics import collect_runtime_metrics
from app.core.snapshot_cache import SnapshotCache
from app.core.websocket_hub import WebSocketHub
from app.services.optimization_service import OptimizationService
from app.services.report_service import ReportService
from app.services.utils import now_iso
from app.snapshot_builder import (
    RefreshOrchestrator,
    _mock_recommendations,
    _mock_repeat_offenders,
    _mock_silver_rows,
    _mock_simulation_scenarios,
    build_simulation_snapshot,
)
from app.services.risk_intelligence import build_risk_dataset
from app.services.chat_service import ChatService
from app.api.chat import router as chat_router
from app.services.sos_service import sos_service

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application state (shared singleton objects)
# ---------------------------------------------------------------------------

settings = load_settings()
db_client = DatabricksClient(settings)
ai_client = UniversalAIClient(settings)
cache = SnapshotCache()
hub = WebSocketHub()
orchestrator = RefreshOrchestrator(
    settings=settings,
    db_client=db_client,
    ai_client=ai_client,
    cache=cache,
    hub=hub,
)
optimize_svc = OptimizationService()
report_svc = ReportService()
chat_svc = ChatService(ai_client, cache)

_refresh_task: asyncio.Task[None] | None = None


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    global _refresh_task
    warmed = await orchestrator.warm_start()
    _refresh_task = asyncio.create_task(
        orchestrator.run_refresh_loop(skip_initial_refresh=warmed)
    )
    yield
    if _refresh_task and not _refresh_task.done():
        _refresh_task.cancel()
        with suppress(asyncio.CancelledError):
            await _refresh_task
    await db_client.close()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="Fire Risk Backend", version="1.0.0", lifespan=lifespan)
app.state.chat_service = chat_svc
app.include_router(chat_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_or_404(name: str) -> dict[str, Any]:
    snap = await cache.get_snapshot(name)
    if snap is None:
        raise HTTPException(
            status_code=503,
            detail=f"Snapshot '{name}' is not ready yet; retry in a few seconds.",
        )
    return snap


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health() -> dict[str, Any]:
    meta = await cache.meta()
    runtime = collect_runtime_metrics()
    ws_connections = await hub.size()
    return {
        "status": "ok",
        "generated_at": now_iso(),
        "databricks_enabled": settings.databricks_enabled,
        "gemini_enabled": settings.gemini_enabled,
        "source_status": meta.get("source_status", "initializing"),
        "last_refresh_completed_at": meta.get("last_refresh_completed_at"),
        "last_refresh_success": meta.get("last_refresh_success", False),
        "query_latency_ms": meta.get("query_latency_ms", 0.0),
        "ai_latency_ms": meta.get("ai_latency_ms", 0.0),
        "ws_connections": ws_connections,
        "cpu_percent": runtime.cpu_percent,
        "memory_percent": runtime.memory_percent,
    }


# ---------------------------------------------------------------------------
# Dashboard pages
# ---------------------------------------------------------------------------

@app.get("/api/dashboard/command-center")
async def dashboard_command_center() -> dict[str, Any]:
    return await _get_or_404("command-center")


@app.get("/api/dashboard/operations")
async def dashboard_operations() -> dict[str, Any]:
    return await _get_or_404("operations")


@app.get("/api/dashboard/simulation")
async def dashboard_simulation() -> dict[str, Any]:
    return await _get_or_404("simulation")


@app.get("/api/dashboard/compliance")
async def dashboard_compliance() -> dict[str, Any]:
    return await _get_or_404("compliance")


@app.get("/api/dashboard/roadmap")
async def dashboard_roadmap() -> dict[str, Any]:
    return await _get_or_404("roadmap")


# ---------------------------------------------------------------------------
# Optimize action
# ---------------------------------------------------------------------------

@app.post("/api/optimize")
async def run_optimize(body: dict[str, Any] | None = None) -> dict[str, Any]:
    body = body or {}
    budget_cap = float(body.get("budget_cap", 1_500_000.0))
    max_districts = int(body.get("max_districts", 3))

    await hub.broadcast({"type": "optimization_started", "generated_at": now_iso()})

    # Fetch latest marker data from cache
    cc_snap = await cache.get_snapshot("command-center")
    if cc_snap:
        risk_markers = cc_snap["data"].get("markers", [])
    else:
        risk_dataset = build_risk_dataset(_mock_silver_rows())
        risk_markers = risk_dataset.get("markers", [])

    ops_snap = await cache.get_snapshot("operations")
    district_rows = ops_snap["data"].get("district_intelligence", []) if ops_snap else []
    response_rows = []  # will be empty if not available
    recommendation_rows = _mock_recommendations()

    result = optimize_svc.run(
        risk_markers=risk_markers,
        district_rows=district_rows,
        response_rows=response_rows,
        recommendation_rows=recommendation_rows,
        budget_cap=budget_cap,
        max_districts=max_districts,
    )

    await cache.set_runtime_artifact("optimization", result)

    await hub.broadcast({
        "type": "optimization_completed",
        "result": result,
        "generated_at": now_iso(),
    })
    return {"success": True, "result": result, "generated_at": now_iso()}


# ---------------------------------------------------------------------------
# Simulation run
# ---------------------------------------------------------------------------

@app.post("/api/simulations/run")
async def run_simulation(body: dict[str, Any] | None = None) -> dict[str, Any]:
    body = body or {}
    grid_units = max(1, min(20, int(body.get("grid_units", 14))))
    iteration_total = 5000
    iteration_current = min(iteration_total - 1, max(1, int(iteration_total * (grid_units / 20))))

    sim_snap = await cache.get_snapshot("simulation")
    if sim_snap:
        scenarios = sim_snap["data"].get("scenarios", [])
        time_risk = sim_snap["data"].get("time_risk", [])
        repeat_offenders = sim_snap["data"].get("repeat_offenders", [])
        sentinel_brief = sim_snap["data"].get("sentinel_brief", "")
        query_latency_ms = sim_snap.get("query_latency_ms", 0.0)
        ai_latency_ms = sim_snap.get("ai_latency_ms", 0.0)
        source_status = sim_snap.get("source_status", "mock")
        alerts: list[str] = sim_snap.get("alerts", [])
    else:
        scenarios = _mock_simulation_scenarios()
        time_risk = []
        repeat_offenders = _mock_repeat_offenders()
        sentinel_brief = "No Databricks data available; using mock scenario."
        query_latency_ms = 0.0
        ai_latency_ms = 0.0
        source_status = "mock"
        alerts = []

    last_opt = await cache.get_runtime_artifact("optimization")
    rt = collect_runtime_metrics()
    runtime_payload = {
        "cpu_percent": rt.cpu_percent,
        "memory_percent": rt.memory_percent,
        "memory_used_mb": rt.memory_used_mb,
    }

    result = build_simulation_snapshot(
        scenarios=scenarios,
        time_risk=time_risk,
        repeat_offenders=repeat_offenders,
        sentinel_brief=sentinel_brief,
        query_latency_ms=query_latency_ms,
        ai_latency_ms=ai_latency_ms,
        source_status=source_status,
        alerts=alerts,
        iteration_current=iteration_current,
        iteration_total=iteration_total,
        runtime=runtime_payload,
        last_optimization=last_opt,
        last_simulation=None,
    )

    await cache.set_runtime_artifact("simulation", result)
    await hub.broadcast({"type": "simulation_completed", "result": result, "generated_at": now_iso()})
    return {"success": True, "result": result, "generated_at": now_iso()}


# ---------------------------------------------------------------------------
# SOS Emergency
# ---------------------------------------------------------------------------

@app.post("/api/sos")
async def trigger_sos(body: dict[str, Any] | None = None) -> dict[str, Any]:
    body = body or {}
    user_id = body.get("user_id", "Tactical Admin")
    
    # Trigger Twilio SMS
    result = await sos_service.send_emergency_alert(user_id=user_id)
    
    if result.get("success"):
        # Broadcast to all connected clients via WS
        await hub.broadcast({
            "type": "pipeline_alert",
            "priority": "CRITICAL",
            "message": f"SOS SIGNAL DISPATCHED BY {user_id.upper()}",
            "generated_at": now_iso()
        })
    
    return result


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

@app.get("/api/reports/compliance")
async def compliance_report(format: str = Query("csv", pattern="^(csv|pdf)$")) -> Response:
    comp_snap = await cache.get_snapshot("compliance")
    if comp_snap:
        metrics = comp_snap["data"].get("executive_metrics", [])
        offenders = comp_snap["data"].get("repeat_offenders", [])
    else:
        metrics = []
        offenders = _mock_repeat_offenders()

    if format == "pdf":
        # Generate AI executive narrative for the dossier
        ai_narrative: str | None = None
        if metrics:
            critical_count = sum(1 for m in metrics if str(m.get("status", "")).upper() == "CRITICAL")
            warning_count  = sum(1 for m in metrics if str(m.get("status", "")).upper() == "WARNING")
            nominal_count  = sum(1 for m in metrics if str(m.get("status", "")).upper() == "NOMINAL")
            metric_summary = "; ".join(
                f"{m.get('metric_name', 'Unknown')}: {m.get('current_value', 'N/A')} {m.get('unit', '')} ({m.get('status', 'N/A')})"
                for m in metrics[:8]
            )
            offender_summary = "; ".join(
                o.get("address", "N/A") for o in offenders[:4]
            ) if offenders else "None on record"

            narrative_prompt = (
                "You are Sentinel Core, the tactical AI analyst for the FIRE Risk Intelligence Platform. "
                "Write a professional 3-4 paragraph 'Executive Interpretation' for a classified compliance dossier. "
                "Use formal, authoritative language. Include inferred insights and forward-looking risk assessments. "
                "Do NOT list raw numbers mechanically — synthesise them into strategic observations.\n\n"
                f"Current System Status: {critical_count} CRITICAL, {warning_count} WARNING, {nominal_count} NOMINAL metrics.\n"
                f"Key Metrics: {metric_summary}\n"
                f"Priority Incident Locations: {offender_summary}\n\n"
                "Write the interpretation now:"
            )
            ai_narrative = await ai_client.generate(
                cache_key=f"report_narrative_{now_iso()[:13]}",  # hourly cache key
                prompt=narrative_prompt,
                ttl_seconds=3600,
            )

        content = report_svc.build_pdf(metrics=metrics, repeat_offenders=offenders, ai_narrative=ai_narrative)
        await hub.broadcast({"type": "report_ready", "format": "pdf", "generated_at": now_iso()})
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=fire_risk_compliance.pdf"},
        )

    content_bytes = report_svc.build_csv(metrics=metrics, repeat_offenders=offenders)
    await hub.broadcast({"type": "report_ready", "format": "csv", "generated_at": now_iso()})
    return Response(
        content=content_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=fire_risk_compliance.csv"},
    )


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

@app.websocket("/ws/live")
async def ws_live(websocket: WebSocket) -> None:
    await hub.connect(websocket)
    try:
        meta = await cache.meta()
        await websocket.send_json({
            "type": "connected",
            "source_status": meta.get("source_status", "initializing"),
            "generated_at": now_iso(),
        })
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=float(settings.websocket_ping_interval_seconds))
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping", "generated_at": now_iso()})
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        await hub.disconnect(websocket)


# ---------------------------------------------------------------------------
# Dev runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
