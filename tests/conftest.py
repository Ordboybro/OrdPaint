import os

# The Qt offscreen backend can crash on some Linux runners when QMenuBar is
# constructed. The minimal backend is sufficient for widget-level tests and
# keeps the suite deterministic in headless CI environments.
os.environ.setdefault("QT_QPA_PLATFORM", "minimal")

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qt_app():
    app = QApplication.instance()
    return app or QApplication([])


@pytest.fixture(scope="session")
def qapp(qt_app):
    """Compatibility alias for tests that use the conventional qapp fixture name."""
    return qt_app


@pytest.fixture(autouse=True)
def ensure_qt_app(qt_app):
    """Keep QPixmap/QPainter tests safe even when they omit an explicit fixture."""
    return qt_app
