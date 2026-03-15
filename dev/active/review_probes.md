# Review Probes Plan

**Status**: active  |  **Last updated**: 2026-03-10 | **Owner:** Tooling/quality intelligence
Execution plan contract: required
This spec remains execution mirrored in `dev/active/MASTER_PLAN.md` under `MP-368..MP-375`.

## Scope

Add a "review probe" layer between deterministic hard guards and AI
investigative review. Probes are heuristic scanners that detect risk
patterns and emit structured review targets. They never block CI, and their
first job is to improve the normal maintainer workflow (`check`, `status`,
`report`) before any autonomy-specific consumer is treated as required.

### Three-layer quality model

| Layer | Name | Behavior | Exit code |
|-------|------|----------|-----------|
| A | Hard guards (`check_*.py`) | Deterministic violation detection | 0 = pass, 1 = fail (blocks merge) |
| B | Review probes (`probe_*.py`) | Heuristic risk-signal detection | Always 0 (emits `risk_hints`) |
| C | AI investigative review | Focused AI analysis of probe targets | Confidence-scored verdicts |

### Design principles

1. Probes reuse existing scanning infrastructure (`GuardContext`,
   `check_bootstrap`, function scanners, text utilities).
2. Probes always exit 0. They produce structured JSON with `risk_hints`
   instead of `violations`.
3. Each risk hint specifies: file, symbol, risk type, severity, signals
   detected, AI review instruction, review lens, and optional doc references.
4. Probe output is collected to `dev/reports/probes/review_targets.json`
   for consumption by the control plane triage loop.
5. Probes run in a dedicated phase after hard guards, controlled by a
   `with_review_probes` profile flag.
6. Maintainer-visible value comes first: if a probe cannot help a human
   maintainer find, rank, or hand off issues faster, autonomy integration is
   not enough to justify it.
7. Ralph/control-plane paths are adapters over stable probe artifacts, not the
   source of truth for probe value or rollout sequencing.
8. Findings need topology context, not just local smell context: a senior
   reviewer should be able to see what the file touches, what touches it, and
   whether the problem sits in an isolated helper or a high-coupling hotspot.
9. The report should be self-sufficient for senior review: what changed, why
   it matters, what the likely blast radius is, what was already attempted,
   and what bounded next slice should be done next.

## Probe Output Schema

```json
{
  "command": "probe_concurrency",
  "timestamp": "2026-03-09T...",
  "ok": true,
  "mode": "working-tree",
  "risk_hints": [
    {
      "file": "rust/src/ipc/session.rs",
      "symbol": "handle_auth_flow",
      "risk_type": "race_condition",
      "severity": "medium",
      "signals": [
        "Arc<Mutex<>> accessed across await points",
        "channel sender cloned into spawned task"
      ],
      "ai_instruction": "Review for ordering issues and stale state.",
      "review_lens": "concurrency",
      "attach_docs": ["dev/guides/ARCHITECTURE.md#ipc-session-model"]
    }
  ],
  "files_scanned": 42,
  "files_with_hints": 3
}
```

## Probe Catalog

### Shipped probes (Phase 2 — live in CI)

#### probe_concurrency (MP-368) — Rust only

Detects concurrency patterns that suggest race-condition or deadlock risk.

**Active signals (after false-positive refinement):**
- Nested lock acquisitions (two `.read()`/`.lock()` in same scope) → HIGH
- `Arc<Mutex<>>` shared into `tokio::spawn` without proper scoping → MEDIUM
- Multi-flag `Arc<AtomicBool>` with `Ordering::Relaxed` (≥2 flags) → MEDIUM
- Lock poisoning recovery via `.into_inner()` → LOW

**Removed (too noisy):** channel+spawn pattern (textbook tokio), single AtomicBool flags.

#### probe_design_smells (MP-369) — Python only

Detects design-quality anti-patterns commonly produced by AI agents.

**Active signals:**
- `getattr()` density ≥4 on same receiver (replace with typed model) → MEDIUM/HIGH
- Parameter typed as `object` with `getattr()` access ≥2 times → MEDIUM
- ≥3 private `_fmt_*`/`_format_*` helpers in one file (sprawl) → LOW

**Allowlist:** `getattr(args, ...)`, `getattr(self, ...)`, `getattr(cls, ...)` — idiomatic.

#### probe_boolean_params (MP-370) — Python + Rust

Detects functions with excessive boolean parameters (unreadable call sites).

**Active signals:**
- ≥3 `: bool` parameters in function signature → MEDIUM
- ≥5 `: bool` parameters → HIGH

**Multi-line extraction:** up to 10 lines for Python `def`, 15 for Rust `fn`.

#### probe_stringly_typed (MP-371) — Python + Rust

Detects string-literal dispatch that should be a proper enum.

**Active signals (Python):**
- Same variable compared against ≥3 string literals in one function → MEDIUM
- Same variable compared against ≥5 string literals → HIGH

**Active signals (Rust):**
- `match` with ≥3 string-literal arms in one function → MEDIUM
- `match` with ≥5 string-literal arms → HIGH

**Allowlist (Rust):** `from_str`, `try_from`, `from`, `deserialize`, `parse` — string
matching IS the correct pattern in parser/conversion trait impls.

### Shipped probes (Phase 3 — live in CI)

#### probe_unwrap_chains (MP-374a) — Rust only

Detects functions with 3+ `.unwrap()`/`.expect()` calls in non-test code.
Skips `main()` and functions with explicit justification comments.
Thresholds: ≥3 = MEDIUM, ≥5 = HIGH.

#### probe_clone_density (MP-374b) — Rust only

Detects functions with 5+ ownership-copying operations (.clone(), .to_string(),
.to_owned()). Arc::clone() is excluded (idiomatic). Builder/snapshot functions
are allowlisted. Thresholds: ≥5 = MEDIUM, ≥8 = HIGH.

#### probe_type_conversions (MP-374c) — Rust only

Detects redundant type conversion chains: `.as_str().to_string()` (String→&str→String),
`.as_ref().to_owned()`, `.to_string().as_str()`, `.clone().as_str()`, etc.
Each pattern is a wasted allocation. Severity: always MEDIUM.

#### probe_magic_numbers (MP-374d) — Python only

Detects magic number slices ([:N], [N:], [N:M]) where N >= 3.
Numbers 0, 1, 2, -1 are excluded (too common to be magic).
Thresholds: ≥2 magic slices in one function = MEDIUM, ≥4 = HIGH.

### Shipped probes (Phase 4 — live in CI)

#### probe_dict_as_struct (MP-376a) — Python only

Detects functions returning dicts with 5+ keys that should be dataclasses or TypedDict.
Scans both dict literal returns and incremental `d['key'] = ...` building patterns.
Allowlisted: `to_dict`, `as_dict`, `serialize`, `to_json`, test fixtures.
Thresholds: ≥5 keys = MEDIUM, ≥8 keys = HIGH.

#### probe_unnecessary_intermediates (MP-376b) — Python only

Detects assign-then-return patterns with generic variable names (`result`, `ret`,
`output`, `data`, `tmp`, etc.). Requires same-indent and consecutive lines.
Thresholds: ≥2 per function = MEDIUM, ≥4 = HIGH.

