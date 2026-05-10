# 🎬 HardPlayer (27.0.0)

HardPlayer is a lightweight, high-performance modular media player built with **Python**, **PyQt6**, and the **MPV Engine**. It combines native system integration with a sleek **Catppuccin Mocha** aesthetic and a pro-grade YouTube acquisition engine.

Developed by **Ahmed (ahmed-x86)**, this player follows the "KISS" philosophy, specifically optimized for the Linux ecosystem.

---

![License](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Linux%20-lightgrey)
![Version](https://img.shields.io/badge/Version-27.0.0-mauve)
![Theme](https://img.shields.io/badge/Theme-Catppuccin%20Mocha-blue)

---

## 📥 Download Links

| Variant | Ubuntu / Debian (DEB) | Fedora / Suse (RPM) | Arch Linux (Pacman) |
| :--- | :--- | :--- | :--- |
| **Standalone (Bundled Qt)** | [Download DEB](https://github.com/ahmed-x86/hardplayer/releases/download/v27.0.0/hardplayer-standalone_27.0.0_amd64.deb) | [Download RPM](https://github.com/ahmed-x86/hardplayer/releases/download/v27.0.0/hardplayer-standalone-27.0.0-1.x86_64.rpm) | [Download Pacman](https://github.com/ahmed-x86/hardplayer/releases/download/v27.0.0/hardplayer-standalone-27.0.0-1-x86_64.pkg.tar.zst) |
| **System-Qt (Lightweight)** | [Download DEB](https://github.com/ahmed-x86/hardplayer/releases/download/v27.0.0/hardplayer-system-qt_27.0.0_amd64.deb) | [Download RPM](https://github.com/ahmed-x86/hardplayer/releases/download/v27.0.0/hardplayer-system-qt-27.0.0-1.x86_64.rpm) | [Download Pacman](https://github.com/ahmed-x86/hardplayer/releases/download/v27.0.0/hardplayer-system-qt-27.0.0-1-x86_64.pkg.tar.zst) |

---

### 🔧 What's Changed in v27.0.0?

* **Crash-Proof Auto Resume**: State management has been drastically improved. If your machine loses power, the system crashes, or the app is abruptly closed, HardPlayer will flawlessly resume the video from the exact second it stopped.
* **Upgraded Search Workflow**: The built-in YouTube search interface now features dedicated **"Download"** and **"Copy Link"** buttons directly on every video card, bypassing the need to navigate through the URL input dialog.
* **Refined Codebase Modularity**: The fetching logic and UI components continue to be isolated into specialized modules (`ui_components.py`, `youtube_feature.py`), optimizing overall maintainability.
* **Embedded Assets**: UI icons remain cleanly embedded directly inside the compiled Nuitka binary structure.

## ✨ What's New in v26.0.0?

* **Auto Resume (Smart Playback)**: Videos now remember exactly where you left off. Reopening a previously watched file prompts a seamlessly integrated resume dialog, letting you continue playback instantly.
* **Codebase Modularity**: Separated the resume logic (`ui_components_continue.py`) and YouTube Playlist fetching into independent modules, establishing a cleaner, highly maintainable architecture.
* **MPRIS Integration Fixed**: D-Bus and GLib modules are correctly bound to host systems. Media keys and external player controllers (like KDE Connect) now work flawlessly on built binaries.

## ✨ What's New in v25.0.0?

* **Thumbnail & Logo Fix**: Resolved an issue where the application's startup logo (`icon_in_app.png`) would not display when launching the installed binary. The build system now enforces runtime asset resolution (`--file-reference-choice=runtime`), ensuring all embedded images load perfectly regardless of the build environment.
* **Next-Gen Release**: Upgraded the core engine to version 25.

## ✨ What's New in v24.0.0?

* **Fixed Ubuntu Builds**: System-Qt for Debian/Ubuntu now utilizes the 24.04 base to ensure `python3-pyqt6` dependency resolution.
* **Embedded Assets**: Nuitka now correctly embeds UI icons (`icon_in_app.png` & `icon.png`) directly into the compiled binaries for a flawless native look.

## ✨ What's New in v23.0.0?

* **Robust Download Resumption**: Integrated a state-management system (`.json` tracking) for interrupted or manually cancelled downloads. HardPlayer will now automatically detect leftover `.part` files and resume the download exactly from where it left off, saving bandwidth and time.
* **Smart YouTube URL Parsing**: Implemented a robust URL cleaner that automatically sanitizes user inputs. It strips unwanted parameters (like `&t=` timestamps or `&list=` playlists) to prevent erratic `yt-dlp` behavior and ensure accurate video metadata fetching.
* **Extended Filename & UI WordWrap**: Removed arbitrary slicing on long video titles. The UI now dynamically wraps text to display the full name flawlessly. Additionally, downloaded files now append the unique YouTube `[ID]` to their names to completely prevent overwriting or naming conflicts.
* **Granular Progress & Merging Status**: The progress UI is now fully stream-aware. It explicitly displays separate sizes for Video and Audio streams, calculates the exact downloaded megabytes, and transitions to a clear "Merging Video & Audio... Please wait ⏳" status when `ffmpeg` is finalizing the file.

## ✨ What's New in v22.0.0?

* **Dual-Variant Release Architecture**: Now offering two distinct build types. **Standalone** includes all Qt6 libraries for "out-of-the-box" compatibility, while **System-Qt** uses your distro's native libraries for a significantly smaller footprint.
* **Pro Media Converter Suite**: Integrated a multi-threaded conversion engine. Directly convert Video (MP4, MKV, WebM, DaVinci ProRes), Audio (MP3, Extraction, Muting), and Images (JPG, WebP, GIF) from the top menu.
* **CUDA-Assisted Pipeline**: Optimized for NVIDIA hardware. Leverages CUDA for hardware-accelerated decoding, paired with high-compatibility encoders (libx264/VP9) to ensure perfect playback on all devices.
* **Smart Progress Tracking**: Real-time conversion analytics featuring precise percentage calculations, speed metrics (e.g., 20x), and duration detection—even for complex MKV containers.
* **Safety-First Cancellation**: New interactive confirmation system when closing active conversions, allowing users to choose between immediate cleanup or saving partially processed files.
* **Optimized Build Logic**: Redesigned GitHub Actions workflow with version-agnostic caching, ensuring lightning-fast compilation across multiple releases.

## ✨ What's New in v21.0.0?

* **UX Improvements**: Fully reorganized the top menus (Hardware and YouTube) using cascading sub-menus for a cleaner, more intuitive interface.
* **Custom Download Location**: Added a new feature to select and save a specific directory for YouTube videos and metadata info (.txt) files directly from the top menu.

## ✨ What's New in v20.0.0?

* **Universal Subtitles**: We have added a translation feature that works for audio and video from the device or YouTube.
* **Advanced YouTube Downloader**: The download system has been upgraded into a comprehensive tool. You can down download subtitles, thumbnails, embed chapters, and save video metadata (.txt), no longer limited to just downloading the video!
* **Smart Subtitle Fetching**: An intelligent system to fetch subtitles (English and Arabic by default) with a built-in anti-ban mechanism (`sleep_interval`) to avoid YouTube IP blocks (Error 429).
* **Enhanced Download UI**: A custom, interactive UI featuring elegant Catppuccin Mauve toggle switches, informational dialogs, and a robust cancellation system with safe cleanup options for incomplete files.

---

## ✨ What's New in v18.0?

* **YouTube Playlist Optimization**: Radical improvement in playlist handling. The player now fetches the first video's data immediately to start playback without waiting for the entire playlist to load.
* **Sidebar Persistence Fix**: Resolved the issue where the sidebar playlist would disappear when selecting a video. The list now remains visible with an updated playback index.
* **Faster Loading Engine**: Reduced data extraction time using optimized `yt-dlp` and `oEmbed` calls to open links faster than ever.

---

## ✨ What's New in v17.0?

* **Preferred YouTube Extension**: Set your default format (`mp4`, `mkv`, `webm`) from the Top Menu. HardPlayer remembers your choice natively via local cache.
* **Smart Format Fallback**: Automatically detects available formats and displays dynamic fallback notes directly on the UI (e.g., `(webm because not found mp4)`).
* **Unified Advanced UI**: The advanced download dialog now features the same beautiful, information-rich table UI as the streaming menu, operating in a seamless "Download Mode".

## 📥 Pro YouTube Downloader (Added in v16.0)

* **Aria2 Acceleration**: Integrated `aria2c` support for multi-threaded acquiring (16 parallel connections), bypassing YouTube's speed throttling.
* **Real-time Analytics**: A dedicated progress window showing live speed (MiB/s), total file size, and exact "Time Left" (ETA).
* **Full Metadata Extraction**: Automatically fetches and displays Channel name, Publication date, Like counts, and Comment counts for every video.
* **Dynamic Format Selection**: Choose between simple quality presets or **Advanced Mode** to input specific Video/Audio Stream IDs for custom merges.

## 🎨 Refined Progress UI

* **Catppuccin Aesthetics**: Progress bars now feature the signature **Catppuccin Green** bar with **Mauve (#cba6f7)** text metrics for maximum readability and style.
* **ANSI-Clean Logic**: New internal filtering to remove messy terminal color codes, ensuring only clean text appears in the UI.

---

## 🧩 Previous Highlights (v15.0)

* **Modular Refactor**: Decoupled core components to ensure the UI thread remains 100% lag-free.
* **Dynamic Quality Flow**: A smart dialog that detects actual available resolutions for any YouTube video before playback.
* **Lazy Loading Engine**: Batches of 6 media items are loaded to prevent freezes in large directories.

---

## 🛠️ Development & Quick Run

HardPlayer provides easy methods for testing and development:

**clone the repo**
```bash
git clone https://github.com/ahmed-x86/hardplayer.git
cd hardplayer
python hardplayer.py


```

---

## 💻 CLI Documentation

HardPlayer's terminal interface remains the fastest way to launch media.

### Available Flags:

* `-device [cpu|intel|amd|nvidia]`: Force hardware decoding backends.
* `-quality [1080p|720p|480p|audio]`: Set YouTube streaming resolution.
* `-search`: Treat input as a YouTube search query.

### Usage Examples:

**1. Fast Launch (Local File + Hardware Decoding)**
*Bypasses the decoding dialog and launches the video immediately on the GPU.*

```bash
hardplayer /path/to/video.mp4 -device old_nvidia

```

**2. Fast Launch (YouTube + Quality + Decoding)**
*Bypasses all dialogs and streams the URL directly with the requested settings.*

```bash
hardplayer "[https://www.youtube.com/watch?v=test](https://www.youtube.com/watch?v=test)" -quality 1080p -device old_nvidia
```

**3. Direct YouTube Search**
*Skips the startup dialog and jumps directly into the search results for the query.*

```bash
hardplayer -search "test"
```

**4. Audio-Only Mode (Podcasts)**
*Disables video output to drastically save RAM and bandwidth. Great for background listening.*

```bash
hardplayer "[https://www.youtube.com/watch?v=test](https://www.youtube.com/watch?v=test)" -quality audio
```

**5. Combined Search & Fast Launch**
*Searches YouTube, and upon selecting a video, instantly plays it with the predefined settings without asking further questions.*

```bash
hardplayer -search "test" -quality 720p -device cpu
```

---

## 🛠️ Core Features & Philosophy

* **Wayland-Native**: Optimized for **Hyprland** with forced EGL contexts for stability.
* **Hardware Mastery**: Specialized support for NVDEC and VA-API with graceful fallbacks.
* **Rich MPRIS**: Seamless integration with Waybar, SwayNC, and system trays.

---

## 📥 Installation

### Arch Linux (Pacman):

```bash
sudo pacman -S aria2  # Required for high-speed downloads
sudo pacman -U hardplayer-system-qt-27.0.0-1-x86_64.pkg.tar.zst
```

### Debian/Ubuntu (DEB):

```bash
sudo apt install aria2
sudo dpkg -i hardplayer-system-qt_27.0.0_amd64.deb
```

## 📦 Requirements

Ensure the following are installed:

* `mpv` (libmpv)
* `ffmpeg`
* `yt-dlp`
* **`aria2`** (For accelerated downloads)

---

**Developed with ☕ and Arch Linux by:** [ahmed-x86](https://github.com/ahmed-x86)

*"Keep it simple, keep it elegant, keep it fast."*