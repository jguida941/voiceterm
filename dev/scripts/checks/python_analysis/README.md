# Python Analysis

Implementation package for Python-focused guards and shared helpers.

- `check_python_*.py`: canonical implementation modules for the Python
  broad-except, cyclic-imports, design-complexity, dict-schema,
  global-mutable, subprocess-policy, and suppression-debt guards.
- `python_default_trap_core.py`: shared AST helpers for default-state and
  global-mutable scans.
- `cyclic_imports_core.py`: shared graph/report logic for
  `check_python_cyclic_imports.py`.
- `cyclic_imports_graph.py`: import-graph construction and SCC traversal.
- `design_complexity_core.py`: branch/return threshold analysis for
  `check_python_design_complexity.py`.
- `probe_single_use_helpers.py`: internal implementation for the
  `probe_single_use_helpers.py` entrypoint, including cross-file call-site and
  relocation detection over the changed-file set.

Layout rule:
- Keep the stable public entrypoints at the `checks/` root as thin wrappers.
- Keep the real Python-analysis implementation here so the root stays flatter
  and easier to scan.
