# OrdPaint architecture

OrdPaint follows a layered desktop-application architecture.

```text
Qt entry point
    |
    v
UI (`ordpaint/ui`)
    |
    +--> Canvas / layer widgets / actions
    |
    v
Core (`ordpaint/core`)
    |
    +--> Document -> Layers -> pixels
    +--> History -> snapshots / transactions
    +--> Selection / Clipboard / Transform
    +--> Project persistence
    +--> Session / Autosave / Recent files
```

## Rules

1. Core must not depend on widgets.
2. UI mutates documents through public core APIs.
3. User-visible mutations must be represented by History where appropriate.
4. High-frequency UI changes should be grouped into history transactions.
5. Rendering should avoid unnecessary full-document recomposition where possible.
6. Project loading must validate untrusted file contents and reject unreasonable sizes.
7. Runtime integration belongs in the UI/application layer, not in `main.py`.

## Performance model

The current renderer uses a bounded composite cache. Future optimization should prefer dirty-region rendering and tile-based storage only when profiling demonstrates that the current QImage model is insufficient.

## Persistence

Project data is separate from UI preferences. Project files contain document state; QSettings stores window/session preferences. Autosave creates a recovery copy rather than silently replacing the user's project.
