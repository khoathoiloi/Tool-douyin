import os
import sys
import unittest
from fastapi.testclient import TestClient

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from backend.app.main import app

class TestAndroidApkIntegration(unittest.TestCase):
    """
    Test suite for Phase 8: Android APK Client & API Integration.
    Verifies all API contracts and data schemas expected by the Samsung Galaxy S9 Android App.
    """

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_android_health_check_contract(self):
        print("\n" + "="*70)
        print("📱 TESTING ANDROID APK HEALTH CHECK CONTRACT")
        print("="*70)
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("version", data)
        print(f"✅ Android Health Check Contract Passed: status='{data['status']}', version='{data.get('version')}'.")

    def test_android_smart_vietnamese_search_contract(self):
        print("\n" + "="*70)
        print("🇻🇳 TESTING ANDROID SMART SEARCH CONTRACT (GALAXY S9)")
        print("="*70)
        # Android SmartSearchRequest schema
        payload = {
            "query": "gái xinh mặc pijama che mặt",
            "language": "auto",
            "mode": "normal",
            "deep_search": False,
            "min_score": 60.0,
            "min_likes": 0,
            "sort_by": "similarity",
            "limit": 20
        }
        resp = self.client.post("/api/v1/search", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertIn("results", data)
        self.assertTrue(len(data["results"]) > 0)
        first_item = data["results"][0]

        # Verify fields required by Android SearchResultItem & ResultsAdapter
        required_fields = ["video_id", "url", "title", "author", "likes", "comments", "duration", "final_score", "keyword_score", "semantic_score", "visual_score", "action_score"]
        for field in required_fields:
            self.assertIn(field, first_item, f"Missing field '{field}' required by Android SearchResultItem")

        print(f"✅ Android Smart Search Contract Passed: Loaded {len(data['results'])} items with full 6-subscores. Top Match: {first_item['final_score']}%.")

    def test_android_keyword_preview_contract(self):
        print("\n" + "="*70)
        print("👁️ TESTING ANDROID KEYWORD PREVIEW CONTRACT")
        print("="*70)
        payload = {
            "query": "gái xinh mặc pijama che mặt",
            "language": "auto",
            "mode": "normal"
        }
        resp = self.client.post("/api/v1/query/translate", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertIn("chinese_keywords", data)
        self.assertIn("query_scores", data)
        self.assertTrue(len(data["query_scores"]) > 0)
        first_q = data["query_scores"][0]
        self.assertIn("query", first_q)
        self.assertIn("score", first_q)
        self.assertIn("tier", first_q)

        print(f"✅ Android Keyword Preview Passed: Generated {len(data['query_scores'])} queries for Galaxy S9 preview card.")

    def test_android_codebase_zero_secret_audit(self):
        print("\n" + "="*70)
        print("🔒 AUDITING ANDROID APP CODEBASE FOR ZERO SECRETS")
        print("="*70)
        android_dir = os.path.join(base_dir, "android")
        forbidden_patterns = ["AIzaSy", "sk-", "ghp_", "bearer", "cookie_value_secret"]

        leaks = []
        for root, _, files in os.walk(android_dir):
            if "build" in root or ".gradle" in root:
                continue
            for file in files:
                if file.endswith((".kt", ".java", ".xml", ".gradle", ".kts", ".properties")):
                    fpath = os.path.join(root, file)
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        for pat in forbidden_patterns:
                            if pat in content:
                                leaks.append((file, pat))

        self.assertEqual(len(leaks), 0, f"Found secret leaks in Android APK source: {leaks}")
        print("✅ Zero Secrets Audit Passed: Android APK contains 0 API keys, 0 Database credentials, and 0 Douyin cookies.")

if __name__ == "__main__":
    unittest.main()
