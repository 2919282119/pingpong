import subprocess
import json
import logging
from pathlib import Path

from app.config import TARGET_FPS, TARGET_WIDTH, TARGET_HEIGHT, TEMP_DIR

logger = logging.getLogger(__name__)


class VideoInfo:
    def __init__(self, path: str, duration_s: float, fps: float,
                 width: int, height: int):
        self.path = path
        self.duration_s = duration_s
        self.fps = fps
        self.width = width
        self.height = height


def probe_video(path: str) -> dict:
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def get_video_info(path: str) -> VideoInfo:
    data = probe_video(path)
    fmt = data.get("format", {})
    duration_s = float(fmt.get("duration", 0))

    fps, width, height = 0.0, 0, 0
    for stream in data.get("streams", []):
        if stream["codec_type"] == "video":
            fps_str = stream.get("avg_frame_rate", "0/1")
            num, den = fps_str.split("/")
            fps = float(num) / float(den) if float(den) > 0 else 0
            width = stream.get("width", 0)
            height = stream.get("height", 0)
            break

    return VideoInfo(path=path, duration_s=duration_s, fps=fps,
                     width=width, height=height)


def preprocess_video(input_path: str) -> tuple[str, VideoInfo]:
    """Compress video to 720p/10fps and return (output_path, info)."""
    stem = Path(input_path).stem
    output_path = str(TEMP_DIR / f"pre_{stem}.mp4")

    logger.info("Preprocessing %s -> %s (%dp, %dfps)", input_path, output_path,
                TARGET_HEIGHT, TARGET_FPS)

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", f"fps={TARGET_FPS},scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-an",
        output_path,
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)

    info = get_video_info(output_path)
    logger.info("Preprocessed video: %.1fs, %dfps, %dx%d",
                info.duration_s, info.fps, info.width, info.height)
    return output_path, info
