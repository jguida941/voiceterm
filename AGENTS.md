# Agents

This file is the canonical SDLC, release, and AI execution policy for this repo.
If any process docs conflict, follow `AGENTS.md` first.

## Purpose

VoiceTerm is a polished, voice-first overlay for AI CLIs.
Primary support: **Codex** and **Claude Code**.
Gemini CLI remains experimental.

Goal of this file: give agents one repeatable process so every task follows the
same execution path with minimal ambiguity.

Top-level enforcement rule: every time an agent creates a file or edits an
existing file, it must run the relevant repo guard/check scripts before
handoff to catch bad practices, policy drift, and structural regressions. This
is mandatory even for small patches. At minimum, run the task-class bundle plus
any touched risk-matrix add-ons, then follow the concrete post-edit check
inventory in `dev/guides/DEVELOPMENT.md` (`What checks protect us` and
`After file edits`).

Direct post-edit enforcement link:
- After every file create/edit, follow
  `dev/guides/DEVELOPMENT.md#after-file-edits` before handoff.

Release-governance note:
- When preparing a release, treat `bundle.release` as the blocking source of
  truth and make sure maintainer docs (`AGENTS.md`,
  `dev/guides/DEVELOPMENT.md`, `dev/active/MASTER_PLAN.md`,
  `dev/history/ENGINEERING_EVOLUTION.md`) plus canonical user docs
  (`README.md`, `QUICK_START.md`, `guides/USAGE.md`, `guides/CLI_FLAGS.md`,
  `guides/INSTALL.md`, `guides/TROUBLESHOOTING.md`) reflect the shipped
  behavior. Recent control-plane/mobile changes also require the
  `check_mobile_relay_protocol.py` guard to stay green in runtime and release
  bundles.

## Source-of-truth map

| Question | Canonical source |
|---|---|
| What are we executing now? | `dev/active/MASTER_PLAN.md` |
| What active docs exist and what role does each play? | `dev/active/INDEX.md` |
| Where is active-doc execution authority vs reference-only scope defined? | `dev/active/INDEX.md` (`Role`, `Execution authority`, `When agents read`) |
| Where is consolidated Theme Studio + overlay visual planning context? | `dev/active/theme_upgrade.md` |
| Where is long-range phase-2 research context? | `dev/deferred/phase2.md` (bridge at `dev/active/phase2.md`) |
| Where is the `devctl` reporting + CIHub integration roadmap? | `dev/active/devctl_reporting_upgrade.md` |
| Where is the autonomous loop + mobile control-plane execution spec? | `dev/active/autonomous_control_plane.md` |
| Where is the shared review-channel + dual-agent shared-screen execution plan? | `dev/active/review_channel.md` |
| Where is the host-process hygiene + Activity Monitor automation plan? | `dev/active/host_process_hygiene.md` |
| Where is the continuous local Codex-reviewer / Claude-coder loop hardening and later template-extraction plan? | `dev/active/continuous_swarm.md` |
| Where is the optional VoiceTerm Operator Console plan? | `dev/active/operator_console.md` |
| Where is the Ralph guardrail remediation/control-plane plan? | `dev/active/ralph_guardrail_control_plane.md` |
| Where is the heuristic review-probe execution plan? | `dev/active/review_probes.md` |
| Where is the code-shape expansion research companion (readability, coupling, AI-specific, information-theoretic probes/guards)? | `dev/active/code_shape_expansion.md` (subordinate evidence/calibration companion feeding `dev/active/review_probes.md` Phase 5b+, not a second execution authority) |
| Where is the portable code-governance engine / multi-repo portability and measurement plan? | `dev/active/portable_code_governance.md` (engine/adoption companion plan) |
| Where is the full reusable AI governance platform / package-extraction architecture plan? | `dev/active/ai_governance_platform.md` (the only main active architecture plan for this product scope) |
| Where is the current `MP-377` startup-authority / repo-pack / typed-plan-registry / runtime-evidence-context closure plan? | `dev/active/platform_authority_loop.md` (subordinate `MP-377` execution spec; read after `dev/active/ai_governance_platform.md`) |
| Where is the governed active-plan markdown contract used by docs-governance and future `PlanRegistry` work? | `dev/active/PLAN_FORMAT.md` (reference-only companion for plan-doc schema/self-hosting) |
| Where is the durable reusable AI governance platform thesis/architecture guide? | `dev/guides/AI_GOVERNANCE_PLATFORM.md` (durable companion to the active platform plan) |
| Where is the loop-output-to-chat coordination runbook? | `dev/active/loop_chat_bridge.md` |
| Where is the completed Rust workspace path/layout migration record? | `dev/archive/2026-03-07-rust-workspace-layout-migration.md` |
| Where is the naming/API cohesion execution plan? | `dev/active/naming_api_cohesion.md` |
| Where is the IDE/provider adapter modularization execution plan? | `dev/active/ide_provider_modularization.md` |
| Where is the pre-release architecture/tooling cleanup execution plan? | `dev/active/pre_release_architecture_audit.md` |
| Where is the consolidated full-surface audit evidence used by that plan? | `dev/active/audit.md` (reference-only) |
| Where is the raw multi-agent audit merge transcript for that evidence set? | `dev/active/move.md` (reference-only supporting evidence) |
| Where are federated internal repo links/import rules (`code-link-ide`, `ci-cd-hub`)? | `dev/integrations/EXTERNAL_REPOS.md` |
| Where do we track repeated manual friction and automation debt? | `dev/audits/AUTOMATION_DEBT_REGISTER.md` |
| Where is the baseline full-surface audit runbook/checklist? | `dev/audits/2026-02-24-autonomy-baseline-audit.md` |
| Where are audit metrics definitions (AI vs script share, automation coverage, charts)? | `dev/audits/METRICS_SCHEMA.md` |
| How do we run the current parallel Codex/Claude markdown swarm cycle? | `dev/active/review_channel.md` |
| Where is the local-first continuous swarm execution contract (next-task promotion, peer liveness, context rotation)? | `dev/active/continuous_swarm.md` |
| Where are `devctl` command semantics and examples? | `dev/scripts/README.md` |
| Where is the plain-language `devctl` system architecture map, including portable naming/map direction? | `dev/guides/DEVCTL_ARCHITECTURE.md` |
| Where is the devctl automation playbook? | `dev/guides/DEVCTL_AUTOGUIDE.md` |
| Where is MCP-to-devctl architecture alignment and extension policy? | `dev/guides/MCP_DEVCTL_ALIGNMENT.md` |
| Where is the portable-governance engine boundary, export flow, and benchmark/evaluation guide? | `dev/guides/PORTABLE_CODE_GOVERNANCE.md` (engine/adoption companion guide) |
| Where is repo-local / portable guard-probe policy and repo-pack surface generation? | `dev/config/devctl_repo_policy.json`, `dev/config/quality_presets/`, and the `dev/scripts/devctl/quality_policy*.py` resolver stack |
| Where is the remediation scaffold template used by guard-driven Rust audits? | `dev/config/templates/rust_audit_findings_template.md` |
| What user behavior is current? | `guides/USAGE.md`, `guides/CLI_FLAGS.md` |
| What flags are actually supported? | `rust/src/bin/voiceterm/config/cli.rs`, `rust/src/config/mod.rs` |
| How do we build/test/release? | `dev/guides/DEVELOPMENT.md`, `dev/scripts/README.md` |
| Where is the developer lifecycle quick guide? | `dev/guides/DEVELOPMENT.md` (`End-to-end lifecycle flow`, `What checks protect us`, `When to push where`) |
| Where are clean-code and Rust-reference rules defined? | `AGENTS.md` (`Engineering quality contract`), `dev/guides/DEVELOPMENT.md` (`Engineering quality review protocol`) |
| What process is mandatory? | `AGENTS.md` |
| What architecture/lifecycle is current? | `dev/guides/ARCHITECTURE.md` |
| Where are CI lane implementations and release publishers? | `.github/workflows/` |
| Where is the plain-language workflow guide? | `.github/workflows/README.md` |
| Where is process history tracked? | `dev/history/ENGINEERING_EVOLUTION.md` |

## Instruction scope and precedence

When multiple instruction sources exist, apply this precedence:

1. Session-level system/developer/user instructions.
2. The nearest `AGENTS.md` to the files being edited.
3. Ancestor `AGENTS.md` files (including repo root).
4. Linked owner docs from the source-of-truth map.

If subtrees require different workflows, add nested `AGENTS.md` files and keep
them scoped to that subtree.

## Autonomous execution route (required)

Use this route to run end-to-end without ambiguity:

1. Load `dev/active/INDEX.md`, then `dev/active/MASTER_PLAN.md`.
2. Use `INDEX.md` role/authority fields to decide which active docs are required:
   - `tracker` is execution authority.
   - `spec` is read when matching MP scope is in play.
   - `runbook` is read for active multi-agent cycles.
   - `reference` is context-only; do not treat as execution state.
3. Select task class in the router table and run the matching command bundle.
4. Apply risk-matrix add-ons for touched runtime risk classes.
5. Run docs-governance/self-review/end-of-session checklist before handoff.

## Mandatory 12-step SOP (always)

Run this sequence for every task. Do not skip steps.

1. Run session bootstrap checks and load `dev/active/INDEX.md` (`bundle.bootstrap`).
   Alternatively, run `python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md`
   for a slim startup context with active plans, hotspots, and deep links.
   Follow the deep links when the task requires full authority from the
   canonical docs (`AGENTS.md`, `dev/active/INDEX.md`, `dev/active/MASTER_PLAN.md`).
   Keep that bootstrap packet small by default and expand with
   `context-graph --query '<term>'` when the task needs more context.
2. Decide scope (`develop` work or `master` release work).
3. Classify task using the task router table.
4. Load only the required context pack listed for your task class.
5. Link or confirm MP scope in `dev/active/MASTER_PLAN.md` before edits.
6. Implement changes and tests.
7. Run the bundle required by your task class.
8. Run matrix tests required by touched risk classes.
9. Update docs/screenshots/ADRs required by governance.
10. Self-review security, memory, errors, concurrency, performance, and style.
11. Push through branch policy and run post-push audit (`bundle.post-push`).
12. Capture handoff summary using `dev/guides/DEVELOPMENT.md` template.

## Execution-plan traceability (required)

For non-trivial work (runtime/tooling/process/CI/release), execution must be
anchored in an active tracked plan doc under `dev/active/`.

1. Create or update the relevant execution-plan doc before implementation
   (for example `dev/active/autonomous_control_plane.md`).
2. Execution-plan docs must include the marker line:
   `Execution plan contract: required`.
3. Execution-plan docs must include these sections:
   - `## Scope`
   - `## Execution Checklist`
   - `## Progress Log`
   - `## Session Resume`
   - `## Audit Evidence`
3.1 Execution-plan docs must expose one parseable metadata header near the top
    of the file. Follow `dev/active/PLAN_FORMAT.md` when editing or creating
    governed plan markdown.
4. The associated MP scope must be present in both `dev/active/INDEX.md` and
   `dev/active/MASTER_PLAN.md`.
4.1 In multi-agent runs, progress/decisions must be written into the active
    plan markdown and/or `MASTER_PLAN` updates; hidden memory-only coordination
    is not acceptable execution state.
4.2 For substantive AI sessions, keep restart state in the active plan's
    `Session Resume` and `Progress Log`. Structured JSONL audit/event logs are
    for machine-readable execution evidence, metrics, and later database/ML
    ingestion, not prose session handoff.
4.3 Do not hand-edit command audit JSONL logs. `python3 dev/scripts/devctl.py`
    commands auto-emit machine-readable event rows; use
    `python3 dev/scripts/devctl.py governance-review --record ...` only for
    adjudicated guard/probe outcomes. If meaningful non-`devctl` work happened
    outside that telemetry path, call out the coverage gap in handoff notes.
5. `python3 dev/scripts/checks/check_active_plan_sync.py` is the enforcement
   gate and must pass before merge.

## Continuous improvement loop (required)

Use a repeat-to-automate loop so the toolchain gets stronger after every run.

1. Record friction points in the active-plan progress log and/or handoff notes
   for every non-trivial execution session.
2. If the same workaround/manual step repeats 2+ times in the same MP scope,
   resolve it before closure by:
   - automating it as a guarded `devctl` command/workflow/check with tests, or
   - logging it as explicit debt in `dev/audits/AUTOMATION_DEBT_REGISTER.md`
     with owner, risk, and exit criteria.
2.1 If `python3 dev/scripts/devctl.py process-cleanup --verify --format md`
    or `python3 dev/scripts/devctl.py process-audit --strict --format md`
    finds a new leaked-process shape, extend the cleanup/audit automation in
    the same MP scope before closure or log explicit debt with the missed
    process shape and the guard path needed to catch it next time.
2.2 When a real issue is found by audit/review/manual use and the current
    tooling did not catch it, first decide whether the miss belongs in an
    existing guard/probe/runtime contract or should become a new reusable,
    low-noise modular enforcement path. Prefer fixing the detection gap over
    landing a one-off patch without a corresponding enforcement follow-up, and
    keep that decision in repo-visible plan state before closure.
2.3 No important issue is complete until it has been evaluated for
    architectural absorption. For any non-trivial bug, review finding,
    runtime failure, audit issue, or docs/process miss, classify whether it is
    a local defect, contract mismatch, missing guard, missing probe, authority
    boundary failure, workflow/process gap, or documentation/plan drift. Then
    either encode the prevention path in an approved surface (guard, probe,
    contract, authority rule, parity check, regression test, docs update) or
    record an explicit waiver with reason. Do not silently close meaningful
    findings as patch-only work.
3. "Cannot automate yet" is acceptable only with a documented reason and a
   guard path (checklist/runbook entry that prevents unsafe execution).
4. When automation lands, update command/docs surfaces in the same change
   (`AGENTS.md`, `dev/scripts/README.md`, `dev/guides/DEVCTL_AUTOGUIDE.md` as needed).
4.1 During staged Python module splits or relocations under `dev/scripts/**`,
    preserve stable compatibility re-exports or aliases in the old module in
    the same change until all repo importers, tests, workflows, and
    pre-commit hooks have been migrated. Treat those compatibility seams as
    part of the maintainer-facing contract, not as disposable cleanup.
5. Baseline full-surface audit execution starts from
   `dev/audits/2026-02-24-autonomy-baseline-audit.md` and should be copied
   forward for each new audit cycle.
6. Audit cycles should emit quantitative metrics from event logs
   (`automation_coverage_pct`, `script_only_pct`, `ai_assisted_pct`,
   `human_manual_pct`, `success_rate_pct`) and chart outputs via
   `python3 dev/scripts/audits/audit_metrics.py`.

## AI operating contract (required)

