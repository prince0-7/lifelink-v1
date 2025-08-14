"""
Analytics-related background tasks
"""
from celery import shared_task
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any
import asyncio
from models import Memory, User, MemoryInsight
import pandas as pd
import numpy as np
from collections import Counter
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json

logger = logging.getLogger(__name__)


@shared_task
def analyze_mood_trends():
    """Analyze mood trends for all users"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def _analyze():
        try:
            # Get all users
            users = await User.find_all().to_list()
            
            for user in users:
                # Get user's memories from the last 30 days
                thirty_days_ago = datetime.now() - timedelta(days=30)
                memories = await Memory.find(
                    Memory.user_id == user.id,
                    Memory.date >= thirty_days_ago
                ).to_list()
                
                if not memories:
                    continue
                
                # Analyze mood trends
                mood_data = analyze_user_mood_trends(memories)
                
                # Create insight
                trend_insight = MemoryInsight(
                    user_id=user.id,
                    insight_type="mood_trend_analysis",
                    content=f"Your mood trend analysis for the past 30 days",
                    metadata={
                        "mood_distribution": mood_data["distribution"],
                        "trend": mood_data["trend"],
                        "dominant_mood": mood_data["dominant_mood"],
                        "volatility": mood_data["volatility"],
                        "recommendations": mood_data["recommendations"]
                    },
                    confidence=0.85,
                    created_at=datetime.now()
                )
                await trend_insight.insert()
                
                logger.info(f"Analyzed mood trends for user {user.id}")
                
        except Exception as e:
            logger.error(f"Error analyzing mood trends: {e}")
    
    loop.run_until_complete(_analyze())


def analyze_user_mood_trends(memories: List[Memory]) -> Dict[str, Any]:
    """Analyze mood trends for a specific user"""
    # Create DataFrame
    df = pd.DataFrame([
        {
            "date": m.date,
            "mood": m.detected_mood or m.mood,
            "sentiment_score": m.sentiment_score or 0.0,
            "day_of_week": m.date.strftime("%A"),
            "hour": m.date.hour
        }
        for m in memories
    ])
    
    # Mood distribution
    mood_counts = df["mood"].value_counts().to_dict()
    total_memories = len(df)
    mood_distribution = {
        mood: {
            "count": count,
            "percentage": (count / total_memories) * 100
        }
        for mood, count in mood_counts.items()
    }
    
    # Dominant mood
    dominant_mood = df["mood"].mode()[0] if not df.empty else "Neutral"
    
    # Mood volatility (how often mood changes)
    mood_changes = 0
    for i in range(1, len(df)):
        if df.iloc[i]["mood"] != df.iloc[i-1]["mood"]:
            mood_changes += 1
    
    volatility = mood_changes / len(df) if len(df) > 1 else 0
    
    # Trend analysis (is mood improving, declining, or stable?)
    if len(df) >= 7:
        # Calculate rolling average of sentiment scores
        df["sentiment_ma"] = df["sentiment_score"].rolling(window=7).mean()
        
        # Check trend in last week vs previous week
        recent_avg = df["sentiment_score"].tail(7).mean()
        previous_avg = df["sentiment_score"].iloc[-14:-7].mean() if len(df) >= 14 else df["sentiment_score"].head(7).mean()
        
        if recent_avg > previous_avg + 0.1:
            trend = "improving"
        elif recent_avg < previous_avg - 0.1:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"
    
    # Time-based patterns
    hourly_moods = df.groupby("hour")["mood"].agg(lambda x: x.mode()[0] if len(x) > 0 else "Neutral").to_dict()
    daily_moods = df.groupby("day_of_week")["mood"].agg(lambda x: x.mode()[0] if len(x) > 0 else "Neutral").to_dict()
    
    # Generate recommendations
    recommendations = generate_mood_recommendations(
        dominant_mood=dominant_mood,
        trend=trend,
        volatility=volatility,
        hourly_patterns=hourly_moods,
        daily_patterns=daily_moods
    )
    
    return {
        "distribution": mood_distribution,
        "dominant_mood": dominant_mood,
        "trend": trend,
        "volatility": volatility,
        "hourly_patterns": hourly_moods,
        "daily_patterns": daily_moods,
        "recommendations": recommendations
    }


def generate_mood_recommendations(
    dominant_mood: str,
    trend: str,
    volatility: float,
    hourly_patterns: Dict[int, str],
    daily_patterns: Dict[str, str]
) -> List[str]:
    """Generate personalized recommendations based on mood analysis"""
    recommendations = []
    
    # Based on dominant mood
    mood_recommendations = {
        "Happy": [
            "Continue engaging in activities that bring you joy",
            "Share your positive experiences with loved ones",
            "Consider documenting what's working well in your life"
        ],
        "Sad": [
            "Consider reaching out to a friend or loved one",
            "Try engaging in gentle physical activity",
            "Practice self-compassion during this difficult time"
        ],
        "Angry": [
            "Try mindfulness or breathing exercises",
            "Consider physical exercise to release tension",
            "Journal about what's triggering these feelings"
        ],
        "Calm": [
            "Maintain your current self-care routines",
            "Use this peaceful time for reflection",
            "Consider trying meditation to deepen this calm"
        ],
        "Neutral": [
            "Try new activities to add variety to your routine",
            "Set small, achievable goals for the day",
            "Connect with others to add more engagement"
        ]
    }
    
    if dominant_mood in mood_recommendations:
        recommendations.extend(mood_recommendations[dominant_mood][:2])
    
    # Based on trend
    if trend == "improving":
        recommendations.append("Your mood is trending upward - keep up the positive momentum!")
    elif trend == "declining":
        recommendations.append("Your mood has been declining - consider what changes might help")
    
    # Based on volatility
    if volatility > 0.7:
        recommendations.append("Your moods are quite variable - consider mood stabilizing activities like regular sleep and exercise")
    elif volatility < 0.3:
        recommendations.append("Your mood is quite stable - this consistency is positive for wellbeing")
    
    # Based on time patterns
    sad_hours = [hour for hour, mood in hourly_patterns.items() if mood == "Sad"]
    if sad_hours:
        recommendations.append(f"You tend to feel down around {sad_hours[0]}:00 - plan uplifting activities for this time")
    
    return recommendations[:5]  # Limit to 5 recommendations


@shared_task
def generate_memory_analytics(user_id: str, period_days: int = 30):
    """Generate comprehensive analytics for a user's memories"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def _generate():
        try:
            # Get memories for the period
            start_date = datetime.now() - timedelta(days=period_days)
            memories = await Memory.find(
                Memory.user_id == user_id,
                Memory.date >= start_date
            ).to_list()
            
            if not memories:
                return
            
            # Generate various analytics
            analytics = {
                "period": f"{period_days} days",
                "total_memories": len(memories),
                "avg_memories_per_day": len(memories) / period_days,
                "mood_analysis": analyze_user_mood_trends(memories),
                "keyword_analysis": analyze_keywords(memories),
                "time_patterns": analyze_time_patterns(memories),
                "growth_insights": generate_growth_insights(memories),
                "visualization_data": prepare_visualization_data(memories)
            }
            
            # Store analytics as insight
            analytics_insight = MemoryInsight(
                user_id=user_id,
                insight_type="comprehensive_analytics",
                content=f"Your {period_days}-day memory analytics",
                metadata=analytics,
                confidence=0.9,
                created_at=datetime.now()
            )
            await analytics_insight.insert()
            
            logger.info(f"Generated analytics for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error generating analytics: {e}")
    
    loop.run_until_complete(_generate())


