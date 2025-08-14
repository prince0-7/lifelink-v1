from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from config import settings
from models import (
    Memory, MemoryInsight, MemoryCreate, MemoryUpdate, 
    MemoryResponse, SearchQuery, AIResponse, AnalysisResponse
)
from services.ai_service_simple import ai_service
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager
import logging
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global database client
db_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    global db_client
    
    # Startup
    try:
        # Connect to MongoDB
        db_client = AsyncIOMotorClient(settings.mongodb_url)
        
        # Initialize Beanie with document models
        await init_beanie(
            database=db_client[settings.database_name],
            document_models=[Memory, MemoryInsight]
        )
        
        # Check AI availability
        await ai_service.check_local_ai()
        
        logger.info("✅ Lifelink API started successfully!")
        logger.info(f"📍 Database: {settings.database_name}")
        logger.info(f"🤖 Local AI Available: {ai_service.local_ai_available}")
    except Exception as e:
        logger.error(f"Startup error: {e}")
    
    yield
    
    # Shutdown
    if db_client:
        db_client.close()
    logger.info("👋 Lifelink API shutting down...")

# Create FastAPI app with lifespan
app = FastAPI(
    title="Lifelink API",
    description="AI-powered personal memory preservation API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Lifelink API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Check API health status"""
    return {
        "status": "healthy",
        "database": "connected" if db_client else "disconnected",
        "ai_status": {
            "local_ai": ai_service.local_ai_available,
            "embedding_model": ai_service.embedding_model is not None
        }
    }

# Memory CRUD endpoints
@app.post("/api/memories", response_model=MemoryResponse)
async def create_memory(memory_data: MemoryCreate):
    """Create a new memory with AI processing"""
    try:
        # Generate AI response and analysis
        ai_result = await ai_service.generate_response(
            memory_data.text,
            {"type": "conversation", "memories": []}
        )
        
        # Generate embedding for semantic search
        embedding = ai_service.generate_embedding(memory_data.text)
        
        # Create memory document
        memory = Memory(
            text=memory_data.text,
            date=datetime.utcnow(),
            mood=memory_data.mood,
            detected_mood=ai_result.get("mood"),
            tags=memory_data.tags or [],
            ai_response=ai_result["response"],
            ai_source=ai_result["source"],
            embedding=embedding,
            keywords=ai_result.get("keywords", []),
            sentiment_scores=ai_result.get("sentiment_scores")
        )
        
        # Save to database
        await memory.create()
        
        # Convert to response model
        return MemoryResponse(
            id=str(memory.id),
            text=memory.text,
            date=memory.date,
            mood=memory.mood,
            detected_mood=memory.detected_mood,
            tags=memory.tags,
            ai_response=memory.ai_response,
            ai_source=memory.ai_source,
            audio_url=memory.audio_url,
            image_url=memory.image_url,
            keywords=memory.keywords
        )
        
    except Exception as e:
        logger.error(f"Error creating memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memories", response_model=List[MemoryResponse])
async def list_memories(
    skip: int = 0,
    limit: int = 50,
    mood: Optional[str] = None,
    tag: Optional[str] = None
):
    """List memories with optional filtering"""
    try:
        # Build query
        query = {}
        if mood:
            query["mood"] = mood
        if tag:
            query["tags"] = {"$in": [tag]}
        
        # Fetch memories
        memories = await Memory.find(query).skip(skip).limit(limit).sort("-date").to_list()
        
        # Convert to response models
        return [
            MemoryResponse(
                id=str(memory.id),
                text=memory.text,
                date=memory.date,
                mood=memory.mood,
                detected_mood=memory.detected_mood,
                tags=memory.tags,
                ai_response=memory.ai_response,
                ai_source=memory.ai_source,
                audio_url=memory.audio_url,
                image_url=memory.image_url,
                keywords=memory.keywords
            )
            for memory in memories
        ]
    except Exception as e:
        logger.error(f"Error listing memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memories/{memory_id}", response_model=MemoryResponse)
async def get_memory(memory_id: str):
    """Get a specific memory by ID"""
    memory = await Memory.get(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return MemoryResponse(
        id=str(memory.id),
        text=memory.text,
        date=memory.date,
        mood=memory.mood,
        detected_mood=memory.detected_mood,
        tags=memory.tags,
        ai_response=memory.ai_response,
        ai_source=memory.ai_source,
        audio_url=memory.audio_url,
        image_url=memory.image_url,
        keywords=memory.keywords
    )

@app.delete("/api/memories/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(memory_id: str):
    """Delete a memory"""
    memory = await Memory.get(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    await memory.delete()

# Test AI endpoint
@app.post("/api/test-ai")
async def test_ai(text: str):
    """Test AI response generation"""
    result = await ai_service.generate_response(text, {})
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_simple:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload
    )
