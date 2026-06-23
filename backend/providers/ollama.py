"""
Ollama LLM Provider implementation.
"""

import ollama
from typing import AsyncIterator, Dict, Any
from backend.providers.base import BaseLLMProvider
from backend.core.logging import get_logger

logger = get_logger(__name__)


class OllamaProvider(BaseLLMProvider):
    """
    Ollama provider for local LLM inference.
    
    Supports models like qwen3:4b, gemma3:4b, phi4-mini, etc.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Ollama provider.
        
        Args:
            config: Configuration dictionary with 'host' and 'model_name'
        """
        super().__init__(config)
        self.host = config.get("host", "http://localhost:11434")
        self.timeout = config.get("timeout", 120)
        
        try:
            self.client = ollama.Client(host=self.host)
            logger.info(f"Ollama provider initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {e}")
            raise
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate text using Ollama.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional Ollama options
            
        Returns:
            str: Generated text
        """
        try:
            logger.debug(f"Generating with Ollama model: {self.model_name}")
            
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    "num_predict": max_tokens,
                    "temperature": temperature,
                    **kwargs
                }
            )
            
            generated_text = response.get('response', '')
            logger.debug(f"Generated {len(generated_text)} characters")
            return generated_text
            
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise
    
    async def stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream text generation using Ollama.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional Ollama options
            
        Yields:
            str: Generated text chunks
        """
        try:
            logger.debug(f"Streaming with Ollama model: {self.model_name}")
            
            stream = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                stream=True,
                options={
                    "num_predict": max_tokens,
                    "temperature": temperature,
                    **kwargs
                }
            )
            
            for chunk in stream:
                if 'response' in chunk:
                    yield chunk['response']
                    
        except Exception as e:
            logger.error(f"Ollama streaming failed: {e}")
            raise
    
    async def health_check(self) -> bool:
        """
        Check if Ollama is available and model is loaded.
        
        Returns:
            bool: True if healthy
        """
        try:
            models = self.client.list()
            available_models = [m['name'] for m in models.get('models', [])]
            
            # Check if our model is available
            model_available = any(
                self.model_name in model or model.startswith(self.model_name)
                for model in available_models
            )
            
            if model_available:
                logger.debug(f"Ollama health check passed for {self.model_name}")
                return True
            else:
                logger.warning(f"Model {self.model_name} not found in Ollama")
                return False
                
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the Ollama model.
        
        Returns:
            dict: Model information
        """
        try:
            info = self.client.show(self.model_name)
            return {
                "provider": "ollama",
                "model_name": self.model_name,
                "host": self.host,
                "details": info
            }
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {
                "provider": "ollama",
                "model_name": self.model_name,
                "host": self.host,
                "error": str(e)
            }

# Made with Bob
