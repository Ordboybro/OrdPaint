import sys

from PySide6.QtWidgets import QApplication

from ordpaint.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("OrdPaint")
    app.setOrganizationName("OrdStudio")

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
