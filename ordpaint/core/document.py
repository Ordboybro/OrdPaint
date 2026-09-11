from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QPainter, QPixmap

from .layer import Layer
from .layer_tree import LayerGroup, LayerTree


@dataclass
class Document:
    width: int = 1200
    height: int = 800
    layers: list[Layer] = field(default_factory=list)
    active_index: int = 0
    layer_tree: LayerTree | None = field(default=None, repr=False)
    revision: int = field(default=0, init=False, repr=False, compare=False)
    _composite_cache: OrderedDict[tuple[int, int, int, int], QPixmap] = field(default_factory=OrderedDict, init=False, repr=False, compare=False)
    _COMPOSITE_CACHE_LIMIT = 4
    _COMPOSITE_CACHE_MAX_PIXELS = 4_000_000

    def __post_init__(self) -> None:
        if self.width < 1 or self.height < 1:
            raise ValueError("Document dimensions must be positive")
        if not self.layers:
            self.layers = [self._new_layer("Layer 1")]
        old_active = self.layers[max(0, min(self.active_index, len(self.layers) - 1))]
        if self.layer_tree is None:
            self.layer_tree = LayerTree(children=list(self.layers))
        self._normalize_tree()
        self._sync_layers_from_tree(preferred_active=old_active)

    def _new_layer(self, name: str) -> Layer:
        pixmap = QPixmap(self.width, self.height)
        pixmap.fill(Qt.GlobalColor.transparent)
        return Layer(name, pixmap)

    def _normalize_tree(self) -> None:
        assert self.layer_tree is not None
        valid = {id(layer): layer for layer in self.layers}
        seen: set[int] = set()
