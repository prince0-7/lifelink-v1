import React, { useState } from 'react';

const MemoryTimeline = ({ memories, darkMode, onMemorySelect }) => {
  const [viewMode, setViewMode] = useState('month');
  
  const groupMemoriesByPeriod = () => {
    const grouped = {};
    
    memories.forEach(memory => {
      const date = new Date(memory.date);
      let key;
      
      switch (viewMode) {
        case 'day':
          key = date.toISOString().split('T')[0];
          break;
        case 'week':
          const weekStart = new Date(date);
          weekStart.setDate(date.getDate() - date.getDay());
          key = weekStart.toISOString().split('T')[0];
          break;
        case 'month':
          key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
          break;
        default:
          key = date.toISOString().split('T')[0];
      }
      
      if (!grouped[key]) grouped[key] = [];
      grouped[key].push(memory);
    });
    
    return grouped;
  };

  const timelineData = groupMemoriesByPeriod();
  
  const getMoodColor = (mood) => {
    const colors = {
      'Happy': '#10b981',
      'Sad': '#3b82f6', 
      'Angry': '#ef4444',
      'Calm': '#8b5cf6'
    };
    return colors[mood] || '#6b7280';
  };

  return (
    <div style={{
      margin: '20px 0',
      padding: '20px',
      backgroundColor: darkMode ? '#1e293b' : '#f8fafc',
      borderRadius: '12px',
      border: `1px solid ${darkMode ? '#334155' : '#e2e8f0'}`
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px'
      }}>
        <h3 style={{margin: 0}}>📅 Memory Timeline</h3>
        <select 
          value={viewMode} 
          onChange={(e) => setViewMode(e.target.value)}
          style={{
            padding: '8px 12px',
            borderRadius: '6px',
            border: '1px solid #cbd5e1'
          }}
        >
          <option value="day">Daily</option>
          <option value="week">Weekly</option>
          <option value="month">Monthly</option>
        </select>
      </div>
      
      <div style={{maxHeight: '400px', overflowY: 'auto'}}>
        {Object.entries(timelineData)
          .sort(([a], [b]) => new Date(b) - new Date(a))
          .map(([period, memories]) => (
            <div key={period} style={{
              display: 'flex',
              alignItems: 'center',
              padding: '12px 0',
              borderBottom: `1px solid ${darkMode ? '#334155' : '#e2e8f0'}`
            }}>
              <div style={{
                minWidth: '120px',
                padding: '6px 12px',
                backgroundColor: '#3b82f6',
                color: 'white',
                borderRadius: '20px',
                fontSize: '12px',
                fontWeight: 'bold',
                textAlign: 'center'
              }}>
                {new Date(period).toLocaleDateString()}
              </div>
              
              <div style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '6px',
                margin: '0 15px',
                flex: 1
              }}>
                {memories.map((memory, idx) => (
                  <div
                    key={idx}
                    style={{
                      width: '12px',
                      height: '12px',
                      borderRadius: '50%',
                      backgroundColor: getMoodColor(memory.mood),
                      cursor: 'pointer',
                      border: '2px solid white',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                    }}
                    onClick={() => onMemorySelect(memory)}
                    title={memory.text.substring(0, 100)}
                  />
                ))}
              </div>
              
              <div style={{
                fontSize: '12px',
                color: darkMode ? '#94a3b8' : '#64748b',
                minWidth: '80px',
                textAlign: 'right'
              }}>
                {memories.length} memories
              </div>
            </div>
          ))}
      </div>
    </div>
  );
};

export default MemoryTimeline;