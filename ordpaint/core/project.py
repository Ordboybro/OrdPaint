from __future__ import annotations

import base64
import binascii
import json
import os
import tempfile
from pathlib import Path

from PySide6.QtCore import QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QImageReader, QPainter, QPixmap

from .document import Document
from .layer import Layer
from .layer_tree import LayerGroup, LayerTree

PROJECT_VERSION = 2
SUPPORTED_PROJECT_VERSIONS = {1, 2}
PROJECT_FORMAT = "ordpaint"
MAX_PROJECT_PIXELS = 100_000_000
MAX_TOTAL_LAYER_PIXELS = 128_000_000
MAX_LAYERS = 512
MAX_PROJECT_BYTES = 512 * 1024 * 1024
MAX_LAYER_NAME_LENGTH = 128
MAX_GROUPS = 512


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
        if len(encoded) > MAX_PROJECT_BYTES:
            raise ProjectError("Данные изображения слишком велики.")
        raw_bytes = base64.b64decode(encoded, validate=True)
    except (UnicodeEncodeError, ValueError, binascii.Error) as exc:
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


def _iter_groups(node):
    if isinstance(node, LayerGroup):
        yield node
        for child in node.children:
            yield from _iter_groups(child)


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
    assert document.layer_tree is not None
    tree_layers = list(document.layer_tree.iter_layers())
    if len(tree_layers) != len(document.layers) or {id(layer) for layer in tree_layers} != {id(layer) for layer in document.layers}:
        raise ProjectError("Иерархия слоёв не соответствует документу.")
    groups = sum(1 for node in document.layer_tree.children for _ in _iter_groups(node))
    if groups > MAX_GROUPS:
        raise ProjectError("В проекте слишком много групп.")
    for layer in document.layers:
        if layer.pixmap.isNull() or layer.pixmap.width() != document.width or layer.pixmap.height() != document.height:
            raise ProjectError("Размер слоя не совпадает с размером документа.")
        if not 0 <= int(layer.opacity) <= 100:
            raise ProjectError("Некорректная непрозрачность слоя.")
        if len(layer.name) > MAX_LAYER_NAME_LENGTH:
            raise ProjectError("Название слоя слишком длинное.")


def _serialize_tree(nodes, layer_indices: dict[int, int]) -> list[dict]:
    result = []
    for node in nodes:
        if isinstance(node, LayerGroup):
            result.append({"type": "group", "name": node.name, "visible": node.visible, "opacity": node.opacity, "locked": node.locked, "children": _serialize_tree(node.children, layer_indices)})
        else:
            result.append({"type": "layer", "index": layer_indices[id(node)]})
    return result


def save_project(document: Document, path: str | Path) -> None:
    _validate_document(document)
    destination = Path(path).expanduser()
    layer_indices = {id(layer): index for index, layer in enumerate(document.layers)}
    payload = {
        "format": PROJECT_FORMAT,
        "version": PROJECT_VERSION,
        "width": document.width,
        "height": document.height,
        "active_index": document.active_index,
        "layers": [{"name": layer.name, "visible": layer.visible, "opacity": layer.opacity, "locked": layer.locked, "blend_mode": int(layer.blend_mode.value), "image": _encode_png(layer.pixmap)} for layer in document.layers],
        "layer_tree": _serialize_tree(document.layer_tree.children, layer_indices),
    }
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
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


