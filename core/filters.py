"""
Core Module: Douyin Video Smart Filter & Sorter
Filters videos by engagement metrics, duration, publish timeframe, and keyword blacklists.
"""

import time
from typing import List, Dict, Any

class DouyinFilter:
    """
    Applies custom criteria to filter and sort Douyin video lists.
    """

    @staticmethod
    def apply_filters(
        videos: List[Dict[str, Any]],
        min_likes: int = 0,
        min_comments: int = 0,
        min_shares: int = 0,
        date_range: str = "all", # "all", "24h", "7d", "30d", "90d"
        duration_type: str = "all", # "all", "short", "medium", "long"
        blacklist_keywords: List[str] = None,
        sort_by: str = "likes_desc" # "likes_desc", "comments_desc", "newest", "shares_desc"
    ) -> List[Dict[str, Any]]:
        if not videos:
            return []

        now_ts = int(time.time())
        blacklist = [kw.strip().lower() for kw in (blacklist_keywords or []) if kw.strip()]
        filtered = []

        for v in videos:
            # 1. Metrics filter
            if v.get("digg_count", 0) < min_likes:
                continue
            if v.get("comment_count", 0) < min_comments:
                continue
            if v.get("share_count", 0) < min_shares:
                continue

            # 2. Duration filter
            dur = v.get("duration", 0)
            if duration_type == "short" and dur >= 60:
                continue
            elif duration_type == "medium" and (dur < 60 or dur > 180):
                continue
            elif duration_type == "long" and dur <= 180:
                continue

            # 3. Date range filter
            create_ts = v.get("create_timestamp", 0)
            if create_ts > 0:
                age_sec = now_ts - create_ts
                if date_range == "24h" and age_sec > 86400:
                    continue
                elif date_range == "7d" and age_sec > 7 * 86400:
                    continue
                elif date_range == "30d" and age_sec > 30 * 86400:
                    continue
                elif date_range == "90d" and age_sec > 90 * 86400:
                    continue

            # 4. Blacklist filter
            title_lower = v.get("title", "").lower()
            if any(bad_kw in title_lower for bad_kw in blacklist):
                continue

            filtered.append(v)

        # 5. Sorting
        if sort_by == "likes_desc":
            filtered.sort(key=lambda x: x.get("digg_count", 0), reverse=True)
        elif sort_by == "comments_desc":
            filtered.sort(key=lambda x: x.get("comment_count", 0), reverse=True)
        elif sort_by == "shares_desc":
            filtered.sort(key=lambda x: x.get("share_count", 0), reverse=True)
        elif sort_by == "newest":
            filtered.sort(key=lambda x: x.get("create_timestamp", 0), reverse=True)

        return filtered
