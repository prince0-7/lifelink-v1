from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from config import settings
from models import Memory, MemoryInsight, MemoryCreate, MemoryUpdate, MemoryResponse, SearchQuery, AIResponse, AnalysisResponse, User
from services.ai_service_simple import ai_service
from services.websocket_manager import sio, ws_manager
from services.vector_service import vector_service
from graphql import create_graphql_router
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging
import base64
import os
import aiofiles
from pathlib import Path
import socketio
from tasks.ai_tasks import generate_memory_embeddings, analyze_memory_sentiment

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Lifelink API", version="2.0")

# Create Socket.IO app
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

# MongoDB client
client = AsyncIOMotorClient(settings.mongodb_url)
database = client[settings.database_name]

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.on_event("startup")
async def startup_event():
    # Initialize Beanie with the Memory, MemoryInsight, and User document models
    await init_beanie(database=database, document_models=[Memory, MemoryInsight, User])
    logger.info("Lifelink API has started.")
    
    # Check AI availability
    ai_available = await ai_service.check_local_ai()
    if ai_available:
        logger.info("AI service is available")
    else:
        logger.warning("AI service is not available - will use fallback responses")
    
    # Add GraphQL endpoint
    graphql_router = create_graphql_router()
    app.include_router(graphql_router, prefix="/graphql")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Lifelink API is shutting down.")

# API Endpoints
@app.post("/memories/", response_model=MemoryResponse)
async def create_memory(memory: MemoryCreate):
    logger.info(f"Creating memory: {memory.text}")
    try:
        # Generate AI response
        logger.info("Generating AI response...")
        ai_response = await ai_service.generate_response(memory.text, {})
        logger.info(f"AI response: {ai_response}")
        
        # Create memory document
        new_memory = Memory(
            text=memory.text,
            date=datetime.now(),
            mood=memory.mood,
            detected_mood=ai_response.get("mood") or memory.mood,
            tags=memory.tags,
            ai_response=ai_response.get("response", "Thank you for sharing this memory!"),
            ai_source=ai_response.get("source", "fallback"),
            keywords=ai_response.get("keywords", [])
        )
        logger.info("Memory document created")
        
        # Save to database
        await new_memory.insert()
        logger.info(f"Memory saved with ID: {new_memory.id}")
        
        # Queue background tasks
        generate_memory_embeddings.delay(str(new_memory.id))
        if new_memory.user_id:
            analyze_memory_sentiment.delay(str(new_memory.id), new_memory.user_id)
        
        # Return response
        memory_dict = new_memory.dict()
        memory_dict['id'] = str(new_memory.id)
        return MemoryResponse(**memory_dict)
        
    except Exception as e:
        logger.error(f"Error creating memory: {str(e)}")
        # Try to save memory without AI features
        try:
            new_memory = Memory(
                text=memory.text,
                date=datetime.now(),
                mood=memory.mood,
                detected_mood=memory.mood,
                tags=memory.tags,
                ai_response="Thank you for sharing this memory with me! ✨",
                ai_source="fallback",
                keywords=[]
            )
            await new_memory.insert()
            memory_dict = new_memory.dict()
            memory_dict['id'] = str(new_memory.id)
            return MemoryResponse(**memory_dict)
        except Exception as inner_e:
            logger.error(f"Failed to save memory: {str(inner_e)}")
            raise HTTPException(status_code=500, detail="Failed to save memory")

@app.get("/memories/", response_model=List[MemoryResponse])
async def list_memories():
    memories = await Memory.find_all().to_list()
    responses = []
    for memory in memories:
        memory_dict = memory.dict()
        memory_dict['id'] = str(memory.id)
        responses.append(MemoryResponse(**memory_dict))
    return responses

@app.put("/memories/{memory_id}", response_model=MemoryResponse)
async def update_memory(memory_id: str, memory_update: MemoryUpdate):
    memory = await Memory.get(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    if memory_update.text:
        memory.text = memory_update.text
    if memory_update.mood:
        memory.mood = memory_update.mood
    if memory_update.tags:
        memory.tags = memory_update.tags

    await memory.save()
    memory_dict = memory.dict()
    memory_dict['id'] = str(memory.id)
    return MemoryResponse(**memory_dict)

@app.delete("/memories/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(memory_id: str):
    memory = await Memory.get(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    await memory.delete()

# Semantic search endpoint
@app.post("/memories/search", response_model=List[MemoryResponse])
async def search_memories(query: SearchQuery):
    """Search memories using semantic search"""
    # Perform semantic search
    results = await vector_service.semantic_search(
        query=query.query,
        limit=query.limit,
        filters={
            "mood": query.mood_filter.value if query.mood_filter else None,
            "date_from": query.date_from.isoformat() if query.date_from else None,
            "date_to": query.date_to.isoformat() if query.date_to else None
        }
    )
    
    # Fetch full memories
    memory_responses = []
    for result in results:
        memory = await Memory.get(result["id"])
        if memory:
            memory_dict = memory.dict()
            memory_dict['id'] = str(memory.id)
            memory_dict['relevance_score'] = result["score"]
            memory_responses.append(MemoryResponse(**memory_dict))
    
    return memory_responses

# Get memory insights
@app.get("/memories/{memory_id}/insights", response_model=List[Dict[str, Any]])
async def get_memory_insights(memory_id: str):
    """Get AI-generated insights for a memory"""
    insights = await MemoryInsight.find(
        MemoryInsight.memory_id == memory_id
    ).to_list()
    
    return [
        {
            "id": str(insight.id),
            "type": insight.insight_type,
            "content": insight.content,
            "confidence": insight.confidence,
            "created_at": insight.created_at
        }
        for insight in insights
    ]

# Health check endpoint
@app.get("/health")
async def health_check():
    vector_stats = vector_service.get_index_stats()
    return {
        "status": "healthy",
        "version": "2.0",
        "ai_available": ai_service.local_ai_available,
        "vector_db": vector_stats,
        "websocket_clients": len(ws_manager.connected_users)
    }

# Run the application
if __name__ == "__main__":
    import uvicorn
    import sys
    import platform
    
    # On Windows, avoid multiprocessing issues
    if platform.system() == "Windows" and settings.reload:
        # Use the simple reload without workers
        uvicorn.run(
            "main:socket_app",  # Use socket_app instead of app
            host=settings.host,
            port=settings.port,
            reload=True,
            reload_dirs=["."],
            workers=1
        )
    else:
        uvicorn.run(
            "main:socket_app",  # Use socket_app instead of app
            host=settings.host,
            port=settings.port,
            reload=settings.reload
        )