def _load_layer_items(raw_layers, width: int, height: int) -> list[Layer]:
    if not isinstance(raw_layers, list) or not raw_layers or len(raw_layers) > MAX_LAYERS:
        raise ProjectError("В проекте указано некорректное количество слоёв.")
    if width * height * len(raw_layers) > MAX_TOTAL_LAYER_PIXELS:
        raise ProjectError("Проект слишком велик для безопасной загрузки.")
    layers: list[Layer] = []
    for item in raw_layers:
        if not isinstance(item, dict):
            raise ProjectError("Повреждена структура слоя.")
        pixmap = _decode_png(item.get("image", ""))
        if pixmap.width() != width or pixmap.height() != height:
            raise ProjectError("Размер изображения слоя не совпадает с размером документа.")
        try:
            blend_mode = QPainter.CompositionMode(int(item.get("blend_mode", int(QPainter.CompositionMode.CompositionMode_SourceOver.value))))
            opacity = int(item.get("opacity", 100))
        except (TypeError, ValueError) as exc:
            raise ProjectError("В слое указаны некорректные параметры.") from exc
        if not 0 <= opacity <= 100:
            raise ProjectError("В слое указана некорректная непрозрачность.")
        raw_name = item.get("name", "Layer")
        if not isinstance(raw_name, str):
            raise ProjectError("Название слоя имеет неверный тип данных.")
        name = raw_name.strip()[:MAX_LAYER_NAME_LENGTH] or "Layer"
        layers.append(Layer(name=name, pixmap=pixmap, visible=bool(item.get("visible", True)), opacity=opacity, blend_mode=blend_mode, locked=bool(item.get("locked", False))))
    return layers


def _deserialize_tree(raw_nodes, layers: list[Layer]) -> LayerTree:
    if not isinstance(raw_nodes, list):
        raise ProjectError("Повреждена иерархия слоёв.")
    seen: set[int] = set()
    groups = 0

    def parse(nodes):
        nonlocal groups
        result = []
        for item in nodes:
            if not isinstance(item, dict):
                raise ProjectError("Повреждена иерархия слоёв.")
            kind = item.get("type")
            if kind == "layer":
                try:
                    index = int(item["index"])
                except (KeyError, TypeError, ValueError) as exc:
                    raise ProjectError("Некорректная ссылка на слой.") from exc
                if not 0 <= index < len(layers) or index in seen:
                    raise ProjectError("Некорректная или повторная ссылка на слой.")
                seen.add(index)
                result.append(layers[index])
            elif kind == "group":
                groups += 1
                if groups > MAX_GROUPS:
                    raise ProjectError("В проекте слишком много групп.")
                try:
                    opacity = int(item.get("opacity", 100))
                except (TypeError, ValueError) as exc:
                    raise ProjectError("Некорректная непрозрачность группы.") from exc
                if not 0 <= opacity <= 100:
                    raise ProjectError("Некорректная непрозрачность группы.")
                children = parse(item.get("children"))
                result.append(LayerGroup(str(item.get("name", "Group"))[:MAX_LAYER_NAME_LENGTH] or "Group", children, bool(item.get("visible", True)), opacity, bool(item.get("locked", False))))
            else:
                raise ProjectError("Неизвестный тип узла иерархии.")
        return result

    children = parse(raw_nodes)
    if seen != set(range(len(layers))):
        raise ProjectError("Иерархия не содержит все слои документа.")
    return LayerTree(children)


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
    version = payload.get("version")
    if version not in SUPPORTED_PROJECT_VERSIONS:
        raise ProjectError(f"Версия проекта не поддерживается: {version!r}.")
    try:
        width = int(payload["width"])
        height = int(payload["height"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ProjectError("В проекте указаны некорректные размеры.") from exc
    if width < 1 or height < 1 or width * height > MAX_PROJECT_PIXELS:
        raise ProjectError("В проекте указаны недопустимые размеры документа.")
    layers = _load_layer_items(payload.get("layers"), width, height)
    try:
        active_index = int(payload.get("active_index", 0))
    except (TypeError, ValueError) as exc:
        raise ProjectError("Некорректный активный слой.") from exc
    if not 0 <= active_index < len(layers):
        raise ProjectError("Некорректный индекс активного слоя.")
    tree = LayerTree(list(layers)) if version == 1 else _deserialize_tree(payload.get("layer_tree"), layers)
    return Document(width, height, layers, active_index, tree)
