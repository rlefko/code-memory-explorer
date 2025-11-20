# 🚀 Claude Code Memory Explorer - Quick Start

## Launch with ONE Command

```bash
cd web-explorer
make
```

**That's it!** Your beautiful code explorer is now running at **http://localhost:8080**

## What Just Happened?

With that single `make` command, we:
1. ✅ Started Qdrant vector database
2. ✅ Built the React frontend for production
3. ✅ Started the FastAPI backend
4. ✅ Configured nginx as reverse proxy
5. ✅ Unified everything on port 8080

## Architecture

```
     Port 8080
         ↓
    ┌─────────┐
    │  nginx  │ ← Single entry point
    └────┬────┘
         │
    ┌────┴────────────┬─────────────┐
    ↓                 ↓             ↓
[Static Files]   [Backend API]  [Qdrant]
 (React App)     (FastAPI)      (Vector DB)
```

## Essential Commands

| Command | What it does |
|---------|-------------|
| `make` | Start everything |
| `make stop` | Stop all services |
| `make logs` | View logs |
| `make dev` | Development mode with hot reload |
| `make open` | Open in browser |
| `make clean` | Remove everything (⚠️ data loss) |
| `make help` | See all commands |

## Features

### 🌑 Beautiful Dark Mode
- Consistent dark theme throughout
- Monaco editor with `vs-dark` theme
- Dark graph visualization
- No light mode toggle (dark only)

### 🎯 Simplified Access
- Everything on **port 8080**
- `/` → Web Interface
- `/api/` → Backend API
- `/api/docs` → API Documentation
- `/qdrant/` → Qdrant Dashboard
- `/ws/` → WebSocket connections

### 🚄 Performance
- Static files served directly by nginx
- Gzip compression enabled
- Browser caching for assets
- Sub-4ms search response

### 🔧 Developer Experience
- Single `make` command
- Beautiful colored output
- Health checks built-in
- Development mode with `make dev`

## Troubleshooting

### Port 8080 Already in Use?
```bash
# Find what's using port 8080
lsof -i :8080

# Or just use make clean to reset
make clean
make
```

### Want to See Logs?
```bash
# All logs
make logs

# Specific service
make logs-backend
make logs-nginx
make logs-qdrant
```

### Need a Shell?
```bash
make shell-backend
make shell-qdrant
```

## Next Steps

1. **Index a project** (if you haven't already):
   ```bash
   claude-indexer index -p /path/to/project -c my-project
   ```

2. **Open the web interface**:
   ```bash
   make open
   # Or manually visit http://localhost:8080
   ```

3. **Explore your code**:
   - Click nodes in the graph
   - Use semantic search
   - View implementations with Monaco editor

## Tech Stack Highlights

- **nginx**: Reverse proxy & static file serving
- **FastAPI**: High-performance Python backend
- **React + TypeScript**: Modern frontend
- **D3.js**: Interactive graph visualizations
- **Monaco Editor**: VS Code's editor (not reinventing the wheel!)
- **Qdrant**: Vector database for semantic search
- **Docker Compose**: Container orchestration
- **Make**: Simple, beautiful commands

---

Built with ❤️ for beautiful code exploration in dark mode!