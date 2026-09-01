import json
import urllib.request
from typing import List, Dict, Any

class LLMReranker:
    @staticmethod
    def rerank_candidates(
        source_profile: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        top_n: int = 30,
        api_key: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Takes top N candidates and uses LLM as a reranking signal.
        """
        if not candidates:
            return []
            
        target_candidates = candidates[:top_n]
        
        if api_key:
            try:
                candidate_snippets = [
                    {"id": c.get("remote_video_id"), "title": c.get("title"), "query": c.get("search_query")}
                    for c in target_candidates
                ]
                prompt = f"""
Source Video Profile:
{json.dumps(source_profile, ensure_ascii=False)}

Candidate Douyin Videos:
{json.dumps(candidate_snippets, ensure_ascii=False)}

Score each candidate's relevance to the source video on a scale from 0.0 to 1.0.
Return JSON array:
[
  {{"candidate_id": "...", "relevance": 0.95, "reason": "Highly similar dance style and soundtrack"}}
]
"""
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
                }
                req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    txt = res_json["candidates"][0]["content"]["parts"][0]["text"]
                    scores = json.loads(txt)
                    score_map = {item["candidate_id"]: item for item in scores if "candidate_id" in item}
                    
                    for c in target_candidates:
                        cid = c.get("remote_video_id")
                        if cid in score_map:
                            llm_rel = score_map[cid].get("relevance", 0.8)
                            c["relevance_score"] = round(llm_rel, 3)
                            # Adjust final score slightly with LLM signal
                            c["final_score"] = round(c.get("final_score", 0.8) * 0.7 + llm_rel * 0.3, 4)
            except Exception as e:
                print(f"[LLMReranker] Reranking fallback: {e}")
                
        # Sort by final_score descending
        candidates.sort(key=lambda x: x.get("final_score", 0.0), reverse=True)
        return candidates
