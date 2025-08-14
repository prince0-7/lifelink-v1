from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
import numpy as np
from models import (
    Memory, MemoryRelationship, MemoryCluster, 
    GraphRequest, GraphResponse, User
)
from services.relationship_service import RelationshipService
from services.auth_service import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
relationship_service = RelationshipService()

@router.get("/memories/graph", response_model=GraphResponse)
async def get_memory_graph(
    time_range: str = Query("all", description="Time range: all, year, month, week"),
    min_strength: float = Query(0.3, description="Minimum relationship strength"),
    include_clusters: bool = Query(True, description="Include cluster information"),
    current_user: User = Depends(get_current_user)
):
    """Get memory graph data with relationships"""
    try:
        # Get memories based on time range
        query = Memory.user_id == current_user.id
        
        if time_range != "all":
            now = datetime.utcnow()
            if time_range == "week":
                start_date = now - timedelta(days=7)
            elif time_range == "month":
                start_date = now - timedelta(days=30)
            elif time_range == "year":
                start_date = now - timedelta(days=365)
            else:
                start_date = now - timedelta(days=30)  # Default to month
            
            query = query & (Memory.created_at >= start_date)
        
        memories = await Memory.find(query).to_list()
        
        if not memories:
            return GraphResponse(
                nodes=[],
                edges=[],
                clusters=[],
                stats={"total_memories": 0, "total_connections": 0}
            )
        
        # Get existing relationships
        relationships = await MemoryRelationship.find(
            MemoryRelationship.user_id == current_user.id,
            MemoryRelationship.strength >= min_strength
        ).to_list()
        
        # Create a set of memory IDs that have relationships
        memory_ids_with_relationships = set()
        for rel in relationships:
            memory_ids_with_relationships.add(rel.source_memory_id)
            memory_ids_with_relationships.add(rel.target_memory_id)
        
        # Filter memories to only include those in the relationships
        if relationships:
            memories = [m for m in memories if str(m.id) in memory_ids_with_relationships]
        
        # Get clusters if requested
        clusters_data = []
        if include_clusters:
            clusters = await MemoryCluster.find(
                MemoryCluster.user_id == current_user.id
            ).to_list()
            clusters_data = [
                {
                    "id": str(cluster.id),
                    "name": cluster.cluster_name,
                    "theme": cluster.theme,
                    "memory_ids": cluster.memory_ids,
                    "keywords": cluster.keywords,
                    "summary": cluster.summary
                }
                for cluster in clusters
            ]
        
        # Build graph data
        nodes = [
            {
                "id": str(m.id),
                "text": m.text[:100] + "..." if len(m.text) > 100 else m.text,
                "full_text": m.text,
                "mood": m.mood,
                "created_at": m.created_at.isoformat(),
                "tags": m.tags,
                "keywords": m.keywords
            }
            for m in memories
        ]
        
        edges = [
            {
                "source": rel.source_memory_id,
                "target": rel.target_memory_id,
                "strength": rel.strength,
                "type": rel.relationship_type,
                "reasons": rel.reasons
            }
            for rel in relationships
        ]
        
        # Calculate stats
        avg_strength = np.mean([rel.strength for rel in relationships]) if relationships else 0
        
        graph_data = GraphResponse(
            nodes=nodes,
            edges=edges,
            clusters=clusters_data if include_clusters else None,
            stats={
                "total_memories": len(memories),
                "total_connections": len(relationships),
                "avg_connection_strength": round(avg_strength, 2),
                "time_range": time_range,
                "clusters_count": len(clusters_data) if include_clusters else 0
            }
        )
        
        return graph_data
        
    except Exception as e:
        logger.error(f"Error getting memory graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/memories/analyze-relationships")
