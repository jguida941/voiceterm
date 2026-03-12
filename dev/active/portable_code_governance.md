# Portable Code Governance Plan

**Status**: active  |  **Last updated**: 2026-03-12 | **Owner:** Tooling/code governance
Execution plan contract: required
This spec remains execution mirrored in `dev/active/MASTER_PLAN.md` under `MP-376`.

## Scope

Turn the current VoiceTerm guard/probe/report stack into a reusable code-governance
engine that can be pointed at arbitrary repositories without editing the engine
itself. The goal is deterministic structural governance for AI-assisted coding:
guards reject recurring bad pattern families, probes rank the remaining design
smells, and the same artifact stream becomes evaluation data for later retrieval
and training work.

This scope is broader than `dev/active/review_probes.md`. That spec still owns
probe implementation and operator-facing review artifacts. This plan owns the
portable-engine boundary, repo-policy/preset layering, measurement/data capture,
external-repo rollout, and export/snapshot packaging for off-repo analysis.

### Strategic outcome

1. Separate engine from repo policy cleanly enough that another repo can adopt
   the same system by swapping policy/preset files instead of editing Python
   orchestration code.
2. Hold guard code to the same or stricter structural standard than guarded code;
   path budgets are temporary stabilization bridges, not the target state.
3. Capture enough run data to evaluate whether the system materially improves
   AI-assisted code quality over time.
4. Package the system and its reports cleanly enough that a reasoning model or a
   maintainer can inspect the full governance stack outside this repo.

## Execution Checklist

- [x] Move built-in guard/probe capability metadata into portable resolver code.
- [x] Move repo enablement and scope roots into repo policy/preset files.
- [x] Add `devctl quality-policy` plus `--quality-policy` overrides for reuse.
- [x] Ship portable Python guards for suppression debt, default-evaluation traps,
      design complexity, and cyclic imports.
- [x] Remove VoiceTerm-only `code_shape` namespace/layout assumptions from the
      portable engine and resolve them from repo-owned guard config instead.
- [x] Document the portable-governance system as an active execution target so
      portability and measurement do not get lost between sessions.
- [x] Define the engine/preset/repo-policy boundary explicitly enough that a new
      repo-adoption guide and future packaging command can be derived from it.
- [x] Define the measurement/event schema for guarded coding episodes:
      task class, changed files, initial diff/output, guard hits, repair loops,
      accepted diff, human edits, test outcomes, and later review outcomes.
- [x] Decide artifact retention rules for portable evaluation data and sample
      exports so the corpus is usable for retrieval/evaluation before any model
      training is attempted.
- [x] Add a first-class snapshot/export path for the full governance system
      (engine, guards, probes, policy, docs, latest reports) so it can be
      reviewed outside the repo without manual file hunting.
- [x] Add a portable evaluation framework that treats correctness as a gate,
      objective structural deltas as the primary signal, and AI/human pairwise
      review as a secondary preference layer.
- [x] Add a durable adjudication ledger for guard/probe findings so the repo
      tracks false-positive rate, fixed-vs-deferred cleanup, and real signal
      quality over time instead of relying only on ephemeral chat notes.
- [x] Seed the first broad pilot corpus source from the maintainer GitHub repo
      inventory so external-repo testing does not depend on this machine's
      local checkout layout.
- [x] Run one non-VoiceTerm pilot repo through the portable stack using
      policy-only customization and record what still leaks VoiceTerm
      assumptions.
- [x] Add a first-class onboarding/full-surface scan mode so `check`,
      `probe-report`, and `governance-export` can evaluate a repo before a
      trustworthy baseline ref exists.
- [x] Add copied-repo bootstrap support so pilot repos with broken submodule
      `.git` indirection can be normalized without manual git surgery.
- [ ] Automate the multi-repo benchmark runner around the new evaluation
      schema/templates instead of keeping the experiment contract doc-only.
- [ ] Mine the next repeated pattern families from live evidence before
      promoting any more hard guards; prefer probe-first rollout unless the
      signal is low-noise and clearly portable.

## Progress Log

- 2026-03-11: Created this execution-plan doc after maintainership review
  highlighted a tracking gap. Existing active docs already covered probe
  implementation and portable-guard slices, but not the broader portable
  governance engine, data-capture, and external-repo rollout direction.
