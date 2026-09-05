# subtitle_button.py

from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QMenu, 
                             QWidgetAction, QListWidget, QListWidgetItem)
from PyQt6.QtGui import QCursor, QColor
from PyQt6.QtCore import Qt, pyqtSignal

class SubtitleButton(QWidget):
    """
    Custom Widget for subtitles acting as a Split Button.
    Main button toggles subtitles on/off.
    Arrow button shows a drop-up scrollable menu to select language.
    """
    clicked = pyqtSignal() 
    track_selected = pyqtSignal(str) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.init_menu()

    def init_ui(self):
        self.setFixedWidth(80) 
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.main_btn = QPushButton("💬 CC")
        self.main_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.main_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        self.arrow_btn = QPushButton("▴")
        self.arrow_btn.setFixedWidth(20)
        self.arrow_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.arrow_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        layout.addWidget(self.main_btn)
        layout.addWidget(self.arrow_btn)

        self.apply_base_style()
        self.main_btn.clicked.connect(self.clicked.emit)

    def init_menu(self):
        self.menu = QMenu(self)
        self.menu.setStyleSheet("""
            QMenu {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 8px;
                padding: 0px;
            }
        """)
        self.arrow_btn.setMenu(self.menu)

        self.scrollable_action = QWidgetAction(self)
        self.list_widget = QListWidget()
        
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #181825;
                color: #cdd6f4;
                border: none;
                outline: none;
                font-family: 'Arial';
                font-size: 13px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px 15px;
                border-radius: 4px;
                margin: 2px 0px;
            }
            QListWidget::item:hover {
                background-color: #313244;
            }
            QListWidget::item:selected {
                background-color: #313244;
                color: #a6e3a1;
            }
            QScrollBar:vertical {
                border: none;
                background: #11111b;
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #45475a;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #585b70;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
        self.list_widget.itemClicked.connect(self._on_list_item_clicked)
        self.scrollable_action.setDefaultWidget(self.list_widget)
        self.menu.addAction(self.scrollable_action)

        self.reset_loading_state()

    def reset_loading_state(self):
        self.list_widget.clear()
        
        item = QListWidgetItem("⏳ جاري جلب الترجمات...")
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.list_widget.addItem(item)
        
        item_off = QListWidgetItem("🚫 Turn Subtitles Off")
        item_off.setData(Qt.ItemDataRole.UserRole, "off")
        self.list_widget.addItem(item_off)

        # عرض 280 مناسب جداً للغات
        self.list_widget.setFixedSize(280, 100)

    def update_tracks(self, manual_subs: dict, auto_subs: dict):
        self.list_widget.clear()

        item_off = QListWidgetItem("🚫 Turn Subtitles Off")
        item_off.setData(Qt.ItemDataRole.UserRole, "off")
        self.list_widget.addItem(item_off)

        if not manual_subs and not auto_subs:
            item_no = QListWidgetItem("❌ لا توجد ترجمات متاحة")
            item_no.setFlags(Qt.ItemFlag.NoItemFlags)
            item_no.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_widget.addItem(item_no)
            self.list_widget.setFixedSize(280, 100)
            return

        if manual_subs:
            self._add_separator("── الترجمات الأصلية ──")
            for lang_code, lang_name in manual_subs.items():
                item = QListWidgetItem(f"📝 {lang_name}")
                item.setData(Qt.ItemDataRole.UserRole, lang_code)
                self.list_widget.addItem(item)

        if auto_subs:
            self._add_separator("── الترجمات التلقائية ──")
            for lang_code, lang_name in auto_subs.items():
                item = QListWidgetItem(f"🤖 {lang_name} (Auto)")
                item.setData(Qt.ItemDataRole.UserRole, f"auto-{lang_code}")
                self.list_widget.addItem(item)

        # حساب الارتفاع: 40 بيكسل للعنصر، والحد الأقصى تم رفعه إلى 650
        total_items = self.list_widget.count()
        calculated_height = (total_items * 40) + 15
        self.list_widget.setFixedSize(280, min(calculated_height, 650))

    def _add_separator(self, text):
        sep = QListWidgetItem(text)
        sep.setFlags(Qt.ItemFlag.NoItemFlags)
        sep.setForeground(QColor("#7f849c"))
        sep.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.list_widget.addItem(sep)

    def _on_list_item_clicked(self, item):
        track_code = item.data(Qt.ItemDataRole.UserRole)
        if track_code:
            self.menu.hide() 
            if track_code == "off":
                self.set_active_status(False)
            else:
                self.set_active_status(True)
            self.track_selected.emit(track_code)

    def apply_base_style(self):
        self.main_btn.setStyleSheet("""
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border-top-left-radius: 6px;
                border-bottom-left-radius: 6px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
                padding: 4px;
                font-size: 14px;
                border: 1px solid #313244;
                border-right: none;
            }
            QPushButton:hover { background-color: #45475a; border-color: #45475a; }
        """)
        
        self.arrow_btn.setStyleSheet("""
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                padding: 4px;
                font-size: 14px;
                border: 1px solid #313244;
                border-left: 1px solid #1e1e2e;
            }
            QPushButton:hover { background-color: #45475a; border-color: #45475a; }
            QPushButton::menu-indicator { image: none; width: 0px; }
        """)

    def set_active_status(self, is_active: bool):
        if is_active:
            self.main_btn.setStyleSheet("""
                QPushButton {
                    background-color: #313244;
                    color: #a6e3a1;
                    border-top-left-radius: 6px;
                    border-bottom-left-radius: 6px;
                    border-top-right-radius: 0px;
                    border-bottom-right-radius: 0px;
                    padding: 4px;
                    font-size: 14px;
                    border: 1px solid #a6e3a1;
                    border-right: none;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #45475a; }
            """)
            self.arrow_btn.setStyleSheet("""
                QPushButton {
                    background-color: #313244;
                    color: #a6e3a1;
                    border-top-left-radius: 0px;
                    border-bottom-left-radius: 0px;
                    border-top-right-radius: 6px;
                    border-bottom-right-radius: 6px;
                    padding: 4px;
                    font-size: 14px;
                    border: 1px solid #a6e3a1;
                    border-left: 1px solid #a6e3a1;
                }
                QPushButton:hover { background-color: #45475a; }
                QPushButton::menu-indicator { image: none; width: 0px; }
            """)
        else:
            self.apply_base_style()