async def analyze_relationships(
    current_user: User = Depends(get_current_user),
    force_refresh: bool = Query(False, description="Force recalculation of relationships")
):
    """Analyze and create relationships between memories"""
    try:
        # Check if relationships already exist and force_refresh is False
        if not force_refresh:
            existing_count = await MemoryRelationship.find(
                MemoryRelationship.user_id == current_user.id
            ).count()
            if existing_count > 0:
                return {
                    "message": "Relationships already analyzed",
                    "count": existing_count,
                    "hint": "Use force_refresh=true to recalculate"
                }
        
        # Get all memories for the user
        memories = await Memory.find(Memory.user_id == current_user.id).to_list()
        
        if len(memories) < 2:
            return {
                "message": "Not enough memories to analyze relationships",
                "count": 0
            }
        
        # Delete existing relationships if force_refresh
        if force_refresh:
            await MemoryRelationship.find(
                MemoryRelationship.user_id == current_user.id
            ).delete()
        
        # Find relationships
        relationships = await relationship_service.find_relationships(
            memories, 
            current_user.id
        )
        
        return {
            "message": "Relationships analyzed successfully",
            "count": len(relationships),
            "strong_connections": len([r for r in relationships if r['strength'] > 0.7])
        }
        
    except Exception as e:
        logger.error(f"Error analyzing relationships: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/memories/detect-clusters")
async def detect_clusters(
    current_user: User = Depends(get_current_user)
):
    """Detect memory clusters based on relationships"""
    try:
        # First ensure relationships exist
        relationship_count = await MemoryRelationship.find(
            MemoryRelationship.user_id == current_user.id
        ).count()
        
        if relationship_count == 0:
            return {
                "message": "No relationships found. Please analyze relationships first.",
                "clusters": []
            }
        
        # Delete existing clusters
        await MemoryCluster.find(
            MemoryCluster.user_id == current_user.id
        ).delete()
        
        # Detect new clusters
        clusters = await relationship_service.detect_clusters(current_user.id)
        
        return {
            "message": "Clusters detected successfully",
            "count": len(clusters),
            "clusters": [
                {
                    "id": str(cluster.id),
                    "name": cluster.cluster_name,
                    "theme": cluster.theme,
                    "size": len(cluster.memory_ids),
                    "keywords": cluster.keywords[:5]
                }
                for cluster in clusters
            ]
        }
        
    except Exception as e:
        logger.error(f"Error detecting clusters: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/memories/{memory_id}/relate/{target_id}")
async def manually_relate_memories(
    memory_id: str,
    target_id: str,
    relationship_type: str = Query("manual", description="Type of relationship"),
    strength: float = Query(0.8, description="Relationship strength (0-1)"),
    current_user: User = Depends(get_current_user)
):
    """Manually create a relationship between two memories"""
    try:
        # Verify both memories exist and belong to user
        source = await Memory.find_one(
            Memory.id == memory_id,
            Memory.user_id == current_user.id
        )
        target = await Memory.find_one(
            Memory.id == target_id,
            Memory.user_id == current_user.id
        )
        
        if not source or not target:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        # Create relationship
        relationship = MemoryRelationship(
            source_memory_id=memory_id,
            target_memory_id=target_id,
            user_id=current_user.id,
            relationship_type=relationship_type,
            strength=min(max(strength, 0.0), 1.0),  # Clamp between 0 and 1
            reasons=["manual_connection"]
        )
        
        await relationship.save()
        
        return {
            "message": "Relationship created successfully",
            "relationship": {
                "source": memory_id,
                "target": target_id,
                "type": relationship_type,
                "strength": relationship.strength
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating manual relationship: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memories/{memory_id}/path/{target_id}")
async def find_memory_path(
    memory_id: str,
    target_id: str,
    current_user: User = Depends(get_current_user)
):
    """Find the path between two memories through relationships"""
    try:
        path = await relationship_service.get_memory_path(
            memory_id, 
            target_id, 
            current_user.id
        )
        
        if not path:
            return {
                "message": "No path found between these memories",
                "path": []
            }
        
        # Get memory details for the path
        path_memories = []
        for memory_id in path:
            memory = await Memory.find_one(Memory.id == memory_id)
            if memory:
                path_memories.append({
                    "id": str(memory.id),
                    "text": memory.text[:50] + "...",
                    "mood": memory.mood,
                    "created_at": memory.created_at.isoformat()
                })
        
        return {
            "message": f"Path found with {len(path)} memories",
            "path": path_memories,
            "distance": len(path) - 1
        }
        
    except Exception as e:
        logger.error(f"Error finding memory path: {e}")
        raise HTTPException(status_code=500, detail=str(e))
