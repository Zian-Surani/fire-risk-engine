from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.services.utils import clamp, priority_score, to_float, to_int


class OptimizationService:
    def run(
        self,
        *,
        risk_markers: list[dict[str, Any]],
        district_rows: list[dict[str, Any]],
        response_rows: list[dict[str, Any]],
        recommendation_rows: list[dict[str, Any]],
        budget_cap: float = 1500000.0,
        max_districts: int = 3,
    ) -> dict[str, Any]:
        district_lookup = {str(row.get("district")): row for row in district_rows}
        response_lookup = {str(row.get("address")): row for row in response_rows}
        candidates: list[dict[str, Any]] = []
        for marker in risk_markers[:25]:
            response_row = response_lookup.get(str(marker.get("address")), {})
            district_row = district_lookup.get(str(marker.get("district")), {})
            response_component = clamp(to_float(response_row.get("avg_response_time_min")) / 20.0, 0.0, 1.0)
            compliance_component = clamp((100.0 - to_float(marker.get("compliance_score"), 100.0)) / 100.0, 0.0, 1.0)
            risk_component = clamp(to_float(marker.get("adjusted_percentile")), 0.0, 1.0)
            cost = 125000.0 + (to_int(marker.get("violation_count")) * 20000.0)
            if marker.get("adjusted_risk_band") == "HIGH":
                cost += 70000.0
            cost_efficiency = 1 - clamp(cost / 400000.0, 0.0, 1.0)
            objective_score = (
                0.35 * risk_component
                + 0.30 * response_component
                + 0.20 * compliance_component
                + 0.15 * cost_efficiency
            )
            candidates.append(
                {
                    "address": marker.get("address"),
                    "district": marker.get("district"),
                    "objective_score": round(objective_score, 4),
                    "response_minutes": round(to_float(response_row.get("avg_response_time_min")), 2),
                    "coverage_gap": round(to_float(district_row.get("resource_gap_score")), 2),
                    "intervention_cost": round(cost, 2),
                    "changed_module": "resource_allocation",
                    "change": f"Shift rapid-response coverage toward {marker.get('display_district')} and schedule targeted inspection sweep.",
                }
            )

        candidates.sort(key=lambda item: item["objective_score"], reverse=True)
        selected: list[dict[str, Any]] = []
        seen_districts: set[str] = set()
        spent = 0.0
        for candidate in candidates:
            district = str(candidate["district"])
            if district in seen_districts and len(seen_districts) >= max_districts:
                continue
            projected_spend = spent + candidate["intervention_cost"]
            if projected_spend > budget_cap and selected:
                continue
            selected.append(candidate)
            seen_districts.add(district)
            spent = projected_spend
            if len(seen_districts) >= max_districts:
                break

        before_response = sum(to_float(row.get("avg_response_time_min")) for row in response_rows[:10]) / max(len(response_rows[:10]), 1)
        response_gain = sum(item["objective_score"] for item in selected) * 1.4
        coverage_gain = len(selected) * 7.5
        compliance_gain = len(selected) * 5.5
        after_response = max(before_response - response_gain, 4.0)

        return {
            "request_id": f"opt-{int(datetime.now(UTC).timestamp())}",
            "generated_at": datetime.now(UTC).isoformat(),
            "changed_modules": ["resource_allocation", "fire_station_coverage", "risk_mitigation_strategy"],
            "allocation_changes": selected,
            "rejected_alternatives": recommendation_rows[:3],
            "objective_scores": {
                "minimize_response_time": 0.30,
                "maximize_coverage": 0.35,
                "improve_compliance": 0.20,
                "minimize_cost": 0.15,
            },
            "improvement_metrics": {
                "budget_used": round(spent, 2),
                "response_time_before_min": round(before_response, 2),
                "response_time_after_min": round(after_response, 2),
                "coverage_improvement_pct": round(coverage_gain, 1),
                "compliance_improvement_pct": round(compliance_gain, 1),
            },
            "narrative": (
                f"Constraint-based optimization selected {len(selected)} interventions across {len(seen_districts)} districts. "
                f"Projected response time improves from {before_response:.1f} to {after_response:.1f} minutes."
            ),
            "ai_confidence": round(62 + len(selected) * 6.5, 1),
        }
