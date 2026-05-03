# playlist_panel.py

import os
import json
import urllib.request
from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                             QScrollArea, QWidget, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QPixmap

# Import the local thumbnail generator
from thumbnail_gen import get_local_thumbnail
# Import the YouTube thumbnail extractor
from get_youtube_thumbnail import get_youtube_thumbnail

class AsyncYouTubeDataFetcher(QThread):
    """
    خيط (Thread) لجلب معلومات يوتيوب والصورة المصغرة بالخلفية 
    دون تجميد واجهة المستخدم. يعتمد على oEmbed لسرعته الخارقة.
    """
    data_fetched = pyqtSignal(str, str, bytes) # Title, Channel Name, Image Bytes

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        title = "YouTube Video"
        uploader = ""
        # استخدام دالتك كمسار احتياطي/أساسي للصورة
        thumb_url = get_youtube_thumbnail(self.url)
        image_bytes = b""

        # 1. جلب اسم الفيديو والقناة باستخدام YouTube oEmbed API السريع جداً
        try:
            # تنظيف الرابط من إضافات القائمة لضمان دقة API
            clean_url = self.url.split('&list=')[0].split('&index=')[0]
            oembed_url = f"https://www.youtube.com/oembed?url={clean_url}&format=json"
            req = urllib.request.Request(oembed_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                title = data.get('title', title)
                uploader = data.get('author_name', uploader)
                # استخدام صورة oEmbed إذا كانت متوفرة لأنها دقيقة
                thumb_url = data.get('thumbnail_url', thumb_url)
        except Exception:
            # التعديل هنا: إذا فشل الاتصال، اجعل العنوان "YouTube Video" بدلاً من الـ ID الطويل
            # لكي لا تظهر نصوص غريبة مثل "Video ID: xxxxxxx" في القائمة
            title = "YouTube Video"

        # 2. تحميل بايتات الصورة المصغرة (Thumbnail Bytes)
        try:
            if thumb_url:
                req_img = urllib.request.Request(thumb_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req_img, timeout=5) as response:
                    image_bytes = response.read()
        except Exception:
            pass

        # إرسال البيانات للواجهة لتحديث الزر
        self.data_fetched.emit(title, uploader, image_bytes)


class PlaylistPanel(QFrame):
    """
    Sidebar Playlist panel with Lazy Loading implementation to prevent UI freezes.
    """
    # Signal emitted with the file path when a media item is clicked
    file_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.playlist = []
        self.loaded_items_count = 0
        self.load_more_btn = None
        self.yt_fetchers = [] # تخزين خيوط الجلب لمنع إغلاقها مبكراً
        
        self.init_ui()

    def init_ui(self):
        # The MAGIC FIX: Force the overlay to be a Native Window 
        # so it draws correctly over the MPV Native Window in Linux/Wayland.
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        self.setFixedWidth(300)
        self.setVisible(False)
        
        # Catppuccin Mocha overlay style (slightly transparent crust/mantle)
        self.setStyleSheet("""
            QFrame { 
                background-color: rgba(24, 24, 37, 230); 
                border-left: 2px solid #313244; 
            }
        """)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Panel Title
        self.title_lbl = QLabel("Media Playlist")
        self.title_lbl.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.title_lbl.setStyleSheet("color: #cdd6f4; background: transparent; margin-bottom: 10px;")
        self.main_layout.addWidget(self.title_lbl)
        
        # Scroll Area setup
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background: transparent;")
        
        self.playlist_content = QWidget()
        self.playlist_content.setStyleSheet("background: transparent;")
        self.playlist_items_layout = QVBoxLayout(self.playlist_content)
        self.playlist_items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.playlist_items_layout.setSpacing(12)
        
        self.scroll_area.setWidget(self.playlist_content)
        self.main_layout.addWidget(self.scroll_area)

    def set_playlist_data(self, files_list):
        """Update the playlist data and reset the UI."""
        self.playlist = files_list
        self.yt_fetchers = [] # تنظيف الخيوط القديمة
        
        # تعديل العنوان ديناميكياً
        if files_list and files_list[0].startswith("http"):
            self.title_lbl.setText("YouTube Playlist")
        else:
            self.title_lbl.setText("Media in Folder")
            
        self.populate_ui()

    def populate_ui(self):
        """Clear existing items and start loading the first batch."""
        # Clear old items to prevent duplicates when switching folders
        while self.playlist_items_layout.count():
            item = self.playlist_items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.loaded_items_count = 0
        self.load_more_items()

    def load_more_items(self):
        """Loads items in batches of 6 to prevent UI freezing (Lazy Loading)."""
        # Remove the 'Load More' button temporarily if it exists
        if hasattr(self, 'load_more_btn') and self.load_more_btn:
            self.playlist_items_layout.removeWidget(self.load_more_btn)
            self.load_more_btn.deleteLater()
            self.load_more_btn = None

        start_index = self.loaded_items_count
        end_index = min(start_index + 6, len(self.playlist))
        batch = self.playlist[start_index:end_index]
            
        for path in batch:
            item_widget = self.create_item_widget(path)
            self.playlist_items_layout.addWidget(item_widget)

        self.loaded_items_count = end_index
        
        # Add the 'Load More' button if there are remaining items in the list
        if self.loaded_items_count < len(self.playlist):
            self.load_more_btn = QPushButton("Load More ⏬")
            self.load_more_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.load_more_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #313244; 
                    color: #cdd6f4; 
                    border-radius: 8px; 
                    padding: 8px; 
                    font-weight: bold; 
                }
                QPushButton:hover { background-color: #45475a; color: #89b4fa; }
            """)
            self.load_more_btn.clicked.connect(self.load_more_items)
            self.playlist_items_layout.addWidget(self.load_more_btn)

    def create_item_widget(self, path):
        """Creates a single video item widget for the playlist."""
        item_frame = QFrame()
        item_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        item_frame.setStyleSheet("""
            QFrame { background-color: #313244; border-radius: 8px; }
            QFrame:hover { background-color: #45475a; }
        """)
        
        h_layout = QHBoxLayout(item_frame)
        h_layout.setContentsMargins(5, 5, 5, 5)
        
        # Thumbnail display
        thumb_label = QLabel()
        thumb_label.setFixedSize(80, 45)
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_label.setStyleSheet("background-color: #11111b; color: #fab387; border-radius: 4px;")
        
        name_label = QLabel()
        name_label.setStyleSheet("color: #cdd6f4; font-size: 11px; background: transparent;")
        name_label.setWordWrap(True)

        if path.startswith("http"):
            # --- معالجة روابط يوتيوب ديناميكياً ---
            thumb_label.setText("⏳")
            name_label.setText("Fetching data...")
            
            # بدء الجلب في الخلفية لتحديث الزر
            fetcher = AsyncYouTubeDataFetcher(path)
            fetcher.data_fetched.connect(lambda t, u, b, nl=name_label, tl=thumb_label: self.update_yt_item(nl, tl, t, u, b))
            self.yt_fetchers.append(fetcher)
            fetcher.start()
        else:
            # --- معالجة الملفات المحلية ---
            thumb_path = get_local_thumbnail(path)
            if thumb_path and os.path.exists(thumb_path):
                pix = QPixmap(thumb_path).scaled(80, 45, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                thumb_label.setPixmap(pix)
            else:
                thumb_label.setText("🎬")

            # Filename formatting (Max 4 words for line 1, 2 words for line 2)
            name = os.path.basename(path)
            words = name.split()
            line1 = " ".join(words[:4])
            line2 = " ".join(words[4:6]) + "..." if len(words) > 4 else ""
            name_label.setText(f"{line1}\n{line2}" if line2 else line1)
        
        h_layout.addWidget(thumb_label)
        h_layout.addWidget(name_label, 1)
        
        # Connect click event to emit the selected file path
        item_frame.mousePressEvent = lambda e, p=path: self.file_selected.emit(p)
        
        return item_frame

    def update_yt_item(self, name_label, thumb_label, title, uploader, image_bytes):
        """تحديث بيانات اليوتيوب في الزر بعد انتهاء الجلب من الخلفية"""
        # قص العنوان الطويل لكي لا يكسر الواجهة
        words = title.split()
        line1 = " ".join(words[:4])
        line2 = " ".join(words[4:7]) + "..." if len(words) > 4 else ""
        display_title = f"{line1}\n{line2}" if line2 else line1
        
        # إضافة اسم القناة بالأسفل (إذا توفرت)
        if uploader:
            display_text = f"{display_title}\n👤 {uploader[:15]}"
        else:
            display_text = display_title
            
        name_label.setText(display_text)
        
        # تطبيق الصورة المصغرة
        if image_bytes:
            pix = QPixmap()
            if pix.loadFromData(image_bytes):
                thumb_label.setPixmap(pix.scaled(80, 45, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                thumb_label.setText("🎬")
        else:
            thumb_label.setText("🎬")

    def update_position(self, container_width, container_height):
        """Updates the sidebar position to dock at the far right, overlaying the content."""
        w = 300
        x = container_width - w
        self.setGeometry(x, 0, w, container_height)