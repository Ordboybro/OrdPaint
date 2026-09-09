import sys

from PySide6.QtWidgets import QApplication

from ordpaint.ui.application_window import MainWindow
from ordpaint.ui.crash_reporter import install as install_crash_reporter
from ordpaint.ui.layout_restore import install as install_layout_restore
from ordpaint.ui.polish import install as install_polish
from ordpaint.ui.resize_integration import install as install_resize


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("OrdPaint")
    app.setApplicationDisplayName("OrdPaint")
    app.setOrganizationName("OrdStudio")
    app.setOrganizationDomain("ordpaint.local")
    app.setStyle("Fusion")
    install_crash_reporter()

    window = MainWindow()
    install_polish(window)
    install_resize(window)
    install_layout_restore(window)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
