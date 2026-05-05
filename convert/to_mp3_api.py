# convert/to_mp3_api.py
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

class ToMp3Worker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, input_path, output_path):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.process = None
        self._is_cancelled = False

    def run(self):
        cmd = [
            'ffmpeg', '-y', '-i', self.input_path,
            '-vn', # تجاهل الفيديو
            '-c:a', 'libmp3lame', '-q:a', '2', # جودة MP3 ممتازة
            self.output_path
        ]
        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in self.process.stdout:
                if self._is_cancelled: break
                self.progress.emit(line.strip())
            
            self.process.wait()
            if self.process.returncode == 0 and not self._is_cancelled:
                self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))

    def abort(self):
        self._is_cancelled = True
        if self.process: self.process.terminate()