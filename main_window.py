# main_window.py

import os
import glob
import threading
import mpv
import json
import subprocess
import re
from pathlib import Path

from PyQt6.QtWidgets import (QMainWindow, QStackedWidget, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QFileDialog, QDialog)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

# --- Import separated modular components ---
from top_menu import TopMenuBar
from bottom_controls import PlayerControlBar
from playlist_panel import PlaylistPanel
from video_surface import VideoSurface
from styles import AppStyles

# Import configurations and features
from config import BASE
from mpris_feature import HardPlayerMPRIS
from hw_decoding import DecodingDialog, DEVICE_MAP
from youtube_feature import YouTubeSimpleQualityDialog, YouTubeQualityDialog, YouTubeSearchDialog
from ui_components import InfoDialog, StartupDialog

# --- استيراد مدير التحويل ---
from top_menu_convert import ConvertMenuManager

try:
    from gi.repository import GLib
except ImportError:
    GLib = None # تم التعديل هنا: نحدد المتغير كـ None بدلاً من تجاهله لتجنب NameError

# --- New: YouTube Playlist Fetcher Thread ---
class YouTubePlaylistFetcher(QThread):
    """
    خيط (Thread) يعمل في الخلفية لجلب جميع الفيديوهات داخل قائمة تشغيل يوتيوب
    باستخدام yt-dlp بدون تجميد واجهة المستخدم.
    """
    playlist_fetched = pyqtSignal(list, str) # يرسل (قائمة الروابط، الرابط الأصلي)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            cmd = [
                "yt-dlp",
                "--flat-playlist",
                "--dump-json",
                "--ignore-errors",
                "--no-warnings",
                self.url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            urls = []
            
            for line in lines:
                if not line.strip(): continue
                try:
                    data = json.loads(line)
                    # استخراج رابط الفيديو من القائمة
                    vid_url = data.get('url') or data.get('webpage_url')
                    if not vid_url and data.get('id'):
                        vid_url = f"https://www.youtube.com/watch?v={data['id']}"
                        
                    if vid_url:
                        urls.append(vid_url)
                except Exception:
                    pass
            
            if urls:
                self.playlist_fetched.emit(urls, self.url)
                
        except Exception as e:
            print(f"[*] ⚠️ Playlist fetch error: {e}")