1. Be autonomous by default: implement, test, docs, and validation end-to-end.
2. Ask only when required: ambiguous UX/product intent, destructive actions,
   credentials/publishing/tagging, or conflicting policy signals.
3. Stay guarded: do not invent behavior, do not skip required checks.
4. After any file create/edit, run the applicable repo guard/check scripts
   before handoff; do not leave changed files unvalidated. Follow
   `dev/guides/DEVELOPMENT.md#after-file-edits`. After complex edits
   (new modules, multi-file refactors, or business-logic changes), also run
   the review probe suite to catch design-quality regressions early:
   `python3 dev/scripts/devctl.py check --profile ci` (includes probes).
4.1 Keep tooling dry-run/report-only paths portable: script-generation,
    dry-run launch, and local preflight flows must not depend on provider CLIs
    or GitHub API reachability unless the action actually needs live
    execution. Preserve explicit strict failure paths separately for real
    launch/fix execution and focused tests.
4.2 When a guard intentionally relaxes live-review freshness on GitHub-hosted
    CI, do not reuse that relaxed guard output as the only trigger for stale
    bridge auto-repair. Auto-refresh helpers must derive stale/missing
    heartbeat repairability from the bridge snapshot itself so CI parity stays
    aligned with the real launch/status contract.
4.3 Any CI job that invokes compile-time Rust guards (for example
    `check_rust_compiler_warnings.py`) must provision the repo Rust toolchain
    plus required platform headers first; tooling/docs workflows cannot assume
    those prerequisites are inherited just because the dedicated Rust CI lane
    already installs them.
4.4 In live review-channel mode, treat
    `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
    as the canonical checkpoint-budget read too. If
    `attention.status=checkpoint_required` or
    `push_enforcement.safe_to_continue_editing=false`, stop widening the
    slice and cut a checkpoint before further edits or any raw push attempt.
4.5 In that same live review-channel mode, treat
    `dev/reports/review_channel/latest/review_state.json` (and the mirrored
    `compact.json` projection) `current_session` block as the canonical typed
    current-status read for live instruction / implementer ACK state. While
    the bridge migration remains in progress, `bridge.md` is a compatibility
    projection and handoff surface, not the preferred source for current-
    status reads.
4.6 Treat `startup-context` the same way: prefer typed
    `review_state.json` fields such as `bridge.review_accepted` when that
    projection is available, and fall back to parsing live `bridge.md` only
    while the bridge-backed migration remains incomplete. Advisory
    checkpoint-budget accounting may exclude policy-declared compatibility
    projections such as `bridge.md`, but canonical git/review truth still
    comes from the real worktree plus reviewer-owned state.
4.7 Treat governed-markdown authority the same way: prefer typed
    `ProjectGovernance` outputs such as `doc_policy`, `doc_registry`, and
    parsed `plan_registry` entries when those projections are available, but
    keep the reviewed markdown `## Session Resume` content as the canonical
    restart surface until startup/runtime explicitly consume typed resume
    state instead of only a boolean presence marker.
4.8 After fixing a meaningful issue, verify both levels before handoff: the
    local defect must be fixed, and the chosen prevention/absorption path must
    either be landed and validated or explicitly deferred/waived with the
    reason recorded in repo-visible state. Passing tests alone is not
    sufficient closure when the issue exposed a reusable architecture gap.
5. Keep changes scoped: ignore unrelated diffs unless user asks.

## Prerequisites

Required tools (install before running any bundle):

- **Rust toolchain**: `rustup` with `1.88.0+` (`rustup update stable`)
- **Python**: `3.11+` (`python3 --version`)
- **cargo-deny**: `cargo install cargo-deny --locked`
- **markdownlint-cli**: `npm install -g markdownlint-cli@0.45.0`
- **GitHub CLI**: `gh auth status -h github.com`
- **jscpd** (optional, duplication audits): `npm install -g jscpd`

Interpreter note:
- `devctl` now keeps repo-owned Python subprocesses on the interpreter that
  launched `dev/scripts/devctl.py` (checks, probes, and `guard-run`
  follow-ups). If local `python3` is older than the repo requirement, invoke
  `python3.11 dev/scripts/devctl.py ...` so nested guard runs stay on the same
  runtime.

Verify with: `python3 dev/scripts/devctl.py list` (exits non-zero if critical
tools are missing).

## Error recovery protocol

When a bundle command fails mid-run:

1. **Read the failure output** — identify which check failed and why.
2. **Fix the root cause** — do not skip or retry blindly.
3. **Re-run only the failed command** to confirm the fix, then re-run the full
   bundle from the start to catch cascading issues.
4. **If the fix is non-trivial**, create an MP item and document the failure in
   the active plan's progress log before continuing.
5. **Never use `--no-verify`, `set +e`, or manual workarounds** to bypass a
   failing gate without an explicit waiver recorded in the checkpoint log.
6. **AI-operated raw `cargo test` / manual test-binary runs must prefer**
   `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test ...`
   so the post-run sweep happens automatically. If a direct/raw invocation has
   already happened, immediately execute:
   `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel`
   and confirm the `process-sweep-pre/process-sweep-post` plus
   `host-process-cleanup-post` steps report no orphaned/stale repo-related host
   processes. `quick` / `fast` now run host-side `process-cleanup --verify`
   by default unless `--no-host-process-cleanup` is passed and explicitly
   justified.
7. **When host process access is available**, run:
   `python3 dev/scripts/devctl.py process-cleanup --verify --format md`
   after manual tooling bundles and before handoff so
   Activity Monitor-visible repo leftovers are cleaned and re-checked against the full host
   process table. Use `python3 dev/scripts/devctl.py process-audit --strict --format md`
   when a read-only host inspection is needed or cleanup must be intentionally skipped. If verify stays red only because recent active local work is still running, rerun the cleanup/audit once that local work finishes; freshly detached repo-related helpers now keep strict audit/verify red immediately even before they age into the orphan bucket.
7.1 **When reproducing or watching long-running local host leaks**, run:
    `python3 dev/scripts/devctl.py process-watch --cleanup --strict --stop-on-clean --iterations <n> --interval-seconds <s> --format md`
    so the host table is re-audited on a cadence until zero repo-related
    processes remain; this watcher now exits zero once it actually recovers to
    a clean host snapshot.

## Engineering quality contract (required)

For non-trivial Rust runtime/tooling changes, contributors must:

1. Validate design/implementation against official references before coding:
   - Rust Book: `https://doc.rust-lang.org/book/`
   - Rust Reference: `https://doc.rust-lang.org/reference/`
   - Rust API Guidelines: `https://rust-lang.github.io/api-guidelines/`
   - Rustonomicon (unsafe/FFI): `https://doc.rust-lang.org/nomicon/`
   - Standard library docs: `https://doc.rust-lang.org/std/`
   - Clippy lint index: `https://rust-lang.github.io/rust-clippy/master/`
2. Keep naming and ownership explicit: names should describe behavior, modules
   should keep one responsibility, and public APIs should expose stable
   intent-based contracts.
3. Treat technical debt as explicit debt: `#[allow(...)]`, non-test
   `unwrap/expect`, and oversized files/functions require documented rationale
   and a follow-up MP item when not resolved immediately.
4. Enforce function size limits: Rust functions must stay under **100 lines**,
   Python functions under **150 lines** (`code_shape` guard). Existing
   exceptions are tracked in `code_shape_policy.py` with expiry dates; new
   oversized functions require a `FunctionShapeException` with owner, expiry,
   and decomposition reason before merge.
5. Prefer consolidation over duplication: extract shared helpers instead of
   repeating logic across overlays/themes/settings/status surfaces. The
   `function_duplication` guard blocks new identical function bodies (>= 6
   lines) across different files; if you need the same logic in two places,
   extract it to a shared module and import.
6. Keep subprocess semantics explicit in repo-owned Python tooling/app code:
   every `subprocess.run(...)` call must pass `check=` intentionally instead of
   relying on the default.
7. Broad Python exception handlers in repo-owned tooling/app code require an
   explicit nearby rationale comment
   (`broad-except: allow reason=...`) instead of silent fail-soft behavior.
8. Record references consulted in handoff for non-trivial Rust changes.

## Review probe suite — AI design-quality enforcement (required)

Review probes are heuristic scanners that detect design-quality regressions
commonly produced by AI agents. Unlike hard guards (exit 0/1), probes always
exit 0 and emit structured `risk_hints` in JSON format. They are the
**second layer** of quality enforcement:

| Layer | Purpose | Exit behavior | Registration |
|---|---|---|---|
| **A — Hard guards** | Block regressions | exit 1 on violation | `quality_policy.py` built-in guard registry + `dev/config/devctl_repo_policy.json` enablement |
| **B — Review probes** | Surface design smells | always exit 0 | `quality_policy.py` built-in probe registry + `dev/config/devctl_repo_policy.json` enablement |
| **C — AI investigative review** | Deep contextual analysis | advisory | manual / future |

### Active probes

| Probe | Detects | Python | Rust |
|---|---|---|---|
| `probe_concurrency` | Nested lock acquisition, mutex+spawn without Arc, relaxed atomics with multi-flag, poison recovery | — | yes |
| `probe_design_smells` | Excessive `getattr()` density, untyped `object` params with attribute access, format helper sprawl | yes | — |
| `probe_boolean_params` | Functions with 3+ boolean parameters (unreadable call sites) | yes | yes |
| `probe_stringly_typed` | String-literal dispatch chains that should be enums | yes | yes |
| `probe_blank_line_frequency` | Excessive blank-line gaps that make function or module logic read as fragmented instead of cohesive | yes | yes |
| `probe_identifier_density` | Dense short or opaque identifier mixes that usually signal unreadable local naming | yes | yes |
| `probe_term_consistency` | Legacy public words and mixed term families inside configured repo-owned code/docs surfaces | yes | — |
| `probe_cognitive_complexity` | Branch-heavy control flow that is hard to review, test, or safely modify | yes | yes |
| `probe_fan_out` | Functions or modules touching too many collaborators, suggesting orchestration sprawl | yes | yes |
| `probe_unwrap_chains` | `.unwrap()`/`.expect()` chains in production code (should use `?` operator) | — | yes |
| `probe_clone_density` | Excessive `.clone()` calls suggesting ownership confusion (Arc::clone excluded) | — | yes |
| `probe_type_conversions` | Redundant type conversion chains (`.as_str().to_string()` round-trips) | — | yes |
| `probe_magic_numbers` | Unnamed numeric literals in slice operations that should be named constants | yes | — |
| `probe_dict_as_struct` | Functions returning dicts with 5+ keys that should be dataclasses/TypedDict | yes | — |
| `probe_unnecessary_intermediates` | Assign-then-return patterns with generic variable names (`result`, `ret`, `output`) | yes | — |
| `probe_vague_errors` | `bail!()`/`anyhow!()` error messages without runtime context variables | — | yes |
| `probe_side_effect_mixing` | Python functions that mix orchestration or mutation with value-shaping logic in one body | yes | — |
| `probe_defensive_overchecking` | 3+ consecutive `isinstance()` checks on the same variable | yes | — |
| `probe_single_use_helpers` | Private functions (`_name`) called only once in the file (indirection without reuse) | yes | — |
| `probe_exception_quality` | Suppressive broad handlers and generic exception translation without runtime context | yes | — |
| `probe_compatibility_shims` | Missing/expired shim metadata, unresolved shim targets, and shim-heavy roots/families | yes | — |
| `probe_tuple_return_complexity` | Functions returning tuples with 3+ elements that should become named structs | — | yes |
| `probe_mutable_parameter_density` | Rust functions carrying too many mutable parameters, indicating ownership or orchestration overload | — | yes |
| `probe_match_arm_complexity` | Rust `match` arms with too much inline logic instead of extracted helpers or richer types | — | yes |

### When agents must run probes

Run probes after **any** of these events:
1. Creating a new module or file with business logic.
2. Refactoring or restructuring existing code (module splits, API changes).
3. Adding new function signatures with 3+ parameters.
4. Introducing string-based dispatch (`match`, `if/elif` chains on strings).
5. Writing concurrent/async code with shared mutable state.

Quick command: `python3 dev/scripts/devctl.py check --profile ci` runs all
hard guards **and** review probes. `python3 dev/scripts/devctl.py probe-report --format md`
is the canonical aggregated probe surface when an agent needs ranked cleanup
order, topology context, or a self-contained handoff packet. It refreshes
`review_targets.json`, `file_topology.json`, `review_packet.{json,md}`, and
hotspot `hotspots.{mmd,dot}` artifacts under `dev/reports/probes/latest/`.
Repo-root `.probe-allowlist.json` entries apply to that canonical `devctl`
path too: `design_decision` entries stay visible in a typed decision-packet
bucket instead of active debt. Matching is by `file` + `symbol` + `probe`
when the allowlist entry declares a probe id; omit `probe` only when the same
decision intentionally applies across all probes for that symbol. The root
payload may carry `schema_version: 1` and
`contract_id: "ProbeAllowlist"`. Those packets are for AI agents and human
reviewers alike; `decision_mode` only controls whether the agent may
auto-apply, should recommend, or must explain and wait for approval.
When the guard/probe surface itself changes (new `probe_*.py` or `check_*.py`
entrypoints, `script_catalog.py`, `quality_policy_defaults.py`,
`dev/config/quality_presets/*.json`, or `dev/config/devctl_repo_policy.json`),
also run `python3 dev/scripts/devctl.py quality-policy --format md` plus
`python3 dev/scripts/devctl.py render-surfaces --format md`; use `--write`
when the policy-owned AI/dev instruction surfaces need regeneration.
When the platform contract surface itself changes (`dev/scripts/devctl/platform/**`,
shared runtime contract models, probe/report schema constants, or
`repo_governance.surface_generation` contract-routing text), also run
`python3 dev/scripts/checks/check_platform_contract_closure.py` plus
`python3 dev/scripts/devctl.py platform-contracts --format md`.
For probes only:
```bash
# Canonical aggregated probe packet:
python3 dev/scripts/devctl.py probe-report --format md
python3 dev/scripts/devctl.py probe-report --format terminal

# Direct script entrypoint (fallback):
python3 dev/scripts/checks/run_probe_report.py --format md
python3 dev/scripts/checks/run_probe_report.py --format terminal

# Individual probes:
python3 dev/scripts/checks/probe_concurrency.py
python3 dev/scripts/checks/probe_design_smells.py
python3 dev/scripts/checks/probe_boolean_params.py
python3 dev/scripts/checks/probe_stringly_typed.py
python3 dev/scripts/checks/probe_blank_line_frequency.py
python3 dev/scripts/checks/probe_identifier_density.py
python3 dev/scripts/checks/probe_term_consistency.py
python3 dev/scripts/checks/probe_cognitive_complexity.py
python3 dev/scripts/checks/probe_fan_out.py
python3 dev/scripts/checks/probe_unwrap_chains.py
python3 dev/scripts/checks/probe_clone_density.py
python3 dev/scripts/checks/probe_type_conversions.py
python3 dev/scripts/checks/probe_magic_numbers.py
python3 dev/scripts/checks/probe_dict_as_struct.py
python3 dev/scripts/checks/probe_unnecessary_intermediates.py
python3 dev/scripts/checks/probe_vague_errors.py
python3 dev/scripts/checks/probe_side_effect_mixing.py
python3 dev/scripts/checks/probe_defensive_overchecking.py
python3 dev/scripts/checks/probe_single_use_helpers.py
python3 dev/scripts/checks/probe_exception_quality.py
python3 dev/scripts/checks/probe_compatibility_shims.py
python3 dev/scripts/checks/probe_tuple_return_complexity.py
python3 dev/scripts/checks/probe_mutable_parameter_density.py
python3 dev/scripts/checks/probe_match_arm_complexity.py
```

