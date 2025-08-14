# Memory Relationship Graph - Implementation Guide

## Overview
The Memory Relationship Graph is a visual representation of how memories connect to each other, creating a mind map of life experiences.

## Technical Architecture

### Frontend Components

#### 1. Graph Visualization Library Setup
```javascript
// Install D3.js or Cytoscape.js
npm install cytoscape cytoscape-cola cytoscape-popper

// Or for D3.js
npm install d3 d3-force-3d
```

#### 2. Memory Graph Component
```jsx
// frontend/src/components/MemoryGraph.jsx
import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import cola from 'cytoscape-cola';

cytoscape.use(cola);

const MemoryGraph = ({ memories, relationships }) => {
  const cyRef = useRef(null);
  const [cy, setCy] = useState(null);

  useEffect(() => {
    const cyInstance = cytoscape({
      container: cyRef.current,
      elements: [
        // Nodes (memories)
        ...memories.map(memory => ({
          data: { 
            id: memory.id, 
            label: memory.text.substring(0, 50) + '...',
            mood: memory.mood,
            date: memory.created_at
          }
        })),
        // Edges (relationships)
        ...relationships.map(rel => ({
          data: { 
            source: rel.source, 
            target: rel.target, 
            strength: rel.strength,
            type: rel.type
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
            'text-max-width': '200px',
            'width': (ele) => 30 + ele.degree() * 5,
            'height': (ele) => 30 + ele.degree() * 5
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 'data(strength)',
            'line-color': '#ccc',
            'target-arrow-color': '#ccc',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier'
          }
        }
      ],
      layout: {
        name: 'cola',
        animate: true,
        randomize: false,
        maxSimulationTime: 2000
      }
    });

    setCy(cyInstance);
  }, [memories, relationships]);

  return <div ref={cyRef} style={{ width: '100%', height: '600px' }} />;
};
```

### Backend API Endpoints

#### 1. Relationship Detection Service
```python
# backend/services/relationship_service.py
from typing import List, Dict, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import spacy
from datetime import datetime, timedelta

class RelationshipService:
    def __init__(self):
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.nlp = spacy.load('en_core_web_sm')
    
    def find_relationships(self, memories: List[Dict]) -> List[Dict]:
        """Find relationships between memories based on multiple factors"""
        relationships = []
        
        # Generate embeddings for all memories
        texts = [m['text'] for m in memories]
        embeddings = self.encoder.encode(texts)
        
        # Calculate similarity matrix
        similarity_matrix = cosine_similarity(embeddings)
        
        for i in range(len(memories)):
            for j in range(i + 1, len(memories)):
                relationship = self._analyze_relationship(
                    memories[i], 
                    memories[j], 
                    similarity_matrix[i][j]
                )
                if relationship['strength'] > 0.3:  # Threshold
                    relationships.append(relationship)
        
        return relationships
    
    def _analyze_relationship(self, mem1: Dict, mem2: Dict, similarity: float) -> Dict:
        """Analyze relationship between two memories"""
        relationship = {
            'source': mem1['id'],
            'target': mem2['id'],
            'strength': 0,
            'type': 'related',
            'reasons': []
        }
        
        # 1. Semantic similarity
        if similarity > 0.7:
            relationship['strength'] += similarity * 0.4
            relationship['reasons'].append('semantic_similarity')
        
        # 2. Temporal proximity
        date1 = datetime.fromisoformat(mem1['created_at'])
        date2 = datetime.fromisoformat(mem2['created_at'])
        time_diff = abs((date1 - date2).days)
        
        if time_diff < 7:  # Within a week
            relationship['strength'] += 0.3
            relationship['type'] = 'temporal'
            relationship['reasons'].append('temporal_proximity')
        
        # 3. Entity overlap
        entities1 = self._extract_entities(mem1['text'])
        entities2 = self._extract_entities(mem2['text'])
        overlap = len(entities1.intersection(entities2))
        
        if overlap > 0:
            relationship['strength'] += overlap * 0.1
            relationship['type'] = 'entity_based'
            relationship['reasons'].append('shared_entities')
        
        # 4. Mood correlation
        if mem1.get('mood') == mem2.get('mood'):
            relationship['strength'] += 0.2
            relationship['reasons'].append('same_mood')
        
        return relationship
    
    def _extract_entities(self, text: str) -> set:
        """Extract named entities from text"""
        doc = self.nlp(text)
        return {ent.text.lower() for ent in doc.ents}
```

