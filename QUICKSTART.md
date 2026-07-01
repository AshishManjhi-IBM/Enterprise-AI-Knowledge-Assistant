# Quick Start Guide

Get the Enterprise Agentic RAG Platform running in 5 minutes!

## Prerequisites Check

Before starting, ensure you have:

- ✅ Python 3.9+ installed
- ✅ Ollama installed and running
- ✅ 8 GB RAM minimum (16 GB recommended)

## Step-by-Step Setup

### 1. Install Dependencies (2 minutes)

```bash
# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 2. Configure Environment (30 seconds)

```bash
# Copy environment template
cp .env.example .env

# Default values work for local development
# Edit .env only if you need custom settings
```

### 3. Start Services (1 minute)

```bash
# Start PostgreSQL and Redis (optional but recommended)
cd deploy/podman
podman-compose up -d

# Check status
podman-compose ps
```

> **Note:** Redis is optional. Without it, conversation memory falls back to in-process storage (no persistence across restarts).

### 4. Verify Ollama (30 seconds)

```bash
# Check Ollama is running
ollama list

# Should show: qwen3:4b, gemma3:4b, or similar
# If not, pull a model:
ollama pull qwen3:4b
```

### 5. Start Backend (30 seconds)

```bash
# From project root
uvicorn backend.api.main:app --reload
```

Open http://localhost:8000/docs to see the full API documentation.

### 6. Start Frontend (30 seconds)

```bash
# In a new terminal, from project root
streamlit run frontend/streamlit/app.py
```

Open http://localhost:8501 to access the UI.

## Verify Everything Works

### Check Backend Health

```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","service":"rag-platform"}
```

### Check Service Status

```bash
curl http://localhost:8000/api/v1/status
# Should show all services as "connected"
```

### Check Agent Health

```bash
curl http://localhost:8000/api/v1/agent/health
# Should return: {"status":"healthy","graph":"compiled",...}
```

### Check Frontend

1. Open http://localhost:8501
2. Sidebar should show "✅ Backend Connected"
3. All services (PostgreSQL, Redis, Ollama) should show green checkmarks
4. Four pages available: 📄 Documents, 💬 Chat, 🤖 Agent, 📊 Evaluate

## Common Issues

### Port Already in Use

```bash
# Check what's using the port
netstat -an | findstr "8000 8501 5432 6379"  # Windows
lsof -i :8000 -i :8501 -i :5432 -i :6379    # Linux/Mac

# Kill the process or use different ports in .env
```

### Podman Services Won't Start

```bash
# Check Podman is running
podman info

# Restart services
cd deploy/podman
podman-compose down
podman-compose up -d
```

### Import Errors

```bash
# Make sure virtual environment is activated
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Agent Responses Are Slow

The agent runs 3–6 LLM calls per query (routing, optional rewrite, grading, generation, grounding). On CPU-only Ollama this can take 2–5 minutes. Speed up with:

```bash
# Disable document grading and grounding check (faster, less accurate)
# Add to .env:
AGENT_ENABLE_DOCUMENT_GRADING=false
AGENT_ENABLE_GROUNDING_CHECK=false
AGENT_MAX_REWRITES=0
```

## Next Steps

Now that everything is running:

1. ✅ **Upload documents** via the 📄 Documents page
2. ✅ **Chat with RAG** via the 💬 Chat page (streaming, memory, guardrails)
3. ✅ **Try agentic mode** via the 🤖 Agent page (LangGraph routing, grading, grounding)
4. ✅ **Evaluate quality** via the 📊 Evaluate page (RAGAS metrics)
5. ✅ Explore the full API at http://localhost:8000/docs

## Stopping Services

```bash
# Stop backend: Ctrl+C in terminal
# Stop frontend: Ctrl+C in terminal

# Stop Podman services
cd deploy/podman
podman-compose down
```

## Getting Help

- 📚 [Full Documentation](README.md)
- 🤖 [Phase 9 Agentic RAG Guide](docs/PHASE_9_IMPLEMENTATION.md)
- 🗺️ [Project Roadmap](docs/project-roadmap.md)

---

**Estimated Setup Time**: 5 minutes
**Status**: Phase 9 Complete ✅ — Phases 0–9 all live
