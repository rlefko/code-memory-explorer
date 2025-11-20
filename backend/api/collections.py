"""
Collections API endpoints for managing indexed codebases.
"""

import subprocess
from typing import List
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from models.schemas import CollectionInfo, ErrorResponse
from services.qdrant_service import get_qdrant_service

router = APIRouter()


@router.get("/", response_model=List[CollectionInfo])
async def list_collections():
    """
    List all available collections with their statistics.

    Returns:
        List of collection information objects.
    """
    try:
        service = get_qdrant_service()
        collection_names = service.list_collections()

        collections = []
        for name in collection_names:
            info = service.get_collection_info(name)

            # Determine health status
            health = "healthy"
            if info.get("error"):
                health = "error"
            elif info.get("entity_count", 0) == 0:
                health = "warning"

            collections.append(
                CollectionInfo(
                    name=name,
                    entity_count=info.get("entity_count", 0),
                    relation_count=info.get("relation_count", 0),
                    file_count=info.get("file_count", 0),
                    last_indexed=datetime.utcnow(),  # Would need to track this properly
                    size_mb=info.get("vectors_count", 0) * 0.006,  # Rough estimate
                    health=health,
                    metadata=info,
                )
            )

        return collections
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{collection_name}", response_model=CollectionInfo)
async def get_collection(collection_name: str):
    """
    Get detailed information about a specific collection.

    Args:
        collection_name: Name of the collection.

    Returns:
        Collection information object.
    """
    try:
        service = get_qdrant_service()
        info = service.get_collection_info(collection_name)

        if info.get("error"):
            raise HTTPException(status_code=404, detail=f"Collection not found: {collection_name}")

        # Determine health status
        health = "healthy"
        if info.get("entity_count", 0) == 0:
            health = "warning"

        return CollectionInfo(
            name=collection_name,
            entity_count=info.get("entity_count", 0),
            relation_count=info.get("relation_count", 0),
            file_count=info.get("file_count", 0),
            last_indexed=datetime.utcnow(),
            size_mb=info.get("vectors_count", 0) * 0.006,
            health=health,
            metadata=info,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{collection_name}/stats")
async def get_collection_stats(collection_name: str):
    """
    Get detailed statistics about a collection.

    Args:
        collection_name: Name of the collection.

    Returns:
        Detailed statistics dictionary.
    """
    try:
        service = get_qdrant_service()
        info = service.get_collection_info(collection_name)

        if info.get("error"):
            raise HTTPException(status_code=404, detail=f"Collection not found: {collection_name}")

        # Get entity breakdown by type
        entities, _ = service.get_graph_data(collection_name, limit=1000)

        entity_breakdown = {}
        for entity in entities:
            entity_type = entity.entity_type.value
            entity_breakdown[entity_type] = entity_breakdown.get(entity_type, 0) + 1

        # Get file statistics
        file_paths = set()
        for entity in entities:
            if entity.file_path:
                file_paths.add(entity.file_path)

        return {
            "collection": collection_name,
            "total_entities": info.get("entity_count", 0),
            "total_relations": info.get("relation_count", 0),
            "total_vectors": info.get("vectors_count", 0),
            "indexed_vectors": info.get("indexed_vectors", 0),
            "entity_breakdown": entity_breakdown,
            "file_count": len(file_paths),
            "file_paths": list(file_paths)[:20],  # First 20 files
            "status": info.get("status"),
            "config": info.get("config"),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{collection_name}/reindex")
async def reindex_collection(
    collection_name: str,
    background_tasks: BackgroundTasks,
    project_path: str = None,
):
    """
    Trigger re-indexing of a collection.

    Args:
        collection_name: Name of the collection.
        project_path: Path to the project to index.
        background_tasks: FastAPI background tasks.

    Returns:
        Status message.
    """
    try:
        service = get_qdrant_service()

        # Check if collection exists
        info = service.get_collection_info(collection_name)
        if info.get("error"):
            raise HTTPException(status_code=404, detail=f"Collection not found: {collection_name}")

        # Start indexing in background
        def run_indexer():
            """Run the indexer command."""
            try:
                cmd = ["claude-indexer", "index", "-c", collection_name]
                if project_path:
                    cmd.extend(["-p", project_path])

                subprocess.run(cmd, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                print(f"Indexing failed: {e}")

        background_tasks.add_task(run_indexer)

        return JSONResponse(
            content={
                "message": f"Reindexing started for collection '{collection_name}'",
                "collection": collection_name,
                "status": "indexing",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{collection_name}")
async def delete_collection(collection_name: str):
    """
    Delete a collection and all its data.

    Args:
        collection_name: Name of the collection to delete.

    Returns:
        Status message.
    """
    try:
        service = get_qdrant_service()

        # Check if collection exists
        info = service.get_collection_info(collection_name)
        if info.get("error"):
            raise HTTPException(status_code=404, detail=f"Collection not found: {collection_name}")

        # Delete the collection
        service.client.delete_collection(collection_name)

        return JSONResponse(
            content={
                "message": f"Collection '{collection_name}' deleted successfully",
                "collection": collection_name,
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))