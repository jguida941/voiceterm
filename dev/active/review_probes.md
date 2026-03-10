# Review Probes Plan

**Status**: active  |  **Last updated**: 2026-03-09 | **Owner:** Tooling/quality intelligence
Execution plan contract: required
This spec remains execution mirrored in `dev/active/MASTER_PLAN.md` under `MP-368..MP-375`.

## Scope

Add a "review probe" layer between deterministic hard guards and AI
investigative review. Probes are heuristic scanners that detect risk
patterns and emit structured review targets — they never block CI, they
feed the AI triage queue.

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

## Probe Catalog (initial set)

### probe_concurrency (MP-368)

Detect code patterns that suggest concurrency/race risk in Rust async code.

**Signal patterns:**
- `Arc<Mutex<>>` or `Arc<RwLock<>>` held across `.await` points
- `tokio::spawn` or `task::spawn` capturing shared mutable state
- Channel sender/receiver split across task boundaries
- Nested lock acquisitions (potential deadlock)
- Retry/polling loops touching shared flags
- UI state coordination with background tasks
- `Mutex` + `async` in the same function scope

**AI review instruction template:**
> Review for ordering issues, stale reads, unsynchronized state
> transitions, and deadlock risk from nested lock acquisitions.

### probe_architecture (MP-369)

Detect structural patterns that suggest hidden coupling or responsibility
drift.

**Signal patterns:**
- Module importing from 4+ unrelated domain namespaces
- Bidirectional import dependencies between modules
- Functions mixing orchestration + business logic + formatting
- Single struct/impl with 15+ methods (proto-god-class below guard threshold)
- Re-exported types creating hidden coupling chains
- Modules with both `pub(crate)` and deep internal structs

**AI review instruction template:**
> Review for hidden coupling, abstraction leaks, and responsibility
> boundaries that may make future changes fragile.

### probe_performance (MP-370)

Detect patterns that may cause performance issues at scale.

**Signal patterns:**
- Nested loops over collections (O(n^2) risk)
- `.clone()` on large structs in loops or hot paths
- `collect::<Vec<_>>()` followed by iteration (unnecessary allocation)
- Sync I/O (`std::fs`, `std::net`) in async context
- Repeated full-state scans in event handlers
- String formatting with `format!()` in tight loops
- Unbounded `Vec::push` without capacity pre-allocation

**AI review instruction template:**
> Review for scale-only performance issues that may not be visible
> in small test scenarios but degrade under production load.

### probe_product_logic (MP-371)

Detect patterns that suggest policy drift or inconsistent business rules.

**Signal patterns:**
- Hardcoded numeric thresholds (magic numbers in conditionals)
- Same constant value defined in multiple files
- Feature-flag branching in 3+ locations (scattered policy)
- State machine transitions without exhaustive match
- Validation rules split across layers (handler + model + view)
- Duplicated policy conditions across different code paths

**AI review instruction template:**
> Review for policy drift, inconsistent behavior across code paths,
> or technically-correct-but-strategically-fragile design.

## Execution Checklist

### Phase 1: Probe framework (MP-372)

- [ ] Create `dev/scripts/checks/probe_bootstrap.py` with shared probe
      base: CLI args, JSON/MD output, `risk_hint` schema, severity enum.
- [ ] Create `dev/scripts/checks/probe_shared.py` with shared probe
      utilities: function extraction, pattern matching, signal aggregation.
- [ ] Add `PROBE_SCRIPT_FILES` dict to `script_catalog.py`.
- [ ] Add `REVIEW_PROBE_CHECKS` tuple to `check_support.py`.
- [ ] Add `with_review_probes` flag to `check_profile.py` presets.
- [ ] Add `run_probe_phase()` to `check_phases.py`.
- [ ] Create `dev/reports/probes/` output directory convention.
- [ ] Add `probe_triage` section to `control_plane_policy.json`.

### Phase 2: First probe implementation (MP-373)

- [ ] Implement `probe_concurrency.py` with Rust async pattern detection.
- [ ] Add test coverage in `dev/scripts/devctl/tests/test_probe_concurrency.py`.
- [ ] Wire through `devctl check --profile ci` and verify JSON output.
- [ ] Validate that probe never returns exit code 1.

### Phase 3: Remaining initial probes (MP-374)

- [ ] Implement `probe_architecture.py`.
- [ ] Implement `probe_performance.py`.
- [ ] Implement `probe_product_logic.py`.
- [ ] Add test coverage for each probe.
- [ ] End-to-end test: run all probes, verify aggregated
      `review_targets.json` output.

### Phase 4: Control plane integration (MP-375)

- [ ] Wire probe output into Ralph triage loop input.
- [ ] Add probe result rendering to `devctl status` / `devctl report`.
- [ ] Add operator console probe dashboard surface (optional).
- [ ] Document probe authoring guide in `dev/scripts/README.md`.

## Progress Log

- 2026-03-09: Created the execution-plan doc for review probes and captured the
  initial probe catalog, schema, and repo-specific research examples for
  concurrency, architecture, performance, and product-logic drift.
- 2026-03-10: Registered this plan in the active-doc index and master plan so
  the strict active-plan governance checks can treat probe work as tracked
  execution scope instead of orphan markdown.

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

## Audit Evidence

- `python3 dev/scripts/checks/check_active_plan_sync.py` -> pending rerun after
  registry + section updates land.
- `python3 dev/scripts/devctl.py docs-check --strict-tooling` -> pending rerun
  after metadata-header normalization and workflow-shell cleanup land.
