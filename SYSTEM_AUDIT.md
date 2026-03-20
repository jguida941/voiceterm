# VoiceTerm / AI Governance Platform — Comprehensive System Audit

**Date:** 2026-03-19
**Scope:** Full codebase review across 13 specialized audit dimensions (2 rounds)
**Auditors:** 14 parallel AI agents (1 lead reconnaissance + 8 Round 1 reviewers + 5 Round 2 deep-dive agents)
**Codebase:** ~87K LOC Rust, ~141K LOC Python tooling, ~49K LOC guards/probes, ~20K LOC operator console
**Round 2 additions:** Token compression, memory systems, governance data flow, system unification, ZGraph research

---

## Executive Summary

VoiceTerm is a **genuinely differentiated product** in a greenfield market category — local-first, deterministic AI code governance. No competitor offers typed finding contracts, decision packets with structured rationale, or a hard-guard / advisory-probe dual-layer enforcement model purpose-built for governing AI coding agents.

However, **four systemic issues** prevent this from becoming a shippable product:

1. **The feedback loop is not closed.** The system captures quality evidence (findings, decisions, scores, trends) but never routes it back to the AI that needs it. The governance-quality-feedback command is not in any bootstrap flow. The AI starts every session blind to quality trends.

2. **The bootstrap is bloated.** ~150K tokens of mandatory reading before the AI can start work. `MASTER_PLAN.md` alone is 318KB. This consumes 75% of a 200K context window on process documentation.

3. **Portability is blocked.** 400+ hardcoded VoiceTerm references, `REPO_ROOT` computed from file-tree position, no installable package (0 on PyPI). New-repo experience graded **F** — cannot function without the full VoiceTerm tree.

4. **Accretive complexity.** The review channel is 78 files / 14K LOC where ~15 files / 800 LOC would suffice. 204 dataclasses for 64K LOC. 7+ parallel state representations. Guard boilerplate duplicated across 70 scripts.

**The product vision is strong. The architecture is sound. The execution gap is real.**

---

## Canonical Integration Status

This file is reference evidence only. It is not a second tracker, execution
spec, or standing roadmap.

Accepted findings from this audit must be translated into canonical execution
state in `dev/active/MASTER_PLAN.md`, the relevant active plan docs under
`dev/active/`, and maintainer docs when process policy changes.

Use this rule set:

1. If a finding here is accepted, add or update executable checklist,
   progress-log, and audit-evidence state in the canonical plan chain.
2. If a finding is rejected, deferred, or narrowed, record that decision in
   the canonical plan chain instead of leaving ambiguity here.
3. Do not point future execution work at `SYSTEM_AUDIT.md` as a shadow
   roadmap once the canonical docs have been updated.
4. When every accepted actionable item has been integrated or explicitly
   rejected in canonical docs, retire the repo-root copy of this audit
   instead of keeping it as a parallel planning surface. The retirement path
   may archive it or delete the repo-root copy once the canonical docs fully
   preserve the decisions and required evidence.

