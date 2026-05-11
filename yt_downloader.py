# yt_downloader.py

import os 
import subprocess
import json
import re
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
from yt_url_parser import clean_youtube_url, clean_ansi

class DownloadWorker(QThread):
    progress_signal = pyqtSignal(dict)
    finished_signal = pyqtSignal()

    def __init__(self, url, format_id, dl_options=None):
        super().__init__()
        self.url = clean_youtube_url(url)
        self.format_id = format_id
        self.dl_options = dl_options or {}
        
        self._abort = False
        self._delete_parts = False
        self.process = None 
        self.downloaded_filepaths = set() 
        
        self.current_stream = "Video"
        self.video_size = "Unknown"
        self.audio_size = "Unknown"
        self.dest_count = 0

    def abort(self, delete_parts):
        self._abort = True
        self._delete_parts = delete_parts
        if self.process:
            self.process.terminate()

    def run(self):
        path_file = Path.home() / ".cache" / "hardplayer" / "download_path.txt"
        output_template = '%(title)s [%(id)s].%(ext)s' 
        target_dir = os.getcwd() 
        
        if path_file.exists():
            custom_path = path_file.read_text(encoding="utf-8").strip()
            if custom_path and os.path.exists(custom_path):
                target_dir = custom_path
                output_template = os.path.join(custom_path, '%(title)s [%(id)s].%(ext)s')

        self.state_file = os.path.join(target_dir, "hardplayer_resume_state.json")
        state_data = {
            "url": self.url,
            "format_id": self.format_id,
            "options": self.dl_options
        }
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f)
        except Exception as e:
            print(f"[*] ⚠️ Could not save resume state file: {e}")

        cmd = [
            "yt-dlp",
            "-f", self.format_id,
            "-o", output_template,
            "--newline",         
            "--ignore-errors",
            "--no-warnings"
        ]

        if self.dl_options.get('subs'):
            cmd.extend(["--write-subs", "--write-auto-subs"])
            lang = self.dl_options.get('sub_lang', 'en,ar')
            if lang:
                cmd.extend(["--sub-langs", lang])
            cmd.extend(["--convert-subs", "srt", "--embed-subs"])

        if self.dl_options.get('thumb'):
            cmd.extend(["--write-thumbnail", "--convert-thumbnails", "jpg", "--embed-thumbnail"])

        if self.dl_options.get('chapters'):
            cmd.extend(["--embed-chapters"])

        cmd.append(self.url)

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            progress_regex = re.compile(
                r'\[download\]\s+(?P<percent>[0-9\.]+)%\s+of\s+~?(?P<size>[0-9a-zA-Z\.]+)'
                r'(?:\s+at\s+(?P<speed>[0-9a-zA-Z\.]+/s))?(?:\s+ETA\s+(?P<eta>[0-9:]+))?'
            )
            
            dest_regex = re.compile(r'\[download\] Destination:\s+(.+)')
            merged_regex = re.compile(r'\[Merger\] Merging formats into \"(.+)\"')

            for line in self.process.stdout:
                if self._abort:
                    break

                line = clean_ansi(line)

                dest_match = dest_regex.search(line)
                if dest_match:
                    self.dest_count += 1
                    if self.dest_count == 1: 
                        self.current_stream = "Video"
                    elif self.dest_count == 2: 
                        self.current_stream = "Audio"
                    self.downloaded_filepaths.add(dest_match.group(1).strip())
                    continue

                merge_match = merged_regex.search(line)
                if merge_match:
                    self.downloaded_filepaths.add(merge_match.group(1).strip())
                    self.progress_signal.emit({'status': 'merging'})
                    continue
                    
                if "[ExtractAudio]" in line or "[Fixup" in line:
                    self.progress_signal.emit({'status': 'processing'})
                    continue

                match = progress_regex.search(line)
                if match:
                    percent_val = float(match.group('percent'))
                    total_size = match.group('size')

                    if self.current_stream == "Video": 
                        self.video_size = total_size
                    elif self.current_stream == "Audio": 
                        self.audio_size = total_size

                    clean_data = {
                        'status': 'downloading',
                        'percent': percent_val,
                        '_speed_str': match.group('speed') if match.group('speed') else 'N/A',
                        '_eta_str': match.group('eta') if match.group('eta') else '00:00',
                        '_total_bytes_str': total_size,
                        'current_stream': self.current_stream,
                        'video_size': self.video_size,
                        'audio_size': self.audio_size
                    }
                    self.progress_signal.emit(clean_data)

            self.process.wait()

            if self._abort:
                raise ValueError("DOWNLOAD_CANCELLED")
                
            if self.process.returncode in (0, 1):
                if hasattr(self, 'state_file') and os.path.exists(self.state_file):
                    try:
                        os.remove(self.state_file)
                    except Exception:
                        pass
                self.finished_signal.emit()

        except ValueError as e:
            if str(e) == "DOWNLOAD_CANCELLED":
                print("[*] 🛑 Download was manually cancelled.")
                if self._delete_parts:
                    for fpath in self.downloaded_filepaths:
                        for ext in ['', '.part', '.ytdl']:
                            f = fpath + ext
                            if os.path.exists(f):
                                try:
                                    os.remove(f)
                                except Exception:
                                    pass
        except Exception as e:
            print(f"[*] ⚠️ Download Worker Error: {e}")