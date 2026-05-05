# convert/to_davinci_by_cuda_api.py
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

class ToDavinciCudaDecodeWorker(QThread):
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
        # مطابق تماماً لمنطق السكربت الخاص بك: CUDA للفك + DNxHR SQ للترميز
        cmd = [
            "ffmpeg", "-y", "-hwaccel", "cuda", 
            "-i", self.input_path, 
            "-c:v", "dnxhd", "-profile:v", "dnxhr_sq", 
            "-pix_fmt", "yuv422p", "-c:a", "pcm_s16le", 
            self.output_path
        ]
        try:
            # استخدام stderr وقراءة الأسطر فوراً لضمان تحديث النسبة المئوية
            self.process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)
            for line in self.process.stderr:
                if self._is_cancelled: break
                self.progress.emit(line)
            
            self.process.wait()
            if self.process.returncode == 0 and not self._is_cancelled:
                self.finished.emit(self.output_path)
            elif not self._is_cancelled:
                self.error.emit("Conversion to DaVinci (CUDA) failed.")
        except Exception as e:
            self.error.emit(str(e))

    def abort(self):
        self._is_cancelled = True
        if self.process: self.process.terminate()