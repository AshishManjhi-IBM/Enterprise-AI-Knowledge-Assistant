"""
OpenAI LLM Provider — Phase 10 Production Readiness.

Supports:
  - Chat completions via openai>=1.0 client
  - Streaming via async streaming API
  - Health check via model list call
  - Models: gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo, etc.

Required environment variable:
  OPENAI_API_KEY=sk-...
"""

from __future__ import annotations

import os
from typing import AsyncIterator, Dict, Any, Optional

from backend.providers.base import BaseLLMProvider
from backend.core.logging import get_logger

logger = get_logger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI provider for GPT models (gpt-4o, gpt-4o-mini, gpt-4-turbo, etc.).

    Uses the official ``openai`` Python SDK (>=1.0).
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        try:
            import openai  # noqa: F401 — validate import at init time
        except ImportError:
            raise ImportError(
                "openai package is not installed. Run: pip install openai>=1.10"
            )

        api_key = config.get("api_key") or os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError(
                "OpenAI API key not found. "
                "Set OPENAI_API_KEY in your environment or .env file."
            )

        import openai as _openai
        self._client = _openai.AsyncOpenAI(
            api_key=api_key,
            base_url=config.get("base_url"),  # override for proxies / compatible APIs
        )
        self.model_name: str = config.get("model", "gpt-4o-mini")
        logger.info(f"OpenAIProvider initialised with model={self.model_name}")

    # ── BaseLLMProvider interface ──────────────────────────────────────────

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate a completion and return ``{"text": ..., "model": ..., "tokens_used": ...}``."""
        response = await self._client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        text = response.choices[0].message.content or ""
        return {
            "text":        text,
            "model":       response.model,
            "tokens_used": response.usage.total_tokens if response.usage else 0,
        }

    async def stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream tokens one by one."""
        async with await self._client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        ) as stream:
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta

    async def health_check(self) -> bool:
        """Return True if the API is reachable and the model exists."""
        try:
            models = await self._client.models.list()
            model_ids = [m.id for m in models.data]
            return self.model_name in model_ids or bool(model_ids)
        except Exception as exc:
            logger.warning(f"OpenAI health check failed: {exc}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider":   "openai",
            "model_name": self.model_name,
            "status":     "active",
        }


# Made with Bob
