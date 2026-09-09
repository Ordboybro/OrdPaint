from __future__ import annotations

import platform
import sys
import traceback
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox


LOG_PATH = Path.home() / ".ordpaint" / "crash.log"


def install() -> None:
    def hook(exc_type, exc_value, exc_traceback) -> None:
        if exc_type is KeyboardInterrupt:
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
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
        app = QApplication.instance()
        if app is not None:
            QMessageBox.critical(
                None,
                "OrdPaint — ошибка",
                "Произошла непредвиденная ошибка.\n\n"
                f"Диагностика сохранена в:\n{LOG_PATH}",
            )

    sys.excepthook = hook
