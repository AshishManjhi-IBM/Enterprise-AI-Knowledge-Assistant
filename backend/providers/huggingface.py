"""
Hugging Face Transformers LLM Provider implementation.
"""

from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer
from typing import AsyncIterator, Dict, Any
import torch
from threading import Thread
from backend.providers.base import BaseLLMProvider
from backend.core.logging import get_logger

logger = get_logger(__name__)


class HuggingFaceProvider(BaseLLMProvider):
    """
    Hugging Face Transformers provider for local LLM inference.
    
    Supports models like Qwen/Qwen2.5-3B-Instruct, google/gemma-3-4b-it, etc.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Hugging Face provider.
        
        Args:
            config: Configuration dictionary with 'model_name' and optional 'cache_dir'
        """
        super().__init__(config)
        self.cache_dir = config.get("cache_dir")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        logger.info(f"Loading Hugging Face model {self.model_name} on {self.device}")
        logger.warning("Model loading may take several minutes on first run...")
        
        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir,
                trust_remote_code=True
            )
            
            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True
            )
            
            # Move to device if CPU
            if self.device == "cpu":
                self.model = self.model.to(self.device)
            
            logger.info(f"Hugging Face model loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load Hugging Face model: {e}")
            raise
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate text using Hugging Face model.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional generation parameters
            
        Returns:
            str: Generated text
        """
        try:
            logger.debug(f"Generating with Hugging Face model: {self.model_name}")
            
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=True if temperature > 0 else False,
                    pad_token_id=self.tokenizer.eos_token_id,
                    **kwargs
                )
            
            # Decode and remove prompt
            full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            generated_text = full_response[len(prompt):].strip()
            
            logger.debug(f"Generated {len(generated_text)} characters")
            return generated_text
            
        except Exception as e:
            logger.error(f"Hugging Face generation failed: {e}")
            raise
    
    async def stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream text generation using Hugging Face model.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional generation parameters
            
        Yields:
            str: Generated text chunks
        """
        try:
            logger.debug(f"Streaming with Hugging Face model: {self.model_name}")
            
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            streamer = TextIteratorStreamer(
                self.tokenizer,
                skip_special_tokens=True,
                skip_prompt=True
            )
            
            generation_kwargs = {
                **inputs,
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "do_sample": True if temperature > 0 else False,
                "streamer": streamer,
                "pad_token_id": self.tokenizer.eos_token_id,
                **kwargs
            }
            
            # Run generation in separate thread
            thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
            thread.start()
            
            # Yield tokens as they're generated
            for text in streamer:
                yield text
            
            thread.join()
            
        except Exception as e:
            logger.error(f"Hugging Face streaming failed: {e}")
            raise
    
    async def health_check(self) -> bool:
        """
        Check if Hugging Face model is loaded and ready.
        
        Returns:
            bool: True if healthy
        """
        try:
            is_healthy = (
                self.model is not None and
                self.tokenizer is not None and
                hasattr(self.model, 'generate')
            )
            
            if is_healthy:
                logger.debug(f"Hugging Face health check passed for {self.model_name}")
            else:
                logger.warning(f"Hugging Face model {self.model_name} not properly loaded")
            
            return is_healthy
            
        except Exception as e:
            logger.error(f"Hugging Face health check failed: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the Hugging Face model.
        
        Returns:
            dict: Model information
        """
        try:
            num_parameters = sum(p.numel() for p in self.model.parameters())
            
            return {
                "provider": "huggingface",
                "model_name": self.model_name,
                "device": self.device,
                "dtype": str(self.model.dtype),
                "parameters": num_parameters,
                "parameters_readable": f"{num_parameters / 1e9:.2f}B"
            }
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {
                "provider": "huggingface",
                "model_name": self.model_name,
                "device": self.device,
                "error": str(e)
            }

# Made with Bob
