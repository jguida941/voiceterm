# AI Governance Platform Plan

**Status**: active  |  **Last updated**: 2026-03-14 | **Owner:** Tooling/control plane/product architecture
Execution plan contract: required
This spec remains execution mirrored in `dev/active/MASTER_PLAN.md` under
`MP-377`, and it is the canonical active architecture plan for the standalone
AI governance product scope. `MASTER_PLAN` stays the repo-wide tracker
authority, but this file is the main scoped plan for architecture decisions,
documentation consolidation, extraction sequencing, and implementation order
under `MP-377`.

For this product scope, treat this file as the only main active plan. Companion
docs may exist for narrower engine/adoption depth or durable guide material,
but they must route back here instead of acting like peer execution authority.

## Scope

Turn the current VoiceTerm-local automation stack into a reusable AI governance
platform that can be installed into arbitrary repositories without editing core
orchestration code. The target product is broader than portable guards alone:
it includes the code-governance engine, typed control-plane/runtime contracts,
repo-adapter boundaries, AI remediation loops, and optional frontends such as
CLI, PyQt6 desktop console, overlay/TUI, and phone/mobile views.

VoiceTerm should become the first consumer of that platform rather than the
place where the whole platform remains embedded. Another repo should be able to
adopt the same system through packaging, bootstrap/setup flows, policy/repo-pack
selection, and provider configuration instead of copying VoiceTerm-specific
Python modules and pruning them by hand.

This plan is intentionally broader than
`dev/active/portable_code_governance.md`. That plan stays focused on the
portable guard/probe/policy/bootstrap/export engine and multi-repo evaluation
work. This plan owns the full reusable product architecture: shared runtime
contracts, frontend convergence, repo-pack packaging, and the staged extraction
of higher-level loops that are still repo-local today.

## Canonical Plan Use

Use this file as the main scope-preservation surface for the standalone
governance product direction.

1. Put product-boundary, packaging, repo-pack, runtime-contract, frontend, and
   documentation-consolidation decisions here first.
2. Keep `dev/active/MASTER_PLAN.md` as the repo-wide tracker, but do not rely
   on `MASTER_PLAN` alone to preserve architecture detail for `MP-377`.
3. Treat `dev/active/portable_code_governance.md` as the narrower companion
   engine plan, not a peer architecture authority for the full product.
4. Treat `dev/guides/AI_GOVERNANCE_PLATFORM.md` as the durable guide derived
   from this active plan, not a second active source of execution state.
5. Any platform-scope tooling, policy, runtime-contract, or extraction change
   that triggers repo docs-governance must update this file. The repo-level
   `docs-check` rule is policy-owned and should enforce this requirement
   without hardcoding VoiceTerm-specific logic into the command implementation.

## Platform Layers

Use these layers consistently while reorganizing the repo and extracting the
reusable product:

1. `governance_core`
   portable guards, probes, policy resolution, bootstrap, export, review ledger,
   measurement schemas, and artifact generation.
2. `governance_runtime`
   typed control state, action execution, loop orchestration, repo sessions,
   queueing, and artifact-store contracts shared by CLI/UI surfaces.
3. `governance_frontends`
   CLI, PyQt6 operator console, overlay/TUI, and phone/mobile surfaces that all
   project the same runtime state instead of re-implementing orchestration.
4. `governance_adapters`
   provider adapters, CI/workflow adapters, VCS adapters, notifier adapters, and
   local-environment capability detection.
5. `repo_packs`
   repo-specific policy, workflow defaults, docs/runbook templates, and any
   bounded repo-local guard or lane wiring that does not belong in the portable
   engine.
6. `product_integrations`
   VoiceTerm-specific packaging and UX, treated as a consumer/integration layer
   over the reusable platform rather than the canonical home of every feature.

## Shared Contracts

Frontends and repo integrations should converge on one explicit backend
contract set:

- `RepoPack`: declares repo policy, default workflows, docs templates,
  adoption checks, path roots via `RepoPathConfig`, and platform compatibility
  requirements for one codebase family.
- `RepoPathConfig`: repo-pack-owned mapping for active docs, report roots,
  bridge files, generated surfaces, and workflow/artifact paths that portable
  layers must resolve through instead of hard-coded `dev/...` literals or
  `Path(__file__).resolve().parents[...]` assumptions.
- `ContextPack`: bounded AI-input bundle with source refs, summaries,
  prioritization metadata, and estimated size/cost fields.
- `ContextBudgetPolicy`: repo-pack-defined limits and fallback behavior for
  bootstrap, adoption-scan, focused-fix, review, and remediation-loop modes.
- `ControlState`: canonical machine-readable state for runs, findings, sessions,
  approvals, and queue status.
- `TypedAction`: explicit command contract for check, probe, bootstrap, fix,
  report, export, review, and remediation actions.
- `RunRecord`: durable record for one governed execution episode, including
  inputs, context-pack telemetry, artifacts, findings, repairs, approvals, and
  outcomes.
- `Finding`, `FindingReview`, `MetricEvent`: versioned evidence/metrics records
  shared by guards, probes, governance review, replay/evaluation flows, and UI
  projections. `Finding` is the canonical machine record carrying `rule_id`,
  `rule_version`, category/language/severity/confidence, file/span, evidence,
  rationale, suggested fix, autofixable state, suppression metadata, and
  artifact refs so every agent/reviewer/markdown projection derives from the
  same base object.
- `ArtifactStore`: stable path/retention interface for reports, snapshots,
  review packets, and benchmark evidence.
- `ProviderAdapter`: abstraction over Codex, Claude, or later providers so
  runtime loops do not hard-code one CLI.
- `WorkflowAdapter`: abstraction over GitHub/CI/local workflow execution so
  Ralph-style or mutation loops stay reusable.

Versioning rules sit beside those contracts, not outside them:

- repo packs must declare `platform_version_requirement`, owned path roots, and
  any compatibility-window assumptions up front
- runtime/artifact payloads must own explicit `schema_version` fields plus one
  documented migration and rollback path before the surface counts as stable
- CI/bootstrap/adoption flows should validate both package/runtime
  compatibility and schema-version compatibility before mutable execution

If a surface cannot be expressed through those shared contracts, it is still
too repo-local to count as extracted.

## Machine-Readable Projection Contract

Machine-readable output is the canonical contract for automation, agent
ingestion, replay, metrics, and later database/ML indexing. Human-readable
rendering is still required, but it is a projection over the same base data.

Required rules:

1. Command/report surfaces should emit canonical `json`/`jsonl` payloads for
   machine consumers and may also emit `md` or visual renderings for humans.
2. Markdown summaries, flowcharts, hotspot diagrams, and handoff writeups must
   derive from the same underlying machine payload instead of becoming the only
   authoritative output.
3. Tiered review packets for agents, junior developers, and senior reviewers
   should be profile-specific projections over one shared evidence record, not
   separate ad hoc schemas per audience.
4. When automation or AI loops do not need prose, prefer the machine-readable
   projection so context usage stays smaller and ingestion stays deterministic.
5. If a command cannot produce a compact machine-readable payload, it is not
   ready to count as a reusable platform surface yet.

## Context Budget And Usage Contract

Context efficiency is a product requirement, not later optimization debt.

The platform should improve AI coding quality without assuming infinite prompt
windows or silently burning large amounts of provider context. Every governed
AI path must make context use explicit, measurable, and repo-pack tunable.

Required rules:

1. Every AI-facing run mode (`bootstrap`, `adoption-scan`, `focused-fix`,
   `review`, `remediation-loop`) must declare a target context envelope and
   reserved headroom before provider dispatch.
2. Runtime should estimate prompt size before execution (`tokens` when a
   provider tokenizer is available, otherwise bytes/lines/files as fallback)
   and record actual prompt/response usage when the provider exposes it.
3. When context would exceed budget, the runtime must choose an explicit
   fallback path: summarize, rank/prune, split into smaller runs, or fail with
   an operator-visible overflow reason. Silent "send everything" behavior is
   not acceptable.
4. Repo packs own budget profiles and defaults. VoiceTerm can keep richer
   local defaults, but another repo must be able to tighten or expand them
   without patching portable orchestration code.
5. Adoption and usage docs must publish budget-aware operating modes so
   maintainers know when to use full-repo scans versus focused slices and what
   rough context/cost bands to expect.
6. Artifact-cost telemetry must stay in the same contract surface: at minimum
   record artifact path/hash/bytes, estimated tokens, stdout receipt bytes,
   reread avoidance by hash, unchanged-artifact skip counts, and cost per
   accepted fix, false positive, and no-op cycle.

## Adoption Flow

The reusable platform should be easy for an AI or maintainer to stand up in a
new repo:

1. Install the platform package and CLI entrypoint.
2. Run a bootstrap command against the target repo.
3. Generate or select a starter `RepoPack` / repo policy, including
   context-budget defaults.
4. Run adoption scan + probe/report packet against the full worktree.
5. Optionally enable frontends such as the PyQt6 console or phone/mobile view.
6. Start governed AI loops with the same typed runtime contracts and declared
   context-budget profiles used here.

The ideal setup path is a scriptable installer plus AI-readable bootstrap docs,
not a maintainer manually wiring scattered files.

## Extraction Sequence

Sequence the architecture work in this order:

1. Stabilize and package the portable governance engine already tracked under
   `MP-376`.
2. Define the shared runtime/action/state and context-budget contracts so
   Ralph, mutation, review-channel, and process-hygiene flows stop inventing
   repo-local shapes.
3. Move frontend shells to those contracts so PyQt6, CLI, overlay/TUI, and
   mobile status surfaces are projections over the same backend.
4. Introduce repo-pack packaging so VoiceTerm becomes one adopter profile.
5. Validate the extracted platform against multiple external repos before
   treating the packaging boundary as complete.

## Platform Completion Gates

Do not treat this product as "done" when the code merely compiles or when the
portable core has been split into a separate repo. `MP-377` is only complete
when all of these are true:

1. The architecture boundary is real: VoiceTerm consumes the platform through
   explicit repo-pack + CLI/API/runtime contracts rather than internal imports.
2. The enforcement pipeline is trustworthy end to end: local CLI checks, CI
   workflows, docs-governance, review-ledger recording, and telemetry paths
   agree on the same policy surface.
3. Context use is sustainable and operator-visible: budget profiles, overflow
   behavior, telemetry, and usage guidance exist for bootstrap/full-scan/
   focused modes, and quality claims do not depend on hidden oversized prompts.
4. Platform accuracy claims are backed by broad evidence, not only local spot
   wins: repeated adoption scans, replayable evaluation runs, and reviewed
   finding quality across this repo plus external adopters.
5. Python and Rust have both gone through continued pattern-mining passes so
   the first language lanes are materially stronger than today's baseline and
   no longer rely on a narrow initial rule set.
6. The future database/ML path is bounded by explicit provenance,
   privacy/redaction, replay, and waiver/suppression rules.
7. The analyzer architecture is language-extensible: new languages plug into
   shared finding/policy/telemetry contracts instead of forcing a second engine
   design.

## Competitive Differentiators

This product should not be framed as "Semgrep plus AI wrappers" or "a prettier
SonarQube". Its defensible shape is the combination of deterministic policy,
runtime contracts, governed multi-agent execution, and portable repo adoption.

Keep these differentiators explicit in private architecture docs and public
proof packs:

1. adaptive feedback sizing instead of one fixed review verbosity level
2. three-layer enforcement: hard guards, advisory probes, and AI review
3. artifact-backed governed loops with replayable evidence and review ledgers
4. paired reviewer/coder multi-agent orchestration instead of one-shot fixes
5. explicit context-budget contracts as a product requirement, not an afterthought
6. mutation/remediation loops under the same policy and evidence model
7. multi-surface control across CLI, desktop, overlay/TUI, and phone/mobile
8. self-hosted portability through repo packs rather than vendor lock-in

External analyzers such as Ruff, Semgrep, Clippy, cargo-audit, Black, or
future AST/search-rewrite tools are subordinate engines or optional tool
adapters under this control plane. They can feed or extend the platform, but
they are not the product boundary and they are not `v0.1` blockers.

Keep the governed signal taxonomy explicit:

1. `language-engine findings`: Ruff/Semgrep/Clippy/cargo-audit/other scanner
   or formatter results routed through repo-owned policy.
2. `AI-shape findings`: deterministic structural failures common in
   AI-generated or AI-refactored code such as nesting debt, helper
   fragmentation, shim sprawl, layout drift, schema instability, and packaging
   violations. Keep local-shape and architectural-shape signals explicit inside
   this family.
3. `repo-contract findings`: command/docs/listing drift, plan sync, artifact
   contract violations, telemetry obligations, layer-boundary failures, and
   other repo-owned governance mismatches.

Behavioral/domain correctness remains a separate validation lane rather than
the platform's main differentiation claim. Product tests, typed invariants,
domain-specific checks, and runtime validation still own "does it actually do
the right thing?" evidence, while the governance platform is strongest on the
deterministic local-shape, architectural-shape, and repo-contract failures AI
systems repeatedly produce.

Keep the platform stack legible as three layers:

1. `engine tools`: Ruff, Semgrep, Clippy, cargo-audit, and similar rule
   engines answer "did this pattern fire?".
2. `shape rules`: repo-owned AI-shape and repo-contract rules answer "did the
   code or repo drift into the deterministic bad shapes we keep seeing?".
3. `governed loop`: the control plane decides when to run checks, what the AI
   reads, when to repair, when to stop, and how evidence is stored.

The third layer is the product. The first two are inputs to that product.

The governing thesis should stay precise:

- we are not changing model weights
- we are improving the environment the model codes inside
- the loop works by constraint, cleaner context, reduced complexity, and a
  better local search space

Code-shape and agent memory are related but separate problems. This platform
primarily attacks repo/code shape so later AI passes need less context, read
smaller artifacts, and touch fewer unrelated surfaces; memory and retrieval
improve as a consequence of that cleaner environment, not because the platform
solves long-term model memory directly.

## Loop Value Proof

The platform does not get to claim "better code" on intuition alone. Every
portable primitive and every stronger loop claim should prove value on four
axes:

1. `correctness preserved`: tests/build/smoke status before and after.
2. `structural quality improved`: findings before/after, which rule families
   dropped, and accepted fixes versus reverted fixes.
3. `cost justified`: bytes/tokens, artifacts reread, unchanged-artifact skips,
   and AI turns/loops per successful repair.
4. `generalization shown`: repos tested, language mix, fix rate, false
   positives, defer rate, and cleanup rate.
5. `follow-up stability`: whether the next bounded change becomes more local,
   needs less reread context, or avoids breakage that was harder to avoid on
   the first pass.

Also track the caution set explicitly:

- high-risk transformations that often change behavior even when shape looks
  better
- noisy rules with high defer/revert/low-trust rates
- large or frequently reopened artifacts that waste context
- common AI-generated bad patterns still passing all current checks
- over-modularization: too many tiny helpers, vague abstractions, or call
  chains that satisfy shape rules while making the code harder to follow
- rule gaming: changes that technically satisfy the rule but do not improve
  readability, maintainability, or safe follow-up edits

## Concrete Migration Roadmap

Use this as the implementation-order contract for `MP-377`. The goal is to
make the boundaries real inside this repo first, then package them, then split
repos only after external-adoption proof exists.

### Target Package Names

Use these package/workspace names unless a later packaging pass finds a strong
reason to rename them:

| Package / layer | Responsibility | Must not own |
|---|---|---|
| `governance_core` | guards, probes, policy resolution, bootstrap, export, review ledger, evaluation/report schemas | repo-specific paths, UI code, provider/workflow execution details |
| `governance_runtime` | `ControlState`, `ReviewState`, `TypedAction`, `RunRecord`, `ArtifactStore`, action dispatch contracts | repo-specific policies, CLI-only parsing, frontend widgets |
| `governance_adapters` | `ProviderAdapter`, `WorkflowAdapter`, VCS/CI/notifier bridges, environment capability detection | repo-pack defaults, frontend shaping, hard-coded VoiceTerm docs/paths |
| `governance_frontends` | CLI surface, PyQt6 console, overlay/TUI, phone/mobile, optional MCP transport | orchestration truth, direct repo-policy logic, hidden state contracts |
| `repo_packs.voiceterm` | VoiceTerm path layout, branch/docs policy, workflow defaults, thresholds, allowlists, release expectations | portable engine code, generic adapters, frontend logic |
| `product_integrations.voiceterm` | VoiceTerm packaging, branding, release wiring, user-facing integration details | portable engine authority, repo-pack-neutral contracts |

### Ownership Boundaries

Apply these boundaries before moving code across repos:

1. `governance_core` may read repo policy, but repo policy must not patch core
   logic.
2. `governance_runtime` is the only place that defines typed action/state/run
   contracts.
3. `governance_adapters` translate external tools and transports into runtime
   contracts; they do not own repo defaults.
4. `governance_frontends` render runtime state and submit typed actions; they
   do not parse repo-local orchestration artifacts directly once a contract
   exists.
5. `repo_packs.voiceterm` owns all VoiceTerm-specific doc lists, path roots,
   workflow defaults, branch policy, and threshold tuning.
6. `product_integrations.voiceterm` may package or brand the system, but it
   must consume the same backend contracts an external adopter would use.

### Portable `v0.1` Release Boundary

The first portable release must stay narrow enough to prove the architecture
without dragging the whole VoiceTerm product surface across the boundary.

`v0.1` in scope:

- installable governance package + stable CLI entrypoint
- repo-pack packaging + compatibility contract
- shared runtime/evidence contracts (`RepoPack`, `RepoPathConfig`,
  `TypedAction`, `ControlState`, `ReviewState`, `RunRecord`, `Finding`,
  `FindingReview`, `MetricEvent`, `ArtifactStore`)
