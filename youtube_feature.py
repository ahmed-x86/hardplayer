# youtube_feature.py

import subprocess
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QLabel, QTextEdit, QLineEdit, QPushButton)
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QFont

class YouTubeQualityDialog(QDialog):
    def __init__(self, yt_url, parent=None):
        super().__init__(parent)
        self.yt_url = yt_url
        self.format_code = "best"
        self.setWindowTitle("YouTube Video Formats")
        self.setFixedSize(850, 500)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        lbl = QLabel(f"🔗 URL: {yt_url}\n⏳ Fetching formats, please wait...")
        lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(lbl)
        
        # Text area to display format options without line wrapping for better readability
        self.info_text = QTextEdit(self)
        self.info_text.setReadOnly(True)
        self.info_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.info_text)
        
        input_layout = QHBoxLayout()
        self.format_input = QLineEdit(self)
        self.format_input.setPlaceholderText("Enter format code (e.g., 299+140 or best)")
        self.format_input.setText("best")
        
        self.play_btn = QPushButton("▶ Continue to Decoding")
        self.play_btn.clicked.connect(self.accept_format)
        
        input_layout.addWidget(QLabel("📝 Format Code:"))
        input_layout.addWidget(self.format_input)
        input_layout.addWidget(self.play_btn)
        
        layout.addLayout(input_layout)
        
        # Use a timer to ensure the UI renders before the blocking fetch process starts
        QTimer.singleShot(100, self.fetch_formats)

    def fetch_formats(self):
        try:
            result = subprocess.run(
                ["yt-dlp", "-F", self.yt_url],
                capture_output=True, text=True, check=True
            )
            self.info_text.setText(result.stdout)
            
            # Auto-scroll to the bottom where high-quality formats usually are
            scrollbar = self.info_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
        except Exception as e:
            self.info_text.setText(f"❌ Error fetching formats. Ensure yt-dlp is installed.\n\n{str(e)}")

    def accept_format(self):
        self.format_code = self.format_input.text().strip()
        if not self.format_code:
            self.format_code = "best"
        self.accept()