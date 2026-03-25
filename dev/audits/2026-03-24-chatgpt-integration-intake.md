# ChatGPT Conversation Integration Intake

**Status**: active intake | **Created**: 2026-03-24 | **Owner**: MP-377 authority-loop / MP-375 probe-feedback-loop

This file captures validated ideas from an external ChatGPT architecture
review that identified real gaps in the codebase. Each item has been audited
against the live codebase by 7 parallel agents and verified as a genuine
gap — not something the system already has.

## Authority Rule

This is intake, not a tracked execution plan. Accepted items must be promoted
into the proper tracked owner: `MASTER_PLAN.md`, `platform_authority_loop.md`,
`review_probes.md`, or `portable_code_governance.md` before implementation.

## 2026-03-25 Resweep Refresh

This intake was re-audited against the current repo state after the original
2026-03-24 capture. The detailed sections below remain useful historical
evidence, but several claims are now partially landed or narrower than they
were when first written.

### Landed Or Narrower Since Initial Intake

- **Compiler framing is no longer an open gap.**
  The compiler-pass framing now exists in
  `dev/active/ai_governance_platform.md` under `## Compiler-Pass Framing`.
  Treat `Gap 5` below as absorbed into the active plan, not as fresh backlog.
- **Repo-owned startup/bootstrap is stronger than the original intake described.**
  `startup-context`, `WorkIntakePacket`, typed `SessionResumeState`, startup
  receipt writing, and fail-closed startup gating are now real runtime/code
  surfaces (`dev/scripts/devctl/runtime/startup_context.py`,
  `dev/scripts/devctl/runtime/work_intake.py`,
  `dev/scripts/devctl/commands/governance/startup_context.py`). This is
  evidence for repo-owned launcher/mutation paths, not proof that a fresh
  interactive Claude session will obey Step 0 without a hook/wrapper.
- **The old probe-summary path bug is fixed.**
  `startup_signals.py` now reads
  `dev/reports/probes/latest/summary.json`, so the earlier wrong-path bug is
  historical only.
- **Review-channel state consumption is no longer zero/none.**
  `current_session`, queue-derived instruction state, and typed attention now
  feed some startup, wait-loop, and recovery paths. Remaining gaps are about
  incomplete authority/decision use, not total non-consumption.
- **Operational feedback already reaches Ralph through escalation packets.**
  The still-open gap is narrower than originally written: Ralph gets recent
  fix history / quality feedback / watchdog / reliability context through
  `context_graph/escalation.py`, but bootstrap still lacks a structured
  recurring-pattern index and `guard-run` still lacks equivalent wiring.

### Still Open After Resweep

- `quality_feedback -> startup-context` remains broken: startup quality signals
  still do not load `quality_feedback_snapshot.json`.
- Bootstrap still lacks a structured recurring-pattern / waiver-memory surface
  (`BadPatternIndex`-style startup enrichment).
- `WorkIntakePacket` is produced but still weakly consumed by launcher /
  scheduler paths; the runtime still uses only a thin slice of the startup
  packet it emits.
- The canonical typed `agent_registry` is still bypassed by some consumers in
  favor of legacy `_compat.agents` / top-level agent projections.
- Prompt consumers still drop richer decision metadata that already exists in
  guidance/finding contracts (`precedent`, `invariants`,
  `validation_plan`); this is the narrowest current seam inside the broader
  output-constraints / fix-strategy lane.

### Narrow Additions From This Resweep

- **Graph reduction before traversal**: the conversation's dead-node
  elimination / deterministic-fact reuse idea does not map to Rust compiler
  plugins or inline annotations in current scope, but it does expose one real
  missing seam in the repo: there is no transparent reducer between raw
  context-graph production and prompt/decision consumers. Current flow is
  effectively `build_context_graph -> query_context_graph ->
  build_context_escalation_packet` with no intermediate stage that prunes
  irrelevant nodes, memoizes repeated deterministic facts, or materializes a
  smaller decision subgraph. Keep this as **audit-only** for now under
  `MP-377`; do not promote it into active implementation scope until the graph
  grows beyond today's file/topology-level model.

### Routing

- No new active-plan doc is required from this resweep.
- Keep remaining startup/intake / review-state / markdown-consumption work in
  `MP-377`.
- Keep failure-rule / output-constraint / bad-pattern / signal-interaction
  work in `MP-375`.

## What ChatGPT Got Wrong (Already Exists)

These claims were factually incorrect — the system already has them:

| Claim | Reality | Evidence |
|---|---|---|
| "Missing closed feedback loop" | `probe_guidance.py` → `ralph_prompt.py` injects `ai_instruction` into prompts | `coderabbit/probe_guidance.py`, `coderabbit/ralph_prompt.py:74-91` |
| "No pattern learning" | 110-entry `finding_reviews.jsonl`, `recurrence_risk` taxonomy, per-check `cleanup_rate` | `governance_review_models.py`, `dev/reports/governance/` |
| "Missing quality metrics" | 7-metric maintainability score, per-check precision/FP rates, improvement deltas | `quality_feedback/models.py`, `quality_feedback_snapshot.json` |
| "Every run is stateless" | 16 report dirs, 6,257 data-science snapshots, startup-context loads quality signals | `startup_signals.py`, `operational_feedback.py` |
| "Governance is only reactive" | 5-layer pre-generation injection (bootstrap → intake → bridge → guidance → escalation) | `CLAUDE.md`, `startup_context.py`, `ralph_prompt.py` |
| "No convergence" | 3-layer iteration: guard-run → triage-loop → autonomy-loop with caps | `autonomy_loop_rounds.py`, `coderabbit_ralph_loop_core.py` |
| "No decision reduction" | `DecisionPacketRecord` with `decision_mode`, triage, weighted quality-backlog scoring | `finding_contracts.py:192-240`, `quality_backlog/priorities.py` |
| "No hierarchy of truths" | 4-level: Signal → FindingRecord → DecisionPacket → GovernanceReviewVerdict | `finding_contracts.py`, `governance_review_models.py` |

## What ChatGPT Got Right (Genuine Gaps)

These are real gaps verified by codebase audit. Each is scoped to the smallest
concrete implementation that closes it.

---

### Gap 1: Dynamic Failure-Rule Ledger

**ChatGPT insight**: "Track recurring failures → inject them into prompt
context → modify generation strategy"

**What exists**: Static `ai_instruction` per probe (defined in probe code),
plus `finding_reviews.jsonl` that records verdicts. But findings are NOT
automatically converted into sorted constraint rules for future prompts.

**What's missing**: A dynamic `failure_rules.jsonl` that:
- Extracts the top N recurring violations from `finding_reviews.jsonl`
  (grouped by `check_id` + `recurrence_risk=recurring|systemic`)
- Converts them into prompt-injectable constraint lines
- Auto-injects the sorted constraints into `ralph_prompt.py` and
  `context_graph/escalation.py` prompts
- Evolves as new findings are adjudicated (not static per-probe)

**Implementation home**: `dev/scripts/devctl/governance/failure_rule_ledger.py`

**Consumers**: `ralph_prompt.py:build_prompt()`, `escalation.py`, `guard_run.py`

**Tracked plan owner**: `MP-375` (probe-feedback-loop), specifically the
"carry failed-fix context into retries" item already tracked at
`MASTER_PLAN.md:2966-2978`.

**Size**: ~120 lines new module + ~30 lines consumer wiring

---

### Gap 2: Output Schema Constraints (Pre-Generation Structure Enforcement)

**ChatGPT insight**: "Prevent bad code from existing at all" — enforce
structure BEFORE generation, not just validate after.

**What exists**: `ai_instruction` tells the AI what to do, `decision_mode`
gates whether it can auto-apply. But no mechanism constrains the OUTPUT
SHAPE — e.g., "you must produce a frozen dataclass, not a dict literal."

**What's missing**: A `generation_contract` surface that:
- Defines allowed output patterns per finding type (e.g., `dict_as_struct`
  findings must produce `@dataclass(frozen=True)`, not another dict)
- Attaches the contract to the prompt alongside `ai_instruction`
- Guard-run validates the fix matches the contract shape (not just that
  guards pass)

**Implementation home**: Extend `DecisionPacketRecord` with
`output_constraints: tuple[str, ...]` field, consumed by `ralph_prompt.py`

**Tracked plan owner**: `MP-375` (probe-feedback-loop), specifically the
"attribution/fix-strategy memory" item at `MASTER_PLAN.md`.

**Size**: ~50 lines contract extension + ~40 lines prompt injection + ~30
lines guard-run validation

---

### Gap 3: Convergence Proof Metric

**ChatGPT insight**: "If you can't measure improvement, you can't prove it
exists" — need threshold-based stopping, not just iteration caps.

**What exists**: `max_rounds`, `max_attempts`, `max_hours` caps in
autonomy-loop. Feedback sizing (stall→downshift, improve→upshift). But no
formal "quality score improved by X%, therefore converged" metric.

**What's missing**: A `convergence_metric` in the autonomy-loop that:
- Computes quality delta per round (probe hint count before vs after)
- Stops early when delta < epsilon (diminishing returns threshold)
- Records convergence proof in the round's `RunRecord`
- Detects divergence (quality got WORSE) and escalates instead of retrying

**Implementation home**: `dev/scripts/devctl/autonomy/convergence.py`

**Consumers**: `autonomy_loop_rounds.py:_should_continue()`, `phone_status.py`

**Tracked plan owner**: `MP-377` authority-loop, adjacent to the
"validation-freshness" gap already tracked.

**Size**: ~80 lines convergence module + ~20 lines loop integration

---

### Gap 4: Session Decision Audit Trail

**ChatGPT insight**: "Decision → Proof → Human/AI Explanation → Validation"
as first-class artifacts per session.

**What exists**: `DecisionPacketRecord` has all the fields. `governance-review`
records verdicts. But there's no unified "here's everything this session
decided and why" artifact.

**What's missing**: A `session_decision_log.json` that:
- Aggregates all `DecisionPacket` actions taken in one session
- Links each decision to: triggered guards, probe guidance used,
  `guidance_disposition` (used/waived/not_applicable), outcome
- Renders as human-readable audit trail (markdown)
- Feeds into the next session's startup context as "what happened last time"

**Implementation home**: `dev/scripts/devctl/governance/session_decision_log.py`

**Consumers**: `startup_signals.py` (load previous session log),
`guard_run.py` (append decisions), `ralph_ai_fix.py` (append fix outcomes)

**Tracked plan owner**: `MP-377` authority-loop, adjacent to the
`CollaborationSession` runtime node already tracked at
`MASTER_PLAN.md:2957-2960`.

**Size**: ~100 lines log module + ~40 lines consumer wiring + ~30 lines
startup loading

---

### Gap 5: Compiler-Pipeline Framing in Architecture Docs

**ChatGPT insight**: Think of the system like a compiler — frontend (parsing/
detection) → middle (analysis/reduction) → backend (enforcement/output).

**What exists**: 4-phase guard orchestration that IS compiler-like but isn't
framed that way. Architecture docs describe it as "guards + probes + bundles"
which undersells the sophistication.

**What's missing**: Adopt the compiler framing in architecture documentation:

| Compiler Phase | VoiceTerm Equivalent | Purpose |
|---|---|---|
| Lexing/Parsing | Probe scan + guard detection | Signal extraction |
| Semantic Analysis | `FindingRecord` + `DecisionPacket` | Pattern classification |
| Optimization | Triage + quality-backlog ranking | Decision reduction |
| Code Generation | `ralph_prompt.py` + `guard_run.py` | Constrained fix emission |
| Linking | `governance-review` + session log | Outcome recording + cross-session binding |

**Implementation home**: Update `dev/guides/AI_GOVERNANCE_PLATFORM.md` with
the compiler-pipeline framing. No code changes — pure documentation.

**Tracked plan owner**: `MP-377` architecture docs.

**Size**: ~50 lines of architecture doc update

## Accepted Sequencing

These gaps should land in this order, following the existing plan spine:

1. **Gap 5** (compiler framing) — zero-cost doc update, improves explainability
2. **Gap 1** (failure-rule ledger) — closes the "static ai_instruction"
   limitation, directly on the MP-375 feedback-loop path
3. **Gap 3** (convergence proof) — adds quality-delta stopping to
   autonomy-loop, directly improves the iteration system
4. **Gap 2** (output schema constraints) — extends DecisionPacket contract,
   requires Gap 1 to be useful
5. **Gap 4** (session decision log) — requires `CollaborationSession` to be
   landed first (tracked MP-377 dependency)

## Additional Gaps Found in Deep Read (Q4-Q22)

