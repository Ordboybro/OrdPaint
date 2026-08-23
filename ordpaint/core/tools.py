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


TOOL_LABELS: dict[Tool, str] = {
    Tool.BRUSH: "Кисть",
    Tool.ERASER: "Ластик",
    Tool.LINE: "Линия",
    Tool.RECTANGLE: "Прямоугольник",
    Tool.ELLIPSE: "Эллипс",
    Tool.FILL: "Заливка",
    Tool.EYEDROPPER: "Пипетка",
    Tool.SELECT_RECT: "Прямоугольное выделение",
}

TOOL_SHORTCUTS: dict[Tool, str] = {
    Tool.BRUSH: "B",
    Tool.ERASER: "E",
    Tool.LINE: "L",
    Tool.RECTANGLE: "R",
    Tool.ELLIPSE: "O",
    Tool.FILL: "G",
    Tool.EYEDROPPER: "I",
    Tool.SELECT_RECT: "M",
}

TOOLS_WITH_BRUSH_SIZE = frozenset({Tool.BRUSH, Tool.ERASER, Tool.LINE, Tool.RECTANGLE, Tool.ELLIPSE})
SHAPE_TOOLS = frozenset({Tool.LINE, Tool.RECTANGLE, Tool.ELLIPSE})


def tool_label(tool: Tool) -> str:
    return TOOL_LABELS[Tool(tool)]


def tool_shortcut(tool: Tool) -> str:
    return TOOL_SHORTCUTS[Tool(tool)]
