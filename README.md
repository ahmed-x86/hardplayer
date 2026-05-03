# 🎬 HardPlayer (v10.0.0) — MPRIS Art & Desktop Integration 🖼️✨

A lightweight, high-performance modular media player built with **Python**, **PyQt6**, and the **MPV Engine**. Version 10.0.0 brings HardPlayer closer to your system than ever before with deep MPRIS2 integration, featuring native cover art and smart local caching, all while maintaining its minimalistic, **Catppuccin Mocha** aesthetic.

Built for Linux ricing enthusiasts who demand both beauty and performance. Compiled into a native binary using **Nuitka**.

![License](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Linux%20-lightgrey)
![Version](https://img.shields.io/badge/Version-10.0.0-mauve)
![Theme](https://img.shields.io/badge/Theme-Catppuccin%20Mocha-blue)

## ✨ What's New in v10.0?
- **Rich MPRIS Metadata:** Full integration with Linux desktop environments (Waybar, SwayNC, KDE, GNOME). HardPlayer now seamlessly sends **Cover Art / Thumbnails** to your system widgets for both local and online media.
- **Lightning-Fast Local Thumbnails:** Automatically extracts a high-quality frame from local videos using an optimized `ffmpeg` fast-seek strategy, ensuring zero UI freezing or playback stutter.
- **Smart Thumbnail Caching:** Extracted local thumbnails are securely hashed and cached to `~/.cache/hardplayer/thumbnails`, guaranteeing zero CPU overhead when replaying your favorite videos.
- **YouTube Artwork Integration:** Directly fetches and displays high-quality YouTube thumbnails in your system's media widget when streaming online content.
- **Legacy v9 Search Engine:** Retains the lightning-fast, native YouTube search engine built entirely around `yt-dlp`'s `--flat-playlist` capability, complete with visual Catppuccin-themed result cards.

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
- **Advanced MPRIS2 Support:** Unmatched native Linux integration. Control your media and view stunning cover art via system trays, Waybar, or **KDE Connect**.
- **Hardware Acceleration Mastery:** Specialized support for **NVIDIA (NVDEC)**, Intel, and AMD GPUs. Graceful CPU fallback if the GPU encounters an unsupported codec.
- **Wayland-Native Performance:** Optimized for compositors like **Hyprland** and **Sway** with forced X11/EGL contexts where necessary to ensure window stability.

## 🐧 The Linux Spirit
HardPlayer is and will always be **Linux-exclusive**. It leverages native Linux technologies to provide a level of integration that cross-platform players simply can't match.

## 📥 Installation

### Arch Linux (Pacman):
```bash
sudo pacman -U hardplayer-10.0.0.pkg.tar.zst
```

### Debian/Ubuntu (DEB):
```bash
sudo dpkg -i hardplayer_10.0.0_amd64.deb
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
Ensure you have the following installed on your system:
- `mpv` (libmpv)
- `ffmpeg` (required for thumbnail generation and media processing)
- `yt-dlp`

## 📜 License
Licensed under **GNU GPL v3**. Open source, privacy-focused, and community-driven.

---
**Developed with ☕ and Arch Linux by:** [ahmed-x86](https://github.com/ahmed-x86)  
*"Keep it simple, keep it elegant, keep it fast."*