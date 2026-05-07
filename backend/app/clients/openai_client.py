from __future__ import annotations

import asyncio
import time
import logging
from dataclasses import dataclass

from openai import OpenAI

from app.core.config import Settings

logger = logging.getLogger(__name__)

@dataclass(slots=True)
class CachedGeneration:
    value: str
    expires_at: float


class OpenAIClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._keys = settings.get_openai_keys_list
        self._current_key_idx = 0
        self._client = OpenAI(api_key=self._keys[self._current_key_idx]) if self._keys else None
        self._cache: dict[str, CachedGeneration] = {}

    def _rotate_key(self) -> None:
        if len(self._keys) > 1:
            self._current_key_idx = (self._current_key_idx + 1) % len(self._keys)
            self._client = OpenAI(api_key=self._keys[self._current_key_idx])
            logger.warning("OpenAI rate limited. Rotated to next API key (index %d).", self._current_key_idx)

    async def generate(self, cache_key: str, prompt: str, *, ttl_seconds: int = 60) -> str | None:
        if not getattr(self.settings, "openai_enabled", False) or not self._client:
            return None

        cached = self._cache.get(cache_key)
        now = time.time()
        if cached and cached.expires_at > now:
            return cached.value

        def _run() -> str:
            if not self._client:
                return ""
            try:
                response = self._client.chat.completions.create(
                    model=getattr(self.settings, "openai_model", "gpt-4.5-preview"),
                    messages=[{"role": "user", "content": prompt}],
                    max_completion_tokens=220,
                )
                return response.choices[0].message.content or ""
            except Exception as e:
                err = str(e)
                if "429" in err or "insufficient_quota" in err.lower():
                    self._rotate_key()
                    # Retry once after rotation
                    if len(self._keys) > 1 and self._client:
                        try:
                            fallback_res = self._client.chat.completions.create(
                                model=getattr(self.settings, "openai_model", "gpt-4.5-preview"),
                                messages=[{"role": "user", "content": prompt}],
                                max_completion_tokens=220,
                            )
                            return fallback_res.choices[0].message.content or ""
                        except Exception as fallback_exc:
                            logger.error(f"OpenAI fallback generation failed: {fallback_exc}")
                            return ""
                logger.error(f"OpenAI generation failed: {e}")
                return ""

        result = await asyncio.to_thread(_run)
        if result:
            self._cache[cache_key] = CachedGeneration(value=result, expires_at=now + ttl_seconds)
            return result
        return None
