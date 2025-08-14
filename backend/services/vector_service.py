"""
Vector database service for semantic search
"""
import pinecone
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import logging
import os
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class VectorService:
    """Service for managing vector embeddings and semantic search"""
    
    def __init__(self):
        self.model = None
        self.index = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._initialize()
    
    def _initialize(self):
        """Initialize Pinecone and embedding model"""
        try:
            # Initialize Pinecone
            pinecone.init(
                api_key=os.getenv("PINECONE_API_KEY"),
                environment=os.getenv("PINECONE_ENV", "us-east-1-aws")
            )
            
            # Create or get index
            index_name = os.getenv("PINECONE_INDEX", "lifelink-memories")
            
            if index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    name=index_name,
                    dimension=384,  # Dimension for all-MiniLM-L6-v2
                    metric="cosine",
                    metadata_config={
                        "indexed": ["user_id", "date", "mood", "tags"]
                    }
                )
            
            self.index = pinecone.Index(index_name)
            
            # Initialize embedding model
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            
            logger.info("Vector service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector service: {e}")
    
    async def generate_embeddings(self, text: str) -> List[float]:
        """Generate embeddings for text"""
        try:
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                self.executor,
                self.model.encode,
                text
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return []
    
    async def index_memory(self, memory: Any) -> bool:
        """Index a memory in the vector database"""
        try:
            # Generate embeddings if not present
            if not memory.embeddings:
                memory.embeddings = await self.generate_embeddings(memory.text)
            
            # Prepare metadata
            metadata = {
                "user_id": str(memory.user_id) if hasattr(memory, 'user_id') else "",
                "text": memory.text[:1000],  # Truncate for metadata
                "date": memory.date.isoformat(),
                "mood": memory.mood or "",
                "detected_mood": memory.detected_mood or "",
                "tags": ",".join(memory.tags or []),
                "has_media": bool(memory.media_urls),
                "created_at": datetime.now().isoformat()
            }
            
            # Upsert to Pinecone
            self.index.upsert(
                vectors=[(str(memory.id), memory.embeddings, metadata)]
            )
            
            logger.info(f"Indexed memory {memory.id} in vector database")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing memory: {e}")
            return False
    
    async def search_similar(
        self,
        query_embeddings: List[float],
        user_id: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar memories"""
        try:
            # Build filter
            query_filter = {}
            if user_id:
                query_filter["user_id"] = user_id
            if filters:
                query_filter.update(filters)
            
            # Search
            results = self.index.query(
                vector=query_embeddings,
                top_k=limit,
                include_metadata=True,
                filter=query_filter if query_filter else None
            )
            
            # Filter by threshold and format results
            similar_memories = []
            for match in results.matches:
                if match.score >= threshold:
                    similar_memories.append({
                        "id": match.id,
                        "score": float(match.score),
                        "text": match.metadata.get("text", ""),
                        "date": match.metadata.get("date", ""),
                        "mood": match.metadata.get("mood", ""),
                        "tags": match.metadata.get("tags", "").split(",") if match.metadata.get("tags") else []
                    })
            
            return similar_memories
            
        except Exception as e:
            logger.error(f"Error searching similar memories: {e}")
            return []
    
    async def semantic_search(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Perform semantic search with text query"""
        try:
            # Generate query embeddings
            query_embeddings = await self.generate_embeddings(query)
            
            # Search
            return await self.search_similar(
                query_embeddings,
                user_id=user_id,
                limit=limit,
                filters=filters
            )
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    async def find_related_memories(
        self,
        memory_id: str,
        user_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find memories related to a specific memory"""
        try:
            # Fetch the memory's embeddings from Pinecone
            fetch_result = self.index.fetch([memory_id])
            
            if memory_id not in fetch_result.vectors:
                logger.warning(f"Memory {memory_id} not found in vector database")
                return []
            
            embeddings = fetch_result.vectors[memory_id].values
            
            # Search for similar memories, excluding the source memory
            results = await self.search_similar(
                embeddings,
                user_id=user_id,
                limit=limit + 1  # Get one extra to exclude source
            )
            
            # Filter out the source memory
            return [r for r in results if r["id"] != memory_id][:limit]
            
        except Exception as e:
            logger.error(f"Error finding related memories: {e}")
            return []
    
    async def delete_memory_embedding(self, memory_id: str) -> bool:
        """Delete a memory from the vector database"""
        try:
            self.index.delete(ids=[memory_id])
            logger.info(f"Deleted memory {memory_id} from vector database")
            return True
        except Exception as e:
            logger.error(f"Error deleting memory embedding: {e}")
            return False
    
    async def update_memory_embedding(self, memory: Any) -> bool:
        """Update a memory's embedding"""
        try:
            # Re-index the memory (upsert will update)
            return await self.index_memory(memory)
        except Exception as e:
            logger.error(f"Error updating memory embedding: {e}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector index"""
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vectors": stats.total_vector_count,
                "dimensions": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": stats.namespaces
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {}


# Create global vector service instance
vector_service = VectorService()
