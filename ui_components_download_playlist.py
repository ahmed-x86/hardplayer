# ui_components_download_playlist.py

import os
import json
import subprocess
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QWidget, QFrame, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from ui_components import ToggleSwitch, DownloadOptionsDialog
from youtube_feature import DownloadWorker, YTInfoFetcher

# ==========================================
# 1. Worker to fetch playlist links quickly
# ==========================================
class PlaylistFetchWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            cmd = ["yt-dlp", "--flat-playlist", "--dump-json", "--ignore-errors", self.url]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            videos = []
            for line in result.stdout.strip().split('\n'):
                if not line: continue
                try:
                    data = json.loads(line)
                    if 'url' in data or 'webpage_url' in data or 'id' in data:
                        vid_url = data.get('url') or data.get('webpage_url') or f"https://www.youtube.com/watch?v={data['id']}"
                        
                        pl_title = data.get('playlist', 'Unknown Playlist')
                        pl_uploader = data.get('playlist_uploader', data.get('uploader', 'Unknown Channel'))

                        videos.append({
                            'title': data.get('title', 'Unknown Video'),
                            'url': vid_url,
                            'playlist_title': pl_title,
                            'playlist_uploader': pl_uploader
                        })
                except json.JSONDecodeError:
                    pass
            self.finished.emit(videos)
        except Exception as e:
            self.error.emit(str(e))

# ==========================================
# 2. Download mode selection dialog (All or Select)
# ==========================================
class PlaylistModeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Playlist Download Mode")
        self.setFixedSize(350, 180)
        self.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")
        self.mode = "all" 

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        lbl = QLabel("📚 Playlist detected!\nHow do you want to download?")
        lbl.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

        btn_all = QPushButton("📥 Download Entire Playlist")
        btn_all.setStyleSheet("QPushButton { background-color: #cba6f7; color: #11111b; font-weight: bold; padding: 12px; border-radius: 6px; } QPushButton:hover { background-color: #b4befe; }")
        btn_all.clicked.connect(self.select_all)

        btn_select = QPushButton("✅ Select Specific Videos")
        btn_select.setStyleSheet("QPushButton { background-color: #89b4fa; color: #11111b; font-weight: bold; padding: 12px; border-radius: 6px; } QPushButton:hover { background-color: #b4befe; }")
        btn_select.clicked.connect(self.select_custom)

        layout.addWidget(btn_all)
        layout.addWidget(btn_select)

    def select_all(self):
        self.mode = "all"
        self.accept()

    def select_custom(self):
        self.mode = "select"
        self.accept()

