# 🎬 HardPlayer (v2.0)

A lightweight, high-performance video player built with **Python**, **PyQt6**, and the legendary **MPV Engine**, compiled into a native binary using **Nuitka** to ensure maximum performance and instant startup on Linux.

![License](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Linux%20-lightgrey)

## 🚀 Features
- **MPV Engine Core:** Replaced the legacy QtMultimedia backend with `libmpv` for flawless multi-format support, native YouTube integration, and unmatched playback performance.
- **Smart Hardware Acceleration:** Intelligently detects Intel, AMD, and NVIDIA GPUs (including robust support for legacy Maxwell cards via `nvdec-copy`). Features an interactive GUI to select your preferred decoding method (`vaapi`, `vdpau`, `nvdec`).
- **Intelligent Fallback & Terminal Logging:** Features a built-in terminal observer that tracks your video codec (e.g., AV1, H.264) in real-time. If your GPU doesn't support hardware decoding for a specific codec, HardPlayer gracefully falls back to CPU decoding and alerts you in the terminal.
- **Wayland & X11 Seamless Integration:** Forces strict X11/EGL contexts (`QT_QPA_PLATFORM="xcb"`, `gpu_context="x11egl"`) under the hood to ensure the video frame stays perfectly embedded inside the app window, completely preventing detached windows on modern Wayland compositors (like Hyprland).
- **YouTube Direct Stream:** Play videos directly from YouTube URLs. MPV handles the streaming natively with `yt-dlp` working silently in the background.
- **Raw Performance:** Instant startup and a minimal memory footprint thanks to native compilation via Nuitka.
- **Smart Aspect Ratio Container:** Custom UI container that eliminates raw black letterboxing, blending the video frame seamlessly with the dark application theme (`#1e1e2a`).

## 🛠️ System Dependencies
HardPlayer relies on the following system tools to function correctly:
- **mpv:** The core media playback engine (`libmpv`).
- **FFmpeg:** Required for backend media processing and decoding.
- **yt-dlp:** Required for fetching and parsing YouTube streams.

## 📥 Installation & Usage

### For Linux Users:
If you have the compiled binary or installed the packaged version (`.deb`, `.rpm`, `.zst`), you can launch it directly from your terminal or application menu:
```bash
hardplayer
```

### Build from Source:
To compile the native binary yourself using Nuitka, ensure you have the required Python dependencies:
```bash
# Install dependencies
pip install PyQt6 python-mpv nuitka zstandard ordered-set

# Compile
python -m nuitka --standalone --remove-output --enable-plugin=pyqt6 --assume-yes-for-downloads hardplayer.py
```

## ⌨️ Keyboard Shortcuts
- **`P`** : Open the media selection dialog (Note: only works if the player is currently idle/stopped).
- **`I`** : Open the System FFmpeg Information dialog.

## 📜 License
This project is licensed under the **GNU GPL v3**. We believe in software freedom and the power of open source. See the `LICENSE` file for more details.

---
**Developed by:** [ahmed-x86](https://github.com/ahmed-x86)  