# top_menu.py

import os
from pathlib import Path
from PyQt6.QtWidgets import QMenuBar, QMenu, QPushButton
from PyQt6.QtGui import QActionGroup, QAction
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction

# استيراد خريطة الأجهزة من ملف الـ hardware decoding الخاص بك
from hw_decoding import DEVICE_MAP
# استيراد نافذة إدخال الرابط من المكونات
from ui_components import YouTubeURLDialog

class TopMenuBar(QMenuBar):
    """
    كلاس مخصص للقائمة العلوية، يدير إعدادات الـ Hardware Decoding
    وزر التحكم في قائمة التشغيل (Playlist).
    """
    # Signals للتواصل مع النافذة الرئيسية
    hw_changed = pyqtSignal(str) # ترسل النوع الجديد عند التغيير
    playlist_toggled = pyqtSignal() # ترسل إشارة عند الضغط على زر القائمة

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent # حفظ مرجع للنافذة الرئيسية
        self.init_style()
        self.setup_menus()
        self.setup_playlist_button()

    def init_style(self):
        """تطبيق ثيم Catppuccin Mocha على القائمة"""
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
        # قائمة Hardware Decoding
        hw_menu = self.addMenu("Hardware (Default) ⚙️")

        # مجموعة أكشن حصرية (Radio Button behavior)
        self.hw_action_group = QActionGroup(self)
        self.hw_action_group.setExclusive(True)

        saved_hwdec = self.get_saved_hwdec()

        for cli_name, hw_arg in DEVICE_MAP.items():
            action = hw_menu.addAction(f"Save: {cli_name} ({hw_arg})")
            action.setCheckable(True)
            self.hw_action_group.addAction(action)
            
            if saved_hwdec == hw_arg:
                action.setChecked(True)

            # ربط الأكشن بالدالة البرمجية
            action.triggered.connect(lambda checked, h=hw_arg: self.save_default_hwdec(h))
            
        hw_menu.addSeparator()
        reset_action = hw_menu.addAction("Reset HW Default 🔄")
        reset_action.triggered.connect(self.reset_default_hwdec)

        # --- إضافة قائمة YouTube الجديدة هنا ---
        youtube_menu = self.addMenu("YouTube 📺")
        download_action = youtube_menu.addAction("Download YouTube Video 📥")
        download_action.triggered.connect(self.show_youtube_dialog)

    def setup_playlist_button(self):
        """إضافة زر الـ Playlist في أقصى اليمين"""
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
        
        # وضع الزر في الزاوية اليمنى العلوية من الـ MenuBar
        self.setCornerWidget(self.playlist_btn, Qt.Corner.TopRightCorner)

    def show_youtube_dialog(self):
        """فتح نافذة إدخال رابط اليوتيوب"""
        self.yt_dialog = YouTubeURLDialog(self.main_window)
        self.yt_dialog.show()

    # --- منطق الـ Cache المستخلص ---
    
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
        
        self.hw_changed.emit("no") # العودة للحالة الافتراضية

    def get_saved_hwdec(self):
        hw_file = Path.home() / ".cache" / "hardplayer" / "hw.txt"
        if hw_file.exists():
            return hw_file.read_text(encoding="utf-8").strip()
        return None