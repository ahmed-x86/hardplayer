# main_window.py

import os
import glob
import threading
import mpv

from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QLabel, QFileDialog, QDialog
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

# Import configurations and features from our other modules
from config import BASE
from mpris_feature import HardPlayerMPRIS
from hw_decoding import DecodingDialog
from youtube_feature import YouTubeQualityDialog
from ui_components import AspectRatioContainer, InfoDialog, StartupDialog

try:
    from gi.repository import GLib
except ImportError:
    pass


class HardPlayerWindow(QMainWindow):
    """
    The main application window that hosts the MPV player and manages media playback.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HardPlayer")
        self.resize(800, 600)
        
        # QStackedWidget allows switching between the logo and the video player
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # --- Logo Screen Setup ---
        self.logo_widget = QWidget()
        logo_layout = QVBoxLayout(self.logo_widget)
        self.logo_label = QLabel("🎬\nHardPlayer")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setFont(QFont("Arial", 48, QFont.Weight.Bold))
        logo_layout.addWidget(self.logo_label)
        
        # --- Video Screen Setup ---
        self.video_widget = QWidget()
        self.video_widget.setAttribute(Qt.WidgetAttribute.WA_DontCreateNativeAncestors)
        self.video_widget.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        
        # Wrap the video widget in our custom aspect ratio container
        self.video_container = AspectRatioContainer(self.video_widget, BASE)
        
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

        # Start the D-Bus/MPRIS service for system media integration
        self.start_mpris_service()
        
        # Show the startup dialog shortly after the main window appears
        QTimer.singleShot(100, self.show_startup_dialog)

    def start_mpris_service(self):
        """Initializes the MPRIS service in a separate background thread."""
        def loop_runner():
            self.mpris_provider = HardPlayerMPRIS(self)
            GLib.MainLoop().run()
            
        threading.Thread(target=loop_runner, daemon=True).start()

    def play_next(self):
        """Plays the next media file in the playlist directory."""
        if self.playlist and self.current_index < len(self.playlist) - 1:
            self.current_index += 1
            self.player.play(self.playlist[self.current_index])

    def play_previous(self):
        """Plays the previous media file in the playlist directory."""
        if self.playlist and self.current_index > 0:
            self.current_index -= 1
            self.player.play(self.playlist[self.current_index])

    def scan_folder(self, current_file):
        """Scans the directory of the selected file to build a local playlist."""
        try:
            folder = os.path.dirname(os.path.abspath(current_file))
            files = []
            for ext in ('*.mp4', '*.mkv', '*.webm', '*.avi'):
                files.extend(glob.glob(os.path.join(folder, ext)))
            self.playlist = sorted(files)
            self.current_index = self.playlist.index(os.path.abspath(current_file))
        except Exception:
            self.playlist = [current_file]
            self.current_index = 0

    def keyPressEvent(self, event):
        """Handles global keyboard shortcuts for the application."""
        if event.key() == Qt.Key.Key_P:
            # Press 'P' to open the media selection dialog (if idle)
            if getattr(self.player, 'core_idle', True): 
                self.show_startup_dialog()
        elif event.key() == Qt.Key.Key_I:
            # Press 'I' to show FFmpeg system information
            self.show_info_dialog()
            
        super().keyPressEvent(event)

    def show_startup_dialog(self):
        """Displays the startup dialog for selecting media."""
        StartupDialog(self).exec()

    def show_info_dialog(self):
        """Displays the FFmpeg information dialog."""
        InfoDialog(self).exec()

    def ask_for_decoding_and_play(self, source):
        """Prompts the user for hardware decoding preferences and starts playback."""
        print(f"\n{'-'*60}\n[*] 📂 Video Selected: {source}")
        
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
                    print(f"\n\033[93m[⚠️ WARNING] Falling back to CPU. The GPU doesn't support hardware decoding for '{str(v_codec).upper()}'.\033[0m\n")
                elif current_hwdec != "no":
                    print(f"\n\033[92m[✅ SUCCESS] Hardware decoding is active! Playing via GPU using '{current_hwdec}'.\033[0m\n")

            # Wait 1.5 seconds for MPV to initialize playback before checking HWDEC status
            QTimer.singleShot(1500, check_hwdec_status)

    def browse_video(self):
        """Opens a file dialog for the user to select a local video file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "", "Video Files (*.mp4 *.mkv *.webm *.avi);;All Files (*)"
        )
        if file_path: 
            self.ask_for_decoding_and_play(file_path)

    def play_youtube(self, yt_url):
        """Handles fetching YouTube formats, asking for HWDEC, and initiating playback."""
        quality_dialog = YouTubeQualityDialog(yt_url, self)
        if quality_dialog.exec() == QDialog.DialogCode.Accepted:
            format_code = quality_dialog.format_code
            
            decoding_dialog = DecodingDialog(self)
            if decoding_dialog.exec() == QDialog.DialogCode.Accepted:
                selected_hwdec = decoding_dialog.selected_hwdec
                
                print(f"\n{'-'*60}\n[*] 🌐 YouTube URL: {yt_url}\n[*] 🍿 Format Selected: {format_code}\n[*] 🖥️  Hardware Decoding: {selected_hwdec}")
                
                self.player['hwdec'] = selected_hwdec
                self.player['ytdl'] = True
                self.player['ytdl-format'] = format_code
                
                self.playlist = [yt_url]
                self.current_index = 0
                self.stack.setCurrentWidget(self.video_container)
                
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