# top_menu_convert.py

import os
import re
import subprocess

# الرقعة السحرية لإصلاح تجميد شريط التقدم للـ FFmpeg
original_popen = subprocess.Popen

def patched_popen(cmd, *args, **kwargs):
    if isinstance(cmd, list) and cmd and cmd[0] == 'ffmpeg':
        if '-progress' not in cmd:
            cmd.insert(1, '-progress')
            cmd.insert(2, 'pipe:1')
    return original_popen(cmd, *args, **kwargs)

subprocess.Popen = patched_popen

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QMenu
from ui_components_convert import ConversionDialogUI

# استيراد جميع ملفات الـ API الـ 18
from convert.to_mp4_api import ToMp4Worker
from convert.to_mp4_by_cuda_api import ToMp4CudaWorker
from convert.to_mp4_nvenc_api import ToMp4NvencWorker

from convert.to_mkv_api import ToMkvWorker
from convert.to_mkv_by_cuda_api import ToMkvCudaWorker
from convert.to_mkv_nvenc_api import ToMkvNvencWorker

from convert.to_webm_api import ToWebmWorker
from convert.to_webm_by_cuda_api import ToWebmCudaWorker
from convert.to_webm_nvenc_api import ToWebmNvencWorker

from convert.to_davinci_api import ToDavinciWorker
from convert.to_davinci_by_cuda_api import ToDavinciCudaDecodeWorker
from convert.to_davinci_cuda_full_api import ToDavinciCudaWorker

from convert.to_mp3_api import ToMp3Worker
from convert.extract_audio_api import ExtractAudioWorker
from convert.mute_video_api import MuteVideoWorker

from convert.to_gif_api import ToGifWorker
from convert.to_jpg_api import ToJpgWorker
from convert.to_webp_api import ToWebpWorker


class ConvertMenuManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.worker = None
        self.dialog = None
        self.setup_menu()

    def setup_menu(self):
        menubar = self.main_window.menuBar()
        convert_menu = menubar.addMenu("Converter 🔄")

        video_menu = convert_menu.addMenu("Video 🎬")
        self._add_action(video_menu, "To MP4", "To MP4")
        self._add_action(video_menu, "To MKV", "To MKV")
        self._add_action(video_menu, "To WebM", "To WebM")
        self._add_action(video_menu, "To DaVinci", "To DaVinci")
        self._add_action(video_menu, "Mute Video", "Mute Video")

        audio_menu = convert_menu.addMenu("Audio 🎵")
        self._add_action(audio_menu, "To MP3", "To MP3")
        self._add_action(audio_menu, "Extract Audio", "Extract Audio")

        image_menu = convert_menu.addMenu("Image 🖼️")
        self._add_action(image_menu, "To JPG", "To JPG")
        self._add_action(image_menu, "To WebP", "To WebP")
        self._add_action(image_menu, "To GIF", "To GIF")

    def _add_action(self, parent_menu, title, mode):
        action = QAction(title, self.main_window)
        action.triggered.connect(lambda ch, m=mode: self.open_convert_dialog(m))
        parent_menu.addAction(action)

    def open_convert_dialog(self, mode):
        self.dialog = ConversionDialogUI(mode, self.main_window)
        self.dialog.btn_browse.clicked.connect(self.select_input_file)
        self.dialog.cancel_requested.connect(self.handle_cancel)
        
        for btn_name, btn_obj in self.dialog.action_buttons.items():
            btn_obj.clicked.connect(lambda ch, m=mode, b=btn_name: self.start_conversion(m, b))
            
        self.dialog.exec()

    def select_input_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self.dialog, "Select Media File", "", "All Files (*.*)")
        if file_path:
            self.dialog.input_file = file_path
            self.dialog.lbl_file.setText(os.path.basename(file_path))
            self.dialog.extract_metadata(file_path)

    def start_conversion(self, mode, button_name):
        # منع التشغيل إذا لم يتم اختيار ملف
        if not self.dialog.input_file:
            QMessageBox.warning(self.dialog, "Warning", "Please select a file first.")
            return

        base_name, _ = os.path.splitext(self.dialog.input_file)
        in_file = self.dialog.input_file
        out_file = ""

        if mode == "To MP4":
            out_file = f"{base_name}_converted.mp4"
            if button_name == "By CPU": self.worker = ToMp4Worker(in_file, out_file)
            elif button_name == "By CUDA": self.worker = ToMp4CudaWorker(in_file, out_file)
            elif button_name == "By NVENC": self.worker = ToMp4NvencWorker(in_file, out_file)

        elif mode == "To MKV":
            out_file = f"{base_name}_converted.mkv"
            if button_name == "By CPU": self.worker = ToMkvWorker(in_file, out_file)
            elif button_name == "By CUDA": self.worker = ToMkvCudaWorker(in_file, out_file)
            elif button_name == "By NVENC": self.worker = ToMkvNvencWorker(in_file, out_file)

        elif mode == "To WebM":
            out_file = f"{base_name}_converted.webm"
            if button_name == "By CPU": self.worker = ToWebmWorker(in_file, out_file)
            elif button_name == "By CUDA": self.worker = ToWebmCudaWorker(in_file, out_file)
            elif button_name == "By NVENC": self.worker = ToWebmNvencWorker(in_file, out_file)

        elif mode == "To DaVinci":
            out_file = f"{base_name}_davinci.mov"
            if button_name == "By CPU": self.worker = ToDavinciWorker(in_file, out_file)
            elif button_name == "By CUDA": self.worker = ToDavinciCudaDecodeWorker(in_file, out_file)
            elif button_name == "By CUDA FULL": self.worker = ToDavinciCudaWorker(in_file, out_file)

        elif mode == "Mute Video":
            out_file = f"{base_name}_muted.mp4"
            self.worker = MuteVideoWorker(in_file, out_file)

        elif mode == "To MP3":
            out_file = f"{base_name}_audio.mp3"
            self.worker = ToMp3Worker(in_file, out_file)

        elif mode == "Extract Audio":
            out_file = f"{base_name}_extracted.m4a"
            self.worker = ExtractAudioWorker(in_file, out_file)

        elif mode == "To JPG":
            out_file = f"{base_name}_frame.jpg"
            self.worker = ToJpgWorker(in_file, out_file)
            
        elif mode == "To WebP":
            out_file = f"{base_name}_animated.webp"
            self.worker = ToWebpWorker(in_file, out_file)
            
        elif mode == "To GIF":
            out_file = f"{base_name}_animated.gif"
            self.worker = ToGifWorker(in_file, out_file)

        if self.worker:
            self.dialog.output_file = out_file
            self.dialog.is_processing = True 
            
            self.worker.progress.connect(self.update_progress)
            self.worker.finished.connect(self.conversion_finished)
            self.worker.error.connect(self.conversion_error)
            
            for btn in self.dialog.action_buttons.values():
                btn.setEnabled(False)
            self.dialog.btn_browse.setEnabled(False)
            
            self.dialog.progress_bar.setValue(0)
            self.dialog.progress_bar.setMaximum(100) 
            self.dialog.lbl_status.setText(f"Processing ({button_name})...")
            
            self.worker.start()

    def update_progress(self, text):
        speed_match = re.search(r"speed=\s*([\d\.]+)x", text)
        if speed_match:
            self.dialog.last_speed = speed_match.group(1)

        time_match = re.search(r"(?:out_)?time=\s*(\d+):(\d{2}):([\d\.]+)", text)
        
        if time_match:
            hours, minutes, seconds = time_match.groups()
            current_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            speed_str = f" | Speed: {getattr(self.dialog, 'last_speed', '0.0')}x"
            
            # إذا استطعنا التقاط المدة، نحسب النسبة المئوية
            if hasattr(self.dialog, 'total_duration') and self.dialog.total_duration > 0:
                percent = (current_seconds / self.dialog.total_duration) * 100
                percent = min(100, max(0, percent)) 
                
                self.dialog.progress_bar.setValue(int(percent))
                self.dialog.progress_bar.setFormat(f"{percent:.1f}%")
                self.dialog.lbl_status.setText(f"Converting... {percent:.1f}% {speed_str}")
            # إذا كانت المدة مجهولة (النسبة غير ممكنة)، نعرض الوقت المنقضي
            else:
                self.dialog.progress_bar.setMaximum(0) # تفعيل الحركة المستمرة
                sec_display = seconds[:5] # لتجنب كثرة الأرقام العشرية
                self.dialog.lbl_status.setText(f"Converting... Time: {hours}:{minutes}:{sec_display} {speed_str}")

    def conversion_finished(self, out_path):
        self.dialog.progress_bar.setMaximum(100)
        self.dialog.progress_bar.setValue(100)
        self.dialog.progress_bar.setFormat("100.0%")
        self.dialog.lbl_status.setText("Conversion Successful! ✅")
        self.reset_ui()
        QMessageBox.information(self.dialog, "Success", f"File successfully saved to:\n{out_path}")

    def conversion_error(self, err_msg):
        self.dialog.progress_bar.setMaximum(100)
        self.dialog.progress_bar.setValue(0)
        self.dialog.lbl_status.setText("Error or Cancelled. ❌")
        self.reset_ui()
        if "cancelled" not in err_msg.lower() and "إلغاء" not in err_msg:
            QMessageBox.critical(self.dialog, "Error", err_msg)

    def handle_cancel(self, delete_files):
        if self.worker and self.worker.isRunning():
            self.worker.abort()
            self.worker.wait() 
            
            if delete_files and os.path.exists(self.dialog.output_file):
                try:
                    os.remove(self.dialog.output_file)
                    print(f"[*] 🗑️ Deleted incomplete file: {self.dialog.output_file}")
                except Exception as e:
                    print(f"[*] ⚠️ Could not delete file: {e}")
            
            self.dialog.lbl_status.setText("Processing cancelled.")
            self.reset_ui()

    def reset_ui(self):
        self.dialog.is_processing = False
        for btn in self.dialog.action_buttons.values():
            btn.setEnabled(True)
        self.dialog.btn_browse.setEnabled(True)
        self.worker = None