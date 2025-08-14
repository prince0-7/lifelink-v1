import React, { useState, useEffect } from 'react';

const AISettings = ({ aiManager, darkMode, onClose }) => {
  const [status, setStatus] = useState(null);
  const [preferences, setPreferences] = useState({});

  useEffect(() => {
    if (aiManager) {
      setStatus(aiManager.getAIStatus());
      setPreferences(aiManager.userPreferences);
    }
  }, [aiManager]);

  const handlePreferenceChange = (key, value) => {
    const newPrefs = { ...preferences, [key]: value };
    setPreferences(newPrefs);
    if (aiManager) {
      aiManager.updatePreferences(newPrefs);
    }
  };

  if (!status) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.5)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: darkMode ? '#1e293b' : 'white',
        padding: '30px',
        borderRadius: '16px',
        maxWidth: '500px',
        width: '90%',
        maxHeight: '80vh',
        overflowY: 'auto',
        boxShadow: '0 20px 40px rgba(0,0,0,0.3)'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px'
        }}>
          <h2 style={{margin: 0}}>🤖 AI Settings</h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '24px',
              cursor: 'pointer',
              color: darkMode ? '#e2e8f0' : '#1e293b'
            }}
          >
            ✕
          </button>
        </div>

        {/* AI Status */}
        <div style={{
          padding: '15px',
          backgroundColor: darkMode ? '#0f172a' : '#f8fafc',
          borderRadius: '8px',
          marginBottom: '20px'
        }}>
          <h3 style={{margin: '0 0 10px 0'}}>🚀 AI Status</h3>
          <div style={{display: 'flex', gap: '10px', flexWrap: 'wrap'}}>
            <span style={{
              padding: '4px 8px',
              borderRadius: '12px',
              fontSize: '12px',
              backgroundColor: status.localAvailable ? '#10b981' : '#ef4444',
              color: 'white'
            }}>
              🏠 Local AI: {status.localAvailable ? 'Available' : 'Offline'}
            </span>
            <span style={{
              padding: '4px 8px',
              borderRadius: '12px',
              fontSize: '12px',
              backgroundColor: status.cloudAvailable ? '#3b82f6' : '#ef4444',
              color: 'white'
            }}>
              ☁️ Cloud AI: {status.cloudAvailable ? 'Available' : 'Offline'}
            </span>
          </div>
          <p style={{
            margin: '10px 0 0 0',
            fontSize: '14px',
            color: darkMode ? '#94a3b8' : '#64748b'
          }}>
            Currently using: <strong>{status.currentProvider}</strong> AI
          </p>
        </div>

        {/* Preferences */}
        <div style={{marginBottom: '20px'}}>
          <h3>⚙️ Preferences</h3>
          
          <div style={{marginBottom: '15px'}}>
            <label style={{display: 'block', marginBottom: '5px'}}>AI Provider</label>
            <select
              value={preferences.aiProvider || 'auto'}
              onChange={(e) => handlePreferenceChange('aiProvider', e.target.value)}
              style={{
                width: '100%',
                padding: '8px',
                borderRadius: '6px',
                border: '1px solid #cbd5e1'
              }}
            >
              <option value="auto">🤖 Auto (Smart Routing)</option>
              <option value="local">🏠 Local Only (Private)</option>
              <option value="cloud">☁️ Cloud Only</option>
            </select>
          </div>

          <div style={{marginBottom: '15px'}}>
            <label style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer'
            }}>
              <input
                type="checkbox"
                checked={preferences.preferLocal || false}
                onChange={(e) => handlePreferenceChange('preferLocal', e.target.checked)}
              />
              🔒 Prefer Local AI (More Private)
            </label>
          </div>

          <div style={{marginBottom: '15px'}}>
            <label style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer'
            }}>
              <input
                type="checkbox"
                checked={preferences.useCloudFallback || false}
                onChange={(e) => handlePreferenceChange('useCloudFallback', e.target.checked)}
              />
              ☁️ Use Cloud Fallback
            </label>
          </div>
        </div>

        {/* Setup Instructions */}
        {!status.localAvailable && (
          <div style={{
            padding: '15px',
            backgroundColor: '#fef3c7',
            borderRadius: '8px',
            marginBottom: '20px',
            border: '1px solid #f59e0b'
          }}>
            <h4 style={{margin: '0 0 10px 0', color: '#92400e'}}>🚀 Setup Local AI (Free Forever)</h4>
            <p style={{margin: '0 0 10px 0', fontSize: '14px', color: '#92400e'}}>
              To enable free, private local AI:
            </p>
            <ol style={{margin: 0, paddingLeft: '20px', fontSize: '14px', color: '#92400e'}}>
              <li>Download Ollama from <strong>ollama.ai</strong></li>
              <li>Install and run: <code>ollama run llama3.1:8b</code></li>
              <li>Restart Lifelink - Local AI will be detected automatically!</li>
            </ol>
          </div>
        )}

        {/* Premium Features */}
        <div style={{
          padding: '15px',
          backgroundColor: darkMode ? '#0f172a' : '#f0f9ff',
          borderRadius: '8px',
          border: `1px solid ${darkMode ? '#1e293b' : '#bae6fd'}`
        }}>
          <h4 style={{margin: '0 0 10px 0'}}>✨ Premium Features (Optional)</h4>
          <input
            type="password"
            placeholder="Enter OpenAI API Key for premium features..."
            value={preferences.premiumAPIKey || ''}
            onChange={(e) => handlePreferenceChange('premiumAPIKey', e.target.value)}
            style={{
              width: '100%',
              padding: '8px',
              borderRadius: '6px',
              border: '1px solid #cbd5e1',
              marginBottom: '10px'
            }}
          />
          <p style={{
            margin: 0,
            fontSize: '12px',
            color: darkMode ? '#94a3b8' : '#64748b'
          }}>
            Optional: Add your API key for advanced AI features. Your key stays private and secure.
          </p>
        </div>

        <button
          onClick={onClose}
          style={{
            width: '100%',
            padding: '12px',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontWeight: 'bold',
            cursor: 'pointer',
            marginTop: '20px'
          }}
        >
          Save Settings
        </button>
      </div>
    </div>
  );
};

export default AISettings;