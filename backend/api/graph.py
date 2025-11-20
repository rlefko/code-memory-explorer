"""
Graph API endpoints for visualization data.
"""

from typing import List, Optional
import hashlib

from fastapi import APIRouter, HTTPException, Query

from models.schemas import (
    GraphRequest,
    GraphData,
    GraphNode,
    GraphEdge,
    EntityType,
    RelationType,
)
from services.qdrant_service import get_qdrant_service

router = APIRouter()


def calculate_node_size(entity, all_relations) -> int:
    """
    Calculate node size based on its connections and importance.
    """
    connection_count = sum(
        1
        for r in all_relations
        if r.from_entity == entity.name or r.to_entity == entity.name
    )
    # Base size 10, +2 per connection, max 50
    return min(10 + (connection_count * 2), 50)


def get_entity_group(entity_type: EntityType) -> int:
    """
    Get group number for coloring based on entity type.
    """
    groups = {
        EntityType.FILE: 0,
        EntityType.CLASS: 1,
        EntityType.FUNCTION: 2,
        EntityType.METHOD: 2,
        EntityType.VARIABLE: 3,
        EntityType.CONSTANT: 3,
        EntityType.IMPORT: 4,
        EntityType.MODULE: 5,
        EntityType.DOCUMENTATION: 6,
        EntityType.TEST: 7,
    }
    return groups.get(entity_type, 8)


