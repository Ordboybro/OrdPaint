from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from PySide6.QtCore import QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QImage, QPainter, QPixmap

from .document import Document
from .layer import Layer

PROJECT_VERSION = 1
PROJECT_FORMAT = "ordpaint"
MAX_PROJECT_PIXELS = 100_000_000
MAX_LAYERS = 512
MAX_PROJECT_BYTES = 512 * 1024 * 1024
MAX_LAYER_NAME_LENGTH = 128


class ProjectError(RuntimeError):
    pass


def _encode_png(pixmap: QPixmap) -> str:
    data = QByteArray()
    buffer = QBuffer(data)
    if not buffer.open(QIODevice.OpenModeFlag.WriteOnly):
        raise ProjectError("Failed to open project image buffer")
    try:
        if not pixmap.save(buffer, "PNG"):
            raise ProjectError("Failed to encode layer")
    finally:
        buffer.close()
    return bytes(data.toBase64()).decode("ascii")


def _decode_png(value: str) -> QPixmap:
    if not isinstance(value, str) or not value:
        raise ProjectError("Invalid layer image data")
    try:
        raw = QByteArray.fromBase64(value.encode("ascii"))
    except (UnicodeError, ValueError) as exc:
        raise ProjectError("Invalid layer image encoding") from exc
    image = QImage.fromData(raw, "PNG")
    if image.isNull():
        raise ProjectError("Invalid layer image")
    return QPixmap.fromImage(image)


def save_project(document: Document, path: str | Path) -> None:
    destination = Path(path).expanduser()
    if document.width * document.height > MAX_PROJECT_PIXELS:
        raise ProjectError("Document is too large to save safely")
    if not document.layers or len(document.layers) > MAX_LAYERS:
        raise ProjectError("Invalid layer count")

    payload = {
        "format": PROJECT_FORMAT,
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
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if len(data.encode("utf-8")) > MAX_PROJECT_BYTES:
        raise ProjectError("Project file is too large to save safely")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(data)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = temporary.name
        os.replace(temporary_path, destination)
        temporary_path = None
    except OSError as exc:
        raise ProjectError("Could not save project") from exc
    finally:
        if temporary_path:
            try:
                os.unlink(temporary_path)
            except OSError:
                pass


def load_project(path: str | Path) -> Document:
    source = Path(path).expanduser()
    try:
        if source.stat().st_size > MAX_PROJECT_BYTES:
            raise ProjectError("Project file is too large to load safely")
        payload = json.loads(source.read_text(encoding="utf-8"))
    except ProjectError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProjectError("Could not read project") from exc

    if not isinstance(payload, dict):
        raise ProjectError("Invalid project structure")
    if payload.get("format", PROJECT_FORMAT) != PROJECT_FORMAT or payload.get("version") != PROJECT_VERSION:
        raise ProjectError("Unsupported project version")

    try:
        width = int(payload["width"])
        height = int(payload["height"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ProjectError("Invalid project dimensions") from exc
    if width < 1 or height < 1 or width * height > MAX_PROJECT_PIXELS:
        raise ProjectError("Invalid project dimensions")

    raw_layers = payload.get("layers")
    if not isinstance(raw_layers, list) or not raw_layers or len(raw_layers) > MAX_LAYERS:
        raise ProjectError("Invalid project layer count")

    layers: list[Layer] = []
    for item in raw_layers:
        if not isinstance(item, dict):
            raise ProjectError("Invalid layer structure")
        pixmap = _decode_png(item.get("image", ""))
        if pixmap.size().width() != width or pixmap.size().height() != height:
            raise ProjectError("Layer dimensions do not match document")
        try:
            blend_value = int(item.get("blend_mode", int(QPainter.CompositionMode.CompositionMode_SourceOver.value)))
            blend_mode = QPainter.CompositionMode(blend_value)
        except (TypeError, ValueError):
            blend_mode = QPainter.CompositionMode.CompositionMode_SourceOver
        try:
            opacity = int(item.get("opacity", 100))
        except (TypeError, ValueError) as exc:
            raise ProjectError("Invalid layer opacity") from exc
        name = str(item.get("name") or "Layer").strip()[:MAX_LAYER_NAME_LENGTH] or "Layer"
        layers.append(
            Layer(
                name=name,
                pixmap=pixmap,
                visible=bool(item.get("visible", True)),
                opacity=max(0, min(100, opacity)),
                blend_mode=blend_mode,
                locked=bool(item.get("locked", False)),
            )
        )

    try:
        active_index = int(payload.get("active_index", 0))
    except (TypeError, ValueError) as exc:
        raise ProjectError("Invalid active layer index") from exc
    active_index = max(0, min(active_index, len(layers) - 1))
    return Document(width=width, height=height, layers=layers, active_index=active_index)
