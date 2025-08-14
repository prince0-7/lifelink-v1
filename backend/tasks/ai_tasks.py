"""
AI-related background tasks
"""
from celery import shared_task
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any
import asyncio
from services.ai_service import ai_service
from services.vector_service import vector_service
from services.websocket_manager import ws_manager
from models import Memory, MemoryInsight, User
import openai
import numpy as np

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_memory_embeddings(self, memory_id: str):
    """Generate embeddings for a memory"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def _generate():
            memory = await Memory.get(memory_id)
            if not memory:
                logger.error(f"Memory {memory_id} not found")
                return
            
            # Generate embeddings
            embeddings = await vector_service.generate_embeddings(memory.text)
            
            # Update memory with embeddings
            memory.embeddings = embeddings
            await memory.save()
            
            # Index in vector database
            await vector_service.index_memory(memory)
            
            logger.info(f"Generated embeddings for memory {memory_id}")
        
        loop.run_until_complete(_generate())
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        self.retry(countdown=60)


@shared_task(bind=True, max_retries=3)
def analyze_memory_sentiment(self, memory_id: str, user_id: str):
    """Analyze sentiment and generate insights for a memory"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def _analyze():
            memory = await Memory.get(memory_id)
            if not memory:
                return
            
            # Emit processing status
            await ws_manager.emit_ai_processing_status(
                user_id, 
                "analyzing", 
                {"step": "sentiment_analysis"}
            )
            
            # Perform sentiment analysis
            sentiment_data = await ai_service.analyze_sentiment(memory.text)
            
            # Generate insights
            insights = await ai_service.generate_insights(memory)
            
            # Save insights
            for insight in insights:
                memory_insight = MemoryInsight(
                    memory_id=memory.id,
                    insight_type=insight["type"],
                    content=insight["content"],
                    confidence=insight["confidence"],
                    created_at=datetime.now()
                )
                await memory_insight.insert()
                
                # Emit new insight
                await ws_manager.emit_memory_insight(user_id, {
                    "memory_id": str(memory.id),
                    "insight": insight
                })
            
            # Update memory with sentiment
            memory.sentiment_score = sentiment_data.get("score")
            memory.sentiment_label = sentiment_data.get("label")
            await memory.save()
            
            # Emit completion
            await ws_manager.emit_ai_processing_status(
                user_id, 
                "completed", 
                {"insights_count": len(insights)}
            )
        
        loop.run_until_complete(_analyze())
        
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        self.retry(countdown=60)


@shared_task
def generate_daily_insights():
    """Generate daily insights for all users"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def _generate():
        try:
            # Get all users
            users = await User.find_all().to_list()
            
            for user in users:
                # Get user's memories from the last 24 hours
                yesterday = datetime.now() - timedelta(days=1)
                memories = await Memory.find(
                    Memory.user_id == user.id,
                    Memory.date >= yesterday
                ).to_list()
                
                if not memories:
                    continue
                
                # Generate daily summary
                summary = await ai_service.generate_daily_summary(memories)
                
                # Find patterns
                patterns = await ai_service.find_memory_patterns(memories)
                
                # Create insight document
                daily_insight = MemoryInsight(
                    user_id=user.id,
                    insight_type="daily_summary",
                    content=summary,
                    metadata={
                        "patterns": patterns,
                        "memory_count": len(memories),
                        "date": datetime.now().date().isoformat()
                    },
                    created_at=datetime.now()
                )
                await daily_insight.insert()
                
                logger.info(f"Generated daily insights for user {user.id}")
                
        except Exception as e:
            logger.error(f"Error generating daily insights: {e}")
    
    loop.run_until_complete(_generate())


@shared_task
def update_memory_embeddings():
    """Update embeddings for memories without them"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def _update():
        try:
            # Find memories without embeddings
            memories = await Memory.find(
                {"embeddings": {"$exists": False}}
            ).limit(100).to_list()
            
            for memory in memories:
                # Queue embedding generation
                generate_memory_embeddings.delay(str(memory.id))
            
            logger.info(f"Queued {len(memories)} memories for embedding generation")
            
        except Exception as e:
            logger.error(f"Error updating embeddings: {e}")
    
    loop.run_until_complete(_update())


@shared_task(bind=True, max_retries=3)
def extract_entities(self, memory_id: str):
    """Extract entities from memory text"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def _extract():
            memory = await Memory.get(memory_id)
            if not memory:
                return
            
            # Extract entities using NLP
            entities = await ai_service.extract_entities(memory.text)
            
            # Update memory
            memory.entities = entities
            await memory.save()
            
            logger.info(f"Extracted {len(entities)} entities from memory {memory_id}")
        
        loop.run_until_complete(_extract())
        
    except Exception as e:
        logger.error(f"Error extracting entities: {e}")
        self.retry(countdown=60)


@shared_task
def find_similar_memories(memory_id: str, user_id: str, threshold: float = 0.7):
    """Find similar memories using vector search"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def _find():
        try:
            memory = await Memory.get(memory_id)
            if not memory or not memory.embeddings:
                return
            
            # Search for similar memories
            similar = await vector_service.search_similar(
                memory.embeddings,
                user_id=user_id,
                limit=5,
                threshold=threshold
            )
            
            # Create connections/insights
            if similar:
                insight = MemoryInsight(
                    memory_id=memory.id,
                    insight_type="similar_memories",
                    content=f"Found {len(similar)} similar memories",
                    metadata={
                        "similar_memory_ids": [s["id"] for s in similar],
                        "similarities": [s["score"] for s in similar]
                    },
                    confidence=0.9,
                    created_at=datetime.now()
                )
                await insight.insert()
                
                # Notify user
                await ws_manager.emit_memory_insight(user_id, {
                    "memory_id": str(memory.id),
                    "type": "similar_memories",
                    "similar": similar
                })
        
        except Exception as e:
            logger.error(f"Error finding similar memories: {e}")
    
    loop.run_until_complete(_find())
