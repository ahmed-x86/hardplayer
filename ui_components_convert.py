# ui_components_convert.py

import os
import subprocess
import json
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QProgressBar, QFileDialog, QFrame, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class ConversionDialogUI(QDialog):
    cancel_requested = pyqtSignal(bool) 

    def __init__(self, mode, parent=None):
        super().__init__(parent)
        self.mode = mode
        self.setWindowTitle(f"HardPlayer Converter - {mode}")
        self.setFixedSize(550, 380)
        self.setStyleSheet("background-color: #11111b; color: #cdd6f4;")

        self.is_processing = False
        self.input_file = ""   # <-- (Fix Core Dumped crash bug)
        self.output_file = ""
        self.total_duration = 0.0 
        self.action_buttons = {} 

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        # 1. File Selection Area
        file_layout = QHBoxLayout()
        self.lbl_file = QLabel("No file selected")
        self.lbl_file.setStyleSheet("background-color: #1e1e2e; padding: 10px; border-radius: 6px; font-weight: bold; border: 1px solid #313244;")
        self.btn_browse = QPushButton("📂 Browse")
        self.btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browse.setStyleSheet("""
            QPushButton { background-color: #89b4fa; color: #11111b; font-weight: bold; padding: 10px; border-radius: 6px; border: none; }
            QPushButton:hover { background-color: #b4befe; }
        """)
        file_layout.addWidget(self.lbl_file, 1)
        file_layout.addWidget(self.btn_browse)
        self.layout.addLayout(file_layout)

        # 2. File Metadata Info Box
        self.info_frame = QFrame()
        self.info_frame.setObjectName("InfoFrame")
        self.info_frame.setStyleSheet("""
            QFrame#InfoFrame {
                background-color: #1e1e2e;
                border-radius: 12px;
                padding: 15px;
                border: 1px solid #313244;
            }
            QLabel {
                font-family: 'JetBrains Mono', 'monospace';
                font-size: 12px;
                background: transparent;
                border: none;
            }
        """)
        info_layout = QVBoxLayout(self.info_frame)
        self.lbl_info = QLabel("<b>File Info:</b> Waiting for input...<br><b>Format:</b> --<br><b>Video Codec:</b> -- | <b>Audio Codec:</b> --")
        self.lbl_info.setStyleSheet("color: #bac2de; line-height: 1.5;")
        info_layout.addWidget(self.lbl_info)
        self.layout.addWidget(self.info_frame)

        # 3. Progress Bar & Status
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar { 
                border: 2px solid #313244; 
                border-radius: 10px; 
                text-align: center; 
                height: 35px; 
                background: #1e1e2e;
                color: #cba6f7; 
                font-weight: bold;
                font-size: 13px;
            }
            QProgressBar::chunk { 
                background-color: #a6e3a1; 
                border-radius: 8px;
            }
        """)
        self.layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("Ready for conversion...")
        self.lbl_status.setStyleSheet("color: #a6adc8; font-size: 12px;")
        self.layout.addWidget(self.lbl_status)

        # 4. Dynamic Action Buttons Area
        self.btn_layout = QHBoxLayout()
        self.layout.addLayout(self.btn_layout)
        
        self.setup_buttons()

    def setup_buttons(self):
        if self.mode in ["To MP4", "To MKV", "To WebM"]:
            self.add_action_btn("By CPU", "#a6e3a1", "#94e2d5")     
            self.add_action_btn("By CUDA", "#f9e2af", "#f2cd32")    
            self.add_action_btn("By NVENC", "#cba6f7", "#b4befe")   
        elif self.mode == "To DaVinci":
            self.add_action_btn("By CPU", "#a6e3a1", "#94e2d5")
            self.add_action_btn("By CUDA", "#f9e2af", "#f2cd32")
            self.add_action_btn("By CUDA FULL", "#cba6f7", "#b4befe")
        else:
            self.add_action_btn("Start Conversion", "#a6e3a1", "#94e2d5")
            
    def add_action_btn(self, name, color, hover_color):
        btn = QPushButton(name)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{ background-color: {color}; color: #11111b; font-weight: bold; padding: 10px; border-radius: 6px; border: none; }}
            QPushButton:hover {{ background-color: {hover_color}; }}
        """)
        self.btn_layout.addWidget(btn)
        self.action_buttons[name] = btn

    def extract_metadata(self, file_path):
        try:
            cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', file_path]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            data = json.loads(res.stdout)
            
            fmt = data.get('format', {})
            streams = data.get('streams', [])
            
            # --- Fix MKV issue: Search for duration everywhere ---
            duration = fmt.get('duration')
            if not duration and streams:
                for s in streams:
                    if s.get('duration'):
                        duration = s.get('duration')
                        break
                        
            if duration:
                self.total_duration = float(duration)
            else:
                self.total_duration = 0.0
            # ----------------------------------------------------

            v_codec, a_codec = "N/A", "N/A"
            for s in streams:
                if s.get('codec_type') == 'video' and v_codec == "N/A": 
                    v_codec = s.get('codec_name', 'Unknown').upper()
                if s.get('codec_type') == 'audio' and a_codec == "N/A": 
                    a_codec = s.get('codec_name', 'Unknown').upper()
            
            format_name = str(fmt.get('format_name', 'Unknown')).upper()
            tags = fmt.get('tags', {})
            
            author = tags.get('artist', tags.get('author', tags.get('title', 'Unknown')))
            filename = os.path.basename(file_path)
            
            info_text = f"<b>📄 Name:</b> {filename}<br><b>🗂️ Format:</b> {format_name}<br><b>🎞️ Video Codec:</b> {v_codec} | <b>🎵 Audio Codec:</b> {a_codec}"
            if author != 'Unknown':
                info_text += f"<br><b>👤 Author/Title:</b> {author}"
                
            self.lbl_info.setText(info_text)
        except Exception:
            self.total_duration = 0.0
            self.lbl_info.setText(f"<b>📄 Name:</b> {os.path.basename(file_path)}<br><b>⚠️ Metadata:</b> Could not read file details.")

    def request_cancel(self):
        if not self.is_processing:
            return True

        dlg = QDialog(self)
        dlg.setWindowTitle("Confirm Cancel")
        dlg.setFixedSize(360, 200)
        dlg.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")
        layout = QVBoxLayout(dlg)
        
        lbl = QLabel("Do you want to stop the conversion?\nDo you want to cancel processing?")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(lbl)
        
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_yes = QPushButton("Yes")
        btn_yes_save = QPushButton("Yes and save files")
        btn_no = QPushButton("No")
        
        btn_yes.setStyleSheet("QPushButton { background: #f38ba8; color: #11111b; font-weight: bold; padding: 8px; border-radius: 4px; } QPushButton:hover { background: #eba0ac; }")
        btn_yes_save.setStyleSheet("QPushButton { background: #f9e2af; color: #11111b; font-weight: bold; padding: 8px; border-radius: 4px; } QPushButton:hover { background: #f2cd32; }")
        btn_no.setStyleSheet("QPushButton { background: #a6e3a1; color: #11111b; font-weight: bold; padding: 8px; border-radius: 4px; } QPushButton:hover { background: #94e2d5; }")
        
        result = 0
        def set_res(val):
            nonlocal result
            result = val
            dlg.accept()
            
        btn_yes.clicked.connect(lambda: set_res(1))
        btn_yes_save.clicked.connect(lambda: set_res(2))
        btn_no.clicked.connect(lambda: set_res(0))
        
        btn_layout.addWidget(btn_yes)
        btn_layout.addWidget(btn_yes_save)
        btn_layout.addWidget(btn_no)
        layout.addLayout(btn_layout)
        
        dlg.exec()
        
        if result == 1:
            self.cancel_requested.emit(True)
            return True
        elif result == 2:
            self.cancel_requested.emit(False)
            return True
            
        return False

    def reject(self):
        if self.request_cancel():
            super().reject()

    def closeEvent(self, event):
        if self.request_cancel():
            event.accept()
        else:
            event.ignore()