#!/usr/bin/env python3

import os
# Force X11 backend to prevent MPV from opening a separate window on Arch Linux / Wayland
os.environ["QT_QPA_PLATFORM"] = "xcb"
# خدعة قوية: إخفاء Wayland عن المحرك لكي لا يتجاهل نافذة الدمج (WID)
if "WAYLAND_DISPLAY" in os.environ:
    del os.environ["WAYLAND_DISPLAY"]

import sys
import subprocess
import shutil
import locale
import mpv

from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                             QWidget, QPushButton, QFileDialog, QDialog, 
                             QHBoxLayout, QLineEdit, QLabel, QStackedWidget,
                             QTextEdit)
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
QTextEdit {{ background-color: {SURFACE0}; color: {TEXT}; border: 1px solid {MAUVE}; border-radius: 6px; padding: 8px; font-family: monospace; font-size: 13px; }}
"""

# ---------------------------------------------------------
# GPU Detection Logic
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
                    options.append(("Nvidia GPU (Maxwell/Older)", "nvdec-copy"))
                else:
                    options.append(("Nvidia GPU (Modern Cards)", "nvdec"))
            except:
                options.append(("Nvidia GPU", "nvdec-copy"))
        else:
            options.append(("Nvidia GPU", "nvdec-copy"))

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
        self.selected_hwdec = "no"

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        lbl = QLabel("🖥️ Select Decoding Device:", self)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(lbl)

        options = get_decoding_options()
        for name, hw_arg in options:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, h=hw_arg: self.select_option(h))
            layout.addWidget(btn)

    def select_option(self, hw_arg):
        self.selected_hwdec = hw_arg
        self.accept()

# ---------------------------------------------------------
# YouTube Quality Selection Dialog
# ---------------------------------------------------------
class YouTubeQualityDialog(QDialog):
    def __init__(self, yt_url, parent=None):
        super().__init__(parent)
        self.yt_url = yt_url
        self.format_code = "best"
        self.setWindowTitle("YouTube Video Formats")
        self.setFixedSize(850, 500)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        lbl = QLabel(f"🔗 URL: {yt_url}\n⏳ Fetching formats, please wait...")
        lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(lbl)
        
        # لعرض المخرجات بدون التفاف الأسطر حتى يظل الجدول منسقاً
        self.info_text = QTextEdit(self)
        self.info_text.setReadOnly(True)
        self.info_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.info_text)
        
        input_layout = QHBoxLayout()
        self.format_input = QLineEdit(self)
        self.format_input.setPlaceholderText("Enter format code (e.g., 299+140 or best)")
        self.format_input.setText("best")
        
        self.play_btn = QPushButton("▶ Continue to Decoding")
        self.play_btn.clicked.connect(self.accept_format)
        
        input_layout.addWidget(QLabel("📝 Format Code:"))
        input_layout.addWidget(self.format_input)
        input_layout.addWidget(self.play_btn)
        
        layout.addLayout(input_layout)
        
        # استخدام Timer لجعل الواجهة تظهر قبل أن يبدأ الجلب (الذي قد يعلق الواجهة لثانية)
        QTimer.singleShot(100, self.fetch_formats)

    def fetch_formats(self):
        try:
            result = subprocess.run(
                ["yt-dlp", "-F", self.yt_url],
                capture_output=True, text=True, check=True
            )
            self.info_text.setText(result.stdout)
            # النزول لأسفل الشاشة تلقائياً حيث تتواجد الجودات العالية
            scrollbar = self.info_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except Exception as e:
            self.info_text.setText(f"❌ Error fetching formats. Ensure yt-dlp is installed.\n\n{str(e)}")

    def accept_format(self):
        self.format_code = self.format_input.text().strip()
        if not self.format_code:
            self.format_code = "best"
        self.accept()

# ---------------------------------------------------------
# Aspect Ratio Container
# ---------------------------------------------------------
class AspectRatioContainer(QWidget):
    def __init__(self, child_widget, bg_color):
        super().__init__()
        self.setStyleSheet(f"background-color: {bg_color};")
        self.child = child_widget
        self.child.setParent(self)
        
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
# FFmpeg Info Dialog
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
        
        def custom_mpv_logger(loglevel, component, message):
            msg = message.lower()
            if "late sei" in msg or "legacy vo" in msg or "streams.videolan.org" in msg:
                return

            if loglevel in ['error', 'fatal']:
                print(f"[{loglevel.upper()}] {component}: {message}")
            elif loglevel == 'info' and component in ['cplayer', 'vd']:
                if 'Video' in message or 'Audio' in message or 'Using hardware decoding' in message:
                    print(f"[INFO] {message}")

        self.player = mpv.MPV(
            wid=str(int(self.video_widget.winId())),
            vo='gpu',
            gpu_context='x11egl',
            osc=False,
            input_default_bindings=False,
            input_vo_keyboard=False,
            keep_open=True,
            loglevel='info',
            log_handler=custom_mpv_logger
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

    # تشغيل الملفات المحلية
    def ask_for_decoding_and_play(self, source):
        print(f"\n{'-'*60}")
        print(f"[*] 📂 Video Selected: {source}")
        
        decoding_dialog = DecodingDialog(self)
        if decoding_dialog.exec() == QDialog.DialogCode.Accepted:
            selected_hwdec = decoding_dialog.selected_hwdec
            
            print(f"[*] 🖥️  Hardware Decoding Requested: {selected_hwdec}")
            self.player['hwdec'] = selected_hwdec
            
            self.stack.setCurrentWidget(self.video_container)
            print(f"[*] ▶️  Passing to MPV Engine...")
            print(f"{'-'*60}\n")
            
            self.player.play(source)

            def check_hwdec_status():
                current_hwdec = getattr(self.player, 'hwdec_current', 'no')
                v_codec = getattr(self.player, 'video_format', 'Unknown')
                
                print(f"[*] 🎞️  Detected Video Codec: {str(v_codec).upper()}")
                
                if selected_hwdec != "no" and current_hwdec == "no":
                    print(f"\n\033[93m[⚠️ WARNING] Falling back to CPU. The GPU doesn't support hardware decoding for the '{str(v_codec).upper()}' codec.\033[0m\n")
                elif current_hwdec != "no":
                    print(f"\n\033[92m[✅ SUCCESS] Hardware decoding is active! Playing via GPU using '{current_hwdec}'.\033[0m\n")

            QTimer.singleShot(1500, check_hwdec_status)

    def browse_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "", "Video Files (*.mp4 *.mkv *.webm *.avi);;All Files (*)"
        )
        if file_path:
            self.ask_for_decoding_and_play(file_path)

    # تشغيل مقاطع يوتيوب بالترتيب الجديد
    def play_youtube(self, yt_url):
        # 1. نافذة الجودات والصيغ
        quality_dialog = YouTubeQualityDialog(yt_url, self)
        if quality_dialog.exec() == QDialog.DialogCode.Accepted:
            format_code = quality_dialog.format_code
            
            # 2. نافذة اختيار العتاد
            decoding_dialog = DecodingDialog(self)
            if decoding_dialog.exec() == QDialog.DialogCode.Accepted:
                selected_hwdec = decoding_dialog.selected_hwdec
                
                print(f"\n{'-'*60}")
                print(f"[*] 🌐 YouTube URL: {yt_url}")
                print(f"[*] 🍿 Format Selected: {format_code}")
                print(f"[*] 🖥️  Hardware Decoding Requested: {selected_hwdec}")
                
                # إعدادات MPV ليوتيوب
                self.player['hwdec'] = selected_hwdec
                self.player['ytdl'] = True
                self.player['ytdl-format'] = format_code
                
                self.stack.setCurrentWidget(self.video_container)
                print(f"[*] ▶️  Passing to MPV Engine...")
                print(f"{'-'*60}\n")
                
                # تمرير الرابط الأصلي مباشرة وسيتكفل mpv بـ ytdl-format
                self.player.play(yt_url)

                def check_hwdec_status():
                    current_hwdec = getattr(self.player, 'hwdec_current', 'no')
                    v_codec = getattr(self.player, 'video_format', 'Unknown')
                    
                    print(f"[*] 🎞️  Detected Video Codec: {str(v_codec).upper()}")
                    
                    if selected_hwdec != "no" and current_hwdec == "no":
                        print(f"\n\033[93m[⚠️ WARNING] Falling back to CPU. The GPU doesn't support hardware decoding for the '{str(v_codec).upper()}' codec.\033[0m\n")
                    elif current_hwdec != "no":
                        print(f"\n\033[92m[✅ SUCCESS] Hardware decoding is active! Playing via GPU using '{current_hwdec}'.\033[0m\n")

                QTimer.singleShot(1500, check_hwdec_status)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    locale.setlocale(locale.LC_NUMERIC, "C")
    
    app.setStyleSheet(stylesheet)
    window = HardPlayerWindow()
    window.show()
    sys.exit(app.exec())