def analyze_keywords(memories: List[Memory]) -> Dict[str, Any]:
    """Analyze keyword patterns in memories"""
    all_keywords = []
    for memory in memories:
        all_keywords.extend(memory.keywords or [])
    
    keyword_counts = Counter(all_keywords)
    
    # Get top keywords
    top_keywords = keyword_counts.most_common(20)
    
    # Keyword trends over time
    keyword_timeline = {}
    for memory in memories:
        week = memory.date.isocalendar()[1]
        if week not in keyword_timeline:
            keyword_timeline[week] = []
        keyword_timeline[week].extend(memory.keywords or [])
    
    # Most common keywords per week
    weekly_top_keywords = {}
    for week, keywords in keyword_timeline.items():
        if keywords:
            weekly_top_keywords[week] = Counter(keywords).most_common(5)
    
    return {
        "top_keywords": top_keywords,
        "total_unique_keywords": len(set(all_keywords)),
        "keyword_diversity": len(set(all_keywords)) / len(all_keywords) if all_keywords else 0,
        "weekly_trends": weekly_top_keywords
    }


def analyze_time_patterns(memories: List[Memory]) -> Dict[str, Any]:
    """Analyze when memories are created"""
    df = pd.DataFrame([
        {
            "date": m.date,
            "hour": m.date.hour,
            "day_of_week": m.date.weekday(),
            "day_name": m.date.strftime("%A"),
            "mood": m.detected_mood or m.mood
        }
        for m in memories
    ])
    
    # Most active hours
    hourly_counts = df["hour"].value_counts().to_dict()
    
    # Most active days
    daily_counts = df["day_name"].value_counts().to_dict()
    
    # Mood by time of day
    mood_by_hour = df.groupby(["hour", "mood"]).size().to_dict()
    
    # Memory creation patterns
    creation_pattern = "morning" if df[df["hour"] < 12].shape[0] > df[df["hour"] >= 12].shape[0] else "evening"
    
    return {
        "most_active_hours": sorted(hourly_counts.items(), key=lambda x: x[1], reverse=True)[:5],
        "most_active_days": sorted(daily_counts.items(), key=lambda x: x[1], reverse=True),
        "creation_pattern": creation_pattern,
        "mood_by_hour": mood_by_hour,
        "peak_hour": max(hourly_counts.items(), key=lambda x: x[1])[0] if hourly_counts else None
    }


