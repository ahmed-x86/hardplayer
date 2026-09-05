# yt_subtitles.py

import subprocess
import json
from PyQt6.QtCore import QThread, pyqtSignal

class SubtitleFetcher(QThread):
    """
    خيط خلفي (Thread) لجلب قائمة الترجمات بدون تجميد واجهة المستخدم
    """
    # الإشارة ترسل قاموسين: الترجمات اليدوية، والترجمات التلقائية
    subtitles_fetched = pyqtSignal(dict, dict)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        manual_subs = {}
        auto_subs = {}
        try:
            # استخدام dump-json لجلب معلومات الفيديو بدون تحميله
            cmd = ["yt-dlp", "--dump-json", "--no-warnings", "--skip-download", self.url]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)

            # 1. استخراج الترجمات اليدوية
            subs = info.get("subtitles", {})
            for lang_code, formats in subs.items():
                name = formats[0].get("name", lang_code) if formats else lang_code
                manual_subs[lang_code] = name

            # 2. استخراج الترجمات التلقائية
            autos = info.get("automatic_captions", {})
            for lang_code, formats in autos.items():
                name = formats[0].get("name", lang_code) if formats else lang_code
                auto_subs[lang_code] = name

        except Exception as e:
            print(f"[*] ⚠️ Error fetching subtitles info: {e}")

        # إرسال البيانات لواجهة المستخدم
        self.subtitles_fetched.emit(manual_subs, auto_subs)

def apply_subtitle_args(cmd: list, dl_options: dict) -> list:
    """
    تقوم هذه الدالة بفحص خيارات التحميل وإضافة أوامر الترجمة المناسبة 
    إلى قائمة أوامر yt-dlp.
    """
    if dl_options and dl_options.get('subs'):
        cmd.extend(["--write-subs", "--write-auto-subs"])
        lang = dl_options.get('sub_lang', 'en,ar')
        if lang:
            cmd.extend(["--sub-langs", lang])
        cmd.extend(["--convert-subs", "srt", "--embed-subs"])
        
    return cmd