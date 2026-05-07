"""Tests for compliance CSV/PDF report builders."""

from __future__ import annotations

from app.services.report_service import ReportService


def test_build_csv_stringifies_numeric_metric_values() -> None:
    svc = ReportService()
    raw = svc.build_csv(
        metrics=[
            {"metric_name": "High-Risk Property Count", "current_value": 42.0, "status": "stable"},
        ],
        repeat_offenders=[],
    )
    text = raw.decode("utf-8")
    assert "42.0" in text or "42" in text


def test_build_pdf_accepts_numeric_current_value() -> None:
    svc = ReportService()
    pdf = svc.build_pdf(
        metrics=[
            {"metric_name": "Test", "current_value": 10.5, "unit": "units", "status": "ok"},
        ],
        repeat_offenders=[],
    )
    assert pdf.startswith(b"%PDF")
