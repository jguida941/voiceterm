# Master Plan (Active, Unified)

## Canonical Plan Rule

- This file is the single active plan for strategy, execution, and release tracking.
- `dev/active/INDEX.md` is the canonical active-doc registry and read-order map for agents.
- `dev/active/theme_upgrade.md` is the consolidated Theme Studio specification + gate catalog + overlay visual research + redesign appendix, but not a separate execution tracker; implementation tasks stay in this file.
- `dev/active/memory_studio.md` is the Memory + Action Studio specification + gate catalog, but not a separate execution tracker; implementation tasks stay in this file.
- `dev/active/devctl_reporting_upgrade.md` is the phased `devctl` reporting/CIHub specification, but not a separate execution tracker; implementation tasks stay in this file under `MP-297..MP-300`, `MP-303`, `MP-306`.
- `dev/active/autonomous_control_plane.md` is the autonomous loop + mobile control-plane execution spec; implementation tasks stay in this file under `MP-325..MP-338, MP-340`.
- `dev/active/loop_chat_bridge.md` is the loop artifact-to-chat suggestion coordination runbook; execution evidence and operator handoffs for this path stay there under `MP-338`.
- `dev/active/naming_api_cohesion.md` is the naming/API cohesion execution spec; implementation tasks stay in this file under `MP-267`.
- `dev/active/ide_provider_modularization.md` is the IDE/provider adapter modularization execution spec; implementation tasks stay in this file under `MP-346`, `MP-354`.
- `dev/active/review_channel.md` now carries the merged markdown-swarm lane plan,
  instruction log, and signoff template for the current Codex/Claude parallel cycle.
- `dev/active/ralph_guardrail_control_plane.md` is the Ralph guardrail control plane execution spec; implementation tasks stay in this file under `MP-360..MP-367`.
- `dev/active/review_probes.md` is the review-probe execution spec; implementation tasks stay in this file under `MP-368..MP-375`.
- Deferred work lives in `dev/deferred/` and must be explicitly reactivated here before implementation.

## Status Snapshot (2026-03-07)
- Last tagged release: `v1.1.1` (2026-03-06)
- Current release target: `post-v1.1.1 planning`
- Active development branch: `develop`
- Release branch: `master`
- Strategic focus: sequential execution with one primary product lane at a
  time: release stability first, then Theme completion, then Memory completion.
- In-flight: release-channel stability fix for Homebrew formula manifest-path
  compatibility (`libexec/src/Cargo.toml` -> `libexec/rust/Cargo.toml`) plus
  Theme GA baseline execution (`MP-161`, `MP-162`, `MP-174`, `MP-166`,
  `MP-167`, `MP-173`).
- Theme execution alignment update: the standalone `plan.md` scratch draft is
  now merged into `dev/active/theme_upgrade.md` as the canonical execution
  checklist for the current Theme tranche; immediate sequencing is helper-path
  consolidation first, persisted style-pack routing closure second, Components
  page activation third, and registry/CI parity closure after the
  `theme_studio_v2` ownership boundary is made explicit.
- Architecture tracker update: `MP-354` closure is complete; remaining
  IDE/provider work is the post-next-release `MP-346` backlog already retained
  in `dev/active/ide_provider_modularization.md` (`Step 3g`, `Step 3h`, and
  AntiGravity readiness intake).
- Execution mode: keep autonomy/tooling/runtime reliability in maintenance-only
  mode while Theme and Memory product lanes are completed in order.
- Maintainer-doc clarity update: `dev/DEVELOPMENT.md` now includes an end-to-end lifecycle flowchart plus check/push routing sections while `AGENTS.md` remains the canonical policy router.
- Tooling docs-governance update: `devctl docs-check --strict-tooling` now enforces markdown metadata-header normalization for `Status`/`Last updated`/`Owner` blocks via `check_markdown_metadata_header.py`.
- External publication governance update: `devctl` is gaining a tracked
  publication-sync surface so external papers/sites can declare watched source
  paths, emit stale-publication drift reports, and surface hygiene warnings
  when repo changes outpace synced public artifacts.
- Loop architecture clarity update: `dev/ARCHITECTURE.md` and
  `dev/DEVELOPMENT.md` now document the custom repo-owned Ralph/Wiggum loop
  path and the federated-repo import model in simple flowchart form.
- Continuous swarm hardening kickoff: `dev/active/continuous_swarm.md` now
  tracks the local-first Codex-reviewer / Claude-coder continuation loop,
  launcher modularization, peer-liveness guards, context-rotation handoff, and
  the later proof-gated template-extraction path.
- Desktop operator console prototype update:
  `dev/active/operator_console.md` now tracks a bounded optional PyQt6
  VoiceTerm Operator Console wrapper over the existing Rust runtime and
  `devctl` control surfaces. The active plan now treats this as a repo-aware
  desktop controller shell over typed repo-owned commands, workflow guidance,
  and bounded AI assist, but still not as a replacement execution authority or
  second control plane.
- Loop comment transport hardening update: shared workflow-loop `gh` helpers now
  avoid invalid `--repo` usage for `gh api` calls so summary-and-comment mode
  can publish and upsert commit/PR comments reliably.
- Audit-remediation update: Round-2 high-severity audit fixes landed for prompt
  detection hot-path queue behavior, transcript merge-loop invariants,
  persistent-config duplication reduction, and devctl release/comment/report
  helper hardening with expanded unit coverage.
- Runtime cleanup update: startup splash logo coloring now uses a single
  theme-family accent (no rainbow line rotation), and the stale orphan
  `rust/src/bin/voiceterm/progress.rs` module has been removed.
- Theme Studio maintainability cleanup update: home/colors/borders/components/
  preview/export byte handling now routes through page-scoped helper functions
  in `theme_studio_input.rs`, with runtime style-adjustment routing split into
  focused helper paths; follow-up dedup also centralized vertical-arrow page
  navigation + runtime override cycle wiring so page handlers avoid repeated
  dispatch scaffolding. Theme Studio suite and full CI profile remained green.
- Theme Studio readability follow-up update: `theme_studio/home_page.rs` now
  uses a dedicated row-metadata struct with static tip strings (instead of
  per-row tip `String` allocations), and writer-state test-only timing
  constants were moved out of `writer/state.rs` production scope into
  `writer/state/tests.rs` so runtime modules stay focused on shipped code.
- CI compatibility hotfix update: release-binary workflow runner labels now use
  actionlint-supported macOS targets, latency guard script path resolution now
  supports `rust/` with `src/` fallback, and explicit `devctl triage --cihub`
  opt-in now preserves capability probing when PATH lookup misses the binary.
- Release workflow stability update: `release_attestation.yml` action pins were
  refreshed to valid GitHub-owned SHAs, and `scorecard.yml` now keeps
  workflow-level permissions read-only with write scopes isolated to the
  scorecard job so OpenSSF publish verification succeeds.
- Release preflight auth stability update: `.github/workflows/release_preflight.yml`
  runtime bundle step now exports `GH_TOKEN: ${{ github.token }}` so
  `devctl check --profile release` can run `gh`-backed release gates in CI.
- Release governance update (2026-03-09): the current pre-release audit
  showed that shipping the mobile/control-plane tranche cleanly requires full
  canonical-doc coverage, not just changelog plus a subset of guides.
  Maintainer docs (`AGENTS.md`, `dev/guides/DEVELOPMENT.md`,
  `dev/history/ENGINEERING_EVOLUTION.md`) and canonical user docs
  (`QUICK_START.md`, `guides/TROUBLESHOOTING.md`) now carry explicit release
  notes for the mobile app/install/control-plane path, and the release bundle
  expectation is that `check_mobile_relay_protocol.py` remains green so Rust,
  Python, and iOS payload contracts ship together.
- Release preflight SARIF permission update:
  `.github/workflows/release_preflight.yml` preflight job now grants
  `security-events: write` so zizmor SARIF uploads can publish to code scanning.
- Release preflight zizmor execution update:
  `.github/workflows/release_preflight.yml` now sets zizmor
  `online-audits: false` to prevent cross-repo compare API 403 failures from
  blocking release preflight.
- Release preflight security-scope update:
  `.github/workflows/release_preflight.yml` now runs
  `devctl security` with `--python-scope changed` and the same resolved
  `--since-ref/--head-ref` range used by AI-guard so preflight enforces
  commit-scoped Python checks instead of full-repo formatting backlog, and it
  avoids hard-failing on repository-wide open CodeQL backlog in release
  preflight; `cargo deny` remains blocking while `devctl security` report
  output is advisory evidence in that lane.
- Compat-matrix parser resilience update: compatibility/naming guard scripts now
  share a minimal YAML fallback parser so tooling CI and local checks stay
  deterministic in minimal Python environments without `PyYAML`.
- Compat-matrix parser fail-closed update: malformed inline collection scalars
  in fallback mode now raise explicit parse errors instead of silent coercion.
- Tooling security hardening update: `devctl` loop/mutation/release helper
  defaults now resolve temporary artifact paths via the system temp directory
  API instead of hardcoded `/tmp` literals, satisfying Bandit `B108` checks in
  release-security gates.
- Control-plane simplification update: MP-340 is now Rust-first only (Rust
  overlay + `devctl` + phone/SSH projections). The optional `app/pyside6`
  command-center track is retired from active execution scope.
- CI lane compatibility update: Rust CI MSRV lane now uses toolchain `1.88.0`
  to match current transitive dependency requirements (`time`/`time-core`);
  CI/docs references were synchronized to the new lane contract.
- MP-346 checkpoint update: `CP-016` automated continuation rerun is captured
  at `dev/reports/mp346/checkpoints/20260305T032253Z-cp016/`; operator
  release-scope matrix update is applied (IDE-first `4/4` required cells:
  Cursor+Codex, Cursor+Claude, JetBrains+Codex, JetBrains+Claude), with
  `other` host and `gemini` baseline checks deferred to post-release backlog.
- MP-346 architecture-audit status update (2026-03-05): IDE-first manual
  matrix closure requirement is complete (`4/4`), and no additional MP-346
  runtime/tooling blockers remain in the current non-regression rerun.
- MP-346 closure-followup update (2026-03-05): prior shape/duplication blockers are
  resolved via check-router/docs-check helper decomposition and duplication
  evidence is refreshed (`dev/reports/duplication/jscpd-report.json`,
  `duplication_percent=0.32`, `duplicates_count=14` after latest cleanup pass);
  closure non-regression rerun is green and the
  prior physical-host manual matrix `7/7` gate is superseded by the IDE-first
  release-scope matrix closure (`4/4`) recorded in `CP-016`.
- MP-347 verification refresh (2026-03-05): closure non-regression command pack
  row `2331` was rerun end-to-end and remains green after canonicalizing
  duplication-audit helper ownership and removing stale archive path literals
  from active docs/changelog.
- MP-347 guard-utility expansion update (2026-03-09): `devctl report` now
  supports `--python-guard-backlog` with ranked hotspot aggregation across
  `check_python_dict_schema`, `check_python_global_mutable`,
  `check_python_design_complexity`, `check_python_cyclic_imports`,
  `check_parameter_count`, `check_nesting_depth`, `check_god_class`,
  `check_python_broad_except`, and `check_python_subprocess_policy`, so Python
  clean-code debt can be burned down in priority order before stricter lane
  promotion.
- MP-347 broad-except hardening update (2026-03-09):
  `check_python_broad_except.py` now treats bare `except:` handlers as
  broad-except policy violations, and newly added fail-soft plotting/telemetry
  paths in devctl autonomy/data-science helpers now carry explicit
  `broad-except: allow reason=...` rationale comments.
- MP-347 mutable-state hardening update (2026-03-09):
  `check_python_global_mutable.py` now also enforces non-regressive growth of
  mutable default argument patterns (`[]`, `{}`, `set()/list()/dict()` style
  defaults) so Python mutable-state pitfalls are blocked even when `global`
  keywords are not involved.
- MP-347 suppression-debt update (2026-03-11): `check_python_suppression_debt.py`
  now enforces non-regressive growth of Python lint/type suppressions
  (`# noqa`, `# type: ignore`, `# pylint: disable`, `# pyright: ignore`)
  using tokenized comment scanning, and the portable Python preset now enables
  it by default so the same engine can block new suppression debt here or in
  another repo without hard-coded VoiceTerm path logic.
- MP-347 default-evaluation hardening update (2026-03-11):
  `check_python_global_mutable.py` now also blocks net-new function-call
  default arguments plus dataclass fields that evaluate mutable or callable
  defaults eagerly instead of routing through `field(default_factory=...)`, so
  the portable Python guard stack now covers the next default-argument trap
  slice without needing a second overlapping guard id.
- MP-347 portability hardening update (2026-03-11):
  `quality_policy.py` now resolves per-guard config payloads, standalone guard
  scripts can read those configs through `check_bootstrap.py`, and
  `devctl quality-policy` plus `devctl check --quality-policy` now surface and
  propagate the same policy-owned settings. VoiceTerm-specific `code_shape`
  namespace/layout rules moved out of the portable engine and into the
  repo-owned preset so another repo can reuse the same guard without hidden
  path assumptions.
- MP-347 portable complexity/import update (2026-03-11):
  `check_python_design_complexity.py` now blocks net-new branch-heavy or
  return-heavy Python functions using policy-owned thresholds (with a
  conservative portable default that repo policy can tighten), and
  `check_python_cyclic_imports.py` now blocks net-new top-level local import
  cycles with repo-policy allowlists for known transitional debt. Both guards
  are registered in the portable Python preset, catalog, bundles, workflows,
  and Python backlog report so the next portable hard-guard backlog narrows to
  Rust `result_large_err` / `large_enum_variant`.
- MP-376 portable governance execution-doc update (2026-03-11):
  added `dev/active/portable_code_governance.md` to track the broader
  reusable code-governance-engine direction explicitly: engine vs repo-policy
  boundaries, measurement/data-capture goals, off-repo snapshot/export needs,
  and the eventual multi-repo pilot rollout. This keeps the strategic
  portability/evaluation goal from being scattered across review-probe log
  entries alone.
- MP-376 export/evaluation update (2026-03-11):
  `devctl governance-export` now packages the governance stack into an
  external snapshot/zip with fresh `quality-policy`, `probe-report`, and
  `data-science` artifacts, `dev/guides/PORTABLE_CODE_GOVERNANCE.md` now
  defines the engine/preset/repo-policy boundary plus the evaluation rubric,
  and template schemas now capture both the guarded-episode measurement
  contract and the multi-repo benchmark record. The first broad external pilot
  corpus source is explicitly the maintainer GitHub repo inventory
  (`https://github.com/jguida941?tab=repositories`), while actual non-VoiceTerm
  pilot execution remains open follow-up work.
- MP-376 pilot-onboarding update (2026-03-11):
  the first non-VoiceTerm pilot ran against `ci-cd-hub` and exposed the
  remaining portability leaks directly. `devctl governance-bootstrap` now
  normalizes copied/submodule repos with broken `.git` indirection, `check` /
  `probe-report` / `governance-export` now accept `--adoption-scan` for
  full-surface onboarding runs without a trusted baseline ref, and
  `probe_exception_quality.py` joins the review-probe suite to surface
  suppressive Python exception handling patterns seen in external tooling code.
- MP-376 measurement-ledger update (2026-03-11):
  `devctl governance-review` now records adjudicated guard/probe findings into
  `dev/reports/governance/finding_reviews.jsonl`, writes rolled-up
  `review_summary.{md,json}` artifacts, and feeds those metrics into
  `devctl data-science` so false-positive rate, confirmed-signal rate, and
  cleanup progress are tracked as durable repo evidence instead of chat-only
  notes.
- MP-376 live-cleanup adjudication update (2026-03-11):
  the first high-severity probe debt was burned down through that ledger:
  `probe_exception_quality` findings in `dev/scripts/devctl/collect.py` were
  fixed by narrowing fallback exception handling, the medium translation hint in
  `dev/scripts/devctl/commands/check_support.py` was removed by replacing the
  subprocess-based tempdir lookup with a direct Python implementation, and the
  reviewed outcomes are now recorded as `fixed` in `governance-review`.
- MP-376 design-smell cleanup update (2026-03-11):
  the next medium-severity `probe_single_use_helpers` slice is now burned down
  too: `dev/scripts/devctl/collect.py` no longer carries one-use file-local
  helpers, and the data-science row collectors were split into
  `dev/scripts/devctl/data_science/source_rows.py` so
  `dev/scripts/devctl/data_science/metrics.py` stays focused on snapshot
  orchestration. Those reviewed outcomes are also now recorded as `fixed` in
  `governance-review`.
