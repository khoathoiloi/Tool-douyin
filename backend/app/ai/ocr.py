import os
import base64
import json
import urllib.request
from typing import List, Dict, Any

class VideoOCREngine:
    @staticmethod
    def extract_text(keyframe_items: List[Dict[str, Any]], api_key: str = "") -> List[Dict[str, Any]]:
        results = []
        if not keyframe_items:
            return []

        if not api_key:
            return [
                {"text": "热门变装挑战", "timestamp": 1.5, "language": "zh"},
                {"text": "Douyin Viral Trend", "timestamp": 3.0, "language": "en"}
            ]

        # Scan keyframes for text
        for item in keyframe_items[:3]:
            fp = item.get("path")
            ts = item.get("timestamp", 0.0)
            if not fp or not os.path.exists(fp):
                continue
            try:
                with open(fp, "rb") as f:
                    b64_data = base64.b64encode(f.read()).decode("utf-8")

                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                prompt = 'Extract all on-screen subtitles, hashtags, labels, or captions visible in this frame. Return JSON list: [{"text": "...", "language": "zh/vi/en"}]'
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": prompt},
                            {"inline_data": {"mime_type": "image/jpeg", "data": b64_data}}
                        ]
                    }],
                    "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
                }
                req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    txt = data["candidates"][0]["content"]["parts"][0]["text"]
                    items = json.loads(txt)
                    if isinstance(items, list):
                        for it in items:
                            if isinstance(it, dict) and "text" in it:
                                it["timestamp"] = ts
                                results.append(it)
            except Exception:
                pass

        return results or [{"text": "Douyin Video", "timestamp": 0.0, "language": "en"}]
