"""
Abstract base class for LLM providers.
Defines the interface that all providers must implement.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any, Optional


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All provider implementations must inherit from this class and implement
    the required methods.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the provider with configuration.
        
        Args:
            config: Provider-specific configuration dictionary
        """
        self.config = config
        self.model_name = config.get("model_name")
        self.provider_name = self.__class__.__name__.replace("Provider", "").lower()
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate text from a prompt.
        
        Args:
            prompt: Input prompt text
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            str: Generated text
        """
        pass
    
    @abstractmethod
    async def stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream text generation from a prompt.
        
        Args:
            prompt: Input prompt text
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            **kwargs: Additional provider-specific parameters
            
        Yields:
            str: Generated text chunks
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is available and healthy.
        
        Returns:
            bool: True if provider is healthy, False otherwise
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            dict: Model information including name, parameters, etc.
        """
        pass
    
    def __repr__(self) -> str:
        """String representation of the provider."""
        return f"{self.__class__.__name__}(model={self.model_name})"

# Made with Bob
