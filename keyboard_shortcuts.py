# keyboard_shortcuts.py

from PyQt6.QtCore import Qt, QObject, QEvent, QTimer
from PyQt6.QtWidgets import QApplication, QLineEdit, QTextEdit, QPlainTextEdit

class KeyboardShortcutHandler(QObject):
    """
    مدير اختصارات لوحة المفاتيح. يعمل كـ Event Filter لالتقاط الضغطات 
    قبل أن تستهلكها عناصر الواجهة الأخرى (مثل مشكلة زر المسطرة).
    """
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
        # تثبيت الفلتر على مستوى التطبيق بالكامل
        QApplication.instance().installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            # 1. إذا كانت النافذة الرئيسية غير نشطة (مثل وجود نافذة فرعية مفتوحة)، اترك الحدث يمر
            if not self.main_window.isActiveWindow():
                return super().eventFilter(obj, event)

            # 2. إذا كان المستخدم يكتب في مربع نص (مثل البحث)، لا نتدخل كي لا نمنعه من كتابة مسافة
            if isinstance(obj, (QLineEdit, QTextEdit, QPlainTextEdit)):
                return super().eventFilter(obj, event)

            key = event.key()
            modifiers = event.modifiers()

            # --- إصلاح مشكلة المسطرة (Space) ---
            # إضافة المسطرة هنا مع إرجاع True يمنع الحدث من تفعيل الأزرار المحددة
            if key in (Qt.Key.Key_Space, Qt.Key.Key_MediaPlay, Qt.Key.Key_MediaTogglePlayPause, Qt.Key.Key_F8):
                self.main_window.toggle_playback()
                return True 

            # [P] إظهار شاشة البداية
            elif key == Qt.Key.Key_P and getattr(self.main_window.player, 'core_idle', True):
                self.main_window.show_startup_dialog()
                return True

            # [I] إظهار معلومات
            elif key == Qt.Key.Key_I:
                self.main_window.show_info_dialog()
                return True

            # [Left] تأخير الفيديو
            elif key == Qt.Key.Key_Left:
                self.main_window._keyboard_seeking = True
                if modifiers & Qt.KeyboardModifier.ShiftModifier:
                    self.main_window.player.seek(-60)  # Shift + Left = 60s
                elif modifiers & Qt.KeyboardModifier.ControlModifier:
                    self.main_window.player.seek(-30)  # Ctrl + Left = 30s
                else:
                    self.main_window.player.seek(-5)   # Left = 5s
                QTimer.singleShot(800, self.main_window._reset_seek_flag)
                return True

            # [Right] تقديم الفيديو
            elif key == Qt.Key.Key_Right:
                self.main_window._keyboard_seeking = True
                if modifiers & Qt.KeyboardModifier.ShiftModifier:
                    self.main_window.player.seek(60)   # Shift + Right = 60s
                elif modifiers & Qt.KeyboardModifier.ControlModifier:
                    self.main_window.player.seek(30)   # Ctrl + Right = 30s
                else:
                    self.main_window.player.seek(5)    # Right = 5s
                QTimer.singleShot(800, self.main_window._reset_seek_flag)
                return True

            # [Media Next / F9] التالي
            elif key in (Qt.Key.Key_MediaNext, Qt.Key.Key_F9):
                self.main_window.play_next()
                return True

            # [Media Previous / F7] السابق
            elif key in (Qt.Key.Key_MediaPrevious, Qt.Key.Key_F7):
                self.main_window.play_previous()
                return True

            # [Media Stop] إيقاف
            elif key == Qt.Key.Key_MediaStop:
                self.main_window.stop_playback()
                return True

            # [C] ترجمة
            elif key == Qt.Key.Key_C:
                self.main_window.toggle_subtitles()
                return True

        # السماح بمرور باقي الأحداث (الأزرار غير المسجلة أعلاه) بشكل طبيعي
        return super().eventFilter(obj, event)