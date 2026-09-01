import os
import sys
import unittest
import asyncio
import subprocess
import imageio_ffmpeg
from fastapi.testclient import TestClient

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from backend.app.main import app
from backend.app.core.database import engine, Base, SessionLocal
from backend.app.core.models import Video, Job, VideoAnalysis, SearchQuery, SearchResult

class TestAllSearchModes(unittest.TestCase):
    """
    Test suite for Phase 6: Text Search + Video Upload Search + Douyin URL Search.
    Verifies all 3 search modes with full pipeline transparency and error handling.
    """

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        # Generate a lightweight test MP4 for video upload test
        cls.test_video_path = os.path.join(base_dir, "uploads", "test_phase6_search.mp4")
        os.makedirs(os.path.dirname(cls.test_video_path), exist_ok=True)
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

        cmd = [
            ffmpeg_exe, "-y",
            "-f", "lavfi", "-i", "testsrc=duration=2:size=320x240:rate=10",
            "-f", "lavfi", "-i", "sine=frequency=1000:duration=2",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            cls.test_video_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def test_mode_1_text_search(self):
        print("\n" + "="*70)
        print("🔍 TESTING MODE 1: SMART TEXT SEARCH (TIẾNG VIỆT -> DOUYIN)")
        print("="*70)

        payload = {
            "query": "gái xinh mặc pijama che mặt",
            "language": "vi",
            "min_score": 60.0,
            "min_likes": 10000,
            "sort_by": "similarity"
        }

        resp = self.client.post("/api/v1/search", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertTrue(data["results_count"] > 0)
        self.assertEqual(data["language"], "vi")
        self.assertTrue(len(data["queries"]) >= 1)

        top_r = data["results"][0]
        self.assertIn("video_id", top_r)
        self.assertIn("final_score", top_r)
        self.assertIn("keyword_score", top_r)
        self.assertIn("semantic_score", top_r)
        self.assertIn("visual_score", top_r)
        self.assertGreaterEqual(top_r["likes"], 10000)

        print(f"✅ Mode 1 Passed: Found {data['results_count']} videos for '{data['original_query']}'. Top match: {top_r['final_score']}% [{top_r['match_tier']}]")

    def test_mode_2_video_upload_search(self):
        print("\n" + "="*70)
        print("📹 TESTING MODE 2: VIDEO UPLOAD SEARCH (FILE -> AI -> DOUYIN)")
        print("="*70)

        self.assertTrue(os.path.exists(self.test_video_path))

        with open(self.test_video_path, "rb") as f:
            resp = self.client.post(
                "/api/v1/analyze/video",
                files={"file": ("test_phase6_search.mp4", f, "video/mp4")},
                data={"user_hint": "Video cô gái nhảy đẹp", "deep_search": "false"}
            )

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        job_id = data["job_id"]
        video_id = data["video_id"]
        self.assertIsNotNone(job_id)

        # Run pipeline synchronously for test runner
        from backend.app.worker.job_runner import PipelineJobRunner
        asyncio.run(PipelineJobRunner.run_full_pipeline(video_id, job_id, self.db, user_hint="Video cô gái nhảy đẹp"))

        # Verify Job Transparency Details
        job_resp = self.client.get(f"/api/v1/jobs/{job_id}")
        self.assertEqual(job_resp.status_code, 200)
        job_data = job_resp.json()

        self.assertEqual(job_data["status"], "completed")
        self.assertIsNotNone(job_data["original_input"])
        self.assertIsNotNone(job_data["analysis"])
        self.assertTrue(len(job_data["queries"]) >= 20)
        self.assertTrue(job_data["results_count"] > 0)

        # Verify Paginated Scored Results
        res_resp = self.client.get(f"/api/v1/search/{job_id}/results?page=1&page_size=10")
        self.assertEqual(res_resp.status_code, 200)
        res_data = res_resp.json()
        self.assertTrue(len(res_data["results"]) > 0)

        top_vid = res_data["results"][0]
        print(f"✅ Mode 2 Passed: Analyzed Video -> Generated {len(job_data['queries'])} queries -> Found {job_data['results_count']} ranked Douyin results.")
        print(f"   AI Description Summary: {job_data['analysis']['summary']}")

    def test_mode_3_douyin_url_search_valid_and_invalid(self):
        print("\n" + "="*70)
        print("🔗 TESTING MODE 3: DOUYIN URL SEARCH & ERROR DEFENSE")
        print("="*70)

        # 1. Invalid URL -> Clear Error Response
        invalid_resp = self.client.post("/api/v1/analyze/url", json={"url": "not_a_valid_link"})
        self.assertEqual(invalid_resp.status_code, 400)
        self.assertIn("INVALID_URL", invalid_resp.text)
        print("✅ Invalid Link Defense: Correctly rejected invalid URL format.")

        # 2. Valid URL Format -> Trigger Pipeline
        valid_url = "https://www.douyin.com/video/7268899827364121901"
        resp = self.client.post("/api/v1/analyze/url", json={"url": valid_url, "user_hint": "Review đồ ăn đêm"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("job_id", data)
        self.assertIn("video_id", data)

        print(f"✅ Valid URL Triggered: Created Job {data['job_id']}.")

if __name__ == "__main__":
    unittest.main()