- 2026-03-11: Current state entering this plan:
  `quality_policy*.py` resolves built-in metadata, repo-local scope roots,
  per-guard config, and preset inheritance; `devctl quality-policy` renders the
  resolved configuration; VoiceTerm-specific `code_shape` namespace rules now
  live in repo-owned config; and the portable Python preset ships suppression
  debt, default-evaluation, design-complexity, and cyclic-import guards.
- 2026-03-11: Maintainer direction is now explicit:
  keep guard code at the same structural standard as guarded code, treat
  path-budget exceptions as temporary only, and sequence next work as
  stabilization -> structural cleanup -> evidence-driven next patterns.
- 2026-03-11: The next strategic expansion beyond portability is the
  measurement layer. The intended dataset shape is:
  raw task/input -> initial output/diff -> guard/probe findings -> repair loops
  -> final accepted diff -> tests/review outcomes.
- 2026-03-11: Requested an external-review snapshot pack containing duplicated
  engine/policy/check/report files plus generated quality-policy/probe artifacts
  so a reasoning model can inspect the whole system out of band.
- 2026-03-11: Added `dev/guides/PORTABLE_CODE_GOVERNANCE.md` as the durable
  reference for engine/preset/repo-policy boundaries, export rules, pilot repo
  selection, and the benchmark/evaluation model. Added schema templates at
  `dev/config/templates/portable_governance_episode.schema.json` and
  `dev/config/templates/portable_governance_eval_record.schema.json` so the
  measurement contract exists outside chat history.
- 2026-03-11: Added `devctl governance-export`, which exports the governance
  stack only to paths outside the repo root, copies the engine/tests/docs/
  workflows, and generates fresh `quality-policy`, `probe-report`, and
  `data-science` artifacts in the exported bundle.
- 2026-03-11: The first broad pilot corpus source is now explicit:
  `https://github.com/jguida941?tab=repositories`. Pilot selection should start
  there instead of relying on whichever sibling repos happen to exist on the
  current machine.
- 2026-03-11: Evaluation direction is now explicit in active state:
  correctness gate first, objective structural/safety deltas second, blind
  pairwise human/AI preference review third. AI judging is a secondary signal,
  not proof by itself.
- 2026-03-11: Ran the first non-VoiceTerm pilot against `ci-cd-hub`. The pilot
  found real external issues and surfaced the remaining portability leaks:
  copied submodule `.git` pointers break git-backed guards, first-run scans
  need a full current-worktree adoption mode, and export/bootstrap packaging
  must carry every file the governance stack expects.
- 2026-03-11: Closed the pilot-onboarding gaps with two portable additions:
  `devctl governance-bootstrap` repairs copied repo git state for disposable
  pilots, and `--adoption-scan` now gives `check`, `probe-report`, and
  `governance-export` a first-class full-surface onboarding mode.
- 2026-03-11: Added `probe_exception_quality.py` as the next evidence-driven
  Python review probe. It surfaces suppressive broad handlers and generic
  exception translation without runtime context, which showed up as a real
  pattern family in external-tooling-style Python code.
- 2026-03-11: Added `devctl governance-review` plus the
  `portable_governance_finding_review.schema.json` template so reviewed
  guard/probe findings are recorded in a durable JSONL ledger with rolled-up
  false-positive, positive-signal, and cleanup-rate metrics. `data-science`
  now ingests that ledger so the main telemetry snapshot shows whether the
  governance stack is actually finding real issues and whether cleanup is
  converging over time.
- 2026-03-11: Burned down the first live advisory debt through that ledger:
  fixed the `probe_exception_quality` findings in `dev/scripts/devctl/collect.py`
  by narrowing fail-soft exception handling and fixed the translation-quality
  hint in `dev/scripts/devctl/commands/check_support.py` by removing the
  needless subprocess wrapper entirely. This is the first explicit proof that
  `governance-review` is part of the real cleanup loop, not just a future
  measurement hook.
- 2026-03-11: Burned down the next medium-severity design-smell slice from the
  same ledger: `probe_single_use_helpers` no longer flags
  `dev/scripts/devctl/collect.py`, and the row-loading helpers were moved out
  of `dev/scripts/devctl/data_science/metrics.py` into the dedicated
  `data_science/source_rows.py` module so the snapshot builder stays readable
  without carrying one-use file-local helpers.
