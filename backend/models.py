from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from beanie import Document, Indexed
from enum import Enum

class MoodType(str, Enum):
    HAPPY = "Happy"
    SAD = "Sad"
    ANGRY = "Angry"
    CALM = "Calm"
    NEUTRAL = "Neutral"

class Memory(Document):
    """Main memory document model"""
    user_id: Optional[str] = None  # For future multi-user support
    text: str
    date: Indexed(datetime)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Mood and tags
    mood: MoodType = MoodType.NEUTRAL
    detected_mood: Optional[MoodType] = None
    tags: List[str] = []
    
    # Media
    audio_url: Optional[str] = None
    image_url: Optional[str] = None
    media_urls: List[str] = []  # Support multiple media files
    transcription: Optional[str] = None
    
    # Location
    location: Optional[Dict[str, Any]] = None  # lat, lng, place_name
    
    # AI Generated
    ai_response: Optional[str] = None
    ai_source: Optional[str] = None  # local, cloud, gpt-4, enhanced-local
    embeddings: Optional[List[float]] = None  # Vector embedding for search
    keywords: List[str] = []
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    entities: Optional[List[Dict[str, Any]]] = None  # Named entities
    
    # Connections
    related_memory_ids: List[str] = []
    is_milestone: bool = False
    
    class Settings:
        name = "memories"
        indexes = [
            [("date", -1)],
            [("mood", 1)],
            [("tags", 1)],
            [("keywords", 1)]
        ]

class MemoryInsight(Document):
    """Individual insights for memories"""
    memory_id: Optional[str] = None
    user_id: Optional[str] = None
    insight_type: str  # sentiment, pattern, connection, milestone, etc.
    content: str
    confidence: float = 0.0
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "memory_insights"
        indexes = [
            [("memory_id", 1)],
            [("user_id", 1)],
            [("insight_type", 1)]
        ]

# Request/Response Models
class MemoryCreate(BaseModel):
    """Request model for creating a memory"""
    text: str
    mood: Optional[MoodType] = MoodType.NEUTRAL
    tags: Optional[List[str]] = []
    audio_data: Optional[str] = None  # Base64 encoded audio
    image_data: Optional[str] = None  # Base64 encoded image

class MemoryUpdate(BaseModel):
    """Request model for updating a memory"""
    text: Optional[str] = None
    mood: Optional[MoodType] = None
    tags: Optional[List[str]] = None

class MemoryResponse(BaseModel):
    """Response model for memory endpoints"""
    id: str
    text: str
    date: datetime
    mood: MoodType
    detected_mood: Optional[MoodType]
    tags: List[str]
    ai_response: Optional[str]
    ai_source: Optional[str]
    audio_url: Optional[str]
    image_url: Optional[str]
    keywords: List[str]
    relevance_score: Optional[float] = None

class SearchQuery(BaseModel):
    """Request model for semantic search"""
    query: str
    mood_filter: Optional[MoodType] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = 20

class AIResponse(BaseModel):
    """Response from AI processing"""
    response: str
    source: str  # local, cloud, enhanced-local, fallback
    mood: Optional[MoodType] = None
    keywords: List[str] = []
    sentiment_scores: Optional[Dict[str, float]] = None

class AnalysisResponse(BaseModel):
    """Response for memory analysis"""
    total_memories: int
    time_span: Optional[Dict[str, Any]]
    emotional_journey: List[Dict[str, Any]]
    key_themes: List[Dict[str, Any]]
    growth_insights: List[str]
    recommendations: List[str]

# User Authentication Model
class User(Document):
    """User model for authentication"""
    username: Indexed(str, unique=True)
    email: Indexed(EmailStr, unique=True)
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    # OAuth
    oauth_provider: Optional[str] = None
    oauth_id: Optional[str] = None
    
    # Preferences
    preferences: Dict[str, Any] = {
        "theme": "light",
        "language": "en",
        "notifications": True,
        "privacy_mode": False
    }
    
    # Stats
    total_memories: int = 0
    last_memory_date: Optional[datetime] = None
    
    class Settings:
        name = "users"
