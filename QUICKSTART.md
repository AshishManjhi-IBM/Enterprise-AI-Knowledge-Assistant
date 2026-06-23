# Quick Start Guide

Get the Enterprise Agentic RAG Platform running in 5 minutes!

## Prerequisites Check

Before starting, ensure you have:

- ✅ Python 3.12+ installed
- ✅ Podman installed and running
- ✅ Ollama installed with models
- ✅ 32GB RAM available

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
# Start PostgreSQL and Redis
cd deploy/podman
podman-compose up -d

# Wait for services to be ready
# Check status
podman-compose ps
```

### 4. Verify Ollama (30 seconds)

```bash
# Check Ollama is running
ollama list

# Should show: qwen3:4b, gemma3:4b, phi4-mini
# If not, pull them:
ollama pull qwen3:4b
```

### 5. Start Backend (30 seconds)

```bash
# From project root
uvicorn backend.api.main:app --reload
```

Open http://localhost:8000/docs to see the API documentation.

### 6. Start Frontend (30 seconds)

```bash
# In a new terminal
cd frontend/streamlit
streamlit run app.py
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

### Check Frontend

1. Open http://localhost:8501
2. Sidebar should show "✅ Backend Connected"
3. All services (PostgreSQL, Redis, Ollama) should show green checkmarks

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

## Next Steps

Now that everything is running:

1. ✅ Explore the API at http://localhost:8000/docs
2. ✅ Check the Streamlit UI at http://localhost:8501
3. ✅ Review the [README.md](README.md) for detailed documentation
4. ✅ Check [docs/](docs/) for architecture and implementation guides
5. 🚀 Ready for Phase 1: Basic RAG implementation!

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
- 🏗️ [Architecture Guide](docs/phase-0-architecture.md)
- 🛠️ [Implementation Guide](docs/implementation-guide.md)
- 🗺️ [Project Roadmap](docs/project-roadmap.md)

---

**Estimated Setup Time**: 5 minutes  
**Status**: Phase 0-0.5 Complete ✅
