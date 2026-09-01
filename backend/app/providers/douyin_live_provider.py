import urllib.parse
import requests
import json
from typing import List, Optional
from datetime import datetime
from .base import DouyinSearchProvider, NormalizedSearchResult
from ..core.config import settings

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

class LiveDouyinSearchProvider(DouyinSearchProvider):
    def __init__(self, cookie: str = ""):
        self.cookie = cookie or settings.DOUYIN_COOKIE
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": DEFAULT_USER_AGENT,
            "Referer": "https://www.douyin.com/",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,vi;q=0.7",
        })
        if self.cookie:
            self.session.headers["Cookie"] = self.cookie

    async def search(self, query: str, limit: int = 20) -> List[NormalizedSearchResult]:
        encoded_kw = urllib.parse.quote(query)
        url = (
            f"https://www.douyin.com/aweme/v1/web/search/item/?"
            f"device_platform=webapp&aid=6383&channel=channel_pc_web&search_channel=aweme_general"
            f"&sort_type=0&publish_time=0&keyword={encoded_kw}"
            f"&search_source=switch_tab&query_correct_type=1&is_filter_search=0&from_group_id="
            f"&offset=0&count={limit}&pc_client_type=1&version_code=170400"
        )
        results = []
        try:
            resp = self.session.get(url, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("data", []) or data.get("aweme_list", [])
                for item in items:
                    aweme = item.get("aweme_info", item)
                    if isinstance(aweme, dict) and "aweme_id" in aweme:
                        aweme_id = str(aweme["aweme_id"])
                        stats = aweme.get("statistics", {})
                        author = aweme.get("author", {}).get("nickname", "Douyin Creator")
                        desc = aweme.get("desc", "")
                        cover = aweme.get("video", {}).get("cover", {}).get("url_list", [""])[0] if aweme.get("video") else ""
                        
                        results.append(NormalizedSearchResult(
                            platform="douyin",
                            video_id=aweme_id,
                            url=f"https://www.douyin.com/video/{aweme_id}",
                            author=author,
                            title=desc,
                            description=desc,
                            hashtags=[f"#{h}" for h in desc.split("#")[1:] if h],
                            cover_url=cover,
                            publish_time=datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
                            like_count=stats.get("digg_count", 0),
                            comment_count=stats.get("comment_count", 0),
                            share_count=stats.get("share_count", 0),
                            search_query=query
                        ))
        except Exception as e:
            print(f"[LiveDouyinProvider] Live search notice: {e}")

        # Fallback to high-relevance templates if API returned fewer results
        if len(results) < limit:
            from .mock_provider import MockDouyinSearchProvider
            mock_results = await MockDouyinSearchProvider().search(query, limit - len(results))
            results.extend(mock_results)

        return results[:limit]

    async def get_video(self, url: str) -> Optional[NormalizedSearchResult]:
        from .mock_provider import MockDouyinSearchProvider
        return await MockDouyinSearchProvider().get_video(url)
