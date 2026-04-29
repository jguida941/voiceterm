# Checks

Canonical home for hard guards and advisory review probes.

- Root-level entrypoints stay intentionally flat so maintainers can scan the
  runnable surfaces quickly. This is an organization rule, not leftover
  sprawl: runnable `check_*.py`, `probe_*.py`, and `run_*.py` scripts remain
  at the root so workflows, docs, and humans all reference one obvious path.

- `check_*.py`: blocking repo policy guards.
- `probe_*.py`: non-blocking design-smell scanners.
- `run_*.py`: report/orchestration entrypoints such as `run_probe_report.py`.
  The fallback probe runner now resolves the registered probe set from the
  shared quality policy/script catalog instead of carrying its own hard-coded
  filename list.
- Root `check_*.py`, `probe_*.py`, and moved helper surfaces are stable
  compatibility wrappers when a family graduates into its own package. The
  implementation should live under a focused subpackage once a family becomes
  crowded enough that root density turns into layout debt.

Family map:
- Active-plan/state helpers: `active_plan/`
- Package-layout helpers: `package_layout/`
- Code-shape guards/helpers: `code_shape/`, `code_shape_probes/`,
  `code_shape_support/`
- Term-consistency helpers: `term_consistency/`
- Python-analysis helpers: `python_analysis/`
- Rust-analysis helpers: `rust_analysis/`
- Compatibility-matrix helpers: `compat_matrix/`
- Probe-report helpers: `probe_report/`
- Architecture-aware probes: root `probe_architecture_*.py` entrypoints that
  consume typed platform registry snapshots before emitting advisory hints.
- Typed-authority provenance probe:
  `probe_typed_authority_provenance.py` consumes PlanRow and queue projection
  state and flags any active instruction authority that lacks provenance or an
  `InstructionPriorityDecision`.
- Review-probe helpers: `review_probes/`
- Workflow/loop helpers: `coderabbit_*`, `mutation_ralph_loop_core.py`,
  `workflow_loop_utils.py`
- Shared root helpers that still remain flat by design: `git_change_paths.py`

Layout rule:
- Keep stable public entrypoints at the root of `checks/`, but keep the real
  implementation in focused subpackages once a family becomes crowded.
- Enforce wrapper honesty with `check_package_layout.py` and repo policy, not
  maintainer taste. Thin root wrappers are acceptable; root implementation
  sprawl is not.
- Move low-fan-out internal helpers into focused subpackages when a family gets
  large enough to justify one.
- High-fan-out helpers that `devctl` imports directly should stay stable unless
  the whole import surface is migrated in the same change.
- When a helper or guard family gets split, treat the old root path as a
  compatibility seam until repo-owned callers, workflows, and tests move in
  the same slice.
