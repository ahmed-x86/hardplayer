# convert/to_mkv_nvenc_api.py
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

class ToMkvNvencWorker(QThread):
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
            'ffmpeg', '-y', '-progress', 'pipe:1', '-hwaccel', 'cuda',
            '-i', self.input_path,
            '-c:v', 'h264_nvenc', '-preset', 'p5', '-b:v', '5M',
            '-c:a', 'ac3', # ترميز صوت مناسب لملفات MKV
            self.output_path
        ]
        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
            for line in self.process.stdout:
                if self._is_cancelled: break
                self.progress.emit(line.strip())
            
            self.process.wait()
            if not self._is_cancelled and self.process.returncode == 0:
                self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))

    def abort(self):
        self._is_cancelled = True
        if self.process: self.process.terminate()