Default AI operating rule:
- Run `python3 dev/scripts/devctl.py check --profile ci` after those changes.
- Run `python3 dev/scripts/devctl.py probe-report --format md` when the change
  needs prioritization, human handoff, or AI follow-up packets.
- Use `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test ...`
  for raw Rust tests / test binaries so post-run hygiene is enforced
  automatically.

### Acting on probe findings

When a probe emits risk hints, agents MUST:
1. Read the `ai_instruction` field — it contains targeted remediation guidance.
2. Fix `high` severity hints before handoff (these are unambiguous smells).
2.1 When a live AI consumer attaches probe guidance (for example Ralph or an
    autonomy `loop-packet` draft), treat that guidance as the default repair
    plan unless you can justify waiving it with a concrete reason. Keep the
    resulting guidance disposition visible in the route's report/packet
    surface so adoption is measurable, and use
    `governance-review --record --guidance-id ... --guidance-followed ...`
    when the finding is adjudicated so the adoption signal survives outside
    the prompt text.
3. Document `medium` severity hints in handoff notes if not fixed immediately.
4. Record adjudicated probe/guard outcomes with
   `python3 dev/scripts/devctl.py governance-review --record ...` when a hint
   is confirmed, fixed, deferred, waived, or judged false-positive so the repo
   maintains a durable finding-quality ledger before handoff.
4.1 Treat every recorded `false_positive` verdict as a rule-quality defect to
    investigate. Before closing the slice, document why the signal was wrong
    and whether the fix belongs in rule narrowing, richer context capture,
    severity demotion, repo-pack policy tuning, or explicit allowlisting.
5. Never suppress probe output — probes are advisory but findings are real.

### Adding new probes

New probes must follow the established pattern:
1. Create `dev/scripts/checks/probe_<name>.py` using `probe_bootstrap.py`.
2. Register in `script_catalog.py::PROBE_SCRIPT_FILES`.
3. Register built-in probe metadata in `dev/scripts/devctl/quality_policy_defaults.py` and enable it in the relevant preset/policy file (`dev/config/quality_presets/*.json`, `dev/config/devctl_repo_policy.json`) when this repo should run it by default.
4. Include per-signal `AI_INSTRUCTIONS` dict for targeted remediation.
5. Always exit 0 — probes emit hints, never block CI.
6. Skip test files (`_is_test_path`) — test code has different design rules.

Portable policy note:
- Built-in guard/probe capability metadata now lives in
  `dev/scripts/devctl/quality_policy_defaults.py`, with resolution/inheritance
  handled by the rest of the `quality_policy*.py` stack.
- Built-in portable presets now live in `dev/config/quality_presets/*.json`.
- Repo-local enablement/default arguments live in
  `dev/config/devctl_repo_policy.json`.
- The repo policy file and any touched preset JSON files are committed source
  of truth, not local-only scratch config. If local validation depends on a
  policy/preset change, commit those `dev/config/**` files in the same slice so
  CI resolves the same guard/probe surface.
- Use `python3 dev/scripts/devctl.py quality-policy --format md` to inspect the
  resolved active guard/probe set, scopes, and warnings before reusing the
  engine somewhere else.
- Use `python3 dev/scripts/devctl.py render-surfaces --format md` to inspect
  policy-owned instruction/starter surfaces from
  `repo_governance.surface_generation`, and `--write` to regenerate them after
  template or context changes.
- Use `python3 dev/scripts/checks/check_platform_contract_closure.py` when the
  shared platform blueprint, runtime contract models, artifact schema
  metadata, or startup-surface routing changes so `platform-contracts`,
  emitted packet metadata, and AI/dev startup surfaces cannot drift apart.
- When a critical contract field gains a live consumer route (for example
  `Finding.ai_instruction` flowing from probe artifacts into the Ralph prompt),
  extend `check_platform_contract_closure.py` with a deterministic field-route
  proof so produced-but-unconsumed regressions fail before handoff.
- When that new route still needs a compatibility seam, keep one canonical
  artifact authority and structured routing keys. Do not let AI consumers
  silently negotiate between multiple artifacts or depend on prose-derived
  matching once typed fields exist; track any temporary fallback in the active
  plan and extend the relevant guard/probe so the seam cannot become
  permanent by accident.
- Use `python3 dev/scripts/devctl.py governance-export --format md` when the
  whole governance stack, latest reports, and policy/templates need to be
  handed to another repo or model outside this checkout.
- Use `python3 dev/scripts/devctl.py governance-review --format md` to inspect
  the current adjudicated finding ledger, and `--record` to append one reviewed
  guard/probe outcome before the summary is regenerated.
- `devctl` command telemetry is auto-emitted to
  `dev/reports/audits/devctl_events.jsonl`; do not hand-edit that ledger.
  The operator rule is:
  - use `devctl` commands for work that should land in command telemetry,
  - use `governance-review --record` for adjudicated finding outcomes,
  - use active-plan markdown for prose session continuity and handoff state.
- Use `python3 dev/scripts/devctl.py governance-bootstrap --target-repo <path> --format md`
  before first-run pilots against copied repos or submodule snapshots that may
  carry broken `.git` indirection.
- `check`, `probe-report`, and `governance-export` accept `--adoption-scan`
  for full current-worktree onboarding scans when a repo has no trustworthy
  baseline yet.
- `check`, `probe-report`, `status --probe-report`, `report --probe-report`,
  `triage --probe-report`, and `render-surfaces` accept
  `--quality-policy <path>`, and
  `DEVCTL_QUALITY_POLICY` provides the same override through the environment.
- When a repo-local policy path becomes a repeated operator workflow, add a
  short wrapper command instead of forcing maintainers to keep using the raw
  policy-path form. Current examples: `launcher-check`,
  `launcher-probes`, and `launcher-policy`.
- To reuse this system in another repo, prefer swapping the repo-policy file
  over editing `check` or `probe-report` orchestration code.

## Cross-architecture quality enforcement (required)

All quality guard tooling MUST align across the three codebase architectures.
The same enforcement patterns apply everywhere — no architecture gets a pass.
Tandem-consistency checks (`check_tandem_consistency.py`) prefer typed
`review_state.json` authority when available; bridge-text fallback is used
only for checks without a typed equivalent (`reviewed_hash_honesty`,
`plan_alignment`, `launch_truth`).

| Architecture | Language | Guard entry point | CI workflow |
|---|---|---|---|
| **voiceterm binary** | Rust | `devctl check --profile ci` (clippy, code-shape, serde, panic-policy, security-footguns) | `rust_ci.yml` |
| **operator console** | Python/PyQt6 | `devctl check --profile ci` (facade-wrappers, god-class, nesting-depth, global-mutable, dict-schema, structural-similarity) | `tooling_control_plane.yml` |
| **devctl tooling** | Python | `devctl check --profile ci` (all Python guards) | `tooling_control_plane.yml` |
| **iOS mobile app** | Swift | `devctl mobile-status` + Xcode build verification | `tooling_control_plane.yml` |

### Ralph loop: AI-driven remediation across all architectures

The Ralph loop (`coderabbit_ralph_loop.yml`) is the closed-loop remediation
pipeline. When CodeRabbit flags issues, AI evaluates each finding, filters
false positives, and fixes real issues — then re-runs CodeRabbit to verify.

**Loop flow:**
1. CodeRabbit reviews code → produces `backlog-medium.json` (medium/high findings)
2. Ralph loop reads backlog → invokes `ralph_ai_fix.py` (the AI fix wrapper)
3. AI fix wrapper feeds findings to Claude Code → AI evaluates + fixes valid issues
4. AI fix wrapper runs architecture-specific validation (Rust tests, Python tests, etc.)
5. AI fix wrapper commits + pushes → CodeRabbit re-reviews the new SHA
6. Ralph loop checks new backlog → repeats until clean or max attempts reached
7. If unresolved after max attempts → escalation comment requests human review

**AI fix wrapper** (`dev/scripts/coderabbit/ralph_ai_fix.py`):
- Reads `RALPH_BACKLOG_DIR/backlog-medium.json`
- Reads canonical probe guidance from `dev/reports/probes/review_targets.json`
  when probe artifacts are available; `review_packet.json` remains a separate
  artifact for other consumers, not a second Ralph guidance authority
- Maps finding categories to architectures (Rust, PyQt6, devctl, iOS)
- Invokes Claude Code with structured prompt including false-positive filtering
- Runs architecture-specific checks before committing
- Prefer structured backlog `path` / `line` fields for matching probe
  guidance to CodeRabbit items; summary-string parsing is compatibility-only
  for older backlog payloads
- Policy-gated via `control_plane_policy.json` allowlist

**Cross-architecture guard alignment rules:**
1. Every new guard script MUST be registered in `dev/scripts/devctl/quality_policy.py` and enabled in `dev/config/devctl_repo_policy.json` when this repo should run it by default.
2. Every repo-enabled AI guard MUST have a step in `tooling_control_plane.yml`.
3. Guard output format MUST support `--since-ref`/`--head-ref` for growth-based gating.
4. The Ralph AI fix wrapper MUST run architecture-specific validation after fixes.
5. No architecture may bypass the Ralph loop — all CodeRabbit findings across Rust,
   Python, and iOS are processed through the same pipeline.

**Configuration:**
- Policy file: `dev/config/control_plane_policy.json`
- Fix command allowlist: `triage_loop.allowed_fix_command_prefixes`
- Autonomy gate: `AUTONOMY_MODE=operate` required for fix execution
- Branch gate: only `develop` branch is allowlisted for automated fixes

## Branch policy (required)

- `develop`: integration branch for normal feature/fix/docs work.
- `master`: release/tag branch and rare hotfix branch.

Non-release work flow:

1. `git fetch origin`
2. `git checkout develop`
3. `git pull --ff-only origin develop`
4. `git checkout -b feature/<topic>` or `git checkout -b fix/<topic>`
5. Implement and run required checks.
6. Require user local validation before push:
   - Ask the user to test locally and confirm go-ahead before any non-release
     `git push`.
   - If the user asks to test before commit, keep changes uncommitted until
     that local validation completes.
7. Commit and push short-lived branch only after explicit user approval.
8. Merge short-lived branch into `develop` only after required checks pass.

Routine helper:

- `python3 dev/scripts/devctl.py push` runs the canonical non-mutating
  branch-push validation path from repo policy (`repo_governance.push`).
- `python3 dev/scripts/devctl.py push --execute` runs the same preflight,
  performs the current short-lived branch push, and then executes the
  configured post-push bundle.
- `python3 dev/scripts/devctl.py sync --push` can audit/sync `develop` +
  `master` + current branch with clean-tree and fast-forward guards.

Release promotion flow:

1. Ensure `develop` checks are green.
2. Merge `develop` into `master`.
3. Tag from `master`.

If a hotfix lands on `master`, back-merge `master` to `develop` promptly.

## Dirty-tree protocol (required)

When `git status --short` is not clean:

1. Do not discard unrelated edits.
2. Edit only files needed for the current task.
3. Use commit-range checks carefully (`--since-ref`) only when the range is
   valid for current branch/repo state.
4. Note unrelated pre-existing changes in handoff when they affect confidence.

## Active-plan onboarding (adding files under `dev/active/`)

When adding any new markdown file under `dev/active/`, this sequence is required:

1. Add an entry in `dev/active/INDEX.md` with:
   - path
   - role (`tracker` | `spec` | `runbook` | `reference`)
   - execution authority
   - MP scope
   - when agents should read it
2. If the file carries execution state, reflect that scope in
   `dev/active/MASTER_PLAN.md` (the only tracker authority).
2.1 If the file is an execution plan, include marker
    `Execution plan contract: required`, one parseable metadata header, and
    sections `Scope`, `Execution Checklist`, `Progress Log`,
    `Session Resume`, and `Audit Evidence`. Follow
    `dev/active/PLAN_FORMAT.md`.
3. Update discovery links in `AGENTS.md` and `dev/README.md`
   if navigation/ownership changed.
3.1 For new active-plan/check-script/devctl-command/app/workflow surfaces, run
    `python3 dev/scripts/checks/check_architecture_surface_sync.py` before
    closing the slice.
4. Run `python3 dev/scripts/checks/check_active_plan_sync.py`.
5. Run `python3 dev/scripts/checks/check_multi_agent_sync.py`.
6. Run `python3 dev/scripts/devctl.py docs-check --strict-tooling`.
7. Run `python3 dev/scripts/devctl.py hygiene`.
8. Commit file + index + governance docs in one change.

## Task router (pick one class)

| User story | Task class | Required bundle |
|---|---|---|
| Changed runtime behavior under `rust/src/**` | Runtime feature/fix | `bundle.runtime` |
| Changed HUD/layout/controls/flags/UI text | HUD/overlay/controls/flags | `bundle.runtime` |
| Touched perf/latency/wake/threading/unsafe/parser boundaries | Risk-sensitive runtime | `bundle.runtime` |
| Changed only user-facing docs | Docs-only | `bundle.docs` |
| Changed tooling/process/CI/governance surfaces | Tooling/process/CI | `bundle.tooling` |
| Preparing/publishing release | Release/tag/distribution | `bundle.release` |

## Context packs (load only what class needs)

### Runtime pack

- `rust/src/bin/voiceterm/main.rs`
- `rust/src/bin/voiceterm/event_loop.rs`
- `rust/src/bin/voiceterm/event_state.rs`
- `rust/src/bin/voiceterm/status_line/`
- `rust/src/bin/voiceterm/hud/`
- `dev/guides/ARCHITECTURE.md`
- `guides/USAGE.md`
- `guides/CLI_FLAGS.md`

### Voice pack

- `rust/src/bin/voiceterm/voice_control/`
- `rust/src/audio/`
- `rust/src/stt.rs`
- `rust/src/bin/voiceterm/wake_word.rs`

### PTY/lifecycle pack

