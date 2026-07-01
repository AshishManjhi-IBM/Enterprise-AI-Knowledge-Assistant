"""
Google Gemini LLM Provider — Phase 10 Production Readiness.

Supports:
  - GenerativeAI API via google-generativeai SDK
  - Streaming via generate_content with stream=True
  - Health check via model list
  - Models: gemini-1.5-pro, gemini-1.5-flash, gemini-pro, etc.

Required environment variable:
  GOOGLE_API_KEY=...
"""

from __future__ import annotations

import os
from typing import AsyncIterator, Dict, Any

from backend.providers.base import BaseLLMProvider
from backend.core.logging import get_logger

logger = get_logger(__name__)


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini provider.

    Uses the official ``google-generativeai`` Python SDK.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        try:
            import google.generativeai  # noqa: F401
        except ImportError:
            raise ImportError(
                "google-generativeai package is not installed. "
                "Run: pip install google-generativeai>=0.5"
            )

        api_key = config.get("api_key") or os.environ.get("GOOGLE_API_KEY", "")
        if not api_key:
            raise ValueError(
                "Google API key not found. "
                "Set GOOGLE_API_KEY in your environment or .env file."
            )

        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model_name: str = config.get("model", "gemini-1.5-flash")
        self._model = genai.GenerativeModel(self.model_name)
        logger.info(f"GeminiProvider initialised with model={self.model_name}")

    # ── BaseLLMProvider interface ──────────────────────────────────────────

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        import asyncio
        import google.generativeai as genai

        generation_config = genai.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
        )
        # SDK generate_content is synchronous — run in executor
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self._model.generate_content(
                prompt, generation_config=generation_config
            ),
        )
        text = response.text if hasattr(response, "text") else ""
        return {
            "text":        text,
            "model":       self.model_name,
            "tokens_used": 0,  # Gemini SDK doesn't always expose token counts
        }

    async def stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncIterator[str]:
        import asyncio
        import google.generativeai as genai

        generation_config = genai.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
        )
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self._model.generate_content(
                prompt, generation_config=generation_config, stream=True
            ),
        )
        for chunk in response:
            if hasattr(chunk, "text") and chunk.text:
                yield chunk.text

    async def health_check(self) -> bool:
        try:
            import google.generativeai as genai
            import asyncio
            loop = asyncio.get_event_loop()
            models = await loop.run_in_executor(
                None, lambda: list(genai.list_models())
            )
            return bool(models)
        except Exception as exc:
            logger.warning(f"Gemini health check failed: {exc}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider":   "gemini",
            "model_name": self.model_name,
            "status":     "active",
        }


# Made with Bob
