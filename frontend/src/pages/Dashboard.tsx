import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { getCollections } from '@/services/api';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Database, FileCode2, GitBranch, Activity, RefreshCw, Eye } from 'lucide-react';

export default function Dashboard() {
  const { data: collections, isLoading, error } = useQuery({
    queryKey: ['collections'],
    queryFn: getCollections,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <div className="container mx-auto py-12">
          <h1 className="text-4xl font-bold mb-8">Claude Code Memory Explorer</h1>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="loading-pulse">
                <CardHeader>
                  <div className="h-6 bg-muted rounded w-3/4"></div>
                  <div className="h-4 bg-muted rounded w-1/2 mt-2"></div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="h-4 bg-muted rounded"></div>
                    <div className="h-4 bg-muted rounded"></div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="text-destructive">Error Loading Collections</CardTitle>
            <CardDescription>
              Failed to connect to the backend API. Please ensure the server is running.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <pre className="text-sm text-muted-foreground">
              {error instanceof Error ? error.message : 'Unknown error'}
            </pre>
          </CardContent>
          <CardFooter>
            <Button onClick={() => window.location.reload()}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Retry
            </Button>
          </CardFooter>
        </Card>
      </div>
    );
  }

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'healthy':
        return 'text-green-600 bg-green-100';
      case 'warning':
        return 'text-yellow-600 bg-yellow-100';
      case 'error':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const formatFileSize = (mb: number) => {
    if (mb < 1) return `${(mb * 1024).toFixed(1)} KB`;
    if (mb > 1024) return `${(mb / 1024).toFixed(2)} GB`;
    return `${mb.toFixed(1)} MB`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-secondary/20">
      <div className="container mx-auto py-12">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
            Claude Code Memory Explorer
          </h1>
          <p className="text-muted-foreground">
            Explore and visualize your indexed codebases with semantic search and interactive graphs
          </p>
        </div>

        {/* Collection Grid */}
        {collections && collections.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {collections.map((collection) => (
              <Card key={collection.name} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <Database className="h-5 w-5 text-primary" />
                        {collection.name}
                      </CardTitle>
                      <CardDescription className="mt-1">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getHealthColor(
                            collection.health
                          )}`}
                        >
                          <Activity className="h-3 w-3 mr-1" />
                          {collection.health}
                        </span>
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground flex items-center gap-1">
                        <FileCode2 className="h-4 w-4" />
                        Entities
                      </span>
                      <span className="font-medium">{collection.entity_count.toLocaleString()}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground flex items-center gap-1">
                        <GitBranch className="h-4 w-4" />
                        Relations
                      </span>
                      <span className="font-medium">{collection.relation_count.toLocaleString()}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Size</span>
                      <span className="font-medium">{formatFileSize(collection.size_mb)}</span>
                    </div>
                  </div>
                </CardContent>
                <CardFooter className="flex gap-2">
                  <Link to={`/project/${collection.name}`} className="flex-1">
                    <Button className="w-full" size="sm">
                      <Eye className="mr-2 h-4 w-4" />
                      Explore
                    </Button>
                  </Link>
                  <Button variant="outline" size="sm">
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="max-w-2xl mx-auto">
            <CardHeader className="text-center">
              <CardTitle>No Collections Found</CardTitle>
              <CardDescription>
                No indexed codebases found. Use the claude-indexer CLI to index your first project.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="bg-muted p-4 rounded-lg">
                <p className="font-mono text-sm">
                  claude-indexer index -p /path/to/project -c my-collection
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Footer Stats */}
        {collections && collections.length > 0 && (
          <div className="mt-12 text-center text-sm text-muted-foreground">
            <p>
              {collections.length} collection{collections.length !== 1 ? 's' : ''} •{' '}
              {collections.reduce((acc, c) => acc + c.entity_count, 0).toLocaleString()} total entities •{' '}
              {collections.reduce((acc, c) => acc + c.relation_count, 0).toLocaleString()} total relations
            </p>
          </div>
        )}
      </div>
    </div>
  );
}