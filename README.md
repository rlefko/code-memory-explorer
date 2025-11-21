# 🚀 Claude Code Memory Explorer

A beautiful, intuitive web application for visualizing and exploring codebases indexed by Claude Code Memory. Transform your code understanding with interactive graphs, semantic search, and progressive code exploration.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Docker](https://img.shields.io/badge/docker-ready-blue)

## ✨ Features

### 🎯 Core Capabilities
- **Interactive Graph Visualization**: Explore code relationships with D3.js force-directed graphs
- **Semantic Search**: Find code by meaning, not just keywords
- **Progressive Disclosure**: Start with overviews, dive into details on demand
- **Real-time Updates**: WebSocket support for live synchronization
- **Multi-Collection Support**: Manage multiple indexed codebases

### 🎨 User Experience
- **Beautiful Dashboard**: Collection cards with health indicators
- **Split-Panel Explorer**: Graph and code side-by-side
- **Monaco Editor**: VS Code's editor for syntax highlighting
- **Dark Mode**: Easy on the eyes for long coding sessions
- **Sub-4ms Search**: Lightning-fast metadata-first architecture

## 🛠️ Tech Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **Qdrant**: Vector database for semantic search
- **WebSockets**: Real-time bidirectional communication

### Frontend
- **React 18**: Modern UI library with TypeScript
- **Vite**: Lightning-fast build tool
- **D3.js**: Powerful data visualization
- **Monaco Editor**: VS Code's code editor
- **TailwindCSS**: Utility-first CSS framework

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Claude Code Memory indexer (`claude-indexer`) installed
- At least one indexed codebase

### One-Command Launch 🎯
```bash
# Start everything with a single command
make

# That's it! The app is now running at http://localhost:8080
```

### Other Useful Commands
```bash
make stop      # Stop all services
make logs      # View logs
make dev       # Development mode with hot reload
make clean     # Remove everything (including data)
make help      # See all available commands
```

## ⚙️ Environment Configuration

### Using External Qdrant Instance

If you already have Qdrant running with indexed data (like at `localhost:6333`), you can use it instead of spinning up a new container:

#### 1. Create Your .env File
Copy `.env.template` to `.env` and configure for external Qdrant:

```bash
# Copy template
cp .env.template .env

# Edit .env file with these key settings:
USE_EXTERNAL_QDRANT=true
EXTERNAL_QDRANT_URL=http://host.docker.internal:6333  # For macOS/Windows
# For Linux, use: EXTERNAL_QDRANT_URL=http://172.17.0.1:6333
```

#### 2. Start with External Qdrant
```bash
make external-qdrant
```

### Environment Variables Reference

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `USE_EXTERNAL_QDRANT` | Use existing Qdrant instead of Docker container | `false` | `true` |
| `EXTERNAL_QDRANT_URL` | URL for external Qdrant from Docker | - | `http://host.docker.internal:6333` |
| `NGINX_PORT` | Main application port | `8080` | `9090` |
| `BACKEND_PORT` | Backend API port (internal) | `8000` | `9000` |
| `QDRANT_PORT` | Qdrant port (internal mode only) | `6333` | `6334` |
| `QDRANT_API_KEY` | Qdrant authentication key | - | `my_secret_key` |
| `QDRANT_COLLECTION` | Default collection to load | - | `my-project` |

### Platform-Specific Notes

**macOS/Windows (Docker Desktop):**
- Use `host.docker.internal` to access host services from Docker
- Example: `EXTERNAL_QDRANT_URL=http://host.docker.internal:6333`

**Linux:**
- Use Docker bridge IP or host IP
- Example: `EXTERNAL_QDRANT_URL=http://172.17.0.1:6333`
- Or use your machine's IP address

### Switching Between Modes

**To use external Qdrant:**
```bash
# Edit .env
USE_EXTERNAL_QDRANT=true
# Run
make external-qdrant
```

**To use internal Qdrant container:**
```bash
# Edit .env
USE_EXTERNAL_QDRANT=false
# Run
make run
```

## 📍 Access Points

Everything is served through nginx on **port 8080**:

- **Web Interface**: http://localhost:8080
- **API Documentation**: http://localhost:8080/api/docs
- **Qdrant Dashboard**: http://localhost:8080/qdrant/dashboard
- **WebSocket Test**: http://localhost:8080/ws/test

## 🎯 Usage Guide

### 1. Dashboard View
The landing page shows all your indexed collections as beautiful cards with:
- Entity and relation counts
- Health status indicators
- Quick actions (explore, refresh)

### 2. Project Explorer
Click "Explore" on any collection to enter the main interface:

#### Graph Panel (Left)
- **Pan & Zoom**: Click and drag to pan, scroll to zoom
- **Select Nodes**: Click any node to view its code
- **Filter by Type**: Use the filter dropdown for specific entity types
- **Drag Nodes**: Reorganize the graph by dragging nodes

#### Code Panel (Right)
- **View Implementation**: See the full source code
- **Progressive Loading**:
  - Minimal: Just the entity
  - Logical: Include same-file helpers
  - Dependencies: Show all related code
- **Relations Info**: See what calls and is called by this entity

#### Search Bar (Top)
- **Modes**: Hybrid (default), Semantic, or Keyword
- **Live Results**: Results appear as you type
- **Smart Ranking**: AI-powered relevance scoring

### 3. Keyboard Shortcuts
- `Cmd/Ctrl + K`: Focus search bar
- `Escape`: Close search results
- `Cmd/Ctrl + Enter`: Toggle fullscreen code view

## 🔧 Development

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
python app.py
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📊 API Endpoints

### Collections
- `GET /api/collections` - List all collections
- `GET /api/collections/{name}` - Get collection details
- `POST /api/collections/{name}/reindex` - Trigger reindexing
- `DELETE /api/collections/{name}` - Delete collection

### Search
- `POST /api/search` - Unified search across collections
- `POST /api/search/similar` - Semantic similarity search
- `GET /api/search/suggestions` - Autocomplete suggestions

### Graph
- `POST /api/graph` - Get graph visualization data
- `GET /api/graph/layout/{collection}` - Pre-calculated layouts
- `GET /api/graph/clusters/{collection}` - Identify clusters
- `GET /api/graph/paths/{collection}` - Find paths between entities

### Entities
- `GET /api/entities` - List entities with filters
- `GET /api/entities/{name}/implementation` - Get source code
- `GET /api/entities/{name}/relations` - Get relationships

## 🐳 Docker Configuration

### Services
- **qdrant**: Vector database (port 6333)
- **backend**: FastAPI server (port 8000)
- **frontend**: React application (port 3000)

### Volumes
- `./qdrant_storage`: Persistent vector database storage
- `../settings.txt`: API keys and configuration

### Networks
- `claude-memory-network`: Bridge network for inter-service communication

## 🔒 Security Notes

- CORS configured for local development
- Add authentication before deploying to production
- Use HTTPS with proper certificates in production
- Restrict Qdrant access in production environments

## 🚨 Troubleshooting

### Port Already in Use
```bash
# Find process using port 6333 (Qdrant)
lsof -i :6333

# Stop existing Qdrant container
docker stop $(docker ps -q --filter "publish=6333")
```

### Services Not Starting
```bash
# Check logs
docker-compose logs -f

# Restart services
docker-compose restart

# Full reset
docker-compose down -v
docker-compose up -d
```

### No Collections Visible
```bash
# Index a test project
claude-indexer index -p /path/to/project -c test-collection

# Verify Qdrant is running
curl http://localhost:6333/health
```

## 📈 Performance Tips

1. **Index Optimization**: Keep collections under 10k entities for best performance
2. **Graph Rendering**: Limit initial graph to 200 nodes
3. **Search Mode**: Use "keyword" for exact matches, "semantic" for concepts
4. **Caching**: Browser automatically caches API responses for 1 minute

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - feel free to use this in your projects!

## 🙏 Acknowledgments

- Claude Code Memory system by Anthropic
- Qdrant vector database team
- D3.js for amazing visualizations
- Monaco Editor from Microsoft

## 📮 Support

For issues or questions:
- Create an issue in the repository
- Check existing documentation
- Review API docs at http://localhost:8000/docs

---

Built with ❤️ for the Claude Code Memory ecosystem