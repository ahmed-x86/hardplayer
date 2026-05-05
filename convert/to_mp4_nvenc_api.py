# convert/to_mp4_nvenc_api.py
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

class ToMp4NvencWorker(QThread):
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
            'ffmpeg', '-y', '-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda',
            '-i', self.input_path,
            '-c:v', 'h264_nvenc', '-preset', 'p6', '-tune', 'hq', '-b:v', '5M',
            '-c:a', 'aac',
            self.output_path
        ]
        try:
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
            )
            for line in self.process.stdout:
                if self._is_cancelled:
                    break
                self.progress.emit(line.strip())
            
            self.process.wait()
            if not self._is_cancelled and self.process.returncode == 0:
                self.finished.emit(self.output_path)
            elif not self._is_cancelled:
                self.error.emit("فشل التحويل. تأكد من دعم كرت الشاشة لـ NVENC.")
        except Exception as e:
            self.error.emit(str(e))

    def abort(self):
        self._is_cancelled = True
        if self.process:
            self.process.terminate()