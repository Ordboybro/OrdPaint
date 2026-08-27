import sys

from PySide6.QtWidgets import QApplication

from ordpaint.ui.application_window import MainWindow


APP_STYLE = """
QMainWindow, QWidget {
    background: #17181c;
    color: #e8eaf0;
}

QMenuBar {
    background: #1d1f24;
    color: #dfe2e8;
    border-bottom: 1px solid #2b2e35;
}

QMenuBar::item {
    padding: 7px 12px;
    background: transparent;
}

QMenuBar::item:selected, QMenu::item:selected {
    background: #2d6cdf;
    color: white;
}

QMenu {
    background: #202329;
    color: #e8eaf0;
    border: 1px solid #353941;
    padding: 5px;
}

QToolBar {
    background: #1d1f24;
    border: 0;
    border-bottom: 1px solid #2b2e35;
    spacing: 5px;
    padding: 5px;
}

QToolButton {
    background: transparent;
    color: #cdd1da;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 6px 8px;
}

QToolButton:hover {
    background: #292d35;
    border-color: #383d47;
}

QToolButton:checked {
    background: #2d6cdf;
    color: white;
}

QDockWidget {
    color: #e8eaf0;
    titlebar-close-icon: none;
}

QDockWidget::title {
    background: #1d1f24;
    border-bottom: 1px solid #2b2e35;
    padding: 8px;
    font-weight: 600;
}

QListWidget, QTreeWidget {
    background: #1d1f24;
    color: #e2e5eb;
    border: 1px solid #2b2e35;
    border-radius: 6px;
    outline: none;
}

QListWidget::item {
    padding: 8px;
    border-radius: 5px;
}

QListWidget::item:selected {
    background: #2d6cdf;
    color: white;
}

QPushButton, QSpinBox, QComboBox {
    background: #25282f;
    color: #e6e8ed;
    border: 1px solid #363a43;
    border-radius: 5px;
    padding: 5px 8px;
}

QPushButton:hover, QComboBox:hover {
    background: #2d3139;
}

QSlider::groove:horizontal {
    height: 4px;
    background: #383d46;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    width: 13px;
    margin: -5px 0;
    border-radius: 7px;
    background: #5f95f2;
}

QStatusBar {
    background: #1d1f24;
    color: #9da3af;
    border-top: 1px solid #2b2e35;
}

QScrollBar:vertical, QScrollBar:horizontal {
    background: #1a1c20;
    border: none;
}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #3b4049;
    border-radius: 5px;
    min-height: 20px;
    min-width: 20px;
}
"""


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("OrdPaint")
    app.setOrganizationName("OrdStudio")
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLE)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
