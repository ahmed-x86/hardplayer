# convert/to_mkv_api.py
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

class ToMkvWorker(QThread):
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
            'ffmpeg', '-y', '-progress', 'pipe:1', '-i', self.input_path,
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
            '-c:a', 'ac3', # صوت السينما القياسي
            self.output_path
        ]
        try:
            # التعديل: تفعيل bufsize=1 و universal_newlines لقراءة المخرجات فوراً
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
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