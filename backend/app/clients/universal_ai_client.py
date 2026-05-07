from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any, Protocol

try:
    from google import genai
except ImportError:
    genai = None

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

try:
    import anthropic as _anthropic_sdk
except ImportError:
    _anthropic_sdk = None

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Provider Protocol
# ---------------------------------------------------------------------------

class AIProvider(Protocol):
    async def generate(self, prompt: str, model: str) -> str | None:
        ...


# ---------------------------------------------------------------------------
# Provider Implementations
# ---------------------------------------------------------------------------

class GeminiProvider:
    def __init__(self, api_key: str):
        self._client = genai.Client(api_key=api_key) if genai else None

    async def generate(self, prompt: str, model: str) -> str | None:
        if not self._client:
            return None
        try:
            response = await self._client.aio.models.generate_content(model=model, contents=prompt)
            return (response.text or "").strip() if getattr(response, "text", None) else None
        except Exception as e:
            logger.warning(f"GeminiProvider failed: {e}")
            return None


class OpenAICompatibleProvider:
    """Handles OpenAI, DeepSeek, Groq, OpenRouter — all use the OpenAI SDK."""

    def __init__(self, api_key: str, base_url: str | None = None, provider_name: str = "OpenAI"):
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url) if AsyncOpenAI else None
        self._name = provider_name

    async def generate(self, prompt: str, model: str) -> str | None:
        if not self._client:
            return None
        try:
            response = await self._client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            return response.choices[0].message.content.strip() if response.choices else None
        except Exception as e:
            logger.warning(f"OpenAICompatibleProvider ({self._name}) failed: {e}")
            return None


class AnthropicProvider:
    """Anthropic Claude via the official anthropic SDK."""

    def __init__(self, api_key: str):
        self._client = _anthropic_sdk.AsyncAnthropic(api_key=api_key) if _anthropic_sdk else None

    async def generate(self, prompt: str, model: str) -> str | None:
        if not self._client:
            return None
        try:
            message = await self._client.messages.create(
                model=model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            if message.content and hasattr(message.content[0], "text"):
                return message.content[0].text.strip()
            return None
        except Exception as e:
            logger.warning(f"AnthropicProvider failed: {e}")
            return None


# ---------------------------------------------------------------------------
# Universal Client with Fallback + Exponential Backoff
# ---------------------------------------------------------------------------

_MAX_RETRIES = 2          # retries per provider on rate-limit (429)
_BACKOFF_BASE = 1.5       # seconds — grows as 1.5, 3.0, 6.0 ...


class UniversalAIClient:
    """
    A unified AI client that attempts multiple providers in order with automatic
    failover and exponential backoff for rate-limit (429) errors.

    Provider priority (highest → lowest):
      1. DeepSeek
      2. Groq
      3. Anthropic (Claude)
      4. OpenRouter
      5. OpenAI (if enabled)
      6. Gemini
    """

    def __init__(self, settings: Any):
        self.settings = settings
        self.providers: list[dict[str, Any]] = []

        # 1. DeepSeek (via OpenAI SDK)
        deepseek_key = getattr(settings, "deepseek_api_key", None) or os.getenv("DEEPSEEK_API_KEY")
        if deepseek_key:
            self.providers.append({
                "name": "DeepSeek",
                "client": OpenAICompatibleProvider(deepseek_key, "https://api.deepseek.com", "DeepSeek"),
                "model": getattr(settings, "deepseek_model", None) or os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            })

        # 2. Groq (via OpenAI SDK)
        groq_key = getattr(settings, "groq_api_key", None) or os.getenv("GROQ_API_KEY")
        if groq_key:
            self.providers.append({
                "name": "Groq",
                "client": OpenAICompatibleProvider(groq_key, "https://api.groq.com/openai/v1", "Groq"),
                "model": getattr(settings, "groq_model", None) or os.getenv("GROQ_MODEL", "llama3-70b-8192"),
            })

        # 3. Anthropic (Claude)
        anthropic_key = getattr(settings, "anthropic_api_key", None) or os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.providers.append({
                "name": "Anthropic",
                "client": AnthropicProvider(anthropic_key),
                "model": getattr(settings, "anthropic_model", None) or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
            })

        # 4. OpenRouter (via OpenAI SDK)
        openrouter_key = getattr(settings, "openrouter_api_key", None) or os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            self.providers.append({
                "name": "OpenRouter",
                "client": OpenAICompatibleProvider(
                    openrouter_key,
                    "https://openrouter.ai/api/v1",
                    "OpenRouter",
                ),
                "model": os.getenv("OPENROUTER_MODEL", "mistralai/mixtral-8x7b-instruct"),
            })

        # 5. Gemini
        gemini_key = getattr(settings, "gemini_api_key", None)
        if gemini_key:
            self.providers.append({
                "name": "Gemini",
                "client": GeminiProvider(gemini_key),
                "model": getattr(settings, "gemini_model", "gemini-2.0-flash"),
            })

        self._cache: dict[str, tuple[str, float]] = {}

        logger.info(
            f"UniversalAIClient initialised with {len(self.providers)} provider(s): "
            + ", ".join(p["name"] for p in self.providers)
        )

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    async def _try_provider(self, provider: dict[str, Any], prompt: str) -> str | None:
        """Attempt a provider with exponential backoff on rate-limit errors."""
        for attempt in range(_MAX_RETRIES + 1):
            try:
                logger.info(f"[{provider['name']}] Attempting generation (attempt {attempt + 1})…")
                result = await provider["client"].generate(prompt, provider["model"])
                if result:
                    return result
                # Empty result: treat as failure, move on immediately
                return None
            except Exception as exc:
                err_str = str(exc).lower()
                is_rate_limit = "429" in err_str or "rate" in err_str or "quota" in err_str or "exceeded" in err_str
                if is_rate_limit and attempt < _MAX_RETRIES:
                    wait = _BACKOFF_BASE * (2 ** attempt)
                    logger.warning(
                        f"[{provider['name']}] Rate limited (attempt {attempt + 1}). "
                        f"Retrying in {wait:.1f}s…"
                    )
                    await asyncio.sleep(wait)
                else:
                    logger.warning(f"[{provider['name']}] Failed: {exc}")
                    return None
        return None

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    async def generate(self, cache_key: str, prompt: str, ttl_seconds: int = 300) -> str | None:
        """Generate text, trying providers in priority order with caching."""
        # Check cache first
        now = time.time()
        if cache_key in self._cache:
            val, expiry = self._cache[cache_key]
            if expiry > now:
                logger.debug(f"Cache hit for key='{cache_key}'")
                return val

        # Try providers in order
        for provider in self.providers:
            result = await self._try_provider(provider, prompt)
            if result:
                self._cache[cache_key] = (result, now + ttl_seconds)
                logger.info(f"UniversalAIClient: Success via {provider['name']}")
                return result

        logger.error("UniversalAIClient: All AI providers failed or no keys configured.")
        return None
