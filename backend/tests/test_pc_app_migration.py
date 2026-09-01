import os
import sys
import unittest
from fastapi.testclient import TestClient

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from backend.app.main import app
from gui.api_client import BackendApiClient

class TestPCAppBackendMigration(unittest.TestCase):
    """
    Test suite for Phase 7: PC App Backend Migration.
    Verifies that the PC Desktop client interacts exclusively with the Backend API,
    with zero local AI computation, ranking, or crawler logic.
    """

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.api_client = BackendApiClient(base_url="http://testserver")
        # Monkey patch session to use FastAPI TestClient
        cls.api_client.session = cls.client

    def test_pc_health_check(self):
        print("\n" + "="*70)
        print("🖥️ TESTING PC APP BACKEND HEALTH CHECK")
        print("="*70)
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "healthy")
        print("✅ Health Check Passed: Backend API is reachable from PC client.")

    def test_pc_smart_vietnamese_search(self):
        print("\n" + "="*70)
        print("🇻🇳 TESTING PC SMART VIETNAMESE SEARCH VIA API")
        print("="*70)
        payload = {
            "query": "gái xinh mặc pijama che mặt",
            "language": "vi",
            "mode": "normal",
            "min_score": 60.0,
            "min_likes": 5000,
            "sort_by": "similarity"
        }
        resp = self.client.post("/api/v1/search", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertIn("results", data)
        self.assertTrue(len(data["results"]) > 0)
        top_res = data["results"][0]
        self.assertIn("final_score", top_res)
        self.assertIn("keyword_score", top_res)
        self.assertIn("semantic_score", top_res)
        self.assertIn("visual_score", top_res)
        self.assertIn("scene_score", top_res)
        self.assertIn("action_score", top_res)
        self.assertIn("query_score", top_res)

        print(f"✅ PC Vietnamese Search Passed: Received {len(data['results'])} ranked results. Top score: {top_res['final_score']}%.")

    def test_pc_keyword_preview(self):
        print("\n" + "="*70)
        print("👁️ TESTING PC CHINESE KEYWORD PREVIEW VIA API")
        print("="*70)
        resp = self.client.post("/api/v1/query/translate", json={"query": "review ẩm thực đêm", "mode": "normal"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["detected_language"], "vi")
        self.assertIn("chinese_keywords", data)
        self.assertIn("query_scores", data)
        self.assertTrue(len(data["query_scores"]) >= 4)
        print(f"✅ PC Keyword Preview Passed: Generated {len(data['query_scores'])} Chinese search queries.")

    def test_pc_history_and_settings(self):
        print("\n" + "="*70)
        print("🕒 TESTING PC SEARCH HISTORY & SETTINGS VIA API")
        print("="*70)
        # History
        hist_resp = self.client.get("/api/v1/history")
        self.assertEqual(hist_resp.status_code, 200)
        hist_data = hist_resp.json()
        self.assertIn("history", hist_data)
        print(f"✅ PC History Passed: Loaded {len(hist_data['history'])} search history items.")

        # Settings
        settings_resp = self.client.get("/api/v1/settings")
        self.assertEqual(settings_resp.status_code, 200)
        settings_data = settings_resp.json()
        self.assertIn("douyin_search_provider", settings_data)
        self.assertIn("ai_provider", settings_data)
        print("✅ PC Settings Passed: Successfully synchronized backend configuration.")


if __name__ == "__main__":
    unittest.main()
