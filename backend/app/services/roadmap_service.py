from __future__ import annotations

from app.data.districts import ROADMAP_COUNTS


class RoadmapService:
    def build_snapshot(self) -> dict:
        return {
            "badges": [
                "Real-time Databricks Reads",
                "Constraint-Based Optimization",
                "Explainable AI Layer",
            ],
            "counts": ROADMAP_COUNTS,
            "modules": [
                {
                    "id": "ingestion",
                    "title": "Data Ingestion",
                    "details": [
                        "Bronze ingestion notebooks persist raw city datasets",
                        "Delta tables preserve historical traceability",
                        "Validation checks guard schema drift",
                    ],
                },
                {
                    "id": "engineering",
                    "title": "Data Engineering",
                    "details": [
                        "Silver unifies 23,634 addresses into silver_fire_risk_base",
                        "34 engineered features include response, compliance, and recency",
                        "Gold layer materialises 13 Delta tables (top 100 critical, district intelligence, "
                        "response optimization, inspection strategy, action playbook, predictive alerts, "
                        "risk heatmap, executive decision matrix, time risk, repeat offenders, structured "
                        "recommendations, impact simulation, executive metrics)",
                    ],
                },
                {
                    "id": "decision",
                    "title": "Decision Layer",
                    "details": [
                        "Adjusted risk amplification for visual contrast",
                        "Multi-objective deployment optimization",
                        "Scenario simulation and AI reasoning",
                    ],
                },
            ],
            "pipeline_nodes": [
                "Data Sources",
                "Ingestion",
                "Processing",
                "ML Models",
                "Decision Engine",
                "Output",
            ],
            "known_limitations": [
                "Gold heatmap coordinates still rely on placeholder lat/lng values",
                "Native risk band distribution is sparse, so the app uses an adjusted risk layer for visualization",
                "OpenAI reasoning falls back to deterministic narratives when no API key is present",
            ],
        }
