# 🎬 HardPlayer (v9.0.0) — The Search Revolution 🔍🚀

A lightweight, high-performance modular media player built with **Python**, **PyQt6**, and the **MPV Engine**. Version 9.0.0 introduces a lightning-fast, native YouTube search engine built entirely around `yt-dlp`, transforming HardPlayer into a standalone media discovery platform without sacrificing its minimalistic, **Catppuccin Mocha** aesthetic.

Built for Linux ricing enthusiasts who demand both beauty and performance. Compiled into a native binary using **Nuitka**.

![License](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Linux%20-lightgrey)
![Version](https://img.shields.io/badge/Version-9.0.0-mauve)
![Theme](https://img.shields.io/badge/Theme-Catppuccin%20Mocha-blue)

## ✨ What's New in v9.0?
- **Native YouTube Search:** You can now directly search YouTube from within the application. Entering a text query instead of a URL instantly fetches the top 5 results.
- **Lightning-Fast Parsing:** Powered by `yt-dlp`'s `--flat-playlist` capability, bypassing heavy metadata extraction to deliver search results in milliseconds.
- **Visual Result Cards:** Search results are displayed in beautifully designed, Catppuccin-themed cards featuring:
  - Asynchronously loaded thumbnails (Zero UI freezing via `QThread`).
  - Channel names, video durations, and formatted view counts.
  - Video description snippets.
- **Zero External Bloat:** Completely dropped unstable third-party search libraries (like `Youtube-python`), relying purely on reliable `yt-dlp` JSON extraction to avoid dependency hell.
- **Unified Media Dialog:** The `P` shortcut now serves as a universal hub for browsing local files, playing direct URLs, or exploring YouTube search queries.

## 🎨 UI & Philosophy
- **Catppuccin Mocha:** A professional, eye-friendly dark interface.
- **KISS Control Bar:** Following the "Keep It Simple, Stupid" philosophy, the top menu bar is gone. All essential controls are consolidated into a sleek bottom bar.
- **Advanced Repeat Logic:** A dedicated smart-toggle button for looping. 
    - **🔁 ✔️ (Green):** Infinite loop enabled via MPV core.
    - **🔁 ✖ (Red):** Play once and stop.
- **Premium Progress Bar:** The seek bar features a gold-tinted (`#e9d4a4`) "sub-page" highlight for clear, elegant visual feedback.

## 🛠️ Core Features
- **Flawless Keyboard Navigation:** Focus-stealing issues resolved. Left/Right arrow keys flawlessly seek (±5 seconds). Native support for standard and hardware media keys (F7, F8, F9 fallbacks included).
- **Dynamic Time Formatting:** Adaptive UI that smartly transitions to `HH:MM:SS` for long videos.
- **Full MPRIS2 Support:** Native Linux integration. Control your media via system trays, Waybar, or **KDE Connect**.
- **Hardware Acceleration Mastery:** Specialized support for **NVIDIA (NVDEC)**, Intel, and AMD. Graceful CPU fallback if the GPU encounters an unsupported codec.
- **Wayland-Native Performance:** Optimized for compositors like **Hyprland** and **Sway** with forced X11/EGL contexts where necessary to ensure window stability.

## 🐧 The Linux Spirit
HardPlayer is and will always be **Linux-exclusive**. It leverages native Linux technologies to provide a level of integration that cross-platform players simply can't match.

## 📥 Installation

### Arch Linux (Pacman):
```bash
sudo pacman -U hardplayer-9.0.0.pkg.tar.zst
```

### Debian/Ubuntu (DEB):
```bash
sudo dpkg -i hardplayer_9.0.0_amd64.deb
```

### Development Run:
```bash
git clone [https://github.com/ahmed-x86/hardplayer.git](https://github.com/ahmed-x86/hardplayer.git)
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
Ensure you have the following installed:
- `mpv` (libmpv)
- `ffmpeg`
- `yt-dlp`

## 📜 License
Licensed under **GNU GPL v3**. Open source, privacy-focused, and community-driven.

---
**Developed with ☕ and Arch Linux by:** [ahmed-x86](https://github.com/ahmed-x86)  
*"Keep it simple, keep it elegant, keep it fast."*