- compact machine receipts for JSON-canonical surfaces
- replay/evaluation harness and first labeled corpus
- Python/Rust-first rule families and policy/evidence flow

`v0.1` explicitly out of scope as blockers:

- PyQt6/operator-console extraction
- iOS/mobile or MCP parity
- full Ralph/review-channel/process-hygiene extraction
- optional external analyzer integrations beyond what already exists in repo
  policy
- broad multi-repo packaging of every frontend or workflow loop

### Phase 0 - Package Boundary And Compatibility Seams

Objective: stop growing the current flat embedded shape while preserving
working imports and commands.

Deliverables:

- create one stable top-level import boundary for portable platform code
- define a real install surface for the governance package: versioned
  `pyproject.toml`, build backend, dependencies, and CLI entrypoint(s) that
  work in a clean environment without `sys.path` patching
- keep compatibility re-exports in old module locations during the move
- define the repo-pack-owned path-resolution contract (`RepoPathConfig`) so
  portable layers stop depending on raw VoiceTerm path literals
- route new files into layer-owned directories only

Initial file moves:

- move platform blueprint helpers under the future `governance_core` path
  starting from:
  - `dev/scripts/devctl/platform/contracts.py`
  - `dev/scripts/devctl/platform/contract_definitions.py`
  - `dev/scripts/devctl/platform/surface_definitions.py`
  - `dev/scripts/devctl/platform/blueprint.py`
- keep `devctl platform-contracts` as a stable public entrypoint:
  - `dev/scripts/devctl/commands/platform_contracts.py`
- harden the install/config seam that currently anchors the embedded layout:
  - `dev/scripts/pyproject.toml`
  - `dev/scripts/devctl/config.py`
- keep the package-layout guard as the enforcement seam:
  - `dev/scripts/checks/check_package_layout.py`
  - `dev/scripts/checks/package_layout/support.py`

Exit criteria:

- new platform code lands under layer-owned directories, not in flat
  `dev/scripts/devctl/` roots
- the governance CLI can be installed in a clean venv/worktree through a real
  package entrypoint
- compatibility imports exist for moved public modules
- portable layers resolve repo-owned paths through repo-pack/path contracts
  instead of direct `dev/active/*`, `dev/reports/*`, or `parents[...]`
  assumptions
- package-layout guard blocks regressions against the new directory contract

### Phase 1 - Extract `governance_core`

Objective: finish the portable engine first.

Scope:

- policy resolution
- guards and probes
- governance bootstrap/export/review
- evaluation/report schemas
- labeled evaluation corpus plus replay harness for version-to-version
  rule/policy comparisons

Files to move first:

- policy/bootstrap/export:
  - `dev/scripts/devctl/quality_policy.py`
  - `dev/scripts/devctl/quality_policy_loader.py`
  - `dev/scripts/devctl/quality_policy_defaults.py`
  - `dev/scripts/devctl/repo_policy.py`
  - `dev/scripts/devctl/governance/bootstrap_policy.py`
  - `dev/scripts/devctl/governance/bootstrap_guide.py`
  - `dev/scripts/devctl/governance_export_support.py`
  - `dev/scripts/devctl/governance_export_artifacts.py`
  - `dev/scripts/devctl/governance_review_log.py`
  - `dev/scripts/devctl/governance_review_models.py`
  - `dev/scripts/devctl/governance_review_render.py`
- portable report/evaluation helpers:
  - `dev/scripts/devctl/review_probe_report.py`
  - `dev/scripts/devctl/probe_report_artifacts.py`
  - `dev/scripts/devctl/probe_topology_builder.py`
  - `dev/scripts/devctl/probe_topology_scan.py`
  - `dev/scripts/devctl/probe_topology_packet.py`
  - `dev/config/templates/portable_governance_eval_record.schema.json`
- guard/probe engine entrypoints remain public but should become thin wrappers:
  - `dev/scripts/checks/check_package_layout.py`
  - `dev/scripts/checks/probe_*.py`
  - `dev/scripts/checks/check_*.py`

Exit criteria:

- another repo can run bootstrap, quality-policy, check, probe-report,
  governance-export, and governance-review without patching core code
- one labeled replay/evaluation path can compare rule or policy revisions
  against the same stored evidence set instead of only live scans
- repo-specific behavior comes only from preset/policy/repo-pack files

### Phase 2 - Extract `governance_runtime`

Objective: replace ad-hoc payload shaping with one executable contract layer.

Scope:

- `ControlState`
- `ReviewState`
- `TypedAction`
- `RunRecord`
- `ArtifactStore`
- `ContextPack`
- `ContextBudgetPolicy`
- `Finding`
- `FindingReview`
- `MetricEvent`
- thin-client snapshot contracts such as `MobileStatusSnapshot`,
  `RalphGuardrailState`, `QualityBacklogState`, and `RepoAnalyticsState`
- promotion/demotion and waiver/suppression lifecycle contracts attached to the
  same evidence model

Files to move first:

- current shared runtime seam:
  - `dev/scripts/devctl/runtime/action_contracts.py`
  - `dev/scripts/devctl/runtime/control_state.py`
  - `dev/scripts/devctl/runtime/review_state.py`
  - `dev/scripts/devctl/runtime/review_state_models.py`
  - `dev/scripts/devctl/runtime/review_state_parser.py`
- current action/control seams that should be re-expressed as runtime
  contracts:
  - `dev/scripts/devctl/commands/controller_action.py`
  - `dev/scripts/devctl/controller_action_support.py`
  - `dev/scripts/devctl/commands/mobile_status.py`
  - `dev/scripts/devctl/mobile_status_views.py`
- current artifact/report retention seams that should collapse into
  `ArtifactStore`:
  - `dev/scripts/devctl/reports_retention.py`
  - `dev/scripts/devctl/path_audit.py`
  - `dev/scripts/devctl/path_audit_report.py`
- current finding/review/metric seams that should converge on shared runtime
  evidence contracts:
  - `dev/scripts/devctl/governance_review_models.py`
  - `dev/scripts/devctl/governance_review_log.py`
  - `dev/scripts/devctl/watchdog/models.py`
  - `dev/scripts/devctl/data_science/metrics.py`

Exit criteria:

- typed JSON contracts are versioned and documented as the canonical state/run
  interface
- typed runtime contracts cover context budgets, finding/review/metric events,
  and thin-client snapshot state instead of leaving those shapes ad hoc
- promotion/waiver behavior is defined against the same evidence model used by
  guards, probes, review ledgers, and replay/evaluation tooling
- frontends can render status and submit actions without importing repo-local
  orchestration packages

### Phase 3 - Extract `governance_adapters`

Objective: move provider/workflow/repo-tool integrations behind adapter
interfaces.

Scope:

- `ProviderAdapter`
- `WorkflowAdapter`
- VCS/CI/notifier/environment adapters

Files to move first:

- Ralph and workflow-control seams:
  - `dev/scripts/coderabbit/ralph_ai_fix.py`
  - `dev/scripts/devctl/commands/ralph_status.py`
  - `dev/scripts/devctl/ralph_status_views.py`
  - `dev/scripts/devctl/collect.py`
  - `dev/scripts/devctl/triage/input_sources.py`
  - `dev/scripts/devctl/triage/loop_support.py`
  - `dev/scripts/devctl/commands/triage_loop.py`
  - `dev/scripts/devctl/commands/mutation_loop.py`
- review/workflow bridge seams:
  - `dev/scripts/devctl/review_channel/core.py`
  - `dev/scripts/devctl/review_channel/state.py`
  - `dev/scripts/devctl/review_channel/event_store.py`
  - `dev/scripts/devctl/review_channel/terminal_app.py`
  - `dev/scripts/devctl/commands/review_channel.py`
  - `dev/scripts/checks/workflow_loop_utils.py`
  - `dev/scripts/devctl/loops/comment.py`
- host/process and integration seams:
  - `dev/scripts/devctl/commands/process_cleanup.py`
  - `dev/scripts/devctl/commands/process_audit.py`
  - `dev/scripts/devctl/commands/process_watch.py`
  - `dev/scripts/devctl/commands/integrations_sync.py`
  - `dev/scripts/devctl/commands/integrations_import.py`

Exit criteria:

- Ralph, mutation, review-channel, and process-hygiene flows execute through
  adapter contracts, not direct VoiceTerm-only assumptions
- provider/workflow selection is data-driven and repo-pack aware
- environment detection and external-tool capability checks are consolidated
  through adapter-owned seams instead of scattered `shutil.which()` or
  platform-specific branching

### Phase 4 - Converge `governance_frontends`

Objective: turn every surface into a thin client over runtime contracts.

Scope:

- CLI
- PyQt6 Operator Console
- phone/mobile
- overlay/TUI
- optional MCP

Files to move or rewire first:

- Operator Console readers that must stop importing repo-local orchestration:
  - `app/operator_console/state/review/review_state.py`
  - `app/operator_console/state/review/artifact_locator.py`
  - `app/operator_console/state/bridge/bridge_sections.py`
  - `app/operator_console/state/snapshots/phone_status_snapshot.py`
  - `app/operator_console/state/snapshots/analytics_snapshot.py`
  - `app/operator_console/state/snapshots/quality_snapshot.py`
  - `app/operator_console/state/snapshots/ralph_guardrail_snapshot.py`
  - `app/operator_console/state/snapshots/watchdog_snapshot.py`
  - `app/operator_console/state/snapshots/snapshot_builder.py`
  - `app/operator_console/state/sessions/session_trace_reader.py`
  - `app/operator_console/workflows/workflow_presets.py`
- CLI surfaces that should become frontend wrappers over runtime actions:
  - `dev/scripts/devctl/commands/status.py`
  - `dev/scripts/devctl/commands/report.py`
  - `dev/scripts/devctl/commands/phone_status.py`
  - `dev/scripts/devctl/commands/platform_contracts.py`

Exit criteria:

- frontends import runtime contracts plus repo-pack metadata only
- frontends no longer parse raw review-channel markdown or VoiceTerm-only
  artifact conventions when a typed contract exists
- frontend CI/governance checks block new direct `dev.scripts.devctl`
  orchestration imports in console/UI code once the replacement runtime
  contract exists

### Phase 5 - Define `repo_packs.voiceterm`

Objective: isolate all VoiceTerm-specific defaults in one adopter profile.

Scope:

- path/layout rules
- repo-path resolution / artifact-root metadata
- docs expectations
- branch/release policy
- platform-version compatibility requirements
- schema-version ownership, migration rules, and rollback/back-compat
  expectations for repo-pack-facing payloads
- workflow defaults
- threshold tuning and allowlists

Files to move or consolidate first:

- repo policy and presets:
  - `dev/config/devctl_repo_policy.json`
  - `dev/config/quality_presets/voiceterm.json`
- VoiceTerm-specific docs/runbook contracts:
  - `AGENTS.md`
  - `dev/active/INDEX.md`
  - `dev/active/MASTER_PLAN.md`
  - `dev/guides/DEVELOPMENT.md`
  - `dev/scripts/README.md`
- current hard-coded VoiceTerm defaults that should become repo-pack metadata:
  - `dev/scripts/devctl/review_channel/core.py`
  - `dev/scripts/devctl/review_channel/parser.py`
  - `app/operator_console/workflows/workflow_presets.py`

Exit criteria:

- another repo can adopt the platform by choosing a repo pack rather than
  copying VoiceTerm docs/path logic
- repo packs declare both repo-path roots and `platform_version_requirement`
  metadata so compatibility can be checked before bootstrap or runtime launch
- compatibility validation covers runtime/package compatibility plus
  schema-version migration and rollback expectations instead of only one static
  version pin
- VoiceTerm-specific governance lives outside the portable core

### Phase 6 - External Pilots And Repo Split Gate

Objective: prove the boundaries before creating separate GitHub repos.

Required pilot flow:

1. install the packaged platform
2. validate repo-pack/platform compatibility before bootstrap
3. run bootstrap against a non-VoiceTerm repo
4. select or generate a repo pack
5. run `quality-policy`, `check --adoption-scan`, and `probe-report`
6. render at least one frontend/status surface
7. run at least one governed loop without patching core code
8. publish the install/adoption proof pack: package install steps,
   compatibility contract, and the public whitepaper/comparison derived from
   the durable guide

Split readiness gate:

- two external repos succeed without core-engine patching
- repo-pack/platform compatibility is versioned, enforced, and exercised
  through at least one upgrade path
- no frontend imports repo-local orchestration packages directly
- Ralph/review-channel/process-hygiene run through adapter contracts
- repo-local assumptions live in repo-pack metadata only

Only after those gates pass should the code be split into separate GitHub
repositories.

### Proposed Repo Split After Proof

If the pilot gate passes, split in this order:

1. `governance-core`
2. `governance-runtime` (or fold into `governance-core` if it stays compact)
3. `repo-pack-voiceterm`
4. optional `governance-operator-console`
5. VoiceTerm remains a product integration and first consumer

### Current Anti-Patterns To Burn Down Before Split

These patterns are explicitly not acceptable at repo-split time:

- portable packages deriving identity from `Path(__file__).resolve().parents[3]`
- frontends importing `dev.scripts.devctl.*` orchestration internals directly
- hard-coded `dev/active/*`, `dev/reports/*`, `code_audit.md`, or VoiceTerm MP
  identifiers inside portable layers
- blueprint-only contracts with no executable runtime owner
- loops that require repo-specific shell commands in core logic rather than
  adapter or repo-pack configuration

### Self-Hosting Enforcement Backlog

The current governance stack catches many local clean-code problems but still
misses several platform-boundary failures because those categories do not yet
have first-class guards/probes. "Why didn't the tools catch this?" must now be
treated as a tracked product question, not a post-hoc complaint.

Before calling extraction mature, the platform should self-host these rule
families against its own tree:

- layer-boundary enforcement that blocks frontends from importing
  orchestration internals once runtime contracts exist
- portable-path construction enforcement that rejects raw
  `Path(__file__).resolve().parents[...]` and other VoiceTerm-specific path
  derivation outside approved bootstrap seams
- provider/workflow adapter-routing enforcement that detects direct provider
  CLI or workflow-tool execution where adapter contracts should own the call
- contract-completion/orphaned-contract enforcement so blueprint-only runtime
  contracts do not linger unused in production code
- schema/platform compatibility enforcement covering
  `platform_version_requirement`, `schema_version`, migration, and rollback
  expectations
- repeatable command-source and shell-execution checks for high-signal cases
  where config or user-controlled input can flow into subprocess or shell
  execution without adapter/runtime validation
- Python contract probes for repeatable typed-boundary blind spots that keep
  surfaced findings opaque (`TypedDict`-sized dict payloads, overly broad
  `Any`, untyped unions at dispatch seams) when those patterns remain
  measurable and low-noise

Every time an audit or external review finds a product-boundary defect, the
follow-up should record whether the miss belongs to an existing rule, a new
rule family, richer runtime contracts, or an explicitly out-of-scope category.

## Consolidated Architecture Assessment And Roadmap

This section is the in-repo scope-preservation record for `MP-377`. It pulls
the repo-grounded architecture review, boundary decisions, and staged roadmap
into one active markdown plan so the work is not trapped in chat history or
split across overlapping documents.

### A. Executive Summary

- This assessment is based on the local checked-out repository, not GitHub.
  Inspected: `git status --short`, `AGENTS.md`,
  `dev/active/MASTER_PLAN.md`, `dev/config/devctl_repo_policy.json`,
  `dev/active/ai_governance_platform.md`,
  `dev/guides/AI_GOVERNANCE_PLATFORM.md`,
  `dev/scripts/devctl/platform/contract_definitions.py`,
  `dev/scripts/devctl/runtime/action_contracts.py`.
  Verified: the local worktree is materially ahead of or different from any
  public baseline, including local architecture work across governance docs,
  policy/config, `devctl`, and platform/runtime surfaces.
  Inferred: local codebase reality must override any simpler public-repo mental
  model.
- The strongest architecture already present is broader and better than a
  portable-guards-only framing. Inspected:
  `dev/active/ai_governance_platform.md`,
  `dev/guides/AI_GOVERNANCE_PLATFORM.md`,
  `dev/scripts/devctl/platform/contract_definitions.py`,
  `dev/scripts/devctl/platform/surface_definitions.py`,
  `dev/scripts/devctl/runtime/control_state.py`.
  Verified: the repo already contains a five-layer governance platform thesis
  centered on `governance_core`, `governance_runtime`,
  `governance_adapters`, `governance_frontends`, and `repo_packs`, plus
  CLI-first determinism, typed runtime contracts, repo-pack policy layering,
  PyQt thin-client intent, and optional MCP alignment.
  Inferred: the right move is extraction and consolidation, not reinvention.
- Recommended direction: make the standalone governance product the primary
  architecture now, preserve `devctl` as the core, promote the repo-pack
  model, generate policy surfaces from one canonical config, move VoiceTerm to
  consumer/integration status, and defer DB-first / ML-first work until the
  package boundary and documentation authority are stable.

### B. Current Codebase Assessment

- The repo is already two intertwined systems: a VoiceTerm runtime/product and
  an embedded governance/control-plane product.
  Inspected: `dev/scripts/devctl.py`, `dev/scripts/devctl/cli.py`,
  `app/operator_console/README.md`,
  `rust/src/bin/voiceterm/memory/store/sqlite.rs`,
  `dev/active/ai_governance_platform.md`.
  Verified: the governance stack is not just helper scripts.
  Inferred: it should stop being treated as an internal VoiceTerm subsystem.
