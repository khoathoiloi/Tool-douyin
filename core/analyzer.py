"""
Core Module: AI Video & Content Analyzer for Douyin
Analyzes video ideas, descriptions, themes, or direct video URLs, and generates optimized Chinese keywords & hashtags for Douyin search algorithms.
"""

import json
import re
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional

DOUYIN_TAXONOMY = {
    "dance_hotgirl": {
        "name": "Nhảy / Vũ đạo / Gái xinh / Dance Cover",
        "keywords": ["抖音热舞", "热门卡点舞", "美女跳舞", "变装跳舞", "魔性舞蹈", "女团舞翻跳", "踩点热舞", "慢摇舞", "性感热舞"],
        "hashtags": ["#热舞", "#美女跳舞", "#卡点舞", "#翻跳", "#舞蹈", "#心动女嘉宾", "#变装"]
    },
    "drama_funny": {
        "name": "Hài hước / Drama / Tiểu phẩm",
        "keywords": ["搞笑短剧", "沙雕日常", "反转剧情", "爆笑名场面", "幽默段子", "戏精日常", "搞笑配音", "大冤种日常"],
        "hashtags": ["#搞笑", "#搞笑短剧", "#沙雕日常", "#笑死我了", "#反转", "#每日一笑", "#幽默"]
    },
    "story_emotion": {
        "name": "Tâm trạng / Cảm xúc / Chữa lành",
        "keywords": ["治愈系视频", "深夜情感", "扎心情感语录", "唯美治愈文案", "人间清醒", "人生感悟", "伤感文案", "治愈系风景"],
        "hashtags": ["#治愈", "#情感共鸣", "#深夜文案", "#人间烟火", "#治愈系风景", "#走心文案"]
    },
    "food_cooking": {
        "name": "Ẩm thực / Nấu ăn / Review đồ ăn",
        "keywords": ["家常菜做法", "深夜美食", "路边摊小吃", "治愈系做饭", "美食教程", "懒人快手菜", "街头美食", "特色小吃"],
        "hashtags": ["#美食", "#一人食", "#我的美食日记", "#街头小吃", "#学做菜", "#吃货日常"]
    },
    "beauty_fashion": {
        "name": "Làm đẹp / Thời trang / Makeup / Gái đẹp",
        "keywords": ["沉浸式护肤", "新手化妆教程", "变装卡点", "显瘦穿搭", "氛围感妆容", "平价好物分享", "高级感穿搭"],
        "hashtags": ["#变装", "#沉浸式护肤", "#每日穿搭", "#化妆教程", "#变美秘籍", "#秋冬穿搭"]
    },
    "tech_tools": {
        "name": "Công nghệ / Thủ thuật / AI / Tool",
        "keywords": ["实用黑科技", "电脑实用技巧", "AI神级工具", "高效办公神器", "手机隐藏功能", "黑科技软件", "生产力工具"],
        "hashtags": ["#黑科技", "#实用小技巧", "#办公神器", "#AI工具", "#效率提升", "#电脑技巧"]
    },
    "travel_scenery": {
        "name": "Du lịch / Phong cảnh / Thiên nhiên",
        "keywords": ["沉浸式旅行", "绝美风景大片", "小众旅游胜地", "治愈系风景壁纸", "旅行Vlog", "自驾游路线", "航拍视角"],
        "hashtags": ["#旅行", "#治愈系风景", "#带着抖音去旅行", "#航拍中国", "#风景壁纸", "#旅行推荐官"]
    },
    "pets_animals": {
        "name": "Thú cưng / Chó mèo dễ thương",
        "keywords": ["萌宠日常", "修猫咪日常", "成精的宠物", "治愈系萌宠", "狗狗搞笑瞬间", "猫咪日常", "宠物迷惑行为"],
        "hashtags": ["#萌宠", "#猫咪的迷惑行为", "#治愈系宠物", "#狗狗日常", "#可爱多", "#萌宠出道计划"]
    },
    "ecommerce_affiliate": {
        "name": "Bán hàng / Review sản phẩm / Hot Trend",
        "keywords": ["抖音爆款好物", "居家实用好物", "学生党必备", "开箱测评", "好物推荐种草", "高颜值好物", "踩雷测评"],
        "hashtags": ["#好物推荐", "#开箱", "#抖音好物年货节", "#居家好物", "#种草", "#测评"]
    },
    "fitness_workout": {
        "name": "Gym / Thể thao / Giảm cân",
        "keywords": ["居家减脂运动", "暴汗燃脂教程", "马甲线训练", "新手健身指南", "拉伸塑形", "高效瘦身"],
        "hashtags": ["#健身", "#减脂打卡", "#居家健身", "#瘦肚子", "#塑形"]
    },
    "military_aviation": {
        "name": "Quân sự / Máy bay / Vũ khí / Lịch sử",
        "keywords": ["战斗机起飞", "军用飞机大片", "米格战机", "空战名场面", "军事航空", "大国重器", "硬核军事"],
        "hashtags": ["#军事", "#战斗机", "#空军", "#硬核", "#军事科普"]
    }
}

