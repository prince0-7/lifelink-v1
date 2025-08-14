"""
GraphQL schema for LifeLink
"""
import strawberry
from strawberry.types import Info
from typing import List, Optional, Dict, Any
from datetime import datetime
import strawberry.fastapi
from models import Memory, MemoryInsight, User
from beanie import PydanticObjectId


@strawberry.type
class MemoryType:
    id: str
    text: str
    date: datetime
    mood: Optional[str]
    detected_mood: Optional[str]
    tags: List[str]
    keywords: List[str]
    ai_response: Optional[str]
    ai_source: Optional[str]
    embeddings: Optional[List[float]]
    media_urls: List[str]
    location: Optional[Dict[str, Any]]
    
    @classmethod
    def from_db(cls, memory: Memory) -> "MemoryType":
        return cls(
            id=str(memory.id),
            text=memory.text,
            date=memory.date,
            mood=memory.mood,
            detected_mood=memory.detected_mood,
            tags=memory.tags or [],
            keywords=memory.keywords or [],
            ai_response=memory.ai_response,
            ai_source=memory.ai_source,
            embeddings=memory.embeddings,
            media_urls=memory.media_urls or [],
            location=memory.location
        )


@strawberry.type
class InsightType:
    id: str
    memory_id: str
    insight_type: str
    content: str
    confidence: float
    created_at: datetime
    
    @classmethod
    def from_db(cls, insight: MemoryInsight) -> "InsightType":
        return cls(
            id=str(insight.id),
            memory_id=str(insight.memory_id),
            insight_type=insight.insight_type,
            content=insight.content,
            confidence=insight.confidence,
            created_at=insight.created_at
        )


@strawberry.type
class MoodTrend:
    mood: str
    count: int
    percentage: float
    dates: List[datetime]


@strawberry.type
class MemoryStats:
    total_memories: int
    total_words: int
    average_words_per_memory: float
    most_common_tags: List[str]
    mood_distribution: List[MoodTrend]
    memories_per_day: Dict[str, int]


@strawberry.input
class MemoryFilter:
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    moods: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    search_text: Optional[str] = None
    has_media: Optional[bool] = None
    limit: Optional[int] = 100


@strawberry.input
class SemanticSearchInput:
    query: str
    limit: Optional[int] = 10
    threshold: Optional[float] = 0.7


