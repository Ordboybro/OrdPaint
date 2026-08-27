from PySide6.QtCore import QSettings

from ordpaint.core.ui_state import UIState
from ordpaint.ui.settings_store import SettingsStore


def test_settings_store_roundtrip(tmp_path, qt_app):
    path = tmp_path / "settings.ini"
    settings = QSettings(str(path), QSettings.Format.IniFormat)
    store = SettingsStore(settings)
    state = UIState(
        geometry=b"geometry",
        window_state=b"state",
        zoom=1.75,
        show_grid=True,
        show_rulers=False,
        grid_size=48,
        brush_size=19,
        opacity=72,
        color="#ff6b00",
        recent_paths=["one.ordpaint", "two.ordpaint"],
    )

    store.save(state)
    restored = store.load()

    assert restored.to_mapping() == state.to_mapping()


def test_settings_store_missing_values_use_defaults(tmp_path, qt_app):
    settings = QSettings(str(tmp_path / "empty.ini"), QSettings.Format.IniFormat)
    state = SettingsStore(settings).load()

    assert state.zoom == 1.0
    assert state.show_grid is False
    assert state.show_rulers is True
    assert state.recent_paths == []
