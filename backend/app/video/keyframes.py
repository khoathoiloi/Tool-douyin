import os
import subprocess
import imageio_ffmpeg
from typing import List, Dict, Any
from .metadata import VideoMetadataExtractor

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

class AdaptiveKeyframeExtractor:
    @staticmethod
    def extract_adaptive_keyframes(
        video_path: str,
        output_dir: str,
        max_frames: int = 10
    ) -> List[Dict[str, Any]]:
        os.makedirs(output_dir, exist_ok=True)
        meta = VideoMetadataExtractor.extract(video_path)
        duration = meta.get("duration", 10.0)
        if duration <= 0:
            return []

        # Adaptive count: short video = 3-5 frames, medium = 6-8 frames, long = 10 frames
        if duration <= 10:
            target_count = 4
        elif duration <= 30:
            target_count = 6
        else:
            target_count = min(max_frames, 10)

        timestamps = []
        # First frame (0.2s), last frame (duration - 0.5s), and intermediate scene intervals
        timestamps.append(0.2)
        step = duration / (target_count - 1)
        for i in range(1, target_count - 1):
            timestamps.append(round(i * step, 2))
        timestamps.append(max(0.5, round(duration - 0.5, 2)))

        keyframes_info = []
        for idx, ts in enumerate(timestamps):
            out_file = os.path.join(output_dir, f"keyframe_{idx+1:02d}_{int(ts*100)}ms.jpg")
            cmd = [
                FFMPEG_EXE, "-y", "-ss", str(ts),
                "-i", video_path,
                "-vframes", "1",
                "-q:v", "2",
                out_file
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(out_file) and os.path.getsize(out_file) > 0:
                keyframes_info.append({
                    "path": out_file,
                    "timestamp": ts,
                    "frame_index": idx + 1,
                    "is_boundary": (idx == 0 or idx == len(timestamps) - 1)
                })

        return keyframes_info
