# Python Analysis Helpers

Internal helper package for Python-only structural guards.

- `cyclic_imports_core.py`: shared graph/report logic for
  `check_python_cyclic_imports.py`.
- `cyclic_imports_graph.py`: import-graph construction and SCC traversal.
- `design_complexity_core.py`: branch/return threshold analysis for
  `check_python_design_complexity.py`.

Layout rule:
- Keep the runnable guard entrypoints at the `checks/` root.
- Keep reusable Python-analysis internals here so the root stays flatter and
  easier to scan.
