This document lists all the necessary components to run or build **HardPlayer v4** on Arch Linux.

## 1. System Packages (Arch Linux)
Since we moved to the **MPV Engine**, the old `qt6-multimedia` packages are no longer required. However, with the new **MPRIS2 integration**, you need specific system libraries to allow D-Bus communication. Install the following via `pacman`:

```bash
sudo pacman -S mpv ffmpeg yt-dlp dbus gobject-introspection cairo pkgconf
```

*Note: `mpv` provides the core rendering engine, `yt-dlp` handles YouTube streaming, and the rest (`dbus`, `gobject-introspection`, `cairo`, `pkgconf`) are required to build and run the system integration components.*

## 2. Python Libraries
Install the required Python wrappers using `pip`. It is recommended to use the `--user` flag or a virtual environment.

```bash
pip install PyQt6 python-mpv dbus-python PyGObject
```

*Note: `dbus-python` and `PyGObject` are newly added to support MPRIS2 integration (KDE Connect, keyboard media keys, and system notifications).*

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