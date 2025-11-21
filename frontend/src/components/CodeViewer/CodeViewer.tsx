import { useQuery } from '@tanstack/react-query';
import Editor from '@monaco-editor/react';
import {
  getEntityImplementation,
  getEntity,
  getEntityRelations,
  EntityRelation,
  EntityDependency
} from '@/services/api';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { X, FileCode, GitBranch, Layers, ChevronRight, Copy, Maximize2 } from 'lucide-react';
import { useState } from 'react';
import { useToast } from '@/components/ui/use-toast';

interface CodeViewerProps {
  entityName: string;
  collection: string;
  onClose?: () => void;
}

export default function CodeViewer({ entityName, collection, onClose }: CodeViewerProps) {
  const [scope, setScope] = useState<'minimal' | 'logical' | 'dependencies'>('minimal');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const { toast } = useToast();

  // Fetch entity details
  const { data: entity } = useQuery({
    queryKey: ['entity', entityName, collection],
    queryFn: () => getEntity(entityName, collection),
  });

  // Fetch implementation
  const { data: implementation, isLoading: codeLoading } = useQuery({
    queryKey: ['implementation', entityName, collection, scope],
    queryFn: () => getEntityImplementation(entityName, collection, scope),
  });

  // Fetch relations
  const { data: relations } = useQuery({
    queryKey: ['relations', entityName, collection],
    queryFn: () => getEntityRelations(entityName, collection),
  });

  const handleCopyCode = () => {
    if (implementation?.implementation) {
      navigator.clipboard.writeText(implementation.implementation);
      toast({
        title: 'Code copied',
        description: 'Code has been copied to clipboard',
      });
    }
  };

  const getLanguageFromFile = (filepath?: string): string => {
    if (!filepath) return 'plaintext';
    const ext = filepath.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'py':
        return 'python';
      case 'js':
      case 'jsx':
        return 'javascript';
      case 'ts':
      case 'tsx':
        return 'typescript';
      case 'java':
        return 'java';
      case 'go':
        return 'go';
      case 'rs':
        return 'rust';
      case 'cpp':
      case 'cc':
      case 'cxx':
        return 'cpp';
      case 'c':
        return 'c';
      case 'cs':
        return 'csharp';
      case 'rb':
        return 'ruby';
      case 'php':
        return 'php';
      case 'swift':
        return 'swift';
      case 'kt':
        return 'kotlin';
      case 'scala':
        return 'scala';
      case 'sh':
        return 'shell';
      case 'yaml':
      case 'yml':
        return 'yaml';
      case 'json':
        return 'json';
      case 'xml':
        return 'xml';
      case 'html':
        return 'html';
      case 'css':
        return 'css';
      case 'scss':
        return 'scss';
      case 'sql':
        return 'sql';
      case 'md':
        return 'markdown';
      default:
        return 'plaintext';
    }
  };

  return (
    <div className={`h-full flex flex-col bg-background ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}>
      {/* Header */}
      <Card className="rounded-none border-x-0 border-t-0">
        <CardHeader className="py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileCode className="h-5 w-5 text-primary" />
              <div>
                <CardTitle className="text-lg">{entityName}</CardTitle>
                {entity && (
                  <p className="text-sm text-muted-foreground">
                    {entity.entity_type} • {entity.file_path || 'No file'}
                    {entity.line_number && ` • Line ${entity.line_number}`}
                  </p>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="ghost"
                onClick={handleCopyCode}
                disabled={!implementation?.implementation}
              >
                <Copy className="h-4 w-4" />
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setIsFullscreen(!isFullscreen)}
              >
                <Maximize2 className="h-4 w-4" />
              </Button>
              {onClose && (
                <Button size="sm" variant="ghost" onClick={onClose}>
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>

          {/* Scope selector */}
          <div className="flex gap-1 mt-3">
            <Button
              size="sm"
              variant={scope === 'minimal' ? 'default' : 'outline'}
              onClick={() => setScope('minimal')}
            >
              Minimal
            </Button>
            <Button
              size="sm"
              variant={scope === 'logical' ? 'default' : 'outline'}
              onClick={() => setScope('logical')}
            >
              Logical
            </Button>
            <Button
              size="sm"
              variant={scope === 'dependencies' ? 'default' : 'outline'}
              onClick={() => setScope('dependencies')}
            >
              Dependencies
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Code Editor */}
        <div className="flex-1">
          {codeLoading ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                <p className="mt-4 text-muted-foreground">Loading code...</p>
              </div>
            </div>
          ) : (
            <Editor
              height="100%"
              language={getLanguageFromFile(entity?.file_path)}
              value={implementation?.implementation || '// No implementation available'}
              theme="vs-dark"
              options={{
                readOnly: true,
                minimap: { enabled: true },
                fontSize: 14,
                wordWrap: 'on',
                scrollBeyondLastLine: false,
                automaticLayout: true,
              }}
            />
          )}
        </div>

        {/* Side Panel */}
        {!isFullscreen && (
          <div className="w-80 border-l overflow-y-auto">
            {/* Entity Info */}
            {entity && (
              <Card className="m-3">
                <CardHeader className="py-3">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Layers className="h-4 w-4" />
                    Entity Information
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  {entity.signature && (
                    <div>
                      <span className="text-muted-foreground">Signature:</span>
                      <pre className="text-xs mt-1 p-2 bg-muted rounded overflow-x-auto">
                        {entity.signature}
                      </pre>
                    </div>
                  )}
                  {entity.docstring && (
                    <div>
                      <span className="text-muted-foreground">Documentation:</span>
                      <p className="text-xs mt-1">{entity.docstring}</p>
                    </div>
                  )}
                  {entity.observations && entity.observations.length > 0 && (
                    <div>
                      <span className="text-muted-foreground">Observations:</span>
                      <ul className="text-xs mt-1 space-y-1">
                        {entity.observations.map((obs, i) => (
                          <li key={i} className="flex items-start gap-1">
                            <ChevronRight className="h-3 w-3 mt-0.5 flex-shrink-0" />
                            {obs}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {entity.complexity_score && (
                    <div>
                      <span className="text-muted-foreground">Complexity:</span>
                      <span className="ml-2">{entity.complexity_score}</span>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Relations */}
            {relations && (
              <Card className="m-3">
                <CardHeader className="py-3">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <GitBranch className="h-4 w-4" />
                    Relations
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  {relations.incoming_relations.length > 0 && (
                    <div>
                      <span className="text-muted-foreground font-medium">
                        Called by ({relations.incoming_relations.length}):
                      </span>
                      <ul className="text-xs mt-1 space-y-1">
                        {relations.incoming_relations.slice(0, 5).map((rel: EntityRelation, i: number) => (
                          <li key={i} className="flex items-center gap-2">
                            <span className="text-primary cursor-pointer hover:underline">
                              {rel.from}
                            </span>
                            <span className="text-muted-foreground">({rel.type})</span>
                          </li>
                        ))}
                        {relations.incoming_relations.length > 5 && (
                          <li className="text-muted-foreground">
                            ... and {relations.incoming_relations.length - 5} more
                          </li>
                        )}
                      </ul>
                    </div>
                  )}

                  {relations.outgoing_relations.length > 0 && (
                    <div>
                      <span className="text-muted-foreground font-medium">
                        Calls ({relations.outgoing_relations.length}):
                      </span>
                      <ul className="text-xs mt-1 space-y-1">
                        {relations.outgoing_relations.slice(0, 5).map((rel: EntityRelation, i: number) => (
                          <li key={i} className="flex items-center gap-2">
                            <span className="text-primary cursor-pointer hover:underline">
                              {rel.to}
                            </span>
                            <span className="text-muted-foreground">({rel.type})</span>
                          </li>
                        ))}
                        {relations.outgoing_relations.length > 5 && (
                          <li className="text-muted-foreground">
                            ... and {relations.outgoing_relations.length - 5} more
                          </li>
                        )}
                      </ul>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Dependencies (when scope is dependencies) */}
            {scope === 'dependencies' && implementation?.dependencies && implementation.dependencies.length > 0 && (
              <Card className="m-3">
                <CardHeader className="py-3">
                  <CardTitle className="text-sm">Dependencies</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="text-xs space-y-1">
                    {implementation.dependencies.map((dep: EntityDependency) => (
                      <li key={dep.id} className="flex items-center gap-2">
                        <span className="text-primary cursor-pointer hover:underline">
                          {dep.name}
                        </span>
                        <span className="text-muted-foreground">({dep.entity_type})</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}