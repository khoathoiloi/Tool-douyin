import os
import sys
import unittest

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from backend.app.douyin.url_parser import DouyinUrlParser

class TestPhase2Input(unittest.TestCase):
    def test_url_validation(self):
        valid_douyin = "https://www.douyin.com/video/7268899827364121914"
        valid_douyin_short = "https://v.douyin.com/iJkvXYZ/"
        valid_tiktok = "https://vt.tiktok.com/ZSVwrT9Lg/"
        invalid_url = "not a valid url"

        self.assertTrue(DouyinUrlParser.is_valid_url(valid_douyin))
        self.assertTrue(DouyinUrlParser.is_douyin_or_tiktok_url(valid_douyin))
        self.assertTrue(DouyinUrlParser.is_douyin_or_tiktok_url(valid_douyin_short))
        self.assertTrue(DouyinUrlParser.is_douyin_or_tiktok_url(valid_tiktok))
        self.assertFalse(DouyinUrlParser.is_valid_url(invalid_url))

    def test_url_metadata_extraction(self):
        upload_dir = os.path.join(base_dir, "uploads")
        meta = DouyinUrlParser.parse_and_fetch_metadata("https://vt.tiktok.com/ZSVwrT9Lg/", upload_dir)
        self.assertTrue(meta["success"])
        self.assertIn("title", meta)
        self.assertTrue(len(meta["title"]) > 0)

if __name__ == "__main__":
    unittest.main()
