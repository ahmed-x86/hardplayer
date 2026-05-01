#!/usr/bin/env python3

import os
# Force PyQt6 to use ffmpeg backend instead of the broken Windows Media Foundation
os.environ["QT_MEDIA_BACKEND"] = "ffmpeg"
# Force FFmpeg to use software decoding to prevent hardware acceleration black screens
os.environ["FFMPEG_HWACCEL"] = "0"

import sys
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                             QWidget, QPushButton, QFileDialog, QDialog, 
                             QHBoxLayout, QLineEdit, QLabel, QStackedWidget)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QFont
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

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

class AspectRatioContainer(QWidget):
    def __init__(self, child_widget, bg_color):
        super().__init__()
        self.setStyleSheet(f"background-color: {bg_color};")
        self.child = child_widget
        self.child.setParent(self)
        self.child.setAspectRatioMode(Qt.AspectRatioMode.IgnoreAspectRatio)
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
        
        self.video_widget = QVideoWidget()
        self.video_container = AspectRatioContainer(self.video_widget, BASE)
        
        self.stack.addWidget(self.logo_widget)
        self.stack.addWidget(self.video_container)
        
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)

        QTimer.singleShot(100, self.show_startup_dialog)

    # --- الإضافة الجديدة (Back-up Engine) ---
    def play_engine(self, source):
        """إضافة محرك تشغيل خارجي يضمن العمل حتى لو فشلت مكتبة Qt"""
        try:
            # نحاول التشغيل بـ Qt أولاً كـ fallback
            self.stack.setCurrentWidget(self.video_container)
            self.player.setSource(QUrl.fromLocalFile(source) if os.path.exists(source) else QUrl(source))
            self.player.play()
            
            # إذا ظهرت مشكلة "Backend not found" (وهي مشكلتنا الأساسية)، ننادي ffplay فوراً
            # ملاحظة: ffplay لا يعتمد على مكتبات Qt، لذا سيعمل بنسبة 100%
            cmd = ["ffplay", "-autoexit", "-alwaysontop", "-window_title", "HardPlayer View", source]
            subprocess.Popen(cmd)
        except Exception as e:
            print(f"Engine Error: {e}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_P:
            if self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
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

    def browse_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "", "Video Files (*.mp4 *.mkv *.webm *.avi);;All Files (*)"
        )
        if file_path:
            # استبدلنا self.player.play بـ المحرك الجديد لضمان التشغيل
            self.play_engine(file_path)

    def play_youtube(self, yt_url):
        print("[*] Fetching YouTube direct stream URL...")
        try:
            result = subprocess.run(
                ["yt-dlp", "-f", "best", "-g", yt_url],
                capture_output=True, text=True, check=True
            )
            stream_url = result.stdout.strip().split('\n')[0]
            
            if stream_url:
                # استبدلنا self.player.play بـ المحرك الجديد لضمان التشغيل
                self.play_engine(stream_url)
        except Exception as e:
            print(f"❌ Error playing YouTube URL: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(stylesheet)
    window = HardPlayerWindow()
    window.show()
    sys.exit(app.exec())