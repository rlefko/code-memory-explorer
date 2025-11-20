"""
Qdrant service wrapper for database operations.
Provides high-level interface to Qdrant vector database.
"""

import hashlib
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    Filter,
    FieldCondition,
    MatchValue,
    PointStruct,
    VectorParams,
    SearchParams,
    SparseVector,
    NamedVector,
    ScoredPoint,
)

from config import get_settings
from models.schemas import Entity, Relation, EntityType, SearchMode, ChunkType


class QdrantService:
    """
    Service class for interacting with Qdrant vector database.
    Handles all database operations including search, retrieval, and updates.
    """

    def __init__(self):
        """Initialize Qdrant client with settings."""
        settings = get_settings()
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            timeout=settings.qdrant_timeout,
        )
        self.settings = settings

    def list_collections(self) -> List[str]:
        """
        List all available collections in Qdrant.

        Returns:
            List of collection names.
        """
        collections = self.client.get_collections()
        return [col.name for col in collections.collections]

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a collection.

        Args:
            collection_name: Name of the collection.

        Returns:
            Dictionary with collection statistics.
        """
        try:
            info = self.client.get_collection(collection_name)

            # Count entities and relations
            entity_count = self.client.count(
                collection_name=collection_name,
                count_filter=Filter(
                    must=[
                        FieldCondition(
                            key="type",
                            match=MatchValue(value="chunk"),
                        ),
                        FieldCondition(
                            key="chunk_type",
                            match=MatchValue(value="metadata"),
                        ),
                    ]
                ),
            ).count

            relation_count = self.client.count(
                collection_name=collection_name,
                count_filter=Filter(
                    must=[
                        FieldCondition(
                            key="chunk_type",
                            match=MatchValue(value="relation"),
                        ),
                    ]
                ),
            ).count

            return {
                "name": collection_name,
                "entity_count": entity_count,
                "relation_count": relation_count,
                "vectors_count": info.vectors_count or 0,
                "points_count": info.points_count or 0,
                "indexed_vectors": info.indexed_vectors_count or 0,
                "status": info.status,
                "config": {
                    "vector_size": info.config.params.vectors.get("dense", {}).size
                    if isinstance(info.config.params.vectors, dict)
                    else None,
                    "distance": info.config.params.vectors.get("dense", {}).distance
                    if isinstance(info.config.params.vectors, dict)
                    else None,
                },
            }
        except Exception as e:
            return {
                "name": collection_name,
                "error": str(e),
                "status": "error",
            }

    async def search_similar(
        self,
        collection: str,
        query_vector: List[float],
        mode: SearchMode = SearchMode.HYBRID,
        entity_types: Optional[List[EntityType]] = None,
        limit: int = 20,
        include_implementation: bool = False,
    ) -> List[Tuple[Entity, float]]:
        """
        Search for similar entities using semantic, keyword, or hybrid search.

        Args:
            collection: Collection to search in.
            query_vector: Query embedding vector.
            mode: Search mode (semantic, keyword, hybrid).
            entity_types: Filter by entity types.
            limit: Maximum results to return.
            include_implementation: Include implementation chunks.

        Returns:
            List of (Entity, score) tuples.
        """
        # Build filter
        must_conditions = [
            FieldCondition(key="type", match=MatchValue(value="chunk")),
        ]

        if not include_implementation:
            must_conditions.append(
                FieldCondition(key="chunk_type", match=MatchValue(value="metadata"))
            )

        if entity_types:
            must_conditions.append(
                FieldCondition(
                    key="metadata.entity_type",
                    match=MatchValue(
                        any=[et.value for et in entity_types]
                    ),
                )
            )

        filter_query = Filter(must=must_conditions)

        # Perform search based on mode
        if mode == SearchMode.SEMANTIC:
            results = self.client.search(
                collection_name=collection,
                query_vector=NamedVector(name="dense", vector=query_vector),
                query_filter=filter_query,
                limit=limit,
            )
        elif mode == SearchMode.KEYWORD:
            # For keyword search, we would need BM25 sparse vectors
            # This is a simplified version - real implementation would use sparse vectors
            results = self.client.search(
                collection_name=collection,
                query_vector=NamedVector(name="dense", vector=query_vector),
                query_filter=filter_query,
                limit=limit,
            )
        else:  # HYBRID
            # Perform both searches and merge results
            semantic_results = self.client.search(
                collection_name=collection,
                query_vector=NamedVector(name="dense", vector=query_vector),
                query_filter=filter_query,
                limit=limit * 2,  # Get more for merging
            )

            # Simplified hybrid - in production, merge with BM25 results
            results = semantic_results[:limit]

        # Convert results to entities
        entities = []
        for point in results:
            entity = self._point_to_entity(point)
            if entity:
                entities.append((entity, point.score))

        return entities

    def get_entity(self, collection: str, entity_name: str) -> Optional[Entity]:
        """
        Get a specific entity by name.

        Args:
            collection: Collection name.
            entity_name: Entity name.

        Returns:
            Entity object or None if not found.
        """
        # Search for entity by name
        filter_query = Filter(
            must=[
                FieldCondition(key="type", match=MatchValue(value="chunk")),
                FieldCondition(key="chunk_type", match=MatchValue(value="metadata")),
                FieldCondition(key="entity_name", match=MatchValue(value=entity_name)),
            ]
        )

        results = self.client.scroll(
            collection_name=collection,
            scroll_filter=filter_query,
            limit=1,
        )[0]

        if results:
            return self._point_to_entity(results[0])
        return None

    def get_implementation(
        self, collection: str, entity_name: str
    ) -> Optional[str]:
        """
        Get implementation code for an entity.

        Args:
            collection: Collection name.
            entity_name: Entity name.

        Returns:
            Implementation code or None if not found.
        """
        filter_query = Filter(
            must=[
                FieldCondition(key="type", match=MatchValue(value="chunk")),
                FieldCondition(
                    key="chunk_type", match=MatchValue(value="implementation")
                ),
                FieldCondition(key="entity_name", match=MatchValue(value=entity_name)),
            ]
        )

        results = self.client.scroll(
            collection_name=collection,
            scroll_filter=filter_query,
            limit=1,
        )[0]

        if results:
            payload = results[0].payload
            return payload.get("content", "")
        return None

    def get_relations(
        self, collection: str, entity_name: Optional[str] = None
    ) -> List[Relation]:
        """
        Get relations, optionally filtered by entity.

        Args:
            collection: Collection name.
            entity_name: Optional entity to filter relations.

        Returns:
            List of relations.
        """
        must_conditions = [
            FieldCondition(key="chunk_type", match=MatchValue(value="relation")),
        ]

        if entity_name:
            # Get relations where entity is involved
            should_conditions = [
                FieldCondition(
                    key="metadata.from_entity",
                    match=MatchValue(value=entity_name),
                ),
                FieldCondition(
                    key="metadata.to_entity",
                    match=MatchValue(value=entity_name),
                ),
            ]
            filter_query = Filter(must=must_conditions, should=should_conditions)
        else:
            filter_query = Filter(must=must_conditions)

        results, _ = self.client.scroll(
            collection_name=collection,
            scroll_filter=filter_query,
            limit=1000,  # Get all relations
        )

        relations = []
        for point in results:
            relation = self._point_to_relation(point)
            if relation:
                relations.append(relation)

        return relations

    def get_graph_data(
        self,
        collection: str,
        entity: Optional[str] = None,
        entity_types: Optional[List[EntityType]] = None,
        depth: int = 2,
        limit: int = 100,
    ) -> Tuple[List[Entity], List[Relation]]:
        """
        Get graph data for visualization.

        Args:
            collection: Collection name.
            entity: Optional entity to center graph on.
            entity_types: Optional entity type filters.
            depth: Graph traversal depth.
            limit: Maximum nodes to return.

        Returns:
            Tuple of (entities, relations).
        """
        if entity:
            # Start from specific entity and traverse
            entities = set()
            relations = []
            to_visit = {entity}
            visited = set()
            current_depth = 0

            while to_visit and current_depth < depth and len(entities) < limit:
                current_entity = to_visit.pop()
                if current_entity in visited:
                    continue

                visited.add(current_entity)

                # Get the entity
                entity_obj = self.get_entity(collection, current_entity)
                if entity_obj:
                    entities.add(entity_obj.name)

                # Get related entities
                entity_relations = self.get_relations(collection, current_entity)
                for rel in entity_relations:
                    relations.append(rel)
                    # Add connected entities to visit
                    if rel.from_entity == current_entity:
                        to_visit.add(rel.to_entity)
                    else:
                        to_visit.add(rel.from_entity)

                current_depth += 1

            # Get entity objects for all names
            entity_objects = []
            for entity_name in entities:
                entity_obj = self.get_entity(collection, entity_name)
                if entity_obj:
                    entity_objects.append(entity_obj)

            return entity_objects, relations
        else:
            # Get all entities and relations with filters
            must_conditions = [
                FieldCondition(key="type", match=MatchValue(value="chunk")),
                FieldCondition(key="chunk_type", match=MatchValue(value="metadata")),
            ]

            if entity_types:
                must_conditions.append(
                    FieldCondition(
                        key="metadata.entity_type",
                        match=MatchValue(any=[et.value for et in entity_types]),
                    )
                )

            filter_query = Filter(must=must_conditions)

            # Get entities
            entity_results, _ = self.client.scroll(
                collection_name=collection,
                scroll_filter=filter_query,
                limit=limit,
            )

            entities = []
            for point in entity_results:
                entity_obj = self._point_to_entity(point)
                if entity_obj:
                    entities.append(entity_obj)

            # Get relations
            relations = self.get_relations(collection)

            return entities, relations

    def _point_to_entity(self, point: Any) -> Optional[Entity]:
        """Convert a Qdrant point to an Entity object."""
        try:
            payload = point.payload
            metadata = payload.get("metadata", {})

            return Entity(
                id=str(point.id),
                name=payload.get("entity_name", ""),
                entity_type=EntityType(metadata.get("entity_type", "function")),
                observations=metadata.get("observations", []),
                file_path=metadata.get("file_path"),
                line_number=metadata.get("line_number"),
                end_line_number=metadata.get("end_line_number"),
                docstring=metadata.get("docstring"),
                signature=metadata.get("signature"),
                complexity_score=metadata.get("complexity_score"),
                metadata=metadata,
            )
        except Exception as e:
            print(f"Error converting point to entity: {e}")
            return None

    def _point_to_relation(self, point: Any) -> Optional[Relation]:
        """Convert a Qdrant point to a Relation object."""
        try:
            payload = point.payload
            metadata = payload.get("metadata", {})

            return Relation(
                id=str(point.id),
                from_entity=metadata.get("from_entity", ""),
                to_entity=metadata.get("to_entity", ""),
                relation_type=metadata.get("relation_type", "uses"),
                context=metadata.get("context"),
                confidence=metadata.get("confidence", 1.0),
                metadata=metadata,
            )
        except Exception as e:
            print(f"Error converting point to relation: {e}")
            return None

    @staticmethod
    def generate_id(content: str) -> int:
        """Generate a deterministic ID from content."""
        hash_obj = hashlib.sha256(content.encode())
        # Take first 8 bytes and convert to int
        return int.from_bytes(hash_obj.digest()[:8], "big") % (2**63)


# Global service instance
_qdrant_service: Optional[QdrantService] = None


def get_qdrant_service() -> QdrantService:
    """Get or create the global Qdrant service instance."""
    global _qdrant_service
    if _qdrant_service is None:
        _qdrant_service = QdrantService()
    return _qdrant_service