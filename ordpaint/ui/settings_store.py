from __future__ import annotations

from PySide6.QtCore import QSettings

from ordpaint.core.ui_state import UIState


class SettingsStore:
    """Small QSettings adapter for the Qt-free :class:`UIState` model."""

    GROUP = "ui"

    def __init__(self, settings: QSettings | None = None) -> None:
        self.settings = settings or QSettings("Ordboy", "OrdPaint")

    def load(self) -> UIState:
        settings = self.settings
        settings.beginGroup(self.GROUP)
        try:
            data = {
                "geometry": settings.value("geometry"),
                "window_state": settings.value("window_state"),
                "zoom": settings.value("zoom", 1.0),
                "show_grid": settings.value("show_grid", False),
                "show_rulers": settings.value("show_rulers", True),
                "grid_size": settings.value("grid_size", 32),
                "brush_size": settings.value("brush_size", 8),
                "opacity": settings.value("opacity", 100),
                "color": settings.value("color", "#111111"),
                "recent_paths": settings.value("recent_paths", []),
            }
        finally:
            settings.endGroup()
        return UIState.from_mapping(data)

    def save(self, state: UIState) -> None:
        data = state.to_mapping()
        settings = self.settings
        settings.beginGroup(self.GROUP)
        try:
            for key, value in data.items():
                settings.setValue(key, value)
        finally:
            settings.endGroup()
        settings.sync()
