# convert/to_jpg_api.py
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

class ToJpgWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, input_path, output_path, timestamp="00:00:05"):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.timestamp = timestamp # الوقت الذي سيتم أخذ اللقطة منه
        self.process = None

    def run(self):
        # استخدام -ss قبل -i لتسريع البحث داخل الفيديو
        cmd = [
            'ffmpeg', '-y', '-ss', self.timestamp,
            '-i', self.input_path,
            '-frames:v', '1', '-q:v', '2',
            self.output_path
        ]
        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            self.process.wait()
            if self.process.returncode == 0:
                self.finished.emit(self.output_path)
            else:
                self.error.emit("فشل التقاط الصورة.")
        except Exception as e:
            self.error.emit(str(e))