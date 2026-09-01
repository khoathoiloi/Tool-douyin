from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class NormalizedSearchResult(BaseModel):
    platform: str = "douyin"
    video_id: str
    url: str
    author: str = ""
    title: str = ""
    description: str = ""
    hashtags: List[str] = Field(default_factory=list)
    cover_url: str = ""
    publish_time: str = ""
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    search_query: str = ""
    retrieved_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class DouyinSearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> List[NormalizedSearchResult]:
        """Search Douyin for videos matching the query."""
        pass

    @abstractmethod
    async def get_video(self, url: str) -> Optional[NormalizedSearchResult]:
        """Get normalized metadata for a specific Douyin video URL."""
        pass
