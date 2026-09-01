import os
import sys
import unittest
from io import BytesIO
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings

class TestCentralBackendAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    # 1. POST /api/v1/search
    def test_endpoint_search_vietnamese(self):
        resp = self.client.post("/api/v1/search", json={
            "query": "gái xinh mặc pijama che mặt",
            "language": "auto",
            "mode": "normal",
            "min_likes": 0
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("results", data)
        self.assertTrue(len(data["results"]) > 0)
        self.assertIn("score", data["results"][0])
        self.assertEqual(data["language"], "vi")

    def test_endpoint_search_chinese_direct(self):
        resp = self.client.post("/api/v1/search", json={
            "keyword": "美女穿睡衣",
            "language": "zh",
            "mode": "normal"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["language"], "zh")
        self.assertTrue(len(data["results"]) > 0)

    # 2. POST /api/v1/files
    def test_endpoint_upload_files(self):
        dummy_file = BytesIO(b"dummy video binary content")
        resp = self.client.post(
            "/api/v1/files",
            files={"file": ("test_clip.mp4", dummy_file, "video/mp4")}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("file_id", data)
        self.assertIn("path", data)
        self.assertEqual(data["filename"], "test_clip.mp4")

    # 3. POST /api/v1/analyze/url
    def test_endpoint_analyze_url(self):
        resp = self.client.post("/api/v1/analyze/url", json={
            "url": "https://vt.tiktok.com/ZSVwrT9Lg/",
            "user_hint": "Galaxy S9 URL Analysis",
            "deep_search": False
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("job_id", data)
        self.assertIn("video_id", data)
        self.assertEqual(data["status"], "queued")
        self.created_job_id = data["job_id"]

    # 4. POST /api/v1/analyze/video
    def test_endpoint_analyze_video(self):
        dummy_video = BytesIO(b"fake video stream")
        resp = self.client.post(
            "/api/v1/analyze/video",
            files={"file": ("sample.mp4", dummy_video, "video/mp4")},
            data={"user_hint": "Test Video Hint", "deep_search": "false"}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("job_id", data)
        self.assertIn("video_id", data)
        self.assertEqual(data["status"], "queued")

    # 5. GET /api/v1/jobs/{job_id} and GET /api/v1/search/{job_id}/results
    def test_endpoint_job_status_and_results(self):
        # Create a quick job via url
        url_resp = self.client.post("/api/v1/analyze/url", json={
            "url": "https://www.douyin.com/video/7268899827364121914"
        })
        job_id = url_resp.json()["job_id"]

        # Poll status
        status_resp = self.client.get(f"/api/v1/jobs/{job_id}")
        self.assertEqual(status_resp.status_code, 200)
        status_data = status_resp.json()
        self.assertEqual(status_data["job_id"], job_id)
        self.assertIn("stage", status_data)

        # Poll results
        results_resp = self.client.get(f"/api/v1/search/{job_id}/results?page=1&page_size=10")
        self.assertEqual(results_resp.status_code, 200)
        results_data = results_resp.json()
        self.assertIn("results", results_data)
        self.assertIn("page", results_data)

    # 6. GET & POST & DELETE /api/v1/history
    def test_endpoint_history_crud(self):
        # Create history entry
        post_resp = self.client.post("/api/v1/history", json={
            "query": "gái xinh mặc pijama",
            "results_count": 12,
            "language": "vi"
        })
        self.assertEqual(post_resp.status_code, 200)
        hist_id = post_resp.json()["id"]

        # Get history list
        get_resp = self.client.get("/api/v1/history")
        self.assertEqual(get_resp.status_code, 200)
        history_list = get_resp.json()["history"]
        self.assertTrue(any(h["id"] == hist_id for h in history_list))

        # Delete history entry
        del_resp = self.client.delete(f"/api/v1/history/{hist_id}")
        self.assertEqual(del_resp.status_code, 200)
        self.assertTrue(del_resp.json()["success"])

    # 7. GET & PUT /api/v1/settings
    def test_endpoint_settings_masked_and_update(self):
        # GET settings
        get_resp = self.client.get("/api/v1/settings")
        self.assertEqual(get_resp.status_code, 200)
        settings_data = get_resp.json()
        self.assertIn("gemini_api_key_masked", settings_data)
        self.assertIn("weights", settings_data)

        # PUT settings
        put_resp = self.client.put("/api/v1/settings", json={
            "douyin_search_provider": "live",
            "weight_semantic": 0.35,
            "weight_visual": 0.25
        })
        self.assertEqual(put_resp.status_code, 200)
        self.assertTrue(put_resp.json()["success"])

    # 8. POST /api/v1/query/translate and /api/v1/query/generate
    def test_endpoint_query_translate_and_generate(self):
        trans_resp = self.client.post("/api/v1/query/translate", json={
            "query": "gái xinh mặc pijama che mặt"
        })
        self.assertEqual(trans_resp.status_code, 200)
        self.assertEqual(trans_resp.json()["detected_language"], "vi")

        gen_resp = self.client.post("/api/v1/query/generate", json={
            "query": "gái xinh mặc pijama che mặt"
        })
        self.assertEqual(gen_resp.status_code, 200)
        self.assertTrue(len(gen_resp.json()["flat_queries"]) > 0)

if __name__ == "__main__":
    unittest.main()
