"""
Azure OpenAI LLM Provider implementation (stub for Phase 10).
"""

from typing import AsyncIterator, Dict, Any
from backend.providers.base import BaseLLMProvider
from backend.core.logging import get_logger

logger = get_logger(__name__)


class AzureOpenAIProvider(BaseLLMProvider):
    """
    Azure OpenAI provider.
    
    TODO: Implement in Phase 10 - Production Readiness
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Azure OpenAI provider."""
        super().__init__(config)
        logger.warning("Azure OpenAI provider is not yet implemented (Phase 10)")
        raise NotImplementedError("Azure OpenAI provider will be implemented in Phase 10")
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate text using Azure OpenAI API."""
        raise NotImplementedError("Azure OpenAI provider will be implemented in Phase 10")
    
    async def stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream text generation using Azure OpenAI API."""
        raise NotImplementedError("Azure OpenAI provider will be implemented in Phase 10")
        yield ""
    
    async def health_check(self) -> bool:
        """Check Azure OpenAI API availability."""
        return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Azure OpenAI model information."""
        return {
            "provider": "azure_openai",
            "model_name": self.model_name,
            "status": "not_implemented"
        }

# Made with Bob
