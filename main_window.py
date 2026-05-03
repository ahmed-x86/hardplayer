# main_window.py

import os
import glob
import threading
import mpv
from pathlib import Path

from PyQt6.QtWidgets import (QMainWindow, QStackedWidget, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QFileDialog, QDialog)
from PyQt6.QtCore import Qt, QTimer
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
# التعديل هنا: استيراد YouTubeSimpleQualityDialog
from youtube_feature import YouTubeSimpleQualityDialog, YouTubeQualityDialog, YouTubeSearchDialog
from ui_components import InfoDialog, StartupDialog

try:
    from gi.repository import GLib
except ImportError:
    pass


class HardPlayerWindow(QMainWindow):
    """
    The main application window. Acts as a controller connecting the UI to the MPV engine.
    """
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

        self.loop_enabled = False
        self.player['loop-file'] = 'no'

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
        self.controls.repeat_toggled.connect(self.toggle_loop)
        self.controls.seek_requested.connect(self.seek_video)

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
        if path.startswith("http"):
            self.play_youtube(path)
        else:
            self.ask_for_decoding_and_play(path)
    
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

    def toggle_loop(self):
        self.loop_enabled = not self.loop_enabled
        self.player['loop-file'] = 'inf' if self.loop_enabled else 'no'
        self.controls.set_repeat_status(self.loop_enabled)
        state = "ENABLED" if self.loop_enabled else "DISABLED"
        print(f"[*] 🔁 Loop Mode: {state}")

    def seek_video(self, position):
        self.player.time_pos = position

    def play_next(self):
        if self.playlist:
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
            
        # Send the new playlist data to the Sidebar
        self.playlist_panel.set_playlist_data(self.playlist)

    def start_mpris_service(self):
        def loop_runner():
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
        
        # Fetch cached HWDEC preference from the TopMenuBar
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

    def play_youtube(self, yt_url):
        format_code = None
        selected_hwdec = "no"

        # 1. Quality configuration (التعديل تم هنا لربط الشاشتين ببعض)
        if self.cli_quality and self.cli_quality in self.quality_map:
            format_code = self.quality_map[self.cli_quality]
        else:
            # إظهار الشاشة المبسطة أولاً
            simple_dialog = YouTubeSimpleQualityDialog(yt_url, self)
            if simple_dialog.exec() == QDialog.DialogCode.Accepted:
                if simple_dialog.format_code == "ADVANCED":
                    # إذا ضغط المستخدم على Advanced، تظهر الشاشة القديمة (المعقدة)
                    quality_dialog = YouTubeQualityDialog(yt_url, self)
                    if quality_dialog.exec() == QDialog.DialogCode.Accepted:
                        format_code = quality_dialog.format_code
                    else:
                        return # في حال ألغى المستخدم العملية
                else:
                    # في حال اختار الجودة من الشاشة المبسطة (مثلاً 1080p أو 720p)
                    format_code = simple_dialog.format_code
            else:
                return # في حال ألغى المستخدم العملية من الشاشة الأولى
                
        # 2. Hardware cache injection
        saved_hwdec = self.menu_bar.get_saved_hwdec()
        if not self.cli_device and saved_hwdec:
            self.cli_device = "cached_hw"
            DEVICE_MAP["cached_hw"] = saved_hwdec

        # 3. Hardware verification
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
        
        self.playlist = [yt_url]
        self.current_index = 0
        self.playlist_panel.set_playlist_data(self.playlist)
        self.stack.setCurrentWidget(self.video_surface)
        
        print(f"[*] ▶️  Passing to MPV Engine...\n{'-'*60}\n")
        self.player.play(yt_url)

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
        super().keyPressEvent(event)

    def _reset_seek_flag(self):
        self._keyboard_seeking = False