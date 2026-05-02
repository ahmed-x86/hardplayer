# 🎬 HardPlayer (v5.0) — The Modular Rebuild

A lightweight, high-performance video player built with **Python**, **PyQt6**, and the legendary **MPV Engine**. Following the KISS philosophy, v5.0 introduces a fully modular architecture. Compiled into a native binary using **Nuitka** to ensure maximum performance, instant startup, and a minimal footprint on Linux.

![License](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Linux%20-lightgrey)
![Version](https://img.shields.io/badge/Version-5.0.0-mauve)

## 🚀 What's New in v5.0?
- **Modular KISS Architecture:** The massive monolithic codebase has been dismantled into logical, easily maintainable components (`config`, `ui`, `mpris`, `youtube`, `hw_decoding`).
- **Enhanced Nuitka Compilation:** Build processes have been updated to seamlessly trace and bundle the new multi-file structure into a single, highly-optimized standalone binary.
- **Stable Integrations (Retained from v4):** Full system MPRIS2 integration (KDE Connect), Hardware Decoding fallbacks, and advanced YouTube `yt-dlp` parsing remain fully intact and faster than ever.

## 🛠️ Core Features
- **Advanced YouTube Quality Selector:** Fetch all available YouTube streams (IDs, Resolution, FPS, Codecs) in a dedicated GUI and pick the exact combination (e.g., `299+140`) that suits your hardware.
- **Full System Integration (MPRIS2):** Your operating system recognizes HardPlayer natively. Control playback via keyboard media keys, system notifications, or remote tools like KDE Connect.
- **Smart Hardware Acceleration:** Native support for Intel, AMD, and NVIDIA. Special optimization for **NVIDIA Maxwell** cards using `nvdec-copy`.
- **MPV Engine Core:** Flawless multi-format support via `libmpv`.
- **Wayland & X11 Seamless Integration:** Forces strict X11/EGL contexts to prevent detached windows on Wayland compositors like **Hyprland** or **Sway**.
- **Intelligent Fallback:** Built-in observer that detects if your GPU lacks support for a specific codec and gracefully falls back to CPU decoding.
- **Catppuccin-Inspired UI:** A clean, dark interface (`#1e1e2a`) that focuses on the content, not the clutter.

## 🐧 Linux Exclusive
HardPlayer is built by a Linux user, for Linux users. It is deeply integrated with Linux-specific technologies (like MPRIS, Wayland/X11 workarounds, and specific GPU drivers). **There are currently no plans to support Windows.**

## 📥 Installation & Usage

### For Arch Linux (The Way):
If you downloaded the `.zst` package from the GitHub releases:
```bash
sudo pacman -U hardplayer-5.0.0.pkg.tar.zst
```

### Run Locally (Development):
Since HardPlayer v5 is modular, you need to clone the repository to run it via Python directly:
```bash
git clone https://github.com/ahmed-x86/hardplayer.git
cd hardplayer
python3 hardplayer.py
```

### Build from Source:
```bash
# Install Python dependencies (including the D-Bus integration tools)
pip install PyQt6 python-mpv nuitka zstandard ordered-set dbus-python PyGObject

# Compile to a native binary (Note the --follow-imports flag for the new modular structure)
python -m nuitka --standalone --remove-output --enable-plugin=pyqt6 --follow-imports --assume-yes-for-downloads hardplayer.py
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
