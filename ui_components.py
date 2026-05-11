# ui_components.py

import subprocess
import os # تمت الإضافة للتعامل مع المسارات
import re # تمت الإضافة لحساب حجم التحميل
from pathlib import Path # مطلوب للوصول للكاش
from PyQt6.QtWidgets import (QWidget, QDialog, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QLineEdit, QSlider, QFrame, 
                             QProgressBar, QScrollArea, QTextEdit)
from PyQt6.QtCore import Qt, pyqtSignal
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

# --- New Components for YouTube Download Feature ---

class ToggleSwitch(QPushButton):
    """زر تشغيل وإيقاف (On/Off) بتصميم احترافي"""
    def __init__(self, parent=None):
        super().__init__("OFF", parent)
        self.setCheckable(True)
        self.setFixedSize(60, 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(self._get_style(False))
        self.toggled.connect(self._on_toggled)

    def _on_toggled(self, checked):
        self.setText("ON" if checked else "OFF")
        self.setStyleSheet(self._get_style(checked))

    def _get_style(self, checked):
        if checked:
            return """
                QPushButton { background-color: #cba6f7; color: #11111b; font-weight: bold; border-radius: 15px; border: none; }
            """
        else:
            return """
                QPushButton { background-color: #45475a; color: #cdd6f4; font-weight: bold; border-radius: 15px; border: none; }
            """

class DownloadOptionsDialog(QDialog):
    """نافذة لاختيار الإضافات (الترجمة، الصورة المصغرة، الفصول، الوصف)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download Extras")
        self.setFixedSize(450, 400)
        self.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        lbl = QLabel("🛠️ Select Additional Features")
        lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

        # دالة مساعدة لإنشاء صف الخيارات
        def create_row(label_text, icon):
            row = QHBoxLayout()
            lbl = QLabel(f"{icon} {label_text}")
            lbl.setFont(QFont("Arial", 11))
            switch = ToggleSwitch()
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(switch)
            return row, switch

        # 1. Subtitles
        sub_row, self.sub_switch = create_row("Download Subtitles & Embed", "📝")
        layout.addLayout(sub_row)
        
        # حاوية جديدة تضم خانة الإدخال وزر المعلومات
        self.sub_input_container = QWidget()
        sub_layout = QHBoxLayout(self.sub_input_container)
        sub_layout.setContentsMargins(0, 0, 0, 0)
        
        self.sub_lang_input = QLineEdit()
        self.sub_lang_input.setText("en,ar") 
        self.sub_lang_input.setStyleSheet("background: #313244; padding: 5px; border-radius: 4px; border: 1px solid #45475a;")
        
        # تصميم جديد لزر الـ info لتجنب مشاكل الإيموجي في لينكس
        self.info_btn = QPushButton(" i ")
        self.info_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.info_btn.setFixedSize(30, 30)
        self.info_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.info_btn.setStyleSheet("""
            QPushButton { background: #313244; color: #cba6f7; border-radius: 15px; font-weight: bold; border: 1px solid #45475a; }
            QPushButton:hover { background: #45475a; border: 1px solid #cba6f7; }
        """)
        self.info_btn.clicked.connect(self.show_sub_info)
        
        sub_layout.addWidget(self.sub_lang_input)
        sub_layout.addWidget(self.info_btn)
        
        self.sub_input_container.hide()
        layout.addWidget(self.sub_input_container)
        
        self.sub_switch.toggled.connect(self.sub_input_container.setVisible)

        # 2. Thumbnail
        thumb_row, self.thumb_switch = create_row("Download Thumbnail (JPG)", "🖼️")
        layout.addLayout(thumb_row)

        # 3. Chapters
        chap_row, self.chap_switch = create_row("Embed Chapters", "📑")
        layout.addLayout(chap_row)

        # 4. Info (Description, Likes, etc)
        info_row, self.info_switch = create_row("Save Video Info (.txt)", "📄")
        layout.addLayout(info_row)

        layout.addStretch()

        self.btn = QPushButton("🚀 Start Download")
        self.btn.setStyleSheet("""
            QPushButton { background-color: #89b4fa; color: #11111b; font-weight: bold; padding: 12px; border-radius: 6px; font-size: 14px; }
            QPushButton:hover { background-color: #b4befe; }
        """)
        self.btn.clicked.connect(self.accept)
        layout.addWidget(self.btn)

    def show_sub_info(self):
        """نافذة المعلومات المنبثقة للغات (بالإنجليزية)"""
        dlg = QDialog(self)
        dlg.setWindowTitle("Subtitles Info")
        dlg.setFixedSize(400, 380)
        dlg.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")
        l = QVBoxLayout(dlg)
        l.setSpacing(10)
        
        txt = QLabel("<b>Subtitle Language Codes:</b><br><br>"
                     "You can download multiple languages by separating them with a comma (e.g., <b>en,ar,fr</b>).<br><br>"
                     "<b>Most Common Codes:</b><br>"
                     "• <b>en</b> : English<br>"
                     "• <b>ar</b> : Arabic<br>"
                     "• <b>fr</b> : French<br>"
                     "• <b>es</b> : Spanish<br>"
                     "• <b>de</b> : German<br>"
                     "• <b>ru</b> : Russian<br>"
                     "• <b>ja</b> : Japanese<br>"
                     "• <b>tr</b> : Turkish<br>"
                     "• <b>hi</b> : Hindi<br><br>"
                     "<i>* Note: yt-dlp will fetch the manual subtitle if available, or automatically fallback to YouTube's auto-generated version.</i>")
        txt.setFont(QFont("Arial", 10))
        txt.setStyleSheet("background: transparent; border: none; line-height: 1.5;")
        txt.setWordWrap(True)
        l.addWidget(txt)
        
        btn = QPushButton("Got it")
        btn.setStyleSheet("""
            QPushButton { background-color: #cba6f7; color: #11111b; font-weight: bold; padding: 8px; border-radius: 4px; }
            QPushButton:hover { background-color: #b4befe; }
        """)
        btn.clicked.connect(dlg.accept)
        l.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        dlg.exec()

    def get_options(self):
        return {
            'subs': self.sub_switch.isChecked(),
            'sub_lang': self.sub_lang_input.text().strip(),
            'thumb': self.thumb_switch.isChecked(),
            'chapters': self.chap_switch.isChecked(),
            'info': self.info_switch.isChecked()
        }

class DownloadProgressDialog(QDialog):
    """
    النافذة النهائية التي تعرض التقدم والبيانات بتصميم Catppuccin Mocha.
    """
    def __init__(self, info, format_code, quality_name, dl_options, parent=None):
        super().__init__(parent)
        self.setWindowTitle("HardPlayer - Acquiring Stream")
        self.setFixedWidth(540)
        self.setStyleSheet("background-color: #11111b; color: #cdd6f4;")
        
        # حفظ ملف المعلومات فوراً إذا تم اختياره
        if dl_options.get('info'):
            self.save_info_file(info)
            
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # --- 1. قسم التفاصيل ---
        self.info_frame = QFrame()
        self.info_frame.setObjectName("InfoFrame")
        self.info_frame.setStyleSheet("""
            QFrame#InfoFrame {
                background-color: #1e1e2e;
                border-radius: 12px;
                padding: 15px;
                border: 1px solid #313244;
            }
            QLabel {
                font-family: 'JetBrains Mono', 'monospace';
                font-size: 12px;
                background: transparent;
                border: none;
            }
        """)
        info_layout = QVBoxLayout(self.info_frame)
        
        # استخراج البيانات الإضافية وتجنب الأخطاء في حال كانت القيمة None
        date_raw = info.get('upload_date') or '00000000'
        date_fmt = f"{date_raw[:4]}-{date_raw[4:6]}-{date_raw[6:]}"
        
        # تفاصيل العرض الموسعة
        self.name_lbl = QLabel(f"<b>📄 Name:</b> {info.get('title', 'Unknown')}")
        self.name_lbl.setWordWrap(True)
        
        self.uploader_lbl = QLabel(f"<b>👤 Channel:</b> {info.get('uploader', 'N/A')}")
        self.date_lbl = QLabel(f"<b>📅 Date:</b> {date_fmt}")
        
        # تفاعلات الفيديو (Likes/Comments)
        likes = info.get('like_count') or 0
        comments = info.get('comment_count') or 0
        self.stats_lbl = QLabel(f"<b>👍 Likes:</b> {likes:,} | <b>💬 Comments:</b> {comments:,}")
        
        # تفاصيل الملف التقنية
        ext_val = info.get('ext', 'N/A')
        if format_code:
            if 'ext=mp4' in format_code:
                ext_val = 'mp4'
            elif 'ext=webm' in format_code:
                ext_val = 'webm'
            elif 'ext=m4a' in format_code:
                ext_val = 'm4a'
                
        self.qual_lbl = QLabel(f"<b>🎬 Quality:</b> {quality_name} | <b>📁 Ext:</b> {ext_val}")
        self.size_lbl = QLabel(f"<b>📦 Size:</b> Calculating...")
        self.size_lbl.setWordWrap(True)
        
        for lbl in [self.name_lbl, self.uploader_lbl, self.date_lbl, self.stats_lbl, self.qual_lbl, self.size_lbl]:
            info_layout.addWidget(lbl)
        
        layout.addWidget(self.info_frame)

        # --- 2. قسم شريط التقدم ---
        self.pbar = QProgressBar()
        self.pbar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pbar.setStyleSheet("""
            QProgressBar { 
                border: 2px solid #313244; 
                border-radius: 10px; 
                text-align: center; 
                height: 35px; 
                background: #1e1e2e;
                color: #cba6f7; 
                font-weight: bold;
                font-size: 13px;
            }
            QProgressBar::chunk { 
                background-color: #a6e3a1; 
                border-radius: 8px;
            }
        """)
        self.pbar.setFormat("Initializing... %p%")
        layout.addWidget(self.pbar)

        # --- 3. قسم الفوتر و زر الإلغاء ---
        footer_layout = QHBoxLayout()
        self.status_lbl = QLabel("Downloading...")
        self.status_lbl.setStyleSheet("color: #bac2de; font-size: 12px;")
        
        self.time_left_lbl = QLabel("Time Left: --:--")
        self.time_left_lbl.setStyleSheet("color: #f9e2af; font-weight: bold; font-size: 13px;")

        self.cancel_btn = QPushButton("Cancel ❌")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton { background-color: #f38ba8; color: #11111b; font-weight: bold; border-radius: 6px; padding: 5px 15px; }
            QPushButton:hover { background-color: #eba0ac; }
        """)
        self.cancel_btn.clicked.connect(self.on_cancel_btn_clicked)
        
        footer_layout.addWidget(self.status_lbl)
        footer_layout.addStretch()
        footer_layout.addWidget(self.time_left_lbl)
        footer_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(footer_layout)

        # بدء التحميل الفعلي عبر العامل (Worker)
        from youtube_feature import DownloadWorker
        self.worker = DownloadWorker(info['webpage_url'], format_code, dl_options)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def request_cancel(self):
        """نافذة التأكيد بـ 3 خيارات وتُرجع النتيجة (True للإغلاق، False للعودة)"""
        if not hasattr(self, 'worker') or not self.worker.isRunning():
            return True

        dlg = QDialog(self)
        dlg.setWindowTitle("Confirm Cancel")
        dlg.setFixedSize(360, 200)
        dlg.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")
        layout = QVBoxLayout(dlg)
        
        lbl = QLabel("هل تريد ايقاف التحميل؟\nAre you sure you want to stop the download?")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(lbl)
        
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_yes = QPushButton("Yes")
        btn_yes_save = QPushButton("Yes and save downloaded files")
        btn_no = QPushButton("No")
        
        btn_yes.setStyleSheet("QPushButton { background: #f38ba8; color: #11111b; font-weight: bold; padding: 8px; border-radius: 4px; } QPushButton:hover { background: #eba0ac; }")
        btn_yes_save.setStyleSheet("QPushButton { background: #f9e2af; color: #11111b; font-weight: bold; padding: 8px; border-radius: 4px; } QPushButton:hover { background: #f2cd32; }")
        btn_no.setStyleSheet("QPushButton { background: #a6e3a1; color: #11111b; font-weight: bold; padding: 8px; border-radius: 4px; } QPushButton:hover { background: #94e2d5; }")
        
        result = 0
        def set_res(val):
            nonlocal result
            result = val
            dlg.accept()
            
        btn_yes.clicked.connect(lambda: set_res(1))
        btn_yes_save.clicked.connect(lambda: set_res(2))
        btn_no.clicked.connect(lambda: set_res(0))
        
        btn_layout.addWidget(btn_yes)
        btn_layout.addWidget(btn_yes_save)
        btn_layout.addWidget(btn_no)
        layout.addLayout(btn_layout)
        
        dlg.exec()
        
        if result == 1:
            self.status_lbl.setText("Cancelling and Cleaning up...")
            self.worker.abort(delete_parts=True)
            self.worker.wait() # الانتظار حتى يتوقف الخيط
            return True
        elif result == 2:
            self.status_lbl.setText("Cancelling...")
            self.worker.abort(delete_parts=False)
            self.worker.wait()
            return True
            
        return False

    def on_cancel_btn_clicked(self):
        """يُستدعى عند الضغط على الزر الأحمر Cancel"""
        if self.request_cancel():
            self.accept() # إغلاق النافذة

    def reject(self):
        """اعتراض زر Esc وأي محاولة إغلاق برمجية لعدم إخفاء النافذة والتحميل مستمر"""
        if hasattr(self, 'worker') and self.worker.isRunning():
            if self.request_cancel():
                super().reject()
        else:
            super().reject()

    def closeEvent(self, event):
        """يُستدعى عند الضغط على زر إغلاق النافذة (X) من الشريط العلوي"""
        if hasattr(self, 'worker') and self.worker.isRunning():
            if self.request_cancel():
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def save_info_file(self, info):
        try:
            # جلب مسار التحميل المخصص من الكاش
            path_file = Path.home() / ".cache" / "hardplayer" / "download_path.txt"
            target_dir = os.getcwd() # الافتراضي هو المجلد الحالي
            
            if path_file.exists():
                custom_path = path_file.read_text(encoding="utf-8").strip()
                if custom_path and os.path.exists(custom_path):
                    target_dir = custom_path # تحديث المجلد للمسار المخصص

            title = info.get('title', 'video')
            clean_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c in ' -_']).rstrip()
            # دمج المجلد المختار مع اسم الملف
            filename = os.path.join(target_dir, f"{clean_title}_info.txt")
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Title: {title}\n")
                f.write(f"Channel: {info.get('uploader', 'N/A')}\n")
                date_raw = info.get('upload_date') or '00000000'
                f.write(f"Upload Date: {date_raw[:4]}-{date_raw[4:6]}-{date_raw[6:]}\n")
                f.write(f"Views: {info.get('view_count', 'N/A')}\n")
                f.write(f"Likes: {info.get('like_count', 'N/A')}\n\n")
                f.write("=========================\n")
                f.write(f"Description:\n{info.get('description', '')}\n")
            print(f"[*] 📄 Info file saved to: {filename}") # طباعة المسار للتأكد
        except Exception as e:
            print(f"[*] ⚠️ Failed to save info file: {e}")

    def update_progress(self, d):
        if d['status'] == 'downloading':
            percent = d.get('percent', 0.0)
            self.pbar.setValue(int(percent))
            
            speed = d.get('_speed_str', '0.00MiB/s')
            eta = d.get('_eta_str', '00:00')
            
            self.pbar.setFormat(f"{percent:.1f}% | Speed: {speed}")
            
            v_size = d.get('video_size', 'Unknown')
            a_size = d.get('audio_size', 'Unknown')
            curr_stream = d.get('current_stream', 'Video')
            total_str = d.get('_total_bytes_str', '0')
            
            # حساب الكمية المحملة فعلياً (كم ميجا نزلت)
            downloaded_str = "Unknown"
            m = re.match(r"([0-9\.]+)([a-zA-Z]+)", total_str)
            if m:
                try:
                    val = float(m.group(1))
                    unit = m.group(2)
                    dl_val = val * (percent / 100.0)
                    downloaded_str = f"{dl_val:.2f}{unit}"
                except:
                    pass
            
            # عرض الحجم بالتفصيل
            size_text = (f"<b>📦 Video Size:</b> {v_size} | <b>🎵 Audio Size:</b> {a_size}<br>"
                         f"<b>⬇️ Downloading ({curr_stream}):</b> {downloaded_str} / {total_str}")
            self.size_lbl.setText(size_text)
            
            self.time_left_lbl.setText(f"Time Left: {eta}")
            self.status_lbl.setText("Downloading...")
            self.status_lbl.setStyleSheet("color: #bac2de; font-size: 12px;")
            
        elif d['status'] == 'merging':
            self.pbar.setValue(100)
            self.pbar.setFormat("100% | Merging...")
            self.status_lbl.setText("Merging Video & Audio... Please wait ⏳")
            self.status_lbl.setStyleSheet("color: #f9e2af; font-weight: bold; font-size: 13px;")
            self.time_left_lbl.setText("Time Left: 00:00")
            
        elif d['status'] == 'processing':
            self.pbar.setValue(100)
            self.pbar.setFormat("100% | Processing...")
            self.status_lbl.setText("Processing file... Please wait ⏳")
            self.status_lbl.setStyleSheet("color: #f9e2af; font-weight: bold; font-size: 13px;")
            self.time_left_lbl.setText("Time Left: 00:00")

    def on_finished(self):
        self.pbar.setValue(100)
        self.pbar.setFormat("Download Finished! 100%")
        self.status_lbl.setText("Finished Successfully!")
        self.status_lbl.setStyleSheet("color: #a6e3a1; font-weight: bold;")
        self.setWindowTitle("HardPlayer - Download Complete! ✅")
        self.cancel_btn.hide() # إخفاء زر الإلغاء بعد الانتهاء


class QualitySelectorDialog(QDialog):
    """
    نافذة اختيار الجودة.
    """
    def __init__(self, info, parent=None):
        super().__init__(parent)
        self.info = info
        self.setWindowTitle("Select Download Quality")
        self.setFixedSize(350, 500)
        self.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")
        
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(12)

        lbl = QLabel("🎥 Choose Video Quality:")
        lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(lbl)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(8)

        pref_ext = None
        ext_file = Path.home() / ".cache" / "hardplayer" / "youtube_video_ext.txt"
        if ext_file.exists():
            pref_ext = ext_file.read_text(encoding="utf-8").strip()

        if pref_ext == "mp4":
            best_code = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/bestvideo+bestaudio/best"
        elif pref_ext:
            best_code = f"bestvideo[ext={pref_ext}]+bestaudio/best[ext={pref_ext}]/bestvideo+bestaudio/best"
        else:
            best_code = "bestvideo+bestaudio/best"

        self.add_quality_btn(content_layout, "🌟 Best Quality (Auto)", best_code, "#a6e3a1")

        formats = info.get('formats', [])
        available_heights = set()
        for f in formats:
            vcodec = f.get('vcodec', 'none')
            height = f.get('height')
            if vcodec != 'none' and height:
                available_heights.add(int(height))
        
        sorted_heights = sorted(list(available_heights), reverse=True)

        for h in sorted_heights:
            emoji = "📺" if h >= 720 else ("📱" if h >= 360 else "🥔")
            
            available_exts = set()
            for f in formats:
                if f.get('vcodec') != 'none' and f.get('height') == h:
                    ext = f.get('ext')
                    if ext:
                        available_exts.add(ext)
            
            note = ""
            if pref_ext and available_exts and (pref_ext not in available_exts):
                fallback_ext = "webm" if "webm" in available_exts else list(available_exts)[0]
                note = f" ({fallback_ext} because not found {pref_ext})"
                
            text = f"{emoji} {h}p{note}"
            
            if pref_ext == "mp4":
                code = f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={h}]+bestaudio/best"
            elif pref_ext:
                code = f"bestvideo[height<={h}][ext={pref_ext}]+bestaudio/bestvideo[height<={h}]+bestaudio/best"
            else:
                code = f"bestvideo[height<={h}]+bestaudio/best"

            self.add_quality_btn(content_layout, text, code)

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        self.layout.addWidget(scroll)

        self.adv_btn = QPushButton("⚙️ Advanced (Custom ID + Audio ID)")
        self.adv_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.adv_btn.setStyleSheet("""
            QPushButton { 
                background-color: transparent; 
                color: #f38ba8; 
                padding: 10px; 
                border-radius: 6px; 
                border: 1px solid #f38ba8;
                font-weight: bold;
            }
            QPushButton:hover { 
                background-color: #f38ba8; 
                color: #11111b; 
            }
        """)
        self.adv_btn.clicked.connect(self.open_advanced)
        self.layout.addWidget(self.adv_btn)

    def add_quality_btn(self, layout, text, code, hover_color="#89b4fa"):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{ 
                background-color: #313244; 
                padding: 10px; 
                border-radius: 6px; 
                font-size: 13px; 
                font-weight: bold;
                text-align: left;
            }}
            QPushButton:hover {{ 
                background-color: {hover_color}; 
                color: #11111b; 
            }}
        """)
        btn.clicked.connect(lambda ch, c=code, t=text: self.start_dl(c, t))
        layout.addWidget(btn)

    def open_advanced(self):
        from youtube_feature import YouTubeQualityDialog
        
        url = self.info.get('webpage_url')
        if not url:
            return
            
        adv_dlg = YouTubeQualityDialog(url, mode="download", parent=self)
        
        if adv_dlg.exec():
            code = adv_dlg.format_code
            if code:
                self.start_dl(code, f"Custom ({code})")

    def start_dl(self, code, name):
        options_dlg = DownloadOptionsDialog(self)
        if options_dlg.exec() == QDialog.DialogCode.Accepted:
            dl_options = options_dlg.get_options()
            dl_dlg = DownloadProgressDialog(self.info, code, name, dl_options, self.parent())
            dl_dlg.show()
            self.close()


class YouTubeURLDialog(QDialog):
    """
    نافذة لطلب رابط اليوتيوب المراد تحميله.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("YouTube Downloader")
        self.setFixedSize(400, 150)
        self.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")
        
        layout = QVBoxLayout(self)
        self.lbl = QLabel("Enter YouTube URL to Download:")
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.url_input.setStyleSheet("background: #313244; padding: 8px; border-radius: 5px; border: 1px solid #45475a;")
        layout.addWidget(self.url_input)
        
        self.next_btn = QPushButton("Download Video 📥")
        self.next_btn.setStyleSheet("""
            QPushButton {
                background-color: #cba6f7; 
                color: #11111b; 
                font-weight: bold; 
                padding: 10px; 
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
            QPushButton:disabled {
                background-color: #585b70;
                color: #a6adc8;
            }
        """)
        self.next_btn.clicked.connect(self.process_url)
        layout.addWidget(self.next_btn)

    def process_url(self):
        url = self.url_input.text().strip()
        if url:
            self.lbl.setText("Fetching metadata... ⏳")
            self.next_btn.setEnabled(False)
            
            if "list=" in url:
                from ui_components_download_playlist import PlaylistFetchWorker
                self.fetcher = PlaylistFetchWorker(url)
                self.fetcher.finished.connect(self.handle_playlist_fetched)
                self.fetcher.start()
            else:
                from youtube_feature import YTInfoFetcher
                self.fetcher = YTInfoFetcher(url)
                self.fetcher.finished.connect(self.show_selector)
                self.fetcher.start()

    def handle_playlist_fetched(self, videos_list):
        if not videos_list:
            self.lbl.setText("❌ Failed to fetch playlist or empty.")
            self.next_btn.setEnabled(True)
            return

        from ui_components_download_playlist import PlaylistModeDialog, PlaylistSelectionDialog, PlaylistProgressDialog
        from youtube_feature import YTInfoFetcher

        
        mode_dlg = PlaylistModeDialog(self)
        if mode_dlg.exec() != QDialog.DialogCode.Accepted:
            self.next_btn.setEnabled(True)
            self.lbl.setText("Enter YouTube URL to Download:")
            return

        selected_videos = videos_list
        if mode_dlg.mode == "select":
            # 2. نافذة التحديد
            select_dlg = PlaylistSelectionDialog(videos_list, self)
            if select_dlg.exec() == QDialog.DialogCode.Accepted:
                selected_videos = select_dlg.get_selected_videos()
            else:
                self.next_btn.setEnabled(True)
                self.lbl.setText("Enter YouTube URL to Download:")
                return

        if not selected_videos:
            self.next_btn.setEnabled(True)
            self.lbl.setText("Enter YouTube URL to Download:")
            return

        
        self.lbl.setText("Getting quality options... ⏳")
        first_url = selected_videos[0]['url']
        
        def on_first_video_info(info):
            self.accept() # إغلاق نافذة الـ URL
            # إظهار نافذة الجودة
            selector = QualitySelectorDialog(info, self.parent())
            
            # اختطاف وظيفة start_dl لنوجهها للقائمة بدل فيديو فردي
            def custom_start_dl(code, name):
                options_dlg = DownloadOptionsDialog(selector)
                if options_dlg.exec() == QDialog.DialogCode.Accepted:
                    dl_options = options_dlg.get_options()
                    # فتح نافذة القوائم النهائية
                    pl_dlg = PlaylistProgressDialog(selected_videos, code, name, dl_options, selector.parent())
                    pl_dlg.show()
                    selector.close()
            
            selector.start_dl = custom_start_dl
            selector.show()

        self.info_fetcher = YTInfoFetcher(first_url)
        self.info_fetcher.finished.connect(on_first_video_info)
        self.info_fetcher.start()

    def show_selector(self, info):
        selector = QualitySelectorDialog(info, self.parent())
        selector.show()
        self.accept()
