#!/bin/bash

# Setup script for using external Qdrant instance
# This script configures the application to use an existing Qdrant instance
# instead of spinning up a new Docker container

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_message() {
    echo -e "${2}${1}${NC}"
}

print_message "🚀 External Qdrant Configuration Setup" "$BLUE"
print_message "=====================================" "$BLUE"
echo

# Detect platform
print_message "🔍 Detecting platform..." "$YELLOW"
OS_TYPE=$(uname -s)
case "$OS_TYPE" in
    Darwin*)
        PLATFORM="macOS"
        DOCKER_HOST="host.docker.internal"
        ;;
    Linux*)
        PLATFORM="Linux"
        # Try to detect if running in Docker Desktop
        if [[ -f /.dockerenv ]] || grep -qa docker /proc/version; then
            DOCKER_HOST="host.docker.internal"
        else
            # Use Docker bridge network gateway
            DOCKER_HOST="172.17.0.1"
        fi
        ;;
    MINGW*|MSYS*|CYGWIN*)
        PLATFORM="Windows"
        DOCKER_HOST="host.docker.internal"
        ;;
    *)
        PLATFORM="Unknown"
        DOCKER_HOST="host.docker.internal"
        ;;
esac

print_message "✅ Platform detected: $PLATFORM" "$GREEN"
print_message "   Docker host: $DOCKER_HOST" "$NC"
echo

# Check if external Qdrant is running
print_message "🔍 Checking external Qdrant at localhost:6333..." "$YELLOW"
if curl -s -f http://localhost:6333/health > /dev/null 2>&1; then
    print_message "✅ External Qdrant is running and healthy!" "$GREEN"

    # Get collections
    COLLECTIONS=$(curl -s http://localhost:6333/collections | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'result' in data and 'collections' in data['result']:
        collections = data['result']['collections']
        print(', '.join([c['name'] for c in collections]) if collections else 'No collections found')
    else:
        print('No collections found')
except:
    print('Error reading collections')
" 2>/dev/null || echo "Unable to read collections")

    print_message "   Collections: $COLLECTIONS" "$NC"
else
    print_message "⚠️  External Qdrant not found at localhost:6333" "$RED"
    print_message "   Please ensure Qdrant is running before continuing" "$YELLOW"
    read -p "Do you want to continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo

# Create .env file if it doesn't exist
if [[ -f .env ]]; then
    print_message "📝 Found existing .env file" "$YELLOW"
    read -p "Do you want to backup and replace it? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
        print_message "✅ Backup created: .env.backup.*" "$GREEN"
    else
        print_message "Keeping existing .env file" "$NC"
        exit 0
    fi
fi

# Create .env file
print_message "📝 Creating .env file for external Qdrant..." "$YELLOW"
cat > .env << EOF
# Claude Code Memory Explorer - Environment Configuration
# Auto-generated for external Qdrant on $PLATFORM

# External Qdrant Configuration
USE_EXTERNAL_QDRANT=true
EXTERNAL_QDRANT_URL=http://$DOCKER_HOST:6333

# Internal Qdrant URL (not used when USE_EXTERNAL_QDRANT=true)
QDRANT_URL=http://qdrant:6333

# Port Configuration
NGINX_PORT=8080
BACKEND_PORT=8000
FRONTEND_PORT=3000

# Qdrant Settings (adjust if needed)
# QDRANT_API_KEY=your_api_key_here
# QDRANT_COLLECTION=your_default_collection
EOF

print_message "✅ .env file created successfully!" "$GREEN"
echo

# Show next steps
print_message "🎯 Next Steps:" "$BLUE"
print_message "=============" "$BLUE"
echo
print_message "1. Review the .env file if you need custom settings" "$NC"
print_message "2. Start the application with external Qdrant:" "$NC"
print_message "   make external-qdrant" "$GREEN"
echo
print_message "The application will use your Qdrant at localhost:6333" "$NC"
print_message "Access the web interface at: http://localhost:8080" "$NC"
echo

# Ask if user wants to start now
read -p "Would you like to start the application now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_message "🚀 Starting application with external Qdrant..." "$BLUE"
    make external-qdrant
fi

print_message "Setup complete! 🎉" "$GREEN"