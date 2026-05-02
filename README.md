# 🎬 HardPlayer (v3.0) — YouTube Master Edition

A lightweight, high-performance video player built with **Python**, **PyQt6**, and the legendary **MPV Engine**. Compiled into a native binary using **Nuitka** to ensure maximum performance, instant startup, and a minimal footprint on Linux.

![License](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Linux%20-lightgrey)
![Version](https://img.shields.io/badge/Version-3.0.0-mauve)

## 🚀 What's New in v3.0?
- **Advanced YouTube Quality Selector:** Unlike standard players, HardPlayer now gives you total control. Fetch all available YouTube streams (IDs, Resoltuion, FPS, Codecs) in a dedicated GUI and pick the exact combination (e.g., `299+140`) that suits your hardware.
- **Enhanced Decoding Logic:** Interactive selection of hardware acceleration (`vaapi`, `nvdec`, `vdpau`) right after choosing your quality, ensuring a smooth 4K/60fps experience.
- **Improved Codec Transparency:** Real-time logging of the active Video Codec (H.264, VP9, AV1) to help you optimize playback for your specific GPU architecture.

## 🛠️ Core Features
- **MPV Engine Core:** Flawless multi-format support via `libmpv`.
- **Smart Hardware Acceleration:** Native support for Intel, AMD, and NVIDIA. Special optimization for **NVIDIA Maxwell** cards using `nvdec-copy`.
- **Wayland & X11 Seamless Integration:** Forces strict X11/EGL contexts to prevent detached windows on Wayland compositors like **Hyprland** or **Sway**.
- **Intelligent Fallback:** Built-in observer that detects if your GPU lacks support for a specific codec and gracefully falls back to CPU decoding.
- **Raw Performance:** Compiled to machine code via Nuitka for instant startup and low RAM usage.
- **Catppuccin-Inspired UI:** A clean, dark interface (`#1e1e2a`) that focuses on the content, not the clutter.

## 📦 System Dependencies
HardPlayer requires these tools to be installed on your system:
- **mpv:** The core media engine (`libmpv`).
- **FFmpeg:** For backend decoding and info processing.
- **yt-dlp:** For fetching advanced YouTube stream metadata.

## 📥 Installation & Usage

### For Arch Linux (The Way):
If you downloaded the `.zst` package from the releases:
```bash
sudo pacman -U hardplayer-3.0.0.pkg.tar.zst
```

### Build from Source:
```bash
# Clone and install Python dependencies
pip install PyQt6 python-mpv nuitka zstandard ordered-set

# Compile to a native binary
python -m nuitka --standalone --remove-output --enable-plugin=pyqt6 --assume-yes-for-downloads hardplayer.py
```

## ⌨️ Keyboard Shortcuts
- **`P`** : Open Media Selection (Local / YouTube).
- **`I`** : Show System FFmpeg & Version Information.

## 📜 License
Licensed under **GNU GPL v3**. Freedom for your software, power for your hardware.

---
**Developed with ☕ and Linux by:** [ahmed-x86](https://github.com/ahmed-x86)  
*"Keep it simple, keep it fast."*