- 2026-03-11: Burned down the next `probe_single_use_helpers` follow-up from
  the same ledger: the CIHub/external-input triage helpers were moved out of
  `dev/scripts/devctl/commands/triage.py` so the command stays
  orchestration-focused, and the reviewed outcome is recorded as `fixed` in
  `governance-review`.
- 2026-03-11: Burned down the next `probe_single_use_helpers` follow-up from
  the same ledger: `dev/scripts/devctl/commands/loop_packet_helpers.py` no
  longer carries one-call wrapper helpers for JSON source loading/command
  normalization or packet-body dispatch. This was not adjudicated as a false
  positive because those helpers had no reuse or test-seam value; the behavior
  now lives directly in `_discover_artifact_sources()` and
  `_build_packet_body()`, and the reviewed outcome is recorded as `fixed` in
  `governance-review`.
- 2026-03-11: Reviewed the next `probe_single_use_helpers` candidate in
  `dev/scripts/devctl/commands/review_channel_bridge_handler.py` and recorded
  it as `deferred`, not `false_positive`. Before review, the probe emitted one
  file-level hint covering five private helpers. After review, the finding
  stays open with narrower rationale: `_validate_live_launch_conflicts()` and
  `_load_bridge_runtime_state()` look like real one-use wrappers,
  `_resolve_promotion_and_terminal_state()` and `_build_sessions()` are
  defensible seams, and `_post_session_lifecycle_event()` is borderline. The
  audit log now captures that mixed call explicitly so the next cleanup can be
  selective instead of blindly inlining the whole file.
- 2026-03-11: Burned down that deferred
  `review_channel_bridge_handler.py` `probe_single_use_helpers` follow-up.
  Before the fix, the handler carried two real one-use wrappers plus three
  meaningful seams under private helper names, so the probe was not a false
  positive but the right remediation was selective. After the fix,
  `validate_live_launch_conflicts()` is reused from
  `review_channel_bridge_action_support.py`, the one-use bridge-state wrapper
  is gone, and the surviving session/promotion/event boundaries now live as
  named action-support helpers in
  `review_channel_bridge_action_support.py` instead of looking like throwaway
  file-local privates. `review_channel_bridge_support.py` stays below the
  code-shape soft limit after that split. `probe_single_use_helpers` no longer
  flags the handler, and the reviewed outcome is now recorded as `fixed` in
  `governance-review`.
- 2026-03-11: Burned down the next
  `probe_single_use_helpers` follow-up in
  `dev/scripts/devctl/governance_export_artifacts.py`. Before the fix, the
  export writer delegated quality-policy, probe-report, and data-science
  artifact generation through three one-call private helpers with no reuse or
  test-seam value, so the probe was not a false positive. After the fix,
  `write_generated_artifacts()` writes those three artifact families directly,
  the file drops out of the probe backlog, and the reviewed outcome is recorded
  as `fixed` in `governance-review`.
- 2026-03-11: Burned down the next
  `probe_single_use_helpers` follow-up in
  `dev/scripts/devctl/governance_export_support.py`. Before the fix, the
  export builder hid repository-external destination validation, snapshot
  source copying, manifest emission, and path-containment checking behind four
  one-call private helpers with no reuse or seam value, so the probe was not a
  false positive. After the fix, `build_governance_export()` performs those
  steps directly while `_sanitize_snapshot_name()` remains the only local
  helper boundary, the file drops out of the probe backlog, and the reviewed
  outcome is recorded as `fixed` in `governance-review`.
- 2026-03-11: Burned down the next
  `probe_single_use_helpers` follow-up in
  `dev/scripts/devctl/watchdog/episode.py`. Before the fix, the episode
  builder delegated provider inference, guard-family classification, and
  escaped-findings counting through three one-call private helpers with no
  reuse or test-seam value, so the probe was not a false positive. After the
  fix, `build_guarded_coding_episode()` derives those values inline while
  `_snapshot()` remains the only reused local helper boundary, the file drops
  out of the probe backlog, and the reviewed outcome is recorded as `fixed` in
  `governance-review`.
