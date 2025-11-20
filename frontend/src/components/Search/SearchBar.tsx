import { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { search, getSearchSuggestions } from '@/services/api';
import { Search, Loader2, Sparkles, Code, FileText, GitBranch } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SearchBarProps {
  collection: string;
  onSelect?: (result: any) => void;
  className?: string;
}

export default function SearchBar({ collection, onSelect, className }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [searchMode, setSearchMode] = useState<'semantic' | 'keyword' | 'hybrid'>('hybrid');
  const searchRef = useRef<HTMLDivElement>(null);

  // Debounced search
  const [debouncedQuery, setDebouncedQuery] = useState('');
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query);
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  // Search query
  const { data: searchResults, isLoading } = useQuery({
    queryKey: ['search', debouncedQuery, collection, searchMode],
    queryFn: () =>
      search({
        query: debouncedQuery,
        collection,
        mode: searchMode,
        limit: 10,
      }),
    enabled: debouncedQuery.length >= 2,
  });

  // Get suggestions for autocomplete
  const { data: suggestions } = useQuery({
    queryKey: ['suggestions', query, collection],
    queryFn: () => getSearchSuggestions(query, collection),
    enabled: query.length >= 2 && query.length < 5,
  });

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (result: any) => {
    setQuery('');
    setIsOpen(false);
    if (onSelect) {
      onSelect(result);
    }
  };

  const getEntityIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'function':
      case 'method':
        return <Code className="h-4 w-4 text-blue-500" />;
      case 'class':
      case 'interface':
        return <FileText className="h-4 w-4 text-green-500" />;
      case 'variable':
      case 'constant':
        return <GitBranch className="h-4 w-4 text-purple-500" />;
      default:
        return <FileText className="h-4 w-4 text-gray-500" />;
    }
  };

  const getModeIcon = (mode: typeof searchMode) => {
    switch (mode) {
      case 'semantic':
        return <Sparkles className="h-3 w-3" />;
      case 'keyword':
        return <Code className="h-3 w-3" />;
      case 'hybrid':
        return <Search className="h-3 w-3" />;
    }
  };

  return (
    <div ref={searchRef} className={cn('relative', className)}>
      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          placeholder={`Search ${collection}...`}
          className="w-full pl-9 pr-20 py-2 bg-background border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
        />

        {/* Search Mode Selector */}
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
          {isLoading && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
          <select
            value={searchMode}
            onChange={(e) => setSearchMode(e.target.value as typeof searchMode)}
            className="text-xs bg-background border rounded px-1 py-0.5"
            onClick={(e) => e.stopPropagation()}
          >
            <option value="hybrid">Hybrid</option>
            <option value="semantic">Semantic</option>
            <option value="keyword">Keyword</option>
          </select>
        </div>
      </div>

      {/* Search Results Dropdown */}
      {isOpen && (query.length >= 2 || searchResults) && (
        <div className="absolute top-full mt-1 w-full bg-background border rounded-lg shadow-lg max-h-96 overflow-y-auto z-50">
          {/* Search mode indicator */}
          {searchResults && (
            <div className="px-3 py-2 border-b text-xs text-muted-foreground flex items-center gap-2">
              {getModeIcon(searchMode)}
              <span>
                {searchMode} search • {searchResults.total} results • {searchResults.took_ms.toFixed(1)}ms
              </span>
            </div>
          )}

          {/* Suggestions */}
          {suggestions && suggestions.length > 0 && !searchResults && (
            <div className="p-2">
              <div className="text-xs text-muted-foreground px-2 py-1">Suggestions</div>
              {suggestions.map((suggestion: any, i: number) => (
                <button
                  key={i}
                  className="w-full text-left px-2 py-1 text-sm hover:bg-muted rounded flex items-center gap-2"
                  onClick={() => setQuery(suggestion.text)}
                >
                  {getEntityIcon(suggestion.type)}
                  <span>{suggestion.text}</span>
                  <span className="text-xs text-muted-foreground">({suggestion.type})</span>
                </button>
              ))}
            </div>
          )}

          {/* Search Results */}
          {searchResults && searchResults.results.length > 0 && (
            <div className="p-2">
              {searchResults.results.map((result, i) => (
                <button
                  key={i}
                  className="w-full text-left p-2 hover:bg-muted rounded transition-colors"
                  onClick={() => handleSelect(result)}
                >
                  <div className="flex items-start gap-2">
                    {getEntityIcon(result.entity.entity_type)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">{result.entity.name}</span>
                        <span className="text-xs text-muted-foreground">
                          ({result.entity.entity_type})
                        </span>
                        <span className="text-xs px-1.5 py-0.5 bg-primary/10 text-primary rounded">
                          {(result.score * 100).toFixed(0)}%
                        </span>
                      </div>
                      {result.entity.file_path && (
                        <div className="text-xs text-muted-foreground truncate">
                          {result.entity.file_path}
                          {result.entity.line_number && `:${result.entity.line_number}`}
                        </div>
                      )}
                      {result.highlights.length > 0 && (
                        <div className="text-xs text-muted-foreground mt-1 line-clamp-2">
                          {result.highlights[0]}
                        </div>
                      )}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* No results */}
          {searchResults && searchResults.results.length === 0 && (
            <div className="p-4 text-center text-sm text-muted-foreground">
              No results found for "{query}"
            </div>
          )}

          {/* Loading */}
          {isLoading && !searchResults && (
            <div className="p-4 text-center">
              <Loader2 className="h-6 w-6 animate-spin mx-auto text-muted-foreground" />
              <p className="text-sm text-muted-foreground mt-2">Searching...</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}