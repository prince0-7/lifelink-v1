import React from 'react';

const MemoryInsights = ({ memories, darkMode }) => {
  const calculateInsights = () => {
    if (memories.length === 0) return {
      totalMemories: 0,
      averagePerDay: 0,
      moodDistribution: {},
      longestStreak: 0,
      mostActiveDay: 'N/A',
      topWords: []
    };

    // Calculate mood distribution
    const moodDistribution = {};
    memories.forEach(memory => {
      const mood = memory.mood || memory.tag || 'Unknown';
      moodDistribution[mood] = (moodDistribution[mood] || 0) + 1;
    });

    // Calculate average memories per day
    const uniqueDates = [...new Set(memories.map(m => m.date))];
    const averagePerDay = memories.length / uniqueDates.length;

    // Calculate longest streak
    const sortedDates = uniqueDates.sort();
    let longestStreak = 1;
    let currentStreak = 1;
    
    for (let i = 1; i < sortedDates.length; i++) {
      const prevDate = new Date(sortedDates[i - 1]);
      const currentDate = new Date(sortedDates[i]);
      const diffTime = Math.abs(currentDate - prevDate);
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      
      if (diffDays === 1) {
        currentStreak++;
        longestStreak = Math.max(longestStreak, currentStreak);
      } else {
        currentStreak = 1;
      }
    }

    // Find most active day of week
    const dayCount = {};
    memories.forEach(memory => {
      const day = new Date(memory.date).toLocaleDateString('en-US', { weekday: 'long' });
      dayCount[day] = (dayCount[day] || 0) + 1;
    });
    const mostActiveDay = Object.entries(dayCount)
      .sort(([,a], [,b]) => b - a)[0]?.[0] || 'N/A';

    // Extract top words
    const wordCount = {};
    const stopWords = ['the', 'and', 'but', 'for', 'are', 'was', 'were', 'been', 'have', 'has', 'had', 'will', 'would', 'could', 'should', 'this', 'that', 'with', 'from'];
    
    memories.forEach(memory => {
      const words = memory.text.toLowerCase()
        .replace(/[^\w\s]/g, ' ')
        .split(/\s+/)
        .filter(word => word.length > 3 && !stopWords.includes(word));
      
      words.forEach(word => {
        wordCount[word] = (wordCount[word] || 0) + 1;
      });
    });
    
    const topWords = Object.entries(wordCount)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 8)
      .map(([word, count]) => ({ word, count }));

    return {
      totalMemories: memories.length,
      averagePerDay: averagePerDay,
      moodDistribution,
      longestStreak: longestStreak === 1 && sortedDates.length === 1 ? 1 : longestStreak,
      mostActiveDay,
      topWords
    };
  };

  const insights = calculateInsights();
  const dominantMood = Object.entries(insights.moodDistribution)
    .sort(([,a], [,b]) => b - a)[0]?.[0] || 'Unknown';

  return (
    <div style={{
      margin: '20px 0',
      padding: '20px',
      backgroundColor: darkMode ? '#1e293b' : '#ffffff',
      borderRadius: '12px',
      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)',
      border: `1px solid ${darkMode ? '#334155' : '#e2e8f0'}`
    }}>
      <h2 style={{margin: '0 0 20px 0'}}>📊 Memory Insights</h2>
      
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
        gap: '15px',
        marginBottom: '20px'
      }}>
        <div style={{
          padding: '15px',
          backgroundColor: darkMode ? '#0f172a' : '#f8fafc',
          borderRadius: '8px',
          textAlign: 'center',
          border: `1px solid ${darkMode ? '#1e293b' : '#e2e8f0'}`
        }}>
          <div style={{
            fontSize: '24px',
            fontWeight: 'bold',
            color: '#3b82f6',
            marginBottom: '5px'
          }}>
            {insights.totalMemories}
          </div>
          <div style={{
            fontSize: '12px',
            color: darkMode ? '#94a3b8' : '#64748b',
            textTransform: 'uppercase'
          }}>
            Total Memories
          </div>
        </div>

        <div style={{
          padding: '15px',
          backgroundColor: darkMode ? '#0f172a' : '#f8fafc',
          borderRadius: '8px',
          textAlign: 'center',
          border: `1px solid ${darkMode ? '#1e293b' : '#e2e8f0'}`
        }}>
          <div style={{
            fontSize: '24px',
            fontWeight: 'bold',
            color: '#10b981',
            marginBottom: '5px'
          }}>
            {insights.averagePerDay.toFixed(1)}
          </div>
          <div style={{
            fontSize: '12px',
            color: darkMode ? '#94a3b8' : '#64748b',
            textTransform: 'uppercase'
          }}>
            Avg per Day
          </div>
        </div>

        <div style={{
          padding: '15px',
          backgroundColor: darkMode ? '#0f172a' : '#f8fafc',
          borderRadius: '8px',
          textAlign: 'center',
          border: `1px solid ${darkMode ? '#1e293b' : '#e2e8f0'}`
        }}>
          <div style={{
            fontSize: '24px',
            fontWeight: 'bold',
            color: '#f59e0b',
            marginBottom: '5px'
          }}>
            {insights.longestStreak}
          </div>
          <div style={{
            fontSize: '12px',
            color: darkMode ? '#94a3b8' : '#64748b',
            textTransform: 'uppercase'
          }}>
            Longest Streak
          </div>
        </div>

        <div style={{
          padding: '15px',
          backgroundColor: darkMode ? '#0f172a' : '#f8fafc',
          borderRadius: '8px',
          textAlign: 'center',
          border: `1px solid ${darkMode ? '#1e293b' : '#e2e8f0'}`
        }}>
          <div style={{
            fontSize: '18px',
            fontWeight: 'bold',
            color: '#8b5cf6',
            marginBottom: '5px'
          }}>
            {insights.mostActiveDay}
          </div>
          <div style={{
            fontSize: '12px',
            color: darkMode ? '#94a3b8' : '#64748b',
            textTransform: 'uppercase'
          }}>
            Most Active Day
          </div>
        </div>
      </div>

      {/* Mood Summary */}
      <div style={{marginBottom: '20px'}}>
        <h3 style={{marginBottom: '10px'}}>🎭 Mood Breakdown</h3>
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '8px'
        }}>
          {Object.entries(insights.moodDistribution).map(([mood, count]) => (
            <span key={mood} style={{
              padding: '6px 12px',
              backgroundColor: getMoodColor(mood),
              color: 'white',
              borderRadius: '20px',
              fontSize: '14px',
              fontWeight: '500'
            }}>
              {getMoodEmoji(mood)} {mood}: {count}
            </span>
          ))}
        </div>
        <p style={{
          marginTop: '10px',
          fontSize: '14px',
          color: darkMode ? '#94a3b8' : '#64748b'
        }}>
          Your dominant mood: <strong>{getMoodEmoji(dominantMood)} {dominantMood}</strong>
        </p>
      </div>

      {/* Top Words */}
      {insights.topWords.length > 0 && (
        <div>
          <h3 style={{marginBottom: '10px'}}>🔤 Most Used Words</h3>
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '8px'
          }}>
            {insights.topWords.map((item, index) => (
              <span key={index} style={{
                padding: '4px 8px',
                backgroundColor: darkMode ? '#0f172a' : '#e0f2fe',
                color: darkMode ? '#60a5fa' : '#0c4a6e',
                borderRadius: '12px',
                fontSize: `${Math.max(12, 16 - index)}px`,
                fontWeight: '500',
                opacity: Math.max(0.6, 1 - (index * 0.1))
              }}>
                {item.word} ({item.count})
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
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

const getMoodEmoji = (mood) => {
  const emojis = {
    'Happy': '😊',
    'Sad': '😢',
    'Angry': '😠',
    'Calm': '🧘',
    'Neutral': '😐'
  };
  return emojis[mood] || '😐';
};

export default MemoryInsights;