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


class ClickableLabel(QLabel):
    """
    Custom QLabel that emits a signal when clicked.
    """
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
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
    seek_requested = pyqtSignal(int)
    subtitle_toggled = pyqtSignal() # Subtitle button signal
    
    # Updated repeat signal to support MPRIS with three states: None, Playlist, Track
    repeat_mode_changed = pyqtSignal(str) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_loop_status = "None" # Default repeat status
        self.show_remaining_time = False # Addition: Time display mode (elapsed or remaining)
        self.init_ui()

    def init_ui(self):
        self.setObjectName("MainControlBar")
        
        # Original Catppuccin CSS logic restored with slight padding tweaks for new height
        self.setStyleSheet("""
            QFrame#MainControlBar {
                background-color: #11111b; 
                border-top: 2px solid #313244;
            }
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border-radius: 6px;
                padding: 4px;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #45475a;
            }
            QSlider::groove:horizontal {
                border: 1px solid #313244;
                height: 6px;
                background: #313244;
                margin: 2px 0;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #e9d4a4;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #89b4fa;
                border: 1px solid #89b4fa;
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QLabel {
                color: #cdd6f4; 
                font-family: 'JetBrains Mono', 'monospace';
                border: none; 
                background: transparent;
            }
        """)
        
        # Reduce height to 50 as requested
        self.setFixedHeight(50)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setSpacing(12)

        self.play_btn = QPushButton("▶")
        self.repeat_btn = QPushButton("🔁 ✖") 
        self.subtitles_btn = QPushButton("💬 CC") 
        
        self.play_btn.setFixedWidth(50)
        self.repeat_btn.setFixedWidth(65)
        self.subtitles_btn.setFixedWidth(60)
        
        self.play_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.repeat_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.subtitles_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Restored NoFocus to prevent seeking glitches
        self.play_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.repeat_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.subtitles_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Connect signals
        self.play_btn.clicked.connect(self.play_toggled.emit)
        self.repeat_btn.clicked.connect(self.cycle_repeat_mode) # Use the new cycle function
        self.subtitles_btn.clicked.connect(self.subtitle_toggled.emit) 

        # Restored the custom ClickableSlider
        self.slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.slider.setEnabled(False)
        self.slider.sliderMoved.connect(self.seek_requested.emit)

        # Modified here to support clicking on the time
        self.time_label = ClickableLabel("00:00 / 00:00")
        self.time_label.setFixedWidth(150) # Increase width slightly for the negative sign
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.time_label.clicked.connect(self.toggle_time_display)

        # Track control buttons
        self.stop_btn = QPushButton("⏹")
        self.prev_btn = QPushButton("⏮")
        self.next_btn = QPushButton("⏭")
        
        # Connect signals for navigation
        self.stop_btn.clicked.connect(self.stop_clicked.emit)
        self.prev_btn.clicked.connect(self.prev_clicked.emit)
        self.next_btn.clicked.connect(self.next_clicked.emit)

        for btn in [self.stop_btn, self.prev_btn, self.next_btn]:
            btn.setFixedWidth(50)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            # Restored NoFocus
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Arrange elements in the layout
        layout.addWidget(self.play_btn)
        layout.addWidget(self.repeat_btn)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.time_label)
        layout.addWidget(self.subtitles_btn) 
        layout.addWidget(self.prev_btn)      
        layout.addWidget(self.stop_btn)      
        layout.addWidget(self.next_btn)      

        # Initialize the initial repeat button appearance
        self.set_repeat_status(self.current_loop_status)

    def toggle_time_display(self):
        """Toggle between showing elapsed time and remaining time."""
        self.show_remaining_time = not self.show_remaining_time

    def set_subtitle_status(self, is_active):
        """Update subtitle button color based on its state."""
        if is_active:
            self.subtitles_btn.setStyleSheet("""
                QPushButton {
                    color: #a6e3a1; 
                    border: 1px solid #a6e3a1; 
                    background-color: #313244;
                    font-weight: bold;
                }
            """)
        else:
            # Clear custom style to return to default appearance
            self.subtitles_btn.setStyleSheet("")

    def cycle_repeat_mode(self):
        """Cycle through the three repeat modes and emit the signal."""
        if self.current_loop_status == "None":
            new_status = "Playlist"
        elif self.current_loop_status == "Playlist":
            new_status = "Track"
        else:
            new_status = "None"
            
        self.set_repeat_status(new_status)
        self.repeat_mode_changed.emit(new_status)

    def set_repeat_status(self, status: str):
        """
        Update repeat button appearance to match the MPRIS state.
        status: "None", "Playlist", or "Track"
        """
        self.current_loop_status = status
        
        if status == "Playlist":
            self.repeat_btn.setText("🔁 ✔️")
            self.repeat_btn.setStyleSheet("""
                QPushButton {
                    color: #a6e3a1; 
                    border: 1px solid #a6e3a1; 
                    background-color: #313244;
                    font-weight: bold;
                }
            """)
        elif status == "Track":
            self.repeat_btn.setText("🔂 1")
            self.repeat_btn.setStyleSheet("""
                QPushButton {
                    color: #89b4fa; 
                    border: 1px solid #89b4fa; 
                    background-color: #313244;
                    font-weight: bold;
                }
            """)
        else: # "None"
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
            
            if self.show_remaining_time:
                remaining_time = duration - current_time
                time_str = f"-{self._format_time(remaining_time, has_hours)} / {self._format_time(duration, has_hours)}"
            else:
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