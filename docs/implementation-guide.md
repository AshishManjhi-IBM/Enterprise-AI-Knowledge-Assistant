# Implementation Guide - Phase 0 to 0.5

## Overview

This guide provides step-by-step instructions for implementing Phase 0 (Core Foundation), Phase 0.25 (Local AI Infrastructure), and Phase 0.5 (Provider Abstraction Layer).

## Prerequisites

- Python 3.12+
- Podman installed and running
- Ollama installed with models: qwen3:4b, gemma3:4b, phi4-mini
- Git
- 32GB RAM (recommended)
- Windows 11 / Linux / macOS

## Phase 0: Core Foundation

### Step 1: Project Structure Setup

Create the complete directory structure:

```bash
# Root directories
mkdir -p backend/{api,agents,core,providers,llm,ingestion,retrievers,rerankers,evaluators,memory,guardrails,tests}
mkdir -p backend/api/{routes,middleware}
mkdir -p backend/providers
mkdir -p backend/tests
mkdir -p frontend/streamlit/{components,utils}
mkdir -p data/{raw,processed,vectorstore}
mkdir -p deploy/podman/scripts
mkdir -p docs
mkdir -p scripts
mkdir -p logs
```

### Step 2: Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### Step 3: Dependencies File

Create `requirements.txt` with all necessary packages:

```txt
# Core Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0

# LangChain Ecosystem
langchain==0.1.0
langchain-community==0.0.20
langchain-core==0.1.10

# LLM Providers
ollama==0.1.6
transformers==4.36.2
torch==2.1.2
accelerate==0.25.0
sentencepiece==0.1.99

# Database
psycopg2-binary==2.9.9
redis==5.0.1
sqlalchemy==2.0.25

# Frontend
streamlit==1.30.0
requests==2.31.0

# Utilities
python-multipart==0.0.6
aiofiles==23.2.1

# Development
pytest==7.4.3
pytest-asyncio==0.23.3
pytest-cov==4.1.0
black==23.12.1
ruff==0.1.9
httpx==0.26.0

# Monitoring (optional for Phase 0)
# langsmith==0.0.77
# opentelemetry-api==1.22.0
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Step 4: Configuration Management

**File: `backend/core/settings.py`**

```python
from pydantic_settings import BaseSettings
from typing import Optional, Literal

class Settings(BaseSettings):
    # Application
    app_name: str = "Enterprise Agentic RAG Platform"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"

    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "rag_platform"
    db_user: str = "rag_user"
    db_password: str = "changeme"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_default_model: str = "qwen3:4b"

    # Hugging Face
    hf_home: str = "./models"
    hf_default_model: str = "Qwen/Qwen3-4B-Instruct"

    # LLM Provider
    default_provider: Literal["ollama", "huggingface", "openai", "anthropic", "gemini", "azure"] = "ollama"
    fallback_provider: Optional[str] = "huggingface"

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    log_max_size: int = 10485760  # 10MB
    log_backup_count: int = 5

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

**File: `backend/core/config.py`**

```python
from backend.core.settings import settings

def get_settings():
    return settings
```

### Step 5: Logging System

**File: `backend/core/logging.py`**

```python
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from backend.core.settings import settings

def setup_logging():
    # Create logs directory
    log_dir = Path(settings.log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger("rag_platform")
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        settings.log_file,
        maxBytes=settings.log_max_size,
        backupCount=settings.log_backup_count
    )
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_format)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

logger = setup_logging()
```

### Step 6: FastAPI Application

**File: `backend/api/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.settings import settings
from backend.core.logging import logger
from backend.api.routes import health, status

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(status.router, prefix=settings.api_prefix, tags=["status"])

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application")

@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }
```

**File: `backend/api/routes/health.py`**

```python
from fastapi import APIRouter
from backend.core.logging import logger

router = APIRouter()

@router.get("/health")
async def health_check():
    logger.debug("Health check requested")
    return {"status": "healthy"}
```

**File: `backend/api/routes/status.py`**

