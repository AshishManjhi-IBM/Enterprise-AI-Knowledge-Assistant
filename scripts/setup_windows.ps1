# Windows Setup Script for Enterprise Agentic RAG Platform

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Enterprise Agentic RAG Platform Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "⚠️  Warning: Not running as Administrator. Some operations may fail." -ForegroundColor Yellow
    Write-Host ""
}

# Step 1: Check Python
Write-Host "Step 1: Checking Python..." -ForegroundColor Green
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.12+ from https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

# Step 2: Check Podman
Write-Host "`nStep 2: Checking Podman..." -ForegroundColor Green
try {
    $podmanVersion = podman --version 2>&1
    Write-Host "✅ $podmanVersion" -ForegroundColor Green
    
    # Check if Podman machine exists
    Write-Host "Checking Podman machine status..." -ForegroundColor Yellow
    $machineList = podman machine list 2>&1
    
    if ($machineList -match "Currently active") {
        Write-Host "✅ Podman machine is running" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Podman machine not running. Attempting to start..." -ForegroundColor Yellow
        
        # Try to start existing machine
        $startResult = podman machine start 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Podman machine started" -ForegroundColor Green
        } else {
            Write-Host "⚠️  No Podman machine found. Initializing..." -ForegroundColor Yellow
            podman machine init
            podman machine start
            Write-Host "✅ Podman machine initialized and started" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "❌ Podman not found. Please install Podman Desktop from https://podman-desktop.io/downloads" -ForegroundColor Red
    Write-Host "   After installation, run: podman machine init && podman machine start" -ForegroundColor Yellow
    exit 1
}

# Step 3: Check Ollama
Write-Host "`nStep 3: Checking Ollama..." -ForegroundColor Green
try {
    $ollamaList = ollama list 2>&1
    Write-Host "✅ Ollama is installed" -ForegroundColor Green
    
    # Check for required models
    $requiredModels = @("qwen3:4b", "gemma3:4b", "phi4-mini")
    $missingModels = @()
    
    foreach ($model in $requiredModels) {
        if ($ollamaList -notmatch $model) {
            $missingModels += $model
        }
    }
    
    if ($missingModels.Count -gt 0) {
        Write-Host "⚠️  Missing models: $($missingModels -join ', ')" -ForegroundColor Yellow
        Write-Host "   Run these commands to download:" -ForegroundColor Yellow
        foreach ($model in $missingModels) {
            Write-Host "   ollama pull $model" -ForegroundColor Cyan
        }
    } else {
        Write-Host "✅ All required models are available" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Ollama not found. Please install from https://ollama.ai/download" -ForegroundColor Red
}

# Step 4: Install podman-compose
Write-Host "`nStep 4: Installing podman-compose..." -ForegroundColor Green
pip install podman-compose --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ podman-compose installed" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install podman-compose" -ForegroundColor Red
}

# Step 5: Create .env file
Write-Host "`nStep 5: Setting up environment..." -ForegroundColor Green
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "✅ Created .env file from template" -ForegroundColor Green
} else {
    Write-Host "✅ .env file already exists" -ForegroundColor Green
}

# Step 6: Install Python dependencies
Write-Host "`nStep 6: Installing Python dependencies..." -ForegroundColor Green
Write-Host "This may take a few minutes..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Python dependencies installed" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Step 7: Start Podman services
Write-Host "`nStep 7: Starting Podman services..." -ForegroundColor Green
Set-Location deploy\podman
podman-compose up -d
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ PostgreSQL and Redis containers started" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to start containers" -ForegroundColor Red
    Write-Host "   Try manually: cd deploy\podman && podman-compose up -d" -ForegroundColor Yellow
}
Set-Location ..\..

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Green
Write-Host "1. Start backend:  uvicorn backend.api.main:app --reload" -ForegroundColor Cyan
Write-Host "2. Start frontend: streamlit run frontend\streamlit\app.py" -ForegroundColor Cyan
Write-Host "3. Open http://localhost:8501" -ForegroundColor Cyan
Write-Host ""
Write-Host "To verify setup: python scripts\verify_setup.py" -ForegroundColor Yellow
Write-Host ""

# Made with Bob
