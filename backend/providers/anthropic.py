"""
Anthropic (Claude) LLM Provider — Phase 10 Production Readiness.

Supports:
  - Messages API via anthropic>=0.20 client
  - Streaming via async streaming API
  - Health check via model info
  - Models: claude-3-5-sonnet-20241022, claude-3-haiku-20240307, etc.

Required environment variable:
  ANTHROPIC_API_KEY=sk-ant-...
"""

from __future__ import annotations

import os
from typing import AsyncIterator, Dict, Any

from backend.providers.base import BaseLLMProvider
from backend.core.logging import get_logger

logger = get_logger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic provider for Claude models.

    Uses the official ``anthropic`` Python SDK (>=0.20).
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        try:
            import anthropic  # noqa: F401
        except ImportError:
            raise ImportError(
                "anthropic package is not installed. Run: pip install anthropic>=0.20"
            )

        api_key = config.get("api_key") or os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise ValueError(
                "Anthropic API key not found. "
                "Set ANTHROPIC_API_KEY in your environment or .env file."
            )

        import anthropic as _anthropic
        self._client = _anthropic.AsyncAnthropic(api_key=api_key)
        self.model_name: str = config.get("model", "claude-3-haiku-20240307")
        logger.info(f"AnthropicProvider initialised with model={self.model_name}")

    # ── BaseLLMProvider interface ──────────────────────────────────────────

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        response = await self._client.messages.create(
            model=self.model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text if response.content else ""
        tokens = (
            response.usage.input_tokens + response.usage.output_tokens
            if response.usage
            else 0
        )
        return {
            "text":        text,
            "model":       response.model,
            "tokens_used": tokens,
        }

    async def stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncIterator[str]:
        async with self._client.messages.stream(
            model=self.model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def health_check(self) -> bool:
        try:
            # A minimal test request
            await self._client.messages.create(
                model=self.model_name,
                max_tokens=1,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except Exception as exc:
            logger.warning(f"Anthropic health check failed: {exc}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider":   "anthropic",
            "model_name": self.model_name,
            "status":     "active",
        }


# Made with Bob
