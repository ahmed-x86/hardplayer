# thumbnail_gen.py

import os
import subprocess
import hashlib
from pathlib import Path

def get_local_thumbnail(video_path):
    """
   It extracts a thumbnail image of a local video and saves it to the cache folder.
    """
    if not video_path or not os.path.isfile(video_path):
        return None
    

    cache_dir = Path.home() / ".cache" / "hardplayer" / "thumbnails"
    cache_dir.mkdir(parents=True, exist_ok=True)
    

    path_hash = hashlib.md5(video_path.encode('utf-8')).hexdigest()
    thumb_path = cache_dir / f"{path_hash}.jpg"
    
    
    if thumb_path.exists():
        return str(thumb_path)
        

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-ss", "00:00:05", 
        "-i", video_path,
        "-vframes", "1",
        "-vf", "scale=320:-1", 
        str(thumb_path)
    ]
    
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return str(thumb_path)
    except Exception:
        return None