These gaps were identified by reading the full 4,904-line conversation and
dispatching 6 additional agents to verify each against the codebase.

---

### Gap 6: Structured Reason Traces Per Decision

**ChatGPT insight (Q19)**: "Make the system explain itself deterministically"
— every decision should output: action, guards triggered, graph path, evidence,
metrics before→after, confidence.

**What exists (~40%)**: `DecisionPacketRecord` has `rationale` + `precedent`.
`ContextEscalationPacket` tracks `matched_nodes` + `evidence`. `GuardedCodingEpisode`
records `guard_result` + `escaped_findings_count`. But these are in separate
subsystems with no unified trace container.

**What's missing**:
- No per-guard pass/fail list in guard-run output (only aggregate probe_scan)
- No graph traversal path in decision records
- No metrics before→after delta per decision
- No confidence scoring on any decision
- No unified `DecisionTrace` artifact linking guards + graph + evidence + outcome

**Implementation home**: `dev/scripts/devctl/governance/decision_trace.py`
— a `DecisionTrace` frozen dataclass that bundles guard results + graph path +
evidence + metrics delta + confidence into one JSON artifact per decision.

**Consumers**: `guard_run.py` (emit trace), `ralph_ai_fix.py` (emit trace),
`session_decision_log.py` (aggregate traces), `startup_signals.py` (load
previous session traces)

**Tracked plan owner**: `MP-377` — adjacent to `CollaborationSession` and
Gap 4 (session decision log). Gap 4 aggregates traces; this gap produces them.

**Size**: ~100 lines trace model + ~60 lines guard-run instrumentation +
~40 lines ralph instrumentation

---

### Gap 7: File Volatility / Stability Metrics in Context Graph

**ChatGPT insight (Q5-Q7)**: "Your guards don't control WHEN to act" — need
stability/volatility metrics computed from change frequency and graph centrality
to gate decision timing.

**What exists**: Temperature encodes change pressure (fan-in/out, hint count,
recency, severity). `quality_backlog/priorities.py` has weighted signal scoring
with severity thresholds (140/350/700). `decision_mode` gates auto_apply vs
approval_required. `control_plane_policy.json` has branch/command allowlists.

**What's missing**:
- No file-level change frequency tracking (how often a file changed across
  recent snapshots)
- No graph centrality metric (PageRank or betweenness) for impact estimation
- No adaptive thresholds that tighten when a file is volatile
- No explicit "stability bias" in the scoring formula

**Implementation home**: Extend `dev/scripts/devctl/context_graph/builder.py`
temperature formula to include `change_frequency` from snapshot history.
Add `centrality_score` to `GraphNode.metadata`.

**Tracked plan owner**: `MP-377` — adjacent to ZGraph temporal snapshots
(already landed). Uses the snapshot diff infrastructure from Part 53.

**Size**: ~60 lines frequency computation + ~40 lines centrality +
~20 lines temperature formula update

---

### Gap 8: Active Bad Pattern Recall in Repair Prompts

**ChatGPT insight (Q17)**: "At bootstrap, feed the AI a list of known bad
patterns with recorded outcomes so next time the same structure appears, the
AI already has context."

**What exists (~40%)**: `operational_feedback.py` loads recent fix history
and quality recommendations. `startup_signals.py` loads governance review
summary + guidance hotspots. Probe findings carry `ai_instruction`.

**What's missing**:
- No "patterns you waived before" detection in next session
- No "this probe fired on this file before, here's what worked" injection
  into repair prompts
- `operational_feedback.py` outputs are used in escalation rendering but NOT
  wired into `guard_run_core.py` or `ralph_ai_fix.py` prompt builders
- No BadPatternIndex at bootstrap listing top recurring violations with
  success/failure stats

**Implementation home**: Wire `operational_feedback.recent_fix_history_lines()`
into `guard_run_core.py` and `ralph_prompt.py`. Add a `BadPatternIndex`
renderer in `startup_signals.py` that groups recurring findings by check_id.

**Tracked plan owner**: `MP-375` — directly on the feedback-loop path.

**Size**: ~40 lines wiring + ~50 lines BadPatternIndex renderer

---

### Gap 9: Discard-and-Regenerate vs Patch-in-Place

**ChatGPT insight (Q4)**: "Never patch outputs in-place. Always: invalid →
discard → regenerate with tighter constraints."

**What exists**: `ralph_ai_fix.py` does `git checkout .` on validation failure
(line 251). But the ralph loop breaks on `fix_rc != 0` instead of retrying
with refined constraints. Guard-run captures snapshots but doesn't enforce
rollback. Autonomy-loop rounds inherit working tree state from previous rounds.

**What's missing**:
- No pre-fix state baseline capture (HEAD hash before Claude runs)
- No conditional rollback when subsequent checks fail after commit
- No regeneration with tighter constraints — system breaks and escalates
  instead of retrying
- State accumulation across autonomy-loop rounds (no clean-slate per round)

**Architectural decision**: This is partially by design — bounded costly AI
invocations favor escalation over infinite retry. But for the portable
governance product, formalizing the "discard bad output" pattern as a guard
would improve safety for external adopters.

**Implementation home**: Add `pre_fix_baseline` capture to `guard_run_core.py`.
Add optional `--rollback-on-failure` flag. For autonomy-loop, add
`--clean-slate` mode that resets to HEAD between rounds.

**Tracked plan owner**: `MP-376` (portable governance) — safety model for
external adopter autonomy loops.

**Size**: ~40 lines baseline capture + ~30 lines rollback logic + ~20 lines
clean-slate mode

---

### Gap 10: Triggered Global Architecture Pass

**ChatGPT insight (Q9)**: "Run targeted global reasoning when triggered by
coupling_delta or repeated changes, using compressed projections — not
scheduled, not always."

**What exists (~75%)**: `context-graph --query` produces bounded subgraphs.
Bootstrap outputs top-10 hotspots. Snapshot trend tracks temperature_direction
and node/edge deltas. Escalation packets carry matched nodes + evidence.

**What's missing**:
- No explicit `coupling_delta > threshold` trigger for full-graph analysis
- No `repeated_changes > N` counter to escalate from local to global scope
- Snapshot trends compute rolling deltas but don't auto-promote to
  architecture-review decisions

**Implementation home**: Add `should_escalate_to_global()` in
`dev/scripts/devctl/context_graph/snapshot_diff.py` using existing
`ContextGraphDelta` fields. Wire into autonomy-loop round decisions.

**Tracked plan owner**: `MP-377` — graph lane widening (deferred until after
authority spine closure).

**Size**: ~30 lines escalation logic + ~20 lines autonomy-loop integration

## Final Sweep Findings (Additional Gaps 11-17 + 7 Disconnections)

A final 4-agent sweep of the full convo.md plus a codebase connection audit
found additional concrete improvements. These fall into two categories:
new architectural gaps and existing components that should be connected.

---

### Gap 11: Deterministic Prompt Ordering Invariant

`ralph_prompt.py` iterates backlog items and probe_guidance entries in
arrival order. No `sorted()` contract ensures the same inputs produce the
same prompt text across runs. Add canonical sorting on all injected
constraint lists before they enter the prompt builder.

**Size**: ~10 lines. **Owner**: MP-375.

---

### Gap 12: Change-Pressure Gating (Distinct from Temperature)

Temperature ranks "where to look." A separate `change_score` should gate
"whether to act." Temperature = presentation; change_score = decision gate.
The system has `decision_mode` per-finding but not per-file/module computed
from composite metrics (size + nesting + coupling + centrality + trend).

**Size**: ~80 lines. **Owner**: MP-377.

---

### Gap 13: Allowed Transformation Menu Per Finding Type

`ai_instruction` tells the AI what's wrong and `decision_mode` gates
whether it can act, but nothing enumerates WHICH transformations are valid
(e.g., `["extract_function", "inline_variable", "add_type_annotation"]`).
Add `allowed_transforms: tuple[str, ...]` to `DecisionPacketRecord` or
probe guidance payload.

**Size**: ~40 lines. **Owner**: MP-375.

---

### Gap 14: TransformationProofPacket (Joining Existing Artifacts)

`GuardGitSnapshot` captures before/after diffs. `DecisionPacketRecord`
captures rationale. `GuardedCodingEpisode` captures guard outcome. But no
artifact joins them into one auditable bundle per AI-authored change:
`{git_diff_stats, graph_delta_summary, decision_packet_ref, guard_outcomes,
metric_improvement}`. The raw ingredients all exist; the join does not.

**Size**: ~80 lines. **Owner**: MP-377.

---

### Gap 15: Signal Relevance Gating (Co-Occurrence Filtering)

When multiple signals fire on the same node, some reinforce each other
(`duplication_detected` + `helper_candidate`) while others are noise
(`dict_usage_detected` alongside a refactoring decision). No mechanism
classifies signal pairs as reinforcing/independent/irrelevant before
aggregation. Add a `signal_interaction_table` consumed during quality-backlog
scoring.

**Size**: ~60 lines. **Owner**: MP-375.

---

### Gap 16: AI-as-Decision-Auditor (Structured Verification Prompts)

Current flow: system detects issue → tells AI to fix it. Missing flow:
system makes decision → feeds structured decision trace to AI → asks AI
to VALIDATE the reasoning before acting. A `validate_decision()` function
that builds a verification prompt from Gap 6 traces, asking the AI to
challenge the reasoning. The `approval_required` path would route through
this instead of just waiting for human approval.

**Size**: ~60 lines. **Owner**: MP-377.

---

### Gap 17: Deterministic Reproducibility Integration Test

No automated test runs the full pipeline twice on the same repo state and
asserts identical output for deterministic layers. For the portable product
(MP-376), proving determinism with an actual test is a concrete differentiator.

**Size**: ~40 lines. **Owner**: MP-376.

---

### 7 Disconnected Feedback Loops (Existing Components → Wire Together)

These are NOT new features — they're existing producers and consumers that
should be connected but aren't. Each is ~10-30 lines of wiring.

| # | Producer | Consumer | Gap | Wire Size |
|---|---|---|---|---|
| D1 | `operational_feedback.py` (quality/watchdog/reliability) | `ralph_prompt.py` | Ralph has zero awareness of quality trends, FP rates, or command reliability | ~20 lines |
| D2 | `watchdog/probe_gate.py` (probe_scan risk) | `autonomy_loop_rounds.py` (loop continuation) | Probe risk=high doesn't gate whether loop continues | ~15 lines |
| D3 | `quality_feedback` (maintainability score) | `decision_mode` selection | No dynamic gating: fragile codebase (grade F) should upgrade to approval_required | ~20 lines |
| D4 | `data_science` (time-series trends) | `autonomy_loop_rounds.py` | Declining command reliability trend doesn't trigger caution | ~20 lines |
| D5 | `snapshot_diff` (temperature shifts) | `escalation.py` (approval gates) | Node getting hotter → should downgrade to approval_required | ~15 lines |
| D6 | `governance-review` (cleanup_rate/waiver rate) | Probe guidance trust levels | High waiver rate probe stays at auto_apply instead of recommend_only | ~15 lines |
| D7 | `ContextGraphDelta` (architecture volatility) | Decision logic (escalation, triage, approval) | Only consumed by markdown renderer, not by any decision gate | ~20 lines |

**Total wiring**: ~125 lines across 7 connections. All producers and
consumers already exist and are tested. The wiring is pure plumbing.

## Updated Scoring Summary

| Gap | Category | % Exists | New Lines | Owner |
|---|---|---|---|---|
| 1. Failure-rule ledger | Feedback loop | 30% | ~150 | MP-375 |
| 2. Output schema constraints | Pre-generation | 20% | ~120 | MP-375 |
| 3. Convergence proof metric | Autonomy | 40% | ~100 | MP-377 |
| 4. Session decision log | Audit trail | 25% | ~170 | MP-377 |
| 5. Compiler framing in docs | Documentation | 0% | ~50 | MP-377 |
| 6. Structured reason traces | Explainability | 40% | ~200 | MP-377 |
| 7. Volatility/stability metrics | Context graph | 10% | ~120 | MP-377 |
| 8. Bad pattern recall in prompts | Feedback loop | 40% | ~90 | MP-375 |
| 9. Discard-and-regenerate | Safety model | 50% | ~90 | MP-376 |
| 10. Triggered global pass | Context graph | 75% | ~50 | MP-377 |
| 11. Prompt ordering invariant | Determinism | 90% | ~10 | MP-375 |
| 12. Change-pressure gating | Decision | 30% | ~80 | MP-377 |
| 13. Transformation menu | Pre-generation | 10% | ~40 | MP-375 |
| 14. TransformationProofPacket | Audit trail | 60% | ~80 | MP-377 |
| 15. Signal co-occurrence filter | Decision | 5% | ~60 | MP-375 |
| 16. AI-as-decision-auditor | Explainability | 10% | ~60 | MP-377 |
| 17. Reproducibility test | Portable proof | 0% | ~40 | MP-376 |
| D1-D7. Feedback loop wiring | Connections | 0% each | ~125 total | Mixed |
| **TOTAL** | | | **~1,635** | |