- 2026-03-11: Burned down the next
  `probe_single_use_helpers` follow-up in
  `dev/scripts/devctl/watchdog/probe_gate.py`. Before the fix, the probe gate
  hid allowlist loading, allowlist matching, and report summarization behind
  three one-call private helpers with no reuse or test-seam value, so the
  probe was not a false positive. After the fix, `run_probe_scan()` performs
  those steps directly, focused unit coverage now exercises allowlist
  filtering/fail-open behavior, the file drops out of the probe backlog, and
  the reviewed outcome is recorded as `fixed` in `governance-review`.
- 2026-03-11: Burned down the next
  `probe_single_use_helpers` follow-up in
  `dev/scripts/devctl/quality_policy_scopes.py`. Before the fix, the scope
  resolver hid Python-root discovery plus configured-root normalization and
  coercion behind four one-call private helpers with no reuse or test-seam
  value, so the probe was not a false positive. After the fix,
  `resolve_quality_scopes()` performs the Python default discovery and
  configured-root normalization directly while `_discover_rust_scope_roots()`
  remains the only meaningful helper boundary, focused unit coverage now
  exercises common Python-root discovery and invalid/duplicate scope handling
  in `dev/scripts/devctl/tests/test_quality_policy.py`, the file drops out of
  the probe backlog, and the reviewed outcome is recorded as `fixed` in
  `governance-review`.
- 2026-03-11: Burned down the next
  `probe_single_use_helpers` follow-up in
  `dev/scripts/devctl/review_probe_report.py`. Before the fix, the aggregated
  probe reporter hid per-probe subprocess execution, hint enrichment, batch
  collection, and terminal hotspot rendering behind four one-call private
  helpers with no reuse or test-seam value, so the probe was not a false
  positive. After the fix, `build_probe_report()` drives probe execution and
  risk-hint enrichment directly, `render_probe_report_terminal()` renders the
  top hotspot inline, focused unit coverage now exercises the terminal hotspot
  path in `dev/scripts/devctl/tests/test_probe_report.py`, the file drops out
  of the probe backlog, and the reviewed outcome is recorded as `fixed` in
  `governance-review`.
- 2026-03-11: Burned down the next
  `probe_single_use_helpers` follow-up in
  `dev/scripts/devctl/triage/support.py`. Before the fix, the markdown
  renderer hid project snapshot, issue list, CIHub, and external-input
  sections behind four one-call private helpers with no reuse or seam value,
  so the probe was not a false positive. After the fix,
  `render_triage_markdown()` builds those sections directly, focused unit
  coverage now exercises CIHub/external-input markdown rendering in
  `dev/scripts/devctl/tests/test_triage.py`, the file drops out of the probe
  backlog, and the reviewed outcome is recorded as `fixed` in
  `governance-review`.
- 2026-03-11: Burned down the final repo-wide
  `probe_single_use_helpers` follow-up in
  `app/operator_console/state/presentation/presentation_state.py`. Before the
  fix, the presentation layer hid snapshot-digest lane serialization,
  repo-analytics change-mix formatting, and CI KPI rendering behind one-call
  private helpers with no reuse or test-seam value, so the probe was not a
  false positive. After the fix, `snapshot_digest()`, `_build_repo_text()`,
  and `_build_kpi_values()` perform those derivations directly, focused unit
  coverage remains green in
  `app/operator_console/tests/state/test_presentation_state.py`, the file
  drops out of the `probe_single_use_helpers` backlog, and the residual low
  `probe_design_smells` formatter-helper hint disappears in the same pass. The
  reviewed outcome is recorded as `fixed` in `governance-review`.
- 2026-03-11: Burned down the next high-severity `probe-report` hotspot in
  `dev/scripts/devctl/phone_status_views.py`. Before the fix, the
  compact/trace/actions projections returned large ad-hoc dict literals and
  `view_payload()` plus `_render_view_markdown()` dispatched on raw view
  strings, so the combined `probe_dict_as_struct` and
  `probe_stringly_typed` hints were not false positives. After the fix,
  `PhoneStatusView` parses the selected view once at the boundary,
  typed projection models live in `dev/scripts/devctl/phone_status_projection.py`,
  `compact_view()`, `trace_view()`, and `actions_view()` emit the same JSON
  shapes through explicit `to_dict()` methods, focused unit coverage now
  exercises compact fallback plus trace-markdown rendering in
  `dev/scripts/devctl/tests/test_phone_status.py`, the file drops out of the
  probe backlog, and the follow-on code-shape split keeps the view renderer
  back under the soft file-size limit. The reviewed outcomes are recorded as
  `fixed` in `governance-review`.
