from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "lifelink_db"
    
    # Server
    host: str = "0.0.0.0"  # Bind to all interfaces
    port: int = 8000
    reload: bool = True
    # Note: Access the API at http://localhost:8000 not http://0.0.0.0:8000
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # AI Configuration
    ollama_base_url: str = "http://localhost:11434"
    whisper_model: str = "base"
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # Optional Cloud AI
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Storage
    upload_folder: str = "./uploads"
    max_file_size: int = 10485760  # 10MB
    
    # Vector Database
    chroma_persist_directory: str = "./chroma_db"
    collection_name: str = "lifelink_memories"
    
    # CORS
    frontend_url: str = "http://localhost:5173"
    
    # Redis configuration
    redis_url: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create settings instance
settings = Settings()

# Create necessary directories
Path(settings.upload_folder).mkdir(exist_ok=True)
Path(settings.chroma_persist_directory).mkdir(exist_ok=True)
