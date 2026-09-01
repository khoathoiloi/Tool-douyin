import time
from typing import List, Optional
from datetime import datetime
from .base import SearchProvider, StandardizedVideoResult

class MockDouyinSearchProvider(SearchProvider):
    async def search(self, query: str, limit: int = 20, offset: int = 0, sort_type: int = 0, publish_time: int = 0) -> List[StandardizedVideoResult]:
        results = []
        creators = ["舞蹈小甜心", "卡点达人阿强", "流行趋势榜", "爆款创作社", "心动女生"]
        for i in range(limit):
            aweme_id = f"72688998273641219{i:02d}"
            results.append(StandardizedVideoResult(
                platform="douyin",
                video_id=aweme_id,
                url=f"https://www.douyin.com/video/{aweme_id}",
                author=creators[i % len(creators)],
                title=f"【{query}】全网超火爆款视频 #{query} #热点",
                cover_url="https://p3-pc.douyinpic.com/origin/tos-cn-p-0015/demo.jpeg",
                thumbnail="https://p3-pc.douyinpic.com/origin/tos-cn-p-0015/demo.jpeg",
                publish_time=datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
                duration=(i * 15 + 20) % 90 + 15,
                likes=(i + 1) * 28500 + 12000,
                comments=(i + 1) * 1200 + 450,
                shares=(i + 1) * 850 + 200,
                query=query,
                score=90 - i * 2,
                match_tier="Very High Match" if i == 0 else "High Match"
            ))
        return results

    async def get_video(self, url: str) -> Optional[StandardizedVideoResult]:
        aweme_id = "7268899827364121914"
        return StandardizedVideoResult(
            platform="douyin",
            video_id=aweme_id,
            url=f"https://www.douyin.com/video/{aweme_id}",
            author="Mock Creator",
            title="Mock Douyin Video Title",
            cover_url="https://p3-pc.douyinpic.com/origin/tos-cn-p-0015/demo.jpeg",
            thumbnail="https://p3-pc.douyinpic.com/origin/tos-cn-p-0015/demo.jpeg",
            publish_time=datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
            likes=100000,
            query="mock"
        )