```python
from fastapi import APIRouter
from backend.core.settings import settings
from backend.core.logging import logger
import psycopg2
import redis
import requests

router = APIRouter()

@router.get("/status")
async def get_status():
    logger.info("Status check requested")

    status = {
        "application": "running",
        "version": settings.app_version,
        "environment": settings.environment,
        "services": {}
    }

    # Check PostgreSQL
    try:
        conn = psycopg2.connect(settings.database_url)
        conn.close()
        status["services"]["postgresql"] = "connected"
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        status["services"]["postgresql"] = "disconnected"

    # Check Redis
    try:
        r = redis.Redis.from_url(settings.redis_url)
        r.ping()
        status["services"]["redis"] = "connected"
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        status["services"]["redis"] = "disconnected"

    # Check Ollama
    try:
        response = requests.get(f"{settings.ollama_host}/api/tags", timeout=5)
        if response.status_code == 200:
            status["services"]["ollama"] = "connected"
        else:
            status["services"]["ollama"] = "disconnected"
    except Exception as e:
        logger.error(f"Ollama connection failed: {e}")
        status["services"]["ollama"] = "disconnected"

    return status
```

### Step 7: Environment Configuration

**File: `.env.example`**

```env
# Application
APP_NAME=Enterprise Agentic RAG Platform
APP_VERSION=0.1.0
ENVIRONMENT=development
DEBUG=true

# API
API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api/v1

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=rag_platform
DB_USER=rag_user
DB_PASSWORD=changeme

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_DEFAULT_MODEL=qwen3:4b

# Hugging Face
HF_HOME=./models
HF_DEFAULT_MODEL=Qwen/Qwen3-4B-Instruct

# LLM Provider
DEFAULT_PROVIDER=ollama
FALLBACK_PROVIDER=huggingface

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5
```

Copy to `.env` for local development:

```bash
cp .env.example .env
```

## Phase 0.25: Local AI Infrastructure

### Step 8: Podman Configuration

**File: `deploy/podman/podman-compose.yml`**

