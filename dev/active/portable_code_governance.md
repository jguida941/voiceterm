# Portable Code Governance Plan

**Status**: active  |  **Last updated**: 2026-03-14 | **Owner:** Tooling/code governance
Execution plan contract: required
This spec remains execution mirrored in `dev/active/MASTER_PLAN.md` under
`MP-376`. It is the narrower engine/adoption companion to
`dev/active/ai_governance_platform.md`, not a peer architecture authority for
the full standalone governance product.

Do not use this file as a second main plan for the product. Keep cross-product
architecture, documentation-consolidation, extraction sequencing, and
standalone-repo boundary decisions in `dev/active/ai_governance_platform.md`,
then use this file only for deeper engine/adoption detail within that frame.

## Scope

Turn the current VoiceTerm guard/probe/report stack into a reusable code-governance
engine that can be pointed at arbitrary repositories without editing the engine
itself. The goal is deterministic structural governance for AI-assisted coding:
guards reject recurring bad pattern families, probes rank the remaining design
smells, and the same artifact stream becomes evaluation data for later retrieval
and training work.

The broader "full reusable product" extraction now lives in
`dev/active/ai_governance_platform.md`, which is the main active plan for that
scope. This plan stays narrower on purpose: portable engine boundaries, repo
policy/preset layering, measurement/data capture, external-repo rollout, and
export/bootstrap packaging for off-repo analysis.

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
   AI-assisted code quality over time without quietly demanding unsustainable
   prompt/context volume.
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
- [ ] Extend guarded-episode measurement with context-budget metrics:
      estimated prompt size (`tokens` when available, otherwise bytes/lines/
      files), compression ratio, overflow path, and actual provider usage when
      exposed so quality gains can be evaluated against prompt cost.
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
- [x] Promote compatibility shims into a portable governance primitive with
      structural validation and policy-owned metadata requirements instead of
      leaving wrapper exceptions as repo-specific layout hacks.
- [x] Add an explicit long-lived public-shim allowlist plus lifecycle
      classification so temporary shims split into `migrate-callers` vs
      `remove-now` instead of one undifferentiated budget warning.
- [x] Burn down the first zero-caller temporary shim tranche once the lifecycle
      scan can prove removal safety from repo-visible evidence.
- [x] Migrate the remaining `review_channel_*` root shim callers to the
      `dev/scripts/devctl/review_channel/` package and delete the leftover
      temporary wrappers once repo-visible usage is gone.
- [x] Re-run the shim governance bundle after the `review_channel_*` migration
      and record the remaining temporary-wrapper counts in the plan and
      governance ledger.
- [x] Burn down the next largest temporary `dev/scripts/devctl` shim families
      or explicitly bless any deliberate long-lived public seams in repo
      policy so the root wrapper count keeps converging instead of plateauing.
- [x] Continue burning down the remaining temporary `dev/scripts/devctl` root
      shim families, starting with `cli_parser_*` by wrapper count and
      `triage_*` by repo-visible reference count, so the post-autonomy shim
      backlog keeps converging from 39 wrappers / 87 references instead of
      plateauing again.
- [x] Continue burning down the remaining temporary `dev/scripts/devctl` root
      shim families, now starting with `process_sweep_*` while the current
      docs-led probe examples keep flagging `data_science_metrics.py` plus
      `governance_bootstrap_*`, so the post-security backlog keeps converging
      instead of flattening out again.
- [ ] Automate the multi-repo benchmark runner around the new evaluation
      schema/templates instead of keeping the experiment contract doc-only.
- [ ] Add a portable structural-readability governance tranche for repo-policy-
      driven file/module/symbol naming and API-intent checks. Keep deterministic
      filename/layout rules eligible for hard guards, but start function/symbol
      clarity and broader KISS/readability enforcement as advisory probes or
      optional autofix/report surfaces until signal quality is proven across
      multiple repos.
