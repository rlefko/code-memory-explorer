"""
Claude Code Memory Explorer - FastAPI Backend
Main application entry point with CORS configuration and route registration.
"""

import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.collections import router as collections_router
from api.entities import router as entities_router
from api.search import router as search_router
from api.graph import router as graph_router
from api.websocket import router as websocket_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan events.
    Initialize resources on startup and cleanup on shutdown.
    """
    # Startup
    print("🚀 Claude Code Memory Explorer API starting...")
    yield
    # Shutdown
    print("👋 Claude Code Memory Explorer API shutting down...")


# Create FastAPI application
app = FastAPI(
    title="Claude Code Memory Explorer API",
    description="Interactive web API for exploring and querying indexed codebases",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development server
        "http://localhost:5173",  # Vite development server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Check if the API is running and healthy."""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "Claude Code Memory Explorer API",
            "version": "1.0.0",
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """Welcome message and API information."""
    return {
        "message": "Welcome to Claude Code Memory Explorer API",
        "documentation": "/docs",
        "openapi": "/openapi.json",
        "health": "/health",
    }


# Register API routers
app.include_router(collections_router, prefix="/api/collections", tags=["Collections"])
app.include_router(entities_router, prefix="/api/entities", tags=["Entities"])
app.include_router(search_router, prefix="/api/search", tags=["Search"])
app.include_router(graph_router, prefix="/api/graph", tags=["Graph"])
app.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle unexpected exceptions gracefully."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "type": type(exc).__name__,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )