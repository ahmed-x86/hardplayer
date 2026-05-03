# ui_components.py

import subprocess
from PyQt6.QtWidgets import (QWidget, QDialog, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QLineEdit, QSlider, QFrame, QProgressBar, QScrollArea)
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
            from youtube_feature import YTInfoFetcher
            self.lbl.setText("Fetching metadata... ⏳")
            self.next_btn.setEnabled(False)
            self.fetcher = YTInfoFetcher(url)
            self.fetcher.finished.connect(self.show_selector)
            self.fetcher.start()

    def show_selector(self, info):
        selector = QualitySelectorDialog(info, self.parent())
        selector.show()
        self.accept()

class QualitySelectorDialog(QDialog):
    """
    تم تعديلها لتطابق شكل قائمة التشغيل تماماً (الديناميكية والجمالية).
    """
    def __init__(self, info, parent=None):
        super().__init__(parent)
        self.info = info
        self.setWindowTitle("Select Download Quality")
        self.setFixedSize(350, 500)
        self.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")
        
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(12)

        # العنوان بنفس الشكل الجمالي
        lbl = QLabel("🎥 Choose Video Quality:")
        lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(lbl)

        # منطقة السكرول
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(8)

        # 1. زر الجودة التلقائية
        self.add_quality_btn(content_layout, "🌟 Best Quality (Auto)", "bestvideo+bestaudio/best", "#a6e3a1")

        # 2. استخراج الجودات المتوفرة ديناميكياً من الـ info
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
            text = f"{emoji} {h}p"
            code = f"bestvideo[height<={h}]+bestaudio/best"
            self.add_quality_btn(content_layout, text, code)

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        self.layout.addWidget(scroll)

        # 3. زر Advanced الملون (بنفس ستايل قائمة التشغيل)
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
        adv_dlg = QDialog(self)
        adv_dlg.setWindowTitle("Advanced Selection")
        adv_dlg.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")
        l = QVBoxLayout(adv_dlg)
        v_in = QLineEdit(); v_in.setPlaceholderText("Video ID (e.g. 299)")
        a_in = QLineEdit(); a_in.setPlaceholderText("Audio ID (e.g. 140)")
        btn = QPushButton("Download")
        btn.clicked.connect(lambda: self.start_dl(f"{v_in.text()}+{a_in.text()}", "Custom"))
        l.addWidget(v_in); l.addWidget(a_in); l.addWidget(btn)
        adv_dlg.exec()

    def start_dl(self, code, name):
        dl_dlg = DownloadProgressDialog(self.info, code, name, self.parent())
        dl_dlg.show()
        self.close()

# --- v8 DownloadProgressDialog (FINAL RE-DESIGN) ---

class DownloadProgressDialog(QDialog):
    """
    النافذة النهائية التي تعرض التقدم والبيانات بتصميم Catppuccin Mocha.
    """
    def __init__(self, info, format_code, quality_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("HardPlayer - Acquiring Stream")
        self.setFixedWidth(520)
        self.setStyleSheet("background-color: #11111b; color: #cdd6f4;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # --- 1. قسم التفاصيل (Refactored Text & More Data) ---
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
        self.name_lbl = QLabel(f"<b>📄 Name:</b> {info.get('title', 'Unknown')[:45]}...")
        self.uploader_lbl = QLabel(f"<b>👤 Channel:</b> {info.get('uploader', 'N/A')}")
        self.date_lbl = QLabel(f"<b>📅 Date:</b> {date_fmt}")
        
        # تفاعلات الفيديو (Likes/Comments) - تم إصلاح الخلل هنا لتجنب NoneType
        likes = info.get('like_count') or 0
        comments = info.get('comment_count') or 0
        self.stats_lbl = QLabel(f"<b>👍 Likes:</b> {likes:,} | <b>💬 Comments:</b> {comments:,}")
        
        # تفاصيل الملف التقنية
        self.qual_lbl = QLabel(f"<b>🎬 Quality:</b> {quality_name} | <b>📁 Ext:</b> {info.get('ext', 'N/A')}")
        self.size_lbl = QLabel(f"<b>📦 Filesize:</b> Calculating...")
        
        for lbl in [self.name_lbl, self.uploader_lbl, self.date_lbl, self.stats_lbl, self.qual_lbl, self.size_lbl]:
            info_layout.addWidget(lbl)
        
        layout.addWidget(self.info_frame)

        # --- 2. قسم شريط التقدم (Progress Bar - Mauve Text) ---
        self.pbar = QProgressBar()
        self.pbar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pbar.setStyleSheet("""
            QProgressBar { 
                border: 2px solid #313244; 
                border-radius: 10px; 
                text-align: center; 
                height: 35px; 
                background: #1e1e2e;
                color: #cba6f7; /* لون الموف (Mauve) للنصوص لزيادة الوضوح */
                font-weight: bold;
                font-size: 13px;
            }
            QProgressBar::chunk { 
                background-color: #a6e3a1; /* أخضر Catppuccin */
                border-radius: 8px;
            }
        """)
        # التنسيق الافتراضي قبل بدء البيانات
        self.pbar.setFormat("Initializing... %p%")
        layout.addWidget(self.pbar)

        # --- 3. قسم الفوتر (Time Remaining) ---
        footer_layout = QHBoxLayout()
        self.status_lbl = QLabel("Downloading...")
        self.status_lbl.setStyleSheet("color: #bac2de; font-size: 12px;")
        
        self.time_left_lbl = QLabel("Time Left: --:--")
        self.time_left_lbl.setStyleSheet("color: #f9e2af; font-weight: bold; font-size: 13px;")
        
        footer_layout.addWidget(self.status_lbl)
        footer_layout.addStretch()
        footer_layout.addWidget(self.time_left_lbl)
        layout.addLayout(footer_layout)

        # بدء التحميل الفعلي عبر العامل (Worker)
        from youtube_feature import DownloadWorker
        self.worker = DownloadWorker(info['webpage_url'], format_code)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def update_progress(self, d):
        if d['status'] == 'downloading':
            # نستخدم دالة حساب النسبة المئوية الرقمية بدقة بدلاً من السلسلة النصية
            percent = d.get('percent', 0.0)
            self.pbar.setValue(int(percent))
            
            # تنظيف واستخراج البيانات النظيفة من العامل لعرضها
            speed = d.get('_speed_str', '0.00MiB/s')
            eta = d.get('_eta_str', '00:00')
            
            # عرض السرعة والنسبة المئوية داخل شريط التقدم في المنتصف بالظبط
            # تم استخدام لون #cba6f7 للنصوص عبر الـ StyleSheet أعلاه لزيادة الوضوح
            self.pbar.setFormat(f"{percent:.1f}% | Speed: {speed}")
            
            # تحديث باقي البيانات وحجم الملف في الواجهة
            self.size_lbl.setText(f"<b>📦 Filesize:</b> {d.get('_total_bytes_str', 'N/A')}")
            self.time_left_lbl.setText(f"Time Left: {eta}")

    def on_finished(self):
        self.pbar.setValue(100)
        self.pbar.setFormat("Download Finished! 100%")
        self.status_lbl.setText("Finished Successfully!")
        self.status_lbl.setStyleSheet("color: #a6e3a1; font-weight: bold;")
        self.setWindowTitle("HardPlayer - Download Complete! ✅")