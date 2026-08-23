from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, Qt
from PySide6.QtGui import QImage, QPixmap

from .document import Document
from .layer import Layer

PROJECT_VERSION = 1


class ProjectError(RuntimeError):
    pass


def _encode_png(pixmap: QPixmap) -> str:
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not pixmap.save(buffer, "PNG"):
        raise ProjectError("Failed to encode layer")
    buffer.close()
    return bytes(data.toBase64()).decode("ascii")


def _decode_png(value: str) -> QPixmap:
    raw = QByteArray.fromBase64(value.encode("ascii"))
    image = QImage.fromData(raw, "PNG")
    if image.isNull():
        raise ProjectError("Invalid layer image")
    return QPixmap.fromImage(image)


def save_project(document: Document, path: str | Path) -> None:
    payload = {
        "version": PROJECT_VERSION,
        "width": document.width,
        "height": document.height,
        "active_index": document.active_index,
        "layers": [
            {
                "name": layer.name,
                "visible": layer.visible,
                "opacity": layer.opacity,
                "locked": layer.locked,
                "blend_mode": int(layer.blend_mode.value),
                "image": _encode_png(layer.pixmap),
            }
            for layer in document.layers
        ],
    }
    Path(path).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def load_project(path: str | Path) -> Document:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectError("Could not read project") from exc
    if payload.get("version") != PROJECT_VERSION:
        raise ProjectError("Unsupported project version")
    width = int(payload["width"])
    height = int(payload["height"])
    raw_layers = payload.get("layers")
    if width < 1 or height < 1 or not isinstance(raw_layers, list) or not raw_layers:
        raise ProjectError("Invalid project structure")
    layers: list[Layer] = []
    for item in raw_layers:
        pixmap = _decode_png(item["image"])
        if pixmap.size().width() != width or pixmap.size().height() != height:
            raise ProjectError("Layer dimensions do not match document")
        try:
            blend_mode = Qt.CompositionMode(int(item.get("blend_mode", int(Qt.CompositionMode.CompositionMode_SourceOver.value))))
        except ValueError:
            blend_mode = Qt.CompositionMode.CompositionMode_SourceOver
        layers.append(Layer(
            name=str(item.get("name") or "Layer"),
            pixmap=pixmap,
            visible=bool(item.get("visible", True)),
            opacity=max(0, min(100, int(item.get("opacity", 100)))),
            blend_mode=blend_mode,
            locked=bool(item.get("locked", False)),
        ))
    active_index = max(0, min(int(payload.get("active_index", 0)), len(layers) - 1))
    return Document(width=width, height=height, layers=layers, active_index=active_index)
