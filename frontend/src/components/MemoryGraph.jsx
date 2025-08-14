import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import cola from 'cytoscape-cola';

// Register the cola layout
cytoscape.use(cola);

const MemoryGraph = ({ memories, relationships, onNodeClick }) => {
  const cyRef = useRef(null);
  const containerRef = useRef(null);
  const [cy, setCy] = useState(null);

  // Get mood color
  const getMoodColor = (mood) => {
    const colors = {
      Happy: '#10b981',
      Sad: '#3b82f6',
      Angry: '#ef4444',
      Calm: '#8b5cf6',
      Neutral: '#6b7280'
    };
    return colors[mood] || colors.Neutral;
  };

  useEffect(() => {
    if (!containerRef.current || !memories || memories.length === 0) return;

    // Initialize Cytoscape
    const cyInstance = cytoscape({
      container: containerRef.current,
      elements: [
        // Nodes (memories)
        ...memories.map(memory => ({
          data: { 
            id: memory.id, 
            label: memory.text.substring(0, 30) + '...',
            fullText: memory.full_text || memory.text,
            mood: memory.mood,
            date: memory.created_at,
            keywords: memory.keywords || []
          },
          classes: memory.mood
        })),
        // Edges (relationships)
        ...relationships.map(rel => ({
          data: { 
            id: `${rel.source}-${rel.target}`,
            source: rel.source, 
            target: rel.target, 
            strength: rel.strength,
            type: rel.type,
            reasons: rel.reasons
          }
        }))
      ],
      style: [
        {
          selector: 'node',
          style: {
            'background-color': (ele) => getMoodColor(ele.data('mood')),
            'label': 'data(label)',
            'text-wrap': 'wrap',
            'text-max-width': '120px',
            'font-size': '12px',
            'text-valign': 'center',
            'text-halign': 'center',
            'width': (ele) => Math.min(30 + ele.degree() * 5, 80),
            'height': (ele) => Math.min(30 + ele.degree() * 5, 80),
            'border-width': 2,
            'border-color': '#fff',
            'overlay-padding': '6px'
          }
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#fbbf24',
            'background-color': (ele) => getMoodColor(ele.data('mood'))
          }
        },
        {
          selector: 'edge',
          style: {
            'width': (ele) => ele.data('strength') * 5,
            'line-color': '#e5e7eb',
            'target-arrow-color': '#9ca3af',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'opacity': (ele) => 0.3 + ele.data('strength') * 0.7
          }
        },
        {
          selector: 'edge[type = "temporal"]',
          style: {
            'line-color': '#3b82f6',
            'target-arrow-color': '#3b82f6',
            'line-style': 'dashed'
          }
        },
        {
          selector: 'edge[type = "semantic"]',
          style: {
            'line-color': '#10b981',
            'target-arrow-color': '#10b981'
          }
        },
        {
          selector: 'edge[type = "entity_based"]',
          style: {
            'line-color': '#f59e0b',
            'target-arrow-color': '#f59e0b'
          }
        }
      ],
      layout: {
        name: 'cola',
        animate: true,
        randomize: false,
        avoidOverlap: true,
        nodeSpacing: 50,
        edgeLength: (edge) => 150 / edge.data('strength'),
        maxSimulationTime: 2000,
        fit: true,
        padding: 20
      },
      minZoom: 0.1,
      maxZoom: 3,
      wheelSensitivity: 0.2
    });

    // Add event handlers
    cyInstance.on('tap', 'node', (evt) => {
      const node = evt.target;
      if (onNodeClick) {
        onNodeClick({
          id: node.data('id'),
          text: node.data('fullText'),
          mood: node.data('mood'),
          date: node.data('date'),
          keywords: node.data('keywords')
        });
      }
    });

    // Add hover effects
    cyInstance.on('mouseover', 'node', (evt) => {
      evt.target.style('z-index', 999);
      containerRef.current.style.cursor = 'pointer';
    });

    cyInstance.on('mouseout', 'node', (evt) => {
      evt.target.style('z-index', 0);
      containerRef.current.style.cursor = 'default';
    });

    setCy(cyInstance);
    cyRef.current = cyInstance;

    // Cleanup
    return () => {
      if (cyInstance) {
        cyInstance.destroy();
      }
    };
  }, [memories, relationships, onNodeClick]);

  // Fit graph to container on resize
  useEffect(() => {
    const handleResize = () => {
      if (cy) {
        cy.resize();
        cy.fit();
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [cy]);

  const handleZoomIn = () => {
    if (cy) {
      cy.zoom(cy.zoom() * 1.2);
      cy.center();
    }
  };

  const handleZoomOut = () => {
    if (cy) {
      cy.zoom(cy.zoom() * 0.8);
      cy.center();
    }
  };

  const handleFit = () => {
    if (cy) {
      cy.fit();
    }
  };

  const handleLayout = (layoutName) => {
    if (cy) {
      cy.layout({ 
        name: layoutName,
        animate: true,
        animationDuration: 1000,
        fit: true,
        padding: 20
      }).run();
    }
  };

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div 
        ref={containerRef} 
        style={{ 
          width: '100%', 
          height: '600px',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          backgroundColor: '#f9fafb'
        }} 
      />
      
      {/* Graph Controls */}
      <div style={{
        position: 'absolute',
        top: '10px',
        right: '10px',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        backgroundColor: 'white',
        padding: '8px',
        borderRadius: '8px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <button onClick={handleZoomIn} title="Zoom In" style={buttonStyle}>
          +
        </button>
        <button onClick={handleZoomOut} title="Zoom Out" style={buttonStyle}>
          -
        </button>
        <button onClick={handleFit} title="Fit to Screen" style={buttonStyle}>
          ⊡
        </button>
        <hr style={{ margin: '4px 0', border: 'none', borderTop: '1px solid #e5e7eb' }} />
        <button onClick={() => handleLayout('grid')} title="Grid Layout" style={buttonStyle}>
          ⊞
        </button>
        <button onClick={() => handleLayout('circle')} title="Circle Layout" style={buttonStyle}>
          ○
        </button>
        <button onClick={() => handleLayout('cola')} title="Force Layout" style={buttonStyle}>
          ≈
        </button>
      </div>

      {/* Legend */}
      <div style={{
        position: 'absolute',
        bottom: '10px',
        left: '10px',
        backgroundColor: 'white',
        padding: '12px',
        borderRadius: '8px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        fontSize: '12px'
      }}>
        <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>Connections</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '4px' }}>
          <div style={{ width: '20px', height: '2px', backgroundColor: '#10b981' }}></div>
          <span>Semantic (similar content)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '4px' }}>
          <div style={{ width: '20px', height: '2px', backgroundColor: '#3b82f6', border: '1px dashed #3b82f6' }}></div>
          <span>Temporal (close in time)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <div style={{ width: '20px', height: '2px', backgroundColor: '#f59e0b' }}></div>
          <span>Entity-based (shared topics)</span>
        </div>
      </div>
    </div>
  );
};

const buttonStyle = {
  width: '32px',
  height: '32px',
  border: '1px solid #e5e7eb',
  borderRadius: '4px',
  backgroundColor: 'white',
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: '16px',
  fontWeight: 'bold',
  color: '#374151'
};

export default MemoryGraph;
