# OrdPaint — Portfolio Presentation

## One-line pitch

OrdPaint is a desktop raster graphics editor built with Python, PySide6 and Qt 6, with a layered document model, non-destructive transform workflow, transactional history, validated native projects, autosave/recovery and automated cross-platform quality checks.

## What this project demonstrates

- Python application architecture beyond a single script.
- Separation of document/core logic from Qt presentation.
- Raster graphics operations and alpha compositing.
- Undo/redo transactions and dirty-state management.
- Defensive file parsing and resource limits.
- Desktop UI engineering with persistent docks and keyboard-driven workflows.
- Automated testing of both core behavior and Qt integration.
- CI/CD and Windows packaging with PyInstaller.

## Demo flow

1. Create a 1920×1080 transparent document.
2. Draw with brush and eraser; change hardness, spacing and smoothing.
3. Use fill with a non-zero tolerance.
4. Create, rename, reorder, lock and blend multiple layers.
5. Select an area and copy/cut/paste it.
6. Start Free Transform, resize, move, flip, rotate, then commit.
7. Undo and redo the complete transform as one logical operation.
8. Change canvas size using an anchor.
9. Scale the image using the fast or smooth resampler.
10. Save an `.ordpaint` project, close it, reopen it and verify the recent-project list.
11. Export the final image to PNG.

## Architecture story

The important design decision is that `Document`, `Layer`, `History`, `Selection`, `TransformState` and project persistence do not depend on the main window layout. Qt widgets translate user input into those core operations. This makes the project easier to test and keeps UI refactors from changing the document model.

## Engineering highlights

### Reliability

Native projects are versioned and validated before loading. Saves are written atomically. Autosave and recovery are handled separately from the normal project path. Invalid projects are rejected instead of being partially applied.

### Performance

The canvas uses a bounded composite cache for smaller documents. Large overlay calculations operate on visible ranges. History has both a snapshot-count limit and an approximate memory budget, preventing an accidental sequence of edits from growing without bound.

### Testing

The suite covers document mutations, raster operations, project hardening, history transactions, transforms, selection, persistence, dialogs and Qt integration. Linux widget tests run in isolated processes under Xvfb because Qt process lifetime is a known source of flaky headless failures.

## Final visual QA

For a portfolio screenshot or demo video, use a clean Windows build and verify the editor against the intended reference layout. The reference image itself is the final visual source of truth; automated tests cannot prove pixel-level visual similarity.
