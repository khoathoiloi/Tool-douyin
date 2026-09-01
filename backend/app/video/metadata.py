import os
import re
import subprocess
import imageio_ffmpeg
from typing import Dict, Any

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

class VideoMetadataExtractor:
    @staticmethod
    def extract(video_path: str) -> Dict[str, Any]:
        if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
            return {
                "duration": 0.0,
                "width": 0,
                "height": 0,
                "fps": 30.0,
                "aspect_ratio": "9:16",
                "codec": "h264",
                "has_audio": False,
                "filesize": 0
            }

        filesize = os.path.getsize(video_path)
        cmd = [FFMPEG_EXE, "-i", video_path]
        proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="replace")
        _, stderr = proc.communicate()

        duration = 0.0
        width = 1080
        height = 1920
        fps = 30.0
        codec = "h264"
        has_audio = "Audio:" in stderr

        dur_m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", stderr)
        if dur_m:
            h, m, s = dur_m.groups()
            duration = float(h) * 3600 + float(m) * 60 + float(s)

        dim_m = re.search(r"Stream.*Video:.*,\s*(\d{2,5})x(\d{2,5})", stderr)
        if dim_m:
            width = int(dim_m.group(1))
            height = int(dim_m.group(2))

        fps_m = re.search(r"(\d+(?:\.\d+)?)\s*fps", stderr) or re.search(r"(\d+(?:\.\d+)?)\s*tbr", stderr)
        if fps_m:
            try:
                fps = float(fps_m.group(1))
            except Exception:
                pass

        codec_m = re.search(r"Video:\s*([a-zA-Z0-9_-]+)", stderr)
        if codec_m:
            codec = codec_m.group(1)

        aspect_ratio = f"{width}:{height}"
        if width > 0 and height > 0:
            ratio_val = width / height
            if 0.5 <= ratio_val <= 0.6:
                aspect_ratio = "9:16"
            elif 1.7 <= ratio_val <= 1.8:
                aspect_ratio = "16:9"
            elif 0.9 <= ratio_val <= 1.1:
                aspect_ratio = "1:1"
            elif 0.7 <= ratio_val <= 0.8:
                aspect_ratio = "3:4"

        return {
            "duration": round(duration, 2),
            "width": width,
            "height": height,
            "fps": round(fps, 1),
            "aspect_ratio": aspect_ratio,
            "codec": codec,
            "has_audio": has_audio,
            "filesize": filesize
        }
