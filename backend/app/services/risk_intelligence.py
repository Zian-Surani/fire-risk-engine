from __future__ import annotations

from typing import Any

from app.data.districts import DISTRICT_CENTROIDS
from app.services.utils import clamp, to_float, to_int


def build_risk_dataset(rows: list[dict[str, Any]]) -> dict[str, Any]:
    enriched: list[dict[str, Any]] = []
    if not rows:
        return {
            "markers": [],
            "top_markers": [],
            "global_risk_index": 0.0,
            "high_risk_zones": 0,
            "average_adjusted_risk": 0.0,
        }

    adjusted_scores: list[float] = []
    for row in rows:
        base_risk = to_float(row.get("risk_score"))
        recency = clamp(to_float(row.get("recency_score")), 0.0, 100.0) / 100.0
        violations = max(to_int(row.get("violation_count")), 0) / 10.0
        response_delay = clamp(to_float(row.get("avg_response_time_min")), 0.0, 20.0) / 20.0 * 0.25
        compliance_gap = clamp(100.0 - to_float(row.get("compliance_score"), 100.0), 0.0, 100.0) / 100.0 * 0.35
        adjusted_score = base_risk * (1 + recency) * (1 + violations) * (1 + response_delay + compliance_gap)
        adjusted_scores.append(adjusted_score)
        row_copy = dict(row)
        row_copy["adjusted_risk_score"] = adjusted_score
        enriched.append(row_copy)

    sorted_scores = sorted(adjusted_scores)
    score_count = len(sorted_scores)
    for row in enriched:
        score = row["adjusted_risk_score"]
        position = sorted_scores.index(score)
        percentile = position / max(score_count - 1, 1)
        if percentile >= 0.95:
            band = "HIGH"
            severity = 5
            color = "#ff6b5f"
        elif percentile >= 0.75:
            band = "MEDIUM"
            severity = 3
            color = "#ffd54a"
        else:
            band = "LOW"
            severity = 1 if percentile < 0.5 else 2
            color = "#71d7cd"
        centroid = DISTRICT_CENTROIDS.get(str(row.get("district") or "UNKNOWN"), DISTRICT_CENTROIDS["UNKNOWN"])
        row["adjusted_percentile"] = round(percentile, 4)
        row["adjusted_risk_band"] = band
        row["visual_severity_level"] = severity
        row["marker_color"] = color
        row["latitude"] = centroid["lat"]
        row["longitude"] = centroid["lng"]
        row["display_district"] = centroid["label"]
        row["risk_drivers"] = rank_risk_drivers(row)
        row["explanation_text"] = build_deterministic_explanation(row)

    enriched.sort(key=lambda item: item["adjusted_risk_score"], reverse=True)
    top_markers = enriched[:250]
    return {
        "markers": top_markers,
        "top_markers": top_markers[:12],
        "global_risk_index": round(sum(adjusted_scores) / len(adjusted_scores) * 100, 1),
        "average_adjusted_risk": round(sum(adjusted_scores) / len(adjusted_scores), 4),
        "high_risk_zones": len([row for row in enriched if row["adjusted_risk_band"] == "HIGH"]),
    }


def rank_risk_drivers(row: dict[str, Any]) -> list[dict[str, Any]]:
    response_minutes = to_float(row.get("avg_response_time_min"))
    compliance_gap = clamp(100.0 - to_float(row.get("compliance_score"), 100.0), 0.0, 100.0)
    drivers = [
        {
            "label": "High incident volume",
            "impact_pct": round(clamp(to_int(row.get("incident_count")) / 6.0, 0.0, 40.0), 1),
        },
        {
            "label": "Repeated violations",
            "impact_pct": round(clamp(to_int(row.get("violation_count")) * 12.0, 0.0, 35.0), 1),
        },
        {
            "label": "Recent activity",
            "impact_pct": round(clamp(to_float(row.get("recency_score")) * 0.3, 0.0, 30.0), 1),
        },
        {
            "label": "Slow response time",
            "impact_pct": round(clamp(response_minutes * 1.6, 0.0, 25.0), 1),
        },
        {
            "label": "Compliance gap",
            "impact_pct": round(clamp(compliance_gap * 0.25, 0.0, 25.0), 1),
        },
        {
            "label": "Human impact history",
            "impact_pct": round(clamp(to_float(row.get("human_impact_score")) / 2.5, 0.0, 35.0), 1),
        },
    ]
    drivers.sort(key=lambda item: item["impact_pct"], reverse=True)
    return drivers[:3]


def build_deterministic_explanation(row: dict[str, Any]) -> str:
    drivers = row["risk_drivers"]
    parts = [f"{driver['label']} (+{driver['impact_pct']}%)" for driver in drivers if driver["impact_pct"] > 0]
    if not parts:
        return "Low activity profile with no dominant risk driver."
    return "; ".join(parts)
