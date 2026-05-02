# 🎬 HardPlayer (v4.0) — The System Integration Update

A lightweight, high-performance video player built with **Python**, **PyQt6**, and the legendary **MPV Engine**. Compiled into a native binary using **Nuitka** to ensure maximum performance, instant startup, and a minimal footprint on Linux.

![License](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Linux%20-lightgrey)
![Version](https://img.shields.io/badge/Version-4.0.0-mauve)

## 🚀 What's New in v4.0?
- **Full System Integration (MPRIS2):** Simply put, your operating system now recognizes HardPlayer like any other major media player. 
  - **Keyboard Media Keys:** You can now use the physical Play, Pause, Next, and Previous buttons on your keyboard.
  - **Remote Control (KDE Connect / Mobile):** Control your videos directly from your phone or smartwatch. Perfect for pausing a movie from the couch!
  - **System Notifications:** See the current playing video title and YouTube thumbnails right in your desktop's volume/media controller.

## 🛠️ Core Features
- **Advanced YouTube Quality Selector:** Fetch all available YouTube streams (IDs, Resolution, FPS, Codecs) in a dedicated GUI and pick the exact combination (e.g., `299+140`) that suits your hardware.
- **Smart Hardware Acceleration:** Native support for Intel, AMD, and NVIDIA. Special optimization for **NVIDIA Maxwell** cards using `nvdec-copy`.
- **MPV Engine Core:** Flawless multi-format support via `libmpv`.
- **Wayland & X11 Seamless Integration:** Forces strict X11/EGL contexts to prevent detached windows on Wayland compositors like **Hyprland** or **Sway**.
- **Intelligent Fallback:** Built-in observer that detects if your GPU lacks support for a specific codec and gracefully falls back to CPU decoding.
- **Catppuccin-Inspired UI:** A clean, dark interface (`#1e1e2a`) that focuses on the content, not the clutter.

## 🐧 Linux Exclusive
HardPlayer is built by a Linux user, for Linux users. It is deeply integrated with Linux-specific technologies (like MPRIS, Wayland/X11 workarounds, and specific GPU drivers). **There are currently no plans to support Windows.**

## 📥 Installation & Usage

### ⚡ Try it Instantly (No Installation)
Want to test it out right now without downloading any packages? Run this single command in your terminal:
```bash
curl -sSL https://raw.githubusercontent.com/ahmed-x86/hardplayer/refs/heads/main/hardplayer.py | python3
```

### For Arch Linux (The Way):
If you downloaded the `.zst` package from the releases:
```bash
sudo pacman -U hardplayer-4.0.0.pkg.tar.zst
```

### Build from Source:
```bash
# Clone and install Python dependencies (including the new D-Bus integration tools)
pip install PyQt6 python-mpv nuitka zstandard ordered-set dbus-python PyGObject

# Compile to a native binary
python -m nuitka --standalone --remove-output --enable-plugin=pyqt6 --assume-yes-for-downloads hardplayer.py
```

## 📦 System Dependencies
HardPlayer requires these tools to be installed on your system:
- **mpv:** The core media engine (`libmpv`).
- **FFmpeg:** For backend decoding and info processing.
- **yt-dlp:** For fetching advanced YouTube stream metadata.

## ⌨️ Keyboard Shortcuts
- **`P`** : Open Media Selection (Local / YouTube).
- **`I`** : Show System FFmpeg & Version Information.

## 📜 License
Licensed under **GNU GPL v3**. Freedom for your software, power for your hardware.

---
**Developed with ☕ and Linux by:** [ahmed-x86](https://github.com/ahmed-x86)  
*"Keep it simple, keep it fast."*