- `rust/src/pty_session/`
- `rust/src/ipc/`
- `rust/src/terminal_restore.rs`

### Tooling/process pack

- `AGENTS.md`
- `dev/active/INDEX.md`
- `dev/active/review_channel.md`
- `dev/guides/DEVELOPMENT.md`
- `dev/guides/MCP_DEVCTL_ALIGNMENT.md`
- `dev/scripts/README.md`
- `dev/history/ENGINEERING_EVOLUTION.md`
- `.github/workflows/`
- `dev/scripts/devctl/commands/`

### Release pack

- `rust/Cargo.toml`
- `pypi/pyproject.toml`
- `app/macos/VoiceTerm.app/Contents/Info.plist`
- `dev/CHANGELOG.md`
- `dev/scripts/README.md`

## Command bundles (rendered reference)

Canonical command authority lives in `dev/scripts/devctl/bundle_registry.py`.
The bundle blocks below are rendered reference for human read-through and must
stay aligned with the registry.

### `bundle.bootstrap`

```bash
git status --short
git branch --show-current
git remote -v
git log --oneline --decorate -n 10
sed -n '1,220p' dev/active/INDEX.md
python3 dev/scripts/devctl.py list
find . -maxdepth 1 -type f -name '--*'
```

### `bundle.runtime`

```bash
python3 dev/scripts/devctl.py check --profile ci
python3 dev/scripts/devctl.py process-cleanup --verify --format md
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/checks/check_active_plan_sync.py
python3 dev/scripts/checks/check_multi_agent_sync.py
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/checks/check_code_shape.py
python3 dev/scripts/checks/check_package_layout.py
python3 dev/scripts/checks/check_python_subprocess_policy.py
python3 dev/scripts/checks/check_workflow_shell_hygiene.py
python3 dev/scripts/checks/check_workflow_action_pinning.py
python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations
python3 dev/scripts/checks/check_compat_matrix.py
python3 dev/scripts/checks/compat_matrix_smoke.py
python3 dev/scripts/checks/check_naming_consistency.py
python3 dev/scripts/checks/check_rust_test_shape.py
python3 dev/scripts/checks/check_rust_lint_debt.py
python3 dev/scripts/checks/check_rust_best_practices.py
python3 dev/scripts/checks/check_rust_compiler_warnings.py
python3 dev/scripts/checks/check_serde_compatibility.py
python3 dev/scripts/checks/check_rust_runtime_panic_policy.py
python3 dev/scripts/checks/check_facade_wrappers.py
python3 dev/scripts/checks/check_god_class.py
python3 dev/scripts/checks/check_mobile_relay_protocol.py
python3 dev/scripts/checks/check_daemon_state_parity.py
python3 dev/scripts/checks/check_nesting_depth.py
python3 dev/scripts/checks/check_parameter_count.py
python3 dev/scripts/checks/check_python_dict_schema.py
python3 dev/scripts/checks/check_python_global_mutable.py
python3 dev/scripts/checks/check_python_design_complexity.py
python3 dev/scripts/checks/check_python_cyclic_imports.py
python3 dev/scripts/checks/check_python_suppression_debt.py
python3 dev/scripts/checks/check_structural_similarity.py
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md
find . -maxdepth 1 -type f -name '--*'
```

### `bundle.docs`

```bash
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/checks/check_active_plan_sync.py
python3 dev/scripts/checks/check_multi_agent_sync.py
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/checks/check_code_shape.py
python3 dev/scripts/checks/check_package_layout.py
python3 dev/scripts/checks/check_python_subprocess_policy.py
python3 dev/scripts/checks/check_workflow_shell_hygiene.py
python3 dev/scripts/checks/check_workflow_action_pinning.py
python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations
python3 dev/scripts/checks/check_compat_matrix.py
python3 dev/scripts/checks/compat_matrix_smoke.py
python3 dev/scripts/checks/check_naming_consistency.py
python3 dev/scripts/checks/check_rust_test_shape.py
python3 dev/scripts/checks/check_rust_lint_debt.py
python3 dev/scripts/checks/check_rust_best_practices.py
python3 dev/scripts/checks/check_rust_compiler_warnings.py
python3 dev/scripts/checks/check_serde_compatibility.py
python3 dev/scripts/checks/check_rust_runtime_panic_policy.py
python3 dev/scripts/checks/check_facade_wrappers.py
python3 dev/scripts/checks/check_god_class.py
python3 dev/scripts/checks/check_mobile_relay_protocol.py
python3 dev/scripts/checks/check_daemon_state_parity.py
python3 dev/scripts/checks/check_nesting_depth.py
python3 dev/scripts/checks/check_parameter_count.py
python3 dev/scripts/checks/check_python_dict_schema.py
python3 dev/scripts/checks/check_python_global_mutable.py
python3 dev/scripts/checks/check_python_design_complexity.py
python3 dev/scripts/checks/check_python_cyclic_imports.py
python3 dev/scripts/checks/check_python_suppression_debt.py
python3 dev/scripts/checks/check_structural_similarity.py
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md
find . -maxdepth 1 -type f -name '--*'
```

### `bundle.tooling`

```bash
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/devctl.py hygiene --strict-warnings
python3 dev/scripts/devctl.py orchestrate-status --format md
python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 120 --format md
python3 dev/scripts/checks/check_agents_contract.py
python3 dev/scripts/checks/check_release_version_parity.py
python3 dev/scripts/checks/check_repo_url_parity.py
python3 dev/scripts/checks/check_guard_enforcement_inventory.py
python3 dev/scripts/checks/check_architecture_surface_sync.py
python3 dev/scripts/checks/check_guide_contract_sync.py
python3 dev/scripts/checks/check_instruction_surface_sync.py
python3 dev/scripts/checks/check_bundle_registry_dry.py
python3 dev/scripts/checks/check_bundle_workflow_parity.py
python3 dev/scripts/checks/check_platform_layer_boundaries.py
python3 dev/scripts/checks/check_platform_contract_closure.py
python3 dev/scripts/checks/check_platform_contract_sync.py
python3 dev/scripts/checks/check_review_channel_bridge.py
python3 dev/scripts/checks/check_startup_authority_contract.py
python3 dev/scripts/checks/check_tandem_consistency.py
python3 dev/scripts/checks/check_governance_closure.py
python3 dev/scripts/checks/check_active_plan_sync.py
python3 dev/scripts/checks/check_multi_agent_sync.py
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/checks/check_code_shape.py
python3 dev/scripts/checks/check_package_layout.py
python3 dev/scripts/checks/check_python_subprocess_policy.py
python3 dev/scripts/checks/check_workflow_shell_hygiene.py
python3 dev/scripts/checks/check_workflow_action_pinning.py
python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations
python3 dev/scripts/checks/check_compat_matrix.py
python3 dev/scripts/checks/compat_matrix_smoke.py
python3 dev/scripts/checks/check_naming_consistency.py
python3 dev/scripts/checks/check_rust_test_shape.py
python3 dev/scripts/checks/check_rust_lint_debt.py
python3 dev/scripts/checks/check_rust_best_practices.py
python3 dev/scripts/checks/check_rust_compiler_warnings.py
python3 dev/scripts/checks/check_serde_compatibility.py
python3 dev/scripts/checks/check_rust_runtime_panic_policy.py
python3 dev/scripts/checks/check_facade_wrappers.py
python3 dev/scripts/checks/check_god_class.py
python3 dev/scripts/checks/check_mobile_relay_protocol.py
python3 dev/scripts/checks/check_daemon_state_parity.py
python3 dev/scripts/checks/check_nesting_depth.py
python3 dev/scripts/checks/check_parameter_count.py
python3 dev/scripts/checks/check_python_dict_schema.py
python3 dev/scripts/checks/check_python_global_mutable.py
python3 dev/scripts/checks/check_python_design_complexity.py
python3 dev/scripts/checks/check_python_cyclic_imports.py
python3 dev/scripts/checks/check_python_suppression_debt.py
python3 dev/scripts/checks/check_structural_similarity.py
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md
find . -maxdepth 1 -type f -name '--*'
python3 -m pytest app/operator_console/tests/ -q --tb=short
python3 dev/scripts/devctl.py process-cleanup --verify --format md
```

### `bundle.release`

```bash
python3 dev/scripts/devctl.py check --profile release
python3 dev/scripts/devctl.py docs-check --user-facing --strict
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/devctl.py hygiene --strict-warnings
python3 dev/scripts/devctl.py orchestrate-status --format md
python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 120 --format md
python3 dev/scripts/checks/check_agents_contract.py
python3 dev/scripts/checks/check_release_version_parity.py
python3 dev/scripts/checks/check_repo_url_parity.py
python3 dev/scripts/checks/check_guard_enforcement_inventory.py
python3 dev/scripts/checks/check_architecture_surface_sync.py
python3 dev/scripts/checks/check_guide_contract_sync.py
python3 dev/scripts/checks/check_instruction_surface_sync.py
python3 dev/scripts/checks/check_bundle_registry_dry.py
python3 dev/scripts/checks/check_bundle_workflow_parity.py
python3 dev/scripts/checks/check_platform_layer_boundaries.py
python3 dev/scripts/checks/check_platform_contract_closure.py
python3 dev/scripts/checks/check_platform_contract_sync.py
python3 dev/scripts/checks/check_review_channel_bridge.py
python3 dev/scripts/checks/check_startup_authority_contract.py
python3 dev/scripts/checks/check_tandem_consistency.py
python3 dev/scripts/checks/check_governance_closure.py
python3 dev/scripts/checks/check_publication_sync.py
CI=1 python3 dev/scripts/checks/check_coderabbit_gate.py --branch master
CI=1 python3 dev/scripts/checks/check_coderabbit_ralph_gate.py --branch master
python3 dev/scripts/checks/check_active_plan_sync.py
python3 dev/scripts/checks/check_multi_agent_sync.py
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/checks/check_code_shape.py
python3 dev/scripts/checks/check_package_layout.py
python3 dev/scripts/checks/check_python_subprocess_policy.py
python3 dev/scripts/checks/check_workflow_shell_hygiene.py
python3 dev/scripts/checks/check_workflow_action_pinning.py
python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations
python3 dev/scripts/checks/check_compat_matrix.py
python3 dev/scripts/checks/compat_matrix_smoke.py
python3 dev/scripts/checks/check_naming_consistency.py
python3 dev/scripts/checks/check_rust_test_shape.py
python3 dev/scripts/checks/check_rust_lint_debt.py
python3 dev/scripts/checks/check_rust_best_practices.py
python3 dev/scripts/checks/check_rust_compiler_warnings.py
python3 dev/scripts/checks/check_serde_compatibility.py
python3 dev/scripts/checks/check_rust_runtime_panic_policy.py
python3 dev/scripts/checks/check_facade_wrappers.py
python3 dev/scripts/checks/check_god_class.py
python3 dev/scripts/checks/check_mobile_relay_protocol.py
python3 dev/scripts/checks/check_daemon_state_parity.py
python3 dev/scripts/checks/check_nesting_depth.py
python3 dev/scripts/checks/check_parameter_count.py
python3 dev/scripts/checks/check_python_dict_schema.py
python3 dev/scripts/checks/check_python_global_mutable.py
python3 dev/scripts/checks/check_python_design_complexity.py
python3 dev/scripts/checks/check_python_cyclic_imports.py
python3 dev/scripts/checks/check_python_suppression_debt.py
python3 dev/scripts/checks/check_structural_similarity.py
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md
find . -maxdepth 1 -type f -name '--*'
python3 dev/scripts/devctl.py process-cleanup --verify --format md
```

### `bundle.post-push`

```bash
git status
git log --oneline --decorate -n 10
python3 dev/scripts/devctl.py status --ci --require-ci --format md
python3 dev/scripts/devctl.py orchestrate-status --format md
python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 120 --format md
python3 dev/scripts/devctl.py docs-check --user-facing --since-ref origin/develop
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/checks/check_active_plan_sync.py
python3 dev/scripts/checks/check_review_channel_bridge.py
python3 dev/scripts/checks/check_multi_agent_sync.py
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/checks/check_code_shape.py --since-ref origin/develop
python3 dev/scripts/checks/check_package_layout.py --since-ref origin/develop
python3 dev/scripts/checks/check_python_subprocess_policy.py --since-ref origin/develop
python3 dev/scripts/checks/check_workflow_shell_hygiene.py
python3 dev/scripts/checks/check_workflow_action_pinning.py
python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations
python3 dev/scripts/checks/check_compat_matrix.py
python3 dev/scripts/checks/compat_matrix_smoke.py
python3 dev/scripts/checks/check_naming_consistency.py
python3 dev/scripts/checks/check_rust_test_shape.py --since-ref origin/develop
python3 dev/scripts/checks/check_rust_lint_debt.py --since-ref origin/develop
python3 dev/scripts/checks/check_rust_best_practices.py --since-ref origin/develop
python3 dev/scripts/checks/check_rust_compiler_warnings.py --since-ref origin/develop
python3 dev/scripts/checks/check_serde_compatibility.py --since-ref origin/develop
python3 dev/scripts/checks/check_rust_runtime_panic_policy.py --since-ref origin/develop
python3 dev/scripts/checks/check_facade_wrappers.py --since-ref origin/develop
python3 dev/scripts/checks/check_god_class.py --since-ref origin/develop
python3 dev/scripts/checks/check_mobile_relay_protocol.py --since-ref origin/develop
python3 dev/scripts/checks/check_daemon_state_parity.py
python3 dev/scripts/checks/check_nesting_depth.py --since-ref origin/develop
python3 dev/scripts/checks/check_parameter_count.py --since-ref origin/develop
python3 dev/scripts/checks/check_python_dict_schema.py --since-ref origin/develop
python3 dev/scripts/checks/check_python_global_mutable.py --since-ref origin/develop
python3 dev/scripts/checks/check_python_design_complexity.py --since-ref origin/develop
python3 dev/scripts/checks/check_python_cyclic_imports.py --since-ref origin/develop
python3 dev/scripts/checks/check_python_suppression_debt.py --since-ref origin/develop
python3 dev/scripts/checks/check_structural_similarity.py --since-ref origin/develop
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md
find . -maxdepth 1 -type f -name '--*'
python3 dev/scripts/devctl.py process-cleanup --verify --format md
```

## Runtime risk matrix (required add-ons)

- Overlay/input/status/HUD changes:
  - `python3 dev/scripts/devctl.py check --profile ci`
  - `cd rust && cargo test --bin voiceterm`
  - preferred AI/raw-test path: `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test --bin voiceterm`
  - required post-run follow-up (if `cargo test` was run directly): `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel` (includes host-side `process-cleanup --verify` by default)
