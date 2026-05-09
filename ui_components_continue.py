# ui_components_continue.py

import os
import json
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from styles import CatppuccinMocha, AppStyles
from config import MAUVE

class ResumeManager:
    """
    مدير لحفظ واسترجاع أوقات توقف الفيديوهات.
    يحفظ البيانات في ملف JSON داخل مسار إعدادات المستخدم.
    """
    def __init__(self):
        self.config_dir = os.path.expanduser("~/.config/hardplayer")
        self.file_path = os.path.join(self.config_dir, "resume_data.json")
        os.makedirs(self.config_dir, exist_ok=True)
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_position(self, filepath, time_pos, duration=None):
        if not filepath or time_pos is None:
            return
            
        # لا تقم بالحفظ إذا كان متبقي أقل من 5 ثواني على نهاية الفيديو
        if duration and (duration - time_pos) < 5:
            self.clear_position(filepath)
            return
            
        # لا تقم بالحفظ إذا لم يتخطى المستخدم أول 5 ثواني
        if time_pos < 5:
            return

        self.data[filepath] = time_pos
        with open(self.file_path, 'w') as f:
            json.dump(self.data, f)

    def get_position(self, filepath):
        return self.data.get(filepath, 0.0)

    def clear_position(self, filepath):
        if filepath in self.data:
            del self.data[filepath]
            with open(self.file_path, 'w') as f:
                json.dump(self.data, f)


class ContinueDialog(QDialog):
    """
    نافذة الاستئناف. لا يمكن إغلاقها إلا باختيار أحد الزرين.
    """
    def __init__(self, parent=None, saved_time=0.0):
        super().__init__(parent)
        self.saved_time = saved_time
        self.choice = "restart"  # القيمة الافتراضية
        self.setup_ui()

    def setup_ui(self):
        # 1. إعدادات النافذة لمنع الإغلاق
        # إزالة شريط العنوان وأزرار (X, Maximize, Minimize)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        self.setModal(True)
        self.setWindowTitle("Resume Playback")
        self.resize(350, 150)
        self.setStyleSheet(AppStyles.DIALOG)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # تحويل الثواني إلى صيغة MM:SS أو HH:MM:SS
        time_str = self._format_time(self.saved_time)

        # 2. النصوص
        lbl_msg = QLabel("Video was closed previously.\nWhere do you want to start?")
        lbl_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_msg.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(lbl_msg)

        # 3. الأزرار
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        btn_continue = QPushButton(f"Continue ({time_str})")
        # تمييز زر المتابعة بلون الـ Mauve بعد التعديل الصحيح
        btn_continue.setStyleSheet(f"""
            QPushButton {{
                background-color: {MAUVE};
                color: {CatppuccinMocha.BASE};
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {CatppuccinMocha.TEXT}; }}
        """)
        
        btn_restart = QPushButton("Play from 00:00")
        
        btn_continue.clicked.connect(self.do_continue)
        btn_restart.clicked.connect(self.do_restart)

        btn_layout.addWidget(btn_restart)
        btn_layout.addWidget(btn_continue)
        layout.addLayout(btn_layout)

    def _format_time(self, seconds):
        seconds = int(seconds)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    def do_continue(self):
        self.choice = "continue"
        self.accept() 

    def do_restart(self):
        self.choice = "restart"
        self.accept()

    def closeEvent(self, event):
        """تجاهل حدث الإغلاق (Alt+F4 أو أي إشارة إغلاق داخلية)"""
        event.ignore()

    def keyPressEvent(self, event):
        """تجاهل ضغطة زر Esc"""
        if event.key() == Qt.Key.Key_Escape:
            event.ignore()
        else:
            super().keyPressEvent(event)