class DouyinAIAnalyzer:
    def __init__(self, api_key: str = "", provider: str = "gemini"):
        self.api_key = api_key.strip()
        self.provider = provider.lower()

    def set_api_key(self, api_key: str, provider: str = "gemini"):
        self.api_key = api_key.strip()
        self.provider = provider.lower()

    def analyze_and_generate_prompts(
        self,
        input_text: str,
        niche_hint: Optional[str] = None,
        max_keywords: int = 8
    ) -> Dict[str, Any]:
        if not input_text.strip():
            return {
                "success": False,
                "error": "Vui lòng nhập mô tả nội dung hoặc chủ đề video."
            }

        if self.api_key:
            try:
                if self.provider == "gemini":
                    return self._call_gemini_ai(input_text, niche_hint, max_keywords)
                elif self.provider == "openai":
                    return self._call_openai_ai(input_text, niche_hint, max_keywords)
            except Exception as e:
                print(f"[Analyzer] API Call failed ({e}), falling back to Offline Engine.")

        return self._generate_offline_prompts(input_text, niche_hint, max_keywords)

    def analyze_video_url(
        self,
        video_url_or_text: str,
        scanner_instance = None,
        niche_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        from core.douyin_scanner import DouyinScanner
        scanner = scanner_instance or DouyinScanner()

        parsed_link = scanner.parse_video_link(video_url_or_text)
        if not parsed_link.get("success", False):
            return self.analyze_and_generate_prompts(video_url_or_text, niche_hint)

        video_title = parsed_link.get("title", "")
        video_author = parsed_link.get("author", "")
        hashtags = parsed_link.get("hashtags", [])

        summary_text = f"{video_title} (Tác giả: {video_author}) {' '.join(hashtags)}"

        analysis_result = self.analyze_and_generate_prompts(summary_text, niche_hint)
        analysis_result["parsed_video"] = parsed_link
        return analysis_result

    def _call_gemini_ai(self, input_text: str, niche_hint: Optional[str], max_keywords: int) -> Dict[str, Any]:
        prompt = f"""
Bạn là chuyên gia phân tích nội dung viral trên Douyin (TikTok Trung Quốc).
Nhiệm vụ: Phân tích nội dung/video dưới đây và tạo ra các từ khóa tìm kiếm tiếng Trung tối ưu nhất cho thuật toán Douyin.

Nội dung mô tả / Video:
{input_text}
Chủ đề gợi ý: {niche_hint or 'Tự động'}

Trả về JSON duy nhất với định dạng:
{{
  "main_query": "Từ khóa tìm kiếm chính bằng tiếng Trung",
  "keywords": ["từ_khóa_1", "từ_khóa_2", "từ_khóa_3", "từ_khóa_4", "từ_khóa_5"],
  "hashtags": ["#hashtag_1", "#hashtag_2", "#hashtag_3", "#hashtag_4"],
  "vietnamese_meaning": {{
    "main_query_vi": "Ý nghĩa tiếng Việt",
    "strategy_vi": "Chiến lược tìm kiếm trên Douyin"
  }}
}}
"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "responseMimeType": "application/json"
            }
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            res_body = json.loads(response.read().decode("utf-8"))
            content_text = res_body["candidates"][0]["content"]["parts"][0]["text"]
            content_text = re.sub(r"^```json\s*", "", content_text.strip(), flags=re.MULTILINE)
            content_text = re.sub(r"```$", "", content_text.strip(), flags=re.MULTILINE)
            result = json.loads(content_text)
            result["success"] = True
            result["source"] = "Gemini AI"
            return result

    def _call_openai_ai(self, input_text: str, niche_hint: Optional[str], max_keywords: int) -> Dict[str, Any]:
        url = "https://api.openai.com/v1/chat/completions"
        system_prompt = "You are a Douyin trend and Chinese search algorithm expert. Output raw JSON only."
        user_prompt = f"Analyze: {input_text}. Output JSON: main_query, keywords, hashtags, vietnamese_meaning (main_query_vi, strategy_vi)."
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            res_body = json.loads(response.read().decode("utf-8"))
            content_text = res_body["choices"][0]["message"]["content"]
            content_text = re.sub(r"^```json\s*", "", content_text.strip(), flags=re.MULTILINE)
            content_text = re.sub(r"```$", "", content_text.strip(), flags=re.MULTILINE)
            result = json.loads(content_text)
            result["success"] = True
            result["source"] = "OpenAI"
            return result

    def _generate_offline_prompts(
        self,
        input_text: str,
        niche_hint: Optional[str],
        max_keywords: int
    ) -> Dict[str, Any]:
        text_lower = input_text.lower()
        matched_key = "dance_hotgirl" # Default modern trend

        if niche_hint and niche_hint in DOUYIN_TAXONOMY:
            matched_key = niche_hint
        else:
            # 1. Dance / Hotgirl / Nhảy / Vũ đạo
            if any(w in text_lower for w in ["nhảy", "dance", "múa", "vũ đạo", "gái", "cô gái", "nữ", "xinh", "hot girl", "sexy", "body", "idol", "cover"]):
                matched_key = "dance_hotgirl"
            # 2. Military / Máy bay
            elif any(w in text_lower for w in ["mig", "máy bay", "quân sự", "vũ khí", "chiến đấu", "chiến cơ", "tiêm kích", "plane", "flight", "pilot"]):
                matched_key = "military_aviation"
            # 3. Food / Ẩm thực
            elif any(w in text_lower for w in ["ăn", "nấu", "món", "bếp", "bánh", "food", "cook", "quán", "vị"]):
                matched_key = "food_cooking"
            # 4. Drama / Hài kịch
            elif any(w in text_lower for w in ["hài", "cười", "troll", "tiểu phẩm", "drama", "tấu hài", "bựa"]):
                matched_key = "drama_funny"
            # 5. Tâm trạng
            elif any(w in text_lower for w in ["tâm trạng", "buồn", "cảm xúc", "tình yêu", "chữa lành", "triết lý", "sad"]):
                matched_key = "story_emotion"
            # 6. Làm đẹp
            elif any(w in text_lower for w in ["makeup", "trang điểm", "đẹp", "son", "quần áo", "outfit", "da", "thời trang"]):
                matched_key = "beauty_fashion"
            # 7. Công nghệ
            elif any(w in text_lower for w in ["công nghệ", "máy tính", "tool", "ai", "app", "thủ thuật", "phần mềm"]):
                matched_key = "tech_tools"
            # 8. Thú cưng
            elif any(w in text_lower for w in ["chó", "mèo", "pet", "thú cưng", "cute", "cún"]):
                matched_key = "pets_animals"
            # 9. Du lịch
            elif any(w in text_lower for w in ["du lịch", "phong cảnh", "núi", "biển", "cảnh đẹp", "travel", "vlog"]):
                matched_key = "travel_scenery"
            # 10. Review / Bán hàng
            elif any(w in text_lower for w in ["bán", "mua", "sản phẩm", "review", "đập hộp", "unboxing", "affiliate"]):
                matched_key = "ecommerce_affiliate"
            # 11. Gym
            elif any(w in text_lower for w in ["gym", "giảm cân", "tập luyện", "fitness", "workout"]):
                matched_key = "fitness_workout"

        niche_info = DOUYIN_TAXONOMY[matched_key]
        main_kw = niche_info["keywords"][0]
        keywords = niche_info["keywords"][:max_keywords]
        hashtags = niche_info["hashtags"]

        return {
            "success": True,
            "source": "Offline Intelligent Engine",
            "main_query": main_kw,
            "keywords": keywords,
            "hashtags": hashtags,
            "vietnamese_meaning": {
                "main_query_vi": f"Chủ đề: {niche_info['name']} (Từ khóa tìm kiếm: '{main_kw}')",
                "strategy_vi": f"Thuật toán Douyin sẽ ưu tiên các video viral thuộc cụm chủ đề {niche_info['name']} có tỷ lệ tương tác cao."
            }
        }
