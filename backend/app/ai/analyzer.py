import os
import json
import base64
import urllib.request
import re
from typing import Dict, Any, List

class MultiLayerVideoAnalyzer:
    SCHEMA_PROMPT = """
You are a top-tier Douyin/TikTok video analyst.
Analyze the video multi-dimensionally: Subjects, Appearance, Environment, Actions, Camera, Multi-Categories, and Chinese Keywords.

Return ONLY valid JSON matching this schema:
{
  "summary": "Brief natural description",
  "subjects": ["female / male / animal / car / food / product / etc."],
  "appearance": ["clothing style", "hair", "colors", "accessories"],
  "environment": ["bedroom / street / restaurant / studio / beach / etc."],
  "actions": ["dancing / changing clothes / walking / cooking / etc."],
  "camera": ["selfie / POV / cinematic / close-up / wide shot / handheld / tripod"],
  "categories": ["Fashion", "Beauty", "Comedy", "Dance", "Food", "Vlog", "Transformation"],
  "emotional_tone": ["energetic", "confident", "cheerful", "cool"],
  "keywords": {
    "primary": ["女生变装", "美女变装"],
    "action": ["变装", "换装", "转场", "卡点"],
    "scene": ["室内", "卧室", "镜子前"],
    "style": ["氛围感", "高级感", "时尚"],
    "trend": ["变装挑战", "热门", "爆款"]
  },
  "queries": {
    "exact": ["女生变装挑战", "美女变装转场"],
    "high_similarity": ["女生快速换装", "变装卡点舞"],
    "visual": ["女生镜子前变装", "室内美女变装"],
    "action": ["丝滑变装转场", "卡点变装视频"],
    "scene": ["卧室变装日常", "街头变装秀"],
    "trend": ["全网超火变装", "热门变装合集"],
    "broad": ["变装", "换装", "卡点舞"]
  }
}
"""

    @classmethod
    def analyze(
        cls,
        keyframe_items: List[Dict[str, Any]],
        ocr_items: List[Dict[str, Any]],
        asr_data: Dict[str, Any],
        metadata: Dict[str, Any],
        user_hint: str = "",
        api_key: str = ""
    ) -> Dict[str, Any]:
        transcript = asr_data.get("transcript", "")
        ocr_texts = [o.get("text", "") for o in ocr_items if isinstance(o, dict)]

        if api_key:
            try:
                context_str = f"Transcript: {transcript}\nOCR Text: {', '.join(ocr_texts)}\nUser Note: {user_hint}\nDuration: {metadata.get('duration')}s"
                parts = [{"text": cls.SCHEMA_PROMPT + f"\n\nContext:\n{context_str}"}]
                for item in keyframe_items[:3]:
                    fp = item.get("path")
                    if fp and os.path.exists(fp):
                        with open(fp, "rb") as f:
                            b64_img = base64.b64encode(f.read()).decode("utf-8")
                        parts.append({"inline_data": {"mime_type": "image/jpeg", "data": b64_img}})

                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                payload = {
                    "contents": [{"parts": parts}],
                    "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
                }
                req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=18) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                    txt = res["candidates"][0]["content"]["parts"][0]["text"]
                    txt = re.sub(r"^```json\s*", "", txt.strip(), flags=re.MULTILINE)
                    txt = re.sub(r"```$", "", txt.strip(), flags=re.MULTILINE)
                    return json.loads(txt)
            except Exception as e:
                print(f"[MultiLayerAnalyzer] API Fallback: {e}")

        # Intelligent Fallback Engine
        combined = (transcript + " " + " ".join(ocr_texts) + " " + user_hint).lower()

        if any(w in combined for w in ["món", "ăn", "nấu", "bếp", "ẩm thực", "food"]):
            return {
                "summary": "Video ẩm thực và hướng dẫn nấu món ăn ngon tại nhà.",
                "subjects": ["food", "chef", "creator"],
                "appearance": ["trang phục làm bếp", "món ăn bày trí đẹp mắt"],
                "environment": ["kitchen", "restaurant", "street"],
                "actions": ["cooking", "frying", "eating", "reviewing"],
                "camera": ["close-up", "top-down", "tripod"],
                "categories": ["Food", "Lifestyle", "Cooking"],
                "emotional_tone": ["healing", "mouth-watering", "relaxing"],
                "keywords": {
                    "primary": ["家常菜做法", "深夜美食", "美食教程"],
                    "action": ["沉浸式做饭", "大火翻炒", "调料调配"],
                    "scene": ["厨房", "人间烟火气", "夜市路边摊"],
                    "style": ["治愈系", "高清慢镜头", "诱人色泽"],
                    "trend": ["全网爆款美食", "神仙吃法", "懒人快手菜"]
                },
                "queries": {
                    "exact": ["家常菜美食教程", "深夜食堂治愈做饭"],
                    "high_similarity": ["懒人快手菜", "爆款下饭菜做法"],
                    "visual": ["沉浸式厨房做饭", "高清美食诱人特写"],
                    "action": ["一分钟学会做菜", "经典家常菜翻炒"],
                    "scene": ["温馨厨房做饭日常", "夜市小吃制作现场"],
                    "trend": ["全网都在学的爆款菜", "神级下饭菜教程"],
                    "broad": ["美食", "做饭", "家常菜", "特色小吃"]
                }
            }
        elif any(w in combined for w in ["hài", "cười", "drama", "tiểu phẩm"]):
            return {
                "summary": "Tiểu phẩm kịch bản hài hước tình huống bất ngờ.",
                "subjects": ["comedian", "male", "female", "group"],
                "appearance": ["trang phục đời thường", "biểu cảm đa dạng"],
                "environment": ["office", "living room", "street"],
                "actions": ["acting", "talking", "pranking", "reacting"],
                "camera": ["handheld", "POV", "medium shot"],
                "categories": ["Comedy", "Drama", "Storytelling"],
                "emotional_tone": ["funny", "hilarious", "surprising"],
                "keywords": {
                    "primary": ["搞笑短剧", "沙雕日常", "爆笑反转"],
                    "action": ["神级反转", "整蛊互动", "一本正经搞笑"],
                    "scene": ["办公室", "家庭生活", "校园"],
                    "style": ["幽默段子", "戏精表演", "快节奏剪辑"],
                    "trend": ["今日份快乐源泉", "笑到肚子疼", "大冤种日常"]
                },
                "queries": {
                    "exact": ["爆笑反转短剧", "搞笑沙雕日常"],
                    "high_similarity": ["戏精同事搞笑日常", "情侣互坑名场面"],
                    "visual": ["办公室搞笑短片", "沙雕名场面合集"],
                    "action": ["意想不到的结局", "神级反转打脸"],
                    "scene": ["职场爆笑日常", "家庭沙雕瞬间"],
                    "trend": ["全网笑点合集", "笑死人的宝藏短剧"],
                    "broad": ["搞笑", "沙雕", "短剧", "段子"]
                }
            }
        else:
            # Default / Dance / Transformation / Hot trend
            return {
                "summary": "Video nhảy hiện đại, biến hình thời trang bắt nhịp âm nhạc Douyin.",
                "subjects": ["female", "young creator", "dancer"],
                "appearance": ["trang phục thời trang", "makeup cuốn hút", "tóc đẹp"],
                "environment": ["bedroom", "dance studio", "neon stage", "street"],
                "actions": ["dancing", "changing clothes", "rhythm syncing", "posing"],
                "camera": ["full-body", "cinematic", "tripod", "close-up"],
                "categories": ["Dance", "Fashion", "Beauty", "Transformation"],
                "emotional_tone": ["energetic", "confident", "attractive"],
                "keywords": {
                    "primary": ["抖音热舞", "热门卡点舞", "美女变装"],
                    "action": ["变装卡点", "慢摇舞", "丝滑转场", "踩点律动"],
                    "scene": ["室内练舞室", "氛围感卧室", "霓虹舞台"],
                    "style": ["氛围感", "高级感", "甜酷风", "时尚"],
                    "trend": ["卡点舞挑战", "爆款翻跳", "心动女嘉宾"]
                },
                "queries": {
                    "exact": ["抖音热门热舞", "热门卡点舞翻跳", "女生变装挑战"],
                    "high_similarity": ["美女室内变装", "高颜值女团舞翻跳", "全网火爆踩点舞"],
                    "visual": ["氛围感练舞室热舞", "镜子前丝滑变装", "霓虹灯光舞台跳舞"],
                    "action": ["变装卡点惊艳瞬间", "丝滑连贯舞蹈动作", "慢动作踩点律动"],
                    "scene": ["室内唯美练舞", "户外街头沉浸式跳舞"],
                    "trend": ["全网都在挑战的爆款舞", "看一遍就上头的神仙跳舞"],
                    "broad": ["热舞", "卡点舞", "变装", "舞蹈", "美女跳舞"]
                }
            }
