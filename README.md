# OrdPaint

**OrdPaint** — desktop raster graphics editor built with Python 3 and PySide6 / Qt 6.

The project is designed as a real portfolio-grade application rather than a single-file Paint clone: document state is isolated in `core`, Qt is kept in `ui`, editing operations are undoable, and quality is checked automatically with Ruff and pytest.

## Features

### Canvas & drawing
- brush and eraser;
- line, rectangle and ellipse tools;
- flood fill with tolerance;
- eyedropper;
- configurable brush size and opacity;
- transparent checkerboard canvas;
- zoom and pan;
- optional rulers and grid;
- cursor position feedback;
- smooth previews for shape drawing and transform operations.

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
- visibility and locking;
- opacity with history transaction support;
- blend modes;
- merge down and merge visible;
- generated thumbnails;
- layer context menu.

### Projects & reliability
- native `.ordpaint` project format;
- versioned project schema;
- atomic project saving;
- import PNG / JPEG / WebP / BMP;
- export PNG / JPEG / WebP / BMP;
- dirty-state tracking;
- Undo / Redo;
- recent projects;
- persistent Qt UI settings;
- autosave;
- crash-recovery draft support;
- safe handling of invalid recovery data.

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
    └── main_window.py
```

The main architectural rule is simple: **core owns document state and editing operations; UI owns Qt interaction and presentation**. History snapshots are created before mutations, while high-frequency UI changes such as sliders use transactions so one user gesture becomes one undo step.

## Installation

Requires Python 3.12+.

```bash
python -m venv .venv

# Windows
.venv\\Scripts\\activate

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

## Quality checks

```bash
ruff check .
ruff format .
pytest -q
```

CI runs the linter, formatter and test suite on every push and pull request. On pushes to `main`, Ruff formatting changes are committed automatically so the branch stays consistently formatted. Qt tests use the `offscreen` platform in CI.

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
| `Ctrl+0` | 100% zoom |
| `Ctrl+Shift+0` | Fit to window |
| `Ctrl+mouse wheel` | Zoom |
| `Space + LMB` | Pan |
| `Middle mouse` | Pan |

## Design direction

OrdPaint uses a dark, compact editor layout with warm orange accents, a dedicated left tool palette, a central canvas, and right-side layers / color panels. The UI is intentionally dense enough for a graphics editor while keeping the canvas dominant.

## Status

OrdPaint is in the final stabilization and polish stage. The core editor workflow is implemented; remaining work should focus on real-world runtime testing, visual refinement, performance profiling on large documents, broader regression coverage, packaging, and release documentation.

## License

MIT — see `LICENSE`.
