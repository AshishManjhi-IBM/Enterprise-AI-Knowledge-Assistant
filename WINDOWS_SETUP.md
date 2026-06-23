# Windows Setup Guide

Quick setup guide specifically for Windows users.

## Prerequisites Installation

### 1. Install Python 3.12+

Download from: https://www.python.org/downloads/

### 2. Install Podman Desktop

Download from: https://podman-desktop.io/downloads

After installation, start Podman Desktop and ensure the Podman machine is running.

### 3. Install Ollama

Download from: https://ollama.ai/download

After installation, pull required models:

```powershell
ollama pull qwen3:4b
ollama pull gemma3:4b
ollama pull phi4-mini
```

## Project Setup

### 1. Install podman-compose

```powershell
pip install podman-compose
```

### 2. Create Virtual Environment

```powershell
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure Environment

```powershell
copy .env.example .env
```

## Starting Services

### Option 1: Using podman-compose (Recommended)

```powershell
cd deploy\podman
podman-compose up -d
```

### Option 2: Using Podman directly

```powershell
# Create network
podman network create rag_network

# Start PostgreSQL
podman run -d `
  --name rag_postgres `
  --network rag_network `
  -e POSTGRES_DB=rag_platform `
  -e POSTGRES_USER=rag_user `
  -e POSTGRES_PASSWORD=changeme `
  -p 5432:5432 `
  postgres:16

# Start Redis
podman run -d `
  --name rag_redis `
  --network rag_network `
  -p 6379:6379 `
  redis:7-alpine
```

### Verify Services

```powershell
podman ps
```

You should see both `rag_postgres` and `rag_redis` running.

## Starting the Application

### Terminal 1: Backend

```powershell
# Make sure virtual environment is activated
venv\Scripts\activate

# Start FastAPI
uvicorn backend.api.main:app --reload
```

### Terminal 2: Frontend

```powershell
# Make sure virtual environment is activated
venv\Scripts\activate

# Start Streamlit
cd frontend\streamlit
streamlit run app.py
```

## Verify Setup

Run the verification script:

```powershell
python scripts\verify_setup.py
```

## Access the Application

- **Frontend UI**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Troubleshooting

### Podman Machine Not Running

```powershell
# Start Podman machine
podman machine start

# Check status
podman machine list
```

### Port Already in Use

```powershell
# Check what's using the port
netstat -ano | findstr "8000"
netstat -ano | findstr "8501"
netstat -ano | findstr "5432"
netstat -ano | findstr "6379"

# Kill process by PID (replace <PID> with actual PID)
taskkill /PID <PID> /F
```

### Ollama Not Responding

```powershell
# Check Ollama service
ollama list

# Restart Ollama service (from Services or Task Manager)
```

### Import Errors

```powershell
# Ensure virtual environment is activated
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## Stopping Services

### Stop Application

- Press `Ctrl+C` in both terminal windows

### Stop Podman Services

Using podman-compose:

```powershell
cd deploy\podman
podman-compose down
```

Using Podman directly:

```powershell
podman stop rag_postgres rag_redis
podman rm rag_postgres rag_redis
```

## Common Windows Issues

### 1. Execution Policy Error

If you get "cannot be loaded because running scripts is disabled":

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2. Long Path Issues

Enable long paths in Windows:

```powershell
# Run as Administrator
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

### 3. Firewall Blocking Ports

Add firewall rules for ports 8000, 8501, 5432, 6379 if needed.

## Next Steps

Once everything is running:

1. Open http://localhost:8501
2. Check that all services show green checkmarks
3. Explore the API at http://localhost:8000/docs
4. Ready for Phase 1 development!

---

**Note**: This guide assumes you're using PowerShell. For Command Prompt, adjust commands accordingly.