- 2026-03-11: Closed the next portability leak that GitHub CI exposed directly:
  the repo quality-policy files existed only as ignored local JSON, so local
  `check`/`probe-report` runs resolved the VoiceTerm policy while GitHub fell
  back to the portable default surface and drifted from local results. The
  fix was governance, not engine behavior: commit the repo policy plus portable
  preset JSON files, document them as versioned source in maintainer docs, and
  keep workflow validation aligned with that tracked policy surface. The same
  CI-parity cleanup also narrowed pre-commit to changed files, fixed the
  tooling-control-plane mypy env export bug, moved iOS CI to `macos-15` so the
  Swift 6 / newer Xcode project lane can run, and burned down the current
  maintainer-lint redundant-closure regressions in the touched Rust files.
- 2026-03-11: Refreshed the external `terminal-as-interface` publication from
  the committed VoiceTerm branch head and then recorded the new sync baseline
  in `dev/config/publication_sync_registry.json`
  (`source_ref=4deb8ec8f8c3709f1fb35955f9763c6147df6a95`,
  `external_ref=9cf965f`). The paper repo now derives its appendix snapshot
  stats from the shared JSON snapshot instead of freezing those counts in
  prose, and `check_publication_sync.py` is back to zero drift.
- 2026-03-12: Closed the next GitHub-only parity follow-up after PR #16 moved
  onto the refreshed governance branch head. `test_process_sweep.py` now
  derives repo and `rust/` cwd fixtures from the live checkout root instead of
  a hard-coded workstation path, review-channel bridge tests pin freshness
  enforcement explicitly so `GITHUB_ACTIONS=true` no longer changes stale-poll
  expectations by accident, the startup-banner render-mode test now clears
  runtime/style-pack overrides before asserting the fallback path, iOS
  `xcode-build` now targets the generic simulator destination instead of a
  runner-specific device name, and the changed-file `pre-commit` lane is back
  to green after explicit watchdog/snapshot re-export cleanup plus the
  corresponding Ruff/format sweep across the touched PR file set.
- 2026-03-12: Finished the next CI-parity cleanup pass on top of that branch
  refresh. `devctl` now keeps repo-owned Python subprocesses on the invoking
  interpreter so local `python3.11 dev/scripts/devctl.py check|probe-report`
  runs no longer fall back to an older `python3` on PATH, split-module
  compatibility exports were restored for `quality_policy`, `collect`,
  `status_report`, `triage/support`, `check_phases`, and
  `check_python_global_mutable`, new support modules
  `dev/scripts/devctl/phone_status_view_support.py`,
  `dev/scripts/devctl/text_utils.py`, and
  `app/operator_console/state/activity/activity_report_support.py` pulled
  `phone_status_views.py` and `activity_reports.py` back under code-shape
  limits without duplicate logic, and the follow-up guard fixes removed the new
  broad-except / suppression-debt / nesting-depth regressions introduced during
  the changed-file Ruff sweep.
- 2026-03-12: Burned down the remaining working-tree review-probe debt from
  the phone/mobile control-plane surfaces. `dev/scripts/devctl/autonomy/phone_status.py`
  now uses a typed `RalphSection` boundary instead of large anonymous helper
  dicts and inlines the one-call latest-attempt / trace-normalization logic in
  `build_phone_status()`, `dev/scripts/devctl/mobile_status_projection.py`
  now carries the typed mobile compact/alert/actions payload models plus view
  parsing/render helpers so `mobile_status_views.py` stays under its
  code-shape limit, and `dev/scripts/devctl/commands/loop_packet_helpers.py`
  now uses `LoopPacketSourceCommand` instead of the last remaining auto-send
  string-literal chain. Focused `phone_status` / `mobile_status` /
  `loop_packet` tests are green, `probe-report` now returns a clean packet,
  and the reviewed outcomes are recorded as `fixed` in `governance-review`.
