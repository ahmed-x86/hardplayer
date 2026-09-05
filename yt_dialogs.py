# yt_dialogs.py

import json
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QLabel, QTextEdit, QLineEdit, QPushButton,
                             QScrollArea, QWidget, QFrame, QApplication)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QPixmap

# --- Import Backend from separate files ---
from yt_url_parser import clean_youtube_url
from yt_assets_fetcher import ImageFetcher
from yt_info_fetcher import YTInfoFetcher
from yt_search_engine import YTSearchEngine
from get_youtube_thumbnail import get_youtube_thumbnail

class YouTubeSimpleQualityDialog(QDialog):
    def __init__(self, yt_url, parent=None):
        super().__init__(parent)
        self.yt_url = clean_youtube_url(yt_url)
        self.format_code = None
        self.setWindowTitle("Select Video Quality")
        self.setFixedSize(350, 500)
        self.setModal(True)
        self.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(12)

        self.loading_lbl = QLabel("⏳ Fetching available qualities...\nPlease wait.")
        self.loading_lbl.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.loading_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.loading_lbl)

        QTimer.singleShot(100, self.fetch_dynamic_qualities)

    def fetch_dynamic_qualities(self):
        try:
            result = subprocess.run(
                ["yt-dlp", "--dump-json", "--no-warnings", self.yt_url],
                capture_output=True, text=True, check=True
            )
            data = json.loads(result.stdout)
            formats = data.get('formats', [])

            available_heights = set()
            for f in formats:
                vcodec = f.get('vcodec', 'none')
                height = f.get('height')
                if vcodec != 'none' and height:
                    available_heights.add(int(height))

            sorted_heights = sorted(list(available_heights), reverse=True)
            self.populate_buttons(sorted_heights, formats)

        except Exception as e:
            print(f"[*] ⚠️ Error fetching dynamic qualities: {e}")
            self.populate_buttons([1080, 720, 480, 360, 240, 144], [])

    def populate_buttons(self, heights, formats=None):
        if formats is None:
            formats = []
            
        pref_ext = None
        ext_file = Path.home() / ".cache" / "hardplayer" / "youtube_video_ext.txt"
        if ext_file.exists():
            pref_ext = ext_file.read_text(encoding="utf-8").strip()

        self.loading_lbl.deleteLater()

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

        if pref_ext == "mp4":
            best_code = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/bestvideo+bestaudio/best"
        elif pref_ext:
            best_code = f"bestvideo[ext={pref_ext}]+bestaudio/best[ext={pref_ext}]/bestvideo+bestaudio/best"
        else:
            best_code = "bestvideo+bestaudio/best"
            
        self.add_quality_button(content_layout, "🌟 Best Quality (Auto)", best_code, "#a6e3a1", "#11111b")

        for h in heights:
            emoji = "📺" if h >= 720 else ("📱" if h >= 360 else "🥔")
            available_exts = set()
            for f in formats:
                if f.get('vcodec') != 'none' and f.get('height') == h:
                    ext = f.get('ext')
                    if ext: available_exts.add(ext)
            
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
                
            self.add_quality_button(content_layout, text, code)

        self.add_quality_button(content_layout, "🎵 Audio Only (MP3/M4A)", "bestaudio/best")

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        self.layout.addWidget(scroll)

        self.adv_btn = QPushButton("⚙️ Advanced (Manual Code)")
        self.adv_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.adv_btn.setStyleSheet("QPushButton { background-color: transparent; color: #f38ba8; padding: 10px; border-radius: 6px; border: 1px solid #f38ba8; font-weight: bold; } QPushButton:hover { background-color: #f38ba8; color: #11111b; }")
        self.adv_btn.clicked.connect(self.open_advanced)
        self.layout.addWidget(self.adv_btn)

    def add_quality_button(self, layout, text, code, bg_hover="#89b4fa", text_hover="#11111b"):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"QPushButton {{ background-color: #313244; padding: 10px; border-radius: 6px; font-size: 13px; font-weight: bold; text-align: left; }} QPushButton:hover {{ background-color: {bg_hover}; color: {text_hover}; }}")
        btn.clicked.connect(lambda checked, c=code: self.select_format(c))
        layout.addWidget(btn)

    def select_format(self, code):
        self.format_code = code
        self.accept()

    def open_advanced(self):
        self.format_code = "ADVANCED"
        self.accept()


