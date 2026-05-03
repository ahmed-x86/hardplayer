# 🎬 HardPlayer (17.0.0) — Smart Formats & Unified UI

HardPlayer is a lightweight, high-performance modular media player built with **Python**, **PyQt6**, and the **MPV Engine**. It combines native system integration with a sleek **Catppuccin Mocha** aesthetic and a pro-grade YouTube acquisition engine.

Developed by **Ahmed (ahmed-x86)**, this player follows the "KISS" philosophy, specifically optimized for the Arch Linux ecosystem.

---

## ✨ What's New in v17.0?
* **Preferred YouTube Extension**: Set your default format (`mp4`, `mkv`, `webm`) from the Top Menu. HardPlayer remembers your choice natively via local cache.
* **Smart Format Fallback**: Automatically detects available formats and displays dynamic fallback notes directly on the UI (e.g., `(webm because not found mp4)`).
* **Unified Advanced UI**: The advanced download dialog now features the same beautiful, information-rich table UI as the streaming menu, operating in a seamless "Download Mode".

## 📥 Pro YouTube Downloader (Added in v16.0)
* **Aria2 Acceleration**: Integrated `aria2c` support for multi-threaded acquiring (16 parallel connections), bypassing YouTube's speed throttling.
* **Real-time Analytics**: A dedicated progress window showing live speed (MiB/s), total file size, and exact "Time Left" (ETA).
* **Full Metadata Extraction**: Automatically fetches and displays Channel name, Publication date, Like counts, and Comment counts for every video.
* **Dynamic Format Selection**: Choose between simple quality presets or **Advanced Mode** to input specific Video/Audio Stream IDs for custom merges.

## 🎨 Refined Progress UI
* **Catppuccin Aesthetics**: Progress bars now feature the signature **Catppuccin Green** bar with **Mauve (#cba6f7)** text metrics for maximum readability and style.
* **ANSI-Clean Logic**: New internal filtering to remove messy terminal color codes, ensuring only clean text appears in the UI.

---

## 🧩 Previous Highlights (v15.0)
* **Modular Refactor**: Decoupled `playback_manager.py` and `cli_handler.py` to ensure the UI thread remains 100% lag-free.
* **Dynamic Quality Flow**: A smart dialog that detects actual available resolutions for any YouTube video before playback.
* **Lazy Loading Engine**: batches of 6 media items are loaded to prevent freezes in large directories.

---

## 🛠️ Development & Quick Run (New!)
HardPlayer provides easy methods for testing and development:

**clone the repo**
```bash
git clone https://github.com/ahmed-x86/hardplayer.git
cd hardplayer
python hardplayer.py
```
---

## 💻 CLI Documentation
HardPlayer's terminal interface remains the fastest way to launch media.

### Available Flags:
* `-device [cpu|intel|amd|nvidia]`: Force hardware decoding backends.
* `-quality [1080p|720p|480p|audio]`: Set YouTube streaming resolution.
* `-search`: Treat input as a YouTube search query.

### Usage Examples:

**1. Fast Launch (Local File + Hardware Decoding)**
*Bypasses the decoding dialog and launches the video immediately on the GPU.*
```bash
hardplayer /path/to/video.mp4 -device old_nvidia
```

**2. Fast Launch (YouTube + Quality + Decoding)**
*Bypasses all dialogs and streams the URL directly with the requested settings.*
```bash
hardplayer "https://www.youtube.com/watch?v=test" -quality 1080p -device old_nvidia
```

**3. Direct YouTube Search**
*Skips the startup dialog and jumps directly into the search results for the query.*
```bash
hardplayer -search "test"
```

**4. Audio-Only Mode (Podcasts)**
*Disables video output to drastically save RAM and bandwidth. Great for background listening.*
```bash
hardplayer "https://www.youtube.com/watch?v=test" -quality audio
```

**5. Combined Search & Fast Launch**
*Searches YouTube, and upon selecting a video, instantly plays it with the predefined settings without asking further questions.*
```bash
hardplayer -search "test" -quality 720p -device cpu
```

---

## 🛠️ Core Features & Philosophy
* **Wayland-Native**: Optimized for **Hyprland** with forced EGL contexts for stability.
* **Hardware Mastery**: Specialized support for NVDEC and VA-API with graceful fallbacks.
* **Rich MPRIS**: Seamless integration with Waybar, SwayNC, and system trays.

---

## 📥 Installation

### Arch Linux (Pacman):
```bash
sudo pacman -S aria2  # Required for high-speed downloads
sudo pacman -U hardplayer-17.0.0.pkg.tar.zst
```

### Debian/Ubuntu (DEB):
```bash
sudo apt install aria2
sudo dpkg -i hardplayer_17.0.0_amd64.deb
```

## 📦 Requirements
Ensure the following are installed:
* `mpv` (libmpv)
* `ffmpeg`
* `yt-dlp`
* **`aria2`** (For accelerated downloads)

---
**Developed with ☕ and Arch Linux by:** [ahmed-x86](https://github.com/ahmed-x86)  
*"Keep it simple, keep it elegant, keep it fast."*