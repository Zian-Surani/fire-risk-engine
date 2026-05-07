"""Tests for snapshot builder functions."""

from __future__ import annotations

from app.snapshot_builder import (
    _mock_executive_metrics,
    _mock_recommendations,
    _mock_repeat_offenders,
    _mock_silver_rows,
    _mock_simulation_scenarios,
    build_command_center_snapshot,
    build_compliance_snapshot,
    build_operations_snapshot,
    build_simulation_snapshot,
    normalize_executive_metrics_row,
    normalize_simulation_row,
    pick_best_simulation_scenario,
)
from app.services.risk_intelligence import build_risk_dataset


class TestMockData:
    def test_mock_silver_rows_count(self):
        rows = _mock_silver_rows()
        assert len(rows) == 60

    def test_mock_silver_rows_have_required_fields(self):
        required = {"address", "district", "risk_score", "compliance_score"}
        for row in _mock_silver_rows():
            assert required.issubset(set(row.keys()))

    def test_mock_executive_metrics(self):
        metrics = _mock_executive_metrics()
        assert len(metrics) >= 4
        names = [m["metric_name"] for m in metrics]
        assert "Total Properties" in names

    def test_mock_recommendations(self):
        recs = _mock_recommendations()
        assert len(recs) == 3
        for rec in recs:
            assert "description" in rec
            assert "action_type" in rec

    def test_mock_repeat_offenders(self):
        offenders = _mock_repeat_offenders()
        assert len(offenders) >= 3
        for o in offenders:
            assert "address" in o
            assert "enforcement_priority" in o

    def test_mock_simulation_scenarios(self):
        scenarios = _mock_simulation_scenarios()
        assert len(scenarios) >= 2
        for s in scenarios:
            assert "scenario_name" in s
            assert "risk_reduction_pct" in s


class TestCommandCenterSnapshot:
    def _build(self, **kwargs):
        defaults = dict(
            risk_dataset=build_risk_dataset(_mock_silver_rows()),
            recommendations=_mock_recommendations(),
            exec_metrics=_mock_executive_metrics(),
            decision_brief="Test brief.",
            query_latency_ms=120.0,
            ai_latency_ms=50.0,
            source_status="mock",
            alerts=[],
        )
        defaults.update(kwargs)
        return build_command_center_snapshot(**defaults)

    def test_envelope_keys(self):
        snap = self._build()
        assert "generated_at" in snap
        assert "data" in snap
        assert "source_status" in snap
        assert "alerts" in snap

    def test_data_has_required_fields(self):
        snap = self._build()
        d = snap["data"]
        assert "global_risk_index" in d
        assert "high_risk_zones" in d
        assert "markers" in d
        assert "districts" in d
        assert "recommendations" in d
        assert "executive_metrics" in d
        assert "decision_brief" in d
        assert "ai_confidence" in d

    def test_decision_brief_propagated(self):
        snap = self._build(decision_brief="My special brief.")
        assert snap["data"]["decision_brief"] == "My special brief."

    def test_source_status_propagated(self):
        snap = self._build(source_status="live")
        assert snap["source_status"] == "live"

    def test_alerts_propagated(self):
        snap = self._build(alerts=["Alert A", "Alert B"])
        assert "Alert A" in snap["alerts"]

    def test_ai_confidence_in_range(self):
        snap = self._build()
        conf = snap["data"]["ai_confidence"]
        assert 0 <= conf <= 100

    def test_runtime_echoed_on_envelope_when_provided(self):
        snap = self._build()
        snap2 = build_command_center_snapshot(
            risk_dataset=build_risk_dataset(_mock_silver_rows()),
            recommendations=_mock_recommendations(),
            exec_metrics=_mock_executive_metrics(),
            decision_brief="x",
            query_latency_ms=1.0,
            ai_latency_ms=0.0,
            source_status="mock",
            alerts=[],
            runtime={"cpu_percent": 12.0, "memory_percent": 40.0, "memory_used_mb": 256.0},
            last_optimization={"request_id": "opt-1"},
        )
        assert snap2.get("runtime", {}).get("cpu_percent") == 12.0
        assert snap2.get("last_optimization", {}).get("request_id") == "opt-1"
        assert "runtime" not in snap


