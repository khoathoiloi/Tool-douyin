import os
import sys
import unittest
import asyncio
import json
import subprocess

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from backend.app.core.database import engine, Base, SessionLocal
from backend.app.core.models import Video, Job, VideoAnalysis, SearchQuery, SearchResult
from backend.app.worker.job_runner import PipelineJobRunner
import imageio_ffmpeg

class TestEndToEndPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.db = SessionLocal()
        
        cls.test_video_path = os.path.join(base_dir, "uploads", "test_integration.mp4")
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

    def test_full_pipeline_execution(self):
        self.assertTrue(os.path.exists(self.test_video_path))
        
        video_id = "test_vid_001"
        job_id = "test_job_001"
        
        self.db.query(Video).filter(Video.id == video_id).delete()
        self.db.query(Job).filter(Job.id == job_id).delete()
        self.db.commit()
        
        video = Video(id=video_id, filename="test_integration.mp4", file_path=self.test_video_path, filesize=os.path.getsize(self.test_video_path))
        job = Job(id=job_id, video_id=video_id, stage="queued", status="pending", progress_percent=0)
        self.db.add(video)
        self.db.add(job)
        self.db.commit()
        
        # Run pipeline
        asyncio.run(PipelineJobRunner.run_full_pipeline(video_id, job_id, self.db, user_hint="Video nháº£y hot trend"))
        
        # Verify Job completed
        updated_job = self.db.query(Job).filter(Job.id == job_id).first()
        self.assertEqual(updated_job.status, "completed")
        self.assertEqual(updated_job.progress_percent, 100)
        
        # Verify Analysis profile
        analysis = self.db.query(VideoAnalysis).filter(VideoAnalysis.video_id == video_id).first()
        self.assertIsNotNone(analysis)
        self.assertTrue(len(analysis.summary) > 0)
        
        # Verify 20 Queries
        queries = self.db.query(SearchQuery).filter(SearchQuery.video_id == video_id).all()
        self.assertGreaterEqual(len(queries), 20)
        
        # Verify Results
        results = self.db.query(SearchResult).filter(SearchResult.video_id == video_id).all()
        self.assertTrue(len(results) > 0)
        self.assertTrue(all(r.url.startswith("https://www.douyin.com/video/") for r in results))
        print(f"\nâœ… Integration Test Passed: Generated {len(queries)} queries and {len(results)} ranked Douyin results!")

if __name__ == "__main__":
    unittest.main()

