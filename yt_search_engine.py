# yt_search_engine.py

import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

class YTSearchEngine(QThread):
    results_fetched = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, query):
        super().__init__()
        self.query = query

    def run(self):
        try:
            result = subprocess.run(
                [
                    "yt-dlp", 
                    f"ytsearch5:{self.query}", 
                    "--dump-json", 
                    "--flat-playlist", 
                    "--no-warnings", 
                    "--ignore-errors"
                ],
                capture_output=True, text=True, check=True
            )
            self.results_fetched.emit(result.stdout.strip())
        except subprocess.CalledProcessError as e:
            self.error_occurred.emit(f"❌ Error during yt-dlp search:\n{e.stderr}")
        except Exception as e:
            self.error_occurred.emit(f"❌ Unexpected Error:\n{str(e)}")