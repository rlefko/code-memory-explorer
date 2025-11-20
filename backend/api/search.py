"""
Search API endpoints for semantic, keyword, and hybrid search.
"""

import time
from typing import List, Optional
import numpy as np

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from models.schemas import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    SearchMode,
    EntityType,
    ChunkType,
)
from services.qdrant_service import get_qdrant_service

router = APIRouter()


# Mock embedding function - in production, use actual embedding service
def generate_mock_embedding(text: str, dimension: int = 1536) -> List[float]:
    """
    Generate a mock embedding vector for testing.
    In production, this would call OpenAI or Voyage AI.
    """
    np.random.seed(hash(text) % 2**32)
    embedding = np.random.randn(dimension)
    # Normalize to unit vector
    embedding = embedding / np.linalg.norm(embedding)
    return embedding.tolist()


@router.post("/", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Perform semantic, keyword, or hybrid search across collections.

    Args:
        request: Search request with query and filters.

    Returns:
        Search response with results and metadata.
    """
    start_time = time.time()

    try:
        service = get_qdrant_service()

        # Validate collection exists if specified
        if request.collection:
            info = service.get_collection_info(request.collection)
            if info.get("error"):
                raise HTTPException(
                    status_code=404,
                    detail=f"Collection not found: {request.collection}",
                )
        else:
            # If no collection specified, get first available
            collections = service.list_collections()
            if not collections:
                raise HTTPException(
                    status_code=404,
                    detail="No collections available",
                )
            request.collection = collections[0]

        # Generate embedding for the query
        # In production, use actual embedding service based on settings
        query_embedding = generate_mock_embedding(request.query)

        # Perform search
        entity_results = await service.search_similar(
            collection=request.collection,
            query_vector=query_embedding,
            mode=request.mode,
            entity_types=request.entity_types,
            limit=request.limit,
            include_implementation=request.include_implementation,
        )

        # Convert to search results
        results = []
        for entity, score in entity_results:
            # Generate highlights (simplified - in production, use actual matching)
            highlights = []
            if entity.docstring and request.query.lower() in entity.docstring.lower():
                highlights.append(entity.docstring[:200])
            elif entity.observations:
                for obs in entity.observations:
                    if request.query.lower() in obs.lower():
                        highlights.append(obs[:200])
                        break

            results.append(
                SearchResult(
                    entity=entity,
                    score=score,
                    chunk_type=ChunkType.METADATA,
                    highlights=highlights,
                )
            )

        # Calculate response time
        took_ms = (time.time() - start_time) * 1000

        return SearchResponse(
            results=results[request.offset : request.offset + request.limit],
            total=len(results),
            query=request.query,
            mode=request.mode,
            took_ms=took_ms,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/similar")
async def search_similar(
    query: str,
    collection: str,
    entity_types: Optional[List[EntityType]] = None,
    limit: int = 20,
    mode: SearchMode = SearchMode.HYBRID,
):
    """
    Find similar entities using semantic search.

    Args:
        query: Search query.
        collection: Collection to search in.
        entity_types: Optional entity type filters.
        limit: Maximum results.
        mode: Search mode.

    Returns:
        List of similar entities with scores.
    """
    try:
        service = get_qdrant_service()

        # Generate embedding
        query_embedding = generate_mock_embedding(query)

        # Search
        results = await service.search_similar(
            collection=collection,
            query_vector=query_embedding,
            mode=mode,
            entity_types=entity_types,
            limit=limit,
            include_implementation=False,
        )

        # Format response
        formatted_results = []
        for entity, score in results:
            formatted_results.append({
                "entity": {
                    "name": entity.name,
                    "type": entity.entity_type,
                    "file_path": entity.file_path,
                    "line_number": entity.line_number,
                    "observations": entity.observations[:3],  # First 3 observations
                },
                "score": score,
            })

        return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions")
async def get_search_suggestions(
    query: str,
    collection: str,
    limit: int = 10,
):
    """
    Get search suggestions based on partial query.

    Args:
        query: Partial search query.
        collection: Collection to search in.
        limit: Maximum suggestions.

    Returns:
        List of suggested completions.
    """
    try:
        if len(query) < 2:
            return []

        service = get_qdrant_service()

        # Get entities that match the prefix
        entities, _ = service.get_graph_data(collection, limit=100)

        suggestions = []
        query_lower = query.lower()

        for entity in entities:
            # Check if entity name starts with query
            if entity.name.lower().startswith(query_lower):
                suggestions.append({
                    "text": entity.name,
                    "type": entity.entity_type,
                    "description": entity.observations[0] if entity.observations else "",
                })

            if len(suggestions) >= limit:
                break

        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multi")
async def multi_collection_search(
    query: str,
    collections: Optional[List[str]] = None,
    mode: SearchMode = SearchMode.HYBRID,
    limit_per_collection: int = 10,
):
    """
    Search across multiple collections simultaneously.

    Args:
        query: Search query.
        collections: List of collections to search (all if not specified).
        mode: Search mode.
        limit_per_collection: Maximum results per collection.

    Returns:
        Results grouped by collection.
    """
    try:
        service = get_qdrant_service()

        # Get collections to search
        if not collections:
            collections = service.list_collections()

        if not collections:
            return {"results": {}, "total": 0}

        # Generate embedding once
        query_embedding = generate_mock_embedding(query)

        # Search each collection
        all_results = {}
        total_count = 0

        for collection_name in collections:
            try:
                # Check collection exists
                info = service.get_collection_info(collection_name)
                if info.get("error"):
                    continue

                # Search
                results = await service.search_similar(
                    collection=collection_name,
                    query_vector=query_embedding,
                    mode=mode,
                    limit=limit_per_collection,
                )

                collection_results = []
                for entity, score in results:
                    collection_results.append({
                        "entity": entity.name,
                        "type": entity.entity_type,
                        "score": score,
                        "file_path": entity.file_path,
                    })

                if collection_results:
                    all_results[collection_name] = collection_results
                    total_count += len(collection_results)

            except Exception as e:
                print(f"Error searching collection {collection_name}: {e}")
                continue

        return {
            "query": query,
            "mode": mode,
            "results": all_results,
            "total": total_count,
            "collections_searched": len(all_results),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))