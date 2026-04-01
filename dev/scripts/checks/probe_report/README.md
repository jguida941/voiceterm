# Probe Report Helpers

Internal helper package for aggregated review-probe rendering.

- `renderer_core.py`: markdown/terminal renderer implementation.
- `render.py`: canonical implementation module behind the stable
  `dev/scripts/checks/probe_report_render.py` wrapper.
- `support.py`: allowlist, snippet, diff, and aggregation helpers.
- `practices.py`: best-practice matching catalog for probe findings.
- `practices_concurrency.py`: concurrency-focused remediation guidance.
- `practices_rust.py`: Rust ownership/error guidance.

Layout rule:
- Keep `run_probe_report.py` and `probe_report_render.py` at the `checks/`
  root as the public runnable/importable surfaces.
- Keep the implementation counterpart for `probe_report_render.py` here so the
  root entrypoint can stay a thin wrapper.
- `run_probe_report.py` should stay a thin fallback runner over the shared
  probe registry/policy, not a second place that hard-codes probe filenames.
- Keep the renderer internals here so the `checks/` root does not accumulate
  report-only support modules.