- Performance/latency-sensitive changes:
  - `python3 dev/scripts/devctl.py check --profile prepush`
  - `./dev/scripts/tests/measure_latency.sh --voice-only --synthetic`
  - `./dev/scripts/tests/measure_latency.sh --ci-guard`
  - `dev/scripts/tests/measure_latency.sh` auto-detects `rust/` workspace paths and falls back to legacy `src/` layouts
  - `dev/scripts/tests/measure_latency.sh` now uses `set -u`-safe empty-array
    expansion so voice-only/CI synthetic modes do not raise `unbound variable`
    errors when optional arg arrays are empty
  - when host process access is available: `python3 dev/scripts/devctl.py process-cleanup --verify --format md`
- Wake-word runtime/detection changes:
  - `bash dev/scripts/tests/wake_word_guard.sh`
  - `python3 dev/scripts/devctl.py check --profile release`
  - when host process access is available: `python3 dev/scripts/devctl.py process-cleanup --verify --format md`
- Threading/lifecycle/memory changes:
  - `cd rust && cargo test --no-default-features legacy_tui::tests::memory_guard_backend_threads_drop -- --nocapture`
  - preferred AI/raw-test path: `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test --no-default-features legacy_tui::tests::memory_guard_backend_threads_drop -- --nocapture`
  - required post-run follow-up (if `cargo test` was run directly): `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel` (includes host-side `process-cleanup --verify` by default)
- Unsafe/FFI lifecycle changes:
  - Update `dev/security/unsafe_governance.md`
  - `cd rust && cargo test pty_session::tests::pty_cli_session_drop_terminates_descendants_in_process_group -- --nocapture`
  - `cd rust && cargo test pty_session::tests::pty_overlay_session_drop_terminates_descendants_in_process_group -- --nocapture`
  - `cd rust && cargo test stt::tests::transcriber_restores_stderr_after_failed_model_load -- --nocapture`
  - preferred AI/raw-test path: `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test pty_session::tests::pty_overlay_session_drop_terminates_descendants_in_process_group -- --nocapture`
  - required post-run follow-up (if `cargo test` was run directly): `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel` (includes host-side `process-cleanup --verify` by default)
- Parser/ANSI boundary hardening changes:
  - `cd rust && cargo test pty_session::tests::prop_find_csi_sequence_respects_bounds -- --nocapture`
  - `cd rust && cargo test pty_session::tests::prop_find_osc_terminator_respects_bounds -- --nocapture`
  - `cd rust && cargo test pty_session::tests::prop_split_incomplete_escape_preserves_original_bytes -- --nocapture`
  - preferred AI/raw-test path: `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test pty_session::tests::prop_find_csi_sequence_respects_bounds -- --nocapture`
  - required post-run follow-up (if `cargo test` was run directly): `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel` (includes host-side `process-cleanup --verify` by default)
- Mutation-hardening work:
  - `python3 dev/scripts/devctl.py mutation-score --threshold 0.80 --max-age-hours 72`
  - optional: `python3 dev/scripts/devctl.py mutants --module overlay`
- Macro/wizard onboarding changes:
  - `./scripts/macros.sh list`
  - `./scripts/macros.sh install --pack safe-core --project-dir . --overwrite`
  - `./scripts/macros.sh validate --output ./.voiceterm/macros.yaml --project-dir .`
  - Validate `gh auth status -h github.com` behavior when GH macros are included
- Dependency/security-hardening changes:
  - `python3 dev/scripts/devctl.py security`
  - optional strict workflow scan: `python3 dev/scripts/devctl.py security --with-zizmor --require-optional-tools`
  - fallback manual path:
    `cargo install cargo-audit --locked`,
    `cd rust && (cargo audit --json > ../rustsec-audit.json || true)`,
    `python3 dev/scripts/checks/check_rustsec_policy.py --input rustsec-audit.json --min-cvss 7.0 --fail-on-kind yanked --fail-on-kind unsound --allowlist-file dev/security/rustsec_allowlist.md`

## Release SOP (master only)

Use this exact sequence:

1. Confirm `git checkout master` and clean working tree.
2. Verify version parity:
   - `python3 dev/scripts/checks/check_release_version_parity.py`
   - `rust/Cargo.toml` has `version = X.Y.Z`
   - `pypi/pyproject.toml` has `[project].version = X.Y.Z`
   - `app/macos/VoiceTerm.app/Contents/Info.plist` has
     `CFBundleShortVersionString = X.Y.Z` and `CFBundleVersion = X.Y.Z`
   - `dev/CHANGELOG.md` has release heading for `X.Y.Z`
   - `dev/active/MASTER_PLAN.md` Status Snapshot has
     `Last tagged release: vX.Y.Z` and `Current release target: post-vX.Y.Z planning`
3. Verify release prerequisites:
   - `gh auth status -h github.com`
   - `CI=1 python3 dev/scripts/devctl.py release-gates --branch master --sha "$(git rev-parse HEAD)" --skip-preflight --wait-seconds 1800 --poll-seconds 20 --format md`
   - GitHub Actions secret `PYPI_API_TOKEN` exists for `.github/workflows/publish_pypi.yml`
   - GitHub Actions secret `HOMEBREW_TAP_TOKEN` exists for `.github/workflows/publish_homebrew.yml`
   - Optional local fallback: Homebrew tap path is resolvable (`HOMEBREW_VOICETERM_PATH` or `brew --repo`)
4. Run `bundle.release`.
5. Run and wait for same-SHA `release_preflight.yml` success:

   ```bash
   gh workflow run release_preflight.yml -f version=<version>
   gh run list --workflow release_preflight.yml --limit 1
   # gh run watch <run-id>
   ```

   - `release_preflight.yml` must provide `GH_TOKEN` to steps that invoke
     `gh` inside `devctl check --profile release`; workflow uses
     `${{ github.token }}` for this wiring.
   - `release_preflight.yml` job must grant `security-events: write` so the
     zizmor SARIF upload step can publish scan results without permission
     failures.
   - `release_preflight.yml` uses `online-audits: false` for zizmor so
     cross-repo compare API restrictions do not hard-fail preflight in CI.
   - `release_preflight.yml` release security step must use
     `--python-scope changed` with the same resolved `--since-ref/--head-ref`
     range as AI-guard checks; do not run full-repo Python format/import scans
     in this lane.
   - `release_preflight.yml` release security step should not hard-block on
     repository-wide open CodeQL backlog (`--with-codeql-alerts`); keep CodeQL
     alert enforcement in dedicated security lanes and triage workflows.
   - In `release_preflight.yml`, `cargo deny` remains the blocking security
     gate; `devctl security` report output is retained as advisory evidence.

6. Run release tagging and notes:

   ```bash
   # Optional one-step metadata prep (Cargo/PyPI/app plist/changelog):
   python3 dev/scripts/devctl.py ship --version <version> --prepare-release
   python3 dev/scripts/devctl.py release --version <version>
   gh release create v<version> --title "v<version>" --notes-file /tmp/voiceterm-release-v<version>.md
   # PyPI publish runs automatically via .github/workflows/publish_pypi.yml.
   gh run list --workflow publish_pypi.yml --limit 1
   # Homebrew publish runs automatically via .github/workflows/publish_homebrew.yml.
   gh run list --workflow publish_homebrew.yml --limit 1
   # Native release binaries publish via .github/workflows/publish_release_binaries.yml.
   gh run list --workflow publish_release_binaries.yml --limit 1
   # Release source provenance attestations run via .github/workflows/release_attestation.yml.
   gh run list --workflow release_attestation.yml --limit 1
   # gh run watch <run-id>
   curl -fsSL https://pypi.org/pypi/voiceterm/<version>/json
   # Local fallback (if workflow is unavailable):
   python3 dev/scripts/devctl.py homebrew --version <version>
   ```

7. Run `bundle.post-push`.

Unified control plane alternatives:

```bash
# Workflow-first release convenience (only after same-SHA preflight success)
gh workflow run release_preflight.yml -f version=<version>
gh run list --workflow release_preflight.yml --limit 1
# gh run watch <run-id>
python3 dev/scripts/devctl.py ship --version <version> --verify --tag --notes --github --yes
# Workflow-first release path with auto metadata prep
python3 dev/scripts/devctl.py ship --version <version> --prepare-release --verify --tag --notes --github --yes
gh run list --workflow publish_pypi.yml --limit 1
gh run list --workflow publish_homebrew.yml --limit 1
gh run list --workflow publish_release_binaries.yml --limit 1
gh run list --workflow release_attestation.yml --limit 1

# Manual fallback (run PyPI/Homebrew locally)
python3 dev/scripts/devctl.py ship --version <version> --pypi --verify-pypi --homebrew --yes
```

## CI workflow dependency graph

Release pipeline flow (trigger order):

```
push to master
  └─> release_preflight.yml ─── (must pass before tagging)
        └─> gh release create vX.Y.Z
              ├─> publish_pypi.yml        (on: release published)
              ├─> publish_homebrew.yml     (on: release published)
              ├─> publish_release_binaries.yml (on: release published)
              └─> release_attestation.yml (on: release published)
```

Development pipeline flow (parallel on push/PR):

```
push to develop / PR
  ├─> rust_ci.yml            (compile + test + clippy + AI guards)
  ├─> voice_mode_guard.yml   (send/transcript delivery)
  ├─> wake_word_guard.yml    (detection accuracy)
  ├─> perf_smoke.yml         (latency bounds)
  ├─> memory_guard.yml       (thread lifecycle)
  ├─> security_guard.yml     (cargo-deny + advisories)
  ├─> workflow_lint.yml      (actionlint syntax)
  ├─> coverage.yml           (Codecov upload)
  ├─> docs_lint.yml          (markdownlint)
  ├─> tooling_control_plane.yml (shape + governance)
  └─> dependency_review.yml  (PR-only, manifest diff)
```

Scheduled / on-demand:

```
schedule / workflow_dispatch
  ├─> mutation-testing.yml       (cargo-mutants)
  ├─> scorecard.yml              (OpenSSF)
  ├─> coderabbit_triage.yml      (finding rollups)
  ├─> coderabbit_ralph_loop.yml  (bounded remediation)
  ├─> autonomy_controller.yml    (bounded loop)
  ├─> autonomy_run.yml           (plan-scoped swarm)
  ├─> mutation_ralph_loop.yml    (mutation remediation)
  ├─> failure_triage.yml         (non-success run triage)
  └─> orchestrator_watchdog.yml  (stale lane alerts)
```

## CI lane mapping (what must be green)

| Change signal | Lanes to verify |
|---|---|
| `rust/src/**` runtime changes | `rust_ci.yml` (Ubuntu main lane + MSRV `1.88.0` check + feature-mode matrix + macOS runtime smoke lane + high-signal Clippy lint-baseline gate) |
| Send mode/macros/transcript delivery | `voice_mode_guard.yml` |
| Wake-word runtime/detection | `wake_word_guard.yml` |
| Perf-sensitive paths | `perf_smoke.yml`, `latency_guard.yml` |
| Long-running worker/thread lifecycle | `memory_guard.yml` |
| Parser/ANSI/OSC boundary logic | `parser_fuzz_guard.yml` |
| Dependency/security policy changes | `security_guard.yml` |
| Dependency manifest/lockfile deltas in PRs | `dependency_review.yml` |
| Workflow syntax + policy drift | `workflow_lint.yml` |
| AI PR review signal ingestion and owner/severity rollups | `coderabbit_triage.yml` |
| Bounded AI remediation loop for CodeRabbit medium/high backlog | `coderabbit_ralph_loop.yml` |
| Bounded autonomous controller loop (checkpoint packets + queue artifacts + optional promote PR) | `autonomy_controller.yml` |
| Guarded plan-scoped autonomy swarm pipeline (scope load + swarm + reviewer + governance + plan evidence append) | `autonomy_run.yml` |
| Bounded mutation remediation loop (report-only default, optional policy-gated fix mode) | `mutation_ralph_loop.yml` |
| Release commit guard for unresolved CodeRabbit medium/high findings | `coderabbit_triage.yml`, `coderabbit_ralph_loop.yml`, `release_preflight.yml`, `publish_pypi.yml`, `publish_homebrew.yml`, `publish_release_binaries.yml`, `release_attestation.yml` |
| Supply-chain posture drift | `scorecard.yml` |
| Coverage reporting / Codecov badge freshness | `coverage.yml` (runs on every push to `develop`/`master` so branch-head badges do not go `unknown` after non-runtime commits) |
| Rust/Python source-file shape drift (God-file growth) | `tooling_control_plane.yml` |
| Multi-agent instruction/ack timers and stale-lane accountability | `tooling_control_plane.yml`, `orchestrator_watchdog.yml` |
| User docs/markdown changes | `docs_lint.yml` |
| Release preflight verification bundle | `release_preflight.yml` |
| GitHub release publication / PyPI distribution | `publish_pypi.yml` |
| GitHub release publication / Homebrew distribution | `publish_homebrew.yml` |
| GitHub release publication / native binaries | `publish_release_binaries.yml` |
| Release source provenance attestation | `release_attestation.yml` |
| Any non-success CI workflow run in watched lanes | `failure_triage.yml` (workflow-run triage bundle + artifact upload for high-signal failures in watched lanes; trusted same-repo events only, branch allowlist defaults to `develop,master` and can be overridden with repo variable `FAILURE_TRIAGE_BRANCHES`) |
| Tooling/process/docs governance surfaces (`dev/scripts/**`, `scripts/macro-packs/**`, `.github/workflows/**`, `AGENTS.md`, `dev/guides/DEVELOPMENT.md`, `dev/scripts/README.md`, `Makefile`) | `tooling_control_plane.yml` |
| Mutation-hardening work | `mutation-testing.yml` (scheduled; threshold is advisory/report-only across branches) plus local mutation-score evidence |

Runner-label note:
- Keep `publish_release_binaries.yml` on actionlint-supported macOS labels (`macos-15-intel` for darwin/amd64, `macos-14` for darwin/arm64).

Workflow hardening note:
- Keep `.github/workflows/scorecard.yml` workflow-level permissions read-only; set `id-token: write` and `security-events: write` at the job level so OpenSSF result publishing passes workflow verification.
- Keep GitHub-owned actions pinned to valid 40-character commit SHAs (for example `actions/attest-build-provenance` and `github/codeql-action/upload-sarif`).

## Documentation governance

Always evaluate:

- `dev/CHANGELOG.md` (required for user-facing behavior changes)
- `dev/active/INDEX.md`
- `dev/active/MASTER_PLAN.md`
- `README.md`
- `QUICK_START.md`
- `guides/USAGE.md`
- `guides/CLI_FLAGS.md`
- `guides/INSTALL.md`
- `guides/TROUBLESHOOTING.md`
- `dev/guides/ARCHITECTURE.md`
- `dev/guides/DEVELOPMENT.md`
- `dev/scripts/README.md`
- `.github/workflows/README.md`
- `dev/audits/README.md`
- `dev/audits/AUTOMATION_DEBT_REGISTER.md`
- `dev/audits/METRICS_SCHEMA.md`
- `dev/integrations/EXTERNAL_REPOS.md`
- `dev/history/ENGINEERING_EVOLUTION.md` (required for tooling/process/CI shifts)

