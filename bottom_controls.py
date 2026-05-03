# bottom_controls.py

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QSlider, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor

class ClickableSlider(QSlider):
    """
    Custom QSlider that jumps to the position where the user clicks.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Prevent the slider from stealing keyboard focus so arrow keys control MPV seeking
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Calculate the relative position based on click coordinates
            val = self.minimum() + ((self.maximum() - self.minimum()) * event.position().x()) / self.width()
            self.setValue(int(val))
            # Manually emit the signal to seek immediately
            self.sliderMoved.emit(int(val))
        super().mousePressEvent(event)


class PlayerControlBar(QFrame):
    """
    Bottom control bar containing media playback controls, progress slider, 
    and time display. Emits signals to communicate with the main MPV engine.
    """
    # Signals for media control actions
    play_toggled = pyqtSignal()
    stop_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    prev_clicked = pyqtSignal()
    repeat_toggled = pyqtSignal()
    seek_requested = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setObjectName("MainControlBar")
        
        # Original Catppuccin CSS logic restored
        self.setStyleSheet("""
            QFrame#MainControlBar {
                background-color: #11111b; 
                border-top: 2px solid #313244;
            }
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border-radius: 6px;
                padding: 5px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #45475a;
            }
            QSlider::groove:horizontal {
                border: 1px solid #313244;
                height: 8px;
                background: #313244;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::sub-page:horizontal {
                background: #e9d4a4;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #89b4fa;
                border: 1px solid #89b4fa;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QLabel {
                color: #cdd6f4; 
                font-family: 'JetBrains Mono', 'monospace';
                border: none; 
                background: transparent;
            }
        """)
        self.setFixedHeight(70)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(15)

        self.play_btn = QPushButton("▶")
        self.repeat_btn = QPushButton("🔁 ✖") 
        self.play_btn.setFixedWidth(55)
        self.repeat_btn.setFixedWidth(75)
        self.play_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.repeat_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Restored NoFocus to prevent seeking glitches
        self.play_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.repeat_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Connect signals
        self.play_btn.clicked.connect(self.play_toggled.emit)
        self.repeat_btn.clicked.connect(self.repeat_toggled.emit)

        # Restored the custom ClickableSlider
        self.slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.slider.setEnabled(False)
        self.slider.sliderMoved.connect(self.seek_requested.emit)

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setFixedWidth(160)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.stop_btn = QPushButton("⏹")
        self.prev_btn = QPushButton("⏮")
        self.next_btn = QPushButton("⏭")
        
        # Connect signals for navigation
        self.stop_btn.clicked.connect(self.stop_clicked.emit)
        self.prev_btn.clicked.connect(self.prev_clicked.emit)
        self.next_btn.clicked.connect(self.next_clicked.emit)

        for btn in [self.stop_btn, self.prev_btn, self.next_btn]:
            btn.setFixedWidth(55)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            # Restored NoFocus
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        layout.addWidget(self.play_btn)
        layout.addWidget(self.repeat_btn)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.time_label)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.prev_btn)
        layout.addWidget(self.next_btn)

    def set_repeat_status(self, is_active):
        """Original logic for toggling the repeat button visuals."""
        if is_active:
            self.repeat_btn.setText("🔁 ✔️")
            self.repeat_btn.setStyleSheet("""
                QPushButton {
                    color: #afd89b; 
                    border: 1px solid #afd89b; 
                    background-color: #313244;
                    font-weight: bold;
                }
            """)
        else:
            self.repeat_btn.setText("🔁 ✖")
            self.repeat_btn.setStyleSheet("""
                QPushButton {
                    color: #f38ba8; 
                    border: 1px solid #f38ba8; 
                    background-color: #313244;
                }
            """)

    def update_ui_state(self, current_time, duration, is_paused, is_seeking):
        """Updates the UI components based on the player state."""
        if current_time is not None and duration is not None:
            self.slider.setEnabled(True)
            
            # Only update slider position if the user is not actively dragging it or using keyboard
            if not self.slider.isSliderDown() and not is_seeking:
                self.slider.setMaximum(int(duration))
                self.slider.setValue(int(current_time))
            
            # Update time label
            has_hours = duration >= 3600
            time_str = f"{self._format_time(current_time, has_hours)} / {self._format_time(duration, has_hours)}"
            self.time_label.setText(time_str)
            
            # Update Play/Pause button text
            if is_paused:
                self.play_btn.setText("▶")
            else:
                self.play_btn.setText("⏸")
        else:
            self.slider.setEnabled(False)
            self.time_label.setText("--:-- / --:--")

    def _format_time(self, seconds, force_hours=False):
        """Helper method to format seconds into HH:MM:SS or MM:SS."""
        if seconds is None or seconds < 0: 
            return "00:00"
        hours, remainder = divmod(int(seconds), 3600)
        mins, secs = divmod(remainder, 60)
        
        if hours > 0 or force_hours:
            return f"{hours:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"