- [ ] Build the short-term anti-pattern feedback loop before any model-training
      push: when guards/probes fire, emit compact repair packets, attach the
      most relevant repo-local good examples and policy hints, rerun targeted
      repair passes, and store reviewed bad->fixed episodes as machine-readable
      evidence for later retrieval, evaluation, and only then possible
      fine-tuning.
- [ ] Define one portable versioned finding schema for guard/probe output so
      rule families, review packets, suppression flow, autofix metadata, and
      later replay/eval records all project from the same evidence contract
      instead of growing separate per-surface payload shapes.
- [ ] Expand the compact machine-output receipt path into a portable artifact-
      cost contract: path/hash/bytes/token estimates, content type, receipt
      size, and rule-family/command metadata should be emitted consistently for
      JSON-canonical surfaces so context spend and reread avoidance are
      measurable across repos.
- [ ] Build the replayable benchmark corpus earlier and more concretely:
      seeded must-flag and must-not-flag Python/Rust examples, reviewed
      historical repo findings, and stable replay inputs for rule-precision
      comparisons before stronger portability or ML claims are made.
- [ ] Tighten Python type/boundary enforcement for the portable engine by
      evaluating stricter typed-contract lanes and executable import-boundary
      checks on core/runtime/report/policy modules instead of relying only on
      the current advisory mypy posture.
- [ ] Evaluate bounded structural-search/autofix integrations for portable
      rule families: AST/semgrep-style matching is useful where it improves
      deterministic detection or safe rewrites, but repo-owned policy and
      evidence contracts must stay authoritative.
- [ ] Add first-class machine-readable wrappers for the highest-value external
      quality lanes so adopters get the same evidence model across native and
      third-party tools: typed Python checks, import-boundary checks, Rust test
      execution, dependency/security audit, and coverage artifacts.
- [ ] Close the false-green layout gap in crowded roots: package-layout
      governance should prove real namespace decomposition for
      `dev/scripts/devctl`, `dev/scripts/devctl/commands`, and the mirrored
      test roots, not only freeze further flat growth while existing crowded
      trees remain mostly intact.
- [ ] Turn the documented `devctl/commands` taxonomy into tree reality instead
      of policy-only intent: converge the still-flat command families on the
      target subpackages (`check/`, `autonomy/`, `review_channel/`,
      `release/`, `process/`) so layout checks and docs describe the same
      package boundary.
- [ ] Burn down the remaining temporary root shim backlog to policy budget and
      remove zero-caller wrappers promptly; current probe evidence should not
      keep tolerating dead root shims once repo-visible usage is confirmed
      absent.
- [ ] Align bootstrap/self-hosting interpreter contracts with the repo's Python
      3.11+ requirement so governance entrypoints and AGENTS bootstrap commands
      do not fail on machines where `python3` still resolves to 3.10 before the
      real layout/quality checks can even start.
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
- 2026-03-12: Tightened the bootstrap handoff for adopted repos so the target
  checkout now gets one obvious repo-local first-read file:
  `dev/guides/PORTABLE_GOVERNANCE_SETUP.md`. `governance-bootstrap` still
  writes the starter repo policy, but now also writes a concrete AI-friendly
  run order and customization checklist into the target repo instead of
  leaving the exported markdown template as the only onboarding surface.
- 2026-03-12: Split the broader architecture ownership cleanly. `MP-376`
  continues to own the portable governance engine, policy layering,
  onboarding/export, and evaluation corpus; the new `MP-377` plan at
  `dev/active/ai_governance_platform.md` now owns the full reusable product
  extraction across runtime/control-plane contracts, repo-pack packaging,
  frontend convergence, and the path toward VoiceTerm becoming one consumer of
  an installable platform.
- 2026-03-12: Added the next shim-governance layer on top of the shared
  compatibility-shim primitive. `probe_compatibility_shims.py` now reuses the
  same AST-first shim validator to rank missing canonical metadata, expired
  wrappers, broken `shim-target` convergence, and shim-heavy roots/families,
  while `run_probe_report.py` now resolves probe entrypoints from the shared
  quality policy/script catalog instead of keeping a second hard-coded probe
  list.
