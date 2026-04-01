# Compat Matrix

Implementation package for compatibility-matrix guards and shared loaders.

- Keep `dev/scripts/checks/check_compat_matrix.py` and
  `dev/scripts/checks/compat_matrix_smoke.py` as stable root wrappers.
- Keep the YAML/JSON loader and the real matrix implementations here so the
  root does not keep growing flat helper modules.
