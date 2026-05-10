# youtube_feature.py

import os 
import subprocess
import urllib.request
from urllib.parse import urlparse, parse_qs
import json
import re
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QLabel, QTextEdit, QLineEdit, QPushButton,
                             QScrollArea, QWidget, QFrame, QApplication)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from pathlib import Path

 
from get_youtube_thumbnail import get_youtube_thumbnail

# دالة لتنظيف النصوص من أكواد ANSI (الرموز الغريبة مثل [0;32m)
def clean_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', str(text))

# دالة لتنظيف رابط اليوتيوب لاستخراج المعرف الأساسي للفيديو فقط
def clean_youtube_url(url):
    try:
        parsed_url = urlparse(url)
        
        # 1. إذا كان الرابط بالشكل العادي (youtube.com/watch?v=...)
        if 'youtube.com' in parsed_url.netloc and '/watch' in parsed_url.path:
            query_params = parse_qs(parsed_url.query)
            if 'v' in query_params:
                video_id = query_params['v'][0]
                return f"https://www.youtube.com/watch?v={video_id}"
        
        # 2. إذا كان الرابط مختصر (youtu.be/...)
        elif 'youtu.be' in parsed_url.netloc:
            video_id = parsed_url.path.lstrip('/')
            return f"https://www.youtube.com/watch?v={video_id}"
            
        # 3. إذا كان الرابط من يوتيوب شورتس (youtube.com/shorts/...)
        elif 'youtube.com' in parsed_url.netloc and '/shorts/' in parsed_url.path:
            video_id = parsed_url.path.split('/shorts/')[-1].split('?')[0]
            return f"https://www.youtube.com/watch?v={video_id}"
            
    except Exception as e:
        print(f"[*] ⚠️ URL parsing error: {e}")
        
    return url