- 2026-03-12: Continued the structural cleanup inside `dev/scripts/checks`
  without moving public entrypoints: the `active_plan`, `python_analysis`, and
  `probe_report` helper families now live behind documented internal
  subpackages so the root of `checks/` stays closer to a list of runnable
  guard/probe scripts instead of mixed entrypoints plus support modules.
- 2026-03-13: Split the new `package_layout` shim-governance seams internally
  without changing the public contract. `package_layout.rules` now re-exports
  focused model/loading/shim-validation helpers, and
  `package_layout.probe_compatibility_shims` now keeps `build_report()` /
  `main()` stable while delegating rule loading, scan logic, and hint building
  to internal modules. This keeps the self-hosting import surface flat and
  testable while letting the implementation stop growing as two large files.
- 2026-03-13: Captured the next pattern-mining direction explicitly after
  maintainership discussion: portable readability governance, not one monolithic
  "clean code" script. The intended slice is repo-policy-driven filename/module
  naming, symbol clarity, and public API intent checks with machine-readable
  findings. Rollout should stay modular: deterministic filename/layout contracts
  can graduate to hard guards once low-noise, while function naming, KISS/
  readability, and broader Python clean-code heuristics should start as
  advisory probes plus optional autofix/report surfaces until cross-repo
  evidence proves them portable.
- 2026-03-13: Captured the short-term path toward better AI output more
  explicitly. The next leverage point is not immediate model training; it is a
  governed repair loop with compact guard/probe repair packets, targeted
  repo-local example retrieval, and reviewed bad->fixed episode storage. That
  gives the platform a practical near-term path to better first-pass code and a
  cleaner long-term dataset for retrieval or fine-tuning later, instead of
  trying to learn directly from raw noisy failure logs.
- 2026-03-13: Captured the next portable-engine follow-ups from a broader
  architecture/product review so they do not stay trapped in chat. The review
  largely matched the repo's existing direction, but it sharpened the missing
  engine-level pieces: one versioned finding schema, stable machine receipts
  plus artifact-cost telemetry, a replayable must-flag/must-not-flag corpus,
  stronger typed/boundary enforcement for portable Python contracts, bounded
  structural-search/autofix integration, and machine-readable wrappers for the
  highest-value third-party lanes. The repo already has early receipt helpers,
  advisory mypy, and security/dependency tooling, so the actual task is to
  harden and productize those seams rather than starting from zero.
- 2026-03-13: Logged a concrete self-hosting gap from live maintainership
  review: the current layout guards are still green for partially the wrong
  reason. `freeze`-mode crowding prevents new flat growth, but it does not yet
  prove the crowded `devctl` roots are actually decomposed, and the intended
  `commands/{check,autonomy,review_channel,release,process}` taxonomy still
  exists more strongly in docs/policy than in the tree. The same review also
  confirmed that root shim debt remains above policy budget and that bootstrap
  still has a Python-version footgun on machines where `python3` is 3.10, so
  those are now explicit execution items rather than chat-only warnings.
- 2026-03-13: Burned down the next self-hosting crowded-root slice in
  `dev/scripts/devctl` without breaking public imports. The new portable
  bootstrap helpers now live under `dev/scripts/devctl/governance/`, the
  `platform-contracts` implementation lives under `dev/scripts/devctl/platform/`,
  the `PathAuditAggregateReport` model moved under
  `dev/scripts/devctl/path_audit_support/`, and the new runtime/platform/probe
  tests moved under topic-aligned test packages instead of the crowded root test
  directory. The root files stay as metadata-bearing compatibility shims, the
  direct unit slices plus `check_package_layout` stay green, `devctl check
  --profile ci` now passes on this branch head, and the remaining pre-existing
  medium `probe_compatibility_shims` backlog for older `devctl` root shims was
  explicitly recorded as `deferred` in `governance-review`.