class YouTubeQualityDialog(QDialog):
    def __init__(self, yt_url, mode="play", parent=None):
        super().__init__(parent)
        self.yt_url = clean_youtube_url(yt_url) 
        self.format_code = "best"
        self.mode = mode  
        
        self.setWindowTitle("YouTube Video Formats (Download Mode)" if self.mode == "download" else "YouTube Video Formats (Advanced)")
        self.setFixedSize(850, 500)
        self.setModal(True)
        self.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        lbl = QLabel(f"🔗 URL: {self.yt_url}\n⏳ Fetching formats, please wait...")
        lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(lbl)
        
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
        
        btn_text = "📥 Download Video" if self.mode == "download" else "▶ Continue to Decoding"
        btn_color = "#cba6f7" if self.mode == "download" else "#89b4fa"
        self.action_btn = QPushButton(btn_text)
        self.action_btn.setStyleSheet(f"QPushButton {{ background-color: {btn_color}; color: #11111b; font-weight: bold; padding: 8px 15px; border-radius: 4px; border: none; }} QPushButton:hover {{ background-color: #b4befe; }}")
        self.action_btn.clicked.connect(self.accept_format)
        
        input_layout.addWidget(QLabel("📝 Format Code:"))
        input_layout.addWidget(self.format_input)
        input_layout.addWidget(self.action_btn)
        
        layout.addLayout(input_layout)
        QTimer.singleShot(100, self.fetch_formats)

    def fetch_formats(self):
        try:
            result = subprocess.run(["yt-dlp", "-F", self.yt_url], capture_output=True, text=True, check=True)
            self.info_text.setText(result.stdout)
            scrollbar = self.info_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except Exception as e:
            self.info_text.setText(f"❌ Error fetching formats.\n\n{str(e)}")

    def accept_format(self):
        self.format_code = self.format_input.text().strip() or "best"
        self.accept()


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

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background-color: transparent;")
        
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_layout.setSpacing(10)
        self.scroll_area.setWidget(self.scroll_content)
        
        self.layout.addWidget(self.scroll_area)
        self.scroll_area.hide()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("QPushButton { background-color: #313244; color: #cdd6f4; padding: 10px; border-radius: 5px; font-weight: bold; } QPushButton:hover { background-color: #45475a; }")
        self.cancel_btn.clicked.connect(self.reject)
        self.layout.addWidget(self.cancel_btn)

        self.fetchers = []
        
        # Bind search interface to the new YTSearchEngine search engine
        self.search_engine = YTSearchEngine(self.query)
        self.search_engine.results_fetched.connect(self.on_results_fetched)
        self.search_engine.error_occurred.connect(self.on_search_error)
        self.search_engine.start()

    def on_results_fetched(self, results_text):
        self.loading_label.hide()
        self.scroll_area.show()
        
        lines = results_text.split('\n')
        for line in lines:
            if not line.strip(): continue
            try:
                video_data = json.loads(line)
                self.add_video_card(video_data)
            except Exception as e:
                print(f"Error parsing JSON for a video: {e}")

    def on_search_error(self, error_msg):
        self.loading_label.setText(error_msg)

    def add_video_card(self, video):
        card = QFrame()
        card.setStyleSheet("QFrame { background-color: #181825; border-radius: 10px; }")
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(10, 10, 10, 10)
        card_layout.setSpacing(15)
        
        video_id = video.get('id', '')
        link = video.get('webpage_url', f"https://www.youtube.com/watch?v={video_id}")
        
        thumb_label = QLabel()
        thumb_label.setFixedSize(160, 90)
        thumb_label.setStyleSheet("background-color: #11111b; border-radius: 5px;")
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_label.setText("Loading...")
        
        thumb_url = get_youtube_thumbnail(link)
        
        if thumb_url:
            fetcher = ImageFetcher(thumb_url, f"vid_{video_id}")
            fetcher.image_fetched.connect(lambda vid, data, lbl=thumb_label: self.update_image(lbl, data, 160, 90))
            fetcher.start()
            self.fetchers.append(fetcher)

        card_layout.addWidget(thumb_label)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        title = video.get('title', 'Unknown Title')
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet("color: #89b4fa; border: none; background: transparent;")
        
        channel_layout = QHBoxLayout()
        channel_name = video.get('uploader', 'Unknown Channel')
        
        avatar_label = QLabel("👤")
        avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_label.setFixedSize(24, 24)
        avatar_label.setStyleSheet("background-color: #313244; border-radius: 12px; color: #cdd6f4; font-size: 12px;")
        
        duration_str = video.get('duration_string')
        if not duration_str:
            d_sec = video.get('duration', 0)
            mins, secs = divmod(int(d_sec), 60)
            duration_str = f"{mins}:{secs:02d}"
            
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
        
        for_layout = QVBoxLayout()
        for_layout.setSpacing(5)
        
        play_btn = QPushButton("▶ Play")
        play_btn.setFixedSize(110, 30)
        play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        play_btn.setStyleSheet("QPushButton { background-color: #a6e3a1; color: #11111b; font-weight: bold; border-radius: 5px; } QPushButton:hover { background-color: #94e2d5; } QPushButton:disabled { background-color: #585b70; color: #a6adc8; }")
        play_btn.clicked.connect(lambda checked, url=link: self.select_video(url))
        
        copy_btn = QPushButton("🔗 Copy Link")
        copy_btn.setFixedSize(110, 30)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setStyleSheet("QPushButton { background-color: #89b4fa; color: #11111b; font-weight: bold; border-radius: 5px; } QPushButton:hover { background-color: #b4befe; } QPushButton:disabled { background-color: #585b70; color: #a6adc8; }")
        copy_btn.clicked.connect(lambda checked, url=link, btn=copy_btn: self.copy_link(url, btn))
        
        dl_btn = QPushButton("📥 Download")
        dl_btn.setFixedSize(110, 30)
        dl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dl_btn.setStyleSheet("QPushButton { background-color: #cba6f7; color: #11111b; font-weight: bold; border-radius: 5px; } QPushButton:hover { background-color: #b4befe; } QPushButton:disabled { background-color: #585b70; color: #a6adc8; }")
        dl_btn.clicked.connect(lambda checked, url=link, p=play_btn, c=copy_btn, d=dl_btn: self.start_download_flow(url, p, c, d))
        
        for_layout.addWidget(play_btn)
        for_layout.addWidget(copy_btn)
        for_layout.addWidget(dl_btn)
        for_layout.addStretch()
        
        card_layout.addLayout(for_layout)
        self.scroll_layout.addWidget(card)

    def update_image(self, label, data, w, h):
        pixmap = QPixmap()
        if pixmap.loadFromData(data):
            label.setPixmap(pixmap.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
            label.setText("")

    def select_video(self, url):
        self.selected_url = url
        self.accept()
        
    def copy_link(self, url, btn):
        QApplication.clipboard().setText(url)
        original_text = btn.text()
        original_style = btn.styleSheet()
        btn.setText("Copied ✔️")
        btn.setStyleSheet("QPushButton { background-color: #a6e3a1; color: #11111b; font-weight: bold; border-radius: 5px; }")
        QTimer.singleShot(1500, lambda: self.reset_button(btn, original_text, original_style))

    def reset_button(self, btn, text, style):
        btn.setText(text)
        btn.setStyleSheet(style)

    def start_download_flow(self, url, play_btn, copy_btn, dl_btn):
        play_btn.setEnabled(False)
        copy_btn.setEnabled(False)
        dl_btn.setEnabled(False)
        dl_btn.setText("⏳ Fetching...")
        
        self.fetcher = YTInfoFetcher(url)
        self.fetcher.finished.connect(self.on_info_fetched)
        self.fetcher.error.connect(lambda err: self.on_fetch_error(err, play_btn, copy_btn, dl_btn))
        self.fetcher.start()

    def on_info_fetched(self, info):
        # Access external interfaces without modifying them, just call what we need
        from ui_components import QualitySelectorDialog 
        
        self.accept() 
        selector = QualitySelectorDialog(info, self.parent())
        selector.show()

    def on_fetch_error(self, err, play_btn, copy_btn, dl_btn):
        play_btn.setEnabled(True)
        copy_btn.setEnabled(True)
        dl_btn.setEnabled(True)
        dl_btn.setText("📥 Download")
        print(f"[*] ⚠️ Fetch error during search download: {err}")