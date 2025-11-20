#!/bin/bash

# Start script for Claude Code Memory Explorer Backend

echo "🚀 Starting Claude Code Memory Explorer Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if Qdrant is running
echo "Checking Qdrant connection..."
python -c "
from qdrant_client import QdrantClient
try:
    client = QdrantClient(url='http://localhost:6333')
    collections = client.get_collections()
    print(f'✅ Qdrant is running with {len(collections.collections)} collections')
except:
    print('❌ Qdrant is not running. Please start it with:')
    print('   docker run -p 6333:6333 -v \$(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant')
    exit(1)
" || exit 1

# Start the FastAPI server
echo "Starting FastAPI server on http://localhost:8000"
echo "API documentation available at http://localhost:8000/docs"
echo "WebSocket test page at http://localhost:8000/ws/test"
echo ""
python app.py