- 2026-03-13: Finished the next shim-governance follow-up on that same
  `dev/scripts/devctl` root backlog. All 84 previously metadata-free root
  compatibility shims now carry canonical `shim-owner` / `shim-reason` /
  `shim-expiry` / `shim-target` fields, the stale `# noqa` suppressions were
  removed from those wrappers, and the missing-metadata variant of
  `probe_compatibility_shims` is gone. The post-fix audit is now much cleaner:
  `devctl check --profile ci` still passes, `probe-report` narrows to pure shim
  budget pressure, and the next highest-signal extraction target is the
  `review_channel_*` root family (13 approved wrappers against a family budget
  of 4) rather than more wrapper metadata work.
- 2026-03-13: Extended shim governance from metadata-only auditing into an
  explicit lifecycle model. `probe_compatibility_shims` now loads a
  repo-policy allowlist for long-lived public shims, treats every other valid
  wrapper as temporary by default, and scans repo-visible imports/path/module
  references to classify temporary shims into `migrate-callers` vs
  `remove-now`. The first VoiceTerm policy seed deliberately stays narrow:
  public `dev/scripts/checks/{check_,probe_,run_}*.py` entrypoints are
  allowlisted, generated artifacts under `dev/reports/` are excluded from
  usage scanning so probe output does not self-justify wrappers, and the
  remaining `dev/scripts/devctl` root wrappers now show up as explicit
  temporary migration debt unless future repo policy blesses specific public
  seams.
- 2026-03-13: Used that new lifecycle scan to burn down the first concrete
  removal slice immediately instead of just recording it. Deleted 25
  zero-caller temporary root shims from `dev/scripts/devctl` (including the
  stale `watchdog_episodes.py` wrapper and six `review_channel_*` wrappers),
  updated the watchdog README to point at the canonical package module, and
  reran the governance bundle. The shim audit state is now materially better:
  the `remove-now` high-severity bucket is gone, `dev/scripts/devctl` root
  temporary wrappers dropped from 88 to 63, and the `review_channel_*` family
  dropped from 13 wrappers to 6. The remaining shim backlog is now purely
  medium-severity caller migration / budget pressure, which makes
  `review_channel_*` the clean next family to finish instead of a mixed
  metadata-plus-delete cleanup.
- 2026-03-13: Finished that `review_channel_*` cleanup tranche end-to-end.
  Updated the remaining docs/tests/active-plan references to the canonical
  `dev/scripts/devctl/review_channel/{event_store,handoff,launch,parser,prompt,state}.py`
  modules, deleted the six leftover temporary root wrappers, reran the review
  channel regression slice plus the shim-governance bundle, and recorded the
  new state. `probe-report` no longer emits a `review_channel_*` family
  finding; the broader `dev/scripts/devctl` root backlog dropped again from 63
  temporary wrappers / 143 repo-visible references to 57 wrappers / 135
  references. The next highest-signal shim work is now the larger remaining
  temporary root families rather than review-channel residue.
- 2026-03-13: Retired the temporary `security_*` root shim family after the
  next probe rerun narrowed the backlog to 23 wrappers / 46 repo-visible
  references. Workflow trigger paths, maintainer docs, active-plan notes, and
  engineering history now point at the canonical
  `dev/scripts/devctl/security/{parser,codeql,python_scope,tiers}.py`
  modules, and the four obsolete root wrappers were deleted. The next
  shim-governance target is now `process_sweep_*` plus the remaining
  docs-led callers for `data_science_metrics.py` and
  `governance_bootstrap_{guide,policy}.py`.
