from __future__ import annotations

from enum import StrEnum


class Tool(StrEnum):
    BRUSH = "brush"
    ERASER = "eraser"
    LINE = "line"
    RECTANGLE = "rectangle"
    ELLIPSE = "ellipse"
    FILL = "fill"
    EYEDROPPER = "eyedropper"
    SELECT_RECT = "select_rect"