```yaml
version: '3.8'

services:
  postgres:
    image: docker.io/library/postgres:16
    container_name: rag_postgres
    environment:
      POSTGRES_DB: rag_platform
      POSTGRES_USER: rag_user
      POSTGRES_PASSWORD: changeme
    ports:
      - '5432:5432'
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ['CMD-SHELL', 'pg_isready -U rag_user']
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: docker.io/library/redis:7-alpine
    container_name: rag_redis
    ports:
      - '6379:6379'
    volumes:
      - redis_data:/data
    healthcheck:
      test: ['CMD', 'redis-cli', 'ping']
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

**File: `deploy/podman/scripts/start.sh`**

```bash
#!/bin/bash
cd "$(dirname "$0")/.."
podman-compose up -d
echo "Services started. Waiting for health checks..."
sleep 10
podman-compose ps
```

**File: `deploy/podman/scripts/stop.sh`**

```bash
#!/bin/bash
cd "$(dirname "$0")/.."
podman-compose down
echo "Services stopped."
```

Make scripts executable:

```bash
chmod +x deploy/podman/scripts/*.sh
```

### Step 9: Verify Ollama Setup

```bash
# Check Ollama is running
ollama list

# Pull required models if not present
ollama pull qwen3:4b
ollama pull gemma3:4b
ollama pull phi4-mini

# Test model
ollama run qwen3:4b "Hello, how are you?"
```

## Phase 0.5: Provider Abstraction Layer

### Step 10: Provider Interface

**File: `backend/providers/base.py`**

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any, Optional

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = config.get("model_name")

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate text from prompt"""
        pass

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream text generation"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is available"""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        pass
```

### Step 11: Ollama Provider

**File: `backend/providers/ollama.py`**

```python
import ollama
from typing import AsyncIterator, Dict, Any
from backend.providers.base import BaseLLMProvider
from backend.core.logging import logger

class OllamaProvider(BaseLLMProvider):
    """Ollama LLM Provider"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.host = config.get("host", "http://localhost:11434")
        self.client = ollama.Client(host=self.host)

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        try:
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    "num_predict": max_tokens,
                    "temperature": temperature,
                    **kwargs
                }
            )
            return response['response']
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
        try:
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
                yield chunk['response']
        except Exception as e:
            logger.error(f"Ollama streaming failed: {e}")
            raise

    async def health_check(self) -> bool:
        try:
            models = self.client.list()
            return any(m['name'].startswith(self.model_name) for m in models['models'])
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        try:
            return self.client.show(self.model_name)
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {}
```

### Step 12: Hugging Face Provider

**File: `backend/providers/huggingface.py`**

```python
from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer
from typing import AsyncIterator, Dict, Any
import torch
from threading import Thread
from backend.providers.base import BaseLLMProvider
from backend.core.logging import logger

class HuggingFaceProvider(BaseLLMProvider):
    """Hugging Face Transformers Provider"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading model {self.model_name} on {self.device}")

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else None
        )

        if self.device == "cpu":
            self.model = self.model.to(self.device)

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                **kwargs
            )

            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response[len(prompt):]  # Remove prompt from response
        except Exception as e:
            logger.error(f"HuggingFace generation failed: {e}")
            raise

    async def stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncIterator[str]:
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            streamer = TextIteratorStreamer(self.tokenizer, skip_special_tokens=True)

            generation_kwargs = {
                **inputs,
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "do_sample": True,
                "streamer": streamer,
                **kwargs
            }

            thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
            thread.start()

            for text in streamer:
                yield text

            thread.join()
        except Exception as e:
            logger.error(f"HuggingFace streaming failed: {e}")
            raise

    async def health_check(self) -> bool:
        try:
            return self.model is not None and self.tokenizer is not None
        except Exception as e:
            logger.error(f"HuggingFace health check failed: {e}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "device": self.device,
            "dtype": str(self.model.dtype),
            "parameters": sum(p.numel() for p in self.model.parameters())
        }
```

### Step 13: Cloud Provider Stubs

Create stub files for future cloud providers:

**Files to create:**

- `backend/providers/openai.py`
- `backend/providers/anthropic.py`
- `backend/providers/gemini.py`
- `backend/providers/azure.py`

Each with basic structure:

```python
from backend.providers.base import BaseLLMProvider
# TODO: Implement in Phase 10
```

### Step 14: LLM Factory

**File: `backend/providers/factory.py`**

```python
from typing import Dict, Any, Optional
from backend.providers.base import BaseLLMProvider
from backend.providers.ollama import OllamaProvider
from backend.providers.huggingface import HuggingFaceProvider
from backend.core.settings import settings
from backend.core.logging import logger

class LLMFactory:
    """Factory for creating LLM providers"""

    _providers = {
        "ollama": OllamaProvider,
        "huggingface": HuggingFaceProvider,
        # Cloud providers (Phase 10)
        # "openai": OpenAIProvider,
        # "anthropic": AnthropicProvider,
        # "gemini": GeminiProvider,
        # "azure": AzureOpenAIProvider,
    }

    @classmethod
    def create(
        cls,
        provider: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> BaseLLMProvider:
        """Create LLM provider instance"""

        provider = provider or settings.default_provider
        config = config or {}

        # Set default configuration
        if provider == "ollama":
            config.setdefault("host", settings.ollama_host)
            config.setdefault("model_name", settings.ollama_default_model)
        elif provider == "huggingface":
            config.setdefault("model_name", settings.hf_default_model)

        # Get provider class
        provider_class = cls._providers.get(provider)
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider}")

        try:
            logger.info(f"Creating {provider} provider")
            return provider_class(config)
        except Exception as e:
            logger.error(f"Failed to create {provider} provider: {e}")

            # Try fallback provider
            if settings.fallback_provider and settings.fallback_provider != provider:
                logger.info(f"Trying fallback provider: {settings.fallback_provider}")
                return cls.create(provider=settings.fallback_provider, config=config)

            raise

    @classmethod
    def list_providers(cls) -> list:
        """List available providers"""
        return list(cls._providers.keys())
```

## Testing

### Step 15: Create Test Files

**File: `backend/tests/test_providers.py`**

```python
import pytest
from backend.providers.factory import LLMFactory

@pytest.mark.asyncio
async def test_ollama_provider():
    provider = LLMFactory.create("ollama")
    assert await provider.health_check()

    response = await provider.generate("Hello, world!")
    assert isinstance(response, str)
    assert len(response) > 0

@pytest.mark.asyncio
async def test_huggingface_provider():
    provider = LLMFactory.create("huggingface")
    assert await provider.health_check()

    # Note: This test may be slow on CPU
    response = await provider.generate("Hello, world!", max_tokens=50)
    assert isinstance(response, str)

def test_factory_list_providers():
    providers = LLMFactory.list_providers()
    assert "ollama" in providers
    assert "huggingface" in providers
```

Run tests:

```bash
pytest backend/tests/ -v
```

## Streamlit Frontend

### Step 16: Streamlit Application

**File: `frontend/streamlit/app.py`**

```python
import streamlit as st
import requests
from backend.core.settings import settings

st.set_page_config(
    page_title=settings.app_name,
    page_icon="🤖",
    layout="wide"
)

st.title(f"🤖 {settings.app_name}")
st.caption(f"Version {settings.app_version}")

# Sidebar
with st.sidebar:
    st.header("Configuration")

    # Provider selection
    provider = st.selectbox(
        "LLM Provider",
        ["ollama", "huggingface"],
        index=0
    )

    # Model selection
    if provider == "ollama":
        model = st.selectbox(
            "Model",
            ["qwen3:4b", "gemma3:4b", "phi4-mini"],
            index=0
        )
    else:
        model = st.text_input("Model", value=settings.hf_default_model)

    # Temperature
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)

    # Max tokens
    max_tokens = st.slider("Max Tokens", 50, 2048, 512, 50)

    st.divider()

    # Status check
    if st.button("Check Status"):
        try:
            response = requests.get(f"http://{settings.api_host}:{settings.api_port}/api/v1/status")
            if response.status_code == 200:
                status = response.json()
                st.success("✅ Backend Connected")

                for service, state in status["services"].items():
                    if state == "connected":
                        st.success(f"✅ {service.title()}")
                    else:
                        st.error(f"❌ {service.title()}")
            else:
                st.error("❌ Backend Error")
        except Exception as e:
            st.error(f"❌ Connection Failed: {e}")

# Main area
st.header("Chat Interface")
st.info("🚧 Chat functionality will be implemented in Phase 1")

# Placeholder for chat
prompt = st.text_area("Enter your message:", height=100)

if st.button("Send", type="primary"):
    if prompt:
        st.info("Chat endpoint will be available in Phase 1")
    else:
        st.warning("Please enter a message")
```

## Deployment Scripts

### Step 17: Development Scripts

**File: `scripts/start_dev.sh`**

```bash
#!/bin/bash

echo "Starting Enterprise Agentic RAG Platform..."

# Start Podman services
echo "Starting Podman services..."
cd deploy/podman
podman-compose up -d
cd ../..

# Wait for services
echo "Waiting for services to be ready..."
sleep 10

# Start FastAPI backend
echo "Starting FastAPI backend..."
cd backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend
sleep 5

# Start Streamlit frontend
echo "Starting Streamlit frontend..."
cd frontend/streamlit
streamlit run app.py &
FRONTEND_PID=$!
cd ../..

echo "All services started!"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Access points:"
echo "- Backend API: http://localhost:8000"
echo "- API Docs: http://localhost:8000/docs"
echo "- Frontend: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "kill $BACKEND_PID $FRONTEND_PID; cd deploy/podman; podman-compose down; exit" INT
wait
```

Make executable:

```bash
chmod +x scripts/start_dev.sh
```

## Validation Checklist

### Phase 0 Validation

- [ ] FastAPI server starts without errors
- [ ] Health endpoint responds: `curl http://localhost:8000/health`
- [ ] API documentation accessible: http://localhost:8000/docs
- [ ] Logging system creates log files
- [ ] Configuration loads from .env

### Phase 0.25 Validation

- [ ] PostgreSQL container running: `podman ps`
- [ ] Redis container running: `podman ps`
- [ ] Can connect to PostgreSQL
- [ ] Can connect to Redis
- [ ] Ollama models available: `ollama list`

### Phase 0.5 Validation

- [ ] Ollama provider health check passes
- [ ] Hugging Face provider loads model
- [ ] Factory creates providers successfully
- [ ] Fallback mechanism works
- [ ] Status endpoint shows all services

## Next Steps

After completing Phase 0-0.5:

1. Implement Phase 1: Basic RAG
2. Add document ingestion
3. Implement vector search
4. Create chat endpoints

## Troubleshooting

### Common Issues

**Issue**: Podman services won't start

- Check Podman is running: `podman info`
- Check port conflicts: `netstat -an | grep 5432`

**Issue**: Ollama connection fails

- Verify Ollama is running: `ollama list`
- Check host configuration in .env

**Issue**: HuggingFace model loading slow

- Expected on CPU, be patient
- Consider using smaller models for testing

**Issue**: Import errors

- Ensure virtual environment is activated
- Reinstall requirements: `pip install -r requirements.txt`

## Support

For issues or questions:

1. Check logs in `logs/app.log`
2. Review API documentation at `/docs`
3. Verify all services are running