- 2026-03-13: Retired the next largest temporary `dev/scripts/devctl` root
  shim family, `autonomy_*`. Migrated the remaining repo-visible
  docs/history/plan references to the canonical
  `dev/scripts/devctl/autonomy/{benchmark_helpers,benchmark_matrix,benchmark_parser,benchmark_render,benchmark_runner,loop_helpers,loop_parser,phone_status,report_helpers,report_render,run_feedback,run_helpers,run_parser,run_plan,run_render,status_parsers,swarm_helpers,swarm_post_audit}.py`
  modules, renamed the package-layout probe's synthetic fixture paths so tests
  no longer self-justify a real wrapper name, deleted the 18 obsolete root
  autonomy shims, and reran autonomy plus review-channel regression coverage.
  The shim-governance state improved materially again: `probe-report` dropped
  the broader `dev/scripts/devctl` root backlog from 57 temporary wrappers /
  135 repo-visible references to 39 wrappers / 87 references, and the next
  highest-signal families are now `cli_parser_*` by wrapper count (8 wrappers /
  12 references) and `triage_*` by repo-visible references (4 wrappers / 14
  references).
- 2026-03-13: Finished the next caller-migration tranche after `autonomy_*`.
  Migrated the remaining repo-visible `cli_parser_*`, `triage_*`, and
  `triage_loop_*` docs/history/active-plan references to the canonical
  `dev/scripts/devctl/cli_parser/` and `dev/scripts/devctl/triage/`
  package-owned modules, then deleted 16 obsolete root wrappers. The shim
  backlog dropped again: `probe-report` now shows 23 temporary
  `dev/scripts/devctl` root shims with 46 repo-visible callers or references,
  down from 39 / 87. The remaining wrapper-heavy families are now
  `process_sweep_*` and `security_*` (4 wrappers each), while the current
  repo-visible-reference examples point at `data_science_metrics.py` and the
  `governance_bootstrap_*` wrappers.
- 2026-03-13: Retired the next shim tranche: `process_sweep_*` (4 wrappers),
  `data_science_metrics.py`, and `governance_bootstrap_{guide,policy}.py`.
  All seven had zero active Python callers; only doc/markdown references
  remained. Updated `AGENTS.md`, `dev/scripts/README.md`,
  `dev/active/ai_governance_platform.md`, `dev/history/ENGINEERING_EVOLUTION.md`,
  and the `process_sweep/README.md` to point at canonical package paths, then
  deleted the root shims. The `dev/scripts/devctl` root temporary wrapper
  count dropped from 23 to 16. All 1274 tests pass.
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
- 2026-03-12: Closed the final review-channel CI parity leak from the same PR
  rerun. The stale-heartbeat auto-refresh path for `devctl review-channel`
  had been using `check_review_channel_bridge.py` metadata errors as its
  trigger, but that guard intentionally suppresses live heartbeat freshness on
  GitHub-hosted CI because the runner is not the real Codex conductor. That
  meant `status` / `launch` could still see a stale bridge snapshot while the
  auto-refresh helper saw no refreshable guard error. The helper now treats
  the bridge guard as a structural gate only and derives refreshability from
  direct bridge snapshot/liveness state instead; the stale-heartbeat tests now
  pin `GITHUB_ACTIONS=true` so the CI runner contract is exercised locally.
- 2026-03-12: Closed the last workflow-only parity blocker on PR #16 too. The
  docs/governance workflow was invoking `check_rust_compiler_warnings.py`
  inside `tooling_control_plane.yml` without the Rust toolchain or Linux ALSA
  headers that the dedicated Rust CI lanes install first, so the docs-policy
  job could fail even while the real Rust jobs stayed green. The workflow now
  provisions Rust and `libasound2-dev` before the compile-time Rust guard, and
  maintainer docs now call out that tooling/docs jobs cannot assume Rust lane
  prerequisites automatically.
- 2026-03-12: Promoted compatibility shims into the portable governance engine
  instead of treating them as an ad hoc VoiceTerm carve-out. The package-layout
  support now uses a shared bootstrap seam, validates shim shape structurally
  before reading optional metadata, supports policy-owned required metadata
  fields such as `owner` / `reason` / `expiry` / `target`, and lets crowded
  root/family reports exclude approved shims from implementation density while
  still surfacing shim counts explicitly.
