# yt_info_fetcher.py

import subprocess
import json
from PyQt6.QtCore import QThread, pyqtSignal
from yt_url_parser import clean_youtube_url

class YTInfoFetcher(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = clean_youtube_url(url)

    def run(self):
        try:
            result = subprocess.run(
                ["yt-dlp", "--dump-json", "--no-warnings", "--ignore-errors", self.url],
                capture_output=True, text=True, check=True
            )
            info = json.loads(result.stdout)
            self.finished.emit(info)
        except subprocess.CalledProcessError as e:
            self.error.emit(f"Process Error: {e.stderr}")
        except Exception as e:
            self.error.emit(str(e))