import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { GraphData, GraphNode, GraphEdge } from '@/services/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ZoomIn, ZoomOut, Maximize2, Filter, Layers } from 'lucide-react';

interface GraphVisualizationProps {
  data: GraphData;
  onNodeClick?: (nodeName: string) => void;
  selectedNode?: string | null;
}

export default function GraphVisualization({
  data,
  onNodeClick,
  selectedNode,
}: GraphVisualizationProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [zoom, setZoom] = useState(1);
  const [filterType, setFilterType] = useState<string | null>(null);

  useEffect(() => {
    if (!svgRef.current || !data.nodes.length) return;

    // Clear previous graph
    d3.select(svgRef.current).selectAll('*').remove();

    // Set up dimensions
    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;

    // Create SVG groups
    const svg = d3.select(svgRef.current);

    // Add zoom behavior
    const zoomBehavior = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 10])
      .on('zoom', (event) => {
        container.attr('transform', event.transform);
        setZoom(event.transform.k);
      });

    svg.call(zoomBehavior);

    const container = svg.append('g');

    // Add arrow markers for directed edges
    svg
      .append('defs')
      .selectAll('marker')
      .data(['arrow'])
      .enter()
      .append('marker')
      .attr('id', 'arrow')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 20)
      .attr('refY', 0)
      .attr('markerWidth', 8)
      .attr('markerHeight', 8)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#4a5568');

    // Filter nodes if needed
    const filteredNodes = filterType
      ? data.nodes.filter((n) => n.entity_type === filterType)
      : data.nodes;

    const nodeIds = new Set(filteredNodes.map((n) => n.id));
    const filteredEdges = data.edges.filter(
      (e) => nodeIds.has(e.source) && nodeIds.has(e.target)
    );

    // Create force simulation
    const simulation = d3
      .forceSimulation<GraphNode>(filteredNodes)
      .force(
        'link',
        d3
          .forceLink<GraphNode, GraphEdge>(filteredEdges)
          .id((d) => d.id)
          .distance(100)
      )
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30));

    // Create links
    const link = container
      .append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(filteredEdges)
      .enter()
      .append('line')
      .attr('class', 'link')
      .attr('stroke', '#4a5568')
      .attr('stroke-width', (d) => Math.sqrt(d.weight))
      .attr('marker-end', 'url(#arrow)')
      .attr('opacity', 0.6);

    // Create node groups
    const node = container
      .append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(filteredNodes)
      .enter()
      .append('g')
      .attr('class', 'node')
      .call(
        d3
          .drag<SVGGElement, GraphNode>()
          .on('start', dragstarted)
          .on('drag', dragged)
          .on('end', dragended) as any
      );

    // Color scale for different entity types
    const colorScale = d3.scaleOrdinal(d3.schemeCategory10);

    // Add circles for nodes
    node
      .append('circle')
      .attr('r', (d) => Math.sqrt(d.size) * 2 + 5)
      .attr('fill', (d) => colorScale(d.entity_type))
      .attr('stroke', (d) => (d.id === selectedNode ? '#000' : '#fff'))
      .attr('stroke-width', (d) => (d.id === selectedNode ? 3 : 1.5))
      .style('cursor', 'pointer')
      .on('click', (_event, d) => {
        if (onNodeClick) {
          onNodeClick(d.id);
        }
      })
      .on('mouseover', function (_event, d) {
        // Highlight connected nodes
        link
          .style('opacity', (l: any) =>
            l.source.id === d.id || l.target.id === d.id ? 1 : 0.1
          );
        node.style('opacity', (n) => {
          const isConnected = filteredEdges.some(
            (e: any) =>
              (e.source.id === d.id && e.target.id === n.id) ||
              (e.target.id === d.id && e.source.id === n.id) ||
              n.id === d.id
          );
          return isConnected ? 1 : 0.1;
        });
      })
      .on('mouseout', function () {
        link.style('opacity', 0.6);
        node.style('opacity', 1);
      });

    // Add labels
    node
      .append('text')
      .text((d) => d.name)
      .attr('x', 0)
      .attr('y', -15)
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .attr('font-weight', (d) => (d.id === selectedNode ? 'bold' : 'normal'))
      .style('pointer-events', 'none');

    // Add tooltips
    node
      .append('title')
      .text(
        (d) =>
          `${d.name}\nType: ${d.entity_type}\n${
            d.metadata.observations
              ? d.metadata.observations[0]
              : 'No description'
          }`
      );

    // Update positions on simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    // Drag functions
    function dragstarted(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event: any, d: any) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    // Cleanup
    return () => {
      simulation.stop();
    };
  }, [data, selectedNode, filterType, onNodeClick]);

  const handleZoomIn = () => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.transition().call(d3.zoom<SVGSVGElement, unknown>().scaleBy as any, 1.3);
  };

  const handleZoomOut = () => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.transition().call(d3.zoom<SVGSVGElement, unknown>().scaleBy as any, 0.7);
  };

  const handleResetZoom = () => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);

    svg
      .transition()
      .call(
        d3.zoom<SVGSVGElement, unknown>().transform as any,
        d3.zoomIdentity.translate(0, 0).scale(1)
      );
  };

  // Get unique entity types for filtering
  const entityTypes = Array.from(new Set(data.nodes.map((n) => n.entity_type)));

  return (
    <div className="h-full relative bg-gradient-to-br from-gray-900 via-slate-900 to-gray-900">
      {/* Controls */}
      <div className="absolute top-4 left-4 z-10 space-y-2">
        <Card className="p-2 flex flex-col gap-1">
          <Button
            size="sm"
            variant="ghost"
            onClick={handleZoomIn}
            title="Zoom In"
          >
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={handleZoomOut}
            title="Zoom Out"
          >
            <ZoomOut className="h-4 w-4" />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={handleResetZoom}
            title="Reset View"
          >
            <Maximize2 className="h-4 w-4" />
          </Button>
        </Card>

        <Card className="p-2">
          <div className="flex items-center gap-1 mb-2">
            <Filter className="h-4 w-4" />
            <span className="text-xs font-medium">Filter</span>
          </div>
          <select
            className="text-xs bg-background border rounded px-2 py-1 w-full"
            value={filterType || ''}
            onChange={(e) => setFilterType(e.target.value || null)}
          >
            <option value="">All Types</option>
            {entityTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </Card>
      </div>

      {/* Stats */}
      <div className="absolute top-4 right-4 z-10">
        <Card className="p-3 text-xs">
          <div className="flex items-center gap-2 mb-1">
            <Layers className="h-4 w-4" />
            <span className="font-medium">Graph Stats</span>
          </div>
          <div className="space-y-1">
            <div>Nodes: {data.nodes.length}</div>
            <div>Edges: {data.edges.length}</div>
            <div>Zoom: {(zoom * 100).toFixed(0)}%</div>
          </div>
        </Card>
      </div>

      {/* SVG */}
      <svg ref={svgRef} className="w-full h-full" />
    </div>
  );
}