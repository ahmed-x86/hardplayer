# convert/to_webm_by_cuda_api.py
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

class ToWebmCudaWorker(QThread):
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
            "ffmpeg", "-y", "-hwaccel", "cuda", 
            "-i", self.input_path, 
            "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "30", 
            "-c:a", "libopus", 
            self.output_path
        ]
        try:
            self.process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)
            for line in self.process.stderr:
                if self._is_cancelled: break
                self.progress.emit(line)
            
            self.process.wait()
            if self.process.returncode == 0 and not self._is_cancelled:
                self.finished.emit(self.output_path)
            elif not self._is_cancelled:
                self.error.emit("Conversion failed.")
        except Exception as e:
            self.error.emit(str(e))

    def abort(self):
        self._is_cancelled = True
        if self.process: self.process.terminate()