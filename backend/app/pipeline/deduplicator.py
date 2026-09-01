import re
from typing import List, Dict, Any

class Deduplicator:
    @staticmethod
    def tokenize(text: str) -> set:
        # Split by whitespace, punctuation, and extract 2-char ngrams for Chinese
        words = set(re.findall(r"\w+", text.lower()))
        if not words or len(words) < 3:
            # 2-gram fallback for Chinese
            clean = re.sub(r"\s+", "", text.lower())
            return set(clean[i:i+2] for i in range(len(clean) - 1)) if len(clean) >= 2 else set([clean])
        return words

    @classmethod
    def deduplicate(cls, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen_ids = set()
        seen_urls = set()
        seen_tokens = []
        unique_results = []
        
        for c in candidates:
            vid_id = str(c.get("remote_video_id", "")).strip()
            url = str(c.get("url", "")).strip()
            title = str(c.get("title", "")).strip()
            
            # 1. Video ID match
            if vid_id and vid_id in seen_ids:
                continue
                
            # 2. Canonical URL match
            if url and url in seen_urls:
                continue
                
            # 3. High Title similarity match (Jaccard word/token similarity)
            title_tokens = cls.tokenize(title)
            is_dup_title = False
            for past_tokens in seen_tokens:
                if len(title_tokens) >= 3 and len(past_tokens) >= 3:
                    overlap = len(title_tokens.intersection(past_tokens)) / max(len(title_tokens), len(past_tokens))
                    if overlap >= 0.90:
                        is_dup_title = True
                        break
            if is_dup_title:
                continue
                
            if vid_id:
                seen_ids.add(vid_id)
            if url:
                seen_urls.add(url)
            seen_tokens.append(title_tokens)
            unique_results.append(c)
            
        return unique_results
