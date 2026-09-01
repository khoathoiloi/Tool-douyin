import os
import re
import urllib.parse
import requests
import uuid
import time
from typing import Dict, Any, Optional

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

class DouyinUrlParser:
    @staticmethod
    def is_valid_url(url: str) -> bool:
        regex = r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*"
        return bool(re.match(regex, url.strip()))

    @staticmethod
    def is_douyin_or_tiktok_url(url: str) -> bool:
        u = url.lower()
        return any(domain in u for domain in [
            "douyin.com", "iesdouyin.com", "v.douyin.com",
            "tiktok.com", "vt.tiktok.com"
        ])

    @classmethod
    def parse_and_fetch_metadata(cls, raw_url: str, upload_dir: str) -> Dict[str, Any]:
        match = re.search(r"https?://[^\s]+", raw_url)
        if not match:
            return {
                "success": False,
                "error_code": "INVALID_URL",
                "error": "Đường dẫn không hợp lệ. Vui lòng dán link Douyin hoặc TikTok."
            }

        target_url = match.group(0).strip()
        title = ""
        author = "Creator"
        cover_url = ""
        video_download_url = ""
        remote_id = ""
        final_url = target_url

        session = requests.Session()
        session.headers.update({"User-Agent": DEFAULT_USER_AGENT})

        # 1. Check TikTok OEMBED
        if "tiktok.com" in target_url:
            try:
                oembed = f"https://www.tiktok.com/oembed?url={urllib.parse.quote(target_url)}"
                resp = session.get(oembed, timeout=8)
                if resp.status_code == 200:
                    d = resp.json()
                    title = d.get("title", "")
                    author = d.get("author_name", author)
                    cover_url = d.get("thumbnail_url", "")
                    final_url = d.get("author_url", target_url)
            except Exception as e:
                print(f"[UrlParser] TikTok OEMBED notice: {e}")

        # 2. Check Douyin Redirect and OpenGraph
        try:
            r = session.get(target_url, allow_redirects=True, timeout=10)
            final_url = r.url

            # Extract Douyin Video ID
            id_m = re.search(r"video/(\d+)", final_url) or re.search(r"(\d{18,20})", final_url)
            if id_m:
                remote_id = id_m.group(1)
                video_download_url = f"https://aweme.snssdk.com/aweme/v1/play/?video_id={remote_id}&ratio=1080p&line=0"

            html = r.text
            if not title:
                og_title = re.search(r'<meta\s+property="og:title"\s+content="([^"]*)"', html)
                if og_title:
                    title = og_title.group(1)
                else:
                    t_match = re.search(r'<title>([^<]*)</title>', html)
                    if t_match:
                        title = t_match.group(1).replace(" - 抖音", "").replace(" - TikTok", "").strip()

            if not cover_url:
                og_img = re.search(r'<meta\s+property="og:image"\s+content="([^"]*)"', html)
                if og_img:
                    cover_url = og_img.group(1)
        except Exception as e:
            print(f"[UrlParser] Douyin HTML fetch notice: {e}")

        if not title:
            title = f"Douyin Video #{remote_id or int(time.time())}"

        # 3. Attempt safe video file download if playable URL is available
        saved_video_path = ""
        if video_download_url:
            try:
                vid_filename = f"{uuid.uuid4()}.mp4"
                temp_path = os.path.join(upload_dir, vid_filename)
                v_resp = session.get(video_download_url, stream=True, timeout=12)
                if v_resp.status_code == 200:
                    with open(temp_path, "wb") as f:
                        for chunk in v_resp.iter_content(chunk_size=1024 * 64):
                            if chunk:
                                f.write(chunk)
                    if os.path.exists(temp_path) and os.path.getsize(temp_path) > 10 * 1024:
                        saved_video_path = temp_path
            except Exception as e:
                print(f"[UrlParser] Video download notice: {e}")

        return {
            "success": True,
            "url": final_url,
            "remote_id": remote_id,
            "title": title,
            "author": author,
            "cover_url": cover_url,
            "video_path": saved_video_path,
            "has_downloaded_video": bool(saved_video_path),
            "hashtags": re.findall(r"#([^#\s]+)", title)
        }
