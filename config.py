# config.py

# --- ألوان الواجهة (Catppuccin Theme) ---
BASE = "#1e1e2a"
TEXT = "#cdd6f4"
MAUVE = "#cba6f7"
SURFACE0 = "#313244"

# --- التنسيقات العامة (Stylesheet) ---
stylesheet = f"""
QMainWindow, QStackedWidget {{ 
    background-color: {BASE}; 
    border: none; 
}}

QDialog {{ 
    background-color: {BASE}; 
    border-radius: 10px; 
}}

QLabel {{ 
    color: {TEXT}; 
    background-color: transparent; 
}}

QPushButton {{ 
    background-color: {SURFACE0}; 
    color: {TEXT}; 
    border: 2px solid {MAUVE}; 
    border-radius: 8px; 
    padding: 8px 16px; 
    font-weight: bold; 
    font-size: 14px; 
}}

QPushButton:hover {{ 
    background-color: {MAUVE}; 
    color: {BASE}; 
}}

QLineEdit {{ 
    background-color: {SURFACE0}; 
    color: {TEXT}; 
    border: 1px solid {MAUVE}; 
    border-radius: 6px; 
    padding: 8px; 
    font-size: 14px; 
}}

QTextEdit {{ 
    background-color: {SURFACE0}; 
    color: {TEXT}; 
    border: 1px solid {MAUVE}; 
    border-radius: 6px; 
    padding: 8px; 
    font-family: monospace; 
    font-size: 13px; 
}}
"""