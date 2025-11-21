import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getCollection, getGraphData } from '@/services/api';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import GraphVisualization from '@/components/Graph/GraphVisualization';
import CodeViewer from '@/components/CodeViewer/CodeViewer';
import SearchBar from '@/components/Search/SearchBar';
import { Network, Code, Search, Settings, ChevronLeft } from 'lucide-react';

export default function ProjectExplorer() {
  const { collection } = useParams<{ collection: string }>();
  const [selectedEntity, setSelectedEntity] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'graph' | 'code' | 'both'>('both');

  // Fetch collection info
  const { data: collectionInfo } = useQuery({
    queryKey: ['collection', collection],
    queryFn: () => getCollection(collection!),
    enabled: !!collection,
  });

  // Fetch graph data
  const { data: graphData, isLoading: graphLoading } = useQuery({
    queryKey: ['graph', collection],
    queryFn: () =>
      getGraphData({
        collection: collection!,
        limit: 200,
      }),
    enabled: !!collection,
  });

  const handleEntitySelect = (entityName: string) => {
    setSelectedEntity(entityName);
    if (viewMode === 'graph') {
      setViewMode('both');
    }
  };

  const handleSearchSelect = (result: any) => {
    setSelectedEntity(result.entity.name);
    // You could also center the graph on this entity
  };

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link to="/">
                <Button variant="ghost" size="sm">
                  <ChevronLeft className="mr-1 h-4 w-4" />
                  Collections
                </Button>
              </Link>
              <div>
                <h1 className="text-xl font-semibold flex items-center gap-2">
                  <Network className="h-5 w-5 text-primary" />
                  {collection}
                </h1>
                {collectionInfo && (
                  <p className="text-sm text-muted-foreground">
                    {collectionInfo.entity_count} entities • {collectionInfo.relation_count} relations
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-center gap-4">
              <SearchBar
                collection={collection!}
                onSelect={handleSearchSelect}
                className="w-80"
              />

              <div className="flex gap-1 border rounded-lg p-1">
                <Button
                  size="sm"
                  variant={viewMode === 'graph' ? 'default' : 'ghost'}
                  onClick={() => setViewMode('graph')}
                >
                  <Network className="h-4 w-4" />
                </Button>
                <Button
                  size="sm"
                  variant={viewMode === 'both' ? 'default' : 'ghost'}
                  onClick={() => setViewMode('both')}
                >
                  Both
                </Button>
                <Button
                  size="sm"
                  variant={viewMode === 'code' ? 'default' : 'ghost'}
                  onClick={() => setViewMode('code')}
                >
                  <Code className="h-4 w-4" />
                </Button>
              </div>

              <Button variant="outline" size="sm">
                <Settings className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {graphLoading ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              <p className="mt-4 text-muted-foreground">Loading graph data...</p>
            </div>
          </div>
        ) : (
          <div className="h-full flex">
            {/* Graph Panel */}
            {(viewMode === 'graph' || viewMode === 'both') && (
              <div
                className={`${
                  viewMode === 'both' ? 'w-1/2' : 'w-full'
                } h-full border-r`}
              >
                {graphData ? (
                  <GraphVisualization
                    data={graphData}
                    onNodeClick={handleEntitySelect}
                    selectedNode={selectedEntity}
                  />
                ) : (
                  <div className="h-full flex items-center justify-center">
                    <Card className="p-6 text-center">
                      <p className="text-muted-foreground">No graph data available</p>
                    </Card>
                  </div>
                )}
              </div>
            )}

            {/* Code Panel */}
            {(viewMode === 'code' || viewMode === 'both') && (
              <div
                className={`${
                  viewMode === 'both' ? 'w-1/2' : 'w-full'
                } h-full`}
              >
                {selectedEntity ? (
                  <CodeViewer
                    entityName={selectedEntity}
                    collection={collection!}
                    onClose={() => setSelectedEntity(null)}
                  />
                ) : (
                  <div className="h-full flex items-center justify-center">
                    <Card className="p-6 text-center max-w-md">
                      <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                      <h3 className="text-lg font-semibold mb-2">No Entity Selected</h3>
                      <p className="text-muted-foreground">
                        Click on a node in the graph or use the search bar to select an entity
                        and view its implementation.
                      </p>
                    </Card>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}