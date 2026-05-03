# main_window.py

import os
import glob
import threading
import mpv

# --- الإضافة الجديدة للتعامل مع ملفات الكاش ---
from pathlib import Path
# ----------------------------------------------

from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QLabel, QFileDialog, QDialog
from PyQt6.QtCore import Qt, QTimer
# تم إضافة QActionGroup للتحكم بعلامات الصح في القائمة المنسدلة
from PyQt6.QtGui import QFont, QPixmap, QActionGroup

# Import configurations and features from our other modules
from config import BASE
from mpris_feature import HardPlayerMPRIS
from hw_decoding import DecodingDialog
from hw_decoding import DEVICE_MAP # تمت الإضافة هنا لجلب خريطة الأجهزة للـ CLI
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
    # تم التعديل هنا: إضافة المتغيرات القادمة من cli_parser
    def __init__(self, cli_path=None, cli_device=None, cli_search=False, cli_quality=None):
        super().__init__()
        self.setWindowTitle("HardPlayer")
        self.resize(800, 600)

        # --- الإضافات الخاصة بحفظ أوامر التيرمنال ---
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
        
        # --- الإضافة الجديدة: إنشاء الشريط العلوي ---
        self.setup_menu_bar()
        # --------------------------------------------

        # --- v6 UI Layout Setup ---
        # تم تعطيل هذا السطر لكي يظهر شريط العتاد الجديد
        # self.setMenuBar(None) 

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
        
        # --- الإضافة الجديدة لضمان قراءة الصورة من مجلد التثبيت دائماً وتخطي السطر السابق ---
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_dir, "icon_in_app.png")
        pixmap = QPixmap(icon_path)
        # ------------------------------------------------------------------------------------

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
        
        # --- تم التعديل هنا: إضافة شرط التيرمنال مع الحفاظ على السطر الأصلي ---
        if not self.cli_path:
            # Show the startup dialog shortly after the main window appears
            QTimer.singleShot(100, self.show_startup_dialog)
        else:
            QTimer.singleShot(100, self.process_cli_launch)

    # =====================================================================
    # --- دوال الشريط العلوي وملف الكاش الجديدة (HW Cache Logic) ---
    # =====================================================================
    def setup_menu_bar(self):
        # تفعيل الشريط العلوي مجدداً بعد حذفه في v6 Layout
        menu_bar = self.menuBar()
        menu_bar.setStyleSheet("""
            QMenuBar { background-color: #11111b; color: #cdd6f4; font-size: 13px; }
            QMenuBar::item:selected { background-color: #313244; border-radius: 4px; }
            QMenu { background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #313244; font-size: 13px; }
            QMenu::item:selected { background-color: #313244; }
            /* --- تمت إضافة التنسيق الجديد لتلوين علامة الصح والخيار المحدد بالأخضر --- */
            QMenu::item:checked { color: #a6e3a1; font-weight: bold; }
            QMenu::indicator { width: 13px; height: 13px; }
        """)

        hw_menu = menu_bar.addMenu("Hardware (Default) ⚙️")

        # إنشاء ActionGroup لضمان أنه يمكن اختيار عتاد واحد فقط في كل مرة (مثل Radio Buttons)
        self.hw_action_group = QActionGroup(self)
        self.hw_action_group.setExclusive(True)

        saved_hwdec = self.get_saved_hwdec()

        for cli_name, hw_arg in DEVICE_MAP.items():
            action = hw_menu.addAction(f"Save: {cli_name} ({hw_arg})")
            
            # تفعيل خاصية علامة الصح (Checkable) للخيار
            action.setCheckable(True)
            self.hw_action_group.addAction(action)
            
            # قراءة الكاش، وإذا كان الخيار متطابقاً، نضع علامة الصح عليه عند بدء البرنامج
            if saved_hwdec == hw_arg:
                action.setChecked(True)

            action.triggered.connect(lambda checked, h=hw_arg: self.save_default_hwdec(h))
            
        hw_menu.addSeparator()
        reset_action = hw_menu.addAction("Reset HW Default 🔄")
        reset_action.triggered.connect(self.reset_default_hwdec)

    def save_default_hwdec(self, hw_arg):
        cache_dir = Path.home() / ".cache" / "hardplayer"
        cache_dir.mkdir(parents=True, exist_ok=True)
        hw_file = cache_dir / "hw.txt"
        
        # write_text تقوم بإنشاء الملف إذا لم يكن موجوداً، أو تحذفه وتكتب فوقه (Overwrite) إذا كان موجوداً
        hw_file.write_text(hw_arg, encoding="utf-8")
        print(f"\n[*] 💾 Saved Default HWDEC: '{hw_arg}' to {hw_file}")

    def reset_default_hwdec(self):
        hw_file = Path.home() / ".cache" / "hardplayer" / "hw.txt"
        if hw_file.exists():
            hw_file.unlink() # يقوم بحذف الملف من الجهاز
            print("\n[*] 🗑️ Reset Default HWDEC. The Dialog will show again on next playback.")
        else:
            print("\n[*] ℹ️ No saved HWDEC found.")
            
        # إزالة علامة الصح المرئية من القائمة المنسدلة
        checked_action = self.hw_action_group.checkedAction()
        if checked_action:
            # يجب إيقاف الحصرية (Exclusive) مؤقتاً لنتمكن من إزالة الصح، ثم إعادتها
            self.hw_action_group.setExclusive(False)
            checked_action.setChecked(False)
            self.hw_action_group.setExclusive(True)

    def get_saved_hwdec(self):
        hw_file = Path.home() / ".cache" / "hardplayer" / "hw.txt"
        if hw_file.exists():
            return hw_file.read_text(encoding="utf-8").strip()
        return None
    # =====================================================================

    # --- الإضافات الجديدة الخاصة بـ CLI ---
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
        
        # --- الإضافة الجديدة: فحص الكاش قبل فتح الديالوج للهروب المبكر ---
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
        # -----------------------------------------------------------------

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
        
        format_code = None
        selected_hwdec = "no"

        # --- 1. التحقق المستقل من الجودة ---
        if self.cli_quality and self.cli_quality in self.quality_map:
            format_code = self.quality_map[self.cli_quality]
            print(f"[*] ⚡ Fast Track: YouTube Quality forced to '{self.cli_quality}'")
        else:
            quality_dialog = YouTubeQualityDialog(yt_url, self)
            if quality_dialog.exec() == QDialog.DialogCode.Accepted:
                format_code = quality_dialog.format_code
            else:
                return # المستخدم أغلق النافذة
                
        # --- الإضافة الجديدة: فحص الكاش وحقنه ليتخطى الديالوج بخدعة بسيطة ---
        saved_hwdec = self.get_saved_hwdec()
        if not self.cli_device and saved_hwdec:
            self.cli_device = "cached_hw"
            DEVICE_MAP["cached_hw"] = saved_hwdec
        # --------------------------------------------------------------------

        # --- 2. التحقق المستقل من العتاد ---
        if self.cli_device and self.cli_device in DEVICE_MAP:
            selected_hwdec = DEVICE_MAP[self.cli_device]
            print(f"[*] ⚡ Fast Track: Hardware Decoding forced to '{self.cli_device}'")
        else:
            decoding_dialog = DecodingDialog(self)
            if decoding_dialog.exec() == QDialog.DialogCode.Accepted:
                selected_hwdec = decoding_dialog.selected_hwdec
            else:
                return # المستخدم أغلق النافذة
                
        # --- 3. التشغيل الفعلي ---
        print(f"\n{'-'*60}\n[*] 🌐 YouTube URL: {yt_url}\n[*] 🍿 Format Selected: {format_code}\n[*] 🖥️  Hardware Decoding: {selected_hwdec}")
        
        self.player['hwdec'] = selected_hwdec
        self.player['ytdl'] = True
        self.player['ytdl-format'] = format_code
        
        self.playlist = [yt_url]
        self.current_index = 0
        self.stack.setCurrentWidget(self.video_container)
        
        # تعطيل الفيديو إذا كان الخيار صوت فقط
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