# thumbnail_gen.py

import os
import subprocess
import hashlib
from pathlib import Path

def get_local_thumbnail(video_path):
    """
    Extracts or finds a thumbnail for a local video.
    Priority: 1. Embedded artwork -> 2. Sidecar file -> 3. Generated fallback/Cache.
    """
    if not video_path or not os.path.isfile(video_path):
        return None
    
    video_p = Path(video_path)
    
    # Prepare Cache Directory for HardPlayer
    cache_dir = Path.home() / ".cache" / "hardplayer" / "thumbnails"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    path_hash = hashlib.md5(str(video_p).encode('utf-8')).hexdigest()
    thumb_path = cache_dir / f"{path_hash}.jpg"

    # 1. Priority: Try to extract Embedded Thumbnail (Cover Art)
    # This is preferred if yt-dlp embedded the thumbnail into the file.
    if not thumb_path.exists():
        extract_cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(video_p),
            "-map", "0:v", "-map", "-0:V", 
            "-c", "copy", "-frames:v", "1",
            str(thumb_path)
        ]
        try:
            result = subprocess.run(extract_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if result.returncode == 0 and thumb_path.exists() and thumb_path.stat().st_size > 0:
                return str(thumb_path)
        except Exception:
            pass
    else:
        # If it exists in cache from a previous embedded extraction or generation
        return str(thumb_path)

    # 2. Priority: Check for Sidecar files (same name, different extension)
    # Helpful if the user keeps images alongside videos.
    image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    for ext in image_extensions:
        sidecar_path = video_p.with_suffix(ext)
        if sidecar_path.exists():
            return str(sidecar_path)

    # 3. Priority: Fallback - Generate thumbnail from frame at 00:00:05
    gen_cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-ss", "00:00:05", 
        "-i", str(video_p),
        "-vframes", "1",
        "-vf", "scale=320:-1", 
        str(thumb_path)
    ]
    
    try:
        subprocess.run(gen_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return str(thumb_path)
    except Exception:
        return None