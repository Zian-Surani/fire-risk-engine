"""Tests for static roadmap snapshot content."""

from __future__ import annotations

from app.data.districts import ROADMAP_COUNTS
from app.services.roadmap_service import RoadmapService


def test_roadmap_counts_match_data_module() -> None:
    snap = RoadmapService().build_snapshot()
    assert snap["counts"] == ROADMAP_COUNTS


def test_roadmap_modules_cover_pipeline_layers() -> None:
    snap = RoadmapService().build_snapshot()
    titles = {m["title"] for m in snap["modules"]}
    assert "Data Ingestion" in titles
    assert "Data Engineering" in titles
    assert "Decision Layer" in titles


def test_engineering_module_mentions_gold_tables() -> None:
    snap = RoadmapService().build_snapshot()
    eng = next(m for m in snap["modules"] if m["id"] == "engineering")
    joined = " ".join(eng["details"])
    assert "impact simulation" in joined.lower() and "13" in joined
