# playlist_panel.py

import os
from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                             QScrollArea, QWidget, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

# Import the local thumbnail generator
from thumbnail_gen import get_local_thumbnail

class PlaylistPanel(QFrame):
    """
    Sidebar Playlist panel with Lazy Loading implementation to prevent UI freezes.
    """
    # Signal emitted with the file path when a media item is clicked
    file_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.playlist = []
        self.loaded_items_count = 0
        self.load_more_btn = None
        
        self.init_ui()

    def init_ui(self):
        # The MAGIC FIX: Force the overlay to be a Native Window 
        # so it draws correctly over the MPV Native Window in Linux/Wayland.
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        self.setFixedWidth(300)
        self.setVisible(False)
        
        # Catppuccin Mocha overlay style (slightly transparent crust/mantle)
        self.setStyleSheet("""
            QFrame { 
                background-color: rgba(24, 24, 37, 230); 
                border-left: 2px solid #313244; 
            }
        """)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Panel Title
        title = QLabel("Media in Folder")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #cdd6f4; background: transparent; margin-bottom: 10px;")
        self.main_layout.addWidget(title)
        
        # Scroll Area setup
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background: transparent;")
        
        self.playlist_content = QWidget()
        self.playlist_content.setStyleSheet("background: transparent;")
        self.playlist_items_layout = QVBoxLayout(self.playlist_content)
        self.playlist_items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.playlist_items_layout.setSpacing(12)
        
        self.scroll_area.setWidget(self.playlist_content)
        self.main_layout.addWidget(self.scroll_area)

    def set_playlist_data(self, files_list):
        """Update the playlist data and reset the UI."""
        self.playlist = files_list
        self.populate_ui()

    def populate_ui(self):
        """Clear existing items and start loading the first batch."""
        # Clear old items to prevent duplicates when switching folders
        while self.playlist_items_layout.count():
            item = self.playlist_items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.loaded_items_count = 0
        self.load_more_items()

    def load_more_items(self):
        """Loads items in batches of 6 to prevent UI freezing (Lazy Loading)."""
        # Remove the 'Load More' button temporarily if it exists
        if hasattr(self, 'load_more_btn') and self.load_more_btn:
            self.playlist_items_layout.removeWidget(self.load_more_btn)
            self.load_more_btn.deleteLater()
            self.load_more_btn = None

        start_index = self.loaded_items_count
        end_index = min(start_index + 6, len(self.playlist))
        batch = self.playlist[start_index:end_index]
            
        for path in batch:
            item_widget = self.create_item_widget(path)
            self.playlist_items_layout.addWidget(item_widget)

        self.loaded_items_count = end_index
        
        # Add the 'Load More' button if there are remaining items in the list
        if self.loaded_items_count < len(self.playlist):
            self.load_more_btn = QPushButton("Load More ⏬")
            self.load_more_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.load_more_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #313244; 
                    color: #cdd6f4; 
                    border-radius: 8px; 
                    padding: 8px; 
                    font-weight: bold; 
                }
                QPushButton:hover { background-color: #45475a; color: #89b4fa; }
            """)
            self.load_more_btn.clicked.connect(self.load_more_items)
            self.playlist_items_layout.addWidget(self.load_more_btn)

    def create_item_widget(self, path):
        """Creates a single video item widget for the playlist."""
        item_frame = QFrame()
        item_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        item_frame.setStyleSheet("""
            QFrame { background-color: #313244; border-radius: 8px; }
            QFrame:hover { background-color: #45475a; }
        """)
        
        h_layout = QHBoxLayout(item_frame)
        h_layout.setContentsMargins(5, 5, 5, 5)
        
        # Thumbnail display
        thumb_label = QLabel()
        thumb_label.setFixedSize(80, 45)
        
        thumb_path = get_local_thumbnail(path) if not path.startswith("http") else None
        
        if thumb_path and os.path.exists(thumb_path):
            pix = QPixmap(thumb_path).scaled(80, 45, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            thumb_label.setPixmap(pix)
        else:
            thumb_label.setText("🎬")
            thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            thumb_label.setStyleSheet("background-color: #11111b; color: #fab387; border-radius: 4px;")

        # Filename formatting (Max 4 words for line 1, 2 words for line 2)
        name = os.path.basename(path)
        words = name.split()
        line1 = " ".join(words[:4])
        line2 = " ".join(words[4:6]) + "..." if len(words) > 4 else ""
        
        name_label = QLabel(f"{line1}\n{line2}" if line2 else line1)
        name_label.setStyleSheet("color: #cdd6f4; font-size: 11px; background: transparent;")
        name_label.setWordWrap(True)
        
        h_layout.addWidget(thumb_label)
        h_layout.addWidget(name_label, 1)
        
        # Connect click event to emit the selected file path
        item_frame.mousePressEvent = lambda e, p=path: self.file_selected.emit(p)
        
        return item_frame

    def update_position(self, container_width, container_height):
        """Updates the sidebar position to dock at the far right, overlaying the content."""
        w = 300
        x = container_width - w
        self.setGeometry(x, 0, w, container_height)