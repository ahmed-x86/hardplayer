#!/usr/bin/env python3

import os
# Force X11 backend to prevent MPV from opening a separate window on Arch Linux / Wayland
os.environ["QT_QPA_PLATFORM"] = "xcb"
os.environ["FFMPEG_HWACCEL"] = "0"

import sys
import subprocess
import shutil
import locale
import mpv

from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                             QWidget, QPushButton, QFileDialog, QDialog, 
                             QHBoxLayout, QLineEdit, QLabel, QStackedWidget)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QFont

BASE = "#1e1e2a"
TEXT = "#cdd6f4"
MAUVE = "#cba6f7"
SURFACE0 = "#313244"

stylesheet = f"""
QMainWindow, QStackedWidget {{ background-color: {BASE}; border: none; }}
QDialog {{ background-color: {BASE}; border-radius: 10px; }}
QLabel {{ color: {TEXT}; background-color: transparent; }}
QPushButton {{ background-color: {SURFACE0}; color: {TEXT}; border: 2px solid {MAUVE}; border-radius: 8px; padding: 8px 16px; font-weight: bold; font-size: 14px; }}
QPushButton:hover {{ background-color: {MAUVE}; color: {BASE}; }}
QLineEdit {{ background-color: {SURFACE0}; color: {TEXT}; border: 1px solid {MAUVE}; border-radius: 6px; padding: 8px; font-size: 14px; }}
"""

# ---------------------------------------------------------
# GPU Detection Logic (From your script)
# ---------------------------------------------------------
def get_decoding_options():
    options = [("CPU (Software Decoding)", "no")]
    try:
        gpu_info = subprocess.check_output(["lspci"], text=True).lower()
    except:
        gpu_info = ""

    if "intel" in gpu_info:
        options.append(("Intel GPU", "vaapi"))

    if "amd" in gpu_info or "ati" in gpu_info:
        options.append(("AMD GPU", "vaapi"))

    if "nvidia" in gpu_info:
        if shutil.which("nvidia-smi"):
            try:
                cc_out = subprocess.check_output(["nvidia-smi", "--query-gpu=compute_cap", "--format=csv,noheader"], text=True)
                major_cc = int(cc_out.split('.')[0])
                if major_cc < 6:
                    options.append(("Nvidia GPU (Old Cards)", "vdpau"))
                else:
                    options.append(("Nvidia GPU (Modern Cards)", "nvdec"))
            except:
                options.append(("Nvidia GPU", "nvdec"))
        else:
            options.append(("Nvidia GPU", "nvdec"))

    try:
        lsmod_out = subprocess.getoutput("lsmod")
        if "nouveau" in lsmod_out.lower():
            options.append(("Nvidia Open Source Driver (Nouveau)", "vaapi"))
    except:
        pass

    return options

# ---------------------------------------------------------
# Decoding Selection Dialog
# ---------------------------------------------------------
class DecodingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hardware Decoding")
        self.setFixedSize(400, 250)
        self.setModal(True)
        self.selected_hwdec = "no" # Default to CPU

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        lbl = QLabel("🖥️ Select Decoding Device:", self)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(lbl)

        options = get_decoding_options()
        for name, hw_arg in options:
            btn = QPushButton(name)
            # Use default argument binding in lambda to capture the current hw_arg
            btn.clicked.connect(lambda checked, h=hw_arg: self.select_option(h))
            layout.addWidget(btn)

    def select_option(self, hw_arg):
        self.selected_hwdec = hw_arg
        self.accept()

# ---------------------------------------------------------
# Aspect Ratio Container to fix black borders
# ---------------------------------------------------------
class AspectRatioContainer(QWidget):
    def __init__(self, child_widget, bg_color):
        super().__init__()
        self.setStyleSheet(f"background-color: {bg_color};")
        self.child = child_widget
        self.child.setParent(self)
        
        # Disabled as QWidget doesn't support this attribute natively
        # self.child.setAspectRatioMode(Qt.AspectRatioMode.IgnoreAspectRatio)
        
        self.aspect_ratio = 16.0 / 9.0

    def resizeEvent(self, event):
        w = self.width()
        h = self.height()
        
        target_w = w
        target_h = int(w / self.aspect_ratio)
        
        if target_h > h:
            target_h = h
            target_w = int(h * self.aspect_ratio)
            
        x = (w - target_w) // 2
        y = (h - target_h) // 2
        
        self.child.setGeometry(x, y, target_w, target_h)
        super().resizeEvent(event)

