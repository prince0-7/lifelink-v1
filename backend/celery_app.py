"""
Celery configuration for background task processing
"""
from celery import Celery
from celery.schedules import crontab
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Celery app
celery_app = Celery(
    'lifelink',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    include=['tasks.ai_tasks', 'tasks.memory_tasks', 'tasks.analytics_tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    result_expires=3600,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'generate-daily-insights': {
        'task': 'tasks.ai_tasks.generate_daily_insights',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    'analyze-mood-trends': {
        'task': 'tasks.analytics_tasks.analyze_mood_trends',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
    'cleanup-old-sessions': {
        'task': 'tasks.memory_tasks.cleanup_old_sessions',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
    },
    'update-memory-embeddings': {
        'task': 'tasks.ai_tasks.update_memory_embeddings',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
}

if __name__ == '__main__':
    celery_app.start()
