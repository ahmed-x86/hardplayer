# 🎬 HardPlayer (15.0.0) — The Modular Refactor

HardPlayer is a lightweight, high-performance modular media player built with **Python**, **PyQt6**, and the **MPV Engine**. It combines native system integration with a robust Command Line Interface (CLI) and a sleek **Catppuccin Mocha** aesthetic.

Developed by **Ahmed (ahmed-x86)**, a Cybersecurity and Computer Science student, this player is designed specifically for the Linux ecosystem, prioritizing the "KISS" (Keep It Simple, Stupid) philosophy and extreme performance.

---

## ✨ What's New in v15.0?

The v15 update represents a complete architectural overhaul to improve maintainability and user experience.

### 🧩 Modular Architecture Refactoring
* **Decoupled Logic**: The previously monolithic `main_window.py` has been dismantled into specialized modules.
* **Playback Manager**: A new `playback_manager.py` handles all MPV instance states and engine logic independently from the UI thread.
* **CLI Handler**: Startup logic and terminal command processing are now managed via `cli_handler.py`.
* **Ease of Maintenance**: This separation of concerns ensures that the application remains fast and easier to update in the future.

### 📺 Dynamic YouTube Quality Flow
* **Simplified UI**: A new user-friendly dialog automatically detects and displays only the actual resolutions available for a specific YouTube video.
* **Advanced Mode**: Retains full control for power users, allowing for manual format code input (e.g., `137+140`) after exploring full format lists.
* **Smart Selection**: Users can choose from 144p up to the highest available quality with a single click, or opt for "Audio Only" to save bandwidth.

---

## ✨ Previous Highlights (v14.0)
* **Floating Playlist Overlay (📜)**: A translucent sidebar for managing media within the player window without disrupting the 16:9 aspect ratio.
* **Lazy Loading Engine (⚡)**: Intelligently loads media in batches of 6 to eliminate UI freezing when opening large directories.
* **Hardware Caching**: Automatically saves GPU preferences in `~/.cache/hardplayer/hw.txt` for persistent configuration.
* **Improved Thumbnails**: Enhanced caching logic for extracting local video thumbnails with higher precision.

---

## 💻 CLI Documentation
HardPlayer features a powerful terminal interface for bypassing UI dialogs.

### Available Flags:
* `-device [cpu|intel|amd|nvidia|old_nvidia]`: Forces specific hardware decoding backends.
* `-quality [best|1080p|720p|480p|audio]`: Forces YouTube streaming resolution.
* `-search`: Treats input as a YouTube search query rather than a direct URL.

### Usage Example:
```bash
# Launch a YouTube search directly for 1080p playback on an NVIDIA GPU
hardplayer -search "Linux Ricing" -quality 1080p -device nvidia
```

---

## 🛠️ Core Features & Philosophy
* **Catppuccin Mocha**: A professional dark theme designed for eye comfort.
* **Wayland-Native**: Optimized for compositors like **Hyprland** with forced X11/EGL contexts for maximum stability.
* **Hardware Mastery**: Specialized support for NVDEC, Intel, and AMD with graceful CPU fallbacks.
* **Rich MPRIS Metadata**: Full integration with Waybar, SwayNC, and system trays including cover art caching.

---

## 📥 Installation

### Arch Linux (Pacman):
```bash
sudo pacman -U hardplayer-15.0.0.pkg.tar.zst
```

### Debian/Ubuntu (DEB):
```bash
sudo dpkg -i hardplayer_15.0.0_amd64.deb
```

## 📦 Requirements
Ensure the following are installed:
* `mpv` (libmpv)
* `ffmpeg`
* `yt-dlp`

---
**Developed with ☕ and Arch Linux by:** [ahmed-x86](https://github.com/ahmed-x86)  
*"Keep it simple, keep it elegant, keep it fast."*