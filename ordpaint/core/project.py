from __future__ import annotations

import base64
import json
import os
import tempfile
from pathlib import Path

from PySide6.QtCore import QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QImageReader, QPainter, QPixmap

from .document import Document
from .layer import Layer

PROJECT_VERSION = 1
PROJECT_FORMAT = "ordpaint"
MAX_PROJECT_PIXELS = 100_000_000
MAX_TOTAL_LAYER_PIXELS = 128_000_000
MAX_LAYERS = 512
MAX_PROJECT_BYTES = 512 * 1024 * 1024
MAX_LAYER_NAME_LENGTH = 128


class ProjectError(RuntimeError):
    """User-facing project I/O or validation failure."""


def _encode_png(pixmap: QPixmap) -> str:
    data = QByteArray()
    buffer = QBuffer(data)
    if not buffer.open(QIODevice.OpenModeFlag.WriteOnly):
        raise ProjectError("Не удалось подготовить изображение проекта.")
    try:
        if not pixmap.save(buffer, "PNG"):
            raise ProjectError("Не удалось закодировать слой проекта.")
    finally:
        buffer.close()
    return bytes(data.toBase64()).decode("ascii")


def _decode_png(value: str) -> QPixmap:
    if not isinstance(value, str) or not value:
        raise ProjectError("У слоя отсутствуют данные изображения.")
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ProjectError("Данные изображения имеют неверную кодировку.") from exc
    if len(encoded) > MAX_PROJECT_BYTES:
        raise ProjectError("Данные изображения слишком велики.")
    try:
        raw_bytes = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ProjectError("Повреждены данные изображения слоя.") from exc
    if not raw_bytes or len(raw_bytes) > MAX_PROJECT_BYTES:
        raise ProjectError("Данные изображения слишком велики.")
    raw = QByteArray(raw_bytes)
    buffer = QBuffer(raw)
    if not buffer.open(QIODevice.OpenModeFlag.ReadOnly):
        raise ProjectError("Не удалось открыть данные изображения слоя.")
    reader = QImageReader(buffer, b"PNG")
    size = reader.size()
    if not size.isValid() or size.width() < 1 or size.height() < 1:
        raise ProjectError("Повреждено изображение слоя.")
    if size.width() * size.height() > MAX_PROJECT_PIXELS:
        raise ProjectError("Изображение слоя слишком большое для безопасной загрузки.")
    image = reader.read()
    if image.isNull():
        raise ProjectError(reader.errorString() or "Не удалось декодировать изображение слоя.")
    return QPixmap.fromImage(image)


def _validate_document(document: Document) -> None:
    if document.width < 1 or document.height < 1:
        raise ProjectError("Некорректные размеры документа.")
    document_pixels = document.width * document.height
    if document_pixels > MAX_PROJECT_PIXELS:
        raise ProjectError("Документ слишком большой для безопасного сохранения.")
    if not document.layers or len(document.layers) > MAX_LAYERS:
        raise ProjectError("Некорректное количество слоёв.")
    if document_pixels * len(document.layers) > MAX_TOTAL_LAYER_PIXELS:
        raise ProjectError("В проекте слишком много данных слоёв.")
    if not 0 <= document.active_index < len(document.layers):
        raise ProjectError("Некорректный активный слой.")
    for layer in document.layers:
        if layer.pixmap.isNull() or layer.pixmap.width() != document.width or layer.pixmap.height() != document.height:
            raise ProjectError("Размер слоя не совпадает с размером документа.")
        if not 0 <= int(layer.opacity) <= 100:
            raise ProjectError("Некорректная непрозрачность слоя.")
        if len(layer.name) > MAX_LAYER_NAME_LENGTH:
            raise ProjectError("Название слоя слишком длинное.")


