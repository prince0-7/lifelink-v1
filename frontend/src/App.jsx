import { useState, useEffect, useRef } from 'react';
import './App.css';
import MemoryCard from './components/MemoryCard';
import MoodChart from './components/MoodChart';
import MemoryTimeline from './components/MemoryTimeline';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import AdvancedSearch from './components/AdvancedSearch';
import AISettings from './components/AISettings';
import MemoryGraphView from './components/MemoryGraphView';
import AIManager from './ai/AIManager';
import { getMemories, createMemory, deleteMemory } from './services/api';

const speakText = (text) => {
  const utterance = new SpeechSynthesisUtterance(text);
  window.speechSynthesis.speak(utterance);
};

function App() {
  // Original state
  const [memory, setMemory] = useState('');
  const [tag, setTag] = useState('Happy');
  const [memories, setMemories] = useState([]);
  const [filterTag, setFilterTag] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterDate, setFilterDate] = useState('');
  const [darkMode, setDarkMode] = useState(false);
  const [aiReaction, setAIReaction] = useState('');
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);
  const [imageData, setImageData] = useState(null);
  
  // Enhanced state
  const [aiManager, setAIManager] = useState(null);
  const [showTimeline, setShowTimeline] = useState(false);
  const [showInsights, setShowInsights] = useState(false);
  const [showAdvancedSearch, setShowAdvancedSearch] = useState(false);
  const [showAISettings, setShowAISettings] = useState(false);
  const [showMemoryGraph, setShowMemoryGraph] = useState(false);
  const [aiGenerating, setAIGenerating] = useState(false);
  const [aiStatus, setAIStatus] = useState({ source: 'none', cost: 0 });

  // Initialize AI Manager
  useEffect(() => {
    const initAI = async () => {
      const manager = new AIManager();
      await manager.initializeAI();
      setAIManager(manager);
    };
    
    initAI();
  }, []);

  // Original useEffects

  useEffect(() => {
    const fetchMemories = async () => {
      try {
        const memories = await getMemories();
        setMemories(memories);
      } catch (error) {
        console.error('Error fetching memories:', error);
        // If backend is not available, show error
        console.log('Could not connect to backend. Make sure the backend server is running on http://localhost:8000');
      }
    };
    fetchMemories();
  }, []);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.log('Speech recognition not supported');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setMemory(prev => prev + ' ' + transcript);
      setIsListening(false);
    };

    recognition.onerror = () => {
      console.log('Speech recognition error');
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;
  }, []);

  useEffect(() => {
    if (aiReaction) {
      speakText(aiReaction);
    }
  }, [aiReaction]);

  // Original functions
  function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onloadend = () => {
      setImageData(reader.result);
    };
    reader.readAsDataURL(file);
  }

  function handleVoiceInput() {
    if (recognitionRef.current && !isListening) {
      setIsListening(true);
      recognitionRef.current.start();
    }
  }

  // ENHANCED SAVE FUNCTION WITH HYBRID AI
  const handleSave = async () => {
    if (memory.trim() === '') return;

    setAIGenerating(true);

    const today = new Date();
    const dateOnly = today.toISOString().split('T')[0];
    
    let detectedMood = 'Neutral';
    let enhancedReaction = 'Thank you for sharing this memory! ✨';

    // Use AI Manager for mood detection and response generation
    if (aiManager) {
      try {
        // Get sentiment analysis
        const sentiment = await aiManager.analyzeSentimentLocal(memory);
        detectedMood = sentiment.mood === 'positive' ? 'Happy' : 
                     sentiment.mood === 'negative' ? 'Sad' : 
                     sentiment.mood === 'calm' ? 'Calm' : 'Neutral';

        // Generate AI response
        const aiResponse = await aiManager.generateResponse(memory, {
          type: 'conversation',
          memories: memories,
          urgency: 'normal'
        });

        if (aiResponse) {
          enhancedReaction = aiResponse.response;
          setAIStatus({ source: aiResponse.source, cost: aiResponse.cost });
        }
      } catch (error) {
        console.error('AI processing error:', error);
        enhancedReaction = 'Thank you for sharing this memory with me! ✨';
      }
    }

    try {
      // Create memory through backend API
      const newMemory = {
        text: memory,
        mood: tag,
        tags: [tag]
      };

      const savedMemory = await createMemory(newMemory);
      
      // Add the returned memory to the local state
      setMemories([savedMemory, ...memories]);
      
      setAIReaction(savedMemory.ai_response || enhancedReaction);
      setMemory('');
      setImageData(null);
      setAIGenerating(false);
    } catch (error) {
      console.error('Error saving memory:', error);
      alert('Error saving memory. Please check if the backend is running.');
      setAIGenerating(false);
    }
  };

  // Original delete function

  const handleDelete = async (memoryId) => {
    try {
      await deleteMemory(memoryId);
      setMemories(memories.filter((memory) => memory.id !== memoryId));
    } catch (error) {
      console.error('Error deleting memory:', error);
      alert('Error deleting memory. Please check if the backend is running.');
    }
  };

  // Enhanced export function
  const handleExport = () => {
    const filteredMemories = memories.filter((item) => {
      const matchesTag = filterTag === 'All' || item.tag === filterTag;
      const matchesSearch = item.text.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesDate = !filterDate || item.date === filterDate;
      return matchesTag && matchesSearch && matchesDate;
    });

    const exportData = {
      exportDate: new Date().toISOString(),
      totalMemories: filteredMemories.length,
      aiProcessed: aiManager ? true : false,
      memories: filteredMemories
    };

    const content = JSON.stringify(exportData, null, 2);
    const blob = new Blob([content], { type: 'application/json' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `lifelink_memories_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
  };

  // Enhanced search function
  const handleAdvancedSearch = async (query) => {
    if (!aiManager || !query.trim()) return [];
    
    // Use AI-powered semantic search
    const results = [];
    
    for (let memory of memories) {
      const relevanceScore = await calculateRelevance(query, memory.text);
      if (relevanceScore > 0.3) {
        results.push({ ...memory, relevanceScore });
      }
    }
    
    return results
      .sort((a, b) => b.relevanceScore - a.relevanceScore)
      .slice(0, 20);
  };

  const calculateRelevance = async (query, text) => {
    // Simple relevance calculation - can be enhanced with AI
    const queryWords = query.toLowerCase().split(' ');
    const textWords = text.toLowerCase().split(' ');
    
    let matches = 0;
    queryWords.forEach(qWord => {
      if (textWords.some(tWord => tWord.includes(qWord))) {
        matches++;
      }
    });
    
    return matches / queryWords.length;
  };

  // AI Memory Analysis
  const handleAnalyzeMemories = async () => {
    if (!aiManager || memories.length === 0) return;
    
    try {
      const analysis = await aiManager.analyzeMemoryCollection(memories);
      console.log('Memory Analysis:', analysis);
      
      // Show analysis in a modal or component
      setAIReaction(`📊 AI Analysis Complete! Found ${analysis.keyThemes.length} key themes in your ${analysis.totalMemories} memories. ${analysis.growthInsights[0] || 'Your memory journey shows interesting patterns!'}`);
    } catch (error) {
      console.error('Memory analysis error:', error);
    }
  };

  return (
    <div style={styles.container(darkMode)}>
      <div style={styles.header}>
        <h1 style={styles.heading}>Lifelink 🧠</h1>
        <p style={styles.subtitle}>
          Your Personal Memory Preservation System
          {aiManager && (
            <span style={styles.aiIndicator}>
              {' '} • AI-Powered {aiStatus.source && `(${aiStatus.source})`}
            </span>
          )}
        </p>
      </div>

      {/* Enhanced Control Panel */}
      <div style={styles.controlPanel}>
        <button
          onClick={() => setDarkMode(!darkMode)}
          style={controlButtonStyle(darkMode, false)}
        >
          {darkMode ? '☀️ Light' : '🌙 Dark'}
        </button>
        
        <button
          onClick={() => setShowTimeline(!showTimeline)}
          style={controlButtonStyle(darkMode, showTimeline)}
        >
          📅 Timeline
        </button>
        
        <button
          onClick={() => setShowInsights(!showInsights)}
          style={controlButtonStyle(darkMode, showInsights)}
        >
          📊 Insights
        </button>
        
        <button
          onClick={() => setShowAdvancedSearch(!showAdvancedSearch)}
          style={controlButtonStyle(darkMode, showAdvancedSearch)}
        >
          🔍 Search
        </button>

        <button
          onClick={() => setShowAISettings(!showAISettings)}
          style={controlButtonStyle(darkMode, showAISettings)}
        >
          🤖 AI Settings
        </button>

        <button
          onClick={() => setShowMemoryGraph(!showMemoryGraph)}
          style={controlButtonStyle(darkMode, showMemoryGraph)}
        >
          🕸️ Graph
        </button>

        {memories.length > 5 && (
          <button
            onClick={handleAnalyzeMemories}
            style={{
              ...controlButtonStyle(darkMode, false),
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
            }}
          >
            ✨ Analyze All
          </button>
        )}
      </div>

      {/* Memory Input Section */}
      <div style={styles.inputSection}>
        <textarea
          value={memory}
          onChange={(e) => setMemory(e.target.value)}
          placeholder="Write your memory... (AI will provide intelligent insights!)"
          rows={4}
          style={{
            ...styles.textarea,
            backgroundColor: darkMode ? '#1e293b' : '#ffffff',
            color: darkMode ? '#e2e8f0' : '#1e293b',
            border: `2px solid ${darkMode ? '#334155' : '#e2e8f0'}`
          }}
        />

        <input
          type="file"
          accept="image/*"
          onChange={handleImageUpload}
          style={styles.fileInput}
        />

        {imageData && (
          <div style={styles.imagePreview}>
            <strong>🖼️ Image Preview:</strong>
            <img
              src={imageData}
              alt="Preview"
              style={styles.previewImage}
            />
          </div>
        )}

        <div style={styles.inputControls}>
          <button 
            onClick={handleVoiceInput} 
            style={{
              ...styles.voiceButton,
              opacity: isListening ? 0.7 : 1
            }}
          >
            🎤 {isListening ? "Listening..." : "Voice Input"}
          </button>

          <div style={styles.moodSelector}>
            <label>Mood: </label>
            <select 
              value={tag} 
              onChange={(e) => setTag(e.target.value)} 
              style={styles.select}
            >
              <option value="Happy">😊 Happy</option>
              <option value="Sad">😢 Sad</option>
              <option value="Angry">😠 Angry</option>
              <option value="Calm">🧘 Calm</option>
            </select>
          </div>
        </div>
      </div>

      {/* Enhanced AI Reaction Display */}
      {aiReaction && (
        <div style={{
          ...styles.aiReaction,
          backgroundColor: darkMode ? '#1f2937' : '#e0f2fe',
          borderColor: getAISourceColor(aiStatus.source)
        }}>
          <div style={styles.aiHeader}>
            <span style={styles.aiLabel}>
              🤖 {getAISourceLabel(aiStatus.source)} AI:
            </span>
            {aiStatus.cost === 0 && (
              <span style={styles.freeLabel}>FREE</span>
            )}
          </div>
          <div style={styles.aiMessage}>
            {aiGenerating ? (
              <div style={styles.loadingDots}>
                <span>Thinking</span>
                <span className="dot">.</span>
                <span className="dot">.</span>
                <span className="dot">.</span>
              </div>
            ) : (
              aiReaction
            )}
          </div>
        </div>
      )}

      <button 
        onClick={handleSave} 
        disabled={!memory.trim() || aiGenerating}
        style={{
          ...styles.saveButton,
          opacity: (!memory.trim() || aiGenerating) ? 0.6 : 1,
          cursor: (!memory.trim() || aiGenerating) ? 'not-allowed' : 'pointer'
        }}
      >
        {aiGenerating ? '🤖 AI Processing...' : '💾 Save Memory'}
      </button>

      {/* Enhanced Features */}
      {showAdvancedSearch && (
        <AdvancedSearch 
          onSearch={handleAdvancedSearch}
          darkMode={darkMode}
        />
      )}

      {showTimeline && (
        <MemoryTimeline 
          memories={memories} 
          darkMode={darkMode}
          onMemorySelect={(memory) => {
            console.log('Selected memory:', memory);
          }}
        />
      )}

      {showMemoryGraph && (
        <MemoryGraphView />
      )}

      {showInsights && (
        <AnalyticsDashboard 
          darkMode={darkMode}
        />
      )}

      {showAISettings && (
        <AISettings
          aiManager={aiManager}
          darkMode={darkMode}
          onClose={() => setShowAISettings(false)}
        />
      )}

      {/* Filtering and Search */}
      <div style={styles.filterSection}>
        <div style={styles.filterRow}>
          <select 
            value={filterTag} 
            onChange={(e) => setFilterTag(e.target.value)} 
            style={styles.select}
          >
            <option value="All">🗂️ All Moods</option>
            <option value="Happy">😊 Happy</option>
            <option value="Sad">😢 Sad</option>
            <option value="Angry">😠 Angry</option>
            <option value="Calm">🧘 Calm</option>
          </select>

          <input
            type="date"
            value={filterDate}
            onChange={(e) => setFilterDate(e.target.value)}
            style={styles.select}
          />
        </div>

        <input
          type="text"
          placeholder="🔍 Search memories..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={styles.searchInput}
        />

        <button onClick={handleExport} style={styles.exportButton}>
          📤 Export Enhanced
        </button>
      </div>

      {/* Memory List */}
      <div style={styles.memoryList}>
        <h2>📜 Your AI-Enhanced Memories:</h2>
        {memories
          .filter((item) => {
            const matchesTag = filterTag === 'All' || item.tag === filterTag;
            const matchesSearch = item.text.toLowerCase().includes(searchQuery.toLowerCase());
            const matchesDate = !filterDate || item.date === filterDate;
            return matchesTag && matchesSearch && matchesDate;
          })
          .map((item, index) => (
            <MemoryCard
              key={item.id || index}
              memory={item.text}
              date={item.date}
              tag={item.mood || item.tag}
              mood={item.detected_mood || item.mood}
              image={item.image}
              aiReaction={item.ai_response}
              onDelete={() => handleDelete(item.id)}
            />
          ))}
      </div>

      {/* Original MoodChart */}
      <MoodChart memories={memories} />
    </div>
  );
}

// Enhanced Styles
const styles = {
  container: (darkMode) => ({
    padding: '40px 20px',
    fontFamily: 'Segoe UI, sans-serif',
    backgroundColor: darkMode ? '#0f172a' : '#f9fafb',
    color: darkMode ? '#e2e8f0' : '#1e293b',
    minHeight: '100vh',
    maxWidth: 900,
    margin: '0 auto',
  }),
  header: {
    textAlign: 'center',
    marginBottom: 30
  },
  heading: {
    fontSize: 42,
    marginBottom: 10,
    fontWeight: '800',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    textAlign: 'center'
  },
  subtitle: {
    color: '#64748b',
    fontSize: 16,
    margin: 0
  },
  aiIndicator: {
    color: '#3b82f6',
    fontWeight: 'bold',
    fontSize: 14
  },
  controlPanel: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '12px',
    marginBottom: 30,
    justifyContent: 'center'
  },
  inputSection: {
    marginBottom: 20
  },
  textarea: {
    width: '100%',
    padding: 16,
    borderRadius: 12,
    fontSize: 16,
    outline: 'none',
    resize: 'vertical',
    fontFamily: 'inherit',
    transition: 'border-color 0.2s ease'
  },
  fileInput: {
    marginTop: 12,
    marginBottom: 12,
    padding: '8px',
    border: '1px solid #ccc',
    borderRadius: '8px',
    width: '100%'
  },
  imagePreview: {
    marginTop: 12
  },
  previewImage: {
    width: '100%',
    maxHeight: 300,
    objectFit: 'cover',
    borderRadius: 12,
    marginTop: 8,
  },
  inputControls: {
    display: 'flex',
    gap: '15px',
    alignItems: 'center',
    marginTop: 15,
    flexWrap: 'wrap'
  },
  voiceButton: {
    padding: '10px 16px',
    backgroundColor: '#d8b4fe',
    color: '#1e1b4b',
    border: 'none',
    borderRadius: 8,
    cursor: 'pointer',
    fontWeight: 'bold',
    fontSize: 14
  },
  moodSelector: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  },
  select: {
    padding: '8px 12px',
    fontSize: 14,
    borderRadius: 6,
    border: '1px solid #cbd5e1',
    outline: 'none',
  },
  aiReaction: {
    margin: '20px 0',
    padding: '20px',
    borderRadius: 16,
    borderLeft: '4px solid',
    boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
  },
  aiHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8
  },
  aiLabel: {
    fontWeight: 'bold',
    fontSize: 16
  },
  freeLabel: {
    padding: '2px 8px',
    backgroundColor: '#10b981',
    color: 'white',
    borderRadius: 12,
    fontSize: 10,
    fontWeight: 'bold'
  },
  aiMessage: {
    fontSize: 15,
    lineHeight: 1.5
  },
  loadingDots: {
    display: 'flex',
    alignItems: 'center',
    gap: '2px'
  },
  saveButton: {
    width: '100%',
    padding: '16px 24px',
    fontSize: 18,
    cursor: 'pointer',
    backgroundColor: '#3b82f6',
    color: 'white',
    border: 'none',
    borderRadius: 12,
    fontWeight: 'bold',
    boxShadow: '0 4px 12px rgba(59,130,246,0.3)',
    transition: 'all 0.2s ease',
    marginBottom: 20
  },
  filterSection: {
    margin: '20px 0'
  },
  filterRow: {
    display: 'flex',
    gap: '10px',
    marginBottom: 15,
    flexWrap: 'wrap'
  },
  searchInput: {
    width: '100%',
    padding: 12,
    fontSize: 16,
    borderRadius: 8,
    border: '1px solid #cbd5e1',
    marginBottom: 10
  },
  exportButton: {
    padding: '10px 20px',
    fontSize: 16,
    cursor: 'pointer',
    backgroundColor: '#10b981',
    color: 'white',
    border: 'none',
    borderRadius: 8,
    fontWeight: 'bold',
  },
  memoryList: {
    marginTop: 40
  }
};

const controlButtonStyle = (darkMode, isActive) => ({
  padding: '10px 16px',
  cursor: 'pointer',
  backgroundColor: isActive 
    ? '#3b82f6' 
    : darkMode ? '#374151' : '#e5e7eb',
  color: isActive 
    ? '#fff' 
    : darkMode ? '#e5e7eb' : '#374151',
  border: 'none',
  borderRadius: 8,
  fontWeight: 'bold',
  fontSize: 14,
  transition: 'all 0.2s ease',
  boxShadow: isActive ? '0 2px 8px rgba(59,130,246,0.3)' : 'none'
});

const getAISourceColor = (source) => {
  const colors = {
    'local': '#10b981',
    'cloud': '#3b82f6',
    'enhanced-local': '#8b5cf6',
    'fallback': '#6b7280'
  };
  return colors[source] || '#6b7280';
};

const getAISourceLabel = (source) => {
  const labels = {
    'local': 'Local',
    'cloud': 'Cloud',
    'enhanced-local': 'Enhanced',
    'fallback': 'Basic'
  };
  return labels[source] || 'AI';
};

export default App;


