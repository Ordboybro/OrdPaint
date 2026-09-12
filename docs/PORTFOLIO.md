# OrdPaint — Portfolio Presentation

## One-line pitch

OrdPaint is a desktop raster graphics editor built with Python, PySide6 and Qt 6, with a layered document model, pixel-mask selections, nested layer organization, pressure-aware brush dynamics, transform workflows, transactional history, validated native projects, autosave/recovery and automated cross-platform quality checks.

## What this project demonstrates

- Python application architecture beyond a single script.
- Separation of document/core logic from Qt presentation.
- Raster graphics operations and alpha compositing.
- Pixel-accurate selection masks with replace/add/subtract/intersect operations.
- Nested layer-group modeling and safe hierarchy moves.
- Pressure, dynamics, spacing and stabilizer primitives for a brush engine.
- Undo/redo transactions and dirty-state management.
- Defensive file parsing and resource limits.
- Desktop UI engineering with persistent docks and keyboard-driven workflows.
- Automated testing of core behavior and Qt integration.
- CI/CD and Windows packaging with PyInstaller.

## Demo flow

1. Create a 1920×1080 transparent document.
2. Draw with brush and eraser; demonstrate pressure, hardness, spacing and smoothing.
3. Use fill with a non-zero tolerance.
4. Make rectangular, elliptical, polygon and lasso selections.
5. Demonstrate replace/add/subtract/intersect selection modes.
6. Create, rename, reorder, lock and blend multiple layers; show nested group organization.
7. Copy/cut/paste selected content and verify selection clipping.
8. Start Free Transform, resize, move, flip, rotate and apply an arbitrary angle.
9. Crop to the active selection and demonstrate image operations.
10. Undo and redo the complete operation as one logical action.
11. Change canvas size using an anchor and scale with fast/smooth resampling.
12. Save an `.ordpaint` project, close it, reopen it and verify recovery/recent-project behavior.
13. Export the final image to PNG.

## Architecture story

The important design decision is that `Document`, `Layer`, `LayerGroup`, `LayerTree`, `History`, `Selection`, `SelectionMask`, `BrushEngine`, `TransformState` and project persistence do not depend on the main window layout. Qt widgets translate user input into those core operations. This keeps UI refactors from changing the document model and makes the most important behavior unit-testable.

## Engineering highlights

### Reliability

Native projects are versioned and validated before loading. Saves are written atomically. Autosave and recovery are handled separately from the normal project path. Invalid projects are rejected instead of being partially applied.

### Performance

The canvas uses a bounded composite cache for smaller documents. Large overlay calculations operate on visible ranges. History has both a snapshot-count limit and an approximate memory budget. Selection masks are kept at document resolution so editing operations can use exact pixel coverage rather than bounding rectangles.

### Testing

The suite covers document mutations, raster operations, project hardening, history transactions, transforms, selection, nested layer trees, brush dynamics, image operations, persistence, dialogs and Qt integration. Linux widget tests run in isolated processes under Xvfb because Qt process lifetime is a known source of flaky headless failures.

## Final visual QA

For the final portfolio screenshot or demo video, use a clean Windows build and compare the editor against the supplied reference layout. The reference image is the final visual source of truth; automated tests cannot prove pixel-level visual similarity. The exact 1:1 pass is intentionally the last visual stage so engineering changes do not have to be repeated.