Plain-language rule for docs updates:

- For user/developer docs (`README.md`, `QUICK_START.md`, `guides/*`, `dev/*`), prefer plain language over policy-heavy wording.
- For workflow docs (`.github/workflows/README.md` + workflow header comments), explain purpose and trigger behavior in plain language.
- Use short, direct sentences and concrete commands.
- Keep technical accuracy, but avoid unnecessary jargon.

Update flow:

1. Link/adjust MP item in `dev/active/MASTER_PLAN.md`.
2. Update `dev/CHANGELOG.md` for user-facing behavior.
3. Update user docs for behavior/flag/UI changes.
4. Update developer docs for architecture/workflow/tooling changes.
5. Update screenshots/tables when UI output changes.
6. Add/update ADR when architecture decisions change.

Enforcement commands:

```bash
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py docs-check --user-facing --strict
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/checks/check_agents_contract.py
python3 dev/scripts/checks/check_agents_bundle_render.py
python3 dev/scripts/checks/check_active_plan_sync.py
python3 dev/scripts/checks/check_multi_agent_sync.py
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/checks/check_code_shape.py
python3 dev/scripts/checks/check_workflow_shell_hygiene.py
python3 dev/scripts/checks/check_workflow_action_pinning.py
python3 dev/scripts/checks/check_bundle_workflow_parity.py
python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations
python3 dev/scripts/checks/check_compat_matrix.py
python3 dev/scripts/checks/compat_matrix_smoke.py
python3 dev/scripts/checks/check_naming_consistency.py
python3 dev/scripts/checks/check_rust_test_shape.py
python3 dev/scripts/checks/check_rust_lint_debt.py
python3 dev/scripts/checks/check_rust_best_practices.py
python3 dev/scripts/checks/check_rust_compiler_warnings.py
python3 dev/scripts/checks/check_rust_runtime_panic_policy.py
```

## Tooling inventory

Canonical tool: `python3 dev/scripts/devctl.py ...`

Core commands:

- `check` (`ci`, `prepush`, `release`, `maintainer-lint`, `pedantic`, `quick`, `fast`, `ai-guard`)
  - Runs setup gates (`fmt`, `clippy`, AI guard scripts) and test/build phases in parallel batches by default.
  - Use `--parallel-workers <n>` to tune worker count, or `--no-parallel` to force sequential execution.
  - Includes automatic orphaned/stale repo-related process cleanup before/after checks (matched VoiceTerm PTY/test trees, repo-runtime cargo/target trees, repo-tooling wrappers, and descendant PTY/helper children such as leaked `cat` harnesses or stale repo-cwd helpers; detached `PPID=1` and stale active runners aged `>=600s` are cleanup targets).
  - Use `--no-process-sweep-cleanup` only when a run must preserve in-flight test processes.
  - `quick` / `fast` keep AI-guard scripts enabled by default (while still skipping test/build lanes) and also run host-side `process-cleanup --verify --format md`; use `--no-host-process-cleanup` only when a live process tree must be preserved and the exception is recorded.
  - `pedantic` is an advisory maintainer lane for intentional lint-hardening sweeps; it is opt-in and not part of required bundles or release gates.
  - `check --profile pedantic` writes structured artifacts to `dev/reports/check/clippy-pedantic-summary.json` and `dev/reports/check/clippy-pedantic-lints.json`; consume them through `report --pedantic` or `triage --pedantic` instead of making ad hoc decisions from raw terminal output.
  - Structured `check` output timestamps are UTC for stable cross-run correlation.
- `check-router` (path-aware lane selector that maps changed files to `bundle.docs|bundle.runtime|bundle.tooling|bundle.release`, reports required risk add-ons, and can execute the routed command set with `--execute`)
- `compat-matrix` (single-view host/provider compatibility matrix summary and policy validation surface)
  - Matrix checks now include a minimal no-dependency YAML fallback parser so
    tooling lanes remain deterministic when `PyYAML` is unavailable.
  - Malformed inline collection scalars in fallback mode now fail closed (no
    silent coercion), preserving guard reliability.
- `docs-check`
  - `--strict-tooling` also runs active-plan + multi-agent sync gates, markdown metadata-header checks, workflow-shell hygiene checks, bundle/workflow parity checks, plus stale-path audit so tooling/process changes cannot bypass active-doc/lane governance.
  - Check-script moves must be reflected in `dev/scripts/devctl/script_catalog.py` so strict-tooling path audits stay canonical.
- `hygiene` (archive/ADR/scripts governance plus orphaned/stale repo-related host-process sweep, including VoiceTerm PTY/test trees, repo-runtime cargo/target trees, repo-tooling wrappers, and repo-cwd background helpers such as `python3 -m unittest`, direct `bash dev/scripts/...` wrappers, or `qemu/node/make` descendants that outlive their repo-owned parent; report-retention drift warnings for stale managed `dev/reports/**` run artifacts, and tracked external-publication drift warnings when watched repo paths outpace synced papers/sites; optional `--fix` removes detected `dev/scripts/**/__pycache__` directories)
- `process-cleanup` (host-side cleanup for orphaned/stale repo-related process trees; expands cleanup roots to full descendant trees so leaked PTY children, repo-cwd background helpers, and orphaned tooling descendants are reaped with their parent wrappers when possible, skips recent active processes by default, and `--verify` reruns strict host audit after cleanup)
- `process-audit` (host-side Activity Monitor equivalent for repo-related runtime/tooling process trees; reports matched roots plus descendants, includes repo-cwd runtime/tooling helpers that would otherwise look generic in Activity Monitor, fails fast if `ps` is unavailable, and `--strict` turns leftover runtime/test trees or stale/orphaned repo-related helpers into a blocking failure before handoff)
- `process-watch` (bounded periodic host-process monitor that reruns the same audit logic on a cadence, optionally performs orphan/stale cleanup before each pass, and stops only when zero repo-related host processes remain if `--stop-on-clean` is set)
- `publication-sync` (tracked external publication report/record surface that compares watched repo paths against the last synced source commit for papers/sites and can record a new baseline after external publish)
- `push` (policy-driven guarded push surface for the current branch; validates repo-owned branch/remote rules plus configured preflight, defaults to non-mutating validation, and uses the configured post-push bundle after `--execute`)
- `path-audit` (stale-reference scan for legacy check-script paths; excludes `dev/archive/`)
- `path-rewrite` (auto-rewrite legacy check-script paths to canonical registry targets; use `--dry-run` first)
- `sync` (branch-sync automation with clean-tree, remote-ref, and `--ff-only` pull guards; optional `--push` for ahead branches)
- `integrations-sync` (policy-guarded sync/status for pinned federated sources under `integrations/`; supports remote update and audit logging)
- `integrations-import` (allowlisted selective importer from pinned federated sources into controlled destination roots with JSONL audit records)
- `cihub-setup` (allowlisted CIHub setup runner with preview/apply modes, capability probing, and strict unsupported-step gating)
- `security` (RustSec policy gate with optional workflow scan support via `--with-zizmor`, optional GitHub code-scanning alert gate via `--with-codeql-alerts`, and Python scope control via `--python-scope auto|changed|all`)
- `mutation-score` (reports outcomes source freshness; strict by default, or non-blocking reminders with `--report-only`; optional stale-data gate via `--max-age-hours`)
- `mutants`
- `release`
- `release-gates` (shared same-SHA release policy gate for CodeRabbit triage + release-preflight + Ralph checks; use `--skip-preflight` when running inside `release_preflight.yml`)
- `release-notes`
- `ship` (release-version reads now use TOML parsing for `[package]`/`[project]` with Python 3.10 fallback parsing)
- `pypi`
- `homebrew` (tap formula URL/version/checksum updates, canonical `desc` sync, and Cargo manifest-path migration sync to `libexec/rust/Cargo.toml` when legacy formulas still reference `libexec/src/Cargo.toml`)
- `status` (supports optional guarded Dev Mode log summaries via `--dev-logs`)
- `orchestrate-status` (single-view orchestrator summary for active-plan sync + multi-agent coordination guard state)
- `orchestrate-watch` (SLA watchdog for stale agent updates and overdue instruction ACKs)
- `report` (supports optional guarded Dev Mode log summaries via `--dev-logs`)
- `data-science` (builds one rolling telemetry snapshot from devctl audit events plus autonomy swarm/benchmark history, folds in governance-review false-positive/cleanup metrics, emits `summary.{md,json}` + SVG charts under `dev/reports/data_science/latest/`, and supports source/output overrides for experiments; devctl also auto-refreshes this snapshot after each command unless `DEVCTL_DATA_SCIENCE_DISABLE=1`)
- `governance-review` (records adjudicated guard/probe findings to
  `dev/reports/governance/finding_reviews.jsonl`, writes
  `dev/reports/governance/latest/review_summary.{md,json}`, and gives the repo
  a durable false-positive / cleanup-rate ledger; `--record` also accepts
  optional `guidance_id` / `guidance_followed` fields so probe-guidance
  adoption can be measured in the same ledger as verdict/fix outcomes)
- `triage` (human/AI triage output with optional CIHub artifact ingestion/bundle emission for owner/risk routing; report timestamps are UTC)
- `triage-loop` (bounded CodeRabbit medium/high loop with mode controls: `report-only`, `plan-then-fix`, `fix-only`; fix execution is policy-gated via `AUTONOMY_MODE`, branch allowlist, and command-prefix allowlist; emits md/json bundles plus a bounded structured backlog slice for downstream autonomy consumers, optional MASTER_PLAN proposal artifacts, and review-escalation comment upserts when attempts exhaust unresolved backlog)
- `loop-packet` (builds a guarded terminal feedback packet from triage/loop JSON sources for dev-mode draft injection with freshness/risk/auto-send-eligibility gates; `triage-loop` sources now also carry a bounded structured backlog slice so autonomy drafts can inject canonical `review_targets.json` probe guidance, mark when guidance adoption is required, and keep that contract in packet JSON instead of hidden prompt-only text)
- `autonomy-loop` (bounded controller loop that orchestrates triage-loop + loop-packet rounds, emits checkpoint packets/queue artifacts, writes phone-ready status snapshots under `dev/reports/autonomy/queue/phone/`, and enforces policy-driven stop reasons; non-dry-run write modes require `AUTONOMY_MODE=operate`)
- `autonomy-benchmark` (active-plan-scoped swarm matrix runner for tactic/swarm-size tradeoff analysis; executes `autonomy-swarm` batches across configurable count/tactic grids, emits per-swarm and per-scenario productivity metrics, and writes benchmark bundles under `dev/reports/autonomy/benchmarks/<label>/`; non-report modes require `--fix-command`)
- `swarm_run` (guarded plan-scoped autonomy pipeline that derives next unchecked plan steps, runs `autonomy-swarm` with reviewer + post-audit defaults, executes governance checks (`check_active_plan_sync`, `check_multi_agent_sync`, `docs-check --strict-tooling`, `orchestrate-status/watch`), and appends run evidence to plan-doc `Progress Log` + `Audit Evidence`; supports optional multi-cycle execution (`--continuous --continuous-max-cycles`) to keep processing plan checklist scope until failure/limit; non-report modes require `--fix-command`)
- `autonomy-report` (builds a human-readable autonomy digest bundle from loop/watch artifacts under `dev/reports/autonomy/library/<label>` with summary markdown/json, copied sources, and optional matplotlib charts)
- `phone-status` (renders iPhone/SSH-safe autonomy status projections from `dev/reports/autonomy/queue/phone/latest.json` with selectable views `full|compact|trace|actions` and optional projection bundle emission: `full.json`, `compact.json`, `trace.ndjson`, `actions.json`, `latest.md`)
- `controller-action` (policy-gated operator action surface for `refresh-status`, `dispatch-report-only`, `pause-loop`, and `resume-loop`; dispatch and mode writes are bounded by workflow/branch allowlists and autonomy mode gates, with optional dry-run and mode-state artifact output)
- `review-channel` (current bridge-gated review-swarm bootstrap surface; `--action launch` reads `dev/active/review_channel.md` + `bridge.md`, emits Codex/Claude conductor launch scripts, defaults live macOS launches to an `auto-dark` Terminal profile when available, and fails closed when the markdown bridge is inactive; `--action status`, `--action ensure`, `--action reviewer-heartbeat`, and `--action reviewer-checkpoint` now also emit machine-readable `reviewer_worker` state plus the typed `current_session` live-status block so current instruction / ACK reads no longer depend on append-only bridge prose, preserve shared-context `guidance_refs` when probe guidance is in scope, and keep those refs visible to downstream packet/prompt consumers, while `ensure --follow` frames carry `review_needed` without claiming semantic review completion; active reviewer checkpoints should prefer one typed `--checkpoint-payload-file` or the existing per-section `--*-file` flags for AI-generated markdown / shell-sensitive content instead of inline shell bodies, and `active_dual_agent` writes must carry the live `--expected-instruction-revision`; the repo-owned wait paths are `--action implementer-wait` for Claude-side bounded waiting and `--action reviewer-wait` for the symmetric Codex-side bounded wait over `reviewer_worker` hash truth plus projected `current_session` ACK/status state from `review_state.json`, not ad hoc shell sleep loops or invented top-level status payload blocks; `--action rollover` writes a repo-visible handoff bundle, relaunches fresh conductors before compaction, and can wait for visible ACK lines in `bridge.md`)
- `autonomy-swarm` (adaptive multi-agent orchestration wrapper with metadata-driven worker sizing, optional `--plan-only` allocation mode, bounded per-agent autonomy-loop fanout, default reserved `AGENT-REVIEW` lane for post-audit review when execution runs with more than one lane, per-run swarm summary bundles under `dev/reports/autonomy/swarms/<label>/`, and default post-audit digest bundles under `dev/reports/autonomy/library/<label>-digest/`; disable with `--no-post-audit` and/or `--no-reviewer-lane`; non-report modes require `--fix-command`)
- `mutation-loop` (bounded mutation remediation loop with mode controls: `report-only`, `plan-then-fix`, `fix-only`; emits md/json/playbook bundles and supports policy-gated fix execution)
- `failure-cleanup` (guarded cleanup for local failure triage bundles under `dev/reports/failures`; default path-root guard, optional `--allow-outside-failure-root` constrained to `dev/reports/**`, CI-green gating with optional `--ci-branch`/`--ci-workflow`/`--ci-event`/`--ci-sha` filters, plus `--dry-run` and confirmation)
- `reports-cleanup` (retention-based cleanup for stale run artifacts under managed `dev/reports/**` roots with protected-path exclusions, dry-run preview, and explicit confirmation/`--yes` delete flow)
- `audit-scaffold`
  - Builds/updates `dev/reports/audits/RUST_AUDIT_FINDINGS.md` from Rust/Python guard failures.
  - Auto-runs when AI-guard checks fail.
  - Run manually when you want a fresh findings file or a commit-range scoped view.
