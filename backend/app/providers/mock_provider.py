import time
from typing import List, Optional
from datetime import datetime
from .base import DouyinSearchProvider, NormalizedSearchResult

class MockDouyinSearchProvider(DouyinSearchProvider):
    async def search(self, query: str, limit: int = 20) -> List[NormalizedSearchResult]:
        results = []
        creators = ["舞蹈小甜心", "卡点达人阿强", "流行趋势榜", "爆款创作社", "心动女生"]
        for i in range(limit):
            aweme_id = f"72688998273641219{i:02d}"
            results.append(NormalizedSearchResult(
                platform="douyin",
                video_id=aweme_id,
                url=f"https://www.douyin.com/video/{aweme_id}",
                author=creators[i % len(creators)],
                title=f"【{query}】全网超火爆款视频 #{query} #热点",
                description=f"精选高赞推荐，一定要看到最后 #{query}",
                hashtags=[f"#{query}", "#热门", "#爆款"],
                cover_url="https://p3-pc.douyinpic.com/origin/tos-cn-p-0015/demo.jpeg",
                publish_time=datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
                like_count=(i + 1) * 28500 + 12000,
                comment_count=(i + 1) * 1200 + 450,
                share_count=(i + 1) * 850 + 200,
                search_query=query
            ))
        return results

    async def get_video(self, url: str) -> Optional[NormalizedSearchResult]:
        aweme_id = "7268899827364121914"
        return NormalizedSearchResult(
            platform="douyin",
            video_id=aweme_id,
            url=f"https://www.douyin.com/video/{aweme_id}",
            author="Mock Creator",
            title="Mock Douyin Video Title",
            description="Mock video description",
            hashtags=["#mock"],
            cover_url="",
            publish_time=datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
            like_count=100000,
            search_query="mock"
        )
