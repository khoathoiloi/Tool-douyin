from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, model_validator

class StandardizedVideoResult(BaseModel):
    """
    Standardized schema for all video search results returned by SearchProvider implementations.
    """
    video_id: str
    title: str = ""
    description: str = ""
    hashtags: List[str] = Field(default_factory=list)
    url: str = ""
    thumbnail: str = ""
    cover_url: str = ""
    author: str = ""
    likes: int = 0
    like_count: int = 0
    comments: int = 0
    comment_count: int = 0
    shares: int = 0
    share_count: int = 0
    duration: int = 30
    publish_time: str = ""
    query: str = ""
    search_query: str = ""
    score: int = 85
    match_tier: str = "High Match"
    platform: str = "douyin"
    video_no_watermark_url: Optional[str] = ""

    @model_validator(mode="after")
    def sync_aliases(self) -> "StandardizedVideoResult":
        # Cover / Thumbnail sync
        if not self.thumbnail and self.cover_url:
            self.thumbnail = self.cover_url
        elif not self.cover_url and self.thumbnail:
            self.cover_url = self.thumbnail

        # Description / Title sync
        if not self.description and self.title:
            self.description = self.title
        elif not self.title and self.description:
            self.title = self.description

        # Likes sync
        if not self.likes and self.like_count:
            self.likes = self.like_count
        elif not self.like_count and self.likes:
            self.like_count = self.likes

        # Comments sync
        if not self.comments and self.comment_count:
            self.comments = self.comment_count
        elif not self.comment_count and self.comments:
            self.comment_count = self.comments

        # Shares sync
        if not self.shares and self.share_count:
            self.shares = self.share_count
        elif not self.share_count and self.shares:
            self.share_count = self.shares

        # Query sync
        if not self.query and self.search_query:
            self.query = self.search_query
        elif not self.search_query and self.query:
            self.search_query = self.query

        return self

# Backward compatibility alias
NormalizedSearchResult = StandardizedVideoResult

class SearchProvider(ABC):
    """
    Abstract Search Provider interface for multi-platform content search (Douyin, TikTok, etc.)
    """
    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        sort_type: int = 0,
        publish_time: int = 0
    ) -> List[StandardizedVideoResult]:
        """Search videos matching the query with pagination and filter support."""
        pass

    @abstractmethod
    async def get_video(self, url: str) -> Optional[StandardizedVideoResult]:
        """Fetch normalized metadata for a specific video URL."""
        pass

# Backward compatibility alias
DouyinSearchProvider = SearchProvider