- MP-376 triage single-use-helper follow-up (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup moved the
  CIHub/external-input triage helpers out of
  `dev/scripts/devctl/commands/triage.py` so the command stays
  orchestration-focused, and the reviewed outcome is now recorded as `fixed`
  in `governance-review`.
- MP-376 loop-packet single-use-helper follow-up (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup is now burned down too:
  `dev/scripts/devctl/commands/loop_packet_helpers.py` no longer hides JSON
  source loading/command normalization or packet-body dispatch behind one-call
  wrappers. This was treated as a real design-smell signal, not a false
  positive, because the flagged helpers had no reuse or test-seam value; the
  behavior now lives directly in `_discover_artifact_sources()` and
  `_build_packet_body()`, and the reviewed outcome is now recorded as `fixed`
  in `governance-review`.
- MP-376 review-channel single-use-helper adjudication (2026-03-11):
  the next `probe_single_use_helpers` candidate under
  `dev/scripts/devctl/commands/review_channel_bridge_handler.py` is now logged
  as `deferred`, not `false_positive`. Before review, the probe emitted one
  file-level hint over five private helpers; after review, the repo state now
  records the narrower call explicitly: `_validate_live_launch_conflicts()`
  and `_load_bridge_runtime_state()` look like real one-use wrappers,
  `_resolve_promotion_and_terminal_state()` and `_build_sessions()` remain
  defensible seams, and `_post_session_lifecycle_event()` is borderline. That
  keeps the next cleanup selective and auditable instead of treating the whole
  hint as either pure noise or a blanket inline order.
- MP-376 review-channel single-use-helper cleanup (2026-03-11):
  that deferred `review_channel_bridge_handler.py` follow-up is now burned down
  with the selective fix the adjudication called for. Before the fix, the file
  mixed two real one-use wrappers with three meaningful seams; after the fix,
  the live-launch conflict logic now reuses
  `review_channel_bridge_action_support.py`, the one-use bridge-state wrapper
  is removed, and the remaining session/promotion/event boundaries now live as
  named action-support helpers instead of private single-use functions.
  `review_channel_bridge_support.py` stays back under the code-shape soft
  limit after that split. This was still treated as a real design-smell
  signal, not a false positive, and `probe_single_use_helpers` no longer flags
  the handler; the reviewed outcome is now recorded as `fixed` in
  `governance-review`.
- MP-376 governance-export single-use-helper cleanup (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup is now burned down in
  `dev/scripts/devctl/governance_export_artifacts.py`. Before the fix, the
  export path hid quality-policy, probe-report, and data-science artifact
  generation behind three one-call private helpers with no reuse or test-seam
  value; after the fix, `write_generated_artifacts()` writes those artifact
  families directly, `probe_single_use_helpers` no longer flags the file, and
  the reviewed outcome is now recorded as `fixed` in `governance-review`.
- MP-376 governance-export builder single-use-helper cleanup (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup is now burned down in
  `dev/scripts/devctl/governance_export_support.py`. Before the fix, the
  export builder hid repository-external destination validation, snapshot
  source copying, manifest emission, and path-containment checking behind four
  one-call private helpers with no reuse or seam value; after the fix,
  `build_governance_export()` performs those steps directly, leaves
  `_sanitize_snapshot_name()` as the only local helper boundary, and
  `probe_single_use_helpers` no longer flags the file. This was treated as a
  real design-smell hit, not a false positive, and the reviewed outcome is now
  recorded as `fixed` in `governance-review`.
- MP-376 watchdog-episode single-use-helper cleanup (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup is now burned down in
  `dev/scripts/devctl/watchdog/episode.py`. Before the fix, the episode
  builder hid provider inference, guard-family classification, and
  escaped-findings counting behind three one-call private helpers with no
  reuse or test-seam value; after the fix, `build_guarded_coding_episode()`
  performs those derivations directly, leaves `_snapshot()` as the only reused
  local helper boundary, and `probe_single_use_helpers` no longer flags the
  file. This was treated as a real design-smell hit, not a false positive, and
  the reviewed outcome is now recorded as `fixed` in `governance-review`.
- MP-376 watchdog-probe-gate single-use-helper cleanup (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup is now burned down in
  `dev/scripts/devctl/watchdog/probe_gate.py`. Before the fix, the probe gate
  hid allowlist loading, allowlist matching, and report summarization behind
  three one-call private helpers with no reuse or test-seam value; after the
  fix, `run_probe_scan()` performs those steps directly, focused unit tests now
  cover allowlist filtering/fail-open behavior, and
  `probe_single_use_helpers` no longer flags the file. This was treated as a
  real design-smell hit, not a false positive, and the reviewed outcome is now
  recorded as `fixed` in `governance-review`.
- MP-376 quality-policy-scope single-use-helper cleanup (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup is now burned down in
  `dev/scripts/devctl/quality_policy_scopes.py`. Before the fix, the scope
  resolver hid Python-root discovery plus configured-root normalization and
  coercion behind four one-call private helpers with no reuse or test-seam
  value; after the fix, `resolve_quality_scopes()` performs those steps
  directly while `_discover_rust_scope_roots()` remains the only meaningful
  helper boundary, focused unit tests now cover common Python-root discovery
  plus invalid/duplicate scope handling, and `probe_single_use_helpers` no
  longer flags the file. This was treated as a real design-smell hit, not a
  false positive, and the reviewed outcome is now recorded as `fixed` in
  `governance-review`.
- MP-376 review-probe-report single-use-helper cleanup (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup is now burned down in
  `dev/scripts/devctl/review_probe_report.py`. Before the fix, the aggregated
  probe reporter hid per-probe subprocess execution, hint enrichment, batch
  collection, and terminal hotspot rendering behind four one-call private
  helpers with no reuse or seam value; after the fix, `build_probe_report()`
  drives probe execution and risk-hint enrichment directly,
  `render_probe_report_terminal()` renders the top hotspot inline, focused
  unit tests now cover the terminal hotspot path, and
  `probe_single_use_helpers` no longer flags the file. This was treated as a
  real design-smell hit, not a false positive, and the reviewed outcome is now
  recorded as `fixed` in `governance-review`.
- MP-376 triage-support single-use-helper cleanup (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup is now burned down in
  `dev/scripts/devctl/triage/support.py`. Before the fix, the markdown
  renderer hid project snapshot, issue list, CIHub, and external-input
  sections behind four one-call private helpers with no reuse or seam value;
  after the fix, `render_triage_markdown()` builds those sections directly,
  focused unit tests now cover CIHub/external-input markdown rendering, and
  `probe_single_use_helpers` no longer flags the file. This was treated as a
  real design-smell hit, not a false positive, and the reviewed outcome is now
  recorded as `fixed` in `governance-review`.
- MP-359 operator-console bundle unblock follow-up (2026-03-11):
  the desktop proof lane is back to green after two bounded fixes. First,
  `app/operator_console/views/layout/__init__.py` now lazy-loads
  `WindowShellMixin`, `HAS_THEME_EDITOR`, and workbench helpers instead of
  importing them eagerly during package init, breaking the package-init
  cycle `help_dialog -> layout.__init__ -> ui_window_shell -> help_dialog`
  that had been failing `test_help_dialog.py` during collection. Second,
  `dev/scripts/devctl/phone_status_views.py` now routes compact/trace/action
  projection through the existing `_section()` helper instead of calling
  removed `_controller/_loop/_source_run/_terminal/_ralph` helpers, so the
  Operator Console phone snapshot path is no longer stuck in unavailable
  fallback. `app/operator_console/tests/` is green again in the canonical
  bundle proof path.
- MP-376 phone-status projection hotspot cleanup (2026-03-11):
  the next high-severity Python review-probe hotspot is now burned down in
  `dev/scripts/devctl/phone_status_views.py`. Before the fix,
  `compact_view()`, `trace_view()`, and `actions_view()` returned large
  ad-hoc dict literals and `view_payload()` plus `_render_view_markdown()`
  branched on raw strings, so the `probe_dict_as_struct` and
  `probe_stringly_typed` hints were treated as real signal, not false
  positives. After the fix, `PhoneStatusView` parses the view boundary once,
  typed projection models live in
  `dev/scripts/devctl/phone_status_projection.py`, focused phone-status tests
  cover compact fallback plus trace markdown rendering, `probe-report` no
  longer flags the file, and the follow-on file split keeps
  `phone_status_views.py` back under the code-shape soft limit.
- MP-359 presentation-state probe cleanup follow-up (2026-03-11):
  the remaining Operator Console advisory debt from the probe suite is now
  burned down in `app/operator_console/state/presentation/presentation_state.py`.
  Before the fix, the file hid snapshot-digest lane serialization,
  repo-analytics change-mix rendering, and CI KPI text behind one-call
  private helpers with no reuse or seam value; after the fix,
  `probe_single_use_helpers` no longer flags the file, the residual low
  formatter-helper `probe_design_smells` hint disappears in the same pass, and
  `app/operator_console/tests/state/test_presentation_state.py` remains green.
- MP-376 operator-console presentation-state single-use-helper cleanup (2026-03-11):
  the final repo-wide `probe_single_use_helpers` ledger cleanup is now burned
  down in `app/operator_console/state/presentation/presentation_state.py`.
  Before the fix, the presentation layer hid snapshot-digest lane
  serialization, repo-analytics change-mix formatting, and CI KPI rendering
  behind one-call private helpers with no reuse or test-seam value; after the
  fix, `snapshot_digest()`, `_build_repo_text()`, and `_build_kpi_values()`
  perform those derivations directly, focused presentation-state tests remain
  green, `probe_single_use_helpers` no longer flags any file repo-wide, and
  the reviewed outcome is now recorded as `fixed` in `governance-review`.
- MP-350 closure update (2026-03-05): additive read-only MCP adapter
  implementation is complete with code-level contract helpers/tests for
  `check --profile release`, `ship --verify`, and cleanup protections;
  execution tracker moved to
  `dev/archive/2026-03-05-devctl-mcp-contract-hardening.md` and durable
  guidance lives in `dev/guides/MCP_DEVCTL_ALIGNMENT.md`.
- MP-347 architecture-audit refresh (2026-03-05): core tooling/runtime guard
  packs are green (`check_code_shape`, duplication audit with fresh `jscpd`,
  rust quality guards, workflow parity, strict-tooling docs governance), and
  strict hygiene catalog/docs alignment is restored for
  `check_duplication_audit_support.py`; remaining follow-up is scoped to
  risk-add-on SSOT consolidation, local strict-hygiene repeatability noise
  (`__pycache__` warning churn unless `--fix`), function-exception paydown
  before `2026-05-15`, and dead-code allow backlog reduction.
- MP-347 docs-policy dedup update (2026-03-06): docs-check path policy now has
  single-source ownership (`docs_check_policy.py`), and
  `docs_check_constants.py` is a compatibility re-export shim with dedicated
  regression coverage in `dev/scripts/devctl/tests/test_docs_check_constants.py`.
- MP-347 shape-governance refresh (2026-03-06): code-shape policy budgets and
  temporary function exceptions were synchronized for the current tooling
  refactor batch (active-plan sync, multi-agent sync, release parser wiring,
  and devctl command runners), with explicit owner/follow-up metadata and
  expiry tracking through `2026-05-15`.
- MP-347 docs-IA boundary cleanup update (2026-03-06): Phase-15 backlog/active
  boundary work is closed; canonical local backlog now lives at
  `dev/deferred/LOCAL_BACKLOG.md`, canonical guard remediation scaffold output
  now lives at `dev/reports/audits/RUST_AUDIT_FINDINGS.md`, and canonical
  phase-2 research now lives at `dev/deferred/phase2.md` (with bridge pointers
  retained for one migration cycle).
- MP-347 mutation-policy update (2026-03-05): `devctl check --profile release`
  now runs mutation-score in report-only mode (non-blocking warnings with
  post-release follow-up guidance when outcomes are missing/stale/below
  threshold) so strict remote CI + CodeRabbit/Ralph gates remain release
  blockers while mutation hardening stays explicitly tracked work.
- MP-346 post-waiver guardrail hardening update: compatibility-matrix checks now
  parse YAML format directly, smoke runtime-backend detection now derives from
  `BackendRegistry` constructor ownership (not module declarations), and
  isolation scanning now skips broader test-only cfg attributes such as
  `cfg(any(test, ...))` with dedicated unit coverage.
- MP-346 review-driven cleanup update: IPC prompt/wrapper preemption now emits
  consistent `JobEnd(cancelled)` events, compatibility-matrix validation now
  fails on duplicate host/provider ids, and matrix smoke now enforces full
  parsed runtime host/backend/provider sets (excluding explicit
  `BackendFamily::Other` sentinel) to prevent silent governance drift.
- MP-346 reviewer follow-up hardening update: isolation cfg-test skipping now
  excludes mixed expressions containing `not(test)` to avoid production-path
  false negatives, matrix smoke backend discovery is no longer coupled to a
  specific `BackendRegistry` vector layout, matrix validation now fails
  malformed host/provider entries missing string `id` fields, and IPC
  cancellation regression coverage now includes active-Claude wrapper and
  `/cancel` `JobEnd(cancelled)` assertions; targeted IPC + memory-guard tests
  are green in this session.
- MP-346 closure-gate stabilization update: full `devctl check --profile ci`
  rerun is green after tightening `legacy_tui::tests::memory_guard_backend_threads_drop`
  to wait for backend-thread count return-to-baseline (removing a transient
  teardown race from suite-wide execution).
- Tooling governance update: workflow shell-heavy commit-range/scope/path
  resolution now routes through `dev/scripts/workflow_shell_bridge.py`,
  `docs-check --strict-tooling` now enforces `check_workflow_shell_hygiene.py`,
  and `tooling_control_plane.yml` now runs explicit naming-consistency and
  workflow-shell hygiene checks.
- MP-346 tooling closure pass update: oversized workflow/devctl helper modules
  were split into companion modules (`autonomy_workflow_bridge`, hygiene ADR
  audits), workflow-shell hygiene now scans both `.yml` + `.yaml` with
  auditable rule-level suppression comments, and release docs now align to the
  same-SHA preflight-first release-gates sequence enforced by publish lanes.
- MP-346 Rust guardrail expansion update: `rust_ci.yml` now emits clippy lint
  histogram JSON and enforces `check_clippy_high_signal.py` against
  `dev/config/clippy/high_signal_lints.json`; `devctl` AI guard + scaffolding
  docs now include `check_rust_test_shape.py` and
  `check_rust_runtime_panic_policy.py`, with unit coverage extended across
  `test_check.py`, `test_audit_scaffold.py`, and dedicated new check-script
  tests.
- MP-346 runtime-lane AI-guard range update: `rust_ci.yml`,
  `release_preflight.yml`, and `security_guard.yml` now resolve commit ranges
  through `workflow_shell_bridge.py resolve-range` and pass those refs to
  `devctl check --profile ai-guard`; `devctl check` also now sequences
  clippy-lint histogram collection before `clippy-high-signal-guard`, and
  naming-consistency parsing was split into a companion module to keep shape
  policy green. Strict clippy zero-warning status was restored after new lint
  families surfaced, and `rust/Cargo.toml` now sets `rust-version = 1.88.0`
  to match the active MSRV lane contract.
- MP-346 pending-guardrail closure update: `devctl release-gates` rendering is
  now Python-3.11-compatible, planned Clippy threshold ratchet is complete
  (`cognitive-complexity-threshold=25`, `too_many_lines=warn`), and new
  duplicate-type + structural-complexity guards are wired into AI-guard and
  audit-scaffold flows; periodic `jscpd` duplication auditing now has a
  dedicated wrapper (`check_duplication_audit.py`) for freshness/threshold
  evidence capture.
- MP-346 continuation audit update: the previously interrupted
  `devctl check --profile ci` rerun is now confirmed green end-to-end, stale
  pre-remediation evidence rows were removed from
  `ide_provider_modularization.md`, and `code_shape_policy.py` now carries an
  explicit path budget for `check_rust_lint_debt.py` so the tooling bundle
  remains non-regressive after the new guardrail wiring.
- MP-347 tooling-ops update: `devctl check --profile fast` now aliases
  `quick` for local iteration naming clarity, and `devctl check-router`
  selects docs/runtime/tooling/release lanes from changed paths with optional
  `--execute` routing of bundle commands plus risk-matrix add-ons.
- MP-347 bundle-governance update: canonical command-bundle authority now
  lives in `dev/scripts/devctl/bundle_registry.py`; `check-router` and
  `check_bundle_workflow_parity.py` now consume the registry, while AGENTS
  bundle blocks are rendered/reference-only docs.
- MP-347 bundle-render automation update: added
  `check_agents_bundle_render.py` (`--write` regen mode) and wired
  `docs-check --strict-tooling` to fail when AGENTS rendered bundle docs drift
  from canonical registry output.
- MP-347 lint-debt governance update: Rust dead-code debt is now inventoryable
  and policy-gated (`--report-dead-code`, `--fail-on-undocumented-dead-code`)
  with all current `#[allow(dead_code)]` instances documented by explicit
  `reason` metadata.
- MP-347 architecture-governance intake update (2026-03-08): post-release
  DevCtl hardening backlog now explicitly includes an
  `architecture_surface_sync` guard for changed/untracked paths plus a
  duplicate/shared-logic candidate guard so new repo surfaces fail earlier
  when they are not wired into authority docs, bundles, workflows, and
  canonical shared-helper boundaries.
- MP-346 formal closure (2026-03-05): Phase 6 governance gate closed;
  all release-scope structural/tooling/governance/testing conditions met
  for IDE-first matrix (4/4); post-release backlog (Gemini overlay,
  JetBrains+Claude render-sync, AntiGravity readiness) tracked in
  `ide_provider_modularization.md` Steps 3g/3h and Phase 5.
- Pre-release architecture audit progress (2026-03-05): Phases 1-7
  are now complete (Phase-7 added 5 new guard scripts, extended 3 existing
  guards, and added hygiene checks; 596/596 tests green).
  Phases 8-14 remain default-deferred post-release unless explicitly promoted
  by operator direction.
- Pre-release architecture audit execution kickoff (2026-03-06): Phase 16
  governance alignment is complete (single pre-release audit authority kept in
  `dev/active/pre_release_architecture_audit.md`; strict tooling
  docs/governance checks green), and the first do-now runtime remediation
  landed by replacing `main.rs` `env::set_var` usage with runtime theme/backend
  overrides; `cargo test --bin voiceterm` remains green (`1526` passed).
- Pre-release architecture audit follow-up (2026-03-06): the
  `feed_prompt_output_and_sync` structural-complexity exception was removed
  after the prompt-occlusion detection split reduced the function below the
  default guard thresholds (`score=9`, `branch_points=7`, `depth=3`).
- Pre-release architecture audit follow-up (2026-03-06): the
  `writer/state/redraw.rs::maybe_redraw_status` structural-complexity
  exception was removed after splitting redraw gating/geometry/apply/render
  helpers reduced the function below the default guard thresholds
  (`score=13`, `branch_points=2`, `depth=2`).
- Pre-release architecture audit follow-up (2026-03-06): writer-state dispatch
  now uses `writer/state/dispatch.rs` for message routing and
  `writer/state/dispatch_pty.rs` for PTY-heavy output. Temporary complexity
  exceptions for dispatch/redraw/prompt were removed after guard checks
  (`check_structural_complexity` `exceptions_defined=0`).
- Pre-release architecture audit follow-up (2026-03-06): readability cleanup
  simplified dense comment/policy wording in the writer dispatch path and
  guard policy text; targeted rustfmt alignment was applied to active Rust
  files and full `devctl check --profile ci` rerun is green.
- Pre-release architecture audit follow-up (2026-03-06): transition
  compatibility cleanup retired `audit-scaffold` legacy `dev/active/` output
  support and retired strict-tooling `dev/DEVELOPMENT.md` alias acceptance;
  `collect_git_status` now uses `git status --porcelain --untracked-files=all`
  so canonical `dev/guides/*` updates are detected without legacy fallback.

## Multi-Agent Coordination Board

This board remains the execution tracker for lane ownership/status.
`dev/active/review_channel.md` now holds the merged markdown-swarm lane plan,
instruction log, shared ledger, and signoff template. `code_audit.md` is the
only live cross-team reviewer/coder coordination surface during active swarm
execution.

Branch guards for all agents:

1. Start from `develop` (never from `master`).
2. Use dedicated worktrees and dedicated feature branches per agent.
3. Rebase each active agent branch after every merge to `origin/develop`.
4. Update this board before and after each execution batch.
5. Keep `master` release-only (merge/tag/publish only).
6. Shared hotspot files (`writer/state.rs`, `prompt_occlusion.rs`,
   `claude_prompt_detect.rs`, `theme/rule_profile.rs`,
   `theme/style_pack.rs`) require an explicit claim in the merged
   `review_channel.md` swarm ledger before edits when Theme
   (`MP-148..MP-182`), naming/API cohesion (`MP-267`), and MP-346 scopes
   overlap.

| Agent | Lane | Active-doc scope | MP scope (authoritative) | Worktree | Branch | Status | Last update (UTC) | Notes |
|---|---|---|---|---|---|---|---|---|
| `AGENT-1` | Codex architecture contract review | `dev/active/review_channel.md`, `dev/active/autonomous_control_plane.md` | `MP-340, MP-355` | `../codex-voice-wt-a1` | `feature/a1-codex-architecture-review` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Codex reviewer lane for controller/review/memory contract boundaries. |
| `AGENT-2` | Codex clean-code and state-boundary review | `dev/active/review_channel.md` + runtime pack | `MP-267, MP-340, MP-355` | `../codex-voice-wt-a2` | `feature/a2-codex-clean-code-review` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Codex reviewer lane for duplication, ownership drift, and mixed-state violations. |
| `AGENT-3` | Codex runtime and handoff review | `dev/active/review_channel.md`, `dev/active/memory_studio.md` + runtime pack | `MP-233, MP-238, MP-243, MP-340, MP-355` | `../codex-voice-wt-a3` | `feature/a3-codex-runtime-handoff-review` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Codex reviewer lane for handoff, bootstrap, memory-bridge, and runtime correctness. |
| `AGENT-4` | Codex CI and workflow reviewer | `dev/active/review_channel.md` + tooling pack | `MP-297, MP-298, MP-303, MP-306, MP-355` | `../codex-voice-wt-a4` | `feature/a4-codex-ci-workflow-review` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Codex reviewer lane for CI/CD, bundle/workflow parity, and push-safety. |
| `AGENT-5` | Codex devctl and process-hygiene reviewer | `dev/active/devctl_reporting_upgrade.md`, `dev/active/host_process_hygiene.md` | `MP-297, MP-298, MP-300, MP-303, MP-306, MP-356` | `../codex-voice-wt-a5` | `feature/a5-codex-devctl-process-review` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Codex reviewer lane for `devctl`, cleanup/audit flow, and maintainer-surface correctness. |
| `AGENT-6` | Codex overlay and UX reviewer | `dev/active/review_channel.md`, `dev/active/autonomous_control_plane.md` + runtime pack | `MP-340, MP-355` | `../codex-voice-wt-a6` | `feature/a6-codex-overlay-ux-review` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Codex reviewer lane for Control/Review/Handoff UX, hitboxes, redraw, and footer honesty. |
| `AGENT-7` | Codex guard and test reviewer | `dev/active/review_channel.md`, `dev/active/host_process_hygiene.md` + tooling pack | `MP-303, MP-355, MP-356` | `../codex-voice-wt-a7` | `feature/a7-codex-guard-review` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Codex reviewer lane for guard coverage, regression tests, and audit evidence quality. |
| `AGENT-8` | Codex integration and re-review loop | `dev/active/MASTER_PLAN.md`, `dev/active/review_channel.md` | `MP-340, MP-355, MP-356` | `../codex-voice-wt-a8` | `feature/a8-codex-integration-review` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; primary Codex merge/readiness lane that polls every 5 minutes when Claude is still coding. |
| `AGENT-9` | Claude bridge push-safety fixes | `dev/active/review_channel.md` + tooling pack | `MP-303, MP-306, MP-355` | `../codex-voice-wt-a9` | `feature/a9-claude-bridge-push-safety` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Claude coding lane for bridge-gate, workflow-order, and branch push-safety fixes. |
| `AGENT-10` | Claude live Git-context fixes | `dev/active/review_channel.md`, `dev/active/autonomous_control_plane.md` + runtime pack | `MP-340, MP-355` | `../codex-voice-wt-a10` | `feature/a10-claude-git-context-fixes` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Claude coding lane for session-root Git context and repo-snapshot correctness. |
| `AGENT-11` | Claude refresh, redraw, and footer fixes | `dev/active/review_channel.md` + runtime pack | `MP-340, MP-355` | `../codex-voice-wt-a11` | `feature/a11-claude-refresh-redraw-fixes` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Claude coding lane for Control/Handoff refresh honesty, error redraw, and footer-hitbox alignment. |
| `AGENT-12` | Claude broker and clipboard fixes | `dev/active/review_channel.md`, `dev/active/autonomous_control_plane.md` + runtime pack | `MP-340, MP-355` | `../codex-voice-wt-a12` | `feature/a12-claude-broker-clipboard-fixes` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Claude coding lane for broker shutdown cleanup/reporting and writer-routed clipboard behavior. |
| `AGENT-13` | Claude handoff and bootstrap fixes | `dev/active/review_channel.md`, `dev/active/memory_studio.md` + runtime pack | `MP-233, MP-238, MP-243, MP-340, MP-355` | `../codex-voice-wt-a13` | `feature/a13-claude-handoff-bootstrap-fixes` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Claude coding lane for fresh-prompt bootstrap docs, handoff packet context, and memory-compatible resume paths. |
| `AGENT-14` | Claude workflow and publication-sync fixes | `dev/active/devctl_reporting_upgrade.md` + tooling pack | `MP-297, MP-298, MP-300, MP-303, MP-306` | `../codex-voice-wt-a14` | `feature/a14-claude-workflow-publication-fixes` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Claude coding lane for publication-sync scope, workflow ordering, and tooling-gate rationalization. |
| `AGENT-15` | Claude clean-code refactors | `dev/active/naming_api_cohesion.md`, `dev/active/review_channel.md` + runtime/tooling packs | `MP-267, MP-340, MP-355` | `../codex-voice-wt-a15` | `feature/a15-claude-clean-code-refactors` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Claude coding lane for dedup, separation-of-concerns cleanup, and mixed-state untangling that reviewers flag. |
| `AGENT-16` | Claude proof and regression closure | `dev/active/review_channel.md`, `dev/active/host_process_hygiene.md` + runtime/tooling packs | `MP-303, MP-340, MP-355, MP-356` | `../codex-voice-wt-a16` | `feature/a16-claude-proof-regression-closure` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Claude coding lane for final guard green runs, regression proofs, and cross-lane verification closeout. |

## Strategic Direction

- Protect current moat: terminal-native PTY orchestration, prompt-aware queueing, local-first voice flow.
- Close trust gap: latency metrics must match user perception and be auditable.
- Build differentiated product value in phases:
  1. Visual-first UX pass (telemetry, motion, layout polish, theme ergonomics)
  2. Workflow differentiators (voice navigation, history, CLI workflow polish)
  3. Theme-systemization (visual surfaces first, then full Theme Studio control parity)
  4. Advanced expansion (streaming STT, tmux/neovim, accessibility)

## Unified Active-Docs Phased Map (Execution Order)

This is the cross-plan execution map so agents and developers stay aligned on
main goal and sequence across all active docs.

### Phase A - Governance + Scope Integrity

1. Keep one execution tracker (`MASTER_PLAN`) and strict active-doc sync.
2. Enforce repeat-to-automate and audit evidence as default operating mode.

Mapped scopes:

- `MP-333`, `MP-337`
- `dev/active/INDEX.md`
- `dev/active/review_channel.md`

### Phase B - Runtime and Workspace Reliability Baseline

1. Keep runtime safety/perf/teardown/wake-word hardening green.
2. Complete workspace layout migration so path contracts are stable.

Mapped scopes:

- `MP-127..MP-138`, `MP-341`, `MP-346`, `MP-354`, runtime hardening + host/provider modularization docs.

### Phase C - Tooling Control Plane + Loop Foundations

1. Keep `devctl` reporting/control-plane lane as the automation backbone.
2. Keep Ralph + mutation loops bounded, source-correlated, and policy-gated.
3. Keep external federation bridges pinned and governed.

Mapped scopes:

- `MP-297..MP-300`, `MP-303`, `MP-306`, `MP-325..MP-329`, `MP-334`
- `dev/active/devctl_reporting_upgrade.md`
- `dev/active/autonomous_control_plane.md` (Phases 1-2/5/6)

### Phase D - Theme/Visual Platform Completion

1. Finish resolver-first Theme Studio migration.
2. Keep visual parity gates strict before any GA expansion.

Mapped scopes:

- `MP-148..MP-182`
- `dev/active/theme_upgrade.md`

### Phase E - Memory + Action Studio Platform

1. Build semantic memory + retrieval + action governance without runtime regressions.
2. Promote only with quality, isolation, and compaction gates passing.

Mapped scopes:

- `MP-230..MP-255`
- `dev/active/memory_studio.md`

### Phase F - Architect Controller (Rust TUI + iPhone + Agent Relay)

1. Deliver unified controller state model consumed by Rust Dev panel and phone.
2. Deliver guarded remote controls and reviewer-agent packet relay.
3. Keep branch/CI/replay policy gates mandatory before promote/write actions.

Mapped scopes:

- `MP-330..MP-332`, `MP-336`, `MP-338`
- `MP-340`
- `dev/active/autonomous_control_plane.md` (Phase 3 + 3.5 + 3.7 + 6.1)
- `dev/active/loop_chat_bridge.md`

### Phase G - Release Hardening + Template Extraction

1. Complete rollout soak, policy hardening, and full audit loops.
2. Extract reusable template package only after governance parity is proven.

Mapped scopes:

- `autonomous_control_plane` rollout/template phases
- release/tracker governance bundles and CI lanes.

## ADR Program Backlog (Cross-Plan, Pending)

Create these ADRs in order so agents/dev do not lose architectural scope.
Accepted authorities for unified controller state contract and agent relay
packet protocol have landed (see `dev/adr/0027-*` and `dev/adr/0028-*`).

Remaining backlog:

1. `ADR-0029` Operator Action Policy Model:
   action classes, approval gates, replay/nonce rules, and deny semantics.
2. `ADR-0030` Phone Adapter Architecture:
   SSH-first, push/SMS/chat adapters, auth boundaries, and fallback strategy.
3. `ADR-0031` Rust Dev-Panel Control-Plane Boundary:
   what stays runtime-local vs control-plane-fed; non-interference guarantees.
4. `ADR-0032` Autonomous Loop Stage Machine:
   triage/plan/fix/verify/review/promote transitions and stop conditions.
5. `ADR-0033` Autonomy Metrics + Scientific Audit Method:
   KPI definitions, experiment protocol, and promotion criteria.
6. `ADR-0034` Template Extraction Contract:
   what must be standardized before reuse across repositories.

## Phase 0 - Completed Release Stabilization (v1.0.51-v1.0.52)

- [x] MP-072 Prevent HUD/timer freeze under continuous PTY output.
- [x] MP-073 Improve IDE terminal input compatibility and hidden-HUD discoverability.
- [x] MP-074 Update docs for HUD/input behavior changes and debug guidance.
- [x] MP-075 Finalize latency display semantics to avoid misleading values.
- [x] MP-076 Add latency audit logging and regression tests for displayed latency behavior.
- [x] MP-077 Run release verification (`cargo build --release --bin voiceterm`, tests, docs-check).
- [x] MP-078 Finalize release notes, bump version, tag, push, GitHub release, and Homebrew tap update.
- [x] MP-096 Expand SDLC agent governance: post-push audit loop, testing matrix by change type, CI expansion policy, and per-push docs sync requirements.
- [x] MP-099 Consolidate overlay research into a single reference source (now consolidated under `dev/active/theme_upgrade.md`) and mirror candidate execution items in this plan.

## Phase 1 - Latency Truth and Observability

- [x] MP-079 Define and document latency terms (capture, STT, post-capture processing, displayed HUD latency).
- [x] MP-080 Hide latency badge when reliable latency cannot be measured.
- [x] MP-081 Emit structured `latency_audit|...` logs for analysis.
- [x] MP-082 Add automated tests around latency calculation behavior.
- [x] MP-097 Fix busy-output HUD responsiveness and stale meter/timer artifacts (settings lag under Codex output, stale REC duration/dB after capture, clamp meter floor to stable display bounds).
- [x] MP-098 Eliminate blocking PTY input writes in the overlay event loop so queued/thinking backend output does not stall live typing responsiveness.
- [x] MP-083 Run and document baseline latency measurements with `latency_measurement` and `dev/scripts/tests/measure_latency.sh` (`dev/archive/2026-02-13-latency-baseline.md`).
- [x] MP-084 Add CI-friendly synthetic latency regression guardrails (`.github/workflows/latency_guard.yml` + `measure_latency.sh --ci-guard`).
- [x] MP-194 Normalize HUD latency severity using speech-relative STT speed (`rtf`) while preserving absolute STT delay display and audit logging fields (`speech_ms`, `rtf`) to reduce false "slow" signals on long utterances.
- [x] MP-195 Stop forwarding malformed/fragmented SGR mouse-report escape bytes into wrapped CLI input during interrupts so raw `[<...` fragments do not leak to users.
- [x] MP-196 Expand non-speech transcript sanitization for ambient-sound hallucination tags (`siren`, `engine`, `water` variants) before PTY delivery.
- [x] MP-111 Add governance hygiene automation for archive/ADR/script-doc drift (`python3 dev/scripts/devctl.py hygiene`) and codify archive/ADR lifecycle policy.
- [x] MP-122 Prevent mutation-lane timeout by sharding scheduled `cargo mutants` runs and enforcing one aggregated score across shards.

## Phase 2 - Overlay Quick Wins

- [x] MP-085 Voice macros and custom triggers (`.voiceterm/macros.yaml`).
- [x] MP-086 Runtime macros ON/OFF toggle (settings state + transcript transform gate).
- [x] MP-087 Restore baseline send-mode semantics (`auto`/`insert`) without an extra review-first gate.
- [x] MP-112 Add CI voice-mode regression lane for macros-toggle and send-mode behavior (`.github/workflows/voice_mode_guard.yml`).
- [x] MP-088 Persistent user config (`~/.config/voiceterm/config.toml`) for core preferences (landed runtime load/apply/save flow with CLI-precedence guards, explicit-flag detection for default-valued args, and status-state restore coverage for macros toggle).

## Phase 2A - Visual HUD Sprint (Current Priority)

- [x] MP-101 Add richer HUD telemetry visuals (sparkline/chart/gauge) with bounded data retention.
- [x] MP-100 Add animation transition framework for overlays and state changes (TachyonFX or equivalent).
- [x] MP-054 Optional right-panel visualization modes in minimal HUD.
- [x] MP-105 Add adaptive/contextual HUD layouts and state-driven module expansion.
- [x] MP-113 Tighten startup splash ergonomics and IDE compatibility (shorter splash duration, reliable teardown in IDE terminals, corrected startup tagline centering, and better truecolor detection for JetBrains-style terminals).
- [x] MP-114 Polish startup/theme UX in IDE terminals (remove startup top-gap, keep requested themes on 256-color terminals, and render Theme Picker neutral when current theme is `none`).
- [x] MP-115 Stabilize terminal compatibility regressions (drop startup arrow escape noise during boot, suppress Ctrl+V idle pulse dot beside `PTT`, and restore conservative ANSI fallback when truecolor is not detected).
- [x] MP-116 Fix JetBrains terminal HUD duplication by hardening scroll-region cursor restore semantics.
- [x] MP-117 Prevent one-column HUD wrap in JetBrains terminals (status-banner width guard + row truncation safety).
- [x] MP-118 Harden cross-terminal HUD rendering and PTY teardown paths (universal one-column HUD safety margin, writer-side row clipping to terminal width, and benign PTY-exit write error suppression on shutdown).
- [x] MP-119 Restore the stable `v1.0.53` writer/render baseline for Full HUD while retaining the one-column layout safety margin to recover reliable IDE terminal rendering.
- [x] MP-120 Revert unstable post-release scroll-region protection changes that reintroduced severe Full HUD duplication/corruption during active Codex output.
- [x] MP-121 Harden JetBrains startup/render handoff by auto-skipping splash in IDE terminals and clearing stale HUD/overlay rows on resize before redraw.
- [x] MP-123 Harden PTY/IPC backend teardown to signal process groups and reap child processes, with regression tests that verify descendant cleanup.
- [x] MP-183 Add a PTY session-lease guard that reaps backend process groups from dead VoiceTerm owners before spawning new sessions, without disrupting concurrently active sessions.
- [x] MP-190 Restore Full HUD shortcuts-row trailing visualization alignment so the right panel remains anchored to the far-right corner in full-width layouts.
- [x] MP-124 Add Full-HUD border-style customization (including borderless mode) and keep right-panel telemetry explicitly user-toggleable to `Off`.
- [x] MP-125 Fix HUD right-panel `Anim only` behavior so idle state keeps a static panel visible instead of hiding the panel until recording.
- [x] MP-126 Complete product/distribution naming rebrand to VoiceTerm across code/docs/scripts/app launcher, and add a PyPI launcher package scaffold (`pypi/`) for `voiceterm`.
- [x] MP-139 Tighten user-facing docs information architecture (entrypoint clarity, navigation consistency, and guide discoverability).
- [x] MP-104 Add explicit voice-state visualization (idle/listening/processing/responding) with clear transitions.
- [x] MP-055 Quick theme switcher in settings.
- [x] MP-102 Add toast notification center with auto-dismiss, severity, and history review (landed runtime status-to-toast ingestion with severity mapping, `Ctrl+N` notification-history overlay toggle, periodic auto-dismiss/re-render behavior, and input/parser/help/docs coverage for toast-history control flow).
- [x] MP-226 Fix Claude-mode command/approval prompt occlusion in active overlay sessions: when Claude enters interactive Bash approval or sandbox permission prompts (for example `Do you want to proceed?` while running `Bash(...)` or cross-worktree read prompts), VoiceTerm HUD/overlay rows can obscure prompt text and controls; implement a Claude-specific prompt-state rendering policy (overlay layering, temporary HUD suppression/resume, or reserved prompt-safe rows) so prompts remain readable/actionable without losing runtime status clarity, with non-regression validation for Codex, Cursor, and JetBrains terminals. (2026-02-27 follow-up hardening: suppression now targets high-confidence interactive approval/permission contexts only; low-confidence generic/composer text no longer triggers HUD suppression to avoid disappear/reappear flicker during normal Codex runs. Additional 2026-02-27 resilience update: terminal row/col resolution now normalizes zero-size IDE probes and writer startup redraw uses normalized size fallback so HUD resume/startup does not wait for a keypress. 2026-02-28 targeted overlay follow-up: numbered approval-card detection now suppresses HUD for sparse `1/2/3` option cards, suppression transitions synchronize normalized geometry with writer redraw, and Cursor transition pre-clear now scrubs stale border fragments during `ClearStatus` handoff paths. 2026-02-28 anti-cycle follow-up: Cursor non-rolling hosts no longer engage suppression from tool-activity text alone, and now use explicit/numbered approval-card hints for suppression engagement to prevent keypress-triggered HUD disappearance in normal composer flow.)
  - Repro note (2026-02-19): issue severity appears higher for local/worktree permission prompts during multi-tool explore batches (`+N more tool uses`), while some single-command Claude prompt flows appear acceptable.
  - Additional repro signal (2026-02-19): severity appears correlated with vertical UI density (long wrapped absolute command paths, larger active task list sections, and multi-line tool-batch summaries), suggesting row-budget/stacking pressure near bottom prompt rows.
  - Repro note (2026-02-19, screenshot evidence): during parallel/background-agent orchestration in Claude, long "workaround options" + permission-wall text can exceed available row budget and push prompt/action rows into unreadable overlap, while equivalent Codex sessions remain readable; treat this as a Claude-specific layout compaction/reserved-row failure case.
  - Evidence to capture per repro: terminal rows/cols, HUD mode/style, prompt type (single-command approval vs local/worktree permission), command preview line-wrap count, tool-batch summary presence (`+N more tool uses`), and screenshot before/after prompt render.
  - 2026-02-28 diagnostic follow-up: added gated Claude HUD tracing (`VOICETERM_DEBUG_CLAUDE_HUD=1`) across prompt-occlusion transitions and writer redraw/defer decisions to isolate a new Cursor+Claude normal-typing regression where HUD disappears after the first keypress (non-approval flow).
  - 2026-02-28 writer follow-up: tightened tool-activity suppression overmatch for plain transcript headings, added explicit stale-banner-anchor clearing in writer redraw, and added a short delayed Cursor+Claude typing repair redraw path to recover minimal-HUD line clobber without reintroducing per-keystroke flash.
  - 2026-02-28 minimal-HUD follow-up: Cursor+Claude typing-hold deferral now bypasses for active one-row HUD frames so minimal-HUD redraw is not postponed behind typing bursts, while full-HUD deferral policy remains unchanged.
  - 2026-02-28 traceability follow-up: Cursor+Claude writer debug logs now emit explicit user-input activity scheduling and enhanced-status render decisions (`prev/next banner height`, `hud_style`, `prompt_suppressed`), and pre/post transition flags are now computed from pre-apply state to prevent false-no-change traces while reproducing the remaining disappearance/overwrite regressions.
  - 2026-02-28 repaint follow-up: pre-clear transition redraws now force full banner repaint (no previous-line diff reuse) in Cursor+Claude paths, with explicit `transition redraw mode` debug traces to prove redraw mode on failing keypress/tool-output sequences.
  - 2026-02-28 non-rolling approval-window follow-up: Cursor non-rolling prompt suppression now keeps a short ANSI-stripped rolling approval window so split approval cards (`Do you want to proceed?` + later `1/2/...` options) still suppress HUD deterministically, while debug traces now log chunk/window match sources (`chunk_*` vs `window_*`) to distinguish real prompt hits from missed detections. Writer repair scheduling was also hardened so future Cursor+Claude repair deadlines are not cleared by unrelated redraws before they fire, reducing one-row HUD “disappear until refresh” loops during typing.
  - 2026-02-28 non-rolling release-gate + row-budget tracing follow-up: Cursor non-rolling suppression now requires explicit input-resolution arming plus drained approval window before release (prevents debounce-only unsuppress while approval context remains live), prompt-context fallback markers now keep detection active when backend label routing is noisy (`Tool use`, `Claude wants to`, `What should Claude do instead?`), Cursor Claude extra gap rows increased (`8 -> 10`), and `apply_pty_winsize` debug traces now emit backend/mode/rows/cols/reserved-rows/PTY-rows so overlay overlap can be diagnosed from logs instead of screenshots alone.
  - 2026-02-28 high-confidence guard follow-up: explicit/numbered approval hints now promote `prompt_guard_enabled` in non-rolling paths, so approval cards can suppress HUD even when backend-label guard signals are noisy; runtime debug chunk logs now include `backend_label` + `prompt_guard` booleans for direct branch tracing; non-rolling suppression semantics are now covered by deterministic thread-local test overrides (no shared env mutation races under parallel test execution).
  - 2026-03-01 stress-loop traceability follow-up: added deterministic Cursor+Claude stress artifact capture under `dev/reports/audits/claude_hud_stress/*` (frame snapshots + log counters + anomaly summaries), narrowed non-rolling release-arm consumption to substantial post-input activity, deferred release-arm relatch on window-only stale hints, and hardened writer typing-hold urgency detection for post-`ClearStatus` suppression transitions so approval/HUD churn can be diagnosed via logs and artifact IDs instead of screenshot-only loops. Current status remains partial (approval overlap reduced but not eliminated; see `dev/audits/2026-02-27-terminal-overlay-regression-audit.md` A2.10).
  - 2026-03-01 rapid-approval hold + frame/log correlation follow-up: non-rolling input-resolution now arms an explicit sticky suppression hold window to avoid unsuppress gaps between consecutive approval cards, and `claude_hud_stress.py` now records frame timestamps plus bottom-row HUD visibility and correlates each frame to suppression-transition/redraw-commit log events for deterministic overlap attribution (see `dev/audits/2026-02-27-terminal-overlay-regression-audit.md` A2.11). Local stress execution in this sandbox remains blocked by detached `screen` session startup failure, so fresh artifact generation is still pending a full terminal host.
  - 2026-03-01 wrapped-approval depth + anomaly-capture follow-up: expanded non-rolling approval scan depth (`2048 -> 8192` bytes, `12 -> 64` lines) so long wrapped option cards in Cursor prompt UIs continue matching numbered approval semantics, and added explicit anomaly logging for `explicit approval hint seen without numbered-match` to surface residual detector misses in runtime logs instead of relying on screenshots alone (see `dev/audits/2026-02-27-terminal-overlay-regression-audit.md` A2.12).
  - 2026-03-01 overlay occlusion closure follow-up: PTY startup winsize is now derived from measured terminal geometry before backend spawn (HUD-aware from frame 1), writer HUD rendering now fences PTY scrolling above reserved HUD rows via scroll-region controls, and resize transitions now force immediate redraw after pre-clear so grow/shrink cycles do not leave input rows hidden until another keypress.
  - 2026-03-01 JetBrains+Claude rendering follow-up: status/banner clear-to-EOL paths now reset ANSI attributes before trimming trailing columns so dark HUD style attributes cannot leak into typed prompt text, and JetBrains Claude extra gap rows now default to `2` for safer startup prompt/HUD separation.
  - 2026-03-01 post-v1.0.98 typing follow-up: JetBrains+Claude writer pre-clear now defers while user input is fresh (typing-hold window) so startup typing bursts do not destructively clear half-HUD rows before idle redraw can restore them.
- [x] MP-285 Standardize HUD policy across all backends: removed Gemini-specific compaction logic to ensure a consistent 4-row Full HUD experience and unified flicker-reduction behavior across Codex, Claude, and Gemini backends.

## Phase 2B - Rust Hardening Audit (Pre-Execution + Implementation)

- [x] MP-127 Replace IPC `/exit` hard process termination with graceful shutdown orchestration and teardown event guarantees (FX-001).
- [x] MP-128 Add explicit runtime ownership and bounded shutdown/join semantics for overlay writer/input threads (FX-002).
- [x] MP-129 Add voice-manager lifecycle hardening for quit-while-recording paths, including explicit stop/join policy and tests (FX-003).
- [x] MP-130 Consolidate process-group signaling/reaping helpers into one canonical utility with invariants tests (FX-004).
- [x] MP-131 Add security/supply-chain CI lane with policy thresholds and failing gates for high-severity issues (FX-005).
- [x] MP-132 Add explicit security posture/threat-model documentation and risky flag guidance (including permission-skip behavior) (FX-006).
- [x] MP-133 Enforce IPC auth timeout + cancellation semantics using tracked auth start timing (FX-007).
- [x] MP-134 Replace IPC fixed-sleep scheduling with event-driven receive strategy to reduce idle CPU jitter (FX-008).
- [x] MP-135 Decompose high-risk event-loop transition/wiring complexity to reduce change blast radius (FX-009).
- [x] MP-136 Establish unsafe-governance checklist for unsafe hotspots with per-invariant test expectations (FX-010).
- [x] MP-137 Add property/fuzz coverage lane for parser and ANSI/OSC boundary handling (FX-011).
- [x] MP-138 Enforce audit/master-plan traceability updates as a mandatory part of each hardening fix (FX-012).
- [x] MP-152 Consolidate hardening governance to `MASTER_PLAN` as the only active tracker: archive `RUST_GUI_AUDIT_2026-02-15.md` under `dev/archive/` and retire dedicated audit-traceability CI/tooling.

## Phase 2C - Theme System Upgrade (Architecture + Guardrails)

Theme Studio execution gate: MP-148..MP-182 are governed by the checklist in
this section. A Theme Studio MP may move to `[x]` only with documented pass
evidence for its mapped gates.

Theme/modularization integration rule: when refactors or fixes touch visual
runtime modules (`theme/*`, `theme_ops.rs`, `theme_picker.rs`, `status_line/*`,
`hud/*`, `writer/*`, `help.rs`, `banner.rs`), update or add the
corresponding `MP-148+` item here in `MASTER_PLAN` and attach mapped
`TS-G*` gate evidence from this section.

Settings-vs-Studio ownership matrix:

| Surface | Owner |
|---|---|
| Theme tokens/palettes, borders, glyph/icon packs, layout/motion behavior, visual state scenes, notification visuals, command-palette/autocomplete visuals | Theme Studio |
| Auto-voice/send-mode/macros, sensitivity/latency display mode, mouse mode, backend/pipeline, close/quit operations | Settings |
| Quick theme cycle and picker shortcuts | Shared entrypoint; deep editing still routes to Theme Studio |

Theme Studio Definition of Done (authoritative checklist):

| Gate | Pass Criteria | Fail Criteria | Required Evidence |
|---|---|---|---|
| `TS-G01 Ownership` | Theme Studio vs Settings ownership matrix is implemented and documented. | Any deep visual edit path remains in Settings post-migration. | Settings menu tests + docs diff. |
| `TS-G02 Schema` | `StylePack` schema/version/migration tests pass for valid + invalid inputs. | Parsing/migration panic, silent drop, or invalid pack applies without fallback. | Unit tests for parse/validate/migrate + fallback tests. |
| `TS-G03 Resolver` | All render paths resolve styles through registry/resolver APIs. | Hardcoded style constants bypass resolver on supported surfaces. | Coverage + static policy gate outputs. |
| `TS-G04 Component IDs` | Every renderable component/state has stable style IDs and defaults. | Unregistered component/state renders in runtime. | Component registry parity tests + snapshots. |
| `TS-G05 Studio Controls` | Every persisted style field is editable in Studio. | Any persisted field has no Studio control mapping. | Studio mapping parity test results. |
| `TS-G06 Snapshot Matrix` | Snapshot suites pass for widths, states, profiles, and key surfaces. | Layout overlap/wrap/clipping regressions vs expected fixtures. | Snapshot artifacts for narrow/medium/wide + state variants. |
| `TS-G07 Interaction UX` | Keyboard-only and mouse-enhanced flows both work with correct focus/hitboxes. | Broken focus order, unreachable controls, or hitbox mismatch. | Interaction integration tests + manual QA checklist output. |
| `TS-G08 Edit Safety` | Apply/save/import/export/undo/redo/rollback flows are deterministic. | User edits can be lost/corrupted or cannot be reverted safely. | End-to-end workflow tests across restart boundaries. |
| `TS-G09 Capability Fallback` | Terminal capability detection + fallback chains behave as specified. | Unsupported capability path crashes or renders unreadable output. | Compatibility matrix tests (truecolor/ansi, graphics/no-graphics). |
| `TS-G10 Runtime Budget` | Render/update paths remain within bounded allocation/tick budgets. | Unbounded buffers, allocation spikes, or frame-thrash in hot paths. | Perf/memory checks + regression benchmarks. |
| `TS-G11 Docs/Operator` | Architecture, usage, troubleshooting, and changelog are updated together. | User-visible behavior changes without aligned docs. | `docs-check` + updated docs references. |
| `TS-G12 Release Readiness` | Full Theme Studio GA validation bundle is green. | Any mandatory gate is missing evidence or failing. | CI report bundle + signoff checklist. |
| `TS-G13 Inspector` | Any rendered element can reveal style path and jump to Studio control. | Inspector cannot locate style ID/path for a rendered element. | Inspector integration tests + state preview tests. |
| `TS-G14 Rule Engine` | Conditional style rules are deterministic and conflict-resolved. | Rule priority conflicts or nondeterministic style outcomes. | Rule engine unit/property tests + scenario snapshots. |
| `TS-G15 Ecosystem Packs` | Third-party widget packs are allowlisted, version-compatible, and parity-mapped. | Dependency added without compatibility matrix or style/studio parity mapping. | Compatibility matrix + parity tests + allowlist audit. |

Theme Studio MP-to-gate mapping:

| MP | Required Gates |
|---|---|
| `MP-148` | `TS-G01`, `TS-G11` |
| `MP-149` | `TS-G02`, `TS-G06`, `TS-G09` |
| `MP-150` | `TS-G02`, `TS-G03` |
| `MP-151` | `TS-G11` |
| `MP-161` | `TS-G03`, `TS-G06`, `TS-G07` |
| `MP-162` | `TS-G03`, `TS-G05` |
| `MP-163` | `TS-G03` |
| `MP-172` | `TS-G04`, `TS-G06` |
| `MP-174` | `TS-G03`, `TS-G05`, `TS-G06` |
| `MP-175` | `TS-G09`, `TS-G15` |
| `MP-176` | `TS-G09`, `TS-G06` |
| `MP-179` | `TS-G15` |
| `MP-180` | `TS-G15`, `TS-G05`, `TS-G06` |
| `MP-182` | `TS-G14`, `TS-G05`, `TS-G06` |
| `MP-164` | `TS-G07` |
| `MP-165` | `TS-G01`, `TS-G07` |
| `MP-166` | `TS-G05`, `TS-G08`, `TS-G07` |
| `MP-167` | `TS-G06`, `TS-G09`, `TS-G10`, `TS-G11`, `TS-G12` |
| `MP-173` | `TS-G03`, `TS-G05`, `TS-G15` |
| `MP-177` | `TS-G15`, `TS-G05` |
| `MP-178` | `TS-G13`, `TS-G07` |
| `MP-181` | `TS-G07`, `TS-G10` |

Theme Studio mandatory verification bundle (per PR):

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py docs-check --user-facing`
- `python3 dev/scripts/devctl.py hygiene`
- `cd rust && cargo test --bin voiceterm`
- use `.github/PULL_REQUEST_TEMPLATE/theme_studio.md` for `TS-G01`..`TS-G15` evidence capture.

- [x] MP-148 Activate the Theme Studio phased track in `MASTER_PLAN` and lock the IA boundary: dedicated `Theme Studio` mode (not `Settings -> Studio`) plus Settings-vs-Studio ownership matrix (landed gate catalog + MP-to-gate map + ownership matrix directly in Phase 2C so visual modularization/fix work now maps to one canonical tracker).
- [x] MP-149 Implement Theme Upgrade Phase 0 safety rails (golden render snapshots, terminal compatibility matrix coverage, and style-schema migration harness) before any user-visible editor expansion (landed style-schema migration harness in `theme/style_schema.rs`, terminal capability matrix tests in `color_mode`, and golden snapshot-matrix coverage for startup banner, theme picker, and status banner render outputs).
- [x] MP-150 Implement Theme Upgrade Phase 1 style engine foundation (`StylePack` schema + resolver + runtime), preserving current built-in theme behavior and startup defaults (landed runtime resolver scaffold `theme/style_pack.rs`, routed `Theme::colors()` through resolver with palette-parity regression tests, enabled runtime schema parsing/migration (`theme/style_schema.rs`) for pack payload ingestion, and hardened schema-version mismatch/invalid-payload fallback to preserve base-theme palettes instead of dropping to `none`).
- [x] MP-151 Ship docs/architecture updates for the new theme system (`dev/ARCHITECTURE.md`, `guides/USAGE.md`, `guides/TROUBLESHOOTING.md`, `dev/CHANGELOG.md`) in lockstep with implementation, including operator guidance, settings-migration guidance, and fallback behavior (landed runtime resolver path docs, schema payload operator guidance, explicit settings-migration notes, and invalid-pack fallback behavior across architecture/usage/troubleshooting/changelog docs).

## Phase 2D - Visual Surface Expansion (Theme Studio Prerequisite)

- [ ] MP-161 Execute a visual-first runtime pass before deep Studio editing: with MP-102 complete, promote MP-103, MP-106, MP-107, MP-108, and MP-109 from Backlog into active execution order with non-regression gates (in progress: toast-history overlay row-width accounting and title rendering were hardened so unicode/ascii glyph themes keep border alignment without stale right-edge artifacts).
- [ ] MP-162 Extend `StylePack` schema/resolver so each runtime visual surface is style-pack addressable (widgets/graphs, toasts, voice-state scenes, command palette, autocomplete, dashboard surfaces), even before all Studio pages ship (in progress: schema/resolver now supports runtime visual overrides for border glyph sets, indicator glyph families, and glyph-set profile selection (`glyphs`: `unicode`/`ascii`) via style-pack payloads, including compact/full/minimal/hidden processing/responding indicator lanes in status rendering while preserving default processing spinner animation unless explicitly overridden; 2026-03-07 aligned next slice: persisted payload-driven runtime routing must close `surfaces.toast_position`, `surfaces.startup_style`, `components.toast_severity_mode`, and `components.banner_style`, not just runtime-only Theme Studio overrides. 2026-03-09 Codex re-review: the status-line ASCII separator leak is closed, but persisted payload-driven consumer proof is still incomplete for those startup/toast/banner fields; keep MP-162 open until consumer-level coverage lands, not just resolver wiring.)
- [x] MP-163 Add explicit coverage tests/gates that fail if new visual runtime surfaces bypass theme resolver paths with hardcoded style constants (landed `theme::tests::runtime_sources_do_not_bypass_theme_resolver_with_palette_constants`, a source-policy gate that scans runtime Rust modules and fails when `THEME_*` palette or `BORDER_*` border constants are referenced outside theme resolver/style-ownership allowlist files).
- [ ] MP-172 Add a styleable component registry and state-matrix contract for all renderable control surfaces (buttons, tabs, lists, tables, trees, scrollbars, modal/popup/tooltip, input/caret/selection) with schema + resolver + snapshot coverage (2026-03-07 alignment note: `theme::component_registry` is still gated by `theme_studio_v2`; the next slice must make that boundary explicit and separate live vs planned registry inventory before registry-backed Studio or CI parity becomes authoritative).
- [ ] MP-174 Migrate existing non-HUD visual surfaces into `StylePack` routing (startup splash/banner, help/settings/theme-picker chrome, calibration/mic-meter visuals, progress bars/spinners, icon/glyph sets) so no current visual path is left outside Theme Studio ownership (in progress: processing/progress spinner rendering paths now resolve through theme/style-pack indicators instead of hardcoded frame constants, glyph-family routing now drives HUD queue/latency/meter symbols + status-line waveform placeholders/pulse dots + progress bar/block/bounce glyphs, `components.progress_bar_family` now routes progress/meter glyph profiles through style-pack resolution, audio-meter calibration/waveform rendering resolves bar/wave/marker glyphs from the shared theme profile, overlay chrome/footer/slider glyphs across help/settings/theme-picker now route through the active glyph profile with footer close hit-testing parity for unicode/ascii separators, startup banner/footer separators now honor glyph-set overrides (`unicode`/`ascii`) across full/compact/minimal banner variants, explicit spinner-style overrides now fall back to ASCII-safe animation frames when glyph profile is ASCII, theme-switch interactions now surface explicit style-pack lock state (read-only/dimmed picker + locked status messaging) when schema payload `base_theme` is active, component-level border routing now resolves `components.overlay_border` across overlay surfaces including transcript-history plus `components.hud_border` for Full-HUD `Theme` border mode through style-pack resolver paths, and 2026-03-09 follow-up hardening routed the remaining status-line full/single-line/compact separators through glyph-aware helpers so ASCII packs stop leaking `│` / `·`; the remaining helper-routing follow-up is now toast severity icons, HUD mode glyphs, and audio-meter markers before introducing additional style-pack fields; post-slice cleanup landed: glyph tables/resolver helpers plus their focused tests extracted from `theme/mod.rs` into `theme/glyphs.rs`. 2026-03-09 Codex re-review confirmed the separator fix but keeps MP-174 open until the remaining helper-routing follow-up lands with focused proof.)
- [x] MP-175 Add a framework capability matrix + parity gate for shipped framework versions (Ratatui widget/symbol families and Crossterm color/input/render capabilities, including synchronized updates + keyboard enhancement flags), and track upgrade deltas before enabling new Studio controls (landed `theme/capability_matrix.rs` with `RatatuiWidget`/`RatatuiSymbolFamily`/`CrosstermCapability` enums, `FrameworkCapabilitySnapshot` pinned at ratatui 0.30 + crossterm 0.29, `check_parity()` gate detecting unregistered widgets and unmapped symbols, `compute_upgrade_delta()` for version transition tracking, `theme_capability_compatible()` for theme/terminal validation, and 18 passing tests covering snapshot parity, delta detection, and breaking-change gates; TS-G09 + TS-G15 evidence).
- [x] MP-176 Implement terminal texture/graphics capability track (`TextureProfile` + adapter policy): symbol-texture baseline for all terminals plus capability-gated Kitty/iTerm2 image paths with enforced fallback chain tests (landed `theme/texture_profile.rs` with `TextureTier` fallback chain (KittyGraphics > ITermInlineImage > Sixel > SymbolTexture > Plain), `SymbolTextureFamily` enum (shade/braille/block/line), `TextureProfile` with max/active tier + terminal detection, `TerminalId` enum covering Kitty/iTerm2/WezTerm/Foot/Mintty/VsCode/Cursor/JetBrains/Alacritty/Warp/Generic/Unknown, environment-based detection via TERM_PROGRAM/TERMINAL_EMULATOR/KITTY_WINDOW_ID/ITERM_SESSION_ID, `resolve_texture_tier()` enforcing fallback chain, and `texture_profile_with_override()` for style-pack tier overrides; 20 passing tests covering fallback ordering, tier resolution, terminal detection, and profile construction; TS-G09 + TS-G06 evidence).
- [x] MP-179 Add dependency baseline strategy for Theme Studio ecosystem packs (Ratatui/Crossterm version pin policy + compatibility matrix + staged upgrade plan) so third-party widget adoption does not fragment resolver/studio parity (landed `theme/dependency_baseline.rs` with `DependencyPin` structs for ratatui 0.30 and crossterm 0.29, `CompatibilityEntry`/`CompatibilityStatus` matrix covering tui-textarea/tui-tree-widget/throbber-widgets-tui/tui-popup/tui-scrollview/tui-big-text/tui-prompts/ratatui-image/tuirealm with per-dep ratatui+crossterm compat status, `UpgradeStep` staged plan (crossterm 0.30 before ratatui 0.31), `check_crate_compatibility()`/`check_pack_compatibility()` policy gates blocking unknown/incompatible crates, and `validate_pin_against_cargo()` for CI pin verification; 19 passing tests covering pin validation, matrix queries, compatibility semantics, and upgrade ordering; TS-G15 evidence).
- [x] MP-180 Pilot a curated widget-pack integration lane (`tui-widgets` family, `tui-textarea`, `tui-tree-widget`, `throbber-widgets-tui`) under style-ID/allowlist gates, with parity tests before feature flags graduate (landed `theme/widget_pack.rs` with `PackMaturity` lifecycle (Candidate > Pilot > Graduated > Retired), `WidgetPackEntry` registry with per-pack `StyleIdScope` namespaces and `ParityRequirement` gates, 6-entry `WIDGET_PACK_REGISTRY` (tui-textarea/tui-tree-widget/throbber-widgets-tui at Pilot; tui-popup/tui-scrollview/tui-big-text at Candidate), `GraduationCheckResult`-based gate blocking pilot packs with unmet parity requirements, `find_pack()`/`active_packs()`/`packs_at_maturity()` queries, `style_id_is_pack_owned()`/`owning_pack_for_style_id()` ownership resolution, and scope overlap detection; 21 passing tests covering registry integrity, scope isolation, maturity ordering, graduation gates, and ownership queries; TS-G15 + TS-G05 + TS-G06 evidence).
- [x] MP-182 Add `RuleProfile` no-code visual automation (threshold/context/state-driven style overrides) with deterministic priority semantics, preview tooling, and snapshot coverage (landed `theme/rule_profile.rs` with `RuleCondition` tagged-union supporting VoiceState/Threshold/Backend/Capability/ColorMode/All/Any conditions, `ThresholdMetric` enum (queue-depth/latency-ms/audio-level-db/terminal-width/terminal-height), `StyleOverride`/`OverrideEntry` for property-level style mutations, `StyleRule` with priority-based conflict resolution and enable/disable toggle, `RuleProfile` with add/remove/toggle operations and `active_rules()` priority-sorted accessor, `evaluate_condition()`/`evaluate_rules()` engine with deterministic first-match-per-key semantics, `preview_rules()` for Studio preview tooling, `parse_rule_profile()` JSON deserialization with nested condition support, and `RuleProfileError` for duplicate/not-found rule operations; 33 passing tests covering condition evaluation, priority semantics, conflict resolution, nested conditions, JSON parsing, and preview output; TS-G14 + TS-G05 + TS-G06 evidence).

## Phase 2E - Theme Studio Delivery (After Visual Surface Expansion)

- [x] MP-164 Implement dedicated `Theme Studio` overlay mode entry points/navigation and remove deep theme editing from generic Settings flows (landed `OverlayMode::ThemeStudio` with dedicated renderer/state selection, routed `Ctrl+Y`/theme-button entrypoints and cross-overlay theme hotkey flows into Theme Studio, added keyboard/mouse navigation (`Enter` action routing to Theme Picker/close plus arrow/ESC handling), wired periodic resize rerender + PTY reserved-row budgeting for Theme Studio mode, and covered interaction/status-row updates with new event-loop/theme-studio/status-line regression tests; TS-G07 evidence: `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `cd rust && cargo test --bin voiceterm`).
- [x] MP-165 Migrate legacy visual controls out of settings list (`SettingsItem::Theme`, `SettingsItem::HudStyle`, `SettingsItem::HudBorders`, `SettingsItem::HudPanel`, `SettingsItem::HudAnimate`) so Settings keeps non-theme runtime controls only (landed by removing those rows from `SETTINGS_ITEMS`, preserving quick visual controls via `Ctrl+Y`/`Ctrl+G` theme paths plus `Ctrl+U` HUD-style cycling outside Settings).
- [ ] MP-166 Deliver Studio page control parity for all `StylePack` fields (tokens, layout, widgets, motion, behavior, notifications, command/discovery surfaces, voice-state scenes, startup/wizard/progress/texture surfaces, accessibility, keybinds, profiles) with undo/redo + rollback (in progress: Theme Studio now includes interactive visual-control rows for existing runtime styling (`HUD style`, `HUD borders`, `Right panel`, `Panel animation`) plus live `StylePack` runtime overrides for `Glyph profile`, `Indicator set`, `Progress spinner`, `Progress bars`, `Theme borders`, `Voice scene`, `Toast position`, `Startup splash`, `Toast severity`, and `Banner style`, all adjustable with Enter and Left/Right controls and live current-value labels; overlay rendering now uses settings-style `label + [ value ]` rows with selected-row highlighting, a dedicated `tip:` description row, wider studio-width clamps (`60..=82`), and footer hints that expose left/right adjustment controls; runtime style-pack override edit safety is now wired with dedicated `Undo edit`, `Redo edit`, and `Rollback edits` rows backed by bounded in-session history; Theme Studio input dispatch now routes through page-scoped helper handlers with shared global-key processing and focused runtime-style adjustment routing in `theme_studio_input.rs`, and home-page row rendering now uses structured row metadata with static tip ownership; 2026-03-09 bounded Components-page slice landed: `components_page.rs` now drills down `group -> component -> state` over canonical `style_id` rows, cycles local preview property edits through `StyleResolver`-owned `ResolvedComponentStyle`, and stays scoped away from `theme_studio_input.rs` / `component_registry.rs`; deep multi-page style-pack parity (`tokens`, `layout/motion`, broader field mapping), live reachability/persistence wiring, and `dead_code` allowance removal remain pending; 2026-03-07 aligned next slice: Components page work must edit `ResolvedComponentStyle` keyed by `(style_id, state)` and must not introduce per-component `ThemeColors` maps).
- [ ] MP-167 Run Theme Studio GA validation and docs lockstep updates (snapshot matrix, terminal compatibility matrix, architecture docs, user docs, troubleshooting guidance, changelog entry).
- [ ] MP-173 Add CI policy gates for future visuals: fail if a new renderable component lacks style-ID registration, and fail if post-parity a style-pack field lacks Studio control mapping (in progress: framework capability parity now fails on any newly added Ratatui widget/symbol without registration/mapping coverage, component-registry tests now require exact inventory parity plus unique stable style IDs, and Theme Studio now enforces explicit style-pack field classification (`mapped` vs `deferred`) with the post-parity gate enabled (`STYLE_PACK_STUDIO_PARITY_COMPLETE = true`) so mapping tests now require zero deferred style-pack fields; 2026-03-07 aligned next slice: registry-backed CI gates must count live renderable components only after the MP-172 live/planned boundary is explicit).
- [ ] MP-177 Add widget-pack extensibility parity (first-party plus allowlisted third-party widgets) so newly adopted widget families must register style IDs + resolver bindings + Studio controls before GA.
- [ ] MP-178 Add Theme Studio element inspector parity so users can select any rendered element and jump directly to component/state style controls (with state preview and style-path tracing).
- [ ] MP-181 Add advanced Studio interaction parity (resizable splits, drag/reorder, scrollview-heavy forms, large text/editor fields) with full keyboard fallback and capability-safe mouse behavior.

## Phase 3 - Overlay Differentiators

- [x] MP-090 Voice terminal navigation actions (scroll/copy/error/explain).
- [x] MP-140 Define and enforce macro-vs-navigation precedence (macros first, explicit built-in phrase escape path).
- [x] MP-141 Add Linux clipboard fallback support for voice `copy last error` (wl-copy/xclip/xsel).
- [x] MP-142 Add `devctl docs-check` commit-range mode for post-commit doc audits on clean working trees.
- [x] MP-156 Add release-notes automation (`generate-release-notes.sh`, `devctl release-notes`, `release.sh` notes-file handoff) so each tag has consistent diff-derived markdown notes for GitHub releases.
- [x] MP-144 Add macro-pack onboarding wizard hardening (expanded developer command packs, repo-aware placeholder templating, and optional post-install setup prompt).
- [x] MP-143 Decompose `voice_control/drain.rs` and `event_loop.rs` into smaller modules to reduce review and regression risk (adjacent runtime architecture debt; tracked separately from tooling-control-plane work).
  - [x] MP-143a Extract shared settings-item action dispatch in `event_loop.rs` so Enter/Left/Right settings paths stop duplicating mutation logic.
  - [x] MP-143b Split `event_loop.rs` overlay/input/output handlers into focused modules (`overlay_dispatch`, `input_dispatch`, `output_dispatch`, `periodic_tasks`) and move tests to `event_loop/tests.rs` while preserving regression coverage.
  - [x] MP-143c0 Move `voice_control/drain.rs` tests into `voice_control/drain/tests.rs` so runtime decomposition can land in smaller, reviewable slices.
  - [x] MP-143c1 Extract `voice_control/drain/message_processing.rs` for macro expansion, status message handling, and latency/preview helpers.
  - [x] MP-143c Split `voice_control/drain.rs` into transcript-delivery (`transcript_delivery.rs`), status/latency updates (`message_processing.rs`), and auto-rearm/finalize components (`auto_rearm.rs`) with unchanged behavior coverage.
- [x] MP-182 Decompose `ipc/session.rs` by extracting non-blocking codex/claude/voice/auth event processors into `ipc/session/event_processing/`, keeping command-loop orchestration in `session.rs` and preserving IPC regression coverage.
- [x] MP-170 Harden IPC test event capture isolation so parallel test runs remain deterministic under `cargo test` and `devctl check --profile ci`.
- [x] MP-091 Searchable transcript history and replay workflow (landed `Ctrl+H` overlay with bounded history storage, type-to-filter search, and replay-to-PTY integration plus event-loop/help wiring).
- [x] MP-229 Upgrade transcript-history from transcript-only snippets to source-aware conversation memory capture (`mic`/`you`/`ai`) with wider rows, selected-entry preview, control-sequence-safe search input (`\x1b[0[I`/focus noise no longer leaks into query text), non-replayable guardrails for assistant-output rows, and opt-in markdown session memory logging (`--session-memory`, `--session-memory-path`) for project-local conversation archives.
- [x] MP-199 Add wake-word runtime controls in settings/config (`OFF`/`ON`, sensitivity, cooldown), defaulting to `OFF` for release safety (landed overlay config flags `--wake-word`, `--wake-word-sensitivity`, `--wake-word-cooldown-ms`; settings overlay items + action handlers for wake toggle/sensitivity/cooldown; regression coverage in `settings_handlers::tests`).
- [x] MP-200 Add low-power always-listening wake detector runtime with explicit start/stop ownership and bounded shutdown/join semantics (landed `wake_word` runtime owner with local detector thread lifecycle, settings-driven start/stop reconciliation, bounded join timeout on shutdown, and periodic capture-active pause sync to avoid recorder contention).
- [x] MP-201 Route wake detections through the existing `Ctrl+R` capture path so wake-word and manual recording share one recording/transcription pipeline (landed shared trigger handling in `event_loop/input_dispatch.rs` so wake detections and manual `Ctrl+R` use the same start-capture path; wake detections ignore active-recording stop toggles by design).
- [x] MP-202 Add debounce and false-positive guardrails plus explicit HUD privacy indicator while wake-listening is active (landed explicit Full-HUD wake privacy badge states `Wake: ON`/`Wake: PAUSED`, plus stricter short-utterance wake phrase gating so long/background mentions are ignored before trigger delivery).
- [x] MP-203 Add wake-word regression + soak validation gates (unit/integration/lifecycle tests and long-run false-positive/latency checks) and require passing evidence before release/tag (landed deterministic wake runtime lifecycle tests via spawn-hooked listener ownership checks, expanded detection-path regression tests, long-run hotword false-positive/latency soak test, reusable guard script `dev/scripts/tests/wake_word_guard.sh`, `devctl check --profile release` wake-guard integration, and dedicated CI lane `.github/workflows/wake_word_guard.yml`).
- [x] MP-286 Add an image-capture interaction mode for Codex sessions: expose a persistent ON/OFF mode, show a concise HUD indicator, support click/hotkey capture triggers, and inject a capture prompt with saved image path into the active PTY so users can run picture-assisted chats without leaving VoiceTerm (landed `image_mode.rs` capture pipeline with platform-default command fallback + configurable `--image-capture-command`, added persistent `--image-mode` runtime toggle in CLI/settings/config, added `IMG` status badge, and routed manual trigger paths (`Ctrl+R` + rec button) to image capture only when image mode is enabled while preserving normal voice-record behavior when disabled; capture injects `Please analyze this image file: <path>` into active PTY respecting send mode (`auto` send with newline vs `insert` staged text); docs/changelog/help/flags updated in `README.md`, `QUICK_START.md`, `guides/USAGE.md`, `guides/CLI_FLAGS.md`, `dev/CHANGELOG.md`; verification evidence: `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `cd rust && cargo test --bin voiceterm`).
- [x] MP-287 Resume a scoped slice of deferred Dev Mode behind a guarded launch flag: add `--dev` activation (with `--dev-mode`/`-D` aliases), keep default runtime behavior unchanged when absent, and surface explicit in-session mode visibility for dev-only experimentation (landed guarded CLI gate `--dev` with aliases in `config/cli.rs`, wired runtime state to `StatusLineState`, and added a `DEV` Full-HUD badge path so guarded mode is explicit only when enabled; default launch behavior remains unchanged when flag is absent; docs/changelog/help groups updated in `README.md`, `QUICK_START.md`, `guides/USAGE.md`, `guides/CLI_FLAGS.md`, `dev/CHANGELOG.md`, and `custom_help.rs`; verification evidence: `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `cd rust && cargo test --bin voiceterm`).
- [x] MP-288 Start deferred Dev Mode foundation by introducing a shared `rust/src/devtools/` core (stable event schema + bounded in-memory session aggregator) and wiring guarded `--dev` runtime capture events into that shared model without changing non-dev runtime behavior (landed new shared `voiceterm::devtools` module with schema-versioned `DevEvent` model + bounded `DevModeStats` ring buffer/session snapshot aggregation in `rust/src/devtools/events.rs` and `rust/src/devtools/state.rs`, exported via `rust/src/devtools/mod.rs` and `rust/src/lib.rs`; runtime bridge now instantiates guarded in-memory dev stats only when `--dev` is enabled (`main.rs`) and records transcript/empty/error voice-job events from the existing drain path without affecting default mode (`event_state.rs`, `event_loop.rs`, `voice_control/drain.rs`); verification evidence: `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `cd rust && cargo test --bin voiceterm`).
- [x] MP-289 Add guarded Dev Mode logging controls and on-disk event persistence: introduce `--dev-log` + `--dev-path`, enforce `--dev` guardrails, and append captured dev events to session JSONL files under the configured dev path without changing non-dev behavior (landed guarded CLI flags `--dev-log` and `--dev-path` in `config/cli.rs` with startup validation gates in `main.rs` (`--dev-log`/`--dev-path` now require `--dev`, and `--dev-path` requires `--dev-log`), added shared dev-event JSONL persistence in `rust/src/devtools/storage.rs` (`DevEventJsonlWriter`, per-session `session-*.jsonl` files under `<dev-root>/sessions/`, default dev root `$HOME/.voiceterm/dev` with `<cwd>/.voiceterm/dev` fallback), and wired runtime logging through the existing guarded voice-drain path so captured dev events append on transcript/empty/error messages only when guarded logging is enabled (`event_state.rs`, `event_loop.rs`, `voice_control/drain.rs`); default non-dev runtime behavior remains unchanged; docs/help/changelog updated in `guides/CLI_FLAGS.md`, `guides/USAGE.md`, `README.md`, `QUICK_START.md`, `custom_help.rs`, and `dev/CHANGELOG.md`; verification evidence: `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `cd rust && cargo test --bin voiceterm`).
- [x] MP-290 Extend Dev CLI reporting with guarded Dev Mode session telemetry summaries: add optional `--dev-logs` support to `devctl status`/`devctl report` (plus `--dev-root` and `--dev-sessions-limit`) so maintainers can inspect recent `session-*.jsonl` event counts/latency/error summaries without opening raw files (landed `collect_dev_log_summary()` in `dev/scripts/devctl/collect.py`, wired CLI flags in `dev/scripts/devctl/cli.py`, rendered markdown/json summary blocks in `dev/scripts/devctl/commands/status.py` and `dev/scripts/devctl/commands/report.py`, and added regression coverage in `dev/scripts/devctl/tests/test_collect_dev_logs.py`, `dev/scripts/devctl/tests/test_status.py`, and `dev/scripts/devctl/tests/test_report.py`; verification evidence: `python3 -m unittest dev.scripts.devctl.tests.test_collect_dev_logs dev.scripts.devctl.tests.test_status dev.scripts.devctl.tests.test_report`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`).
- [x] MP-291 Add a guarded `Ctrl+D` Dev panel overlay for `--dev` sessions: landed new `dev_panel.rs` formatter/render contract (read-only guard/logging/session-counter view), added `InputEvent::DevPanelToggle` parsing for raw `Ctrl+D` (`0x04`) and CSI-u `Ctrl+D`, wired guarded toggle behavior (`--dev` opens/closes panel; non-dev forwards `Ctrl+D` EOF byte to PTY so legacy behavior is preserved), introduced `OverlayMode::DevPanel` rendering/open/close/resize/mouse/reserved-row handling (`event_loop.rs`, `overlay_dispatch.rs`, `periodic_tasks.rs`, `overlay_mouse.rs`, `terminal.rs`, `overlays.rs`), and updated shortcut/help docs (`help.rs`, `guides/USAGE.md`, `guides/CLI_FLAGS.md`, `README.md`, `QUICK_START.md`, `dev/CHANGELOG.md`); verification evidence: `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `cd rust && cargo check --bin voiceterm`, `cd rust && cargo test --bin voiceterm`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [x] MP-295 Harden prompt-occlusion guardrails for Codex/Claude reply boxes: extend `prompt/claude_prompt_detect.rs` detection beyond approval-only patterns to include reply/composer prompt markers (including Unicode prompt glyphs and Codex command-composer hint text), enable the guard for both Codex and Claude backend labels during startup (`main.rs`), preserve zero-row HUD suppression + PTY row-budget restore behavior when suppression toggles (`prompt/mod.rs`, `event_loop` suppression path), and keep reply/composer suppression active while users type (clear only on submit/cancel input instead of every typed byte); docs/changelog updated in `guides/TROUBLESHOOTING.md`, `dev/ARCHITECTURE.md`, and `dev/CHANGELOG.md`; verification evidence: `cd rust && cargo test claude_prompt_detect --bin voiceterm`, `cd rust && cargo test reply_composer_ --bin voiceterm`, `cd rust && cargo test set_claude_prompt_suppression_updates_pty_row_budget --bin voiceterm`, `cd rust && cargo test periodic_tasks_clear_stale_prompt_suppression_without_new_output --bin voiceterm`, `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [ ] MP-301 Investigate intermittent wake/send reliability for real-world speech variants (for example `hate codex`, `hate cloud`, and while-speaking submit attempts) using targeted matcher tests plus transcript-level debug evidence.
  - [x] Initial slice: expand wake alias/send-intent coverage (`hate`/`pay` -> `hey`, `cloud`/`clog` -> `claude`, plus `send it` / `sending` / `sand`) and emit wake transcript decision traces in debug logs (`voiceterm --logs --log-content`).
  - [x] Reliability slice (2026-02-27): align wake-listener VAD threshold to live mic-sensitivity baseline (plus wake headroom) so wake detection tracks the same voice setup users already tuned for normal capture; also relaxed short wake-capture bounds (`min speech`, `lookback`, `silence tail`) and expanded `claude` alias normalization (`claud`, `clawed`) for lower-effort phrase pickup without shouting.
  - [ ] Follow-up slice: collect reproducible field log samples and tune mid-utterance submit heuristics without increasing false positives from background conversation.

## Phase 3B - Tooling Control Plane Consolidation

- [x] MP-157 Execute tooling-control-plane consolidation (archived at `dev/archive/2026-02-17-tooling-control-plane-consolidation.md`): implement `devctl ship`, deterministic step exits, dry-run behavior, machine-readable step reports, and adapter conversion for release entry points.
- [x] MP-158 Harden `devctl docs-check` policy enforcement so docs requirements are change-class aware and deprecated maintainer command references are surfaced as actionable failures.
- [x] MP-159 Add a dedicated tooling CI quality lane for `devctl` command behavior and maintainer shell-script integrity (release, release-notes, PyPI, Homebrew helpers).
- [x] MP-160 Canonicalize maintainer docs and macro/help surfaces to `devctl` first (`AGENTS.md`, `dev/DEVELOPMENT.md`, `dev/scripts/README.md`, maintainer macro packs, and `Makefile` help), keeping legacy wrappers documented as transitional adapters.
- [x] MP-302 Expand docs-governance control plane and process traceability: enforce strict tooling docs checks plus conditional strict user-facing docs checks in CI, add markdown/image/CLI-flag integrity guards, block accidental root `--*` artifact files, and document handoff/source-of-truth workflow for both human and AI contributors.
- [x] MP-239 Reorganize `AGENTS.md` into an agent-first execution router (task classes, context packs, normal-push vs release workflows, branch sync policy, command bundles, and explicit autonomy/guardrail rules) so AI contributors can deterministically choose the right docs, tools, and checks for each task.
- [x] MP-245 Refine `AGENTS.md` and `dev/DEVELOPMENT.md` into an index-first, user-story-driven execution system: add explicit start-up bootstrap steps, dirty-tree protocol, single-source command bundles, CI lane mapping by risk/path, release version-parity checks (`Cargo.toml` + `pyproject.toml` + macOS `Info.plist` + changelog) with a dedicated parity guard (`dev/scripts/checks/check_release_version_parity.py`), add an AGENTS-structure guard (`dev/scripts/checks/check_agents_contract.py`), and add an active-plan registry/sync guard (`dev/scripts/checks/check_active_plan_sync.py` + `dev/active/INDEX.md`) so SOP/router/bundle and active-doc discovery contracts fail early in local/CI governance checks.
- [x] MP-256 Add an orphaned-test process guardrail to tooling governance by extending `devctl hygiene` to detect leaked `target/debug/deps/voiceterm-*` binaries (error on detached `PPID=1` candidates, warning on active runs), then harden `devctl check` with automatic pre/post orphaned-test cleanup sweeps so interrupted local runs do not accumulate stale test binaries across worktrees.
- [x] MP-258 Automate PyPI publish in release flow by adding `.github/workflows/publish_pypi.yml` (triggered on `release: published`) and aligning maintainer docs so release runs publish through GitHub Actions while `devctl pypi --upload --yes` remains an explicit fallback path.
- [x] MP-259 Automate Codecov coverage uploads by adding `.github/workflows/coverage.yml` (Rust `cargo llvm-cov` LCOV generation + Codecov OIDC upload) and aligning maintainer docs/lane mapping so the README coverage badge is backed by current CI reports instead of `unknown`.
- [x] MP-260 Add non-regressive source-shape guardrails for Rust/Python so oversized files cannot silently drift into new God-file debt: add `dev/scripts/checks/check_code_shape.py` (working-tree + commit-range modes with soft/hard file-size limits and oversize-growth budgets), wire it into `tooling_control_plane.yml`, and add bundle/docs coverage for local maintainer runs.
- [x] MP-261 Refresh README brand banner with a new VoiceTerm hero logo asset (`img/logo-hero.png`) based on the finalized artwork while keeping subtitle/icon identity and removing redundant platform chips from the banner artwork itself (README remains the only consumer; generation script exploration was one-off and not retained in repo tooling).
- [x] MP-282 Consolidate visual planning docs by folding `dev/active/overlay.md` and `dev/active/theme_studio_redesign.md` into `dev/active/theme_upgrade.md`, then update active-index/sync-governance references so one canonical visual spec remains.
- [x] MP-283 Harden release distribution automation by adding a CI release preflight lane (`release_preflight.yml`), a Homebrew publish workflow path (`publish_homebrew.yml`), and safety guards for Homebrew tarball/SHA validation plus `devctl ship` release-version parity enforcement before CI/local publish steps.
- [x] MP-284 Reconcile ADR inventory to runtime truth: remove stale unimplemented proposal ADRs, promote architecture ADRs that match shipped behavior (overlay mode, runtime config precedence, session history boundaries, writer render invariants), and add missing ADR coverage for wake-word ownership, voice-macro precedence, and Claude prompt-safe HUD suppression.
- [x] MP-292 Refactor `devctl` internals to reduce module size, remove command-output drift, and harden missing-binary behavior: extracted shared process-sweep helpers (`dev/scripts/devctl/process_sweep.py`) for `check`/`hygiene`, shared `check` profile normalization (`dev/scripts/devctl/commands/check_profile.py`), shared status/report payload+markdown rendering (`dev/scripts/devctl/status_report.py`), split ship orchestration from step/runtime helpers (`dev/scripts/devctl/commands/ship.py`, `dev/scripts/devctl/commands/ship_common.py`, `dev/scripts/devctl/commands/ship_steps.py`), extracted hygiene audit helpers (`dev/scripts/devctl/commands/hygiene_audits.py`), updated `run_cmd`/ship command checks to return structured failures instead of uncaught Python exceptions when required binaries are missing, and rewrote helper/module docstrings in plain language so junior developers and AI agents can quickly understand when/why each helper exists; verification evidence: `python3 -m unittest discover -s dev/scripts/devctl/tests -p 'test_*.py'`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_agents_contract.py`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_release_version_parity.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [x] MP-293 Add a dedicated `devctl security` command so maintainers can run a local security gate aligned with CI policy: landed `dev/scripts/devctl/commands/security.py` (RustSec JSON capture + policy enforcement + optional `zizmor` workflow scan with `--require-optional-tools` strict mode), extracted security CLI parser wiring into `dev/scripts/devctl/security_parser.py` to keep `dev/scripts/devctl/cli.py` below code-shape growth limits, wired list output in `dev/scripts/devctl/commands/listing.py`, added regression coverage in `dev/scripts/devctl/tests/test_security.py`, expanded plain-language process-sweep context for interrupted/stalled test cleanup in `dev/scripts/devctl/process_sweep.py`, and updated maintainer/governance docs (`AGENTS.md`, `dev/DEVELOPMENT.md`, `dev/scripts/README.md`, `dev/history/ENGINEERING_EVOLUTION.md`); verification evidence: `python3 -m unittest discover -s dev/scripts/devctl/tests -p 'test_*.py'`, `python3 dev/scripts/devctl.py security --dry-run --with-zizmor --require-optional-tools --format json`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_agents_contract.py`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_release_version_parity.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [x] MP-294 Consolidate engineering narrative docs into a single canonical history source by folding `dev/docs/TECHNICAL_SHOWCASE.md` and `dev/docs/LINKEDIN_POST.md` into appendices in `dev/history/ENGINEERING_EVOLUTION.md`, then retiring the duplicated `dev/docs/` source files so updates only target one document; verification evidence: `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [x] MP-297 Execute a focused `devctl check` usability/performance hardening sequence from maintainer review findings in ordered slices:
  - [x] `#5` failure-output diagnostics: `run_cmd` now streams subprocess output while preserving bounded failure excerpts for non-zero exits (`dev/scripts/devctl/common.py`), `check` prints explicit failed-step summaries with captured context (`dev/scripts/devctl/commands/check.py`), markdown reports include a dedicated failure-output section (`dev/scripts/devctl/steps.py`), and regression coverage/docs were updated (`dev/scripts/devctl/tests/test_common.py`, `dev/scripts/README.md`, `dev/history/ENGINEERING_EVOLUTION.md`); verification evidence: `python3 -m unittest discover -s dev/scripts/devctl/tests -p 'test_*.py'`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_agents_contract.py`, `python3 dev/scripts/checks/check_release_version_parity.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
  - [x] `#1` check-step parallelism: `devctl check` now runs independent setup gates (`fmt`, `clippy`, AI guard scripts) and the test/build phase through deterministic parallel batches with stable report ordering (`dev/scripts/devctl/commands/check.py`), includes maintainer controls for sequential fallback and worker tuning (`--no-parallel`, `--parallel-workers` in `dev/scripts/devctl/cli.py`), and adds regression coverage for parser wiring, parallel-path selection, and ordered aggregation (`dev/scripts/devctl/tests/test_check.py`); verification evidence: `python3 -m unittest dev.scripts.devctl.tests.test_check`.
  - [x] `#7` profile-vs-flag conflict validation: extracted `validate_profile_flag_conflicts()` into `check_profile.py` with `PROFILE_PRESETS` single source of truth, added 12 regression tests in `test_check.py`.
  - [x] `#4` explicit progress feedback: extracted `count_quality_steps()` and `emit_progress()` into `check_progress.py` with serial `[N/M]` and parallel `[N-M/T]` formats, added 10 regression tests in `test_check.py`.
  - [x] `#2` runaway-process containment: `run_cmd` now starts child steps in isolated process groups and tears down the full subprocess tree on interrupt (`dev/scripts/devctl/common.py`), while process sweep now treats stale active `voiceterm-*` test runners as cleanup/error candidates in both `check` and `hygiene` (`dev/scripts/devctl/process_sweep.py`, `dev/scripts/devctl/commands/check.py`, `dev/scripts/devctl/commands/hygiene.py`); regression coverage added in `dev/scripts/devctl/tests/test_common.py`, `dev/scripts/devctl/tests/test_process_sweep.py`, `dev/scripts/devctl/tests/test_check.py`, and `dev/scripts/devctl/tests/test_hygiene.py`.
  - [x] `#8` ADR-reference + governance parity guard: `devctl hygiene` now flags stale ADR reference patterns (hard-coded ADR counts and wildcard ADR file ranges), validates ADR backlog parity between `MASTER_PLAN` and `autonomous_control_plane`, and enforces reserved-ID coverage for missing backlog ADR files, with regression coverage in `dev/scripts/devctl/tests/test_hygiene.py`; docs were normalized to index-based ADR references in `dev/active/theme_upgrade.md` and `dev/history/ENGINEERING_EVOLUTION.md`, and release/tooling workflows now run workflow-shell + IDE/provider isolation + compat-matrix schema/smoke + naming consistency checks in their governance bundles.
  - [x] `#9` external publication drift governance: landed the tracked
    publication registry (`dev/config/publication_sync_registry.json`),
    `devctl publication-sync` report/record flow
    (`dev/scripts/devctl/publication_sync.py`,
    `dev/scripts/devctl/publication_sync_parser.py`,
    `dev/scripts/devctl/commands/publication_sync.py`), hygiene warnings via
    `dev/scripts/devctl/commands/hygiene.py` +
    `dev/scripts/devctl/commands/hygiene_audits.py`, the explicit guard
    `dev/scripts/checks/check_publication_sync.py`, release-preflight wiring,
    and regression coverage in
    `dev/scripts/devctl/tests/test_publication_sync.py` plus
    `dev/scripts/devctl/tests/test_check_publication_sync.py`; verification
    evidence: `python3 -m unittest dev.scripts.devctl.tests.test_publication_sync dev.scripts.devctl.tests.test_check_publication_sync`,
    `python3 dev/scripts/devctl.py publication-sync --format json`,
    `python3 dev/scripts/checks/check_publication_sync.py --report-only`.
- [x] MP-298 Parallelize independent `devctl status`/`report` collection probes and `ship --verify` subchecks with deterministic aggregation so I/O-heavy control-plane workflows run faster without changing pass/fail policy semantics.
  - [x] 2026-03-09 Rust-audit reporting slice: `devctl report` now has an optional
    parallel-collected `--rust-audits` probe that aggregates the Rust
    best-practices, lint-debt, and runtime-panic guards into one human-readable
    Markdown section with risk/fix explanations, optional matplotlib charts via
    `--with-charts`, deterministic report bundle emission (`--emit-bundle`),
    and shared full-tree support after adding `--absolute` mode to
    `check_rust_runtime_panic_policy.py`; targeted regression coverage added in
    `test_report.py`, `test_status_report_parallel.py`,
    `test_rust_audit_report.py`, and
    `test_check_rust_runtime_panic_policy.py`.
  - [x] 2026-03-09 `ship --verify` closure slice: independent verify subchecks
    now run through deterministic parallel aggregation in
    `dev/scripts/devctl/commands/ship_steps.py`, using quiet worker execution
    plus ordered failure selection so the first failing declared substep still
    determines the verify result even when workers complete out of order;
    regression coverage added in `dev/scripts/devctl/tests/test_ship.py` and
    `dev/scripts/devctl/tests/test_common.py`, with local proof via
    `python3 -m unittest dev.scripts.devctl.tests.test_common dev.scripts.devctl.tests.test_ship`
    and `python3 dev/scripts/devctl.py ship --version 1.1.1 --verify --dry-run --format json`.
- [x] MP-299 Add a `devctl triage` workflow that emits both human-readable markdown and AI-friendly JSON, with optional CIHub ingestion: landed new command surface (`dev/scripts/devctl/commands/triage.py`) plus parser/command inventory wiring (`dev/scripts/devctl/cli.py`, `dev/scripts/devctl/commands/listing.py`), optional `cihub triage` execution + artifact ingestion (`triage.json`, `priority.json`, `triage.md`) under configurable emit directories, and bundle emission mode (`--emit-bundle` writes `<prefix>.md` + `<prefix>.ai.json`) for project handoff/automation use; regression coverage/docs updated in `dev/scripts/devctl/tests/test_triage.py` and `dev/scripts/README.md`; verification evidence: `python3 -m unittest discover -s dev/scripts/devctl/tests -p 'test_*.py'`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_agents_contract.py`, `python3 dev/scripts/checks/check_release_version_parity.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [x] MP-300 Deepen `devctl triage` CIHub integration with actionable routing data: map `cihub` artifact records (`priority.json`, `triage.json`) into normalized issues (`category`, `severity`, `owner`, `summary`) via shared enrichment helpers (`dev/scripts/devctl/triage_enrich.py`), add configurable category-owner overrides (`--owner-map-file`) in parser wiring (`dev/scripts/devctl/triage_parser.py`), include rollup counts by severity/category/owner in report payload + markdown output (`dev/scripts/devctl/triage_support.py`), and extend regression coverage for severity/owner routing + owner-map overrides (`dev/scripts/devctl/tests/test_triage.py`) with docs updates in `dev/scripts/README.md`; verification evidence: `python3 -m unittest discover -s dev/scripts/devctl/tests -p 'test_*.py'`, `python3 dev/scripts/devctl.py triage --format md --no-cihub --emit-bundle --bundle-dir /tmp --bundle-prefix vt-triage-smoke --output /tmp/vt-triage-smoke.md`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_agents_contract.py`, `python3 dev/scripts/checks/check_release_version_parity.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [x] MP-306 Add proactive report-retention governance to the `devctl` control plane: landed `devctl reports-cleanup` with retention safeguards (`--max-age-days`, `--keep-recent`, protected-path exclusions, dry-run preview, confirmation/`--yes` delete path), wired `hygiene` to always surface stale report-growth warnings with direct cleanup guidance, and added parser/command/hygiene regression coverage plus maintainer docs updates (`dev/scripts/README.md`, `dev/DEVCTL_AUTOGUIDE.md`).
- [x] MP-339 Migrate repository Rust workspace path from `src/` to `rust/` and update runtime/tooling/CI/docs path contracts in one governed pass (`dev/archive/2026-03-07-rust-workspace-layout-migration.md`), preserving behavior while removing the `src/src` naming pattern (landed filesystem rename + path-contract rewrites across scripts/checks/workflows/docs; follow-up guard hardening landed rename-aware baseline mapping for Rust debt/security checks, active-root discovery + fail-fast behavior for `check_rust_audit_patterns.py`, and an explicit non-regressive `mem::forget` policy in `check_rust_best_practices.py`; sync/tooling gates and Rust build smoke from `rust/` succeeded).
- [x] MP-303 Add automated release-metadata preparation to the `devctl` control plane so maintainers can run one command path before verify/tag: added `--prepare-release` support on `devctl ship`/`devctl release` (`dev/scripts/devctl/cli.py`, `dev/scripts/devctl/commands/release.py`, `dev/scripts/devctl/commands/ship.py`), implemented canonical metadata updaters for Cargo/PyPI/macOS app plist plus changelog heading rollover under `dev/scripts/devctl/commands/release_prep.py` and `ship_steps.py`, and covered step wiring + idempotent prep behavior in `dev/scripts/devctl/tests/test_ship.py` and `dev/scripts/devctl/tests/test_release_prep.py`; docs/governance updates in `AGENTS.md`, `dev/DEVELOPMENT.md`, `dev/scripts/README.md`, and `dev/history/ENGINEERING_EVOLUTION.md`; verification evidence: `python3 -m unittest dev.scripts.devctl.tests.test_ship dev.scripts.devctl.tests.test_release_prep`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_agents_contract.py`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_release_version_parity.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [ ] MP-257 Run a plain-language readability pass across primary `dev/` entry docs (`dev/README.md`, `dev/DEVELOPMENT.md`, `dev/ARCHITECTURE.md`) so new developers can follow workflows quickly without losing technical accuracy.
  - [x] 2026-02-25 workflow readability slice: added `.github/workflows/README.md` with plain-language explanations for all workflow lanes (what runs, when it runs, and local reproduce commands) and added short purpose headers to every `.github/workflows/*.yml` file so intent is visible without opening full YAML bodies.
  - [x] 2026-02-25 core-dev-doc readability slice: simplified workflow/process language in `dev/README.md`, `dev/DEVELOPMENT.md`, and `dev/ARCHITECTURE.md` so operators can scan what to run and why without policy-heavy wording.
  - [x] 2026-02-25 user-guide readability slice: simplified wording across `guides/README.md`, `guides/INSTALL.md`, `guides/USAGE.md`, `guides/CLI_FLAGS.md`, `guides/TROUBLESHOOTING.md`, and `guides/WHISPER.md` while preserving command/flag behavior and technical accuracy.
  - [x] 2026-02-25 root-entry readability slice: simplified wording in `README.md`, `QUICK_START.md`, and `DEV_INDEX.md` so first-time users and maintainers can scan setup/docs links quickly without changing any commands, flags, or workflow behavior.
  - [x] 2026-02-25 follow-up dev-entry readability slice: refined plain-language wording in `dev/README.md`, `dev/DEVELOPMENT.md`, and `dev/ARCHITECTURE.md`, and replaced the outdated `src/src` tree in `dev/DEVELOPMENT.md` with the current `rust/` layout summary so docs are both easier to scan and accurate.

## Phase 3C - Codebase Best-Practice Consolidation (Active Audit Track)

- [x] MP-184 Publish a dedicated execution record for full-repo Rust best-practice cleanup and keep task-level progress scoped to that audit track.
- [x] MP-185 Decompose settings action handling for lower coupling and clearer ownership (`settings_handlers` runtime/test separation, enum-cycle consolidation, constructor removal, status-helper extraction, and `SettingsActionContext` sub-context split landed; adjacent `ButtonActionContext::new` constructor removal also landed for consistent context wiring).
- [x] MP-186 Consolidate status-line rendering/button logic (`status_line/buttons.rs` and `status_line/format.rs`) to remove duplicated style/layout decisions and isolate legacy compatibility paths (landed: shared button highlight + queue/ready/latency badge helpers; legacy row helpers are `#[cfg(test)]`-gated with shared framing/separator helpers and reduced dead-code surface; tests split into `status_line/buttons/tests.rs` and `status_line/format/tests.rs`).
- [x] MP-187 Consolidate PTY lifecycle internals into canonical spawn/shutdown helpers and harden session-guard identity/cleanup throttling to reduce stale-process risk without blocking concurrent sessions (landed shared PTY lifecycle helpers in `pty_session/pty.rs`, plus session-lease start-time identity validation and atomic cleanup cadence throttling in `pty_session/session_guard.rs`; additional detached-orphan sweep fallback now reaps stale backend CLIs with `PPID=1` when they are not lease-owned and no longer share a TTY with a live shell, with deterministic unit coverage for elapsed-time parsing and candidate filtering).
- [x] MP-188 Decompose backend orchestration hotspots (`codex/pty_backend.rs`, `ipc/session.rs`) into narrower modules with explicit policy boundaries and lower test/runtime coupling (completed in v1.0.80: landed `codex/pty_backend/{output_sanitize,session_call,job_flow,test_support}.rs` plus `ipc/session/{stdin_reader,claude_job,auth_flow,loop_control,state,event_sink,test_support}.rs`, keeping parent orchestrators focused on runtime control flow).
- [x] MP-189 Add a focused maintainer lint-hardening lane (strict clippy profile + targeted allowlist) and burn down high-value warnings (`must_use`, error docs, redundant clones/closures, risky casts, dead-code drift) (completed in v1.0.80: landed `devctl check --profile maintainer-lint` + `.github/workflows/lint_hardening.yml`, burned down targeted warnings, added Linux ALSA dependency setup for the lane, and documented intentional deferral of precision/truncation DSP cast families).
- [x] MP-191 Fix Homebrew `opt` launcher path detection in `scripts/start.sh` + `scripts/setup.sh` so upgrades reuse persistent user model storage (`~/.local/share/voiceterm/models`) instead of redownloading into versioned Cellar `libexec/whisper_models`.
- [x] MP-192 Fix Full HUD ribbon baseline rendering by padding short waveform history at floor level (`-60 dB`) so right-panel visuals ramp upward instead of drawing a full-height block.
- [x] MP-193 Restore insert-mode early-send behavior for `Ctrl+E` while recording so noisy-room captures can stop early and submit immediately (one-shot force-send path + regression tests + docs alignment).
- [x] MP-197 Make hidden-HUD idle launcher visuals intentionally subdued (dull/muted text and `[open]`) so hidden mode remains non-intrusive.
- [x] MP-198 Align insert-mode `Ctrl+E` dispatch semantics (send staged text, finalize+submit while recording, consume idle/no-staged input) and apply the same muted hidden-launcher gray to hidden recording output.
- [x] MP-204 Refine hidden-HUD idle launcher controls for lower visual noise and better explicitness (remove inline `Ctrl+U` hint from hidden launcher text, add muted `[hide]` control next to `[open]`, support collapsing hidden launcher chrome to `[open]` only, and make `open` two-step from collapsed mode: restore launcher first, then switch HUD style on the next open).
- [x] MP-205 Harden discoverability + feedback ergonomics (expand startup hints for `?`/settings/mouse discoverability, add grouped help overlay sections, and surface explicit idle `Ctrl+E` feedback with `Nothing to send`).
- [x] MP-206 Add first-run onboarding hint persistence (`~/.config/voiceterm/onboarding_state.toml`) so a `Getting started` hint remains until the first successful transcript capture.
- [x] MP-207 Extract shared overlay frame rendering helpers (`overlay_frame`) and route help/settings/theme-picker framing through the shared path to reduce duplicated border/title/separator logic.
- [x] MP-208 Standardize overlay/HUD width accounting with Unicode-aware display width and add HUD module `priority()` semantics so queue/latency indicators survive constrained widths ahead of lower-priority modules.
- [x] MP-209 Replace opaque runtime status errors with log-path-aware messages (`... (log: <path>)`) across capture/transcript failure paths.
- [x] MP-210 Keep splash unchanged, but move discoverability/help affordances into runtime HUD/overlay surfaces (hidden HUD idle hint now includes `? help` + `^O settings`; help overlay adds clickable Docs/Troubleshooting OSC-8 links).
- [x] MP-211 Replace flat clap default `--help` output with a themed, grouped renderer backed by clap command metadata (manual `-h`/`--help` interception, sectioned categories, single-accent hacker-style scan path with dim borders + bracketed headers, theme/no-color parity, and coverage guard so new flags cannot silently skip grouping).
- [x] MP-212 Remove stale pre-release/backlog doc references, align `VoiceTerm.app` Info.plist version with `rust/Cargo.toml`, and sync new `voiceterm` modules in changelog/developer structure docs.
- [x] MP-213 Add a Rust code-review research pack and wire it into the code-quality execution track with an explicit closure/archive handoff path into Theme Upgrade phases (`MP-148+`).
- [x] MP-218 Fix overlay mouse hit-testing for non-left-aligned coordinate spaces so settings/theme/help row clicks and slider adjustments still apply when terminals report centered-panel `x` coordinates.
- [x] MP-219 Clarify settings overlay footer control hints (`[×] close · ↑/↓ move · Enter select · Click/Tap select`) and add regression coverage so footer close click hit-testing stays intact after copy updates.
- [x] MP-220 Fix settings slider click direction handling so pointer input on `Sensitivity`/`Wake sensitivity` tracks can move left/right by click position, with regression tests for backward slider clicks.
- [x] MP-221 Fix hidden-launcher mouse click redraw parity so `[hide]` and collapsed `[open]` clicks immediately repaint launcher state (matching arrow-key `Enter` behavior), with regression tests for both click paths.
- [x] MP-222 Resolve post-release `lint_hardening` CI failures by removing redundant-closure clippy violations in `custom_help.rs` and restoring maintainer-lint lane parity on `master`.
- [x] MP-223 Unify README CI/mutation badge theming to black/gray endpoint styling and enforce red failure states via renderer scripts (`render_ci_badge.py`, `render_mutation_badge.py`) plus CI workflow auto-publish on `master`.
- [x] MP-224 Harden Theme Studio style-pack test determinism by isolating unit tests from ambient shell `VOICETERM_STYLE_PACK_JSON` exports (tests now ignore runtime style-pack env unless explicit opt-in is set, and lock-path tests opt in intentionally), preventing cross-shell snapshot/render drift during `cargo test --bin voiceterm`.
- [x] MP-225 Fix Enter-key auto-mode flip regression: when stale HUD button focus is on `ToggleAutoVoice`, pressing `Enter` now submits PTY input (no mode flip), backed by a focused event-loop regression test and docs sync.
- [x] MP-228 Audit user-doc information architecture and seed screenshot-refresh governance: rebalance `QUICK_START.md` to onboarding scope, move deep runtime semantics to guides, document transcript-history mouse behavior and env parity (`VOICETERM_ONBOARDING_STATE`), and add a maintainer capture matrix for pending UI surfaces.
- [x] MP-214 Close out the active code-quality track by triaging remaining findings, archiving audit records, and continuing execution from Theme Upgrade (`MP-148+`).
- [x] MP-215 Standardize runtime status-line width/truncation on Unicode-aware display width in remaining char-count paths (`rust/src/bin/voiceterm/writer/render.rs` and `rust/src/bin/voiceterm/status_style.rs`) with regression coverage for wide glyphs (landed Unicode-aware width/truncation in writer sanitize/render/status-style paths, preserved printable Unicode status text, and added regression tests for wide-glyph truncation and width accounting).
- [x] MP-216 Consolidate duplicate transcript-preview formatting logic shared by `rust/src/bin/voiceterm/voice_control/navigation.rs` and `rust/src/bin/voiceterm/voice_control/drain/message_processing.rs` into a single helper with shared tests (landed shared `voice_control/transcript_preview.rs` formatter and removed duplicated implementations from navigation/drain paths with focused unit coverage).
- [x] MP-217 Enable settings-overlay row mouse actions so row clicks select and apply setting toggles/cycles (including click paths for `Close` and `Quit`) instead of requiring keyboard-only action keys.
- [x] MP-262 Publish a full senior-level engineering audit baseline in `dev/archive/2026-02-20-senior-engineering-audit.md` with measured code-shape, lint-debt, CI hardening, and automation findings mapped to executable follow-up MPs.
- [x] MP-263 Harden GitHub Actions supply-chain posture: pin third-party actions by commit SHA, define explicit least-privilege `permissions:` on every workflow, and add `concurrency:` groups where duplicate in-flight runs can race or waste minutes (landed by pinning all workflow action refs to 40-char SHAs across `.github/workflows/*.yml`, adding explicit `permissions:`/`concurrency:` blocks to every workflow, and narrowing write scope to job-level where badge-update pushes require `contents: write`).
- [x] MP-264 Add repository ownership and dependency automation baseline by introducing `.github/CODEOWNERS` and `.github/dependabot.yml` (grouped update policies + review routing) so tooling/runtime changes always have accountable reviewers and timely dependency refresh cadence (landed with explicit ownership coverage for runtime/tooling/distribution paths and weekly grouped update policies for GitHub Actions, Cargo, and PyPI packaging surfaces).
- [ ] MP-265 Decompose oversized runtime modules with explicit shape budgets and staged extraction plans (top hotspots: `event_loop/input_dispatch.rs`, `status_line/format.rs`, `status_line/buttons.rs`, `theme/rule_profile.rs`, `theme/style_pack.rs`, `transcript_history.rs`; next maintainability-audit tranche should prioritize `event_loop.rs`, `main.rs`, `dev_command/{broker,review_artifact,command_state}.rs`, and `dev_panel/{review_surface,cockpit_page/mod}.rs`) while preserving non-regression behavior coverage (in progress: `dev/scripts/checks/check_code_shape.py` now enforces path-level non-growth budgets for the hotspot files so decomposition work is CI-measurable instead of policy-only; `event_loop/input_dispatch.rs` overlay-mode handling was extracted into `event_loop/input_dispatch/overlay.rs` + `event_loop/input_dispatch/overlay/overlay_mouse.rs`; prior slice extracted status-line right-panel formatting/animation helpers from `status_line/format.rs` into `status_line/right_panel.rs`; latest slices move minimal-HUD right-panel scene/waveform/pulse helpers from `status_line/buttons.rs` into `status_line/right_panel.rs` and extract queue/wake/latency badge formatting into `status_line/buttons/badges.rs`, reducing `status_line/buttons.rs` from 1059 to 801 lines while keeping focused status-line tests green; newest slices extract compact/minimal HUD helpers into `status_line/format/compact.rs`, then move single-line layout helpers into `status_line/format/single_line.rs`, reduce `theme/rule_profile.rs` by moving inline tests into `theme/rule_profile/tests.rs` (`922 -> 265`), and move writer-state test-only timing constants from `writer/state.rs` into `writer/state/tests.rs` so production writer modules remain runtime-focused; raised file-shape overrides were removed with focused runtime suites and clippy reruns green, writer message routing remains split across `writer/state/dispatch.rs` plus `writer/state/dispatch_pty.rs` after retiring temporary dispatch/redraw/prompt complexity exceptions, and the newest Rust-overlay cleanup split `dev_panel/review_surface.rs` lane helpers plus `dev_panel/cockpit_page/mod.rs` control sections into focused sibling modules (`review_surface_lanes.rs`, `cockpit_page/control_sections.rs`) so both Dev-panel hotspots now sit well below their prior shape-risk thresholds).
- [ ] MP-266 Burn down Rust lint-debt hotspots by reducing `#[allow(...)]` surface area and non-test `unwrap/expect` usage, then add measurable gates/reporting so debt cannot silently regress (in progress: landed `dev/scripts/checks/check_rust_lint_debt.py` with working-tree + commit-range modes, wired governance bundles/docs references, and added tooling-control-plane CI enforcement so changed Rust files cannot add net-new lint debt without an explicit failure signal; latest slice removes 22 `#[allow(dead_code)]` suppressions by scoping PTY counter helper APIs/re-exports to tests in `pty_session/counters.rs` + `pty_session/mod.rs`, with full `devctl check --profile ci` and lifecycle matrix test coverage green; newest enforcement slice keeps AI-guard scripts enabled in `check --profile quick|fast` so default local iteration and post-test quick follow-up paths no longer skip structural/code-quality guards by profile default).
- [ ] MP-267 Run a naming/API cohesion pass across theme/event-loop/status/memory surfaces to remove ambiguous names, tighten public API intent, and consolidate duplicated helper logic into shared modules (`dev/active/naming_api_cohesion.md`; in progress: canonical `swarm_run` command naming now enforced in parser/dispatch/workflow/docs with no legacy alias in active command paths, duplicate triage/mutation policy engines consolidated into shared `loop_fix_policy.py` helper with tests, duplicated devctl numeric parsing consolidated into `dev/scripts/devctl/numeric.py` (`to_int`/`to_float`/`to_optional_float`) with callsite rewiring, Theme Studio list navigation consolidated under shared `theme_studio/nav.rs` with consistent `select_prev`/`select_next` naming across page state + input-dispatch call paths, and prompt-occlusion suppression transitions extracted into `event_loop/prompt_occlusion.rs` so output/input/periodic dispatchers share one runtime owner for suppression side effects).
- [x] MP-268 Codify a Rust-reference-first engineering quality contract in `AGENTS.md` and `dev/DEVELOPMENT.md`, including mandatory official-doc reference pack links and handoff evidence requirements for non-trivial Rust changes.
- [ ] MP-269 Add Theme Studio style-pack hot reload (`notify` watcher + debounce + deterministic rollback-safe apply path) so theme iteration does not require restarting VoiceTerm.
- [ ] MP-270 Add algorithmic theme generation mode (`palette`-backed seed-color derivation with contrast guards) and expose it in Theme Studio as an optional starting point, not a replacement for manual edits.
- [ ] MP-271 Replace ad-hoc animation transitions with a deterministic easing profile layer (`keyframe`-style easing contracts or equivalent) and benchmark frame-cost impact on constrained terminals.
- [ ] MP-272 Define and implement Memory Studio context-injection contract for Codex/Claude handoff flows (selection policy, token budget, provenance formatting, failure rollback).
- [ ] MP-273 Produce an overlay architecture ADR evaluating terminal-only vs hybrid desktop overlay (`egui_overlay`/window-layer path) with explicit capability matrix, migration risk, and phased rollout recommendation.
- [x] MP-274 Add AI coding guardrails for Rust best-practice drift by introducing `dev/scripts/checks/check_rust_best_practices.py` (working-tree + commit-range non-regression checks for reason-less `#[allow(...)]`, undocumented `unsafe { ... }`, and public `unsafe fn` without `# Safety` docs), wiring it into `devctl check` (`--profile ai-guard` plus automatic `prepush`/`release` guard steps), and enforcing commit-range execution in `.github/workflows/tooling_control_plane.yml` with docs/bundle parity updates.
- [x] MP-275 Normalize `--input-device` values before runtime recorder lookup by collapsing wrapped whitespace/newline runs and rejecting empty normalized names so wake/manual capture initialization stays resilient to terminal line-wrap paste artifacts.
- [x] MP-276 Harden wake-word runtime diagnostics/ownership handoff: HUD now reflects listener-startup failures (`Wake: ERR` + status/log-path message) instead of false `Wake: ON` state when listener init fails, and wake detection now self-pauses listener capture before triggering shared capture startup to reduce microphone ownership races.
- [x] MP-277 Expand wake-word matcher alias normalization for common STT token-split variants (`code x` -> `codex`, `voice term` -> `voiceterm`) while preserving short-utterance guardrails and updating troubleshooting phrase guidance.
- [x] MP-278 Correct wake-trigger capture origin labeling end-to-end so wake-detected recordings flow through the shared capture path with explicit `WakeWord` trigger semantics (logs/status no longer misreport wake-initiated captures as manual starts).
- [x] MP-279 Reduce wake-state confusion and listener churn: keep `Wake: ON` badge styling steady (no pulse redraw), remove periodic wake-badge animation ticks, and extend wake-listener capture windows to reduce frequent microphone open/close cycling on macOS.
- [x] MP-280 Harden wake re-arm reliability after first trigger by decoupling wake detections from the auto-voice pause latch, allowing longer command tails when wake phrases lead the transcript, and adding no-audio retry backoff to reduce rapid microphone indicator churn on transient capture failures.
- [x] MP-281 Add built-in voice submit intents for insert mode (`send`, `send message`, `submit`) so staged transcripts can be submitted hands-free through the same newline path as Enter, including one-shot wake tails (`hey codex send` / `hey claude send`).
- [x] MP-296 Keep latency visibility stable in auto mode by preserving the last successful latency sample across auto-capture `Empty` cycles and allowing the shortcuts-row latency badge to remain visible during auto recording/processing (manual mode continues hiding during active capture); coverage added in `status_line/buttons/tests.rs` and `voice_control/drain/tests.rs`.

## Phase 3D - Memory + Action Studio (Planning Track)

Memory Studio execution gate: MP-230..MP-255 are governed by
`dev/active/memory_studio.md`. A Memory MP may move to `[x]` only with
documented `MS-G*` pass evidence.

- [x] MP-230 Establish canonical memory event schema + storage foundation (JSONL append log + SQLite index) for machine-usable local memory (`MS-G01`, `MS-G02`).
- [ ] MP-231 Implement deterministic retrieval APIs (topic/task/time/semantic) with provenance-tagged ranking and bounded token budgets (`MS-G03`, `MS-G04`, `MS-G18`, `MS-G19`). Current proving substrate is the shipped in-memory index plus `boot_pack` / `task_pack`; 2026-03-09 follow-ups now auto-extract bounded `MP-*` refs, repo file paths, and small topic tags on live ingest and emit operator-cockpit export artifacts for `task_pack`, `session_handoff`, and `survival_index`. The first scoring-trace/query-evidence closure slice is now live in `memory/survival_index.rs` and Memory cockpit exports (`query_traces` + deduplicated evidence rows); remaining scope is broader semantic/topic ranking coverage and browser-level retrieval UX.
- [x] MP-232 Ship context-pack generation (`context_pack.json` + `context_pack.md`) for AI boot/handoff workflows with explicit evidence references (`MS-G03`, `MS-G07`).
- [ ] MP-233 Deliver Memory Browser overlay (filter/expand/scroll/replay-safe controls) with keyboard+mouse parity (`MS-G06`, `MS-G20`). Current proving path should surface memory status/query/export views inside the Rust operator cockpit first, then expand into the fuller Memory Browser once the cross-plan operator flow is stable. The shipped proof is broader now: Control-tab memory status, a dedicated read-only Memory cockpit tab backed by ingest/review/boot-pack/handoff previews, the Boot-pack-backed Handoff preview, and repo-visible JSON/Markdown exports for `boot_pack`, `task_pack`, `session_handoff`, and the first `survival_index` preview are live. Remaining open scope is the full browser UX plus attach-by-ref/state-flow integration on top of those exports.
- [ ] MP-234 Deliver Action Center overlay with policy-tiered command execution (read-only/confirm-required/blocked), preview/approval flow, and action-run audit logging (`MS-G05`, `MS-G06`). Action policy/catalog scaffolding already exists in `memory/action_audit.rs`; this scope still needs runtime approval flows, audit wiring, and convergence with the MP-340 typed action router so memory-derived suggestions, overlay buttons, and review-channel requests share one approval/waiver model instead of parallel executors.
- [ ] MP-235 Add memory governance controls (retention, redaction hooks, per-project isolation) and regression tests for bounded growth/privacy invariants (`MS-G04`, `MS-G05`). Redaction plus retention-GC foundation is already shipped in `memory/governance.rs`; remaining scope is user-facing policy wiring, isolation profiles, and regression coverage.
- [ ] MP-236 Complete docs + release readiness for Memory Studio (architecture/user docs/changelog + CI evidence bundle) (`MS-G07`, `MS-G08`).
- [ ] MP-237 Add memory-evaluation harness and quality gates (`precision@k`, evidence coverage, deterministic pack snapshots, latency budgets) for release blocking (`MS-G03`, `MS-G04`, `MS-G08`).
- [ ] MP-238 Add model-adapter interop for context packs (Codex/Claude-compatible pack rendering while preserving canonical JSON provenance, including review-channel/controller handoff attachments) (`MS-G03`, `MS-G07`, `MS-G08`). Current runtime proof already builds a boot-pack-backed fresh bootstrap prompt in the Rust handoff cockpit, the Memory cockpit now emits repo-visible JSON/Markdown exports for `boot_pack`, `task_pack`, `session_handoff`, and `survival_index`, and the typed Rust action catalog carries review launch/rollover plus pause/resume actions with JSON summary rendering. Structured `review_state` attach-by-ref is now partially landed: event-backed review packets preserve `context_pack_refs` into reduced state/actions projections, Rust review surfaces/fresh prompts render those refs read-only, and the PyQt6 operator approval path keeps them lossless through decision artifacts. Missing scope is `controller_state` parity, broader provider-shaped review/control attachments, and packet-outcome ingest parity.
- [ ] MP-240 Add validated Memory Cards as a derived-truth layer (decision/project_fact/procedure/gotcha/task_state/glossary) with evidence links, TTL policies, and branch-aware validation-before-injection (`MS-G03`, `MS-G09`).
- [x] MP-241 Wire dev tooling and git intelligence into memory ingestion (`devctl status/report`, release-notes artifacts, git range summaries) and ship compiler outputs (`project_synopsis`, `session_handoff`, `change_digest`) in JSON+MD (`MS-G02`, `MS-G10`).
- [ ] MP-242 Ship read-only MCP memory exposure (resources + tools for search/context packs/validation) with deterministic provenance payloads and policy-safe defaults (`MS-G03`, `MS-G11`).
- [ ] MP-243 Add user memory-control modes (`off`, `capture_only`, `assist`, `paused`, `incognito`) with UI/state persistence and regression coverage for trust/privacy invariants (`MS-G05`, `MS-G06`). Current implementation now spans the Rust Dev-panel Control + Memory tabs with runtime mode/status visibility and mode-cycling, and the 2026-03-09 persistence slice landed startup restore plus persistent-config load/save so the configured `memory_mode` no longer resets on boot and dev-panel mode changes persist immediately into later snapshots. Closure still requires visible controls outside `--dev` plus negative-control/receipt UX.
- [ ] MP-244 Add sequence-aware action safety escalation so multi-command workflows increase policy tier when risk patterns combine (mutation + network + shell exec) and require explicit confirmation evidence (`MS-G05`, `MS-G11`).
- [ ] MP-246 Implement repetition-mining over memory events/command runs to detect high-frequency scriptable workflows, with support+confidence thresholds and provenance-scored candidates (`MS-G03`, `MS-G10`, `MS-G12`).
- [ ] MP-247 Ship automation suggestion flow that proposes script templates + `AGENTS.md` instruction patches + workflow snippets with preview/approve/reject UX (no auto-apply) and acceptance telemetry (`MS-G05`, `MS-G06`, `MS-G12`).
- [ ] MP-248 Add opt-in external transcript import adapters (for example ChatGPT export files) normalized into canonical memory schema with source tagging/redaction and retrieval-only defaults for safety (`MS-G01`, `MS-G05`, `MS-G13`).
- [ ] MP-249 Implement isolation profiles for action execution (`host_read_only`, `container_strict`, `host_confirmed`) with policy wiring, audit logging, and escape-attempt regression tests (`MS-G05`, `MS-G14`).
- [ ] MP-250 Build compaction experiment harness (A/B against no-compaction baseline) with replay fixtures, benchmark adapters, and report artifacts covering quality/citation/latency/token metrics (`MS-G03`, `MS-G15`).
- [ ] MP-251 Gate compaction default-on rollout behind non-inferiority/evidence thresholds and publish operator guidance for safe enablement strategy (`MS-G07`, `MS-G08`, `MS-G15`).
- [ ] MP-252 Prototype Apple Silicon acceleration paths (SIMD/Metal/Core ML where applicable) for memory retrieval/compaction workloads and publish backend benchmark matrix vs CPU reference (`MS-G03`, `MS-G16`).
- [ ] MP-253 Gate acceleration rollout behind non-inferiority quality checks, deterministic-evidence parity checks, and runtime fallback guarantees (`MS-G08`, `MS-G16`).
- [ ] MP-254 Evaluate ZGraph-inspired symbolic compaction for memory units/context packs (pattern aliases for repeated paths/commands/errors), with reversible transforms and deterministic citation-equivalence checks (`MS-G03`, `MS-G15`, `MS-G17`).
- [ ] MP-255 Gate any symbolic compaction rollout behind non-inferiority quality thresholds, round-trip parity fixtures, and explicit default-off operator guidance until `MS-G17` passes (`MS-G07`, `MS-G08`, `MS-G17`).

2026-03-09 implementation alignment for the memory lane: the current runtime
already ships JSONL-backed memory ingest/recovery, an in-memory retrieval
index, operator-cockpit memory status/mode snapshots, and a boot-pack-backed
handoff/bootstrap prompt. The 2026-03-09 runtime follow-ups also landed
operator-cockpit query/export views by emitting repo-visible `boot_pack`,
`task_pack`, `session_handoff`, and `survival_index` JSON/Markdown artifacts
from the Rust Memory tab. The first scoring-trace closure is now shipped via
`memory/survival_index.rs` + structured `survival_index` exports. The next
slice is to turn the remaining proof path into `MP-231`/`MP-238`/`MP-243`
closure evidence by expanding retrieval coverage, finishing review/control
`context_pack_refs` consumption, and landing packet-outcome ingest
before the full Memory Browser / Action Center overlays
become the main product surface.

## Phase 3A - Mutation Hardening (Parallel Track)

- [ ] MP-015 Improve mutation score with targeted high-value tests (promoted from Backlog).
  - [ ] Build a fresh shard-by-shard survivor baseline on `master` and rank hotspots by missed mutants.
  - [x] Add mutation outcomes freshness visibility and stale-data gating in local tooling (`check_mutation_score.py` + `devctl mutation-score` now report source path/age and support `--max-age-hours`).
  - [x] Add targeted mutation-killer coverage for `theme_ops::cycle_theme` ordering/wrap semantics so default-return/empty-list/position-selection mutants are caught deterministically.
  - [x] Add targeted mutation-killer coverage for `Theme::from_name` alias arms (`tokyonight`/`tokyo-night`/`tokyo`, `gruvbox`/`gruv`) and `Theme::available()` list parity so empty/placeholder return mutants are caught.
  - [x] Add targeted mutation-killer coverage for `status_style::status_display_width` arithmetic and `terminal::take_sigwinch` clear-on-read semantics so constant-return/math mutants are caught.
  - [x] Add targeted mutation-killer coverage for `main.rs` runtime guards (`contains_jetbrains_hint`, `is_jetbrains_terminal`, `resolved_meter_update_ms`, and `join_thread_with_timeout`) and eliminate focused survivors (`cargo mutants --file src/bin/voiceterm/main.rs`: 18 caught, 0 missed, 1 unviable).
  - [x] Add targeted mutation-killer coverage for `input/mouse.rs` protocol guards/parsers (SGR/URXVT/X10 prefix+length boundaries and dispatch detection), eliminating focused survivors (`cargo mutants --file src/bin/voiceterm/input/mouse.rs`: 76 caught, 0 missed, 17 unviable).
  - [x] Remove the equivalent survivor path in `config/theme.rs` (`theme_for_backend` redundant `NO_COLOR` branch), keep explicit env-behavior regression coverage, and re-verify focused mutants (`cargo mutants --file src/bin/voiceterm/config/theme.rs`: 6 caught, 0 missed) plus `devctl check --profile ci` green.
  - [x] Eliminate `event_loop.rs` helper/boundary survivors by adding direct coverage for drain/winsize/overlay rendering/button-registry/picker reset paths, hardening settings-direction boundary assertions, and refactoring slider sign math to non-equivalent `is_negative()` checks (`cargo mutants --file src/bin/voiceterm/event_loop.rs`: 58 caught, 0 missed, 2 unviable) with `devctl check --profile ci` green.
  - [x] Remove `config/backend.rs` argument-length equivalent survivors in backend command resolution (`command_parts.len() > 1`) by refactoring to iterator-based split (`next + collect`) and re-verifying focused mutants (`cargo mutants --file src/bin/voiceterm/config/backend.rs`: 1 caught, 0 missed, 1 unviable) with `devctl check --profile ci` green.
  - [x] Add targeted `config/util.rs` path-shape boundary coverage for `is_path_like` (absolute/relative path positives, bare binary and empty-value negatives) and re-verify focused mutants (`cargo mutants --file src/bin/voiceterm/config/util.rs`: 11 caught, 0 missed) with `devctl check --profile ci` green.
  - [x] Add targeted regression coverage for runtime utility hotspots `auth.rs` and `lock.rs` (login command validation + exit-status mapping paths and mutex poison-recovery paths) so low-coverage utility modules stay protected without introducing lint-debt growth.
  - [x] Harden `event_loop/input_dispatch/overlay/overlay_mouse.rs` boundary predicates and add focused Theme Studio/settings mouse regression coverage (footer non-close area, border columns, option-row activation/out-of-range guards), eliminating the focused survivor cluster (`cargo mutants --file src/bin/voiceterm/event_loop/input_dispatch/overlay/overlay_mouse.rs --re 'overlay_mouse\\.rs:(32|39|99|100|119|142|143|144|145):'`: 8 caught, 0 missed).
  - [ ] Add targeted tests for top survivors in current hotspots (`src/bin/voiceterm/config/*`, `src/bin/voiceterm/hud/*`, `src/bin/voiceterm/input/mouse.rs`) and any new top offenders.
  - [ ] Ensure shard jobs always publish outcomes artifacts even when mutants survive.
  - [ ] Re-run mutation workflow until aggregate score holds at or above `0.80` on `master` for two consecutive runs (manual + scheduled).
  - [ ] Keep non-mutation quality gates green after each hardening batch (`python3 dev/scripts/devctl.py check --profile ci`, `Security Guard`).
- MP-015 acceptance gates:
  1. `.github/workflows/mutation-testing.yml` passes on `master` with threshold `0.80`.
  2. Aggregated score gate passes via `python3 dev/scripts/checks/check_mutation_score.py --glob "mutation-shards/**/shard-*-outcomes.json" --threshold 0.80`.
  3. Shard outcomes artifacts are present for all 8 shards in each validation run.
  4. Added hardening tests remain stable across two consecutive mutation workflow runs.

## Phase 4 - Advanced Expansion

- [ ] MP-092 Streaming STT and partial transcript overlay.
- [ ] MP-093 tmux/neovim integration track.
- [ ] MP-094 Accessibility suite (fatigue hints, quiet mode, screen-reader compatibility).
- [ ] MP-095 Custom vocabulary learning and correction persistence.

## Backlog (Not Scheduled)

- [ ] MP-016 Stress test heavy I/O for bounded-memory behavior.
- [ ] MP-031 Add PTY health monitoring for hung process detection.
- [ ] MP-032 Add retry logic for transient audio device failures.
- [ ] MP-033 Add benchmarks to CI for latency regression detection.
- [ ] MP-034 Add mic-meter hotkey for calibration.
- [ ] MP-037 Consider configurable PTY output channel capacity.
- [ ] MP-145 Eliminate startup cursor/ANSI escape artifacts shown in Cursor (Codex and Claude backends), with focus on the splash-screen teardown to VoiceTerm HUD handoff window where artifacts appear before full load. (in progress: writer pre-clear is now constrained to JetBrains terminals to reduce Cursor typing-time HUD flash while preserving JetBrains scroll-ghost mitigation.)
- [x] MP-146 Improve controls-row bracket styling so `[` `]` tokens track active theme colors and selected states use stronger contrast/readability (especially for arrow-mode focus visibility) (landed controls-row bracket tint routing so unfocused pills inherit active button highlight colors instead of always dim brackets, plus focused button emphasis via bold+info-bracket rendering for stronger keyboard focus visibility; covered by `status_line::buttons` regressions `format_button_brackets_track_highlight_color_when_unfocused`, `focused_button_uses_info_brackets_with_bold_emphasis`, and existing focus-bracket parity tests).
- [x] MP-147 Fix Cursor-only mouse-mode scroll conflict: with mouse mode ON, chat/conversation scroll should still work in Cursor for both Codex and Claude backends; preserve current JetBrains behavior (works today in PyCharm/JetBrains), keep architecture/change scope explicitly Cursor-specific, and require JetBrains non-regression validation so the Cursor fix does not break JetBrains scrolling. (landed Cursor-specific scroll-safe mouse handling in writer mouse control: Cursor keeps wheel scrollback available while settings can remain `Mouse: ON - scroll preserved in Cursor`, while JetBrains and other terminals retain existing mouse behavior.) Regression note (2026-02-25): users still report Cursor touchpad/wheel scrolling failing while `Mouse` is ON, with scrollbar drag still working; follow-up tracked in `MP-344`.
- [ ] MP-227 Explore low-noise progress-animation polish for task/status rows (inspired by Claude-style subtle shimmer/accent transitions during active thinking), including optional tiny accent pulses/color sweeps with strict readability/contrast bounds and no distraction under sustained usage; keep as post-priority visual refinement (not current execution scope).
- [x] MP-153 Add a CI docs-governance lane that runs `python3 dev/scripts/devctl.py docs-check --user-facing --strict` for user-facing behavior/doc changes so documentation drift fails early (completed via MP-302 docs-policy lane hardening in `.github/workflows/tooling_control_plane.yml`).
- [ ] MP-154 Add a governance consistency check for active docs + macro packs so removed workflows/scripts are not referenced in non-archive content.
- [ ] MP-155 Add a single pre-release verification command/profile that aggregates CI checks, mutation threshold, docs-governance checks, and hygiene into one machine-readable report artifact.
- [ ] MP-322 Investigate and fix wake-word + send intent "nothing to send" false negative: when using `Hey Claude, send` or `Hey Codex, send` voice commands, VoiceTerm sometimes reports "Nothing to send" even though there is staged text in the PTY input buffer; reproduce with both Claude and Codex backends, capture transcript decision traces (`voiceterm --logs --log-content`), verify send-intent detection timing relative to transcript staging, add targeted matcher/integration tests for the wake-tail send flow, and ensure the send intent checks for staged PTY content (not just VoiceTerm internal staged text state). Physical testing required alongside automated coverage.
- [ ] MP-323 Restore keyboard left/right caret navigation while editing staged text: currently Left/Right (and equivalent arrow-key paths) are captured by tab/button focus navigation instead of moving the text cursor inside the transcript/input field, which blocks correction of Whisper transcription mistakes before submit. Reproduce in active VoiceTerm sessions with staged text, route Left/Right to caret movement whenever text input/edit mode is active, preserve existing tab/control navigation when text edit mode is not active, and add focused keyboard/mouse regression coverage to prevent future text-edit lockouts. (2026-02-27 input-path hardening landed for related navigation regressions: shared arrow parser now accepts colon-parameterized CSI forms used by keyboard-enhancement modes, preventing settings/theme/overlay arrow-navigation dropouts after backend prompt-state transitions. 2026-03-02 field report follow-up: Codex and Claude sessions still show split ownership where arrow keys route either to terminal caret or HUD buttons based on `insert_pending_send`, and users recover by pressing `Ctrl+T`/other hotkeys; scope now includes a deterministic input-ownership model with explicit HUD-focus entry/exit semantics so caret editing and HUD button access remain available without mode confusion. 2026-03-05 backlog clarification: preserve explicit up/down focus handoff between chat region and overlay controls so Left/Right operates on the active surface only; defer this fix until post-next-release unless it becomes a release blocker.)
- [ ] MP-324 Finalize Ralph loop rollout evidence on default branch: after the workflow lands on the default branch, run one `workflow_dispatch` `CodeRabbit Ralph Loop` execution on `develop` (`execution_mode=report-only`) and confirm `check_coderabbit_ralph_gate.py --branch develop` resolves by workflow-run evidence rather than fallback logic; capture run URL and gate output in tooling handoff notes so release gating assumptions are explicit for all agents.
- [x] MP-325 Harden Ralph loop source-run correlation: pin `triage-loop` execution to authoritative source run id/sha when launched from `workflow_run`, fail safely on source mismatch, and preserve manual-dispatch fallback behavior (landed `--source-run-id/--source-run-sha/--source-event` parser+command+core wiring, source-run attempt pinning, run/artifact SHA mismatch detection with explicit `source_run_sha_mismatch` reason codes, and workflow source-run id/sha forwarding in `.github/workflows/coderabbit_ralph_loop.yml`).
- [x] MP-326 Implement real `summary-and-comment` notify semantics for `triage-loop`: add comment-target resolution (`auto|pr|commit`), idempotent marker updates, and workflow permission hardening so comment mode is deterministic and non-spammy (landed comment target flags, PR/commit target resolver, marker-based upsert behavior via GitHub API, and workflow permission updates including `pull-requests: write` + `issues: write`).
- [x] MP-327 Add bounded mutation remediation command surface (`devctl mutation-loop`) with report-only default, scored hotspot outputs, freshness checks, and optional policy-gated fix attempts (landed `dev/scripts/devctl/commands/mutation_loop.py`, `mutation_loop_parser.py`, `mutation_ralph_loop_core.py`, bundle/playbook outputs, and targeted unit coverage).
- [x] MP-328 Add `.github/workflows/mutation_ralph_loop.yml` orchestration: mutation-loop mode controls, bounded retry parameters, artifact bundling, and optional notify surfaces with default non-blocking behavior (landed workflow_run + workflow_dispatch wiring, mode/threshold/notify/comment inputs, summary output, and artifact upload).
- [x] MP-329 Add mutation auto-fix command policy gate: enforce allowlisted commands/prefixes, explicit reason codes on deny paths, and auditable action traces for each attempt (landed `control_plane_policy.json` baseline, `AUTONOMY_MODE` + branch allowlist + command-prefix gating, and policy-deny reason surfacing in mutation loop reports).
- [ ] MP-330 Scaffold Rust containerized mobile control-plane service (`voiceterm-control`) with read-only health/loop/ci/mutation endpoints and constrained workflow-dispatch controls.
- [ ] MP-331 Add phone adapter track (SMS-first pilot + push/chat follow-up) with policy-gated action routing, webhook auth, response/audit persistence, and bounded remote-operation scope. (partial: `devctl autonomy-loop` now emits phone-ready status snapshots under `dev/reports/autonomy/queue/phone/latest.{json,md}` including terminal trace, draft text, and source run context for read-first mobile surfaces; `devctl phone-status` now provides SSH/iPhone-safe projection views (`full|compact|trace|actions`) with optional projection bundle emission for controller-state files; `devctl controller-action` now provides a guarded safe subset (`refresh-status`, `dispatch-report-only`, `pause-loop`, `resume-loop`) with allowlist/kill-switch policy checks and auditable outputs; `app/ios/VoiceTermMobileApp` is now the runnable first-party iPhone shell, `app/ios/VoiceTermMobile` is the shared core package it imports, the app now exposes a short tutorial + live-bundle-first startup path, `devctl mobile-app` now supports a real simulator demo, a live-review simulator mode, and physical-device wizard/install actions, and the mobile bundle now surfaces typed Ralph/controller action previews through the shared backend contract. Remaining scope is the real live adapter: connect the iPhone to the Mac-hosted Rust control service on the same network first, add typed approve/deny plus operator-note/message actions, provider-aware continue/retask flows, and staged phone voice-to-action input, then add a secure off-LAN/cellular path with reconnect/resume semantics so the phone can rejoin long-running plans already active on the home machine without opening raw PTY/devctl ports to the public internet.)
- [ ] MP-332 Add autonomy guardrails and traceability controls (`control_plane_policy.json`, replay protection, mode kill-switch, branch-protection-aware action rejection, duplicate/stale run suppression). (partial: `control_plane_policy.json` added, `AUTONOMY_MODE` + branch/prefix policy gate wired for both mutation and triage fix modes, triage loop now emits dedicated review-escalation comment upserts when retries exhaust unresolved backlog, marker-based duplicate comment suppression landed, `devctl check --profile release` now enforces strict remote release gates (`status --ci --require-ci` + CI-mode CodeRabbit/Ralph checks), bounded controller surfaces now ship via `devctl autonomy-loop` + `.github/workflows/autonomy_controller.yml` with run-scoped checkpoint packet queue artifacts, and scheduled autonomy/watchdog/mutation-loop workflow-run behavior is now mode-gated so background loops are opt-in instead of default red-noise; replay protection + deeper branch-protection/merge-queue enforcement remain pending.)
- [x] MP-333 Enforce active execution-plan traceability governance: non-trivial agent work must be anchored to a `dev/active/*.md` execution-plan doc (with checklist/progress/audit sections), and tooling guardrails must fail when contract markers/required sections drift (landed enforcement updates in `check_active_plan_sync.py` for required execution-plan docs + marker + required sections, plus AGENTS contract references).
- [x] MP-334 Add external-repo federation bridge for reusable autonomy components: pin `code-link-ide` + `ci-cd-hub` in `integrations/`, provide one-command sync path, and document governed selective-import workflow for this repo template path. (landed submodule links + shell helper + `devctl integrations-sync`/`integrations-import` command surfaces, policy allowlists in `control_plane_policy.json` (`integration_federation`), destination-root guards, and JSONL audit logging for sync/import actions.)
- [ ] MP-335 Fix wake word send intent not triggering in auto mode: when VoiceTerm is in auto-listen mode and actively listening, saying "Hey Codex send" (or "Hey Claude send") does not trigger the send action — the wake word is effectively ignored while the mic is already open. Expected behavior: the wake-word detector should remain active during auto-mode listening so that saying the send wake phrase finalizes and submits the current transcript. Distinct from MP-322 (which covers "nothing to send" false negatives when the wake word does fire); this issue is that the wake word never fires at all in auto mode. Reproduce by enabling auto mode, speaking a transcript, then saying "Hey Codex send" without pausing — observe that the message is not sent. Physical testing required.
- [ ] MP-336 Add `network-monitor-tui` to the external federation + dev-mode bridge scope: link a pinned `integrations/network-monitor-tui` source, define allowlisted import profile(s) for throughput/latency sampler primitives, expose a read-only metrics surface for `--dev` + phone status views without introducing remote-control side effects, and add isolated runtime mode flags (`--monitor` and/or `--mode monitor`) so monitor/tooling startup does not interfere with the default Whisper voice-overlay path. The future monitor entry path should open the same Rust operator cockpit used by `--dev`, not a second forked console.
- [x] MP-337 Add repeat-to-automate governance and baseline scientific audit program: require repeated manual work to become guarded automation or explicit debt, add tracked `dev/audits/` runbook/register/schema artifacts, ship analyzer tooling (`dev/scripts/audits/audit_metrics.py`) that quantifies script-only vs AI-assisted vs manual execution share with optional chart outputs, and auto-emit per-command `devctl` audit events (`dev/reports/audits/devctl_events.jsonl`) for continuous trend data.
- [ ] MP-338 Stand up a loop-output-to-chat coordination lane: maintain a dedicated runbook for loop suggestion handoff (`dev/active/loop_chat_bridge.md`), define dry-run/live-run evidence capture, and keep operator decisions/next actions append-only so loop guidance can be promoted safely into autonomous execution. (partial: added `devctl autonomy-report` dated digest bundles, upgraded `devctl autonomy-swarm` to one-command execution with default post-audit digest + reserved `AGENT-REVIEW` lane for live runs, added `devctl swarm_run` for guarded plan-scoped swarm + governance + plan-evidence append, added bounded continuous cycle support via `--continuous/--continuous-max-cycles` so runs keep advancing unchecked checklist items until `plan_complete`, `max_cycles_reached`, or `cycle_failed`, wired workflow-dispatch lane `.github/workflows/autonomy_run.yml`, and added `devctl autonomy-benchmark` matrix reports for plan-scoped swarm-size/tactic tradeoff evidence.)
- [ ] MP-340 Deliver one-system operator surfaces + deterministic autonomy learning: keep Rust overlay as runtime primary, keep iPhone/SSH surfaces over one `controller_state` contract, and implement artifact-driven playbook learning (fingerprints, confidence, promotion/decay gates) so repeated loop tasks are reused safely with auditable evidence. This umbrella scope also owns the cross-plan contract that keeps Memory Studio (`MP-230..MP-255`), the review channel (`MP-355`), and controller surfaces on one shared event/header model, one provider-aware handoff path, and one future unified timeline/replay view rather than three parallel side channels. Current direction: grow the existing Rust Dev panel into a staged operator cockpit (`Control`, `Ops`, `Review`, `Actions`, `Handoff`, plus developer-oriented Git/GitHub/CI/script/memory views), then let `--monitor` reuse that same cockpit as a dedicated startup path. The first `Ops` slice is the Rust-first lane for host-process hygiene, triage summaries, and later external monitor adapters, so those readouts stay in the typed control surface instead of Theme Studio or a parallel ad hoc UI. Buttons may emit high-level intents and AI may resolve those intents to the correct approved playbook, but execution must still route through one typed action catalog plus shared policy/approval/waiver model rather than bypassing safety with raw shell/API execution. MP-340 now also explicitly carries an overlay-native live guard-watchdog direction: the overlay may observe Codex/Claude PTY traffic, session-tail artifacts, repo diffs, and typed review/controller packets to infer what the agent is doing and trigger the matching repo guard family, but guard enforcement must stay typed, policy-gated, debounced, and auditable through `devctl` / controller actions rather than raw terminal injection. The watchdog is now also required to prove impact scientifically: capture matched before/after guarded coding episodes, use paired analysis by task, report effect sizes with confidence intervals plus practical-significance thresholds, and only then promote claims that the guards materially improve Codex/Claude output; the MP-340 analytics layer must also capture repo-owned speed/latency/churn/retry/collaboration metrics from terminal and guard episodes so the project can study time-to-green, guard-hit heatmaps, provider deltas, and other operational signals with a real dashboard instead of anecdotes. Later ML work is allowed, but only as a second-phase ranking/prediction layer over that same artifact corpus after deterministic learning and offline evaluation are already working. Current `phone-status` / `controller-action` payloads and Rust Dev-panel snapshot builders are still interim projections; `devctl mobile-status` is now the first merged SSH-safe phone shim that combines review + controller state, `app/ios/VoiceTermMobile` is the shared first-party core package over that payload, and `app/ios/VoiceTermMobileApp` is the runnable iPhone/iPad app shell over the same emitted mobile bundle with guided simulator demo plus live-review proving modes and typed Ralph/controller action previews, but true MP-340 convergence still only happens once Rust, phone, review, and memory all read one emitted `controller_state` projection set with parity tests and provider-aware memory pack attachments. The mobile end-state is no longer just read-first bundle import: the Mac-hosted Rust control service must become the shared live source for overlay/dev/phone clients, the iPhone must gain typed approvals and structured operator-note/message dispatch plus staged voice-to-action flows, and the same host state must remain reachable over both local Wi-Fi and a secure off-LAN/cellular adapter with reconnect/resume semantics so ongoing plans continue on the home machine without exposing raw PTY or freeform shell access publicly. Immediate follow-up is now explicit: prove a simple phone ping/alert path first, then close richer iPhone parity over the same backend with split/combined terminal-style lane mirrors, typed approvals/notes/instructions, plan-to-agent assignment, simple/technical modes, provider-aware continue/retask routing, and reconnect/resume behavior. PyQt6 today, iPhone now, and any future Electron/Tauri shell later are clients of that shared backend only; none of them become the backend. Execution profiles should be explicit: `Guarded` by default, `AI-assisted Guarded` when the planner picks from the approved catalog, and a visible dev-only `Unsafe Direct` mode for local bypasses that stays red, noisy, and auditable rather than hidden. (2026-02-26 reset: retired the optional `app/pyside6` desktop command-center scaffold to keep operator execution Rust-first; all active scope now routes through Rust Dev panel + `devctl phone-status` + policy-gated `controller-action`. 2026-02-26 federation follow-up: completed fit-gap audit and added narrow import profiles for targeted `code-link-ide`/`ci-cd-hub` reuse instead of broad tree imports.)
- [ ] MP-341 Runtime architecture hardening pass for product-grade boundaries: tighten `rust/src/lib.rs` public surface (remove legacy re-export drift and prefer internal/facade boundaries), replace stringly `VoiceJobMessage::Error(String)` with typed error categories at subsystem boundaries, harden command parsing (`CustomBackend` quoting-safe parsing), reduce global-side-effect risk in Whisper stderr suppression path, and modernize PyPI launcher distribution flow away from clone+local-build bootstrap toward verified binary delivery. (partial 2026-02-25: hardened SIGWINCH registration via `sigaction` + `SA_RESTART`, removed production `unreachable!()` fallback in Theme Studio non-home renderer path, and reduced silent PTY-output drop risk with explicit unexpected-branch diagnostics.)
- [ ] MP-342 Increase push-to-talk startup grace by about 1 second to prevent early cutoff when users do not speak immediately after pressing PTT: currently first-press captures can end too quickly if there is a short delay before speech starts. Reproduce in Codex/Claude sessions, tune initial-silence/warmup handling for natural speech onset, add regression coverage for delayed speech starts, and verify no regressions for intentional short taps.
- [ ] MP-343 Stabilize screenshot button reliability: screenshot capture currently succeeds intermittently and can stop unexpectedly after some successful attempts. Reproduce repeated capture attempts in active sessions, harden button-triggered capture lifecycle/error handling, add regression coverage for repeated runs, and verify physical behavior with screenshot evidence.
- [ ] MP-344 Re-investigate Cursor mouse-mode scroll behavior and restore reliable wheel/touchpad scrolling when `Mouse` is ON: current reports indicate wheel/touchpad scrolling does not move chat history in Cursor while the draggable scrollbar still works. Document and preserve current workaround (`Mouse` ON + drag scrollbar, or set `Mouse` OFF for touchpad/wheel scrolling and use keyboard button focus with `Enter`), reproduce on Codex/Claude sessions, harden input-mode handling, and add regression coverage for Cursor-specific scroll paths. Scientific baseline seeded on 2026-02-25 via `devctl autonomy-benchmark` run `mp342-344-baseline-matrix-20260225` (covers `MP-342/MP-343/MP-344`; artifacts under `dev/reports/autonomy/benchmarks/mp342-344-baseline-matrix-20260225/`); live control-vs-swarm A/B run captured via `mp342-344-live-baseline-matrix-20260225` plus graph bundle `dev/reports/autonomy/experiments/mp342-344-swarm-vs-solo-20260225/`. 2026-03-05 backlog clarification: keep this scoped as post-next-release work unless it becomes a release blocker.
- [x] MP-345 Stand up a visible `data_science` telemetry workspace and continuous devctl metrics refresh so every devctl command contributes to long-run productivity/agent-sizing research: landed `data_science/README.md` workspace docs, new `devctl data-science` command (`summary.{md,json}` + SVG charts), automatic post-command refresh hook in `dev/scripts/devctl/cli.py` (disable with `DEVCTL_DATA_SCIENCE_DISABLE=1`), and weighted agent recommendation scoring from swarm/benchmark history (`success`, `tasks/min`, `tasks/agent`) under `dev/reports/data_science/latest/`; docs/history updated in `AGENTS.md`, `dev/scripts/README.md`, `dev/DEVCTL_AUTOGUIDE.md`, and `dev/history/ENGINEERING_EVOLUTION.md`.
- [x] MP-346 Execute IDE/provider modularization and compatibility hardening so host-specific behavior (`cursor`, `jetbrains`, `other`) and provider-specific behavior (`codex`, `claude`, `gemini`) are isolated behind explicit adapters, validated by matrix tests, and protected by God-file/code-shape/tooling governance gates (`dev/active/ide_provider_modularization.md`). (2026-03-02 docs scope: published explicit user-facing IDE compatibility matrix in README/USAGE with aligned links in QUICK_START + guides so only verified hosts are advertised as supported. 2026-03-02 audit triage scope added: dependency-policy gate hardening, guard-script coverage closure, adapter-contract completion inventory, and cross-plan shared-file ownership gates. 2026-03-02 exhaustive audit intake triage added: Dependabot/CODEOWNERS path-contract repair, active-plan sync required-row expansion, failure-triage watchlist coverage, current `bytes` RustSec remediation decision, Gemini/docs wording parity, plus CI baseline hardening gaps (MSRV/feature-matrix/macOS runtime lane + `cargo doc` gate) and governance tracker drift fixes. 2026-03-02 seventh-pass audit scope added: explicit host/runtime policy mapping for rolling detector + output redraw and 3 additional RuntimeProfile cross-product decisions, plus check-script signal hardening (`check_rust_audit_patterns`, `check_release_version_parity`, stale code-shape override detection). 2026-03-02 post-review blocker cleanup landed: `check_active_plan_sync.py` shape-budget recovery, `check_ide_provider_isolation.py` docs inventory registration, dedicated `check_agents_contract.py` test coverage, refreshed path-audit aggregate reporting, Gemini backend wording parity across user/developer docs, a new `cargo doc --workspace --no-deps --all-features` gate in `rust_ci.yml`, and explicit `cargo deny` enforcement in security/release workflow lanes. 2026-03-02 dependency-policy remediation closure landed: transitive `bytes` moved to `1.11.1`, `rust/deny.toml` now documents crate-scoped license exceptions for current runtime dependencies plus explicit `RUSTSEC-2024-0436` (`paste`) ignore rationale, and local `cargo deny` gate rerun passes. 2026-03-02 phase-0 governance/tooling follow-up landed: Rust CI now includes explicit MSRV/feature-matrix/macOS runtime validation, failure triage initially expanded for broad watch coverage, `check_code_shape.py` enforces stale override review-window checks, tracker drift was resolved (`MASTER_PLAN` board + local backlog ID deconfliction), and cross-plan shared-hotspot ownership/freeze gates are now mandatory in the runbook + board policy. 2026-03-04 phase-1 incremental cleanup slice landed: status-line JetBrains+Claude single-line fallback routing now consumes canonical `runtime_compat` helper and writer render host detection now maps through canonical `detect_terminal_host()` ownership instead of duplicate local host sniffing logic. 2026-03-04 additional phase-1 host-enum unification landed: writer render/state paths now use canonical `TerminalHost` directly (removed `writer/render.rs` `TerminalFamily` enum and replaced state-side `TerminalFamily` references), with writer-focused plus full `cargo test --bin voiceterm` coverage rerun. 2026-03-04 CI signal hardening follow-up landed: failure-triage scope narrowed to high-signal failure conclusions, release publishers now wait for same-SHA CodeRabbit/Ralph + `Release Preflight` gates, and scheduled autonomy/watchdog/mutation-loop workflow-run behavior now defaults to opt-in mode controls to reduce non-actionable red runs. 2026-03-04 additional phase-1 host-routing cleanup landed for banner/color/theme paths: banner skip policy now routes through canonical `runtime_compat::is_jetbrains_terminal`, color truecolor inference now uses canonical `runtime_compat::detect_terminal_host` for JetBrains/Cursor signals, and `theme/detect.rs` Warp fallback now respects canonical host precedence with dedicated regression coverage. 2026-03-04 final phase-1 host-routing slice landed in `theme/texture_profile.rs`: Cursor/JetBrains identity now routes through canonical `runtime_compat::detect_terminal_host`, local parsing is limited to non-host capability IDs, and regression coverage now asserts host precedence plus Kitty/iTerm fallback markers. 2026-03-04 canonical host-cache contract slice landed: runtime host detection now owns `OnceLock<TerminalHost>` caching in `runtime_compat`, thread-local test override/reset coverage validates deterministic host injection, and writer render no longer duplicates host caching. 2026-03-04 host-cache panic-path hardening landed: `runtime_compat` test override scoping now restores prior thread-local host values via drop guard on unwind, with dedicated panic regression coverage. 2026-03-04 Phase-1.5 shared-helper extraction landed: duplicated HUD debug env parsing/preview helpers were removed from `writer/state.rs`, `event_loop/prompt_occlusion.rs`, and `terminal.rs` and replaced with a shared `hud_debug` module, with full `cargo test --bin voiceterm` rerun green. 2026-03-04 additional Phase-1.5 backend-detection cleanup landed: writer-state backend checks now route through canonical `runtime_compat::backend_family_from_env()` + `BackendFamily` enum matching instead of raw backend-label substring parsing, with full runtime suite rerun green. 2026-03-04 provider-contract scaffolding slice landed: new `provider_adapter` signature module defines `ProviderAdapter`/`PromptDetectionStrategy` and provider-policy enums/config so Phase-2+ extraction can target stable trait contracts; CI profile rerun is green after adding signature-only scaffolding. 2026-03-04 Phase-1.5 closure slice landed: ANSI stripping now routes through shared `ansi` utility, env-var locking in runtime tests now routes through shared `test_env` helper instead of duplicated per-module locks, and `claude_prompt_suppressed` was renamed to `prompt_suppressed` across runtime/test code with full runtime+bundle validation green. 2026-03-04 Phase-2a data-only host timing extraction landed: `runtime_compat::HostTimingConfig` now owns host timing values keyed by `TerminalHost`, and writer timing call sites route through config lookups while preserving characterization behavior and passing full runtime + bundle validation. 2026-03-04 Phase-2b preclear policy extraction landed: writer preclear decisioning now routes through typed `PreclearPolicy` + `PreclearOutcome` so preclear decision and post-preclear flag effects are centralized while preserving existing host/provider behavior and full runtime + bundle validation remained green. 2026-03-04 Phase-2c redraw policy extraction landed: writer output redraw decisioning now routes through typed `RedrawPolicy` + `RedrawPolicyContext` consuming `PreclearOutcome`, so scroll/non-scroll/destructive-clear redraw outcomes are centralized while preserving existing host/provider behavior and full runtime + bundle validation remained green. 2026-03-04 Phase-2d idle-gating timing extraction landed: `maybe_redraw_status` idle/quiet-window/repair-settle gating now routes through typed `IdleRedrawTimingContext` + `resolve_idle_redraw_timing` in `writer/timing.rs`, with full runtime + bundle validation remaining green. 2026-03-04 Phase-2e message-dispatch + runtime-profile extraction closure landed: WriterState now resolves and injects a typed RuntimeProfile at construction, handle_message is dispatch-only, and PTY handling routes through explicit preclear/redraw policy pipeline helpers plus state-update application helpers, and completed the writer-state decomposition target (`writer/state.rs` now 448 lines across dedicated `state/*` modules), so Step 2f is the next scope. 2026-03-04 post-closure governance audit added immediate Step-2f tightening scope: new Step 2f.1 (allowlist burn-down + shape-budget reset), Step 2f.2 (function-size guardrails for dispatcher/pipeline hotspots), and explicit Phase-4 compatibility-governance kickoff (`ide_provider_matrix.yaml`, `check_compat_matrix.py`, `compat_matrix_smoke.py`, `devctl compat-matrix`) directly after Step-2f closure. 2026-03-04 CP-013 closure landed: Step 2f/2f.1/2f.2 are now implemented with blocking isolation defaults, narrowed explicit allowlists, tightened shape budgets, function guardrails with owner/expiry exceptions, and the Phase-4 compatibility governance scaffold is active. 2026-03-04 post-CP-013 hardening slice landed: isolation scanner now catches host-enum + provider-backend helper coupling patterns without broad helper-name false positives, runtime mixed-condition callsites in writer render/dispatch/redraw were rerouted through runtime-profile and canonical compatibility helpers, prompt hotspots were reduced under hard limits (`prompt_occlusion.rs` 1143 and `claude_prompt_detect.rs` 623 via test-module extraction), and lint-debt guard now detects inner `#![allow(...)]` attributes with dedicated regression coverage. 2026-03-04 Phase-3a prompt strategy wiring landed: prompt detector construction now routes through provider adapters with Claude-owned strategy ownership plus temporary legacy-shim parity fallback; CI/runtime/docs governance bundle remains green. 2026-03-04 checkpoint/state sync: `CP-016` docs/state continuation sync is in progress; Step `3a.1` (legacy-shim retirement) is closed, Step `3c` is closed, Step `3b` is now closed (Steps `3e` and `3f` are closed), and Phase-5/Phase-6 closure gates (AntiGravity decision + ADR lock) remain pending. 2026-03-05 Phase-5 defer decision: AntiGravity moved to deferred scope until runtime host fingerprint evidence exists; active MP-346 host matrix scope is now `cursor`/`jetbrains`/`other`. 2026-03-05 Phase-6 governance closure landed: ADR `0035` and ADR `0036` are accepted and indexed, leaving IDE-first `CP-016` manual matrix closure (`4/4`) complete for release scope, with deferred `other`/`gemini` validation tracked as post-next-release backlog. 2026-03-04 additional CP-016 hardening landed: IPC lifecycle routing now delegates through a dedicated provider lifecycle adapter module and isolation guardrails now enforce file-scope coupling detection with explicit temporary allowlist debt for Step-3b hotspot files.)
- [ ] MP-347 Add an execution router for pre-push checks and tighten dead-code debt governance across Rust runtime/tooling paths. (2026-03-05 PR-1 landed: added `devctl check --profile fast` as a compatibility alias of `quick` and updated command/docs surfaces. 2026-03-05 PR-2 landed: added `devctl check-router` with changed-path lane selection (`docs`, `runtime`, `tooling`, `release`), strict unknown-path escalation to tooling lane, risk-add-on detection from AGENTS risk-matrix signals, and optional `--execute` mode that runs routed bundle commands. 2026-03-05 dead-code governance slice landed: `check_rust_lint_debt.py` now inventories dead-code allows and supports policy flags (`--report-dead-code`, `--fail-on-undocumented-dead-code`, `--fail-on-any-dead-code`), AI guard runs now include dead-code reporting, and all current runtime dead-code allow attributes carry explicit rationale metadata. 2026-03-05 PR-3 landed: command bundles moved into canonical `dev/scripts/devctl/bundle_registry.py`; `check-router` and `check_bundle_workflow_parity.py` now consume registry commands and AGENTS bundle blocks are rendered/reference-only. 2026-03-05 PR-4 landed: heavy-check placement formalized in maintainer docs (`prepush`/`release`/CI remain strict; `fast`/`quick` stay local-only minimal lanes). 2026-03-05 PR-5 landed: AGENTS rendered bundle docs are now auto-validated/regenerable via `check_agents_bundle_render.py` and strict-tooling docs gate wiring. 2026-03-05 post-implementation architecture audit reopened remaining scope: current `check_code_shape.py` merge-blockers (`check_router.py` and `docs_check_support.py` growth), router/docs-governance taxonomy duplication, risk-add-on SSOT drift risk, and missing `jscpd` report evidence in `check_duplication_audit.py` must be resolved before re-closing this MP. 2026-03-05 phase-1 closure cleanup landed: shape blockers are resolved via check-router/docs-check decomposition, `check_duplication_audit.py` now emits explicit `status`/`blocked_by_tooling` evidence fields plus an explicit constrained-environment fallback (`--run-python-fallback`) while preserving `jscpd` as primary, canonical `jscpd` report evidence is refreshed (`dev/reports/duplication/jscpd-report.json`), and the closure non-regression command pack is green; remaining MP-347 follow-up is taxonomy/SSOT hardening. 2026-03-05 verification refresh: canonical helper ownership for duplication audit is now stable (`check_duplication_audit_support.py`), stale archive literals were removed from active docs/changelog, and the row `2331` non-regression pack rerun remains fully green. 2026-03-06 docs-IA intake update: Round 4 developer-information-architecture + active-directory hygiene audit is now tracked in `dev/active/pre_release_architecture_audit.md` (Phase 15) and remains open pending migration implementation. 2026-03-06 docs-index follow-up: reduced duplicate entrypoint drift by making `dev/README.md` the explicit canonical developer index and converting `DEV_INDEX.md` into a thin bridge page. 2026-03-06 guide-path migration follow-up: moved durable maintainer guides to `dev/guides/` with one-cycle bridge files at legacy paths and updated mapped coupling surfaces (`docs_check_policy`, `check_router_constants`, `tooling_control_plane.yml`, AGENTS/README entrypoints, and docs-check/path-rewrite tests). 2026-03-08 maintainer-lint follow-up: add an explicit advisory `pedantic` `devctl check` profile, keep it out of required bundles and release gates, and document it as an opt-in lint-hardening sweep so agents use it intentionally instead of treating pedantic noise as mandatory release work. 2026-03-08 pedantic follow-up: keep pedantic on the existing `report`/`triage` architecture by having `check --profile pedantic` emit structured artifacts under `dev/reports/check/`, `report --pedantic` / `triage --pedantic` consume those artifacts through the shared project snapshot, support explicit inline regeneration via `--pedantic-refresh`, and use `dev/config/clippy/pedantic_policy.json` to record promote/defer/review decisions so AI classification is repo-owned instead of ad hoc per release. 2026-03-08 maintainability/IA follow-up: Phase-15 cleanup remains open for retiring temporary bridge entrypoints like `dev/ARCHITECTURE.md` and `dev/BACKLOG.md`, collapsing duplicate `dev/` entrypoints, and turning AGENTS trimming into a real post-release execution slice instead of a lingering note. 2026-03-09 guard follow-up: `check_rust_security_footguns.py` now also flags `unreachable!()` in hot runtime paths under `rust/src/bin/voiceterm/**`, `rust/src/audio/**`, and `rust/src/ipc/**`, with matching unit coverage, so the pre-push guard set keeps tightening around panic-shaped "should never happen" shortcuts in shipped runtime code.)
- [ ] MP-348 Investigate Codex composer/input-row occlusion after recent Codex CLI updates (reported 2026-03-05): during red/green diff-heavy output, IDE terminal sessions can show the backend input/composer row visually obscured near the HUD boundary. `Post-next-release only`; do not execute before release promotion unless explicitly reclassified as a blocker. Required evidence pack: one screenshot + `voiceterm --logs --codex` trace with terminal host/version, HUD style, terminal `rows/cols`, and overlap timing (`while working` vs `ready for input`). Initial code-audit hypothesis for follow-up validation: `terminal.rs` currently keeps Codex on a fixed v1.0.95 reserved-row budget (no extra safety-gap rows), and prompt-occlusion guard routing is presently Claude-only via `runtime_compat::backend_supports_prompt_occlusion_guard`, so Codex composer/card layout changes may bypass suppression and row-budget safeguards. Add targeted regression tests once logs confirm a deterministic repro.
- [ ] MP-349 Investigate Cursor+Claude plan-mode history/HUD corruption + transient garbled terminal output (reported 2026-03-05): in Cursor terminal sessions, asking Claude to enter plan mode (especially with local/background agents) can cause the visible history region to disappear while HUD/status UI rows render over output; some lines show garbled characters/symbols during the bad state. Repro clue from physical testing: issue clears after terminal resize/readjust, suggesting geometry/redraw synchronization drift. `Post-next-release only`; do not execute before release promotion unless explicitly reclassified as a blocker. Required evidence pack: before/after resize screenshots, terminal host/version, provider/backend, HUD style/mode, terminal `rows/cols` before and after resize, `voiceterm --logs` trace with `VOICETERM_DEBUG_CLAUDE_HUD=1`, and a timestamped sequence (`plan request -> corruption -> resize/readjust -> recovery`). Initial code-audit hypotheses: stale geometry cache, missed full-repaint transition, or prompt/HUD reserved-row mismatch in Cursor non-rolling flow. Add deterministic regression tests after a stable log-backed repro is confirmed.
- [x] MP-350 Keep `devctl` as primary control plane and add optional read-only
  MCP adapter without duplicate enforcement layers: locked release/check/cleanup
  semantics as executable contracts, documented MCP as additive (not a
  replacement), and closed the execution tracker into archive
  (`dev/archive/2026-03-05-devctl-mcp-contract-hardening.md`) while retaining
  durable guidance (`dev/MCP_DEVCTL_ALIGNMENT.md`, `dev/DEVCTL_AUTOGUIDE.md`,
  `dev/scripts/README.md`, `dev/ARCHITECTURE.md`).
- [ ] MP-351 Expand the built-in theme catalog with additional curated VoiceTerm
  themes, wire them through Theme Picker/Theme Studio/export surfaces, keep
  CLI/docs parity, and add snapshot coverage so new themes do not regress
  ANSI/256color fallback behavior.
- [ ] MP-352 Add slash-command control for voice modes so users can switch
  between `PTT`/manual voice, `AUTO`, and idle/listening-off flows without
  relying only on hotkeys; deliver `/voice` as a standalone command inside
  Codex CLI and Claude Code sessions without requiring the full VoiceTerm PTY
  overlay. Architecture audit (2026-03-06) confirmed PTY-based slash-menu
  injection is not viable; implementation path is phased: (A) `--capture-once`
  subprocess mode + markdown skill files for immediate `/voice` availability,
  (B) MCP server in Rust (`voiceterm-mcp`) exposing `voice_capture`,
  `voice_status`, `voice_mode_set` tools for both platforms, (C) Claude Code
  plugin packaging + Codex command file for native slash-menu UX. Execution
  spec: `dev/active/slash_command_standalone.md`. 2026-03-09 status: Phase A
  implementation is landed locally (`--capture-once --format text`, slash
  templates, user docs, targeted capture tests green), while full runtime
  validation remains open because current branch-wide guard/test failures are
  unrelated to the slash-command slice. Require manual validation of
  enable/disable/exit behavior before closure.
- [ ] MP-353 Add a settings toggle for momentary push-to-talk hotkey behavior
  ("hold to talk") so manual voice can run as either the current toggle model
  or a press-and-hold capture mode; wire the preference through Settings plus
  config/CLI surfaces, preserve current behavior by default, and require
  physical hotkey validation before closure.
- [x] MP-354 Execute post-release IDE/provider coupling remediation so the
  writer dispatch/timing/startup paths reduce cross-product blast radius before
  additional runtime feature work continues. Scope is tracked in
  `dev/active/ide_provider_modularization.md` Phase 7 (`Step 7a`-`Step 7f`):
  adapter-owned writer state split, `handle_pty_output` pipeline decomposition,
  redraw timing/policy de-tangling, `main.rs` startup decomposition, shared VAD
  factory ownership, and guard-script dedup follow-up with checkpoint packets.
  2026-03-07 status: `Step 7a`, `Step 7b`, `Step 7c`, `Step 7d`, `Step 7e`,
  and `Step 7f` complete (writer adapter-owned state split +
  `handle_pty_output` staged decomposition + runtime-variant timing/policy
  de-tangling + startup phase decomposition + shared
  `audio::create_vad_engine` ownership + guard bootstrap/helper dedup
  closure); queued follow-up `R8 + R9 + R10`, `R6 + R7 + R11`,
  `R12 + R13 + R18`, and residual low-risk `R14 + R15 + R16 + R17` are now
  complete, and Python residual follow-up `P11 + P12` is now complete as well
  (typed `RuleEvalContext`, `AppConfig::validate` helper split, grouped
  prompt-occlusion output signals, glyph-table style resolution,
  runtime/schema + style-schema macro dedup cleanup, parser control-byte
  dispatch helper extraction, wake-listener join lifecycle dedup, lookup-based
  wake send-intent suffix matching, named legacy UI color constants, typed
  `BannerConfig` ownership, render host-resolution threading cleanup,
  style-pack override state accessor dedup, UTC tooling/check report timestamp
  normalization, and explicit `SECONDS_PER_DAY` age-math constants). MP-354 is
  closed; the doc stays active only because post-next-release `MP-346` backlog
  items remain deferred there. Phase-7 priority queue remains closed.
- [ ] MP-355 Deliver a dedicated shared review-channel + staged shared-screen
  execution slice: extend the MP-340 control-plane direction with one
  review-focused packet/event contract (`review_event` append-only authority +
  `review_state` latest snapshot), standard projections (`json`, `ndjson`,
  `md`, `terminal_packet`), and a flat `devctl review-channel` action surface
  (`post`, `status`, `watch`, `inbox`, `ack`, `history`); render a shared
  VoiceTerm surface where Codex + Claude + operator lanes are visible
  together as one collaborative terminal-native workflow, keep separate
  PTY ownership in the initial phases while packets/staged drafts/peer
  awareness stay visible on that same surface, add the structured
  `check_review_channel.py` guard plus retention/audit integration in the same
  tranche, and keep `check_review_channel_bridge.py` as the temporary
  markdown-bridge guard while `code_audit.md` remains the active projection.
  Defer true concurrent shared-target-session writing until lock/lease,
  ack/apply, and audit guardrails are proven. Phase-0 design closure requires
  explicit reconciliation with MP-340 plus `ADR-0027`/
  `ADR-0028`, a lossless header mapping into Memory Studio's canonical event
  envelope, and one
  `context_pack_refs` contract for `task_pack` / `handoff_pack` /
  `survival_index` attachments. Early phases must emit
  `packet_posted|packet_acked|packet_dismissed|packet_applied` into the memory
  ingest path when capture is active and keep provider-specific attachment
  shaping routed through Memory adapter profiles instead of a review-only pack
  format. Current
  transitional operating mode uses repo-root `code_audit.md` as a sanctioned
  coordination-log projection with explicit ownership, poll cadence, current-
  state fields, and `check_review_channel_bridge.py` governance until the
  structured artifact path lands, and the final artifact model must remain
  compatible with memory/handoff compilation. Routed actions requested from the
  review lane must go through the same typed command catalog and shared
  approval/waiver engine used by operator buttons and controller surfaces; no
  review-specific raw shell or raw API bypass is allowed. 2026-03-09 bridge-
  hardening follow-up landed: rollover now rejects
  `--await-ack-seconds <= 0` so fresh-session ACK stays fail-closed, and the
  temporary `check_review_channel_bridge.py` guard now requires live
  `Last Reviewed Scope` plus a non-idle `Current Instruction For Claude`
  section whenever the markdown bridge is active. 2026-03-09 bridge-backed
  status follow-up landed: `devctl review-channel --action status` now writes
  current-latest projections under `dev/reports/review_channel/latest/`
  (`review_state.json`, `compact.json`, `full.json`, `actions.json`,
  `latest.md`, `registry/agents.json`), and rollover ACK detection now
  normalizes markdown list items correctly so live visible ACK lines are
  actually observed. 2026-03-09 launch/freshness follow-up landed: fresh
  conductor bootstrap now fails closed on untracked bridge files, stale
  reviewer polls beyond the five-minute heartbeat contract, and idle/missing
  live next-action state; the bridge liveness model now distinguishes
  `poll_due` vs `stale`, and rollover ACK validation now requires the exact ACK
  line inside the provider-owned bridge section (`Poll Status` for Codex,
  `Claude Ack` for Claude) instead of raw substring matches. 2026-03-09
  workflow-parity follow-up landed: `check_bundle_workflow_parity.py` now
  parses per-job run scopes, requires the tooling bundle sequence to stay in
  `docs-policy`, and requires the operator-console pytest lane to stay in
  `operator-console-tests` so wrong-job or out-of-order regressions fail
  closed instead of passing on command-presence alone. Codex re-review later
  the same day narrowed the bridge-hardening closure: `launch` still does not
  invoke the full bridge guard before bootstrap, freshness enforcement is
  still split between the five-minute heartbeat contract and a looser guard
  threshold, generated rollover prompts still hardcode the default ACK
  timeout instead of threading the selected value end-to-end, and one
  duplicate `test_review_channel.py` name still shadows intended coverage.
  Keep MP-355 open until those launch/freshness/ACK/coverage gaps are closed.
  2026-03-09 operator
  validation follow-up confirmed the current dirty-tree behavior: focused
  `test_review_channel` coverage passed (`31` tests), `devctl review-channel
  --action status --terminal none --format md` wrote the latest projection
  bundle successfully, and `launch` / `rollover` dry-runs remain expected-red
  while `code_audit.md` and `dev/active/review_channel.md` stay untracked
  bridge files in this checkout. A later 2026-03-09 fail-closed follow-up also
  closed the missing-`Claude Status` / missing-`Claude Ack` launch gap and
  stopped degraded `waiting_on_peer` bridge states from reporting `ok: true`
  or `claude.status == active` in review/mobile projections. A later same-day
  launcher follow-up also writes per-session metadata plus live-flushed
  conductor transcript logs under
  `dev/reports/review_channel/latest/sessions/` so repo-owned desktop shells
  can tail real session output without taking PTY ownership away from
  Terminal.app. Another same-day operator-blocker fix now clears inherited
  `CLAUDECODE` markers inside generated Claude conductor scripts so live
  Terminal-app launches do not fail as nested Claude Code sessions when
  started from an existing Claude-owned shell. A later 2026-03-09 Codex
  re-review also confirmed via focused `test_review_channel` coverage that
  custom `--await-ack-seconds` values are threaded end-to-end, so that older
  suspected ACK-timeout bug is no longer part of MP-355's open blocker set.
  A later same-day live-launch audit also found a new bootstrap honesty gap:
  non-dangerous Codex conductors can spend their first minutes on worker fan-
  out and approval-bound tool prompts before rewriting `Last Codex poll`,
  letting the bridge age into stale even while the session logs are active.
  The launcher prompt now requires Codex to stamp `Last Codex poll`, `Last
  non-audit worktree hash`, and `Poll Status` before fan-out and forbids
  parking silently on unanswered approval prompts without reflecting that
  blocked state in the bridge. A later same-day overlay/runtime follow-up also
  landed the first structured-authority consumer in the Rust shell: the Dev-
  panel Review surface now prefers event-backed review artifacts
  (`projections/latest/full.json`, `state/latest.json`, or legacy
  `latest/*.json` outputs) whenever review-channel event sentinels exist,
  parses those JSON projections into the same `ReviewArtifact` view model used
  by the existing markdown bridge, and falls back to `code_audit.md` only when
  structured state is absent. That proves the overlay can move onto canonical
  review state without changing default startup mode. A later same-day
  launcher hardening fix now refuses a second live `review-channel --action
  launch --terminal terminal-app` when the existing repo-owned
  `latest/sessions/` artifacts still look active, so operators cannot
  accidentally open duplicate Codex/Claude conductor windows that race on the
  same session-tail files, but the remaining
  event-backed `watch|inbox|ack|dismiss|apply|history` path is still open.
  Execution spec: `dev/active/review_channel.md`.
- [ ] MP-356 Tighten host-process hygiene automation so local AI/dev runs stop
  relying on manual Activity Monitor checks: add a dedicated host-side
  `devctl process-audit`/`devctl process-cleanup` surface, make the shared
  process sweep descendant-aware for leaked PTY child trees and orphaned-root
  cleanup descendants, update `AGENTS.md`/dev docs so post-test and pre-handoff
  host cleanup/audits are explicit, and close the remaining PTY lifeline
  watchdog leak so `cargo test --bin voiceterm theme` no longer sheds orphaned
  `voiceterm-*` helpers on the host. Follow-up widened the same audit/cleanup
  path to catch orphaned repo-tooling wrapper trees (for example stale
  `zsh -c python3 dev/scripts/...` roots with descendant helpers such as
  `qemu-system-riscv64`), direct shell-script wrappers, repo-runtime
  cargo/target trees from non-`--bin voiceterm` Rust tests, and repo-cwd
  generic helpers (`python3 -m unittest`, `node`/`npm`, `make`/`just`,
  `screen`/`tmux`, `qemu`, `cat`) that outlive their parent tree, while also
  excluding the current audit command's own ancestor tree. Follow-up synthetic
  leak repros tightened strict verification further: freshly detached
  repo-related helpers (`PPID=1`, still younger than the orphan age gate) now
  fail `process-audit --strict` / `process-cleanup --verify` immediately under
  a dedicated `recent_detached` state, and `process-watch` now exits zero once
  it actually recovers to a clean host instead of staying red because earlier
  dirty iterations are preserved in history. `check --profile quick|fast` now
  runs host-side cleanup/verify by default after raw cargo/test-binary
  follow-ups, and routed docs/runtime/tooling/release/post-push bundle
  authority ends with `process-cleanup --verify --format md` so the default
  AI/dev lane re-runs strict host cleanup automatically. Verified 2026-03-08
  with targeted PTY lifecycle tests, process-hygiene unit coverage, `cargo
  test --bin voiceterm theme -- --nocapture`, the required post-run quick
  sweep, strict host `process-audit`, live cleanup/verify of the orphaned
  repo-tooling `zsh -> qemu` tree, and live `process-watch` recovery from fresh
  synthetic repo-runtime + repo-tooling detached-orphan repros. Follow-up
  tracing closed one more live gap on 2026-03-08: banner tests no longer
  deadlock on nested env-lock acquisition, attached interactive helpers are no
  longer reported as stale repo-tooling failures, and AI-operated raw Rust
  tests now have a first-class `devctl guard-run` path that always executes
  the required post-run hygiene follow-up. Execution spec:
  `dev/active/host_process_hygiene.md`. 2026-03-09 Codex re-review reopened
  follow-up hardening: orphaned non-allowlisted repo-cwd descendants can
  still slip once the matched parent exits, tty-attached repo helpers
  (`python3 -m pytest` / `python3 -m unittest`) are still under-classified,
  and `guard-run --cwd <other-repo>` still audits/cleans this repo instead of
  the target cwd. Re-close only after focused regression proof covers those
  shapes.
- [ ] MP-357 Fix Claude/Cursor IDE overlay disappearing on terminal resize and
  when launching VoiceTerm in a terminal with pre-existing scrollback content:
  the HUD/status-line overlay can vanish or fail to render after a window resize
  event, and sessions started in terminals that already contain prior output
  sometimes never show the overlay at all. Reproduce both paths (resize-triggered
  disappearance and dirty-scrollback startup), capture `voiceterm --logs` traces
  with terminal host/version, `rows/cols` before and after resize, and scrollback
  line count at launch. Initial hypotheses: stale geometry cache not refreshed on
  SIGWINCH, or initial row-budget calculation not accounting for existing
  scrollback offset. Add deterministic regression coverage for both triggers
  before closure. `Post-next-release only`; do not execute before release
  promotion unless explicitly reclassified as a blocker.
- [ ] MP-358 Harden the local-first continuous Codex-reviewer / Claude-coder
  loop before any reusable template extraction: keep `MASTER_PLAN` plus the
  relevant active-plan checklist as the canonical queue, require automatic
  next-task promotion while scoped work remains, add peer-liveness/stale-peer
  guardrails so neither side keeps working blindly after the other goes stale,
  modularize and clean up the Python launcher/orchestration path with explicit
  failure-report coverage, rotate both conductor terminals through repo-visible
  handoff state once remaining context drops below 50%, and keep host-process
  hygiene green during relaunch/rotation so stale local test or conductor
  sessions do not accumulate detached repo processes. Only after this loop is
  proven stable on VoiceTerm should the same path be carved into a reusable
  toolkit/template. 2026-03-09 Codex re-review confirmed the report-level
  liveness state machine and fail-closed zero-second ACK rejection. The latest
  launcher slice now also supervises clean provider exits so conductors relaunch
  in-place instead of silently dying after one summary. A follow-up MP-358
  tranche also taught host hygiene/process-audit to keep attached supervised
  review-channel conductors visible without classifying them as stale leaks, and
  landed a typed `review-channel --action promote` path plus derived-next-task
  status projections so queue advancement is no longer ad hoc bridge editing.
  The latest launcher hardening slice also adds a typed
  `--refresh-bridge-heartbeat-if-stale` self-heal path for launch/rollover so
  stale reviewer-heartbeat metadata no longer strands the operator at a dead
  `Last Codex poll` guard failure when the rest of the bridge contract is
  still valid.
  The remaining open gaps are end-to-end auto-promotion proof, the 2-3 minute
  poll / five-minute heartbeat contract, and stale-peer recovery. Execution
  spec: `dev/active/continuous_swarm.md`.
- [ ] MP-359 Deliver a bounded optional PyQt6 VoiceTerm Operator Console for
  the current review-channel workflow: keep Rust as the PTY/runtime owner,
  keep `devctl review-channel` as the launcher/control surface, render Codex +
  Claude + Operator Bridge State side by side from repo-visible artifacts, and
  provide desktop launch/rollover plus operator decision capture without
  introducing a second control plane. Phase 1.5 (information hierarchy)
  landed: structured `KeyValuePanel` + `StatusIndicator` + toolbar dots
  replace text dumps, `widgets.py` extracted, 67 tests passing. Phases 3-8
  roadmap added: Approval Queue Center Stage, Agent Timeline, Guardrails /
  Kill Switch, System Health, Diff Viewer, and Validation. Phase 2.6 now has
  a concrete directory layout plan (`state/`, `views/`, `theme/`) to organize
  modules before more panels land. The Activity tab now exposes card-based
  agent summaries, typed quick actions (`review-channel --dry-run`,
  `status --ci`, `triage --ci`, `process-audit --strict`), selectable
  human-readable report topics, and staged Codex/Claude summary drafts with
  explicit provenance while keeping command execution on the shared repo-owned
  path. The next AI-assist tranche now explicitly includes an opt-in live
  provider-backed `AI Summary` path for the selected report, with bounded
  Codex/Claude execution, explicit provenance, repo-visible diagnostics, and a
  staged-draft fallback when live provider access is unavailable. The next
  operator-control tranche now
  explicitly includes a one-click `Start Swarm` flow plus direct typed yes/no
  and terminal-control buttons once the `review-channel` action surface grows
  beyond `launch|rollover`, plus a first-class CI/CD status + workflow/log
  visibility panel built on the existing `devctl` surfaces, push-linked run
  history, and an allowlisted script/action palette with AI-assisted action
  selection that still resolves to typed repo-owned commands. The same tranche
  has now landed its first operator-visible pieces: `Start Swarm` exposes
  JSON preflight -> live launch chaining with staged
  preflight/launch/running/failure status on Home + Activity, shared busy-state
  wiring, and command previews, and a new `Workbench` layout adds snap presets
  over resizable lane/report/monitor panes. The latest MP-359 follow-up also
  routes `Dry Run`, `Live`, `Start Swarm`, and `Rollover` through the typed
  review-channel stale-heartbeat self-heal path so the desktop shell no longer
  looks inert when the markdown bridge ages out, and now persists the selected
  layout/workbench tab/splitter state to
  `dev/reports/review_channel/operator_console/layout_state.json` so "screen
  got weird" reports stay reproducible. A follow-up in the same lane now adds
  explicit layout reset/export/import controls plus a new Workbench timeline
  surface that synthesizes per-agent/system events from snapshot + rollover
  handoff artifacts while keeping Raw Bridge as a dedicated tab. A further
  same-day Phase-4.5 slice adds shared workflow chrome to Workbench with a top
  strip (slice/goal/current writer/branch/swarm health), Codex/Claude last
  seen/applied markers, and a bottom posted->read->acked->implementing->tests
  ->reviewed->apply transition row with a script-derived next-action footer.
  The same tranche
  now explicitly includes a GUI swarm-planner surface that reuses
  `autonomy-swarm` / `swarm_run` token-aware sizing logic and feedback signals
  instead of inventing a desktop-only heuristic, plus a visible swarm
  efficiency governor that logs the metrics and control decision behind every
  hold/downshift/upshift/freeze/repurpose action. The same MP now also tracks
  a layout-workbench path for snap-aware pane resizing/repositioning plus a
  multi-theme registry meant to converge on Rust overlay theme/style-pack
  semantics instead of becoming a desktop-only styling fork, with explicit
  style-pack import/read parity first and export/write parity only after the
  desktop mapping is proven round-trip-safe. The plan now also explicitly
  includes a repo-aware Command Center, built-in `What this does / When to use
  it / Before you run it / What it will execute / Success / Failure` guidance
  surfaces, repo-state workflow modes (`Develop`, `Review`, `Swarm`,
  `CI Triage`, `Release`, `Process Cleanup`, `Docs/Governance`), and an
  integrated `Ask | Stage | Run` AI-help contract so the desktop app can
  answer questions, stage commands or draft artifacts, and execute the same
  typed repo-owned actions through both manual and AI-assisted paths. 2026-03-09 follow-up hardening
  landed: the live app and theme editor now share one stylesheet compositor,
  `bundle.tooling` now runs the operator-console suite in the canonical local
  proof path, and the GUI launcher now uses `sys.executable` instead of a bare
  `python3` shell assumption. The same tranche now also includes a fuller
  left-anchored theme workbench with `Colors` / `Typography` / `Metrics`
  pages, a real preview gallery, and tokenized typography/radius/padding
  styling so the editor can theme more than just raw color swatches.
  The latest workflow-controller hardening follow-up now makes `Run Loop`
  audit `devctl orchestrate-status` before it launches
  `devctl swarm_run --continuous`, and the shared Home/Activity launchpads
  keep the last audit/loop result inline so operators do not have to dig
  through raw launcher text to see whether the selected markdown scope is
  blocked, launching, or complete.
  2026-03-09 theme-authority follow-up landed: `ThemeState` now carries
  optional builtin `theme_id` identity, `ThemeEngine` is the single
  builtin/custom/draft apply authority, the toolbar reflects draft/custom
  state explicitly instead of keeping a parallel builtin-only truth, and
  detail dialogs now use live engine colors. The same bounded fix also
  repaired an accidental Operator Console import break in `views/widgets.py`
  and the local proof path is green aside from the known bridge-guard
  expected-red on untracked `code_audit.md` / `dev/active/review_channel.md`.
  A later 2026-03-09 saved-theme compatibility fix hydrated legacy partial
  `_last_theme.json` and custom preset payloads onto the current semantic
  palette before apply, closing the PyQt6 startup crash on missing keys such
  as `toolbar_bg`.
  The first follow-up after that crash also moved the agent-detail diff pane
  off fixed RGB highlight tints and back onto the live theme palette, closing
  one of the remaining hardcoded desktop surfaces called out by MP-359.
  A further same-day continuation split the editor into surface-scoped
  `Surfaces` / `Navigation` / `Workflows` pages and expanded the in-editor
  preview to cover toolbar/header chrome, nav + monitor tabs, approval queue,
  diagnostics/log pane, diff pane, and representative empty/error states so
  the next theme passes can touch more of the real shell without guessing.
  The next bounded parity slice is now landed too: the desktop theme engine
  can read canonical style-pack JSON payloads plus theme-file TOML metadata,
  hydrate only the shared Rust `base_theme` onto the matching builtin desktop
  palette, and surface provenance plus explicit `Not yet mapped` reporting for
  Rust-only fields such as `overrides`, `surfaces`, `components`, and
  non-`meta` theme-file sections. Export/write parity remains intentionally
  open until that broader cross-surface contract is proven stable.
  A follow-up bounded write slice is now in too: the desktop editor can export
  canonical theme-file TOML and minimal style-pack JSON only when the current
  state still maps exactly to a shared builtin `base_theme`, while lossy
  desktop-only edits stay blocked with explicit messaging instead of fake
  canonical files. The same slice split theme state/storage/overlay parity
  helpers out of `theme_engine.py` so the coordinator no longer keeps growing
  into another mixed-responsibility desktop god-file.
  A further bounded cleanup then removed another obvious pocket of desktop-only
  literals: agent-detail diff fallback colors now resolve from the shared
  builtin semantic palette, and the theme-editor color swatch derives its own
  border/hover chrome from the active swatch instead of fixed hardcoded
  accent/border values. The broader remaining work is still the larger
  hardcoded-surface sweep across the rest of the desktop shell.
  The next same-day sweep narrowed that remaining shell work further by
  removing shared stylesheet RGBA literals from menu hover/border and
  scrollbar track chrome. Those values now derive from semantic theme colors
  (`hover_overlay`, `menu_border_subtle`, `scrollbar_track_bg`) materialized
  by the shared palette builder and exposed in the desktop editor, so later
  cleanup can target only component-specific hardcoded pockets instead of
  generic shell overlays. A final same-day cleanup then removed the last real
  user-facing literal fallback still left in the live theme/view path:
  `agent_detail.py` now falls back to the builtin semantic `text` color when a
  supplied theme value is invalid instead of dropping to raw white, leaving
  only seed data, example payload text, and generic contrast helpers as
  remaining literal hits in the desktop theme tree. One more bounded helper
  follow-up then removed those generic helper escapes from the live editor
  path too: theme-editor swatch buttons now derive contrast text and
  border/hover chrome from the active theme's `text`/`bg_top` colors instead
  of raw black/white constants, so the remaining literal hits are limited to
  palette seed data and example payload text rather than live component
  chrome.
  2026-03-09 screenshot-hardening follow-up landed: wrapped bridge panes now
  avoid the misleading lower-left scrollbar-handle affordance on the common
  read path, non-diff markdown is no longer painted as removal text in agent
  detail dialogs, provider badges and broader tooltips are visible in the
  chrome, in-window `Help` / `Developer` menus now explain the workflow
  without kicking operators out to repo docs, and the theme editor import page
  now explains current import/highlight semantics inline. 2026-03-09 home/read
  follow-up landed too: the app now opens on a guided `Home` launchpad instead
  of dropping directly into raw dashboards, and a shared `Read` mode switch
  now flips report/footer wording between simple and technical modes while
  feeding the same selected source report into staged AI drafts. A later
  2026-03-09 density/mobile-parity follow-up replaced stale Home/Analytics
  filler with repo-owned git/mutation/CI summaries plus read-only
  `phone-status` parity over the same payload planned for iPhone-safe
  surfaces, tightened sidebar/button density, and documented
  `integrations/code-link-ide` as a future reference adapter rather than a
  runtime dependency of the desktop shell. Next slice: expand
  the editor into fuller page-scoped controls for text/borders/buttons/nav/
  approvals/log panes, and push the remaining hardcoded desktop surfaces onto
  the shared token/preview path so the console can theme nearly the full UI
  without widening into a second control plane. Codex re-review later the same
  day narrowed the current closure: the theme-authority split is resolved, but
  live-launch portability/docs honesty, analytics/CI honesty, real
  startup/mutating-path proof, launcher-script execution coverage, and
  checklist/progress consistency remain open before MP-359 can be called
  green. A further bounded Step-6 follow-up is now closed too: the approval
  queue no longer vanishes when empty and instead keeps a visible `0 Pending`
  zero-state so operators retain the center approval affordance even before
  the larger `ApprovalSpine` card migration lands. Another same-day bounded
  technical-density follow-up then made `Read -> Technical` visually real
  instead of prose-only: the PyQt6 Home and Activity surfaces now switch to
  denser terminal-style digest framing with smaller toolbar-first guidance and
  monospace digest/read panes, addressing operator feedback that the shell was
  still too banner-heavy for a command-center workflow. A further same-day
  session-surface follow-up then fixed the next real live-tail gap: the
  desktop no longer crams terminal text, session metadata, and registry rows
  into one pane. `session_trace_reader.py` now keeps separate readable history
  plus current-screen snapshots while filtering private-CSI parse junk and
  `thinking with high effort` spinner noise, and the Workbench/Monitor/Sidebar
  session surfaces now render a large terminal-history pane with smaller
  stats/screen + registry support below so the lower deck carries useful live
  signal instead of blank space. A later same-day operator-feedback follow-up
  tightened that contract again: live session panes now prefer the
  reconstructed visible terminal screen over the noisier raw history stream
  whenever a `script(1)` trace is available, truncated tail reads align to the
  next line boundary so partial ANSI/control fragments do not leak into the
  UI, and the lower `Stats` / `Registry` pair is now one double-click
  flippable card per provider instead of two cramped panes. The next bounded
  follow-up then moved the default shell back onto a card-first snap-aware
  Workbench: visible preset pills returned, the three lane cards stay on
  screen together, launcher/bridge/diagnostics now render side by side
  instead of behind workbench tabs, and always-visible helper copy was
  compacted so terminal surfaces dominate. The next operator-feedback slice
  then restored explicit `Codex Session` and `Claude Session` panes backed by
  the review-channel full projection's agent registry plus bridge state, and
  the default Workbench now uses a top-row `Codex Session | Operator Spine |
  Claude Session` split with raw logs/digests below so the shell shows what
  each side is doing again without pretending those panes are live PTY
  emulators. The next same-day cleanup then grouped that lower deck by job
  instead of leaving every card visible at once: Workbench now uses
  `Terminal`, `Stats`, `Approvals`, and `Reports` tabs so launcher streams,
  repo stats, decision routing, and digest/draft work each live on one
  focused surface. The next operator-feedback follow-up then pushed that idea
  through the whole Workbench instead of keeping a fixed session strip above
  it: `Sessions`, `Terminal`, `Stats`, `Approvals`, and `Reports` are now
  full-page task tabs, so the streaming session row is its own focused page
  and the workbench tabs sit at the top of the surface instead of in the
  middle of the layout. The next same-day live-session follow-up then made
  those `Codex Session` / `Claude Session` panes prefer real tailed launch
  transcripts from `dev/reports/review_channel/latest/sessions/` whenever the
  review-channel launcher has emitted them, while keeping the prior
  full-projection bridge/registry digest as the honest fallback when no live
  log exists yet. A same-day Theme Editor follow-up then repurposed the right
  rail from an always-on preview gallery into `Quick Tune`, `Coverage`, and
  optional `Preview` tabs, and restyled the operator toolbar action buttons
  toward flatter dashboard/instrument-panel chrome. A later same-day theme
  tranche then promoted the editor from colors/tokens into a fuller theme
  contract with persisted `components` + `motion` settings, component-style
  families for borders/buttons/toolbar chrome/inputs/tabs/surfaces, new
  `Components` and `Motion` authoring pages, and a real preview playground for
  front/back card swaps plus pulse feedback so motion controls are no longer
  just roadmap copy. The next explicit planning follow-up now captures the
  remaining density/scale-up work too: chart-backed repo analytics and
  mutation/hotspot views, 4/6/8+ snap-aware multi-agent layouts, read-only
  split/combined lane terminal monitors, broader tooltip/help saturation, and
  richer QSS/theme-pack import plus semantic-highlight controls that keep
  normal report content from reading like an error state. Current stopping
  point: Cursor lane wiring now reaches the Activity summary cards and quality
  reports can emit live review-channel `finding` packets; follow-on cleanup of
  the architecture/memory/guardrail primer content is parked as an explicit
  backlog item in `dev/active/operator_console.md` Phase 4.7.
  (directory reorg) then Phase 3 (approval queue center stage), with `Start
  Swarm`, typed control wiring, and CI visibility tracked in parallel.
  Execution spec:
  `dev/active/operator_console.md`.

- [x] MP-360 Wire AI-driven remediation into Ralph loop: create
  `ralph_ai_fix.py` with Claude Code invocation, false-positive filtering,
  architecture-specific validation (Rust/PyQt6/devctl/iOS), approval-mode
  support, and commit/push automation. Update policy allowlist and workflow
  default fix command. Add cross-architecture guard enforcement policy to
  `AGENTS.md` and wire 7 new guard scripts into `tooling_control_plane.yml`.
- [ ] MP-361 Create guardrail configuration registry
  (`dev/config/ralph_guardrails.json`) mapping finding categories to AGENTS.md
  standards, documentation links, and AI fix skills so the AI brain has
  context for each finding class.
- [ ] MP-362 Emit structured guardrail report (`ralph-report.json`) from AI fix
  wrapper with per-finding status, standards refs, fix skills used, and
  aggregate analytics (fix rate, by-architecture, by-severity, false-positive
  rate).
- [ ] MP-363 Add `devctl ralph-status` CLI command with SVG charts (fix rate
  over time, findings by architecture, false-positive rate), data-science
  integration, and phone status projection.
- [ ] MP-364 Add operator console Ralph dashboard (PyQt6 widget with finding
  table, progress bars, guard health indicators, and control buttons for
  start/pause/resume/configure).
- [ ] MP-365 Integrate Ralph loop metrics into phone/iOS status views (compact
  phase/fix_rate/unresolved fields, start/pause/configure actions, and iOS
  MobileRelayViewModel display).
- [ ] MP-366 Deliver unified guardrail control surface
  (`ralph_control_state.json`) so devctl CLI, operator console, and phone app
  all read/write the same start/pause/configure/monitor state with policy
  gates and audit logging.
- [ ] MP-367 Add `check_ralph_guardrail_parity.py` guard to verify every entry
  in `AI_GUARD_CHECKS` has a step in `tooling_control_plane.yml`, a row in
  `ralph_guardrails.json`, and a skill mapping — closing the loop so new
  guards are automatically wired into the full pipeline.
  Execution spec: `dev/active/ralph_guardrail_control_plane.md`.
- [x] MP-368 Implement `probe_concurrency` so heuristic review probes can flag
  async/shared-state race signals without blocking CI.
- [x] MP-369 Implement `probe_design_smells` so Python AI-slop patterns such as
  heavy `getattr()` density and formatter sprawl become typed review targets.
- [x] MP-370 Implement `probe_boolean_params` so unreadable multi-bool
  signatures in Python and Rust are surfaced before they calcify into APIs.
- [x] MP-371 Implement `probe_stringly_typed` so string-dispatch paths that
  should become enums/contracts are surfaced as explicit review hints.
- [x] MP-372 Land the shared review-probe framework (`probe_bootstrap.py`,
  shared schema/utilities, probe registration, and check-profile integration).
- [x] MP-373 Wire the first end-to-end review-probe path with tests and
  non-blocking `devctl check` integration.
- [x] MP-374 Deliver the expanded review-probe catalog plus aggregated
  `devctl probe-report` / `status --probe-report` / `report --probe-report`
  surfaces and stable `review_targets.json` output. Remaining follow-up is
  operator-facing ranking/baselines and deeper probe-specific regression
  coverage, not initial plumbing.
- [ ] MP-375 Shift review-probe next work to operator-first adoption:
  ranking/baselines, self-contained senior-review packets, connectivity-aware
  hotspot scoring, changed-subgraph / hotspot visuals, governance parity, and
  optional operator-console review dashboards. 2026-03-10 follow-up:
  `devctl triage --probe-report` now promotes aggregated probe debt into
  routed issues/next actions, and local `loop-packet` fallback requests the
  same probe summary so packets stay probe-aware even without a prior
  artifact. Later 2026-03-10 follow-up: `devctl probe-report` now emits ranked
  hotspot scoring, `file_topology.json`, `review_packet.{json,md}`, and
  Mermaid/DOT hotspot views, while `status` / `report` / `triage` consume the
  same ranked hotspot summary. A first cleanup pass using that packet reduced
  live findings from 23 across 18 files to 18 across 14 files. Control-plane
  or Ralph adapters stay later and should build on the same stable probe
  artifacts. Latest follow-up: maintainer governance docs now explicitly tell
  AI when to run `check --profile ci`, `probe-report`, and `guard-run`, and
  document the topology/review-packet artifacts emitted by the probe stack.
  Latest portability follow-up: built-in guard/probe capability metadata now
  lives in `devctl/quality_policy_defaults.py`, repo-local
  enablement/default args now live in `dev/config/devctl_repo_policy.json`,
  and `check` / `probe-report` resolve active steps from the
  `quality_policy*.py` policy stack so the current behavior is preserved here
  while the engine moves toward repo-portable presets. Latest preset
  follow-up: VoiceTerm now extends reusable portable presets under
  `dev/config/quality_presets/`, VoiceTerm-only matrix/isolation guards live
  behind the repo-specific preset instead of the portable fallback, and
  `check` / `probe-report` plus probe-backed `status` / `report` / `triage`
  all accept `--quality-policy`; `DEVCTL_QUALITY_POLICY` provides the same
  automation override, and `devctl quality-policy` now renders the resolved
  policy/scopes so maintainers can validate another repo policy without
  editing orchestration code. Latest scope follow-up: scan roots are no longer baked
  into the standalone Python/Rust guard+probe scripts; the repo policy now
  owns `python_guard_roots`, `python_probe_roots`, `rust_guard_roots`, and
  `rust_probe_roots`, and probe-report artifacts surface those resolved roots
  for operator review. Latest portable-guard slices now ship
  `check_python_suppression_debt.py`, `check_python_design_complexity.py`, and
  `check_python_cyclic_imports.py` as default portable Python guards, while
  default-argument traps route through the expanded
  `check_python_global_mutable.py` guard. Latest portability follow-up:
  `check_code_shape.py` namespace/layout rules now resolve from repo-policy
  guard config instead of VoiceTerm-only hard-coded tuples. Next portable
  hard-guard backlog now narrows to Rust `result_large_err` /
  `large_enum_variant` evaluation.
  Execution spec: `dev/active/review_probes.md`.

- [ ] MP-376 Build the portable code-governance engine + evidence corpus:
  keep the guard/probe/report stack reusable across arbitrary repos without
  engine edits, define the boundary between engine code, portable presets, and
  repo-local policy, capture guarded coding episodes as evaluation data
  (initial output, guard hits, repair loops, accepted diff, human edits, test
  and later-review outcomes), keep the adjudicated finding ledger
  (`governance-review`) current so false-positive and cleanup rates are visible
  in `data-science`, keep first-run onboarding (`governance-bootstrap` +
  `--adoption-scan`) and export flows reusable across arbitrary repos, and
  keep mining repeated low-noise pattern families from live evidence before
  promoting more hard guards. The first external pilot (`ci-cd-hub`) is now
  complete; remaining scope is benchmark automation, active cleanup against the
  evidence log, more pilot-proof engine cleanup, and evidence-driven next
  pattern selection while holding guard code to the same or stricter
  structural standard as guarded code. Execution spec:
  `dev/active/portable_code_governance.md`. Latest CI-parity follow-up
  (2026-03-11): GitHub exposed that `dev/config/devctl_repo_policy.json` and
  the portable preset JSON files were still ignored local artifacts, so local
  validation and CI were resolving different guard/probe sets. The policy/preset
  files are now tracked repo assets, maintainer docs explicitly call out that
  policy changes must be committed, pre-commit CI is narrowed to changed files,
  the tooling-control-plane mypy env export bug is fixed, iOS CI now runs on
  `macos-15` for Swift 6 / newer Xcode project compatibility, and the current
  maintainer-lint redundant-closure regressions are burned down. Latest
  publication-sync follow-up: refreshed the external
  `terminal-as-interface` paper snapshot from committed VoiceTerm HEAD and
  recorded the new baseline in `dev/config/publication_sync_registry.json`
  (`source_ref=4deb8ec8f8c3709f1fb35955f9763c6147df6a95`,
  `external_ref=9cf965f`), returning `check_publication_sync.py` to zero drift.
  Latest PR-gate follow-up (2026-03-12): the remaining GitHub-only failures on
  PR #16 are burned down locally by making `process_sweep` fixtures checkout-
  agnostic, pinning review-channel stale-poll tests to explicit freshness
  policy, clearing leaked runtime/style-pack overrides from the startup-banner
  fallback test, switching iOS `xcode-build` to the generic simulator
  destination, and taking the changed-file `pre-commit` lane back to green.
  Latest closure pass (2026-03-12): the next rerun exposed real local
  portability debt instead of more GitHub workflow drift, so `devctl` now
  keeps repo-owned Python subprocesses on the invoking interpreter,
  compatibility exports are restored for split modules
  (`quality_policy`, `collect`, `status_report`, `triage/support`,
  `check_phases`, `check_python_global_mutable`), and new support modules for
  phone-status plus Activity-tab report helpers pull the touched Python files
  back under code-shape/function-duplication limits without changing behavior.
  Latest probe-cleanup follow-up (2026-03-12): the remaining working-tree
  review hints are now burned down too. `autonomy/phone_status.py` uses a
  typed `RalphSection` boundary instead of anonymous dict helpers,
  `mobile_status_views.py` now delegates typed payload/view support to the new
  `mobile_status_projection.py` module so the renderer stays below its
  code-shape cap, `loop_packet_helpers.py` uses `LoopPacketSourceCommand` for
  the last auto-send string dispatch, the probe packet rerun is clean, and the
  governance ledger is updated with six additional `fixed` probe rows.
  Latest push-repair follow-up (2026-03-12): the first rerun on the refreshed
  PR caught a real changed-file `pre-commit` regression where Ruff had stripped
  compatibility exports still used across the repo. Those re-export seams are
  now restored compactly in `common.py`, `status_report.py`, `collect.py`,
  `triage/support.py`, `commands/check_phases.py`, `process_sweep/core.py`,
  `phone_status_view_support.py`, `quality_policy.py`,
  `check_python_global_mutable.py`, and `probe_report_render.py`; `common.py`
  stays back under its shape cap; changed-file `pre-commit` is green locally
  again; and the full `dev/scripts/devctl/tests` suite reran at
  `1184 passed, 4 subtests passed`.
  Latest docs-governance follow-up (2026-03-12): strict-tooling drift is
  closed too. `AGENTS.md`, `dev/guides/DEVELOPMENT.md`, and
  `dev/scripts/README.md` now document that staged `dev/scripts/**` module
  splits must keep compatibility re-exports until repo importers, tests,
  workflows, and pre-commit hooks migrate together. After refreshing the
  review-channel heartbeat, `docs-check --strict-tooling` and the full
  canonical `bundle.tooling` replay are green again under `python3.11` on the
  local workstation, including `397 passed, 181 skipped` in the Operator
  Console suite and a clean `process-cleanup --verify`.
  Latest CI-runner parity follow-up (2026-03-12): the next GitHub rerun
  exposed two environment-sensitive Python regressions plus one operator-
  console timing bug, and they are now burned down locally. Review-channel
  bridge session generation no longer hard-fails when the default resolver
  cannot find `codex`/`claude` on the current PATH before a dry-run or
  simulated launch script is even written, `triage-loop` now passes the
  command module's CI/connectivity predicates through its preflight helper so
  the existing non-blocking-local connectivity test holds under GitHub
  Actions, and `JobRecord.duration_seconds` clamps negative monotonic deltas
  to zero. The reproduced failure shapes are green locally, the full
  `dev/scripts/devctl/tests` suite reran at `1184 passed, 4 subtests passed`,
  and `app/operator_console/tests/` reran at `397 passed, 181 skipped`.

Control-plane program sequencing (maps to MP-330/331/332/336/338/340/355/360..367):

1. Ship canonical multi-view controller state projections (`full/compact/trace/actions`) from one packet source.
2. Add SSH-first/iPhone-safe read surfaces (`phone-status`) and Rust Dev-panel parity for run/agent/policy visibility.
3. Land the dedicated review-channel state/event contract and multi-format
   projections as a review-focused profile over the broader
   `controller_state` direction so reviewer/coder communication is packetized
   instead of living in hidden chat state.
4. Add a shared-screen VoiceTerm review surface that shows Codex, Claude, and
   operator lanes together while keeping early PTY ownership separate.
5. Keep desktop GUI clients non-canonical; allow only thin optional wrappers
   over Rust surfaces (`--dev`, future shared-screen review UI),
   `phone-status`, `controller-action`, and `devctl` APIs.
6. Add guarded operator actions (`dispatch-report-only`, `pause`, `resume`, `refresh`) with full audit logging.
7. Add reviewer-agent packet ingestion lane so loop-review feedback is machine-consumable, not manual copy/paste.
8. Add charted KPI trend surfaces (loop throughput, unresolved trend, mutation trend, automation-vs-AI mix) for architect decisions.
9. Add deterministic learning loop (`fingerprint -> playbook -> confidence -> guarded promote/decay`) with explicit evidence.
10. Promote staged write controls and any true shared-session mode only after replay protection + branch-protection-aware promotion guards are verified.

## Deferred Plans

- `dev/deferred/DEV_MODE_PLAN.md` (paused until Phases 1-2 outcomes are complete).
- MP-089 LLM-assisted voice-to-command generation (optional local/API provider) is deferred; current product focus is Codex/Claude CLI-native flow quality, not an additional LLM mediation layer.
- Post-next-release MP-346 backlog: stabilize Gemini startup/HUD flash behavior in `cursor` and `jetbrains` via adapter-owned policy paths (no new mixed host/provider branching outside adapter/runtime-profile ownership), with checkpoint + matrix evidence before closure.
- Post-next-release MP-346 backlog: investigate JetBrains+Claude non-regressive render-sync artifacts seen during long-output sessions (intermittent help/settings overlay flashing and duplicated bottom status-strip/HUD rows after short replies), capture focused logs/screenshots, and route fixes through adapter/runtime-profile ownership paths.
- Post-next-release MP-346 backlog: start AntiGravity reactivation readiness intake by defining runtime host fingerprint requirements and a compatibility-test design for `codex`/`claude`/`gemini` expectations before lifting deferred scope.
- Post-next-release MP-348 backlog: Codex red/green diff-era composer/input-row occlusion investigation is explicitly deferred until after release and requires logs+screenshot evidence before any runtime change.
- Post-next-release MP-349 backlog: Cursor+Claude plan-mode history/HUD corruption and transient garbled terminal output is explicitly deferred until after release; resize/readjust-driven recovery is a primary diagnostic clue for geometry/redraw synchronization investigation.
- AntiGravity host support is deferred until runtime fingerprint evidence
  exists; current release-scope MP-346 matrix closure is IDE-first
  (`cursor`, `jetbrains`), while `other` host validation is explicit
  post-next-release backlog.

## Release Policy (Checklist)

1. Confirm version parity and changelog readiness (`rust/Cargo.toml`,
   `pypi/pyproject.toml`, app plist, `dev/CHANGELOG.md`).
2. Run release verification bundle (`bundle.release`).
3. Run and wait for `release_preflight.yml` success for the exact target
   version/SHA.
4. Create/tag release from `master` only after same-SHA preflight success.
5. Monitor publish workflows (`publish_pypi`, `publish_homebrew`,
   `publish_release_binaries`, `release_attestation`) and verify PyPI payload
   (`https://pypi.org/pypi/voiceterm/<version>/json`).
6. Use local manual publish fallbacks only if workflows are unavailable.

## Execution Gate (Every Feature)

1. Create or link an MP item before implementation.
2. Implement the feature and add/update tests in the same change.
3. Run SDLC verification for scope:
   `python3 dev/scripts/devctl.py check --profile ci`
4. Run docs coverage check for user-facing work:
   `python3 dev/scripts/devctl.py docs-check --user-facing`
5. Update required docs (`dev/CHANGELOG.md` + relevant guides) before merge.
6. Push only after checks pass and plan/docs are aligned.

## References

- Execution + release tracking: `dev/active/MASTER_PLAN.md`
- Theme Studio architecture + gate checklist + consolidated overlay research/redesign detail: `dev/active/theme_upgrade.md`
- Memory + Action Studio architecture + gate checklist: `dev/active/memory_studio.md`
- Pre-release architecture/tooling cleanup execution plan: `dev/active/pre_release_architecture_audit.md`
- Consolidated full-surface audit findings evidence (reference-only): `dev/active/audit.md`
- Raw multi-agent audit merge transcript evidence (reference-only): `dev/active/move.md`
- Devctl MCP + contract alignment guide: `dev/MCP_DEVCTL_ALIGNMENT.md`
- Autonomous loop + mobile control-plane execution spec: `dev/active/autonomous_control_plane.md`
- Loop artifact-to-chat suggestion coordination runbook: `dev/active/loop_chat_bridge.md`
- IDE/provider adapter modularization execution spec: `dev/active/ide_provider_modularization.md`
- Standalone slash command plan (Codex/Claude without overlay): `dev/active/slash_command_standalone.md`
- SDLC policy: `AGENTS.md`
- Architecture: `dev/ARCHITECTURE.md`
- Changelog: `dev/CHANGELOG.md`

## Archive Log

- `dev/archive/2026-03-05-devctl-mcp-contract-hardening.md`
- `dev/archive/2026-01-29-claudeaudit-completed.md`
- `dev/archive/2026-01-29-docs-governance.md`
- `dev/archive/2026-02-01-terminal-restore-guard.md`
- `dev/archive/2026-02-01-transcript-queue-flush.md`
- `dev/archive/2026-02-02-release-audit-completed.md`
- `dev/archive/2026-02-17-tooling-control-plane-consolidation.md`
- `dev/archive/2026-02-20-senior-engineering-audit.md`