- The local worktree itself is an architectural signal.
  Inspected: `git status --short`, `dev/scripts/devctl/platform/`,
  `dev/scripts/devctl/runtime/`, `dev/scripts/checks/package_layout/`,
  `dev/scripts/coderabbit/`, `dev/scripts/workflow_bridge/`.
  Verified: there is local-only and in-flight architecture work.
  Inferred: recommendations that ignore the dirty local tree will be wrong.
- The authority stack is clear at the top and fragmented below.
  Inspected: `AGENTS.md`, `CLAUDE.md`, `dev/active/INDEX.md`,
  `dev/active/MASTER_PLAN.md`, `dev/active/portable_code_governance.md`,
  `dev/active/ai_governance_platform.md`.
  Verified: `AGENTS -> INDEX -> MASTER_PLAN` is the declared authority chain.
  Inferred: the next problem is not missing governance, it is fragmented
  governance.
- The current implementation style is thin-client, artifact-backed, and
  command-driven.
  Inspected: `app/operator_console/state/snapshots/snapshot_builder.py`,
  `app/operator_console/workflows/command_builder_core.py`,
  `dev/scripts/devctl/commands/check.py`,
  `dev/scripts/devctl/runtime/control_state.py`.
  Verified: the code already prefers deterministic commands and file-backed
  artifacts.
  Inferred: the standalone product should standardize that model rather than
  replace it with an app-centric backend.

### C. What Already Exists

- `CLI-first source of truth`: already implemented.
  Inspected: `dev/scripts/devctl.py`, `dev/scripts/devctl/cli.py`,
  `dev/scripts/devctl/commands/check.py`,
  `dev/scripts/devctl/bundle_registry.py`.
  Verified: `devctl` owns command parsing, policy resolution, checks, bundles,
  and post-command telemetry.
  Inferred: this is the right extraction nucleus.
- `Deterministic analyzers, guards, and probes`: already implemented.
  Inspected: `dev/scripts/devctl/quality_policy_defaults.py`,
  `dev/scripts/devctl/quality_policy.py`,
  `dev/scripts/checks/check_code_shape.py`,
  `dev/scripts/checks/check_package_layout.py`,
  `dev/scripts/checks/probe_compatibility_shims.py`.
  Verified: the repo currently resolves 28 AI guards and 15 review probes in
  the active policy.
  Inferred: the core product claim already exists.
- `Repo-pack style policy layering`: partially implemented.
  Inspected: `dev/config/devctl_repo_policy.json`,
  `dev/config/quality_presets/portable_python.json`,
  `dev/config/quality_presets/portable_rust.json`,
  `dev/config/quality_presets/portable_python_rust.json`,
  `dev/config/quality_presets/voiceterm.json`,
  `dev/scripts/devctl/platform/contract_definitions.py`.
  Verified: presets, repo overrides, and a `RepoPack` contract already exist.
  Inferred: this needs to become a first-class package/install surface.
- `Generated agent surfaces from canonical policy`: partially implemented.
  Inspected: `dev/scripts/checks/check_agents_bundle_render.py`,
  `dev/scripts/checks/check_agents_contract.py`, `AGENTS.md`, `CLAUDE.md`,
  `dev/scripts/devctl/bundle_registry.py`.
  Verified: only the AGENTS bundle surface is rendered and checked;
  `CLAUDE.md` remains manual/local-only.
  Inferred: the repo does not yet have the single-source generation model we
  need.
- `Thin skills/templates`: partially implemented.
  Inspected: `dev/templates/slash/README.md`,
  `dev/templates/slash/claude/SKILL.md`,
  `dev/templates/slash/codex/voice.md`.
  Verified: the repo already uses thin skill/slash templates as adapters over
  real runtime commands.
  Inferred: this is the right model to generalize.
- `Hooks as deterministic enforcement`: implemented but should be redesigned.
  Inspected: `.pre-commit-config.yaml`,
  `.github/workflows/tooling_control_plane.yml`,
  `.github/workflows/release_preflight.yml`, `.git/hooks`.
  Verified: enforcement exists via `devctl`, CI, and optional pre-commit;
  `.git/hooks` is not the real system boundary.
  Inferred: future hook surfaces should be generated adapters, not assumed
  local git-hook state.
- `Structured telemetry and history`: partially implemented.
  Inspected: `dev/scripts/devctl/audit_events.py`,
  `dev/scripts/devctl/governance_review_log.py`,
  `dev/scripts/devctl/review_probe_report.py`,
  `dev/scripts/devctl/watchdog/episode.py`,
  `dev/scripts/devctl/data_science/metrics.py`,
  `dev/reports/governance/finding_reviews.jsonl`,
  `dev/reports/data_science/history/snapshots.jsonl`.
  Verified: the repo already has multiple durable JSONL/NDJSON ledgers.
  Inferred: a canonical artifact/event-store contract is needed before a
  heavier database layer.
- `Database-backed system of record`: missing.
  Inspected: repo-wide sqlite usage,
  `rust/src/bin/voiceterm/memory/store/sqlite.rs`,
  `integrations/code-link-ide/docs/spec/audit-log.md`, local `orb.db`.
  Verified: there is no repo-wide governance DB in active use.
  Inferred: JSONL plus optional SQLite index is the right near-term target.
- `PyQt6 observability layer`: already implemented but should be redesigned.
  Inspected: `app/operator_console/README.md`,
  `app/operator_console/views/main_window.py`,
  `app/operator_console/views/ui_refresh.py`,
  `app/operator_console/state/snapshots/analytics_snapshot.py`,
  `app/operator_console/state/snapshots/phone_status_snapshot.py`.
  Verified: the UI is real and useful.
  Inferred: it must stop importing repo-local internals and hard-coding
  VoiceTerm paths if it is to become a reusable frontend.
- `Typed runtime contracts`: partially implemented.
  Inspected: `dev/scripts/devctl/runtime/action_contracts.py`,
  `dev/scripts/devctl/runtime/control_state.py`,
  `dev/scripts/devctl/runtime/review_state.py`,
  `dev/scripts/devctl/platform/contract_definitions.py`.
  Verified: `TypedAction`, `RunRecord`, `ArtifactStore`, `ControlState`, and
  `ReviewState` exist already.
  Inferred: those seams should become the actual dependency direction, not
  just blueprint docs.
- `Optional MCP`: already implemented in the right posture.
  Inspected: `dev/scripts/devctl/commands/mcp.py`,
  `dev/guides/MCP_DEVCTL_ALIGNMENT.md`,
  `dev/active/slash_command_standalone.md`.
  Verified: current MCP is read-only/additive and explicitly not the authority
  layer.
  Inferred: keep it optional and late.
- `Safe remediation loops`: partially implemented.
  Inspected: `dev/scripts/coderabbit/ralph_ai_fix.py`,
  `dev/scripts/devctl/commands/triage_loop.py`,
  `dev/scripts/devctl/commands/mutation_loop.py`,
  `dev/scripts/devctl/commands/autonomy_loop.py`,
  `dev/config/control_plane_policy.json`.
  Verified: the repo already has bounded refinement/fix loops with policy
  gates.
  Inferred: these belong in an adapter/orchestration layer, not in the core
  rule engine.
- `ML later, not enforcement`: partially implemented in the right direction.
  Inspected: `dev/scripts/devctl/data_science/metrics.py`,
  `dev/config/templates/portable_governance_episode.schema.json`,
  `dev/config/templates/portable_governance_finding_review.schema.json`,
  `dev/guides/PORTABLE_CODE_GOVERNANCE.md`.
  Verified: telemetry, evaluation records, and finding ledgers already exist.
  Inferred: the substrate for later ranking exists without letting ML replace
  deterministic checks.

### C.5. Other Architectural Patterns Already Present In The Repo

- `Review-channel collaboration runtime`: preserve and merge into the
  standalone runtime as a collaboration/approval subsystem.
  Inspected: `dev/scripts/devctl/review_channel/event_store.py`,
  `dev/scripts/devctl/review_channel/state.py`,
  `app/operator_console/collaboration/conversation_state.py`,
  `app/operator_console/collaboration/task_board_state.py`,
  `app/operator_console/collaboration/timeline_builder.py`.
  Verified: collaboration packets, approvals, and session views already exist.
  Inferred: this is a product differentiator the original prompt
  underestimated.
- `Continuous swarm / rollover / shared-screen workflow`: preserve, but keep
  it above the core engine.
  Inspected: `dev/active/continuous_swarm.md`,
  `dev/active/review_channel.md`,
  `dev/scripts/devctl/commands/review_channel.py`.
  Verified: the repo already has a serious multi-agent orchestration model.
  Inferred: it should become a reusable workflow-adapter layer.
- `Host-process hygiene and execution cleanup`: preserve as an optional
  extension.
  Inspected: `dev/scripts/devctl/commands/process_cleanup.py`,
  `dev/scripts/devctl/commands/process_audit.py`,
  `dev/scripts/devctl/commands/process_watch.py`,
  `dev/active/host_process_hygiene.md`.
  Verified: process hygiene is already a governed subsystem.
  Inferred: keep it repo-pack or platform-extension scoped, not mandatory for
  every adopter.
- `Memory + Action Studio`: preserve separately and do not collapse it into the
  governance core.
  Inspected: `dev/active/memory_studio.md`,
  `rust/src/bin/voiceterm/memory/store/sqlite.rs`,
  `rust/src/devtools/events.rs`, `rust/src/devtools/storage.rs`.
  Verified: there is already a parallel structured-memory architecture.
  Inferred: share event-store ideas, but do not let memory broaden the first
  standalone-governance scope.
- `Federated import/reuse model`: preserve as reference/import tooling, not a
  runtime dependency.
  Inspected: `dev/integrations/EXTERNAL_REPOS.md`,
  `dev/scripts/devctl/commands/integrations_sync.py`,
  `integrations/ci-cd-hub/pyproject.toml`,
  `integrations/code-link-ide/docs/spec/audit-log.md`.
  Verified: the repo already studies and reuses external patterns in a
  disciplined way.
  Inferred: that helps extraction, but submodules must not become the package
  boundary.
- `Graph/report/topology observability`: preserve and use as the basis for
  explainability.
  Inspected: `dev/scripts/devctl/probe_report_artifacts.py`,
  `dev/reports/probes/latest/review_packet.md`,
  `dev/reports/probes/latest/hotspots.mmd`.
  Verified: graph/topology outputs already exist.
  Inferred: the PyQt6 UI should consume these instead of inventing its own
  ranking logic.

### D. Gaps And Architectural Problems

- There is no single canonical architecture document today unless this plan is
  explicitly used that way.
  Inspected: `dev/active/portable_code_governance.md`,
  `dev/active/ai_governance_platform.md`,
  `dev/guides/PORTABLE_CODE_GOVERNANCE.md`,
  `dev/guides/AI_GOVERNANCE_PLATFORM.md`.
  Verified: architecture is split across two active plans and two durable
  guides.
  Inferred: consolidation is not optional.
- Execution state is distributed even though `MASTER_PLAN` is supposed to be
  singular tracker authority.
  Inspected: `dev/active/MASTER_PLAN.md`, `dev/active/operator_console.md`,
  `dev/active/autonomous_control_plane.md`,
  `dev/active/review_channel.md`, `dev/active/review_probes.md`.
  Verified: multiple scope docs still carry live checklist/progress state.
  Inferred: contributors can follow the wrong plan even while obeying docs.
- Surface generation is incomplete.
  Inspected: `dev/scripts/checks/check_agents_bundle_render.py`, `CLAUDE.md`,
  `dev/templates/slash/claude/SKILL.md`.
  Verified: AGENTS bundle rendering exists, but no general
  `AGENTS` / `CLAUDE` / skills / hooks generator does.
  Inferred: drift remains structurally likely.
- The artifact model is structured but fragmented.
  Inspected: `dev/scripts/devctl/audit_events.py`,
  `dev/scripts/devctl/governance_review_log.py`,
  `dev/scripts/devctl/review_probe_report.py`,
  `dev/scripts/devctl/watchdog/episode.py`,
  `dev/scripts/devctl/review_channel/event_store.py`.
  Verified: there are multiple ledgers with overlapping semantics.
  Inferred: a canonical run/finding/artifact model is needed before a DB or
  more dashboards.
- Portability blockers are real and concrete.
  Inspected: `app/operator_console/state/snapshots/analytics_snapshot.py`,
  `app/operator_console/state/snapshots/quality_snapshot.py`,
  `dev/scripts/devctl/metric_writers.py`,
  `dev/scripts/devctl/governance_export_support.py`.
  Verified: parts of the system assume the current repo root or home-directory
  paths.
  Inferred: extraction will fail unless those assumptions move behind
  repo-pack/runtime contracts.
- The package layout itself says extraction is overdue.
  Inspected: `dev/scripts/checks/check_package_layout.py` plus current output,
  `dev/scripts/checks/probe_compatibility_shims.py` plus current output.
  Verified: crowded directories include `dev/scripts/checks`,
  `dev/scripts/devctl`, and `dev/scripts/devctl/commands`, and root shim debt
  still exceeds budget.
  Inferred: the codebase is already telling us to split the platform cleanly.
- Repo policy shape is brittle.
  Inspected: `dev/config/devctl_repo_policy.json`,
  `dev/scripts/devctl/quality_policy_loader.py`.
  Verified: the policy file currently has duplicate top-level
  `repo_governance` keys and the loader path does not reject that by contract.
  Inferred: canonical policy generation will remain fragile until both the
  file and loader are normalized.

### D.5. Separation And Repo-Boundary Analysis

- What should be extracted first is the real portable core.
  Inspected: `dev/scripts/devctl/quality_policy.py`,
  `dev/scripts/devctl/quality_policy_defaults.py`,
  `dev/scripts/devctl/commands/check.py`,
  `dev/scripts/devctl/commands/governance/export.py`,
  `dev/scripts/devctl/commands/governance/bootstrap.py`,
  `dev/scripts/devctl/commands/governance/review.py`,
  `dev/scripts/checks/`.
  Verified: these are already mostly productized.
  Inferred: they belong in the standalone repo before frontends move.
- What can remain temporarily bridged is VoiceTerm-specific integration.
  Inspected: `pypi/src/voiceterm/cli.py`, `app/operator_console/`,
  Rust overlay/runtime code, `.github/workflows/`.
  Verified: these are product/integration layers, not the governance core.
  Inferred: they should consume the extracted platform, not host it.
- The biggest blockers to extraction are direct imports and path assumptions.
  Inspected: `app/operator_console/state/snapshots/analytics_snapshot.py`,
  `app/operator_console/state/snapshots/phone_status_snapshot.py`,
  `app/operator_console/workflows/command_builder_core.py`,
  `dev/scripts/devctl/governance_export_support.py`.
  Verified: clients and export code still assume this repo's filesystem layout.
  Inferred: a package boundary without contract cleanup would only move the
  coupling elsewhere.
- VoiceTerm's future consumption model should be external CLI/API plus repo
  pack, not internal module imports.
  Inspected: `dev/scripts/devctl/platform/contract_definitions.py`,
  `dev/scripts/devctl/runtime/action_contracts.py`,
  `dev/config/devctl_repo_policy.json`.
  Verified: the needed contracts already exist in seed form.
  Inferred: VoiceTerm should call the standalone system the same way another
  repo would.
- Avoid drift by making repo packs versioned and tested.
  Inspected: `dev/scripts/devctl/commands/quality_policy.py`,
  `dev/scripts/devctl/commands/platform_contracts.py`,
  `dev/scripts/checks/check_architecture_surface_sync.py`.
  Verified: the repo already has contract-oriented validation habits.
  Inferred: use that to pin repo-pack/platform compatibility.

### D.6. Documentation / Planning Fragmentation Analysis

- Keep `dev/active/MASTER_PLAN.md` as the tracker only.
  Verified from `AGENTS.md` and `dev/active/INDEX.md`: it is the canonical
  execution tracker.
  Inferred: it should stop doubling as a partial architecture document.
- Make `dev/active/ai_governance_platform.md` the single active architecture
  plan for the standalone product.
  Verified: it already owns the broader reusable-platform lane.
  Inferred: it is the strongest candidate for consolidation and should be the
  main plan for this scope.
- Fold `dev/active/portable_code_governance.md` into a narrower engine-focused
  companion role rather than keeping it as peer architecture authority.
  Verified: it overlaps heavily with the broader platform plan.
  Inferred: keeping both as peers will keep causing drift.
- Make `dev/guides/AI_GOVERNANCE_PLATFORM.md` the single durable architecture
  guide for the standalone product.
  Verified: it already states the five-layer thesis.
  Inferred: `dev/guides/PORTABLE_CODE_GOVERNANCE.md` should narrow to
  repo-adoption and engine-usage guidance.
- Keep `dev/guides/ARCHITECTURE.md` as VoiceTerm product architecture, not
  governance-platform architecture.
  Verified: it is broader repo architecture.
  Inferred: mixing it with the extracted product architecture will blur the
  boundary again.
- Replace manual instruction surfaces with generated ones.
  Inspected: `AGENTS.md`, `CLAUDE.md`, `dev/templates/slash/claude/SKILL.md`.
  Verified: these are currently separate human-maintained surfaces.
  Inferred: this is the most preventable source of future drift.

### E. Recommended Architecture

Verified basis: `dev/active/ai_governance_platform.md`,
`dev/guides/AI_GOVERNANCE_PLATFORM.md`,
`dev/scripts/devctl/platform/contract_definitions.py`,
`dev/scripts/devctl/runtime/action_contracts.py`,
`dev/scripts/devctl/runtime/control_state.py`.

Recommended target:

```text
governance_core/
  policy/
  guards/
  probes/
  docs_governance/
  bootstrap/
  export/
  review_ledger/
governance_runtime/
  contracts/
  actions/
  artifact_store/
  run_history/
  collaboration/
governance_adapters/
  providers/
  workflows/
  vcs/
  hooks/
  notifications/
governance_frontends/
repo_packs/
  voiceterm/
  ci_cd_hub/
  templates/
docs/
  ARCHITECTURE.md
  ADOPTION.md
  REPO_PACKS.md
  RUNBOOKS/
```

