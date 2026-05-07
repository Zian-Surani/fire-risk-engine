from __future__ import annotations

import json
import logging
from typing import Any

from app.core.snapshot_cache import SnapshotCache
from app.clients.universal_ai_client import UniversalAIClient

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, ai_client: UniversalAIClient, cache: SnapshotCache):
        self._ai_client = ai_client
        self._cache = cache

    async def generate_chat_reply(self, messages: list[dict[str, str]], page_context: str | None = None) -> str:
        """
        Takes a list of messages, prepends a system prompt containing the latest 
        snapshot metrics (RAG capability), and returns an AI response.
        """
        # Fetch RAG Context
        cc_snap = await self._cache.get_snapshot("command-center")
        ops_snap = await self._cache.get_snapshot("operations")
        
        context_data = {}
        if cc_snap and "data" in cc_snap:
            context_data["Global Risk Index"] = cc_snap["data"].get("global_risk_index")
            context_data["Average Adjusted Risk"] = cc_snap["data"].get("average_adjusted_risk")
            context_data["High Risk Zones"] = cc_snap["data"].get("high_risk_zones")
            context_data["Top Critical Districts"] = [d.get("display_district") for d in cc_snap["data"].get("districts", [])[:3]]
            context_data["Executive Metrics"] = cc_snap["data"].get("executive_metrics")
            
        if ops_snap and "data" in ops_snap:
            context_data["Active Ground Units"] = ops_snap["data"].get("ground_units_active")
            context_data["Average Response Time (mins)"] = ops_snap["data"].get("avg_response_time_min")
            context_data["System Status"] = ops_snap["data"].get("system_health_pct")

        route_info = f"\n*IMPORTANT: The user is currently viewing the '{page_context}' page on the dashboard. Tailor your context to this view if applicable.*" if page_context else ""

        system_prompt = (
            "You are the 'Sentinel Core' - the advanced AI at the heart of the Fire Risk Intelligence Platform (FIRE). "
            "Your personality is inspired by classic retro arcade games (Pac-Man). You should be professional and tactical, "
            "but enjoy referencing data as 'pellets', 'high scores', 'chomping through telemetry', and avoidance of 'risk ghosts'.\n\n"
            "COW (Context of Work): Use the following REAL-TIME TELEMETRY SNAPSHOT to answer user queries. "
            "This is your primary ground truth. If asked for recommendations, relate it directly to these metrics.\n"
            f"{json.dumps(context_data, indent=2)}\n\n"
            "If the telemetry is empty or you lack specific metrics, inform the commander that you are scanning for fresh data. "
            f"{route_info}"
        )

        # Gemini supports multi-turn chat via string formatting or SDK, but we are using `generate_content` which takes 
        # a string or list of contents. To keep it simple, we stringify the history.
        conversation_str = system_prompt + "\n\n--- Conversation History ---\n"
        for msg in messages:
            role = "USER" if msg.get("role") == "user" else "PAC-BOT"
            conversation_str += f"{role}: {msg.get('content')}\n"
            
        conversation_str += "PAC-BOT: "

        # Since it's chat, we don't necessarily want to heavily cache it. TTL=0 effectively forces a fresh generation.
        # But we pass a cache key based on the last user message just in case the framework requires it.
        last_msg = messages[-1].get("content", "empty")[:50]
        cache_key = f"chat_{hash(conversation_str + last_msg)}"
        
        reply = await self._ai_client.generate(cache_key, conversation_str, ttl_seconds=1)
        if not reply:
            return "Waka waka... 🍓 Sorry commander, I couldn't process your request. Check your API token or try again! [Rate limits exceeded]"

        return reply

    async def analyze_location(self, location: str) -> str:
        """
        Takes a location string and returns an AI analysis for that specific area 
        based on overall system metrics and learned RAG context.
        """
        cc_snap = await self._cache.get_snapshot("command-center")
        context = cc_snap["data"] if cc_snap else {}
        
        prompt = (
            f"You are the FIRE intelligence system backend. The user has searched for a specific geographical location: '{location}'. "
            f"Given our current command center context: \n"
            f"{json.dumps(context, indent=2)}\n\n"
            f"Generate a concise, analytical 3-sentence summary highlighting the presumed fire risk, response capability, "
            f"and a strategic recommendation for this location based on the data provided. Speak as a serious tactical advisor, no arcade references here."
        )
        
        cache_key = f"loc_analysis_{hash(location)}"
        reply = await self._ai_client.generate(cache_key, prompt, ttl_seconds=300)
        
        if not reply:
            return f"Analysis unavailable for {location} due to limited telemetry. Proceed with standard caution."
            
        return reply
