# convert/to_mp4_api.py
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

class ToMp4Worker(QThread):
    progress = pyqtSignal(str) # إرسال المخرجات أو النسبة
    finished = pyqtSignal(str) # إرسال مسار الملف النهائي
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
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'aac', '-b:a', '128k',
            self.output_path
        ]
        try:
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, universal_newlines=True
            )
            for line in self.process.stdout:
                if self._is_cancelled:
                    break
                self.progress.emit(line.strip())
            
            self.process.wait()
            if self._is_cancelled:
                self.error.emit("تم إلغاء التحويل.")
            elif self.process.returncode == 0:
                self.finished.emit(self.output_path)
            else:
                self.error.emit(f"حدث خطأ أثناء التحويل (Code: {self.process.returncode})")
        except Exception as e:
            self.error.emit(f"استثناء: {str(e)}")

    def abort(self):
        self._is_cancelled = True
        if self.process:
            self.process.terminate()