- Canonical config design: extend the current repo-policy model, do not
  replace it with a new philosophy. Use one repo-pack config as the source of
  truth for policy, scopes, docs manifests, workflow mappings, risk add-ons,
  instruction surfaces, skill templates, and hook profiles. Start from
  `dev/config/devctl_repo_policy.json` and the preset chain under
  `dev/config/quality_presets/`; normalize it into one schema with no
  duplicate-key ambiguity.
- Generated file strategy: add one renderer command that emits `AGENTS.md`,
  `CLAUDE.md`, skill/slash templates, pre-commit fragments, and CI workflow
  stubs from repo-pack config plus templates. Reuse the current
  bundle-rendering pattern from
  `dev/scripts/checks/check_agents_bundle_render.py`, but expand it to
  whole-surface generation.
- CLI command surface: keep CLI as the product core. The minimal stable surface
  should be `check`, `probe-report`, `quality-policy`,
  `governance-bootstrap`, `governance-export`, `governance-review`,
  `platform-contracts`, `render-surfaces`, `artifacts status`,
  `artifacts gc`, and optional loops.
- Database/event schema: structured artifacts should be the system of record
  and markdown a derived view. Near term, standardize on append-only
  JSONL/NDJSON plus schemas for `TypedAction`, `RunRecord`, `Finding`,
  `FindingReview`, `ArtifactManifest`, `Packet`, and `MetricEvent`, with an
  optional SQLite index later for query speed.
- Session continuity and audit/event history must stay separate:
  - active-plan markdown (`Session Resume`, `Progress Log`) is the canonical
    "left off here" surface for AI and maintainer handoff;
  - transitional shared-markdown coordination surfaces such as the current
    review-channel bridge remain human/agent projections and bootstrap aids,
    not the long-term system of record;
  - structured ledgers (`devctl_events.jsonl`, `finding_reviews.jsonl`,
    watchdog episodes, swarm/benchmark summaries) are the machine-readable
    runtime evidence that later rolls into `RunRecord` / `ArtifactStore`,
    optional SQLite indexing, and ML/ranking inputs.
- PyQt6 UI architecture: keep PyQt6, but make it a pure client over runtime
  contracts or CLI JSON responses. No direct repo-local imports, no hard-coded
  repo-root assumptions, no private filesystem contracts.
- ML later: add ML only as an advisory layer over telemetry and governance
  review artifacts for ranking and prioritization. It must not replace
  deterministic gates.
- MCP later: keep MCP read-only and optional. If write-capable MCP exists
  later, route it through the same typed action and approval contracts as the
  CLI, not a separate control plane.
- Separation boundary: VoiceTerm becomes one repo pack plus client
  integrations. It can ship a wrapper CLI, overlay integration, and optional
  Operator Console skin, but it should consume the governance platform the
  same way any other adopter does.
- Canonical docs structure after extraction: one `ARCHITECTURE.md` for product
  design, one tracker document for active execution, one repo-pack guide, and
  generated instruction surfaces. Do not repeat architecture ownership across
  multiple active plans once extracted.

### E.5. Missing Gaps, Blind Spots, And Scope Corrections

- Missing capability: a real install/upgrade story for the governance
  platform.
  Inspected: `dev/scripts/devctl/governance_export_support.py`,
  `dev/scripts/devctl/governance_bootstrap_support.py`.
  Verified: export/bootstrap is snapshot-oriented, not package-oriented.
  Inferred: packaging is the first product gap.
- Missing boundary: a stable service/API between core/runtime and frontends.
  Inspected: `dev/scripts/devctl/platform/contract_definitions.py`,
  `app/operator_console/state/snapshots/analytics_snapshot.py`.
  Verified: contracts exist, but clients still read raw artifacts and internals.
  Inferred: this needs an explicit backend protocol.
- Missing scaling plan: multi-repo contract tests and adopter fixtures.
  Inspected: `dev/scripts/devctl/commands/governance/bootstrap.py`,
  `dev/guides/PORTABLE_CODE_GOVERNANCE.md`,
  `integrations/ci-cd-hub/pyproject.toml`.
  Verified: adoption thinking exists.
  Inferred: the product still needs a formal pilot matrix beyond VoiceTerm.
- Missing model: a unified artifact taxonomy and retention policy.
  Inspected: `dev/scripts/devctl/reports_retention.py`,
  `dev/scripts/devctl/watchdog/episode.py`,
  `dev/scripts/devctl/review_channel/event_store.py`.
  Verified: retention and artifacts exist piecemeal.
  Inferred: extraction needs one artifact-store contract.
- Missing boundary: one explicit audit/event model that tells contributors
  which data belongs in plan markdown versus structured ledgers.
  Inspected: `dev/scripts/devctl/audit_events.py`,
  `dev/scripts/devctl/governance_review_log.py`,
  `dev/audits/METRICS_SCHEMA.md`, `dev/guides/DEVELOPMENT.md`.
  Verified: command telemetry and finding adjudication are already durable
  JSONL ledgers, but the repo has not stated clearly enough that session
  continuity belongs in plan markdown while those ledgers serve runtime
  evidence, metrics, and later DB/ML ingestion.
  Inferred: extraction needs that distinction to stay explicit so a future
  database does not become a dumping ground for prose handoff.
- Missing coverage: broader full-codebase and full-cycle evidence before the
  repo can make strong accuracy claims.
  Inspected: `dev/audits/2026-02-24-autonomy-baseline-audit.md`,
  `dev/scripts/devctl/watchdog/episode.py`,
  `dev/guides/PORTABLE_CODE_GOVERNANCE.md`.
  Verified: the repo has `--adoption-scan`, guarded-coding episode logging, and
  a baseline full-surface audit runbook, but current adjudication evidence is
  still concentrated in a narrow set of probe findings and a small watchdog
  sample.
  Inferred: we need repeated full-worktree audit cycles plus richer watchdog
  coverage before "near-100% accuracy" is a defensible claim.
- Missing policy: false positives should trigger root-cause remediation, not
  just ledger accounting.
  Inspected: `dev/scripts/devctl/governance_review_log.py`,
  `dev/guides/DEVELOPMENT.md`, `AGENTS.md`.
  Verified: the repo records false-positive verdicts, but it has not yet made
  "why was this wrong and how do we narrow it?" an explicit execution
  requirement.
  Inferred: the platform should treat false positives as rule-quality defects
  until proven otherwise.
- Missing context-budget contract: the platform does not yet treat AI-context
  usage as a first-class bounded runtime resource.
  Inspected: `dev/active/ai_governance_platform.md`,
  `dev/active/portable_code_governance.md`,
  `dev/guides/AI_GOVERNANCE_PLATFORM.md`,
  `dev/config/templates/portable_governance_episode.schema.json`.
  Verified: the current plan emphasizes findings, evidence, and portability,
  but it does not yet define mode-specific context budgets, overflow behavior,
  or prompt-usage telemetry as product requirements.
  Inferred: without explicit context contracts, the platform could improve code
  quality while becoming too expensive or too large-context to use in practice.
- Missing metric: adjudication coverage, not just adjudication outcome.
  Inspected: `dev/scripts/devctl/governance_review_log.py`,
  `dev/scripts/devctl/data_science/metrics.py`,
  `dev/reports/governance/latest/review_summary.json`.
  Verified: the repo reports false-positive and cleanup rates for reviewed
  findings, but it does not yet expose how much of the guard/probe surface is
  still unreviewed by signal family, repo, or scan mode.
  Inferred: strong quality claims need "coverage of reviewed findings" metrics,
  not only "quality of reviewed findings" metrics.
- Missing DB-readiness contract: schema migration and provenance strategy for
  the eventual structured store.
  Inspected: `dev/scripts/devctl/runtime/action_contracts.py`,
  `dev/scripts/devctl/platform/contract_definitions.py`,
  `dev/scripts/devctl/watchdog/models.py`,
  `dev/config/templates/portable_governance_eval_record.schema.json`.
  Verified: the repo already uses `schema_version`, `run_id`,
  `controller_run_id`, `session_id`, `repo_pack_id`, and retention metadata in
  several places, but the future database plan does not yet say which fields
  are canonical, how migrations are handled, or how JSONL backfill maps into
  DB tables.
  Inferred: the platform needs a formal ingestion/provenance contract before a
  database layer lands.
- Missing privacy/redaction rule for the future event store and ML corpus.
  Inspected: `dev/guides/ARCHITECTURE.md`,
  `dev/scripts/devctl/audit_events.py`,
  `dev/scripts/devctl/watchdog/episode.py`.
  Verified: the repo already stores command args, paths, provider/session IDs,
  and other provenance-bearing fields in structured artifacts.
  Inferred: we need explicit redaction/privacy policy before scaling that data
  into a richer DB or ML-ranking corpus.
- Missing promotion criteria for hard guards versus advisory probes.
  Inspected: `AGENTS.md`, `dev/scripts/devctl/quality_policy_defaults.py`,
  `dev/scripts/devctl/governance_review_log.py`.
  Verified: the repo distinguishes blocking guards from advisory probes, but it
  does not yet define a measured graduation rule tied to false-positive rate,
  cleanup rate, sample size, and adoption-scan stability.
  Inferred: the platform needs one explicit promotion/demotion rubric so noisy
  heuristics do not silently harden into blockers.
- Missing evaluation corpus and replay harness for rule-quality regression.
  Inspected: `dev/config/templates/portable_governance_eval_record.schema.json`,
  `dev/guides/PORTABLE_CODE_GOVERNANCE.md`,
  `dev/scripts/devctl/data_science/metrics.py`,
  `dev/reports/autonomy/benchmarks/`.
  Verified: the repo already has evaluation-record schema support, benchmark
  artifacts, and telemetry rollups, but it does not yet define one curated
  cross-repo corpus or replay flow that can compare rule/policy versions
  against the same labeled evidence set.
  Inferred: before stronger accuracy claims, DB expansion, or ML-assisted
  ranking, the platform needs a repeatable regression harness that measures
  guard/probe quality across stable inputs instead of only live current-repo
  scans.
- Missing waiver/suppression lifecycle for noisy-but-known signals.
  Inspected: `AGENTS.md`,
  `dev/scripts/devctl/governance_review_log.py`,
  `dev/scripts/devctl/quality_policy_defaults.py`,
  `dev/scripts/devctl/rust_audit/catalog.py`,
  `dev/scripts/devctl/script_catalog.py`.
  Verified: the repo already has waiver/approval concepts, suppression-debt
  guards, and adjudicated review logging, but the standalone platform plan does
  not yet define one lifecycle for waivers/allowlists/suppressions with owner,
  reason, expiry, and reevaluation triggers.
  Inferred: if false positives are handled ad hoc, the system will accumulate
  silent exceptions and lose the very determinism/credibility it is trying to
  preserve.
- Missing completion gate: the repo does not yet state sharply enough that the
  product is unfinished until architecture, pipeline, and evidence quality are
  all proven together.
  Inspected: `dev/active/MASTER_PLAN.md`,
  `dev/guides/AI_GOVERNANCE_PLATFORM.md`,
  `.github/workflows/tooling_control_plane.yml`,
  `dev/scripts/devctl/bundle_registry.py`.
  Verified: the roadmap and checks exist, but the plan previously left too much
  room for "split the repo and call it done" thinking.
  Inferred: the platform needs explicit completion gates so extraction,
  pipeline parity, reviewed evidence, and telemetry trust all count as closure
  criteria.
- Missing pattern-mining program: broader Python/Rust discovery is implied, but
  not yet stated as a standing execution loop in the product plan.
  Inspected: `dev/active/portable_code_governance.md`,
  `dev/guides/PORTABLE_CODE_GOVERNANCE.md`,
  `dev/reports/governance/latest/`,
  `dev/scripts/devctl/data_science/metrics.py`.
  Verified: the repo has evidence surfaces, evaluation schema, and pilot-corpus
  intent, but the broader product plan does not yet say "keep mining repeated
  low-noise patterns from this repo and external repos, especially in Python
  and Rust, until the rule families are much stronger."
  Inferred: the differentiation from generic AI review tools depends on a
  repeatable mining -> probe -> adjudication -> promotion loop, not a one-time
  initial guard set.
- Missing language-extension contract: the plan says the product should expand
  beyond Python/Rust later, but it does not yet define how new language support
  fits the same architecture.
  Inspected: `dev/config/quality_presets/portable_python.json`,
  `dev/config/quality_presets/portable_rust.json`,
  `dev/config/quality_presets/portable_python_rust.json`,
  `dev/scripts/devctl/quality_policy_defaults.py`,
  `dev/scripts/devctl/platform/contract_definitions.py`.
  Verified: the current policy/preset stack already implies a language-aware
  model for Python/Rust.
  Inferred: before new languages arrive, the platform should formalize a
  language-pack/analyzer-module contract so future Swift/TypeScript/etc. reuse
  the same finding schemas, policy resolution, review ledger, and telemetry
  model instead of spawning ad hoc subsystems.
- Assumption to validate: whether JSONL plus optional SQLite is enough for the
  first standalone version.
  Inspected: `dev/scripts/devctl/audit_events.py`,
  `integrations/code-link-ide/docs/spec/audit-log.md`.
  Verified: the repo already succeeds with structured flat-file ledgers.
  Inferred: do not force a DB before query pain justifies it.
- Prototype before full build-out: run the extracted package against VoiceTerm
  and one non-VoiceTerm adopter such as `ci-cd-hub`, using the same repo-pack
  renderer and check surface. That is the shortest way to validate the
  boundary.

### F. Prioritized Implementation Roadmap

- `Phase 1 - Consolidate authority and architecture docs`
  Goal: create one coherent architecture path before more code moves.
  Why it matters: the main failure mode now is plan drift, not missing intent.
  Files/modules: `dev/active/ai_governance_platform.md`,
  `dev/active/portable_code_governance.md`,
  `dev/guides/AI_GOVERNANCE_PLATFORM.md`,
  `dev/guides/PORTABLE_CODE_GOVERNANCE.md`,
  `dev/active/INDEX.md`, `dev/active/MASTER_PLAN.md`.
  Deliverables: one active architecture plan, one durable architecture guide,
  updated index/router language.
  Acceptance criteria: `check_active_plan_sync`,
  `docs-check --strict-tooling`, and
  `check_architecture_surface_sync` pass, and no second peer architecture doc
  remains active.
- `Phase 2 - Normalize repo-pack policy and surface generation`
  Goal: make one canonical config the source for policy plus generated
  instruction surfaces.
  Files/modules: `dev/config/devctl_repo_policy.json`,
  `dev/scripts/devctl/quality_policy.py`,
  `dev/scripts/devctl/quality_policy_defaults.py`,
  `dev/scripts/checks/check_agents_bundle_render.py`,
  `AGENTS.md`, `CLAUDE.md`, `dev/templates/slash/`.
  Deliverables: `render-surfaces` command, generation checks, and repo-pack
  context-budget profiles with usage-tier documentation hooks.
  Acceptance criteria: `AGENTS.md`, `CLAUDE.md`, slash/skill templates, and
  hook/config stubs regenerate cleanly from policy, and repo-pack config can
  declare bounded context modes without patching orchestration code.
- `Phase 3 - Harden the portable core inside the current repo`
  Goal: reduce shim debt and make platform/runtime packages the real internal
  boundary.
  Files/modules: `dev/scripts/devctl/platform/`,
  `dev/scripts/devctl/runtime/`, `dev/scripts/devctl/repo_policy.py`,
  `dev/scripts/devctl/governance/bootstrap_policy.py`,
  `dev/scripts/devctl/data_science/metrics.py`,
  `dev/scripts/checks/check_package_layout.py`,
  `dev/scripts/checks/probe_compatibility_shims.py`.
  Deliverables: lower shim count, lower crowded-root counts, cleaner package
  boundaries, and the first context-usage telemetry path wired into runtime
  evidence.
  Acceptance criteria: shim probe falls materially, package-layout pressure
  drops, and governed runs emit bounded context telemetry rather than hiding
  prompt size inside provider-specific logs.
- `Phase 4 - Extract the standalone repository and package`
  Goal: create the standalone governance product without breaking VoiceTerm.
  Files/modules: portable slices of `dev/scripts/devctl/`,
  `dev/scripts/checks/`, `dev/config/quality_presets/`,
  `dev/config/templates/`.
  Deliverables: installable standalone repo, versioned CLI, VoiceTerm repo pack.
  Acceptance criteria: VoiceTerm can run the extracted CLI locally and at
  least one second repo can adopt it through bootstrap.
- `Phase 5 - Rebind frontends and loops to the extracted runtime`
  Goal: make UI, MCP, and loops clients of the new platform rather than
  private in-repo consumers.
  Files/modules: `app/operator_console/`,
  `dev/scripts/devctl/commands/mcp.py`,
  `dev/scripts/devctl/commands/triage_loop.py`,
  `dev/scripts/devctl/commands/mutation_loop.py`,
  `dev/scripts/devctl/commands/autonomy_loop.py`.
  Deliverables: reusable PyQt client, stable runtime API, adapter-based loops.
  Acceptance criteria: Operator Console can point at the extracted runtime and
  VoiceTerm behaves as one consumer, not the host.

### F.5. Standalone-Repo Migration Roadmap

- Extract first: policy resolution, guard/probe registry, checks, docs
  governance, bootstrap/export/review, runtime contracts, and artifact-store
  code from `dev/scripts/devctl/` and `dev/scripts/checks/`. Temporary bridge:
  keep `dev/scripts/devctl.py` as a wrapper that calls the installed
  standalone package.
