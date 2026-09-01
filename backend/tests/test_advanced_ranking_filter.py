import asyncio
import unittest
from backend.app.ranking.scoring import MultiLayerScoringEngine
from backend.app.ranking.filters import AdvancedResultFilter
from backend.app.smart_search.smart_search_service import SmartSearchService

class TestAdvancedRankingAndFilter(unittest.IsolatedAsyncioTestCase):
    """
    Test suite for Phase 5 Advanced Content Filter + Ranking Engine and Benchmark Metrics.
    """

    async def test_sub_scores_breakdown_and_normalization(self):
        print("\n" + "="*70)
        print("🧪 TESTING 6-DIMENSIONAL SUB-SCORES BREAKDOWN & 0-100 NORMALIZATION")
        print("="*70)

        res = await SmartSearchService.execute_smart_search(
            query="gái xinh mặc pijama che mặt",
            language="vi",
            min_score=60.0
        )

        self.assertTrue(res["results_count"] > 0)
        top_item = res["results"][0]

        # Verify all 6 sub-scores and final_score exist and are in range [0, 100]
        score_fields = [
            "keyword_score",
            "semantic_score",
            "visual_score",
            "scene_score",
            "action_score",
            "query_score",
            "final_score"
        ]

        for sf in score_fields:
            self.assertIn(sf, top_item, f"Missing score field: {sf}")
            score_val = top_item[sf]
            self.assertTrue(0 <= score_val <= 100, f"Score {sf}={score_val} is out of 0-100 bounds!")

        print(f"✅ Top Result Sub-Scores for '{res['original_query']}':")
        print(f"   • Keyword Score:  {top_item['keyword_score']}/100")
        print(f"   • Semantic Score: {top_item['semantic_score']}/100")
        print(f"   • Visual Score:   {top_item['visual_score']}/100")
        print(f"   • Scene Score:    {top_item['scene_score']}/100")
        print(f"   • Action Score:   {top_item['action_score']}/100")
        print(f"   • Query Score:    {top_item['query_score']}/100")
        print(f"   ⭐️ FINAL SCORE:   {top_item['final_score']}/100 [{top_item['match_tier']}]")

    async def test_multi_dimensional_filters_and_sorting(self):
        print("\n" + "="*70)
        print("🧪 TESTING MULTI-DIMENSIONAL FILTERS & SORTING MODES")
        print("="*70)

        # 1. Likes Filter & Sort by Likes DESC
        likes_res = await SmartSearchService.execute_smart_search(
            query="mèo con dễ thương ngủ ngon",
            min_likes=20000,
            sort_by="likes"
        )
        self.assertTrue(likes_res["results_count"] > 0)
        for r in likes_res["results"]:
            self.assertGreaterEqual(r["likes"], 20000)

        # Verify sorted likes descending
        likes_list = [r["likes"] for r in likes_res["results"]]
        self.assertEqual(likes_list, sorted(likes_list, reverse=True))
        print(f"✅ Filter min_likes=20000 + Sort by Likes: {likes_list[:5]}")

        # 2. Duration Filter
        dur_res = await SmartSearchService.execute_smart_search(
            query="cô gái nấu ăn trong bếp",
            min_duration=15,
            max_duration=60,
            sort_by="similarity"
        )
        for r in dur_res["results"]:
            self.assertTrue(15 <= r["duration"] <= 60)
        print(f"✅ Filter duration [15s - 60s]: Passed for {dur_res['results_count']} videos")

        # 3. Sort by Comments DESC
        comments_res = await SmartSearchService.execute_smart_search(
            query="siêu xe tăng tốc trên cao tốc",
            sort_by="comments"
        )
        comments_list = [r["comments"] for r in comments_res["results"]]
        self.assertEqual(comments_list, sorted(comments_list, reverse=True))
        print(f"✅ Sort by Comments DESC: {comments_list[:5]}")

    def test_benchmark_metrics_before_vs_after_filter(self):
        print("\n" + "="*70)
        print("📊 BENCHMARK COMPARISON: BEFORE FILTER VS AFTER FILTER")
        print("="*70)

        # Simulate a noisy raw candidate batch with ads and duplicates
        raw_before = [
            {"video_id": "vid_01", "title": "【美女穿睡衣遮脸】全网超火爆款", "final_score": 92, "likes": 50000},
            {"video_id": "vid_01", "title": "【美女穿睡衣遮脸】全网超火爆款", "final_score": 92, "likes": 50000}, # Duplicate
            {"video_id": "vid_02", "title": "【美女睡衣自拍】高颜值日常", "final_score": 88, "likes": 35000},
            {"video_id": "vid_03", "title": "【睡衣商品促销】包邮下单淘宝店铺", "final_score": 45, "likes": 120}, # Ad
            {"video_id": "vid_04", "title": "【高颜值女生睡衣】写真自拍", "final_score": 85, "likes": 42000},
            {"video_id": "vid_05", "title": "【美女穿搭】居家服", "final_score": 75, "likes": 15000},
            {"video_id": "vid_06", "title": "【今日爆款广告】点击购买", "final_score": 30, "likes": 50} # Ad
        ]

        # Apply Advanced Result Filter (deduplicated, min_score=70, no ads)
        unique_raw = []
        seen = set()
        for r in raw_before:
            if r["video_id"] not in seen:
                seen.add(r["video_id"])
                unique_raw.append(r)

        filtered_after = AdvancedResultFilter.apply_filters(
            results=unique_raw,
            min_score=70.0,
            negative_keywords=["广告", "商品", "店铺", "购买", "包邮"]
        )

        metrics = AdvancedResultFilter.calculate_benchmark_metrics(
            before_list=raw_before,
            after_list=filtered_after,
            target_intent_keywords=["美女", "睡衣", "自拍", "高颜值"]
        )

        b = metrics["before_filter"]
        a = metrics["after_filter"]

        print(f"📌 BEFORE FILTER (Raw Search Candidates):")
        print(f"   • Total Items:      {b['total']}")
        print(f"   • Precision:        {b['precision']}%")
        print(f"   • Duplicate Rate:   {b['duplicate_rate']}%")
        print(f"   • Irrelevant Rate:  {b['irrelevant_rate']}%")
        print(f"   • Average Score:    {b['average_score']}/100")

        print(f"\n✨ AFTER FILTER (Advanced Multi-Criteria Filter):")
        print(f"   • Total Items:      {a['total']}")
        print(f"   • Precision:        {a['precision']}%")
        print(f"   • Duplicate Rate:   {a['duplicate_rate']}%")
        print(f"   • Irrelevant Rate:  {a['irrelevant_rate']}%")
        print(f"   • Average Score:    {a['average_score']}/100")
        print("="*70)

        # Assertions
        self.assertEqual(a["duplicate_rate"], 0.0, "Duplicate rate after filter must be 0%")
        self.assertEqual(a["irrelevant_rate"], 0.0, "Irrelevant ad rate after filter must be 0%")
        self.assertEqual(a["precision"], 100.0, "Precision after filter should be 100%")
        self.assertGreater(a["average_score"], b["average_score"], "Average score must improve after filter!")

if __name__ == "__main__":
    unittest.main()
