# Operator Console Test Map

The tests should mirror the runtime package shape.

Use this directory like this:

- `tests/views/`: Qt widget and layout tests
- `views/README.md` inside the runtime package documents the current view split
- `tests/theme/`: theme registry, engine, editor, import/export, and stylesheet tests
- `tests/state/`: legacy tests for shared state/snapshot helpers
- `tests/collaboration/`: conversation, task board, timeline, context-pack
  behavior

When you add a new runtime package, add a matching test package instead of
dropping more files into `tests/state/`.

Current direction:

- workflow tests should grow under a dedicated `tests/workflows/` package
- layout persistence tests should move toward a dedicated `tests/layout/`
  package
- theme tests should keep moving out of the top-level `tests/` bucket
- `tests/state/` should shrink as compatibility shims are retired

Top-level `tests/` should stay light.

Keep files at the root only when they cover package-wide helpers such as:

- launcher/help/logging support
- package-entry behavior
- cross-package integration seams that do not belong to one feature area
