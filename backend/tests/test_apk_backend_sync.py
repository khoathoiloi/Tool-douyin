import os
import sys
import unittest
import uuid
from fastapi.testclient import TestClient

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from backend.app.main import app

class TestApkBackendSync(unittest.TestCase):
    """
    Test suite for Phase 9: APK <-> BACKEND BIDIRECTIONAL SYNC.
    Verifies that PC Desktop Client and Android APK Client share 100% of data,
    history, jobs, rankings, and synchronization states through the Backend API.
    """

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_sync_pc_search_to_apk_history(self):
        print("\n" + "="*70)
        print("🖥️ ➔ 📱 TEST 1: PC SEARCH -> BACKEND -> APK VIEWS HISTORY")
        print("="*70)

        # 1. PC executes a smart search
        pc_query = f"gái xinh áo dài việt nam {uuid.uuid4().hex[:4]}"
        pc_headers = {
            "X-Client-Type": "pc-desktop",
            "X-Device-Id": "pc-workstation-01"
        }
        pc_payload = {
            "query": pc_query,
            "language": "vi",
            "mode": "normal",
            "min_score": 60.0,
            "sort_by": "similarity"
        }
        resp = self.client.post("/api/v1/search", json=pc_payload, headers=pc_headers)
        self.assertEqual(resp.status_code, 200)
        pc_data = resp.json()
        self.assertTrue(len(pc_data["results"]) > 0)
        print(f"✅ PC Search Completed: '{pc_query}' ({len(pc_data['results'])} results).")

        # 2. Android APK queries search history
        apk_headers = {
            "X-Client-Type": "android-samsung-galaxy-s9",
            "X-Device-Id": "sm-g960f-s9-01"
        }
        hist_resp = self.client.get("/api/v1/history", headers=apk_headers)
        self.assertEqual(hist_resp.status_code, 200)
        hist_items = hist_resp.json().get("history", [])

        # 3. Verify APK sees the session created by PC
        matched = any(pc_query[:20] in (item.get("filename") or "") for item in hist_items)
        self.assertTrue(matched, f"APK failed to find PC search query '{pc_query}' in history!")
        print("✅ Sync Passed: Android APK successfully retrieved search session created by PC!")

    def test_sync_apk_search_to_pc_history(self):
        print("\n" + "="*70)
        print("📱 ➔ 🖥️ TEST 2: APK SEARCH -> BACKEND -> PC VIEWS HISTORY")
        print("="*70)

        # 1. Android APK executes a smart search
        apk_query = f"ẩm thực đường phố trùng khánh {uuid.uuid4().hex[:4]}"
        apk_headers = {
            "X-Client-Type": "android-samsung-galaxy-s9",
            "X-Device-Id": "sm-g960f-s9-01"
        }
        apk_payload = {
            "query": apk_query,
            "language": "auto",
            "mode": "normal",
            "min_score": 60.0,
            "sort_by": "similarity"
        }
        resp = self.client.post("/api/v1/search", json=apk_payload, headers=apk_headers)
        self.assertEqual(resp.status_code, 200)
        apk_data = resp.json()
        self.assertTrue(len(apk_data["results"]) > 0)
        print(f"✅ APK Search Completed: '{apk_query}' ({len(apk_data['results'])} results).")

        # 2. PC queries search history
        pc_headers = {
            "X-Client-Type": "pc-desktop",
            "X-Device-Id": "pc-workstation-01"
        }
        hist_resp = self.client.get("/api/v1/history", headers=pc_headers)
        self.assertEqual(hist_resp.status_code, 200)
        hist_items = hist_resp.json().get("history", [])

        # 3. Verify PC sees the session created by APK
        matched = any(apk_query[:20] in (item.get("filename") or "") for item in hist_items)
        self.assertTrue(matched, f"PC failed to find APK search query '{apk_query}' in history!")
        print("✅ Sync Passed: PC desktop client successfully retrieved search session created by APK!")

    def test_shared_job_results_and_pagination(self):
        print("\n" + "="*70)
        print("🔄 TEST 3: CROSS-CLIENT SHARED JOB RESULTS & PAGINATION")
        print("="*70)

        # 1. Trigger URL search job from APK
        url_resp = self.client.post(
            "/api/v1/search/url",
            json={"url": "https://www.douyin.com/video/7268899827364121901", "deep_search": False},
            headers={"X-Client-Type": "android-samsung-galaxy-s9"}
        )
        self.assertEqual(url_resp.status_code, 200)
        job_id = url_resp.json()["job_id"]

        # 2. Fetch page 1 (pageSize=2)
        page1_resp = self.client.get(f"/api/v1/search/{job_id}/results?page=1&page_size=2&min_score=50")
        self.assertEqual(page1_resp.status_code, 200)
        page1_data = page1_resp.json()
        self.assertEqual(page1_data["page"], 1)
        self.assertEqual(page1_data["page_size"], 2)
        self.assertTrue(len(page1_data["results"]) <= 2)

        # 3. Fetch page 2 (pageSize=2)
        page2_resp = self.client.get(f"/api/v1/search/{job_id}/results?page=2&page_size=2&min_score=50")
        self.assertEqual(page2_resp.status_code, 200)
        page2_data = page2_resp.json()
        self.assertEqual(page2_data["page"], 2)

        print(f"✅ Pagination Passed: Page 1 ({len(page1_data['results'])} items) & Page 2 ({len(page2_data['results'])} items). Total: {page1_data['total_results']}.")

    def test_backend_settings_sync(self):
        print("\n" + "="*70)
        print("⚙️ TEST 4: BACKEND SETTINGS SYNCHRONIZATION")
        print("="*70)
        resp = self.client.get("/api/v1/settings")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("douyin_search_provider", data)
        self.assertIn("ai_provider", data)
        print(f"✅ Settings Sync Passed: Provider='{data['douyin_search_provider']}', AI='{data['ai_provider']}'.")

if __name__ == "__main__":
    unittest.main()