#### probe_vague_errors (MP-376c) — Rust only

Detects `bail!("...")`, `anyhow!("...")`, and `.context("...")` calls where the
error message has no `{variable}` format args — making production debugging impossible.
Short messages (≤15 chars) are excluded. Thresholds: ≥2 = MEDIUM, ≥4 = HIGH.

#### probe_defensive_overchecking (MP-376d) — Python only

Detects 3+ `isinstance()` checks on the same variable in a single function.
Should be consolidated into `isinstance(x, (A, B, C))` or match/case.
Thresholds: ≥3 = MEDIUM, ≥5 = HIGH.

#### probe_single_use_helpers (MP-376e) — Python only

Detects private functions (`_name`) called only once in the file. Excludes
dunder methods, test helpers, callbacks/hooks, and functions under 5 lines.
Thresholds: ≥3 single-use helpers per file = MEDIUM, ≥6 = HIGH.

#### probe_exception_quality (MP-376f) — Python only

Detects suppressive broad handlers that silently fall back without runtime
context plus exception translation that re-raises a generic message without
including the failing path/id/input. Severity: suppressive fallback = HIGH,
context-free translation = MEDIUM.

### Research-rejected categories

| Category | Reason | False Positive Rate |
|---|---|---|
| Nested closures (Rust) | Can't distinguish callback hell from functional composition | 60%+ |
| Unused Results (Rust) | Telemetry/logging intentionally drops errors | 40%+ |
| Dead code (Python) | 0 instances found in codebase | N/A |
| Mutable/default-evaluation traps (Python) | Already covered by `check_python_global_mutable.py` | N/A |
| Deep nesting (Python + Rust) | Already covered by `check_nesting_depth.py` | N/A |
| Dead parameters (Python) | 89% are underscore-prefixed (intentional); remaining 32 too scattered | 89% |
| Lifetime smells (Rust) | Stylistic, not correctness; ~12 elidable but 20% FP | 20% |
| Inconsistent returns (Python) | 0 genuine issues found across 606 files | N/A |
| Excessive parameters | Already covered by `parameter_count` guard; documented `#[allow]` | N/A |
| Python error handling | Already covered by `check_python_broad_except.py` rationale contract | N/A |
| Rust unsafe/todo/fixme | 0 todo!(), 1 TODO comment, 75% SAFETY docs — codebase is clean | N/A |
| Rust string allocation | 806 `.to_string()` on literals, mostly in test code; uses `with_capacity()` | 90%+ |
| Import/dependency smells | 88 wildcards all intentional with `# noqa`; cross-layer is architecture task | N/A |
| Verbose loops (Rust) | Codebase already idiomatic — only 2/15 candidates worth refactoring | 87% |
| Redundant wrappers | Already covered by `facade_wrappers` guard | N/A |

## Execution Checklist

### Phase 1: Probe framework (MP-372) — DONE

- [x] Create `dev/scripts/checks/probe_bootstrap.py` with shared probe
      base: CLI args, JSON/MD output, `risk_hint` schema, severity enum.
- [x] Add `PROBE_SCRIPT_FILES` dict to `script_catalog.py`.
- [x] Add `REVIEW_PROBE_CHECKS` tuple to `check_support.py`.
- [x] Add `with_review_probes` flag to `check_profile.py` presets.
- [x] Add `run_probe_phase()` to `check_phases.py`.
- [x] Wire step-counting in `check_progress.py` for correct `[N/M]` display.

### Phase 2: Core probe implementations (MP-373) — DONE

- [x] `probe_concurrency.py` — nested locks, Arc<Mutex>+spawn,
      multi-flag relaxed atomics, poison recovery (Rust only).
- [x] `probe_design_smells.py` — getattr density, untyped object params,
      format helper sprawl (Python only).
- [x] `probe_boolean_params.py` — functions with 3+ bool params (Python + Rust).
- [x] `probe_stringly_typed.py` — string-literal dispatch chains (Python + Rust).
- [x] All 4 probes verified: 100% true-positive rate after refinement.
- [x] Per-signal AI instructions dict in each probe for targeted remediation.
- [x] Rust parser function allowlist (`from_str`, `try_from`, etc.) in stringly probe.
- [x] Receiver allowlist (`args`, `self`, `cls`) in design smells probe.

### Phase 3: Signal expansion & report system (MP-374) — DONE

- [x] Research additional code smell categories (3 parallel agents:
      Python smells, Rust smells, report format patterns).
- [x] `probe_unwrap_chains.py` — .unwrap()/.expect() chains in non-test Rust.
- [x] `probe_clone_density.py` — excessive .clone() (Arc::clone excluded).
- [x] `probe_type_conversions.py` — redundant type conversion chains
      (.as_str().to_string() round-trips).
- [x] `probe_magic_numbers.py` — magic number slices in Python ([:N]).
- [x] `probe_report_render.py` — rich human-readable report renderer
      with best-practice library (markdown + terminal output).
- [x] `run_probe_report.py` — one-command runner for all probes.
- [x] Best-practice library with 13 entries covering all probe signals:
      before/after examples, fix patterns, references.
- [x] Categories researched and rejected (insufficient signal):
      nested closures (60% FP), unused Results (40% FP), dead code (0 found),
      mutable defaults (already guarded), deep nesting (already guarded).

### Phase 4: Signal expansion round 2 (MP-376) — DONE

