"""
LLM Provider Factory with dynamic provider selection and fallback mechanism.
"""

from typing import Dict, Any, Optional
from backend.providers.base import BaseLLMProvider
from backend.providers.ollama import OllamaProvider
from backend.providers.huggingface import HuggingFaceProvider
from backend.providers.openai import OpenAIProvider
from backend.providers.anthropic import AnthropicProvider
from backend.providers.gemini import GeminiProvider
from backend.providers.azure import AzureOpenAIProvider
from backend.core.settings import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)


class LLMFactory:
    """
    Factory for creating LLM provider instances.
    
    Implements the Factory pattern with automatic fallback mechanism.
    """
    
    # Registry of available providers
    _providers = {
        "ollama": OllamaProvider,
        "huggingface": HuggingFaceProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "gemini": GeminiProvider,
        "azure": AzureOpenAIProvider,
    }
    
    @classmethod
    def create(
        cls,
        provider: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> BaseLLMProvider:
        """
        Create an LLM provider instance.
        
        Args:
            provider: Provider name (ollama, huggingface, etc.)
            config: Provider-specific configuration
            
        Returns:
            BaseLLMProvider: Configured provider instance
            
        Raises:
            ValueError: If provider is unknown
            RuntimeError: If provider creation fails and no fallback available
        """
        provider = provider or settings.default_provider
        config = config or {}
        
        # Set default configuration based on provider
        config = cls._get_default_config(provider, config)
        
        # Get provider class
        provider_class = cls._providers.get(provider)
        if not provider_class:
            available = ", ".join(cls._providers.keys())
            raise ValueError(
                f"Unknown provider: {provider}. Available providers: {available}"
            )
        
        # Try to create provider
        try:
            logger.info(f"Creating {provider} provider with model: {config.get('model_name')}")
            instance = provider_class(config)
            logger.info(f"Successfully created {provider} provider")
            return instance
            
        except NotImplementedError as e:
            # Provider not yet implemented
            logger.warning(f"{provider} provider not implemented: {e}")
            
            # Try fallback
            if settings.fallback_provider and settings.fallback_provider != provider:
                logger.info(f"Attempting fallback to {settings.fallback_provider}")
                return cls.create(provider=settings.fallback_provider, config=config)
            
            raise RuntimeError(
                f"Provider {provider} not implemented and no fallback available"
            )
            
        except Exception as e:
            # Provider creation failed
            logger.error(f"Failed to create {provider} provider: {e}")
            
            # Try fallback
            if settings.fallback_provider and settings.fallback_provider != provider:
                logger.info(f"Attempting fallback to {settings.fallback_provider}")
                try:
                    return cls.create(provider=settings.fallback_provider, config=config)
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
                    raise RuntimeError(
                        f"Both primary ({provider}) and fallback ({settings.fallback_provider}) "
                        f"providers failed"
                    )
            
            raise RuntimeError(f"Failed to create {provider} provider: {e}")
    
    @classmethod
    def _get_default_config(
        cls,
        provider: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get default configuration for a provider.
        
        Args:
            provider: Provider name
            config: User-provided configuration
            
        Returns:
            dict: Merged configuration with defaults
        """
        defaults = {}
        
        if provider == "ollama":
            defaults = {
                "host": settings.ollama_host,
                "model_name": settings.ollama_default_model,
                "timeout": settings.ollama_timeout
            }
        elif provider == "huggingface":
            defaults = {
                "model_name": settings.hf_default_model,
                "cache_dir": settings.hf_cache_dir
            }
        elif provider in ["openai", "anthropic", "gemini", "azure"]:
            defaults = {
                "model_name": config.get("model_name", "gpt-4")
            }
        
        # Merge with user config (user config takes precedence)
        return {**defaults, **config}
    
    @classmethod
    def list_providers(cls) -> list[str]:
        """
        List all available provider names.
        
        Returns:
            list: Provider names
        """
        return list(cls._providers.keys())
    
    @classmethod
    def get_provider_info(cls, provider: str) -> Dict[str, Any]:
        """
        Get information about a provider.
        
        Args:
            provider: Provider name
            
        Returns:
            dict: Provider information
        """
        provider_class = cls._providers.get(provider)
        if not provider_class:
            return {"error": f"Unknown provider: {provider}"}
        
        return {
            "name": provider,
            "class": provider_class.__name__,
            "implemented": provider not in ["openai", "anthropic", "gemini", "azure"]
        }
    
    @classmethod
    async def health_check_all(cls) -> Dict[str, bool]:
        """
        Check health of all implemented providers.
        
        Returns:
            dict: Provider name to health status mapping
        """
        health_status = {}
        
        for provider_name in ["ollama", "huggingface"]:
            try:
                provider = cls.create(provider=provider_name)
                health_status[provider_name] = await provider.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {provider_name}: {e}")
                health_status[provider_name] = False
        
        return health_status

# Made with Bob
