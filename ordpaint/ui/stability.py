from __future__ import annotations

from ordpaint.core.tools import Tool
from ordpaint.ui.canvas import Canvas
from ordpaint.ui import main_window as main_window_module


_LEGACY_TOOL_PALETTE = {
    Tool.BRUSH,
    Tool.ERASER,
    Tool.LINE,
    Tool.RECTANGLE,
    Tool.ELLIPSE,
    Tool.FILL,
    Tool.EYEDROPPER,
    Tool.SELECT_RECT,
}


def install() -> None:
    """Keep legacy shell construction compatible while newer tools install themselves later."""
    if getattr(Canvas, "_ordpaint_stability_installed", False):
        return

    original_canvas_init = Canvas.__init__
    original_set_document = Canvas.set_document
    original_create_tools_dock = main_window_module.MainWindow._create_tools_dock

    def canvas_init(self, document, parent=None):
        original_canvas_init(self, document, parent)
        self.selection.set_document_size(document.width, document.height)

    def set_document(self, document):
        original_set_document(self, document)
        self.selection.set_document_size(document.width, document.height)

    def create_tools_dock(self):
        original_info = main_window_module.TOOL_INFO
        main_window_module.TOOL_INFO = {
            tool: info for tool, info in original_info.items() if tool in _LEGACY_TOOL_PALETTE
        }
        try:
            original_create_tools_dock(self)
        finally:
            main_window_module.TOOL_INFO = original_info

    Canvas.__init__ = canvas_init
    Canvas.set_document = set_document
    main_window_module.MainWindow._create_tools_dock = create_tools_dock
    Canvas._ordpaint_stability_installed = True
