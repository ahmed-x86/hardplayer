# cli_parser.py

import argparse

def parse_cli_args():
    """
    معالجة أوامر التيرمنال للنسخة v11 (CLI-Friendly)
    """
    parser = argparse.ArgumentParser(description="HardPlayer v11 - Power User CLI Update")
    
    # مسار الملف أو الرابط (اختياري)
    parser.add_argument("path", nargs="?", default=None, 
                        help="Path to video file or YouTube URL")
    
    # تحديد كارت الشاشة يدوياً لتخطي نافذة السؤال
    parser.add_argument("-device", "--device", 
                        choices=['cpu', 'intel', 'amd', 'nvidia', 'old_nvidia'],
                        help="Force hardware decoding device (bypasses dialog)")
    
    # خيار البحث المباشر في يوتيوب من التيرمنال
    parser.add_argument("-search", "--search", action="store_true",
                        help="Treat the path argument as a YouTube search query")
                        
    # تحديد جودة اليوتيوب أو تشغيل كصوت فقط
    parser.add_argument("-quality", "--quality", 
                        choices=['best', '1080p', '720p', '480p', 'audio'],
                        help="Force YouTube playback quality (bypasses quality dialog)")
                        
    # نستخدم parse_known_args حتى لا يتعارض مع أي فلاج خاص بـ Qt
    args, unknown = parser.parse_known_args()
    return args