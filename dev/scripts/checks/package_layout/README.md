# Package Layout

Helper logic for `check_package_layout.py`.

- Keep the public guard entrypoint at `dev/scripts/checks/check_package_layout.py`.
- Keep the implementation under `dev/scripts/checks/package_layout/command.py`
  so the root entrypoint can stay a thin compatibility wrapper.
- Keep the public shim-debt probe entrypoint at
  `dev/scripts/checks/probe_compatibility_shims.py`, with implementation
  under `dev/scripts/checks/package_layout/probe_compatibility_shims.py` so
  crowded-root policy can treat both root files as thin wrappers over the same
  package-owned shim-governance surface.
- Keep the staged code-shape probe family under
  `dev/scripts/checks/code_shape_probes/` while the public
  `probe_{cognitive_complexity,identifier_density,fan_out,side_effect_mixing,match_arm_complexity,tuple_return_complexity,...}.py`
  entrypoints stay as thin wrappers in the root.
- Keep the term-consistency probe implementation under
  `dev/scripts/checks/term_consistency/` while
  `dev/scripts/checks/probe_term_consistency.py` stays a thin wrapper in the
  root.
- Keep the generated-surface sync entrypoint at
  `dev/scripts/checks/package_layout/check_instruction_surface_sync.py`, with
  implementation under
  `dev/scripts/checks/package_layout/instruction_surface_sync.py` so the
  crowded `checks/` root does not grow another flat runner.
- Keep shared import/bootstrap behavior in
  `dev/scripts/checks/package_layout/bootstrap.py` so package-layout modules do
  not each grow their own repo-root/path-repair logic.
- Keep `package_layout.rules` and `package_layout.probe_compatibility_shims`
  as stable import surfaces even when internal helpers are split further.
- Current internal split keeps focused helpers in `rule_models.py`,
  `rule_parsing.py`, `shim_validation.py`, `probe_compatibility_rules.py`,
  `probe_compatibility_scan.py`, and `probe_compatibility_hints.py`.
- Keep repo-policy rule parsing and layout enforcement helpers here so the
  `checks/` root stays reserved for runnable surfaces.
- Current rule families cover flat-root placement, crowded-family namespace
  moves plus crowded-family baseline/adoption blocking, docs sync for new
  namespace roots, and crowded-directory freeze/baseline reporting for
  self-hosting organization governance.
- Compatibility shims are now a first-class policy concept here: wrapper shape
  is AST-validated, metadata fields can be required by repo policy, and
  approved shims are tracked separately from real implementation density during
  crowded-root/family baseline scans.
- The shim probe now has two governance layers:
  repo policy can declare explicit long-lived public shims, and every other
  valid shim is treated as temporary. Temporary shims are scanned for
  repo-visible callers (imports, docs/config/workflow references, script-path
  mentions) so the probe can distinguish `migrate-callers` debt from
  `remove-now` debt once a wrapper has gone unused.
- Usage scanning should exclude generated artifact roots such as
  `dev/reports/` through repo policy so probe output does not self-justify
  wrappers by reading its own emitted reports.
- The crowded `checks/` root now recognizes any thin wrapper that targets the
  `package_layout` namespace; the policy no longer hard-codes one exact import
  line such as `from package_layout.command import main`.
- Canonical shim metadata keys are `owner`, `reason`, `expiry`, and `target`.
- Valid shim example:
  ```python
  """Backward-compat shim -- use `package_layout.command`."""
  # shim-owner: tooling/code-governance
  # shim-reason: preserve the stable check entrypoint during package split
  # shim-expiry: 2026-06-30
  # shim-target: dev/scripts/checks/package_layout/command.py
  from package_layout.command import main
  ```
- Invalid shim example:
  a short wrapper that adds real logic or omits required metadata. Those files
  stay counted as implementation debt instead of being treated as approved
  shims.
