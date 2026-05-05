# convert/to_davinci_api.py
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

class ToDavinciWorker(QThread):
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
            '-c:v', 'prores_ks', '-profile:v', '3', '-vendor', 'apl0', '-pix_fmt', 'yuv422p10le', # فيديو احترافي
            '-c:a', 'pcm_s16le', # صوت خام مدعوم في كل البرامج
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
            elif not self._is_cancelled:
                self.error.emit(f"خطأ في التحويل (Code: {self.process.returncode})")
        except Exception as e:
            self.error.emit(str(e))

    def abort(self):
        self._is_cancelled = True
        if self.process: self.process.terminate()