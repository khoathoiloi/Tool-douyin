import asyncio
import unittest
from backend.app.providers.base import SearchProvider, StandardizedVideoResult
from backend.app.providers.douyin_live_provider import DouyinProvider, LiveDouyinSearchProvider
from backend.app.providers.factory import get_search_provider
from backend.app.smart_search.smart_search_service import SmartSearchService

class TestDouyinSearchEngine(unittest.IsolatedAsyncioTestCase):
    """
    Test suite for Phase 4 Douyin Search Engine, SearchProvider abstraction,
    standardized schemas, multi-query priority search, deduplication and ranking.
    """

    async def test_provider_abstraction_and_inheritance(self):
        provider = get_search_provider()
        self.assertIsInstance(provider, SearchProvider)
        self.assertIsInstance(provider, DouyinProvider)

    async def test_douyin_provider_search_multiple_chinese_keywords(self):
        provider = DouyinProvider()
        test_chinese_keywords = [
            "美女穿睡衣",
            "可爱小猫",
            "顶级超跑加速",
            "夜市美食测评",
            "生活实用小妙招",
            "惊艳化妆变装"
        ]

        print("\n" + "="*70)
        print("🧪 TESTING DOUYIN PROVIDER WITH MULTIPLE CHINESE KEYWORDS")
        print("="*70)

        for kw in test_chinese_keywords:
            results = await provider.search(kw, limit=5)
            self.assertTrue(len(results) >= 1)
            first = results[0]

            # Verify all standardized fields are present
            self.assertIsInstance(first, StandardizedVideoResult)
            self.assertTrue(bool(first.video_id))
            self.assertTrue(bool(first.title))
            self.assertTrue(bool(first.url))
            self.assertIn("douyin.com", first.url)
            self.assertTrue(first.likes >= 0)
            self.assertTrue(first.comments >= 0)
            self.assertTrue(first.shares >= 0)
            self.assertTrue(first.duration >= 0)
            self.assertTrue(bool(first.publish_time))
            self.assertEqual(first.query, kw)

            print(f"✅ Search '{kw}': Retrieved {len(results)} videos. Top: '{first.title[:35]}...' (Likes: {first.likes:,})")

    async def test_end_to_end_pipeline_vietnamese_to_douyin_results(self):
        print("\n" + "="*70)
        print("🧪 TESTING FULL PIPELINE (VIETNAMESE -> DOUYIN CANDIDATES -> DEDUPLICATE -> RANKING)")
        print("="*70)

        res = await SmartSearchService.execute_smart_search(
            query="gái xinh mặc pijama che mặt",
            language="vi",
            mode="normal",
            min_likes=1000
        )

        self.assertEqual(res["language"], "vi")
        self.assertTrue(res["results_count"] > 0)
        self.assertTrue(len(res["results"]) > 0)

        first_res = res["results"][0]
        # Verify standardized fields in response JSON
        required_fields = [
            "video_id", "title", "url", "thumbnail", "author",
            "likes", "comments", "shares", "duration", "publish_time",
            "query", "score", "match_tier"
        ]
        for field in required_fields:
            self.assertIn(field, first_res, f"Missing standardized field: {field}")

        # Check deduplication
        video_ids = [r["video_id"] for r in res["results"]]
        self.assertEqual(len(video_ids), len(set(video_ids)), "Duplicate video IDs found in search results!")

        # Check sorted scores
        scores = [r["score"] for r in res["results"]]
        self.assertEqual(scores, sorted(scores, reverse=True), "Results are not sorted by score descending!")

        print(f"✅ Pipeline Output: {len(res['results'])} ranked videos.")
        print(f"   Top Result #1: [{first_res['match_tier']} - {first_res['score']}%]")
        print(f"   Title: {first_res['title']}")
        print(f"   URL: {first_res['url']}")
        print(f"   Likes: {first_res['likes']:,} | Comments: {first_res['comments']:,} | Shares: {first_res['shares']:,}")

if __name__ == "__main__":
    unittest.main()
