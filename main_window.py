# main_window.py

import os
import glob
import threading
import mpv

from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QLabel, QFileDialog, QDialog
from PyQt6.QtCore import Qt, QTimer
# تم إضافة QPixmap هنا لتحميل الصور
from PyQt6.QtGui import QFont, QPixmap

# Import configurations and features from our other modules
from config import BASE
from mpris_feature import HardPlayerMPRIS
from hw_decoding import DecodingDialog
from youtube_feature import YouTubeQualityDialog, YouTubeSearchDialog
# تم إضافة PlayerControlBar هنا
from ui_components import AspectRatioContainer, InfoDialog, StartupDialog, PlayerControlBar

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
        
        # --- v6 UI Layout Setup ---
        # إزالة شريط القوائم العلوي تماماً
        self.setMenuBar(None)

        self.central_widget = QWidget()
        # Catppuccin Mocha Background
        self.central_widget.setStyleSheet("background-color: #1e1e2e;")
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # QStackedWidget allows switching between the logo and the video player
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        # إضافة شريط التحكم السفلي v6
        self.controls = PlayerControlBar(self)
        self.main_layout.addWidget(self.controls)
        
        # --- Logo Screen Setup ---
        self.logo_widget = QWidget()
        logo_layout = QVBoxLayout(self.logo_widget)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter) # توسيط المحتوى عمودياً

        # إضافة أيقونة البرنامج من ملف icon_in_app.png
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap("icon_in_app.png")
        if not pixmap.isNull():
            # تغيير حجم الصورة لـ 150x150 مع الحفاظ على التناسب والجودة
            self.icon_label.setPixmap(pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_layout.addWidget(self.icon_label)

        # عنوان البرنامج تحت الصورة
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
        self.controls.stop_btn.clicked.connect(self.stop_playback) # تم التعديل للدالة الجديدة للرجوع للرئيسية
        self.controls.next_btn.clicked.connect(self.play_next)
        self.controls.prev_btn.clicked.connect(self.play_previous)
        self.controls.repeat_btn.clicked.connect(self.toggle_loop)
        self.controls.slider.sliderMoved.connect(self.seek_video)

        # المتغير ده هيشتغل كقفل لمنع التايمر من التدخل وقت استخدام الكيبورد
        self._keyboard_seeking = False

        # تايمر لتحديث الواجهة (شريط التقدم والوقت)
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self.update_ui_state)
        self.ui_timer.start(500)

        # Start the D-Bus/MPRIS service for system media integration
        self.start_mpris_service()
        
        # Show the startup dialog shortly after the main window appears
        QTimer.singleShot(100, self.show_startup_dialog)

    # --- v6 Control Methods ---
    def toggle_playback(self):
        """Toggles play/pause state."""
        self.player.pause = not self.player.pause

    def stop_playback(self):
        """stop video and go back to main screen"""
        self.player.stop()  # إيقاف محرك MPV
        self.stack.setCurrentWidget(self.logo_widget)  # التبديل إلى شاشة الشعار (اللون #1e1e2e)
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
            
            # تحديث السلايدر
            if not self.controls.slider.isSliderDown() and not getattr(self, '_keyboard_seeking', False):
                self.controls.slider.setMaximum(int(duration))
                self.controls.slider.setValue(int(current))
            
            # اكتشاف الساعات وإضافة مسافات جمالية
            has_hours = duration >= 3600
            time_str = f"{self.format_time(current, has_hours)} / {self.format_time(duration, has_hours)}"
            self.controls.time_label.setText(time_str)
            
            # تحديث أيقونة الزر ولونها بناءً على الثيم
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
                self.current_index = 0 # العودة لأول فيديو إذا وصلنا للنهاية
            self.player.play(self.playlist[self.current_index])

    def play_previous(self):
        """Plays the previous media file in the playlist directory."""
        if self.playlist:
            if self.current_index > 0:
                self.current_index -= 1
            else:
                self.current_index = len(self.playlist) - 1 # الانتقال لآخر فيديو إذا كنا في البداية
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
        # إضافة دعم مفاتيح الأسهم للتقديم والتأخير باستخدام seek النيتيف
        elif event.key() == Qt.Key.Key_Left:
            self._keyboard_seeking = True
            self.player.seek(-5) 
            QTimer.singleShot(800, self._reset_seek_flag) # فك القفل بعد 800 مللي ثانية
        elif event.key() == Qt.Key.Key_Right:
            self._keyboard_seeking = True
            self.player.seek(5)
            QTimer.singleShot(800, self._reset_seek_flag)
            
        # --- التعديل هنا: إضافة دعم أزرار الميديا الخاصة بالكيبورد مع F7 و F8 و F9 كبدائل ---
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

    
    def search_youtube_and_play(self, query):
        """Searches YouTube and plays the selected video."""
        search_dialog = YouTubeSearchDialog(query, self)
        if search_dialog.exec() == QDialog.DialogCode.Accepted:
            selected_url = search_dialog.selected_url
            if selected_url:
                self.play_youtube(selected_url)

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