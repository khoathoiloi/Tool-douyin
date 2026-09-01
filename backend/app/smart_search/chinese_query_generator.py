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

    # Comprehensive Semantic Mapping Table (Domain concepts -> Chinese Douyin keywords & idioms)
    SEMANTIC_MAPPINGS = {
        "gai_xinh": {
            "primary": ["美女", "高颜值女生", "漂亮女生", "美女小姐姐", "心动女生"],
            "style": ["日常", "自拍", "氛围感", "生活感", "颜值控"]
        },
        "trai_dep": {
            "primary": ["帅哥", "高颜值男生", "清爽帅哥", "氛围感帅哥", "小哥哥"],
            "style": ["日常", "穿搭", "变装", "自拍"]
        },
        "nu_sinh": {
            "primary": ["校花", "女学生", "清纯少女", "毕业季女声"],
            "clothing": ["校服", "毕业服", "学生装", "白裙"],
            "style": ["青春", "写真", "毕业季", "校园"]
        },
        "em_be": {
            "primary": ["人类幼崽", "萌娃", "可爱宝宝", "萌宝", "小女孩"],
            "style": ["治愈系", "超可爱", "搞笑萌娃", "日常", "萌宝日常"]
        },
        "chu_tich": {
            "primary": ["董事长", "总裁", "大老板", "霸道总裁"],
            "style": ["反转短剧", "微短剧", "打脸剧情", "名场面"]
        },
        "pijama": {
            "clothing": ["睡衣", "睡衣穿搭", "居家服", "可爱睡衣", "丝绸睡衣"],
            "action": ["穿睡衣", "睡衣自拍"]
        },
        "che_mat": {
            "action": ["遮脸", "捂脸", "不露脸", "挡脸", "手势遮脸"],
            "style": ["神秘感", "氛围感"]
        },
        "ao_dai": {
            "clothing": ["奥黛", "越南奥黛", "旗袍", "汉服", "古风", "白裙"],
            "style": ["国风", "优雅", "写真", "唯美"]
        },
        "bikini": {
            "clothing": ["比基尼", "泳装", "夏日穿搭", "泳衣"],
            "scene": ["海边", "沙滩", "海岛", "度假"],
            "style": ["夏日风", "氛围感", "写真"]
        },
        "do_dong": {
            "clothing": ["冬季穿搭", "大衣", "羽绒服", "高级感穿搭"],
            "style": ["秋冬穿搭", "帅气", "高级感", "保暖搭配"]
        },
        "do_gym": {
            "clothing": ["健身服", "瑜伽裤", "运动穿搭"],
            "action": ["减脂暴汗", "马甲线训练", "居家健身", "瘦肚子"],
            "style": ["自律", "燃脂", "健身打卡"]
        },
        "nhay": {
            "action": ["跳舞", "热舞", "卡点舞", "翻跳", "踩点舞", "慢摇"],
            "style": ["抖音热舞", "神仙舞蹈", "全网爆款", "卡点"]
        },
        "nau_an": {
            "action": ["做饭", "烹饪", "美食教程", "沉浸式做饭", "下厨", "烘焙", "做蛋糕"],
            "scene": ["厨房", "深夜食堂", "人间烟火气"],
            "style": ["治愈系", "家常菜", "懒人美食", "新手教程"]
        },
        "bien_hinh": {
            "action": ["变装", "化妆变美", "素颜vs全妆", "变身", "变装前后"],
            "style": ["惊艳变装", "卡点变装", "神级变装"]
        },
        "hat_cover": {
            "action": ["翻唱", "唱歌", "深情翻唱", "伤感翻唱"],
            "style": ["深夜emo", "走心歌曲", "治愈系音乐", "烟嗓"]
        },
        "review_food": {
            "primary": ["美食测评", "探店", "试吃"],
            "action": ["夜市小吃", "街头美食", "沉浸式试吃", "美食探店"],
            "style": ["真实测评", "吃货日常", "深夜食堂"]
        },
        "review_tech": {
            "primary": ["开箱测评", "数码新品", "科技"],
            "action": ["沉浸式开箱", "上手体验", "新机测评"],
            "style": ["避坑指南", "真实体验", "黑科技"]
        },
        "meo": {
            "primary": ["猫咪", "小猫", "萌宠", "可爱猫咪", "小奶猫"],
            "style": ["治愈", "搞笑", "萌宠日常", "吸猫"]
        },
        "cho": {
            "primary": ["狗狗", "金毛", "萌宠", "聪明狗狗"],
            "action": ["做家务", "懂事日常", "搞笑名场面"],
            "style": ["成精了", "治愈", "神仙狗狗"]
        },
        "xe": {
            "primary": ["汽车", "超跑", "豪车", "跑车", "声浪"],
            "action": ["直线加速", "声浪炸街", "试驾测评", "提车"],
            "style": ["速度与激情", "大片感"]
        },
        "hai_huoc": {
            "primary": ["搞笑", "沙雕", "爆笑", "幽默", "整蛊"],
            "style": ["沙雕日常", "神级反转", "今日份快乐", "闺蜜互坑"]
        },
        "phong_canh": {
            "primary": ["自然风景", "雪山", "壮丽风光", "绝美大自然"],
            "style": ["4K治愈", "大片壁纸", "航拍中国", "治愈系风景"]
        },
        "meo_vat": {
            "primary": ["实用小技巧", "生活小妙招", "生活技巧"],
            "style": ["超级实用", "后悔没早知道", "涨知识"]
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
            scored_queries.append({"query": q, "score": max(50, score), "tier": "exact" if idx == 0 else ("high" if idx <= 4 else "medium")})

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
        q_lower = raw_query.lower()
        entities = analysis.get("entities", {})

        primary_kw: List[str] = []
        clothing_kw: List[str] = []
        action_kw: List[str] = []
        scene_kw: List[str] = []
        style_kw: List[str] = []

        # Domain triggers
        has_baby = "em bé" in entities.get("subject", []) or any(w in q_lower for w in ["em bé", "bé gái", "bé trai", "baby", "trẻ con", "bé"])
        has_girl = not has_baby and ("gái xinh" in entities.get("subject", []) or any(w in q_lower for w in ["gái", "girl", "nữ", "hotgirl", "cô gái", "cô nàng"]))
        has_boy = "trai đẹp" in entities.get("subject", []) or any(w in q_lower for w in ["trai", "nam", "soái ca", "chàng trai"])
        has_student = "nữ sinh" in entities.get("subject", []) or any(w in q_lower for w in ["nữ sinh", "học sinh", "kỷ yếu", "sinh viên"])
        has_ceo = "chủ tịch" in entities.get("subject", []) or any(w in q_lower for w in ["chủ tịch", "tổng tài", "sếp", "giám đốc"])

        has_pijama = "pijama" in entities.get("clothing", []) or any(w in q_lower for w in ["pijama", "đồ ngủ", "pyjama", "pajamas"])
        has_aodai = "áo dài" in entities.get("clothing", []) or any(w in q_lower for w in ["áo dài", "áo dài trắng", "sườn xám"])
        has_bikini = "bikini" in entities.get("clothing", []) or any(w in q_lower for w in ["bikini", "áo tắm", "đồ bơi"])
        has_winter = "đồ đông" in entities.get("clothing", []) or any(w in q_lower for w in ["mùa đông", "áo khoác", "đồ đông", "áo len"])
        has_gym = "tập gym" in entities.get("action", []) or any(w in q_lower for w in ["gym", "giảm mỡ", "mỡ bụng", "workout", "giảm cân"])

        has_che_mat = "che mặt" in entities.get("action", []) or any(w in q_lower for w in ["che mặt", "giấu mặt", "bịt mặt", "mask", "hiding", "cover"])
        has_dance = "nhảy múa" in entities.get("action", []) or any(w in q_lower for w in ["nhảy", "dance", "múa", "vũ đạo", "nhạc hot"])
        has_cook = "nấu ăn" in entities.get("action", []) or any(w in q_lower for w in ["nấu", "cook", "làm bánh", "bánh sinh nhật", "ẩm thực", "ăn"])
        has_bienhinh = "biến hình" in entities.get("action", []) or any(w in q_lower for w in ["biến hình", "make up", "trang điểm", "lột xác"])
        has_sing = "hát cover" in entities.get("action", []) or any(w in q_lower for w in ["hát", "cover", "ca hát", "nhạc buồn"])
        has_food_review = any(w in q_lower for w in ["review đồ ăn", "đồ ăn đường phố", "ăn thử", "món ngon", "ẩm thực đêm"])
        has_tech_review = any(w in q_lower for w in ["đập hộp", "mở hộp", "điện thoại", "công nghệ", "review điện thoại"])
        has_lifehack = "mẹo vặt" in entities.get("action", []) or any(w in q_lower for w in ["mẹo vặt", "thủ thuật", "hữu ích", "mẹo cuộc sống"])

        has_cat = "mèo" in entities.get("subject", []) or any(w in q_lower for w in ["mèo", "cat", "mèo con", "mèo ngủ"])
        has_dog = "chó" in entities.get("subject", []) or any(w in q_lower for w in ["chó", "cún", "chó cưng", "làm việc nhà"])
        has_car = "siêu xe" in entities.get("subject", []) or any(w in q_lower for w in ["xe", "car", "ô tô", "siêu xe", "cao tốc", "tăng tốc"])
        has_nature = "núi tuyết" in entities.get("scene", []) or any(w in q_lower for w in ["núi tuyết", "phong cảnh", "thiên nhiên", "hùng vĩ", "tuyết"])
        has_funny = "hài hước" in entities.get("appearance", []) or any(w in q_lower for w in ["hài", "funny", "cười", "bựa", "troll", "bạn thân", "bể bụng"])
        has_drama = "drama" in entities.get("style", []) or any(w in q_lower for w in ["drama", "phim ngắn", "cái kết", "tiểu phẩm"])

        # Aggregate Keywords
        if has_baby:
            primary_kw.extend(cls.SEMANTIC_MAPPINGS["em_be"]["primary"])
            style_kw.extend(cls.SEMANTIC_MAPPINGS["em_be"]["style"])
        if has_girl:
            primary_kw.extend(cls.SEMANTIC_MAPPINGS["gai_xinh"]["primary"])
            style_kw.extend(cls.SEMANTIC_MAPPINGS["gai_xinh"]["style"])
        if has_boy:
            primary_kw.extend(cls.SEMANTIC_MAPPINGS["trai_dep"]["primary"])
            style_kw.extend(cls.SEMANTIC_MAPPINGS["trai_dep"]["style"])
        if has_student:
            primary_kw.extend(cls.SEMANTIC_MAPPINGS["nu_sinh"]["primary"])
            clothing_kw.extend(cls.SEMANTIC_MAPPINGS["nu_sinh"]["clothing"])
            style_kw.extend(cls.SEMANTIC_MAPPINGS["nu_sinh"]["style"])
        if has_ceo:
            primary_kw.extend(cls.SEMANTIC_MAPPINGS["chu_tich"]["primary"])
            style_kw.extend(cls.SEMANTIC_MAPPINGS["chu_tich"]["style"])
        if has_pijama:
            clothing_kw.extend(cls.SEMANTIC_MAPPINGS["pijama"]["clothing"])
            action_kw.extend(cls.SEMANTIC_MAPPINGS["pijama"]["action"])
        if has_aodai:
            clothing_kw.extend(cls.SEMANTIC_MAPPINGS["ao_dai"]["clothing"])
            style_kw.extend(cls.SEMANTIC_MAPPINGS["ao_dai"]["style"])
        if has_bikini:
            clothing_kw.extend(cls.SEMANTIC_MAPPINGS["bikini"]["clothing"])
            scene_kw.extend(cls.SEMANTIC_MAPPINGS["bikini"]["scene"])
            style_kw.extend(cls.SEMANTIC_MAPPINGS["bikini"]["style"])
        if has_winter:
            clothing_kw.extend(cls.SEMANTIC_MAPPINGS["do_dong"]["clothing"])
            style_kw.extend(cls.SEMANTIC_MAPPINGS["do_dong"]["style"])
        if has_gym:
            clothing_kw.extend(cls.SEMANTIC_MAPPINGS["do_gym"]["clothing"])
            action_kw.extend(cls.SEMANTIC_MAPPINGS["do_gym"]["action"])
            style_kw.extend(cls.SEMANTIC_MAPPINGS["do_gym"]["style"])
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
        if has_bienhinh:
            action_kw.extend(cls.SEMANTIC_MAPPINGS["bien_hinh"]["action"])
            style_kw.extend(cls.SEMANTIC_MAPPINGS["bien_hinh"]["style"])
        if has_sing:
            action_kw.extend(cls.SEMANTIC_MAPPINGS["hat_cover"]["action"])
            style_kw.extend(cls.SEMANTIC_MAPPINGS["hat_cover"]["style"])
        if has_food_review:
            primary_kw.extend(cls.SEMANTIC_MAPPINGS["review_food"]["primary"])
            action_kw.extend(cls.SEMANTIC_MAPPINGS["review_food"]["action"])
            style_kw.extend(cls.SEMANTIC_MAPPINGS["review_food"]["style"])
        if has_tech_review:
            primary_kw.extend(cls.SEMANTIC_MAPPINGS["review_tech"]["primary"])
            action_kw.extend(cls.SEMANTIC_MAPPINGS["review_tech"]["action"])
            style_kw.extend(cls.SEMANTIC_MAPPINGS["review_tech"]["style"])
        if has_cat:
            primary_kw.extend(cls.SEMANTIC_MAPPINGS["meo"]["primary"])
            style_kw.extend(cls.SEMANTIC_MAPPINGS["meo"]["style"])
        if has_dog:
            primary_kw.extend(cls.SEMANTIC_MAPPINGS["cho"]["primary"])
            action_kw.extend(cls.SEMANTIC_MAPPINGS["cho"]["action"])
            style_kw.extend(cls.SEMANTIC_MAPPINGS["cho"]["style"])
        if has_car:
            primary_kw.extend(cls.SEMANTIC_MAPPINGS["xe"]["primary"])
            action_kw.extend(cls.SEMANTIC_MAPPINGS["xe"]["action"])
            style_kw.extend(cls.SEMANTIC_MAPPINGS["xe"]["style"])
        if has_nature:
            primary_kw.extend(cls.SEMANTIC_MAPPINGS["phong_canh"]["primary"])
            style_kw.extend(cls.SEMANTIC_MAPPINGS["phong_canh"]["style"])
        if has_funny:
            primary_kw.extend(cls.SEMANTIC_MAPPINGS["hai_huoc"]["primary"])
            style_kw.extend(cls.SEMANTIC_MAPPINGS["hai_huoc"]["style"])
        if has_lifehack:
            primary_kw.extend(cls.SEMANTIC_MAPPINGS["meo_vat"]["primary"])
            style_kw.extend(cls.SEMANTIC_MAPPINGS["meo_vat"]["style"])

        if not primary_kw and not action_kw and not clothing_kw:
            primary_kw = ["热门视频", "高赞精选", "抖音推荐"]

        # Deduplicate
        primary_kw = list(dict.fromkeys(primary_kw))[:6]
        clothing_kw = list(dict.fromkeys(clothing_kw))[:5]
        action_kw = list(dict.fromkeys(action_kw))[:5]
        scene_kw = list(dict.fromkeys(scene_kw))[:4]
        style_kw = list(dict.fromkeys(style_kw))[:5]

        # Natural Douyin Queries Builder for specific domains
        exact_queries: List[str] = []
        high_queries: List[str] = []
        med_queries: List[str] = []
        broad_queries: List[str] = []

        # 1. gái xinh mặc pijama che mặt
        if has_girl and has_pijama and has_che_mat:
            exact_queries = ["美女穿睡衣遮脸"]
            high_queries = ["美女睡衣自拍", "高颜值女生睡衣", "漂亮女生穿睡衣", "美女睡衣捂脸"]
            med_queries = ["美女睡衣日常", "女生睡衣遮脸", "美女卧室睡衣", "美女睡衣自拍遮脸"]
            broad_queries = ["美女睡衣", "睡衣女孩", "睡衣自拍"]

        # 19. bé gái nhảy múa siêu đáng yêu (Must be before general girl/dance)
        elif has_baby:
            exact_queries = ["萌娃人类幼崽超可爱跳舞", "可爱小女孩跳舞名场面"]
            high_queries = ["治愈系萌宝翻跳", "人类幼崽搞笑跳舞", "小萌宝踩点跳舞"]
            med_queries = ["萌娃跳舞瞬间", "治愈宝宝日常", "可爱人类幼崽日常"]
            broad_queries = ["萌娃跳舞", "可爱宝宝", "人类幼崽"]

        # 2. cô gái nấu ăn trong bếp
        elif has_cook and (has_girl or "bếp" in q_lower or "kitchen" in q_lower):
            exact_queries = ["女生厨房做饭", "美女下厨日常"]
            high_queries = ["沉浸式厨房做饭", "治愈系做饭Vlog", "美女做家常菜"]
            med_queries = ["厨房烟火气美食", "一分钟家常菜", "一个人好好吃饭"]
            broad_queries = ["做饭教程", "厨房做饭", "家常菜"]

        # 3. gái xinh nhảy nhạc hot trend
        elif has_dance and (has_girl or "trend" in q_lower):
            exact_queries = ["美女跳舞热门卡点", "热门卡点舞翻跳"]
            high_queries = ["美女跳舞名场面", "高颜值女团舞", "全网爆款热舞", "踩点慢摇舞"]
            med_queries = ["变装卡点热舞", "丝滑舞蹈动作", "一镜到底直拍"]
            broad_queries = ["抖音热舞", "卡点舞", "热舞翻跳"]

        # 4. video mèo con dễ thương ngủ ngon
        elif has_cat and ("ngủ" in q_lower or "dễ thương" in q_lower or "sleep" in q_lower):
            exact_queries = ["可爱小猫睡觉", "萌宠猫咪日常"]
            high_queries = ["治愈系小奶猫", "猫咪睡觉名场面", "萌宠小猫治愈日常"]
            med_queries = ["吸猫日常Vlog", "神仙颜值小猫", "猫咪打呼噜"]
            broad_queries = ["猫咪", "萌宠", "小猫睡觉"]

        # 5. review đồ ăn đường phố đêm
        elif has_food_review or ("đường phố" in q_lower and "ăn" in q_lower):
            exact_queries = ["夜市路边摊美食测评", "街头美食探店"]
            high_queries = ["深夜食堂美食试吃", "沉浸式街头美食", "爆款特色小吃测评"]
            med_queries = ["真实美食探店", "路边摊人间烟火", "超下饭街头小吃"]
            broad_queries = ["美食测评", "街头美食", "夜市探店"]

        # 6. xe siêu xe tăng tốc trên đường cao tốc
        elif has_car and ("cao tốc" in q_lower or "tăng tốc" in q_lower or "speed" in q_lower):
            exact_queries = ["顶级超跑高速声浪", "超跑直线加速"]
            high_queries = ["声浪炸街名场面", "超跑飙车大片", "沉浸式超跑驾驶"]
            med_queries = ["豪车声浪测评", "顶级跑车狂飙", "超跑改装名场面"]
            broad_queries = ["超跑", "汽车加速", "超跑声浪"]

        # 7. hài hước troll bạn thân bể bụng
        elif has_funny and ("bạn" in q_lower or "troll" in q_lower or "bể bụng" in q_lower):
            exact_queries = ["整蛊搞笑闺蜜日常", "爆笑闺蜜互坑"]
            high_queries = ["沙雕日常名场面", "搞笑反转短剧", "笑到肚子疼的瞬间"]
            med_queries = ["大冤种朋友互坑", "戏精朋友搞笑", "今日份快乐源泉"]
            broad_queries = ["搞笑合集", "沙雕短剧", "整蛊搞笑"]

        # 8. hướng dẫn làm bánh sinh nhật tại nhà
        elif "bánh" in q_lower or "cake" in q_lower:
            exact_queries = ["家庭自制生日蛋糕教程", "新手做蛋糕教学"]
            high_queries = ["零失败烘焙教程", "生日蛋糕制作步骤", "懒人自制甜品蛋糕"]
            med_queries = ["看一遍就会做蛋糕", "治愈系自制蛋糕", "不用烤箱做蛋糕"]
            broad_queries = ["做蛋糕教程", "生日蛋糕", "烘焙教程"]

        # 9. nữ sinh mặc áo dài trắng chụp kỷ yếu
        elif has_student or has_aodai:
            exact_queries = ["白裙奥黛毕业季拍照", "清纯校花毕业照"]
            high_queries = ["唯美毕业季自拍", "越南奥黛写真", "白裙校园氛围感"]
            med_queries = ["青春校园拍照姿势", "唯美白裙少女", "毕业季纪念写真"]
            broad_queries = ["奥黛写真", "毕业季拍照", "校花自拍"]

        # 10. hot girl biến hình trước và sau khi trang điểm
        elif has_bienhinh:
            exact_queries = ["高颜值美女变装前vs变装后", "惊艳化妆变装名场面"]
            high_queries = ["素颜vs全妆变美", "变装卡点惊艳瞬间", "神级化妆换头术"]
            med_queries = ["氛围感妆容教程", "一秒变女神变装", "前后对比惊艳变装"]
            broad_queries = ["变装", "化妆前后", "变装卡点"]

        # 11. tập gym giảm mỡ bụng tại nhà cho nữ
        elif has_gym:
            exact_queries = ["女生居家瘦肚子暴汗燃脂", "居家减脂马甲线训练"]
            high_queries = ["新手女生居家健身", "暴汗燃脂高效瘦身", "7天高效瘦肚子"]
            med_queries = ["不用器械减脂动作", "马甲线养成计划", "懒人居家全身燃脂"]
            broad_queries = ["居家健身", "瘦肚子", "减脂训练"]

        # 12. phong cảnh thiên nhiên núi tuyết hùng vĩ
        elif has_nature:
            exact_queries = ["绝美壮丽雪山自然风光", "治愈系雪山大片"]
            high_queries = ["震撼自然风景4K", "航拍雪山绝美壁纸", "大自然治愈系风景"]
            med_queries = ["雪山日照金山名场面", "沉浸式看雪山", "旷世奇景自然大片"]
            broad_queries = ["雪山风光", "自然风景", "雪山大片"]

        # 13. mở hộp đập hộp điện thoại công nghệ mới nhất
        elif has_tech_review:
            exact_queries = ["最新旗舰手机沉浸式开箱", "数码科技新品开箱测评"]
            high_queries = ["手机真实上手体验", "开箱避坑指南测评", "旗舰手机深度测评"]
            med_queries = ["黑科技手机开箱", "数码好物真实测评", "手机拍照功能测评"]
            broad_queries = ["手机开箱", "数码测评", "科技开箱"]

        # 14. cô nàng mặc bikini tắm biển mùa hè
        elif has_bikini:
            exact_queries = ["夏日海边比基尼美女", "沙滩度假风穿搭"]
            high_queries = ["海边度假氛围感自拍", "阳光沙滩美女写真", "清凉夏日海边度假"]
            med_queries = ["海边绝美拍照姿势", "度假风海边自拍", "夏日心动海滩女生"]
            broad_queries = ["海边美女", "比基尼穿搭", "沙滩写真"]

        # 15. hát cover nhạc buồn tâm trạng đêm khuya
        elif has_sing:
            exact_queries = ["深夜伤感emo翻唱", "扎心烟嗓伤感歌曲"]
            high_queries = ["深夜治愈系唱歌", "走心情感歌曲翻唱", "开口跪神仙翻唱"]
            med_queries = ["一个人深夜听的歌", "伤感扎心语录歌曲", "治愈系晚安歌曲"]
            broad_queries = ["伤感翻唱", "深夜听歌", "歌曲翻唱"]

        # 16. thủ thuật mẹo vặt cuộc sống cực kỳ hữu ích
        elif has_lifehack:
            exact_queries = ["超级实用生活小妙招", "居家生活必备小技巧"]
            high_queries = ["后悔没早知道的实用技巧", "冷门但超实用技巧", "生活小妙招合集"]
            med_queries = ["家务省力神技巧", "聪明人都在用的小窍门", "生活实用黑科技"]
            broad_queries = ["生活小妙招", "实用技巧", "生活小技巧"]

        # 17. chó cưng thông minh giúp chủ làm việc nhà
        elif has_dog:
            exact_queries = ["成精的聪明狗狗帮做家务", "超聪明金毛懂事日常"]
            high_queries = ["萌宠狗狗神仙操作", "狗狗治愈懂事瞬间", "聪明狗狗名场面"]
            med_queries = ["懂事的狗狗惹人爱", "金毛暖心日常", "成精的宠物狗"]
            broad_queries = ["聪明狗狗", "狗狗日常", "萌宠家务"]

        # 18. thời trang phối đồ nam ngầu mùa đông
        elif has_winter and (has_boy or "nam" in q_lower or "men" in q_lower):
            exact_queries = ["帅气男生冬季高级感穿搭", "男生秋冬氛围感穿搭"]
            high_queries = ["潮流男生保暖穿搭", "高级感男装搭配技巧", "男生韩系冬季穿搭"]
            med_queries = ["显高显瘦男士穿搭", "干净清爽男生穿搭", "冬季男生百搭外套"]
            broad_queries = ["男生穿搭", "冬季穿搭", "男装搭配"]

        # 20. phim ngắn drama chủ tịch giả vèo và cái kết
        elif has_ceo or has_drama:
            exact_queries = ["董事长低调假装穷人短剧", "剧情反转打脸短剧"]
            high_queries = ["大结局神级反转微短剧", "霸道总裁逆袭短剧", "隐藏身份总裁短剧"]
            med_queries = ["爆款热门微短剧合集", "爽文逆袭打脸名场面", "狗血剧情反转短剧"]
            broad_queries = ["总裁短剧", "反转短剧", "微短剧"]

        # Generic / Short queries (e.g. "gái xinh")
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

            txt = re.sub(r"^```(?:json)?\s*", "", txt.strip(), flags=re.MULTILINE)
            txt = re.sub(r"```$", "", txt.strip(), flags=re.MULTILINE)
            parsed = json.loads(txt)

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
