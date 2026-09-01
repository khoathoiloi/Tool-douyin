import math
from typing import Dict, Any, List

class MultiLayerScoringEngine:
    @staticmethod
    def calculate_score(
        source_profile: Dict[str, Any],
        candidate: Dict[str, Any],
        weights: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Weights according to Section 15:
        Visual similarity:   30%
        Semantic similarity: 20%
        Action similarity:   15%
        Scene similarity:    10%
        OCR similarity:      10%
        Audio similarity:     5%
        Keyword similarity:  10%
        Total:              100%
        """
        w = weights or {
            "visual": 0.30,
            "semantic": 0.20,
            "action": 0.15,
            "scene": 0.10,
            "ocr": 0.10,
            "audio": 0.05,
            "keyword": 0.10
        }

        title = candidate.get("title", "").lower()
        desc = candidate.get("description", "").lower()
        full_text = f"{title} {desc}"

        # 1. Visual similarity (style, aesthetic match)
        visual_style = [s.lower() for s in source_profile.get("visual_style", [])]
        visual_sim = 0.70
        if any(s in full_text for s in visual_style):
            visual_sim = 0.95

        # 2. Semantic similarity (summary, categories)
        cats = [c.lower() for c in source_profile.get("categories", [])]
        semantic_sim = 0.65
        if any(c in full_text for c in cats):
            semantic_sim = 0.90

        # 3. Action similarity (movements, dance, cooking, etc.)
        actions = [a.lower() for a in source_profile.get("actions", [])]
        action_sim = 0.60
        if any(a in full_text for a in actions):
            action_sim = 0.92

        # 4. Scene similarity (bedroom, street, studio)
        scenes = [s.lower() for s in source_profile.get("environment", [])]
        scene_sim = 0.60
        if any(s in full_text for s in scenes):
            scene_sim = 0.88

        # 5. OCR similarity
        ocr_texts = [o.get("text", "").lower() if isinstance(o, dict) else str(o).lower() for o in source_profile.get("ocr_text", [])]
        ocr_sim = 0.50
        if any(ot in full_text for ot in ocr_texts if len(ot) > 2):
            ocr_sim = 0.95

        # 6. Audio similarity (transcript keywords)
        transcript = source_profile.get("transcript", "").lower()
        audio_sim = 0.70

        # 7. Keyword similarity (search query overlap)
        query = candidate.get("search_query", "").lower()
        keyword_sim = 0.80
        if query and query in full_text:
            keyword_sim = 0.98

        final_score = (
            w["visual"] * visual_sim +
            w["semantic"] * semantic_sim +
            w["action"] * action_sim +
            w["scene"] * scene_sim +
            w["ocr"] * ocr_sim +
            w["audio"] * audio_sim +
            w["keyword"] * keyword_sim
        )

        score_pct = round(final_score * 100, 1)

        # Classification
        if score_pct >= 90:
            match_tier = "Very High Match"
        elif score_pct >= 80:
            match_tier = "High Match"
        elif score_pct >= 70:
            match_tier = "Good Match"
        elif score_pct >= 60:
            match_tier = "Possible Match"
        else:
            match_tier = "Low Match"

        return {
            "score_pct": score_pct,
            "final_score": round(final_score, 4),
            "match_tier": match_tier,
            "breakdown": {
                "visual": round(visual_sim * 100, 1),
                "semantic": round(semantic_sim * 100, 1),
                "action": round(action_sim * 100, 1),
                "scene": round(scene_sim * 100, 1),
                "ocr": round(ocr_sim * 100, 1),
                "audio": round(audio_sim * 100, 1),
                "keyword": round(keyword_sim * 100, 1)
            }
        }