## Deep Sweep: Systemic Disconnections Found by 8 Agents

This section documents findings from a full-system trace across all runtime
models, report artifacts, governance commands, context-graph edges, watchdog
data, review-channel state, and the probe finding lifecycle. The theme is
consistent: **the system produces rich typed data but routes most of it to
rendering, not decisions.**

---

### Finding A: Context Graph Edges Are Rendering-Only

37,000+ edges across 7 kinds. **Zero edge kinds are consumed by decision
logic.** All 7 (imports, documented_by, guards, routes_to, scoped_by,
contains, related_to) feed into markdown rendering, snapshot reporting, and
concept diagrams — but NEVER into:
- Probe guidance selection (uses text matching, not edge traversal)
- Check routing (uses script_catalog.py, not graph edges)
- Approval gating (uses decision_mode from policy, not graph topology)
- Triage priority (uses quality-backlog scores, not graph centrality)

The one exception: `documented_by` edges downgrade query confidence to
`"low_confidence"` when they're the only match — a quality signal, not a
routing decision.

**Gap**: Wire guard/scoped_by edges into probe guidance selection so
probe guidance is topology-aware (e.g., probes that fire on a file with
high guard coverage could be auto-downgraded to recommend_only).

---

### Finding B: Review-Channel Produces Rich State Nobody Reads

The review-channel system produces 6 data families. Decision systems
consume only 2 of them:

| Data Family | Produced | Consumed by Decisions | Consumed by Rendering |
|---|---|---|---|
| bridge liveness (reviewer_mode, freshness) | Yes | **Yes** (startup gate, tandem) | Yes |
| current_session (instruction, scope) | Yes | **Yes** (work-intake selection) | Yes |
| queue_state (pending counts per agent) | Yes | **No** | Yes |
| attention_state (status, recommended_action) | Yes | **No** | Yes |
| agent_registry (job_state, capabilities) | Yes | **No** | Yes |
| event_history (follow logs, traces) | Yes (1.5MB+) | **No** | Audit only |

