# OrdPaint release checklist

This checklist is the final gate before calling a build portfolio-ready.

## Automated quality

- [ ] `ruff check .`
- [ ] `ruff format --check .`
- [ ] `QT_QPA_PLATFORM=offscreen pytest -q`
- [ ] Windows release workflow completes successfully

## Runtime smoke test

- [ ] Launch on a clean Windows environment
- [ ] New document
- [ ] Brush / eraser / line / rectangle / ellipse / fill / eyedropper
- [ ] Selection, copy, cut, paste
- [ ] Transform move / resize / flip / rotate / commit / cancel
- [ ] Add / duplicate / rename / delete layers
- [ ] Reorder layers with drag and drop
- [ ] Merge down / merge visible
- [ ] Save / Save As / Open / Export
- [ ] Close confirmation for unsaved changes
- [ ] Autosave and recovery
- [ ] Recent files
- [ ] Restart and verify UI settings

## Visual QA

- [ ] Compare the main window against the OrdPaint reference image
- [ ] Check spacing, typography, panel proportions, icons and accent states
- [ ] Check hover / pressed / disabled / selected states
- [ ] Check high-DPI scaling
- [ ] Check 100%, fit, zoom and pan

## Performance QA

- [ ] 2048x2048 document with 10 layers
- [ ] 4096x4096 document with multiple layers
- [ ] Long brush strokes remain responsive
- [ ] Transform remains responsive
- [ ] Zoom/pan remain responsive
- [ ] Memory does not grow without bound during normal editing

## Release

- [ ] Version updated
- [ ] README reflects the shipped feature set
- [ ] Screenshots added
- [ ] Demo GIF/video added
- [ ] Windows artifact tested
- [ ] GitHub Release created

A green CI run alone is not a substitute for the runtime and visual checks above.
