import React from 'react';

function MemoryCard({ memory, date, tag, mood, image, aiReaction, onDelete }) {
  const memoryData = typeof memory === 'object' && memory !== null ? memory : null;
  const memoryText = memoryData ? memoryData.text : memory;
  const memoryDate = date || memoryData?.date;
  const memoryTag = tag || memoryData?.tag || memoryData?.mood;
  const memoryMood = mood || memoryData?.detected_mood || memoryData?.mood;
  const memoryImage = image || memoryData?.image || memoryData?.image_url;
  const memoryAiReaction = aiReaction || memoryData?.ai_response;

  // Optional: auto-emoji for mood
  const getMoodEmoji = (moodText) => {
    if (!moodText) return '';
    const mood = moodText.toLowerCase();
    if (mood.includes("happy") || mood.includes("joy")) return "😊";
    if (mood.includes("sad")) return "😢";
    if (mood.includes("angry")) return "😠";
    if (mood.includes("excited")) return "🤩";
    if (mood.includes("tired")) return "😴";
    if (mood.includes("love")) return "❤️";
    return "🧠";
  };

  const displayMood = memoryMood || memoryTag || 'Not detected';

  return (
    <div
      style={{
        fontSize: 18,
        marginBottom: 20,
        padding: 16,
        backgroundColor: '#f1f5f9',
        color: '#1e293b',
        borderRadius: 12,
        boxShadow: '0 2px 6px rgba(0,0,0,0.05)',
      }}
    >
      <p>{memoryText}</p>

      <p style={{ marginTop: 8 }}>
        <strong>Mood:</strong> {getMoodEmoji(displayMood)} {displayMood}
      </p>

      {memoryImage && (
        <img
          src={memoryImage}
          alt="memory"
          style={{
            width: '100%',
            marginTop: 10,
            maxHeight: 300,
            objectFit: 'cover',
            borderRadius: 8,
          }}
        />
      )}

      {memoryAiReaction && (
        <div style={{
          marginTop: 12,
          padding: 12,
          backgroundColor: '#e0f2fe',
          borderRadius: 8,
          borderLeft: '3px solid #3b82f6'
        }}>
          <strong style={{ color: '#3b82f6' }}>🤖 AI Response:</strong>
          <p style={{ marginTop: 4, marginBottom: 0 }}>{memoryAiReaction}</p>
        </div>
      )}

      <em style={{ color: '#888' }}>Date: {memoryDate}</em>

      {onDelete && (
        <div>
          <button
            onClick={() => onDelete(memoryData?.id)}
            style={{
              marginTop: 10,
              padding: '6px 12px',
              backgroundColor: '#ef4444',
              color: 'white',
              border: 'none',
              borderRadius: 6,
              cursor: 'pointer',
              fontWeight: 'bold',
            }}
          >
            ❌ Delete
          </button>
        </div>
      )}
    </div>
  );
}

export default MemoryCard;


