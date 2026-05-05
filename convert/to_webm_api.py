# convert/to_webm_api.py
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

class ToWebmWorker(QThread):
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
            '-c:v', 'libvpx-vp9', '-crf', '30', '-b:v', '0', # ضغط ذكي
            '-c:a', 'libopus',
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