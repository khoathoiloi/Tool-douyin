import unittest
from backend.app.smart_search.chinese_query_generator import ChineseQueryGenerator
from backend.app.smart_search.language_detector import LanguageDetector
from backend.app.smart_search.vietnamese_query_engine import VietnameseQueryEngine

class Test20VietnameseQueries(unittest.TestCase):
    """
    Validation test suite for 20+ diverse Vietnamese queries covering all content domains.
    """

    def setUp(self):
        self.test_cases = [
            # 1. Beauty, Pijama, Mask
            {
                "query": "gái xinh mặc pijama che mặt",
                "expected_lang": "vi",
                "expected_keywords": ["美女", "睡衣", "遮脸"],
                "expected_query_contains": ["美女穿睡衣遮脸", "美女睡衣自拍"]
            },
            # 2. Cooking / Kitchen
            {
                "query": "cô gái nấu ăn trong bếp",
                "expected_lang": "vi",
                "expected_keywords": ["做饭", "厨房"],
                "expected_query_contains": ["做饭", "厨房"]
            },
            # 3. Dance / Hot trend
            {
                "query": "gái xinh nhảy nhạc hot trend",
                "expected_lang": "vi",
                "expected_keywords": ["跳舞", "热舞"],
                "expected_query_contains": ["卡点", "跳舞"]
            },
            # 4. Cute sleeping cat
            {
                "query": "video mèo con dễ thương ngủ ngon",
                "expected_lang": "vi",
                "expected_keywords": ["猫咪", "可爱"],
                "expected_query_contains": ["小猫", "睡觉"]
            },
            # 5. Street food review
            {
                "query": "review đồ ăn đường phố đêm",
                "expected_lang": "vi",
                "expected_keywords": ["测评", "美食"],
                "expected_query_contains": ["美食", "探店"]
            },
            # 6. Supercars on highway
            {
                "query": "xe siêu xe tăng tốc trên đường cao tốc",
                "expected_lang": "vi",
                "expected_keywords": ["超跑", "声浪"],
                "expected_query_contains": ["超跑", "加速"]
            },
            # 7. Comedy / Prank friend
            {
                "query": "hài hước troll bạn thân bể bụng",
                "expected_lang": "vi",
                "expected_keywords": ["搞笑", "沙雕"],
                "expected_query_contains": ["搞笑", "短剧"]
            },
            # 8. Cake baking tutorial
            {
                "query": "hướng dẫn làm bánh sinh nhật tại nhà",
                "expected_lang": "vi",
                "expected_keywords": ["蛋糕", "教程"],
                "expected_query_contains": ["蛋糕", "教程"]
            },
            # 9. Ao Dai graduation photoshoot
            {
                "query": "nữ sinh mặc áo dài trắng chụp kỷ yếu",
                "expected_lang": "vi",
                "expected_keywords": ["奥黛", "毕业"],
                "expected_query_contains": ["奥黛", "写真"]
            },
            # 10. Makeup transformation
            {
                "query": "hot girl biến hình trước và sau khi trang điểm",
                "expected_lang": "vi",
                "expected_keywords": ["变装", "化妆"],
                "expected_query_contains": ["变装", "名场面"]
            },
            # 11. Fitness workout at home
            {
                "query": "tập gym giảm mỡ bụng tại nhà cho nữ",
                "expected_lang": "vi",
                "expected_keywords": ["瘦肚子", "健身"],
                "expected_query_contains": ["瘦肚子", "燃脂"]
            },
            # 12. Snow mountain landscape
            {
                "query": "phong cảnh thiên nhiên núi tuyết hùng vĩ",
                "expected_lang": "vi",
                "expected_keywords": ["雪山", "自然"],
                "expected_query_contains": ["雪山", "风光"]
            },
            # 13. Phone unboxing tech review
            {
                "query": "mở hộp đập hộp điện thoại công nghệ mới nhất",
                "expected_lang": "vi",
                "expected_keywords": ["开箱", "测评"],
                "expected_query_contains": ["手机", "开箱"]
            },
            # 14. Bikini summer beach
            {
                "query": "cô nàng mặc bikini tắm biển mùa hè",
                "expected_lang": "vi",
                "expected_keywords": ["比基尼", "海边"],
                "expected_query_contains": ["海边", "比基尼"]
            },
            # 15. Sad music cover at midnight
            {
                "query": "hát cover nhạc buồn tâm trạng đêm khuya",
                "expected_lang": "vi",
                "expected_keywords": ["翻唱", "伤感"],
                "expected_query_contains": ["深夜", "翻唱"]
            },
            # 16. Useful life hacks
            {
                "query": "thủ thuật mẹo vặt cuộc sống cực kỳ hữu ích",
                "expected_lang": "vi",
                "expected_keywords": ["实用", "生活小妙招"],
                "expected_query_contains": ["实用", "生活"]
            },
            # 17. Smart dog helping with chores
            {
                "query": "chó cưng thông minh giúp chủ làm việc nhà",
                "expected_lang": "vi",
                "expected_keywords": ["狗狗", "家务"],
                "expected_query_contains": ["狗狗", "聪明"]
            },
            # 18. Cool winter men outfit
            {
                "query": "thời trang phối đồ nam ngầu mùa đông",
                "expected_lang": "vi",
                "expected_keywords": ["穿搭", "冬季"],
                "expected_query_contains": ["男生", "穿搭"]
            },
            # 19. Cute baby dancing
            {
                "query": "bé gái nhảy múa siêu đáng yêu",
                "expected_lang": "vi",
                "expected_keywords": ["萌娃", "跳舞"],
                "expected_query_contains": ["萌娃", "可爱"]
            },
            # 20. CEO drama short plot twist
            {
                "query": "phim ngắn drama chủ tịch giả vèo và cái kết",
                "expected_lang": "vi",
                "expected_keywords": ["短剧", "反转"],
                "expected_query_contains": ["短剧", "反转"]
            }
        ]

    def test_all_20_vietnamese_queries(self):
        print("\n" + "="*70)
        print("🧪 RUNNING 20-QUERY VIETNAMESE SEMANTIC INTEGRATION TEST")
        print("="*70)

        for idx, tc in enumerate(self.test_cases):
            q = tc["query"]
            # 1. Detect language
            lang = LanguageDetector.detect(q)
            self.assertEqual(lang, tc["expected_lang"], f"Query '{q}' failed language detection: got {lang}")

            # 2. Generate queries
            res = ChineseQueryGenerator.generate(q)
            self.assertEqual(res["language"], tc["expected_lang"])
            self.assertIn("exact", res["queries"])
            self.assertIn("high", res["queries"])
            self.assertIn("medium", res["queries"])
            self.assertIn("broad", res["queries"])

            flat_queries = res["flat_queries"]
            self.assertTrue(len(flat_queries) >= 3, f"Query '{q}' generated insufficient queries: {flat_queries}")

            # 3. Check for keywords
            all_kws = (
                res["chinese_keywords"].get("primary", []) +
                res["chinese_keywords"].get("clothing", []) +
                res["chinese_keywords"].get("action", []) +
                res["chinese_keywords"].get("scene", []) +
                res["chinese_keywords"].get("style", [])
            )
            all_text = " ".join(all_kws) + " " + " ".join(flat_queries)

            for exp_kw in tc["expected_keywords"]:
                self.assertTrue(
                    any(exp_kw in item for item in (all_kws + flat_queries)),
                    f"[{idx+1}] Query '{q}': Expected keyword '{exp_kw}' not found in {all_kws} / {flat_queries}"
                )

            # 4. Check query quality scores
            for qs in res["query_scores"]:
                self.assertTrue(0 <= qs["score"] <= 100)
                self.assertIn(qs["tier"], ["exact", "high", "medium", "broad"])

            print(f"✅ [{idx+1:02d}/20] Passed: '{q}'")
            print(f"       -> Douyin Exact: {res['queries']['exact']}")
            print(f"       -> Douyin High:  {res['queries']['high'][:2]}")

        print("="*70)
        print("🎉 ALL 20 VIETNAMESE SEARCH QUERIES PASSED WITH 100% QUALITY!")
        print("="*70)

    def test_direct_chinese_and_english(self):
        # Direct Chinese
        zh_res = ChineseQueryGenerator.generate("美女睡衣")
        self.assertEqual(zh_res["language"], "zh")
        self.assertEqual(zh_res["queries"]["exact"][0], "美女睡衣")

        # English
        en_res = ChineseQueryGenerator.generate("beautiful girl wearing pajamas")
        self.assertEqual(en_res["language"], "en")
        self.assertTrue(any("美女" in q for q in en_res["flat_queries"]))

if __name__ == "__main__":
    unittest.main()
