# styles.py

"""
Centralized stylesheet and color palette for HardPlayer.
Utilizes the Catppuccin Mocha color scheme for a consistent, modern UI.
"""

class CatppuccinMocha:
    """
    Color palette for the Catppuccin Mocha theme.
    Useful if you need to reference specific hex colors dynamically in code.
    """
    CRUST = "#11111b"     # Darkest background (used for video letterboxing, top menu)
    MANTLE = "#181825"    # Dark background (used for bottom controls, sidebar overlay)
    BASE = "#1e1e2e"      # Default application background
    SURFACE0 = "#313244"  # Default button/item backgrounds
    SURFACE1 = "#45475a"  # Hovered button/item backgrounds
    TEXT = "#cdd6f4"      # Primary text color
    BLUE = "#89b4fa"      # Primary accent color (active elements, hover text)
    GREEN = "#a6e3a1"     # Success/Toggled accent color (e.g., active loop)
    PEACH = "#fab387"     # Secondary accent (e.g., default thumbnail icon)


class AppStyles:
    """
    Pre-defined Qt Style Sheets (QSS) for various UI components.
    """
    
    # -----------------------------------------
    # Main Window & Global
    # -----------------------------------------
    MAIN_WINDOW = f"""
        QMainWindow {{
            background-color: {CatppuccinMocha.BASE};
        }}
        QWidget#CentralWidget {{
            background-color: {CatppuccinMocha.BASE};
        }}
    """

    # -----------------------------------------
    # Scroll Area (Sidebar)
    # -----------------------------------------
    SCROLL_AREA = f"""
        QScrollArea {{
            border: none; 
            background: transparent;
        }}
        /* Optional: Customizing the vertical scrollbar to fit the theme */
        QScrollBar:vertical {{
            background: {CatppuccinMocha.CRUST};
            width: 10px;
            margin: 0px 0px 0px 0px;
            border-radius: 5px;
        }}
        QScrollBar::handle:vertical {{
            background: {CatppuccinMocha.SURFACE0};
            min-height: 20px;
            border-radius: 5px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {CatppuccinMocha.SURFACE1};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
    """

    # -----------------------------------------
    # Generic Dialog (e.g., Startup, Info, YouTube Dialogs)
    # -----------------------------------------
    DIALOG = f"""
        QDialog {{
            background-color: {CatppuccinMocha.BASE};
            color: {CatppuccinMocha.TEXT};
        }}
        QLabel {{
            color: {CatppuccinMocha.TEXT};
        }}
        QPushButton {{
            background-color: {CatppuccinMocha.SURFACE0};
            color: {CatppuccinMocha.TEXT};
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {CatppuccinMocha.SURFACE1};
            color: {CatppuccinMocha.BLUE};
        }}
        QLineEdit {{
            background-color: {CatppuccinMocha.CRUST};
            color: {CatppuccinMocha.TEXT};
            border: 1px solid {CatppuccinMocha.SURFACE0};
            border-radius: 4px;
            padding: 6px;
        }}
        QLineEdit:focus {{
            border: 1px solid {CatppuccinMocha.BLUE};
        }}
    """

    # -----------------------------------------
    # Buttons - Ghost/Transparent (used for close buttons or icons)
    # -----------------------------------------
    GHOST_BUTTON = f"""
        QPushButton {{
            background: transparent;
            color: {CatppuccinMocha.TEXT};
            border: none;
        }}
        QPushButton:hover {{
            color: {CatppuccinMocha.BLUE};
        }}
    """