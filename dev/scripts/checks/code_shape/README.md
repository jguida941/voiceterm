# Code Shape Guards

Implementation package for the code-shape guard family.

- Keep the stable public entrypoints at `dev/scripts/checks/check_*.py`.
- Keep the real implementations here so the `dev/scripts/checks/` root only
  carries thin compatibility wrappers for this family.
- Keep shared policy/support modules here as the canonical implementation
  surface; root `code_shape_*.py` files are compatibility shims only.
