"""
Enhanced AI service with GPT-4o, LangChain, and advanced NLP
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

# OpenAI
import openai
from openai import AsyncOpenAI

# LangChain
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain.memory import ConversationSummaryMemory
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# NLP
import spacy
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# Initialize
logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Download NLTK data
nltk.download('vader_lexicon', quiet=True)
nltk.download('punkt', quiet=True)


class EnhancedAIService:
    """Enhanced AI service with GPT-4o and advanced NLP"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.nlp = None
        self.sia = None
        self.llm = None
        self._initialize()
    
    def _initialize(self):
        """Initialize NLP models and LangChain"""
        try:
            # Load spaCy model
            self.nlp = spacy.load("en_core_web_sm")
            
            # Initialize sentiment analyzer
            self.sia = SentimentIntensityAnalyzer()
            
            # Initialize LangChain with GPT-4o
            self.llm = ChatOpenAI(
                model="gpt-4-0125-preview",
                temperature=0.7,
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
            
            logger.info("Enhanced AI service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced AI service: {e}")
    
    async def generate_response(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI response using GPT-4o"""
        try:
            # Create prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a compassionate AI companion helping users reflect on their memories and emotions. 
                Your responses should be:
                - Empathetic and supportive
                - Insightful and thought-provoking
                - Encouraging personal growth
                - Respecting privacy and boundaries
                
                Analyze the memory and provide:
                1. A supportive response
                2. Key themes or patterns
                3. Suggested reflection questions
                4. Mood analysis
                """),
                ("human", "{memory}")
            ])
            
            # Create chain
            chain = LLMChain(llm=self.llm, prompt=prompt)
            
            # Generate response
            response = await chain.arun(memory=text)
            
            # Extract mood
            mood = await self._detect_mood_gpt4(text)
            
            # Extract keywords
            keywords = await self._extract_keywords(text)
            
            return {
                "response": response,
                "source": "gpt-4o",
                "mood": mood,
                "keywords": keywords,
                "model": "gpt-4-0125-preview"
            }
            
        except Exception as e:
            logger.error(f"Error generating GPT-4o response: {e}")
            # Fallback to GPT-3.5
            return await self._generate_gpt35_response(text)
    
    async def _generate_gpt35_response(self, text: str) -> Dict[str, Any]:
        """Fallback to GPT-3.5-turbo"""
        try:
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a compassionate AI companion. Provide a brief, supportive response to the user's memory."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            return {
                "response": response.choices[0].message.content,
                "source": "gpt-3.5",
                "mood": await self._detect_mood_nltk(text),
                "keywords": await self._extract_keywords(text),
                "model": "gpt-3.5-turbo"
            }
            
        except Exception as e:
            logger.error(f"Error with GPT-3.5: {e}")
            return self._get_fallback_response(text)
    
    async def _detect_mood_gpt4(self, text: str) -> str:
        """Detect mood using GPT-4"""
        try:
            response = await client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "Analyze the emotional tone of this text and respond with ONLY one word: Happy, Sad, Angry, Calm, or Neutral"
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.3,
                max_tokens=10
            )
            
            mood = response.choices[0].message.content.strip().title()
            if mood not in ["Happy", "Sad", "Angry", "Calm", "Neutral"]:
                mood = "Neutral"
            return mood
            
        except Exception as e:
            logger.error(f"Error detecting mood with GPT-4: {e}")
            return await self._detect_mood_nltk(text)
    
    async def _detect_mood_nltk(self, text: str) -> str:
        """Detect mood using NLTK"""
        try:
            loop = asyncio.get_event_loop()
            scores = await loop.run_in_executor(
                self.executor,
                self.sia.polarity_scores,
                text
            )
            
            # Map sentiment scores to moods
            if scores['compound'] >= 0.5:
                return "Happy"
            elif scores['compound'] <= -0.5:
                return "Sad"
            elif scores['neg'] > 0.5:
                return "Angry"
            elif abs(scores['compound']) < 0.1:
                return "Neutral"
            else:
                return "Calm"
                
        except Exception as e:
            logger.error(f"Error with NLTK mood detection: {e}")
            return "Neutral"
    
    async def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords using spaCy"""
        try:
            loop = asyncio.get_event_loop()
            doc = await loop.run_in_executor(self.executor, self.nlp, text)
            
            # Extract important words (nouns, verbs, adjectives)
            keywords = []
            for token in doc:
                if (token.pos_ in ["NOUN", "VERB", "ADJ"] and 
                    not token.is_stop and 
                    len(token.text) > 3):
                    keywords.append(token.lemma_.lower())
            
            # Also extract named entities
            for ent in doc.ents:
                keywords.append(ent.text.lower())
            
            # Remove duplicates and limit
            keywords = list(set(keywords))[:10]
            
            return keywords
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Detailed sentiment analysis"""
        try:
            # NLTK sentiment
            scores = self.sia.polarity_scores(text)
            
            # GPT-4 analysis for nuanced understanding
            response = await client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[
                    {
                        "role": "system",
                        "content": """Analyze the emotional nuances in this text. Provide:
                        1. Primary emotion
                        2. Secondary emotions
                        3. Emotional intensity (1-10)
                        4. Brief explanation
                        Format as JSON."""
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.5,
                max_tokens=200
            )
            
            import json
            gpt_analysis = json.loads(response.choices[0].message.content)
            
            return {
                "score": scores['compound'],
                "label": await self._detect_mood_gpt4(text),
                "nltk_scores": scores,
                "gpt_analysis": gpt_analysis
            }
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return {
                "score": 0.0,
                "label": "Neutral",
                "error": str(e)
            }
    
    async def extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract named entities"""
        try:
            loop = asyncio.get_event_loop()
            doc = await loop.run_in_executor(self.executor, self.nlp, text)
            
            entities = []
            for ent in doc.ents:
                entities.append({
                    "text": ent.text,
                    "type": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char
                })
            
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return []
    
    async def generate_insights(self, memory: Any) -> List[Dict[str, Any]]:
        """Generate deep insights about a memory"""
        try:
            prompt = f"""
            Analyze this memory and provide 3-5 insights:
            
            Memory: {memory.text}
            Date: {memory.date}
            Mood: {memory.mood}
            
            Provide insights about:
            1. Emotional patterns
            2. Personal growth opportunities
            3. Connections to wellbeing
            4. Suggested actions or reflections
            
            Format each insight as JSON with: type, content, confidence (0-1)
            """
            
            response = await client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[
                    {"role": "system", "content": "You are an insightful life coach and psychologist."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            # Parse insights
            import json
            insights_text = response.choices[0].message.content
            insights = json.loads(insights_text)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return []
    
    async def generate_daily_summary(self, memories: List[Any]) -> str:
        """Generate a daily summary of memories"""
        try:
            # Prepare memory texts
            memory_texts = "\n\n".join([
                f"[{m.date.strftime('%H:%M')}] {m.text} (Mood: {m.mood})"
                for m in memories
            ])
            
            prompt = f"""
            Create a compassionate daily summary of these memories:
            
            {memory_texts}
            
            Include:
            1. Overall emotional theme
            2. Key moments or experiences
            3. Patterns noticed
            4. Encouragement for tomorrow
            
            Keep it warm, personal, and under 200 words.
            """
            
            response = await client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[
                    {"role": "system", "content": "You are a caring journal companion."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")
            return "Today was filled with various experiences and emotions. Take a moment to reflect on what you've learned."
    
    async def find_memory_patterns(self, memories: List[Any]) -> List[Dict[str, Any]]:
        """Find patterns across memories"""
        try:
            # Analyze with GPT-4
            memory_data = [
                {
                    "text": m.text,
                    "mood": m.mood,
                    "date": m.date.isoformat(),
                    "keywords": m.keywords
                }
                for m in memories
            ]
            
            prompt = f"""
            Analyze these memories and identify patterns:
            
            {json.dumps(memory_data, indent=2)}
            
            Find patterns in:
            1. Recurring themes
            2. Emotional cycles
            3. Triggers for different moods
            4. Growth areas
            
            Return as JSON array of pattern objects with: type, description, frequency, memories_affected
            """
            
            response = await client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[
                    {"role": "system", "content": "You are a pattern recognition expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=500
            )
            
            import json
            patterns = json.loads(response.choices[0].message.content)
            return patterns
            
        except Exception as e:
            logger.error(f"Error finding patterns: {e}")
            return []
    
    def _get_fallback_response(self, text: str) -> Dict[str, Any]:
        """Fallback response when all AI services fail"""
        responses = [
            "Thank you for sharing this memory with me. Every moment you capture is valuable.",
            "I appreciate you taking the time to reflect on this experience.",
            "Your memories are important. Thank you for preserving this moment.",
            "Every memory you share helps paint the picture of your unique journey.",
            "Thank you for trusting me with this part of your story."
        ]
        
        import random
        return {
            "response": random.choice(responses),
            "source": "fallback",
            "mood": "Neutral",
            "keywords": [],
            "model": "none"
        }


# Create enhanced AI service instance
enhanced_ai_service = EnhancedAIService()
