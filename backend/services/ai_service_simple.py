import httpx
from typing import List, Dict, Optional
import numpy as np
from config import settings
from models import MoodType
import logging
import sys

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.local_ai_available = False
        self.embedding_model = None
        self.initialize()
    
    def initialize(self):
        """Initialize AI models and check availability"""
        logger.info("Initializing AI Service (simplified version)")
        # Skip embedding model for now
        self.embedding_model = None
        
        # Check Ollama availability
        import asyncio
        if sys.platform.startswith('win'):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    async def check_local_ai(self) -> bool:
        """Check if Ollama is available"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{settings.ollama_base_url}/api/tags", timeout=5.0)
                if response.status_code == 200:
                    self.local_ai_available = True
                    logger.info("Local AI (Ollama) is available")
                    return True
        except Exception as e:
            logger.warning(f"Local AI not available: {e}")
        
        self.local_ai_available = False
        return False
    
    async def generate_response(self, prompt: str, context: Dict = {}) -> Dict:
        """Generate AI response using available AI services"""
        try:
            # Try local AI first
            if self.local_ai_available:
                response = await self._generate_local_response(prompt, context)
                if response:
                    return {
                        "response": response,
                        "source": "local",
                        "mood": None,
                        "keywords": self._extract_keywords(prompt),
                        "sentiment_scores": None
                    }
            
            # Fallback to enhanced local processing
            response = self._generate_enhanced_local_response(prompt, context)
            sentiment = self._analyze_sentiment(prompt)
            
            return {
                "response": response,
                "source": "enhanced-local",
                "mood": sentiment["mood"],
                "keywords": sentiment["keywords"],
                "sentiment_scores": sentiment["scores"]
            }
            
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return {
                "response": "Thank you for sharing this memory with me. Your experiences are valuable and I'm honored to be part of your journey. ✨",
                "source": "fallback",
                "mood": MoodType.NEUTRAL,
                "keywords": [],
                "sentiment_scores": {}
            }
    
    async def _generate_local_response(self, prompt: str, context: Dict) -> Optional[str]:
        """Generate response using Ollama"""
        if not self.local_ai_available:
            return None
        
        try:
            system_prompt = self._build_system_prompt(context)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.ollama_base_url}/api/generate",
                    json={
                        "model": "llama3.1:8b",
                        "prompt": f"{system_prompt}\n\nUser: {prompt}",
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "max_tokens": 200
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "")
                    
        except Exception as e:
            logger.error(f"Local AI error: {e}")
        
        return None
    
    def _generate_enhanced_local_response(self, prompt: str, context: Dict) -> str:
        """Generate response using local processing"""
        sentiment = self._analyze_sentiment(prompt)
        memories = context.get("memories", [])
        
        # Analyze patterns if memories provided
        patterns = self._analyze_memory_patterns(memories) if memories else {}
        
        # Generate contextual response based on sentiment
        if sentiment["mood"] == MoodType.HAPPY:
            response = "I can feel the joy in your words! "
            if patterns.get("recent_positive_streak", 0) > 2:
                response += "You've been experiencing so many wonderful moments lately. "
            response += "These happy memories are precious treasures that brighten your life journey. ✨"
            
        elif sentiment["mood"] == MoodType.SAD:
            response = "I hear that you're going through something difficult. "
            if patterns.get("recent_negative_streak", 0) > 2:
                response += "I notice this has been a challenging period. Remember, you have inner strength that has carried you through before. "
            response += "Your feelings are valid, and I'm here to support you. 💙"
            
        elif sentiment["mood"] == MoodType.CALM:
            response = "There's a beautiful sense of peace in your words. "
            response += "These moments of tranquility are essential for your well-being. 🧘"
            
        else:
            response = "Thank you for sharing this moment with me. "
            if len(memories) > 10:
                response += "Your growing collection of memories creates a rich tapestry of experiences. "
            response += "Every memory adds depth to your unique story. 📖"
        
        # Add personalized insights
        if patterns.get("dominant_mood") and patterns["dominant_mood"] != MoodType.NEUTRAL:
            response += f"\n\nI've noticed {patterns['dominant_mood'].lower()} has been a recurring theme in your recent memories."
        
        if sentiment["keywords"]:
            response += f" The themes of {', '.join(sentiment['keywords'][:3])} really stand out."
        
        return response
    
    def _analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of text"""
        positive_words = {'happy', 'joy', 'excited', 'amazing', 'wonderful', 'great', 'love', 
                         'blessed', 'grateful', 'accomplished', 'proud', 'fantastic'}
        negative_words = {'sad', 'lonely', 'depressed', 'angry', 'upset', 'frustrated', 
                         'worried', 'anxious', 'stressed', 'disappointed', 'hurt'}
        calm_words = {'calm', 'peaceful', 'relaxed', 'serene', 'tranquil', 'quiet', 'meditative'}
        
        words = text.lower().split()
        
        positive_score = sum(1 for word in words if any(pw in word for pw in positive_words))
        negative_score = sum(1 for word in words if any(nw in word for nw in negative_words))
        calm_score = sum(1 for word in words if any(cw in word for cw in calm_words))
        
        total_score = positive_score + negative_score + calm_score
        
        if total_score == 0:
            mood = MoodType.NEUTRAL
        elif positive_score > negative_score and positive_score > calm_score:
            mood = MoodType.HAPPY
        elif negative_score > positive_score and negative_score > calm_score:
            mood = MoodType.SAD
        elif calm_score > 0:
            mood = MoodType.CALM
        else:
            mood = MoodType.NEUTRAL
        
        return {
            "mood": mood,
            "scores": {
                "positive": positive_score,
                "negative": negative_score,
                "calm": calm_score
            },
            "keywords": self._extract_keywords(text)
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        stop_words = {'the', 'and', 'but', 'for', 'are', 'was', 'were', 'been', 'have', 
                     'has', 'had', 'will', 'would', 'could', 'should', 'this', 'that',
                     'with', 'from', 'they', 'them', 'their', 'there', 'where', 'when'}
        
        words = text.lower().replace('.', ' ').replace(',', ' ').split()
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        
        # Return unique keywords
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)
        
        return unique_keywords[:10]
    
    def _analyze_memory_patterns(self, memories: List[Dict]) -> Dict:
        """Analyze patterns in memory collection"""
        if not memories:
            return {}
        
        recent = memories[:10]  # Last 10 memories
        mood_counts = {}
        recent_positive_streak = 0
        recent_negative_streak = 0
        
        for i, memory in enumerate(recent):
            mood = memory.get("mood", MoodType.NEUTRAL)
            mood_counts[mood] = mood_counts.get(mood, 0) + 1
            
            if i < 5:  # Last 5 memories
                if mood in [MoodType.HAPPY, "positive"]:
                    recent_positive_streak += 1
                elif mood in [MoodType.SAD, MoodType.ANGRY, "negative"]:
                    recent_negative_streak += 1
        
        # Find dominant mood
        dominant_mood = max(mood_counts.items(), key=lambda x: x[1])[0] if mood_counts else MoodType.NEUTRAL
        
        return {
            "dominant_mood": dominant_mood,
            "mood_counts": mood_counts,
            "recent_positive_streak": recent_positive_streak,
            "recent_negative_streak": recent_negative_streak,
            "total_memories": len(memories)
        }
    
    def _build_system_prompt(self, context: Dict) -> str:
        """Build system prompt for AI"""
        memories_count = len(context.get("memories", []))
        
        prompt = """You are a compassionate AI companion for Lifelink, a personal memory preservation app.
        You help users reflect on their memories and provide emotional support.
        
        Guidelines:
        - Be warm, empathetic, and encouraging
        - Keep responses under 200 words
        - Focus on emotional well-being and personal growth
        - Respect privacy and feelings
        - Offer gentle insights without being preachy"""
        
        if memories_count > 0:
            prompt += f"\n\nContext: The user has {memories_count} memories recorded."
        
        if context.get("type") == "analysis":
            prompt += "\n\nTask: Provide thoughtful analysis of memory patterns."
        
        return prompt
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate a simple embedding for text (placeholder)"""
        # For now, return a simple hash-based embedding
        # In production, use sentence-transformers
        try:
            # Simple character-based embedding (placeholder)
            embedding = [0.0] * 384  # Standard embedding size
            for i, char in enumerate(text[:384]):
                embedding[i % 384] = float(ord(char)) / 255.0
            return embedding
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return 0.0

# Singleton instance
ai_service = AIService()
