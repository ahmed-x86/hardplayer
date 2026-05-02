# 🎬 HardPlayer (v8.0.0) — The Polish Update ✨🚀

A lightweight, high-performance modular media player built with **Python**, **PyQt6**, and the **MPV Engine**. Version 8.0.0 focuses on rock-solid stability, UX refinement, and precise keyboard navigation, building upon the premium **Catppuccin Mocha** aesthetic introduced in earlier versions. 

Built for Linux ricing enthusiasts who demand both beauty and performance. Compiled into a native binary using **Nuitka**.

![License](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Linux%20-lightgrey)
![Version](https://img.shields.io/badge/Version-8.0.0-mauve)
![Theme](https://img.shields.io/badge/Theme-Catppuccin%20Mocha-blue)

## ✨ What's New in v8.0?
- **Flawless Keyboard Navigation:** Resolved UI focus-stealing issues. Left/Right arrow keys now seamlessly seek (±5 seconds) using MPV's native relative seeking without glitching the progress bar.
- **Hardware-Resilient Media Keys:** Added robust support for global media keys, including smart fallbacks (F7, F8, F9) to bypass hardware limitations on workstation laptops (like HP ZBooks) that fail to pass standard `XF86Audio` events.
- **Dynamic Time Formatting:** The time label now automatically adapts to display hours (`HH:MM:SS`) for long videos, completely fixing the UI stylesheet leakage that caused visual artifacts.
- **Smart Playlist Wrapping:** Hitting "Next" on the last video or "Previous" on the first video now intelligently loops around the local directory playlist.
- **Graceful Stop Logic:** The Stop (`⏹`) button now immediately terminates the MPV engine and smoothly returns you to the branded logo screen.
- **Clickable Slider:** A custom-built `ClickableSlider` allows for instant "jump-to-click" progress tracking.

## 🎨 UI & Philosophy
- **Catppuccin Mocha:** A professional, eye-friendly dark interface.
- **KISS Control Bar:** Following the "Keep It Simple, Stupid" philosophy, the top menu bar is gone. All essential controls are consolidated into a sleek bottom bar.
- **Advanced Repeat Logic:** A dedicated smart-toggle button for looping. 
    - **🔁 ✔️ (Green):** Infinite loop enabled via MPV core.
    - **🔁 ✖ (Red):** Play once and stop.
- **Premium Progress Bar:** The seek bar features a gold-tinted (`#e9d4a4`) "sub-page" highlight for clear, elegant visual feedback.

## 🛠️ Core Features
- **Advanced YouTube Stream Parsing:** Integrated `yt-dlp` GUI to pick specific resolutions and codecs (e.g., `303+140`).
- **Full MPRIS2 Support:** Native Linux integration. Control your media via system trays, Waybar, or **KDE Connect**.
- **Hardware Acceleration Mastery:** Specialized support for **NVIDIA (NVDEC)**, Intel, and AMD.
- **Intelligent Fallback:** Real-time monitoring that gracefully switches to CPU decoding if the GPU encounters an unsupported codec.
- **Wayland-Native Performance:** Optimized for compositors like **Hyprland** and **Sway** with forced X11/EGL contexts where necessary to ensure window stability.

## 🐧 The Linux Spirit
HardPlayer is and will always be **Linux-exclusive**. It leverages native Linux technologies to provide a level of integration that cross-platform players simply can't match.

## 📥 Installation

### Arch Linux (Pacman):
```bash
sudo pacman -U hardplayer-8.0.0.pkg.tar.zst
```

### Debian/Ubuntu (DEB):
```bash
sudo dpkg -i hardplayer_8.0.0_amd64.deb
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
- **`Left / Right Arrows`** : Seek -5 / +5 seconds.
- **`Media Keys (or F7/F8/F9)`** : Previous / Play-Pause / Next.
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