- Keep temporarily bridged: VoiceTerm-specific repo pack config, release
  workflows, Operator Console skin, and Rust overlay/mobile integration under
  `dev/config/`, `.github/workflows/`, `app/operator_console/`, and
  `pypi/src/voiceterm/cli.py`.
- Replace direct coupling with interfaces: CLI entrypoints, repo-pack configs,
  typed JSON contracts, generated instruction surfaces, and optionally a
  Python package API. Avoid future imports from
  `VoiceTerm -> dev.scripts.devctl.*` once extraction starts.
- VoiceTerm after extraction should consume the system by installing the
  governance package, shipping a `voiceterm` repo pack, invoking checks and
  exports via CLI/API, and using generated instruction surfaces. VoiceTerm
  should stop being the permanent filesystem host for platform code.
- Prevent drift after separation with contract tests and version pinning.
  VoiceTerm should pin a platform version and repo-pack version, and CI should
  validate `platform-contracts`, `quality-policy`, and `render-surfaces`
  compatibility on every update.

### F.6. Documentation Consolidation Roadmap

- Merge or subordinate `dev/active/portable_code_governance.md` beneath this
  plan. One active full-product architecture plan only.
- Merge durable architecture content into
  `dev/guides/AI_GOVERNANCE_PLATFORM.md`; retain
  `dev/guides/PORTABLE_CODE_GOVERNANCE.md` only as an adoption/how-to guide if
  it becomes materially shorter and non-overlapping.
- Retain `dev/active/MASTER_PLAN.md` as tracker authority and
  `dev/active/INDEX.md` as router authority. Do not keep architectural state
  split across execution specs once consolidated.
- Generate instruction and workflow docs from repo-pack config:
  `AGENTS.md`, `CLAUDE.md`, slash/skill templates, and hook/workflow stubs.
- Add drift checks for every generated surface. The current AGENTS bundle check
  is the pattern; expand it so plan drift and instruction drift fail fast.

### G. File-By-File Or Module-By-Module Action Plan

- `dev/active/ai_governance_platform.md`: promote to the single active
  architecture plan for the standalone product.
- `dev/active/portable_code_governance.md`: shrink to an engine/adoption
  appendix or companion after consolidation.
- `dev/guides/AI_GOVERNANCE_PLATFORM.md`: keep as the canonical durable
  architecture document.
- `dev/guides/PORTABLE_CODE_GOVERNANCE.md`: narrow to adopter workflow and
  repo-pack onboarding.
- `dev/config/devctl_repo_policy.json`: remove duplicate keys and extend schema
  for instruction surfaces, hook profiles, workflow templates, and repo-pack
  metadata.
- `dev/config/quality_presets/`: keep as portable defaults with clean
  separation between engine defaults and repo-pack overrides.
- `dev/scripts/devctl/quality_policy.py` and
  `dev/scripts/devctl/quality_policy_defaults.py`: become the formal repo-pack
  resolver stack in the extracted package.
- `dev/scripts/checks/check_agents_bundle_render.py` and
  `dev/scripts/checks/check_agents_contract.py`: generalize into
  surface-render and surface-contract checks for all generated instruction
  files.
- `AGENTS.md`, `CLAUDE.md`, `dev/templates/slash/`: move to generated outputs
  from repo-pack config plus templates.
- `dev/scripts/devctl/platform/` and `dev/scripts/devctl/runtime/`: become the
  internal package roots other modules must depend on, not just blueprint docs.
- `dev/scripts/devctl/audit_events.py`,
  `dev/scripts/devctl/governance_review_log.py`,
  `dev/scripts/devctl/review_probe_report.py`,
  `dev/scripts/devctl/watchdog/episode.py`: unify under one
  artifact-store/run-history contract.
- `dev/scripts/devctl/governance_export_support.py` and
  `dev/scripts/devctl/governance_bootstrap_support.py`: shift from
  snapshot-copy semantics toward package install/render semantics.
- `app/operator_console/state/snapshots/analytics_snapshot.py` and
  `app/operator_console/state/snapshots/quality_snapshot.py`: remove hard-coded
  VoiceTerm repo restrictions and consume stable runtime/artifact APIs.
- `.github/workflows/` and `.pre-commit-config.yaml`: move toward generated or
  templated hook/workflow surfaces from repo-pack policy.
- `pypi/src/voiceterm/cli.py`: keep VoiceTerm packaging focused on VoiceTerm;
  do not use the PyPI launcher as the governance package boundary.

### H. Risks And Tradeoffs

- Extracting while the worktree is dirty risks stabilizing the wrong seams; the
  countermeasure is to consolidate docs first, not to delay extraction
  indefinitely.
- Keeping too many compatibility shims will slow extraction; removing them too
  fast will break callers. The repo already has the right shim-metadata
  discipline, so use staged shrinkage.
- Standardizing on JSONL plus projections first is the pragmatic move, even if
  users keep asking for a heavier database.
- Generalizing too much too early could erase VoiceTerm-specific quality. The
  fix is the repo-pack model, not more in-engine special cases.
- Pulling the PyQt client out too early could create a second backend. The fix
  is a strict runtime-contract boundary and CLI/API-only data access.
- Loop extraction is trickier than core-rule extraction because workflows,
  branches, notifications, and provider CLIs remain environment-sensitive.

### I. What Not To Build Yet

- Do not make MCP the primary control plane.
- Do not build a mandatory database-backed runtime before the artifact-store
  contract is unified.
- Do not widen the PyQt6 UI into a second orchestration backend before
  extraction and API stabilization.
- Do not prioritize optional Ruff/Semgrep/Black/Clippy wrapper work ahead of
  freezing the core contracts, repo-pack boundary, replay/evaluation path, and
  package/install surface.
- Do not pull the Memory Studio scope into the first standalone governance
  release.
- Do not attempt broad multi-repo packaging of every workflow loop before
  repo-pack rendering and contract tests exist.

### J. Final Recommendation

- The repo-grounded recommendation is to formalize the direction that already
  exists: a standalone deterministic governance product centered on CLI
  authority, repo-pack policy, deterministic guards/probes, typed runtime
  contracts, structured artifacts, and thin adapters.
- The immediate move is:
  1. consolidate architecture authority into this plan,
  2. normalize canonical policy/config generation,
  3. harden internal runtime/platform boundaries in-place,
  4. package the portable core once the contract freeze and boundary proof are
     real,
  5. rebind VoiceTerm, PyQt6, MCP, and loop surfaces as consumers of that
     product, then split repos only after external-pilot proof.
- VoiceTerm should survive as the first adopter and integration target, but it
  should stop being the permanent host architecture for the governance system.

## Execution Checklist

- [x] Consolidate the repo-grounded architecture review, boundary analysis, and
      phased roadmap into this one active plan so the work no longer depends on
      chat history or overlapping architecture docs.
- [x] Define the reusable package/workspace boundary and naming so the platform
      can ship independently from VoiceTerm.
- [x] Write one durable maintainable architecture/thesis/flowchart guide for
      the reusable platform so the product direction is not trapped in active
      plan notes or chat history alone.
- [x] Add one read-only executable platform blueprint surface
      (`devctl platform-contracts`) so frontends, adopters, and AI setup flows
      can consume the intended backend/repo-pack contract in machine-readable
      form instead of parsing active-plan prose only.
- [ ] Define the shared runtime contracts (`RepoPack`, `ControlState`,
      `TypedAction`, `RunRecord`, `ArtifactStore`, `ProviderAdapter`,
      `WorkflowAdapter`) in one canonical backend layer.
- [ ] Extract Ralph, mutation, review-channel, and host-process hygiene loops
      off repo-local assumptions and onto those shared contracts.
- [ ] Converge CLI, PyQt6 operator console, overlay/TUI, and phone/mobile
      views onto the same runtime state model instead of duplicated shaping.
- [ ] Ship a bootstrap/adoption flow that an AI can run against a new repo
      without hand-editing core engine code.
- [ ] Define repo-pack packaging so repo-local policy/workflow/docs defaults
      live outside the portable core.
- [ ] Keep VoiceTerm working as the first consumer while replacing direct
      imports of repo-embedded platform logic with explicit integration seams.
- [ ] When a meaningful MP-377 slice turns green with validation, docs, and
      reviewer signoff, capture a bounded commit/push checkpoint through the
      normal approval path instead of letting the extraction lane accumulate an
      unreviewable dirty tree.
- [ ] Collapse the remaining peer architecture/doc duplication so this plan is
      the single active authority for the full-product governance architecture
      while durable guides become clearly subordinate/reference surfaces.
- [x] Normalize repo-pack policy/config so generated instruction surfaces can
      come from one canonical source without duplicate-key ambiguity.
- [ ] Define one canonical event-history model that keeps session continuity in
      active-plan markdown while unifying `devctl_events`, governance review
      rows, watchdog episodes, swarm summaries, and future `RunRecord`
      artifacts behind one runtime/artifact-store contract.
- [ ] Define first-class context contracts (`ContextPack`,
      `ContextBudgetPolicy`) plus repo-pack-tunable budget tiers so AI loops
      stay bounded across bootstrap, full-scan, focused-fix, review, and
      remediation modes.
- [ ] Add context-usage telemetry to `RunRecord`/event history/adoption
      evidence: estimated prompt size, actual provider usage when available,
      compression ratio, and explicit overflow/truncation path.
- [ ] Make "why didn't the tools catch this?" a first-class execution rule:
      for each externally found issue or audit finding, record the enforcement
      miss, decide whether it belongs to an existing guard/probe/runtime
      contract or a new rule family, and keep that follow-up in repo-visible
      plan state before closure.
- [ ] Add the self-hosting enforcement tranche for platform-boundary blind
      spots: layer boundaries, portable path construction, provider/workflow
      adapter routing, contract completion, schema/platform compatibility, and
      the first repeatable command-source/shell-execution checks.
- [ ] Expand the watchdog and audit evidence beyond today's narrow slices:
      run repeated full-worktree `--adoption-scan` cycles, widen guarded-coding
      episode coverage, and baseline more guard/probe families so platform
      accuracy claims are backed by codebase-wide evidence instead of a small
      reviewed subset.
- [ ] Treat false positives as rule-quality bugs: for every recorded
      `false_positive`, capture the root cause and either narrow the rule,
      add context, demote severity, move it behind repo-pack policy, or
      explicitly justify why it remains advisory.
- [ ] Add adjudication-coverage metrics: reviewed-vs-unreviewed findings by
      guard/probe family, scan mode, repo, and time window so the repo can
      distinguish "good outcomes on a small sample" from broad signal quality.
- [ ] Define the database-ingestion/provenance contract before adding a DB:
      canonical IDs, schema-version migration rules, JSONL-to-DB mapping,
      repo-pack/policy version stamping, and backfill strategy.
- [ ] Define privacy/redaction rules for structured telemetry before expanding
      the event store or ML corpus: which fields can be persisted verbatim,
      which must be redacted/hashed, and which artifacts need shorter
      retention.
- [ ] Define a measured promotion rubric for guard tiers so advisory probes only
      become blocking guards when sample size, false-positive rate, cleanup
      rate, and adoption-scan stability justify it.
- [ ] Ship budget-aware usage guidance so adopters know when to use full-repo
      scans versus focused slices, what the expected context bands are, and
      when the platform will summarize, split, or refuse oversized runs.
- [ ] Freeze the platform boundary with executable import/layer contracts so
      `governance_core`, `governance_runtime`, `governance_adapters`,
      `governance_frontends`, `repo_packs`, and VoiceTerm-specific integrations
      cannot silently bleed back together during extraction.
- [ ] Define one versioned finding/evidence schema at the center of the
      platform: `rule_id`, `rule_version`, category/language/severity/
      confidence, file/span, evidence, rationale, suggested fix, autofixable
      flag, suppression policy, and artifact refs, with every agent/reviewer/
      markdown projection derived from that same base record.
- [ ] Finish the machine-receipt contract for JSON-canonical surfaces so
      stdout becomes a stable control channel rather than prose status output:
      compact receipts should include artifact path/hash/bytes/token estimates,
      content type, and command/rule-family metadata.
- [ ] Extend artifact-cost telemetry from the current machine-output helpers
      into a first-class platform metric surface: rereads avoided by hash,
      bytes per accepted fix, token cost per false positive, token cost per
      no-op cycle, and other context-efficiency measures visible to operators.
- [ ] Freeze the artifact-backed retrieval contract for machine-first runs:
      the full JSON artifact stays on disk, stdout carries only a compact
      control receipt, and runtime retrieval opens the full artifact only when
      the hash changes or deeper detail is actually needed. The near-term
      storage target remains JSONL plus an optional SQLite catalog keyed by
      artifact path/hash/bytes/token estimate, run/task/git refs, and summary
      pointers rather than a mandatory database-backed runtime.
- [ ] Strengthen Python contract/boundary enforcement for the portable core:
      move beyond today's advisory mypy lane by evaluating stricter typed
      contract paths plus executable import-boundary enforcement for core vs
      adapters vs frontends vs repo-pack code.
- [ ] Evaluate structural search/rewrite tooling as a bounded extension under
      platform contracts: use repo-owned Semgrep/AST-based rules and optional
      autofixers where they fit, but keep the canonical policy/evidence model
      in repo-owned governance code rather than outsourcing product semantics.
- [ ] Build a replayable evaluation harness for rule quality: define a labeled
      cross-repo corpus, stable replay inputs, and version-to-version accuracy
      comparisons so new policy/rule changes are measured against the same
      evidence set before stronger product claims or ML-ranking work lands.
- [ ] Add guard-quality meta-governance so the platform can grade its own
      rules: every blocking/advisory rule should carry expected benefit,
      bad/good examples, replay coverage, and reviewed false-positive/defer/
      fix stats, and a meta-guard/report lane should flag noisy, untested,
      overlapping, or non-uplifting rules before the check surface turns into
      low-value noise.
- [ ] Define a waiver/suppression lifecycle that matches the deterministic
      governance goal: owner, rationale, scope, expiry, reevaluation trigger,
      and reporting hooks so suppressions stay visible debt instead of becoming
      unbounded hidden escape hatches.
- [ ] Define platform completion gates so `MP-377` cannot close on packaging
      work alone: architecture boundary, pipeline parity, reviewed evidence
      quality, replay coverage, telemetry trust, and cross-repo adoption all
      need explicit closure criteria.
- [ ] Establish a standing pattern-mining program for Python and Rust first:
      repeated scans over this repo plus external adopters should keep feeding
      new low-noise probe/guard candidates, with adjudication evidence used to
      decide which patterns graduate, stay advisory, or get discarded.
- [ ] Define the language-extension contract up front: shared finding schema,
      policy hooks, review-ledger semantics, telemetry fields, and packaging
      model for future language analyzers so support can grow beyond
      Python/Rust without fracturing the platform architecture.
- [ ] Continue directory-by-directory organization so filesystem layout mirrors
      package boundaries and support modules stop accumulating in flat roots.
- [ ] Make `devctl` self-hosting for layout governance: overcrowded roots must
      be discoverable by policy, frozen against further flat growth, and
      baseline/adoption scans must explain the same organization contract to
      external repos before packaging/splitting proceeds.
- [ ] Make `devctl/commands` and other high-density families explicit
      namespaces, not implicit dumping grounds: the repo pack should baseline-
      report crowded flat families, freeze further flat family growth, and
      point agents to concrete target subpackages such as `commands/check/`,
      `commands/autonomy/`, and `commands/release/`.
- [ ] Validate the extracted platform on at least two non-VoiceTerm repos with
      no core-engine patching required between adoptions.

## Session Resume

Use this section as the single "left off here" surface for fresh AI sessions
working on `MP-377`.

### Current status

- `dev/active/ai_governance_platform.md` is the only main active plan for this
  product scope; companion docs now route back here instead of acting like peer
  execution authority.
