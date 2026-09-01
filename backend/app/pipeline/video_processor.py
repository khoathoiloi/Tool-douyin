import os
import subprocess
import json
import imageio_ffmpeg
from typing import List, Dict, Any, Tuple

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

class VideoProcessor:
    @staticmethod
    def get_video_metadata(video_path: str) -> Dict[str, Any]:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        filesize = os.path.getsize(video_path)
        # Run ffmpeg to get duration and dimensions
        cmd = [FFMPEG_EXE, "-i", video_path]
        proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="replace")
        _, stderr = proc.communicate()
        
        duration = 0.0
        width = 0
        height = 0
        
        import re
        dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", stderr)
        if dur_match:
            hours, minutes, seconds = dur_match.groups()
            duration = float(hours) * 3600 + float(minutes) * 60 + float(seconds)
            
        dim_match = re.search(r"Stream.*Video:.*,\s*(\d{2,5})x(\d{2,5})", stderr)
        if dim_match:
            width = int(dim_match.group(1))
            height = int(dim_match.group(2))
            
        return {
            "filesize": filesize,
            "duration": round(duration, 2),
            "width": width,
            "height": height
        }

    @staticmethod
    def extract_frames(video_path: str, output_dir: str, num_frames: int = 5) -> List[str]:
        os.makedirs(output_dir, exist_ok=True)
        meta = VideoProcessor.get_video_metadata(video_path)
        duration = meta.get("duration", 10.0)
        if duration <= 0:
            duration = 10.0
            
        frame_paths = []
        step = max(0.5, duration / (num_frames + 1))
        
        for i in range(1, num_frames + 1):
            ts = i * step
            out_file = os.path.join(output_dir, f"frame_{i:02d}.jpg")
            cmd = [
                FFMPEG_EXE, "-y", "-ss", str(round(ts, 2)),
                "-i", video_path,
                "-vframes", "1",
                "-q:v", "2",
                out_file
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(out_file) and os.path.getsize(out_file) > 0:
                frame_paths.append(out_file)
                
        return frame_paths

    @staticmethod
    def extract_audio(video_path: str, output_audio_path: str) -> str:
        os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)
        cmd = [
            FFMPEG_EXE, "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "libmp3lame",
            "-q:a", "4",
            output_audio_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(output_audio_path) and os.path.getsize(output_audio_path) > 0:
            return output_audio_path
        return ""
