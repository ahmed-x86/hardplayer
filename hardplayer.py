#!/usr/bin/env python3
# hardplayer.py

import os
import sys
import locale

# Force the X11 backend to prevent MPV from opening a separate, detached window
# when running on Arch Linux with a Wayland compositor (like Hyprland).
os.environ["QT_QPA_PLATFORM"] = "xcb"

# A clever workaround: Hide Wayland from the engine so it doesn't ignore the Window ID (WID)
if "WAYLAND_DISPLAY" in os.environ:
    del os.environ["WAYLAND_DISPLAY"]

from PyQt6.QtWidgets import QApplication

# Import the stylesheet from our configuration file
from config import stylesheet

# Import the main window class from our main module
from main_window import HardPlayerWindow

def main():
    app = QApplication(sys.argv)
    
    # Set the locale to 'C' (standard C locale) to prevent MPV from failing
    # due to floating-point number parsing issues (like expecting ',' instead of '.')
    locale.setlocale(locale.LC_NUMERIC, "C")
    
    # Apply the global Catppuccin theme stylesheet
    app.setStyleSheet(stylesheet)
    
    # Initialize and show the main media player window
    window = HardPlayerWindow()
    window.show()
    
    # Start the application's event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()