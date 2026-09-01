import os
import sys
import unittest

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from backend.app.video.metadata import VideoMetadataExtractor
from backend.app.video.keyframes import AdaptiveKeyframeExtractor
from backend.app.ai.ocr import VideoOCREngine
from backend.app.ai.asr import VideoASREngine
from backend.app.ai.analyzer import MultiLayerVideoAnalyzer

class TestPhase3VideoAnalysis(unittest.TestCase):
    def test_metadata_extraction(self):
        video_path = os.path.join(base_dir, "uploads", "test_integration.mp4")
        if os.path.exists(video_path):
            meta = VideoMetadataExtractor.extract(video_path)
            self.assertIn("duration", meta)
            self.assertIn("fps", meta)
            self.assertIn("aspect_ratio", meta)
            self.assertIn("codec", meta)

    def test_multi_layer_analysis_schema(self):
        profile = MultiLayerVideoAnalyzer.analyze(
            keyframe_items=[],
            ocr_items=[{"text": "热门变装", "timestamp": 1.0}],
            asr_data={"transcript": "Nhạc hot trend"},
            metadata={"duration": 15.0},
            user_hint="Cô gái nhảy biến hình"
        )
        self.assertIn("summary", profile)
        self.assertIn("subjects", profile)
        self.assertIn("actions", profile)
        self.assertIn("categories", profile)
        self.assertIn("keywords", profile)
        self.assertIn("queries", profile)
        
        # Verify query categories
        queries = profile["queries"]
        for cat in ["exact", "high_similarity", "visual", "action", "scene", "trend", "broad"]:
            self.assertIn(cat, queries)
            self.assertTrue(len(queries[cat]) > 0)

if __name__ == "__main__":
    unittest.main()
