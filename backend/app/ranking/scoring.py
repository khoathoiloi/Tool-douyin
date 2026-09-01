from typing import Dict, Any, List

class MultiLayerScoringEngine:
    """
    Standardized Multi-Dimensional Scoring Engine (Phase 5).
    Computes keyword, semantic, visual, scene, action, and query quality scores
    scaled to normalized 0-100 values.
    """

    @staticmethod
    def calculate_score(
        source_profile: Dict[str, Any],
        candidate: Dict[str, Any],
        weights: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Calculates 6-dimensional sub-scores and final normalized composite score (0-100).
        """
        w = weights or {
            "visual": 0.30,
            "semantic": 0.25,
            "action": 0.15,
            "scene": 0.10,
            "keyword": 0.15,
            "query": 0.05
        }

        title = str(candidate.get("title", "")).lower()
        desc = str(candidate.get("description", "")).lower()
        full_text = f"{title} {desc}"
        search_q = str(candidate.get("query") or candidate.get("search_query") or "").lower()

        # 1. Visual Score (0-100)
        visual_style = [str(s).lower() for s in (source_profile.get("visual_style", []) or source_profile.get("style", []))]
        visual_ratio = 0.75
        if any(v in full_text for v in visual_style + ["自拍", "日常", "穿搭", "变装", "氛围感", "写真", "唯美"]):
            visual_ratio = 0.95
        visual_score = int(round(visual_ratio * 100))

        # 2. Semantic Score (0-100)
        cats = [str(c).lower() for c in (source_profile.get("categories", []) or source_profile.get("primary", []))]
        semantic_ratio = 0.70
        if any(c in full_text for c in cats):
            semantic_ratio = 0.92
        elif search_q and any(word in full_text for word in search_q.split()):
            semantic_ratio = 0.88
        semantic_score = int(round(semantic_ratio * 100))

        # 3. Action Score (0-100)
        actions = [str(a).lower() for a in source_profile.get("actions", [])]
        action_ratio = 0.65
        if any(a in full_text for a in actions + ["跳舞", "做饭", "遮脸", "变装", "测评", "开箱", "翻唱", "瘦肚子", "做家务"]):
            action_ratio = 0.95
        action_score = int(round(action_ratio * 100))

        # 4. Scene Score (0-100)
        scenes = [str(s).lower() for s in (source_profile.get("environment", []) or source_profile.get("scene", []))]
        scene_ratio = 0.70
        if any(s in full_text for s in scenes + ["卧室", "室内", "房间", "厨房", "海边", "雪山", "街头", "夜市", "公路"]):
            scene_ratio = 0.92
        scene_score = int(round(scene_ratio * 100))

        # 5. Keyword Score (0-100)
        keywords = [str(k).lower() for k in (source_profile.get("keywords", []) or source_profile.get("primary", []))]
        kw_hits = sum(1 for k in keywords if k and k in full_text)
        keyword_ratio = min(1.0, 0.60 + kw_hits * 0.20)
        keyword_score = int(round(keyword_ratio * 100))

        # 6. Query Quality Score (0-100)
        query_score = int(candidate.get("query_score", candidate.get("score", 85)))
        query_score = max(50, min(100, query_score))

        # Final Composite Score (0-100)
        final_float = (
            w["visual"] * visual_score +
            w["semantic"] * semantic_score +
            w["action"] * action_score +
            w["scene"] * scene_score +
            w["keyword"] * keyword_score +
            w["query"] * query_score
        )
        final_score = int(round(final_float))

        # Classification
        if final_score >= 90:
            match_tier = "Very High Match"
        elif final_score >= 80:
            match_tier = "High Match"
        elif final_score >= 70:
            match_tier = "Good Match"
        elif final_score >= 60:
            match_tier = "Possible Match"
        else:
            match_tier = "Low Match"

        return {
            "final_score": final_score,
            "score": final_score,
            "match_tier": match_tier,
            "keyword_score": keyword_score,
            "semantic_score": semantic_score,
            "visual_score": visual_score,
            "scene_score": scene_score,
            "action_score": action_score,
            "query_score": query_score,
            "score_pct": final_score
        }
