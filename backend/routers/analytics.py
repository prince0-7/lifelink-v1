from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta
from models import Memory, MemoryCluster, User
from services.analytics_service import AnalyticsService
from services.auth_service import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
analytics_service = AnalyticsService()

@router.get("/mood-trends")
async def get_mood_trends(
    period: str = Query("month", description="Time period: week, month, year"),
    current_user: User = Depends(get_current_user)
):
    """Get mood trends over time"""
    try:
        memories = await Memory.find(Memory.user_id == current_user.id).to_list()
        trends = await analytics_service.get_mood_trends(memories, period)
        
        # Track analytics view
        await analytics_service.track_event(
            current_user.id, 
            "view_mood_trends", 
            {"period": period}
        )
        
        return trends
    except Exception as e:
        logger.error(f"Error getting mood trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/consistency")
async def get_journaling_consistency(
    days: int = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user)
):
    """Get journaling consistency metrics"""
    try:
        memories = await Memory.find(Memory.user_id == current_user.id).to_list()
        consistency = await analytics_service.get_journaling_consistency(memories, days)
        
        await analytics_service.track_event(
            current_user.id, 
            "view_consistency", 
            {"days": days}
        )
        
        return consistency
    except Exception as e:
        logger.error(f"Error getting consistency data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/peak-times")
async def get_peak_times(
    current_user: User = Depends(get_current_user)
):
    """Get peak activity times"""
    try:
        memories = await Memory.find(Memory.user_id == current_user.id).to_list()
        peak_times = await analytics_service.get_peak_times(memories)
        
        await analytics_service.track_event(
            current_user.id, 
            "view_peak_times", 
            {}
        )
        
        return peak_times
    except Exception as e:
        logger.error(f"Error getting peak times: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/keywords")
async def get_keyword_trends(
    limit: int = Query(20, description="Maximum number of keywords to return"),
    current_user: User = Depends(get_current_user)
):
    """Get trending keywords and topics"""
    try:
        memories = await Memory.find(Memory.user_id == current_user.id).to_list()
        keywords = await analytics_service.get_keyword_trends(memories, limit)
        
        await analytics_service.track_event(
            current_user.id, 
            "view_keywords", 
            {"limit": limit}
        )
        
        return keywords
    except Exception as e:
        logger.error(f"Error getting keyword trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory-length")
async def get_memory_length_analysis(
    current_user: User = Depends(get_current_user)
):
    """Analyze memory lengths and writing patterns"""
    try:
        memories = await Memory.find(Memory.user_id == current_user.id).to_list()
        analysis = await analytics_service.get_memory_length_analysis(memories)
        
        await analytics_service.track_event(
            current_user.id, 
            "view_length_analysis", 
            {}
        )
        
        return analysis
    except Exception as e:
        logger.error(f"Error analyzing memory lengths: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/emotional-journey")
async def get_emotional_journey(
    days: int = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user)
):
    """Get emotional journey analysis"""
    try:
        memories = await Memory.find(Memory.user_id == current_user.id).to_list()
        journey = await analytics_service.get_emotional_journey(memories, days)
        
        await analytics_service.track_event(
            current_user.id, 
            "view_emotional_journey", 
            {"days": days}
        )
        
        return journey
    except Exception as e:
        logger.error(f"Error getting emotional journey: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights-summary")
async def get_insights_summary(
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive insights summary"""
    try:
        memories = await Memory.find(Memory.user_id == current_user.id).to_list()
        clusters = await MemoryCluster.find(MemoryCluster.user_id == current_user.id).to_list()
        
        summary = await analytics_service.get_insights_summary(
            current_user.id,
            memories,
            clusters
        )
        
        await analytics_service.track_event(
            current_user.id, 
            "view_insights_summary", 
            {}
        )
        
        return summary
    except Exception as e:
        logger.error(f"Error getting insights summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/activity-heatmap")
async def get_activity_heatmap(
    year: int = Query(None, description="Year to analyze (default: current year)"),
    current_user: User = Depends(get_current_user)
):
    """Get activity heatmap data for calendar visualization"""
    try:
        if not year:
            year = datetime.utcnow().year
        
        # Get memories for the specified year
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)
        
        memories = await Memory.find(
            Memory.user_id == current_user.id,
            Memory.created_at >= start_date,
            Memory.created_at <= end_date
        ).to_list()
        
        # Create heatmap data
        heatmap_data = {}
        for memory in memories:
            date_key = memory.created_at.date().isoformat()
            if date_key not in heatmap_data:
                heatmap_data[date_key] = {
                    "count": 0,
                    "moods": []
                }
            heatmap_data[date_key]["count"] += 1
            heatmap_data[date_key]["moods"].append(memory.mood)
        
        # Calculate dominant mood for each day
        for date_key in heatmap_data:
            moods = heatmap_data[date_key]["moods"]
            if moods:
                # Get most common mood
                mood_counts = {}
                for mood in moods:
                    mood_counts[mood] = mood_counts.get(mood, 0) + 1
                dominant_mood = max(mood_counts, key=mood_counts.get)
                heatmap_data[date_key]["dominant_mood"] = dominant_mood
        
        await analytics_service.track_event(
            current_user.id, 
            "view_activity_heatmap", 
            {"year": year}
        )
        
        return {
            "year": year,
            "data": heatmap_data,
            "total_days_with_memories": len(heatmap_data),
            "total_memories": len(memories)
        }
        
    except Exception as e:
        logger.error(f"Error getting activity heatmap: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/track-event")
async def track_event(
    event_type: str,
    event_data: dict = {},
    current_user: User = Depends(get_current_user)
):
    """Track custom analytics events"""
    try:
        await analytics_service.track_event(
            current_user.id,
            event_type,
            event_data
        )
        return {"message": "Event tracked successfully"}
    except Exception as e:
        logger.error(f"Error tracking event: {e}")
        raise HTTPException(status_code=500, detail=str(e))
