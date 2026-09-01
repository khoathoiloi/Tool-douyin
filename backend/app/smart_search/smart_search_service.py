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
from ..core.models import Video, SearchResult
from sqlalchemy.orm import Session

class SmartSearchService:
    """
    End-to-end Smart Douyin Search Coordinator:
    Vietnamese/English/Chinese NLP -> Chinese Queries -> Multi-stage Douyin Search -> Deduplication -> Re-ranking.
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
        min_likes: int = 0,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Full Search Pipeline: executes queries, collects candidates, filters ads, re-ranks, and saves.
        """
        # 1. Obtain Chinese Queries
        preview_data = await cls.translate_and_generate(query, language, mode)
        active_queries = custom_queries if (custom_queries and len(custom_queries) > 0) else preview_data.get("flat_queries", [])

        if not active_queries:
            active_queries = [query]

        provider = get_search_provider()
        target_results = 30 if mode == "deep" else 15
        per_query_limit = 10 if mode == "deep" else 6

        # 2. Multi-stage Execution (Exact -> High -> Medium -> Broad)
        raw_candidates = []
        negative_kws = preview_data.get("negative_keywords", [])

        for q in active_queries[:15]:
            try:
                results = await provider.search(q, limit=per_query_limit)
                for r in results:
                    raw_candidates.append({
                        "platform": r.platform,
                        "remote_video_id": r.video_id,
                        "url": r.url,
                        "author": r.author,
                        "title": r.title,
                        "description": r.title or "",
                        "hashtags": [],
                        "cover_url": r.thumbnail or "",
                        "thumbnail": r.thumbnail or "",
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

        # 4. Multi-criteria Re-ranking
        ranked_results = []
        kw_scores_map = {item["query"]: item["score"] for item in preview_data.get("query_scores", [])}
        primary_kws = preview_data.get("chinese_keywords", {}).get("primary", [])
        action_kws = preview_data.get("chinese_keywords", {}).get("action", [])
        clothing_kws = preview_data.get("chinese_keywords", {}).get("clothing", [])

        for cand in unique_candidates:
            title = cand.get("title", "")
            desc = cand.get("description", "")
            full_text = f"{title} {desc}"
            search_q = cand.get("search_query", "")

            # Filter negative keywords (Ads / Ecommerce shops)
            if any(neg in full_text for neg in negative_kws if len(neg) >= 2):
                continue

            # Filter min likes if requested
            if min_likes > 0 and cand.get("likes", 0) < min_likes:
                continue

            # Calculate Criteria Scores (0.0 to 1.0)
            # Keyword relevance
            kw_match_count = sum(1 for kw in (primary_kws + clothing_kws) if kw in full_text)
            score_keyword = min(1.0, 0.5 + (kw_match_count * 0.25))

            # Action relevance
            action_match = any(act in full_text for act in action_kws)
            score_action = 0.95 if action_match else 0.70

            # Semantic relevance
            score_semantic = 0.95 if search_q in full_text else 0.85

            # Visual relevance heuristic
            score_visual = 0.90 if any(v in full_text for v in ["自拍", "日常", "穿搭", "变装", "氛围感", "写真"]) else 0.80

            # Scene score
            score_scene = 0.90 if any(s in full_text for s in ["卧室", "室内", "房间", "厨房", "海边", "雪山"]) else 0.75

            # Query quality score from generator
            query_quality_pct = kw_scores_map.get(search_q, 80) / 100.0

            # Spec Formula:
            # Score = 0.30*Visual + 0.25*Semantic + 0.15*Action + 0.10*Scene + 0.15*Keyword + 0.05*QueryQuality
            final_composite_score = (
                0.30 * score_visual +
                0.25 * score_semantic +
                0.15 * score_action +
                0.10 * score_scene +
                0.15 * score_keyword +
                0.05 * query_quality_pct
            )

            cand["final_score"] = round(final_composite_score, 4)
            cand["score"] = int(round(final_composite_score * 100))
            cand["score_pct"] = cand["score"]
            cand["match_tier"] = (
                "Very High Match" if cand["score"] >= 90 else (
                    "High Match" if cand["score"] >= 80 else (
                        "Good Match" if cand["score"] >= 70 else "Possible Match"
                    )
                )
            )
            ranked_results.append(cand)

        # Sort by final score descending
        ranked_results.sort(key=lambda x: x["final_score"], reverse=True)
        final_list = ranked_results[:target_results]

        # 5. Persist to Database if session provided
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
                    relevance_score=item.get("final_score", 0.9),
                    final_score=item.get("final_score", 0.9)
                )
                db.add(sr)
            db.commit()

        # Standardized output matching Phase 4 specification
        standardized_results = []
        for idx, item in enumerate(final_list):
            standardized_results.append({
                "rank": idx + 1,
                "video_id": item.get("remote_video_id"),
                "title": item.get("title"),
                "url": item.get("url"),
                "thumbnail": item.get("thumbnail") or item.get("cover_url"),
                "author": item.get("author"),
                "likes": item.get("likes", 0),
                "comments": item.get("comments", 0),
                "shares": item.get("shares", 0),
                "duration": item.get("duration", 30),
                "publish_time": item.get("publish_time", ""),
                "query": item.get("query", ""),
                "score": item.get("score", 85),
                "match_tier": item.get("match_tier", "High Match"),
                "cover_url": item.get("thumbnail") or item.get("cover_url"),
                "like_count": item.get("likes", 0),
                "comment_count": item.get("comments", 0),
                "share_count": item.get("shares", 0),
                "search_query": item.get("query", "")
            })

        return {
            "job_id": job_id,
            "video_id": video_id,
            "original_query": query,
            "language": preview_data.get("detected_language", "vi"),
            "translated_keywords": primary_kws + clothing_kws + action_kws,
            "queries": active_queries,
            "preview": preview_data,
            "results_count": len(standardized_results),
            "results": standardized_results
        }
