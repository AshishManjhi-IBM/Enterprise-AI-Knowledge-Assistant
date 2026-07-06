# 🚀 Quick Start - Enterprise Agentic RAG Platform

## You're Almost Ready!

Dependencies are being installed. Once complete, follow these steps:

## Step 1: Start Backend (Terminal 1)

```bash
uvicorn backend.api.main:app --reload
```

**Expected Output:**

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

## Step 2: Start Frontend (Terminal 2)

Open a **new terminal** and run:

```bash
streamlit run frontend\streamlit\app.py
```

**Expected Output:**

```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

## Step 3: Access the Application

### Frontend (Main UI)

Open your browser to: **http://localhost:8501**

You should see:

- ✅ Backend Connected (green checkmark)
- ✅ PostgreSQL Connected
- ✅ Redis Connected
- ✅ Ollama Connected

### API Documentation

Open: **http://localhost:8000/docs**

Interactive API documentation with all endpoints.

### Health Check

Test: **http://localhost:8000/health**

Should return: `{"status":"healthy","service":"rag-platform"}`

## What You Can Do Now

### 1. Test Ollama Provider

In the Streamlit UI:

- Select "ollama" as provider
- Choose "qwen3:4b" model
- Adjust temperature and max tokens
- (Chat will be available in Phase 1)

### 2. Explore API

Visit http://localhost:8000/docs and try:

- `GET /health` - Health check
- `GET /api/v1/status` - Detailed status
- `GET /api/v1/status/providers` - Available providers

### 3. Check Logs

```bash
# View application logs
type logs\app.log

# Or tail logs (PowerShell)
Get-Content logs\app.log -Wait -Tail 50
```

## Troubleshooting

### Backend Won't Start

```bash
# Check if port 8000 is in use
netstat -ano | findstr "8000"

# If in use, kill the process or use different port
uvicorn backend.api.main:app --reload --port 8001
```

### Frontend Won't Start

```bash
# Check if port 8501 is in use
netstat -ano | findstr "8501"

# If in use, Streamlit will auto-select next available port
```

### Import Errors

```bash
# Ensure all dependencies are installed
pip install -r requirements.txt

# Check installation
pip list | findstr fastapi
pip list | findstr streamlit
```

## Next Steps

Once both servers are running:

1. ✅ **Verify Status** - Check all services are green in UI
2. ✅ **Test API** - Try endpoints in /docs
3. ✅ **Explore Code** - Review backend/providers/
4. 🚀 **Ready for Phase 1** - Document ingestion and RAG!

## Quick Commands Reference

```bash
# Start backend
uvicorn backend.api.main:app --reload

# Start frontend
streamlit run frontend\streamlit\app.py

# Check status
curl http://localhost:8000/health

# View logs
type logs\app.log

# Stop services
# Press Ctrl+C in each terminal
```

## Documentation

- **[README.md](README.md)** - Full documentation
- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute guide
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Fix issues
- **[docs/](docs/)** - Architecture & guides

## Support

Everything working? Great! 🎉

Having issues? Check:

1. [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. [WINDOWS_SETUP.md](WINDOWS_SETUP.md)
3. Logs in `logs/app.log`

---

**Status**: Phase 0-0.5 Complete ✅  
**Ready**: Yes! Start the servers above  
**Next**: Phase 1 - Basic RAG
