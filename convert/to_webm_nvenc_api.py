# convert/to_webm_nvenc_api.py
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

class ToWebmNvencWorker(QThread):
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
            'ffmpeg', '-y', '-hwaccel', 'cuda',
            '-i', self.input_path,
            '-c:v', 'av1_nvenc', '-preset', 'p6', '-b:v', '3M', # ترميز AV1 الخفيف جداً
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
            self.error.emit("فشل التحويل. تأكد أن كرت الشاشة لديك يدعم ترميز AV1.")

    def abort(self):
        self._is_cancelled = True
        if self.process: self.process.terminate()