- 2026-03-12: Closed the post-push pre-commit/compatibility follow-up that the
  refreshed PR surfaced immediately. Ruff had stripped several legacy
  re-export seams that the repo still imports/tests through, so
  `dev/scripts/devctl/common.py`, `status_report.py`, `collect.py`,
  `triage/support.py`, `commands/check_phases.py`,
  `process_sweep/core.py`, `phone_status_view_support.py`,
  `quality_policy.py`, `check_python_global_mutable.py`, and
  `probe_report_render.py` now keep those compatibility names explicitly while
  `common.py` stays under code-shape via a compact compatibility-export table
  instead of line-by-line alias boilerplate. The changed-file `pre-commit`
  lane is clean locally again, `check_code_shape.py` is green, and the full
  `dev/scripts/devctl/tests` suite reran at `1184 passed, 4 subtests passed`.
- 2026-03-12: Closed the docs-governance follow-up on that same repaired tree.
  `AGENTS.md`, `dev/guides/DEVELOPMENT.md`, and `dev/scripts/README.md` now
  state the maintainer contract explicitly: staged `dev/scripts/**` module
  splits must preserve compatibility re-exports until repo importers/tests/
  workflows move together. With that rule documented, `docs-check
  --strict-tooling` is green again, the bridge heartbeat was refreshed before
  rerun, and the full canonical `bundle.tooling` command list replayed cleanly
  under `python3.11` on this workstation (`397 passed, 181 skipped` in the
  Operator Console suite, zero repo processes left after cleanup).
- 2026-03-12: Closed the next GitHub runner parity bugs the new PR SHA exposed.
  Review-channel launch/rollover tests were environment-sensitive because
  session-script generation resolved `codex`/`claude` from the current PATH
  before the script even launched; bridge session building now falls back to
  the provider command name for the default resolver so dry-run and simulated
  launch paths stay portable while explicit missing-CLI tests still patch the
  failure path. `triage-loop` now threads the command module's CI/connectivity
  predicates into the preflight helper so the existing non-blocking-local test
  stays valid inside GitHub Actions, and `JobRecord.duration_seconds` now clamps
  negative monotonic deltas to zero so the Operator Console job-state surface no
  longer fails on runners whose monotonic counter is below the test fixture's
  synthetic `started_at`. Reproduced CI-shaped tests are green locally,
  `dev/scripts/devctl/tests` reran at `1184 passed, 4 subtests passed`, and
  `app/operator_console/tests/` reran at `397 passed, 181 skipped`.

## Audit Evidence

- Portable resolver inspection: `python3 dev/scripts/devctl.py quality-policy --format md`
- Probe packet + hotspot report: `python3 dev/scripts/devctl.py probe-report --format md`
- First-run onboarding scan:
  `python3 dev/scripts/devctl.py check --profile ci --quality-policy <policy> --adoption-scan`
  `python3 dev/scripts/devctl.py probe-report --quality-policy <policy> --adoption-scan --format md`
- Main guard lane validation:
  `python3 dev/scripts/devctl.py check --profile ci --skip-fmt --skip-clippy --skip-tests --skip-build`
- Structural cleanup validation:
  `python3 dev/scripts/checks/check_code_shape.py --format json`
  `python3 dev/scripts/checks/check_parameter_count.py --format json`
  `python3 dev/scripts/checks/check_function_duplication.py --format json`
- Governance checks:
  `python3 dev/scripts/checks/check_active_plan_sync.py`
  `python3 dev/scripts/checks/check_multi_agent_sync.py`
  `python3 dev/scripts/checks/check_architecture_surface_sync.py`
  `python3 dev/scripts/checks/check_guard_enforcement_inventory.py`
  `python3 dev/scripts/checks/check_bundle_workflow_parity.py`
  `python3 dev/scripts/devctl.py docs-check --strict-tooling`
  `python3 dev/scripts/devctl.py process-cleanup --verify --format md`
- Export path:
  `python3 dev/scripts/devctl.py governance-export --format md`
- Finding-quality ledger:
  `python3 dev/scripts/devctl.py governance-review --format md`
  `python3 dev/scripts/devctl.py governance-review --record --signal-type <guard|probe> --check-id <id> --verdict <verdict> --path <file> --format md`
- Pilot bootstrap path:
  `python3 dev/scripts/devctl.py governance-bootstrap --target-repo <path> --format md`
- Known unrelated hygiene warning:
  `python3 dev/scripts/devctl.py hygiene --strict-warnings` remains red because
  of pre-existing publication drift and because hygiene can observe the cleanup
  subprocess while it runs; standalone cleanup verify is green.