- `list`

### Quick command intent (plain language)

| Command | Run it when | Why |
|---|---|---|
| `python3 dev/scripts/devctl.py check --profile fast` | while iterating locally | fast local sanity lane (alias of `quick`) that keeps AI-guard scripts on; never a substitute for required pre-push bundles |
| `python3 dev/scripts/devctl.py check --profile pedantic` | you are intentionally doing a broader lint-hardening sweep, usually after a large refactor or as optional pre-release cleanup | runs advisory `clippy::pedantic`, writes structured artifacts under `dev/reports/check/`, and stays out of required merge/release flow |
| `python3 dev/scripts/devctl.py report --pedantic --pedantic-refresh --format json` | you want one command that refreshes the advisory sweep and emits a structured repo-owned summary | reruns pedantic artifact generation, then reads those artifacts plus `dev/config/clippy/pedantic_policy.json` for review/AI consumption |
| `python3 dev/scripts/devctl.py report --rust-audits --with-charts --emit-bundle --format md` | you want one readable Rust guard audit pack with charts, stats, and file hotspots | runs the Rust best-practices, lint-debt, and runtime-panic guards together, explains why the reported patterns are risky, and writes `.md` + `.json` bundle artifacts with optional matplotlib charts |
| `python3 dev/scripts/devctl.py triage --pedantic --no-cihub --emit-bundle --format md` | you want an AI-friendly pedantic cleanup packet without creating a second triage system | folds the saved pedantic artifacts into normal `triage` output and bundle files; add `--pedantic-refresh` only when you intentionally want triage to regenerate the artifacts inline |
| `python3 dev/scripts/devctl.py check-router --since-ref origin/develop --execute` | before push when scope spans docs/runtime/tooling/release surfaces | auto-selects the stricter required lane, includes risk add-ons, and runs the routed bundle commands |
| `python3 dev/scripts/devctl.py check --profile ci` | before a normal push | catches compile/test/lint issues early |
| `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test --bin voiceterm ...` | an AI/dev session needs to run raw Rust tests or test binaries directly | runs the command without a shell wrapper, then automatically executes the required post-test hygiene follow-up so stale host processes do not accumulate |
| `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel` | right after raw `cargo test` / manual test-binary runs | runs the AI-guard script pack plus host-side `process-cleanup --verify`, so stale repo-related host trees and structural regressions are caught before later runs |
| `python3 dev/scripts/devctl.py process-cleanup --verify --format md` | after PTY/runtime tests, manual tooling bundles, or before handoff when host access is available | safely kills orphaned/stale repo-related host process trees, including descendant PTY children, repo-cwd background helpers, and orphaned tooling descendants, then reruns strict host audit |
| `python3 dev/scripts/devctl.py process-audit --strict --format md` | when you need read-only host diagnosis or cleanup was intentionally skipped | audits the real host process table for repo leftovers visible in Activity Monitor, including descendant PTY children and repo-cwd runtime/tooling helpers that would otherwise look generic |
| `python3 dev/scripts/devctl.py process-watch --cleanup --strict --stop-on-clean --iterations 6 --interval-seconds 15 --format md` | you are reproducing a host leak or running long-lived local work and want periodic checks instead of one final sweep | reruns the host audit/cleanup loop on a cadence and stops only after the host process table is clean |
| `python3 dev/scripts/devctl.py check --profile release` | before release/tag validation on `master` | adds strict remote CI-status + CodeRabbit/Ralph release gates on top of local checks, with mutation-score surfaced as non-blocking reminder output |
| `python3 dev/scripts/devctl.py docs-check --user-facing` | user behavior/docs changed | keeps user docs aligned with behavior |
| `python3 dev/scripts/devctl.py docs-check --strict-tooling` | tooling/process/CI changed | enforces governance and active-plan sync |
| `python3 dev/scripts/devctl.py render-surfaces --format md` | repo-pack templates/policy changed or you need to inspect governed instruction/starter surfaces | previews the current sync state for policy-owned generated surfaces; add `--write` to regenerate drifted outputs |
| `python3 dev/scripts/devctl.py publication-sync --format md` | external paper/site content depends on repo evidence and you need drift visibility | reports watched-path changes since the last recorded sync and shows how to record a new baseline after publish |
| `python3 dev/scripts/devctl.py data-science --format md` | you want one fresh telemetry + agent-sizing snapshot | summarizes command productivity, success/latency stats, and recommended swarm size from historical runs |
| `python3 dev/scripts/devctl.py governance-review --format md` | you want the current false-positive / cleanup scoreboard for adjudicated guard and probe findings | reads the governance review JSONL log, rolls up latest verdicts per finding, and writes refreshed `review_summary.{md,json}` artifacts |
| `python3 dev/scripts/devctl.py integrations-sync --status-only --format md` | you want current federated source pins (`code-link-ide`, `ci-cd-hub`) before import/sync work | gives auditable source SHA + status visibility in one command |
| `python3 dev/scripts/devctl.py integrations-import --list-profiles --format md` | you want to import reusable upstream surfaces safely | shows allowlisted source/profile mappings before any file writes |
| `python3 dev/scripts/devctl.py triage-loop --branch develop --mode plan-then-fix --max-attempts 3 --format md` | you want bounded CodeRabbit remediation automation with artifacts | runs report/fix loop under policy gates, writes actionable loop evidence plus the bounded backlog slice used by autonomy `loop-packet`, and can auto-publish review escalation comments when retries exhaust |
| `python3 dev/scripts/devctl.py loop-packet --format json` | you want one guarded packet for terminal draft injection from loop/triage evidence | builds a risk-scored packet with draft text and auto-send eligibility metadata |
| `python3 dev/scripts/devctl.py autonomy-loop --plan-id <id> --branch-base develop --mode report-only --max-rounds 6 --max-hours 4 --max-tasks 24 --format json` | you want a bounded autonomy-controller run with checkpoint packets and queue artifacts | orchestrates triage-loop/loop-packet rounds with policy-gated stop reasons, run-scoped outputs, and phone-ready `latest.json`/`latest.md` status snapshots |
| `python3 dev/scripts/devctl.py phone-status --view compact --format md` | you want one fast iPhone/SSH-safe controller snapshot from loop artifacts | loads `queue/phone/latest.json`, renders a compact/trace/actions/full view, and can emit controller-state projection files for downstream clients |
| `python3 dev/scripts/devctl.py controller-action --action dispatch-report-only --repo <owner/repo> --branch develop --dry-run --format md` | you want one guarded remote-control action surface without ad-hoc shell steps | validates policy allowlists/mode gates, then executes or previews bounded dispatch/pause/resume/status actions with auditable output |
| `python3 dev/scripts/devctl.py review-channel --action launch --terminal none --dry-run --format md` | you want to bootstrap the current Codex-reviewer / Claude-coder 8+8 markdown swarm from a fresh conversation | validates that the markdown bridge is still active, reads the merged lane table from `dev/active/review_channel.md`, generates conductor launch scripts, and shows the exact bootstrap before opening any terminals |
| `python3 dev/scripts/devctl.py review-channel --action rollover --rollover-threshold-pct 50 --await-ack-seconds 180 --format md` | the active conductor is nearing compaction and needs a clean relaunch instead of relying on recovery summaries | writes a repo-visible handoff bundle, relaunches fresh Codex/Claude conductors, and waits for visible rollover ACK lines in `bridge.md` before the retiring session exits |
| `python3 dev/scripts/devctl.py autonomy-benchmark --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --swarm-counts 10,15,20,30,40 --tactics uniform,specialized,research-first,test-first --dry-run --format md` | you want measurable swarm tradeoff data before scaling live worker runs | validates active-plan scope, runs tactic/swarm-size matrix batches, and emits one benchmark report with per-scenario productivity metrics/charts |
| `python3 dev/scripts/devctl.py swarm_run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --mode report-only --run-label <label> --format md` | you want one fully-guarded plan-scoped swarm run without manual glue steps | loads active-plan scope, executes swarm with reviewer+post-audit defaults, runs governance checks, and appends progress/audit evidence to the plan doc |
| `python3 dev/scripts/devctl.py autonomy-report --source-root dev/reports/autonomy --library-root dev/reports/autonomy/library --run-label <label> --format md` | you want one operator-readable autonomy digest | assembles latest loop/watch artifacts into a dated bundle with markdown/json summary and chart outputs |
| `python3 dev/scripts/devctl.py autonomy-swarm --question-file <plan.md> --adaptive --min-agents 4 --max-agents 20 --plan-only --format md` | you want one governed worker-allocation decision before launching Claude/Codex lanes | computes metadata-driven agent sizing with rationale and emits a deterministic swarm plan artifact |
| `python3 dev/scripts/devctl.py autonomy-swarm --agents 10 --question-file <plan.md> --mode report-only --run-label <label> --format md` | you want one-command live swarm execution with built-in review lane and digest | runs bounded worker fanout, reserves default `AGENT-REVIEW` when possible, and auto-runs post-audit digest artifacts |
| `python3 dev/scripts/devctl.py mutation-loop --branch develop --mode report-only --threshold 0.80 --max-attempts 3 --format md` | you want bounded mutation remediation automation with hotspot evidence | runs report/fix loop and writes actionable mutation artifacts |
| `python3 dev/scripts/devctl.py reports-cleanup --dry-run` | hygiene warns report artifacts are stale/heavy | previews retention cleanup candidates under managed `dev/reports/**` roots |
| `python3 dev/scripts/devctl.py security` | deps or security-sensitive code changed | catches policy/advisory issues |
| `python3 dev/scripts/devctl.py audit-scaffold --force --yes --format md` | guard failures need a fix plan | creates one shared remediation file |

Implementation note for maintainers:

- Shared internals in `devctl` are intentional and should stay centralized:
  `dev/scripts/devctl/process_sweep/` (process parsing/cleanup package),
  `dev/scripts/devctl/security/parser.py` (security CLI parser wiring),
  `dev/scripts/devctl/security/codeql.py` (CodeQL alert-fetch wiring for security gate),
  `dev/scripts/devctl/security/python_scope.py` (Python changed/all scope resolution + core scanner targets),
  `dev/scripts/devctl/audit_events.py` (auto-emitted per-command audit-metrics event logging),
  `dev/scripts/devctl/autonomy/report_helpers.py` (autonomy-report source discovery + summarization helpers),
  `dev/scripts/devctl/autonomy/report_render.py` (autonomy-report markdown/chart renderer helpers),
  `dev/scripts/devctl/autonomy/swarm_helpers.py` (adaptive swarm metadata scoring + sizing + report renderer helpers),
  `dev/scripts/devctl/autonomy/swarm_post_audit.py` (shared autonomy-swarm post-audit payload + digest helpers),
  `dev/scripts/devctl/autonomy/loop_helpers.py` (shared autonomy-loop packet/policy/render helper logic),
  `dev/scripts/devctl/autonomy/phone_status.py` (phone-ready autonomy status payload/render helpers),
  `dev/scripts/devctl/phone_status_views.py` (phone-status projection/render helpers and projection-bundle writer),
  `dev/scripts/devctl/autonomy/status_parsers.py` (shared parser wiring for autonomy-report + phone-status),
  `dev/scripts/devctl/controller_action_parser.py` (`controller-action` parser wiring),
  `dev/scripts/devctl/controller_action_support.py` (`controller-action` policy/mode/dispatch helper logic),
  `dev/scripts/devctl/sync_parser.py` (sync CLI parser wiring),
  `dev/scripts/devctl/integrations_sync_parser.py` (`integrations-sync` parser wiring),
  `dev/scripts/devctl/integrations_import_parser.py` (`integrations-import` parser wiring),
  `dev/scripts/devctl/cihub_setup_parser.py` (`cihub-setup` parser wiring),
  `dev/scripts/devctl/integration_federation_policy.py` (external federation policy + allowlist helpers),
  `dev/scripts/devctl/orchestrate_parser.py` (orchestrator CLI parser wiring),
  `dev/scripts/devctl/script_catalog.py` (canonical check-script path registry),
  `dev/scripts/devctl/path_audit_parser.py` (path-audit/path-rewrite parser wiring),
  `dev/scripts/devctl/path_audit.py` (shared stale-path scanner + rewrite engine),
  `dev/scripts/devctl/triage/parser.py` (triage parser wiring),
  `dev/scripts/devctl/triage/loop_parser.py` (triage-loop parser wiring),
  `dev/scripts/devctl/loop_fix_policy.py` (shared fix-policy engine used by both triage-loop and mutation-loop policy wrappers),
  `dev/scripts/devctl/triage/loop_policy.py` (triage-loop fix policy evaluation),
  `dev/scripts/devctl/triage/loop_escalation.py` (triage-loop escalation comment helper logic),
  `dev/scripts/devctl/triage/loop_support.py` (triage-loop connectivity/comment/bundle helper logic),
  `dev/scripts/devctl/loop_packet_parser.py` (loop-packet parser wiring),
  `dev/scripts/devctl/autonomy/loop_parser.py` (autonomy-loop parser wiring),
  `dev/scripts/devctl/autonomy/benchmark_parser.py` (autonomy-benchmark parser wiring),
  `dev/scripts/devctl/autonomy/run_parser.py` (`swarm_run` parser wiring),
  `dev/scripts/devctl/autonomy/benchmark_helpers.py` (autonomy-benchmark scenario orchestration + metrics helpers),
  `dev/scripts/devctl/autonomy/benchmark_matrix.py` (autonomy-benchmark matrix planner/execution helpers),
  `dev/scripts/devctl/autonomy/benchmark_runner.py` (autonomy-benchmark scenario runner + per-scenario bundle helpers),
  `dev/scripts/devctl/autonomy/benchmark_render.py` (autonomy-benchmark markdown/chart renderer),
  `dev/scripts/devctl/autonomy/run_helpers.py` (`swarm_run` shared scope/prompt/governance/plan-update helpers),
  `dev/scripts/devctl/autonomy/run_render.py` (`swarm_run` markdown renderer),
  `dev/scripts/devctl/failure_cleanup_parser.py` (failure-cleanup parser wiring),
  `dev/scripts/devctl/reports_cleanup_parser.py` (reports-cleanup parser wiring),
  `dev/scripts/devctl/reports_retention.py` (shared report-retention planner used by hygiene + reports-cleanup),
  `dev/scripts/devctl/commands/audit_scaffold.py` (guard-to-remediation scaffold generation),
  `dev/scripts/devctl/triage/support.py` (triage rendering + bundle helpers),
  `dev/scripts/devctl/triage/enrich.py` (triage owner/category/severity enrichment),
  `dev/scripts/devctl/commands/triage_loop.py` (bounded CodeRabbit loop command),
  `dev/scripts/devctl/commands/controller_action.py` (policy-gated controller action command),
  `dev/scripts/devctl/commands/loop_packet.py` (guarded loop-to-terminal packet builder),
  `dev/scripts/devctl/commands/autonomy_loop.py` (bounded autonomy controller loop command + checkpoint queue artifacts),
  `dev/scripts/devctl/commands/autonomy_benchmark.py` (active-plan-scoped swarm matrix benchmark command),
  `dev/scripts/devctl/commands/autonomy_run.py` (guarded plan-scoped `swarm_run` pipeline command),
  `dev/scripts/devctl/commands/autonomy_report.py` (human-readable autonomy digest command),
  `dev/scripts/devctl/commands/autonomy_swarm.py` (adaptive swarm planner/executor with per-agent autonomy-loop fanout),
  `dev/scripts/devctl/commands/autonomy_loop_support.py` (autonomy-loop validation + policy-deny report helpers),
  `dev/scripts/devctl/commands/autonomy_loop_rounds.py` (autonomy-loop round executor helper),
  `dev/scripts/devctl/commands/docs_check_support.py` (docs-check policy + failure-action helper builders),
  `dev/scripts/devctl/commands/docs_check_render.py` (docs-check markdown renderer helpers),
  `dev/scripts/devctl/commands/check_profile.py` (check profile normalization),
  `dev/scripts/devctl/policy_gate.py` (shared JSON policy gate runner),
  `dev/scripts/devctl/status_report.py` (status/report payload + markdown
  rendering), `dev/scripts/devctl/commands/security.py` (local security gate
  orchestration + optional scanner policy),
  `dev/scripts/devctl/commands/integrations_sync.py` (policy-guarded external-source sync/status command),
  `dev/scripts/devctl/commands/integrations_import.py` (allowlisted selective external-source importer + audit log),
  `dev/scripts/devctl/commands/cihub_setup.py` (allowlisted CIHub setup command implementation),
  `dev/scripts/devctl/commands/failure_cleanup.py` (guarded failure-artifact cleanup),
  `dev/scripts/devctl/commands/reports_cleanup.py` (retention-based stale report cleanup),
  and `dev/scripts/devctl/commands/ship_common.py` /
  `dev/scripts/devctl/commands/ship_steps.py` (release-step helpers), plus
  `dev/scripts/devctl/common.py` for shared command-execution failure handling.
  Keep new logic in these helpers to avoid command drift.

