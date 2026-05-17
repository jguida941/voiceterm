# Probe Support Helpers

Internal helper package for lightweight probe bootstrap/runtime utilities.

- `bootstrap.py`: shared probe parser/report helpers plus reusable scan-corpus
  loaders such as the Python call-site counter used by context-blind probes.

Layout rule:
- Keep runnable probe entrypoints at the `checks/` root as compatibility
  shims.
- Keep import-safe helper modules here so probes can reuse shared bootstrap
  logic without pulling in heavier report-rendering packages.
