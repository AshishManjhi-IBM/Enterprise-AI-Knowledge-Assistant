"""
Azure OpenAI LLM Provider — Phase 10 Production Readiness.

Supports:
  - Azure OpenAI Service via openai>=1.0 AzureOpenAI client
  - Streaming
  - Health check via model list
  - Deployments: gpt-4o, gpt-4-turbo, gpt-35-turbo, etc.

Required environment variables:
  AZURE_OPENAI_API_KEY=...
  AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
  AZURE_OPENAI_DEPLOYMENT=gpt-4o           # deployment name (not model name)
  AZURE_OPENAI_API_VERSION=2024-02-01      # optional, defaults to 2024-02-01
"""

from __future__ import annotations

import os
from typing import AsyncIterator, Dict, Any

from backend.providers.base import BaseLLMProvider
from backend.core.logging import get_logger

logger = get_logger(__name__)


class AzureOpenAIProvider(BaseLLMProvider):
    """
    Azure OpenAI provider.

    Wraps the ``openai.AsyncAzureOpenAI`` client which is included in
    the ``openai`` Python SDK (>=1.0).
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        try:
            import openai  # noqa: F401
        except ImportError:
            raise ImportError(
                "openai package is not installed. Run: pip install openai>=1.10"
            )

        api_key  = config.get("api_key")  or os.environ.get("AZURE_OPENAI_API_KEY", "")
        endpoint = config.get("endpoint") or os.environ.get("AZURE_OPENAI_ENDPOINT", "")
        deployment = config.get("deployment") or os.environ.get("AZURE_OPENAI_DEPLOYMENT", "")
        api_version = config.get("api_version") or os.environ.get(
            "AZURE_OPENAI_API_VERSION", "2024-02-01"
        )

        if not api_key:
            raise ValueError(
                "Azure OpenAI API key not found. Set AZURE_OPENAI_API_KEY."
            )
        if not endpoint:
            raise ValueError(
                "Azure OpenAI endpoint not found. Set AZURE_OPENAI_ENDPOINT."
            )
        if not deployment:
            raise ValueError(
                "Azure OpenAI deployment name not found. Set AZURE_OPENAI_DEPLOYMENT."
            )

        import openai as _openai
        self._client = _openai.AsyncAzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version,
        )
        self.model_name: str = deployment   # Azure uses deployment name as model
        logger.info(
            f"AzureOpenAIProvider initialised: endpoint={endpoint} deployment={deployment}"
        )

    # ── BaseLLMProvider interface ──────────────────────────────────────────

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        response = await self._client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        text = response.choices[0].message.content or ""
        return {
            "text":        text,
            "model":       self.model_name,
            "tokens_used": response.usage.total_tokens if response.usage else 0,
        }

    async def stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncIterator[str]:
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
        try:
            models = await self._client.models.list()
            return bool(models.data)
        except Exception as exc:
            logger.warning(f"Azure OpenAI health check failed: {exc}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider":    "azure",
            "model_name":  self.model_name,
            "status":      "active",
        }


# Made with Bob