class YouTubeSimpleQualityDialog(QDialog):
    """
    A simple, user-friendly dialog for selecting YouTube video quality.
    Dynamically fetches only the available resolutions for the specific video.
    """
    def __init__(self, yt_url, parent=None):
        super().__init__(parent)
        self.yt_url = clean_youtube_url(yt_url) # تنظيف الرابط هنا
        self.format_code = None
        self.setWindowTitle("Select Video Quality")
        self.setFixedSize(350, 500)
        self.setModal(True)
        self.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(12)

        # واجهة التحميل المبدئية
        self.loading_lbl = QLabel("⏳ Fetching available qualities...\nPlease wait.")
        self.loading_lbl.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.loading_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.loading_lbl)

        # بدء عملية الجلب بعد ظهور النافذة مباشرة لتجنب تجميد الواجهة قبل الظهور
        QTimer.singleShot(100, self.fetch_dynamic_qualities)

    def fetch_dynamic_qualities(self):
        """Fetches the video JSON metadata and extracts available resolutions."""
        try:
            # استخراج الـ JSON الخاص بالفيديو
            result = subprocess.run(
                ["yt-dlp", "--dump-json", "--no-warnings", self.yt_url],
                capture_output=True, text=True, check=True
            )
            data = json.loads(result.stdout)
            formats = data.get('formats', [])

            available_heights = set()
            
            # فلترة الصيغ للبحث عن الـ Video Streams فقط
            for f in formats:
                vcodec = f.get('vcodec', 'none')
                height = f.get('height')
                # لو فيه كوديك فيديو وارتفاع محدد، نضيفه للقائمة
                if vcodec != 'none' and height:
                    available_heights.add(int(height))

            # ترتيب الجودات من الأعلى للأقل (مثلاً: 1080, 720, 480...)
            sorted_heights = sorted(list(available_heights), reverse=True)
            # نمرر الـ formats الكاملة للوظيفة لاستخراج الصيغ لاحقاً
            self.populate_buttons(sorted_heights, formats)

        except Exception as e:
            # في حالة حدوث خطأ، نعود للجودات الافتراضية
            print(f"[*] ⚠️ Error fetching dynamic qualities: {e}")
            self.populate_buttons([1080, 720, 480, 360, 240, 144], [])

    def populate_buttons(self, heights, formats=None):
        """Generates the UI buttons based on the fetched resolutions and preferred extension."""
        if formats is None:
            formats = []
            
        # قراءة الصيغة المفضلة من الكاش
        pref_ext = None
        ext_file = Path.home() / ".cache" / "hardplayer" / "youtube_video_ext.txt"
        if ext_file.exists():
            pref_ext = ext_file.read_text(encoding="utf-8").strip()

        # إزالة رسالة التحميل
        self.loading_lbl.deleteLater()

        lbl = QLabel("🎥 Choose Video Quality:")
        lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(lbl)

        # Scroll area في حال كانت الجودات المتوفرة كثيرة جداً
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(8)

        # 1. زر الجودة التلقائية (مع احترام الصيغة المفضلة)
        if pref_ext == "mp4":
            best_code = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/bestvideo+bestaudio/best"
        elif pref_ext:
            best_code = f"bestvideo[ext={pref_ext}]+bestaudio/best[ext={pref_ext}]/bestvideo+bestaudio/best"
        else:
            best_code = "bestvideo+bestaudio/best"
            
        self.add_quality_button(content_layout, "🌟 Best Quality (Auto)", best_code, "#a6e3a1", "#11111b")

        # 2. توليد أزرار الجودة المتوفرة
        for h in heights:
            emoji = "📺" if h >= 720 else ("📱" if h >= 360 else "🥔")
            
            # -- التعديل الجديد لاكتشاف الصيغ المتاحة لهذه الدقة --
            available_exts = set()
            for f in formats:
                if f.get('vcodec') != 'none' and f.get('height') == h:
                    ext = f.get('ext')
                    if ext:
                        available_exts.add(ext)
            
            note = ""
            # إذا كان هناك صيغة مفضلة ولم تكن موجودة في الصيغ المتاحة لهذه الدقة
            if pref_ext and available_exts and (pref_ext not in available_exts):
                # نحدد الصيغة البديلة التي سيتم اللجوء إليها (غالباً webm في الدقات العالية)
                fallback_ext = "webm" if "webm" in available_exts else list(available_exts)[0]
                note = f" ({fallback_ext} because not found {pref_ext})"
                
            text = f"{emoji} {h}p{note}"
            
            # بناء كود yt-dlp مع الصيغة المفضلة ومسار احتياطي (Fallback)
            if pref_ext == "mp4":
                code = f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={h}]+bestaudio/best"
            elif pref_ext:
                code = f"bestvideo[height<={h}][ext={pref_ext}]+bestaudio/bestvideo[height<={h}]+bestaudio/best"
            else:
                code = f"bestvideo[height<={h}]+bestaudio/best"
                
            self.add_quality_button(content_layout, text, code)

        # 3. زر الصوت فقط
        self.add_quality_button(content_layout, "🎵 Audio Only (MP3/M4A)", "bestaudio/best")

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        self.layout.addWidget(scroll)

        # 4. زر الخيارات المتقدمة للمحترفين
        self.adv_btn = QPushButton("⚙️ Advanced (Manual Code)")
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

    def add_quality_button(self, layout, text, code, bg_hover="#89b4fa", text_hover="#11111b"):
        """Helper to create and style dynamic buttons."""
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
                background-color: {bg_hover}; 
                color: {text_hover}; 
            }}
        """)
        btn.clicked.connect(lambda checked, c=code: self.select_format(c))
        layout.addWidget(btn)

    def select_format(self, code):
        """Sets the format code and closes the simple dialog."""
        self.format_code = code
        self.accept()

    def open_advanced(self):
        """Signals the main window to open the advanced dialog."""
        self.format_code = "ADVANCED"
        self.accept()


class YouTubeQualityDialog(QDialog):
    def __init__(self, yt_url, mode="play", parent=None):
        super().__init__(parent)
        self.yt_url = clean_youtube_url(yt_url) # تنظيف الرابط هنا
        self.format_code = "best"
        self.mode = mode  # تحديد وضع النافذة (تشغيل أم تحميل)
        
        # تغيير العنوان بناءً على الوضع
        if self.mode == "download":
            self.setWindowTitle("YouTube Video Formats (Download Mode)")
        else:
            self.setWindowTitle("YouTube Video Formats (Advanced)")
            
        self.setFixedSize(850, 500)
        self.setModal(True)
        self.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        lbl = QLabel(f"🔗 URL: {self.yt_url}\n⏳ Fetching formats, please wait...")
        lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(lbl)
        
        # Text area to display format options without line wrapping for better readability
        self.info_text = QTextEdit(self)
        self.info_text.setReadOnly(True)
        self.info_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.info_text.setStyleSheet("background-color: #11111b; font-family: monospace; font-size: 13px; border-radius: 6px;")
        layout.addWidget(self.info_text)
        
        input_layout = QHBoxLayout()
        self.format_input = QLineEdit(self)
        self.format_input.setPlaceholderText("Enter format code (e.g., 299+140 or best)")
        self.format_input.setText("best")
        self.format_input.setStyleSheet("background-color: #313244; padding: 8px; border-radius: 4px; border: 1px solid #45475a;")
        
        # تغيير شكل ووظيفة الزر ديناميكياً
        if self.mode == "download":
            self.action_btn = QPushButton("📥 Download Video")
            self.action_btn.setStyleSheet("""
                QPushButton { background-color: #cba6f7; color: #11111b; font-weight: bold; padding: 8px 15px; border-radius: 4px; border: none; }
                QPushButton:hover { background-color: #b4befe; }
            """)
        else:
            self.action_btn = QPushButton("▶ Continue to Decoding")
            self.action_btn.setStyleSheet("""
                QPushButton { background-color: #89b4fa; color: #11111b; font-weight: bold; padding: 8px 15px; border-radius: 4px; border: none; }
                QPushButton:hover { background-color: #b4befe; }
            """)
            
        self.action_btn.clicked.connect(self.accept_format)
        
        input_layout.addWidget(QLabel("📝 Format Code:"))
        input_layout.addWidget(self.format_input)
        input_layout.addWidget(self.action_btn)
        
        layout.addLayout(input_layout)
        
        # Use a timer to ensure the UI renders before the blocking fetch process starts
        QTimer.singleShot(100, self.fetch_formats)

    def fetch_formats(self):
        try:
            result = subprocess.run(
                ["yt-dlp", "-F", self.yt_url],
                capture_output=True, text=True, check=True
            )
            self.info_text.setText(result.stdout)
            
            # Auto-scroll to the bottom where high-quality formats usually are
            scrollbar = self.info_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
        except Exception as e:
            self.info_text.setText(f"❌ Error fetching formats. Ensure yt-dlp is installed.\n\n{str(e)}")

    def accept_format(self):
        self.format_code = self.format_input.text().strip()
        if not self.format_code:
            self.format_code = "best"
        self.accept()


# --- v9 YouTube Search Features Using yt-dlp ---

class ImageFetcher(QThread):
    """Fetches images in the background so the UI doesn't freeze."""
    image_fetched = pyqtSignal(str, bytes)

    def __init__(self, url, identifier):
        super().__init__()
        self.url = url
        self.identifier = identifier

    def run(self):
        try:
            req = urllib.request.Request(self.url, headers={'User-Agent': 'Mozilla/5.0'})
            data = urllib.request.urlopen(req).read()
            self.image_fetched.emit(self.identifier, data)
        except Exception as e:
            pass # Ignore fetch errors for missing thumbnails

class YouTubeSearchDialog(QDialog):
    def __init__(self, query, parent=None):
        super().__init__(parent)
        self.query = query
        self.selected_url = None
        self.setWindowTitle(f"YouTube Search: {query}")
        self.setFixedSize(750, 600)
        self.setModal(True)
        self.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")

        self.layout = QVBoxLayout(self)
        
        self.loading_label = QLabel(f"🔍 Searching YouTube via yt-dlp for: '{query}'...")
        self.loading_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.loading_label)

        # Scroll area for results
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background-color: transparent;")
        
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_layout.setSpacing(10)
        self.scroll_area.setWidget(self.scroll_content)
        
        self.layout.addWidget(self.scroll_area)
        self.scroll_area.hide() # Hidden until results are loaded

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("""
            QPushButton { background-color: #313244; color: #cdd6f4; padding: 10px; border-radius: 5px; font-weight: bold; }
            QPushButton:hover { background-color: #45475a; }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        self.layout.addWidget(self.cancel_btn)

        self.fetchers = []
        QTimer.singleShot(100, self.perform_search)

    def perform_search(self):
        """Uses yt-dlp native search capabilities to fetch results."""
        try:
            # السحر هنا: إضافة --flat-playlist بتخلي البحث أسرع 10 أضعاف!
            result = subprocess.run(
                [
                    "yt-dlp", 
                    f"ytsearch5:{self.query}", 
                    "--dump-json", 
                    "--flat-playlist", 
                    "--no-warnings", 
                    "--ignore-errors"
                ],
                capture_output=True, text=True, check=True
            )
            
            self.loading_label.hide()
            self.scroll_area.show()
            
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if not line.strip(): continue
                try:
                    video_data = json.loads(line)
                    self.add_video_card(video_data)
                except Exception as e:
                    print(f"Error parsing JSON for a video: {e}")
                    
        except subprocess.CalledProcessError as e:
            self.loading_label.setText(f"❌ Error during yt-dlp search:\n{e.stderr}")
        except Exception as e:
            self.loading_label.setText(f"❌ Unexpected Error:\n{str(e)}")

    def add_video_card(self, video):
        card = QFrame()
        card.setStyleSheet("QFrame { background-color: #181825; border-radius: 10px; }")
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(10, 10, 10, 10)
        card_layout.setSpacing(15)
        
        video_id = video.get('id', '')
        link = video.get('webpage_url', f"https://www.youtube.com/watch?v={video_id}")
        
        # 1. Video Thumbnail
        thumb_label = QLabel()
        thumb_label.setFixedSize(160, 90)
        thumb_label.setStyleSheet("background-color: #11111b; border-radius: 5px;")
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_label.setText("Loading...")
        
        # استخدام الدالة الخارجية لجلب رابط الصورة المصغرة بناءً على الرابط
        thumb_url = get_youtube_thumbnail(link)
        
        if thumb_url:
            fetcher = ImageFetcher(thumb_url, f"vid_{video_id}")
            fetcher.image_fetched.connect(lambda vid, data, lbl=thumb_label: self.update_image(lbl, data, 160, 90))
            fetcher.start()
            self.fetchers.append(fetcher)

        card_layout.addWidget(thumb_label)
        
        # 2. Information Panel
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        # Title
        title = video.get('title', 'Unknown Title')
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet("color: #89b4fa; border: none; background: transparent;")
        
        # Channel & Metadata Row
        channel_layout = QHBoxLayout()
        channel_name = video.get('uploader', 'Unknown Channel')
        
        # Avatar placeholder (yt-dlp doesn't directly fetch channel avatars in simple search)
        avatar_label = QLabel("👤")
        avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_label.setFixedSize(24, 24)
        avatar_label.setStyleSheet("background-color: #313244; border-radius: 12px; color: #cdd6f4; font-size: 12px;")
        
        # Format duration
        duration_str = video.get('duration_string')
        if not duration_str:
            d_sec = video.get('duration', 0)
            mins, secs = divmod(int(d_sec), 60)
            duration_str = f"{mins}:{secs:02d}"
            
        # Format views
        views = video.get('view_count', 0)
        def format_views(v):
            if v is None: return "N/A"
            if v >= 1000000: return f"{v/1000000:.1f}M"
            if v >= 1000: return f"{v/1000:.1f}K"
            return str(v)
            
        meta_str = f"<b>{channel_name}</b> • {duration_str} • {format_views(views)} views"
        meta_lbl = QLabel(meta_str)
        meta_lbl.setFont(QFont("Arial", 9))
        meta_lbl.setStyleSheet("color: #a6adc8; border: none; background: transparent;")
        
        channel_layout.addWidget(avatar_label)
        channel_layout.addWidget(meta_lbl)
        channel_layout.addStretch()
        
        # Description Snippet
        desc_snippet = video.get('description', '')
        if desc_snippet and len(desc_snippet) > 90:
            desc_snippet = desc_snippet[:90].replace('\n', ' ') + "..."
                
        desc_lbl = QLabel(desc_snippet)
        desc_lbl.setFont(QFont("Arial", 9))
        desc_lbl.setStyleSheet("color: #bac2de; border: none; background: transparent;")
        desc_lbl.setWordWrap(True)
        
        info_layout.addWidget(title_lbl)
        info_layout.addLayout(channel_layout)
        info_layout.addWidget(desc_lbl)
        info_layout.addStretch()
        
        card_layout.addLayout(info_layout)
        
        # 3. Action Buttons (التعديل الجديد)
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(5)
        
        play_btn = QPushButton("▶ Play")
        play_btn.setFixedSize(110, 30)
        play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        play_btn.setStyleSheet("""
            QPushButton { background-color: #a6e3a1; color: #11111b; font-weight: bold; border-radius: 5px; }
            QPushButton:hover { background-color: #94e2d5; }
            QPushButton:disabled { background-color: #585b70; color: #a6adc8; }
        """)
        play_btn.clicked.connect(lambda checked, url=link: self.select_video(url))
        
        copy_btn = QPushButton("🔗 Copy Link")
        copy_btn.setFixedSize(110, 30)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setStyleSheet("""
            QPushButton { background-color: #89b4fa; color: #11111b; font-weight: bold; border-radius: 5px; }
            QPushButton:hover { background-color: #b4befe; }
            QPushButton:disabled { background-color: #585b70; color: #a6adc8; }
        """)
        copy_btn.clicked.connect(lambda checked, url=link, btn=copy_btn: self.copy_link(url, btn))
        
        dl_btn = QPushButton("📥 Download")
        dl_btn.setFixedSize(110, 30)
        dl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dl_btn.setStyleSheet("""
            QPushButton { background-color: #cba6f7; color: #11111b; font-weight: bold; border-radius: 5px; }
            QPushButton:hover { background-color: #b4befe; }
            QPushButton:disabled { background-color: #585b70; color: #a6adc8; }
        """)
        dl_btn.clicked.connect(lambda checked, url=link, p=play_btn, c=copy_btn, d=dl_btn: self.start_download_flow(url, p, c, d))
        
        btn_layout.addWidget(play_btn)
        btn_layout.addWidget(copy_btn)
        btn_layout.addWidget(dl_btn)
        btn_layout.addStretch()
        
        card_layout.addLayout(btn_layout)
        self.scroll_layout.addWidget(card)

    def update_image(self, label, data, w, h):
        pixmap = QPixmap()
        if pixmap.loadFromData(data):
            label.setPixmap(pixmap.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
            label.setText("")

    def select_video(self, url):
        self.selected_url = url
        self.accept()

    # --- الدوال الجديدة للنسخ والتحميل ---
    
    def copy_link(self, url, btn):
        QApplication.clipboard().setText(url)
        original_text = btn.text()
        original_style = btn.styleSheet()
        
        btn.setText("Copied ✔️")
        btn.setStyleSheet("""
            QPushButton { background-color: #a6e3a1; color: #11111b; font-weight: bold; border-radius: 5px; }
        """)
        
        QTimer.singleShot(1500, lambda: self.reset_button(btn, original_text, original_style))

    def reset_button(self, btn, text, style):
        btn.setText(text)
        btn.setStyleSheet(style)

    def start_download_flow(self, url, play_btn, copy_btn, dl_btn):
        # تعطيل الأزرار حتى لا يتم الضغط أكثر من مرة
        play_btn.setEnabled(False)
        copy_btn.setEnabled(False)
        dl_btn.setEnabled(False)
        dl_btn.setText("⏳ Fetching...")
        
        # استدعاء YTInfoFetcher المدمج لإنهاء جلب البيانات
        self.fetcher = YTInfoFetcher(url)
        self.fetcher.finished.connect(self.on_info_fetched)
        self.fetcher.error.connect(lambda err: self.on_fetch_error(err, play_btn, copy_btn, dl_btn))
        self.fetcher.start()

    def on_info_fetched(self, info):
        # استدعاء محلي لتجنب الـ Circular Import
        from ui_components import QualitySelectorDialog 
        
        # إغلاق نافذة البحث والانتقال لتحميل
        self.accept() 
        selector = QualitySelectorDialog(info, self.parent())
        selector.show()

    def on_fetch_error(self, err, play_btn, copy_btn, dl_btn):
        # تفعيل الأزرار مرة أخرى في حالة الخطأ
        play_btn.setEnabled(True)
        copy_btn.setEnabled(True)
        dl_btn.setEnabled(True)
        dl_btn.setText("📥 Download")
        print(f"[*] ⚠️ Fetch error during search download: {err}")

# --- New Components for Background Fetching and Downloading (System yt-dlp version) ---

class YTInfoFetcher(QThread):
    """خيط لجلب كافة بيانات الفيديو التفصيلية في الخلفية باستخدام أوامر النظام."""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = clean_youtube_url(url) # تنظيف الرابط هنا

    def run(self):
        try:
            # استدعاء yt-dlp من النظام وجلب البيانات كـ JSON
            result = subprocess.run(
                ["yt-dlp", "--dump-json", "--no-warnings", "--ignore-errors", self.url],
                capture_output=True, text=True, check=True
            )
            info = json.loads(result.stdout)
            self.finished.emit(info)
        except subprocess.CalledProcessError as e:
            self.error.emit(f"Process Error: {e.stderr}")
        except Exception as e:
            self.error.emit(str(e))

class DownloadWorker(QThread):
    """خيط للتحميل الفعلي للفيديو وإرسال التقدم بالاعتماد على مخرجات yt-dlp في الطرفية"""
    progress_signal = pyqtSignal(dict)
    finished_signal = pyqtSignal()

    def __init__(self, url, format_id, dl_options=None):
        super().__init__()
        self.url = clean_youtube_url(url) # تنظيف الرابط هنا
        self.format_id = format_id
        self.dl_options = dl_options or {}
        
        # متغيرات التحكم بالإلغاء ومسح الملفات
        self._abort = False
        self._delete_parts = False
        self.process = None # لحفظ كائن العملية للتمكن من قتلها
        self.downloaded_filepaths = set() # لحفظ مسارات الملفات قيد التحميل لتنظيفها لاحقاً
        
        # متغيرات تتبع الأحجام والتيار (فيديو أم صوت)
        self.current_stream = "Video"
        self.video_size = "Unknown"
        self.audio_size = "Unknown"
        self.dest_count = 0

    def abort(self, delete_parts):
        """دالة لإرسال أمر إيقاف التحميل وإنهاء العملية النظامية"""
        self._abort = True
        self._delete_parts = delete_parts
        if self.process:
            self.process.terminate() # إنهاء عملية subprocess فوراً

    def run(self):
        # جلب مسار التحميل المخصص من الكاش
        path_file = Path.home() / ".cache" / "hardplayer" / "download_path.txt"
        output_template = '%(title)s [%(id)s].%(ext)s' # القالب الافتراضي
        target_dir = os.getcwd() # مسار افتراضي لحفظ ملف الاستكمال
        
        if path_file.exists():
            custom_path = path_file.read_text(encoding="utf-8").strip()
            if custom_path and os.path.exists(custom_path):
                target_dir = custom_path
                # دمج المجلد المختار مع قالب اسم الملف
                output_template = os.path.join(custom_path, '%(title)s [%(id)s].%(ext)s')

        # حفظ بيانات التحميل لتمكين الاستكمال لاحقاً
        self.state_file = os.path.join(target_dir, "hardplayer_resume_state.json")
        state_data = {
            "url": self.url,
            "format_id": self.format_id,
            "options": self.dl_options
        }
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f)
        except Exception as e:
            print(f"[*] ⚠️ Could not save resume state file: {e}")

        # بناء أمر yt-dlp
        cmd = [
            "yt-dlp",
            "-f", self.format_id,
            "-o", output_template,
            "--newline",         # ضروري جداً لقراءة التقدم سطراً بسطر في الـ stdout
            "--ignore-errors",
            "--no-warnings"
        ]

        # 1. الترجمة
        if self.dl_options.get('subs'):
            cmd.extend(["--write-subs", "--write-auto-subs"])
            lang = self.dl_options.get('sub_lang', 'en,ar')
            if lang:
                cmd.extend(["--sub-langs", lang])
            # تحويل ودمج الترجمة
            cmd.extend(["--convert-subs", "srt", "--embed-subs"])

        # 2. الصورة المصغرة
        if self.dl_options.get('thumb'):
            cmd.extend(["--write-thumbnail", "--convert-thumbnails", "jpg", "--embed-thumbnail"])

        # 3. الفصول
        if self.dl_options.get('chapters'):
            cmd.extend(["--embed-chapters"])

        # إضافة الرابط في نهاية الأمر
        cmd.append(self.url)

        try:
            # استخدام Popen لقراءة المخرجات بشكل حي أثناء التحميل
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # تعبير نمطي مرن لاستخراج (النسبة، الحجم، السرعة، الوقت المتبقي)
            progress_regex = re.compile(
                r'\[download\]\s+(?P<percent>[0-9\.]+)%\s+of\s+~?(?P<size>[0-9a-zA-Z\.]+)'
                r'(?:\s+at\s+(?P<speed>[0-9a-zA-Z\.]+/s))?(?:\s+ETA\s+(?P<eta>[0-9:]+))?'
            )
            
            # استخراج مسارات الملفات للتمكن من حذفها في حالة الإلغاء
            dest_regex = re.compile(r'\[download\] Destination:\s+(.+)')
            merged_regex = re.compile(r'\[Merger\] Merging formats into \"(.+)\"')

            # قراءة المخرجات سطراً بسطر في الوقت الفعلي
            for line in self.process.stdout:
                if self._abort:
                    break

                line = clean_ansi(line)

                # 1. مراقبة الوجهة لمعرفة متى بدأ الفيديو ومتى بدأ الصوت
                dest_match = dest_regex.search(line)
                if dest_match:
                    self.dest_count += 1
                    if self.dest_count == 1: 
                        self.current_stream = "Video"
                    elif self.dest_count == 2: 
                        self.current_stream = "Audio"
                    self.downloaded_filepaths.add(dest_match.group(1).strip())
                    continue

                # 2. مراقبة عمليات الدمج والاستخراج لتحديث الواجهة بـ (Merging/Processing)
                merge_match = merged_regex.search(line)
                if merge_match:
                    self.downloaded_filepaths.add(merge_match.group(1).strip())
                    self.progress_signal.emit({'status': 'merging'})
                    continue
                    
                if "[ExtractAudio]" in line or "[Fixup" in line:
                    self.progress_signal.emit({'status': 'processing'})
                    continue

                # 3. إرسال بيانات التقدم والأحجام
                match = progress_regex.search(line)
                if match:
                    percent_val = float(match.group('percent'))
                    total_size = match.group('size')

                    if self.current_stream == "Video": 
                        self.video_size = total_size
                    elif self.current_stream == "Audio": 
                        self.audio_size = total_size

                    clean_data = {
                        'status': 'downloading',
                        'percent': percent_val,
                        '_speed_str': match.group('speed') if match.group('speed') else 'N/A',
                        '_eta_str': match.group('eta') if match.group('eta') else '00:00',
                        '_total_bytes_str': total_size,
                        'current_stream': self.current_stream,
                        'video_size': self.video_size,
                        'audio_size': self.audio_size
                    }
                    self.progress_signal.emit(clean_data)

            # انتظار انتهاء العملية
            self.process.wait()

            if self._abort:
                raise ValueError("DOWNLOAD_CANCELLED")
                
            # إرسال إشارة الانتهاء إذا كانت العملية ناجحة
            if self.process.returncode == 0 or self.process.returncode == 1:
                # التحميل اكتمل بنجاح، امسح ملف الاستكمال
                if hasattr(self, 'state_file') and os.path.exists(self.state_file):
                    try:
                        os.remove(self.state_file)
                    except Exception:
                        pass
                self.finished_signal.emit()

        except ValueError as e:
            if str(e) == "DOWNLOAD_CANCELLED":
                print("[*] 🛑 Download was manually cancelled.")
                if self._delete_parts:
                    for fpath in self.downloaded_filepaths:
                        for ext in ['', '.part', '.ytdl']:
                            f = fpath + ext
                            if os.path.exists(f):
                                try:
                                    os.remove(f)
                                except Exception:
                                    pass
        except Exception as e:
            print(f"[*] ⚠️ Download Worker Error: {e}")