@strawberry.type
class Query:
    @strawberry.field
    async def memory(self, memory_id: str) -> Optional[MemoryType]:
        """Get a specific memory by ID"""
        memory = await Memory.get(memory_id)
        return MemoryType.from_db(memory) if memory else None
    
    @strawberry.field
    async def memories(
        self, 
        filter: Optional[MemoryFilter] = None,
        offset: int = 0,
        limit: int = 100
    ) -> List[MemoryType]:
        """Get memories with optional filtering"""
        query = {}
        
        if filter:
            if filter.start_date:
                query["date"] = {"$gte": filter.start_date}
            if filter.end_date:
                query.setdefault("date", {})["$lte"] = filter.end_date
            if filter.moods:
                query["$or"] = [
                    {"mood": {"$in": filter.moods}},
                    {"detected_mood": {"$in": filter.moods}}
                ]
            if filter.tags:
                query["tags"] = {"$in": filter.tags}
            if filter.search_text:
                query["$text"] = {"$search": filter.search_text}
            if filter.has_media is not None:
                if filter.has_media:
                    query["media_urls"] = {"$exists": True, "$ne": []}
                else:
                    query["$or"] = [
                        {"media_urls": {"$exists": False}},
                        {"media_urls": []}
                    ]
        
        memories = await Memory.find(query).skip(offset).limit(limit).to_list()
        return [MemoryType.from_db(m) for m in memories]
    
    @strawberry.field
    async def semantic_search(self, input: SemanticSearchInput) -> List[MemoryType]:
        """Search memories using semantic similarity"""
        # This will be implemented with vector search
        # For now, return text search results
        memories = await Memory.find(
            {"$text": {"$search": input.query}}
        ).limit(input.limit).to_list()
        return [MemoryType.from_db(m) for m in memories]
    
    @strawberry.field
    async def memory_insights(self, memory_id: str) -> List[InsightType]:
        """Get insights for a specific memory"""
        insights = await MemoryInsight.find(
            MemoryInsight.memory_id == PydanticObjectId(memory_id)
        ).to_list()
        return [InsightType.from_db(i) for i in insights]
    
    @strawberry.field
    async def memory_stats(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> MemoryStats:
        """Get statistics about memories"""
        query = {}
        if start_date:
            query["date"] = {"$gte": start_date}
        if end_date:
            query.setdefault("date", {})["$lte"] = end_date
        
        memories = await Memory.find(query).to_list()
        
        # Calculate stats
        total_memories = len(memories)
        total_words = sum(len(m.text.split()) for m in memories)
        avg_words = total_words / total_memories if total_memories > 0 else 0
        
        # Tag frequency
        tag_counts = {}
        for memory in memories:
            for tag in (memory.tags or []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        most_common_tags = sorted(
            tag_counts.keys(), 
            key=lambda x: tag_counts[x], 
            reverse=True
        )[:10]
        
        # Mood distribution
        mood_data = {}
        for memory in memories:
            mood = memory.detected_mood or memory.mood
            if mood:
                if mood not in mood_data:
                    mood_data[mood] = {"count": 0, "dates": []}
                mood_data[mood]["count"] += 1
                mood_data[mood]["dates"].append(memory.date)
        
        mood_distribution = [
            MoodTrend(
                mood=mood,
                count=data["count"],
                percentage=(data["count"] / total_memories * 100) if total_memories > 0 else 0,
                dates=data["dates"]
            )
            for mood, data in mood_data.items()
        ]
        
        # Memories per day
        memories_per_day = {}
        for memory in memories:
            day_key = memory.date.strftime("%Y-%m-%d")
            memories_per_day[day_key] = memories_per_day.get(day_key, 0) + 1
        
        return MemoryStats(
            total_memories=total_memories,
            total_words=total_words,
            average_words_per_memory=avg_words,
            most_common_tags=most_common_tags,
            mood_distribution=mood_distribution,
            memories_per_day=memories_per_day
        )


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_memory(
        self,
        text: str,
        mood: Optional[str] = None,
        tags: Optional[List[str]] = None,
        media_urls: Optional[List[str]] = None,
        location: Optional[Dict[str, Any]] = None
    ) -> MemoryType:
        """Create a new memory"""
        from services.ai_service import ai_service
        
        # Generate AI response
        ai_response = await ai_service.generate_response(text, {})
        
        # Create memory
        memory = Memory(
            text=text,
            date=datetime.now(),
            mood=mood,
            detected_mood=ai_response.get("mood") or mood,
            tags=tags or [],
            keywords=ai_response.get("keywords", []),
            ai_response=ai_response.get("response", ""),
            ai_source=ai_response.get("source", ""),
            media_urls=media_urls or [],
            location=location
        )
        
        await memory.insert()
        return MemoryType.from_db(memory)
    
    @strawberry.mutation
    async def update_memory(
        self,
        memory_id: str,
        text: Optional[str] = None,
        mood: Optional[str] = None,
        tags: Optional[List[str]] = None,
        media_urls: Optional[List[str]] = None
    ) -> Optional[MemoryType]:
        """Update an existing memory"""
        memory = await Memory.get(memory_id)
        if not memory:
            return None
        
        if text:
            memory.text = text
        if mood:
            memory.mood = mood
        if tags is not None:
            memory.tags = tags
        if media_urls is not None:
            memory.media_urls = media_urls
        
        await memory.save()
        return MemoryType.from_db(memory)
    
    @strawberry.mutation
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory"""
        memory = await Memory.get(memory_id)
        if not memory:
            return False
        
        await memory.delete()
        return True


# Create GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation)

# Create GraphQL router
def create_graphql_router():
    from strawberry.fastapi import GraphQLRouter
    return GraphQLRouter(schema)
