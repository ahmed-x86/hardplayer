# main_window.py

import os
import glob
import threading
import mpv

# --- New addition for handling cache files ---
from pathlib import Path
# ----------------------------------------------

# Import local thumbnail generator for v14
from thumbnail_gen import get_local_thumbnail

from PyQt6.QtWidgets import (QMainWindow, QStackedWidget, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QFileDialog, QDialog, 
                             QScrollArea, QFrame, QSizePolicy, QPushButton)
from PyQt6.QtCore import Qt, QTimer, QSize
# QActionGroup added to manage checkmarks in the dropdown menu
from PyQt6.QtGui import QFont, QPixmap, QActionGroup, QIcon

# Import configurations and features from our other modules
from config import BASE
from mpris_feature import HardPlayerMPRIS
from hw_decoding import DecodingDialog
from hw_decoding import DEVICE_MAP # Added here to fetch device map for CLI
from youtube_feature import YouTubeQualityDialog, YouTubeSearchDialog
# PlayerControlBar imported here
from ui_components import AspectRatioContainer, InfoDialog, StartupDialog, PlayerControlBar

try:
    from gi.repository import GLib
except ImportError:
    pass


class HardPlayerWindow(QMainWindow):
    """
    The main application window that hosts the MPV player and manages media playback.
    """
    # Modified: Added variables passed from cli_parser
    def __init__(self, cli_path=None, cli_device=None, cli_search=False, cli_quality=None):
        super().__init__()
        self.setWindowTitle("HardPlayer")
        self.resize(1000, 600) # Increased width slightly to accommodate the Playlist

        # --- CLI / Terminal command preservation additions ---
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
        # ---------------------------------------------
        
        # --- New addition: Setup the top menu bar ---
        self.setup_menu_bar()
        # --------------------------------------------

        # --- v6 UI Layout Setup ---
        # Line disabled to allow the new hardware bar to appear
        # self.setMenuBar(None) 

        self.central_widget = QWidget()
        # Catppuccin Mocha Background
        self.central_widget.setStyleSheet("background-color: #1e1e2e;")
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- v14: Restructuring content container for Sidebar Playlist ---
        self.content_container = QWidget()
        # This layout is dedicated to the stack (Video) to take full space
        self.content_layout = QHBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        # QStackedWidget allows switching between the logo and the video player
        self.stack = QStackedWidget()
        self.content_layout.addWidget(self.stack)

        # Adding the new Sidebar for v14
        self.setup_playlist_sidebar()
        self.main_layout.addWidget(self.content_container)
        # ------------------------------------------------------------------

        # Adding the bottom control bar v6
        self.controls = PlayerControlBar(self)
        self.main_layout.addWidget(self.controls)
        
        # --- Logo Screen Setup ---
        self.logo_widget = QWidget()
        logo_layout = QVBoxLayout(self.logo_widget)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter) # Center content vertically

        # Adding app icon from icon_in_app.png
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # --- Addition: Ensure image is read from the installation directory ---
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_dir, "icon_in_app.png")
        pixmap = QPixmap(icon_path)
        # ----------------------------------------------------------------------

        if not pixmap.isNull():
            # Resize icon to 150x150 maintaining aspect ratio and smoothness
            self.icon_label.setPixmap(pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_layout.addWidget(self.icon_label)

        # App title under the image
        self.logo_label = QLabel("HardPlayer")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setFont(QFont("Arial", 48, QFont.Weight.Bold))
        # Catppuccin Text Color
        self.logo_label.setStyleSheet("color: #cdd6f4;")
        logo_layout.addWidget(self.logo_label)
        
        # --- Video Screen Setup ---
        self.video_widget = QWidget()
        self.video_widget.setAttribute(Qt.WidgetAttribute.WA_DontCreateNativeAncestors)
        self.video_widget.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        
        # Wrap the video widget in our custom aspect ratio container
        # Using Catppuccin Crust for the letterboxing
        self.video_container = AspectRatioContainer(self.video_widget, "#11111b")
        
        self.stack.addWidget(self.logo_widget)
        self.stack.addWidget(self.video_container)
        
        # --- Playlist Management ---
        self.playlist = []
        self.current_index = -1

        # Custom logger to filter out unnecessary MPV noise
        def custom_mpv_logger(loglevel, component, message):
            msg = message.lower()
            if any(x in msg for x in ["late sei", "legacy vo", "streams.videolan.org"]): 
                return
            
            if loglevel in ['error', 'fatal']: 
                print(f"[{loglevel.upper()}] {component}: {message}")
            elif loglevel == 'info' and component in ['cplayer', 'vd']:
                if any(x in message for x in ['Video', 'Audio', 'Using hardware decoding']):
                    print(f"[INFO] {message}")

        # Initialize the MPV instance
        self.player = mpv.MPV(
            wid=str(int(self.video_widget.winId())),
            vo='gpu', 
            gpu_context='x11egl', 
            osc=False,
            input_default_bindings=False, 
            input_vo_keyboard=False, 
            keep_open=True,
            loglevel='info', 
            log_handler=custom_mpv_logger
        )

        # Initialize Loop Status
        self.loop_enabled = False
        self.player['loop-file'] = 'no'
        self.controls.set_repeat_status(False)

        # --- v6 Logic Connections ---
        self.controls.play_btn.clicked.connect(self.toggle_playback)
        self.controls.stop_btn.clicked.connect(self.stop_playback) # Back to main screen
        self.controls.next_btn.clicked.connect(self.play_next)
        self.controls.prev_btn.clicked.connect(self.play_previous)
        self.controls.repeat_btn.clicked.connect(self.toggle_loop)
        self.controls.slider.sliderMoved.connect(self.seek_video)

        # Keyboard seeking lock to prevent timer interference
        self._keyboard_seeking = False

        # UI Update Timer (Slider and Time labels)
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self.update_ui_state)
        self.ui_timer.start(500)

        # Start the D-Bus/MPRIS service for system media integration
        self.start_mpris_service()
        
        # --- CLI Launch handling ---
        if not self.cli_path:
            # Show the startup dialog shortly after the main window appears
            QTimer.singleShot(100, self.show_startup_dialog)
        else:
            QTimer.singleShot(100, self.process_cli_launch)

    # =====================================================================
    # --- Menu Bar and Cache Logic Functions (HW Cache Logic) ---
    # =====================================================================
    def setup_menu_bar(self):
        # Enable top menu bar
        menu_bar = self.menuBar()
        menu_bar.setStyleSheet("""
            QMenuBar { background-color: #11111b; color: #cdd6f4; font-size: 13px; }
            QMenuBar::item:selected { background-color: #313244; border-radius: 4px; }
            QMenu { background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #313244; font-size: 13px; }
            QMenu::item:selected { background-color: #313244; }
            /* Styling for checked items/green color for selected option */
            QMenu::item:checked { color: #a6e3a1; font-weight: bold; }
            QMenu::indicator { width: 13px; height: 13px; }
        """)

        hw_menu = menu_bar.addMenu("Hardware (Default) ⚙️")

        # Exclusive ActionGroup for Radio Button behavior
        self.hw_action_group = QActionGroup(self)
        self.hw_action_group.setExclusive(True)

        saved_hwdec = self.get_saved_hwdec()

        for cli_name, hw_arg in DEVICE_MAP.items():
            action = hw_menu.addAction(f"Save: {cli_name} ({hw_arg})")
            action.setCheckable(True)
            self.hw_action_group.addAction(action)
            
            if saved_hwdec == hw_arg:
                action.setChecked(True)

            action.triggered.connect(lambda checked, h=hw_arg: self.save_default_hwdec(h))
            
        hw_menu.addSeparator()
        reset_action = hw_menu.addAction("Reset HW Default 🔄")
        reset_action.triggered.connect(self.reset_default_hwdec)

        # --- v14: Playlist button on the far right as an icon only ---
        self.playlist_btn = QPushButton("📜")
        self.playlist_btn.setFixedWidth(50)
        self.playlist_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.playlist_btn.setStyleSheet("""
            QPushButton { 
                background: transparent; 
                color: #cdd6f4; 
                font-size: 20px; 
                border: none;
                margin-right: 5px;
            }
            QPushButton:hover { color: #89b4fa; }
        """)
        self.playlist_btn.clicked.connect(self.toggle_playlist_sidebar)
        
        # Place button at the top-right corner of the MenuBar
        menu_bar.setCornerWidget(self.playlist_btn, Qt.Corner.TopRightCorner)

    def save_default_hwdec(self, hw_arg):
        cache_dir = Path.home() / ".cache" / "hardplayer"
        cache_dir.mkdir(parents=True, exist_ok=True)
        hw_file = cache_dir / "hw.txt"
        hw_file.write_text(hw_arg, encoding="utf-8")
        print(f"\n[*] 💾 Saved Default HWDEC: '{hw_arg}' to {hw_file}")

    def reset_default_hwdec(self):
        hw_file = Path.home() / ".cache" / "hardplayer" / "hw.txt"
        if hw_file.exists():
            hw_file.unlink() 
            print("\n[*] 🗑️ Reset Default HWDEC. Dialog will show again on next playback.")
        else:
            print("\n[*] ℹ️ No saved HWDEC found.")
            
        checked_action = self.hw_action_group.checkedAction()
        if checked_action:
            self.hw_action_group.setExclusive(False)
            checked_action.setChecked(False)
            self.hw_action_group.setExclusive(True)

    def get_saved_hwdec(self):
        hw_file = Path.home() / ".cache" / "hardplayer" / "hw.txt"
        if hw_file.exists():
            return hw_file.read_text(encoding="utf-8").strip()
        return None

    # --- v14: Playlist Sidebar Logic ---
    def setup_playlist_sidebar(self):
        # Playlist sidebar as an overlay child of content_container
        self.playlist_sidebar = QFrame(self.content_container)
        
        # MAGIC FIX: Force the overlay to be a Native Window so it draws over the MPV Native Window
        self.playlist_sidebar.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        
        self.playlist_sidebar.setFixedWidth(300)
        
        # Transparent overlay style
        self.playlist_sidebar.setStyleSheet("""
            QFrame { 
                background-color: rgba(24, 24, 37, 230); 
                border-left: 2px solid #313244; 
            }
        """)
        self.playlist_sidebar.setVisible(False)
        
        sidebar_layout = QVBoxLayout(self.playlist_sidebar)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Media in Folder")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #cdd6f4; background: transparent; margin-bottom: 10px;")
        sidebar_layout.addWidget(title)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background: transparent;")
        
        self.playlist_content = QWidget()
        self.playlist_content.setStyleSheet("background: transparent;")
        self.playlist_items_layout = QVBoxLayout(self.playlist_content)
        self.playlist_items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.playlist_items_layout.setSpacing(12)
        
        self.scroll_area.setWidget(self.playlist_content)
        sidebar_layout.addWidget(self.scroll_area)
        
        # Notice: It is intentionally NOT added to the layout so it remains an absolute overlay

    def resizeEvent(self, event):
        """Update sidebar position and size on window resize for overlay effect"""
        super().resizeEvent(event)
        if hasattr(self, 'playlist_sidebar'):
            # Dock sidebar to far right and take full content container height
            w = 300
            h = self.content_container.height()
            x = self.content_container.width() - w
            self.playlist_sidebar.setGeometry(x, 0, w, h)

    def toggle_playlist_sidebar(self):
        is_visible = self.playlist_sidebar.isVisible()
        self.playlist_sidebar.setVisible(not is_visible)
        if not is_visible:
            # Raise sidebar to ensure visibility over video layer
            self.playlist_sidebar.raise_()
            self.populate_playlist_ui()

    def populate_playlist_ui(self):
        # Clear playlist content to prevent duplicates
        while self.playlist_items_layout.count():
            item = self.playlist_items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # --- NEW ADDITION: Initialize Lazy Loading Variables ---
        self.loaded_items_count = 0
        self.load_more_btn = None
        self.load_more_items()

    def load_more_items(self):
        """Loads items in batches of 6 to prevent UI freezing (Lazy Loading)"""
        # Remove the 'Load More' button temporarily if it exists
        if hasattr(self, 'load_more_btn') and self.load_more_btn:
            self.playlist_items_layout.removeWidget(self.load_more_btn)
            self.load_more_btn.deleteLater()
            self.load_more_btn = None

        start_index = getattr(self, 'loaded_items_count', 0)
        end_index = min(start_index + 6, len(self.playlist))
        batch = self.playlist[start_index:end_index]
            
        # for path in self.playlist:  # <-- ORIGINAL LINE DISABLED TO PREVENT FREEZE
        for path in batch:            # <-- NEW LINE ADDED TO LOAD ONLY 6 VIDEOS AT A TIME
            item_widget = QFrame()
            item_widget.setCursor(Qt.CursorShape.PointingHandCursor)
            item_widget.setStyleSheet("""
                QFrame { background-color: #313244; border-radius: 8px; }
                QFrame:hover { background-color: #45475a; }
            """)
            
            h_layout = QHBoxLayout(item_widget)
            h_layout.setContentsMargins(5, 5, 5, 5)
            
            # Thumbnail display
            thumb_label = QLabel()
            thumb_label.setFixedSize(80, 45)
            thumb_path = get_local_thumbnail(path) if not path.startswith("http") else None
            
            if thumb_path and os.path.exists(thumb_path):
                pix = QPixmap(thumb_path).scaled(80, 45, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                thumb_label.setPixmap(pix)
            else:
                thumb_label.setText("🎬")
                thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                thumb_label.setStyleSheet("background-color: #11111b; color: #fab387; border-radius: 4px;")

            # Filename formatting (Max 4 words per line)
            name = os.path.basename(path)
            words = name.split()
            line1 = " ".join(words[:4])
            line2 = ""
            if len(words) > 4:
                rem = words[4:]
                if len(rem) > 2:
                    line2 = " ".join(rem[:2]) + "..."
                else:
                    line2 = " ".join(rem)
            
            formatted_name = f"{line1}\n{line2}" if line2 else line1
            
            name_label = QLabel(formatted_name)
            name_label.setStyleSheet("color: #cdd6f4; font-size: 11px; background: transparent;")
            name_label.setWordWrap(True)
            
            h_layout.addWidget(thumb_label)
            h_layout.addWidget(name_label, 1)
            
            # Connect click event to play file
            item_widget.mousePressEvent = lambda e, p=path: self.play_from_sidebar(p)
            
            self.playlist_items_layout.addWidget(item_widget)

        # --- NEW ADDITION: Update index and add the Load More button ---
        self.loaded_items_count = end_index
        
        if self.loaded_items_count < len(self.playlist):
            self.load_more_btn = QPushButton("Load More ⏬")
            self.load_more_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.load_more_btn.setStyleSheet("""
                QPushButton { background-color: #313244; color: #cdd6f4; border-radius: 8px; padding: 8px; font-weight: bold; }
                QPushButton:hover { background-color: #45475a; color: #89b4fa; }
            """)
            self.load_more_btn.clicked.connect(self.load_more_items)
            self.playlist_items_layout.addWidget(self.load_more_btn)

    def play_from_sidebar(self, path):
        print(f"[*] 🔄 Switching to: {path}")
        self.player.stop()
        if path.startswith("http"):
            self.play_youtube(path)
        else:
            self.ask_for_decoding_and_play(path)
    # =====================================================================

    # --- CLI handling logic ---
    def process_cli_launch(self):
        if self.cli_search:
            self.search_youtube_and_play(self.cli_path)
            return

        is_url = self.cli_path.startswith("http://") or self.cli_path.startswith("https://")

        if self.cli_device or self.cli_quality:
            if is_url:
                self.play_youtube(self.cli_path)
            else:
                self.fast_launch_local()
        else:
            if is_url:
                self.play_youtube(self.cli_path)
            else:
                self.ask_for_decoding_and_play(self.cli_path)

    def fast_launch_local(self):
        selected_hwdec = "no"
        if self.cli_device and self.cli_device in DEVICE_MAP:
            selected_hwdec = DEVICE_MAP[self.cli_device]
            print(f"\n{'-'*60}\n[*] 🚀 CLI Fast Launch Activated")
            print(f"[*] 🖥️  Hardware Decoding Forced: {self.cli_device} -> {selected_hwdec}")

        self.player['hwdec'] = selected_hwdec
        self.scan_folder(self.cli_path)
        self.stack.setCurrentWidget(self.video_container)
        self.player.play(self.cli_path)
    # --------------------------------------

    # --- v6 Control Methods ---
    def toggle_playback(self):
        """Toggles play/pause state."""
        self.player.pause = not self.player.pause

    def stop_playback(self):
        """Stop video and go back to main screen"""
        self.player.stop()  # Stop MPV engine
        self.stack.setCurrentWidget(self.logo_widget)  # Switch to logo screen
        print("[*] ⏹ Playback stopped, returning to main screen.")

    def toggle_loop(self):
        """Toggles file looping and updates UI button color."""
        self.loop_enabled = not self.loop_enabled
        if self.loop_enabled:
            self.player['loop-file'] = 'inf'
            self.controls.set_repeat_status(True)
            print("[*] 🔁 Loop Mode: ENABLED (Video will restart)")
        else:
            self.player['loop-file'] = 'no'
            self.controls.set_repeat_status(False)
            print("[*] 🔁 Loop Mode: DISABLED")

    def seek_video(self, position):
        """Seeks to a specific position in the video."""
        self.player.time_pos = position

    def update_ui_state(self):
        """Updates the progress slider and time label."""
        if self.player.time_pos is not None:
            self.controls.slider.setEnabled(True)
            duration = self.player.duration or 0
            current = self.player.time_pos
            
            # Update slider position
            if not self.controls.slider.isSliderDown() and not getattr(self, '_keyboard_seeking', False):
                self.controls.slider.setMaximum(int(duration))
                self.controls.slider.setValue(int(current))
            
            # Time format HH:MM:SS or MM:SS
            has_hours = duration >= 3600
            time_str = f"{self.format_time(current, has_hours)} / {self.format_time(duration, has_hours)}"
            self.controls.time_label.setText(time_str)
            
            # Update Play/Pause button styling
            if self.player.pause:
                self.controls.play_btn.setText("▶")
                self.controls.play_btn.setStyleSheet("color: #cdd6f4; background-color: #313244;")
            else:
                self.controls.play_btn.setText("⏸")
                self.controls.play_btn.setStyleSheet("color: #89b4fa; background-color: #313244;")
        else:
            self.controls.slider.setEnabled(False)
            self.controls.time_label.setText("--:-- / --:--")

    def format_time(self, seconds, force_hours=False):
        """Helper to format seconds into HH:MM:SS or MM:SS."""
        if seconds is None or seconds < 0: return "00:00"
        hours, remainder = divmod(int(seconds), 3600)
        mins, secs = divmod(remainder, 60)
        
        if hours > 0 or force_hours:
            return f"{hours:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"

    # --- Original Logic Preserved ---
    def start_mpris_service(self):
        """Initializes the MPRIS service in a separate background thread."""
        def loop_runner():
            self.mpris_provider = HardPlayerMPRIS(self)
            GLib.MainLoop().run()
            
        threading.Thread(target=loop_runner, daemon=True).start()

    def play_next(self):
        """Plays the next media file in the playlist directory."""
        if self.playlist:
            if self.current_index < len(self.playlist) - 1:
                self.current_index += 1
            else:
                self.current_index = 0 # Return to first video if at end
            self.player.play(self.playlist[self.current_index])

    def play_previous(self):
        """Plays the previous media file in the playlist directory."""
        if self.playlist:
            if self.current_index > 0:
                self.current_index -= 1
            else:
                self.current_index = len(self.playlist) - 1 # Go to last video if at start
            self.player.play(self.playlist[self.current_index])

    def scan_folder(self, current_file):
        """Scans directory of selected file to build a local playlist."""
        try:
            folder = os.path.dirname(os.path.abspath(current_file))
            files = []
            # Filter for video extensions
            for ext in ('*.mp4', '*.mkv', '*.webm', '*.avi', '*.ts', '*.m4v'):
                files.extend(glob.glob(os.path.join(folder, ext)))
            self.playlist = sorted(files)
            self.current_index = self.playlist.index(os.path.abspath(current_file))
        except Exception:
            self.playlist = [current_file]
            self.current_index = 0

    def keyPressEvent(self, event):
        """Handles global keyboard shortcuts."""
        if event.key() == Qt.Key.Key_P:
            # Press 'P' to open media selection dialog
            if getattr(self.player, 'core_idle', True): 
                self.show_startup_dialog()
        elif event.key() == Qt.Key.Key_I:
            # Press 'I' to show system/FFmpeg info
            self.show_info_dialog()
        # Arrow keys for seeking
        elif event.key() == Qt.Key.Key_Left:
            self._keyboard_seeking = True
            self.player.seek(-5) 
            QTimer.singleShot(800, self._reset_seek_flag)
        elif event.key() == Qt.Key.Key_Right:
            self._keyboard_seeking = True
            self.player.seek(5)
            QTimer.singleShot(800, self._reset_seek_flag)
            
        # Support for media keys and F7, F8, F9 alternatives
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
        """Releases the UI lock after keyboard seeking."""
        self._keyboard_seeking = False

    def show_startup_dialog(self):
        """Displays startup dialog for media selection."""
        StartupDialog(self).exec()

    def show_info_dialog(self):
        """Displays FFmpeg information dialog."""
        InfoDialog(self).exec()

    def ask_for_decoding_and_play(self, source):
        """Prompts for hardware decoding preferences and starts playback."""
        print(f"\n{'-'*60}\n[*] 📂 Video Selected: {source}")
        
        # --- Check cache before opening dialog (Early escape) ---
        saved_hwdec = self.get_saved_hwdec()
        if saved_hwdec:
            print(f"[*] ⚡ Fast Track: Using Saved HWDEC '{saved_hwdec}'")
            self.player['hwdec'] = saved_hwdec
            self.scan_folder(source)
            self.stack.setCurrentWidget(self.video_container)
            print(f"[*] ▶️  Passing to MPV Engine...\n{'-'*60}\n")
            self.player.play(source)
            QTimer.singleShot(1500, lambda: print(f"[*] 🎞️ Playing via Saved Cache: {saved_hwdec}"))
            return
        # ---------------------------------------------------------

        decoding_dialog = DecodingDialog(self)
        if decoding_dialog.exec() == QDialog.DialogCode.Accepted:
            selected_hwdec = decoding_dialog.selected_hwdec
            print(f"[*] 🖥️  Hardware Decoding Requested: {selected_hwdec}")
            
            self.player['hwdec'] = selected_hwdec
            self.scan_folder(source)
            self.stack.setCurrentWidget(self.video_container)
            
            print(f"[*] ▶️  Passing to MPV Engine...\n{'-'*60}\n")
            self.player.play(source)

            def check_hwdec_status():
                current_hwdec = getattr(self.player, 'hwdec_current', 'no')
                v_codec = getattr(self.player, 'video_format', 'Unknown')
                print(f"[*] 🎞️  Detected Video Codec: {str(v_codec).upper()}")
                
                if selected_hwdec != "no" and current_hwdec == "no":
                    print(f"\n\033[93m[⚠️ WARNING] Falling back to CPU. GPU doesn't support hardware decoding for '{str(v_codec).upper()}'.\033[0m\n")
                elif current_hwdec != "no":
                    print(f"\n\033[92m[✅ SUCCESS] Hardware decoding active! Playing via GPU using '{current_hwdec}'.\033[0m\n")

            QTimer.singleShot(1500, check_hwdec_status)

    def browse_video(self):
        """Opens file dialog for video selection."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "", "Video Files (*.mp4 *.mkv *.webm *.avi);;All Files (*)"
        )
        if file_path: 
            self.ask_for_decoding_and_play(file_path)

    def search_youtube_and_play(self, query):
        """Searches YouTube and plays selected video."""
        search_dialog = YouTubeSearchDialog(query, self)
        if search_dialog.exec() == QDialog.DialogCode.Accepted:
            selected_url = search_dialog.selected_url
            if selected_url:
                self.play_youtube(selected_url)

    def play_youtube(self, yt_url):
        """Handles YouTube formats, HWDEC prompt, and playback initiation."""
        
        format_code = None
        selected_hwdec = "no"

        # --- 1. Quality verification ---
        if self.cli_quality and self.cli_quality in self.quality_map:
            format_code = self.quality_map[self.cli_quality]
            print(f"[*] ⚡ Fast Track: YouTube Quality forced to '{self.cli_quality}'")
        else:
            quality_dialog = YouTubeQualityDialog(yt_url, self)
            if quality_dialog.exec() == QDialog.DialogCode.Accepted:
                format_code = quality_dialog.format_code
            else:
                return
                
        # --- Check cache and inject to skip dialog ---
        saved_hwdec = self.get_saved_hwdec()
        if not self.cli_device and saved_hwdec:
            self.cli_device = "cached_hw"
            DEVICE_MAP["cached_hw"] = saved_hwdec
        # ---------------------------------------------

        # --- 2. Hardware verification ---
        if self.cli_device and self.cli_device in DEVICE_MAP:
            selected_hwdec = DEVICE_MAP[self.cli_device]
            print(f"[*] ⚡ Fast Track: Hardware Decoding forced to '{self.cli_device}'")
        else:
            decoding_dialog = DecodingDialog(self)
            if decoding_dialog.exec() == QDialog.DialogCode.Accepted:
                selected_hwdec = decoding_dialog.selected_hwdec
            else:
                return
                
        # --- 3. Actual initiation ---
        print(f"\n{'-'*60}\n[*] 🌐 YouTube URL: {yt_url}\n[*] 🍿 Format Selected: {format_code}\n[*] 🖥️  Hardware Decoding: {selected_hwdec}")
        
        self.player['hwdec'] = selected_hwdec
        self.player['ytdl'] = True
        self.player['ytdl-format'] = format_code
        
        self.playlist = [yt_url]
        self.current_index = 0
        self.stack.setCurrentWidget(self.video_container)
        
        # Disable video if audio-only selected
        if self.cli_quality == 'audio':
            self.player['vid'] = 'no'
        else:
            self.player['vid'] = 'auto'

        print(f"[*] ▶️  Passing to MPV Engine...\n{'-'*60}\n")
        self.player.play(yt_url)

        def check_hwdec_status():
            current_hwdec = getattr(self.player, 'hwdec_current', 'no')
            v_codec = getattr(self.player, 'video_format', 'Unknown')
            print(f"[*] 🎞️  Detected Video Codec: {str(v_codec).upper()}")
            
            if selected_hwdec != "no" and current_hwdec == "no":
                print(f"\n\033[93m[⚠️ WARNING] Falling back to CPU.\033[0m\n")
            elif current_hwdec != "no":
                print(f"\n\033[92m[✅ SUCCESS] Playing via GPU using '{current_hwdec}'.\033[0m\n")

        QTimer.singleShot(1500, check_hwdec_status)