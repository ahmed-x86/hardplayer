# top_menu.py

import os
from pathlib import Path
from PyQt6.QtWidgets import QMenuBar, QMenu, QPushButton, QFileDialog
from PyQt6.QtGui import QActionGroup, QAction
from PyQt6.QtCore import Qt, pyqtSignal

# Import the hardware map from your hardware decoding file
from hw_decoding import DEVICE_MAP
# Import the URL entry dialog from components
from ui_components import YouTubeURLDialog

# --- Import the new convert menu manager ---
from top_menu_convert import ConvertMenuManager

class TopMenuBar(QMenuBar):
    """
    Custom top menu bar class, handles Hardware Decoding settings,
    playlist control button, and the convert menu.
    """
    # Signals for communicating with the main window
    hw_changed = pyqtSignal(str) # Emits the new type upon alteration
    playlist_toggled = pyqtSignal() # Emits a signal when clicking the playlist button

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent # Save reference to the main window
        self.init_style()
        self.setup_menus()
        self.setup_playlist_button()

    def init_style(self):
        """Apply Catppuccin Mocha theme to the menu"""
        self.setStyleSheet("""
            QMenuBar { 
                background-color: #11111b; 
                color: #cdd6f4; 
                font-size: 13px; 
            }
            QMenuBar::item:selected { 
                background-color: #313244; 
                border-radius: 4px; 
            }
            QMenu { 
                background-color: #1e1e2e; 
                color: #cdd6f4; 
                border: 1px solid #313244; 
                font-size: 13px; 
            }
            QMenu::item:selected { 
                background-color: #313244; 
            }
            QMenu::item:checked { 
                color: #a6e3a1; 
                font-weight: bold; 
            }
            QMenu::indicator { 
                width: 13px; 
                height: 13px; 
            }
        """)

    def setup_menus(self):
        # --- Hardware Menu ---
        hw_menu = self.addMenu("Hardware ⚙️")

        # Create a sub-menu to organize options
        default_hw_menu = hw_menu.addMenu("Default Backend 🖥️")

        # Exclusive action group (Radio Button behavior)
        self.hw_action_group = QActionGroup(self)
        self.hw_action_group.setExclusive(True)

        saved_hwdec = self.get_saved_hwdec()

        for cli_name, hw_arg in DEVICE_MAP.items():
            action = default_hw_menu.addAction(f"{cli_name} ({hw_arg})")
            action.setCheckable(True)
            self.hw_action_group.addAction(action)
            
            if saved_hwdec == hw_arg:
                action.setChecked(True)

            # Bind the action to the functional method
            action.triggered.connect(lambda checked, h=hw_arg: self.save_default_hwdec(h))
            
        default_hw_menu.addSeparator()
        reset_action = default_hw_menu.addAction("Reset Default 🔄")
        reset_action.triggered.connect(self.reset_default_hwdec)

        # --- YouTube Menu ---
        youtube_menu = self.addMenu("YouTube 📺")
        download_action = youtube_menu.addAction("Download YouTube Video 📥")
        download_action.triggered.connect(self.show_youtube_dialog)

        youtube_menu.addSeparator()

        # Sub-menu to specify the download folder
        loc_menu = youtube_menu.addMenu("Download Location 📁")
        set_loc_action = loc_menu.addAction("Set Download Folder 📂")
        set_loc_action.triggered.connect(self.select_download_directory)
        reset_loc_action = loc_menu.addAction("Reset to Default 🔄")
        reset_loc_action.triggered.connect(self.reset_download_path)

        youtube_menu.addSeparator()

        # Create a sub-menu for extensions
        ext_menu = youtube_menu.addMenu("Default Extension 🗂️")

        # Action group for extensions inside the sub-menu
        self.ext_action_group = QActionGroup(self)
        self.ext_action_group.setExclusive(True)

        saved_ext = self.get_saved_yt_ext()
        extensions = ["mp4", "mkv", "webm"]

        for ext in extensions:
            action = ext_menu.addAction(f".{ext}")
            action.setCheckable(True)
            self.ext_action_group.addAction(action)
            
            if saved_ext == ext:
                action.setChecked(True)

            action.triggered.connect(lambda checked, e=ext: self.save_yt_ext(e))

        ext_menu.addSeparator()
        reset_ext_action = ext_menu.addAction("Reset Extension 🔄")
        reset_ext_action.triggered.connect(self.reset_yt_ext)

        # --- Convert Menu ---
        # We pass the main window (main_window) to the convert manager so it can build its menu inside it
        self.convert_manager = ConvertMenuManager(self.main_window)

    def setup_playlist_button(self):
        """Add the Playlist button at the far right"""
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
        self.playlist_btn.clicked.connect(self.playlist_toggled.emit)
        
        # Place the button in the top right corner of the MenuBar
        self.setCornerWidget(self.playlist_btn, Qt.Corner.TopRightCorner)

    def show_youtube_dialog(self):
        """Open the YouTube URL entry dialog"""
        self.yt_dialog = YouTubeURLDialog(self.main_window)
        self.yt_dialog.show()

    # --- Extracted Cache Logic ---
    
    def save_default_hwdec(self, hw_arg):
        cache_dir = Path.home() / ".cache" / "hardplayer"
        cache_dir.mkdir(parents=True, exist_ok=True)
        hw_file = cache_dir / "hw.txt"
        hw_file.write_text(hw_arg, encoding="utf-8")
        print(f"\n[*] 💾 Saved Default HWDEC: '{hw_arg}'")
        self.hw_changed.emit(hw_arg)

    def reset_default_hwdec(self):
        hw_file = Path.home() / ".cache" / "hardplayer" / "hw.txt"
        if hw_file.exists():
            hw_file.unlink() 
            print("\n[*] 🗑️ Reset Default HWDEC.")
        
        checked_action = self.hw_action_group.checkedAction()
        if checked_action:
            self.hw_action_group.setExclusive(False)
            checked_action.setChecked(False)
            self.hw_action_group.setExclusive(True)
        
        self.hw_changed.emit("no") # Return to default state

    # --- Cache Logic for Default YouTube Extension ---

    def save_yt_ext(self, ext):
        cache_dir = Path.home() / ".cache" / "hardplayer"
        cache_dir.mkdir(parents=True, exist_ok=True)
        ext_file = cache_dir / "youtube_video_ext.txt"
        ext_file.write_text(ext, encoding="utf-8")
        print(f"\n[*] 💾 Saved Default YouTube Extension: '{ext}'")

    def reset_yt_ext(self):
        ext_file = Path.home() / ".cache" / "hardplayer" / "youtube_video_ext.txt"
        if ext_file.exists():
            ext_file.unlink()
            print("\n[*] 🗑️ Reset Default YouTube Extension.")
        
        checked_action = self.ext_action_group.checkedAction()
        if checked_action:
            self.ext_action_group.setExclusive(False)
            checked_action.setChecked(False)
            self.ext_action_group.setExclusive(True)

    def get_saved_yt_ext(self):
        ext_file = Path.home() / ".cache" / "hardplayer" / "youtube_video_ext.txt"
        if ext_file.exists():
            return ext_file.read_text(encoding="utf-8").strip()
        return None

    def get_saved_hwdec(self):
        hw_file = Path.home() / ".cache" / "hardplayer" / "hw.txt"
        if hw_file.exists():
            return hw_file.read_text(encoding="utf-8").strip()
        return None

    # --- Cache Logic for Download Path ---

    def select_download_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if directory:
            self.save_download_path(directory)

    def save_download_path(self, path):
        cache_dir = Path.home() / ".cache" / "hardplayer"
        cache_dir.mkdir(parents=True, exist_ok=True)
        path_file = cache_dir / "download_path.txt"
        path_file.write_text(path, encoding="utf-8")
        print(f"\n[*] 💾 Saved Download Path: '{path}'")

    def reset_download_path(self):
        path_file = Path.home() / ".cache" / "hardplayer" / "download_path.txt"
        if path_file.exists():
            path_file.unlink()
            print("\n[*] 🗑️ Reset Download Path to Default.")

    def get_saved_download_path(self):
        path_file = Path.home() / ".cache" / "hardplayer" / "download_path.txt"
        if path_file.exists():
            return path_file.read_text(encoding="utf-8").strip()
        return None