Supporting scripts:

- `dev/scripts/checks/check_agents_contract.py`
- `dev/scripts/checks/check_agents_bundle_render.py`
- `dev/scripts/checks/check_active_plan_sync.py`
- `dev/scripts/checks/check_architecture_surface_sync.py`
- `dev/scripts/checks/check_review_channel_bridge.py`
- `dev/scripts/checks/check_multi_agent_sync.py`
- `dev/scripts/checks/check_cli_flags_parity.py`
- `dev/scripts/checks/check_release_version_parity.py`
- `dev/scripts/checks/check_coderabbit_gate.py`
- `dev/scripts/checks/check_coderabbit_ralph_gate.py`
- `dev/scripts/checks/check_screenshot_integrity.py`
- `dev/scripts/checks/check_code_shape.py`
- `dev/scripts/checks/check_workflow_shell_hygiene.py`
- `dev/scripts/checks/check_workflow_action_pinning.py`
- `dev/scripts/checks/check_bundle_workflow_parity.py`
- `dev/scripts/checks/check_ide_provider_isolation.py`
- `dev/scripts/checks/check_compat_matrix.py`
- `dev/scripts/checks/compat_matrix_smoke.py`
- `dev/scripts/checks/check_naming_consistency.py`
- `dev/scripts/checks/check_rust_test_shape.py`
- `dev/scripts/checks/check_rust_lint_debt.py`
- `dev/scripts/checks/check_rust_best_practices.py`
- `dev/scripts/checks/check_rust_compiler_warnings.py`
- `dev/scripts/checks/check_serde_compatibility.py`
- `dev/scripts/checks/check_rust_runtime_panic_policy.py`
- `dev/scripts/checks/check_rust_security_footguns.py`
- `dev/scripts/checks/check_clippy_high_signal.py`
- `dev/scripts/checks/check_mutation_score.py`
- `dev/scripts/checks/check_rustsec_policy.py`
- `dev/scripts/checks/run_coderabbit_ralph_loop.py`
- `dev/scripts/checks/mutation_ralph_loop_core.py`
- `dev/scripts/checks/workflow_loop_utils.py`
- `dev/scripts/audits/audit_metrics.py`
- `dev/scripts/tests/measure_latency.sh`
- `dev/scripts/tests/wake_word_guard.sh`
- `dev/scripts/workflow_bridge/shell.py`
- `scripts/macros.sh`

`check_code_shape.py` enforces both language-level limits and path-level
hotspot budgets, adds targeted function-length guardrails for dispatcher/
pipeline hotspots, and flags stale loose path overrides when files remain below
language soft limits for the configured review window.
`check_workflow_shell_hygiene.py` blocks fragile inline workflow shell patterns
(`find ... | head -n 1`, inline Python snippets) so helper bridges stay the
canonical workflow logic path.
`check_workflow_action_pinning.py` blocks non-SHA and dynamic `uses:` refs so
workflow actions stay pinned to immutable commits.
`check_agents_bundle_render.py` blocks drift between AGENTS rendered bundle
reference docs and canonical registry output; run with `--write` to regenerate
the section from `dev/scripts/devctl/bundle_registry.py`.
`check_architecture_surface_sync.py` blocks newly added active-plan docs,
check scripts, devctl commands, app surfaces, and workflow files from landing
without their owning authority wiring (index/plan/docs/bundle/workflow README
references).
`check_python_subprocess_policy.py` blocks repo-owned Python tooling and
Operator Console code from calling `subprocess.run(...)` without an explicit
`check=` keyword.
`check_command_source_validation.py` blocks launcher/package Python entrypoints
from rebuilding unsafe command sources (`shlex.split(...)` on CLI/env/config
input, raw `sys.argv` forwarding, env-controlled command argv without
validation); during the pilot it is intentionally scoped through the selectable
launcher lane rather than the full default repo policy.
`check_python_broad_except.py` blocks newly added `except Exception` /
`except BaseException` handlers in repo-owned Python tooling/app code unless a
nearby `broad-except: allow reason=...` comment documents the fail-soft path.
`check_bundle_workflow_parity.py` blocks registry/workflow command-bundle drift
by verifying `bundle.tooling` and `bundle.release` commands from
`dev/scripts/devctl/bundle_registry.py` still appear in their owning workflows.
`check_ide_provider_isolation.py` now runs in blocking mode by default and
allows mixed host/provider statements only in explicitly allowlisted policy
owner files.
`check_compat_matrix.py` + `compat_matrix_smoke.py` enforce machine-readable
host/provider compatibility metadata coverage and runtime enum smoke parity.
`check_naming_consistency.py` enforces canonical host/provider token alignment
across runtime enums, backend registry IDs, compatibility matrix policy sets,
and IDE/provider isolation token patterns.
`check_rust_test_shape.py` enforces non-regressive growth controls for Rust
test hotspots (`tests.rs` / `tests/**`) with path-specific budgets for known
large suites.
`check_active_plan_sync.py` enforces active-doc index/spec parity, mirrored-spec
phase heading and `MASTER_PLAN` link contracts, and `MASTER_PLAN` Status
Snapshot release freshness (branch policy + release-tag consistency).
`check_review_channel_bridge.py` enforces the temporary markdown review bridge
contract so `bridge.md` remains a valid fresh-conversation bootstrap
artifact for the current Codex-reviewer / Claude-coder loop, including the
required authority bootstrap order, section ownership, local+UTC heartbeat
header, and operator-visible reviewer chat ping requirement.
`check_multi_agent_sync.py` enforces dynamic multi-agent coordination parity
between the `MASTER_PLAN` board and the runbook (lane/MP/worktree/branch alignment,
instruction/ack protocol validation, lane-lock + MP-collision handoff checks,
status/date format checks, ledger traceability, and end-of-cycle signoff when
all agent lanes are marked merged).
`check_rust_lint_debt.py` enforces non-regressive growth for `#[allow(...)]`
and non-test `unwrap/expect` call-sites in changed Rust files.
`check_rust_best_practices.py` blocks non-regressive growth of reason-less
`#[allow(...)]`, undocumented `unsafe { ... }` blocks, public `unsafe fn`
surfaces without `# Safety` docs, and `std::mem::forget`/`mem::forget` usage
in changed Rust files, plus `Result<_, String>` surfaces, suppressed
channel-send and event-emitter results, bare detached `thread::spawn(...)`
statements without a nearby `detached-thread: allow reason=...` note,
`unwrap()/expect()` on `join`/`recv` paths, and suspicious
`OpenOptions::new().create(true)` chains that do not make overwrite semantics
explicit via `append(true)`, `truncate(...)`, or `create_new(true)`, plus
direct `==` / `!=` comparisons against float literals, plus app-owned
persistent TOML writes that still use direct overwrite helpers instead of a
temp-file swap, plus hand-rolled persistent TOML parsers where the standard
`toml` crate should be used instead.
`check_rust_compiler_warnings.py` runs a no-run JSON `cargo test` compile and
fails when rustc warnings resolve to changed repo-owned `.rs` files, so
warning-only debt such as `unused_imports` gets a dedicated changed-file gate
instead of hiding behind broader Clippy/best-practices checks.
`check_serde_compatibility.py` blocks newly introduced internally or
adjacently tagged Rust `Deserialize` enums unless they either define a
`#[serde(other)]` fallback variant or document intentional fail-closed
behavior with a nearby `serde-compat: allow reason=...` comment.
`check_rust_runtime_panic_policy.py` blocks non-regressive growth of runtime
`panic!` call-sites unless the new panic path is explicitly allowlisted with
`panic-policy: allow reason=...` rationale comments, and it supports
`--absolute` for full-tree Rust panic audits.
`check_rust_security_footguns.py` also blocks non-regressive growth of
`unreachable!()` in runtime hot paths in addition to the existing shell-spawn,
weak-crypto, permissive-mode, PID-cast, and syscall-cast checks.
`check_guard_enforcement_inventory.py` blocks cataloged check scripts from
drifting out of real bundle/workflow enforcement lanes unless they are
explicitly marked helper-only, manual-only, or temporary advisory backlog
exemptions.
`check_clippy_high_signal.py` enforces baseline ceilings for selected
high-signal Clippy lints using lint-code histogram JSON from
`collect_clippy_warnings.py`.

## CI workflows (reference)

- `rust_ci.yml`
- `voice_mode_guard.yml`
- `wake_word_guard.yml`
- `perf_smoke.yml`
- `latency_guard.yml`
- `memory_guard.yml`
- `mutation-testing.yml`
- `security_guard.yml`
- `dependency_review.yml`
- `workflow_lint.yml`
- `coderabbit_triage.yml`
- `scorecard.yml`
- `parser_fuzz_guard.yml`
- `coverage.yml`
- `docs_lint.yml`
- `lint_hardening.yml`
- `coderabbit_ralph_loop.yml`
- `autonomy_controller.yml`
- `autonomy_run.yml`
- `release_preflight.yml`
- `release_attestation.yml`
- `tooling_control_plane.yml`
- `orchestrator_watchdog.yml`
- `failure_triage.yml`
- `publish_pypi.yml`
- `publish_homebrew.yml`
- `publish_release_binaries.yml`

## CI expansion policy

Add or extend CI when new risk classes are introduced:

- New latency-sensitive logic -> perf/latency guard coverage
- New long-running threads/workers -> memory loop/soak coverage
- New release/distribution mechanics -> release/homebrew/pypi validation
- New user modes/flags -> at least one integration lane exercises them
- New dependency/supply-chain exposure -> security policy coverage
- New parser/control-sequence boundary logic -> property-fuzz coverage
- New/edited workflows must keep action refs SHA-pinned (`uses: org/action@<40-hex>`)
  and declare explicit `permissions:` + `concurrency:` blocks.

## Mandatory self-review checklist

Before calling implementation done, review for:

- Security: injection, unsafe input handling, secret exposure
- Memory: unbounded buffers, leaks, large allocations
- Error handling: unwrap/expect in non-test code, missing failure paths
- Concurrency: deadlocks, races, lock contention
- Performance: unnecessary allocations, blocking in hot paths
- Style/maintenance: clippy warnings, naming, dead code
- API/docs alignment: Rust reference checks captured for non-trivial changes
- CI supply chain: workflow refs pinned, permissions least-privilege, concurrency set
- CI runtime hardening: workflows define explicit `timeout-minutes` budgets for long-running/security-sensitive jobs

## Handoff paper trail protocol

For substantive sessions, use `dev/guides/DEVELOPMENT.md` -> `Handoff paper trail template`.
Include:

- exact commands run
- docs decisions (`updated` or `no change needed`)
- screenshot decisions
- Rust references consulted (for non-trivial Rust changes)
- follow-up MP IDs

## Archive and ADR policy

- Keep `dev/archive/` immutable (no deletions/rewrites).
- Keep active execution in `dev/active/MASTER_PLAN.md`.
- Use `dev/adr/` for architecture decisions.
- Keep ADR numbering governance metadata current in `dev/adr/README.md`
  (`Retired ADR IDs`, `Reserved ADR IDs`, and `next: NNNN`).
- Supersede ADRs with new ADRs; do not rewrite old ADR history.

## End-of-session checklist

- [ ] Mandatory SOP steps were completed.
- [ ] Verification commands passed for scope.
- [ ] When host process access was available and PTY/runtime tests, manual tooling bundles, or other orphan-risk local work ran, `python3 dev/scripts/devctl.py process-cleanup --verify --format md` passed or the limitation was recorded; if cleanup was intentionally skipped, `python3 dev/scripts/devctl.py process-audit --strict --format md` passed or the limitation was recorded.
- [ ] Docs updated per governance checklist.
- [ ] `dev/CHANGELOG.md` updated if behavior is user-facing.
- [ ] `dev/active/MASTER_PLAN.md` updated.
- [ ] Repeat-to-automate outcomes captured (new automation or debt-register entry).
- [ ] Follow-up work captured as MP items.
- [ ] Handoff summary captured.
- [ ] Root `--*` artifact check run and clean.
- [ ] Git state is clean or intentionally staged/committed.

## Notes

- `dev/archive/2026-01-29-claudeaudit-completed.md` contains the production readiness checklist.
- Prefer editing existing files over creating new ones.
