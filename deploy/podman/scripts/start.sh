#!/bin/bash
# Start Podman services for RAG Platform

set -e

echo "🚀 Starting Enterprise Agentic RAG Platform Services..."
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PODMAN_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PODMAN_DIR"

# Check if podman-compose is available
if ! command -v podman-compose &> /dev/null; then
    echo "❌ podman-compose not found. Please install it first."
    echo "   pip install podman-compose"
    exit 1
fi

# Start services
echo "📦 Starting PostgreSQL and Redis containers..."
podman-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
podman-compose ps

echo ""
echo "✅ Services started successfully!"
echo ""
echo "Service URLs:"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo ""
echo "To view logs:"
echo "  podman-compose logs -f"
echo ""
echo "To stop services:"
echo "  ./scripts/stop.sh"

# Made with Bob
