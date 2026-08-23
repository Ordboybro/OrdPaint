import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtGui import QGuiApplication


@pytest.fixture(scope="session")
def qt_app():
    app = QGuiApplication.instance()
    return app or QGuiApplication([])
