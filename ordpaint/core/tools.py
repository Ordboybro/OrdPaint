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
}

TOOL_LABELS = {tool: info.label for tool, info in TOOL_INFO.items()}
TOOL_SHORTCUTS = {tool: info.shortcut for tool, info in TOOL_INFO.items()}
TOOLS_WITH_BRUSH_SIZE = frozenset(tool for tool, info in TOOL_INFO.items() if info.supports_size)
SHAPE_TOOLS = frozenset({Tool.LINE, Tool.RECTANGLE, Tool.ELLIPSE})


def tool_label(tool: Tool) -> str:
    return TOOL_INFO[Tool(tool)].label


def tool_shortcut(tool: Tool) -> str:
    return TOOL_INFO[Tool(tool)].shortcut
