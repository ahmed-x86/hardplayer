#!/usr/bin/env python3

import os
# إجبار FFmpeg على استخدام المعالج لفك التشفير لتجنب مشاكل الهاردوير مع الفيديوهات المحلية
os.environ["FFMPEG_HWACCEL"] = "0"
# تم إزالة أسطر إخفاء الـ logs لكي تظهر في التيرمنال

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

# ---------------------------------------------------------
# الحاوية الذكية اللي هتحل مشكلة الحواف السوداء
# ---------------------------------------------------------
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
# ---------------------------------------------------------

class StartupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("HardPlayer - Open Media")
        self.setFixedSize(450, 180)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        self.lbl = QLabel("اختر ملف فيديو محلي أو أدخل رابط يوتيوب:", self)
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl)
        
        self.browse_btn = QPushButton("📁 Browse Local Video", self)
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

    # ---------------------------------------------------------
    # التقاط ضغطات الكيبورد
    # ---------------------------------------------------------
    def keyPressEvent(self, event):
        # التحقق مما إذا كان الزر المضغوط هو حرف P (سواء كان كابيتال أو سمول)
        if event.key() == Qt.Key.Key_P:
            # التحقق إذا لم يكن هناك فيديو في وضع التشغيل حالياً
            if self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
                self.show_startup_dialog()
                
        # تمرير الحدث للنافذة الأم لضمان عدم تعطل باقي الاختصارات الافتراضية
        super().keyPressEvent(event)

    def show_startup_dialog(self):
        dialog = StartupDialog(self)
        dialog.exec()

    def browse_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "", "Video Files (*.mp4 *.mkv *.webm *.avi);;All Files (*)"
        )
        if file_path:
            self.stack.setCurrentWidget(self.video_container)
            self.player.setSource(QUrl.fromLocalFile(file_path))
            self.player.play()

    def play_youtube(self, yt_url):
        print("[*] Fetching YouTube direct stream URL...")
        try:
            result = subprocess.run(
                ["yt-dlp", "-f", "bestvideo[vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best", "-g", yt_url],
                capture_output=True, text=True, check=True
            )
            # أخذ الرابط الأول من مخرجات yt-dlp
            stream_url = result.stdout.strip().split('\n')[0]
            
            if stream_url:
                self.stack.setCurrentWidget(self.video_container)
                self.player.setSource(QUrl(stream_url))
                self.player.play()
        except Exception as e:
            print(f"❌ Error playing YouTube URL: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(stylesheet)
    window = HardPlayerWindow()
    window.show()
    sys.exit(app.exec())