from typing import List, Dict, Any
from ..providers.base import DouyinSearchProvider, NormalizedSearchResult
from ..pipeline.deduplicator import Deduplicator

class WaterfallSearchStrategy:
    @staticmethod
    async def execute_search(
        queries_by_tier: Dict[str, List[str]],
        provider: DouyinSearchProvider,
        deep_search: bool = False,
        max_candidates: int = 100,
        max_queries: int = 30
    ) -> List[NormalizedSearchResult]:
        """
        4-Phase Waterfall Search Strategy:
        Phase 1: EXACT queries
        Phase 2: HIGH_SIMILARITY queries
        Phase 3: VISUAL + ACTION + SCENE queries
        Phase 4: TREND + BROAD queries
        """
        collected: List[NormalizedSearchResult] = []
        queries_run = 0
        target_candidates = 300 if deep_search else max_candidates
        query_limit = max_queries if deep_search else min(15, max_queries)

        phases = [
            ("Phase 1 - Exact", queries_by_tier.get("exact", [])),
            ("Phase 2 - High Similarity", queries_by_tier.get("high_similarity", [])),
            ("Phase 3 - Visual/Action", queries_by_tier.get("visual", []) + queries_by_tier.get("action", []) + queries_by_tier.get("scene", [])),
            ("Phase 4 - Trend/Broad", queries_by_tier.get("trend", []) + queries_by_tier.get("broad", []))
        ]

        seen_queries = set()

        for phase_name, query_list in phases:
            if len(collected) >= target_candidates or queries_run >= query_limit:
                break

            for q in query_list:
                clean_q = q.strip()
                if not clean_q or clean_q in seen_queries:
                    continue
                seen_queries.add(clean_q)

                if queries_run >= query_limit:
                    break

                try:
                    limit_per_query = 20 if deep_search else 10
                    results = await provider.search(clean_q, limit=limit_per_query)
                    collected.extend(results)
                    queries_run += 1
                except Exception as e:
                    print(f"[SearchStrategy] Error searching '{clean_q}': {e}")

                if len(collected) >= target_candidates:
                    break

        # Convert to dict for deduplication
        cand_dicts = [
            {
                "platform": c.platform,
                "remote_video_id": c.video_id,
                "url": c.url,
                "author": c.author,
                "title": c.title,
                "description": c.description,
                "hashtags": c.hashtags,
                "cover_url": c.cover_url,
                "publish_time": c.publish_time,
                "like_count": c.like_count,
                "comment_count": c.comment_count,
                "share_count": c.share_count,
                "search_query": c.search_query
            } for c in collected
        ]

        unique_cands = Deduplicator.deduplicate(cand_dicts)

        return [
            NormalizedSearchResult(
                platform=u["platform"],
                video_id=u["remote_video_id"],
                url=u["url"],
                author=u["author"],
                title=u["title"],
                description=u["description"],
                hashtags=u["hashtags"],
                cover_url=u["cover_url"],
                publish_time=u["publish_time"],
                like_count=u["like_count"],
                comment_count=u["comment_count"],
                share_count=u["share_count"],
                search_query=u["search_query"]
            ) for u in unique_cands
        ]
