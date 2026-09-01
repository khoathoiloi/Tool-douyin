import uuid
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from .language_detector import LanguageDetector
from .chinese_query_generator import ChineseQueryGenerator
from .search_cache import SearchCache
from ..providers.factory import get_search_provider
from ..pipeline.deduplicator import Deduplicator
from ..ranking.scoring import MultiLayerScoringEngine
from ..ranking.filters import AdvancedResultFilter
from ..core.models import Video, SearchResult
from sqlalchemy.orm import Session

class SmartSearchService:
    """
    End-to-end Smart Douyin Search & Advanced Ranking Coordinator (Phase 5).
    Vietnamese/English/Chinese NLP -> Chinese Queries -> Multi-stage Douyin Search -> Deduplication -> 6-Dimensional Re-ranking -> Advanced Multi-criteria Filter -> Results.
    """

    @classmethod
    async def translate_and_generate(
        cls,
        query: str,
        language: str = "auto",
        mode: str = "normal"
    ) -> Dict[str, Any]:
        """
        Phase 1: Translation & Query Preview (Used for Manual Mode and Preview UI).
        """
        cached = SearchCache.get(query, language, mode)
        if cached and "query_preview" in cached:
            return cached["query_preview"]

        generated = ChineseQueryGenerator.generate(query=query, language=language, mode=mode)
        preview_data = {
            "original_query": query,
            "detected_language": generated.get("language", "vi"),
            "intent": generated.get("intent", "VISUAL_CONTENT_SEARCH"),
            "semantic_entities": generated.get("semantic_entities", {}),
            "chinese_keywords": generated.get("chinese_keywords", {}),
            "queries": generated.get("queries", {}),
            "flat_queries": generated.get("flat_queries", []),
            "query_scores": generated.get("query_scores", []),
            "negative_keywords": generated.get("negative_keywords", [])
        }

        # Cache preview
        SearchCache.set(query, {"query_preview": preview_data}, language=language, mode=mode, ttl_seconds=1800)
        return preview_data

    @classmethod
    async def execute_smart_search(
        cls,
        query: str,
        language: str = "auto",
        mode: str = "normal",
        custom_queries: Optional[List[str]] = None,
        min_score: float = 60.0,
        min_likes: int = 0,
        max_likes: Optional[int] = None,
        min_comments: int = 0,
        min_shares: int = 0,
        min_duration: int = 0,
        max_duration: Optional[int] = None,
        category_filter: Optional[List[str]] = None,
        query_filter: Optional[str] = None,
        author_filter: Optional[str] = None,
        sort_by: str = "similarity",
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Full Search & Re-ranking Pipeline:
        1. NLP query generation
        2. Multi-stage Douyin query execution
        3. Deduplication
        4. 6-Dimensional Sub-Scoring (keyword, semantic, visual, scene, action, query, final)
        5. Advanced Filtering (score, likes, duration, author, negative keywords)
        6. Sorting & Persistence.
        """
        # 1. Obtain Chinese Queries
        preview_data = await cls.translate_and_generate(query, language, mode)
        active_queries = custom_queries if (custom_queries and len(custom_queries) > 0) else preview_data.get("flat_queries", [])

        if not active_queries:
            active_queries = [query]

        provider = get_search_provider()
        target_results = 30 if mode == "deep" else 15
        per_query_limit = 10 if mode == "deep" else 6

        # 2. Multi-stage Execution
        raw_candidates = []
        negative_kws = preview_data.get("negative_keywords", [])

        for q in active_queries[:15]:
            try:
                results = await provider.search(q, limit=per_query_limit)
                for r in results:
                    raw_candidates.append({
                        "platform": r.platform,
                        "remote_video_id": r.video_id,
                        "video_id": r.video_id,
                        "url": r.url,
                        "author": r.author,
                        "title": r.title,
                        "description": r.title or "",
                        "hashtags": r.hashtags,
                        "cover_url": r.thumbnail or r.cover_url or "",
                        "thumbnail": r.thumbnail or r.cover_url or "",
                        "publish_time": r.publish_time,
                        "duration": r.duration or 30,
                        "like_count": r.likes,
                        "likes": r.likes,
                        "comment_count": r.comments,
                        "comments": r.comments,
                        "share_count": r.shares,
                        "shares": r.shares,
                        "search_query": q,
                        "query": q,
                        "video_no_watermark_url": r.video_no_watermark_url
                    })
                if len(raw_candidates) >= target_results * 2:
                    break
            except Exception as e:
                print(f"[SmartSearchService] Error searching '{q}': {e}")

        # 3. Deduplication
        unique_candidates = Deduplicator.deduplicate(raw_candidates)

        # 4. 6-Dimensional Multi-Criteria Scoring (ScoringEngine)
        source_profile = {
            "keywords": preview_data.get("chinese_keywords", {}).get("primary", []),
            "categories": preview_data.get("chinese_keywords", {}).get("primary", []),
            "actions": preview_data.get("chinese_keywords", {}).get("action", []),
            "environment": preview_data.get("chinese_keywords", {}).get("scene", []),
            "visual_style": preview_data.get("chinese_keywords", {}).get("style", []),
            "style": preview_data.get("chinese_keywords", {}).get("style", [])
        }

        kw_scores_map = {item["query"]: item["score"] for item in preview_data.get("query_scores", [])}

        scored_candidates = []
        for cand in unique_candidates:
            search_q = cand.get("query", "")
            cand["query_score"] = kw_scores_map.get(search_q, 85)

            score_res = MultiLayerScoringEngine.calculate_score(source_profile, cand)
            cand.update({
                "keyword_score": score_res["keyword_score"],
                "semantic_score": score_res["semantic_score"],
                "visual_score": score_res["visual_score"],
                "scene_score": score_res["scene_score"],
                "action_score": score_res["action_score"],
                "query_score": score_res["query_score"],
                "final_score": score_res["final_score"],
                "score": score_res["final_score"],
                "score_pct": score_res["final_score"],
                "match_tier": score_res["match_tier"]
            })
            scored_candidates.append(cand)

        # 5. Advanced Result Filtering & Sorting (AdvancedResultFilter)
        filtered_results = AdvancedResultFilter.apply_filters(
            results=scored_candidates,
            min_score=min_score,
            min_likes=min_likes,
            max_likes=max_likes,
            min_comments=min_comments,
            min_shares=min_shares,
            min_duration=min_duration,
            max_duration=max_duration,
            category_filter=category_filter,
            query_filter=query_filter,
            author_filter=author_filter,
            negative_keywords=negative_kws,
            sort_by=sort_by
        )

        final_list = filtered_results[:target_results]

        # 6. Database Persistence
        job_id = str(uuid.uuid4())
        video_id = f"smart_{uuid.uuid4().hex[:8]}"

        if db:
            video_rec = Video(
                id=video_id,
                filename=f"SmartSearch_{query[:30]}.txt",
                file_path="",
                filesize=0
            )
            db.add(video_rec)

            for item in final_list:
                sr = SearchResult(
                    id=str(uuid.uuid4()),
                    video_id=video_id,
                    platform=item.get("platform", "douyin"),
                    remote_video_id=item.get("remote_video_id"),
                    url=item.get("url"),
                    author=item.get("author"),
                    title=item.get("title"),
                    description=item.get("description"),
                    hashtags=json.dumps(item.get("hashtags", []), ensure_ascii=False),
                    cover_url=item.get("thumbnail") or item.get("cover_url"),
                    publish_time=item.get("publish_time"),
                    like_count=item.get("likes", 0),
                    comment_count=item.get("comments", 0),
                    share_count=item.get("shares", 0),
                    search_query=item.get("query"),
                    relevance_score=float(item.get("final_score", 85)) / 100.0,
                    final_score=float(item.get("final_score", 85)) / 100.0
                )
                db.add(sr)
            db.commit()

        # Format standardized output
        standardized_results = []
        for idx, item in enumerate(final_list):
            standardized_results.append({
                "rank": idx + 1,
                "video_id": item.get("remote_video_id"),
                "title": item.get("title"),
                "url": item.get("url"),
                "thumbnail": item.get("thumbnail") or item.get("cover_url"),
                "cover_url": item.get("thumbnail") or item.get("cover_url"),
                "author": item.get("author"),
                "likes": item.get("likes", 0),
                "like_count": item.get("likes", 0),
                "comments": item.get("comments", 0),
                "comment_count": item.get("comments", 0),
                "shares": item.get("shares", 0),
                "share_count": item.get("shares", 0),
                "duration": item.get("duration", 30),
                "publish_time": item.get("publish_time", ""),
                "query": item.get("query", ""),
                "search_query": item.get("query", ""),
                "keyword_score": item.get("keyword_score", 80),
                "semantic_score": item.get("semantic_score", 85),
                "visual_score": item.get("visual_score", 90),
                "scene_score": item.get("scene_score", 80),
                "action_score": item.get("action_score", 85),
                "query_score": item.get("query_score", 90),
                "final_score": item.get("final_score", 88),
                "score": item.get("final_score", 88),
                "match_tier": item.get("match_tier", "High Match")
            })

        return {
            "job_id": job_id,
            "video_id": video_id,
            "original_query": query,
            "language": preview_data.get("detected_language", "vi"),
            "translated_keywords": preview_data.get("chinese_keywords", {}).get("primary", []) + preview_data.get("chinese_keywords", {}).get("clothing", []),
            "queries": active_queries,
            "preview": preview_data,
            "results_count": len(standardized_results),
            "results": standardized_results
        }
