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
- Helper modules without those prefixes are internal support code for one guard
  family or one shared analysis surface. Those helpers are grouped
  conceptually by family even when they remain at the root for stable import
  paths.

Family map:
- Active-plan/state helpers: `active_plan/`
- Package-layout helpers: `package_layout/`
- Code-shape policy helpers: `code_shape_*`
- Term-consistency helpers: `term_consistency/`
- Python-analysis helpers: `python_analysis/`, `yaml_json_loader.py`
- Probe-report helpers: `probe_report/`, `probe_path_filters.py`
- Workflow/loop helpers: `coderabbit_*`, `mutation_ralph_loop_core.py`,
  `workflow_loop_utils.py`
- Rust/common helpers: `rust_guard_common.py`, `rust_check_text_utils.py`,
  `git_change_paths.py`

Layout rule:
- Keep entrypoints at the root of `checks/`.
- Enforce root placement with `check_package_layout.py` and repo policy, not
  maintainer taste. The engine decides whether a new file matches the
  configured public-entrypoint globs; the repo pack decides which roots may
  stay flat.
- Move low-fan-out internal helpers into focused subpackages when a family gets
  large enough to justify one.
- High-fan-out helpers that `devctl` imports directly should stay stable unless
  the whole import surface is migrated in the same change.
- When a helper family gets split, treat the old import path as a compatibility
  seam until repo-owned callers, workflows, and tests move in the same slice.
