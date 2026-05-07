from __future__ import annotations

from typing import Any

from app.clients.gemini_client import GeminiClient


class AIService:
    def __init__(self, client: GeminiClient) -> None:
        self.client = client

    async def explain_location(self, marker: dict[str, Any]) -> str:
        fallback = (
            f"{marker.get('address', 'This property')} is {marker.get('adjusted_risk_band', 'LOW')} risk due to "
            f"{marker.get('explanation_text', 'limited operational signals')}."
        )
        prompt = (
            "You are a fire operations analyst. In 2 sentences, explain why this location is risky and what to do next. "
            "Focus on budget-aware, operator-friendly reasoning.\n\n"
            f"Address: {marker.get('address')}\n"
            f"District: {marker.get('district')}\n"
            f"Adjusted risk band: {marker.get('adjusted_risk_band')}\n"
            f"Adjusted risk score: {marker.get('adjusted_risk_score'):.4f}\n"
            f"Drivers: {marker.get('explanation_text')}\n"
        )
        return await self.client.generate(f"location:{marker.get('address')}", prompt) or fallback

    async def build_decision_brief(
        self,
        *,
        top_marker: dict[str, Any] | None,
        best_scenario: dict[str, Any] | None,
    ) -> str:
        fallback_parts = []
        if top_marker:
            fallback_parts.append(
                f"Prioritize {top_marker.get('address')} first. Main drivers: {top_marker.get('explanation_text')}."
            )
        if best_scenario:
            fallback_parts.append(
                f"Best current scenario is {best_scenario.get('scenario_name')} with net benefit {best_scenario.get('net_benefit')}."
            )
        fallback = " ".join(fallback_parts).strip() or "No AI decision brief is available yet."
        prompt = (
            "You are Sentinel Core for a fire risk operations center. Respond in 3 short sentences. "
            "Cover: why the current hotspot matters, what to do if budget is constrained, and the best next action within 7 days.\n\n"
            f"Top marker: {top_marker}\n"
            f"Best scenario: {best_scenario}\n"
        )
        return await self.client.generate("decision-brief", prompt) or fallback