- Session-level "where we left off" state belongs in this file's `Session
  Resume` and `Progress Log`, not in the future structured audit/database
  ledger.
- Repo docs-governance now enforces that platform-scope tooling/policy/runtime/
  extraction changes must update this plan through the policy-owned
  `docs-check` rule in `dev/config/devctl_repo_policy.json`.
- The docs-check implementation was refactored into
  `dev/scripts/devctl/commands/docs/` so the enforcement path now passes the
  repo's own shape/complexity/parameter-count/dict-schema guards.
- The repo already has structured machine-readable ledgers for runtime
  evidence: `dev/reports/audits/devctl_events.jsonl` for command telemetry,
  `dev/reports/governance/external_pilot_findings.jsonl` for raw imported
  external findings, and `dev/reports/governance/finding_reviews.jsonl` for
  adjudicated guard/probe/audit outcomes. Those logs should feed the future
  database/data-science layer, not replace the plan's `Session Resume` /
  `Progress Log`.
- The current operator protocol is now explicit: `devctl` owns command-level
  telemetry, `governance-import-findings` owns raw external-finding intake,
  `governance-review --record` owns adjudicated finding outcomes, and handoff
  notes must say when meaningful work happened outside those ledgers so
  coverage is not overstated.
- The canonical platform docs are no longer untracked-only local state:
  `dev/active/ai_governance_platform.md` and
  `dev/guides/AI_GOVERNANCE_PLATFORM.md` are now staged in git so fresh AI
  sessions and the next commit can preserve this scope without depending on
  chat history.
- The current Codex-reviewer / Claude-coder execution lane is usable for
  `MP-377` work right now: on 2026-03-13,
  `python3 dev/scripts/devctl.py review-channel --action launch --terminal none --dry-run --format md --refresh-bridge-heartbeat-if-stale`
  passed, refreshed the live markdown-bridge heartbeat, and emitted the
  expected 8 Codex reviewer lanes plus 8 Claude coder lanes. Treat that as
  real execution scaffolding for plan work, not as proof that the
  review-channel / continuous-swarm plans are fully closed.
- `Phase 2 - Normalize repo-pack policy and surface generation` now has a
  repo-backed first slice: `repo_governance.surface_generation` owns repo-pack
  metadata/context/surface policy, `devctl render-surfaces` renders or
  validates the governed outputs, `check_instruction_surface_sync` plus
  `docs-check --strict-tooling` enforce template-backed drift, and starter
  bootstrap/template flows seed the same contract for adopter repos.
- The generated-surface path is now hardened enough for broader reuse:
  report-mode surface checks tolerate missing local-only outputs such as
  `CLAUDE.md`, `render-surfaces --write` remains the explicit regeneration
  path, and the maintainer docs/tests now describe and cover that contract.
- The stable public generated-surface sync path remains
  `dev/scripts/checks/check_instruction_surface_sync.py`. Package-local logic
  stays under `dev/scripts/checks/package_layout/`; registries, workflows, and
  rendered docs should keep pointing at the stable public root shim instead of
  drifting to package-internal `check_*` entrypoints.
- Portable onboarding guidance is now aligned with that same repo-pack
  contract: bootstrap/setup docs tell adopters to inspect
  `repo_governance.surface_generation`, then run
  `python3 dev/scripts/devctl.py render-surfaces --write --format md` before
  their first full adoption scan.
- The governance command family now follows the machine-first projection rule
  directly in code. `governance-bootstrap`, `governance-export`,
  `governance-review`, and `render-surfaces` share one output/error helper,
  emit canonical JSON for machine consumers, and keep markdown as the human
  render on top of that payload instead of each command inventing its own
  result-flow shape.
- A follow-up architecture audit on 2026-03-13 confirmed that the current
  shared output path does not dump full JSON to stdout when `--output` is set.
  `write_output()` writes the artifact and only prints `Report saved to: ...`,
  so the remaining token-efficiency problem is not terminal flooding. The real
  gap is that this receipt is still human prose rather than a compact stable
  machine envelope, and the runtime/data-science stack still does not record
  artifact bytes, hashes, or estimated token cost for those machine payloads.
- The next abstraction should therefore not be a blanket rewrite of
  `emit_output()` for every `devctl` command. Many commands remain
  human/terminal-oriented. The better platform seam is a reusable
  machine-artifact emitter for JSON-canonical packet/report surfaces first
  (`governance-*`, `platform-contracts`, `probe-report`, `data-science`,
  `loop-packet`, then later review/autonomy surfaces), with compact machine
  receipts and measurable artifact-cost metadata layered on top of the
  existing generic output helper.
- That next slice is now partially implemented. JSON-canonical surfaces that
  use the new machine-output path write the full compact JSON artifact to disk,
  emit only a compact JSON receipt on stdout when `--format json --output ...`
  is used, and append artifact metadata (`path`, `sha256`, `size_bytes`,
  `estimated_tokens`, `stdout_receipt_size_bytes`) into `devctl` command
  telemetry so the repo can start measuring transport cost instead of only
  command duration/success.
- Self-hosting validation now covers nested command packages instead of
  silently preferring flat roots. `check_architecture_surface_sync.py` can now
  resolve aliased imports such as
  `from .commands.governance import bootstrap as governance_bootstrap`, so the
  governance package move is enforced by the repo's own architecture guard
  rather than living behind a false-positive blind spot.
- Self-hosting layout governance is green on the current tree, but the pass is
  still partly a freeze/baseline result rather than proof that the topology is
  fully decomposed. `check_package_layout.py` is currently preventing new
  sprawl in already-crowded roots such as `dev/scripts/checks`,
  `dev/scripts/devctl`, `dev/scripts/devctl/commands`, and
  `dev/scripts/devctl/tests`; those directories still need further package/test
  splits before the repo can claim the script surface is genuinely tidy.
- The first extraction-boundary hard guard is now live in repo policy.
  `check_platform_layer_boundaries.py` freezes new Python imports from
  Operator Console or shared runtime/platform files into repo-local
  orchestration modules, so the next extraction slices can harden seams
  without waiting for the full repo split first.
- Routed bundle execution now honors the repo-required interpreter too.
  `check-router --execute` rewrites repo-owned `python3 ...` bundle commands
  to the active interpreter before execution, which closes the concrete
  Python-3.10 fallback gap the plan had flagged in self-hosting reliability.
- The first concrete `repo_packs.voiceterm` consumer seam is now real.
  VoiceTerm-specific workflow-plan metadata and review-bridge path defaults
  now live under `dev/scripts/devctl/repo_packs/voiceterm.py`, and the
  Operator Console reads that repo-pack-owned surface instead of importing
  `review_channel` internals or hard-coding active-plan docs inside frontend
  modules.
- `RepoPathConfig` is now a real frozen dataclass with 33 fields, exposed as
  `VOICETERM_PATH_CONFIG`. Consumers span 13+ OC/frontend modules, 4
  review-channel runtime modules, 2 governance ledger modules, 2 autonomy
  parsers, and 7 devctl command files (via `process_helpers` and
  `review_helpers` adapter modules under `repo_packs/`). Five read-only
  collector helpers
  (`voiceterm_repo_root`, `collect_devctl_git_status`,
  `collect_devctl_mutation_summary`, `collect_devctl_ci_runs`,
  `collect_devctl_quality_backlog`) let the frontend call devctl collection
  through the repo-pack boundary instead of importing forbidden orchestration
  modules directly or using dynamic-import workarounds.
- The latest architecture re-audit tightened the framing without changing the
  direction: external analyzers remain subordinate engines or later adapters
  under the governance control plane, the governed signal taxonomy is explicit
  (`language-engine`, `AI-shape`, `repo-contract` findings), and the first
  portable release stays intentionally narrow instead of trying to extract
  every frontend or workflow loop at once.
- The recent iOS/mobile path cleanup is only partial. Shell scripts now name
  the canonical VoiceTerm paths, but `MobileRelayPreviewData.swift` still
  duplicates literals with only a source-of-truth comment, so that surface
  remains interim documentation rather than a finished repo-pack contract.
- The transitional `review_channel` runtime modules (`core.py`, `state.py`,
  `event_store.py`, `promotion.py`) now read path defaults from
  `VOICETERM_PATH_CONFIG` instead of defining their own literals.
  `RepoPathConfig` has 20 fields total. `parser.py` and `events.py` needed
  no changes — backward-compat aliases flow through the import chain.
- Widened the repo-pack boundary further with 4 more accepted passes:
  `mobile_status.py` now routes review-state loading through
  `repo_packs/review_helpers.py`; 6 command files moved `resolve_repo` /
  `run_capture` off the checks layer into `repo_packs/process_helpers.py`;
  governance ledger modules dropped compile-time `REPO_ROOT` for runtime
  `voiceterm_repo_root()` fallback; and `run_parser.py`,
  `benchmark_parser.py`, `cli_parser/reporting.py` all consume
  `VOICETERM_PATH_CONFIG` for autonomy/report defaults. Remaining duplicate
  defaults in `data_science/metrics.py`, `autonomy/report_helpers.py`,
  `audit_events.py`, and `watchdog/episode.py` migrated onto the same
  config. `RepoPathConfig` now has 42 fields, voiceterm.py at 349 lines.
- MP-358 tandem-loop work is now underway alongside the extraction lane:
  fixed `--scope` promotion bug (`86b902c`), added `--auto-promote` with
  end-to-end tests, wired `reviewed_hash_current` into status/launch/
  attention/handoff surfaces, enforced `block_launch` peer-liveness guard,
  and added `REVIEWED_HASH_STALE` attention signal. These are runtime
  contract improvements that complement the repo-pack extraction boundary
  by making the shared runner surfaces honest about bridge truth.

### Next actions

Operational reminder: when a meaningful MP-377 slice is green with code,
validation, docs, and reviewer acceptance, stop widening the dirty tree and
prepare a bounded commit/push checkpoint through the normal approval path.

1. Continue turning the remaining audit intake into self-hosting enforcement
   work: the first layer-boundary guard is live, and the next backlog should
   cover portable path construction, adapter routing, contract completion,
   schema compatibility, and repeatable command-source/shell-execution misses.
2. ~~Move the next real seam from frontend path cleanup to transitional
   runtime separation~~ — done enough to accept for this slice. The
   `review_channel` runtime modules now resolve VoiceTerm paths through
   repo-pack/runtime contracts, `mobile_status.py` now loads review status
   through `repo_packs.review_helpers` instead of importing
   `review_channel.*` directly, and the narrow `controller_action.py` /
   `triage_loop.py` checks-layer fit-gap is closed through the devctl-owned
   `process_helpers` seam. The next real seam is governance/report path
   ownership: `governance_review_log.py`,
   `governance/external_findings_log.py`, and their mirrored defaults in
   `data_science/metrics.py` should stop owning raw
   `dev/reports/governance/*` defaults directly, then the follow-up seam is
   `autonomy/run_parser.py` reducing hard-coded VoiceTerm plan/report
   defaults.
3. Keep the iOS/mobile path cleanup marked partial until generated or emitted
   repo-pack-owned metadata replaces duplicate literals in preview/demo
   surfaces; comments alone do not close that seam.
4. Define the installable governance package surface explicitly:
   `pyproject.toml`, build backend, versioning, dependency contract, and stable
   CLI entrypoint(s) for clean-environment installs.
5. ~~Widen `RepoPathConfig` coverage~~ — done. `RepoPathConfig` now has 15
   fields, 13 OC/frontend modules consume `VOICETERM_PATH_CONFIG`, 5
   repo-pack collector helpers replace forbidden imports, and iOS shell
   scripts centralize paths with source-of-truth comments. Only non-blocking
   presentation/help strings and test fixtures retain inline path literals.
6. Finish the compatibility contract, not just the version field:
   document schema-version ownership, migration rules, compatibility checks,
   and rollback expectations alongside repo-pack/platform version pinning.
7. Expand the adapter/frontend migration: `artifact_locator.py`,
   `bridge_sections.py`, and `session_trace_reader.py` are now path-migrated
   to `VOICETERM_PATH_CONFIG`. The remaining deeper couplings are
   `workflow_loop_utils.py`, `loops/comment.py`, the transitional
   `review_channel` runtime, and related read-only consumers which need
   adapter-contract work (replacing direct `subprocess`/`gh` calls and local
   path ownership with `WorkflowAdapter` / repo-pack contracts rather than
   more path migration).
8. Continue `Phase 2 - Normalize repo-pack policy and surface generation` by
   adding explicit repo-pack context-budget profiles and usage-tier guidance
   hooks; the generated surfaces are now policy-owned, but bounded context
   modes still need to become first-class repo-pack behavior too.
9. Promote the missing runtime evidence contracts into the executable
   `governance_runtime` surface: `ContextPack`, `ContextBudgetPolicy`,
   `Finding`, `FindingReview`, `MetricEvent`, and the thin-client snapshot
   states now scattered across operator-console readers.
10. Keep using this section plus the `Progress Log` for session handoff. Do not
   create a second "main plan" or a separate hidden scratch log for `MP-377`.
11. Define the canonical event-history/runtime-evidence contract that unifies
   existing JSONL ledgers (`devctl_events`, governance reviews, watchdog
   episodes, swarm summaries) without collapsing session handoff into the
   future database layer.
12. Define the context-budget contract and first repo-pack usage tiers before
   packaging more AI-facing loops; prompt cost must stay explicit platform
   behavior instead of hidden product debt.
13. Add a machine-artifact control-envelope contract for JSON-canonical
   surfaces so `--output` can produce compact machine receipts plus artifact
   hash/byte/token metadata without forcing the same behavior onto
   human-first commands.
14. Promote the same machine-first projection rule beyond the governance
   command family into review-channel, autonomy, and data-science packet
   surfaces so agents, operators, junior developers, and senior reviewers can
   consume one shared evidence payload at different projection/detail levels.
15. Extend runtime evidence beyond command duration/success: `RunRecord`,
    `devctl_events`, and later data-science rollups need artifact-size,
    artifact-hash, and estimated token fields so the repo can measure whether
    machine-first outputs are actually reducing context cost.
16. Continue burning down the crowded freeze-mode roots that
    `check_package_layout.py` is currently baselining. The next structural
    cleanup work should keep moving real implementation/test code out of flat
    `checks/`, `devctl/`, `commands/`, and `tests/` roots so the repo can later
    ratchet those areas toward stricter package ownership instead of living in
    permanent freeze mode.
17. Tighten structured-ledger coverage so manual/chat-driven fix sessions can
    either emit first-class run records or explicitly declare telemetry gaps
    instead of leaving command-history completeness ambiguous.
18. Increase full-codebase evidence density: use repeated `--adoption-scan`
    audit cycles and wider watchdog coverage so the repo can measure real
    false-positive and cleanup rates across more than the current reviewed
    subset.
19. Make false-positive remediation explicit: each false positive should produce
    a root-cause note and a concrete rule/policy follow-up unless the repo can
    justify leaving it as an intentionally advisory heuristic.
20. Add a replayable rule-quality benchmark path: define the first labeled
    cross-repo corpus and the versioned replay/evaluation flow that future
    DB/ML work must consume instead of relying only on live current-worktree
    scans.
21. Define the waiver/suppression lifecycle so known-noisy signals remain
    visible, expiring governance debt rather than becoming permanent silent
    bypasses.
22. Write explicit platform completion gates so this scope cannot be called
    done after repo split or packaging alone; closure should require
    architecture, pipeline, evidence, and telemetry trust together.
23. Add the repo-pack/platform compatibility guard and exercise it in pilot
    upgrades before treating external adoption as complete.
24. Preserve the platform’s differentiators in public proof, not only private
    plan text: adaptive feedback sizing, three-layer enforcement, artifact-
    backed governed loops, multi-agent review/coding, context budgets, mutation
    remediation, multi-surface control, and self-hosted portability should all
    survive into the durable/public whitepaper.
25. Start the standing Python/Rust pattern-mining loop against this repo and
    external pilot repos so new rule families come from measured evidence, not
    one-off intuition.
26. Measure which current rule families show repeatable AI-quality uplift
    across multiple repos instead of only sounding correct locally; treat
    those empirically supported families as the first true portable
    primitives.
27. Build the first loop-value proof packet for recent successful cleanup
    runs: before/after tests/builds, findings delta by rule family, artifact
    and token cost, reread/skip counts, loops-to-green, artifacts consumed
    per successful change, defer/revert rates, and the first ranked list of
    candidate portable primitives.
28. Keep a living list of common AI-generated bad patterns that still pass all
    current checks so future guard/probe work is driven by measured misses,
    not taste alone.
29. Define the future language-extension contract while Python/Rust are still
    the active lanes so new languages can plug into the same architecture
    instead of creating parallel subsystems later.

### Resume instructions for the next AI session

1. Read `AGENTS.md`, then `dev/active/INDEX.md`, then
   `dev/active/MASTER_PLAN.md`.
2. Read this file and treat it as the only main active plan for the standalone
   governance product scope.
3. Read this `Session Resume` section and the latest `Progress Log` entries
   before making recommendations or edits.
4. Continue from the listed `Next actions` unless the user explicitly
   reprioritizes.
5. Before ending the session, update both this `Session Resume` section and the
   `Progress Log` with what changed, what remains, and what the next AI should
   do.

## Progress Log

- 2026-03-15: Re-audited `MP-377` against the current repo and the latest
  control-plane thesis. Confirmed the direction remains correct, then promoted
  the missing explicit rules into the plan: external analyzers
  (Ruff/Semgrep/Clippy/Black/etc.) are subordinate engines or later adapters
  under this control plane, the governed signal taxonomy is now explicit
  (`language-engine`, `AI-shape`, `repo-contract` findings), and the first
  portable release stays intentionally narrow instead of blocking on PyQt6,
  mobile, MCP, or full workflow-loop extraction.
- 2026-03-15: Added the missing "prove the loop is worth it" rubric instead of
  leaving value claims implied. `MP-377` now says the product stack is
  `engine tools -> shape rules -> governed loop`, makes the governed loop the
  actual product layer, and requires loop-value proof on correctness
  preservation, structural improvement, cost per successful repair, and
  cross-repo generalization. The same update also made noisy rules, risky
  transformations, token bottlenecks, and still-missed AI failure patterns
  explicit review targets instead of background concerns.
- 2026-03-15: Tightened the thesis language so the scope stays honest. The
  plan now says we are improving the environment the model codes inside rather
  than "teaching the model better code," keeps code-shape separate from the
  agent-memory problem, adds follow-up stability as a measured outcome, and
  names over-modularization plus rule gaming as explicit failure modes to
  guard against when evaluating cleanup rules.
- 2026-03-15: Added the missing artifact-retrieval and guard-quality details
  to the machine-first scope. `MP-377` now says the full artifact stays on
  disk, stdout should be only a compact receipt, hash-aware reread avoidance
  is part of the runtime contract, and JSONL plus an optional SQLite catalog
  is the near-term indexing target rather than a mandatory database runtime.
  The same update also makes rule-quality meta-governance explicit: each
  guard/probe should carry examples, expected benefit, replay coverage, and
  reviewed false-positive/defer/fix stats, and the platform needs a
  meta-guard/report path that flags noisy or non-uplifting rules before they
  silently accumulate.
- 2026-03-15: Re-reviewed the recent iOS/mobile path cleanup and downgraded it
  from "closed seam" to "partial seam." The shell scripts now name the
  canonical VoiceTerm paths, but `MobileRelayPreviewData.swift` still carries
  duplicate literals with only a source-of-truth comment. Keep that surface
  marked interim until generated or emitted repo-pack-owned metadata replaces
  the duplicated literals. The same review pass also added an explicit
  green-slice commit/push reminder so `MP-377` does not keep widening an
  unreviewable dirty tree once a bounded slice is green.
- 2026-03-15: Extended the repo-pack path boundary to iOS/mobile surfaces.
  Shell scripts (`sync_live_bundle_to_simulator.sh`,
  `run_guided_simulator_demo.sh`) now centralize VoiceTerm artifact paths as
  variables with `RepoPathConfig` source-of-truth comments instead of
  inlining them in CLI args. Swift preview data
  (`MobileRelayPreviewData.swift`) now carries a canonical-source comment
  linking back to `repo_packs/voiceterm.py::RepoPathConfig`. Full
  cross-language code generation from repo-pack config is a later phase, but
  the path ownership is now explicit rather than silently scattered.
- 2026-03-15: Widened the Python frontend path boundary to 4 more Operator
  Console modules outside the state package: `logging_support.py`,
  `run.py`, `layout/layout_state.py`, and
  `collaboration/timeline_builder.py`. Added `dev_log_root_rel` and
  `layout_state_rel` to `RepoPathConfig`.
- 2026-03-15: Widened the `repo_packs.voiceterm` boundary from 5 path constants
  to a full `RepoPathConfig` frozen dataclass (13 fields) plus 5 read-only
  collector helpers (`voiceterm_repo_root`, `collect_devctl_git_status`,
  `collect_devctl_mutation_summary`, `collect_devctl_ci_runs`,
  `collect_devctl_quality_backlog`). Migrated 8 Operator Console modules to
  consume `VOICETERM_PATH_CONFIG` instead of defining their own path literals:
  `review_state.py`, `artifact_locator.py`, `bridge_sections.py`,
  `session_trace_reader.py`, `watchdog_snapshot.py`, `ralph_guardrail_snapshot.py`,
  `analytics_snapshot.py`, `quality_snapshot.py`. The last two also dropped their
  forbidden `dev.scripts.devctl.collect` and `dev.scripts.devctl.config` imports
  in favor of repo-pack-owned helpers, removing the frontend-local `importlib`
  workaround after Codex reviewer feedback. All 1328 tests pass,
  platform-layer-boundary guard is green with 0 violations, and `docs-check
  --strict-tooling` is ok.
- 2026-03-14: Started materializing the planned `repo_packs.voiceterm`
  boundary instead of only talking about it in architecture prose. Added
  `dev/scripts/devctl/repo_packs/voiceterm.py` as the first repo-pack-owned
  VoiceTerm metadata/read-only helper surface, moved the Operator Console
  workflow preset definitions onto that module, and replaced
  `phone_status_snapshot.py`'s direct `dev.scripts.devctl.review_channel.*`
  imports with one narrow repo-pack-owned `load_review_payload_from_bridge()`
  helper. That reduces the existing frontend-to-orchestration coupling without
  pretending the full `RepoPathConfig` contract is already finished.
- 2026-03-14: Closed the routed-bundle Python-version mismatch that had still
  been undermining self-hosting reliability. `check-router --execute` used to
  shell the canonical bundle strings verbatim, which meant mixed-runtime
  machines could still run routed `devctl` / guard / pytest commands under an
  older ambient `python3` even though direct `devctl check` and `guard-run`
  already reused the active interpreter. The router now rewrites repo-owned
  `python3 ...` shell commands to the active interpreter before execution,
  shared command helpers cover both script and `-m pytest` forms, and the
  focused router/common tests now pin that contract directly.
- 2026-03-14: Landed the first hard extraction-boundary enforcement slice
  instead of leaving the separation rule in plan prose. The new
  `check_platform_layer_boundaries.py` guard now lives behind repo policy and
  `devctl check --profile ci`, blocks new Operator Console and
  runtime/platform imports that reach directly into repo-local orchestration
  packages, and keeps its implementation plus tests in namespaced helper
  packages so the crowded `dev/scripts/checks` / `dev/scripts/devctl/tests`
  roots do not grow further. The same slice also taught
  `check_test_coverage_parity.py` to recurse into namespaced test packages so
  self-hosting coverage enforcement stays aligned with the package-layout
  direction instead of forcing new tests back into the flat root, and updated
  `check_architecture_surface_sync.py` so repo-enabled AI guards are treated as
  valid bundle/workflow-owned surfaces when they are enforced indirectly
  through `devctl check`.
- 2026-03-14: Added the missing raw external-evidence intake path for the
  future database/ML stack. `devctl governance-import-findings` now imports
  JSON/JSONL pilot findings into
  `dev/reports/governance/external_pilot_findings.jsonl`, writes a repo/check
  coverage summary under `dev/reports/governance/external_findings_latest/`,
  and `data-science` now joins that raw corpus with
  `finding_reviews.jsonl` so adjudication coverage is visible instead of
  pretending every imported finding was confirmed.
- 2026-03-13: Added the first explicit "simple command over policy file"
  façade for vibecoder-facing use. VoiceTerm now carries a focused launcher
  policy at `dev/config/devctl_policies/launcher.json` plus short wrapper
  commands (`launcher-check`, `launcher-probes`, `launcher-policy`) that
  target `scripts/` + `pypi/src` without forcing maintainers to remember raw
  `--quality-policy` paths. The architecture point is now explicit in repo
  state: policy files remain the authority, while human-facing entrypoints may
  project a smaller simpler command vocabulary over them.
- 2026-03-13: Landed the first launcher-lane hard guard rather than only the
  lane shell. `check_command_source_validation.py` now ships as a focused
  pilot guard for `scripts/` + `pypi/src`, the launcher policy enables it
  explicitly, and the two live launcher findings were hardened in the same
  slice: `scripts/python_fallback.py` no longer accepts free-form
  `--codex-args`, while `pypi/src/voiceterm/cli.py` validates repo URL/ref and
  forwarded argv before process launch.
- 2026-03-13: Added the missing self-hosting enforcement intake after the
  latest multi-agent audits. `MP-377` now says explicitly that every external
  audit finding must answer "why didn't the current tools catch this?" in
  repo-visible plan state, and it names the missing rule families instead of
  leaving them implicit: layer-boundary enforcement, portable path
  construction, provider/workflow adapter routing, contract completion,
  schema/platform compatibility, and the first repeatable command-source /
  shell-execution checks.
- 2026-03-13: Tightened the roadmap around the remaining concrete audit misses
  rather than only the abstract architecture. Phase 3 now includes
  `workflow_loop_utils.py` and `loops/comment.py`, Phase 4 now includes the
  deeper console-coupling files (`artifact_locator.py`, `bridge_sections.py`,
  `session_trace_reader.py`), the shared-contract section now states migration
  and rollback expectations beside version fields, and the plan now carries a
  dedicated differentiation section so the public proof pack is not left to
  imply the product thesis by accident.
- 2026-03-12: Created this execution-plan doc to separate two scopes that had
  started to blur together: `MP-376` owns the portable guard/probe engine,
  while this new `MP-377` scope owns the broader reusable product/platform
  extraction across runtime loops, frontends, repo packs, and packaging.
- 2026-03-12: Current architecture truth is now explicit in active state: the
  guard/probe/policy/bootstrap/export path is materially portable, but Ralph,
  mutation orchestration, review-channel/control-plane surfaces, host-process
  hygiene automation, and several frontend projections are still more
  VoiceTerm-local than platform-grade.
- 2026-03-12: Set the target product shape to one shared backend used by CLI,
  PyQt6, overlay/TUI, and phone/mobile surfaces, with VoiceTerm acting as a
  first consumer/repo pack instead of the permanent implementation host.
- 2026-03-12: Added `dev/guides/AI_GOVERNANCE_PLATFORM.md` as the durable
  maintainer-facing "whitepaper plus flowchart" guide for this direction so
  the core thesis is explicit: executable local governance is the authority,
  frontends are adapters, repo packs isolate repo-local behavior, and new
  repos should adopt the system through package + bootstrap instead of manual
  file copying.
- 2026-03-12: Added the first code-facing platform extraction seam under
  `dev/scripts/devctl/platform/` plus the read-only `devctl platform-contracts`
  command. The contract is still a blueprint, not yet the fully migrated
  runtime implementation, but it gives adopters and future frontends one
  machine-readable backend/layer/boundary source of truth instead of forcing
  them to infer the architecture from scattered docs and repo-local modules.
- 2026-03-12: Made repo organization part of the extraction contract rather
  than a cosmetic cleanup task: directory structure should reflect portable
  layers and public entrypoints, while internal helper families move behind
  documented subpackages or package-local directories.
- 2026-03-12: Landed the first executable shared runtime seam under
  `dev/scripts/devctl/runtime/`: `ControlState` is now a real typed contract,
  `devctl mobile-status` emits it alongside the legacy compatibility payloads,
  and the Operator Console phone snapshot loader now consumes that shared
  contract instead of re-deriving review/controller state entirely from ad-hoc
  nested dict access. This is only the first migration seam; review-channel
  packet readers, session metadata readers, collaboration surfaces, and other
  control-plane loops still need to move onto the same backend layer.
- 2026-03-12: Landed the next shared runtime seam beside `ControlState` under
  `dev/scripts/devctl/runtime/`: `ReviewState` now normalizes
  `review_state.json` and `full.json` review-channel artifacts into one typed
  session/queue/bridge/packet/registry contract, and the Operator Console
  review/session/collaboration readers now consume that runtime contract
  instead of re-walking raw review-channel dicts in each surface. This keeps
  `ControlState` as the compact cross-surface summary while moving detailed
  review-channel state into the same backend contract layer rather than leaving
  it trapped in app-local adapters.
- 2026-03-12: Promoted repo organization from a code-shape sidecar into a
  first-class portable guard concept. `check_package_layout.py` now owns
  declarative flat-root, namespace-family, and docs-sync organization rules via
  repo policy, which is the right packaging shape for agentic adoption: the
  engine evaluates structure contracts, while each repo pack decides its own
  filesystem standards.
- 2026-03-12: Added the first concrete `MP-377` migration roadmap directly to
  this active plan: target package names, ownership boundaries, phase-by-phase
  extraction order, split-readiness gates, and the initial file groups to move
  first. The immediate execution stance is now explicit: modularize fully
  in-place first, prove the boundaries with external pilots second, and split
  repositories only after runtime/adapters/frontends stop depending on
  VoiceTerm-local assumptions.
- 2026-03-13: Captured the next architecture-hardening tranche after an
  external product/portability review that largely aligned with the current
  layer model. The review did not change the platform direction; it confirmed
  it and sharpened the missing contract surfaces: freeze the import/layer
  boundary, define one versioned finding/evidence schema, finish compact
  machine receipts plus artifact-cost telemetry, strengthen Python typed/
  boundary enforcement, and preserve a replayable corpus before pushing harder
  toward training or wider rule-surface growth.
- 2026-03-13: Logged a second execution-state warning from maintainership
  review so the architecture plan stays honest about current extraction status.
  The package-layout/shim system is directionally correct, but several signals
  are still "policy says this should exist" rather than "the tree already
  matches": crowded `devctl` roots are passing mostly under freeze-mode,
  `devctl/commands` still has more intended namespaces in docs than in the real
  package tree, root shim counts remain above budget, and bootstrap still has a
  Python-version mismatch on machines where `python3` is 3.10. That evidence
  reinforces the current plan stance: next work is continued decomposition and
  self-hosting reliability, not declaring the packaging boundary finished.
- 2026-03-12: Landed the next executable runtime seam under
  `dev/scripts/devctl/runtime/`: `TypedAction`, `RunRecord`, `ArtifactStore`,
  `ProviderAdapter`, and `WorkflowAdapter` now exist as real typed contract
  records with mapping adapters and focused unit coverage. They are not yet the
  universal execution path for Ralph/review-channel/frontends, but the runtime
  layer now owns more than status snapshots alone, which is the right next
  step before adapterizing the higher-level loops.
- 2026-03-12: Wired `TypedAction` into the first live command path:
  `devctl controller-action` now emits a stable runtime contract in both the
  command report and the persisted controller-mode artifact, so phone/mobile
  surfaces and later adapters can inspect one deterministic operator-action
  payload instead of inferring intent from mixed CLI args and ad-hoc result
  dicts. This is the first non-blueprint execution path under `MP-377`; the
  next candidates should be `review-channel` and Ralph dispatch/remediation
  flows.
- 2026-03-12: Promoted layout governance from “new file placement” into a
  self-hosting platform requirement. The package-layout engine now needs to do
  two things at once: freeze further growth in already crowded flat roots such
  as `dev/scripts/checks` / `dev/scripts/devctl` / `commands` / `tests`, and
  surface that baseline crowding explicitly so external-repo adopters and
  agents can understand the organization contract before drift starts.
- 2026-03-12: Extended the same self-hosting layout governance to crowded flat
  module families. `check_package_layout.py` should now surface families such
  as `devctl/commands/check_*`, `autonomy_*`, `docs_*`, `release_*`, and
  `ship_*` as explicit baseline debt while freezing further flat growth toward
  concrete namespace targets. Thin public wrappers may still stay flat when the
  policy marks them as compatibility shims. This closes a real blind spot:
  directory counts alone were not enough to explain why `commands/` still
  looked like a dumping ground even after crowding rules landed.
- 2026-03-12: Tightened self-hosting/adoption behavior again: `package_layout`
  now emits one blocking baseline violation per crowded root/family during
  `--adoption-scan` instead of only warning about them. That means external
  repos and `devctl` itself can fail a full topology audit for existing layout
  debt without requiring a new file to be added first, while normal working-
  tree mode still preserves the lighter freeze-on-drift behavior.
- 2026-03-12: Validation against `devctl check --profile ci --adoption-scan`
  confirmed the new package-layout behavior, but it also exposed a separate
  portability gap outside this slice: several other guards still assume a clean
  worktree or a real git ref instead of the adoption-scan empty-tree sentinel,
  and tracked deleted files in a migration-heavy worktree can still surface
  parser noise. That follow-up belongs under the same self-hosting/adoption
  hardening track before claiming full portable first-run parity.
- 2026-03-12: Tightened the same layout-governance seam around compatibility
  wrappers. `package_layout/bootstrap.py` now owns the package-local
  import/runtime bridge instead of repeating repo-root fallback logic across
  each module, and compatibility shims are now a portable validated concept:
  wrapper shape is structural, policy can require standard metadata fields, and
  crowded root/family reports can distinguish real implementation density from
  approved transitional shims.
- 2026-03-12: Extended that compatibility-shim contract into the advisory
  review layer too. `probe_compatibility_shims.py` now reuses the same
  portable shim primitive to surface stale wrapper debt
  (missing/expired metadata, broken targets, shim-heavy roots/families), and
  even the fallback `run_probe_report.py` path now resolves probe entrypoints
  from shared policy/registry state instead of carrying a second flat list by
  hand. That is the architecture we want everywhere: one engine primitive,
  repo-owned policy knobs, and thin public runners that stay aligned by
  construction.
- 2026-03-13: Burned down the remaining live `probe_single_use_helpers` debt
  in the current extraction seam. `controller_action.py`, `docs_check.py`,
  `path_audit.py`, and `runtime/control_state.py` now keep only named
  runtime/governance seams instead of one-use private wrappers, and the probe
  packet is down to one real portability signal: the oversized
  `dev/scripts/devctl` root shim population that still needs a package/repo-
  pack extraction pass rather than more local micro-cleanups.
- 2026-03-13: Consolidated the repo-grounded architecture review and full
  staged roadmap directly into this file so `MP-377` now has one main active
  plan linked from the tracker instead of relying on chat transcripts and
  overlapping docs. The explicit working stance is now: this file is the
  canonical active plan for the standalone governance product,
  `dev/active/portable_code_governance.md` remains the narrower engine
  companion, `dev/active/MASTER_PLAN.md` remains the tracker, and immediate
  execution starts with documentation consolidation plus canonical
  policy/config normalization.
- 2026-03-13: Added an explicit `Session Resume` contract to this plan so new
  AI conversations do not restart from scratch. The intended operating model is
  now: this file holds the canonical left-off state for `MP-377`, fresh AI
  sessions must read it before proceeding, and each substantive session should
  refresh both `Session Resume` and `Progress Log` before handoff.
- 2026-03-13: Hardened the repo-facing docs-governance path around this plan.
  `dev/config/devctl_repo_policy.json` now carries a policy-owned
  `tooling_doc_requirement_rules` entry that requires
  `dev/active/ai_governance_platform.md` for platform-scope tooling/policy/
  runtime/extraction changes, and `devctl docs-check` now enforces that rule
  without hardcoding VoiceTerm-only plan logic into the command.
- 2026-03-13: Audited the platform plan for context efficiency and found a real
  architecture gap: `MP-377` previously tracked rule quality, portability, and
  evidence quality, but not whether those gains required unsustainably large
  prompt/context usage. This plan now treats context as a first-class platform
  contract through `ContextPack` and `ContextBudgetPolicy`, adds completion and
  execution gates for bounded context usage, requires usage-tier guidance for
  adopters, and routes context telemetry into future `RunRecord` / event-
  history work so code-quality gains are measured against prompt cost too.
- 2026-03-13: Refactored `devctl docs-check` into
  `dev/scripts/devctl/commands/docs/` so the new canonical-plan enforcement
  path also satisfies the repo's own shape, complexity, parameter-count, and
  dict-schema guards. Validation for that slice included targeted `pytest`
  coverage plus `check_architecture_surface_sync`,
  `check_agents_bundle_render`, `docs-check --strict-tooling`, and
  `check --profile ci`.
- 2026-03-13: Clarified the platform's history model so contributors stop
  mixing session handoff with structured telemetry. The repo now says
  explicitly that `Session Resume` / `Progress Log` are the canonical restart
  surface for `MP-377`, while `devctl_events.jsonl`,
  `finding_reviews.jsonl`, watchdog episodes, and later `RunRecord`
  projections are the machine-readable runtime evidence that should feed
  metrics, optional SQLite indexing, and later ML/ranking layers.
- 2026-03-13: Tightened the operator/handoff rule around those ledgers. The
  repo now says explicitly that agents should not hand-edit command audit
  JSONL, should use `devctl` for command telemetry, should append
  `governance-review --record` rows before handoff for adjudicated findings,
  and should call out any non-`devctl` telemetry gaps in the handoff rather
  than implying complete machine coverage.
- 2026-03-13: Raised the accuracy bar in plan state. The repo now explicitly
  treats broader `--adoption-scan` audit cycles plus richer watchdog evidence
  as a prerequisite for strong platform-accuracy claims, and it now treats
  recorded false positives as rule-quality defects that need root-cause
  analysis and a narrowing/tuning follow-up rather than passive counting.
- 2026-03-13: Expanded the missing-scope list again to cover the next gaps that
  matter before DB/ML/product claims: adjudication coverage metrics, formal
  DB-ingestion/provenance contracts, privacy/redaction rules for structured
  telemetry, and measured promotion criteria for moving advisory probes into
  blocking guard tiers.
- 2026-03-13: Expanded the plan again around long-range trustworthiness gaps
  that the repo already implies but had not made explicit enough: a replayable
  cross-repo rule-quality corpus/harness for regression measurement, and one
  waiver/suppression lifecycle so false positives are narrowed instead of
  quietly converted into permanent exceptions.
- 2026-03-13: Tightened the plan's closure bar and language strategy. `MP-377`
  now says this product is not "done" until architecture, pipeline, telemetry,
  and reviewed-evidence trust are all proven together; it also now makes
  continued Python/Rust pattern mining a standing workstream and defines future
  language support as one shared analyzer-contract problem, not a series of
  repo-specific bolt-ons.
- 2026-03-13: Cleared the immediate scope-loss risk for fresh AI sessions by
  staging `dev/active/ai_governance_platform.md` and
  `dev/guides/AI_GOVERNANCE_PLATFORM.md` in git, then updated `Session Resume`
  so the next conversation can begin directly from Phase 2 / runtime-evidence
  work instead of re-litigating whether the canonical plan is preserved.
- 2026-03-13: Validated the current multi-agent execution path before starting
  Phase 2 work. The bridge-gated dry-run command
  `python3 dev/scripts/devctl.py review-channel --action launch --terminal none --dry-run --format md --refresh-bridge-heartbeat-if-stale`
  passed on the active tree, refreshed `code_audit.md`, and confirmed that the
  repo can still launch the planned 8 Codex reviewer lanes plus 8 Claude coder
  lanes from repo-owned state. That means `MP-377` implementation can use the
  existing reviewer/coder system now, while still treating peer-liveness,
  stale-peer recovery, and full hands-off proof as open `MP-358` closure work
  rather than assumed product completeness.
- 2026-03-13: Turned the machine-first output rule into concrete self-hosting
  behavior for the moved governance package. `governance-bootstrap`,
  `governance-export`, `governance-review`, and `render-surfaces` now share a
  package-local output/error helper that treats JSON as the canonical machine
  payload and markdown as the human projection; a new dispatch-level CLI test
  proves parser + `COMMAND_HANDLERS` + JSON output stability across the moved
  governance family; and `check_architecture_surface_sync.py` now resolves
  aliased nested command imports so package-owned command modules are enforced
  correctly instead of being judged by flat-root-only expectations.
- 2026-03-13: Audited the next machine-output step before changing the shared
  helper again. The current `--output` path already avoids full stdout JSON
  dumps because `write_output()` writes the artifact and prints only `Report
  saved to: ...`; the real platform gap is that the receipt is human prose and
  the runtime/data-science stack still does not measure artifact bytes,
  hashes, or estimated tokens. The next slice should add a dedicated
  machine-artifact emitter plus artifact-cost telemetry for JSON-canonical
  surfaces instead of globally forcing every human-oriented `devctl` command
  through the same control-channel contract.
- 2026-03-13: Implemented the first machine-artifact emission slice. The new
  shared machine-output path now powers `governance-*`,
  `platform-contracts`, `probe-report`, `data-science`, and `loop-packet`
  when they emit JSON: `--format json --output ...` writes one compact JSON
  artifact file plus a compact JSON receipt on stdout instead of the old human
  `Report saved to:` string, and `devctl_events` / `data-science` now record
  artifact path/hash/byte/token metrics (including stdout receipt size) so the
  repo can compare context cost against fix quality over time.
- 2026-03-13: Finished the first generated-surface integration pass so the new
  repo-pack surface layer is no longer just files on disk. `render-surfaces`
  is now reachable from the public CLI and `devctl list`, the parser/command
  code moved under governance-owned namespaces instead of adding more crowded
  flat-root modules, and the paired
  `check_instruction_surface_sync.py` guard now runs in
  tooling/release governance bundles and workflows.
- 2026-03-13: Completed the broader repo-pack surface-generation wiring around
  that first pass. `dev/config/devctl_repo_policy.json` now owns
  `repo_governance.surface_generation` for repo-pack metadata, shared template
  context, and governed outputs; portable starter policy/bootstrap flows seed
  the same contract for adopter repos; maintainer docs now document
  `render-surfaces`; and focused regression coverage protects the new parser,
  docs-check messaging, starter-policy generation, and surface reports.
- 2026-03-13: Hardened that Phase 2 generated-surface contract for real
  day-to-day use. `render-surfaces` now treats missing local-only outputs as a
  non-failing report state while keeping `--write` as the explicit materialize
  path, portable starter bootstrap now points adopters at
  `render-surfaces --write`, the durable architecture guide now names the
  generated instruction/starter assets directly, and the focused test surface
  covers both the repo-local report semantics and the bootstrap next-step
  contract.
- 2026-03-13: Re-ran the self-hosting governance proof path after the
  concurrent layout/integration edits settled. These commands passed on the
  current tree under the repo-required Python 3.11 interpreter:
  `devctl render-surfaces --format md`,
  `check_instruction_surface_sync.py`,
  `check_package_layout.py`,
  `check_architecture_surface_sync.py`,
  `check_bundle_workflow_parity.py`,
  `check_guard_enforcement_inventory.py`,
  `check_bundle_registry_dry.py`,
  `pytest dev/scripts/devctl/tests/governance/test_render_surfaces.py dev/scripts/devctl/tests/test_bundle_registry.py dev/scripts/devctl/tests/test_script_catalog.py`,
  `devctl docs-check --strict-tooling`,
  `check_active_plan_sync.py`,
  `check_multi_agent_sync.py`,
  `devctl hygiene --strict-warnings`,
  and elevated `devctl process-cleanup --verify --format md`. The broader
  `devctl check --profile ci` lane still fails, but the remaining red is now
  outside this generated-surface/layout slice: pre-existing shape and
  dict-schema debt in `dev/scripts/devctl/governance/bootstrap_policy.py` and
  `dev/scripts/devctl/governance/surfaces.py`.
- 2026-03-13: Concurrent namespace work briefly re-broke the focused
  generated-surface regression path after that validation snapshot. The active
  runtime helper path is now `dev/scripts/devctl/governance/surface_runtime.py`
  (no separate `surfaces_runtime.py` remains in the current tree), its
  `check_agents_bundle_render` import now resolves package-style pytest runs
  without relying on a flat-root `checks` module, the public guard runner now
  lives at `dev/scripts/checks/check_instruction_surface_sync.py`,
  and the docs-check strict-tooling fixture now points at
  `dev/scripts/devctl/commands/governance/render_surfaces.py` instead of the
  old flat command path. Re-run the focused governance tests before trusting
  any older "targeted pytest passed" note from this date.
- 2026-03-13: Revalidated the same slice again after a larger concurrent
  modularization wave touched much of `dev/scripts/**`. The important nuance
  is now explicit for future sessions: `check_package_layout.py` is green
  because the new generated-surface/governance files are placed correctly and
  the self-hosting rules are blocking new flat-root growth there, but the repo
  still carries freeze-mode crowding in `dev/scripts/checks`,
  `dev/scripts/devctl`, `dev/scripts/devctl/commands`, and
  `dev/scripts/devctl/tests`. The next structural follow-up is therefore not
  more generated-surface wiring; it is continued decomposition of those
  crowded roots while the Phase 2 context-budget/runtime work moves forward.
- 2026-03-13: Fixed a concurrent registry/docs/workflow drift that had pointed
  the generated-surface sync guard at
  `dev/scripts/checks/package_layout/check_instruction_surface_sync.py`.
  Restored the stable public root shim at
  `dev/scripts/checks/check_instruction_surface_sync.py`, kept the
  package-local implementation under `dev/scripts/checks/package_layout/`,
  resynced bundle/workflow/docs/test references, and revalidated with
  `check_instruction_surface_sync.py`, `check_package_layout.py`,
  `check_agents_bundle_render.py`, `check_bundle_workflow_parity.py`,
  `devctl render-surfaces --format md`, `devctl docs-check --strict-tooling`,
  and focused `pytest` over `test_governance_bootstrap.py`,
  `test_render_surfaces.py`, `test_docs_check.py`, and
  `test_check_guard_enforcement_inventory.py`.
- 2026-03-13: Closed the Phase 2 repo-pack surface-generation slice on a green
  self-hosting validation bundle. Portable governance onboarding docs/templates
  now explicitly tell adopters to tighten
  `repo_governance.surface_generation.*` and run
  `python3 dev/scripts/devctl.py render-surfaces --write --format md`, the
  final parameter-count regression in `bootstrap_surfaces.py` was resolved via
  a typed `SurfaceSeed` wrapper, and these end-of-session gates passed on the
  final tree: `devctl check --profile ci`, `devctl docs-check --strict-tooling`,
  `check_active_plan_sync.py`, `check_agents_bundle_render.py --format md`,
  `check_multi_agent_sync.py`, `check_instruction_surface_sync.py --format md`,
  and `check_package_layout.py`. The remaining probe output is advisory only:
  `surface_runtime.py` still carries medium design-smell hints and the broader
  `dev/scripts/devctl` compatibility-shim backlog remains active platform debt.
- 2026-03-13: Started burning down the crowded flat-root governance family
  under `dev/scripts/devctl/commands/` and `dev/scripts/devctl/tests/`.
  `governance-bootstrap`, `governance-export`, and `governance-review` now
  live under `dev/scripts/devctl/commands/governance/`, their focused tests now
  live under `dev/scripts/devctl/tests/governance/`, and
  `dev.scripts.devctl.commands` re-exports the governance modules so repo
  package imports can stay stable without keeping more `governance_*` files in
  the crowded command root.
- 2026-03-13: Validated a consolidated multi-agent gap synthesis against the
  active `MP-377` plan and current repo state. Confirmed that context-budget
  contracts, the finding/review/metric evidence schema, the replayable
  evaluation harness, the promotion/demotion rubric, and the
  waiver/suppression lifecycle were already acknowledged as platform gaps but
  still lived mostly in checklist or narrative form instead of the phase
  roadmap. Promoted those into explicit phase scope, added the missing package
  install surface (`pyproject.toml`, build backend, CLI entrypoint),
  repo-pack-owned path-resolution contract (`RepoPathConfig`), repo-pack /
  platform compatibility requirement, expanded adapter/frontend file lists, and
  added pilot-proof expectations for compatibility and public differentiation
  so extraction does not run ahead of the supporting contracts.
- 2026-03-14: Closed the next instruction-surface governance gap for cross-AI
  portability. The generated `claude_instructions` repo-pack surface now
  carries explicit blocking post-edit verification language, repo policy can
  declare required rendered snippets, `render-surfaces` /
  `check_instruction_surface_sync` fail when those semantics disappear, and the
  governance tests now pin the VoiceTerm-specific done criteria (`bundle.*`
  routing plus `check --profile ci`) so Claude-facing local instructions do
  not silently collapse back into a non-binding command list.
- 2026-03-14: Accepted the next MP-377 command/runtime boundary cuts after
  focused validation. `mobile_status.py` now reads review status through
  `repo_packs.review_helpers.load_mobile_review_state()` instead of importing
  `review_channel.events`, `review_channel.event_store`, or
  `review_channel.state` directly, and the narrow `controller_action.py` /
  `triage_loop.py` checks-layer reroute now uses devctl-owned
  `process_helpers.resolve_repo` / `run_capture` instead of reaching into
  `checks.coderabbit_ralph_loop_core`. That closes the current command-layer
  fit-gap without forcing a larger controller redesign in the same slice and
  moves the next extraction target to governance evidence path ownership plus
  autonomy default-profile ownership.

## Audit Evidence

- `dev/scripts/devctl/platform/contracts.py`
- `dev/scripts/devctl/platform/blueprint.py`
- `dev/scripts/devctl/platform/parser.py`
- `dev/scripts/devctl/commands/platform_contracts.py`
- `dev/scripts/devctl/repo_packs/voiceterm.py`
- `dev/scripts/devctl/runtime/control_state.py`
- `dev/scripts/devctl/runtime/action_contracts.py`
- `dev/scripts/devctl/runtime/review_state.py`
- `dev/scripts/checks/check_platform_layer_boundaries.py`
- `dev/scripts/checks/check_architecture_surface_sync.py`
- `dev/scripts/checks/architecture_boundary/command.py`
- `dev/scripts/checks/check_test_coverage_parity.py`
- `dev/scripts/devctl/common.py`
- `dev/scripts/devctl/controller_action_support.py`
- `dev/scripts/devctl/mobile_status_views.py`
- `dev/scripts/devctl/commands/mobile_status.py`
- `dev/scripts/devctl/commands/controller_action.py`
- `dev/scripts/devctl/commands/triage_loop.py`
- `dev/scripts/devctl/repo_packs/review_helpers.py`
- `dev/scripts/devctl/governance_review_log.py`
- `dev/scripts/devctl/governance/external_findings_log.py`
- `dev/scripts/devctl/data_science/metrics.py`
- `dev/scripts/devctl/autonomy/run_parser.py`
- `dev/scripts/devctl/review_channel/core.py`
- `dev/scripts/devctl/review_channel/state.py`
- `dev/scripts/devctl/tests/test_action_contracts.py`
- `dev/scripts/devctl/tests/test_controller_action.py`
- `dev/scripts/devctl/tests/test_check_architecture_surface_sync.py`
- `dev/scripts/devctl/tests/checks/architecture_boundary/test_check_platform_layer_boundaries.py`
- `dev/scripts/devctl/tests/checks/package_layout/test_rules.py`
- `dev/scripts/devctl/tests/test_check_router.py`
- `dev/scripts/devctl/tests/test_check_test_coverage_parity.py`
- `dev/scripts/devctl/tests/test_common.py`
- `app/operator_console/state/review/review_state.py`
- `app/operator_console/state/snapshots/snapshot_builder.py`
- `app/operator_console/state/sessions/session_builder.py`
- `app/operator_console/state/sessions/session_builder_support.py`
- `app/operator_console/collaboration/conversation_state.py`
- `app/operator_console/collaboration/task_board_state.py`
- `app/operator_console/state/snapshots/phone_status_snapshot.py`
- `app/operator_console/workflows/workflow_presets.py`
- `dev/active/portable_code_governance.md`
- `dev/active/autonomous_control_plane.md`
- `dev/active/operator_console.md`
- `dev/active/ralph_guardrail_control_plane.md`
- `dev/guides/AI_GOVERNANCE_PLATFORM.md`
- `dev/guides/DEVELOPMENT.md`
- `dev/guides/PORTABLE_CODE_GOVERNANCE.md`
- `dev/audits/METRICS_SCHEMA.md`
- `dev/scripts/README.md`
- `AGENTS.md`
- `dev/active/MASTER_PLAN.md`
- `dev/active/INDEX.md`
- `dev/config/devctl_repo_policy.json`
- `dev/config/templates/claude_instructions.template.md`
- `dev/scripts/devctl/commands/docs_check.py`
- `dev/scripts/devctl/commands/docs_check_policy.py`
- `dev/scripts/devctl/commands/docs_check_render.py`
- `dev/scripts/devctl/commands/docs/check_runtime.py`
- `dev/scripts/devctl/commands/docs/policy_defaults.py`
- `dev/scripts/devctl/commands/docs/policy_runtime.py`
- `dev/scripts/devctl/commands/docs/render_sections.py`
- `dev/scripts/devctl/commands/governance/render_surfaces.py`
- `dev/scripts/devctl/governance/parser.py`
- `dev/scripts/devctl/governance/bootstrap_surfaces.py`
- `dev/scripts/devctl/governance/surfaces.py`
- `dev/scripts/devctl/governance/surface_runtime.py`
- `dev/scripts/checks/check_instruction_surface_sync.py`
- `dev/scripts/checks/package_layout/instruction_surface_sync.py`
- `dev/scripts/devctl/commands/governance/bootstrap.py`
- `dev/scripts/devctl/commands/governance/export.py`
- `dev/scripts/devctl/commands/governance/review.py`
- `dev/scripts/devctl/tests/governance/test_governance_bootstrap.py`
- `dev/scripts/devctl/tests/governance/test_governance_export.py`
- `dev/scripts/devctl/tests/governance/test_governance_review.py`
- `dev/config/templates/portable_governance_repo_setup.template.md`
- `dev/scripts/devctl/tests/governance/test_render_surfaces.py`
- `dev/scripts/devctl/tests/test_docs_check.py`
- `dev/scripts/devctl/tests/test_docs_check_constants.py`
- `dev/scripts/devctl/tests/test_quality_policy.py`
