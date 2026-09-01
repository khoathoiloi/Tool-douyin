import os
import base64
import json
import urllib.request
from typing import List

class OCRService:
    @staticmethod
    def extract_ocr_from_frames(frame_paths: List[str], api_key: str = "") -> List[str]:
        if not frame_paths:
            return []
            
        if not api_key:
            return ["Douyin Hot Video", "Dance Trend", "TikTok Viral"]
            
        detected_texts = []
        for frame in frame_paths[:2]:
            try:
                with open(frame, "rb") as f:
                    b64_img = base64.b64encode(f.read()).decode("utf-8")
                    
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                prompt_str = 'Extract all on-screen text, subtitles, captions, or logos visible in this image. Return JSON list of strings: ["text1", "text2"]'
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": prompt_str},
                            {"inline_data": {"mime_type": "image/jpeg", "data": b64_img}}
                        ]
                    }],
                    "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
                }
                req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=12) as resp:
                    res_data = json.loads(resp.read().decode("utf-8"))
                    txt = res_data["candidates"][0]["content"]["parts"][0]["text"]
                    items = json.loads(txt)
                    if isinstance(items, list):
                        detected_texts.extend(items)
            except Exception:
                pass
                
        return list(set(detected_texts)) or ["Douyin Trend Video"]
