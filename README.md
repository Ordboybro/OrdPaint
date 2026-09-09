# OrdPaint

**OrdPaint** — desktop raster graphics editor built with Python 3.12+ and PySide6 / Qt 6.

The project is designed as a portfolio-grade application rather than a single-file Paint clone: document state is isolated in `core`, Qt interaction is kept in `ui`, editing operations are undoable, projects are validated and saved atomically, and quality is checked automatically with Ruff and pytest.

## Features

### Canvas & drawing
- brush and eraser with size, opacity, hardness, spacing and smoothing controls;
- line, rectangle and ellipse tools;
- flood fill with configurable tolerance;
- eyedropper;
- transparent checkerboard canvas;
- zoom around cursor, Ctrl+wheel zoom and pan with Space+LMB or middle mouse;
- rulers and configurable grid;
- cursor coordinates and canvas boundary feedback;
- live previews for shape drawing and transforms.

### Selection & transform
- rectangular selection;
- replace / add / subtract / intersect modes;
- Select All / Deselect;
- animated marching-ants selection border;
- copy / cut / paste through the system clipboard;
- floating paste preview;
- floating transform workflow;
- move and resize with handles;
- aspect-ratio constrained resize;
- flip horizontal / vertical;
- rotate 90° left / right;
- Enter to commit and Escape to cancel.

### Layers
- create, duplicate and delete;
- rename with unique names;
- drag & drop reordering;
- visibility, locking and opacity;
- blend modes;
- merge down and merge visible;
- generated thumbnails;
- layer context menu.

### Projects & reliability
- native `.ordpaint` project format;
- versioned schema and defensive validation;
- atomic project saving with filesystem sync;
- import PNG / JPEG / WebP / BMP;
- export PNG / JPEG / WebP / BMP;
- dirty-state tracking;
- bounded Undo / Redo with transaction support and a memory budget;
- recent projects and persistent UI state;
- autosave and crash-recovery drafts;
- persistent crash diagnostics at `~/.ordpaint/crash.log`;
- bounded project and layer resource limits to reject pathological files safely;
- resize-canvas anchors and image scaling with selectable resampling.

### Editor chrome
- dark charcoal workspace with warm orange accent;
- vector SVG-style tool icons instead of Unicode pseudo-icons;
- dedicated color studio with HEX/RGBA editing and recent swatches;
- dedicated brush settings panel;
- grid settings dialog;
- persistent docks and editor state.

## Architecture

```text
ordpaint/
├── core/
│   ├── document.py
│   ├── layer.py
│   ├── history.py
│   ├── raster.py
│   ├── selection.py
│   ├── clipboard.py
│   ├── transform.py
│   ├── transform_controller.py
│   ├── project.py
│   ├── autosave.py
│   ├── recent.py
│   ├── session.py
│   ├── ui_state.py
│   └── tools.py
└── ui/
    ├── canvas.py
    ├── layer_list.py
    ├── settings_store.py
    ├── application_window.py
    ├── main_window.py
    ├── new_document_dialog.py
    ├── resize_dialog.py
    ├── resize_integration.py
    ├── grid_settings_dialog.py
    ├── polish.py
    └── crash_reporter.py
```

The architectural rule is simple: **core owns document state and editing operations; UI owns Qt interaction and presentation**. History snapshots are created before mutations, while high-frequency UI changes are grouped into transactions. Large histories are also constrained by a memory budget.

## Installation

Requires Python 3.12+.

```bash
python -m venv .venv

# Windows
.venv\\Scripts\\activate

# Linux/macOS
source .venv/bin/activate

python -m pip install -r requirements.txt
python main.py
```

## Quality checks

```bash
ruff check .
ruff format --check .
pytest -q
```

CI runs compile checks, Ruff and the regression suite on every push and pull request. Linux widget tests are isolated per test file under Xvfb to prevent Qt process-lifetime failures from contaminating unrelated tests. Windows runs the full suite natively, and the release workflow builds a Windows PyInstaller package.

## Hotkeys

| Key | Action |
|---|---|
| `B` | Brush |
| `E` | Eraser |
| `L` | Line |
| `R` | Rectangle |
| `O` | Ellipse |
| `G` | Fill |
| `I` | Eyedropper |
| `M` | Selection |
| `Ctrl+T` | Free Transform |
| `Enter` | Commit Transform |
| `Esc` | Cancel Transform |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+C` | Copy |
| `Ctrl+X` | Cut |
| `Ctrl+V` | Paste |
| `Delete` | Delete selection |
| `Ctrl+S` | Save |
| `Ctrl+O` | Open |
| `Ctrl+N` | New |
| `Ctrl+G` | Grid |
| `Ctrl+0` | 100% zoom |
| `Ctrl+Shift+0` | Fit to window |
| `Ctrl+mouse wheel` | Zoom around cursor |
| `Space + LMB` | Pan |
| `Middle mouse` | Pan |

## Design direction

OrdPaint uses a dark, compact editor layout with warm orange accents, a dedicated left tool palette, a central canvas, and right-side layers / color panels. The UI is intentionally dense enough for a graphics editor while keeping the canvas dominant.

## Status

OrdPaint is in release-candidate stabilization. The core editor workflow, project format, layer system, selection/transform workflow, persistence services, defensive resource limits, automated regression suite, and Windows packaging pipeline are implemented. Final release work is desktop QA against the visual reference, packaged-executable smoke testing, and verification on a clean Windows machine.

## License

MIT — see `LICENSE`.
