# yt_url_parser.py

import re
from urllib.parse import urlparse, parse_qs

def clean_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', str(text))

def clean_youtube_url(url):
    try:
        parsed_url = urlparse(url)
        
        if 'youtube.com' in parsed_url.netloc and '/watch' in parsed_url.path:
            query_params = parse_qs(parsed_url.query)
            if 'v' in query_params:
                video_id = query_params['v'][0]
                return f"https://www.youtube.com/watch?v={video_id}"
        
        elif 'youtu.be' in parsed_url.netloc:
            video_id = parsed_url.path.lstrip('/')
            return f"https://www.youtube.com/watch?v={video_id}"
            
        elif 'youtube.com' in parsed_url.netloc and '/shorts/' in parsed_url.path:
            video_id = parsed_url.path.split('/shorts/')[-1].split('?')[0]
            return f"https://www.youtube.com/watch?v={video_id}"
            
    except Exception as e:
        print(f"[*] ⚠️ URL parsing error: {e}")
        
    return url