from typing import List, Dict, Any

class AdvancedResultFilter:
    @staticmethod
    def apply_filters(
        results: List[Dict[str, Any]],
        min_score: float = 70.0,
        min_likes: int = 0,
        min_comments: int = 0,
        min_shares: int = 0,
        category_filter: List[str] = None,
        sort_by: str = "similarity"
    ) -> List[Dict[str, Any]]:
        filtered = []

        for r in results:
            score = r.get("score_pct", r.get("final_score", 0.0) * 100)
            if score < min_score:
                continue

            if min_likes > 0 and r.get("like_count", 0) < min_likes:
                continue

            if min_comments > 0 and r.get("comment_count", 0) < min_comments:
                continue

            if min_shares > 0 and r.get("share_count", 0) < min_shares:
                continue

            if category_filter:
                title = r.get("title", "").lower()
                if not any(c.lower() in title for c in category_filter):
                    continue

            filtered.append(r)

        # Sorting
        if sort_by == "likes":
            filtered.sort(key=lambda x: x.get("like_count", 0), reverse=True)
        elif sort_by == "comments":
            filtered.sort(key=lambda x: x.get("comment_count", 0), reverse=True)
        elif sort_by == "shares":
            filtered.sort(key=lambda x: x.get("share_count", 0), reverse=True)
        elif sort_by == "newest":
            filtered.sort(key=lambda x: x.get("publish_time", ""), reverse=True)
        else:
            # Default: similarity DESC
            filtered.sort(key=lambda x: x.get("final_score", 0.0), reverse=True)

        return filtered
