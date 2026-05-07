from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    page_context: str | None = None

class LocationRequest(BaseModel):
    location: str

@router.post("")
async def chat_endpoint(payload: ChatRequest, request: Request) -> dict[str, Any]:
    """Generates an AI response for the Pac-Man RAG chatbot."""
    chat_svc = request.app.state.chat_service
    if not chat_svc:
        raise HTTPException(status_code=500, detail="Chat service not initialized")
        
    messages = [{"role": m.role, "content": m.content} for m in payload.messages]
    
    reply = await chat_svc.generate_chat_reply(messages, page_context=payload.page_context)
    
    return {
        "reply": reply
    }

@router.post("/analyze-location")
async def analyze_location_endpoint(payload: LocationRequest, request: Request) -> dict[str, Any]:
    """Provides a data-inferred analysis of a specific geographic location via AI."""
    chat_svc = request.app.state.chat_service
    if not chat_svc:
        raise HTTPException(status_code=500, detail="Chat service not initialized")
        
    reply = await chat_svc.analyze_location(payload.location)
    
    return {
        "analysis": reply
    }
