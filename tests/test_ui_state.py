from ordpaint.core.ui_state import UIState


def test_defaults_are_portfolio_safe() -> None:
    state = UIState()

    assert state.zoom == 1.0
    assert state.show_grid is False
    assert state.show_rulers is True
    assert state.color == "#111111"


def test_from_mapping_normalizes_invalid_values() -> None:
    state = UIState.from_mapping(
        {
            "zoom": "999",
            "grid_size": 1,
            "brush_size": 900,
            "opacity": 0,
            "color": "not-a-color",
            "recent_paths": ["A.ordpaint", "a.ordpaint", "B.ordpaint", ""],
        }
    )

    assert state.zoom == UIState.MAX_ZOOM
    assert state.grid_size == 2
    assert state.brush_size == 500
    assert state.opacity == 1
    assert state.color == "#111111"
    assert state.recent_paths == ["A.ordpaint", "B.ordpaint"]


def test_roundtrip_keeps_persisted_values() -> None:
    original = UIState(
        geometry=b"geometry",
        window_state=b"state",
        zoom=1.75,
        show_grid=True,
        show_rulers=False,
        grid_size=64,
        brush_size=24,
        opacity=73,
        color="#AaBbCc",
        recent_paths=["first.ordpaint", "second.ordpaint"],
    )

    restored = UIState.from_mapping(original.to_mapping())

    assert restored.geometry == b"geometry"
    assert restored.window_state == b"state"
    assert restored.zoom == 1.75
    assert restored.show_grid is True
    assert restored.show_rulers is False
    assert restored.grid_size == 64
    assert restored.brush_size == 24
    assert restored.opacity == 73
    assert restored.color == "#aabbcc"
    assert restored.recent_paths == ["first.ordpaint", "second.ordpaint"]


def test_invalid_optional_values_fall_back_safely() -> None:
    state = UIState.from_mapping(
        {
            "geometry": object(),
            "window_state": object(),
            "zoom": "bad",
            "recent_paths": "not-a-list",
        }
    )

    assert state.geometry is None
    assert state.window_state is None
    assert state.zoom == 1.0
    assert state.recent_paths == []
