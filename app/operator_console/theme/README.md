# Operator Console Theme Map

This directory is split by theme responsibility.

- `colors.py`: named theme palettes and registry
- `stylesheet.py`: top-level stylesheet compositor
- `config/`: editable theme tokens, component styles, motion settings, and
  the helpers that resolve those settings into concrete values
- `qss/`: the raw QSS fragment builders that make up the final stylesheet
- `runtime/`: persistence, active-theme state, gallery seeds, and engine logic
- `editor/`: theme editing UI, preview, controls, and motion playground
- `io/`: overlay import/export, file dialogs, and sync helpers

Top-level `theme/` should mostly expose the public API and the two stable
entrypoints: `colors.py` and `stylesheet.py`.

Rule: if a file is just a settings schema, runtime helper, editor widget, or
QSS fragment, it should not sit flat at the top of `theme/`.

Keep the root of `theme/` limited to:

- `colors.py`
- `stylesheet.py`
- `__init__.py`
- this README

Everything else should live in `runtime/`, `editor/`, `io/`, `config/`, or
`qss/`.
