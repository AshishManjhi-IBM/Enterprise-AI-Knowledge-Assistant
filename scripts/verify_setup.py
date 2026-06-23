"""
Setup verification script for Enterprise Agentic RAG Platform.
Checks all components and reports status.
"""

import sys
import subprocess
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_status(component, status, message=""):
    """Print component status."""
    symbol = "✅" if status else "❌"
    print(f"{symbol} {component:30} {message}")

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    is_valid = version.major == 3 and version.minor >= 11
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    print_status("Python Version", is_valid, f"({version_str})")
    return is_valid

def check_imports():
    """Check if required packages are installed."""
    packages = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "streamlit": "Streamlit",
        "ollama": "Ollama",
        "transformers": "Transformers",
        "torch": "PyTorch",
        "psycopg2": "PostgreSQL Driver",
        "redis": "Redis",
        "pydantic": "Pydantic",
        "requests": "Requests"
    }
    
    all_ok = True
    for package, name in packages.items():
        try:
            __import__(package)
            print_status(name, True, "installed")
        except ImportError:
            print_status(name, False, "NOT INSTALLED")
            all_ok = False
    
    return all_ok

def check_podman():
    """Check if Podman is available."""
    try:
        result = subprocess.run(
            ["podman", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        is_ok = result.returncode == 0
        version = result.stdout.strip() if is_ok else ""
        print_status("Podman", is_ok, version)
        return is_ok
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print_status("Podman", False, "NOT FOUND")
        return False

def check_ollama():
    """Check if Ollama is available."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        is_ok = result.returncode == 0
        if is_ok:
            models = [line.split()[0] for line in result.stdout.strip().split('\n')[1:]]
            required = ["qwen3:4b", "gemma3:4b", "phi4-mini"]
            has_models = any(any(req in model for req in required) for model in models)
            print_status("Ollama", True, f"({len(models)} models)")
            if not has_models:
                print("  ⚠️  Recommended models not found. Run:")
                print("     ollama pull qwen3:4b")
                print("     ollama pull gemma3:4b")
                print("     ollama pull phi4-mini")
        else:
            print_status("Ollama", False, "NOT RUNNING")
        return is_ok
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print_status("Ollama", False, "NOT FOUND")
        return False

def check_file_structure():
    """Check if project structure is correct."""
    required_paths = [
        "backend/api/main.py",
        "backend/core/settings.py",
        "backend/providers/factory.py",
        "frontend/streamlit/app.py",
        "deploy/podman/podman-compose.yml",
        "requirements.txt",
        ".env.example"
    ]
    
    all_ok = True
    for path in required_paths:
        exists = Path(path).exists()
        if not exists:
            print_status(path, False, "MISSING")
            all_ok = False
    
    if all_ok:
        print_status("Project Structure", True, "all files present")
    
    return all_ok

def check_env_file():
    """Check if .env file exists."""
    env_exists = Path(".env").exists()
    if not env_exists:
        print_status(".env file", False, "NOT FOUND")
        print("  ℹ️  Run: cp .env.example .env")
    else:
        print_status(".env file", True, "found")
    return env_exists

def check_services():
    """Check if Podman services are running."""
    try:
        result = subprocess.run(
            ["podman", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            containers = result.stdout.strip().split('\n')
            postgres_running = any("postgres" in c for c in containers)
            redis_running = any("redis" in c for c in containers)
            
            print_status("PostgreSQL Container", postgres_running)
            print_status("Redis Container", redis_running)
            
            if not (postgres_running and redis_running):
                print("  ℹ️  Start services: cd deploy/podman && podman-compose up -d")
            
            return postgres_running and redis_running
        else:
            print_status("Podman Services", False, "Cannot check")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print_status("Podman Services", False, "Cannot check")
        return False

def main():
    """Run all verification checks."""
    print_header("Enterprise Agentic RAG Platform - Setup Verification")
    
    print_header("1. System Requirements")
    python_ok = check_python_version()
    podman_ok = check_podman()
    ollama_ok = check_ollama()
    
    print_header("2. Python Packages")
    packages_ok = check_imports()
    
    print_header("3. Project Structure")
    structure_ok = check_file_structure()
    env_ok = check_env_file()
    
    print_header("4. Services")
    services_ok = check_services()
    
    print_header("Summary")
    
    all_checks = [
        ("Python 3.12+", python_ok),
        ("Podman", podman_ok),
        ("Ollama", ollama_ok),
        ("Python Packages", packages_ok),
        ("Project Structure", structure_ok),
        (".env Configuration", env_ok),
        ("Podman Services", services_ok)
    ]
    
    passed = sum(1 for _, ok in all_checks if ok)
    total = len(all_checks)
    
    print(f"\nPassed: {passed}/{total} checks")
    
    if passed == total:
        print("\n🎉 All checks passed! You're ready to start the application.")
        print("\nNext steps:")
        print("  1. Start backend:  uvicorn backend.api.main:app --reload")
        print("  2. Start frontend: streamlit run frontend/streamlit/app.py")
        print("  3. Open http://localhost:8501")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        print("\nFor help, see:")
        print("  - README.md")
        print("  - QUICKSTART.md")
        print("  - docs/implementation-guide.md")
        return 1

if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
