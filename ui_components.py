# ui_components.py

import subprocess
from PyQt6.QtWidgets import (QWidget, QDialog, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QLineEdit, QSlider, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Importing the text color from our configuration
from config import TEXT, BASE

class ClickableSlider(QSlider):
    """
    Custom QSlider that jumps to the position where the user clicks.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # منع السلايدر نهائياً من سرقة الكيبورد عشان الأسهم تشتغل لتقديم الفيديو
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # حساب القيمة النسبية بناءً على إحداثيات الضغطة في عرض السلايدر
            val = self.minimum() + ((self.maximum() - self.minimum()) * event.position().x()) / self.width()
            self.setValue(int(val))
            # إرسال إشارة sliderMoved يدوياً ليقوم المشغل بعمل Seek فوراً
            self.sliderMoved.emit(int(val))
        super().mousePressEvent(event)

class AspectRatioContainer(QWidget):
    """
    A container widget that maintains a specific aspect ratio (16:9 by default)
    for its child widget (the video player).
    """
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


class InfoDialog(QDialog):
    """
    A dialog that displays information about the system's FFmpeg installation.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("System FFmpeg Info")
        self.setFixedSize(500, 200)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        self.lbl = QLabel("System FFmpeg Version:")
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(self.lbl)
        
        self.info_text = QLabel()
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
    """
    The initial dialog prompting the user to select a local file or input a YouTube URL.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("HardPlayer - Open Media")
        self.setFixedSize(450, 180)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        self.lbl = QLabel("Select a local video file or search YouTube:")
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl)
        
        self.browse_btn = QPushButton("📁 Browse Local Video")
        self.browse_btn.clicked.connect(self.parent().browse_video)
        self.browse_btn.clicked.connect(self.accept)
        layout.addWidget(self.browse_btn)

        yt_layout = QHBoxLayout()
        self.yt_input = QLineEdit()
        self.yt_input.setPlaceholderText("https://youtube.com/... or Search query")
        
        self.yt_btn = QPushButton("▶ Play / Search")
        self.yt_btn.clicked.connect(self.play_url)
        
        yt_layout.addWidget(self.yt_input)
        yt_layout.addWidget(self.yt_btn)
        layout.addLayout(yt_layout)

    def play_url(self):
        query = self.yt_input.text().strip()
        if query:
            # التعديل هنا: لو الرابط مباشر يشغله، لو كلام عادي يفتح نافذة البحث
            if query.startswith("http://") or query.startswith("https://"):
                self.parent().play_youtube(query)
            else:
                self.parent().search_youtube_and_play(query)
            self.accept()

# --- v6 PlayerControlBar with Dark Theme Style ---

class PlayerControlBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 1. إعطاء اسم فريد للشريط الرئيسي علشان التنسيق ما يتسربش للعناصر الداخلية
        self.setObjectName("MainControlBar")
        
        # 2. حصر التنسيق على QFrame#MainControlBar فقط
        self.setStyleSheet("""
            QFrame#MainControlBar {
                background-color: #11111b; 
                border-top: 2px solid #313244;
            }
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border-radius: 6px;
                padding: 5px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #45475a;
            }
            QSlider::groove:horizontal {
                border: 1px solid #313244;
                height: 8px;
                background: #313244;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::sub-page:horizontal {
                background: #e9d4a4;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #89b4fa;
                border: 1px solid #89b4fa;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QLabel {
                color: #cdd6f4; 
                font-family: 'JetBrains Mono', 'monospace';
                /* تأكيد إزالة أي حدود أو خلفيات من الـ Label */
                border: none; 
                background: transparent;
            }
        """)
        self.setFixedHeight(70)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(15)

        self.play_btn = QPushButton("▶")
        self.repeat_btn = QPushButton("🔁 ✖") 
        self.play_btn.setFixedWidth(55)
        self.repeat_btn.setFixedWidth(75)

        # منع أزرار التشغيل والتكرار من سرقة التركيز
        self.play_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.repeat_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # تم تغيير QSlider التقليدي إلى ClickableSlider المطور
        self.slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.slider.setEnabled(False)

        # زيادة العرض لتنسيق المسافات والساعات الجديد
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setFixedWidth(160)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.stop_btn = QPushButton("⏹")
        self.prev_btn = QPushButton("⏮")
        self.next_btn = QPushButton("⏭")
        
        # منع باقي الأزرار من سرقة التركيز
        for btn in [self.stop_btn, self.prev_btn, self.next_btn]:
            btn.setFixedWidth(55)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        layout.addWidget(self.play_btn)
        layout.addWidget(self.repeat_btn)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.time_label)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.prev_btn)
        layout.addWidget(self.next_btn)

    def set_repeat_status(self, is_active):
        if is_active:
            self.repeat_btn.setText("🔁 ✔️")
            self.repeat_btn.setStyleSheet("""
                QPushButton {
                    color: #afd89b; 
                    border: 1px solid #afd89b; 
                    background-color: #313244;
                    font-weight: bold;
                }
            """)
        else:
            self.repeat_btn.setText("🔁 ✖")
            self.repeat_btn.setStyleSheet("""
                QPushButton {
                    color: #f38ba8; 
                    border: 1px solid #f38ba8; 
                    background-color: #313244;
                }
            """)