@router.post("/", response_model=GraphData)
async def get_graph_data(request: GraphRequest):
    """
    Get graph data for visualization.

    Args:
        request: Graph request with filters.

    Returns:
        Graph data with nodes and edges.
    """
    try:
        service = get_qdrant_service()

        # Get entities and relations
        entities, relations = service.get_graph_data(
            collection=request.collection,
            entity=request.entity,
            entity_types=request.entity_types,
            depth=request.depth,
            limit=request.limit,
        )

        if not entities:
            return GraphData(
                nodes=[],
                edges=[],
                metadata={
                    "message": "No entities found",
                    "collection": request.collection,
                },
            )

        # Create nodes
        nodes = []
        entity_names = set()
        for entity in entities:
            entity_names.add(entity.name)
            nodes.append(
                GraphNode(
                    id=entity.name,
                    name=entity.name,
                    entity_type=entity.entity_type,
                    size=calculate_node_size(entity, relations),
                    group=get_entity_group(entity.entity_type),
                    metadata={
                        "file_path": entity.file_path,
                        "line_number": entity.line_number,
                        "observations": entity.observations[:2],  # First 2 observations
                        "docstring": entity.docstring[:100] if entity.docstring else None,
                    },
                )
            )

        # Create edges (only include edges where both nodes exist)
        edges = []
        for relation in relations:
            if relation.from_entity in entity_names and relation.to_entity in entity_names:
                edges.append(
                    GraphEdge(
                        source=relation.from_entity,
                        target=relation.to_entity,
                        relation_type=relation.relation_type,
                        weight=relation.confidence,
                    )
                )

        return GraphData(
            nodes=nodes,
            edges=edges,
            metadata={
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "collection": request.collection,
                "centered_on": request.entity,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/layout/{collection}")
async def get_graph_layouts(
    collection: str,
    layout_type: str = Query("force", description="Layout type: force, hierarchical, radial"),
    entity: Optional[str] = None,
    limit: int = Query(100, ge=10, le=500),
):
    """
    Get pre-calculated graph layouts for different visualization modes.

    Args:
        collection: Collection name.
        layout_type: Type of layout (force, hierarchical, radial).
        entity: Optional entity to center on.
        limit: Maximum nodes.

    Returns:
        Graph data with layout positions.
    """
    try:
        service = get_qdrant_service()

        # Get graph data
        entities, relations = service.get_graph_data(
            collection=collection,
            entity=entity,
            limit=limit,
        )

        nodes = []
        edges = []
        entity_names = set()

        # Create basic graph structure
        for i, entity in enumerate(entities):
            entity_names.add(entity.name)

            # Calculate position based on layout type
            if layout_type == "hierarchical":
                # Simple hierarchical layout based on file path depth
                depth = entity.file_path.count("/") if entity.file_path else 0
                x = (i % 10) * 100
                y = depth * 150
            elif layout_type == "radial":
                # Radial layout
                import math

                angle = (2 * math.pi * i) / max(len(entities), 1)
                radius = 200 + (i % 3) * 100
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
            else:  # force
                # Initial random positions for force-directed layout
                import random

                random.seed(i)
                x = random.uniform(-300, 300)
                y = random.uniform(-300, 300)

            nodes.append({
                "id": entity.name,
                "name": entity.name,
                "type": entity.entity_type,
                "x": x,
                "y": y,
                "size": calculate_node_size(entity, relations),
                "group": get_entity_group(entity.entity_type),
            })

        # Add edges
        for relation in relations:
            if relation.from_entity in entity_names and relation.to_entity in entity_names:
                edges.append({
                    "source": relation.from_entity,
                    "target": relation.to_entity,
                    "type": relation.relation_type,
                })

        return {
            "layout_type": layout_type,
            "nodes": nodes,
            "edges": edges,
            "bounds": {
                "min_x": min(n["x"] for n in nodes) if nodes else 0,
                "max_x": max(n["x"] for n in nodes) if nodes else 0,
                "min_y": min(n["y"] for n in nodes) if nodes else 0,
                "max_y": max(n["y"] for n in nodes) if nodes else 0,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clusters/{collection}")
async def get_graph_clusters(
    collection: str,
    min_cluster_size: int = Query(3, ge=2, le=20),
):
    """
    Identify clusters in the graph for better visualization.

    Args:
        collection: Collection name.
        min_cluster_size: Minimum nodes for a cluster.

    Returns:
        Cluster information.
    """
    try:
        service = get_qdrant_service()

        # Get all entities and relations
        entities, relations = service.get_graph_data(
            collection=collection,
            limit=500,
        )

        # Build adjacency list
        adjacency = {}
        for entity in entities:
            adjacency[entity.name] = set()

        for relation in relations:
            if relation.from_entity in adjacency:
                adjacency[relation.from_entity].add(relation.to_entity)
            if relation.to_entity in adjacency:
                adjacency[relation.to_entity].add(relation.from_entity)

        # Simple clustering based on connected components
        visited = set()
        clusters = []

        def dfs(node, cluster):
            if node in visited:
                return
            visited.add(node)
            cluster.add(node)
            for neighbor in adjacency.get(node, []):
                dfs(neighbor, cluster)

        for entity in entities:
            if entity.name not in visited:
                cluster = set()
                dfs(entity.name, cluster)
                if len(cluster) >= min_cluster_size:
                    clusters.append(list(cluster))

        # Sort clusters by size
        clusters.sort(key=len, reverse=True)

        # Generate cluster metadata
        cluster_info = []
        for i, cluster_nodes in enumerate(clusters[:10]):  # Top 10 clusters
            # Get entities in this cluster
            cluster_entities = [e for e in entities if e.name in cluster_nodes]

            # Determine cluster type based on most common entity type
            type_counts = {}
            for entity in cluster_entities:
                type_counts[entity.entity_type] = type_counts.get(entity.entity_type, 0) + 1

            dominant_type = max(type_counts, key=type_counts.get) if type_counts else "mixed"

            cluster_info.append({
                "id": f"cluster_{i}",
                "size": len(cluster_nodes),
                "dominant_type": dominant_type,
                "nodes": cluster_nodes[:20],  # First 20 nodes
                "sample_files": list(
                    set(e.file_path for e in cluster_entities[:10] if e.file_path)
                ),
            })

        return {
            "collection": collection,
            "total_clusters": len(clusters),
            "clusters": cluster_info,
            "isolated_nodes": len(entities) - len(visited),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/paths/{collection}")
async def find_paths(
    collection: str,
    source: str = Query(..., description="Source entity name"),
    target: str = Query(..., description="Target entity name"),
    max_depth: int = Query(5, ge=1, le=10),
):
    """
    Find paths between two entities in the graph.

    Args:
        collection: Collection name.
        source: Source entity name.
        target: Target entity name.
        max_depth: Maximum search depth.

    Returns:
        List of paths between entities.
    """
    try:
        service = get_qdrant_service()

        # Check both entities exist
        source_entity = service.get_entity(collection, source)
        target_entity = service.get_entity(collection, target)

        if not source_entity:
            raise HTTPException(status_code=404, detail=f"Source entity not found: {source}")
        if not target_entity:
            raise HTTPException(status_code=404, detail=f"Target entity not found: {target}")

        # Get relations for path finding
        all_relations = service.get_relations(collection)

        # Build adjacency list
        adjacency = {}
        for relation in all_relations:
            if relation.from_entity not in adjacency:
                adjacency[relation.from_entity] = []
            adjacency[relation.from_entity].append({
                "to": relation.to_entity,
                "type": relation.relation_type,
            })

        # BFS to find shortest paths
        from collections import deque

        queue = deque([(source, [source], [])])
        visited = {source}
        paths = []

        while queue and len(paths) < 5:  # Find up to 5 paths
            current, path, edge_types = queue.popleft()

            if len(path) > max_depth:
                continue

            if current == target:
                paths.append({
                    "path": path,
                    "edge_types": edge_types,
                    "length": len(path) - 1,
                })
                continue

            for edge in adjacency.get(current, []):
                next_node = edge["to"]
                if next_node not in visited or len(path) < max_depth:
                    queue.append((
                        next_node,
                        path + [next_node],
                        edge_types + [edge["type"]],
                    ))
                    visited.add(next_node)

        return {
            "source": source,
            "target": target,
            "paths_found": len(paths),
            "paths": paths,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))