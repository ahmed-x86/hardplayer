# yt_assets_fetcher.py

import urllib.request
from PyQt6.QtCore import QThread, pyqtSignal

class ImageFetcher(QThread):
    image_fetched = pyqtSignal(str, bytes)

    def __init__(self, url, identifier):
        super().__init__()
        self.url = url
        self.identifier = identifier

    def run(self):
        try:
            req = urllib.request.Request(self.url, headers={'User-Agent': 'Mozilla/5.0'})
            data = urllib.request.urlopen(req).read()
            self.image_fetched.emit(self.identifier, data)
        except Exception:
            pass 