# ==========================================
# 3. Video selection dialog
# ==========================================
class PlaylistSelectionDialog(QDialog):
    def __init__(self, videos, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Videos")
        self.setFixedSize(500, 600)
        self.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")
        
        self.videos = videos
        self.displayed_count = 0
        self.step = 5
        self.video_toggles = [] 

        self.layout = QVBoxLayout(self)
        
        lbl = QLabel(f"Total Videos: {len(self.videos)}\nSelect videos to download:")
        lbl.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.layout.addWidget(lbl)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background: transparent;")
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(10)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll.setWidget(self.content_widget)
        self.layout.addWidget(self.scroll)

        self.btn_show_more = QPushButton("⬇️ Show More (5)")
        self.btn_show_more.setStyleSheet("QPushButton { background-color: #313244; color: #cdd6f4; font-weight: bold; padding: 10px; border-radius: 6px; } QPushButton:hover { background-color: #45475a; }")
        self.btn_show_more.clicked.connect(self.load_more)
        self.layout.addWidget(self.btn_show_more)

        self.btn_confirm = QPushButton("🚀 Continue to Quality")
        self.btn_confirm.setStyleSheet("QPushButton { background-color: #a6e3a1; color: #11111b; font-weight: bold; padding: 12px; border-radius: 6px; } QPushButton:hover { background-color: #94e2d5; }")
        self.btn_confirm.clicked.connect(self.accept)
        self.layout.addWidget(self.btn_confirm)

        self.load_more()

    def load_more(self):
        end_idx = min(self.displayed_count + self.step, len(self.videos))
        for i in range(self.displayed_count, end_idx):
            vid = self.videos[i]
            row = QFrame()
            row.setStyleSheet("background-color: #11111b; border-radius: 8px; padding: 5px;")
            row_layout = QHBoxLayout(row)
            
            lbl_title = QLabel(f"{i+1}. {vid['title']}")
            lbl_title.setWordWrap(True)
            lbl_title.setStyleSheet("background: transparent; border: none;")
            
            toggle = ToggleSwitch()
            toggle.setChecked(True) 
            
            row_layout.addWidget(lbl_title, 1)
            row_layout.addWidget(toggle)
            
            self.content_layout.addWidget(row)
            self.video_toggles.append({"video": vid, "toggle": toggle})
            
        self.displayed_count = end_idx
        
        if self.displayed_count >= len(self.videos):
            self.btn_show_more.hide()

    def get_selected_videos(self):
        return [item["video"] for item in self.video_toggles if item["toggle"].isChecked()]


# ==========================================
# 4. Playlist queue management window (Tracker)
# ==========================================
class PlaylistProgressDialog(QDialog):
    def __init__(self, video_list, format_code, quality_name, dl_options, parent=None):
        super().__init__(parent)
        self.video_list = video_list
        self.format_code = format_code
        self.quality_name = quality_name
        self.dl_options = dl_options
        self.total_videos = len(video_list)
        self.current_index = 0
        self.is_cancelled = False
        
        self.current_dl_dlg = None 
        
        pl_title = video_list[0].get('playlist_title', 'Unknown Playlist')
        pl_channel = video_list[0].get('playlist_uploader', 'Unknown Channel')

        self.setWindowTitle("HardPlayer - Playlist Tracker")
        self.setFixedWidth(540) 
        self.setStyleSheet("background-color: #11111b; color: #cdd6f4;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # --- 1. Info Box ---
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
        
        self.name_lbl = QLabel(f"<b>📄 Playlist Name:</b> {pl_title}")
        self.name_lbl.setWordWrap(True)
        
        self.uploader_lbl = QLabel(f"<b>👤 Channel:</b> {pl_channel}")
        self.stats_lbl = QLabel(f"<b>📦 Total Videos:</b> {self.total_videos} | <b>🎬 Quality:</b> {self.quality_name}")
        
        self.current_vid_lbl = QLabel("<b>🔄 Current Task:</b> Initializing queue...")
        self.current_vid_lbl.setStyleSheet("color: #89b4fa; font-weight: bold;")
        self.current_vid_lbl.setWordWrap(True)

        info_layout.addWidget(self.name_lbl)
        info_layout.addWidget(self.uploader_lbl)
        info_layout.addWidget(self.stats_lbl)
        info_layout.addWidget(self.current_vid_lbl)
        
        layout.addWidget(self.info_frame)

        # --- 2. Overall Progress Bar ---
        self.overall_pbar = QProgressBar()
        self.overall_pbar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.overall_pbar.setStyleSheet("""
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
        self.overall_pbar.setValue(0)
        self.overall_pbar.setFormat("Overall Progress: 0%")
        layout.addWidget(self.overall_pbar)

        # --- 3. Footer and Control Buttons ---
        footer_layout = QHBoxLayout()
        
        self.playlist_status_lbl = QLabel(f"Video 1 of {self.total_videos}")
        self.playlist_status_lbl.setStyleSheet("color: #a6e3a1; font-weight: bold; font-size: 13px;")
        
        self.cancel_btn = QPushButton("Cancel Playlist ❌")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton { background-color: #f38ba8; color: #11111b; font-weight: bold; border-radius: 6px; padding: 5px 15px; }
            QPushButton:hover { background-color: #eba0ac; }
        """)
        self.cancel_btn.clicked.connect(self.on_cancel)
        
        footer_layout.addWidget(self.playlist_status_lbl)
        footer_layout.addStretch()
        footer_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(footer_layout)

        QTimer.singleShot(500, self.download_next)

    def update_overall_progress(self):
        percent = int((self.current_index / self.total_videos) * 100)
        self.overall_pbar.setValue(percent)
        self.overall_pbar.setFormat(f"Overall Progress: {percent}%")

    def download_next(self):
        if self.is_cancelled: return
        
        self.update_overall_progress()

        if self.current_index >= self.total_videos:
            self.finish_playlist()
            return

        current_video = self.video_list[self.current_index]
        self.playlist_status_lbl.setText(f"Video {self.current_index + 1} of {self.total_videos}")
        self.current_vid_lbl.setText(f"<b>🔄 Current Task:</b> Fetching Info for: {current_video['title'][:35]}... ⏳")
        
        self.info_fetcher = YTInfoFetcher(current_video['url'])
        self.info_fetcher.finished.connect(self.on_info_fetched)
        self.info_fetcher.error.connect(self.on_info_error)
        self.info_fetcher.start()

    def on_info_fetched(self, info):
        if self.is_cancelled: return
        
        self.current_vid_lbl.setText(f"<b>🔄 Current Task:</b> Downloading Video {self.current_index + 1}...")
        
        from ui_components import DownloadProgressDialog
        self.current_dl_dlg = DownloadProgressDialog(info, self.format_code, self.quality_name, self.dl_options, self.parent())
        
        tracker_geom = self.geometry()
        self.current_dl_dlg.move(tracker_geom.right() + 15, tracker_geom.top())
        
        self.current_dl_dlg.worker.finished_signal.connect(self.on_single_success)
        self.current_dl_dlg.rejected.connect(self.on_single_rejected)
        
        self.current_dl_dlg.show()

    def on_single_success(self):
        if self.is_cancelled: return
        QTimer.singleShot(1500, self.close_current_and_next)

    def close_current_and_next(self):
        if self.current_dl_dlg:
            try: self.current_dl_dlg.rejected.disconnect(self.on_single_rejected)
            except: pass
            self.current_dl_dlg.hide()
            self.current_dl_dlg.deleteLater()
            self.current_dl_dlg = None
        
        self.current_index += 1
        self.download_next()

    def on_single_rejected(self):
        if self.is_cancelled: return
        self.current_dl_dlg = None
        self.current_index += 1
        self.download_next()

    def on_info_error(self, err):
        if self.is_cancelled: return
        self.current_vid_lbl.setText(f"<b>⚠️ Error:</b> Skipping to next video...")
        self.current_index += 1
        QTimer.singleShot(1500, self.download_next)

    def finish_playlist(self):
        self.overall_pbar.setValue(100)
        self.overall_pbar.setFormat("Overall Progress: 100% Done")
        self.overall_pbar.setStyleSheet("""
            QProgressBar { border: 2px solid #313244; border-radius: 10px; text-align: center; height: 35px; background: #1e1e2e; color: #11111b; font-weight: bold; font-size: 13px; }
            QProgressBar::chunk { background-color: #a6e3a1; border-radius: 8px; }
        """)
        
        self.playlist_status_lbl.setText("✅ Complete!")
        self.current_vid_lbl.setText("<b>🔄 Status:</b> All selected videos downloaded successfully.")
        self.current_vid_lbl.setStyleSheet("color: #a6e3a1; font-weight: bold;")
        self.cancel_btn.setText("Close")
        self.cancel_btn.clicked.disconnect()
        self.cancel_btn.clicked.connect(self.accept)

    def request_cancel(self):
        if self.is_cancelled or self.current_index >= self.total_videos:
            return True

        dlg = QDialog(self)
        dlg.setWindowTitle("Confirm Cancel")
        dlg.setFixedSize(360, 150)
        dlg.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")
        layout = QVBoxLayout(dlg)
        
        lbl = QLabel("Are you sure you want to cancel the ENTIRE playlist download?")
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(lbl)
        
        btn_layout = QHBoxLayout()
        btn_yes = QPushButton("Yes, Stop All")
        btn_no = QPushButton("No, Continue")
        
        btn_yes.setStyleSheet("background: #f38ba8; color: #11111b; font-weight: bold; padding: 8px; border-radius: 4px;")
        btn_no.setStyleSheet("background: #a6e3a1; color: #11111b; font-weight: bold; padding: 8px; border-radius: 4px;")
        
        res = [False]
        def set_yes(): res[0] = True; dlg.accept()
        def set_no(): res[0] = False; dlg.accept()
        
        btn_yes.clicked.connect(set_yes)
        btn_no.clicked.connect(set_no)
        
        btn_layout.addWidget(btn_yes)
        btn_layout.addWidget(btn_no)
        layout.addLayout(btn_layout)
        
        dlg.exec()
        
        if res[0]:
            self.is_cancelled = True
            self.current_vid_lbl.setText("<b>🔄 Status:</b> Cancelling...")
            self.current_vid_lbl.setStyleSheet("color: #f38ba8; font-weight: bold;")
            if self.current_dl_dlg:
                self.current_dl_dlg.worker.abort(delete_parts=True)
                self.current_dl_dlg.worker.wait()
                try: self.current_dl_dlg.rejected.disconnect(self.on_single_rejected)
                except: pass
                self.current_dl_dlg.hide()
                self.current_dl_dlg.deleteLater()
                self.current_dl_dlg = None
            return True
        return False

    def on_cancel(self):
        if self.request_cancel():
            self.accept()

    def reject(self):
        if self.request_cancel():
            super().reject()

    def closeEvent(self, event):
        if self.request_cancel():
            event.accept()
        else:
            event.ignore()