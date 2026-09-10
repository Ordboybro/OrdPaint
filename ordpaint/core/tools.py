from __future__ import annotations

from dataclasses import dataclass
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
    SELECT_ELLIPSE = "select_ellipse"
    SELECT_POLYGON = "select_polygon"
    SELECT_LASSO = "select_lasso"
    CROP = "crop"


@dataclass(frozen=True)
class ToolInfo:
    label: str
    shortcut: str
    group: str
    supports_size: bool = False


TOOL_INFO = {
    Tool.BRUSH: ToolInfo("Кисть", "B", "paint", True),
    Tool.ERASER: ToolInfo("Ластик", "E", "paint", True),
    Tool.LINE: ToolInfo("Линия", "L", "shape", True),
    Tool.RECTANGLE: ToolInfo("Прямоугольник", "R", "shape", True),
    Tool.ELLIPSE: ToolInfo("Эллипс", "O", "shape", True),
    Tool.FILL: ToolInfo("Заливка", "G", "paint"),
    Tool.EYEDROPPER: ToolInfo("Пипетка", "I", "color"),
    Tool.SELECT_RECT: ToolInfo("Прямоугольное выделение", "M", "selection"),
    Tool.SELECT_ELLIPSE: ToolInfo("Овальное выделение", "Shift+M", "selection"),
    Tool.SELECT_POLYGON: ToolInfo("Многоугольное выделение", "P", "selection"),
    Tool.SELECT_LASSO: ToolInfo("Лассо", "Shift+P", "selection"),
    Tool.CROP: ToolInfo("Кадрирование", "C", "image"),
}

TOOL_LABELS = {tool: info.label for tool, info in TOOL_INFO.items()}
TOOL_SHORTCUTS = {tool: info.shortcut for tool, info in TOOL_INFO.items()}
TOOLS_WITH_BRUSH_SIZE = frozenset(tool for tool, info in TOOL_INFO.items() if info.supports_size)
SHAPE_TOOLS = frozenset({Tool.LINE, Tool.RECTANGLE, Tool.ELLIPSE})
SELECTION_TOOLS = frozenset({Tool.SELECT_RECT, Tool.SELECT_ELLIPSE, Tool.SELECT_POLYGON, Tool.SELECT_LASSO})


def tool_label(tool: Tool) -> str:
    return TOOL_INFO[Tool(tool)].label


def tool_shortcut(tool: Tool) -> str:
    return TOOL_INFO[Tool(tool)].shortcut
