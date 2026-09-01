import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Douyin Content Finder"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Database
    DATABASE_URL: str = "sqlite:///./app.db"
    
    # Storage
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    UPLOAD_DIR: str = os.path.join(BASE_DIR, "uploads")
    MAX_VIDEO_SIZE_MB: int = 500
    ALLOWED_EXTENSIONS: List[str] = ["mp4", "mov", "avi", "mkv", "webm"]
    
    # AI Providers
    AI_PROVIDER: str = "gemini" # gemini, openai, offline
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    DOUYIN_COOKIE: str = ""
    DOUYIN_SEARCH_PROVIDER: str = "live" # live, mock
    
    # Ranking Weights (Sum = 1.0)
    WEIGHT_SEMANTIC: float = 0.35
    WEIGHT_VISUAL: float = 0.25
    WEIGHT_KEYWORD: float = 0.15
    WEIGHT_HASHTAG: float = 0.10
    WEIGHT_CONTENT_TYPE: float = 0.10
    WEIGHT_POPULARITY: float = 0.05
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
