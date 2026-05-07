from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Any

try:
    from google import genai
except ImportError:  # pragma: no cover - exercised via runtime bootstrap, not unit tests
    genai = None  # type: ignore[assignment]

from app.core.config import Settings

logger = logging.getLogger(__name__)

_RETRY_IN_RE = re.compile(r"retry in ([\d.]+)\s*s", re.IGNORECASE)


def _parse_retry_delay_seconds(exc: BaseException) -> float | None:
    """Best-effort parse of server-suggested retry delay from error text."""
    text = str(exc)
    m = _RETRY_IN_RE.search(text)
    if m:
        return float(m.group(1))
    return None


@dataclass(slots=True)
class CachedGeneration:
    value: str
    expires_at: float


class GeminiClient:
    """Gemini text generation via the Google Gen AI SDK (google-genai), with HA key cycling."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._keys = settings.get_gemini_keys_list
        self._current_key_idx = 0
        self._client: Any | None = None
        if not self._keys:
            pass # No keys provided
        elif genai is None:
            logger.warning(
                "Gemini is configured but the google-genai package is not installed; "
                "falling back to deterministic backend responses."
            )
        else:
            self._client = genai.Client(api_key=self._keys[self._current_key_idx])
        self._cache: dict[str, CachedGeneration] = {}
        self._cooldown_until: float = 0.0

    def _in_cooldown(self) -> bool:
        return time.time() < self._cooldown_until

    def _enter_rate_limit_cooldown(self, exc: BaseException) -> None:
        if len(self._keys) > 1:
            self._current_key_idx = (self._current_key_idx + 1) % len(self._keys)
            self._client = genai.Client(api_key=self._keys[self._current_key_idx])
            logger.warning("Gemini rate limited. Rotated to next API key (index %d).", self._current_key_idx)
            self._cooldown_until = time.time() + 1.0
            return

        suggested = _parse_retry_delay_seconds(exc)
        base = float(self.settings.gemini_rate_limit_cooldown_seconds)
        cooldown = max(base, suggested or 0.0, 60.0)
        self._cooldown_until = time.time() + cooldown
        logger.warning(
            "Gemini rate limited (429 / quota); skipping API calls for ~%ds. "
            "Raise GEMINI_CACHE_TTL_SECONDS, set GEMINI_ENABLED=false, or enable billing — "
            "https://ai.google.dev/gemini-api/docs/rate-limits",
            int(cooldown),
        )

    async def generate(self, cache_key: str, prompt: str, *, ttl_seconds: int | None = None) -> str | None:
        if not self.settings.gemini_enabled or not self._client:
            return None

        ttl = (
            ttl_seconds
            if ttl_seconds is not None
            else self.settings.gemini_cache_ttl_seconds
        )

        now = time.time()
        cached = self._cache.get(cache_key)
        if cached and cached.expires_at > now:
            return cached.value

        if self._in_cooldown():
            logger.debug("Gemini cooldown active; skip generate (%s)", cache_key)
            return None

        try:
            response = await self._client.aio.models.generate_content(
                model=self.settings.gemini_model,
                contents=prompt,
            )
        except Exception as exc:
            err = str(exc)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                self._enter_rate_limit_cooldown(exc)
                # If we swapped keys, try again once before failing out permanently for this request
                if len(self._keys) > 1:
                    try:
                        response = await self._client.aio.models.generate_content(
                            model=self.settings.gemini_model,
                            contents=prompt,
                        )
                    except Exception as fallback_exc:
                        logger.warning("Gemini generate_content failed on fallback key: %s", fallback_exc)
                        return None
                else:
                    return None
            else:
                logger.warning(
                    "Gemini generate_content failed (model=%s): %s",
                    self.settings.gemini_model,
                    exc,
                )
                return None

        text = (response.text or "").strip() if getattr(response, "text", None) else ""
        if text:
            self._cache[cache_key] = CachedGeneration(value=text, expires_at=now + ttl)
        return text or None
