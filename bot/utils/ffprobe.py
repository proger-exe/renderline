import subprocess
import json
from pathlib import Path


def get_video_duration(video_path: Path) -> float:
    """Get video duration in seconds using ffprobe"""
    try:
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(video_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        duration = float(data["format"]["duration"])
        return duration
    except (subprocess.CalledProcessError, KeyError, ValueError) as e:
        raise Exception(f"Failed to get video duration: {str(e)}")
