import os
import json
import re
import urllib.request
from typing import Dict, List, Any, Optional

from .language_detector import LanguageDetector
from .vietnamese_query_engine import VietnameseQueryEngine
from ..core.config import settings

class ChineseQueryGenerator:
    """
    Intelligent Douyin Search Query Generator.
    Translates Vietnamese / English into native Chinese search queries with
    semantic expansion, priority tiers, quality scores, and negative keywords.
    """

    # Comprehensive Semantic Mapping Table (Vietnamese/English concept -> Chinese Douyin keywords)
    SEMANTIC_MAPPINGS = {
        "gai_xinh": {
            "primary": ["美女", "高颜值女生", "漂亮女生", "美女小姐姐", "心动女生"],
            "style": ["日常", "自拍", "氛围感", "生活感", "颜值控"]
        },
        "trai_dep": {
            "primary": ["帅哥", "高颜值男生", "清爽帅哥", "氛围感帅哥", "小哥哥"],
            "style": ["日常", "穿搭", "变装", "自拍"]
        },
        "pijama": {
            "clothing": ["睡衣", "睡衣穿搭", "居家服", "可爱睡衣", "丝绸睡衣"],
            "action": ["穿睡衣", "睡衣自拍"]
        },
        "che_mat": {
            "action": ["遮脸", "捂脸", "不露脸", "挡脸", "手势遮脸"],
            "style": ["神秘感", "氛围感"]
        },
        "vay": {
            "clothing": ["裙子", "连衣裙", "白裙子", "小裙子", "吊带裙"],
            "style": ["显瘦穿搭", "气质"]
        },
        "ao_dai": {
            "clothing": ["奥黛", "越南奥黛", "旗袍", "汉服", "古风"],
            "style": ["国风", "优雅"]
        },
        "nhay": {
            "action": ["跳舞", "热舞", "卡点舞", "翻跳", "踩点舞", "慢摇"],
            "style": ["抖音热舞", "神仙舞蹈", "全网爆款"]
        },
        "nau_an": {
            "action": ["做饭", "烹饪", "美食教程", "沉浸式做饭", "下厨"],
            "scene": ["厨房", "深夜食堂", "人间烟火气"],
            "style": ["治愈系", "家常菜", "懒人美食"]
        },
        "meo": {
            "primary": ["猫咪", "小猫", "萌宠", "可爱猫咪", "吸猫"],
            "style": ["治愈", "搞笑", "萌宠日常"]
        },
        "xe": {
            "primary": ["汽车", "超跑", "豪车", "跑车", "改装车"],
            "action": ["沉浸式开箱", "试驾测评", "提车"]
        },
        "hai_huoc": {
            "primary": ["搞笑", "沙雕", "爆笑", "幽默", "段子"],
            "style": ["沙雕日常", "神级反转", "今日份快乐"]
        },
        "trong_phong": {
            "scene": ["卧室", "房间", "室内", "床上"],
            "style": ["日常", "居家", "沉浸式"]
        },
        "review": {
            "primary": ["测评", "探店", "试吃"],
            "action": ["测评", "开箱", "试吃", "体验", "探店", "美食测评"],
            "style": ["真实测评", "避坑指南", "吃货日常"]
        }
    }

    # Standard Negative Keywords to eliminate ads / shops when searching visual content
    STANDARD_NEGATIVE_KEYWORDS = ["广告", "商品", "店铺", "购买", "包邮", "淘宝", "下单", "招商"]

    @classmethod
    def generate(
        cls,
        query: str,
        language: str = "auto",
        mode: str = "normal",
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main entrypoint: takes any user query in vi, zh, or en and generates
        structured, Douyin-optimized Chinese queries.
        """
        raw_query = query.strip()
        detected_lang = LanguageDetector.detect(raw_query, preferred=language)

        # 1. Chinese Input Handler (Direct Search Mode)
        if detected_lang == "zh":
            return cls._handle_chinese_input(raw_query, mode)

        # 2. Extract Entities from Vietnamese / English
        analysis = VietnameseQueryEngine.analyze(raw_query)

        # 3. Check for configured AI Provider (Gemini / OpenAI / custom endpoint)
        ai_key = api_key or os.getenv("AI_API_KEY") or getattr(settings, "GEMINI_API_KEY", "") or getattr(settings, "OPENAI_API_KEY", "")
        ai_base_url = os.getenv("AI_BASE_URL")
        ai_model = os.getenv("AI_MODEL", "gemini-1.5-flash")

        if ai_key:
            ai_result = cls._call_ai_orchestrator(
                query=raw_query,
                lang=detected_lang,
                analysis=analysis,
                mode=mode,
                api_key=ai_key,
                base_url=ai_base_url,
                model=ai_model
            )
            if ai_result:
                return ai_result

        # 4. High-Quality Offline Semantic Engine Fallback
        return cls._generate_offline(raw_query, detected_lang, analysis, mode)

    @classmethod
    def _handle_chinese_input(cls, query: str, mode: str) -> Dict[str, Any]:
        """
        Handles direct Chinese queries cleanly without translation corruption.
        """
        is_deep = (mode == "deep")
        exact_q = query.strip()
        
        high_queries = [
            f"{exact_q}日常",
            f"{exact_q}自拍",
            f"爆款{exact_q}",
            f"高赞{exact_q}"
        ]
        med_queries = [
            f"{exact_q}合集",
            f"{exact_q}推荐",
            f"{exact_q}热门",
            f"{exact_q}精选"
        ]
        broad_queries = [
            exact_q[:4] if len(exact_q) > 4 else exact_q
        ]

        all_queries = [exact_q] + high_queries + (med_queries if is_deep else med_queries[:2])
        scored_queries = []
        for idx, q in enumerate(all_queries):
            score = 98 if idx == 0 else (92 - idx * 2)
            scored_queries.append({"query": q, "score": max(50, score), "tier": "exact" if idx == 0 else "high"})

        return {
            "language": "zh",
            "original_query": query,
            "intent": "DIRECT_SEARCH",
            "semantic_entities": {"subject": [query]},
            "chinese_keywords": {
                "primary": [exact_q],
                "action": [],
                "clothing": [],
                "scene": [],
                "style": ["热门", "精选"]
            },
            "queries": {
                "exact": [exact_q],
                "high": high_queries[:3],
                "medium": med_queries[:3],
                "broad": broad_queries
            },
            "flat_queries": [item["query"] for item in scored_queries],
            "query_scores": scored_queries,
            "negative_keywords": cls.STANDARD_NEGATIVE_KEYWORDS
        }

    @classmethod
    def _generate_offline(
        cls,
        raw_query: str,
        lang: str,
        analysis: Dict[str, Any],
        mode: str
    ) -> Dict[str, Any]:
        """
        Deterministic, natural Douyin semantic generator based on deep domain patterns.
        """
        q_lower = raw_query.lower()
        entities = analysis.get("entities", {})

        primary_kw: List[str] = []
        clothing_kw: List[str] = []
        action_kw: List[str] = []
        scene_kw: List[str] = []
        style_kw: List[str] = []

        # Map entities to Chinese concepts
        has_girl = "gái xinh" in entities.get("subject", []) or any(w in q_lower for w in ["gái", "girl", "nữ", "hotgirl", "cô gái"])
        has_pijama = "pijama" in entities.get("clothing", []) or any(w in q_lower for w in ["pijama", "đồ ngủ", "pyjama", "pajamas"])
        has_che_mat = "che mặt" in entities.get("action", []) or any(w in q_lower for w in ["che mặt", "giấu mặt", "bịt mặt", "mask", "hiding", "cover"])
        has_dance = "nhảy múa" in entities.get("action", []) or any(w in q_lower for w in ["nhảy", "dance", "múa"])
        has_cook = "nấu ăn" in entities.get("action", []) or any(w in q_lower for w in ["nấu", "cook", "làm bánh", "ẩm thực", "ăn"])
        has_room = "trong phòng" in entities.get("scene", []) or any(w in q_lower for w in ["phòng", "room", "nhà", "giường"])
        has_cat = "thú cưng" in entities.get("subject", []) or any(w in q_lower for w in ["mèo", "cat", "cún", "chó"])
        has_car = "ô tô" in entities.get("subject", []) or any(w in q_lower for w in ["xe", "car", "ô tô", "siêu xe"])
        has_funny = "hài hước" in entities.get("appearance", []) or any(w in q_lower for w in ["hài", "funny", "cười", "bựa"])
        has_review = "review" in entities.get("action", []) or any(w in q_lower for w in ["review", "đánh giá", "ăn thử", "mở hộp", "đồ ăn"])

        # Populate keywords
        if has_girl:
            primary_kw.extend(cls.SEMANTIC_MAPPINGS["gai_xinh"]["primary"])
            style_kw.extend(cls.SEMANTIC_MAPPINGS["gai_xinh"]["style"])
        if has_pijama:
            clothing_kw.extend(cls.SEMANTIC_MAPPINGS["pijama"]["clothing"])
            action_kw.extend(cls.SEMANTIC_MAPPINGS["pijama"]["action"])
        if has_che_mat:
            action_kw.extend(cls.SEMANTIC_MAPPINGS["che_mat"]["action"])
            style_kw.extend(cls.SEMANTIC_MAPPINGS["che_mat"]["style"])
        if has_dance:
            action_kw.extend(cls.SEMANTIC_MAPPINGS["nhay"]["action"])
            style_kw.extend(cls.SEMANTIC_MAPPINGS["nhay"]["style"])
        if has_cook:
            action_kw.extend(cls.SEMANTIC_MAPPINGS["nau_an"]["action"])
            scene_kw.extend(cls.SEMANTIC_MAPPINGS["nau_an"]["scene"])
            style_kw.extend(cls.SEMANTIC_MAPPINGS["nau_an"]["style"])
        if has_room:
            scene_kw.extend(cls.SEMANTIC_MAPPINGS["trong_phong"]["scene"])
        if has_cat:
            primary_kw.extend(cls.SEMANTIC_MAPPINGS["meo"]["primary"])
            style_kw.extend(cls.SEMANTIC_MAPPINGS["meo"]["style"])
        if has_car:
            primary_kw.extend(cls.SEMANTIC_MAPPINGS["xe"]["primary"])
            action_kw.extend(cls.SEMANTIC_MAPPINGS["xe"]["action"])
        if has_funny:
            primary_kw.extend(cls.SEMANTIC_MAPPINGS["hai_huoc"]["primary"])
            style_kw.extend(cls.SEMANTIC_MAPPINGS["hai_huoc"]["style"])
        if has_review:
            primary_kw.extend(cls.SEMANTIC_MAPPINGS["review"]["primary"])
            action_kw.extend(cls.SEMANTIC_MAPPINGS["review"]["action"])
            style_kw.extend(cls.SEMANTIC_MAPPINGS["review"]["style"])

        # Fallback if no specific entity was triggered
        if not primary_kw and not action_kw and not clothing_kw:
            primary_kw = ["热门视频", "高赞精选", "抖音推荐"]

        # Deduplicate keyword groups
        primary_kw = list(dict.fromkeys(primary_kw))[:5]
        clothing_kw = list(dict.fromkeys(clothing_kw))[:4]
        action_kw = list(dict.fromkeys(action_kw))[:4]
        scene_kw = list(dict.fromkeys(scene_kw))[:4]
        style_kw = list(dict.fromkeys(style_kw))[:4]

        # Generate Douyin Natural Queries
        exact_queries: List[str] = []
        high_queries: List[str] = []
        med_queries: List[str] = []
        broad_queries: List[str] = []

        if has_girl and has_pijama and has_che_mat:
            exact_queries = ["美女穿睡衣遮脸"]
            high_queries = ["美女睡衣自拍", "高颜值女生睡衣", "漂亮女生穿睡衣", "美女睡衣捂脸"]
            med_queries = ["美女睡衣日常", "女生睡衣遮脸", "美女卧室睡衣", "美女睡衣自拍遮脸"]
            broad_queries = ["美女睡衣", "睡衣女孩", "睡衣自拍"]
        elif has_girl and has_pijama:
            exact_queries = ["美女穿睡衣", "美女睡衣自拍"]
            high_queries = ["高颜值女生睡衣", "漂亮女生穿睡衣", "美女睡衣日常"]
            med_queries = ["睡衣女孩", "女生睡衣穿搭", "美女卧室睡衣"]
            broad_queries = ["美女睡衣", "睡衣自拍"]
        elif has_girl and has_che_mat:
            exact_queries = ["美女遮脸自拍", "不露脸美女"]
            high_queries = ["美女捂脸", "高颜值女生遮脸", "氛围感遮脸美女"]
            med_queries = ["神秘感美女自拍", "挡脸小姐姐"]
            broad_queries = ["遮脸自拍", "不露脸"]
        elif has_review and has_cook:
            exact_queries = ["美食测评试吃", "街头美食探店"]
            high_queries = ["沉浸式美食测评", "深夜美食试吃", "爆款美食探店"]
            med_queries = ["真实美食测评", "特色小吃测评"]
            broad_queries = ["美食测评", "探店"]
        elif has_dance:
            exact_queries = ["抖音热门热舞", "热门卡点舞翻跳"]
            high_queries = ["美女跳舞名场面", "全网火爆踩点舞", "高颜值女团舞"]
            med_queries = ["变装卡点热舞", "律动慢摇舞", "一镜到底舞蹈"]
            broad_queries = ["抖音热舞", "卡点舞"]
        elif has_cook:
            exact_queries = ["家常菜美食教程", "沉浸式做饭"]
            high_queries = ["深夜食堂治愈做饭", "懒人快手美食", "人间烟火气做饭"]
            med_queries = ["一分钟美食快剪", "治愈系做饭Vlog"]
            broad_queries = ["做饭教程", "家常菜"]
        elif has_cat:
            exact_queries = ["可爱萌宠猫咪", "治愈系吸猫日常"]
            high_queries = ["搞笑沙雕小猫", "神仙颜值小猫"]
            med_queries = ["猫咪名场面", "小猫日常Vlog"]
            broad_queries = ["猫咪", "萌宠"]
        elif has_car:
            exact_queries = ["超跑声浪名场面", "沉浸式汽车测评"]
            high_queries = ["豪车开箱", "帅气超跑驾驶"]
            med_queries = ["汽车改装日常", "顶级跑车欣赏"]
            broad_queries = ["汽车", "超跑"]
        elif has_funny:
            exact_queries = ["爆笑反转短剧", "沙雕搞笑日常"]
            high_queries = ["幽默段子名场面", "笑到肚子疼的瞬间"]
            med_queries = ["戏精同事搞笑", "高能爆笑剪辑"]
            broad_queries = ["搞笑合集", "沙雕"]
        elif has_review:
            exact_queries = ["真实产品测评", "开箱测评体验"]
            high_queries = ["沉浸式开箱测评", "避坑指南测评"]
            med_queries = ["开箱日常", "真实体验测评"]
            broad_queries = ["测评", "开箱"]
        elif has_girl:
            exact_queries = ["美女", "高颜值女生", "漂亮女生"]
            high_queries = ["美女小姐姐", "心动女生日常", "气质女神"]
            med_queries = ["高颜值自拍", "氛围感美女"]
            broad_queries = ["美女", "高颜值"]
        else:
            exact_queries = [primary_kw[0] if primary_kw else "精选视频"]
            high_queries = [f"{k}日常" for k in primary_kw[:3]]
            med_queries = [f"{k}合集" for k in primary_kw[:3]]
            broad_queries = primary_kw[:2]

        # Combine into scored query objects
        all_scored: List[Dict[str, Any]] = []
        seen = set()

        for q in exact_queries:
            if q not in seen:
                seen.add(q)
                all_scored.append({"query": q, "score": 97, "tier": "exact", "reason": "核心精确意图"})
        for q in high_queries:
            if q not in seen:
                seen.add(q)
                all_scored.append({"query": q, "score": 91, "tier": "high", "reason": "高契合度搜索词"})
        for q in med_queries:
            if q not in seen:
                seen.add(q)
                all_scored.append({"query": q, "score": 82, "tier": "medium", "reason": "中等扩展相关词"})
        for q in broad_queries:
            if q not in seen:
                seen.add(q)
                all_scored.append({"query": q, "score": 65, "tier": "broad", "reason": "宽泛基础词"})

        limit = 25 if mode == "deep" else 15
        selected_scored = all_scored[:limit]

        return {
            "language": lang,
            "original_query": raw_query,
            "intent": analysis.get("intent", "VISUAL_CONTENT_SEARCH"),
            "semantic_entities": entities,
            "chinese_keywords": {
                "primary": primary_kw,
                "clothing": clothing_kw,
                "action": action_kw,
                "scene": scene_kw,
                "style": style_kw
            },
            "queries": {
                "exact": exact_queries,
                "high": high_queries,
                "medium": med_queries,
                "broad": broad_queries
            },
            "flat_queries": [item["query"] for item in selected_scored],
            "query_scores": selected_scored,
            "negative_keywords": cls.STANDARD_NEGATIVE_KEYWORDS
        }

    @classmethod
    def _call_ai_orchestrator(
        cls,
        query: str,
        lang: str,
        analysis: Dict[str, Any],
        mode: str,
        api_key: str,
        base_url: Optional[str] = None,
        model: str = "gemini-1.5-flash"
    ) -> Optional[Dict[str, Any]]:
        """
        Executes a single, robust AI request to extract entities and generate
        native Douyin Chinese search queries in one pass.
        """
        prompt = f"""
You are a Douyin (TikTok China) SEO and Search Algorithm specialist.
The user inputted a search query in {lang}: "{query}"

Task:
1. Understand the search intent (do NOT translate word-by-word).
2. Extract semantic entities (subject, appearance, clothing, action, scene, style).
3. Map to natural Chinese Douyin keywords (how native Chinese users actually search on Douyin).
4. Generate search queries categorized by priority:
   - exact (1-2 queries with ~95-100 score)
   - high (3-5 queries with ~88-94 score)
   - medium (3-5 queries with ~75-87 score)
   - broad (2-3 queries with ~50-74 score)
5. Generate negative keywords if needed (e.g. to filter ads/products).

Return ONLY valid JSON matching this schema:
{{
  "language": "{lang}",
  "original_query": "{query}",
  "intent": "visual_content_search",
  "semantic_entities": {{
    "subject": ["gái xinh"],
    "clothing": ["pijama"],
    "action": ["che mặt"]
  }},
  "chinese_keywords": {{
    "primary": ["美女", "高颜值女生"],
    "clothing": ["睡衣"],
    "action": ["遮脸", "捂脸"],
    "scene": ["卧室", "房间"],
    "style": ["自拍", "日常"]
  }},
  "queries": {{
    "exact": ["美女穿睡衣遮脸"],
    "high": ["美女睡衣自拍", "高颜值女生睡衣"],
    "medium": ["美女睡衣日常", "女生睡衣遮脸"],
    "broad": ["美女睡衣", "睡衣女孩"]
  }},
  "negative_keywords": ["广告", "商品", "店铺"]
}}
"""
        try:
            if "gemini" in model.lower() and not base_url:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
                }
                req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=12) as resp:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    txt = res_json["candidates"][0]["content"]["parts"][0]["text"]
            else:
                # OpenAI or custom base_url
                ep = (base_url or "https://api.openai.com/v1").rstrip("/") + "/chat/completions"
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2
                }
                req = urllib.request.Request(
                    ep,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
                )
                with urllib.request.urlopen(req, timeout=12) as resp:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    txt = res_json["choices"][0]["message"]["content"]

            # JSON Cleaning / Repair
            txt = re.sub(r"^```(?:json)?\s*", "", txt.strip(), flags=re.MULTILINE)
            txt = re.sub(r"```$", "", txt.strip(), flags=re.MULTILINE)
            parsed = json.loads(txt)

            # Flatten & assign scores
            all_scored = []
            seen = set()
            for tier, default_score in [("exact", 97), ("high", 91), ("medium", 82), ("broad", 65)]:
                for q in parsed.get("queries", {}).get(tier, []):
                    if q not in seen:
                        seen.add(q)
                        all_scored.append({"query": q, "score": default_score, "tier": tier})

            parsed["flat_queries"] = [item["query"] for item in all_scored]
            parsed["query_scores"] = all_scored
            if "negative_keywords" not in parsed or not parsed["negative_keywords"]:
                parsed["negative_keywords"] = cls.STANDARD_NEGATIVE_KEYWORDS

            return parsed
        except Exception as e:
            print(f"[ChineseQueryGenerator] AI error: {e}")
            return None