def save_project(document: Document, path: str | Path) -> None:
    _validate_document(document)
    destination = Path(path).expanduser()
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
    encoded = data.encode("utf-8")
    if len(encoded) > MAX_PROJECT_BYTES:
        raise ProjectError("Файл проекта слишком большой для безопасного сохранения.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile("wb", dir=destination.parent, prefix=f".{destination.name}.", suffix=".tmp", delete=False) as temporary:
            temporary.write(encoded)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = temporary.name
        os.replace(temporary_path, destination)
        temporary_path = None
    except OSError as exc:
        raise ProjectError(f"Не удалось сохранить проект: {exc}") from exc
    finally:
        if temporary_path:
            try:
                os.unlink(temporary_path)
            except OSError:
                pass


def load_project(path: str | Path) -> Document:
    source = Path(path).expanduser()
    try:
        size = source.stat().st_size
        if size > MAX_PROJECT_BYTES:
            raise ProjectError("Файл проекта слишком большой для безопасной загрузки.")
        if size == 0:
            raise ProjectError("Файл проекта пустой или повреждён.")
        payload = json.loads(source.read_text(encoding="utf-8"))
    except ProjectError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProjectError("Не удалось прочитать проект: файл повреждён или недоступен.") from exc

    if not isinstance(payload, dict):
        raise ProjectError("Повреждена структура проекта.")
    if payload.get("format") != PROJECT_FORMAT:
        raise ProjectError("Это не файл проекта OrdPaint.")
    if payload.get("version") != PROJECT_VERSION:
        raise ProjectError(f"Версия проекта не поддерживается: {payload.get('version')!r}.")

    try:
        width = int(payload["width"])
        height = int(payload["height"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ProjectError("В проекте указаны некорректные размеры.") from exc
    document_pixels = width * height
    if width < 1 or height < 1 or document_pixels > MAX_PROJECT_PIXELS:
        raise ProjectError("В проекте указаны недопустимые размеры документа.")

    raw_layers = payload.get("layers")
    if not isinstance(raw_layers, list) or not raw_layers or len(raw_layers) > MAX_LAYERS:
        raise ProjectError("В проекте указано некорректное количество слоёв.")
    if document_pixels * len(raw_layers) > MAX_TOTAL_LAYER_PIXELS:
        raise ProjectError("Проект слишком велик для безопасной загрузки.")

    layers: list[Layer] = []
    for item in raw_layers:
        if not isinstance(item, dict):
            raise ProjectError("Повреждена структура слоя.")
        pixmap = _decode_png(item.get("image", ""))
        if pixmap.width() != width or pixmap.height() != height:
            raise ProjectError("Размер изображения слоя не совпадает с размером документа.")
        try:
            blend_value = int(item.get("blend_mode", int(QPainter.CompositionMode.CompositionMode_SourceOver.value)))
            blend_mode = QPainter.CompositionMode(blend_value)
        except (TypeError, ValueError) as exc:
            raise ProjectError("В слое указан неизвестный режим смешивания.") from exc
        try:
            opacity = int(item.get("opacity", 100))
        except (TypeError, ValueError) as exc:
            raise ProjectError("В слое указана некорректная непрозрачность.") from exc
        if not 0 <= opacity <= 100:
            raise ProjectError("В слое указана некорректная непрозрачность.")
        raw_name = item.get("name", "Layer")
        if not isinstance(raw_name, str):
            raise ProjectError("Название слоя имеет неверный тип данных.")
        name = raw_name.strip()[:MAX_LAYER_NAME_LENGTH] or "Layer"
        layers.append(Layer(name=name, pixmap=pixmap, visible=bool(item.get("visible", True)), opacity=opacity, blend_mode=blend_mode, locked=bool(item.get("locked", False))))

    try:
        active_index = int(payload.get("active_index", 0))
    except (TypeError, ValueError) as exc:
        raise ProjectError("Некорректный активный слой.") from exc
    if not 0 <= active_index < len(layers):
        raise ProjectError("Некорректный индекс активного слоя.")
    return Document(width=width, height=height, layers=layers, active_index=active_index)
