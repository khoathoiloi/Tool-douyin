import unittest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.smart_search.language_detector import LanguageDetector
from backend.app.smart_search.vietnamese_query_engine import VietnameseQueryEngine
from backend.app.smart_search.chinese_query_generator import ChineseQueryGenerator
from backend.app.smart_search.search_cache import SearchCache
from backend.app.smart_search.smart_search_service import SmartSearchService

class TestSmartSearchPipeline(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        SearchCache.clear()

    # 1. Test Language Detection
    def test_language_detection(self):
        self.assertEqual(LanguageDetector.detect("gái xinh mặc pijama che mặt"), "vi")
        self.assertEqual(LanguageDetector.detect("cô gái nấu ăn"), "vi")
        self.assertEqual(LanguageDetector.detect("美女睡衣"), "zh")
        self.assertEqual(LanguageDetector.detect("抖音热门舞蹈"), "zh")
        self.assertEqual(LanguageDetector.detect("beautiful girl wearing pajamas"), "en")
        self.assertEqual(LanguageDetector.detect("cute cat playing"), "en")

    # 2. Test 1: Complex Vietnamese Input
    def test_complex_vietnamese_query(self):
        q = "gái xinh mặc pijama che mặt"
        result = ChineseQueryGenerator.generate(q)
        self.assertEqual(result["language"], "vi")
        self.assertIn("exact", result["queries"])
        self.assertTrue(len(result["flat_queries"]) >= 5)

        # Must generate relevant keywords
        self.assertIn("美女", result["chinese_keywords"]["primary"])
        self.assertIn("睡衣", result["chinese_keywords"]["clothing"])
        self.assertIn("遮脸", result["chinese_keywords"]["action"])

        # Check exact and high queries
        flat = result["flat_queries"]
        self.assertTrue(any("美女" in item and "睡衣" in item for item in flat))
        self.assertTrue(any("遮脸" in item or "自拍" in item for item in flat))

    # 3. Test 2: Direct Chinese Query
    def test_direct_chinese_query(self):
        q = "美女睡衣"
        result = ChineseQueryGenerator.generate(q)
        self.assertEqual(result["language"], "zh")
        self.assertEqual(result["queries"]["exact"][0], "美女睡衣")
        self.assertIn("美女睡衣", result["flat_queries"])

    # 4. Test 3: English Input
    def test_english_query(self):
        q = "beautiful girl wearing pajamas"
        result = ChineseQueryGenerator.generate(q)
        self.assertEqual(result["language"], "en")
        self.assertTrue(len(result["flat_queries"]) >= 3)
        self.assertTrue(any("美女" in item or "睡衣" in item for item in result["flat_queries"]))

    # 5. Test 4: Short Vietnamese Input
    def test_short_vietnamese_query(self):
        q = "gái xinh"
        result = ChineseQueryGenerator.generate(q)
        self.assertEqual(result["language"], "vi")
        self.assertIn("美女", result["chinese_keywords"]["primary"])
        # Should not produce overly long sentences
        for item in result["flat_queries"]:
            self.assertTrue(len(item) <= 15)

    # 6. Test 5: Ambiguous Query (Graceful Fallback)
    def test_ambiguous_query(self):
        q = "video đẹp"
        result = ChineseQueryGenerator.generate(q)
        self.assertTrue(len(result["flat_queries"]) > 0)
        self.assertNotIn("error", result)

    # 7. Test Domain Queries
    def test_domain_queries(self):
        domains = [
            ("cô gái nấu ăn", "做饭"),
            ("video hài", "搞笑"),
            ("mèo dễ thương", "猫咪"),
            ("xe ô tô", "汽车"),
            ("review đồ ăn", "测评")
        ]
        for query_str, expected_kw in domains:
            res = ChineseQueryGenerator.generate(query_str)
            all_generated = " ".join(res["flat_queries"]) + " " + " ".join(res["chinese_keywords"]["primary"]) + " " + " ".join(res["chinese_keywords"]["action"])
            self.assertTrue(expected_kw in all_generated, f"Expected {expected_kw} for query '{query_str}'")

    # 8. Test Search Cache
    def test_search_cache(self):
        SearchCache.set("gái xinh", {"test": "data"}, "vi", "normal", ttl_seconds=60)
        cached = SearchCache.get("gái xinh", "vi", "normal")
        self.assertIsNotNone(cached)
        self.assertEqual(cached.get("test"), "data")

    # 9. Test API Endpoints
    def test_api_translate_endpoint(self):
        resp = self.client.post("/api/v1/query/translate", json={
            "query": "gái xinh mặc pijama che mặt",
            "language": "auto",
            "mode": "normal"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["detected_language"], "vi")
        self.assertTrue(len(data["flat_queries"]) > 0)
        self.assertTrue(len(data["query_scores"]) > 0)

    def test_api_smart_search_endpoint(self):
        resp = self.client.post("/api/v1/search/smart", json={
            "query": "gái xinh mặc pijama che mặt",
            "language": "auto",
            "mode": "normal"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("results", data)
        self.assertTrue(data["results_count"] > 0)
        self.assertIn("score", data["results"][0])
        self.assertIn("url", data["results"][0])

if __name__ == "__main__":
    unittest.main()