# ---------------------------------------------------------
# FFmpeg Info Dialog (Triggered by 'I' key)
# ---------------------------------------------------------
class InfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("System FFmpeg Info")
        self.setFixedSize(500, 200)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        self.lbl = QLabel("System FFmpeg Version:", self)
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(self.lbl)
        
        self.info_text = QLabel(self)
        self.info_text.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.info_text.setWordWrap(True)
        self.info_text.setStyleSheet(f"font-family: monospace; font-size: 12px; color: {TEXT};")
        layout.addWidget(self.info_text)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        layout.addWidget(self.close_btn)
        
        self.get_ffmpeg_info()

    def get_ffmpeg_info(self):
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True, text=True, check=True
            )
            lines = result.stdout.strip().split('\n')[:2]
            self.info_text.setText("\n".join(lines))
        except FileNotFoundError:
            self.info_text.setText("❌ FFmpeg is NOT installed or NOT found in system PATH.")
        except Exception as e:
            self.info_text.setText(f"❌ Error executing FFmpeg: {str(e)}")

# ---------------------------------------------------------
# Startup Media Dialog
# ---------------------------------------------------------
class StartupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("HardPlayer - Open Media")
        self.setFixedSize(450, 180)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        self.lbl = QLabel("Select a local video file or enter a YouTube URL:", self)
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl)
        
        self.browse_btn = QPushButton("📁 Browse Local Video")
        self.browse_btn.clicked.connect(self.parent().browse_video)
        self.browse_btn.clicked.connect(self.accept)
        layout.addWidget(self.browse_btn)

        yt_layout = QHBoxLayout()
        self.yt_input = QLineEdit(self)
        self.yt_input.setPlaceholderText("https://youtube.com/...")
        self.yt_btn = QPushButton("▶ Play URL")
        self.yt_btn.clicked.connect(self.play_url)
        
        yt_layout.addWidget(self.yt_input)
        yt_layout.addWidget(self.yt_btn)
        layout.addLayout(yt_layout)

    def play_url(self):
        url = self.yt_input.text().strip()
        if url:
            self.parent().play_youtube(url)
            self.accept()

# ---------------------------------------------------------
# Main Window
# ---------------------------------------------------------
class HardPlayerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HardPlayer")
        self.resize(800, 600)
        
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        self.logo_widget = QWidget()
        logo_layout = QVBoxLayout(self.logo_widget)
        self.logo_label = QLabel("🎬\nHardPlayer")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setFont(QFont("Arial", 48, QFont.Weight.Bold))
        logo_layout.addWidget(self.logo_label)
        
        self.video_widget = QWidget()
        self.video_widget.setAttribute(Qt.WidgetAttribute.WA_DontCreateNativeAncestors)
        self.video_widget.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        
        self.video_container = AspectRatioContainer(self.video_widget, BASE)
        
        self.stack.addWidget(self.logo_widget)
        self.stack.addWidget(self.video_container)
        
        # إجبار المحرك على استخدام x11 لكي لا ينفصل عن النافذة في Wayland
        self.player = mpv.MPV(
            wid=str(int(self.video_widget.winId())),
            vo='x11',
            osc=False,
            input_default_bindings=False,
            input_vo_keyboard=False,
            keep_open=True
        )

        QTimer.singleShot(100, self.show_startup_dialog)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_P:
            if getattr(self.player, 'core_idle', True):
                self.show_startup_dialog()
        elif event.key() == Qt.Key.Key_I:
            self.show_info_dialog()
            
        super().keyPressEvent(event)

    def show_startup_dialog(self):
        dialog = StartupDialog(self)
        dialog.exec()

    def show_info_dialog(self):
        dialog = InfoDialog(self)
        dialog.exec()

    def ask_for_decoding_and_play(self, source):
        decoding_dialog = DecodingDialog(self)
        if decoding_dialog.exec() == QDialog.DialogCode.Accepted:
            selected_hwdec = decoding_dialog.selected_hwdec
            
            # تمرير خيار المعالج/الكارت إلى محرك MPV
            self.player['hwdec'] = selected_hwdec
            print(f"[*] Playing with hwdec: {selected_hwdec}")
            
            self.stack.setCurrentWidget(self.video_container)
            self.player.play(source)

    def browse_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "", "Video Files (*.mp4 *.mkv *.webm *.avi);;All Files (*)"
        )
        if file_path:
            self.ask_for_decoding_and_play(file_path)

    def play_youtube(self, yt_url):
        print("[*] Fetching YouTube direct stream URL...")
        try:
            result = subprocess.run(
                ["yt-dlp", "-f", "bestvideo[vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best", "-g", yt_url],
                capture_output=True, text=True, check=True
            )
            stream_url = result.stdout.strip().split('\n')[0]
            
            if stream_url:
                self.ask_for_decoding_and_play(stream_url)
        except Exception as e:
            print(f"❌ Error playing YouTube URL: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # حل مشكلة الانهيار (Segmentation fault) المطلوبة
    locale.setlocale(locale.LC_NUMERIC, "C")
    
    app.setStyleSheet(stylesheet)
    window = HardPlayerWindow()
    window.show()
    sys.exit(app.exec())