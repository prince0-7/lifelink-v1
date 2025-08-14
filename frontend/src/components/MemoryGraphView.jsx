import React, { useState, useEffect } from 'react';
import MemoryGraph from './MemoryGraph';
import { getMemoryGraph, analyzeRelationships, detectClusters } from '../services/api';

const MemoryGraphView = () => {
  const [graphData, setGraphData] = useState(null);
  const [timeRange, setTimeRange] = useState('month');
  const [minStrength, setMinStrength] = useState(0.3);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedMemory, setSelectedMemory] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    loadGraphData();
  }, [timeRange, minStrength]);

  const loadGraphData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getMemoryGraph(timeRange, minStrength);
      setGraphData(data);
    } catch (error) {
      console.error('Error loading graph data:', error);
      setError('Failed to load memory graph. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeRelationships = async () => {
    setAnalyzing(true);
    try {
      const result = await analyzeRelationships(false);
      alert(`Analyzed ${result.count} relationships! Found ${result.strong_connections} strong connections.`);
      // Reload graph data
      await loadGraphData();
    } catch (error) {
      console.error('Error analyzing relationships:', error);
      alert('Failed to analyze relationships. Please try again.');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleDetectClusters = async () => {
    setAnalyzing(true);
    try {
      const result = await detectClusters();
      alert(`Detected ${result.count} memory clusters!`);
      // Reload graph data
      await loadGraphData();
    } catch (error) {
      console.error('Error detecting clusters:', error);
      alert('Failed to detect clusters. Please try again.');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleNodeClick = (memory) => {
    setSelectedMemory(memory);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <div>Loading memory graph...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <div style={{ textAlign: 'center' }}>
          <p style={{ color: '#ef4444' }}>{error}</p>
          <button onClick={loadGraphData} style={buttonStyle}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  const hasData = graphData && graphData.nodes && graphData.nodes.length > 0;

  return (
    <div style={{ padding: '20px' }}>
      <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '20px' }}>
        Memory Relationship Graph
      </h2>

      {/* Controls */}
      <div style={{ 
        display: 'flex', 
        gap: '20px', 
        marginBottom: '20px',
        flexWrap: 'wrap',
        alignItems: 'center'
      }}>
        <div>
          <label style={{ marginRight: '8px' }}>Time Range:</label>
          <select 
            value={timeRange} 
            onChange={(e) => setTimeRange(e.target.value)}
            style={selectStyle}
          >
            <option value="week">Past Week</option>
            <option value="month">Past Month</option>
            <option value="year">Past Year</option>
            <option value="all">All Time</option>
          </select>
        </div>
        
        <div>
          <label style={{ marginRight: '8px' }}>Min Connection Strength:</label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={minStrength}
            onChange={(e) => setMinStrength(parseFloat(e.target.value))}
            style={{ verticalAlign: 'middle' }}
          />
          <span style={{ marginLeft: '8px' }}>{minStrength.toFixed(1)}</span>
        </div>

        <button 
          onClick={handleAnalyzeRelationships}
          disabled={analyzing}
          style={{ ...buttonStyle, marginLeft: 'auto' }}
        >
          {analyzing ? 'Analyzing...' : 'Analyze Relationships'}
        </button>

        <button 
          onClick={handleDetectClusters}
          disabled={analyzing || !hasData}
          style={buttonStyle}
        >
          Detect Clusters
        </button>
      </div>

      {/* Graph */}
      {hasData ? (
        <>
          <MemoryGraph 
            memories={graphData.nodes} 
            relationships={graphData.edges} 
            onNodeClick={handleNodeClick}
          />
          
          {/* Stats */}
          <div style={{
            marginTop: '20px',
            padding: '16px',
            backgroundColor: '#f3f4f6',
            borderRadius: '8px'
          }}>
            <h3 style={{ fontWeight: 'bold', marginBottom: '8px' }}>Graph Statistics</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
              <div>
                <span style={{ fontWeight: '500' }}>Total Memories:</span> {graphData.stats.total_memories}
              </div>
              <div>
                <span style={{ fontWeight: '500' }}>Connections:</span> {graphData.stats.total_connections}
              </div>
              <div>
                <span style={{ fontWeight: '500' }}>Avg Connection Strength:</span> {graphData.stats.avg_connection_strength}
              </div>
              {graphData.stats.clusters_count > 0 && (
                <div>
                  <span style={{ fontWeight: '500' }}>Clusters:</span> {graphData.stats.clusters_count}
                </div>
              )}
            </div>
          </div>

          {/* Clusters */}
          {graphData.clusters && graphData.clusters.length > 0 && (
            <div style={{
              marginTop: '20px',
              padding: '16px',
              backgroundColor: '#f3f4f6',
              borderRadius: '8px'
            }}>
              <h3 style={{ fontWeight: 'bold', marginBottom: '8px' }}>Memory Clusters</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '12px' }}>
                {graphData.clusters.map(cluster => (
                  <div 
                    key={cluster.id}
                    style={{
                      padding: '12px',
                      backgroundColor: 'white',
                      borderRadius: '6px',
                      border: '1px solid #e5e7eb'
                    }}
                  >
                    <h4 style={{ fontWeight: 'bold', marginBottom: '4px' }}>{cluster.name}</h4>
                    <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>
                      {cluster.summary}
                    </p>
                    <div style={{ fontSize: '12px' }}>
                      <span style={{ fontWeight: '500' }}>Theme:</span> {cluster.theme} | 
                      <span style={{ fontWeight: '500', marginLeft: '8px' }}>Size:</span> {cluster.memory_ids.length} memories
                    </div>
                    {cluster.keywords && cluster.keywords.length > 0 && (
                      <div style={{ marginTop: '8px', display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                        {cluster.keywords.slice(0, 5).map((keyword, idx) => (
                          <span 
                            key={idx}
                            style={{
                              fontSize: '11px',
                              padding: '2px 6px',
                              backgroundColor: '#e5e7eb',
                              borderRadius: '4px'
                            }}
                          >
                            {keyword}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Selected Memory Details */}
          {selectedMemory && (
            <div style={{
              marginTop: '20px',
              padding: '16px',
              backgroundColor: '#f9fafb',
              borderRadius: '8px',
              border: '1px solid #e5e7eb'
            }}>
              <h3 style={{ fontWeight: 'bold', marginBottom: '8px' }}>Selected Memory</h3>
              <p style={{ marginBottom: '8px' }}>{selectedMemory.text}</p>
              <div style={{ fontSize: '14px', color: '#6b7280' }}>
                <span style={{ fontWeight: '500' }}>Mood:</span> {selectedMemory.mood} | 
                <span style={{ fontWeight: '500', marginLeft: '12px' }}>Date:</span> {new Date(selectedMemory.date).toLocaleDateString()}
              </div>
              {selectedMemory.keywords && selectedMemory.keywords.length > 0 && (
                <div style={{ marginTop: '8px' }}>
                  <span style={{ fontWeight: '500', fontSize: '14px' }}>Keywords:</span>
                  <div style={{ marginTop: '4px', display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                    {selectedMemory.keywords.map((keyword, idx) => (
                      <span 
                        key={idx}
                        style={{
                          fontSize: '12px',
                          padding: '2px 6px',
                          backgroundColor: '#e5e7eb',
                          borderRadius: '4px'
                        }}
                      >
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      ) : (
        <div style={{ 
          textAlign: 'center', 
          padding: '60px 20px',
          backgroundColor: '#f9fafb',
          borderRadius: '8px'
        }}>
          <p style={{ fontSize: '18px', marginBottom: '20px' }}>
            No memory connections found for the selected time range.
          </p>
          <p style={{ color: '#6b7280', marginBottom: '20px' }}>
            Try analyzing relationships first or adjusting the filters.
          </p>
          <button onClick={handleAnalyzeRelationships} style={buttonStyle}>
            Analyze Relationships Now
          </button>
        </div>
      )}
    </div>
  );
};

const buttonStyle = {
  padding: '8px 16px',
  backgroundColor: '#3b82f6',
  color: 'white',
  border: 'none',
  borderRadius: '6px',
  cursor: 'pointer',
  fontWeight: '500',
  fontSize: '14px'
};

const selectStyle = {
  padding: '6px 12px',
  border: '1px solid #e5e7eb',
  borderRadius: '6px',
  backgroundColor: 'white',
  cursor: 'pointer'
};

export default MemoryGraphView;
