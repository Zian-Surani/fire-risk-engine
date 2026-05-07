"""Tests for the multi-objective optimization service."""

from __future__ import annotations

import pytest

from app.services.optimization_service import OptimizationService


def _make_marker(address="100 Test St", district="1", adjusted_percentile=0.8, compliance_score=70.0, violation_count=2, adjusted_risk_band="HIGH", display_district="District 1", adjusted_risk_score=5.0):
    return {
        "address": address,
        "district": district,
        "adjusted_percentile": adjusted_percentile,
        "compliance_score": compliance_score,
        "violation_count": violation_count,
        "adjusted_risk_band": adjusted_risk_band,
        "display_district": display_district,
        "adjusted_risk_score": adjusted_risk_score,
    }


def _make_response_row(address="100 Test St", avg_response_time_min=10.0):
    return {"address": address, "avg_response_time_min": avg_response_time_min}


def _make_district_row(district="1", resource_gap_score=0.5):
    return {"district": district, "resource_gap_score": resource_gap_score}


class TestOptimizationService:
    def setup_method(self):
        self.svc = OptimizationService()

    def _run(self, markers=None, district_rows=None, response_rows=None, recommendation_rows=None, budget_cap=1_500_000.0, max_districts=3):
        return self.svc.run(
            risk_markers=markers or [],
            district_rows=district_rows or [],
            response_rows=response_rows or [],
            recommendation_rows=recommendation_rows or [],
            budget_cap=budget_cap,
            max_districts=max_districts,
        )

    def test_empty_markers_returns_result_structure(self):
        result = self._run()
        assert "request_id" in result
        assert "allocation_changes" in result
        assert "improvement_metrics" in result
        assert "objective_scores" in result
        assert result["allocation_changes"] == []

    def test_single_marker_selected(self):
        markers = [_make_marker()]
        result = self._run(markers=markers)
        assert len(result["allocation_changes"]) == 1

    def test_budget_cap_respected(self):
        # Give many markers but very small budget
        markers = [_make_marker(address=f"{i} St", district=str(i % 5 + 1)) for i in range(20)]
        result = self._run(markers=markers, budget_cap=100_000.0)
        total_cost = sum(c["intervention_cost"] for c in result["allocation_changes"])
        # If any was selected, budget must hold (or nothing was selected)
        if result["allocation_changes"]:
            assert total_cost <= 100_000.0 or len(result["allocation_changes"]) == 1

    def test_max_districts_respected(self):
        # All markers from different districts
        markers = [_make_marker(address=f"{i} Main St", district=str(i + 1)) for i in range(10)]
        result = self._run(markers=markers, max_districts=2)
        selected_districts = {c["district"] for c in result["allocation_changes"]}
        assert len(selected_districts) <= 2

    def test_objective_scores_sum_to_1(self):
        result = self._run()
        total = sum(result["objective_scores"].values())
        assert abs(total - 1.0) < 0.01

    def test_high_risk_band_adds_cost(self):
        # HIGH band marker should have higher cost
        high = _make_marker(adjusted_risk_band="HIGH", violation_count=0)
        low = _make_marker(adjusted_risk_band="LOW", violation_count=0, district="2", address="200 Test Ave")
        result_high = self._run(markers=[high])
        result_low = self._run(markers=[low])
        if result_high["allocation_changes"] and result_low["allocation_changes"]:
            cost_high = result_high["allocation_changes"][0]["intervention_cost"]
            cost_low = result_low["allocation_changes"][0]["intervention_cost"]
            assert cost_high > cost_low

    def test_narrative_is_nonempty_string(self):
        markers = [_make_marker()]
        result = self._run(markers=markers)
        assert isinstance(result["narrative"], str)
        assert len(result["narrative"]) > 10

    def test_ai_confidence_in_range(self):
        markers = [_make_marker()]
        result = self._run(markers=markers)
        assert 0 <= result["ai_confidence"] <= 100

    def test_improvement_metrics_present(self):
        markers = [_make_marker()]
        response_rows = [_make_response_row()]
        result = self._run(markers=markers, response_rows=response_rows)
        metrics = result["improvement_metrics"]
        assert "budget_used" in metrics
        assert "response_time_before_min" in metrics
        assert "response_time_after_min" in metrics
        assert metrics["response_time_after_min"] >= 4.0  # capped minimum