class TestOperationsSnapshot:
    def _build(self, **kwargs):
        defaults = dict(
            district_rows=[{"district": "1", "resource_gap_score": 0.3, "avg_response_time_min": 8.0}],
            response_rows=[{"avg_response_time_min": 9.0}],
            recommendations=_mock_recommendations(),
            runtime_cpu=22.5,
            runtime_mem=45.0,
            runtime_mem_mb=512.0,
            query_latency_ms=100.0,
            source_status="mock",
            alerts=[],
        )
        defaults.update(kwargs)
        return build_operations_snapshot(**defaults)

    def test_envelope_structure(self):
        snap = self._build()
        assert "data" in snap
        assert "generated_at" in snap

    def test_data_fields(self):
        d = self._build()["data"]
        assert "ground_units_active" in d
        assert "system_health_pct" in d
        assert "avg_response_time_min" in d
        assert "dispatch_items" in d
        assert "refresh_healthy" in d

    def test_refresh_healthy_when_live(self):
        d = self._build(source_status="live")["data"]
        assert d["refresh_healthy"] is True

    def test_refresh_not_healthy_when_mock(self):
        d = self._build(source_status="mock")["data"]
        assert d["refresh_healthy"] is False

    def test_system_health_bounded(self):
        d = self._build(runtime_cpu=0.0)["data"]
        assert 0 <= d["system_health_pct"] <= 100


class TestSimulationSnapshot:
    def _build(self, **kwargs):
        defaults = dict(
            scenarios=_mock_simulation_scenarios(),
            time_risk=[],
            repeat_offenders=_mock_repeat_offenders(),
            sentinel_brief="Test sentinel.",
            query_latency_ms=80.0,
            ai_latency_ms=40.0,
            source_status="mock",
            alerts=[],
            iteration_current=None,
            iteration_total=None,
        )
        defaults.update(kwargs)
        return build_simulation_snapshot(**defaults)

    def test_data_fields(self):
        d = self._build()["data"]
        assert "scenarios" in d
        assert "best_scenario" in d
        assert "risk_reduction_pct" in d
        assert "spread_bars" in d
        assert "efficiency_pct" in d
        assert "sentinel_brief" in d

    def test_spread_bars_default_when_no_time_risk(self):
        d = self._build(time_risk=[])["data"]
        assert len(d["spread_bars"]) == 6  # default 6-bar set

    def test_sentinel_brief_propagated(self):
        d = self._build(sentinel_brief="Hello Sentinel")["data"]
        assert d["sentinel_brief"] == "Hello Sentinel"

    def test_iteration_overrides(self):
        d = self._build(iteration_current=99, iteration_total=100)["data"]
        assert d["iteration_current"] == 99
        assert d["iteration_total"] == 100


class TestNormalization:
    def test_normalize_gold_simulation_row(self):
        row = {
            "scenario_name": "SCENARIO A: Inspect",
            "incident_reduction_pct": 15.2,
            "net_benefit": 120000.0,
            "recommendation_priority": "HIGHLY RECOMMENDED",
            "intervention_cost": 450000.0,
            "projected_annual_incidents": 100,
        }
        n = normalize_simulation_row(row)
        assert n["risk_reduction_pct"] == 15.2
        assert n["feasibility"] == "HIGH"

    def test_pick_best_skips_baseline(self):
        scenarios = [
            {"scenario_name": "BASELINE: No intervention", "risk_reduction_pct": 0.0, "net_benefit": -100.0},
            {"scenario_name": "SCENARIO A", "risk_reduction_pct": 20.0, "net_benefit": 500000.0},
        ]
        best = pick_best_simulation_scenario(scenarios)
        assert "BASELINE" not in best["scenario_name"].upper()


class TestComplianceSnapshot:
    def _build(self, **kwargs):
        defaults = dict(
            repeat_offenders=_mock_repeat_offenders(),
            exec_metrics=_mock_executive_metrics(),
            query_latency_ms=90.0,
            source_status="mock",
            alerts=[],
        )
        defaults.update(kwargs)
        return build_compliance_snapshot(**defaults)

    def test_data_fields(self):
        d = self._build()["data"]
        assert "repeat_offenders" in d
        assert "kpis" in d
        assert "policy_violations_30d" in d
        assert "compliance_rate" in d
        assert "frameworks" in d

    def test_kpis_have_labels(self):
        kpis = self._build()["data"]["kpis"]
        assert len(kpis) >= 2
        for kpi in kpis:
            assert "label" in kpi
            assert "value" in kpi
            assert "status" in kpi

    def test_frameworks_present(self):
        frameworks = self._build()["data"]["frameworks"]
        assert len(frameworks) >= 2
