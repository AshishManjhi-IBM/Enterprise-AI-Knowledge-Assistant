#!/bin/bash
# Stop Podman services for RAG Platform

set -e

echo "🛑 Stopping Enterprise Agentic RAG Platform Services..."
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PODMAN_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PODMAN_DIR"

# Stop services
echo "📦 Stopping PostgreSQL and Redis containers..."
podman-compose down

echo ""
echo "✅ Services stopped successfully!"
echo ""
echo "To start services again:"
echo "  ./scripts/start.sh"

# Made with Bob
