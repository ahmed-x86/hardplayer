# 🎬 HardPlayer (v11.0.0) — Power User CLI & Fast Launch 🚀💻

A lightweight, high-performance modular media player built with **Python**, **PyQt6**, and the **MPV Engine**. Version 11.0.0 transforms HardPlayer into a Power User's dream, introducing a robust Command Line Interface (CLI) that allows you to bypass UI dialogs, force hardware decoding, and search YouTube directly from your terminal, all while maintaining its minimalistic, **Catppuccin Mocha** aesthetic.

Built for Linux ricing enthusiasts who demand both beauty and performance. Compiled into a native binary using **Nuitka**.

![License](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Linux%20-lightgrey)
![Version](https://img.shields.io/badge/Version-11.0.0-mauve)
![Theme](https://img.shields.io/badge/Theme-Catppuccin%20Mocha-blue)

## ✨ What's New in v11.0?
- **Power User CLI:** Full terminal control! Launch media, search YouTube, and force hardware decoding directly from your command line.
- **Fast Launch (UI Bypass):** Skip the startup and decoding dialogs entirely. Inject your preferences via arguments to instantly blast media straight to the MPV engine.
- **Advanced HWDEC Mapping:** New custom device map including `-device old_nvidia` (maps to `cuda-copy`) for perfect hardware acceleration compatibility with older GPUs.
- **Audio-Only Mode:** Save RAM and bandwidth by playing YouTube videos as music/podcasts using the `-quality audio` flag.
- **Rich MPRIS Metadata (v10 Legacy):** Full integration with Linux desktop environments (Waybar, SwayNC) with **Cover Art / Thumbnails** caching.

## 💻 CLI Documentation (v11 Power User Mode)
HardPlayer v11 introduces a powerful terminal interface. You can mix and match flags to bypass UI dialogs entirely.

### Available Flags:
* `-device [cpu|intel|amd|nvidia|old_nvidia]` : Forces hardware decoding. (`old_nvidia` uses `cuda-copy` for legacy GPU compatibility).
* `-quality [best|1080p|720p|480p|audio]` : Forces YouTube resolution. `audio` plays as a music stream without video.
* `-search` : Treats the input path as a YouTube search query.

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

## 🎨 UI & Philosophy
- **Catppuccin Mocha:** A professional, eye-friendly dark interface.
- **KISS Control Bar:** Following the "Keep It Simple, Stupid" philosophy, the top menu bar is gone. All essential controls are consolidated into a sleek bottom bar.
- **Advanced Repeat Logic:** A dedicated smart-toggle button for looping. 
    - **🔁 ✔️ (Green):** Infinite loop enabled via MPV core.
    - **🔁 ✖ (Red):** Play once and stop.
- **Premium Progress Bar:** The seek bar features a gold-tinted (`#e9d4a4`) "sub-page" highlight for clear, elegant visual feedback.

## 🛠️ Core Features
- **Flawless Keyboard Navigation:** Focus-stealing issues resolved. Left/Right arrow keys flawlessly seek (±5 seconds). Native support for standard and hardware media keys (F7, F8, F9 fallbacks included).
- **Advanced MPRIS2 Support:** Unmatched native Linux integration. Control your media and view stunning cover art via system trays, Waybar, or **KDE Connect**.
- **Hardware Acceleration Mastery:** Specialized support for **NVIDIA (NVDEC)**, Intel, and AMD GPUs. Graceful CPU fallback if the GPU encounters an unsupported codec.
- **Wayland-Native Performance:** Optimized for compositors like **Hyprland** and **Sway** with forced X11/EGL contexts where necessary to ensure window stability.

## 🐧 The Linux Spirit
HardPlayer is and will always be **Linux-exclusive**. It leverages native Linux technologies to provide a level of integration that cross-platform players simply can't match.

## 📥 Installation

### Arch Linux (Pacman):
```bash
sudo pacman -U hardplayer-11.0.0.pkg.tar.zst
```

### Debian/Ubuntu (DEB):
```bash
sudo dpkg -i hardplayer_11.0.0_amd64.deb
```

### Development Run:
```bash
git clone https://github.com/ahmed-x86/hardplayer.git
cd hardplayer
python3 hardplayer.py
```

## ⌨️ Keyboard Shortcuts
- **`P`** : Open Media Selection / YouTube Search.
- **`I`** : Show System FFmpeg & Hardware Info.
- **`Left / Right Arrows`** : Seek -5 / +5 seconds.
- **`Media Keys (or F7/F8/F9)`** : Previous / Play-Pause / Next.
- **`Space`** : Play / Pause (Native MPV).

## 📦 Requirements
Ensure you have the following installed on your system:
- `mpv` (libmpv)
- `ffmpeg` (required for thumbnail generation and media processing)
- `yt-dlp`

## 📜 License
Licensed under **GNU GPL v3**. Open source, privacy-focused, and community-driven.

---
**Developed with ☕ and Arch Linux by:** [ahmed-x86](https://github.com/ahmed-x86)  
*"Keep it simple, keep it elegant, keep it fast."*