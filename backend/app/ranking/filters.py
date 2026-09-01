from typing import List, Dict, Any, Optional
from datetime import datetime

class AdvancedResultFilter:
    """
    Advanced Content Filter & Ranking Engine (Phase 5).
    Provides multi-dimensional filtering, customizable sorting, and benchmark statistics.
    """

    @staticmethod
    def apply_filters(
        results: List[Dict[str, Any]],
        min_score: float = 70.0,
        min_likes: int = 0,
        max_likes: Optional[int] = None,
        min_comments: int = 0,
        max_comments: Optional[int] = None,
        min_shares: int = 0,
        max_shares: Optional[int] = None,
        min_duration: int = 0,
        max_duration: Optional[int] = None,
        category_filter: Optional[List[str]] = None,
        query_filter: Optional[str] = None,
        author_filter: Optional[str] = None,
        negative_keywords: Optional[List[str]] = None,
        sort_by: str = "similarity"
    ) -> List[Dict[str, Any]]:
        filtered: List[Dict[str, Any]] = []
        neg_kws = negative_keywords or ["广告", "商品", "店铺", "购买", "包邮"]

        for r in results:
            title = str(r.get("title", "")).lower()
            desc = str(r.get("description", "")).lower()
            full_text = f"{title} {desc}"

            # 1. Negative keywords filter (Ad/Shop elimination)
            if any(neg.lower() in full_text for neg in neg_kws if len(neg) >= 2):
                continue

            # 2. Similarity Score filter
            score = float(r.get("final_score", r.get("score", 0)))
            if score < min_score:
                continue

            # 3. Likes filter
            likes = int(r.get("likes", r.get("like_count", 0)))
            if likes < min_likes:
                continue
            if max_likes is not None and likes > max_likes:
                continue

            # 4. Comments filter
            comments = int(r.get("comments", r.get("comment_count", 0)))
            if comments < min_comments:
                continue
            if max_comments is not None and comments > max_comments:
                continue

            # 5. Shares filter
            shares = int(r.get("shares", r.get("share_count", 0)))
            if shares < min_shares:
                continue
            if max_shares is not None and shares > max_shares:
                continue

            # 6. Duration filter
            duration = int(r.get("duration", 30))
            if duration < min_duration:
                continue
            if max_duration is not None and duration > max_duration:
                continue

            # 7. Category filter
            if category_filter:
                if not any(c.lower() in full_text for c in category_filter):
                    continue

            # 8. Query filter
            if query_filter:
                r_query = str(r.get("query", r.get("search_query", ""))).lower()
                if query_filter.lower() not in r_query and query_filter.lower() not in full_text:
                    continue

            # 9. Author filter
            if author_filter:
                r_author = str(r.get("author", "")).lower()
                if author_filter.lower() not in r_author:
                    continue

            filtered.append(r)

        # Sorting Modes
        sort_key = sort_by.lower().strip()
        if sort_key in ["likes", "top_likes"]:
            filtered.sort(key=lambda x: int(x.get("likes", x.get("like_count", 0))), reverse=True)
        elif sort_key in ["comments", "top_comments"]:
            filtered.sort(key=lambda x: int(x.get("comments", x.get("comment_count", 0))), reverse=True)
        elif sort_key in ["shares", "top_shares"]:
            filtered.sort(key=lambda x: int(x.get("shares", x.get("share_count", 0))), reverse=True)
        elif sort_key in ["newest", "date", "recent"]:
            filtered.sort(key=lambda x: str(x.get("publish_time", "")), reverse=True)
        elif sort_key in ["duration_asc", "shortest"]:
            filtered.sort(key=lambda x: int(x.get("duration", 30)), reverse=False)
        elif sort_key in ["duration_desc", "longest"]:
            filtered.sort(key=lambda x: int(x.get("duration", 30)), reverse=True)
        else:
            # Default: Similarity / Relevance (final_score DESC)
            filtered.sort(key=lambda x: float(x.get("final_score", x.get("score", 0))), reverse=True)

        return filtered

    @staticmethod
    def calculate_benchmark_metrics(
        before_list: List[Dict[str, Any]],
        after_list: List[Dict[str, Any]],
        target_intent_keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Computes precision, duplicate rate, irrelevant rate, and average score
        for BEFORE FILTER vs AFTER FILTER comparison.
        """
        kws = [k.lower() for k in (target_intent_keywords or ["美女", "睡衣", "做饭", "猫", "超跑", "变装"])]
        neg_kws = ["广告", "商品", "店铺", "购买", "包邮", "淘宝", "下单"]

        def analyze_batch(items: List[Dict[str, Any]]) -> Dict[str, Any]:
            if not items:
                return {
                    "total": 0,
                    "precision": 0.0,
                    "duplicate_rate": 0.0,
                    "irrelevant_rate": 0.0,
                    "average_score": 0.0
                }

            total = len(items)
            # Duplicate rate
            seen_ids = set()
            dup_count = 0
            for it in items:
                vid = it.get("video_id") or it.get("remote_video_id")
                if vid in seen_ids:
                    dup_count += 1
                seen_ids.add(vid)
            dup_rate = round((dup_count / total) * 100, 2)

            # Irrelevant rate (Contains ads or unrelated keywords)
            irrelevant_count = 0
            relevant_count = 0
            total_score = 0

            for it in items:
                text = (str(it.get("title", "")) + " " + str(it.get("description", ""))).lower()
                is_ad = any(neg in text for neg in neg_kws)
                is_rel = any(kw in text for kw in kws) if kws else True

                if is_ad or not is_rel:
                    irrelevant_count += 1
                else:
                    relevant_count += 1

                total_score += float(it.get("final_score", it.get("score", 70)))

            precision = round((relevant_count / total) * 100, 2)
            irrel_rate = round((irrelevant_count / total) * 100, 2)
            avg_score = round(total_score / total, 2)

            return {
                "total": total,
                "precision": precision,
                "duplicate_rate": dup_rate,
                "irrelevant_rate": irrel_rate,
                "average_score": avg_score
            }

        return {
            "before_filter": analyze_batch(before_list),
            "after_filter": analyze_batch(after_list)
        }
