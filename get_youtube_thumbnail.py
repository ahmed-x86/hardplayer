# get_youtube_thumbnail.py
import re

def get_youtube_thumbnail(url):
    """
    Extracts the video ID from a YouTube URL and returns the high-quality thumbnail link.
    Supports: Standard, Shortened (youtu.be), Embed, Shorts, and Live URLs.
    """
    if not url or not ('youtube.com' in url or 'youtu.be' in url):
        return None
    
    # Comprehensive regex pattern for all known YouTube URL formats
    regex = r'(?:v=|youtu\.be\/|embed\/|shorts\/|live\/)([^&?#]+)'
    match = re.search(regex, url)
    
    if match:
        video_id = match.group(1)
        # Using hqdefault ensures a thumbnail is returned for almost any video
        return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    
    return None