# video_surface.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt

class AspectRatioContainer(QWidget):
    """
    A custom container that maintains the aspect ratio of its child widget (the video player).
    It dynamically adds letterboxing or pillarboxing to prevent the video from stretching.
    """
    def __init__(self, child_widget, bg_color="#11111b", parent=None):
        super().__init__(parent)
        self.child_widget = child_widget
        self.bg_color = bg_color
        
        # Set the background color for the letterboxing area (Catppuccin Crust)
        self.setStyleSheet(f"background-color: {self.bg_color};")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Center the video widget inside the layout
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.child_widget)

    def resizeEvent(self, event):
        """
        Calculates the optimal size for the video widget to maintain a standard 16:9 
        aspect ratio whenever the main window is resized by the user or window manager.
        """
        super().resizeEvent(event)
        
        # Standard 16:9 aspect ratio target
        target_aspect = 16.0 / 9.0
        
        current_width = self.width()
        current_height = self.height()
        
        if current_height == 0:
            return
            
        current_aspect = current_width / current_height
        
        if current_aspect > target_aspect:
            # Window is too wide: Maximize height and scale width (Pillarboxing / Vertical bars)
            new_height = current_height
            new_width = int(new_height * target_aspect)
        else:
            # Window is too tall: Maximize width and scale height (Letterboxing / Horizontal bars)
            new_width = current_width
            new_height = int(new_width / target_aspect)
            
        # Apply the calculated dimensions to the MPV surface
        self.child_widget.setFixedSize(new_width, new_height)


class VideoSurface(QWidget):
    """
    The main video surface module. It creates the native X11/Wayland window required 
    by the MPV engine for hardware acceleration and wraps it in the AspectRatioContainer.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Create the inner widget that MPV will attach to
        self.video_widget = QWidget()
        
        # CRITICAL FOR LINUX / WAYLAND:
        # Prevent Qt from drawing its own background and force a Native Window ID.
        # This allows MPV's GPU context (e.g., x11egl or wayland) to hook into it seamlessly.
        self.video_widget.setAttribute(Qt.WidgetAttribute.WA_DontCreateNativeAncestors)
        self.video_widget.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        
        # 2. Wrap it in the AspectRatioContainer
        # Using Catppuccin Crust (#11111b) for the background color
        self.container = AspectRatioContainer(self.video_widget, "#11111b")
        
        self.layout.addWidget(self.container)

    def get_mpv_wid(self):
        """
        Returns the Window ID (WID) as a string. 
        Pass this to the 'wid' argument when initializing mpv.MPV().
        """
        return str(int(self.video_widget.winId()))