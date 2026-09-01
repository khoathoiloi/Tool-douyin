import os
import sys
import unittest
import asyncio

base_dir = r"C:\\Users\\Administrator\\\.gemini\\antigravity\\scratch\\Tool-douyin"
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from fastapi.testclient import TestClient
from backend.app.main import app

class TestAndroidApiV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_search_by_url_endpoint(self):
        resp = self.client.post("/api/v1/search/url", json={
            "url": "https://vt.tiktok.com/ZSVwrT9Lg/",
            "user_hint": "Galaxy S9 Test",
            "deep_search": False
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("job_id", data)
        self.assertIn("video_id", data)
        self.assertEqual(data["status"], "queued")
        print(f"\n[Android API v1] URL search created job: {data['job_id']}")

    def test_search_by_keyword_endpoint(self):
        resp = self.client.post("/api/v1/search/keyword", json={
            "keyword": "女生变装",
            "deep_search": False,
            "limit": 10
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("job_id", data)
        self.assertIn("results", data)
        self.assertTrue(len(data["results"]) > 0)
        self.assertTrue(all("score" in r for r in data["results"]))
        print(f"[Android API v1] Keyword search returned {len(data['results'])} results for Galaxy S9.")

if __name__ == "__main__":
    unittest.main()