#### 2. Graph API Endpoints
```python
# backend/routers/graph.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from services.relationship_service import RelationshipService
from models import Memory
from dependencies import get_current_user

router = APIRouter()
relationship_service = RelationshipService()

@router.get("/memories/graph")
async def get_memory_graph(
    current_user = Depends(get_current_user),
    time_range: str = "all",  # all, year, month, week
    min_strength: float = 0.3
):
    """Get memory graph data with relationships"""
    
    # Fetch memories based on time range
    memories = await Memory.find(
        Memory.user_id == current_user.id
    ).to_list()
    
    # Filter by time range if specified
    if time_range != "all":
        memories = filter_by_time_range(memories, time_range)
    
    # Find relationships
    relationships = relationship_service.find_relationships(memories)
    
    # Filter by minimum strength
    relationships = [r for r in relationships if r['strength'] >= min_strength]
    
    # Build graph data
    graph_data = {
        "nodes": [
            {
                "id": str(m.id),
                "text": m.text,
                "mood": m.mood,
                "created_at": m.created_at.isoformat(),
                "tags": m.tags
            }
            for m in memories
        ],
        "edges": relationships,
        "stats": {
            "total_memories": len(memories),
            "total_connections": len(relationships),
            "avg_connection_strength": np.mean([r['strength'] for r in relationships]) if relationships else 0
        }
    }
    
    return graph_data

@router.post("/memories/{memory_id}/relate")
async def manually_relate_memories(
    memory_id: str,
    related_memory_id: str,
    relationship_type: str = "manual",
    current_user = Depends(get_current_user)
):
    """Manually create a relationship between memories"""
    # Implementation for manual relationship creation
    pass
```

### Database Schema Updates

```python
# backend/models.py
from beanie import Document
from typing import List, Optional
from datetime import datetime

class MemoryRelationship(Document):
    source_memory_id: str
    target_memory_id: str
    user_id: str
    relationship_type: str  # semantic, temporal, entity_based, manual
    strength: float  # 0.0 to 1.0
    reasons: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "memory_relationships"
        indexes = [
            [("user_id", 1), ("source_memory_id", 1)],
            [("user_id", 1), ("target_memory_id", 1)]
        ]
```

### Advanced Features

#### 1. Cluster Detection
```python
def detect_memory_clusters(relationships: List[Dict], memories: List[Dict]) -> List[Dict]:
    """Detect clusters of related memories using community detection"""
    import networkx as nx
    from networkx.algorithms import community
    
    # Build network graph
    G = nx.Graph()
    for mem in memories:
        G.add_node(mem['id'], **mem)
    
    for rel in relationships:
        G.add_edge(rel['source'], rel['target'], weight=rel['strength'])
    
    # Detect communities
    communities = community.louvain_communities(G)
    
    clusters = []
    for i, community_nodes in enumerate(communities):
        cluster_memories = [m for m in memories if m['id'] in community_nodes]
        clusters.append({
            'id': f'cluster_{i}',
            'memories': cluster_memories,
            'theme': detect_cluster_theme(cluster_memories),
            'size': len(community_nodes)
        })
    
    return clusters
```

#### 2. Path Finding
```python
@router.get("/memories/{memory_id}/path/{target_id}")
async def find_memory_path(
    memory_id: str,
    target_id: str,
    current_user = Depends(get_current_user)
):
    """Find the path between two memories through relationships"""
    # Implementation using Dijkstra's algorithm
    pass
```

### Frontend Integration

```jsx
// frontend/src/components/MemoryGraphView.jsx
import React, { useState, useEffect } from 'react';
import MemoryGraph from './MemoryGraph';
import { getMemoryGraph } from '../services/api';

const MemoryGraphView = () => {
  const [graphData, setGraphData] = useState(null);
  const [timeRange, setTimeRange] = useState('month');
  const [minStrength, setMinStrength] = useState(0.3);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadGraphData();
  }, [timeRange, minStrength]);

  const loadGraphData = async () => {
    setLoading(true);
    try {
      const data = await getMemoryGraph(timeRange, minStrength);
      setGraphData(data);
    } catch (error) {
      console.error('Error loading graph data:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="memory-graph-container">
      <div className="graph-controls">
        <select value={timeRange} onChange={(e) => setTimeRange(e.target.value)}>
          <option value="week">Past Week</option>
          <option value="month">Past Month</option>
          <option value="year">Past Year</option>
          <option value="all">All Time</option>
        </select>
        
        <input
          type="range"
          min="0"
          max="1"
          step="0.1"
          value={minStrength}
          onChange={(e) => setMinStrength(parseFloat(e.target.value))}
        />
        <span>Min Connection Strength: {minStrength}</span>
      </div>

      {loading ? (
        <div>Loading graph...</div>
      ) : (
        <>
          <MemoryGraph 
            memories={graphData.nodes} 
            relationships={graphData.edges} 
          />
          <div className="graph-stats">
            <p>Total Memories: {graphData.stats.total_memories}</p>
            <p>Connections: {graphData.stats.total_connections}</p>
            <p>Avg Strength: {graphData.stats.avg_connection_strength.toFixed(2)}</p>
          </div>
        </>
      )}
    </div>
  );
};
```

## Performance Considerations

1. **Caching**: Cache relationship calculations for frequently accessed memories
2. **Batch Processing**: Process relationships in background using Celery
3. **Incremental Updates**: Only recalculate relationships for new memories
4. **Graph Rendering**: Use WebGL-based renderers for large graphs (>1000 nodes)

## Next Steps

1. Implement the backend relationship service
2. Create the graph visualization component
3. Add graph filtering and interaction features
4. Implement cluster detection and themes
5. Add export functionality for graph data
