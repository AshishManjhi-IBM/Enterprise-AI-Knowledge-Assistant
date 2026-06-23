# Troubleshooting Guide

## Podman Machine Issues on Windows

### Issue: "machine did not transition into running state"

This is a common issue with Podman on Windows. Here are solutions:

### Solution 1: Reset Podman Machine

```powershell
# Stop and remove existing machine
podman machine stop
podman machine rm podman-machine-default

# Create new machine with more resources
podman machine init --cpus 4 --memory 8192 --disk-size 50

# Start the machine
podman machine start
```

### Solution 2: Use Podman Desktop

1. Open **Podman Desktop** application
2. Go to **Settings** → **Resources**
3. Click **Start** on the Podman machine
4. Wait for it to fully start (may take 2-3 minutes)

### Solution 3: Use Docker Desktop Instead

If Podman continues to have issues, you can use Docker Desktop as an alternative:

#### Install Docker Desktop

1. Download from: https://www.docker.com/products/docker-desktop/
2. Install and start Docker Desktop
3. Ensure WSL 2 backend is enabled

#### Use Docker Compose Instead

```powershell
cd deploy\podman

# Use docker-compose instead of podman-compose
docker-compose up -d

# Check status
docker ps
```

The `podman-compose.yml` file is compatible with Docker Compose.

### Solution 4: Run Services Manually with Podman

If podman-compose doesn't work, run containers individually:

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
  docker.io/library/postgres:16

# Start Redis
podman run -d `
  --name rag_redis `
  --network rag_network `
  -p 6379:6379 `
  docker.io/library/redis:7-alpine

# Verify
podman ps
```

## Alternative: Skip Podman/Docker for Now

You can run the application without containers by installing PostgreSQL and Redis locally:

### Install PostgreSQL Locally

1. Download from: https://www.postgresql.org/download/windows/
2. Install with default settings
3. Create database:

```sql
CREATE DATABASE rag_platform;
CREATE USER rag_user WITH PASSWORD 'changeme';
GRANT ALL PRIVILEGES ON DATABASE rag_platform TO rag_user;
```

### Install Redis Locally

1. Download from: https://github.com/microsoftarchive/redis/releases
2. Install and start Redis service
3. Or use Redis in WSL:

```bash
wsl
sudo apt-get install redis-server
sudo service redis-server start
```

### Update .env File

```env
DB_HOST=localhost
DB_PORT=5432
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Common Issues

### 1. Port Already in Use

**Check what's using the port:**

```powershell
netstat -ano | findstr "5432"
netstat -ano | findstr "6379"
```

**Kill the process:**

```powershell
taskkill /PID <PID> /F
```

### 2. WSL Issues

**Reset WSL:**

```powershell
wsl --shutdown
wsl --unregister podman-machine-default
```

**Update WSL:**

```powershell
wsl --update
```

### 3. Hyper-V Issues

Ensure Hyper-V is enabled:

```powershell
# Run as Administrator
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
```

### 4. Firewall Blocking

Add firewall rules:

```powershell
# Run as Administrator
New-NetFirewallRule -DisplayName "PostgreSQL" -Direction Inbound -LocalPort 5432 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Redis" -Direction Inbound -LocalPort 6379 -Protocol TCP -Action Allow
```

## Testing Without Database

You can test the backend without PostgreSQL/Redis by commenting out the database checks in `backend/api/routes/status.py`:

```python
# Temporarily comment out PostgreSQL and Redis checks
# Just test Ollama and the API itself
```

## Recommended Approach for Windows

For the smoothest experience on Windows:

1. **Use Docker Desktop** instead of Podman
2. **Or** install PostgreSQL and Redis locally
3. **Or** skip database setup for now and focus on testing the LLM providers

The core functionality (Ollama and Hugging Face providers) works without databases.

## Quick Test Without Databases

1. Start only the backend:

```powershell
uvicorn backend.api.main:app --reload
```

2. Test the health endpoint:

```powershell
curl http://localhost:8000/health
```

3. Test Ollama provider directly in Python:

```python
from backend.providers.factory import LLMFactory

# Create Ollama provider
provider = LLMFactory.create("ollama")

# Test generation
import asyncio
response = asyncio.run(provider.generate("Hello, how are you?"))
print(response)
```

## Getting Help

If issues persist:

1. Check Podman Desktop logs
2. Check Windows Event Viewer
3. Try Docker Desktop as alternative
4. Run without containers using local services

## Success Without Containers

The application can run successfully with:

- ✅ Ollama (for LLM)
- ✅ Local PostgreSQL (optional)
- ✅ Local Redis (optional)
- ✅ FastAPI backend
- ✅ Streamlit frontend

Containers are convenient but not required for development!