- 2026-03-12: Tightened the crowded `checks/` root follow-through for that
  shim primitive. The root shim exemption no longer hard-codes
  `package_layout.command`; it now accepts any thin `package_layout.*` wrapper,
  ignores canonical shim metadata lines in the wrapper-size budget, and keeps
  both `check_package_layout.py` and `probe_compatibility_shims.py` as stable
  root entrypoints over package-owned implementations. The paired devctl tests
  also moved under `dev/scripts/devctl/tests/checks/package_layout/` so the
  crowded test root mirrors the same package boundary.
- 2026-03-13: Added context-efficiency as an explicit portable-governance
  measurement requirement. The engine plan already tracked guarded-episode
  data, evaluation corpora, and adoption evidence, but it did not yet say
  whether better rule outcomes had to be weighed against prompt/context cost.
  The execution checklist now requires context-budget metrics so future
  evaluation can compare code-quality gains against actual context usage rather
  than treating prompt volume as invisible overhead.
- 2026-03-14: Corrected the external-repo proof path after validating that the
  earlier March 14 `ci-cd-hub` claim was only partially portable. The raw
  `probe-report --repo-path` numbers were reproducible, but policy resolution,
  relative artifact paths, topology scans, and git-status collection still
  leaked the engine checkout, while starter policies only scanned `scripts/`
  in repos with larger top-level Python packages. The portable fixes now route
  repo-root lookups through the runtime override, seed portable preset JSON
  files into bootstrapped repos, and write explicit `quality_scopes` into
  starter policies so repos like `ci-cd-hub` scan `scripts`, `_quarantine`,
  `cihub`, and `tests` instead of silently narrowing to `scripts/`.
- 2026-03-14: Reran the corrected pilot corpus after those fixes. The previous
  quoted `ci-cd-hub` result (`7` hints: `1 high`, `5 medium`, `1 low`) was an
  under-scan; the corrected March 14 onboarding run found `159` hints
  (`53 high`, `104 medium`, `2 low`) across `509` source files with `93`
  hinted files. The corrected 13-repo aggregate is now `311` hints
  (`115 high`, `193 medium`, `3 low`) with `3` clean repos and `0` scan
  errors, replacing the previously quoted `158`-hint aggregate. The durable
  audit note and machine-readable summary live at
  `dev/reports/audits/2026-03-14-portable-governance-pilot-rerun.md` and
  `dev/reports/audits/portable_governance_pilot_2026-03-14.json`.
- 2026-03-14: The rerun also clarified why some repos still look "low":
  current portable coverage is Python/Rust-only, so repos with large Java,
  TypeScript, or React surfaces only get findings from Python-side tooling or
  scripts until language packs for those ecosystems are added. That gap is now
  explicit evidence for the next portability tranche instead of a vague chat
  concern.
- 2026-03-14: Confirmed that the hard-guard lane is now portable enough to use
  in onboarding mode, not just the probe lane. Running
  `check --profile ci --repo-path /tmp/governance-pilots/ci-cd-hub --adoption-scan`
  completed without engine crashes and returned `13` failing guard families out
  of `16` executed steps, while `package-layout-guard`, `god-class-guard`, and
  `audit-scaffold-auto` stayed clean. That result is now captured beside the
  corrected probe counts in the audit note/JSON, and six representative
  `ci-cd-hub` probe findings were recorded into `governance-review` as
  `confirmed_issue` rows so the proof path includes adjudicated external
  evidence, not only raw packets.

## Session Resume

- Corrected March 14 pilot evidence is now durable in
  `dev/reports/audits/2026-03-14-portable-governance-pilot-rerun.md` and
  `dev/reports/audits/portable_governance_pilot_2026-03-14.json`.
- `probe-report --repo-path` now resolves target repo policy, scope, topology,
  git-status, and artifact paths consistently enough to trust cross-repo
  counts for Python/Rust repos.
- `ci-cd-hub` is the strongest proof point: `7` hints was an under-scan;
  corrected onboarding counts are `159` hints across `scripts`, `_quarantine`,
  `cihub`, and `tests`.
