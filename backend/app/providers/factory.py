from ..core.config import settings
from .base import DouyinSearchProvider
from .mock_provider import MockDouyinSearchProvider
from .douyin_live_provider import LiveDouyinSearchProvider

def get_search_provider() -> DouyinSearchProvider:
    if settings.DOUYIN_SEARCH_PROVIDER.lower() == "mock":
        return MockDouyinSearchProvider()
    return LiveDouyinSearchProvider(cookie=settings.DOUYIN_COOKIE)
