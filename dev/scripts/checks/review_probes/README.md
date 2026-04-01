# Review Probes

Implementation package for the remaining advisory review probes.

- Keep the stable public entrypoints at `dev/scripts/checks/probe_*.py`.
- Keep the real implementations here so the `checks/` root exposes stable
  wrappers while the implementation grows by family instead of by flat file
  count.
- Keep shared review-probe helpers here when multiple probes need the same
  path-filter or analysis support.
