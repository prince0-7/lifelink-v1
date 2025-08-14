"""
WebSocket Manager for real-time features using Socket.IO
"""
import socketio
from typing import Dict, Set, Optional
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",  # Configure this based on your needs
    logger=True,
    engineio_logger=True
)

# Track connected users
connected_users: Dict[str, Set[str]] = {}  # user_id -> set of session_ids
session_to_user: Dict[str, str] = {}  # session_id -> user_id


class WebSocketManager:
    """Manages WebSocket connections and real-time features"""
    
    def __init__(self):
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup Socket.IO event handlers"""
        
        @sio.event
        async def connect(sid, environ):
            """Handle new connection"""
            logger.info(f"Client connected: {sid}")
            await sio.emit('connected', {'message': 'Welcome to LifeLink!'}, to=sid)
        
        @sio.event
        async def disconnect(sid):
            """Handle disconnection"""
            logger.info(f"Client disconnected: {sid}")
            
            # Remove user tracking
            if sid in session_to_user:
                user_id = session_to_user[sid]
                if user_id in connected_users:
                    connected_users[user_id].discard(sid)
                    if not connected_users[user_id]:
                        del connected_users[user_id]
                del session_to_user[sid]
        
        @sio.event
        async def authenticate(sid, data):
            """Authenticate user"""
            user_id = data.get('user_id')
            if user_id:
                # Track user session
                if user_id not in connected_users:
                    connected_users[user_id] = set()
                connected_users[user_id].add(sid)
                session_to_user[sid] = user_id
                
                await sio.emit('authenticated', {'success': True}, to=sid)
                logger.info(f"User {user_id} authenticated on session {sid}")
        
        @sio.event
        async def typing(sid, data):
            """Handle typing indicator"""
            if sid in session_to_user:
                user_id = session_to_user[sid]
                # Broadcast to other users (implement room logic as needed)
                await sio.emit('user_typing', {
                    'user_id': user_id,
                    'is_typing': data.get('is_typing', False)
                }, skip_sid=sid)
        
        @sio.event
        async def memory_update(sid, data):
            """Handle real-time memory updates"""
            if sid in session_to_user:
                user_id = session_to_user[sid]
                # Broadcast memory update to user's other sessions
                for session_id in connected_users.get(user_id, []):
                    if session_id != sid:
                        await sio.emit('memory_updated', data, to=session_id)
    
    async def emit_ai_processing_status(self, user_id: str, status: str, data: Optional[dict] = None):
        """Emit AI processing status to user"""
        if user_id in connected_users:
            payload = {
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'data': data or {}
            }
            for sid in connected_users[user_id]:
                await sio.emit('ai_processing_status', payload, to=sid)
    
    async def emit_memory_insight(self, user_id: str, insight: dict):
        """Emit new memory insight to user"""
        if user_id in connected_users:
            for sid in connected_users[user_id]:
                await sio.emit('new_memory_insight', insight, to=sid)
    
    async def emit_mood_update(self, user_id: str, mood_data: dict):
        """Emit mood analysis update"""
        if user_id in connected_users:
            for sid in connected_users[user_id]:
                await sio.emit('mood_updated', mood_data, to=sid)
    
    async def broadcast_system_message(self, message: str, message_type: str = 'info'):
        """Broadcast system message to all connected users"""
        await sio.emit('system_message', {
            'message': message,
            'type': message_type,
            'timestamp': datetime.now().isoformat()
        })


# Create global WebSocket manager instance
ws_manager = WebSocketManager()

# Export Socket.IO app for mounting
def create_socketio_app():
    """Create Socket.IO ASGI app"""
    return socketio.ASGIApp(sio, other_asgi_app=None)
