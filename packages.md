```python?code_reference&code_event_index=3
content = """# 🛠️ HardPlayer v2.0 - Dependencies & Installation

This document lists all the necessary components to run or build **HardPlayer v2** on Arch Linux.

## 1. System Packages (Arch Linux)
Since we moved to the **MPV Engine**, the old `qt6-multimedia` packages are no longer required. You need to install the following via `pacman`:

```bash
sudo pacman -S mpv ffmpeg yt-dlp
```

*Note: `mpv` provides the core rendering engine, while `yt-dlp` handles YouTube streaming.*

## 2. Python Libraries
Install the required Python wrappers using `pip`. It is recommended to use the `--user` flag or a virtual environment.

```bash
pip install PyQt6 python-mpv
```

## 3. Build Dependencies (Optional)
If you intend to compile the project into a native binary using **Nuitka**, you will also need:

```bash
pip install nuitka zstandard ordered-set
```

## 4. Troubleshooting (Wayland/Hyprland)
HardPlayer is configured to force the **XCB (X11)** backend to ensure perfect window embedding. Ensure you have the X11 compatibility layer installed (standard on most Arch installs):

```bash
sudo pacman -S xorg-server-xwayland
```

---
**Maintained by:** [ahmed-x86](https://github.com/ahmed-x86)
"""

with open("DEPENDENCIES.md", "w", encoding="utf-8") as f:
    f.write(content)