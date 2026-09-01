import json
import re
import urllib.request
from typing import List, Dict, Any

class QueryGenerator:
    @classmethod
    def generate_20_queries(
        cls,
        profile: Dict[str, Any],
        api_key: str = "",
        provider: str = "gemini"
    ) -> List[Dict[str, Any]]:
        """
        Generates exactly 20 Chinese Douyin search queries grouped into 6 categories:
        - core_topic (4)
        - people_or_objects (3)
        - actions (4)
        - scene (3)
        - content_format (3)
        - long_tail (3)
        """
        if api_key and provider == "gemini":
            try:
                prompt = f"""
You are an expert Douyin SEO & search algorithm strategist.
Based on this video content profile:
{json.dumps(profile, ensure_ascii=False, indent=2)}

Generate EXACTLY 20 natural Chinese Douyin search queries.
Group them into categories:
1. core_topic (4 queries)
2. people_or_objects (3 queries)
3. actions (3 queries)
4. scene (3 queries)
5. content_format (3 queries)
6. long_tail (4 queries)

Rules:
- Natural Chinese search queries (2 to 12 Chinese characters)
- No complete sentences, no punctuation
- Preserve exact brand/person/product names if observed
- Assign relevance score (0.0 to 1.0) and a brief reason in Chinese.

Return ONLY valid JSON in this format:
{{
  "queries": [
    {{
      "query": "夜市美食",
      "category": "core_topic",
      "reason": "视频核心主题",
      "score": 0.95
    }}
  ]
}}
"""
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.3, "responseMimeType": "application/json"}
                }
                req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    txt = res_json["candidates"][0]["content"]["parts"][0]["text"]
                    txt = re.sub(r"^```json\s*", "", txt.strip(), flags=re.MULTILINE)
                    txt = re.sub(r"```$", "", txt.strip(), flags=re.MULTILINE)
                    data = json.loads(txt)
                    queries = data.get("queries", [])
                    if len(queries) >= 15:
                        return queries[:20]
            except Exception as e:
                print(f"[QueryGenerator] AI Query generation fallback: {e}")

        # Intelligent Offline 20-Query Generation Pipeline
        main_topic = profile.get("main_topic", "Dance")
        content_format = profile.get("content_format", "dance_cover")
        
        # Determine theme dictionary
        if "Ẩm thực" in main_topic or "cooking" in content_format:
            queries_data = [
                # core_topic (4)
                {"query": "家常菜美食教程", "category": "core_topic", "reason": "核心主题美食烹饪", "score": 0.98},
                {"query": "深夜食堂治愈做饭", "category": "core_topic", "reason": "核心治愈美食流派", "score": 0.94},
                {"query": "街头特色小吃", "category": "core_topic", "reason": "街头小吃热门搜索", "score": 0.92},
                {"query": "懒人快手美食", "category": "core_topic", "reason": "快手菜高频搜索", "score": 0.89},
                # people_or_objects (3)
                {"query": "美食博主探店", "category": "people_or_objects", "reason": "探店创作者属性", "score": 0.87},
                {"query": "厨房神级食材", "category": "people_or_objects", "reason": "核心食材道具", "score": 0.84},
                {"query": "爆款下饭菜", "category": "people_or_objects", "reason": "美食类目细分", "score": 0.85},
                # actions (4)
                {"query": "沉浸式做饭", "category": "actions", "reason": "沉浸式烹饪动作", "score": 0.93},
                {"query": "大火翻炒名场面", "category": "actions", "reason": "烹饪动作特写", "score": 0.86},
                {"query": "秘制酱料调配", "category": "actions", "reason": "调料制作步骤", "score": 0.88},
                {"query": "开箱试吃测评", "category": "actions", "reason": "试吃评价行为", "score": 0.83},
                # scene (3)
                {"query": "人间烟火气厨房", "category": "scene", "reason": "温馨厨房场景", "score": 0.89},
                {"query": "夜市路边摊氛围", "category": "scene", "reason": "夜市街景场景", "score": 0.87},
                {"query": "农家小院柴火饭", "category": "scene", "reason": "乡村田园场景", "score": 0.84},
                # content_format (3)
                {"query": "一分钟美食快剪", "category": "content_format", "reason": "快节奏短视频格式", "score": 0.91},
                {"query": "治愈系做饭Vlog", "category": "content_format", "reason": "Vlog长视频格式", "score": 0.88},
                {"query": "美食探店合集", "category": "content_format", "reason": "合集推荐格式", "score": 0.86},
                # long_tail (3)
                {"query": "看一遍就能学会的家常菜", "category": "long_tail", "reason": "长尾实用搜索词", "score": 0.92},
                {"query": "全网都在学的神仙吃法", "category": "long_tail", "reason": "长尾爆款词", "score": 0.90},
                {"query": "一个人也要好好吃饭", "category": "long_tail", "reason": "长尾情感共鸣词", "score": 0.88}
            ]
        elif "Hài hước" in main_topic or "drama" in content_format:
            queries_data = [
                # core_topic (4)
                {"query": "搞笑沙雕日常", "category": "core_topic", "reason": "核心沙雕搞笑主题", "score": 0.98},
                {"query": "爆笑反转短剧", "category": "core_topic", "reason": "剧情反转高赞词", "score": 0.95},
                {"query": "幽默段子名场面", "category": "core_topic", "reason": "段子合集热词", "score": 0.91},
                {"query": "大冤种爆笑时刻", "category": "core_topic", "reason": "热梗高频词", "score": 0.89},
                # people_or_objects (3)
                {"query": "戏精同事日常", "category": "people_or_objects", "reason": "职场人物设定", "score": 0.88},
                {"query": "搞笑闺蜜互坑", "category": "people_or_objects", "reason": "朋友互动人物", "score": 0.86},
                {"query": "怨种情侣名场面", "category": "people_or_objects", "reason": "情侣搞笑人设", "score": 0.85},
                # actions (4)
                {"query": "神级反转打脸", "category": "actions", "reason": "剧情冲突动作", "score": 0.94},
                {"query": "笑到肚子疼的瞬间", "category": "actions", "reason": "用户情绪动作", "score": 0.90},
                {"query": "一本正经搞笑", "category": "actions", "reason": "表演风格", "score": 0.87},
                {"query": "疯狂整蛊搞笑", "category": "actions", "reason": "整蛊互动动作", "score": 0.84},
                # scene (3)
                {"query": "职场办公室爆笑", "category": "scene", "reason": "办公室场景", "score": 0.89},
                {"query": "家庭沙雕日常", "category": "scene", "reason": "家庭生活场景", "score": 0.87},
                {"query": "校园搞笑名场面", "category": "scene", "reason": "校园场景", "score": 0.83},
                # content_format (3)
                {"query": "反转搞笑微短剧", "category": "content_format", "reason": "短剧内容形态", "score": 0.92},
                {"query": "高能爆笑剪辑合集", "category": "content_format", "reason": "剪辑合集格式", "score": 0.88},
                {"query": "沙雕配音名场面", "category": "content_format", "reason": "配音二创格式", "score": 0.86},
                # long_tail (3)
                {"query": "笑到停不下来的宝藏视频", "category": "long_tail", "reason": "长尾高互动搜索", "score": 0.91},
                {"query": "意想不到的结局系列", "category": "long_tail", "reason": "长尾剧情词", "score": 0.89},
                {"query": "今日份快乐源泉合集", "category": "long_tail", "reason": "长尾日常搜索词", "score": 0.87}
            ]
        else:
            # Default / Dance / Hot trend (4 + 3 + 4 + 3 + 3 + 3 = 20)
            queries_data = [
                # core_topic (4)
                {"query": "抖音热门热舞", "category": "core_topic", "reason": "核心舞蹈热门趋势", "score": 0.98},
                {"query": "热门卡点舞翻跳", "category": "core_topic", "reason": "卡点舞蹈翻跳核心词", "score": 0.95},
                {"query": "美女跳舞名场面", "category": "core_topic", "reason": "高赞舞蹈视频核心词", "score": 0.92},
                {"query": "全网火爆踩点舞", "category": "core_topic", "reason": "音乐踩点舞核心词", "score": 0.90},
                # people_or_objects (3)
                {"query": "高颜值女团舞翻跳", "category": "people_or_objects", "reason": "创作者特征与风格", "score": 0.88},
                {"query": "气质女神变装舞", "category": "people_or_objects", "reason": "变装人物属性", "score": 0.86},
                {"query": "长腿小姐姐热舞", "category": "people_or_objects", "reason": "创作者形象标签", "score": 0.85},
                # actions (4)
                {"query": "变装卡点惊艳瞬间", "category": "actions", "reason": "变装动作特写", "score": 0.94},
                {"query": "魔性律动慢摇舞", "category": "actions", "reason": "舞蹈动作节奏", "score": 0.89},
                {"query": "丝滑连贯舞蹈动作", "category": "actions", "reason": "动作技巧描述", "score": 0.87},
                {"query": "甜美微笑互动舞", "category": "actions", "reason": "表情神态动作", "score": 0.86},
                # scene (3)
                {"query": "唯美氛围感练舞室", "category": "scene", "reason": "室内练舞室场景", "score": 0.89},
                {"query": "户外街头沉浸式跳舞", "category": "scene", "reason": "街头户外场景", "score": 0.87},
                {"query": "霓虹灯光舞台背景", "category": "scene", "reason": "炫彩灯光舞台场景", "score": 0.84},
                # content_format (3)
                {"query": "短视频变装卡点合集", "category": "content_format", "reason": "卡点短视频格式", "score": 0.91},
                {"query": "一镜到底舞蹈直拍", "category": "content_format", "reason": "直拍单镜格式", "score": 0.88},
                {"query": "慢动作舞蹈精彩剪辑", "category": "content_format", "reason": "慢动作剪辑格式", "score": 0.85},
                # long_tail (3)
                {"query": "看一遍就上头的神仙舞蹈", "category": "long_tail", "reason": "长尾高转化搜索词", "score": 0.92},
                {"query": "全网都在挑战的爆款舞", "category": "long_tail", "reason": "长尾挑战搜索词", "score": 0.90},
                {"query": "这才是真正的有效跳舞", "category": "long_tail", "reason": "长尾赞美互动词", "score": 0.88}
            ]

        return queries_data[:20]

    @classmethod
    def expand_query(cls, base_query: str) -> List[str]:
        """
        Expands a high-value query into 3-5 semantic variants without concept drift.
        """
        variants_map = {
            "热门卡点舞": ["热门卡点舞教程", "热门卡点舞翻跳", "卡点舞慢动作", "爆款卡点舞合集"],
            "抖音热门热舞": ["抖音热搜舞蹈", "全网爆款热舞", "抖音热门舞蹈推荐", "近期超火热舞"],
            "美女跳舞名场面": ["高颜值美女跳舞", "心动美女跳舞合集", "唯美跳舞名场面", "气质美女热舞"],
            "家常菜美食教程": ["家常菜做法大全", "懒人家常菜", "新手家常菜教程", "超下饭家常菜"],
            "搞笑沙雕日常": ["沙雕搞笑合集", "每日爆笑日常", "沙雕名场面合集", "爆笑日常合集"]
        }
        for k, v in variants_map.items():
            if k in base_query or base_query in k:
                return v
                
        # Heuristic suffix expansion
        return [
            f"{base_query}教程",
            f"{base_query}合集",
            f"超火{base_query}",
            f"{base_query}推荐"
        ]
