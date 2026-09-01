"""
Core Module: Exporter & Batch Video Downloader
Exports extracted Douyin videos to Excel (.xlsx), CSV, TXT, and downloads video files safely without leaving 0 KB files.
"""

import os
import re
import csv
import time
import requests
import pandas as pd
from typing import List, Dict, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

MOBILE_USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
DESKTOP_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

class DouyinExporter:
    @staticmethod
    def export_to_excel(videos: List[Dict[str, Any]], filepath: str) -> str:
        rows = []
        for i, v in enumerate(videos, 1):
            web_link = v.get("web_url") or v.get("share_url") or f"https://www.douyin.com/video/{v.get('aweme_id')}"
            download_link = v.get("video_no_watermark_url") or web_link
            rows.append({
                "STT": i,
                "ID Video": v.get("aweme_id", ""),
                "Tiêu đề Video": v.get("title", ""),
                "Tác giả": v.get("author_name", ""),
                "Lượt Thích (Likes)": v.get("digg_count", 0),
                "Lượt Bình luận": v.get("comment_count", 0),
                "Lượt Chia sẻ": v.get("share_count", 0),
                "Thời lượng (giây)": v.get("duration", 0),
                "Thời gian đăng": v.get("create_time", ""),
                "Link Xem Trên Web (Click Xem Trực Tiếp)": web_link,
                "Link Tải Video": download_link,
                "Hashtags": " ".join(v.get("hashtags", []))
            })

        df = pd.DataFrame(rows)
        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Douyin Videos")

        return filepath

    @staticmethod
    def export_to_csv(videos: List[Dict[str, Any]], filepath: str) -> str:
        keys = ["STT", "ID", "Title", "Author", "Likes", "Comments", "Shares", "Duration_Sec", "Publish_Time", "Web_Watch_URL", "Download_URL"]
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(keys)
            for i, v in enumerate(videos, 1):
                web_link = v.get("web_url") or v.get("share_url") or f"https://www.douyin.com/video/{v.get('aweme_id')}"
                download_link = v.get("video_no_watermark_url") or web_link
                writer.writerow([
                    i,
                    v.get("aweme_id", ""),
                    v.get("title", ""),
                    v.get("author_name", ""),
                    v.get("digg_count", 0),
                    v.get("comment_count", 0),
                    v.get("share_count", 0),
                    v.get("duration", 0),
                    v.get("create_time", ""),
                    web_link,
                    download_link
                ])
        return filepath

    @staticmethod
    def export_to_txt(videos: List[Dict[str, Any]], filepath: str, only_links: bool = False) -> str:
        with open(filepath, "w", encoding="utf-8") as f:
            for i, v in enumerate(videos, 1):
                web_link = v.get("web_url") or v.get("share_url") or f"https://www.douyin.com/video/{v.get('aweme_id')}"
                download_link = v.get("video_no_watermark_url") or web_link
                if only_links:
                    f.write(str(web_link) + "\n")
                else:
                    f.write(f"[{i}] {v.get('title', '')}\n")
                    f.write(f"    Tác giả: {v.get('author_name', '')} | Likes: {v.get('digg_count', 0):,}\n")
                    f.write(f"    Link xem Web: {web_link}\n")
                    f.write(f"    Link tải HD : {download_link}\n\n")
        return filepath

    @staticmethod
    def download_single_video(video: Dict[str, Any], output_dir: str, cookie: str = "") -> Dict[str, Any]:
        """
        Downloads a video cleanly. Only saves if content is valid MP4 data (> 10 KB).
        """
        aweme_id = str(video.get("aweme_id", f"video_{int(time.time())}"))
        raw_title = video.get("title", aweme_id)
        safe_title = re.sub(r'[\\/*?:"<>|]', "", raw_title)[:50].strip()
        filename = f"{aweme_id}_{safe_title}.mp4"
        filepath = os.path.join(output_dir, filename)

        candidate_urls = []
        if video.get("video_no_watermark_url"):
            candidate_urls.append(video["video_no_watermark_url"])
        candidate_urls.append(f"https://aweme.snssdk.com/aweme/v1/play/?video_id={aweme_id}&ratio=1080p&line=0")
        candidate_urls.append(f"https://www.douyin.com/aweme/v1/play/?video_id={aweme_id}&ratio=1080p&line=0")

        headers = {
            "User-Agent": MOBILE_USER_AGENT,
            "Referer": "https://www.douyin.com/"
        }
        if cookie:
            headers["Cookie"] = cookie

        for url in candidate_urls:
            try:
                resp = requests.get(url, headers=headers, stream=True, allow_redirects=True, timeout=15)
                if resp.status_code == 200 and "video" in resp.headers.get("Content-Type", "video"):
                    temp_file = filepath + ".tmp"
                    written = 0
                    with open(temp_file, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=65536):
                            if chunk:
                                f.write(chunk)
                                written += len(chunk)
                    if written > 10240: # Valid video file > 10KB
                        if os.path.exists(filepath):
                            os.remove(filepath)
                        os.rename(temp_file, filepath)
                        return {"success": True, "id": aweme_id, "filepath": filepath, "bytes": written}
                    else:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
            except Exception:
                pass

        # If direct download did not succeed (due to Douyin anti-hotlink check), clean up temp
        return {
            "success": False,
            "id": aweme_id,
            "error": "Douyin bảo vệ luồng video. Bạn có thể mở xem trực tiếp trên trình duyệt hoặc thêm Cookie Douyin trong Cài đặt."
        }

    @classmethod
    def batch_download(
        cls,
        videos: List[Dict[str, Any]],
        output_dir: str,
        max_workers: int = 4,
        cookie: str = "",
        progress_callback: Optional[Callable[[int, int, Dict[str, Any]], None]] = None
    ) -> List[Dict[str, Any]]:
        os.makedirs(output_dir, exist_ok=True)
        results = []
        total = len(videos)
        completed = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_video = {
                executor.submit(cls.download_single_video, v, output_dir, cookie): v
                for v in videos
            }
            for future in as_completed(future_to_video):
                res = future.result()
                results.append(res)
                completed += 1
                if progress_callback:
                    progress_callback(completed, total, res)

        return results
