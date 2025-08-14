// ===== COMPONENTS/ADVANCEDSEARCH.JSX - FIXED VERSION =====
import React, { useState } from 'react';

const AdvancedSearch = ({ onSearch, darkMode }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setIsSearching(true);
    
    // Simulate search delay for better UX
    setTimeout(() => {
      const results = onSearch(searchQuery);
      setSearchResults(results);
      setIsSearching(false);
    }, 300);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults([]);
  };

  const getMoodColor = (mood) => {
    const colors = {
      'Happy': '#10b981',
      'Sad': '#3b82f6',
      'Angry': '#ef4444', 
      'Calm': '#8b5cf6',
      'Neutral': '#6b7280'
    };
    return colors[mood] || colors['Neutral'];
  };

  return (
    <div style={{
      margin: '20px 0',
      padding: '20px',
      backgroundColor: darkMode ? '#1e293b' : '#f8fafc',
      borderRadius: '12px',
      border: `1px solid ${darkMode ? '#334155' : '#e2e8f0'}`
    }}>
      <h3 style={{margin: '0 0 15px 0'}}>🔍 Advanced Memory Search</h3>
      
      <div style={{
        display: 'flex',
        gap: '10px',
        marginBottom: '15px'
      }}>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Search your memories with keywords..."
          style={{
            flex: 1,
            padding: '12px',
            borderRadius: '8px',
            border: `1px solid ${darkMode ? '#475569' : '#cbd5e1'}`,
            backgroundColor: darkMode ? '#0f172a' : '#ffffff',
            color: darkMode ? '#e2e8f0' : '#1e293b',
            fontSize: '16px'
          }}
        />
        
        <button
          onClick={handleSearch}
          disabled={isSearching || !searchQuery.trim()}
          style={{
            padding: '12px 20px',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: isSearching ? 'not-allowed' : 'pointer',
            fontWeight: 'bold',
            opacity: isSearching ? 0.6 : 1
          }}
        >
          {isSearching ? '🔄' : '🔍'} Search
        </button>
        
        {searchResults.length > 0 && (
          <button
            onClick={clearSearch}
            style={{
              padding: '12px 16px',
              backgroundColor: '#6b7280',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer'
            }}
          >
            ✕ Clear
          </button>
        )}
      </div>

      {searchResults.length > 0 && (
        <div>
          <h4 style={{
            margin: '0 0 10px 0',
            color: darkMode ? '#60a5fa' : '#1d4ed8'
          }}>
            Found {searchResults.length} matching memories:
          </h4>
          
          <div style={{
            maxHeight: '300px',
            overflowY: 'auto'
          }}>
            {searchResults.map((memory, index) => (
              <div key={index} style={{
                padding: '12px',
                marginBottom: '8px',
                backgroundColor: darkMode ? '#0f172a' : '#ffffff',
                borderRadius: '8px',
                border: `1px solid ${darkMode ? '#1e293b' : '#e2e8f0'}`,
                cursor: 'pointer',
                transition: 'background-color 0.2s ease'
              }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  marginBottom: '8px'
                }}>
                  <span style={{
                    fontSize: '12px',
                    backgroundColor: getMoodColor(memory.mood || memory.tag),
                    padding: '2px 8px',
                    borderRadius: '12px',
                    color: 'white'
                  }}>
                    {memory.mood || memory.tag}
                  </span>
                  <span style={{
                    fontSize: '12px',
                    color: darkMode ? '#94a3b8' : '#64748b'
                  }}>
                    {new Date(memory.date).toLocaleDateString()}
                  </span>
                </div>
                
                <p style={{
                  margin: 0,
                  fontSize: '14px',
                  lineHeight: '1.4'
                }}>
                  {memory.text.length > 150 
                    ? memory.text.substring(0, 150) + '...'
                    : memory.text
                  }
                </p>
                
                {memory.aiReaction && (
                  <div style={{
                    marginTop: '8px',
                    fontSize: '12px',
                    fontStyle: 'italic',
                    color: darkMode ? '#60a5fa' : '#3b82f6'
                  }}>
                    🤖 {memory.aiReaction}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {searchQuery && searchResults.length === 0 && !isSearching && (
        <div style={{
          padding: '20px',
          textAlign: 'center',
          color: darkMode ? '#94a3b8' : '#64748b',
          fontStyle: 'italic'
        }}>
          No memories found matching "{searchQuery}". Try different keywords!
        </div>
      )}
    </div>
  );
};

export default AdvancedSearch;