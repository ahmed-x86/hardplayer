# 🎬 HardPlayer (v1.0)

A lightweight, high-performance video player built with **Python** and **PyQt6**, compiled into a native binary using **Nuitka** to ensure maximum performance and instant startup on Linux and Windows.

![License](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Linux%20-lightgrey)

## 🚀 Features
- **Raw Performance:** Instant startup and low memory footprint thanks to native compilation (Native ELF/EXE) via Nuitka.
- **Smart Aspect Ratio Container:** Custom UI container that eliminates raw black letterboxing, blending the video frame seamlessly with the dark application theme (`#1e1e2a`).
- **YouTube Direct Stream:** Play videos directly from YouTube URLs using `yt-dlp` (forces H.264/AVC for maximum hardware compatibility).
- **Universal Hardware Compatibility:** Bypasses legacy GPU limitations (e.g., lack of AV1 decoding) by enforcing robust software decoding (`FFMPEG_HWACCEL="0"`), ensuring all modern video formats play smoothly.
- **Minimalist Interface:** Content-focused design devoid of unnecessary clutter.

## 🛠️ System Dependencies
HardPlayer relies on the following system tools to function correctly:
- **FFmpeg:** Required by the Qt Multimedia backend for video processing and decoding.
- **yt-dlp:** Required for fetching and parsing YouTube streams.

## 📥 Installation & Usage

### For Linux Users:
If you have the compiled binary (`hardplayer.bin`), you can run it directly:
```bash
chmod +x hardplayer.bin
./hardplayer.bin
```

### Build from Source:
To compile the native binary yourself using Nuitka:
```bash
# Install dependencies
pip install PyQt6 yt-dlp nuitka

# Compile
python -m nuitka --remove-output hardplayer.py
```

## ⌨️ Keyboard Shortcuts
- **`P`** : Open the media selection dialog (Note: only works if the player is currently stopped/empty).

## 📜 License
This project is licensed under the **GNU GPL v3**. We believe in software freedom and the power of open source. See the `LICENSE` file for more details.

---
**Developed by:** [ahmed-x86](https://github.com/ahmed-x86)  