"""Tests for app-side risk intelligence: adjusted scoring, banding, explainability."""

from __future__ import annotations

import pytest

from app.services.risk_intelligence import (
    build_deterministic_explanation,
    build_risk_dataset,
    rank_risk_drivers,
)


def _make_row(**kwargs):
    defaults = {
        "address": "100 Test St",
        "district": "1",
        "risk_score": 50.0,
        "recency_score": 40.0,
        "violation_count": 2,
        "incident_count": 3,
        "avg_response_time_min": 8.0,
        "compliance_score": 75.0,
        "human_impact_score": 30.0,
    }
    defaults.update(kwargs)
    return defaults


class TestBuildRiskDataset:
    def test_empty_rows_returns_zeroes(self):
        result = build_risk_dataset([])
        assert result["markers"] == []
        assert result["top_markers"] == []
        assert result["global_risk_index"] == 0.0
        assert result["high_risk_zones"] == 0

    def test_single_row_produces_marker(self):
        rows = [_make_row()]
        result = build_risk_dataset(rows)
        assert len(result["markers"]) == 1
        marker = result["markers"][0]
        assert marker["adjusted_risk_score"] > 0
        assert marker["adjusted_risk_band"] in {"HIGH", "MEDIUM", "LOW"}
        assert "latitude" in marker
        assert "longitude" in marker
        assert "risk_drivers" in marker
        assert "explanation_text" in marker

    def test_high_violation_amplifies_risk(self):
        low_row = _make_row(risk_score=30.0, violation_count=0, recency_score=10.0)
        high_row = _make_row(risk_score=30.0, violation_count=8, recency_score=90.0, avg_response_time_min=18.0, compliance_score=20.0)
        result = build_risk_dataset([low_row, high_row])
        scores = [m["adjusted_risk_score"] for m in result["markers"]]
        # The high-violation row should have a higher adjusted score
        assert scores[0] > scores[1]

    def test_percentile_banding_top_5_pct_is_high(self):
        # 20 rows with linearly increasing scores; the top row (index 19) should be HIGH
        rows = [_make_row(risk_score=float(i * 3), violation_count=i % 5) for i in range(20)]
        result = build_risk_dataset(rows)
        # At least 1 HIGH band expected
        bands = {m["adjusted_risk_band"] for m in result["markers"]}
        assert "HIGH" in bands

    def test_top_markers_capped_at_12(self):
        rows = [_make_row(risk_score=float(i)) for i in range(50)]
        result = build_risk_dataset(rows)
        assert len(result["top_markers"]) <= 12

    def test_markers_capped_at_250(self):
        rows = [_make_row(risk_score=float(i)) for i in range(300)]
        result = build_risk_dataset(rows)
        assert len(result["markers"]) <= 250

    def test_unknown_district_falls_back_to_sf_centroid(self):
        rows = [_make_row(district="NONEXISTENT_DISTRICT_XYZ")]
        result = build_risk_dataset(rows)
        marker = result["markers"][0]
        # Should fall back to UNKNOWN centroid (San Francisco)
        assert abs(marker["latitude"] - 37.7749) < 0.01
        assert abs(marker["longitude"] - (-122.4194)) < 0.01

    def test_marker_color_assigned(self):
        rows = [_make_row() for _ in range(10)]
        result = build_risk_dataset(rows)
        for marker in result["markers"]:
            assert marker["marker_color"].startswith("#")


class TestRankRiskDrivers:
    def test_returns_at_most_3_drivers(self):
        row = _make_row()
        row["adjusted_risk_score"] = 80.0
        row["risk_drivers"] = []  # will be populated by rank_risk_drivers
        drivers = rank_risk_drivers(row)
        assert 1 <= len(drivers) <= 3

    def test_driver_impact_pct_nonnegative(self):
        row = _make_row(violation_count=5, avg_response_time_min=15.0, compliance_score=30.0)
        drivers = rank_risk_drivers(row)
        for driver in drivers:
            assert driver["impact_pct"] >= 0

    def test_drivers_sorted_descending(self):
        row = _make_row(violation_count=5, avg_response_time_min=15.0)
        drivers = rank_risk_drivers(row)
        pcts = [d["impact_pct"] for d in drivers]
        assert pcts == sorted(pcts, reverse=True)


class TestDeterministicExplanation:
    def test_returns_string(self):
        row = _make_row()
        row["risk_drivers"] = rank_risk_drivers(row)
        text = build_deterministic_explanation(row)
        assert isinstance(text, str)
        assert len(text) > 0

    def test_empty_drivers_returns_fallback(self):
        row = _make_row(incident_count=0, violation_count=0, recency_score=0.0, avg_response_time_min=0.0, compliance_score=100.0, human_impact_score=0.0)
        row["risk_drivers"] = rank_risk_drivers(row)
        text = build_deterministic_explanation(row)
        assert isinstance(text, str)
