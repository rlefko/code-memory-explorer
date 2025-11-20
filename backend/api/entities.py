"""
Entities API endpoints for managing entities in the knowledge graph.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from models.schemas import Entity, ImplementationResponse, EntityType
from services.qdrant_service import get_qdrant_service

router = APIRouter()


@router.get("/", response_model=List[Entity])
async def list_entities(
    collection: str = Query(..., description="Collection name"),
    entity_types: Optional[List[EntityType]] = Query(None, description="Filter by entity types"),
    limit: int = Query(50, ge=1, le=500, description="Maximum entities to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """
    List entities in a collection with optional filtering.

    Args:
        collection: Collection name.
        entity_types: Optional filter by entity types.
        limit: Maximum number of entities to return.
        offset: Pagination offset.

    Returns:
        List of entities.
    """
    try:
        service = get_qdrant_service()

        # Get entities from graph data
        entities, _ = service.get_graph_data(
            collection=collection,
            entity_types=entity_types,
            limit=limit + offset,
        )

        # Apply pagination
        return entities[offset : offset + limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{entity_name}", response_model=Entity)
async def get_entity(
    entity_name: str,
    collection: str = Query(..., description="Collection name"),
):
    """
    Get detailed information about a specific entity.

    Args:
        entity_name: Name of the entity.
        collection: Collection name.

    Returns:
        Entity object.
    """
    try:
        service = get_qdrant_service()
        entity = service.get_entity(collection, entity_name)

        if not entity:
            raise HTTPException(status_code=404, detail=f"Entity not found: {entity_name}")

        return entity
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{entity_name}/implementation", response_model=ImplementationResponse)
async def get_entity_implementation(
    entity_name: str,
    collection: str = Query(..., description="Collection name"),
    scope: str = Query("minimal", description="Scope: minimal, logical, dependencies"),
):
    """
    Get implementation code for an entity.

    Args:
        entity_name: Name of the entity.
        collection: Collection name.
        scope: Implementation scope (minimal, logical, dependencies).

    Returns:
        Implementation response with code and related entities.
    """
    try:
        service = get_qdrant_service()

        # Get the entity
        entity = service.get_entity(collection, entity_name)
        if not entity:
            raise HTTPException(status_code=404, detail=f"Entity not found: {entity_name}")

        # Get implementation
        implementation = service.get_implementation(collection, entity_name)
        if not implementation:
            implementation = "// Implementation not available"

        # Get related entities based on scope
        dependencies = []
        callers = []

        if scope in ["logical", "dependencies"]:
            # Get relations for this entity
            relations = service.get_relations(collection, entity_name)

            for relation in relations:
                if relation.from_entity == entity_name:
                    # This entity calls/uses another
                    dep_entity = service.get_entity(collection, relation.to_entity)
                    if dep_entity:
                        dependencies.append(dep_entity)
                else:
                    # Another entity calls/uses this
                    caller_entity = service.get_entity(collection, relation.from_entity)
                    if caller_entity:
                        callers.append(caller_entity)

        # Determine language from file extension
        language = "plaintext"
        if entity.file_path:
            if entity.file_path.endswith(".py"):
                language = "python"
            elif entity.file_path.endswith((".js", ".jsx")):
                language = "javascript"
            elif entity.file_path.endswith((".ts", ".tsx")):
                language = "typescript"
            elif entity.file_path.endswith(".java"):
                language = "java"
            elif entity.file_path.endswith(".go"):
                language = "go"
            elif entity.file_path.endswith(".rs"):
                language = "rust"

        return ImplementationResponse(
            entity=entity,
            implementation=implementation,
            language=language,
            dependencies=dependencies[:10] if scope == "dependencies" else [],
            callers=callers[:10] if scope == "dependencies" else [],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{entity_name}/relations")
async def get_entity_relations(
    entity_name: str,
    collection: str = Query(..., description="Collection name"),
):
    """
    Get all relations involving a specific entity.

    Args:
        entity_name: Name of the entity.
        collection: Collection name.

    Returns:
        Dictionary with incoming and outgoing relations.
    """
    try:
        service = get_qdrant_service()

        # Check entity exists
        entity = service.get_entity(collection, entity_name)
        if not entity:
            raise HTTPException(status_code=404, detail=f"Entity not found: {entity_name}")

        # Get all relations for this entity
        relations = service.get_relations(collection, entity_name)

        # Separate incoming and outgoing
        incoming = []
        outgoing = []

        for relation in relations:
            if relation.from_entity == entity_name:
                outgoing.append({
                    "to": relation.to_entity,
                    "type": relation.relation_type,
                    "context": relation.context,
                })
            else:
                incoming.append({
                    "from": relation.from_entity,
                    "type": relation.relation_type,
                    "context": relation.context,
                })

        return {
            "entity": entity_name,
            "incoming_relations": incoming,
            "outgoing_relations": outgoing,
            "total_incoming": len(incoming),
            "total_outgoing": len(outgoing),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{entity_name}/usage")
async def get_entity_usage(
    entity_name: str,
    collection: str = Query(..., description="Collection name"),
):
    """
    Get usage statistics and patterns for an entity.

    Args:
        entity_name: Name of the entity.
        collection: Collection name.

    Returns:
        Usage statistics and calling patterns.
    """
    try:
        service = get_qdrant_service()

        # Check entity exists
        entity = service.get_entity(collection, entity_name)
        if not entity:
            raise HTTPException(status_code=404, detail=f"Entity not found: {entity_name}")

        # Get relations
        relations = service.get_relations(collection, entity_name)

        # Analyze usage patterns
        callers = set()
        callees = set()
        imports = set()
        imported_by = set()

        for relation in relations:
            if relation.from_entity == entity_name:
                if relation.relation_type == "calls":
                    callees.add(relation.to_entity)
                elif relation.relation_type == "imports":
                    imports.add(relation.to_entity)
            else:
                if relation.relation_type == "calls":
                    callers.add(relation.from_entity)
                elif relation.relation_type == "imports":
                    imported_by.add(relation.from_entity)

        return {
            "entity": entity_name,
            "entity_type": entity.entity_type,
            "file_path": entity.file_path,
            "usage_stats": {
                "called_by": list(callers),
                "calls": list(callees),
                "imported_by": list(imported_by),
                "imports": list(imports),
                "total_references": len(callers) + len(imported_by),
            },
            "complexity": {
                "cyclomatic": entity.complexity_score or 0,
                "dependencies": len(callees) + len(imports),
                "dependents": len(callers) + len(imported_by),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))