**Gap**: Wire `queue_state.pending_total` into autonomy-loop decisions
(high pending count → don't spawn more work). Wire `attention_state` into
startup-context so agents know if they should wait vs proceed. Wire
`agent_registry.job_state` into swarm scheduling.

---

### Finding C: Probe Finding Lifecycle Has 5 Break Points

The 9-step lifecycle (probe → report → decision packet → ralph guidance →
governance review → quality feedback → startup signals → startup context →
operator console) works end-to-end — but 5 critical feedback paths are
missing:

1. **Probes don't read the verdict ledger** — same finding fires repeatedly
   even after `verdict: fixed` is recorded
2. **Startup hotspot never advances** — always shows same top file even when
   all hints in it are fixed
3. **Ralph sees stale guidance** — decision packets frozen at generation time,
   not updated with verdict status
4. **Quality feedback doesn't adjust probe thresholds** — high-FP probes
   keep firing at same sensitivity
5. **No suppression of already-acted findings** — operator manually ignores
   "already recorded" hints in probe output

**Gap**: Read `finding_reviews.jsonl` in `build_probe_report()` to filter
findings with `verdict: fixed`. Load verdicts in `_load_guidance_hotspots()`
to advance to next incomplete file. Mark decision packets as "acted on" to
suppress stale ralph guidance.

---

### Finding D: 100+ MB of Artifacts Never Read by Decisions

226 MB in `dev/reports/`. Only ~15 MB feeds into decision logic:

| Artifact | Size | Decision Consumer |
|---|---|---|
| probes/latest/ (summary, topology, packet) | 2.7 MB | **Yes** — startup signals, context graph |
| governance/latest/review_summary.json | 148 KB | **Yes** — startup signals, operational feedback |
| review_channel/latest/review_state.json | 147 KB | **Yes** — startup gate, work-intake |
| data_science/latest/summary.json | 89 MB dir | **Yes** — watchdog, reliability |
| startup/latest/receipt.json | 574 B | **Yes** — startup gate |
| autonomy/queue/ (inbox/outbox) | variable | **Yes** — live coordination |
| **graph_snapshots/** | **99 MB** | **No** — archive only |
| **audits/devctl_events.jsonl** | **11.5 MB** | **No** — report context only |
| **research/** | **7 MB** | **No** — experiment archive |
| **review_channel/ follow logs** | **7.5 MB** | **No** — audit trail only |

**Gap**: Not a code gap — an artifact hygiene gap. For the portable product,
separate decision-path artifacts (slim, typed) from audit/history artifacts
(can be archived or pruned).

---

### Finding E: 4 Typed Runtime Models With Zero Active Consumers

| Model | Defined In | Active Producers | Active Consumers |
|---|---|---|---|
| `ProviderAdapter` | action_contracts.py | 0 | Tests + contract rows only |
| `WorkflowAdapter` | action_contracts.py | 0 | Tests + contract rows only |
| `ArtifactStore` | action_contracts.py | 0 | Contract rows only |
| `RunRecord` | action_contracts.py | Minimal | Tests + contract rows only |

These are aspirational schema definitions ahead of implementation. They
should either be implemented or explicitly marked as deferred/placeholder.

**Also**: `WorkIntakePacket` and `StartupContext` are well-produced but have
**no agent launcher code** that reads their fields. The packets are emitted
to markdown/JSON but no agent startup path programmatically consumes
`work_intake.warm_refs` or `work_intake.routing.preflight_command`.

---

### Finding F: 79 Typed Models With Zero Cross-Module Consumers

A full scan found 79 dataclasses/TypedDicts defined in devctl that are never
imported outside their own module (plus tests). Breakdown:

- 23 review-channel models (wait states, auth projections, daemon events)
- 13 governance/bootstrap models (policy results, export payloads)
- 15 command-specific models (wait configs, action reports)
- 12 policy/config models (resolved policies, scan modes)
- 8 runtime contract TypedDicts (artifact metrics, finding payloads)
- 8 data structure models (query payloads, hint excerpts)

~60% are over-modeled internal state (could be inlined). ~40% are
futures/placeholder contracts for anticipated integrations. This is technical
debt, not a ChatGPT-conversation gap — but it's the same "designed but never
wired" pattern at a finer grain.

---

### Finding G: Triage Output Not Read by Autonomy Loop

The `triage` command produces classified issues with severity, next actions,
and rollup metrics. The `autonomy-loop` conceptually depends on triage for
work selection — but **does NOT programmatically read triage output**. The
autonomy loop uses probe findings + policy directly. Wiring triage output
as a structured input to autonomy round planning would close a natural
feedback loop.

## Meta-Finding: The System Doesn't Guard Itself

The deepest finding from all 13+ agents across this session: **the guard
system checks code quality but not governance system completeness.**

### Why Guards Missed Everything We Found

Guards are **syntactic** (shape, duplication, imports, safety) not
**semantic** (data flow, consumer wiring, lifecycle closure). The system
can detect a 3-line function duplication but not that 79 typed models have
zero consumers or that 100MB of artifacts are write-only.

### 4 Self-Improvement Guards (The "Compiler Improves Its Type System" Pattern)

| Guard | Catches | Lines |
|---|---|---|
| `check_prevention_surface_closure` | `missing_guard` findings with no follow-up guard or MP | ~80 |
| `check_loop_closure` | Commands whose output is never consumed by a handler | ~100 |
| `check_type_consumer_parity` | Typed models with zero non-test consumers | ~95 |
| `check_finding_lifecycle_closure` | Finding IDs that never reach a terminal verdict | ~115 |

**Total: ~390 lines.** All deterministic, Layer A, CI-blocking. Use existing
data (governance_review_log.jsonl, finding_id, prevention_surface, runtime
models, COMMAND_HANDLERS). No new models needed.

### The Missing Instruction Surface

AGENTS.md says "classify as missing_guard → encode prevention path." But
doesn't say "propose the guard implementation." Add:

> When you adjudicate with `prevention_surface="missing_guard"`, you MUST
> propose the guard: name, what it checks, FP risk estimate, follow-up MP.
> If `decision_mode="auto_apply"`, implement directly. The
> `check_prevention_surface_closure` guard blocks CI if you classify without
> follow-up.

This turns "detect and record" into "detect, record, AND ensure the gap
gets closed." The system becomes a compiler that strengthens its own type
system every time it finds a new class of error.

## Self-Strengthening Loop Architecture

The system should automatically get smarter with each issue. Currently it
collects intelligence but doesn't feed it back into decisions or
self-improvement.

### AI Operates With 12% of System Intelligence

| Category | Total | In Startup | Visible |
|---|---|---|---|
| Guards (by name) | 65 | 4 | 6% |
| Probes (by name) | 28 | 0 | 0% |
| Quality dimensions | 7 | 0 | 0% |
| Per-check cleanup rates | 40+ | 0 | 0% |
| Guard family reliability | 5 families | 1 macro | 20% |
| File finding density | 2,006 files | 0 | 0% |
| Neighbor risk graphs | 38,080 edges | 0 | 0% |
| Recurrence patterns | per-finding | 0 | 0% |

### 5-Phase Loop (~810 New Lines)

Phase 1 — Detect & Classify (75% exists, ~40 lines): populate finding_class,
prevention_surface, recurrence_risk. Add AGENTS.md instruction for guard
proposals.

Phase 2 — Pattern Recognition (30% exists, ~190 lines): new
`pattern_recognizer.py` grouping ledger rows, threshold count >= 3 AND
recurrence_risk in {recurring, systemic}. Wire into startup_signals.

Phase 3 — Guard Proposal (20% exists, ~190 lines): new
`guard_proposal_generator.py` with FP risk estimation from similar probes,
scaffold from PROBE_TEMPLATE_README.md, decision_mode routing.

Phase 4 — Implement & Validate (40% exists, ~240 lines): new
`guard_implementation_task.py` + `guard_validation.py`. Phase 5b gates:
FP < 5%, catches original pattern, tests pass.

Phase 5 — Learn (35% exists, ~150 lines): guard provenance, pattern closure,
effectiveness metric (effective/noisy/insufficient/pending).

### Build First: 200 Lines

1. `pattern_recognizer.py` (~120 lines) — surfaces recurring patterns
2. `check_prevention_surface_closure.py` (~80 lines) — blocks CI when
   missing_guard findings have no follow-up

### Startup Intelligence Expansion (12% → 70%)

Add to startup_signals / startup-context:
1. Per-check cleanup rankings (top 5 easiest, top 5 hardest)
2. Guard family reliability (Rust 4% vs Tooling 100%)
3. File-level finding density (files with 5+ open findings)
4. Deferred finding reasons
5. Neighbor risk (top 3 at-risk files for current target)
6. Recurring patterns from pattern_recognizer
7. Maintainability score + sub-dimensions

### Instruction Surface Addition

Add to AGENTS.md and CLAUDE.md: when adjudicating with
`prevention_surface="missing_guard"`, MUST propose the guard (name, what it
checks, FP risk, follow-up MP). `check_prevention_surface_closure` blocks
CI if classified without follow-up.

## Updated Sequencing (All 10 Gaps)

**Phase 1 — Immediate (feedback loop closure, MP-375)**:
1. Gap 8 (bad pattern recall) — smallest, wires existing data into prompts
2. Gap 1 (failure-rule ledger) — dynamic constraint evolution
3. Gap 2 (output schema constraints) — extends DecisionPacket

**Phase 2 — Authority spine (MP-377)**:
4. Gap 6 (reason traces) — unified decision instrumentation
5. Gap 3 (convergence proof) — quality-delta stopping
6. Gap 4 (session decision log) — aggregates Gap 6 traces

**Phase 3 — Graph/safety (MP-377 + MP-376)**:
7. Gap 7 (volatility metrics) — uses snapshot infrastructure
8. Gap 10 (triggered global pass) — uses volatility metrics
9. Gap 9 (discard-and-regenerate) — safety model for portable product

**Phase 4 — Documentation**:
10. Gap 5 (compiler framing) — can land anytime, zero code

## How This Relates to the ChatGPT Conversation

The ChatGPT conversation (22 questions in `convo.md`) contained valuable
architectural framing but made incorrect assumptions about what the codebase
already has. Final tally after three audit passes (13 agents total):

- **8 were factually wrong** (system already has feedback loops, metrics,
  persistence, decision reduction, pre-generation injection, convergence caps,
  decision mode gating, action space allowlists)
- **17 were valid gaps** (Gaps 1-17 above)
- **7 disconnected feedback loops** (D1-D7 — existing components that should
  be wired together)
- **2 were partially right** (compiler framing, reject/regenerate)

The valid work totals **~1,635 lines** across 17 gaps + 7 wiring tasks. All
are **incremental additions to existing infrastructure**, not new architecture.

The three most impactful themes from the ChatGPT conversation:

1. **Compiler mental model**: guards = type system, probes = linting, context
   graph = AST, AI reasoning = controlled optimization pass, governance-review
   = linker. This framing improves explainability without code changes.

2. **Close the feedback loops**: 7 existing data producers (operational
   feedback, watchdog, quality metrics, snapshot deltas, governance verdicts)
   feed into markdown rendering but NOT into decision gates. Wiring them into
   the autonomy-loop, ralph prompts, and approval logic is ~125 lines of pure
   plumbing with outsized impact on autonomous safety.

3. **"Determinism decides IF, AI decides HOW"**: The system already separates
   detection (guards) from action (AI). But the separation isn't explicit
   enough — no per-file change-pressure gating, no transformation menu per
   finding type, no computed "should we act" threshold. Making that split
   first-class would close the biggest remaining architectural gap.

---

## Self-Strengthening Loop Architecture

**The compiler that improves its own type system.**

Every issue the system finds makes future detection stronger. AI makes
better architectural decisions over time because outcomes feed back into
detection rules, prompt constraints, and approval thresholds. This section
designs the complete closed loop across five phases.

### Design Principles

1. **Determinism first**: Guards and probes are deterministic pattern matchers.
   AI decides HOW to fix; the system decides IF to act and WHAT to check.
2. **Monotonic strengthening**: The set of checks can only grow. Removing a
   check requires an explicit governance-review waiver with `waiver_reason`.
3. **FP-gated promotion**: No generated guard enters CI until its false-positive
   rate is validated below 5% on the existing codebase.
4. **Outcome-linked**: Every guard traces back to the finding(s) that motivated
   it, and every finding traces forward to the guard(s) that prevent recurrence.

---

### Phase 1 — Issue Detection & Classification

**Purpose**: Find issues and record them with enough metadata to enable
pattern recognition downstream.

#### What exists today (~75%)

| Component | File | Role |
|---|---|---|
| 64 hard guards | `dev/scripts/checks/check_*.py` | Layer A: deterministic CI blockers |
| 25 review probes | `dev/scripts/checks/probe_*.py` | Layer B: advisory design-smell detection |
| `FindingRecord` | `runtime/finding_contracts.py:138` | Canonical evidence row with `finding_id`, `check_id`, `severity`, `ai_instruction` |
| `GovernanceReviewInput` | `governance_review_models.py:44` | Adjudication row with `finding_class`, `recurrence_risk`, `prevention_surface` |
| `governance_review_log.jsonl` | `dev/reports/governance/` | Durable append-only ledger of all adjudicated findings |
| `build_governance_review_row()` | `governance_review_log.py:95` | Validates and normalizes every review row before append |

#### What's new (~25%)

**1a. Enriched classification fields on `GovernanceReviewInput`** (~30 lines)

Add three optional fields to `GovernanceReviewInput` and the row builder:

```python
# In governance_review_models.py
@dataclass(frozen=True)
class GovernanceReviewInput:
    # ... existing fields ...
    pattern_signature: str | None = None      # e.g., "dict_literal:5+_keys:return_position"
    proposed_guard_name: str | None = None     # e.g., "check_dict_as_struct"
    proposed_guard_fp_risk: str | None = None  # "low" | "medium" | "high"
```

**Why**: `finding_class` + `prevention_surface` + `recurrence_risk` classify
the problem category, but nothing captures the CONCRETE detection pattern.
`pattern_signature` is the machine-readable fingerprint that Phase 2 groups
on. `proposed_guard_name` + `proposed_guard_fp_risk` are the Phase 3
outputs written back at adjudication time.

**1b. Instruction surface addition to AGENTS.md** (~10 lines)

> When you adjudicate with `prevention_surface="missing_guard"` or
> `prevention_surface="missing_probe"`, you MUST also set:
> - `pattern_signature`: normalized detection pattern (file glob + symbol
>   pattern + AST shape)
> - `proposed_guard_name`: the check/probe script name
> - `proposed_guard_fp_risk`: estimated FP risk from similar probes
>
> The `check_prevention_surface_closure` guard blocks CI if you classify
> `missing_guard`/`missing_probe` without these fields.

**Estimated lines**: ~40 total (30 model + 10 instruction surface)

---

### Phase 2 — Pattern Recognition

**Purpose**: Query the governance review ledger for recurring patterns,
group them, and surface candidates for guard/probe generation.

#### What exists today (~30%)

| Component | File | Role |
|---|---|---|
| `read_governance_review_rows()` | `governance_review_log.py:208` | Reads bounded JSONL rows |
| `build_governance_review_stats()` | `governance_review_log.py:219` | Groups by `check_id`, `signal_type`, computes `cleanup_rate`, `fp_rate` |
| `latest_rows_by_finding()` | `governance/ledger_helpers.py:48` | Deduplicates by `finding_id`, keeps latest |
| `Recommendation` model | `quality_feedback/models.py:215` | Structured tuning recommendation with priority, evidence, impact |
| `recommendation_engine.py` | `quality_feedback/recommendation_engine.py` | Generates prioritized recommendations from quality data |

#### What's new — `pattern_recognizer.py` (~120 lines)

**Implementation home**: `dev/scripts/devctl/governance/pattern_recognizer.py`

```python
@dataclass(frozen=True)
class RecurringPattern:
    """One grouped pattern extracted from the governance review ledger."""
    pattern_key: tuple[str, str, str]   # (check_id, finding_class, prevention_surface)
    pattern_signature: str | None       # normalized from adjudication rows
    occurrence_count: int               # total rows matching this key
    session_count: int                  # distinct sessions (by timestamp date)
    recurrence_risk: str                # highest risk level seen
    severity_max: str                   # highest severity seen
    representative_finding_ids: tuple[str, ...]  # up to 5 example finding_ids
    ai_instructions: tuple[str, ...]    # unique ai_instruction texts seen
    proposed_guard_name: str | None     # from adjudication if present
    guard_proposal_ready: bool          # True when count >= 3 AND recurrence_risk in {recurring, systemic}


def recognize_patterns(
    rows: list[dict[str, Any]],
    *,
    min_occurrences: int = 3,
    qualifying_risks: frozenset[str] = frozenset({"recurring", "systemic"}),
) -> list[RecurringPattern]:
    """Group review-log rows into recurring patterns and rank by proposal readiness."""
```

**Interface**:
- **Input**: `list[dict]` from `read_governance_review_rows()` — already validated
- **Output**: `list[RecurringPattern]` sorted by `(guard_proposal_ready DESC, occurrence_count DESC)`
- **Grouping key**: `(check_id, finding_class, prevention_surface)`
- **Session counting**: Groups by `timestamp_utc[:10]` (date portion) to measure
  cross-session recurrence, not just within-session repeats
- **Threshold**: `guard_proposal_ready=True` when `occurrence_count >= min_occurrences`
  AND highest `recurrence_risk` is in `qualifying_risks`

**Consumers**:
- Phase 3 (`guard_proposal_generator.py`) reads `RecurringPattern` list
- `startup_signals.py` loads top-3 ready patterns into bootstrap context
- `recommendation_engine.py` can reference ready patterns in recommendations
- `devctl pattern-report` new command renders recognized patterns

**Estimated lines**: ~120 (module) + ~30 (startup_signals wiring) + ~40 (command)

---

### Phase 3 — Guard Proposal Generation

**Purpose**: For qualifying patterns, generate a guard/probe scaffold,
estimate FP risk, and route through `decision_mode`.

#### What exists today (~20%)

| Component | File | Role |
|---|---|---|
| `PROBE_TEMPLATE_README.md` | `dev/scripts/checks/` | Documents scaffold structure: `ProbeReport`, `RiskHint`, `build_probe_parser`, `emit_probe_report` |
| `probe_bootstrap.py` | `dev/scripts/checks/` | Shared probe infrastructure (parser, report model, emitter) |
| `script_catalog.py` | `devctl/script_catalog.py` | `CHECK_SCRIPT_FILES` and `PROBE_SCRIPT_FILES` registration dicts |
| `quality_policy_defaults.py` | `devctl/quality_policy_defaults.py` | `AI_GUARD_REGISTRY` and `REVIEW_PROBE_REGISTRY` with `QualityStepSpec` |
| `check_support.py` | `devctl/commands/check_support.py` | `build_probe_cmd()` and `build_ai_guard_cmd()` command builders |
| `CheckQualityScore` | `quality_feedback/models.py:178` | Per-check `precision_pct`, `fp_rate_pct`, `cleanup_rate_pct` |
| `FPClassification` | `quality_feedback/models.py:150` | Classified FP with `root_cause`, `confidence`, `evidence` |
| `FP_ROOT_CAUSES` | `quality_feedback/models.py:43` | `{context_blind, threshold_noise, style_opinion, pattern_mismatch, unknown}` |
| `DecisionPacketPolicy` | `finding_contracts.py:101` | Policy bundle with `decision_mode`, `rationale`, `invariants`, `validation_plan` |

#### What's new — `guard_proposal_generator.py` (~150 lines)

**Implementation home**: `dev/scripts/devctl/governance/guard_proposal_generator.py`

```python
@dataclass(frozen=True)
class GuardProposal:
    """One generated guard/probe proposal from a recurring pattern."""
    proposal_id: str                    # deterministic hash of pattern_key
    pattern: RecurringPattern           # the source pattern
    guard_type: str                     # "check" (Layer A) or "probe" (Layer B)
    guard_name: str                     # e.g., "check_dict_as_struct" or "probe_nested_dicts"
    detection_strategy: str             # "regex", "ast_walk", "import_graph", "metric_threshold"
    scaffold_code: str                  # generated Python scaffold from template
    fp_risk_estimate: str               # "low" | "medium" | "high"
    fp_risk_evidence: str               # how the estimate was computed
    decision_mode: str                  # from policy: "auto_apply" | "approval_required" | "recommend_only"
    registration_steps: tuple[str, ...] # what to add to script_catalog, quality_policy_defaults, etc.
    test_plan: tuple[str, ...]          # validation steps before CI integration
    source_finding_ids: tuple[str, ...] # traceability back to original findings


def generate_guard_proposal(
    pattern: RecurringPattern,
    *,
    existing_checks: frozenset[str],    # from CHECK_SCRIPT_FILES.keys()
    existing_probes: frozenset[str],    # from PROBE_SCRIPT_FILES.keys()
    check_quality_scores: list[CheckQualityScore],  # FP data for similar probes
    decision_mode_override: str | None = None,
) -> GuardProposal | None:
    """Generate one guard/probe proposal for a qualifying recurring pattern.

    Returns None if the pattern already has a matching guard/probe or
    if FP risk is too high for the detected pattern type.
    """
```

**Guard type routing logic**:
- `finding_class == "missing_guard"` → `guard_type = "check"` (Layer A, CI-blocking)
- `finding_class == "missing_probe"` → `guard_type = "probe"` (Layer B, advisory)
- `finding_class in {"rule_quality", "contract_mismatch"}` → `guard_type = "check"`
- All others → `guard_type = "probe"` (start advisory, promote later)

**FP risk estimation**:
- Looks up `CheckQualityScore` for probes with similar `check_id` prefixes
- If similar probes have `fp_rate_pct > 15%`: `fp_risk = "high"`
- If `fp_rate_pct` between 5-15%: `fp_risk = "medium"`
- Below 5% or no similar data: `fp_risk = "low"`
- High FP risk + `decision_mode="auto_apply"` → downgrade to `"approval_required"`

**Scaffold generation**:
- Uses `PROBE_TEMPLATE_README.md` structure as the template
- Fills in: probe name, detection regex/pattern from `pattern_signature`,
  `ai_instruction` from the most common instruction in the pattern's findings,
  `risk_type` and `review_lens` from the pattern's representative findings
- Scaffold is valid Python that can run immediately (exit 0, scan target roots)

**Decision mode routing**:
- `fp_risk = "low"` AND `recurrence_risk = "systemic"` → `auto_apply`
- `fp_risk = "medium"` OR `recurrence_risk = "recurring"` → `approval_required`
- `fp_risk = "high"` → `recommend_only` (human must review before activation)
- Operator can override via `decision_mode_override` parameter

**How it uses `ai_instruction`**:
- Extracts unique `ai_instruction` texts from the pattern's findings
- Uses the most frequent instruction as the new guard's `ai_instruction`
- Appends the pattern signature and occurrence count as context

**Estimated lines**: ~150 (generator) + ~40 (scaffold template engine)

---

### Phase 4 — AI Implementation & Validation

**Purpose**: AI implements the proposed guard, the system validates it
catches the original pattern without excessive false positives, and the
guard enters the CI pipeline.

#### What exists today (~40%)

| Component | File | Role |
|---|---|---|
| `autonomy-loop` | `devctl/autonomy/` | Multi-round AI fix loop with triage, branching, checkpointing |
| `guard-run` | `devctl/guard_run_core.py` | Wraps AI commands with pre/post git snapshots, probe scanning, watchdog |
| `GuardGitSnapshot` | `guard_run_core.py:23` | Pre/post diff metrics (files changed, lines added/removed) |
| `WatchdogContext` | `guard_run_core.py:39` | Episode metadata (provider, retry count, escaped findings) |
| `feedback_sizing` | `autonomy/run_feedback.py` | Adaptive agent count based on stall/improve streaks |
| `bundle.tooling` task class | `AGENTS.md` | Verification bundle for tooling changes |
| `pytest` suite | `devctl/tests/` | 1098 tests covering guards, probes, governance models |
| `check --profile ci` | `devctl/commands/check.py` | Full CI check invocation |

#### What's new — `guard_implementation_task.py` (~130 lines)

**Implementation home**: `dev/scripts/devctl/governance/guard_implementation_task.py`

This module defines the structured task that the autonomy-loop executes
to implement a guard proposal.

```python
@dataclass(frozen=True)
class GuardImplementationTask:
    """Structured autonomy-loop task for implementing one guard proposal."""
    proposal: GuardProposal
    implementation_steps: tuple[str, ...]  # ordered steps for the AI
    validation_gate: GuardValidationGate   # pass/fail criteria
    rollback_on_failure: bool = True


@dataclass(frozen=True)
class GuardValidationGate:
    """Pass/fail criteria for a newly implemented guard."""
    max_fp_rate_pct: float = 5.0          # must be below this on test corpus
    must_catch_original: bool = True       # must catch the original pattern
    must_pass_existing_tests: bool = True  # must not break existing test suite
    must_pass_ci_profile: str = "quick"    # minimum CI profile that must pass


def build_implementation_steps(proposal: GuardProposal) -> tuple[str, ...]:
    """Generate the ordered implementation steps for the AI to follow."""
```

**Implementation steps generated** (the AI receives these as structured instructions):

1. Write `dev/scripts/checks/{guard_name}.py` using the scaffold from `proposal.scaffold_code`
2. Register in `script_catalog.py` under `_CHECK_SCRIPT_ENTRIES` or `_PROBE_SCRIPT_ENTRIES`
3. Register in `quality_policy_defaults.py` under the appropriate registry
4. Write test file `dev/scripts/devctl/tests/checks/test_{guard_name}.py` with:
   - At least one test that triggers the detection (uses code from representative findings)
   - At least one test that verifies no false positive on clean code
5. Run `python3 dev/scripts/devctl.py check --profile quick` to verify no regressions
6. Run the new guard standalone and verify it catches the original pattern
7. Run `python3 -m pytest dev/scripts/devctl/tests/ -q` to verify test suite passes

**Validation gate execution** (~80 lines in `guard_validation.py`):

```python
def validate_guard_implementation(
    task: GuardImplementationTask,
    *,
    repo_root: Path,
) -> GuardValidationResult:
    """Run the Phase 5b gate: FP rate, original-pattern catch, test suite."""
```

The validation runs:
1. Execute the new guard on the full codebase, collect findings
2. Cross-reference findings against the governance review ledger:
   - Findings matching known `confirmed_issue` or `fixed` rows → true positives
   - Findings matching known `false_positive` rows → false positives
   - New findings with no ledger match → manually counted, flagged for review
3. Compute `fp_rate_pct` from the cross-reference
4. Check that at least one finding matches the original `pattern_signature`
5. Run `pytest` on the new test file
6. If all gates pass: `GuardValidationResult(passed=True, ...)`
7. If any gate fails: `GuardValidationResult(passed=False, failure_reason=..., ...)`

**Autonomy-loop orchestration**:

The existing autonomy-loop already handles multi-round AI tasks with:
- `triage-loop` for work selection
- `guard-run` for pre/post snapshot safety
- `feedback_sizing` for adaptive round management
- `phone_status` for operator visibility

The new module plugs in as a **task source** for the autonomy-loop:
1. `pattern_recognizer.py` runs at the start of each autonomy cycle
2. If `guard_proposal_ready` patterns exist, `guard_proposal_generator.py`
   creates `GuardProposal` objects
3. Each proposal becomes a `GuardImplementationTask` in the autonomy queue
4. The existing round-based loop picks it up, gives it to the AI, validates
5. On validation success, the guard is committed and enters CI
6. On validation failure, the task is marked as `deferred` with the failure
   reason, and the pattern's `recurrence_risk` is preserved for retry

**Estimated lines**: ~130 (task) + ~80 (validation) + ~30 (autonomy queue wiring)

---

### Phase 5 — Integration & Learning

**Purpose**: The new guard enters CI, catches future occurrences
deterministically, and the system records the closure — feeding back
into Phase 2 for continuous improvement.

#### What exists today (~35%)

| Component | File | Role |
|---|---|---|
| `bundle.tooling` | `AGENTS.md` | Post-edit verification for tooling changes |
| `governance-review --record` | `devctl/commands/governance/review.py` | Records verdicts with `prevention_surface`, `guidance_id`, `guidance_followed` |
| `quality_feedback` | `devctl/governance/quality_feedback/` | Tracks per-check `precision_pct`, `fp_rate_pct`, `cleanup_rate_pct` over time |
| `ImprovementDelta` | `quality_feedback/models.py:195` | Tracks `overall_score_delta`, `improved_checks`, `degraded_checks` between snapshots |
| `startup_signals.py` | `devctl/runtime/startup_signals.py` | Loads governance review summary + guidance hotspots at session start |
| `operational_feedback.py` | `devctl/context_graph/operational_feedback.py` | Recent fix history, quality recommendations, watchdog digest for prompts |

#### What's new

**5a. Guard provenance tracking** (~40 lines)

Add to the governance review row builder:

```python
# New fields in GovernanceReviewInput
guard_created: str | None = None        # e.g., "check_nested_dict_return"
guard_created_from_proposal: str | None = None  # proposal_id hash
```

When a guard is successfully created from a proposal, the system records:
```
governance-review --record \
  --signal-type guard \
  --check-id check_nested_dict_return \
  --verdict fixed \
  --finding-class missing_guard \
  --recurrence-risk systemic \
  --prevention-surface guard \
  --notes "Auto-generated from recurring pattern (5 occurrences across 3 sessions)" \
  --guard-created check_nested_dict_return \
  --guard-created-from-proposal abc123def456
```

**5b. Quality feedback integration** (~30 lines)

After the guard runs in CI for 2+ sessions:
1. `quality_feedback` computes its `CheckQualityScore` automatically
   (this already happens for all registered checks)
2. The `recommendation_engine` can flag it if FP rate drifts above threshold
3. `ImprovementDelta` tracks whether the new guard improved the overall score

**5c. Pattern closure feedback** (~50 lines in `pattern_recognizer.py`)

```python
def recognize_patterns(...) -> list[RecurringPattern]:
    # ... existing grouping logic ...

    # Phase 5 closure: exclude patterns that already have an active guard
    active_guards = set(CHECK_SCRIPT_FILES.keys()) | set(PROBE_SCRIPT_FILES.keys())
    for pattern in patterns:
        if pattern.proposed_guard_name and pattern.proposed_guard_name in active_guards:
            pattern = replace(pattern, guard_proposal_ready=False)
            # The pattern still exists in the ledger but is no longer a proposal
            # candidate because its guard is already in CI
```

**5d. Startup context enrichment** (~30 lines in `startup_signals.py`)

```python
def load_startup_quality_signals(repo_root: Path) -> dict[str, object]:
    # ... existing loads ...
    self_strengthening = _load_self_strengthening_status(repo_root)
    if self_strengthening:
        signals["self_strengthening"] = self_strengthening

def _load_self_strengthening_status(repo_root: Path) -> dict[str, object] | None:
    """Load pattern recognition status for bootstrap context."""
    # Returns: {
    #   "ready_patterns": 3,       # patterns qualifying for guard generation
    #   "guards_created": 2,       # guards created from patterns (lifetime)
    #   "latest_guard": "check_nested_dict_return",
    #   "pending_validation": 1,   # proposals awaiting FP validation
    # }
```

**5e. Learning feedback into Phase 2** (the closed loop)

The learning cycle closes through three existing mechanisms, plus one new one:

1. **Existing**: When the new guard catches a future occurrence, it produces
   a `FindingRecord` with the same `check_id` as the guard. This finding
   enters the governance review ledger, incrementing the `occurrence_count`
   for that `check_id` — but now it's a guard finding, not a pattern finding.
   The pattern's `recurrence_risk` effectively drops because the guard is
   catching it deterministically.

2. **Existing**: `quality_feedback` tracks the guard's `cleanup_rate_pct`.
   If the rate is high, the `recommendation_engine` leaves it alone. If low,
   it generates a `cleanup_stall` recommendation.

3. **Existing**: `ImprovementDelta` records whether adding the guard improved
   or degraded the overall maintainability score. If degraded (too many FPs),
   it shows up as a `degraded_checks` entry.

4. **New**: `pattern_recognizer.py` reads guard creation provenance from the
   ledger and computes a `guard_effectiveness` metric:

```python
@dataclass(frozen=True)
class GuardEffectivenessMetric:
    """Tracks how well a self-generated guard is performing."""
    guard_name: str
    source_proposal_id: str
    findings_caught: int          # findings attributed to this guard
    fp_count: int                 # false positives on this guard
    fp_rate_pct: float
    sessions_active: int          # sessions since guard entered CI
    original_pattern_recurrence: int  # how many times the original pattern fired since
    effectiveness: str            # "effective" | "noisy" | "insufficient" | "pending"
```

Effectiveness classification:
- `effective`: `fp_rate_pct < 5%` AND `original_pattern_recurrence == 0`
- `noisy`: `fp_rate_pct >= 5%` → triggers recommendation to tune or demote
- `insufficient`: `original_pattern_recurrence > 0` despite guard being active → guard has a detection gap
- `pending`: fewer than 2 sessions of data

**Estimated lines**: ~150 total (40 provenance + 30 quality feedback + 50 closure + 30 startup)

---

### Complete Data Flow Diagram

```
                    Phase 1: DETECT
                    ================
  Guards (64)  ──┐
  Probes (25)  ──┤──> FindingRecord ──> GovernanceReviewInput
  AI Review    ──┘    (finding_id,      (finding_class,
                       check_id,         recurrence_risk,
                       ai_instruction)   prevention_surface,
                                         pattern_signature)
                           │
                           ▼
                    governance_review_log.jsonl
                           │
                    Phase 2: RECOGNIZE
                    ==================
                           │
                           ▼
                    pattern_recognizer.py
                    ┌──────────────────────┐
                    │ GROUP BY:            │
                    │  (check_id,          │
                    │   finding_class,     │
                    │   prevention_surface)│
                    │                      │
                    │ FILTER:              │
                    │  count >= 3          │
                    │  risk ∈ {recurring,  │
                    │          systemic}   │
                    └──────────────────────┘
                           │
                           ▼
                    RecurringPattern
                    (guard_proposal_ready=True)
                           │
                    Phase 3: PROPOSE
                    =================
                           │
                           ▼
                    guard_proposal_generator.py
                    ┌──────────────────────────┐
                    │ 1. Check not duplicate    │
                    │ 2. Route guard type       │
                    │ 3. Estimate FP risk       │
                    │ 4. Generate scaffold      │
                    │ 5. Set decision_mode      │
                    │ 6. Build registration     │
                    └──────────────────────────┘
                           │
                           ▼
                    GuardProposal
                    (scaffold_code, decision_mode)
                           │
              ┌────────────┴────────────┐
              │ decision_mode routing   │
              ▼                         ▼
        auto_apply              approval_required /
              │                 recommend_only
              │                         │
              ▼                         ▼
        Phase 4: IMPLEMENT       Queue for human
        =====================    review
              │
              ▼
        autonomy-loop
        ┌────────────────────────────┐
        │ 1. Write guard .py         │
        │ 2. Register in catalogs    │
        │ 3. Write tests             │
        │ 4. Run validation gate:    │
        │    - FP rate < 5%          │
        │    - Catches original      │
        │    - Tests pass            │
        │    - CI profile passes     │
        └────────────────────────────┘
              │
        ┌─────┴─────┐
        ▼           ▼
      PASS        FAIL
        │           │
        ▼           ▼
        Phase 5:  Mark deferred,
        INTEGRATE preserve pattern
        ===========
        │
        ▼
  ┌─────────────────────────────┐
  │ 1. Guard enters CI          │
  │ 2. governance-review records│
  │    guard_created linkage    │
  │ 3. quality_feedback tracks  │
  │    precision/FP/cleanup     │
  │ 4. startup_signals loads    │
  │    self_strengthening status│
  │ 5. pattern_recognizer       │
  │    excludes closed patterns │
  │ 6. GuardEffectiveness       │──────> Back to Phase 2
  │    monitors guard health    │        (continuous cycle)
  └─────────────────────────────┘
```

---

### Per-Phase Scoring Summary

| Phase | What Exists | % | What's New | New Lines | Most Impactful First Build |
|---|---|---|---|---|---|
| 1. Detection & Classification | Guards, probes, FindingRecord, GovernanceReviewInput, ledger | 75% | `pattern_signature`, `proposed_guard_name`, `proposed_guard_fp_risk` fields; AGENTS.md instruction surface | ~40 | `pattern_signature` field — without it, Phase 2 cannot group precisely |
| 2. Pattern Recognition | Ledger reader, stats builder, latest_rows_by_finding, recommendation_engine | 30% | `pattern_recognizer.py` with `RecurringPattern` model, startup_signals wiring, `devctl pattern-report` command | ~190 | `pattern_recognizer.py` — this is the brain of the loop |
| 3. Guard Proposal Generation | Probe template, script_catalog, quality_policy, check_support, FP models | 20% | `guard_proposal_generator.py` with `GuardProposal` model, scaffold template engine, FP estimator | ~190 | `generate_guard_proposal()` — converts patterns into actionable scaffolds |
| 4. AI Implementation & Validation | autonomy-loop, guard-run, feedback_sizing, pytest suite, bundle.tooling | 40% | `guard_implementation_task.py`, `guard_validation.py`, autonomy queue wiring | ~240 | `GuardValidationGate` — the quality gate that prevents bad guards from entering CI |
| 5. Integration & Learning | governance-review, quality_feedback, ImprovementDelta, startup_signals, operational_feedback | 35% | Guard provenance fields, pattern closure logic, GuardEffectivenessMetric, startup enrichment | ~150 | `GuardEffectivenessMetric` — closes the loop by measuring whether self-generated guards actually work |
| **TOTAL** | | | | **~810** | |

---

### The ONE Most Impactful Piece to Build First

**`pattern_recognizer.py`** (~120 lines).

Rationale:
1. It is the prerequisite for every downstream phase
2. It uses ONLY existing data (`governance_review_log.jsonl` rows)
3. It requires ZERO new infrastructure — just reads, groups, and returns typed data
4. It immediately answers the question "what patterns keep recurring?" which
   is currently only answerable by human inspection of the ledger
5. It can be validated by running it against the existing 110-entry
   `finding_reviews.jsonl` and checking the output makes sense
6. Once built, it unblocks Phase 3 (proposals) and Phase 5c (closure detection)
   in parallel
7. It plugs directly into `startup_signals.py` so every AI session gets
   "here are the patterns that keep recurring" at bootstrap

**Second priority**: `check_prevention_surface_closure.py` (~80 lines, already
described in the Meta-Finding section above). This is the self-referential
guard that blocks CI if someone classifies `missing_guard` without proposing
the guard. It makes the system REQUIRE closure on every gap it finds.

Together, these two pieces (~200 lines) create the minimal self-strengthening
loop: detect pattern recurrence, require closure on gaps, and report what
needs guards. Everything else (scaffold generation, AI implementation,
validation gates) builds on top of this foundation.

---

### Relationship to Existing Gaps

This architecture directly implements or subsumes several intake gaps:

| Intake Gap | Relationship |
|---|---|
| Gap 1 (failure-rule ledger) | Phase 2 pattern recognition PRODUCES the dynamic failure rules; Phase 5 startup enrichment INJECTS them |
| Gap 8 (bad pattern recall) | Phase 2 `RecurringPattern` + Phase 5d startup context IS the bad pattern index |
| Gap 3 (convergence proof) | Phase 4 `GuardValidationGate` provides per-guard convergence evidence; Phase 5 `GuardEffectivenessMetric` provides system-level convergence |
| Gap 6 (reason traces) | Phase 1 `pattern_signature` + Phase 3 `GuardProposal.source_finding_ids` provide full traceability |
| Meta-finding (system doesn't guard itself) | Phase 3 + Phase 4 = the system generating its own guards; `check_prevention_surface_closure` = the system enforcing that it does so |
| D6 (governance-review waiver rate → probe trust) | Phase 5 `GuardEffectivenessMetric.fp_rate_pct` feeds directly into probe trust adjustment |

---

### Tracked Plan Owner

This architecture spans two existing plan owners:

- **MP-375** (probe-feedback-loop): Phases 1-3 (detection, recognition, proposal)
  — these extend the existing probe lifecycle with self-improvement
- **MP-377** (authority-loop): Phases 4-5 (implementation, validation, learning)
  — these extend the autonomy system with guard-generation tasks

No new MP needed. The work is incremental extensions to two active plans.

## Full-System Audit (8-Agent Deep Sweep)

Final comprehensive audit across CLI dispatch, governance data flow, autonomy
loops, runtime contracts, check orchestration, plan alignment, coderabbit/ralph,
and operator console. Findings organized by subsystem.

### CLI Dispatch Layer

- **68 commands registered**, only 8 referenced in bundles (expected — most
  are standalone)
- **`triage-loop` and `mutation-loop` skip startup gate** despite modifying
  repo state. Safety gap — add to gated commands.
- **No horizontal command chaining** — commands are artifact-centric, not
  workflow-centric. Each writes to `dev/reports/`, downstream reads from same
  paths. No live piping.
- **`swarm_run` naming inconsistency** — uses underscore while all other
  autonomy commands use hyphens.

### Governance Data Flow

- **3 of 6 governance commands are dead-ends**: `governance-export`,
  `governance-bootstrap`, `governance-draft` produce output consumed by
  zero downstream commands.
- **Maintainability score (60/100, Grade D) drives zero decisions** — computed
  by quality_feedback, stored in snapshot, displayed in console, but no merge
  gate, no approval escalation, no autonomy-loop strategy uses it.
- **Recommendation engine output is advisory-only** — generates prioritized
  recommendations (FP reduction, cleanup stall, complexity, threshold tuning)
  but no automated system acts on them.
- **Improvement tracker computed but unused** — compares current vs previous
  quality snapshot, stores delta, but no gate checks "did quality improve?"

### Autonomy/Loop Subsystem (10 Critical Disconnections)

This is the subsystem with the most disconnections:

1. **Each autonomy round starts cold** — round N+1 has zero knowledge of
   round N's triage report, checkpoint packet, or unresolved issues.
2. **Triage-loop and mutation-loop don't communicate** — mutations created
   by one are invisible to the other.
3. **Feedback sizing computes decisions but doesn't apply them** — the
   `next_agents` decision is computed but may not reach the next swarm spawn.
4. **Watchdog episodes not consumed by autonomy decisions** — guard flakiness
   is invisible to the loop; if a guard times out 5 rounds in a row, the
   loop keeps calling it.
5. **`autonomy-report` produces artifacts nobody reads** — not used as input
   to next autonomy run or operator console.
6. **Checkpoint packets written but not queried by next round** — recommended
   next actions from round N are forgotten by round N+1.
7. **`recommend_agent_count()` ignores feedback history** — pure forward-
   looking heuristic, zero historical awareness.
8. **Guidance `approval_required` doesn't pause autonomy loop** — high-risk
   guidance visible in packets but doesn't gate progression.
9. **Loop branch strategy is static** — can't adapt based on divergence
   accumulation across rounds.
10. **Probe scan risk doesn't gate loop continuation** — even if probe_scan
    reports risk="high", loop continues.

**Root cause**: The autonomy system produces rich packets (checkpoint,
terminal, guidance contracts, episodes) but **packets are sinks, not
sources**. Each component reads fresh inputs and produces outputs, but few
components read prior outputs as guidance for the next invocation.

### Runtime Contracts

- **All major contracts have producer-consumer coverage** — no orphaned
  contracts in the core pipeline.
- **7 of 10 contract types lack version constants** — StartupContext,
  WorkIntakePacket, ReviewState, RoleProfile, PushEnforcement, ControlState,
  StartupReceipt define `schema_version: int = 1` as field defaults but no
  module-level `*_SCHEMA_VERSION` constant for programmatic discovery.
- **finding_contracts.py defines 8 version constants but only 2 are exported**
  in `__init__.py`.

### Check Orchestration

- **Pipeline is well-structured** (4-phase, Boolean AND composition) but has
  optimization opportunities:
  - Phase 3 runs steps sequentially that could be parallel (~15-30% speedup)
  - Quick profile still runs expensive VoiceTerm-only guards
  - No guard cost metadata (cheap/medium/expensive) for profile optimization
- **Clippy → clippy-high-signal-guard** is the only inter-guard file-based
  dependency — works but undocumented.
- **Multiple guards re-parse same files independently** — no parse caching.

### Plan Alignment

- **Plan docs are highly accurate** — 128 open items, ~120 correctly marked.
- **3 items should be updated**:
  - "Replace boolean-only Session Resume" → CLOSED (SessionResumeState exists)
  - "Land PlanTargetRef/WorkIntakePacket/CollaborationSession" → Refine:
    PlanTargetRef + WorkIntakePacket landed, only CollaborationSession remains
  - "Turn report-only fields into live inputs" → Mostly complete, narrow
    remaining scope
- **3 referenced evidence files don't exist** (UNIVERSAL_SYSTEM_EVIDENCE.md,
  GUARD_AUDIT_FINDINGS.md, ZGRAPH_RESEARCH_EVIDENCE.md) — acceptable as
  cold/reference tier.

### CodeRabbit/Ralph Integration (3 Critical Gaps)

Ralph is a production-quality stateless AI fixer but NOT a learning system:

1. **No failed-attempt recovery** — when attempt 1 fails checks, attempt 2
   starts fresh with zero knowledge of why attempt 1 failed. Previous
   ralph-report.json is never loaded or analyzed.
2. **Guidance waivers are write-only** — when Claude waives probe guidance,
   the reasoning is captured in ralph-report.json but never recorded to
   governance-review or fed back to future attempts.
3. **Ralph-report.json is a leaf artifact** — written but consumed by zero
   downstream systems. Not fed into governance-review, not displayed in
   operator console, not analyzed for patterns.

Additionally:
- **Probe guidance loaded in 2 separate codepaths** (devctl + coderabbit)
  with risk of divergence.
- **Watchdog metrics and file temperature not in Claude prompt** — Ralph
  doesn't know which files are hotspots or which guards are flaky.

### Operator Console

- **Reads quality_feedback, watchdog, ralph_guardrail, quality_backlog** ✓
- **Does NOT read**: probe findings (13 advisory checks), governance-review
  ledger (finding lifecycle), external findings, recurring patterns.
- **Read-only for governance** — cannot approve/dismiss findings from UI
  (exception: operator approvals via record_operator_decision).
- **Has parallel data loading from devctl** — loads bridge.md and
  review_state.json directly instead of using StartupContext/WorkIntakePacket.
  Console may see stale governance data if startup context has fresher packets.
- **Mobile app displays subset** — phone_status has compact view but also
  lacks probe findings and governance-review ledger.

## Complete Disconnection Inventory

All disconnections found across the entire system, sorted by impact:

| # | Producer → Consumer Gap | Subsystem | Impact | Fix Size |
|---|---|---|---|---|
| 1 | Autonomy round N → round N+1 (cold start) | Autonomy | Critical | ~50 lines |
| 2 | Ralph attempt N-1 failures → attempt N prompt | Ralph | High | ~40 lines |
| 3 | Watchdog episodes → autonomy loop decisions | Autonomy | High | ~30 lines |
| 4 | Feedback sizing → swarm agent count | Autonomy | High | ~20 lines |
| 5 | Maintainability score → any decision gate | Governance | High | ~20 lines |
| 6 | Ralph-report.json → governance-review ledger | Ralph | High | ~30 lines |
| 7 | Recommendation engine → automated action | Governance | Medium | ~40 lines |
| 8 | Probe scan risk → autonomy loop gate | Autonomy | Medium | ~15 lines |
| 9 | Checkpoint packets → next round planning | Autonomy | Medium | ~30 lines |
| 10 | Guidance approval_required → autonomy pause | Autonomy | Medium | ~20 lines |
| 11 | Triage output → autonomy-loop input | CLI | Medium | ~25 lines |
| 12 | Probe findings → operator console display | Console | Medium | ~40 lines |
| 13 | Governance-review ledger → console display | Console | Medium | ~40 lines |
| 14 | ContextGraphDelta → decision logic | Context graph | Medium | ~20 lines |
| 15 | Quality feedback → decision_mode escalation | Governance | Medium | ~20 lines |
| 16 | Temperature shifts → approval gating | Context graph | Low | ~15 lines |
| 17 | Cleanup rate → probe trust levels | Governance | Low | ~15 lines |
| 18 | governance-export → any feedback loop | Governance | Low | Design only |
| 19 | Improvement tracker → any gate | Governance | Low | ~15 lines |
| 20 | Version constants → __init__.py exports | Runtime | Low | ~30 lines |

**Total new wiring: ~530 lines** to close all 20 disconnections.

## Grand Total: Everything Found

| Category | Count | New Lines |
|---|---|---|
| Gaps (1-17) | 17 | ~1,635 |
| Feedback loop wiring (D1-D7) | 7 | ~125 |
| Self-strengthening loop (5 phases) | 1 system | ~810 |
| Systemic findings (A-G) | 7 | Architectural |
| Meta-guards (self-improvement) | 4 | ~390 |
| Full-system disconnections (1-20) | 20 | ~530 |
| Startup intelligence expansion | 7 items | ~200 |
| Plan corrections needed | 3 items | ~10 |
| **TOTAL** | | **~3,700** |

All work is incremental on existing infrastructure. No new architecture
needed. The system has all the sensors — it just needs the wires connected.

## Full-System Deep Sweep (Final 5-Agent Pass)

### CI Workflow Coverage: 60+ Governance Commands, Zero in CI

15 of 30 CI workflows use devctl, but ONLY for core CI (build/test/lint/
security), autonomy loops, and release flows. The entire governance/quality
command surface is absent from CI:

- `quality-policy` — not in any workflow
- `probe-report` — not in any workflow
- `governance-review` — not in any workflow
- `governance-quality-feedback` — not in any workflow
- `platform-contracts` — not in any workflow (only the closure GUARD runs)
- `startup-context` — not in any workflow
- `context-graph` — not in any workflow

The `startup_authority_contract` guard IS in 2 workflows (release_preflight,
tooling_control_plane). But the commands that PRODUCE governance data are
never triggered by CI — only guards that VALIDATE it run.

`mutation_testing.yml` does not exist as a file — the workflow is likely
defined elsewhere or has been removed. This explains the 12 days of
cancelled mutation runs.

### Test Coverage: 18 Subsystems with Zero Tests

2,007 tests collected. 6 subsystems tested (commands, context_graph,
governance, platform, review_channel, runtime). But **18 subsystems have
zero test coverage** across ~82 Python files:

| Untested Subsystem | Files | Risk |
|---|---|---|
| **autonomy** | 21 | CRITICAL — operational feedback sizing, no tests |
| **triage** | 12 | HIGH — backlog prioritization untested |
| **cli_parser** | 10 | MEDIUM — arg routing |
| **data_science** | 7 | MEDIUM — metrics aggregation |
| **probe_topology** | 7 | MEDIUM — hotspot calculation |
| **process_sweep** | 7 | MEDIUM — cleanup logic |
| **watchdog** | 5 | HIGH — episode tracking untested |
| **quality_backlog** | 5 | MEDIUM — priority scoring |
| **integrations** | 5 | LOW — external sync |
| **security** | 5 | MEDIUM — audit patterns |
| **publication_sync** | 4 | LOW — external sync |
| **repo_packs** | 4 | MEDIUM — path config |
| **loops** | 4 | HIGH — fix policy untested |
| **mutation_loop** | 4 | LOW — mutation remediation |
| **rust_audit** | 4 | LOW — Rust-specific |
| **probe_report** | 2 | MEDIUM — report aggregation |
| **path_audit_support** | 2 | LOW — migration |
| **probe_topology_support** | N/A | LOW |

**Highest risk**: autonomy (21 files, 0 tests) — this is the feedback
sizing system that decides agent count and loop continuation.

### Config/Template Layer: 7-10 Orphaned Files

32 files in `dev/config/` (123KB). 21 actively consumed. 7-10 orphaned:

- `voiceterm.json` quality preset — 11.5KB, zero code references
- `claude_voice_skill.template.md` — referenced in policy but no
  SurfaceSeed in bootstrap_surfaces.py (config-code drift)
- `portable_devctl_repo_policy.template.json` — not wired to
  governance-bootstrap copy flow
- `portable_governance_repo_setup.template.md` — not wired to rendering
- 3 JSON schemas (episode, eval_record, finding_review) — defined but
  zero validation code consumes them

**Blocks portable-governance export**: The portable templates exist but
aren't integrated into the `governance-bootstrap` or `governance-export`
command flows.

### Rust-Python Boundary: Clean But One-Directional

321 Rust files (352 context-graph nodes) + ~1,739 Python nodes. The
boundary is cleanly partitioned:

- **Rust → Python**: Single choke-point `DevCommandBroker` with 14
  hardcoded `DevCommandKind` enum variants. No dynamic arg construction.
- **Python → Rust**: Zero instances (outside test harnesses).
- **One bypass**: `ops_snapshot.rs` calls `python3` directly with
  hardcoded args (bypasses broker logging/timeouts). Low risk but
  undocumented.
- **936 panic sites in Rust** across 127 pub functions — tracked by guards
  but could benefit from a dedicated panic-safety audit guard.
- **No Rust→Python contract schema** — devctl_args() returns static str
  slices. If devctl.py changes a command signature, Rust won't know.

### Live System Coherence: All Green, One Path Bug

- Platform contract closure: 9 runtime contracts, 8 artifact schemas,
  6 field routes, 2 families — ALL pass, 0 violations.
- Quality policy: 6 configs active, 2 platform layer boundary rules
  enforced.
- Governance review: 95 findings, 0% FP rate, 65.26% cleanup rate.
- Startup authority: 10/10 checks pass.
- Startup context carries: governance_review + watchdog + command_reliability
  + guidance_hotspot (push_policy.py, 14 hints).

**BUT**: probe_report is MISSING from startup quality_signals due to
the path bug documented below. And guidance_hotspots returns empty when
there are zero probe findings (which happens when probes scan 0 files
in working-tree mode).

## Live System Test Findings (8 Agents Running Every Command)

### Test Suite: 3,089 Tests, 4 Failures

| Suite | Passed | Failed |
|---|---|---|
| Full devctl | 2,003 | 4 |
| Runtime | 118 | 0 |
| Context graph | 95 | 0 |
| Governance | 123 | 1 |
| Checks | 168 | 0 |
| Operator console | 582 | 0 |

4 failures (3 distinct bugs):
1. `test_doc_authority.py:132` — classifier returns `reference` not `guide`
2. `test_check_review_channel_bridge.py` — resolved bridge without promoted
   next task no longer flags correctly
3. `test_mobile_status.py` (2 tests) — expect `stale`, get `runtime_missing`

### Probe System: Blind on Clean Trees, 4185 Findings on Full Scan

| Mode | Files Scanned | Findings |
|---|---|---|
| Default (working-tree) | **0** | **0** — BLIND |
| `--since-ref HEAD~10` | 459 | 152 (97 HIGH, 55 MED) |
| `--since-ref origin/master` | 11,644 | 4,185 (2,528 HIGH, 1,657 MED) |

The system has 4,185 real findings but shows 0 by default. No
`--full-scan` mode exists. After every commit, probes go blind.

### Context Graph Queries: Work But Have Systemic Issues

| Query | Matched | Neighbors | Edges | Confidence |
|---|---|---|---|---|
| `startup_context` | 4 | 51 | 100 | high |
| `work_intake` | 6 | 37 | 169 | high |
| `ralph_prompt` | 1 | 28 | 27 | high |
| `autonomy_loop` | 5 | 38 | 113 | high |

**5 systemic graph issues found by testing**:

1. **Guard-edge cartesian explosion** — every query returns
   N_guards × N_files guard edges. For `work_intake`: 169 edges total
   but only ~20 are useful imports. The other 149 are guard-to-file
   noise that drowns the signal.
2. **Plan-to-file linking is weak** — only `startup_context` had a
   `scoped_by` plan edge. The autonomy, ralph, and work_intake
   subsystems are plan-orphans despite having active plan docs.
3. **Command routing edges sparse** — `cmd:startup-context → routes_to`
   worked, but `cmd:autonomy-loop → routes_to` did not appear.
4. **No cross-subsystem edges** — graph has imports within subsystems
   but no concept-level edges between them. AI cannot see "autonomy
   depends on review-channel."
5. **Diff mode only tracks temperature** — cannot show "edge X added"
   or "file Y gained a new import." Structural changes invisible.

### Data Flow Chain Tests: 1 Break Found

| Chain | Status |
|---|---|
| probe-report → startup-context | **FLOWS** |
| governance-review → startup-context | **FLOWS** |
| **quality-feedback → startup-context** | **BROKEN** — maintainability score (60/100, Grade D), recommendations, Halstead MI never reach startup packet |
| data-science → startup-context | **FLOWS** |
| context-graph → prompt guidance | **GAP** — topology only, no actionable prompt fragments |

### Check-Router vs Startup-Context Bundle Mismatch

startup-context selects `bundle.tooling` (from plan analysis).
check-router selects `bundle.docs` (from 0 committed changes in
since-ref range). An AI following both gets conflicting signals. Root
cause: check-router only considers committed diffs, not dirty worktree.

### Governance Command Outputs

| Command | Useful to AI? | Key Finding |
|---|---|---|
| governance-review | HIGH | 95 findings, 65.26% cleanup, but no severity breakdown |
| quality-feedback | HIGH | 60/100 Grade D, but 3 of 7 sub-scores say "no evidence loaded" |
| quality-policy | HIGH | 32 guards + 25 probes fully enumerated |
| doc-authority | HIGH | 17 budget violations, 4 overlaps, 8 consolidation candidates |
| platform-contracts | MEDIUM | 14 contracts described, but no health status |
| governance-draft | LOW | Duplicates bootstrap, unique value is push enforcement only |

### AI Bootstrap Experience Test

An agent ran the exact CLAUDE.md bootstrap flow and reported what it
could and couldn't determine:

**CAN determine**: repo shape, where to resume work, push/checkpoint
state, aggregate quality numbers, top hotspot files, key commands.

**CANNOT determine**: which 19 findings are open (no file/severity
detail), which guards are flaky (only aggregate success rate), which
probes have high FP rates (no per-probe breakdown), what the 20
disconnections are, what temperature means, plan execution state for
17 of 18 plans.

**Verdict**: Bootstrap is effective for session resume but opaque about
system health details. AI operates with ~12% of available intelligence.

### Telemetry Systems

| System | Status | Data Quality |
|---|---|---|
| data-science | Active | 14,784 events, watchdog, adjudication tables |
| ralph-status | **Dormant** — no report artifacts exist |
| phone-status | **Dormant** — no autonomy run active |
| hygiene | Active | 1 stale publication, mutation badge 19 days old |
| status/report | Lean | Mutation score broken (invalid JSON) |

### Rust-Python Boundary

Clean one-directional flow via `DevCommandBroker` (14 hardcoded enum
variants). One bypass: `ops_snapshot.rs` calls python3 directly. 936
panic sites across 127 pub functions. No Rust→Python contract schema
(args are hardcoded static str slices).

### Config/Template Layer

32 config files, 21 active, 7-10 orphaned. Key drift:
`claude_voice_skill.template.md` referenced in policy but no
SurfaceSeed renders it. Portable governance templates not wired to
bootstrap/export commands.

## Fixes Applied This Session

### FIX 1: startup_signals.py probe path (APPLIED + VERIFIED, 1 line)

### FIX 2: ZGraph guard-edge noise filter (APPLIED + VERIFIED, ~10 lines)

`query.py::query_context_graph()` now filters guard edges from results
unless the query matched a guard node directly. Results:
- `work_intake` query: 169 edges → 31 edges (82% noise removed)
- `ralph_prompt` query: 27 edges → 4 edges (85% noise removed)
- `autonomy_loop` query: 113 edges → 21 edges (81% noise removed)
- Guard queries still work (test `code_shape` returns guard coverage)
- 95/95 context-graph tests pass

### FIX 3: ZGraph plan linkage from word matching — REVERTED

Initially implemented plan-stem ↔ directory-name word overlap to boost
plan coverage from 6% to 12%. Codex correctly identified this violates
the MP-377 contract: `scoped_by` is a typed ownership edge that must
come from registry/ownership data, not keyword guessing. The change
also inflated coverage by giving reference docs (audit.md, phase2.md)
ownership edges they shouldn't have.

**Reverted to policy-prefix-only plan linkage.** The real fix is to add
more docs-policy `trigger_prefixes` rules (explicit ownership) or to
extend `ProjectGovernance.path_roots` to carry per-plan scope prefixes.
That's a tracked MP-377 item, not a quick hack.

**Guard-edge filter tradeoff noted**: Codex found that `cli.py` queries
return 0 guard edges even though 46 exist in the full graph. The filter
removes noise for subsystem queries but hides "what guards protect this
file?" answers. Proper fix: add `--include-guards` flag to the query
command. Current filter is still a net improvement (80%+ noise removed).

Combined effect of surviving fixes: guard-edge filter makes queries
useful (31 edges instead of 169 for work_intake). Plan linkage remains
at 6% until explicit ownership data is added — that's correct behavior
for a system that refuses to guess ownership.

### FIX 1 (original): startup_signals.py probe path (APPLIED + VERIFIED)

Changed `dev/reports/probes/summary.json` → `dev/reports/probes/latest/summary.json`.
One line. Bootstrap now shows 4,188 hints across 594 files. Before: showed 0.
guidance_hotspots also restored (reads from same probe artifacts).

Probe hints verified accurate:
- `_build_editor_workbench` calls 25 functions → correctly flagged as hub
- `_build_color_groups_page` uses 33 identifiers → correctly flagged
- Decision packets carry correct `decision_mode=recommend_only` with rationale
- `bounded_next_slice` gives concrete function-level guidance

### ZGraph-Derived Findings (Running Context-Graph Programmatically)

**Plan linkage is extremely sparse**: Only 115 of 2,006 source files have
`scoped_by` plan edges. 1,891 files (94%) have no plan ownership in the
graph. Top unscoped: `dev/scripts/devctl/` (619 files), `rust/src/bin/`
(244), `dev/scripts/checks/` (193).

**120 high-fan-in files have no plan**: `config.py` (123 importers),
`common.py` (107), `check_bootstrap.py` (92), `cli.py` (57),
`repo_packs/__init__.py` (45). These are the most critical files in the
codebase and no plan doc claims responsibility.

**65 leaf-importer files identified**: Files with 0 importers but 3+
imports — validated as entry points (main.rs, test files, lib.rs), not
dead code. ZGraph correctly distinguishes these.

**Probe hints verified accurate**: The top hotspot
(`theme_editor.py`, 45 hints) has specific, correct findings:
`_build_editor_workbench` calls 25 functions (real coupling),
`_build_color_groups_page` uses 33 identifiers (real complexity).
Decision packets carry correct `recommend_only` modes with rationale
explaining why each is intentional design.

### ZGraph: Working Navigation, Not Yet Working Decision System

The context graph builds correctly (2,006 nodes, 38,080 edges) and
queries work. But it's a navigation/rendering tool, not a decision
engine. Here's exactly what needs to change:

**Problem 1: Guard-edge cartesian noise (149 of 169 edges are junk)**

Every query returns N_guards × N_matched_files. A `work_intake` query
returns 169 edges but only 20 are useful imports. The rest are
"guard X applies to file Y" which is true for every file.

Fix: Filter guard edges from query results by default. Add
`--include-guard-edges` flag for when you actually want them. ~20 lines
in `query.py::query_context_graph()`.

**Problem 2: Plan linkage is 6% (115 of 2,006 files)**

The `scoped_by` edge builder matches INDEX.md prose keywords to file
paths. This heuristic misses most files because INDEX.md entries
describe plan docs, not implementation files.

Fix: Extend `_collect_plan_scope_edges()` in `builder.py` to also match
plan doc `trigger_prefixes` from doc_policy rules AND the `path_roots`
from plan registry entries. The plan for `ai_governance_platform.md`
should scope `dev/scripts/devctl/`. ~40 lines in builder.py.

**Problem 3: No cross-subsystem edges**

The graph has imports (file → file) and contains (concept → file) but
no architectural edges (subsystem → subsystem). An AI can't see
"autonomy depends on review-channel."

Fix: In `concepts.py::build_concept_nodes()`, the `related_to` edge
already computes cross-concept import weight. But threshold is >= 2
imports, which misses weak coupling. Lower threshold to >= 1 AND add a
`depends_on` edge kind for concept-to-concept relationships that carry
the import count as metadata. ~30 lines.

**Problem 4: Edges don't feed decisions**

37,000 edges but zero consumed by any decision gate. Guards, probes,
triage, autonomy-loop — none query the graph.

Fix (staged):
- Stage 1: Wire `query_context_graph()` into `ralph_prompt.py` so
  Ralph sees the architectural neighborhood of each file it's fixing.
  When fixing `startup_context.py`, Ralph would see its 51 neighbors
  and 100 edges — understanding impact radius. ~30 lines.
- Stage 2: Wire graph temperature into `quality_backlog/priorities.py`
  so high-temperature files get higher priority scores. ~15 lines.
- Stage 3: Wire `ContextGraphDelta` (snapshot diff) into
  `autonomy_loop_rounds.py` so rising temperature triggers caution
  (approval_required). ~20 lines.
- Stage 4: Wire plan linkage into `triage` so unscoped files (no plan
  owner) get flagged as governance gaps. ~20 lines.

**Problem 5: Diff only tracks temperature, not structure**

`snapshot_diff.py` computes node/edge count deltas and temperature
shifts but can't show specific edge additions/removals.

Fix: The `compute_graph_delta()` function already computes
`added_edge_keys` and `removed_edge_keys` (lines 74-75). It reports
counts and samples. Extend to also report edge-kind breakdown:
"3 new import edges, 1 removed scoped_by edge." ~15 lines in
`snapshot_diff.py` and `snapshot_diff_render.py`.

**Total to make ZGraph a decision system: ~190 lines across 6 files.**

### CONFIRMED: New Claude Sessions Skip Bootstrap

A new Claude Code session opened on this repo and did NOT run the
CLAUDE.md bootstrap commands (startup-context, context-graph --mode
bootstrap). It went straight to reading files and chatting. The
bootstrap instructions are in CLAUDE.md Step 0-1 but nothing enforces
execution.

This is the same pattern as the checkpoint-enforcement gap: the system
DOCUMENTS what should happen but doesn't ENFORCE it. Unlike Codex
(which reads AGENTS.md and bridge.md), Claude Code reads CLAUDE.md as
passive context — it's treated as "guidelines" not "mandatory steps."

**Impact**: Every new Claude session starts without quality signals,
without probe findings, without governance verdicts, without the
work-intake packet. The AI operates blind until it happens to run the
right commands. The entire startup intelligence pipeline we built
(startup_signals, quality_signals, guidance_hotspots, bootstrap
packet) is bypassed.

**Fix options**:
1. Claude Code hooks — configure a `session-start` hook in
   `.claude/settings.json` that auto-runs startup-context before the
   first prompt. This is the mechanical fix.
2. Make CLAUDE.md Step 0 language stronger — "You MUST run this command
   BEFORE reading any files or responding to any task. If you skip this
   step, your decisions will be uninformed."
3. Add a startup receipt check to the beginning of every devctl command
   (already built in `startup_gate.py`) — but this gates devctl
   commands, not Claude's general file-reading behavior.

### CONFIRMED BREAK: quality-feedback → startup-context

`governance-quality-feedback` produces maintainability score (60/100, Grade D),
Halstead MI (29.5), and recommendations. This data NEVER reaches
startup-context. `startup_signals.py` has no loader for
`quality_feedback_snapshot.json`. AI never sees the maintainability grade.

## Live System Test Findings (Running Actual Commands)

These issues were found by actually RUNNING devctl commands and examining
what the system produces vs what it claims to produce.

### BUG: probe-report scans 0 files when working tree is clean

`python3 dev/scripts/devctl.py probe-report --format md` in `working-tree`
mode scans ZERO files when there are no dirty files. 25 probes run but find
nothing because there's nothing to scan. With `--since-ref HEAD~5` it
immediately finds 6+ real findings.

**Impact**: After every commit, the probe system goes blind. The startup
context gets "0 hints" even on a codebase with known issues. AI sees a
clean bill of health that isn't real.

**Fix options**:
1. Default to `--since-ref origin/develop` (scan all branch changes)
2. Add `--full-scan` mode that scans all files in scope roots
3. Change startup_signals to use cached `latest/summary.json` from the
   last `--since-ref` run instead of triggering a fresh `working-tree` scan

### BUG: startup_signals.py has wrong path for probe_report

`startup_signals.py` line 40 reads from:
`dev/reports/probes/summary.json` (DOES NOT EXIST)

Actual file location:
`dev/reports/probes/latest/summary.json` (EXISTS, 1.1 MB)

**Impact**: Bootstrap quality_signals NEVER includes `probe_report` data.
The AI always sees governance_review + watchdog + command_reliability but
NEVER sees probe findings. This has been broken since the startup_signals
module was created.

**Fix**: Change path to `dev/reports/probes/latest/summary.json`. One line.

### CI Check Status (Full Profile)

`check --profile ci` passes all guards on the current tree. All 34 AI
guards and 25 probes report ok=True with 0 violations. The system is
structurally healthy — the issues are in data flow, not code quality.

### Snapshot Diff Shows Stable Architecture

`context-graph --mode diff` between last two snapshots shows 0 changes
(same commit, stable temperature, no edge additions/removals). The graph
infrastructure works but produces no delta signal when nothing changed —
expected behavior.

## Conversation-Tail Delta (2026-03-25 Re-audit, Lines 4907-5668)

The line-4907+ re-read did **not** uncover another broad bootstrap,
self-hosting, or compiler-framing gap. Those themes are already covered in
the active `MP-377` plan stack:

- compiler-pass framing already landed in
  `dev/active/ai_governance_platform.md`
- bounded startup/progressive context expansion is already tracked through
  `startup-context`, `WorkIntakePacket`, warm refs, and the query-engine
  follow-up in `dev/active/platform_authority_loop.md`
- governed-markdown self-hosting is already tracked through `DocPolicy`,
  `DocRegistry`, `PlanRegistry`, and the self-hosting simplification program

The one useful under-specified idea from that tail is narrower and should be
tracked as a deferred graph/runtime optimization rather than as a new
foundational architecture lane.

### Gap 18: Graph Compaction / Normalization Before AI Traversal

**Conversation-tail insight**: apply compiler-style simplification before AI
reasoning so the model traverses a smaller, more deterministic structure.

**Repo-specific translation**: do **not** interpret this literally as AST-level
dead-code elimination or function inlining. The current VoiceTerm graph is
file/plan/command/concept-level, not function-level. The useful missing slice
is a generated-only graph compaction pass that improves startup/query routing:

- strip or downweight known render-only/noisy relations in default query paths
- precompute bounded high-signal neighbor sets for common startup/query cases
- preserve canonical refs while separating "routing-grade" edges from
  "render-only" edges
- keep the pass reversible and disposable so it never becomes a second
  authority store

**What exists**: `query_context_graph()` already filters generic guard-edge
fan-out, and `platform_authority_loop.md` already tracks honest confidence,
bounded inference, and startup/query-engine rollout.

**What's missing**:
- no explicit normalization/compaction phase between `build_context_graph()`
  and `query_context_graph()`
- no typed metadata distinguishing routing-grade vs render-only edges
- no precomputed compact neighborhood for startup/work-intake consumers
- no explicit test proving compaction preserves canonical refs while reducing
  query noise

**Implementation home**: `dev/scripts/devctl/context_graph/builder.py`,
`dev/scripts/devctl/context_graph/query.py`, and likely a new small helper
such as `dev/scripts/devctl/context_graph/normalization.py`

**Tracked plan owner**: `MP-377`, after the current startup/query-engine
authority proof. Treat this as a post-authority-loop optimization, not as a
blocker ahead of startup-consumer closure.

**Size**: ~80-120 lines plus focused query/consumer regressions
