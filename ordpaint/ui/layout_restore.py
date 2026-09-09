from __future__ import annotations


def install(window) -> None:
    state = getattr(window, "ui_state", None)
    if state is not None and state.window_state:
        window.restoreState(state.window_state)
