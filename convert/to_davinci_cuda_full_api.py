# convert/to_davinci_cuda_full_api.py
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

class ToDavinciCudaWorker(QThread):
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
        # مطابق للسكربت الذي يعمل معك في التيرمنال مع الـ vf
        cmd = [
            "ffmpeg", "-y", "-hwaccel", "cuda", 
            "-hwaccel_output_format", "cuda", 
            "-i", self.input_path, 
            "-vf", "scale_cuda=format=yuv422p", 
            "-c:v", "dnxhd", "-profile:v", "dnxhr_sq", 
            "-c:a", "pcm_s16le", 
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