import math
from typing import Dict, Any, List
from ..core.config import settings

class RankingEngine:
    @staticmethod
    def calculate_scores(
        source_profile: Dict[str, Any],
        candidate: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Multi-factor score calculation based on Build Specification:
        final_score = 
            0.35 * semantic_similarity +
            0.25 * visual_similarity +
            0.15 * keyword_similarity +
            0.10 * hashtag_similarity +
            0.10 * content_type_similarity +
            0.05 * popularity_score
        """
        title = candidate.get("title", "").lower()
        desc = candidate.get("description", "").lower()
        candidate_text = f"{title} {desc}"
        
        # 1. Semantic Similarity
        summary = source_profile.get("summary", "").lower()
        search_concepts = [c.lower() for c in source_profile.get("search_concepts", [])]
        semantic_matches = sum(1 for c in search_concepts if c in candidate_text)
        semantic_sim = min(1.0, 0.4 + (semantic_matches * 0.2))
        
        # 2. Visual / Style Similarity
        content_format = source_profile.get("content_format", "").lower()
        visual_sim = 0.75 # Baseline visual style alignment
        if content_format and content_format in candidate_text:
            visual_sim = 0.95
            
        # 3. Keyword Similarity
        query_used = candidate.get("search_query", "").lower()
        keyword_sim = 0.6
        if query_used and query_used in candidate_text:
            keyword_sim = 0.95
            
        # 4. Hashtag Similarity
        cand_hashtags = candidate.get("hashtags", []) or []
        source_hashtags = [f"#{c}" for c in search_concepts]
        hashtag_overlap = sum(1 for h in cand_hashtags if any(sh in h for sh in source_hashtags))
        hashtag_sim = min(1.0, 0.5 + (hashtag_overlap * 0.25))
        
        # 5. Content Type Similarity
        content_type_sim = 0.85
        
        # 6. Popularity Score (Log scale, capped at 1.0)
        likes = candidate.get("like_count", 0)
        pop_score = min(1.0, math.log10(max(10, likes)) / 7.0) # 10M likes = 1.0
        
        # Weighted Final Score
        final_score = (
            settings.WEIGHT_SEMANTIC * semantic_sim +
            settings.WEIGHT_VISUAL * visual_sim +
            settings.WEIGHT_KEYWORD * keyword_sim +
            settings.WEIGHT_HASHTAG * hashtag_sim +
            settings.WEIGHT_CONTENT_TYPE * content_type_sim +
            settings.WEIGHT_POPULARITY * pop_score
        )
        
        return {
            "semantic_similarity": round(semantic_sim, 3),
            "visual_similarity": round(visual_sim, 3),
            "keyword_similarity": round(keyword_sim, 3),
            "hashtag_similarity": round(hashtag_sim, 3),
            "content_type_similarity": round(content_type_sim, 3),
            "popularity_score": round(pop_score, 3),
            "final_score": round(final_score, 4)
        }
