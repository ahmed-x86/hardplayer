# 🎬 HardPlayer (v6.0.0) — The UI Revolution 🚀

A lightweight, high-performance modular media player built with **Python**, **PyQt6**, and the **MPV Engine**. Version 6.0.0 marks a total visual overhaul, bringing a premium **Catppuccin Mocha** aesthetic and a streamlined **VLC-inspired** control logic. 

Built for Linux ricing enthusiasts who demand both beauty and performance. Compiled into a native binary using **Nuitka**.

![License](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Linux%20-lightgrey)
![Version](https://img.shields.io/badge/Version-6.0.0-mauve)
![Theme](https://img.shields.io/badge/Theme-Catppuccin%20Mocha-blue)

## 🎨 What's New in v6.0?
- **Total UI Redesign:** Implemented the **Catppuccin Mocha** palette for a professional, eye-friendly dark interface.
- **KISS Control Bar:** Following the "Keep It Simple, Stupid" philosophy, the top menu bar has been removed. All essential controls are now consolidated into a sleek, unified bottom bar.
- **Advanced Repeat Logic:** A dedicated smart-toggle button for looping. 
    - **🔁 ✔️ (Green):** Infinite loop enabled via MPV core.
    - **🔁 ✖ (Red):** Play once and stop.
- **Premium Progress Bar:** The seek bar now features a gold-tinted (`#e9d4a4`) "sub-page" highlight, providing clear visual feedback of the played duration with a touch of elegance.
- **Modular Stability:** Refined the modular architecture introduced in v5, ensuring even faster startup times and lower resource usage.

## 🛠️ Core Features
- **Advanced YouTube Stream Parsing:** Integrated `yt-dlp` GUI to pick specific resolutions and codecs (e.g., `303+140`).
- **Full MPRIS2 Support:** Native Linux integration. Control your media via system trays, lock screens, or **KDE Connect**.
- **Hardware Acceleration Mastery:** Specialized support for **NVIDIA (NVDEC)**, Intel, and AMD.
- **Intelligent Fallback:** Real-time monitoring that gracefully switches to CPU decoding if the GPU encounters an unsupported codec.
- **Wayland-Native Performance:** Optimized for compositors like **Hyprland** and **Sway** with forced X11/EGL contexts where necessary to ensure window stability.

## 🐧 The Linux Spirit
HardPlayer is and will always be **Linux-exclusive**. It leverages native Linux technologies to provide a level of integration that cross-platform players simply can't match.

## 📥 Installation

### Arch Linux (Pacman):
```bash
sudo pacman -U hardplayer-6.0.0.pkg.tar.zst
```

### Debian/Ubuntu (DEB):
```bash
sudo dpkg -i hardplayer_6.0.0_amd64.deb
```

### Development Run:
```bash
git clone https://github.com/ahmed-x86/hardplayer.git
cd hardplayer
python3 hardplayer.py
```

## ⌨️ Keyboard Shortcuts
- **`P`** : Open Media Selection (Local / YouTube).
- **`I`** : Show System FFmpeg & Hardware Info.
- **`Space`** : Play / Pause (Native MPV).

## 📦 Requirements
Ensure you have the following installed:
- `mpv` (libmpv)
- `ffmpeg`
- `yt-dlp`

## 📜 License
Licensed under **GNU GPL v3**. Open source, privacy-focused, and community-driven.

---
**Developed with ☕ and Arch Linux by:** [ahmed-x86](https://github.com/ahmed-x86)  
*"Keep it simple, keep it elegant, keep it fast."*