class HardPlayerWindow(QMainWindow):
    """
    The main application window. Acts as a controller connecting the UI to the MPV engine.
    """
    # إشارة تخبرنا أن الفيديو قد انتهى بأمان
    video_ended = pyqtSignal()

    def __init__(self, cli_path=None, cli_device=None, cli_search=False, cli_quality=None):
        super().__init__()
        self.setWindowTitle("HardPlayer")
        self.resize(1000, 600)
        self.setStyleSheet(AppStyles.MAIN_WINDOW)

        # --- CLI arguments ---
        self.cli_path = cli_path
        self.cli_device = cli_device
        self.cli_search = cli_search
        self.cli_quality = cli_quality
        
        self.quality_map = {
            'best': 'bestvideo+bestaudio/best',
            '1080p': 'bestvideo[height<=1080]+bestaudio/best',
            '720p': 'bestvideo[height<=720]+bestaudio/best',
            '480p': 'bestvideo[height<=480]+bestaudio/best',
            'audio': 'bestaudio/best'
        }

        self.setup_ui()
        self.setup_mpv()
        self.connect_signals()

        # D-Bus/MPRIS integration
        self.start_mpris_service()
        
        # CLI Launch handling
        if not self.cli_path:
            QTimer.singleShot(100, self.show_startup_dialog)
        else:
            QTimer.singleShot(100, self.process_cli_launch)

    def setup_ui(self):
        """Build the UI structure using the separated modular components."""
        # 1. Top Menu
        self.menu_bar = TopMenuBar(self)
        self.setMenuBar(self.menu_bar)

        # 2. Central Layout
        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 3. Content Container (Video + Sidebar Overlay)
        self.content_container = QWidget()
        self.content_layout = QHBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        # 4. Video/Logo Stack
        self.stack = QStackedWidget()
        self.content_layout.addWidget(self.stack)

        self.setup_logo_screen()
        
        # Using VideoSurface instead of manually building the Native Window here
        self.video_surface = VideoSurface()
        self.stack.addWidget(self.video_surface)

        self.main_layout.addWidget(self.content_container)

        # 5. Playlist Sidebar (Overlay)
        self.playlist_panel = PlaylistPanel(self.content_container)

        # 6. Bottom Controls
        self.controls = PlayerControlBar(self)
        self.main_layout.addWidget(self.controls)

        self.playlist = []
        self.current_index = -1
        self._keyboard_seeking = False
        
        # --- استدعاء مدير قائمة التحويل وربطه بالنافذة الرئيسية ---
        self.convert_manager = ConvertMenuManager(self)

    def setup_logo_screen(self):
        """Set up the startup screen (Logo)."""
        self.logo_widget = QWidget()
        logo_layout = QVBoxLayout(self.logo_widget)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        pixmap = QPixmap(os.path.join(base_dir, "icon_in_app.png"))
        if not pixmap.isNull():
            self.icon_label.setPixmap(pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        self.logo_label = QLabel("HardPlayer")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setFont(QFont("Arial", 48, QFont.Weight.Bold))
        self.logo_label.setStyleSheet("color: #cdd6f4;")
        
        logo_layout.addWidget(self.icon_label)
        logo_layout.addWidget(self.logo_label)
        self.stack.addWidget(self.logo_widget)

    def setup_mpv(self):
        """Initialize the MPV engine and link it to the Video Surface."""
        def custom_mpv_logger(loglevel, component, message):
            msg = message.lower()
            if any(x in msg for x in ["late sei", "legacy vo", "streams.videolan.org"]): return
            if loglevel in ['error', 'fatal']: print(f"[{loglevel.upper()}] {component}: {message}")
            elif loglevel == 'info' and component in ['cplayer', 'vd']:
                if any(x in message for x in ['Video', 'Audio', 'Using hardware decoding']):
                    print(f"[INFO] {message}")

        self.player = mpv.MPV(
            wid=self.video_surface.get_mpv_wid(),
            vo='gpu', 
            gpu_context='x11egl', 
            osc=False,
            input_default_bindings=False, 
            input_vo_keyboard=False, 
            keep_open=True,
            loglevel='info', 
            log_handler=custom_mpv_logger
        )

        # ==========================================
        # --- فرض نافذة الفيديو لتعمل الترجمة مع الصوتيات ---
        # ==========================================
        self.player['force-window'] = 'yes'

        # إعداد التكرار الأولي للبرنامج
        self.current_loop_status = "None"
        self.player['loop-file'] = 'no'
        
        # --- إضافة: السماح بالبحث التلقائي عن ملفات الترجمة ---
        self.player['sub-auto'] = 'fuzzy'

        # --- تخصيص شكل الترجمة (ستايل المربع الشفاف) ---
        self.player['sub-color'] = '#c4a6f1'           
        self.player['sub-back-color'] = '#B31d1d2c'    
        self.player['sub-border-style'] = 'opaque-box' 
        self.player['sub-border-size'] = 3             
        self.player['sub-shadow-offset'] = 0           
        self.player['sub-margin-y'] = 40               

        # ==========================================
        # --- إصلاح منطق إزاحة الأسطر (The Sliding Logic) ---
        # ==========================================
        # هذا هو السطر الذي سيدمر إحداثيات يوتيوب ويجعل النص ينزلق بسلاسة للأعلى
        self.player['sub-ass-override'] = 'strip' 
        
        self.player['sub-fix-timing'] = 'no' 
        self.player['sub-ass-force-margins'] = 'yes'
        self.player['sub-use-margins'] = 'yes'
        self.player['sub-align-y'] = 'bottom'
        
        # حالة تفعيل الترجمة في الواجهة
        self._subtitles_enabled = False

        # ربط مراقب (Observer) لخاصية sub-text للتأكد من عدم ظهور مربعات فارغة
        self.player.observe_property('sub-text', self.on_sub_text_change)
        
        # مراقبة متى ينتهي الفيديو لنتحكم بالقائمة "بضمير"
        self.player.observe_property('eof-reached', self.on_eof_reached)

        # UI Timer
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self.update_ui_state)
        self.ui_timer.start(500)

    def connect_signals(self):
        """Connect UI signals to logical functions."""
        # Top Menu
        self.menu_bar.playlist_toggled.connect(self.toggle_playlist_sidebar)
        
        # Playlist Panel
        self.playlist_panel.file_selected.connect(self.play_from_sidebar)
        
        # Bottom Controls
        self.controls.play_toggled.connect(self.toggle_playback)
        self.controls.stop_clicked.connect(self.stop_playback)
        self.controls.next_clicked.connect(self.play_next)
        self.controls.prev_clicked.connect(self.play_previous)
        self.controls.seek_requested.connect(self.seek_video)
        
        # ربط التكرار الجديد
        self.controls.repeat_mode_changed.connect(self.handle_ui_repeat_change)
        # ربط الترجمة
        self.controls.subtitle_toggled.connect(self.toggle_subtitles)
        
        # ربط إشارة انتهاء الفيديو
        self.video_ended.connect(self.handle_video_ended)

    # ==========================================
    # --- UI & Event Overrides ---
    # ==========================================
    def resizeEvent(self, event):
        """Update the sidebar position when the window is resized."""
        super().resizeEvent(event)
        self.playlist_panel.update_position(self.content_container.width(), self.content_container.height())

    def toggle_playlist_sidebar(self):
        is_visible = self.playlist_panel.isVisible()
        self.playlist_panel.setVisible(not is_visible)
        if not is_visible:
            self.playlist_panel.raise_()

    def update_ui_state(self):
        """Pass the player state to the bottom control bar."""
        self.controls.update_ui_state(
            current_time=self.player.time_pos,
            duration=self.player.duration,
            is_paused=self.player.pause,
            is_seeking=self._keyboard_seeking
        )

    # ==========================================
    # --- Playback Logic & CLI ---
    # ==========================================
    def play_from_sidebar(self, path):
        print(f"[*] 🔄 Switching to: {path}")
        self.player.stop()
        
        if path in self.playlist:
            self.current_index = self.playlist.index(path)
            
        self.play_youtube(path, reset_playlist=False)
    
    def browse_video(self):
        """Opens file dialog for video selection."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "", "Video Files (*.mp4 *.mkv *.webm *.avi *.ts *.m4v);;All Files (*)"
        )
        if file_path: 
            self.ask_for_decoding_and_play(file_path)

    def toggle_playback(self):
        self.player.pause = not self.player.pause

    def stop_playback(self):
        self.player.stop()
        self.stack.setCurrentWidget(self.logo_widget)
        print("[*] ⏹ Playback stopped, returning to main screen.")

    # ==========================================
    # --- Loop Logic (Simple Mode) ---
    # ==========================================
    def handle_ui_repeat_change(self, status: str):
        """يتغير الوضع عند النقر على الزر في الواجهة"""
        self.current_loop_status = status
        # نخبر MPV ليعيد مقطع واحد فقط، أو لا يفعل شيء في الحالات الأخرى (ونتحكم نحن)
        self.player['loop-file'] = 'inf' if status == "Track" else 'no'
        print(f"[*] 🔁 Loop Mode: {status}")
        
        if hasattr(self, 'mpris_provider') and self.mpris_provider:
            self.mpris_provider.update_loop_status(status)

    def handle_mpris_loop_change(self, status: str):
        """يتغير الوضع من الهاتف"""
        self.current_loop_status = status
        self.player['loop-file'] = 'inf' if status == "Track" else 'no'
        self.controls.set_repeat_status(status)

    def on_eof_reached(self, name, value):
        """عندما ينتهي تشغيل ملف، MPV يرسل هذه القيمة كـ True"""
        if value:
            self.video_ended.emit()

    def handle_video_ended(self):
        """الفصل في ما يحدث بعد انتهاء الفيديو بناءً على القائمة"""
        if not self.playlist: return
        if self.current_loop_status == "Track": return # MPV يعيده لوحده

        is_last_video = (self.current_index >= len(self.playlist) - 1)

        if self.current_loop_status == "Playlist":
            # play_next ستنتقل للتالي، وإذا كان الأخير ستعود للأول بفضل العلامة %
            self.play_next()
        elif self.current_loop_status == "None":
            if not is_last_video:
                self.play_next()
            else:
                self.stop_playback()

    # --- إضافة: دالة التبديل للترجمة بأمان (Safe Toggle) ---
    def toggle_subtitles(self):
        """التحكم في إظهار أو إخفاء الترجمة وتغيير لون الزر"""
        try:
            self._subtitles_enabled = not getattr(self, '_subtitles_enabled', False)
            
            # جلب النص الحالي بأمان تام لتفادي انهيار المحرك إذا لم يكن جاهزاً
            current_text = ""
            try:
                current_text = getattr(self.player, 'sub_text', "")
            except Exception:
                pass
                
            try:
                if self._subtitles_enabled and current_text and str(current_text).strip():
                    self.player['sub-visibility'] = True
                else:
                    self.player['sub-visibility'] = False
            except Exception:
                pass
            
            self.controls.set_subtitle_status(self._subtitles_enabled)
            state = "ON" if self._subtitles_enabled else "OFF"
            print(f"[*] 💬 Subtitles: {state}")
        except Exception as e:
            print(f"[*] ⚠️ Error toggling subtitles: {e}")

    def on_sub_text_change(self, name, value):
        """مراقب لضمان عدم ظهور المربع المعتم إذا كان النص فارغاً (Safe Observer)"""
        try:
            if not getattr(self, '_subtitles_enabled', False):
                self.player['sub-visibility'] = False
                return
                
            if not value or str(value).strip() == "":
                self.player['sub-visibility'] = False
            else:
                self.player['sub-visibility'] = True
        except Exception:
            # تجاهل صامت لتفادي أي أخطاء أثناء تغيير حالة الفيديو (Core Dump prevention)
            pass

    def seek_video(self, position):
        self.player.time_pos = position

    def play_next(self):
        if self.playlist:
            # بفضل % len()، هذه الدالة ترجع لأول فيديو إذا كنا في آخر فيديو
            self.current_index = (self.current_index + 1) % len(self.playlist)
            self.player.play(self.playlist[self.current_index])

    def play_previous(self):
        if self.playlist:
            self.current_index = (self.current_index - 1) % len(self.playlist)
            self.player.play(self.playlist[self.current_index])

    def scan_folder(self, current_file):
        try:
            folder = os.path.dirname(os.path.abspath(current_file))
            files = []
            for ext in ('*.mp4', '*.mkv', '*.webm', '*.avi', '*.ts', '*.m4v'):
                files.extend(glob.glob(os.path.join(folder, ext)))
            self.playlist = sorted(files)
            self.current_index = self.playlist.index(os.path.abspath(current_file))
        except Exception:
            self.playlist = [current_file]
            self.current_index = 0
            
        self.playlist_panel.set_playlist_data(self.playlist)

    def start_mpris_service(self):
        def loop_runner():
            
            if GLib is None:
                print("[*] ⚠️ GLib module is missing. MPRIS integration will be disabled in this build.")
                return
            self.mpris_provider = HardPlayerMPRIS(self)
            GLib.MainLoop().run()
        threading.Thread(target=loop_runner, daemon=True).start()

    def process_cli_launch(self):
        if self.cli_search:
            self.search_youtube_and_play(self.cli_path)
            return
        is_url = self.cli_path.startswith("http://") or self.cli_path.startswith("https://")
        if self.cli_device or self.cli_quality:
            self.play_youtube(self.cli_path) if is_url else self.fast_launch_local()
        else:
            self.play_youtube(self.cli_path) if is_url else self.ask_for_decoding_and_play(self.cli_path)

    def fast_launch_local(self):
        selected_hwdec = DEVICE_MAP.get(self.cli_device, "no")
        if selected_hwdec != "no":
            print(f"\n{'-'*60}\n[*] 🚀 CLI Fast Launch Activated")
            print(f"[*] 🖥️  Hardware Decoding Forced: {self.cli_device} -> {selected_hwdec}")

        self.player['hwdec'] = selected_hwdec
        self.scan_folder(self.cli_path)
        self.stack.setCurrentWidget(self.video_surface)
        self.player.play(self.cli_path)

    def ask_for_decoding_and_play(self, source):
        print(f"\n{'-'*60}\n[*] 📂 Video Selected: {source}")
        
        saved_hwdec = self.menu_bar.get_saved_hwdec()
        if saved_hwdec:
            print(f"[*] ⚡ Fast Track: Using Saved HWDEC '{saved_hwdec}'")
            self.player['hwdec'] = saved_hwdec
            self.scan_folder(source)
            self.stack.setCurrentWidget(self.video_surface)
            print(f"[*] ▶️  Passing to MPV Engine...\n{'-'*60}\n")
            self.player.play(source)
            return

        decoding_dialog = DecodingDialog(self)
        if decoding_dialog.exec() == QDialog.DialogCode.Accepted:
            selected_hwdec = decoding_dialog.selected_hwdec
            print(f"[*] 🖥️  Hardware Decoding Requested: {selected_hwdec}")
            
            self.player['hwdec'] = selected_hwdec
            self.scan_folder(source)
            self.stack.setCurrentWidget(self.video_surface)
            
            print(f"[*] ▶️  Passing to MPV Engine...\n{'-'*60}\n")
            self.player.play(source)

            def check_hwdec_status():
                current_hwdec = getattr(self.player, 'hwdec_current', 'no')
                if current_hwdec == "no" and selected_hwdec != "no":
                    print(f"\n\033[93m[⚠️ WARNING] Falling back to CPU.\033[0m\n")
                elif current_hwdec != "no":
                    print(f"\n\033[92m[✅ SUCCESS] Hardware decoding active! ({current_hwdec}).\033[0m\n")

            QTimer.singleShot(1500, check_hwdec_status)

    def search_youtube_and_play(self, query):
        search_dialog = YouTubeSearchDialog(query, self)
        if search_dialog.exec() == QDialog.DialogCode.Accepted and search_dialog.selected_url:
            self.play_youtube(search_dialog.selected_url)

    def play_youtube(self, yt_url, reset_playlist=True):
        format_code = None
        selected_hwdec = "no"

        clean_url_for_quality = yt_url
        
        if "list=" in yt_url or "playlist?" in yt_url:
            match = re.search(r'v=([^&]+)', yt_url)
            if match:
                clean_url_for_quality = f"https://www.youtube.com/watch?v={match.group(1)}"
            else:
                print("[*] 🔍 Pure playlist detected. Fetching the FIRST video for quality selection...")
                try:
                    cmd = [
                        "yt-dlp", 
                        "--flat-playlist", 
                        "--playlist-items", "1", 
                        "--dump-json", 
                        yt_url
                    ]
                    res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                    data = json.loads(res.stdout.strip().split('\n')[0])
                    if data.get('id'):
                        clean_url_for_quality = f"https://www.youtube.com/watch?v={data['id']}"
                except Exception as e:
                    print(f"[*] ⚠️ Failed to fetch first video: {e}")
                    pass

        if self.cli_quality and self.cli_quality in self.quality_map:
            format_code = self.quality_map[self.cli_quality]
        else:
            simple_dialog = YouTubeSimpleQualityDialog(clean_url_for_quality, self)
            if simple_dialog.exec() == QDialog.DialogCode.Accepted:
                if simple_dialog.format_code == "ADVANCED":
                    quality_dialog = YouTubeQualityDialog(clean_url_for_quality, self)
                    if quality_dialog.exec() == QDialog.DialogCode.Accepted:
                        format_code = quality_dialog.format_code
                    else:
                        return
                else:
                    format_code = simple_dialog.format_code
            else:
                return

        if format_code and "/" not in format_code and "[" not in format_code:
            format_code = f"{format_code}/best"
                
        saved_hwdec = self.menu_bar.get_saved_hwdec()
        if not self.cli_device and saved_hwdec:
            self.cli_device = "cached_hw"
            DEVICE_MAP["cached_hw"] = saved_hwdec

        if self.cli_device and self.cli_device in DEVICE_MAP:
            selected_hwdec = DEVICE_MAP[self.cli_device]
        else:
            decoding_dialog = DecodingDialog(self)
            if decoding_dialog.exec() == QDialog.DialogCode.Accepted:
                selected_hwdec = decoding_dialog.selected_hwdec
            else:
                return
                
        print(f"\n{'-'*60}\n[*] 🌐 YouTube URL: {yt_url}\n[*] 🍿 Format Selected: {format_code}\n[*] 🖥️  Hardware Decoding: {selected_hwdec}")
        
        self.player['hwdec'] = selected_hwdec
        self.player['ytdl'] = True
        self.player['ytdl-format'] = format_code
        self.player['vid'] = 'no' if self.cli_quality == 'audio' else 'auto'

        self.player['ytdl-raw-options'] = {
            "write-sub": "",
            "write-auto-sub": "",
            "sub-langs": "ar,en,en-US,en-GB"
        }
        self.player['slang'] = 'ar,en' 
        
        try:
            self.player['sub-visibility'] = False 
        except Exception:
            pass
            
        # إعادة ضبط الحالة عند تشغيل فيديو جديد
        self._subtitles_enabled = False
        self.controls.set_subtitle_status(False)
        # ==========================================
        
        if reset_playlist:
            if "list=" in yt_url or "playlist?" in yt_url:
                print("[*] 📜 YouTube Playlist detected. Fetching items in background...")
                self.playlist = [yt_url]
                self.current_index = 0
                self.playlist_panel.set_playlist_data(self.playlist)
                
                self.yt_playlist_fetcher = YouTubePlaylistFetcher(yt_url)
                self.yt_playlist_fetcher.playlist_fetched.connect(self._on_yt_playlist_fetched)
                self.yt_playlist_fetcher.start()
            else:
                self.playlist = [yt_url]
                self.current_index = 0
                self.playlist_panel.set_playlist_data(self.playlist)
        
        self.stack.setCurrentWidget(self.video_surface)
        
        print(f"[*] ▶️  Passing to MPV Engine...\n{'-'*60}\n")
        self.player.play(yt_url)

    def _on_yt_playlist_fetched(self, urls, original_url):
        if not urls: return
        print(f"[*] ✅ Fetched {len(urls)} videos from playlist.")
        self.playlist = urls
        
        match = re.search(r'v=([^&]+)', original_url)
        if match:
            vid_id = match.group(1)
            for i, u in enumerate(self.playlist):
                if vid_id in u:
                    self.current_index = i
                    break
        else:
            self.current_index = 0
            
        self.playlist_panel.set_playlist_data(self.playlist)

    def show_startup_dialog(self):
        StartupDialog(self).exec()

    def show_info_dialog(self):
        InfoDialog(self).exec()

    # ==========================================
    # --- Keyboard Controls ---
    # ==========================================
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_P and getattr(self.player, 'core_idle', True): 
            self.show_startup_dialog()
        elif event.key() == Qt.Key.Key_I:
            self.show_info_dialog()
        elif event.key() == Qt.Key.Key_Left:
            self._keyboard_seeking = True
            self.player.seek(-5) 
            QTimer.singleShot(800, self._reset_seek_flag)
        elif event.key() == Qt.Key.Key_Right:
            self._keyboard_seeking = True
            self.player.seek(5)
            QTimer.singleShot(800, self._reset_seek_flag)
        elif event.key() in (Qt.Key.Key_MediaNext, Qt.Key.Key_F9):
            self.play_next()
        elif event.key() in (Qt.Key.Key_MediaPrevious, Qt.Key.Key_F7):
            self.play_previous()
        elif event.key() in (Qt.Key.Key_MediaPlay, Qt.Key.Key_MediaTogglePlayPause, Qt.Key.Key_F8):
            self.toggle_playback()
        elif event.key() == Qt.Key.Key_MediaStop:
            self.stop_playback()
        # --- إضافة اختصار كيبورد (حرف C) لتشغيل/إيقاف الترجمة سريعاً ---
        elif event.key() == Qt.Key.Key_C:
            self.toggle_subtitles()
        super().keyPressEvent(event)

    def _reset_seek_flag(self):
        self._keyboard_seeking = False