- The harder validation path now works too: `check --repo-path --adoption-scan`
  on `ci-cd-hub` completes and surfaces `13` failing guard families, so the
  engine is catching real hard-guard debt instead of only emitting probes.
- Next portability step should expand beyond Python/Rust so mixed Java/React
  and TypeScript repos stop looking artificially clean.

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
- 2026-03-13 autonomy shim-family retirement evidence:
  `python3.11 -m pytest dev/scripts/devctl/tests/checks/package_layout/test_probe_compatibility_shims.py dev/scripts/devctl/tests/test_autonomy_benchmark.py dev/scripts/devctl/tests/test_autonomy_loop.py dev/scripts/devctl/tests/test_autonomy_report.py dev/scripts/devctl/tests/test_autonomy_run.py dev/scripts/devctl/tests/test_autonomy_swarm.py dev/scripts/devctl/tests/test_review_channel.py -q --tb=short`
  `python3 dev/scripts/devctl.py probe-report --format md`
  `python3 dev/scripts/devctl.py check --profile ci`
  `python3 dev/scripts/devctl.py governance-review --record --finding-id devctl-autonomy-root-shims --signal-type probe --check-id probe_compatibility_shims --verdict fixed --path dev/scripts/devctl --symbol 'autonomy_*' --severity medium --risk-type compatibility_shim_family_budget --source-command "python3 dev/scripts/devctl.py probe-report --format md" --scan-mode working-tree --notes "...deleted 18 temporary root autonomy shims..." --format md`
  `python3 dev/scripts/devctl.py docs-check --strict-tooling`
  `python3 dev/scripts/checks/check_active_plan_sync.py`
  `python3 dev/scripts/checks/check_review_channel_bridge.py` (`code_audit.md` failed only because `Last Codex poll` was stale in the live bridge state)
  `python3 dev/scripts/devctl.py process-cleanup --verify --format md`
  `python3 dev/scripts/devctl.py process-cleanup --verify --format md`
- Export path:
  `python3 dev/scripts/devctl.py governance-export --format md`
- Finding-quality ledger:
  `python3 dev/scripts/devctl.py governance-review --format md`
  `python3 dev/scripts/devctl.py governance-review --record --signal-type <guard|probe> --check-id <id> --verdict <verdict> --path <file> --format md`
- Pilot bootstrap path:
  `python3 dev/scripts/devctl.py governance-bootstrap --target-repo <path> --format md`
- 2026-03-14 corrected external-pilot rerun:
  `python3 dev/scripts/devctl.py governance-bootstrap --target-repo /tmp/governance-pilots/ci-cd-hub --force-starter-policy --format json`
  `python3 dev/scripts/devctl.py probe-report --adoption-scan --repo-path /tmp/governance-pilots/ci-cd-hub --format json --output /tmp/cihub-probe-report.json`
  `python3 dev/scripts/devctl.py check --profile ci --repo-path /tmp/governance-pilots/ci-cd-hub --adoption-scan --format json --output /tmp/cihub-check-adoption.json`
  `python3 dev/scripts/devctl.py governance-review --record --signal-type probe --check-id <probe_id> --verdict confirmed_issue --repo-name ci-cd-hub --repo-path /tmp/governance-pilots/ci-cd-hub ...`
  local 13-repo rerun over `/tmp/governance-pilots/*` via repeated
  `governance-bootstrap --force-starter-policy` plus
  `probe-report --adoption-scan --repo-path`; durable summary saved to
  `dev/reports/audits/portable_governance_pilot_2026-03-14.json` and
  `dev/reports/audits/2026-03-14-portable-governance-pilot-rerun.md`
- Known unrelated hygiene warning:
  `python3 dev/scripts/devctl.py hygiene --strict-warnings` remains red because
  of pre-existing publication drift and because hygiene can observe the cleanup
  subprocess while it runs; standalone cleanup verify is green.
