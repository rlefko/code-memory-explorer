import axios from 'axios';
import * as d3 from 'd3';

// Create axios instance with default config
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface CollectionInfo {
  name: string;
  entity_count: number;
  relation_count: number;
  file_count: number;
  last_indexed: string;
  size_mb: number;
  health: 'healthy' | 'warning' | 'error';
  metadata: Record<string, any>;
}

export interface Entity {
  id: string;
  name: string;
  entity_type: string;
  observations: string[];
  file_path?: string;
  line_number?: number;
  end_line_number?: number;
  docstring?: string;
  signature?: string;
  complexity_score?: number;
  metadata: Record<string, any>;
}

export interface Relation {
  id: string;
  from_entity: string;
  to_entity: string;
  relation_type: string;
  context?: string;
  confidence: number;
  metadata: Record<string, any>;
}

export interface SearchResult {
  entity: Entity;
  score: number;
  chunk_type: 'metadata' | 'implementation';
  highlights: string[];
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
  mode: 'semantic' | 'keyword' | 'hybrid';
  took_ms: number;
}

export interface GraphNode extends d3.SimulationNodeDatum {
  id: string;
  name: string;
  entity_type: string;
  size: number;
  group: number;
  metadata: Record<string, any>;
}

export interface GraphEdge {
  source: string;
  target: string;
  relation_type: string;
  weight: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  metadata: Record<string, any>;
}

export interface EntityRelation {
  from: string;
  to: string;
  type: string;
  confidence?: number;
  context?: string;
}

export interface EntityRelationsResponse {
  incoming_relations: EntityRelation[];
  outgoing_relations: EntityRelation[];
}

export interface EntityDependency {
  id: string;
  name: string;
  entity_type: string;
  file_path?: string;
}

export interface ImplementationResponse {
  implementation: string;
  dependencies?: EntityDependency[];
  scope: 'minimal' | 'logical' | 'dependencies';
}

// API functions

// Collections
export const getCollections = async (): Promise<CollectionInfo[]> => {
  const response = await api.get('/collections');
  return response.data;
};

export const getCollection = async (name: string): Promise<CollectionInfo> => {
  const response = await api.get(`/collections/${name}`);
  return response.data;
};

export const getCollectionStats = async (name: string) => {
  const response = await api.get(`/collections/${name}/stats`);
  return response.data;
};

export const reindexCollection = async (name: string, projectPath?: string) => {
  const response = await api.post(`/collections/${name}/reindex`, { project_path: projectPath });
  return response.data;
};

export const deleteCollection = async (name: string) => {
  const response = await api.delete(`/collections/${name}`);
  return response.data;
};

// Search
export const search = async (params: {
  query: string;
  collection?: string;
  mode?: 'semantic' | 'keyword' | 'hybrid';
  entity_types?: string[];
  limit?: number;
  offset?: number;
  include_implementation?: boolean;
}): Promise<SearchResponse> => {
  const response = await api.post('/search', params);
  return response.data;
};

export const searchSimilar = async (params: {
  query: string;
  collection: string;
  entity_types?: string[];
  limit?: number;
  mode?: 'semantic' | 'keyword' | 'hybrid';
}) => {
  const response = await api.post('/search/similar', params);
  return response.data;
};

export const getSearchSuggestions = async (query: string, collection: string) => {
  const response = await api.get('/search/suggestions', {
    params: { query, collection },
  });
  return response.data;
};

// Entities
export const getEntities = async (params: {
  collection: string;
  entity_types?: string[];
  limit?: number;
  offset?: number;
}): Promise<Entity[]> => {
  const response = await api.get('/entities', { params });
  return response.data;
};

export const getEntity = async (entityName: string, collection: string): Promise<Entity> => {
  const response = await api.get(`/entities/${entityName}`, {
    params: { collection },
  });
  return response.data;
};

export const getEntityImplementation = async (
  entityName: string,
  collection: string,
  scope: 'minimal' | 'logical' | 'dependencies' = 'minimal'
): Promise<ImplementationResponse> => {
  const response = await api.get(`/entities/${entityName}/implementation`, {
    params: { collection, scope },
  });
  return response.data;
};

export const getEntityRelations = async (entityName: string, collection: string): Promise<EntityRelationsResponse> => {
  const response = await api.get(`/entities/${entityName}/relations`, {
    params: { collection },
  });
  return response.data;
};

// Graph
export const getGraphData = async (params: {
  collection: string;
  entity?: string;
  entity_types?: string[];
  depth?: number;
  limit?: number;
}): Promise<GraphData> => {
  const response = await api.post('/graph', params);
  return response.data;
};

export const getGraphLayout = async (
  collection: string,
  layoutType: 'force' | 'hierarchical' | 'radial' = 'force',
  entity?: string,
  limit: number = 100
) => {
  const response = await api.get(`/graph/layout/${collection}`, {
    params: { layout_type: layoutType, entity, limit },
  });
  return response.data;
};

export const getGraphClusters = async (collection: string, minClusterSize: number = 3) => {
  const response = await api.get(`/graph/clusters/${collection}`, {
    params: { min_cluster_size: minClusterSize },
  });
  return response.data;
};

export const findPaths = async (
  collection: string,
  source: string,
  target: string,
  maxDepth: number = 5
) => {
  const response = await api.get(`/graph/paths/${collection}`, {
    params: { source, target, max_depth: maxDepth },
  });
  return response.data;
};

// WebSocket
export const createWebSocketConnection = (clientId: string): WebSocket => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;
  return new WebSocket(`${protocol}//${host}/ws/${clientId}`);
};

export default api;