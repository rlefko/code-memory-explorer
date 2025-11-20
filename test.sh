#!/bin/bash

# Quick test script to verify the setup works

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🧪 Testing Claude Code Memory Explorer Setup"
echo "============================================"
echo ""

# Check if services are running
echo "Checking services..."

# Check nginx
if curl -s http://localhost:8080/health > /dev/null; then
    echo -e "${GREEN}✅ Nginx is responding${NC}"
else
    echo -e "${RED}❌ Nginx not responding${NC}"
    exit 1
fi

# Check API
if curl -s http://localhost:8080/api/health > /dev/null; then
    echo -e "${GREEN}✅ Backend API is healthy${NC}"
else
    echo -e "${RED}❌ Backend API not responding${NC}"
    exit 1
fi

# Check Qdrant
if curl -s http://localhost:8080/qdrant/health > /dev/null; then
    echo -e "${GREEN}✅ Qdrant is healthy${NC}"
else
    echo -e "${RED}❌ Qdrant not responding${NC}"
    exit 1
fi

# Check frontend
if curl -s http://localhost:8080/ | grep -q "Claude Code Memory Explorer"; then
    echo -e "${GREEN}✅ Frontend is serving${NC}"
else
    echo -e "${RED}❌ Frontend not serving${NC}"
    exit 1
fi

# Check API endpoints
echo ""
echo "Testing API endpoints..."

# Test collections endpoint
if curl -s http://localhost:8080/api/collections > /dev/null; then
    echo -e "${GREEN}✅ Collections API working${NC}"
else
    echo -e "${RED}❌ Collections API failed${NC}"
fi

echo ""
echo -e "${GREEN}🎉 All tests passed! The application is working correctly.${NC}"
echo ""
echo "Access points:"
echo "  Web Interface: http://localhost:8080"
echo "  API Docs: http://localhost:8080/api/docs"
echo "  Qdrant Dashboard: http://localhost:8080/qdrant/dashboard"