Any stale counts, routing suggestions, or temporary MP mappings inside this
file are historical once superseded by the canonical plan/docs chain.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Cross-Cutting Findings](#2-cross-cutting-findings)
3. [Layer-by-Layer Analysis](#3-layer-by-layer-analysis)
4. [Missing Guards and Probes](#4-missing-guards-and-probes)
5. [Unified Recommendations](#5-unified-recommendations-prioritized)
6. [Critical Path to Product MVP](#6-critical-path-to-product-mvp)
7. [Competitive Position](#7-competitive-position)
8. [Grading Summary](#8-grading-summary)

---

## 1. System Overview

### What This System Is

A 5-layer AI governance platform that makes AI write better code through deterministic enforcement, evidence capture, and feedback loops:

- **Layer 1:** 70 hard guards — deterministic checks that block merge on violation
- **Layer 2:** 24 advisory probes — quality hints that always exit 0
- **Layer 3:** Autonomy loops — AI triage → fix → verify cycles
- **Layer 4:** 30 CI workflows — all routing through devctl commands
- **Layer 5:** Surfaces — CLI (67 commands), operator console (PyQt6), mobile (iOS), Rust overlay

### Core Product Thesis

> "Prompt instructions are useful, but executable local control is what makes AI-assisted engineering reliable."

### The Authority Chain (Partially Implemented)

```
ProjectGovernance → RepoPack → PlanRegistry → PlanTargetRef
    → WorkIntakePacket → CollaborationSession → TypedAction
    → ActionResult / RunRecord / Finding → ContextPack
```

### Key Architectural Patterns

| Pattern | Where Used | Assessment |
|---------|-----------|------------|
| Growth-based non-regression | All guards | Sound — prevents quality degradation without boiling the ocean |
| Guard/probe dual-layer | Layer 1 + 2 | Well-conceived — hard enforcement + advisory hints |
| Bundle composition | `bundle_registry.py` | DRY and clean — shared layers composed into 6 bundles |
| Schema versioning on every artifact | All contracts | Correct — `schema_version` + `contract_id` on everything |
| Deterministic finding identity | `governance/identity.py` | Sound — SHA1 hash of stable seed, repo-relative |
| CheckContext dataclass | `check.py` | Good — replaces closure-captured mutable state |
| Event-sourced review channel | `review_channel/` | Over-engineered for current needs (see §3.6) |

---

## 2. Cross-Cutting Findings

These findings emerged across multiple audit dimensions and represent systemic patterns.

### 2.1 The Feedback Loop Is Not Closed (CRITICAL)

**Found by:** AI Information Flow agent, Architecture agent, Product Vision agent

The system has built impressive evidence capture infrastructure:
- `governance-quality-feedback` computes a 7-dimension composite maintainability score (0-100, letter grade A-F)
- `improvement_tracker.py` computes deltas showing improved/degraded checks
- `recommendation_engine.py` generates AI-readable recommendations
- The governance ledger holds 110 finding records with structured verdicts
- `devctl_events.jsonl` contains 12,238 command telemetry rows

**But none of this reaches the AI:**
- `governance-quality-feedback` is not mentioned in CLAUDE.md, AGENTS.md, or DEVELOPMENT.md
- It is not in any bundle (bootstrap, runtime, docs, tooling, release)
- The governance ledger is never auto-loaded on session start
- The recommendation engine generates guidance that no AI session ever sees
- Quality snapshots require manual `--previous-snapshot` invocation for trends

**Impact:** Every AI session starts blind to quality trends, past decisions, and historical false positives. The AI rediscovers known issues from scratch. The system proves nothing about whether it's making AI code better over time.

### 2.2 Bootstrap Bloat (~150K Tokens) (HIGH)

**Found by:** AI Information Flow agent

| Document | Size | Tokens (~) | Required? |
|----------|------|-----------|-----------|
| `MASTER_PLAN.md` | 318 KB | ~95K | Step 3 of every bootstrap |
| `AGENTS.md` | 114 KB | ~33K | Step 1 (mandatory) |
| `DEVELOPMENT.md` | 82 KB | ~25K | Before any non-trivial work |
| `code_audit.md` | 63 KB | ~19K | In dual-agent mode |
| Other (INDEX.md, README.md, etc.) | ~30 KB | ~9K | Various steps |
| **Total** | **~607 KB** | **~150K** | |

For a 200K-token context window, this leaves ~50K tokens for actual work. Even for 1M context, 150K tokens of process before writing code is significant overhead.

**Industry best practice** recommends three tiers:
- **Hot** (always loaded, <5K tokens): project identity, quality score, active scope, key commands
- **Warm** (per task class, <20K tokens): task-specific context + relevant sections
- **Cold** (on demand): full plans, history, complete catalogs

### 2.3 Duplicate `ReviewBridgeState` — Silent Type Shadowing (HIGH)

**Found by:** Architecture agent, Python Tooling agent

Two classes named `ReviewBridgeState` exist with different fields:
- `runtime/control_state.py` — 10 fields (thin mobile/control projection)
- `runtime/review_state_models.py` — 17 fields (full review channel model)

Both are exported from `runtime/__init__.py`, where the latter silently shadows the former. Type checkers would flag this; runtime Python duck-types through it. `ControlState.review_bridge` actually holds the 10-field version, but any code importing from the package gets the 17-field version.

### 2.4 Guard Boilerplate Duplication (~2,500 Lines) (HIGH)

**Found by:** Guard/Probe agent

70 guard scripts each carry 40-80 lines of identical boilerplate:
- `_is_python_test_path()` reimplemented in 6+ files
- `_growth()` / `_has_positive_growth()` duplicated across 5+ files
- `_render_md()` duplicated in every guard
- 10-20 line try/except import blocks in every script
- Identical `main()` skeleton (parse args, enumerate paths, compute growth, build report)

**Irony:** The system has a `check_function_duplication` guard that catches exactly this pattern — but the guards themselves are the worst offenders.

### 2.5 Over-Decomposition Pattern (MEDIUM)

**Found by:** Review Channel agent, Python Tooling agent

The review channel is 78 files / 14,100 LOC where ~15 files / 800 LOC would suffice (17x minimum). Examples:
- `handoff.py` spawned `handoff_constants.py`, `handoff_time.py`, `handoff_markdown.py`, `handoff_render.py` — 5 files for one concept
- `status_projection_helpers.py` (48 lines) has exactly 2 functions
- `bridge_runtime_state.py` (47 lines), `bridge_promotion.py` (80 lines) — tiny extracts
- 7+ parallel representations of the same state (CQRS taken too far)

Similarly: 204 dataclasses for 64K LOC (1 per 315 lines) is extremely high density.

### 2.6 VoiceTerm Path Coupling (CRITICAL for Portability)

**Found by:** Product Vision agent, Architecture agent

| Blocker | Count | Severity |
|---------|-------|----------|
| `voiceterm`/`VoiceTerm`/`codex-voice` in Python | 81 occurrences / 30 files | HIGH |
| `active_path_config()` / `VOICETERM_PATH_CONFIG` usage | 97 occurrences / 25 files | HIGH |
| Hardcoded `dev/scripts/`, `dev/reports/`, `dev/active/` paths | 166+ / 30+ files | HIGH |
| `REPO_ROOT = Path(__file__).parents[3]` | config.py:10 | CRITICAL |
| Bundle registry with hardcoded paths | 91 references in one file | CRITICAL |
| No `pip install` path | 0 packages on PyPI | CRITICAL |

### 2.7 Shotgun Surgery for New Agents (MEDIUM)

**Found by:** Architecture agent

Adding a new AI agent (beyond Codex/Claude/Cursor) requires touching 5+ files because of per-agent fields:
- `OperatorConsoleSnapshot` has `codex_panel_text`, `claude_panel_text`, `cursor_panel_text` instead of `agents: dict[str, AgentPanelData]`
- `command_builder_core.py` hardcodes agent validation
- `review_state_models.py` agent registry
- `core.py` lane parsing regex
- `surface_definitions.py` caller authority buckets

---

## 3. Layer-by-Layer Analysis

### 3.1 Rust Binary (87K LOC) — Grade: A-

**Thread architecture:** Sound. Single-threaded event loop with crossbeam bounded channels to IO threads. No shared mutable state on the hot path. Only 1 `unsafe` block (signal handler, correctly implemented). No deadlocks or race conditions found.

**Key findings:**
- `EventLoopState` is a god struct (34 fields) — needs sub-grouping into semantic bundles
- `VoiceDrainContext` requires 25+ borrowed fields to construct — needs a builder method
- Duplicate backend dispatch: `BackendFamily` (runtime_compat.rs) and `ProviderId` (provider_adapter.rs) represent the same concept
- `runtime_compat.rs` (796 lines) is a parallel provider-dispatch layer that should flow through `ProviderAdapter`
- Hand-rolled base64 encoder in `writer/mod.rs` — should use the `base64` crate
- Low `.unwrap()` density (82 across 62K LOC) — disciplined
- Provider abstraction is clean but thin — only prompt occlusion is abstracted; backend-specific behavior leaks through runtime_compat

**No correctness bugs found.** The Rust layer is well-architected for its complexity.

### 3.2 Python Tooling (141K LOC) — Grade: C+

**Module structure:** ~450 non-test files across 27 directories. 67 CLI commands. 138+ test files.

**God functions (>200 lines):**

| Lines | File | Function |
|-------|------|----------|
| 322 | `commands/autonomy_run.py:34` | `run` |
| 218 | `commands/autonomy_loop.py:37` | `run` |
| 216 | `commands/sync.py:140` | `run` |
| 211 | `commands/integrations_import.py:33` | `run` |
| 203 | `commands/autonomy_loop_rounds.py:26` | `run_controller_rounds` |

**Code smells:**
- `common.py` uses `globals()` injection to re-export 15 functions from `common_io.py` — invisible to type checkers and IDEs
- Bottom-of-file imports in 12 instances (circular dependency workarounds)
- `getattr(args, "field", None)` pattern pervasive in every `run()` function — type-unsafe
- Stringly-typed packet status (`"pending"`, `"acked"`, `"dismissed"`) — should be StrEnum
- Finding severity (`"low"`, `"medium"`, `"high"`) compared as raw strings across 10+ files
- Dead code at `review_channel/events.py:200` — unreachable `return rows` after `return refreshed, event`

**Data model:** 204 dataclasses. Runtime layer is the cleanest (Grade A-). Consistent frozen+slotted pattern. But manual `to_dict()` methods (20-40 lines each) could use shared helper.

**Tests:** ~1,098 tests. `test_review_channel.py` at **7,829 lines** is 5x the next largest — unmaintainable, needs splitting.

### 3.3 Guard System (70 Guards, 24 Probes) — Grade: B+

**Architecture is sound.** Growth-based non-regression, dual-layer enforcement, clean bundle composition, consistent templates.

**Actual counts:** 70 hard guards (not 64 as documented), 24 advisory probes.

**Categories:**
- Code Shape & Complexity: 13 guards
- Rust-Specific: 10 guards
- Architecture & Governance: 16 guards
- Build/Release/CI: 12 guards
- Python-Specific: 3 guards
- Layout & Naming: 6 guards
- Test & Coverage: 2 guards
- Tooling Meta: 3 guards
- Design Quality Probes: 7
- Error Handling Probes: 3
- Complexity Metric Probes: 5
- Code Style Probes: 4
- Rust-Specific Probes: 5

**Key issue:** Guard boilerplate duplication (~2,500 lines). A `GrowthGuard` base class would reduce each guard from ~100 lines template to ~20 lines unique logic.

**Portability:** 37 guards portable, 30 configurable (JSON), 16 VoiceTerm-coupled. 24/24 probes are 100% portable.

### 3.4 CI/Workflows (30 Workflows) — Grade: B

**Strengths:** Consistent hygiene (SHA-pinned actions, least-privilege permissions, concurrency groups, `set -euo pipefail`). Clean delegation to devctl. Autonomy integration graded A.

**Issues:**
- `tooling_control_plane.yml` is a 633-line monolith with 44 sequential guard steps
- `docs_lint.yml` is fully redundant (subset of tooling_control_plane)
- ALSA header installation duplicated in 14 workflow files
- `release_preflight.yml` pastes 40+ raw commands instead of using bundle registry
- Markdownlint runs in 3 separate workflows on the same files
- 4 specialized Rust guard workflows (`voice_mode_guard`, `memory_guard`, `wake_word_guard`, `latency_guard`) overlap with `rust_ci.yml`'s `cargo test --workspace`

**Portability:** Python guard engine is portable; workflow YAML requires manual rewrite per repo. No workflow generation from bundle registry exists.

### 3.5 Operator Console (20K LOC) — Grade: C

- 30+ direct import paths into devctl internals (feature envy)
- 8 files import `VOICETERM_PATH_CONFIG` directly
- Per-agent fields instead of generic collection
- Functional but deeply coupled to VoiceTerm's directory structure

### 3.6 Review Channel (14K LOC, 78 Files) — Grade: C+

**State machine:** Well-defined with proper StrEnums (ReviewerMode, CodexPollState, OverallLivenessState). Packet transitions explicitly validated.

**Over-engineering:**
- 78 files where ~15 would suffice (17x minimum)
- 7+ parallel state representations (markdown bridge, JSON state, compact/full/actions/trace/agents projections, legacy mirror, heartbeat files)
- CQRS/event-sourcing pattern not earning its complexity for current use case
- The markdown bridge (`code_audit.md`) is fragile — regex-based section parsing, no file locking, concurrent writer risk
- Code explicitly labels the bridge as "transitional" but it remains the primary authority

**Robustness strengths:** Good crash recovery (PID liveness checks, heartbeat staleness, auto-demotion of stale bridges). 3-tier freshness model.

**Robustness gaps:** No file locking on bridge writes. `pgrep -f` can false-positive. No automatic daemon restart. Worktree hash recomputed on every polling tick (expensive).

### 3.7 AI Information Pipeline — Grade: B- (Infrastructure A, Delivery D)

**What's built:** Quality scoring, improvement tracking, recommendation engine, governance ledger, decision packets, allowlist-to-decision pipeline, 12K+ telemetry events.

**What reaches the AI:** Guard pass/fail (immediate), probe risk_hints with ai_instruction (when run), bridge state (in dual-agent mode).

**What doesn't reach the AI:** Quality trends, historical findings, false-positive patterns, recommendations, command telemetry summaries, cross-session context.

**Black box integrity:** Mostly sound. Guards are deterministic and blocking. Allowlist is versioned. Bypass paths forbidden. Leaks: probes are non-blocking (AI can ignore), governance-review recording is voluntary (110 rows vs 12K events), FunctionShapeException is self-service.

**ai_instruction quality:** Consistently good across all probes examined. Language-specific, concrete examples, severity-graduated. Gap: instructions don't reference related findings or past decisions.

---

## 4. Missing Guards and Probes

### P1 — Critical Missing Guards

| Guard | What It Catches | Why It Matters |
|-------|----------------|----------------|
| `check_unused_imports` | Python imports never referenced; Rust `use` warnings | #1 AI supply-chain attack vector — hallucinated package names can be registered by attackers |
| `check_hardcoded_secrets` | API keys, tokens, passwords, connection strings in source | 45% of AI-generated code has security vulnerabilities (Veracode 2025). No Python equivalent exists |
| `check_dead_code_growth` | Functions/methods defined but never called | AI generates dead code at high rate; dead code misleads future AI agents |

### P2 — Important Missing Probes

| Probe | What It Catches | Why It Matters |
|-------|----------------|----------------|
| `probe_test_quality` | Tests with zero assertions, trivially true assertions, tests that never call the function under test | AI frequently produces "always-pass" tests — false coverage worse than no coverage |
| `probe_none_safety` | Attribute access on potentially-None variables; typed returns with None paths | `NoneType` errors are the most common runtime failure in AI-generated Python |
| `probe_over_abstraction` | Abstract classes with only one subclass; interfaces with one implementation | Over-engineering is a known AI anti-pattern |
| `probe_error_strategy_consistency` | Modules with 3+ different error handling strategies | Inconsistent patterns confuse future AI agents |
| `probe_local_naming_coherence` | Mixed naming conventions within a single file | Local naming drift is a leading AI code quality signal |

### P3 — Lower Priority

| Item | Description |
|------|-------------|
| `probe_comment_quality` | High/low comment ratios; comments restating the line below |
| `check_import_organization` | Consistent import ordering (stdlib, third-party, local) |
| Strengthen `check_structural_similarity` | AST-based comparison to catch variable-renamed copies |

---

## 5. Unified Recommendations (Prioritized)

### Tier 0: Close the Feedback Loop

| # | Recommendation | Impact | Effort |
|---|---------------|--------|--------|
| R1 | **Add `governance-quality-feedback` to the bootstrap bundle.** One line in `bundle.bootstrap`. Every AI session immediately sees quality score and trend. | Critical | Low |
| R2 | **Auto-save quality snapshots.** After each `governance-quality-feedback` run, save to well-known path. Next run auto-diffs. AI sees "Score: 78.3 (up 3.1 from last session)." | Critical | Low |
| R3 | **Create `devctl session-context --format md`.** Focused 2K-token summary replacing 150K tokens of markdown: branch, recent commits, open findings, quality score, active MP scope, pending actions. | High | Medium |
| R4 | **Tier the bootstrap into hot/warm/cold.** Hot (<5K tokens): identity + score + scope + commands. Warm (<20K per task): task-specific context. Cold (on demand): full plans, history. | High | Medium |

### Tier 1: Fix Structural Issues

| # | Recommendation | Impact | Effort |
|---|---------------|--------|--------|
| R5 | **Resolve dual `ReviewBridgeState`.** Rename `control_state.ReviewBridgeState` to `ControlBridgeSummary`. Fix `__init__.py` shadowing. | High | Low |
| R6 | **Extract guard boilerplate into `GrowthGuard` base class.** Handles arg parsing, path enumeration, growth computation, report output. Each guard supplies only `_count_metrics()` and thresholds. Eliminates ~2,500 lines of duplication. | High | Medium |
| R7 | **Remove dead code at `review_channel/events.py:200`.** Unreachable `return rows` after `return refreshed, event`. | Low | Trivial |
| R8 | **Replace `globals()` re-export hack in `common.py:24-42`.** Use explicit `from .common_io import (...)`. Restores IDE support and type checking. | Medium | Low |
| R9 | **Split `test_review_channel.py` (7,829 lines)** into 5+ focused test modules by feature area. | Medium | Low |
| R10 | **Introduce `PacketStatus(StrEnum)` and `FindingSeverity(StrEnum)`.** Replace string comparisons across 10+ files. | Medium | Low |

### Tier 2: Reduce Over-Engineering

| # | Recommendation | Impact | Effort |
|---|---------------|--------|--------|
| R11 | **Consolidate review channel from 78 to ~30 files.** Merge handoff family (5→2), follow family (4→2), status family (4→2), auth family (3→1), bridge family (3→1). | High | High |
| R12 | **Reduce state representations from 7+ to 2.** Keep event log (trace.ndjson) as authority + one JSON projection. Deprecate legacy mirror, multiple projection files, separate heartbeat files. Make markdown bridge a read-only projection of event state. | High | High |
| R13 | **Decompose top 5 god-functions.** `autonomy_run.py::run` (322 lines), `autonomy_loop.py::run` (218), `sync.py::run` (216), `integrations_import.py::run` (211), `autonomy_loop_rounds.py::run_controller_rounds` (203). Split into parse/validate, execute, render phases. | Medium | Medium |
| R14 | **Replace per-agent fields with generic collection.** `OperatorConsoleSnapshot` should use `agents: dict[str, AgentLaneSnapshot]` instead of `codex_panel_text`, `claude_panel_text`, etc. | Medium | Medium |

### Tier 3: Improve CI/DevEx

| # | Recommendation | Impact | Effort |
|---|---------------|--------|--------|
| R15 | **Split `tooling_control_plane.yml` (633 lines)** into 3-4 focused workflows: devctl_tests, governance_guards, code_quality_guards, python_typecheck. | High | Medium |
| R16 | **Delete `docs_lint.yml`** — fully redundant with markdownlint step in tooling_control_plane. | Low | Trivial |
| R17 | **Extract shared Rust/ALSA setup into composite action.** Create `.github/actions/setup-rust/action.yml`. Replace 14 duplicate installations. | Medium | Low |
| R18 | **Make `release_preflight.yml` and `tooling_control_plane.yml` use bundle registry** instead of listing 40+ individual commands. | High | Medium |

### Tier 4: Rust Layer Improvements

| # | Recommendation | Impact | Effort |
|---|---------------|--------|--------|
| R19 | **Unify `BackendFamily` and `ProviderId`.** Merge into single canonical enum. Route all backend-specific behavior through `ProviderAdapter`. | Medium | Medium |
| R20 | **Break `EventLoopState` into tighter sub-bundles.** Group remaining flat fields: `VoiceCaptureVisualState`, `SessionRuntimeState`, `MemoryRuntimeState`. | Medium | Medium |
| R21 | **Move runtime_compat host/backend policy into ProviderAdapter.** The 796-line file is a parallel dispatch layer. | Medium | High |
| R22 | **Replace hand-rolled base64 with crate.** Swap 22-line custom encoder in `writer/mod.rs` for `base64` crate. | Low | Trivial |

### Tier 5: Strengthen the Black Box

| # | Recommendation | Impact | Effort |
|---|---------------|--------|--------|
| R23 | **Enforce governance-review recording with a guard.** `check_governance_recording_coverage.py` — compare probe finding count vs governance-review rows recorded. Currently 110 rows vs 12K events = massive under-recording. | High | Medium |
| R24 | **Make probe findings reference the governance ledger.** When a finding matches a known `finding_id` with a verdict, include history in the risk_hint: `{"history": {"previous_verdict": "false_positive", "notes": "..."}}`. | High | Medium |
| R25 | **Add `--format ai` to guard output.** One line on pass, structured JSON on fail with only actionable information. Reduces AI token consumption. | Medium | Medium |
| R26 | **Cross-reference ai_instruction with decision packets.** When a symbol has a `design_decision` in the allowlist, append note to the ai_instruction. | Medium | Low |

### Tier 6: Portability (Required for Product)

| # | Recommendation | Impact | Effort |
|---|---------------|--------|--------|
| R27 | **Replace `REPO_ROOT = Path(__file__).parents[3]`** with lazy resolver using `.git` traversal or env var. Make all modules use `get_repo_root()`. | Critical | Medium |
| R28 | **Kill the VoiceTerm default fallback.** `active_path_config()` returning `VOICETERM_PATH_CONFIG` when no override is set should raise an error instead, forcing explicit initialization. | Critical | Low |
| R29 | **Create an installable Python package.** `pyproject.toml` with proper dependencies, entry points, version. Register on PyPI. Make `pip install ai-code-gov` work. | Critical | High |
| R30 | **Make guards/probes run standalone.** Each guard should accept a target directory as argument. Remove import-time `REPO_ROOT` dependency from `script_catalog.py`. | Critical | High |
| R31 | **Implement `gov init` for new repos.** Scan repo, generate `.governance/policy.json`, write starter config. The `governance-draft` module is 80% there. | Critical | Medium |
| R32 | **Reduce external command surface from 67 to ~8.** `gov init`, `gov check`, `gov probe`, `gov report`, `gov status`, `gov policy`, `gov review`, `gov feedback`. Keep full surface behind `gov advanced`. | High | Medium |

---

## 6. Critical Path to Product MVP

### Phase 1: Close the Loop (1-2 weeks)

1. Add `governance-quality-feedback` to bootstrap bundle
2. Auto-save quality snapshots for trend diffing
3. Create `devctl session-context` command (2K-token focused summary)
4. Tier CLAUDE.md bootstrap into hot/warm/cold

### Phase 2: Fix Structural Debt (2-3 weeks)

5. Resolve dual `ReviewBridgeState`
6. Extract `GrowthGuard` base class
7. Fix dead code, globals() hack, stringly-typed patterns
8. Split the 7,829-line test file

### Phase 3: Package for Extraction (3-4 weeks)

9. Replace `REPO_ROOT` with lazy resolver
10. Kill VoiceTerm default fallback
11. Create installable Python package
12. Make guards/probes run standalone with target directory argument
13. Implement `gov init` bootstrap for new repos

### Phase 4: Prove It Works (1-2 weeks)

14. Pick a real open-source Python repo
15. Run `gov init` and `gov check` against it
16. Fix every crash, missing path, and VoiceTerm assumption
17. Document the experience and measure time-to-first-value

### What Can Be Deferred

- Multi-agent coordination (review channel, collaboration sessions)
- Operator console / PyQt6 frontend
- Mobile/phone status surfaces
- CI workflow generation
- Autonomy loops / swarm orchestration
- PlanRegistry / PlanTargetRef / ContextPack
- Plugin/entrypoint discovery
- Cross-repo federated governance
- Schema migration packs (until v2 ships)

---

## 7. Competitive Position

### Market Landscape (2026)

| Competitor | Model | What This System Does Better |
|-----------|-------|----------------------------|
| **SonarQube** | 6,500 rules, 35+ languages | AI agent governance, decision packets, local-first enforcement |
| **CodeRabbit** | AI PR review, 46% accuracy | Deterministic guarantees, not just suggestions. Guards block, not advise. |
| **Codacy** | $15/user/month, AI Guardrails | No cloud dependency. Works offline. Typed finding contracts. |
| **Semgrep** | Pattern-matching SAST | AI-specific probes (clone_density, boolean_params, design_smells). Quality measurement. |
| **Snyk** | Security-first | Broader scope: quality + governance + measurement, not just security |

### Unique Differentiators (No Competitor Has These)

1. **AI agent governance** — Purpose-built typed action/result/finding chain for AI-in-the-loop
2. **Guard + Probe split** — Two-tier enforcement preventing alert fatigue
3. **Decision packets** — Structured rationale with precedent, invariants, validation_plan
4. **Measurement-first** — ImprovementDelta, quality-to-cost telemetry, false-positive tracking
5. **Multi-agent coordination** — Review channel for coder+reviewer agent tandem
6. **Local-first deterministic** — No cloud dependency, works offline

### Market Timing

41% of commits are now AI-assisted (2026). Teams report 42-48% improvement in bug detection with AI review. But no tool specifically governs AI coding agents with deterministic local enforcement. **This is a greenfield category.**

---

## 8. Grading Summary

| Dimension | Grade | Key Issue |
|-----------|-------|-----------|
| **Rust Binary** | A- | Sound threading, minimal unsafe. God struct needs decomposition. |
| **Guard/Probe System** | B+ | Strong architecture. Boilerplate duplication is the main weakness. |
| **Python Tooling** | C+ | God functions, globals hack, 204 dataclasses, 7.8K-line test file. |
| **CI/Workflows** | B | Well-structured but 633-line monolith and YAML duplication. |
| **Review Channel** | C+ | Working but 17x over-engineered. 78 files, 7+ state representations. |
| **Operator Console** | C | Functional but deeply coupled to VoiceTerm paths. |
| **AI Information Flow** | B- | Infrastructure A, Delivery D. Feedback loop not closed. |
| **Architecture** | B | Sound layer separation. Contract system good. Portability blocked. |
| **Product Vision** | B+ | Genuinely differentiated. Over-specified. |
| **Portability** | D | 400+ hardcoded references. New-repo experience: F. |
| **Competitive Position** | A- | Unique in local-first AI governance. No direct competitor. |
| **Black Box Integrity** | B+ | Guards deterministic and blocking. Probes are the main leak. |

### Overall Assessment

**The product idea is genuinely differentiated and the market timing is strong.** The architecture is fundamentally sound — the 5-layer model, the guard/probe split, the typed contracts, and the evidence capture infrastructure are well-designed.

**The gap is between "documented architecture" and "someone else can use it."** The system has invested heavily in internal specifications (30K+ words of plan docs) while the external packaging remains at zero. The feedback loop — the core value proposition ("AI writes better code over time") — is built but not connected.

**Closing the feedback loop (Tier 0) and creating an installable package (Tier 6) are the two highest-leverage actions.** Everything else is optimization of a working system.

---

## Appendix: Key File References

### Critical Fixes

| File | Line | Issue |
|------|------|-------|
| `dev/scripts/devctl/review_channel/events.py` | 200 | Dead code: unreachable `return rows` |
| `dev/scripts/devctl/runtime/control_state.py` | 38 | Duplicate `ReviewBridgeState` class name |
| `dev/scripts/devctl/common.py` | 24-42 | `globals()` injection hack |
| `dev/scripts/devctl/config.py` | 10 | `REPO_ROOT = Path(__file__).parents[3]` |
| `dev/scripts/devctl/repo_packs/__init__.py` | 50 | VoiceTerm default fallback |

### Large Files Needing Attention

| File | Lines | Issue |
|------|-------|-------|
| `dev/scripts/devctl/tests/test_review_channel.py` | 7,829 | Split into 5+ focused modules |
| `.github/workflows/tooling_control_plane.yml` | 633 | Split into 3-4 workflows |
| `dev/scripts/devctl/commands/autonomy_run.py` | 322+ | God function `run()` |
| `rust/src/bin/voiceterm/main.rs` | 944 | Approaching soft limit |
| `rust/src/bin/voiceterm/runtime_compat.rs` | 796 | Parallel provider dispatch |

### Sources Consulted

- [CodeRabbit: AI vs Human Code Generation Report](https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report)
- [CodeScene: Agentic AI Coding Best Practices](https://codescene.com/blog/agentic-ai-coding-best-practice-patterns-for-speed-with-quality)
- [Anthropic: 2026 Agentic Coding Trends Report](https://resources.anthropic.com/hubfs/2026%20Agentic%20Coding%20Trends%20Report.pdf)
- [Evaluation-Driven Development and Operations of LLM Agents (arxiv)](https://arxiv.org/html/2411.13768v3)
- [Codified Context: Infrastructure for AI Agents (arxiv)](https://arxiv.org/html/2602.20478v1)
- [Guardrails for Agentic Coding (van Eyck)](https://jvaneyck.wordpress.com/2026/02/22/guardrails-for-agentic-coding/)
- [Veracode 2025: AI Code Security](https://www.darkreading.com/application-security/coders-adopt-ai-agents-security-pitfalls-lurk-2026)
- [SonarQube Rules Documentation](https://docs.sonarsource.com/sonarqube-server/quality-standards-administration/managing-rules/rules)
- [Best AI Code Review Tools 2026](https://www.qodo.ai/blog/best-automated-code-review-tools-2026/)

---

# ROUND 2: Deep-Dive Findings

*5 additional agents investigated token compression, memory architecture, governance data flow, system unification, and ZGraph integration.*

---

## 9. Token Compression & Bootstrap Optimization

### 9.1 The Measured Problem

| Document | Bytes | Est. Tokens | Actually Used | Waste Rate |
|----------|-------|-------------|--------------|------------|
| `MASTER_PLAN.md` | 318,409 | ~79,600 | ~2,000 | 97.5% |
| `dev/scripts/README.md` | 133,215 | ~33,300 | ~1,700 | 94.9% |
| `AGENTS.md` | 114,332 | ~28,500 | ~5,000 | 82.5% |
| `DEVELOPMENT.md` | 82,536 | ~20,600 | ~4,400 | 78.6% |
| `code_audit.md` | 63,270 | ~15,800 | ~2,000 | 87.3% |
| `INDEX.md` | 8,431 | ~2,100 | ~800 | 61.9% |
| `CLAUDE.md` | 7,965 | ~2,000 | ~800 | 60.0% |
| **TOTAL** | **728,158** | **~181,900** | **~16,700** | **90.8%** |

**Of ~182K tokens loaded, a typical task needs ~16.7K.** The remaining 165K tokens are wasted context.

### 9.2 Three-Tier Context Architecture (Design)

**Tier 1 — HOT CONTEXT (always loaded, ~3,780 tokens)**

Auto-generated snapshot replacing CLAUDE.md as bootstrap entry:
- `bootstrap.yaml` (~1,800 tokens): identity, mode, quality scores, active scope, key commands, file limits
- `manifest.yaml` (~480 tokens): cold retrieval index with trigger conditions
- `quality.yaml` (~300 tokens): scores, trends, guard calibration
- `plan_digest.yaml` (~1,200 tokens): compressed MASTER_PLAN (phase status, active lanes, open items count)

**Tier 2 — WARM CONTEXT (per task class, ~8,500 tokens)**

Task router selects exactly one warm context pack:
- `warm.runtime` (~8K tokens): bundle.runtime commands, runtime risk matrix, post-edit checks, active plan scope
- `warm.tooling` (~12K tokens): bundle.tooling commands, probe reference, post-edit checks
- `warm.docs` (~5K tokens): documentation governance, bundle.docs
- `warm.release` (~10K tokens): release SOP, bundle.release
- `warm.bridge` (~4K tokens, only in `active_dual_agent`): bridge rules + live state sections

**Tier 3 — COLD CONTEXT (on-demand, 0 tokens by default)**

The manifest includes a retrieval index (~15 entries) with trigger conditions:
```yaml
cold_index:
  - {id: sot_map,        trigger: "where is X defined",         file: "AGENTS.md",    lines: "38-89"}
  - {id: probe_registry, trigger: "adding/editing probes",      file: "AGENTS.md",    lines: "336-433"}
  - {id: cmd_catalog,    trigger: "devctl command reference",   file: "README.md",    lines: "206-500"}
  - {id: mp_backlog,     trigger: "planning new work",          file: "MASTER_PLAN",  lines: "1641-2723"}
  # ...
```

### 9.3 Token Budget Comparison

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Minimum session context | 166,100 | 3,780 | **-97.7%** |
| Typical session context | 181,900 | 12,280 | **-93.2%** |
| Maximum (everything loaded) | 181,900 | ~40,000 | **-78.0%** |
| Context recovered for work | 0 | ~170,000 | **+170K tokens** |

### 9.4 New CLAUDE.md (~200 tokens, down from 2,000)

```markdown
# Bootstrap
Read `.devctl/bootstrap.yaml`. If absent or stale, run:
  python3 dev/scripts/devctl.py bootstrap-context
After bootstrap, classify your task and read the matching warm pack.
For full SDLC policy, read AGENTS.md. Load only when warm pack is insufficient.
Mandatory: after every file edit, run the bundle for your task class.
```

### 9.5 Implementation: `devctl bootstrap-context` Command

- Reads existing devctl outputs (platform-contracts, check, quality-policy, git state, INDEX.md)
- Generates `.devctl/bootstrap.yaml`, `.devctl/manifest.yaml`, `.devctl/quality.yaml`, `.devctl/plan_digest.yaml`, `.devctl/warm/<class>.md`
- `.devctl/` is gitignored — ephemeral session artifacts
- Cache invalidation via `source_hash` combining `git rev-parse HEAD` + policy file hashes
- Estimated implementation effort: 7-10 hours

---

## 10. ZGraph Notation & Symbolic Compression

### 10.1 What ZGraph Is

ZGraph-Notation (invented by Justin Guida, June 2025) compresses adjacency matrices into minimal symbolic form. A row `[0, 0, 0, 0, 1, 0]` becomes `Z4` — "edge to node 4." Extensions: `Z3=7` (weighted), `Z5<->` (bidirectional), `Z2,4,7` (multi-edge).

**Key properties:** Sparse-matrix efficient, O(1) pattern recognition, lossless round-trip, natural language mapping.

### 10.2 How ZGraph Generalizes to Bootstrap Compression

The bootstrap files contain graph structures that ZGraph notation naturally compresses:

**Plan authority graph (27 tokens vs ~2,000 tokens of prose):**
```
MP377 -> [ai_governance_platform, platform_authority_loop]
MP376 -> [portable_code_governance] <sub MP377>
MP368..375 -> [review_probes]
MP359 -> [operator_console]
MP358 -> [continuous_swarm]
```

**Quality trend (compact time-series):**
```
Q[code_health] = [0.72, 0.75, 0.78, 0.81] @[M60, M61, M62, M63]
Q[governance] = [0.45, 0.52, 0.61, 0.68] @[M60, M61, M62, M63]
```

**Module dependency graph:**
```
Z[review_channel] -> Z[event_models, state, parser, heartbeat, promotion]
Z[platform_contracts] -> Z[runtime, finding_contracts, action_contracts]
```

### 10.3 ConceptIndex: ZGraph-Based Navigation Artifact

A single compact artifact (~2,000 tokens) serving as the navigational map for the entire knowledge base:
- System identity and active execution state
- Plan authority graph in ZGraph notation
- Module dependency graph
- Guard/probe registry summary
- Quality snapshot
- Task routing rules

**This is an INDEX, not a summary.** It tells the AI where to look, not what the documents say. Full documents remain the source of truth. The ConceptIndex is generated deterministically from existing devctl command outputs.

### 10.4 Industry Validation

| Approach | Source | Relevance |
|----------|--------|-----------|
| **Codified Context** (arXiv 2602.20478) | 3-tier hot/warm/cold system, tested 283 sessions | Direct architectural match |
| **ACON** (arXiv 2510.00615) | 26-54% token reduction, 95%+ task accuracy, gradient-free | Validates compression approach |
| **Code-Craft** (arXiv 2504.08975) | Graph-based codebase representation, 82% retrieval improvement | Validates graph navigation |
| **Anthropic** (Context Engineering Guide) | "Retrieve precisely when needed" | Validates on-demand loading |
| **CogniLayer MCP** | 80-200K+ tokens saved per session | Validates scale of savings |
| **Factory.ai** (36K production messages) | Structured summarization outperforms raw context | Validates compression approach |

### 10.5 Integration with MASTER_PLAN

The MASTER_PLAN already accepts this direction:
- Lines 194-200: "Startup-token burden is now explicit product debt" + target description
- Lines 259-264: Accepts "ConceptIndex, optionally emitted in a ZGraph-compatible encoding"
- Lines 213-225: Defines Architectural Knowledge Base with topic-keyed SQLite, token budgets, ConceptIndex integration

**Sequencing:** ConceptIndex / topic chapters / ZGraph encoding are **P1 deliverables that depend on P0 contracts being stable** (MASTER_PLAN.md:273-281, ai_governance_platform.md:681-689). The active plan explicitly says "do not pull the full knowledge base forward into P0." The P0 evidence bridge and contract freeze must land first. However, the `devctl bootstrap-context` command (§9.5) — which generates compressed YAML from *existing* devctl outputs without requiring ConceptIndex — can land earlier as a standalone token-reduction tool since it composes existing commands, not new contracts.

**ConceptIndex rules (must be frozen before P1 execution):**
1. **Generated-only** — never hand-authored; deterministic from contracts, plans, guard/probe metadata
2. **Schema-versioned** — explicit `schema_version`, symbol namespace, provenance refs on every artifact
3. **Fail-closed expansion** — if symbolic expansion parity check fails, fall back to warm raw chapters
4. **Eval gate** — must demonstrate non-inferior task success, citation validity, unsupported-claim rate, tokens, and p95 latency (per memory_studio.md:1410-1417). Token savings alone do not qualify.

**Authority model:** ZGraph/ConceptIndex is a compact IR (intermediate representation) over canonical contracts and artifacts. It is the navigation layer, not the source of truth. Authority stays in generated contracts and canonical artifacts; the symbolic form indexes them, never replaces them.

---

## 11. Memory Systems Architecture

### 11.1 Seven Disconnected Memory Systems

| System | Location | Status | Cross-Agent? |
|--------|----------|--------|-------------|
| **Claude Auto-Memory** | `~/.claude/projects/.../memory/` | 12 entries, operational | Claude-only |
| **Rust Memory Studio** | `rust/src/bin/voiceterm/memory/` | Fully built, `#![allow(dead_code)]` | VoiceTerm-only, unwired |
| **Governance Review Ledger** | `dev/reports/governance/*.jsonl` | 110 rows, operational | Any agent (manual) |
| **Quality Feedback Snapshot** | `dev/reports/governance/quality_feedback_latest/` | Operational, 120s cache | Operator Console only |
| **JSONL Telemetry** | `dev/reports/devctl_events.jsonl` | 12,238 rows | Never consumed |
| **Finding Contracts** | `runtime/finding_contracts.py` | Typed but ephemeral | Probe-only path |
| **Live Bridge** | `code_audit.md` | Current-state only, no history | Both agents, no persistence |

**Critical gap: Cross-agent memory does not exist.** Claude and Codex cannot share session knowledge. The Rust Memory Studio (the most sophisticated system — FTS5 search, context packs, token budgeting, query planning) is completely unwired to Python governance.

### 11.2 What Gets Lost Between Sessions

| Information | Persistence? | Impact |
|-------------|-------------|--------|
| Guard failure patterns & fix strategies | None | AI rediscovers known issues |
| Session-to-session causal chains | Git commits only | Why decisions were made is lost |
| Codebase architectural understanding | Re-derived from scratch | ~150K tokens of re-reading |
| Quality trajectory (which session improved what) | None | No per-session attribution |
| Bridge conversation history | Overwritten (current-state only) | Reviewer/coder negotiations lost |
| Failed approaches and why | None | Same failures repeated |

### 11.3 No Session Lifecycle Manager

There are no start/end bookends for AI sessions:
- **No `devctl session start`** — no intake packet generated
- **No `devctl session end`** — no session journal artifact
- **No "what did last session do" command** — no cross-session context

### 11.4 Stale Memory Problem

Claude auto-memory entries have no expiry or validation. Example: MEMORY.md says "Last tagged release: v1.0.99 (2026-03-03)" but the repo is at v1.1.1 (2026-03-06). Stale facts persist and mislead.

### 11.5 Recommendations

| # | Action | Impact |
|---|--------|--------|
| M1 | Build `devctl session-context` — bounded intake packet from git diff + quality + governance | Critical |
| M2 | Build `devctl session-end --summary "..."` — emit session journal artifact | High |
| M3 | Port Rust ContextPack logic to Python devctl (or expose via command) | High |
| M4 | Create cross-agent memory surface at `dev/reports/sessions/latest_summary.json` | High |
| M5 | Add `resolution_summary` field to `GovernanceReviewInput` for fix strategy learning | Medium |
| M6 | Make feedback entries machine-actionable as prompt guard lines | Medium |
| M7 | Add memory validation command that checks memory facts against repo state | Medium |

---

## 12. Governance Data Flow & Unification

### 12.1 The Two Break Points in the Feedback Loop

```
BREAK POINT 1: Evidence never enters the ledger
═══════════════════════════════════════════════
Guards → FindingRecord.to_dict() → DEAD END (ephemeral, never persisted)
Probes → FindingRecord.to_dict() → DEAD END (ephemeral, never persisted)
Failures → FailurePacket → DEAD END (never enters governance)
Review events → 12,238 rows → DEAD END (never enters governance)

BREAK POINT 2: Quality scores never reach the AI
═══════════════════════════════════════════════
Governance Ledger → QualityFeedbackSnapshot → Operator Console (display only)
                                            → AI Agent context: NOT CONNECTED
```

### 12.2 Thirteen Data Stores, Mostly Disconnected

| Store | Schema | Typed? | Persisted? | Feeds Into |
|-------|--------|--------|-----------|------------|
| Governance Review Ledger | Raw dict rows | No | Yes (JSONL) | Quality feedback |
| External Findings Ledger | Raw dict rows | No | Yes (JSONL) | Quality feedback |
| FindingRecord contracts | Typed dataclass | Yes | No (ephemeral) | Nothing |
| DecisionPacketRecord | Typed dataclass | Yes | No (ephemeral) | Nothing |
| FailurePacket | Typed dataclass | Yes | No (ephemeral) | Status report only |
| ActionResult contracts | Typed dataclass | Yes | Rarely | Nothing |
| ProjectGovernance | Typed dataclass | Yes | Yes (JSON) | Startup authority |
| Quality Feedback Snapshot | Typed dataclass | Yes | Yes (JSON) | Operator Console |
| Review Channel State | 7+ representations | Mixed | Yes (7+ files) | Nothing |
| Probe Report artifacts | JSON | Structured | Yes (JSON) | Nothing |
| Guard Report artifacts | Raw dict | No | No (ephemeral) | Nothing |
| Data Science rows | Typed dataclass | Yes | No | Nothing |
| JSONL Telemetry | Raw dict | No | Yes (12K rows) | Nothing |

### 12.3 Dual Finding Identity Schemes

`governance/identity.py::hash_identity_parts()` and `runtime/finding_contracts.py::build_finding_id()` hash **different field sets**. The same finding gets different `finding_id` values depending on which path creates it.

### 12.4 Three of Seven Quality Dimensions Permanently Unavailable

| Dimension | Weight | Data Source Exists? | Wired? |
|-----------|--------|-------------------|--------|
| `halstead_mi` | 0.20 | Yes (Halstead analysis) | Yes |
| `code_shape` | 0.10 | Yes (code_shape guard) | **No** |
| `duplication` | 0.10 | Yes (function_duplication guard) | **No** |
| `guard_issue_burden` | 0.20 | Partial (only manual rows) | Partial |
| `finding_density` | 0.15 | Partial (only manual rows) | Partial |
| `time_to_green` | 0.10 | Yes (CI run data) | **No** |
| `cleanup_rate` | 0.15 | Partial (only manual rows) | Partial |

### 12.5 Unified Evidence Pipeline (Design)

```
Guard/Probe Output → Standard FindingRecord → Governance Ledger → Quality Aggregator → AI Dashboard
```

**Key changes:**
1. Auto-persist guard findings: `python_guard_report.py` appends `FindingRecord` to governance JSONL with `verdict="open"`
2. Auto-persist probe findings: `review_probe_report.py` appends `FindingRecord` to governance JSONL
3. Wire 3 missing quality dimensions: `code_shape` from guard output, `duplication` from guard output, `time_to_green` from CI run data
4. Unify identity hashing into one `build_finding_id()` function
5. Migrate ledger rows from raw dicts to `FindingRecord.to_dict()` format

### 12.6 AI Quality Dashboard (Design)

Compact block for every session start and post-verification cycle:

```markdown
## Quality Dashboard
- **Score**: 72.5/100 (Grade C) | Trend: +2.3 (improving)
- **Lenses**: code_health=68.2/D, governance_quality=75.1/C, operability=n/a
- **Open findings**: 15 (3 high, 8 medium, 4 low)
- **Guard calibration**: 82.5% precision, 17.5% FP rate
- **Top action**: probe_single_use_helpers — Add wrapper-code exclusions (high impact)
- **Last governance review**: 4.2h ago | Cleanup rate: 65%
```

Delivered via: CLAUDE.md injection, bridge injection (dual-agent), guard output augmentation.

---

## 13. System Unification Blueprint

### 13.1 Module Consolidation Targets

| Area | Current Files | Target Files | Reduction |
|------|--------------|-------------|-----------|
| devctl/ top-level .py | 76 | ~20 | 74% |
| review_channel/ | 58 | ~15 | 74% |
| commands/ | 124 | ~40 | 68% |
| **Total non-test source** | **~417** | **~200** | **52%** |
| Dataclasses | 206 | ~120 | 42% |
| State classes | 32 | ~12 | 62% |
| `*_from_mapping` functions | 21 | 1 (generic) | 95% |

### 13.2 External Command Surface: 67 → 7

| External Command | Internal Commands Subsumed |
|-----------------|--------------------------|
| `gov init` | governance-bootstrap, governance-draft, render-surfaces |
| `gov check` | check --profile ci, check-router, docs-check, hygiene |
| `gov report` | status, probe-report, quality-policy, platform-contracts |
| `gov review` | governance-review, review-channel, governance-import-findings |
| `gov fix` | guard-run, triage, triage-loop, autonomy-loop |
| `gov release` | release-gates, release, ship, release-notes |
| `gov config` | quality-policy, render-surfaces, list |

Internal 67-command surface remains for power users. `gov` is a thin dispatch wrapper.

### 13.3 Unified Output Contract

Every guard, probe, and report wraps in a standard envelope:

```json
{
  "contract_id": "gov.check.code-shape",
  "schema_version": 1,
  "timestamp": "2026-03-19T12:00:00Z",
  "ok": true,
  "severity": "pass",
  "summary": "All files within shape limits",
  "findings": [...],
  "metrics": {"files_scanned": 441, "elapsed_seconds": 1.2}
}
```

This unifies what guards call "violations" and probes call "risk_hints" into one schema. `--format` flags standardized: `json | md | terminal | sarif`.

### 13.4 Deletion Candidates

| Item | Reason | Action |
|------|--------|--------|
| `.github/workflows/docs_lint.yml` | Fully redundant with tooling_control_plane | Delete |
| `globals()` hack in `common.py:24-41` | Compatibility shim | Replace with explicit imports |
| Dead code at `events.py:200` | Unreachable return | Delete line |
| 21 hand-written `*_from_mapping` functions | ~500 lines boilerplate | Replace with 30-line generic |
| 38 scattered `*_parser.py` files at devctl root | Should be colocated with commands | Move |
| 9 `governance_*` files at devctl root | Should be in `governance/` package | Move |

### 13.5 Review Channel Consolidation Map

```
CURRENT (58 files)                    → TARGET (~15 files)
handoff.py + 4 handoff_*.py           → handoff.py (1 file)
3 promotion*.py + bridge_promotion.py → promotion.py (1 file)
6 follow*.py + reviewer_follow.py     → follow.py + follow_stream.py (2 files)
4 status*.py                          → projection.py (1 file)
5 event*.py + daemon_events/reducer   → events.py + event_store.py (2 files)
4 prompt*.py                          → prompt.py (1 file)
3 attach_auth*.py                     → auth.py (1 file)
peer_liveness + peer_recovery         → peers.py (1 file)
bridge_validation + bridge_runtime    → bridge.py (1 file)
3 parser*.py                          → parser.py (1 file)
```

### 13.6 Implementation Sequence

| Phase | Work | Duration | Risk |
|-------|------|----------|------|
| **Phase 1: Quick Wins** | Dedupe ReviewBridgeState, kill globals() hack, generic from_dict, delete docs_lint.yml | 1-2 days | Low |
| **Phase 2: File Consolidation** | Review channel 58→15, move governance files, move parser files | 3-5 days | Medium |
| **Phase 3: Output Contract** | Define OutputEnvelope, add to ProbeReport, add to check_bootstrap | 3-5 days | Medium |
| **Phase 4: Command Surface** | Build `gov` wrapper, merge status commands, merge governance commands | 5-7 days | Higher |
| **Phase 5: Deep Simplification** | State class consolidation, commands/ restructure, dashboard | Ongoing | Medium |

---

## 14. Unified Action Plan (All Rounds Combined)

### Tier 0: Close the Feedback Loop (Highest Leverage)

| # | Action | Source |
|---|--------|--------|
| A1 | Auto-persist guard/probe findings to governance ledger | §12.5 |
| A2 | Wire 3 missing quality dimensions (code_shape, duplication, time_to_green) | §12.4 |
| A3 | Build AI Quality Dashboard and inject into CLAUDE.md/bridge | §12.6 |
| A4 | Unify finding identity hashing into one function | §12.3 |

### Tier 1: Compress the Bootstrap (Biggest Token Savings)

| # | Action | Dependency | Source |
|---|--------|-----------|--------|
| A5 | Build `devctl bootstrap-context` command (generates .devctl/ artifacts) | None — composes existing commands | §9.5 |
| A6 | Design 3-tier hot/warm/cold context packs | None — YAML generation from existing outputs | §9.2 |
| A7 | Replace CLAUDE.md with 200-token bootstrap pointer | A5 landing | §9.4 |
| A8 | Build ConceptIndex generator (ZGraph-compatible) | **P0 contract freeze must land first** (MASTER_PLAN:273) | §10.3 |

### Tier 2: Unify the Memory Layer

| # | Action | Source |
|---|--------|--------|
| A9 | Build `devctl session-context` (intake packet from git diff + quality) | §11.5 |
| A10 | Build `devctl session-end` (session journal artifact) | §11.5 |
| A11 | Create cross-agent memory surface | §11.5 |
| A12 | Port Rust ContextPack logic to Python | §11.5 |

### Tier 3: Fix Structural Debt

| # | Action | Source |
|---|--------|--------|
| A13 | Resolve dual ReviewBridgeState | §2.3 |
| A14 | Extract GrowthGuard base class (eliminates ~2,500 lines) | §2.4 |
| A15 | Consolidate review channel 58→15 files | §13.5 |
| A16 | Generic from_dict deserializer (replaces 21 functions) | §13.1 |
| A17 | Fix globals() hack, dead code, stringly-typed patterns | §3.2 |

### Tier 4: Simplify the Surface

| # | Action | Source |
|---|--------|--------|
| A18 | Build `gov` 7-command external surface | §13.2 |
| A19 | Unified output contract (OutputEnvelope) | §13.3 |
| A20 | Split tooling_control_plane.yml (633→3-4 workflows) | §3.4 |
| A21 | Extract shared Rust/ALSA composite action | §3.4 |

### Tier 5: Product Portability

| # | Action | Source |
|---|--------|--------|
| A22 | Replace `REPO_ROOT = Path(__file__).parents[3]` with lazy resolver | §2.6 |
| A23 | Kill VoiceTerm default fallback in active_path_config() | §2.6 |
| A24 | Create installable Python package (pip install) | §6 |
| A25 | Implement `gov init` bootstrap for new repos | §6 |
| A26 | Prove on second repo (zero core patches) | §6 |

### Tier 6: Strengthen the Black Box

| # | Action | Source |
|---|--------|--------|
| A27 | Add missing guards: unused imports, hardcoded secrets, dead code | §4 |
| A28 | Add missing probes: test quality, None-safety, over-abstraction | §4 |
| A29 | Enforce governance-review recording with a guard | §5 |
| A30 | Make probe findings reference governance ledger history | §5 |

---

## Appendix: Round 2 Sources

- [ZGraph-Notation Repository](https://github.com/jguida941/ZGraph-Notation)
- [ACON: Agent Context Optimization (arXiv:2510.00615)](https://arxiv.org/abs/2510.00615)
- [Codified Context: Infrastructure for AI Agents (arXiv:2602.20478)](https://arxiv.org/abs/2602.20478)
- [LocAgent: Graph-Guided LLM Agents (ACL 2025)](https://arxiv.org/abs/2503.09089)
- [Code-Craft: Hierarchical Graph-Based Code Summarization](https://arxiv.org/abs/2504.08975)
- [LongCodeZip: Perplexity-Based Code Compression (ASE 2025)](https://arxiv.org/abs/2510.00446)
- [500xCompressor (ACL 2025)](https://github.com/ZongqianLi/500xCompressor)
- [NAACL 2025 Prompt Compression Survey](https://github.com/ZongqianLi/Prompt-Compression-Survey)
- [Anthropic: Effective Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Factory.ai: Evaluating Context Compression](https://factory.ai/news/evaluating-compression)
- [CogniLayer MCP Server](https://github.com/LakyFx/CogniLayer)
- [CodexGraph (NAACL 2025)](https://arxiv.org/abs/2408.03910)
- [Anthropic: 2026 Agentic Coding Trends Report](https://resources.anthropic.com/hubfs/2026%20Agentic%20Coding%20Trends%20Report.pdf)

---

# ROUND 3: Security, Safety & Self-Consistency

*7 agents (1 lead + 6 specialized) investigated areas Rounds 1-2 missed entirely: autonomy self-modification, daemon security, evidence integrity, guard consistency, operator console coupling depth, and test coverage gaps.*

---

## 15. CRITICAL: Daemon Remote Code Execution (RCE)

**Severity: CRITICAL. 2 critical, 5 high, 5 medium, 3 low findings.**

### 15.1 Attack Surface

| Surface | Bind Address | Auth | TLS |
|---------|-------------|------|-----|
| Unix socket | `~/.voiceterm/control.sock` | **None** | N/A |
| WebSocket | **`0.0.0.0:9876`** (hardcoded, all interfaces) | **None** | **None** |

Any connected client can: `SpawnAgent` (arbitrary binary via `execvp()`), `SendToAgent` (arbitrary PTY input), `KillAgent`, `ListAgents`, `GetStatus`, `Shutdown`.

### 15.2 Critical Vulnerabilities

**C-1: Arbitrary command execution via WebSocket.** `SpawnAgent.provider` flows directly to `execvp()` with zero validation — no allowlist, no path sanitization. Any LAN peer can achieve full RCE.

**C-2: WebSocket hardcoded to `0.0.0.0`.** Not configurable. Combined with C-1, any device on the local network can execute arbitrary commands as the daemon's user.

### 15.3 High Vulnerabilities

- **H-1:** No authentication on either transport
- **H-2:** No TLS — agent output (secrets, API keys) transmitted in cleartext
- **H-3:** Remote daemon shutdown with one command
- **H-4:** Unrestricted process termination via `KillAgent`
- **H-5:** Terminal escape injection via `SendToAgent` — can inject Ctrl-C, shell commands

### 15.4 Browser CSRF Attack

Malicious webpage connects to `ws://127.0.0.1:9876` (no Origin check) → exfiltrates all agent output, spawns malicious agents, or shuts down daemon. No same-origin protection exists.

### 15.5 P0 Mitigations (Must Fix)

| # | Fix | Impact |
|---|-----|--------|
| D1 | Bind WebSocket to `127.0.0.1` by default | Eliminates remote RCE |
| D2 | Provider allowlist for `SpawnAgent` | Blocks arbitrary binary execution |
| D3 | Token-based auth (random token in `~/.voiceterm/auth_token`) | Blocks unauthorized access |
| D4 | Set Unix socket permissions to `0600` | Blocks local users on shared systems |
| D5 | WebSocket Origin validation | Blocks browser CSRF |

---

## 16. Autonomy Self-Modification Safety

### 16.1 Self-Modification Risks

The autonomy system writes to plan documents via `update_plan_doc()`. **Nothing prevents it from modifying its own control files:**
- `AGENTS.md`, `CLAUDE.md` — AI instructions
- `dev/config/control_plane_policy.json` — hard caps and allowlists
- `dev/scripts/devctl/loops/fix_policy.py` — the enforcement code itself

### 16.2 Policy Bypass Vulnerabilities

| Finding | Severity |
|---------|----------|
| `swarm_run` bypasses ALL policy hard caps (no max_rounds/hours/tasks) | HIGH |
| `autonomy-swarm` has zero fix_policy enforcement | HIGH |
| No path restrictions on plan document writes | HIGH |
| Environment variable overrides policy entirely (`*_ALLOWED_PREFIXES`) | HIGH |
| Dead-letter policy fields (`max_comment_updates_per_hour`, `max_attempts_hard_cap`) never enforced | MEDIUM |
| `auto_send` is risk-only, not authority-scoped | MEDIUM |

### 16.3 Required Safety Controls

| # | Control | Priority |
|---|---------|----------|
| S1 | Add fix_policy enforcement to `autonomy-swarm` and `swarm_run` | P0 |
| S2 | Path-restrict `update_plan_doc` to `dev/active/` only | P0 |
| S3 | Immutable-files guard: block autonomy writes to control-plane files | P0 |
| S4 | Replicate hard-cap enforcement in `swarm_run` | P0 |
| S5 | Enforce or remove dead-letter policy fields | P1 |
| S6 | Per-round plan-modification counter with ceiling | P1 |

### 16.4 Code Duplication

- `iso_z()` in 3 files, `slug()` in 2, `resolve_path()` in 3
- `triage/loop_policy.py` and `mutation_loop/policy.py` are near-identical 32-line wrappers

---

## 17. Evidence Pipeline Integrity

### 17.1 Two-Write Atomicity Bug (ALL 12 JSONL Write Sites)

```python
handle.write(json.dumps(row, sort_keys=True))  # call 1
handle.write("\n")                               # call 2  ← concurrent interleave window
```

Under concurrent autonomy writes, rows fuse and are silently dropped on read.
**Fix: `handle.write(json.dumps(row) + "\n")`** — single call, atomic under `PIPE_BUF`.

### 17.2 Missing Integrity Controls

File locking, write-ahead log, per-row checksums, sequence numbers, rotation policy, corruption detection, tamper detection — **all missing** across all 12 JSONL write sites.

### 17.3 Inconsistent Error Handling

`event_store.py` raises `ValueError` on corrupt events (fail-closed) while every other reader silently skips bad rows (fail-open). One corrupt event kills the entire review channel.

### 17.4 Required Fixes

| # | Fix | Priority |
|---|-----|----------|
| E1 | Single-write atomicity (12 sites) | P0 |
| E2 | Centralized `append_jsonl_row()` with file locking | P1 |
| E3 | `check_jsonl_store_integrity` guard | P1 |
| E4 | Unify error handling (consistent fail-open or fail-closed) | P2 |
| E5 | Rotation policy (50MB or 100K rows) | P2 |

---

## 18. Guard System Self-Consistency

### 18.1 The Self-Referential Bug

**`governance_closure` (the meta-guard that validates all other guards) is itself not enforced in CI.** Not in any bundle, workflow, quality policy, or exemption list. If it runs, it flags itself as a violation.

**`daemon_state_parity`** has the same gap — registered but zero enforcement pathway.

### 18.2 True Guard Count: 66

66 registered entries map to 66 files on disk. The 62/64/70 discrepancy is explained by: support modules counted as guards (3), probe support files (3), and differently-scoped counts.

### 18.3 Other Findings

- `function_duplication` and `python_broad_except` not in `_GUARD_CHECKS` — skipped by `bundle.docs` and `bundle.runtime`
- `compat_matrix_smoke.py` breaks `check_*.py` naming convention
- No disk-vs-catalog parity check in the meta-guard

### 18.4 Required Fixes

| # | Fix | Priority |
|---|-----|----------|
| G1 | Add `governance_closure` to `_SHARED_GOVERNANCE_CHECKS` | P0 |
| G2 | Add `daemon_state_parity` to bundle or give exemption | P1 |
| G3 | Add disk-vs-catalog parity check to meta-guard | P1 |

---

## 19. Test Coverage: Deep but Dangerously Narrow

### 19.1 The Coverage Paradox

| Metric | Value |
|--------|-------|
| Overall ratio | 0.77:1 (looks healthy) |
| Production LOC with NO test file | **45,375 (72.1%)** |
| Modules with zero tests | **~230 files** |
| Assertions per test | 3.4 (good quality) |
| End-to-end integration tests | **0** |
| Mock/patch usages | 1,042 (95% mock-based) |

### 19.2 Critical Coverage Gaps

| Subsystem | Test Ratio | Risk |
|-----------|-----------|------|
| watchdog/ | 0.15:1 | Guards AI quality |
| platform/ | 0.09:1 | Contract system |
| quality_feedback/ | 0:1 | Scoring engine |
| autonomy/ (18 files) | 0:1 | Swarm orchestration |
| cli_parser/ | 0:1 | Parser builders |
| commands/ (~60 files) | 0:1 | Most commands |

### 19.3 Required Improvements

| # | Fix | Priority |
|---|-----|----------|
| T1 | Split `test_review_channel.py` (7,829 lines) into 10+ files | P1 |
| T2 | Add watchdog tests (0.15:1 → 0.5:1) | P1 |
| T3 | Add platform contract tests (0.09:1 → 0.5:1) | P1 |
| T4 | Add failure-mode tests (JSONL, subprocess, concurrent access) | P1 |
| T5 | Add boundary integration tests (guard → finding → ledger → feedback) | P2 |

---

## 20. Operator Console: Full Coupling Map

- **27 import sites** across 22 files, pulling 45 symbols from 5 devctl sub-packages
- **10 files** import `VOICETERM_PATH_CONFIG` directly (biggest portability blocker)
- **18 per-agent fields** across 19 files for 3 hardcoded agents
- **No command injection risk** — commands built as Python lists via QProcess
- **Extraction: ~35 of 162 files** need modification (22%)

---

## 21. Complete Action Plan (All 3 Rounds — ~45 Items, 9 Tiers)

### Tier -1: Security (MUST FIX — blocks all network use)
D1-D5: Daemon security (bind loopback, provider allowlist, auth token, socket perms, Origin check)
S1-S4: Autonomy safety (fix_policy enforcement, path restrictions, immutable-files guard, hard caps)

### Tier 0: Evidence Integrity + Feedback Loop
E1: Fix two-write atomicity bug (12 sites)
G1: Add governance_closure to bundles
A1-A4: Close feedback loop (auto-persist findings, wire quality dimensions, AI dashboard, unify identity)

### Tier 1: Compress Bootstrap
A5-A7: bootstrap-context command, tiered context packs, 200-token CLAUDE.md
A8: ConceptIndex generator (after P0 contract freeze)

### Tier 2: Memory & Sessions
A9-A12: session-context, session-end, cross-agent memory, ContextPack port

### Tier 3: Structural Debt
A13-A17: ReviewBridgeState, GrowthGuard base, review channel consolidation, generic from_dict, code fixes

### Tier 4: Simplify Surface
A18-A21: gov 7-command surface, unified output contract, split CI monolith, shared composite action

### Tier 5: Portability
A22-A26: REPO_ROOT resolver, kill default fallback, pip package, gov init, second-repo proof

### Tier 6: Strengthen Black Box
A27-A30: Missing guards (unused imports, secrets, dead code), missing probes, enforce recording, reference history

### Tier 7: Test Hardening
T1-T5: Split monolith, watchdog/platform tests, failure-mode tests, integration tests

---

## Appendix: Complete Audit Summary

| Round | Agents | Focus | Key Finding |
|-------|--------|-------|-------------|
| 1 | 9 | System reconnaissance + 8 layer reviews | Feedback loop not closed, 90.8% bootstrap waste |
| 2 | 5 | Token compression, memory, governance flow, unification, ZGraph | 93.2% token reduction design, 13 disconnected data stores |
| 3 | 7 | Security, safety, integrity, consistency, coupling, tests | **Critical daemon RCE**, autonomy self-modification gaps, 72.1% untested code |
| **Total** | **21 agents** | **19 audit dimensions** | **~45 action items across 9 priority tiers** |
| 4 (Final) | 3 | Plan readiness, specificity validation, MASTER_PLAN merge draft | 71% of items too vague → rewrites produced; 5 new MPs drafted; execution sequencing complete |
| **Grand Total** | **24 agents** | **22 audit dimensions** | **49 action items, implementation-ready for Tier -1 and Tier 0** |

---

# ROUND 4: Implementation Readiness & MASTER_PLAN Integration

*3 agents validated the plan for implementation readiness, rewrote vague items, and drafted the exact MASTER_PLAN merge text.*

---

## 22. Specificity Assessment: 22% Ready → Tier -1/0 Now 100% Ready

Of 49 action items, only 11 (22%) had exact file paths, code changes, and acceptance tests. The validator agent rewrote all Tier -1 and Tier 0 vague items. Here are the implementation-ready rewrites:

### 22.1 Daemon Security Rewrites (D2, D3, D5)

**D2 (Provider Allowlist) — REWRITTEN:**
In `rust/src/bin/voiceterm/daemon/run.rs` at the `DaemonCommand::SpawnAgent` match arm (line 127): add `const ALLOWED_PROVIDERS: &[&str] = &["codex", "claude", "gemini", "cursor"];`. Before `execvp`, validate provider. Store overrides in `~/.voiceterm/provider_allowlist.json`.
*Done when:* spawning `provider: "malicious"` returns an error.

**D3 (Token Auth) — REWRITTEN:**
On first daemon start, generate 32-byte random token, write to `~/.voiceterm/auth_token` with mode 0600. In `ws_bridge.rs`, require first WebSocket message to be `{"auth": "<token>"}`. In `socket_listener.rs`, same for Unix socket.
*Done when:* connecting without token gets disconnected; connecting with correct token succeeds.

**D5 (Origin Validation) — REWRITTEN:**
In `ws_bridge.rs`, during WebSocket upgrade, check `Origin` header. Allow `Origin: null` (non-browser) and `http://127.0.0.1:*` or `http://localhost:*`. Reject all others with HTTP 403.
*Done when:* a test with `Origin: http://evil.com` gets 403.

### 22.2 Autonomy Safety Rewrites (S1, S3, S4, S5, S6)

**S1 (Fix Policy in Swarm) — REWRITTEN:**
In `dev/scripts/devctl/autonomy/swarm_helpers.py` and `run_helpers.py`, import `evaluate_fix_policy` from `loops/fix_policy.py`, call before each agent task. If denied, skip task and log.
*Done when:* `max_rounds=0` in fix_policy causes swarm to exit with "policy denied".

**S3 (Immutable Files Guard) — REWRITTEN:**
Create `dev/scripts/checks/check_autonomy_immutable_files.py`. Define `IMMUTABLE_FILES = ["AGENTS.md", "CLAUDE.md", "dev/config/control_plane_policy.json", "dev/scripts/devctl/loops/fix_policy.py"]`. In `autonomy_run.py` and `run_plan.py`, check before writes. In guard, scan git diff for autonomy commits touching immutable files.
*Done when:* guard passes on clean state, fails when autonomy modifies AGENTS.md.

**S4 (Hard Caps in swarm_run) — REWRITTEN:**
In `dev/scripts/devctl/autonomy/run_helpers.py`, enforce `max_rounds`, `max_hours`, `max_tasks` from `FixPolicy`. Track in loop state, exit when any cap hit.
*Done when:* `max_rounds=2` causes exit after exactly 2 rounds.

**S5 (Dead-Letter Fields) — REWRITTEN:**
In `dev/scripts/devctl/loops/fix_policy.py`, either (a) add enforcement of `max_comment_updates_per_hour` and `max_attempts_hard_cap`, or (b) remove the fields from config.
*Done when:* grep returns 0 matches (removed) or all matches include enforcement.

**S6 (Plan Modification Counter) — REWRITTEN:**
In `dev/scripts/devctl/commands/autonomy_run.py`, after each `update_plan_doc()`, increment counter. `MAX_PLAN_MODS_PER_ROUND = 5`. Reject 6th+ modification.
*Done when:* 6th call in one round gets rejected.

### 22.3 Evidence & Guard Rewrites (E2, E3, G3, A1)

**E2 (Centralized JSONL Writer) — REWRITTEN:**
In `dev/scripts/devctl/jsonl_support.py`, add `append_jsonl_row(path, row)` with `fcntl.flock(LOCK_EX)` and single write. Replace all 7 two-write sites. *Done when:* `grep "handle.write(json.dumps" dev/scripts/devctl/` returns only the centralized function.

**E3 (JSONL Integrity Guard) — REWRITTEN:**
Create `dev/scripts/checks/check_jsonl_store_integrity.py`. Enumerate `.jsonl` under `dev/reports/`. Parse every line. Exit non-zero on any corrupt row. Register in `script_catalog.py`.
*Done when:* injecting malformed line causes guard failure.

**G3 (Disk-vs-Catalog Parity) — REWRITTEN:**
In `check_governance_closure.py`, glob `dev/scripts/checks/check_*.py`, compare to catalog entries. File on disk not in catalog = violation.
*Done when:* adding `check_fake.py` without registering causes failure.

**A1 (Auto-Persist Findings) — REWRITTEN:**
In `python_guard_report.py`, after guard results, call `append_jsonl_row(governance_ledger_path, FindingRecord(...).to_dict())` for each violation. Same in `review_probe_report.py` for probes.
*Done when:* `check --profile ci` with a code_shape violation produces a new row in findings ledger.

---

## 23. MASTER_PLAN Integration Design

### 23.1 New MP Items (5)

| MP | Scope | Priority | Dependencies |
|----|-------|----------|-------------|
| **MP-379** | Daemon security hardening (D1-D5) | P1 | None |
| **MP-380** | Autonomy safety boundaries (S1-S6) | P1 | None |
| **MP-381** | Evidence pipeline integrity (E1-E5, A1-A4) | **P0** | Part of evidence-identity freeze |
| **MP-382** | Guard meta-governance closure (G1-G3) | P0 | Builds on governance_closure guard |
| **MP-383** | Test coverage hardening (T1-T5) | P1 | None |

### 23.2 Items Folding Into Existing MPs

| Existing MP | Audit Items Absorbed |
|-------------|---------------------|
| **MP-377** | A5-A7 (bootstrap compression), A8 (ConceptIndex, P1), A9-A12 (memory), A13 (ReviewBridgeState), A18-A19 (gov surface), A22-A26 (portability), R1-R5, R8, R10-R14, R27-R32 |
| **MP-376** | A14 (GrowthGuard base), A30 (standalone guards), R6, R25 |
| **MP-375** | A28 (missing probes), T5 (probe_test_quality) |
| **MP-355** | A15 (review channel consolidation), R11-R12 |

### 23.3 Immediate Fixes (No MP)

| Fix | Action |
|-----|--------|
| Dead code at `events.py:200` | Delete line |
| `globals()` hack in `common.py:24-41` | Replace with explicit imports |
| Delete `docs_lint.yml` | Remove redundant workflow |
| Hand-rolled base64 in `writer/mod.rs` | Use `base64` crate |
| E1: Two-write atomicity (7 confirmed sites) | Single write call |
| G1: Add `governance_closure` to bundles | One-line bundle_registry change |

### 23.4 INDEX.md Registration

```
| SYSTEM_AUDIT.md | reference | reference-only | MP-379..MP-383 evidence | reviewing audit findings, competitive position, grading |
```

---

## 24. Claude + Codex Collaboration Plan

### 24.1 Role Assignment

**Claude implements (code changes):**
- All immediate fixes (Day 1 morning)
- D1-D5 daemon security (Rust changes)
- S1-S2 autonomy safety (Python)
- G1 bundle_registry fix
- A13 ReviewBridgeState rename
- E1-E2 JSONL atomicity + centralized writer
- A5 bootstrap-context command
- T1 test file split

**Codex reviews (architecture, security, plan):**
- D1-D5 security changes (Rust review)
- S1-S4 safety boundary review
- A14 GrowthGuard base class design
- Plan doc updates (MASTER_PLAN, INDEX.md)

### 24.2 First 48 Hours

**Day 1 (Claude implements, self-validates with `check --profile ci`):**
- Morning: Immediate fixes (R7, R8, R16, E1, G1) — ~3 hours
- Afternoon: D1-D3 (bind loopback, provider allowlist, auth token) — ~3 hours
- End of day: S1-S2 (fix_policy in swarm, path-restrict plan writes) — ~2 hours

**Day 2 (Codex reviews Day 1, Claude continues):**
- Morning: Codex reviews daemon security changes; Claude does D4-D5, S3-S4
- Afternoon: A13 (ReviewBridgeState), E2 (centralized writer)
- End of day: Commit security + integrity slice, update MASTER_PLAN with MP-379, MP-380, MP-381

### 24.3 First Week

| Days | Work | Who |
|------|------|-----|
| 3-4 | A14 (GrowthGuard base class — extract, migrate 5 guards) | Claude implements, Codex reviews design |
| 5 | A1 (auto-persist findings) + T1 (split test monolith) | Claude, parallel |
| 6-7 | A5 (bootstrap-context command — 7-10 hours) | Claude implements |

### 24.4 Handoff Protocol

Use the existing review-channel bridge (`code_audit.md`):
1. Claude implements bounded slice, runs full CI
2. Claude posts diff scope in bridge as "ready for review"
3. Codex reviews via `git diff` and guard output
4. Codex writes findings or promotes via verdict
5. Claude addresses findings, iterates

### 24.5 Risk Mitigations

| Risk | Mitigation |
|------|-----------|
| D1 (bind loopback) may break mobile path | Verify mobile app connection before applying |
| A15 (review channel consolidation) during live use | Defer until current branch merges to develop |
| GrowthGuard (A14) may change pass/fail semantics | Migrate one guard at a time, compare output byte-for-byte |
| Bootstrap compression (A5-A7) may under-inform AI | Keep cold retrieval tier, add fallback in slim CLAUDE.md |
| MASTER_PLAN growing past 2,800 lines | Keep new MP entries minimal (2-3 lines), but integrate accepted audit findings into canonical plan/docs instead of pointing future work at `SYSTEM_AUDIT.md`. |

---

## 25. Dependency Graph

```
PARALLEL (Day 1-2, no dependencies):
  D1-D5 ──── Rust daemon security
  S1-S4 ──── Python autonomy safety
  E1 ──────── JSONL atomicity (7 sites)
  G1 ──────── governance_closure to bundles
  Immediate fixes (R7, R8, R16)

PARALLEL (Day 3-5, after Group 1):
  A13 ──── ReviewBridgeState rename
  A14 ──── GrowthGuard base class ──→ enables A30 (standalone guards)
  E2 ───── centralized writer ──→ enables E3 (integrity guard)
  A1 ───── auto-persist findings ──→ enables A2, A29, A30
  T1 ───── split test monolith

SEQUENTIAL (Week 1-2):
  A2 (wire quality dims) ──→ A3 (AI dashboard) ──→ A7 (slim CLAUDE.md)
  A5 (bootstrap-context) ──→ A6 (tiered packs) ──→ A7
  A4 (unify identity) ─────→ A30 (reference history)

DEFERRED (after P0 contract freeze):
  A8 (ConceptIndex) ─── blocked by MASTER_PLAN:273
  A15 (review channel consolidation) ─── high risk, defer
  A18-A19 (gov surface) ─── product architecture
  A22-A26 (portability chain) ─── depends on contract freeze
  A9-A12 (memory/sessions) ─── depends on contract freeze
```

---

# ROUND 5: Architecture Validation & Deep Feasibility

*4 agents (1 lead + 3 specialized) validated ZGraph compression ratios, guard system extraction readiness, and package separation feasibility against the actual codebase.*

---

## 26. ZGraph Compression: Measured and Validated

### 26.1 Measured Compression Ratios

| Data Domain | Prose Tokens | ZGraph Tokens | Compression |
|-------------|-------------|---------------|-------------|
| Plan authority graph | ~13,000 | ~350 | **37:1** |
| Command surface discovery | ~33,303 | ~100 | **333:1** |
| Module dependency graph | ~8,000 | ~275 | **29:1** |
| Quality scores | ~3,000 | ~120 | **25:1** |
| Guard/probe registry | ~2,361 | ~395 | **6:1** |
| **Total sampled** | **~26,361** | **~1,140** | **~23:1 average** |

At 10:1 average compression across the full 167K-token bootstrap, the load drops from **83% to 8.3%** of a 200K context window.

### 26.2 Rust Memory Studio: Built but Completely Unwired

The Rust memory module (`rust/src/bin/voiceterm/memory/`, 11 files) is production-quality:

| Component | Status |
|-----------|--------|
| `MemoryEvent` envelope (14 fields) | Built, tested |
| `MemoryIngestor` (dual-write: JSONL + in-memory) | Built, tested |
| `MemoryIndex` (HashMap-backed, topic/task/text queries) | Built, tested |
| `JsonlWriter` (append-only, 10MB rotation) | Built, tested |
| `RetrievalQuery` (5 query types with scoring) | Built, tested |
| `ContextPack` (boot/task/hybrid with token budgeting) | Built, tested |
| `SurvivalIndex` (deterministic compaction) | Built, tested |
| SQLite DDL schema (9 tables, FTS5) | Specified, not wired |
| **Runtime integration** | **`#![allow(dead_code)]` — zero callers** |

**Key insight:** The `ContextPack` and `SurvivalIndex` already implement the "database → index → bounded packet" pattern. Token budgeting (`trim_to_budget`), provenance tagging (`PackEvidence`), and query tracing are all there. This is 80% of what `bootstrap-context` needs — but in Rust, disconnected from Python.

### 26.3 Bridge Recommendation: Pure Python, No Rust Dependency

`bootstrap-context` should be a pure Python devctl command composing existing outputs. The Rust Memory Studio remains available for future integration. The bridge is a file (`bootstrap_context.json`), not an API. When Rust activates SQLite later, it consumes the same file via `ingest_event_raw()` — zero Rust changes needed.

### 26.4 Concrete `bootstrap-context` Design

**Module structure:**
```
dev/scripts/devctl/governance/bootstrap_context/
    __init__.py
    collector.py          # Gathers data from existing devctl outputs
    schema.py             # BootstrapContext dataclass + YAML schema
    zgraph_encoder.py     # Encodes graphs into ZGraph notation
    cache.py              # Cache management (git-hash + mtime based)
    renderer.py           # JSON/YAML/Markdown output
```

**Cache invalidation:** `sha256(git-tree-hash + policy-mtime + plan-mtime)`, 5-minute TTL. Falls back to stale cache with `stale: true` flag while regenerating.

**Implementation effort:** 8-12 days across 4 phases (foundation, ZGraph encoder, renderer + integration, measurement + validation).

### 26.5 ZGraph Proof Plan (REQUIRED — Paper Ratios Are Not Proof)

The 23:1 average compression measured in §26.1 is calculated on paper, not proven in code. **Before ZGraph enters the execution plan, it must be proven with real tokenizers, real AI sessions, and real task outcomes.** This follows the eval gate from `memory_studio.md:1410-1417`.

#### Experiment 1: Token Count Validation (2-3 hours)

**Goal:** Prove the compression ratios with a real tokenizer, not the 4-chars/token heuristic.

```python
# dev/scripts/devctl/tests/zgraph/test_compression_ratios.py

import tiktoken  # or anthropic tokenizer

def test_plan_authority_compression():
    """Prove ZGraph compresses the plan authority graph."""
    # Version A: extract the prose from MASTER_PLAN.md status snapshot
    prose = extract_status_snapshot("dev/active/MASTER_PLAN.md")
    prose_tokens = count_tokens(prose)

    # Version B: generate ZGraph from the same data
    zgraph = generate_plan_authority_zgraph("dev/active/MASTER_PLAN.md")
    zgraph_tokens = count_tokens(zgraph)

    ratio = prose_tokens / zgraph_tokens
    assert ratio >= 10, f"Expected 10:1 minimum, got {ratio:.1f}:1"
    # Record: actual ratio, prose tokens, zgraph tokens

def test_command_surface_compression():
    """Prove ZGraph compresses the command surface."""
    prose = read_file("dev/scripts/README.md")
    prose_tokens = count_tokens(prose)

    zgraph = generate_command_map_zgraph()
    zgraph_tokens = count_tokens(zgraph)

    ratio = prose_tokens / zgraph_tokens
    assert ratio >= 50, f"Expected 50:1 minimum, got {ratio:.1f}:1"

def test_guard_registry_compression():
    """Prove ZGraph compresses the guard/probe registry."""
    prose = extract_guard_prose("AGENTS.md")  # the full probe/guard sections
    prose_tokens = count_tokens(prose)

    zgraph = generate_guard_registry_zgraph()
    zgraph_tokens = count_tokens(zgraph)

    ratio = prose_tokens / zgraph_tokens
    assert ratio >= 3, f"Expected 3:1 minimum, got {ratio:.1f}:1"

def test_full_bootstrap_compression():
    """Prove the total bootstrap compresses meaningfully."""
    # Current: CLAUDE.md + AGENTS.md + INDEX.md + MASTER_PLAN.md
    total_prose = sum(count_tokens(read_file(f)) for f in BOOTSTRAP_FILES)

    # Compressed: bootstrap.yaml with ZGraph sections
    bootstrap = generate_bootstrap_context()
    total_compressed = count_tokens(yaml.dump(bootstrap))

    ratio = total_prose / total_compressed
    assert ratio >= 8, f"Expected 8:1 minimum, got {ratio:.1f}:1"
    print(f"Full bootstrap: {total_prose} -> {total_compressed} tokens ({ratio:.1f}:1)")
```

**Acceptance:** All 4 tests pass with real tokenizer. Ratios are recorded as evidence.

#### Experiment 2: Lossless Round-Trip (1-2 hours)

**Goal:** Prove ZGraph is an index, not lossy compression. Every ZGraph symbol must expand back to the original data.

```python
def test_zgraph_roundtrip_plan_authority():
    """Every ZGraph node/edge must resolve to a real plan doc."""
    zgraph = generate_plan_authority_zgraph("dev/active/MASTER_PLAN.md")
    nodes = parse_zgraph_nodes(zgraph)

    for node in nodes:
        # Node references a real MP number
        assert node.id in MASTER_PLAN_MP_NUMBERS
        # Node's plan doc path exists on disk
        if hasattr(node, 'plan_doc'):
            assert Path(node.plan_doc).exists(), f"{node.id} -> {node.plan_doc} missing"

def test_zgraph_roundtrip_guard_registry():
    """Every ZGraph guard node must resolve to a real guard script."""
    zgraph = generate_guard_registry_zgraph()
    nodes = parse_zgraph_nodes(zgraph)

    for node in nodes:
        # Guard ID exists in script_catalog
        assert node.id in REGISTERED_GUARD_IDS
        # Guard file exists on disk
        assert guard_script_path(node.id).exists()
```

**Acceptance:** Every ZGraph symbol resolves to a real file/entity. No orphan symbols, no missing targets.

#### Experiment 3: AI Task Comparison (4-6 hours)

**Goal:** Prove that an AI agent using ZGraph-compressed bootstrap performs at least as well as one reading full prose. This is the eval gate from `memory_studio.md`.

**Protocol:**
1. Define 5 representative tasks:
   - "Which guard catches function length violations?" (command discovery)
   - "What is the current P0 priority?" (plan navigation)
   - "Add a new guard for unused imports" (guard creation)
   - "Fix the code_shape violation in file X" (bounded code fix)
   - "What is the quality trend?" (governance query)

2. Run each task twice:
   - **Control:** Current bootstrap (CLAUDE.md → AGENTS.md → MASTER_PLAN.md, ~132K tokens)
   - **Test:** Compressed bootstrap (bootstrap.yaml + warm pack, ~12K tokens)

3. Measure per task:
   - **Task success** (did the AI complete it correctly? Y/N)
   - **Citation validity** (did the AI reference real files/commands? count valid/invalid)
   - **Unsupported claims** (did the AI hallucinate capabilities that don't exist? count)
   - **Token consumption** (total tokens used including tool calls)
   - **Time to first useful action** (seconds from session start to first code/command)

4. **Pass gate (from memory_studio.md:1410-1417):**
   - Task success: test ≥ control (non-inferior)
   - Citation validity: test ≥ 90% of control
   - Unsupported claims: test ≤ control + 1
   - Token savings: test < 50% of control tokens

**Acceptance:** All 4 gate conditions pass across 5 tasks. If any quality metric regresses beyond non-inferiority bounds, reject ZGraph and fall back to prose compression only (tiered warm/cold loading without symbolic encoding).

#### Experiment 4: Fail-Closed Expansion (1 hour)

**Goal:** Prove the system gracefully degrades when ZGraph symbols can't expand.

```python
def test_stale_zgraph_fallback():
    """When ZGraph references a deleted plan doc, system falls back to warm pack."""
    # Generate bootstrap with current state
    bootstrap = generate_bootstrap_context()

    # Simulate stale state: remove a plan doc
    os.rename("dev/active/ai_governance_platform.md", "/tmp/backup.md")

    try:
        # Expansion should detect the missing file
        expanded = expand_zgraph_references(bootstrap.authority_graph)
        # Should return fallback with warning, not crash
        assert expanded.has_warnings
        assert "ai_governance_platform.md" in expanded.warnings[0]
        assert expanded.fallback_used  # fell back to warm raw chapters
    finally:
        os.rename("/tmp/backup.md", "dev/active/ai_governance_platform.md")
```

**Acceptance:** Missing/stale ZGraph symbols produce warnings and fall back to warm pack, never crash.

#### Summary: ZGraph Proof Checklist

| Experiment | What It Proves | Effort | Gate |
|-----------|---------------|--------|------|
| Token count validation | Compression ratios are real | 2-3h | Ratios ≥ thresholds |
| Lossless round-trip | ZGraph is index, not lossy | 1-2h | 100% symbol resolution |
| AI task comparison | Agent quality preserved | 4-6h | Non-inferior on all 4 metrics |
| Fail-closed expansion | Graceful degradation | 1h | Warnings, not crashes |
| **Total** | | **8-12h** | **All 4 pass** |

**This proof must complete BEFORE `bootstrap-context` ships with ZGraph encoding.** The command can ship with plain YAML compression first (hot/warm/cold tiering from §9.2 already achieves 93% reduction without ZGraph). ZGraph is an optimization on top — valuable if proven, not a blocker.

### 26.6 ZGraph for Code Navigation

Academic validation (LocAgent ACL 2025, CodexGraph NAACL 2025, Code-Craft): graph-based code navigation outperforms similarity-based retrieval by 15.6% because dependency chains are traversable. ZGraph would compress the codebase topology (file → function → dependency) in a way that helps AI navigate without reading everything. The command surface alone achieves **333:1** compression on paper — Experiment 1 above validates this with a real tokenizer.

---

## 27. Guard System: Ready for Extraction with GrowthGuard

### 27.1 Exact Boilerplate Quantification

| Pattern | Files | Occurrences | Lines Wasted |
|---------|-------|-------------|-------------|
| `try/except ModuleNotFoundError` import | 98 | 117 | ~800-1,200 |
| `_render_md()` identical structure | 41 | 41 | ~1,000 |
| `_growth()` identical body | 9 | 9 | ~18 |
| `_has_positive_growth()` identical body | 10 | 10 | ~20 |
| `_is_python_test_path()` identical body | 4+ | 4+ | ~8 |
| `build_parser` / `ArgumentParser` identical | 67 | 67 | ~200 |
| **Total boilerplate** | | | **~2,500-3,500 lines** |

**In a typical growth guard (251 lines), 67.3% is boilerplate, 32.7% is domain logic.**

### 27.2 GrowthGuard Base Class API

```python
class GrowthGuard(ABC):
    @abstractmethod
    def command_name(self) -> str: ...
    @abstractmethod
    def supported_suffixes(self) -> frozenset[str]: ...
    @abstractmethod
    def count_metrics(self, text, *, path, suffix) -> dict[str, int]: ...
    @abstractmethod
    def guidance_text(self) -> str: ...
    # Base handles: imports, parser, path enumeration, growth computation,
    # test-path filtering, report construction, JSON/MD output, exit code
```

**Before/after: `check_facade_wrappers.py`:** 219 lines → 55 lines (75% reduction).
**Across 9 growth guards:** 2,245 → 660 lines = **1,585 lines eliminated (71%)**.
**Base class itself:** ~120 lines.

### 27.3 Self-Hosting Verdict

Running the guard system on its own code would trigger:
- `check_structural_similarity`: 9 growth guards have identical `main()` structures
- `check_function_duplication`: identical function bodies in 9+ files
- `check_code_shape`: 7,829-line test file exceeds hard limit by 12x

**The guards created exactly the patterns they're designed to prevent.** Test files are excluded from shape governance (`_should_skip_test_path`), which is why the 7,829-line test survives. GrowthGuard eliminates the guard-side duplication; splitting the test file eliminates the test-side violation.

### 27.4 Missing Guard Feasibility

| Guard | Feasibility | Approach | Est. LOC |
|-------|------------|----------|----------|
| `check_unused_imports` | **HIGH** | Python `ast`: walk Import nodes, compare to Name nodes. Growth-based. | 150-200 |
| `check_hardcoded_secrets` | **MEDIUM** | Regex for AWS keys, GitHub tokens, OpenAI keys (distinctive prefixes). Hard guard. | 100-150 |
| `check_dead_code_growth` | **LOW** (full), **MEDIUM** (heuristic) | Heuristic: ripgrep for function names with zero cross-file references. Growth-based. | 200-250 |

### 27.5 Decorator-Based Registration

```python
@guard("facade_wrappers", tags=("python", "design"), profiles=("ci", "quick"))
class FacadeWrapperGuard(GrowthGuard):
    def count_metrics(self, text, *, path, suffix): ...
```

Supports pip entry points:
```toml
[project.entry-points."codeguard.guards"]
facade_wrappers = "codeguard.guards.facade_wrappers:FacadeWrapperGuard"
```

Migration: 4 phases — add decorator alongside tuples, migrate one at a time, remove tuples, enable entry-point discovery.

### 27.6 Pattern-to-Guard Pipeline

| Step | Current | With GrowthGuard + Decorator |
|------|---------|----------------------------|
| Write guard | 60-90 min (copy 169 lines boilerplate) | **15-20 min** (only `count_metrics()`) |
| Register | 3 files to edit | **1 line** (`@guard()` decorator) |
| Add to CI | Edit YAML workflow | **Automatic** (registry discovery) |
| Write tests | 30-60 min | **10-15 min** (test `count_metrics()` directly) |
| **Total** | **2-4 hours** | **30-45 minutes** |

---

## 28. Package Separation: 11-Day MVP to `pip install ai-code-gov`

### 28.1 The Critical Portability Gift

**92 guard/probe scripts already support `DEVCTL_REPO_ROOT` env var** via `check_bootstrap.py`. The new package just needs to set this env var before spawning guard subprocesses. This eliminates the need to edit 92 individual files.

### 28.2 Work Count by Change Category

| Change | Files to Edit |
|--------|--------------|
| Replace `Path(__file__).parents[3]` (keystone: `config.py`) | 1 + 16 peripheral + 28 tests = **45** |
| Kill `VOICETERM_PATH_CONFIG` default fallback | **2** (repo_packs/__init__.py, voiceterm.py) |
| Replace hardcoded `dev/scripts/checks/` paths | **2** source-of-truth (script_catalog.py, bundle_registry.py) + 72 test files |
| Make guards accept `--target-dir` | **0** (env var approach works for MVP) |

### 28.3 Minimum Viable Package

```
ai_code_gov/
    config.py               # Git-based root + .governance/policy.json
    policy/                 # Quality policy resolution (5 files)
    runner/                 # Command runner + output helpers (2 files)
    catalog.py              # Guard/probe registry (path-agnostic)
    check/                  # Check orchestrator (6 files)
    guards/                 # 15 portable Python + 12 Rust guards
    probes/                 # 16 portable Python + 8 Rust probes
    bootstrap.py            # Guard bootstrap
    governance/             # draft.py, identity.py, ledger_helpers.py
    runtime/                # project_governance.py, value_coercion.py
    init.py                 # gov init command
    cli.py                  # 8 commands: init, check, probes, policy, draft, report, export, version
```

### 28.4 "First 10 Minutes" Experience

```bash
pip install ai-code-gov                    # 30 seconds
cd ~/my-project && gov init                # 5 seconds → creates .governance/policy.json
gov check                                  # 30-60 seconds → 15 guards + 16 probes
```

Output shows guard pass/fail, probe risk hints with AI instructions, total time. **Under 3 minutes to first results.**

### 28.5 Implementation Effort

| Phase | Work | Days |
|-------|------|------|
| Package skeleton (config, policy, runner, CLI) | 15 new files | 3 |
| Guard/probe extraction | ~73 files | 4 |
| `gov init` + first-run UX | 6 new files | 1.5 |
| Testing + PyPI polish | ~45 files | 2.5 |
| **MVP Total** | | **~11 days** |
| VoiceTerm consumes package (optional follow-up) | ~116 files | 3.5 |

### 28.6 Review Channel: Separate Package

The review channel (58 files) should NOT be in the core `ai-code-gov` package. It's a coordination protocol, not a quality tool. Extract later as `ai-code-gov-review` with ~10 files (bridge reader, event store, heartbeat, peer liveness).

---

## 29. New Architectural Ideas (From Lead Agent)

### 29.1 The "Why Stack" — 500-Token Product Thesis

Every AI session should read this FIRST — before any process instructions:

```
This repo builds a LOCAL-FIRST AI GOVERNANCE PLATFORM. The thesis: prompt
instructions are useful, but executable local control is what makes AI-assisted
engineering reliable. Guards block bad code deterministically. Probes surface
design smells as advisory hints. The governance ledger tracks evidence of
quality improvement over time. The feedback loop closes when quality data
reaches the AI at session start.

Your job: make the AI write better code, then prove it with evidence.
Current quality score: {score}. Trend: {trend}. Active scope: {mp}.
```

**This is why the AI doesn't "get it" without being told every time.** AGENTS.md is 1,300 lines of WHAT and HOW with zero WHY.

### 29.2 Guards Created the Overcomplexity They Prevent

The aggressive function-length limits forced the review channel into 58 micro-files. The system's own guards produced the decomposition pattern they're designed to catch. **Self-hosting enforcement (running guards on guard code) would have caught this.** This should be a CI step once GrowthGuard lands.

### 29.3 Review Channel Needs v2, Not Consolidation

58 → 15 files is wrong. The real answer is 58 → **5 files**: one `ReviewSession` dataclass (authority), one JSONL event log (trace), one markdown renderer (projection), one heartbeat/liveness check, one parser. The current structure is an artifact of incremental development, not architectural necessity.

### 29.4 Session Lifecycle: The Missing Primitive

The system has `guard-run` (one fix), `autonomy-loop` (one cycle), `autonomy-swarm` (multiple loops). But no `session` primitive that captures: what the AI was asked, what it read, what it changed, what guards ran, quality delta, duration. Without this, you can measure code quality but not attribute improvement to specific sessions/agents/strategies.

### 29.5 `@mappable` Decorator

Replace 21 hand-written `*_from_mapping()` functions with:
```python
@mappable
@dataclass(frozen=True, slots=True)
class FindingRecord: ...
```
Eliminates ~500 lines. Prevents mapping/field drift.

### 29.6 Spec vs Reality: ~40% Implemented

`SYSTEM_ARCHITECTURE_SPEC.md` describes contracts (`PlanRegistry`, `PlanTargetRef`, `WorkIntakePacket`, `CollaborationSession`, `MapFocusQuery`) that do not exist as code. The runtime layer covers only `ActionResult`, `Finding`, `DecisionPacket`, `ControlState`, `ReviewState`, `ProjectGovernance`, `FailurePacket`, `RoleProfile`.

---

## 30. Grand Summary — All Rounds

| Round | Agents | Key Contribution |
|-------|--------|-----------------|
| 1 | 9 | System inventory: 5-layer architecture, broken feedback loop, 90.8% waste |
| 2 | 5 | Solution design: 93.2% token reduction, unified pipeline, ZGraph integration |
| 3 | 7 | Failure analysis: critical daemon RCE, autonomy safety gaps, JSONL bugs, 72.1% untested |
| 4 | 3 | Implementation readiness: 71% vague → rewrites, MASTER_PLAN merge draft, sequencing |
| 5 | 4 | Deep validation: measured 23:1 ZGraph compression, GrowthGuard 71% LOC reduction, 11-day pip MVP |
| **Total** | **28 agents** | **49 action items, 9 priority tiers, implementation-ready** |

### The Architecture in One Sentence

**A local-first deterministic governance engine that catches bad AI coding patterns through guards (blocking) and probes (advisory), tracks evidence in a finding ledger, scores quality improvement over time, and compresses its own context to <3K tokens via ZGraph symbolic notation — extractable to any repo via `pip install ai-code-gov`.**
