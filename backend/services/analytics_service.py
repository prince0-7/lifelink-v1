from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import numpy as np
from models import Memory, MemoryCluster, AnalyticsEvent, MoodType
import logging

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for generating analytics and insights from memories"""
    
    async def get_mood_trends(self, memories: List[Memory], period: str = "month") -> Dict[str, Any]:
        """Analyze mood trends over time"""
        if not memories:
            return {"periods": [], "moods": {}}
        
        # Sort memories by date
        sorted_memories = sorted(memories, key=lambda m: m.created_at)
        
        # Determine time buckets based on period
        if period == "week":
            bucket_days = 1
        elif period == "month":
            bucket_days = 7
        elif period == "year":
            bucket_days = 30
        else:
            bucket_days = 7
        
        # Group memories by time buckets
        buckets = defaultdict(lambda: defaultdict(int))
        mood_counts = defaultdict(int)
        
        for memory in sorted_memories:
            # Calculate bucket
            bucket_date = memory.created_at.date()
            if bucket_days > 1:
                days_since_epoch = (bucket_date - datetime(2020, 1, 1).date()).days
                bucket_key = days_since_epoch // bucket_days
                bucket_date = datetime(2020, 1, 1).date() + timedelta(days=bucket_key * bucket_days)
            
            mood = memory.mood or "Neutral"
            buckets[bucket_date.isoformat()][mood] += 1
            mood_counts[mood] += 1
        
        # Format data for chart
        periods = sorted(buckets.keys())
        mood_data = {}
        
        for mood in ["Happy", "Sad", "Angry", "Calm", "Neutral"]:
            mood_data[mood] = []
            for period_key in periods:
                mood_data[mood].append(buckets[period_key].get(mood, 0))
        
        return {
            "periods": periods,
            "moods": mood_data,
            "total_counts": dict(mood_counts),
            "dominant_mood": max(mood_counts, key=mood_counts.get) if mood_counts else "Neutral"
        }
    
    async def get_journaling_consistency(self, memories: List[Memory], days: int = 30) -> Dict[str, Any]:
        """Analyze journaling consistency over the specified period"""
        if not memories:
            return {
                "streak": 0,
                "total_days": 0,
                "consistency_score": 0,
                "gaps": []
            }
        
        # Get memories from the last N days
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_memories = [m for m in memories if m.created_at >= cutoff_date]
        
        if not recent_memories:
            return {
                "streak": 0,
                "total_days": 0,
                "consistency_score": 0,
                "gaps": []
            }
        
        # Group by date
        dates_with_memories = set()
        for memory in recent_memories:
            dates_with_memories.add(memory.created_at.date())
        
        # Calculate current streak
        current_streak = 0
        date = datetime.utcnow().date()
        while date in dates_with_memories:
            current_streak += 1
            date -= timedelta(days=1)
        
        # Calculate longest streak in period
        longest_streak = 0
        temp_streak = 0
        for i in range(days):
            check_date = (datetime.utcnow().date() - timedelta(days=i))
            if check_date in dates_with_memories:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 0
        
        # Find gaps
        gaps = []
        last_date = None
        sorted_dates = sorted(dates_with_memories, reverse=True)
        
        for date in sorted_dates:
            if last_date and (last_date - date).days > 1:
                gaps.append({
                    "start": date.isoformat(),
                    "end": last_date.isoformat(),
                    "days": (last_date - date).days - 1
                })
            last_date = date
        
        # Calculate consistency score (percentage of days with entries)
        consistency_score = (len(dates_with_memories) / days) * 100
        
        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "total_days": len(dates_with_memories),
            "consistency_score": round(consistency_score, 1),
            "gaps": gaps[:5],  # Top 5 gaps
            "avg_memories_per_day": round(len(recent_memories) / max(len(dates_with_memories), 1), 1)
        }
    
    async def get_peak_times(self, memories: List[Memory]) -> Dict[str, Any]:
        """Analyze when users are most active in creating memories"""
        if not memories:
            return {
                "by_hour": {},
                "by_day": {},
                "peak_hour": None,
                "peak_day": None
            }
        
        hour_counts = defaultdict(int)
        day_counts = defaultdict(int)
        
        for memory in memories:
            hour = memory.created_at.hour
            day = memory.created_at.strftime("%A")
            
            hour_counts[hour] += 1
            day_counts[day] += 1
        
        # Find peak times
        peak_hour = max(hour_counts, key=hour_counts.get) if hour_counts else None
        peak_day = max(day_counts, key=day_counts.get) if day_counts else None
        
        # Format hour data
        hour_data = {str(h): hour_counts.get(h, 0) for h in range(24)}
        
        # Ensure all days are represented
        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_data = {day: day_counts.get(day, 0) for day in days_order}
        
        return {
            "by_hour": hour_data,
            "by_day": day_data,
            "peak_hour": peak_hour,
            "peak_day": peak_day,
            "peak_hour_label": f"{peak_hour}:00-{peak_hour+1}:00" if peak_hour is not None else None
        }
    
    async def get_keyword_trends(self, memories: List[Memory], limit: int = 20) -> Dict[str, Any]:
        """Analyze most common keywords and topics"""
        if not memories:
            return {"keywords": [], "topics": []}
        
        # Collect all keywords
        keyword_counts = Counter()
        for memory in memories:
            if memory.keywords:
                keyword_counts.update(memory.keywords)
        
        # Get top keywords
        top_keywords = [
            {"word": word, "count": count}
            for word, count in keyword_counts.most_common(limit)
        ]
        
        # Extract topics from tags
        tag_counts = Counter()
        for memory in memories:
            if memory.tags:
                tag_counts.update(memory.tags)
        
        top_topics = [
            {"topic": tag, "count": count}
            for tag, count in tag_counts.most_common(10)
        ]
        
        return {
            "keywords": top_keywords,
            "topics": top_topics,
            "total_unique_keywords": len(keyword_counts),
            "total_unique_topics": len(tag_counts)
        }
    
    async def get_memory_length_analysis(self, memories: List[Memory]) -> Dict[str, Any]:
        """Analyze memory lengths and writing patterns"""
        if not memories:
            return {
                "avg_length": 0,
                "shortest": 0,
                "longest": 0,
                "distribution": {}
            }
        
        lengths = [len(memory.text) for memory in memories]
        
        # Calculate statistics
        avg_length = sum(lengths) / len(lengths)
        shortest = min(lengths)
        longest = max(lengths)
        
        # Create distribution buckets
        buckets = {
            "very_short": 0,  # < 50 chars
            "short": 0,       # 50-150 chars
            "medium": 0,      # 150-300 chars
            "long": 0,        # 300-600 chars
            "very_long": 0    # > 600 chars
        }
        
        for length in lengths:
            if length < 50:
                buckets["very_short"] += 1
            elif length < 150:
                buckets["short"] += 1
            elif length < 300:
                buckets["medium"] += 1
            elif length < 600:
                buckets["long"] += 1
            else:
                buckets["very_long"] += 1
        
        return {
            "avg_length": round(avg_length, 0),
            "shortest": shortest,
            "longest": longest,
            "distribution": buckets,
            "median_length": sorted(lengths)[len(lengths) // 2] if lengths else 0
        }
    
    async def get_emotional_journey(self, memories: List[Memory], period_days: int = 30) -> Dict[str, Any]:
        """Analyze emotional journey over time"""
        if not memories:
            return {
                "timeline": [],
                "mood_shifts": 0,
                "emotional_volatility": 0
            }
        
        # Sort memories by date
        sorted_memories = sorted(memories, key=lambda m: m.created_at)
        
        # Create timeline
        timeline = []
        mood_values = {
            "Happy": 1.0,
            "Calm": 0.5,
            "Neutral": 0.0,
            "Sad": -0.5,
            "Angry": -1.0
        }
        
        prev_mood = None
        mood_shifts = 0
        mood_scores = []
        
        for memory in sorted_memories:
            mood = memory.mood or "Neutral"
            score = mood_values.get(mood, 0.0)
            mood_scores.append(score)
            
            timeline.append({
                "date": memory.created_at.isoformat(),
                "mood": mood,
                "score": score,
                "text_preview": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text
            })
            
            if prev_mood and prev_mood != mood:
                mood_shifts += 1
            prev_mood = mood
        
        # Calculate emotional volatility (standard deviation of mood scores)
        emotional_volatility = np.std(mood_scores) if mood_scores else 0
        
        # Get recent emotional trend
        recent_memories = [m for m in sorted_memories if m.created_at >= datetime.utcnow() - timedelta(days=period_days)]
        recent_scores = [mood_values.get(m.mood or "Neutral", 0.0) for m in recent_memories]
        
        trend = "stable"
        if len(recent_scores) >= 2:
            recent_avg = sum(recent_scores[-5:]) / len(recent_scores[-5:])
            older_avg = sum(recent_scores[:5]) / len(recent_scores[:5])
            if recent_avg > older_avg + 0.3:
                trend = "improving"
            elif recent_avg < older_avg - 0.3:
                trend = "declining"
        
        return {
            "timeline": timeline[-50:],  # Last 50 entries
            "mood_shifts": mood_shifts,
            "emotional_volatility": round(emotional_volatility, 2),
            "average_mood_score": round(sum(mood_scores) / len(mood_scores), 2) if mood_scores else 0,
            "recent_trend": trend
        }
    
    async def get_insights_summary(self, user_id: str, memories: List[Memory], clusters: List[MemoryCluster]) -> Dict[str, Any]:
        """Generate a comprehensive insights summary"""
        # Get all analytics
        mood_trends = await self.get_mood_trends(memories, "month")
        consistency = await self.get_journaling_consistency(memories, 30)
        peak_times = await self.get_peak_times(memories)
        keywords = await self.get_keyword_trends(memories)
        length_analysis = await self.get_memory_length_analysis(memories)
        emotional_journey = await self.get_emotional_journey(memories)
        
        # Generate insights
        insights = []
        
        # Mood insight
        if mood_trends["dominant_mood"]:
            insights.append(f"Your dominant mood has been {mood_trends['dominant_mood']}.")
        
        # Consistency insight
        if consistency["current_streak"] > 7:
            insights.append(f"Great job! You're on a {consistency['current_streak']}-day streak!")
        elif consistency["current_streak"] == 0:
            insights.append("Time to get back to journaling! Your streak has been broken.")
        
        # Peak time insight
        if peak_times["peak_hour"] is not None:
            insights.append(f"You're most active at {peak_times['peak_hour_label']}.")
        
        # Length insight
        if length_analysis["avg_length"] > 300:
            insights.append("You write detailed, thoughtful memories.")
        elif length_analysis["avg_length"] < 100:
            insights.append("Your memories are concise and to the point.")
        
        # Emotional journey insight
        if emotional_journey["recent_trend"] == "improving":
            insights.append("Your emotional well-being seems to be improving recently!")
        elif emotional_journey["recent_trend"] == "declining":
            insights.append("You might be going through a challenging period. Remember to take care of yourself.")
        
        # Cluster insight
        if clusters:
            top_themes = [c.theme for c in clusters[:3]]
            insights.append(f"Your main life themes are: {', '.join(top_themes)}.")
        
        return {
            "summary": {
                "total_memories": len(memories),
                "total_clusters": len(clusters),
                "consistency_score": consistency["consistency_score"],
                "dominant_mood": mood_trends["dominant_mood"],
                "avg_memory_length": length_analysis["avg_length"],
                "emotional_volatility": emotional_journey["emotional_volatility"]
            },
            "insights": insights,
            "mood_trends": mood_trends,
            "consistency": consistency,
            "peak_times": peak_times,
            "keywords": keywords,
            "length_analysis": length_analysis,
            "emotional_journey": emotional_journey
        }
    
    async def track_event(self, user_id: str, event_type: str, event_data: Dict[str, Any]):
        """Track analytics events"""
        try:
            event = AnalyticsEvent(
                user_id=user_id,
                event_type=event_type,
                event_data=event_data
            )
            await event.save()
        except Exception as e:
            logger.error(f"Error tracking event: {e}")
