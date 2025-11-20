#!/bin/bash

# Claude Code Memory Explorer - Setup Script
# This script sets up and launches the web application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored message
print_message() {
    echo -e "${2}${1}${NC}"
}

print_message "🚀 Claude Code Memory Explorer Setup" "$BLUE"
print_message "=====================================" "$BLUE"
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
print_message "📋 Checking prerequisites..." "$YELLOW"

# Check Docker
if ! command_exists docker; then
    print_message "❌ Docker is not installed. Please install Docker first." "$RED"
    print_message "   Visit: https://docs.docker.com/get-docker/" "$NC"
    exit 1
fi
print_message "✅ Docker is installed" "$GREEN"

# Check Docker Compose
if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
    print_message "❌ Docker Compose is not installed. Please install Docker Compose first." "$RED"
    print_message "   Visit: https://docs.docker.com/compose/install/" "$NC"
    exit 1
fi
print_message "✅ Docker Compose is installed" "$GREEN"

# Check if Qdrant is already running on port 6333
if lsof -Pi :6333 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_message "⚠️  Port 6333 is already in use (Qdrant default port)" "$YELLOW"
    read -p "Do you want to stop the existing service? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_message "Stopping existing Qdrant service..." "$YELLOW"
        docker stop $(docker ps -q --filter "publish=6333") 2>/dev/null || true
        sleep 2
    else
        print_message "Please stop the existing service or modify docker-compose.yml to use a different port" "$RED"
        exit 1
    fi
fi

echo

# Build or pull images
print_message "🔨 Building Docker images..." "$YELLOW"
print_message "This may take a few minutes on first run..." "$NC"

# Use docker-compose or docker compose depending on what's available
if command_exists docker-compose; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

$COMPOSE_CMD build

echo

# Start services
print_message "🎯 Starting services..." "$YELLOW"
$COMPOSE_CMD up -d

echo

# Wait for services to be ready
print_message "⏳ Waiting for services to be ready..." "$YELLOW"

# Wait for Qdrant
echo -n "Waiting for Qdrant..."
for i in {1..30}; do
    if curl -s http://localhost:6333/health >/dev/null 2>&1; then
        print_message " Ready!" "$GREEN"
        break
    fi
    echo -n "."
    sleep 1
done

# Wait for Backend
echo -n "Waiting for Backend API..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        print_message " Ready!" "$GREEN"
        break
    fi
    echo -n "."
    sleep 1
done

# Wait for Frontend
echo -n "Waiting for Frontend..."
for i in {1..10}; do
    if curl -s http://localhost:3000 >/dev/null 2>&1; then
        print_message " Ready!" "$GREEN"
        break
    fi
    echo -n "."
    sleep 1
done

echo
print_message "✨ All services are up and running!" "$GREEN"
echo

# Check if any collections exist
print_message "📊 Checking for indexed collections..." "$YELLOW"
COLLECTIONS=$(curl -s http://localhost:8000/api/collections | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data))" 2>/dev/null || echo "0")

if [ "$COLLECTIONS" = "0" ]; then
    print_message "No collections found. To get started, index a project:" "$YELLOW"
    print_message "  claude-indexer index -p /path/to/project -c my-collection" "$NC"
else
    print_message "Found $COLLECTIONS indexed collection(s)" "$GREEN"
fi

echo
print_message "🎉 Setup complete!" "$GREEN"
print_message "=================================" "$GREEN"
echo
print_message "📍 Access the application at:" "$BLUE"
print_message "   Web Interface: http://localhost:3000" "$NC"
print_message "   API Documentation: http://localhost:8000/docs" "$NC"
print_message "   Qdrant Dashboard: http://localhost:6333/dashboard" "$NC"
echo
print_message "📝 Useful commands:" "$BLUE"
print_message "   View logs: $COMPOSE_CMD logs -f" "$NC"
print_message "   Stop services: $COMPOSE_CMD down" "$NC"
print_message "   Restart services: $COMPOSE_CMD restart" "$NC"
print_message "   Remove everything: $COMPOSE_CMD down -v" "$NC"
echo

# Ask if user wants to open browser
read -p "Would you like to open the web interface now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Detect OS and open browser
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open http://localhost:3000
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open http://localhost:3000 2>/dev/null || print_message "Please open http://localhost:3000 in your browser" "$YELLOW"
    else
        print_message "Please open http://localhost:3000 in your browser" "$YELLOW"
    fi
fi

print_message "Enjoy exploring your code! 🚀" "$GREEN"