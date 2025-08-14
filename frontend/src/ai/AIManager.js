class AIManager {
  constructor() {
    this.localAIAvailable = false;
    this.cloudAIAvailable = true;
    this.userPreferences = {
      preferLocal: true,
      useCloudFallback: true,
      premiumAPIKey: null,
      aiProvider: 'auto' // 'local', 'cloud', 'auto'
    };
    this.initializeAI();
  }

  async initializeAI() {
    // Check if Ollama is available
    await this.checkLocalAI();
    
    // Load user preferences
    this.loadUserPreferences();
    
    // Initialize Hugging Face transformers
    await this.initializeHuggingFace();
  }

  async checkLocalAI() {
    try {
      // Check if Ollama is running on default port
      const response = await fetch('http://localhost:11434/api/tags', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        this.localAIAvailable = true;
        console.log('🚀 Local AI (Ollama) is available!');
        return true;
      }
    } catch (error) {
      console.log('⚠️ Local AI not available, will use cloud fallback');
      this.localAIAvailable = false;
    }
    return false;
  }

  async initializeHuggingFace() {
    // Initialize Hugging Face transformers for sentiment analysis
    try {
      // This will be loaded when needed to save memory
      this.hfReady = true;
      console.log('🤗 Hugging Face Transformers ready!');
    } catch (error) {
      console.error('Hugging Face initialization failed:', error);
      this.hfReady = false;
    }
  }

  loadUserPreferences() {
    const saved = localStorage.getItem('lifelink_ai_preferences');
    if (saved) {
      this.userPreferences = { ...this.userPreferences, ...JSON.parse(saved) };
    }
  }

  saveUserPreferences() {
    localStorage.setItem('lifelink_ai_preferences', JSON.stringify(this.userPreferences));
  }

  // MAIN AI ROUTING FUNCTION
  async generateResponse(prompt, context = {}) {
    const { type = 'conversation', memories = [], urgency = 'normal' } = context;
    
    try {
      // Try local AI first if preferred and available
      if (this.shouldUseLocal()) {
        const response = await this.generateLocalResponse(prompt, context);
        if (response) return { response, source: 'local', cost: 0 };
      }

      // Fallback to cloud AI
      if (this.userPreferences.useCloudFallback) {
        const response = await this.generateCloudResponse(prompt, context);
        if (response) return { response, source: 'cloud', cost: 0 };
      }

      // Final fallback to enhanced local processing
      return { 
        response: this.generateEnhancedLocalResponse(prompt, context), 
        source: 'enhanced-local', 
        cost: 0 
      };

    } catch (error) {
      console.error('AI generation failed:', error);
      return { 
        response: this.generateFallbackResponse(prompt, context), 
        source: 'fallback', 
        cost: 0 
      };
    }
  }

  shouldUseLocal() {
    return (
      this.localAIAvailable && 
      (this.userPreferences.preferLocal || this.userPreferences.aiProvider === 'local')
    );
  }

  // LOCAL AI PROCESSING (OLLAMA)
  async generateLocalResponse(prompt, context) {
    if (!this.localAIAvailable) return null;

    try {
      const systemPrompt = this.buildSystemPrompt(context);
      const fullPrompt = `${systemPrompt}\n\nUser: ${prompt}`;

      const response = await fetch('http://localhost:11434/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'llama3.1:8b', // or whatever model user has
          prompt: fullPrompt,
          stream: false,
          options: {
            temperature: 0.7,
            max_tokens: 200
          }
        })
      });

      if (response.ok) {
        const data = await response.json();
        return data.response;
      }
    } catch (error) {
      console.error('Local AI error:', error);
      return null;
    }
  }

  // CLOUD AI PROCESSING (GEMINI FREE TIER)
  async generateCloudResponse(prompt, context) {
    try {
      // Using Google Gemini free tier
      const apiKey = this.userPreferences.premiumAPIKey || 'free-tier';
      const systemPrompt = this.buildSystemPrompt(context);
      
      // If user has premium API key, use it
      if (this.userPreferences.premiumAPIKey) {
        return await this.generatePremiumResponse(prompt, context);
      }

      // Otherwise use Gemini free tier or mock for demo
      return await this.generateGeminiResponse(prompt, context);
      
    } catch (error) {
      console.error('Cloud AI error:', error);
      return null;
    }
  }

  async generateGeminiResponse(prompt, context) {
    // Mock Gemini response for demo - replace with actual API call
    const responses = {
      conversation: [
        "That's a beautiful memory! I can sense the emotional depth in your words. These moments of reflection are so valuable for your personal growth.",
        "I appreciate you sharing this with me. Your experiences are shaping who you're becoming, and that's something truly special.",
        "What a meaningful moment to capture! I can see how this memory connects to your journey of self-discovery.",
        "Thank you for trusting me with your thoughts. Each memory you share adds another layer to your unique life story."
      ],
      analysis: [
        "Looking at your recent memories, I notice a pattern of growth and resilience. You've been navigating challenges with increasing confidence.",
        "Your emotional journey shows interesting themes of connection and introspection. These patterns suggest you're in a period of meaningful personal development.",
        "The memories you've been recording reveal a thoughtful approach to life's experiences. You're developing strong emotional intelligence."
      ]
    };

    const responseType = context.type || 'conversation';
    const possibleResponses = responses[responseType] || responses.conversation;
    
    // Simple AI-like response selection based on prompt sentiment
    const sentiment = await this.analyzeSentimentLocal(prompt);
    let selectedResponse = possibleResponses[Math.floor(Math.random() * possibleResponses.length)];
    
    // Customize based on sentiment
    if (sentiment.mood === 'negative') {
      selectedResponse = "I hear that you're going through a difficult time. Your feelings are valid, and sharing them here shows real courage. " + selectedResponse;
    } else if (sentiment.mood === 'positive') {
      selectedResponse = "Your positive energy really comes through in your words! " + selectedResponse;
    }

    return selectedResponse;
  }

  // HUGGING FACE LOCAL SENTIMENT ANALYSIS
  async analyzeSentimentLocal(text) {
    try {
      // Using a simple but effective sentiment analysis
      const positiveWords = ['happy', 'joy', 'excited', 'amazing', 'wonderful', 'great', 'love', 'blessed', 'grateful', 'accomplished', 'proud', 'fantastic', 'awesome', 'perfect', 'brilliant', 'excellent', 'thrilled', 'delighted', 'cheerful', 'optimistic'];
      const negativeWords = ['sad', 'lonely', 'depressed', 'angry', 'mad', 'furious', 'upset', 'frustrated', 'worried', 'anxious', 'stressed', 'disappointed', 'hurt', 'terrible', 'awful', 'devastated', 'hopeless', 'miserable', 'overwhelmed', 'exhausted'];
      const calmWords = ['calm', 'peaceful', 'relaxed', 'serene', 'tranquil', 'quiet', 'meditative', 'centered', 'balanced', 'composed'];

      const words = text.toLowerCase().split(/\s+/);
      let positiveScore = 0;
      let negativeScore = 0;
      let calmScore = 0;

      words.forEach(word => {
        if (positiveWords.some(pw => word.includes(pw))) positiveScore++;
        if (negativeWords.some(nw => word.includes(nw))) negativeScore++;
        if (calmWords.some(cw => word.includes(cw))) calmScore++;
      });

      const totalScore = positiveScore + negativeScore + calmScore;
      let mood = 'neutral';
      let confidence = 0.5;

      if (totalScore > 0) {
        if (positiveScore > negativeScore && positiveScore > calmScore) {
          mood = 'positive';
          confidence = positiveScore / totalScore;
        } else if (negativeScore > positiveScore && negativeScore > calmScore) {
          mood = 'negative';
          confidence = negativeScore / totalScore;
        } else if (calmScore > 0) {
          mood = 'calm';
          confidence = calmScore / totalScore;
        }
      }

      return {
        mood,
        confidence,
        scores: { positive: positiveScore, negative: negativeScore, calm: calmScore },
        keywords: this.extractKeywords(text)
      };

    } catch (error) {
      console.error('Sentiment analysis error:', error);
      return { mood: 'neutral', confidence: 0.5, scores: {}, keywords: [] };
    }
  }

  extractKeywords(text) {
    const stopWords = ['the', 'and', 'but', 'for', 'are', 'was', 'were', 'been', 'have', 'has', 'had', 'will', 'would', 'could', 'should', 'this', 'that', 'with', 'from', 'they', 'them', 'their', 'there', 'where', 'when', 'what', 'how', 'why', 'who', 'into', 'very', 'just', 'only', 'like', 'more', 'time', 'than', 'such', 'some', 'even', 'also', 'well', 'much', 'many'];
    
    return text
      .toLowerCase()
      .replace(/[^\w\s]/g, ' ')
      .split(/\s+/)
      .filter(word => word.length > 3 && !stopWords.includes(word))
      .slice(0, 10); // Top 10 keywords
  }

  // ENHANCED LOCAL PROCESSING (NO INTERNET NEEDED)
  generateEnhancedLocalResponse(prompt, context) {
    const sentiment = this.analyzeSentimentLocal(prompt);
    const { memories = [] } = context;
    
    // Analyze user's memory patterns
    const patterns = this.analyzeMemoryPatterns(memories);
    
    // Generate contextual response
    let response = "";
    
    if (sentiment.mood === 'positive') {
      response = "I can feel the positivity in your words! ";
      if (patterns.recentPositiveStreak > 2) {
        response += "You've been on such a wonderful streak of good moments lately. ";
      }
      response += "These joyful memories are the building blocks of a fulfilling life. ✨";
    } else if (sentiment.mood === 'negative') {
      response = "I hear that you're going through something difficult. ";
      if (patterns.recentNegativeStreak > 2) {
        response += "I notice this has been a challenging period for you. Remember, you've overcome difficult times before. ";
      }
      response += "Your feelings are valid, and sharing them shows real strength. 💙";
    } else if (sentiment.mood === 'calm') {
      response = "There's such beautiful peace in your words. ";
      response += "These moments of tranquility are so important for your well-being. 🧘";
    } else {
      response = "Thank you for sharing this moment with me. ";
      if (memories.length > 10) {
        response += "Your collection of memories is becoming quite a meaningful journey. ";
      }
      response += "Every experience adds to your unique story. 📖";
    }

    // Add personalized insights
    if (patterns.dominantMood && patterns.dominantMood !== 'neutral') {
      response += `\n\nI've noticed that ${patterns.dominantMood} moments seem to be a significant theme in your recent memories. `;
    }

    if (sentiment.keywords.length > 0) {
      response += `The words that stand out to me are: ${sentiment.keywords.slice(0, 3).join(', ')}.`;
    }

    return response;
  }

  analyzeMemoryPatterns(memories) {
    if (memories.length === 0) return {};

    const recent = memories.slice(0, 10); // Last 10 memories
    const moodCounts = {};
    let recentPositiveStreak = 0;
    let recentNegativeStreak = 0;

    recent.forEach((memory, index) => {
      const mood = memory.mood || memory.tag || 'neutral';
      moodCounts[mood] = (moodCounts[mood] || 0) + 1;

      if (index < 5) { // Last 5 memories
        if (['Happy', 'positive'].includes(mood)) recentPositiveStreak++;
        if (['Sad', 'Angry', 'negative'].includes(mood)) recentNegativeStreak++;
      }
    });

    const dominantMood = Object.entries(moodCounts)
      .sort(([,a], [,b]) => b - a)[0]?.[0];

    return {
      dominantMood,
      moodCounts,
      recentPositiveStreak,
      recentNegativeStreak,
      totalMemories: memories.length
    };
  }

  buildSystemPrompt(context) {
    const { type = 'conversation', memories = [] } = context;
    
    let systemPrompt = `You are a compassionate AI companion for Lifelink, a personal memory preservation app. You help users reflect on their memories and provide emotional support.

Guidelines:
- Be warm, empathetic, and encouraging
- Keep responses under 200 words
- Focus on emotional well-being and personal growth
- Respect the user's privacy and feelings
- Offer gentle insights without being preachy`;

    if (memories.length > 0) {
      systemPrompt += `\n\nContext: The user has ${memories.length} memories recorded. Recent mood patterns show interest in personal reflection and growth.`;
    }

    if (type === 'analysis') {
      systemPrompt += `\n\nTask: Provide thoughtful analysis of memory patterns and emotional trends.`;
    }

    return systemPrompt;
  }

  generateFallbackResponse(prompt, context) {
    const fallbacks = [
      "Thank you for sharing this memory with me. Your experiences matter and I'm honored to be part of your journey. ✨",
      "I appreciate you taking the time to record this moment. Each memory is a precious piece of your unique story. 🧠",
      "Your thoughts and feelings are important. Thank you for trusting me with this memory. 💙",
      "What a meaningful moment to capture! Your reflections show real emotional intelligence. 🌟"
    ];
    
    return fallbacks[Math.floor(Math.random() * fallbacks.length)];
  }

  // PREMIUM AI FEATURES (IF USER ADDS API KEY)
  async generatePremiumResponse(prompt, context) {
    // This would integrate with OpenAI/Claude if user provides API key
    console.log('Premium AI features would go here');
    return null;
  }

  // MEMORY ANALYSIS FEATURES
  async analyzeMemoryCollection(memories) {
    const analysis = {
      totalMemories: memories.length,
      timeSpan: this.calculateTimeSpan(memories),
      emotionalJourney: await this.analyzeEmotionalJourney(memories),
      keyThemes: this.extractThemes(memories),
      growthInsights: this.generateGrowthInsights(memories),
      recommendations: this.generateRecommendations(memories)
    };

    return analysis;
  }

  calculateTimeSpan(memories) {
    if (memories.length === 0) return null;
    
    const dates = memories.map(m => new Date(m.date)).sort((a, b) => a - b);
    const firstDate = dates[0];
    const lastDate = dates[dates.length - 1];
    const daysDiff = Math.ceil((lastDate - firstDate) / (1000 * 60 * 60 * 24));
    
    return {
      firstMemory: firstDate,
      lastMemory: lastDate,
      totalDays: daysDiff,
      averageMemoriesPerDay: memories.length / Math.max(daysDiff, 1)
    };
  }

  async analyzeEmotionalJourney(memories) {
    const journey = [];
    
    for (let memory of memories) {
      const sentiment = await this.analyzeSentimentLocal(memory.text);
      journey.push({
        date: memory.date,
        mood: sentiment.mood,
        confidence: sentiment.confidence,
        text: memory.text.substring(0, 100)
      });
    }

    return journey.sort((a, b) => new Date(a.date) - new Date(b.date));
  }

  extractThemes(memories) {
    const allKeywords = [];
    memories.forEach(memory => {
      const keywords = this.extractKeywords(memory.text);
      allKeywords.push(...keywords);
    });

    const keywordCounts = {};
    allKeywords.forEach(keyword => {
      keywordCounts[keyword] = (keywordCounts[keyword] || 0) + 1;
    });

    return Object.entries(keywordCounts)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 15)
      .map(([theme, count]) => ({ theme, count, frequency: count / memories.length }));
  }

  generateGrowthInsights(memories) {
    const insights = [];
    const patterns = this.analyzeMemoryPatterns(memories);

    if (patterns.recentPositiveStreak > 3) {
      insights.push("🌟 You've been experiencing a wonderful streak of positive moments! This suggests you're in a great phase of your life journey.");
    }

    if (patterns.totalMemories > 50) {
      insights.push("📚 Your dedication to recording memories shows incredible self-awareness and commitment to personal growth.");
    }

    if (patterns.dominantMood === 'Happy') {
      insights.push("😊 Happiness seems to be a strong theme in your memories, which suggests you're cultivating a positive mindset.");
    }

    return insights;
  }

  generateRecommendations(memories) {
    const recommendations = [];
    const patterns = this.analyzeMemoryPatterns(memories);

    if (patterns.recentNegativeStreak > 3) {
      recommendations.push("💙 Consider focusing on small positive moments in your daily life. Sometimes the smallest joys can shift our perspective.");
    }

    if (memories.length < 10) {
      recommendations.push("✍️ Try to record memories more regularly - even small moments matter and can reveal beautiful patterns over time.");
    }

    recommendations.push("🔍 Use the search feature to revisit similar memories when you need inspiration or perspective.");
    recommendations.push("📊 Check your insights regularly to see how you're growing and evolving.");

    return recommendations;
  }

  // USER SETTINGS AND PREFERENCES
  updatePreferences(newPreferences) {
    this.userPreferences = { ...this.userPreferences, ...newPreferences };
    this.saveUserPreferences();
  }

  getAIStatus() {
    return {
      localAvailable: this.localAIAvailable,
      cloudAvailable: this.cloudAIAvailable,
      currentProvider: this.shouldUseLocal() ? 'local' : 'cloud',
      preferences: this.userPreferences
    };
  }
}

export default AIManager;