def generate_growth_insights(memories: List[Memory]) -> List[str]:
    """Generate insights about personal growth from memories"""
    insights = []
    
    # Check for increasing positivity
    sentiment_scores = [m.sentiment_score for m in memories if m.sentiment_score is not None]
    if len(sentiment_scores) >= 10:
        recent_sentiment = np.mean(sentiment_scores[-5:])
        older_sentiment = np.mean(sentiment_scores[:5])
        
        if recent_sentiment > older_sentiment + 0.2:
            insights.append("Your recent memories show increasing positivity - you're on an upward trajectory!")
        elif recent_sentiment < older_sentiment - 0.2:
            insights.append("Your recent memories show some challenges - remember that difficult times lead to growth")
    
    # Check for milestone memories
    milestone_count = sum(1 for m in memories if m.is_milestone)
    if milestone_count > 0:
        insights.append(f"You've marked {milestone_count} milestone memories - celebrating achievements is important!")
    
    # Check for consistency
    dates = [m.date.date() for m in memories]
    unique_dates = len(set(dates))
    consistency_ratio = unique_dates / len(dates) if dates else 0
    
    if consistency_ratio > 0.8:
        insights.append("You're consistently journaling - this regular practice supports self-awareness")
    
    # Check for variety in experiences
    unique_keywords = set()
    for m in memories:
        unique_keywords.update(m.keywords or [])
    
    if len(unique_keywords) > 50:
        insights.append("Your memories show rich variety in experiences - you're embracing life's diversity")
    
    return insights


def prepare_visualization_data(memories: List[Memory]) -> Dict[str, Any]:
    """Prepare data for frontend visualizations"""
    # Mood over time
    mood_timeline = [
        {
            "date": m.date.isoformat(),
            "mood": m.detected_mood or m.mood,
            "sentiment": m.sentiment_score or 0
        }
        for m in sorted(memories, key=lambda x: x.date)
    ]
    
    # Mood distribution pie chart
    mood_counts = Counter(m.detected_mood or m.mood for m in memories)
    mood_distribution = [
        {"mood": mood, "count": count}
        for mood, count in mood_counts.items()
    ]
    
    # Word cloud data
    all_keywords = []
    for m in memories:
        all_keywords.extend(m.keywords or [])
    
    word_cloud_data = [
        {"text": word, "value": count}
        for word, count in Counter(all_keywords).most_common(50)
    ]
    
    # Activity heatmap
    heatmap_data = {}
    for m in memories:
        day = m.date.strftime("%Y-%m-%d")
        if day not in heatmap_data:
            heatmap_data[day] = 0
        heatmap_data[day] += 1
    
    return {
        "mood_timeline": mood_timeline,
        "mood_distribution": mood_distribution,
        "word_cloud": word_cloud_data,
        "activity_heatmap": heatmap_data
    }


@shared_task
def cleanup_old_analytics():
    """Clean up old analytics data"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def _cleanup():
        try:
            # Delete analytics insights older than 90 days
            ninety_days_ago = datetime.now() - timedelta(days=90)
            
            old_insights = await MemoryInsight.find(
                MemoryInsight.insight_type.in_(["mood_trend_analysis", "comprehensive_analytics"]),
                MemoryInsight.created_at < ninety_days_ago
            ).to_list()
            
            for insight in old_insights:
                await insight.delete()
            
            logger.info(f"Cleaned up {len(old_insights)} old analytics insights")
            
        except Exception as e:
            logger.error(f"Error cleaning up analytics: {e}")
    
    loop.run_until_complete(_cleanup())
