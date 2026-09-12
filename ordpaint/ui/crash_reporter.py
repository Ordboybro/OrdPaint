from __future__ import annotations

import os
import platform
import sys
import traceback
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox


LOG_PATH = Path.home() / ".ordpaint" / "crash.log"


def install() -> None:
    previous_hook = sys.excepthook

    def hook(exc_type, exc_value, exc_traceback) -> None:
        if exc_type is KeyboardInterrupt:
            previous_hook(exc_type, exc_value, exc_traceback)
            return
        try:
            LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            details = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            entry = (
                f"\n=== {datetime.now().isoformat(timespec='seconds')} ===\n"
                f"Python: {platform.python_version()}\n"
                f"Platform: {platform.platform()}\n"
                f"{details}"
            )
            with LOG_PATH.open("a", encoding="utf-8") as handle:
                handle.write(entry)
        except OSError:
            pass

        # Never open a modal Qt dialog from pytest/headless runs: if the
        # exception itself came from Qt, doing so can turn a useful traceback
        # into a native crash. Keep the original exception visible to pytest.
        if os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("CI"):
            previous_hook(exc_type, exc_value, exc_traceback)
            return

        app = QApplication.instance()
        if app is None:
            previous_hook(exc_type, exc_value, exc_traceback)
            return
        try:
            QMessageBox.critical(
                None,
                "OrdPaint — ошибка",
                "Произошла непредвиденная ошибка.\n\n"
                f"Диагностика сохранена в:\n{LOG_PATH}",
            )
        except RuntimeError:
            previous_hook(exc_type, exc_value, exc_traceback)

    sys.excepthook = hook
