# keyboard_shortcuts.py

from PyQt6.QtCore import Qt, QObject, QEvent, QTimer
from PyQt6.QtWidgets import QApplication, QLineEdit, QTextEdit, QPlainTextEdit

class KeyboardShortcutHandler(QObject):
    """
    Keyboard shortcuts manager. Works as an Event Filter to capture key presses
    before other UI elements consume them (such as the spacebar issue).
    """
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
        # Install the filter at the entire application level
        QApplication.instance().installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            # 1. If the main window is inactive (e.g., a sub-window is open), let the event pass
            if not self.main_window.isActiveWindow():
                return super().eventFilter(obj, event)

            # 2. If the user is typing in a text box (e.g., search), do not intervene so as not to prevent them from typing a space
            if isinstance(obj, (QLineEdit, QTextEdit, QPlainTextEdit)):
                return super().eventFilter(obj, event)

            key = event.key()
            modifiers = event.modifiers()

            # --- Fix the spacebar issue (Space) ---
            # Adding the spacebar here along with returning True prevents the event from triggering focused buttons
            if key in (Qt.Key.Key_Space, Qt.Key.Key_MediaPlay, Qt.Key.Key_MediaTogglePlayPause, Qt.Key.Key_F8):
                self.main_window.toggle_playback()
                return True 

            # [P] Show the startup screen
            elif key == Qt.Key.Key_P and getattr(self.main_window.player, 'core_idle', True):
                self.main_window.show_startup_dialog()
                return True

            # [I] Show info
            elif key == Qt.Key.Key_I:
                self.main_window.show_info_dialog()
                return True

            # [Left] Rewind video
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

            # [Right] Forward video
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

            # [Media Next / F9] Next
            elif key in (Qt.Key.Key_MediaNext, Qt.Key.Key_F9):
                self.main_window.play_next()
                return True

            # [Media Previous / F7] Previous
            elif key in (Qt.Key.Key_MediaPrevious, Qt.Key.Key_F7):
                self.main_window.play_previous()
                return True

            # [Media Stop] Stop
            elif key == Qt.Key.Key_MediaStop:
                self.main_window.stop_playback()
                return True

            # [C] Subtitles
            elif key == Qt.Key.Key_C:
                self.main_window.toggle_subtitles()
                return True

        # Allow the rest of the events (unregistered keys above) to pass normally
        return super().eventFilter(obj, event)