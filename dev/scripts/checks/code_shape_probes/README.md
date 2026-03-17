# Code Shape Probes

Implementation namespace for the newer code-shape review probes.

- Keep the stable public entrypoints at `dev/scripts/checks/probe_*.py`.
- Keep the real implementation for the staged code-shape family here so the
  crowded `dev/scripts/checks/` root does not grow further.
- Keep root wrappers as thin backward-compat shims with canonical shim
  metadata (`shim-owner`, `shim-reason`, `shim-expiry`, `shim-target`).
- Keep shared helpers here when multiple code-shape probes would otherwise
  duplicate the same path/signal/signature utilities.