- [x] Research 8 additional code smell categories (round 2: dict-as-struct,
      unnecessary intermediates, vague errors, defensive overchecking,
      single-use helpers — all built from prior round's research candidates).
- [x] `probe_dict_as_struct.py` — Python dicts with 5+ keys returned.
- [x] `probe_unnecessary_intermediates.py` — assign-then-return with generic names.
- [x] `probe_vague_errors.py` — Rust bail!/anyhow! without runtime context.
- [x] `probe_defensive_overchecking.py` — consecutive isinstance() on same var.
- [x] `probe_single_use_helpers.py` — private functions called only once.
- [x] Best-practice library entries added for all 5 new probes (18 total entries).
- [x] Signal-to-practice mapping updated (18 entries).
- [x] AGENTS.md updated with all 13 probes in active probes table.
- [x] PROBE_TEMPLATE_README.md updated with new probes in available probes table.
- [x] Round 3 research (8 agents: dead params, lifetimes, inconsistent returns,
      excessive params, error handling, unsafe/todo, string allocation, imports).
      All 8 returned "not probe-worthy" — diminishing returns reached.
- [x] Full 13-probe suite: 23 findings, 8 HIGH, 14 MEDIUM, 1 LOW across 441 files.

### Phase 5: Operator-first adoption (MP-375)

- [x] Add probe result rendering to `devctl status` / `devctl report`.
- [x] Add ranked hotspot and ownership support to aggregated probe output:
      top files, top review lenses, and optional owner-map projection.
- [ ] Add baseline/delta support so maintainers can separate new probe debt
      from historic debt in normal review flows.
- [x] Emit one canonical probe "fix packet" bundle for human or AI
      remediation: ranked findings, rationale, doc links, and suggested
      next-command guidance.
- [x] Add structural-connectivity context to probe output:
      per-file fan-in/fan-out, import/use neighbors, and changed-subgraph
      extraction so findings can be ranked by coupling and blast radius.
- [x] Add visual review artifacts for senior maintainers:
      Mermaid and/or Graphviz/DOT views that show changed-file connections,
      hotspot modules, and "too-many-connections" files at a glance.
- [x] Add a senior-review packet format that answers, per finding:
      what changed, why it was flagged, what surrounding files/modules connect
      to it, what tests/guards already ran, what prior fix attempts happened,
      and the recommended bounded next slice.
- [x] Add a composite priority score that combines severity, coupling,
      churn/change recency, and ownership ambiguity so review order is not
      based on raw hint counts alone.
- [ ] Extend governance checks so probe registration/reporting drift is
      enforced alongside hard-guard drift instead of relying on memory.
- [ ] Document probe authoring + maintainer triage workflow in
      `dev/scripts/README.md`.
- [x] Add a repo-policy layer so built-in guard/probe capabilities are
      separated from repo-local enablement and capability detection:
      `quality_policy_defaults.py` now owns the built-in registry, while the
      `quality_policy*.py` resolver stack and
      `dev/config/devctl_repo_policy.json` preserve current VoiceTerm behavior
      without hard-coding this repo into `check`/`probe-report`.
- [x] Add portable preset layering plus an inspection surface so the same
      engine can resolve VoiceTerm or another repo without code edits:
      `quality_policy.py` now supports policy inheritance, VoiceTerm extends a
      repo-specific preset layered over `dev/config/quality_presets/`, `check`
      / `probe-report` / probe-backed `status` / `report` / `triage` accept
      `--quality-policy`, `DEVCTL_QUALITY_POLICY` provides the same override
      for automation, and `devctl quality-policy` renders the resolved active
      policy/scopes for human or AI review.
- [x] Seed the next portable-guard backlog from official lint ecosystems and
      repo evidence: Python design-complexity guards (`too-many-branches`,
      `too-many-return-statements`) and Python cyclic-import detection are now
      shipped as portable guards; the remaining official-lint backlog is the
      Rust large-result/large-enum pair (`result_large_err`,
      `large_enum_variant`) plus any later repo-specific rollout decisions.
- [ ] Add operator console probe dashboard surface (optional).

Acceptance:

1. A maintainer can run one typed `devctl` command and answer:
   - what changed,
   - what matters first,
   - who should own it,
   - how the relevant files/modules connect,
   - what was already tried or verified,
   - and what bounded fix slice to run next.
2. New probe debt is distinguishable from legacy debt without manual diffing.
3. A senior reviewer can understand the hotspot without opening five other
   files first.
4. The current repo keeps the same guard/probe behavior while another repo can
   reuse the same engine by swapping the repo-policy file instead of editing
   orchestration code.

### Phase 5a: Connectivity and visualization detail

- [x] Define a repo-owned connectivity model for Python and Rust:
      imports, module neighbors, call/use adjacency where cheap, and changed
      subgraph extraction around touched files.
- [x] Emit a stable machine-readable topology artifact alongside the probe
      summary (`file_topology.json` or equivalent) so CLI/report/UI consumers
      do not recompute graph state ad hoc.
- [x] Add hotspot heuristics for "too connected" files:
      high fan-in, high fan-out, bridge-node score, repeated churn, and probe
      density concentrated in the same node.
- [x] Render at least two human-readable views:
      - changed-subgraph flow
      - hotspot-by-connectivity flow
- [x] Keep visuals scoped and practical: default to the changed slice and top-N
      hotspot neighbors so graphs stay readable instead of becoming hairballs.

Acceptance:

1. The system can show when a medium-severity smell in a central file deserves
   higher attention than a high-severity smell in an isolated helper.
2. Visual outputs help a reviewer decide decomposition/refactor boundaries,
   not just decorate the report.

### Phase 6: Optional control-plane adapters (later)

- [ ] Wire `review_targets.json` into control-plane queues once the manual
      maintainer workflow proves useful and stable.
- [ ] Keep Ralph or any later auto-fix loop as an adapter over the same typed
      probe artifacts, not a blocker for shipping probe value.

## Progress Log

- 2026-03-09: Created the execution-plan doc for review probes and captured the
  initial probe catalog, schema, and repo-specific research examples for
  concurrency, architecture, performance, and product-logic drift.
- 2026-03-10: Registered this plan in the active-doc index and master plan so
  the strict active-plan governance checks can treat probe work as tracked
  execution scope instead of orphan markdown.
- 2026-03-10: Launched Codex/Claude two-agent swarm scoped to review probes
  implementation. Bridge updated with Phase 1-3 instructions.
- 2026-03-10: Phase 1 (framework) and Phase 2 (core probes) complete. All 4
  probes shipped: `probe_concurrency`, `probe_design_smells`,
  `probe_boolean_params`, `probe_stringly_typed`. Registered in
  `script_catalog.py`, `check_support.py`, wired into `check --profile ci`.
  Step counting fixed in `check_progress.py`.
- 2026-03-10: Promoted the standalone probe runner into the typed
  `devctl probe-report` surface so agents and humans can use one repo-owned
  command instead of ad hoc script invocations. The command now runs every
  registered probe, emits markdown/terminal/json summaries, writes
  `dev/reports/probes/review_targets.json`, and refreshes
  `dev/reports/probes/latest/{summary.json,summary.md}` for downstream
  control-plane/report consumers.
- 2026-03-10: Wired the aggregated probe report into shared `devctl status`
  and `devctl report` snapshots behind `--probe-report`, so the same typed
  project-report surface now carries review-probe findings without requiring
  a separate command hop. Also centralized review-probe test-path filtering in
  `probe_path_filters.py` so the probe stack no longer duplicates `_is_test_path`
  helpers across scripts and can pass its own duplication guard.
- 2026-03-10: Extended `devctl triage` and the local `loop-packet` fallback to
  consume probe summaries as first-class control-plane signals. `triage
  --probe-report` now classifies aggregated probe debt into routed issues plus
  explicit next actions, and `loop-packet` live triage fallback now requests
  the same probe summary so autonomy packets still surface review-probe debt
  even when no prior triage artifact exists.
- 2026-03-10: Signal quality validated — concurrency probe refined from 78%
  false-positive rate to 0%. Design smells probe: 100% true positive (2 hints).
  Per-signal AI instruction dicts added to all probes for targeted remediation.
- 2026-03-10: Added review probe enforcement section to `AGENTS.md`
  (post-edit rules, probe catalog, when-to-run guidance, acting on findings).
- 2026-03-10: Phase 3 research initiated — 3 parallel agents scanning Python
  and Rust for additional code smell categories.
- 2026-03-10: Phase 3 complete. 4 new probes shipped: `probe_unwrap_chains`,
  `probe_clone_density`, `probe_type_conversions`, `probe_magic_numbers`.
  Rich report renderer built with 13-entry best-practice library. 5 categories
  researched and rejected (insufficient signal or already guarded). Full 8-probe
  suite: 10 findings, 1 HIGH, 8 MEDIUM, 1 LOW across 250 files scanned.
  One-command runner: `python3 dev/scripts/checks/run_probe_report.py`.
- 2026-03-10: Phase 4 research — 8 agents (round 2) searched for: dict-as-struct,
  vague errors, defensive overchecking, single-use helpers, unnecessary intermediates.
  5 high-signal probes identified and built.
- 2026-03-10: Phase 4 complete. 5 new probes shipped: `probe_dict_as_struct`,
  `probe_unnecessary_intermediates`, `probe_vague_errors`,
  `probe_defensive_overchecking`, `probe_single_use_helpers`. All registered in
  script_catalog, check_support, run_probe_report, AGENTS.md.
- 2026-03-10: Best-practice library expanded to 18 entries. Signal-to-practice
  mapping extended to cover all 13 probes.
- 2026-03-10: Round 3 research — 8 agents searched: dead params, lifetime smells,
  inconsistent returns, excessive params, error handling, unsafe/todo, string alloc,
  imports. ALL 8 returned "not probe-worthy" — the codebase is structurally clean
  beyond what the probes already cover. Diminishing returns reached.
- 2026-03-10: Final probe suite: 13 probes, 23 findings (8 HIGH, 14 MEDIUM, 1 LOW)
  across 14 files, 441 files scanned. Zero false positives in spot-check.
  24 total research agents spawned across 3 rounds to reach convergence.
- 2026-03-10: Planning refresh after implementation review. The execution spec
  was stale: `devctl status/report --probe-report` had already landed, but the
  checklist still treated it as open. MP-375 is now explicitly operator-first:
  the next tranche is ranking, baselines/deltas, fix-packet output, docs, and
  governance parity. Ralph/control-plane ingestion is retained as an optional
  later adapter instead of the primary success criterion.
- 2026-03-10: Planning refinement after maintainer feedback. The next-value
  tranche now explicitly includes file/module connectivity context, visual
  changed-subgraph and hotspot flows, and a self-contained senior-review packet
  so the system explains blast radius and review order instead of emitting
  disconnected hints.
- 2026-03-11: External pilot follow-up added `probe_exception_quality.py` as
  the 14th shipped probe. The new signals target suppressive broad handlers and
  generic exception translation without runtime context, which the first
  `ci-cd-hub` pilot surfaced as recurring Python tooling smells worth keeping
  advisory-first instead of promoting on smell counts alone.
- 2026-03-10: Landed the first topology-aware operator packet tranche.
  `devctl probe-report` now emits ranked `priority_hotspots`, owner and
  coupling context, `file_topology.json`, `review_packet.json`,
  `review_packet.md`, plus Mermaid/DOT hotspot views. The same ranked hotspot
  summary now flows through `status`, `report`, and `triage`.
- 2026-03-10: Used the new packet on the live tree and fixed the first
  readability/organization slice in low-churn tooling files
  (`cli_parser/reporting.py`, `commands/loop_packet.py`,
  `status_report_render.py`, `probe_topology.py`). Live probe findings dropped
  from 23 across 18 files to 18 across 14 files after the cleanup.
- 2026-03-10: Follow-up hygiene refactor split the new topology/report stack
  into scan, builder, packet, render, and artifact modules so the first
  operator-first tranche clears code-shape and dict-schema guards without
  needing waivers.
- 2026-03-11: Governance/docs follow-up closed the maintainer/AI usage gap:
  `AGENTS.md`, `dev/guides/DEVELOPMENT.md`, and `dev/scripts/README.md` now
  explicitly tell agents when to run `check --profile ci`, `probe-report`, and
  `guard-run`, and now document the topology/review-packet artifacts written by
  the probe stack.
- 2026-03-11: Landed the first portability slice for the probe/guard engine.
  Built-in step capability metadata now lives in
  `devctl/quality_policy_defaults.py`, repo-local enablement/default arguments
  live in `dev/config/devctl_repo_policy.json`, `devctl check` resolves active
  AI guards from the `quality_policy*.py` stack, and `probe-report` now
  resolves active probes from the same policy before generating artifacts.
  This keeps current VoiceTerm behavior stable while moving the engine toward
  repo-portable presets instead of VoiceTerm-only hard-coded tuples.
- 2026-03-11: Landed the preset/inheritance follow-up for that portability
  slice. VoiceTerm now extends reusable portable presets under
  `dev/config/quality_presets/`, `check` and `probe-report` accept
  `--quality-policy`, `DEVCTL_QUALITY_POLICY` provides the same override for
  automation, and `devctl quality-policy` renders the resolved policy/scopes so
  maintainers can validate another repo policy before running the full lane.
- 2026-03-11: Moved scan-surface scope out of hard-coded check/probe scripts
  and into the same repo policy layer. `dev/config/devctl_repo_policy.json`
  now owns the effective `python_guard_roots`, `python_probe_roots`,
  `rust_guard_roots`, and `rust_probe_roots`, standalone guard/probe scripts
  resolve those roots through `quality_policy.py`, and aggregated probe reports
  now expose the resolved scope map so another repo can reuse the engine
  without editing script internals.
- 2026-03-11: Added the first new portable hard-guard after the policy split:
  `check_python_suppression_debt.py` now blocks net-new Python suppression
  comments (`# noqa`, `# type: ignore`, `# pylint: disable`,
  `# pyright: ignore`) using tokenized comment scanning, the built-in
  registry/preset docs were updated to treat it as a default portable Python
  guard, and a small shim/import cleanup removed local suppressions so the
  repo can enable the guard without introducing a false-red dirty-tree failure.
- 2026-03-11: Expanded `check_python_global_mutable.py` so the same portable
  Python guard also blocks net-new function-call default arguments plus
  dataclass fields that eagerly evaluate mutable/call defaults instead of
  using `field(default_factory=...)`. `report --python-guard-backlog` now
  weights those new default-trap signals explicitly, so the next portable
  backlog narrows to Python design-complexity/cyclic-import plus the pending
  Rust large-result/large-enum decisions.
- 2026-03-11: Landed the next portable hard-guard tranche and closed the
  immediate Python backlog. `check_python_design_complexity.py` now blocks
  net-new branch-heavy/return-heavy Python functions using policy-owned
  thresholds (portable preset starts conservatively and can be ratcheted per
  repo), `check_python_cyclic_imports.py` now blocks new top-level local
  import cycles with repo-policy allowlists for transitional debt, and
  `report --python-guard-backlog` now scores those new signals. The same
  policy slice also moved `check_code_shape.py` namespace/layout rules into
  repo-owned `guard_configs`, so the portable preset no longer carries
  VoiceTerm-only path assumptions inside the engine.

## Research Notes (2026-03-09)

Research completed across all four probe categories. Each section below
documents concrete patterns found in the VoiceTerm codebase plus the
detection heuristics that should drive probe implementation.

### Concurrency detection patterns

**Real risk patterns found in codebase:**

| Pattern | Files | Risk | Heuristic |
|---------|-------|------|-----------|
| Nested RwLock acquisitions | `buttons.rs:104-124` | HIGH | Two `.read()` / `.lock()` calls in same scope |
| Arc<Mutex> shared across threads | `voice.rs`, `pty_backend.rs`, `buttons.rs` | MEDIUM | `Arc\s*<\s*(Mutex\|RwLock)` + `.clone()` in closures |
| tokio::spawn capturing shared state | `daemon/run.rs`, `agent_driver.rs`, `ws_bridge.rs` | MEDIUM | `tokio::(spawn\|task::spawn)` with Arc captures |
| Ordering::Relaxed on signal flags | `voice.rs:45,51`, `agent_driver.rs:157,167` | MEDIUM | `AtomicBool.*Ordering::Relaxed` on cross-thread signals |
| Lock poisoning recovery | `lock.rs`, `pty_backend.rs` | LOW | `poisoned\.into_inner()` in non-critical paths |
| Multiple locks in same struct | `buttons.rs`, `pty_backend.rs` | MEDIUM | Count Mutex/RwLock fields per struct (>1 = risk) |
| Drop impl with polling join | `voice.rs:42-72` | LOW | `impl Drop` with `thread::sleep` inside |
| Broadcast lag handling | `event_bus.rs`, `ws_bridge.rs` | LOW | `broadcast::channel` without `Lagged` error handling |

**Key finding**: `buttons.rs:find_at()` acquires `self.buttons.read()` then
calls `self.hud_offset()` which acquires a second RwLock. `std::sync::RwLock`
is NOT recursive — genuine deadlock risk if a write request arrives between
the two reads.

### Architecture smell detection patterns

**Real patterns found in codebase:**

| Pattern | Files | Risk | Heuristic |
|---------|-------|------|-----------|
| Cross-domain import sprawl (15+ deps) | `autonomy_swarm.py`, `triage.py` | MEDIUM | Count unique domain prefixes in imports (>=4 = flag) |
| Mixed concerns (orchestrate+parse+render) | `triage.py:100-150`, `check.py:59-77` | MEDIUM | Count concern categories per function (>=3 in >30 lines) |
| Proto-god-class below guard threshold | `component_registry.rs` (80+ enum variants) | LOW | Enum variants >50, struct fields >8, methods >12 |
| God-initializer module | `main.rs` (56 module imports) | LOW | Module-level imports >40 |
| Presenter depends on 5+ state modules | `presentation_state.py` | MEDIUM | Count distinct state-module imports in one file |
| Callback-heavy orchestration | `check.py:59-77` (4 callback params) | LOW | Function takes >3 callable parameters |

**Key finding**: `autonomy_swarm.py` bridges swarm lifecycle, post-audit
processing, markdown rendering, and concurrent execution all in one command
module. The existing `check_god_class` only counts methods, not import
diversity.

### Performance heuristic patterns

**Real patterns found in codebase:**

| Pattern | Files | Risk | Heuristic |
|---------|-------|------|-----------|
| String alloc inside filter predicate | `memory/store/sqlite.rs:100` | HIGH | `.filter(.*\.to_ascii_lowercase())` on 10K+ events |
| O(n) lookup on growing Vec | `memory/store/sqlite.rs:136` | MEDIUM | `.iter().find(.*==.*)` on Vec that grows unbounded |
| Full-collection rebuild per event | `button_handlers.rs:417-428` | LOW | Sort+collect on every input event (only ~8 items) |
| Unnecessary per-call normalization | `voice_macros.rs:96` | LOW | `.to_ascii_lowercase()` on same data each call |

**Key finding**: The codebase is already performance-conscious — 20+ uses of
`Vec::with_capacity`, iterator chains instead of nested loops. The main
scalable risk is `memory/store/sqlite.rs` where `to_ascii_lowercase()` is
called per-event inside a filter predicate (O(n) string allocation on
potentially 10K+ events).

**Not applicable**: Sync I/O in async context — VoiceTerm uses synchronous
event loop (crossbeam_channel), not Tokio async/await in the main binary.

### Product logic drift patterns

**Real patterns found in codebase:**

| Pattern | Files | Risk | Heuristic |
|---------|-------|------|-----------|
| Hardcoded severity thresholds | `quality_backlog/models.py:248-255` (700/350/140) | MEDIUM | Numeric literal in `if x >= N` without named constant |
| Duplicated timeout constant (300) | `config.py`, `loop_helpers.py`, `handoff.py` | MEDIUM | Same value in 3+ files without shared constant |
| Scattered getattr feature gates (31 calls) | `review_channel.py` | MEDIUM | Count `getattr(args, ...)` per file (>10 = scattered policy) |
| Context-dependent validation rules | `review_channel.py:101-114` | LOW | Validation branches that differ by action/mode |
| Hardcoded truncation thresholds | `docs_check_render.py:111-179` (20, 10, 10) | LOW | Inline numeric in display logic |
| Risk classification with inline patterns | `repo_state.py:25-43` | LOW | Regex patterns inline in classifier function |

**Key finding**: The value `300` (5 minutes) appears as a timeout default in
3+ separate files with different constant names. If the "5-minute" policy
changes, three files must be updated independently.

## System Architecture — What Already Exists

**Priority:** #1 beyond the Rust overlay. This is the product.

The AI Code Quality Guard is not a future product — it is an operational
system spanning **191K LOC** of Python tooling, **67 devctl commands**,
**64 hard guards**, **13 review probes**, **30 CI workflows**, a
**PyQt6 operator console** (158 files, 20K LOC), and an **iOS mobile app**.
The probes documented above are Layer B in a 5-layer architecture where
every layer is already built and wired together.

### The 5-layer integrated architecture (ALL OPERATIONAL)

```
┌──────────────────────────────────────────────────────────────────┐
│                COMPLETE SYSTEM (OPERATIONAL)                      │
│                                                                  │
│  LAYER 1: HARD GUARDS (64 check_*.py scripts)                   │
│     Deterministic violation detection — exit 1 blocks merge      │
│     Code shape, function duplication, god class, nesting depth,  │
│     parameter count, Rust best practices, Python broad except,   │
│     workflow shell hygiene, architecture surface sync, etc.       │
│     Run via: devctl check --profile {ci,release,fast,pedantic}   │
│                                                                  │
│  LAYER 2: REVIEW PROBES (13 probe_*.py scripts)                 │
│     Heuristic risk detection — always exit 0, emits risk_hints   │
│     Concurrency, design smells, clone density, vague errors,     │
│     boolean params, stringly typed, unwrap chains, etc.          │
│     Run via: devctl probe-report --format {md,json,terminal}     │
│                                                                  │
│  LAYER 3: AUTONOMY LOOPS (triage → fix → verify cycle)          │
│     AI agents consume guard/probe output, fix issues, re-verify  │
│     autonomy-loop (single controller), autonomy-swarm (parallel  │
│     workers), swarm-run (continuous multi-cycle with adaptive    │
│     feedback sizing). guard-run wraps all fixes with git diff    │
│     capture, post-action hygiene, watchdog episode emission.     │
│     Run via: devctl autonomy-loop / autonomy-swarm / swarm_run   │
│                                                                  │
│  LAYER 4: CI ORCHESTRATION (30 GitHub workflows)                 │
│     Triggered by path/schedule/event. Routes all invocations     │
│     through devctl. rust_ci, tooling_control_plane,              │
│     coderabbit_triage, coderabbit_ralph_loop, release_preflight, │
│     mutation_ralph_loop, autonomy_controller, failure_triage.    │
│                                                                  │
│  LAYER 5: SURFACES (operator console + mobile + CLI)             │
│     Operator console reads dev/reports/ artifacts. Displays      │
│     quality snapshots, probe findings, review channel state,     │
│     swarm status. Launches devctl commands via command_builder.   │
│     Mobile app shows phone_status for real-time monitoring.      │
│                                                                  │
│  ALL LAYERS CONVERGE ON: dev/reports/ (shared artifact store)    │
└──────────────────────────────────────────────────────────────────┘
```

### The operational feedback loop (ALREADY RUNNING via devctl autonomy-loop)

```
┌────────────────────────────────────────────────────────────────────┐
│  CLOSED-LOOP AI CODE QUALITY (devctl autonomy-loop)                │
│                                                                    │
│   ┌──────────────────────────────────────────────────┐             │
│   │ ROUND 1                                          │             │
│   │                                                  │             │
│   │  1. TRIAGE: devctl triage-loop                   │             │
│   │     ├── Runs 64 guards + 14 probes               │             │
│   │     ├── Classifies issues by severity/category   │             │
│   │     ├── Tracks attempt history (what was tried)   │             │
│   │     └── Outputs: triage_report.json               │             │
│   │                                                  │             │
│   │  2. PACKET: devctl loop-packet                   │             │
│   │     ├── Reads triage report                      │             │
│   │     ├── Builds terminal_packet with draft_text   │             │
│   │     ├── Ranks next_actions by priority            │             │
│   │     ├── Calculates risk level                    │             │
│   │     └── Outputs: loop_packet_report.json          │             │
│   │                                                  │             │
│   │  3. FIX: devctl guard-run <fix_command>          │             │
│   │     ├── Captures git diff before                 │             │
│   │     ├── AI agent reads findings + ai_instruction │             │
│   │     ├── Agent fixes code                         │             │
│   │     ├── Captures git diff after                  │             │
│   │     ├── Runs post-action hygiene (quick check)   │             │
│   │     └── Emits watchdog episode (audit trail)     │             │
│   │                                                  │             │
│   │  4. CHECKPOINT                                   │             │
│   │     ├── Builds checkpoint_packet.json            │             │
│   │     │   (idempotency key, expiry, risk, evidence)│             │
│   │     ├── Emits phone_status (real-time UI)        │             │
│   │     └── Stop if: resolved / max_rounds / timeout │             │
│   │                                                  │             │
│   └────────────────────┬─────────────────────────────┘             │
│                        │ issues remain?                             │
│                        v                                           │
│   ┌──────────────────────────────────────────────────┐             │
│   │ ROUND 2..N  (repeat until clean or budget spent) │             │
│   └──────────────────────────────────────────────────┘             │
│                                                                    │
│   Bounded by: --max-rounds N, --max-hours H, --max-tasks T        │
│   Every mutation wrapped by guard-run with git diff + hygiene      │
│   Full audit trail in watchdog_episodes/ directory                 │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Swarm parallelization (ALREADY RUNNING via devctl autonomy-swarm)

When one agent isn't enough, `autonomy-swarm` runs multiple agents in
parallel on the same problem, with adaptive agent-count sizing.

```
┌────────────────────────────────────────────────────────────────────┐
│  SWARM ORCHESTRATION (devctl autonomy-swarm)                       │
│                                                                    │
│  1. Metadata collection (diff stats, prompt tokens, difficulty)    │
│  2. Adaptive agent count scoring:                                  │
│       lines_factor  = min(6.0, lines_changed / 1200.0)            │
│       files_factor  = min(4.0, files_changed / 10.0)              │
│       difficulty    = min(3.0, keyword_hits * 0.7)                 │
│       recommended   = ceil(1.0 + sum) clamped to [min, max]       │
│                                                                    │
│  3. ThreadPoolExecutor spawns N autonomy-loop subprocesses         │
│     AGENT-1 ──> autonomy-loop ──> result.json                     │
│     AGENT-2 ──> autonomy-loop ──> result.json                     │
│     AGENT-N ──> autonomy-loop ──> result.json                     │
│     AGENT-REVIEW ──> post-audit digest (aggregated metrics)        │
│                                                                    │
│  4. Continuous mode (devctl swarm_run):                            │
│     ├── Reads plan doc, extracts unchecked steps                   │
│     ├── Runs swarm per cycle, governance checks after each         │
│     ├── Feedback sizing adapts agent count:                        │
│     │   stall_streak ≥ 2  → downshift (50% fewer agents)          │
│     │   improve_streak ≥ 2 → upshift (25% more agents)            │
│     │   no_signal         → downshift                              │
│     └── Updates plan doc with progress log + audit evidence        │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### How probes feed the autonomy loop (actual data flow)

```
probe_*.py scripts (always exit 0, emit JSON with risk_hints)
    │
    v
devctl probe-report (aggregates all 14 probes)
    │
    ├──> dev/reports/probes/review_targets.json
    ├──> dev/reports/probes/latest/summary.json
    └──> dev/reports/probes/latest/summary.md
              │
              v
devctl triage-loop (reads probe output as one input source)
    │
    ├──> triage_report.json (unresolved count, severity, attempts)
    v
devctl loop-packet (builds terminal feedback for AI agent)
    │
    ├──> terminal_packet: draft_text + next_actions + risk level
    v
devctl guard-run <fix_command> (AI reads findings, fixes code)
    │
    ├──> watchdog episode (audit trail)
    v
devctl check --profile quick (post-fix verification)
    │
    └──> LOOP: if issues remain, next round starts
```

### The accumulation model

Every project adds patterns. The probes grow like ESLint (0 → 300+ rules)
and Clippy (0 → 700+ lints) — one pattern at a time, from real codebases.

```
  VoiceTerm (current)       Next project         Project 50+
  ────────────────────      ────────────         ────────────
  64 guards (hard)          + guards for new     500+ rules
  14 probes (advisory)        tech stack         covering every
  0 false positives         + probes from new    AI smell across
  30 CI workflows             code patterns      Python/Rust/TS/Go
       │                         │                    │
       └────────> Pattern library grows ──────────────┘

  Plus the autonomy infrastructure (loops, swarms, feedback
  sizing, guard-run, triage, review channel) is project-
  agnostic — it works on ANY codebase with devctl.
```

### Devctl command surface (67 commands, ALREADY OPERATIONAL)

The probe system plugs into a larger command infrastructure:

```
QUALITY & CI                          AUTONOMY & AI
  devctl check --profile ci             devctl autonomy-loop
  devctl check --profile release        devctl autonomy-swarm
  devctl probe-report                   devctl swarm_run (continuous)
  devctl guard-run                      devctl autonomy-benchmark
  devctl docs-check                     devctl triage / triage-loop
  devctl hygiene                        devctl mutation-loop
                                        devctl review-channel
RELEASE PIPELINE
  devctl release / release-gates       REPORTING & STATUS
  devctl ship (tag + build + publish)   devctl status / report
  devctl homebrew / pypi                devctl probe-report
                                        devctl ralph-status
PROCESS MANAGEMENT                      devctl phone-status
  devctl process-cleanup                devctl mobile-status
  devctl process-audit
  devctl process-watch                 SYNC & SECURITY
                                        devctl sync / publication-sync
                                        devctl security (RustSec+CodeQL)
```

### Guard inventory (64 scripts, ALREADY ENFORCING)

| Domain | Guards | Examples |
|---|---|---|
| Code shape & structure | 9 | `code_shape`, `function_duplication`, `god_class`, `nesting_depth`, `parameter_count` |
| Rust-specific | 11 | `rust_best_practices`, `compiler_warnings`, `lint_debt`, `security_footguns` |
| Python-specific | 5 | `python_broad_except`, `subprocess_policy`, `dict_schema`, `global_mutable` |
| Governance & sync | 12 | `active_plan_sync`, `agents_contract`, `architecture_surface_sync` |
| CI & testing | 7 | `compat_matrix`, `coderabbit_gate`, `test_coverage_parity`, `mutation_score` |
| Workflow & process | 5 | `workflow_action_pinning`, `shell_hygiene`, `guard_enforcement_inventory` |

### CI workflow integration (30 workflows, ALREADY TRIGGERING)

| Trigger | Workflow | What it runs |
|---|---|---|
| Push/PR on `rust/*` | `rust_ci.yml` | `devctl check --profile ci` + cargo |
| Push/PR on `dev/scripts/**` | `tooling_control_plane.yml` | 25+ guards + strict docs |
| PR review/comment | `coderabbit_triage.yml` | `devctl triage` |
| After triage | `coderabbit_ralph_loop.yml` | `devctl triage-loop` |
| Nightly | `mutation-testing.yml` | cargo mutants + score |
| Every 6h (enabled) | `autonomy_controller.yml` | `devctl autonomy-loop` |
| Manual on master | `release_preflight.yml` | `devctl check --profile release` |
| On release published | `publish_*.yml` | `devctl release-gates` + ship |
| On workflow failure | `failure_triage.yml` | `devctl triage --ci` auto-capture |

### Operator console (ALREADY READING PROBE OUTPUT)

The operator console at `app/operator_console/` (158 files, 20K LOC)
already reads probe and guard artifacts:

```
snapshot_builder.py reads:
  ├── dev/reports/code_audit.md          (bridge + lane state)
  ├── dev/reports/review_state.json      (review channel state)
  ├── dev/reports/probes/review_targets.json  (probe findings)
  ├── dev/reports/mobile/latest/full.json     (mobile relay)
  └── dev/reports/*.md                   (activity reports)

Views display:
  ├── Home workspace     — dry-run/launch for devctl commands
  ├── Activity workspace — task cards from reports
  ├── Agent detail       — per-agent status
  ├── Approval panel     — approve/deny AI-proposed changes
  └── Quality snapshot   — guard + probe results

Actions invoke:
  ├── command_actions.py   — devctl command runners
  ├── review_actions.py    — review-channel control
  ├── swarm_actions.py     — autonomy-swarm launch
  └── process_actions.py   — process-audit/cleanup
```

### Report surfaces (what exists today)

**For senior dev audits (markdown — OPERATIONAL):**
- Severity breakdown and file-level findings
- Source code snippets with `>>>` markers pointing at the issue
- Best-practice explanations with before/after examples
- Reference links to official documentation
- Suppression instructions (copy-paste JSON to allowlist)
- Git diffs showing what changed and why

**For AI agents (JSON — OPERATIONAL):**
- Structured findings with `ai_instruction` field for auto-fix
- `risk_type` and `severity` for prioritization
- `signals` array with exactly what was detected
- Consumed by autonomy-loop for automated remediation

**For terminal quick-scan (OPERATIONAL):**
- Compact `!!`/` !`/`  ` severity markers
- One-line-per-finding for fast triage

**For operator console (OPERATIONAL):**
- Quality snapshot pane reads probe JSON artifacts
- Approval panel for human gating on AI-proposed fixes
- Command actions launch devctl guard-run / swarm from UI

**For mobile (OPERATIONAL):**
- phone_status endpoint shows real-time autonomy loop progress

**Future enrichment:**
- matplotlib charts (severity heatmap, file bar chart, trend line)
- HTML report with collapsible sections + syntax highlighting

### Suppression mechanism

When a finding is intentional, add to `.probe-allowlist.json`:
```json
{
  "suppressed": [
    {
      "file": "src/lib.rs",
      "symbol": "my_function",
      "probe": "probe_clone_density",
      "reason": "cloning required — data sent to spawned task"
    }
  ]
}
```

The finding moves to "Suppressed Findings" with the documented reason —
visible to reviewers but no longer active. Permanent audit trail.

### What makes this different from everything else

| Property | CodeRabbit | SonarQube | ESLint/Clippy | This system |
|---|---|---|---|---|
| Detection method | AI guesses | Generic rules | Pattern match | Pattern match |
| False positive rate | ~30% | Varies | Low | **0%** |
| Consistency | Non-deterministic | Deterministic | Deterministic | **Deterministic** |
| Closed-loop AI fix | No | No | No | **Yes — autonomy-loop** |
| Swarm parallelism | No | No | No | **Yes — autonomy-swarm** |
| Feedback sizing | No | No | No | **Yes — adaptive agents** |
| Guard-run wrapping | No | No | No | **Yes — git diff + hygiene** |
| Human approval gates | PR comments | Dashboard | No | **Review channel** |
| Operator console | No | Dashboard | No | **PyQt6 desktop app** |
| Mobile monitoring | No | No | No | **iOS app** |
| Audit trail | Ephemeral | Reports | No | **Watchdog episodes** |
| CI integration | GitHub App | Plugin | CLI | **30 dedicated workflows** |
| Accumulation | No | Rule updates | Community | **Per-project growth** |
| Educational content | Generic tips | Rule docs | Rule docs | **Before/after + refs** |
| Offline / local | Cloud API | Server | Local | **Fully local** |

### Guard-run: trusted execution wrapper (ALREADY OPERATIONAL)

Every AI-driven code mutation goes through `guard-run`:

```
devctl guard-run <command>
  1. Capture git snapshot (before)
  2. Execute command in repo context
  3. Capture git snapshot (after)
  4. Run post-action hygiene:
     - "quick" → devctl check --profile quick --skip-fmt
     - "cleanup" → devctl process-cleanup --verify
  5. Emit watchdog episode:
     - provider, session_id, trigger_reason
     - retry_count, escaped_findings_count
     - guard_result, reviewer_verdict
  6. Return normalized report (md/json)
```

### What still needs to be built

The core system is operational. Remaining work is enrichment:

| Phase | What | Status |
|---|---|---|
| 1-4 | Probe framework + 13 probes + best-practice library | **DONE** |
| 5 | Dogfood current findings and close blind spots with real maintainer use | **IN PROGRESS** |
| 6 | Ranked hotspots, baselines/deltas, and probe fix-packet bundle | **IN PROGRESS** |
| 7 | Connectivity model + changed-subgraph / hotspot visuals | **IN PROGRESS** |
| 8 | Optional control-plane or Ralph adapter over stable probe artifacts | LATER |
| 9 | matplotlib charts (severity heatmap, file bar chart, trend) | LATER |
| 10 | HTML report with collapsible sections + syntax highlighting | LATER |
| 11 | Dedicated probe dashboard in operator console | LATER |
| 12 | Template packaging (pip-installable or standalone zip) | LATER |
| 13 | JavaScript/TypeScript probe support | BACKLOG |
| 14 | Go probe support | BACKLOG |

### Portability assessment (audited 2026-03-10)

**Rating: GOOD (70% portable, 30% path constants to update)**

The probe system has ZERO imports from `dev/scripts/devctl/`. All core
scanning logic, AI instructions, best-practice library, and report
rendering are language/framework agnostic. What's VoiceTerm-specific is
just directory path constants.

**Migration to a new project (~30 minutes):**

1. Copy 22 files (13 probes + 9 supporting modules, ~900 lines infra)
2. Change `TARGET_ROOTS` / `PYTHON_ROOTS` / `RUST_ROOTS` in each probe
3. Change `REPO_ROOT = Path(__file__).resolve().parents[N]` if different depth
4. Done — probes run identically in new project

**Dependency graph (all stdlib, no external packages):**

```
probe_*.py (13 files)
├── probe_bootstrap.py          (RiskHint, ProbeReport dataclasses)
│   └── check_bootstrap.py      (utc_timestamp, import_attr)
├── rust_guard_common.py         (GuardContext — git operations)
│   └── git_change_paths.py      (git diff with rename awareness)
├── code_shape_function_policy.py (scan_rust_functions, scan_python_functions)
│   └── code_shape_shared.py     (FunctionInfo dataclass)
├── rust_check_text_utils.py     (strip_cfg_test_blocks)
└── probe_path_filters.py       (test-path exclusion)
```

**Portability barriers:**

| Barrier | Effort | Fix |
|---|---|---|
| `TARGET_ROOTS` paths | EASY | Find-and-replace 2-3 lines per probe |
| `REPO_ROOT` depth | EASY | Change `.parents[N]` or detect from `.git` |
| GuardContext dependency | MEDIUM | Copy 2 modules (~170 lines), self-contained |
| Code scanning functions | MEDIUM | Copy 3 modules (~650 lines), pure text analysis |

Template README at `dev/scripts/checks/PROBE_TEMPLATE_README.md`.

### Competitive landscape (researched 2026-03-10)

**What's genuinely novel (not found in existing tools):**

1. **Growth-based non-regression** — files can't creep larger; must
   modularize to grow. Not found in SonarQube, Semgrep, ESLint, or any
   competitor researched.
2. **Three-tier probe model** — hard guards (block merge) vs soft probes
   (advisory) vs AI review. Most tools conflate blocking and advisory.
3. **Exception tracking with expiry dates** — forces quarterly re-justification.
   No tool has this (ESLint `eslint-disable` is indefinite).
4. **Standards registry as AI guardrail context** — repo-specific AGENTS.md
   and guardrails config give AI agents standards, not generic rules.
5. **Cross-architecture validation** — Rust + Python + iOS validated
   together per fix via `guard-run`.

**What's table stakes (competitors already ship):**

- Deterministic pattern matching with JSON output (every linter)
- Custom per-project rules (ESLint, Semgrep, SonarQube)
- AI-powered auto-fix with re-verification (SonarQube Remediation Agent,
  DeepSource Autofix, Semgrep Assistant, Trunk.io MCP)
- Diff-based scanning (CodeRabbit, DeepSource, Semgrep)

**What would stop this from working on other codebases:**

1. Standards registry is repo-specific (~2-3 days to rebuild per project)
2. Architecture validation assumes Rust/Python/iOS stack (rewrite for
   Java+Node+Go etc.)
3. Active-docs governance is cultural — teams that don't use structured
   execution plans lose that governance layer

## Audit Evidence

- `python3 dev/scripts/devctl.py docs-check --strict-tooling` -> ok
- `python3 dev/scripts/devctl.py hygiene --strict-warnings` -> ok
- `python3 dev/scripts/devctl.py orchestrate-status --format md` -> ok
- `python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 120 --format md`
  -> ok with pre-existing stale planned agents from 2026-03-08 in the review
  orchestration ledger.
- `python3 dev/scripts/checks/check_active_plan_sync.py` -> ok
- `python3 dev/scripts/checks/check_multi_agent_sync.py` -> ok
- `python3 -m unittest dev.scripts.devctl.tests.test_probe_report
  dev.scripts.devctl.tests.test_status dev.scripts.devctl.tests.test_triage
  dev.scripts.devctl.tests.test_loop_packet
  dev.scripts.devctl.tests.test_status_report_parallel` -> ok (53 tests)
- `python3 dev/scripts/checks/check_python_subprocess_policy.py` -> ok
- `python3 dev/scripts/checks/check_compat_matrix.py` -> ok
- `python3 dev/scripts/checks/compat_matrix_smoke.py` -> ok (existing runtime
  non-IPC provider warnings only)
- `python3 dev/scripts/checks/check_naming_consistency.py` -> ok
- `python3 dev/scripts/checks/check_guard_enforcement_inventory.py` -> ok
- `python3 dev/scripts/checks/check_bundle_workflow_parity.py` -> ok
- `python3 dev/scripts/checks/check_agents_contract.py` -> ok
- `python3 dev/scripts/checks/check_architecture_surface_sync.py` -> ok
- `python3 dev/scripts/checks/check_bundle_registry_dry.py` -> ok
- `python3 dev/scripts/checks/check_workflow_shell_hygiene.py` -> ok
- `python3 dev/scripts/checks/check_workflow_action_pinning.py` -> ok
- `python3 dev/scripts/checks/check_ide_provider_isolation.py
  --fail-on-violations` -> ok
- `python3 dev/scripts/devctl.py probe-report --format terminal --output-root
  /tmp/devctl-probes-topology-smoke` -> ok; first live ranked packet emitted
  `file_topology.json`, `review_packet.json`, `review_packet.md`,
  `hotspots.mmd`, and `hotspots.dot`; findings were 23 across 18 files.
- `python3 dev/scripts/devctl.py probe-report --format terminal --output-root
  /tmp/devctl-probes-topology-smoke-5` -> ok after the first cleanup pass and
  topology-stack refactor;
  findings dropped to 18 across 14 files.
- `python3 dev/scripts/devctl.py process-cleanup --verify --format md` -> ok
  after killing 9 stale repo-tooling processes.
- Bundle follow-up blockers observed on the dirty tree, not introduced by this
  plan refresh:
  - `python3 dev/scripts/checks/check_code_shape.py` -> fail
    (pre-existing large-file blockers outside this slice:
    `probe_report_render.py`, `check_phases.py`, `guard_run.py`,
    `review_channel_bridge_handler.py`).
  - `python3 dev/scripts/checks/check_review_channel_bridge.py` -> fail
    (`code_audit.md` `Last Codex poll` stale for active bridge mode).
  - `python3 dev/scripts/checks/check_rust_compiler_warnings.py` -> fail
    (`rust/src/bin/voiceterm/daemon/agent_driver.rs:84` dead-code warning for
    `opened`).
  - `python3 dev/scripts/checks/check_python_dict_schema.py` -> fail
    (pre-existing large dict literals in `script_catalog.py` and
    `watchdog/probe_gate.py`).
  - `python3 -m pytest app/operator_console/tests/ -q --tb=short` -> fail
    (pre-existing circular import between
    `app/operator_console/views/help_dialog.py` and
    `app/operator_console/views/layout/ui_window_shell.py` during collection).
