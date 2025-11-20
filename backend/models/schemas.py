"""
Pydantic schemas for API request/response models.
"""

from typing import Any, Dict, List, Optional, Literal
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# Enums
class EntityType(str, Enum):
    """Supported entity types in the knowledge graph."""

    PROJECT = "project"
    DIRECTORY = "directory"
    FILE = "file"
    CLASS = "class"
    INTERFACE = "interface"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    CONSTANT = "constant"
    IMPORT = "import"
    MODULE = "module"
    DOCUMENTATION = "documentation"
    TEST = "test"
    CHAT_HISTORY = "chat_history"
    DEBUGGING_PATTERN = "debugging_pattern"
    IMPLEMENTATION_PATTERN = "implementation_pattern"
    INTEGRATION_PATTERN = "integration_pattern"
    CONFIGURATION_PATTERN = "configuration_pattern"
    ARCHITECTURE_PATTERN = "architecture_pattern"
    PERFORMANCE_PATTERN = "performance_pattern"


class RelationType(str, Enum):
    """Supported relation types in the knowledge graph."""

    CONTAINS = "contains"
    IMPORTS = "imports"
    INHERITS = "inherits"
    CALLS = "calls"
    USES = "uses"
    IMPLEMENTS = "implements"
    EXTENDS = "extends"
    DOCUMENTS = "documents"
    TESTS = "tests"
    REFERENCES = "references"


class SearchMode(str, Enum):
    """Search mode for querying."""

    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


class ChunkType(str, Enum):
    """Chunk types for progressive disclosure."""

    METADATA = "metadata"
    IMPLEMENTATION = "implementation"


# Request Models
class SearchRequest(BaseModel):
    """Request model for search operations."""

    query: str = Field(..., min_length=1, description="Search query string")
    collection: Optional[str] = Field(None, description="Collection to search in")
    mode: SearchMode = Field(SearchMode.HYBRID, description="Search mode")
    entity_types: Optional[List[EntityType]] = Field(None, description="Filter by entity types")
    limit: int = Field(20, ge=1, le=100, description="Maximum results to return")
    offset: int = Field(0, ge=0, description="Pagination offset")
    include_implementation: bool = Field(False, description="Include implementation chunks")


class GraphRequest(BaseModel):
    """Request model for graph data retrieval."""

    collection: str = Field(..., description="Collection name")
    entity: Optional[str] = Field(None, description="Focus on specific entity")
    entity_types: Optional[List[EntityType]] = Field(None, description="Filter entity types")
    depth: int = Field(2, ge=1, le=5, description="Graph traversal depth")
    limit: int = Field(100, ge=1, le=500, description="Maximum nodes to return")


# Response Models
class CollectionInfo(BaseModel):
    """Information about a collection."""

    name: str
    entity_count: int = 0
    relation_count: int = 0
    file_count: int = 0
    last_indexed: Optional[datetime] = None
    size_mb: float = 0.0
    health: Literal["healthy", "warning", "error"] = "healthy"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Entity(BaseModel):
    """Entity in the knowledge graph."""

    id: str
    name: str
    entity_type: EntityType
    observations: List[str] = Field(default_factory=list)
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    end_line_number: Optional[int] = None
    docstring: Optional[str] = None
    signature: Optional[str] = None
    complexity_score: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Relation(BaseModel):
    """Relation between entities."""

    id: str
    from_entity: str
    to_entity: str
    relation_type: RelationType
    context: Optional[str] = None
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    """Single search result."""

    entity: Entity
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    chunk_type: ChunkType
    highlights: List[str] = Field(default_factory=list, description="Highlighted snippets")


class SearchResponse(BaseModel):
    """Response for search operations."""

    results: List[SearchResult]
    total: int
    query: str
    mode: SearchMode
    took_ms: float


class GraphNode(BaseModel):
    """Node in the graph visualization."""

    id: str
    name: str
    entity_type: EntityType
    size: int = Field(10, description="Node size based on importance")
    group: int = Field(0, description="Group for coloring")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """Edge in the graph visualization."""

    source: str
    target: str
    relation_type: RelationType
    weight: float = Field(1.0, description="Edge weight for visualization")


class GraphData(BaseModel):
    """Complete graph data for visualization."""

    nodes: List[GraphNode]
    edges: List[GraphEdge]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ImplementationResponse(BaseModel):
    """Response containing entity implementation."""

    entity: Entity
    implementation: str
    language: str
    dependencies: List[Entity] = Field(default_factory=list)
    callers: List[Entity] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


# WebSocket Models
class WSMessage(BaseModel):
    """WebSocket message format."""

    type: Literal["ping", "pong", "update", "error", "subscribe", "unsubscribe"]
    collection: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)