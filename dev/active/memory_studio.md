# Memory + Action Studio Plan (Semantic Memory + Agent Overlay)

Date: 2026-02-19
Status: Next primary product lane after Theme completion; active design/proof-path work is already underway for the operator-cockpit execution slice under `MP-233`, `MP-238`, and `MP-243` (execution mirrored in `dev/active/MASTER_PLAN.md` as MP-230..MP-255)
Scope: Turn VoiceTerm memory from transcript snippets into a structured, AI-usable
knowledge and action layer for Codex/Claude terminal workflows

`dev/active/MASTER_PLAN.md` remains the canonical execution tracker. This file
is the architecture/spec + quality gates for the Memory track.

## Product Goal

Build a first-class `Memory + Action Studio` so VoiceTerm can:

- capture what happened (user, assistant, commands, outcomes) in machine-usable form
- retrieve relevant context fast and accurately by topic/task/time
- generate deterministic context packs for AI prompts and handoffs
- run safe terminal actions from inside the overlay (with policy + approvals)

This is the core differentiator: voice + terminal orchestration + semantic memory
+ safe actions in one local-first workflow.

## Differentiation Targets vs ChatGPT + Claude

The feature must do more than generic assistant memory:

- auditable memory with strict provenance (`where did this come from?`)
- project-scoped memory rooted in terminal reality (commands, files, tests, outcomes)
- deterministic context packs that are reproducible and diffable
- model-agnostic output so Codex, Claude, and future backends can consume the same pack
- validated derived memory cards with citations + staleness policy (not raw chat recall only)
- explicit safety policy for action execution (not silent background mutation)

Why this is distinct:

- ChatGPT memory is user-level personalization, not project-grounded terminal execution memory.
- Claude Code memory is file-based and useful, but does not provide a first-class structured
  event store + retrieval scoring + action audit in one local overlay loop.

## Why This Matters

Current memory surfaces are useful but limited:

- `transcript_history.rs` stores bounded rows for browse/replay
- `session_memory.rs` writes append-only markdown lines

These are human-readable, but not enough for robust AI retrieval. We need a
structured memory substrate that is both human-auditable and machine-queryable.

## Implementation Snapshot (2026-03-06)

### Shipped Foundation (Code Present)

- Canonical memory schema/types + ID/timestamp helpers (`memory/types.rs`, `memory/schema.rs`)
- Append-only JSONL event store with rotation (`memory/store/jsonl.rs`)
- Query index APIs for recent/topic/task/text/timeline retrieval (`memory/store/sqlite.rs`)
- Runtime ingest wiring from transcript + PTY input/output (`main.rs`, `event_loop.rs`, `event_loop/output_dispatch.rs`, `voice_control/drain/transcript_delivery.rs`, `memory/ingest.rs`)
- Baseline governance controls (redaction + retention GC) (`memory/governance.rs`)
- Context-pack builders (JSON + Markdown rendering helpers) (`memory/context_pack.rs`)
- Action policy catalog/classification scaffolding (`memory/action_audit.rs`)

### Partially Shipped (Scaffolded, Not Fully Wired)

- Retrieval is deterministic but still basic; no intent planner, no semantic rerank, no graph boosts yet.
- SQLite DDL contract exists, but runtime index remains in-memory vectors (no live SQLite read/write path).
- Live ingest now performs bounded deterministic metadata extraction for `MP-*`
  refs, obvious repo file paths, and a small topic-tag allowlist, so runtime
  `ByTopic` / `ByTask` retrieval is no longer blocked on empty metadata alone.
  Richer semantic tags, symbols, contradiction metadata, and broader
  query/export surfaces are still missing.
- The Rust operator cockpit now exposes a dedicated read-only Memory tab with refresh-on-visible-tab wiring plus memory-ingest/review/boot-pack/handoff preview sections, but broader query/export views and dedicated browser navigation are still missing.
- Memory modes (`off`, `capture_only`, `assist`, `paused`, `incognito`) now restore from persistent config at startup, persist immediately from the dev-panel mode toggle path, and flow through runtime config snapshots, but broader trust/privacy controls and visible controls outside `--dev` remain incomplete.
- Context-pack struct/output is present, but several required fields are still missing (`retrieval_plan`, `validation_report`, `source_mix`, contradiction metadata).
- Review/control-plane interop is partially proven through the shared handoff prompt; pack exports plus event-backed attach-by-ref `context_pack_refs` are now wired through the current review/control proof path, but normalized packet-outcome ingestion and wider `controller_state` parity are not wired yet.
- Action policy logic exists, but action execution/audit is not yet integrated into overlay runtime flows.

### Missing for Product-Ready Persistent Memory

- Memory Browser overlay UX (`MP-233`) and Action Center overlay UX (`MP-234`)
- Memory Cards + Memory Units + contradiction workflow (`MP-240`)
- MCP read-only memory exposure contract (`MP-242`)
- Memory evaluation harness and release gates (`MP-237`)
- External transcript import adapters (`MP-248`)
- Isolation profiles for action execution (`MP-249`)

## Plan Additions (2026-03-06)

These additions came from an implementation audit plus current cross-model memory patterns.
They fit inside existing MP scopes (no new MP IDs required).

| Addition | Why it matters | Land under |
|---|---|---|
| Memory receipts in overlay (`why this was injected`, `keep`, `forget`, `not now`) | Builds trust and gives users direct control over what persists. | `MP-233`, `MP-243`, `MP-247` |
| Promotion pipeline (`event -> candidate -> validated card`) with explicit approval state | Keeps durable memory clean and reduces noisy auto-saves. | `MP-240` |
| Adapter profiles for `codex`, `claude`, `gemini` with one canonical pack input plus routed review/control-plane attachments | Prevents provider-specific drift while keeping deterministic provenance. | `MP-238`, `MP-242` |
| Scope layers (`session`, `project`, optional `user`) with strict default to project scope | Improves reuse without leaking unrelated context across repos. | `MP-243` |
| Negative memory controls (`never remember this`, topic/path denylist) | Makes privacy behavior obvious and lowers accidental retention risk. | `MP-243`, `MP-248` |
| Retrieval usefulness telemetry (`accepted`, `ignored`, `wrong`) tied to evidence IDs and downstream review outcomes | Lets ranking improve from real usage instead of offline scoring only. | `MP-237`, `MP-247` |
| Contradiction playbook (`auto-quarantine`, `show both`, `manual resolve`) | Avoids silently injecting conflicting memory claims. | `MP-240` |
| Cold-start `repo_bootstrap_card` from docs + stable commands + guardrails | Makes first-run memory useful immediately, even before deep history exists. | `MP-232`, `MP-241` |
| Review/control-plane interop (`context_pack_refs`, packet-to-memory ingest bridge, packet/task lookup) | Keeps review, memory, and operator surfaces on one auditable contract instead of parallel side channels. | `MP-238`, `MP-241`, `MP-243` |

### Execution Order Update (post-audit)

1. Finish `MP-231` with intent-aware retrieval profiles and explicit scoring traces.
2. Wire `MP-243` controls into runtime + persistent config so users can trust memory modes.
3. Deliver `MP-233`/`MP-234` overlay surfaces with memory receipts and safe action approvals.
4. Land `MP-240` validated cards/units before widening retrieval influence on prompts.
5. Add `MP-237` quality harness as a release blocker before enabling advanced compaction/automation tracks.

### Immediate proving slice (2026-03-09)

This is the master-aligned next execution slice for the current shipped code:

1. Promote the existing operator-cockpit proof path by adding memory query/export views for `task_pack`, `session_handoff`, and the first `survival_index` preview on top of the shipped `boot_pack` snapshot.
2. Finish `MP-243` runtime trust wiring by loading/saving memory mode through persistent config and surfacing clear capture/retrieval state beyond the current dev-only mode cycle.
3. Finish the `MP-238` bridge by attaching packs through `context_pack_refs` and ingesting review/control packet outcomes as canonical memory events.
4. Expand into the full Memory Browser / Action Center overlays only after the operator-cockpit proof can survive handoff, restart, and cross-agent review flows without hidden state.

Progress note (2026-03-09):
- The Rust Dev panel now includes a dedicated read-only Memory cockpit tab fed
  by memory ingest state plus review/boot-pack/handoff preview data, with
  refresh wired through the visible-tab path. This advances the operator
  proof-path for `MP-233`; the 2026-03-09 follow-up now emits repo-visible
  `.voiceterm/memory/exports/*.{json,md}` artifacts for `boot_pack`,
  `task_pack`, `session_handoff`, and the first `survival_index` preview on
  refresh. Remaining open scope is attach-by-ref `context_pack_refs` interop
  plus review/control packet-outcome ingest.
- The bounded `MP-243` persistence slice is now landed: startup restore uses
  the persisted `memory_mode`, runtime config snapshots preserve/write that
  mode explicitly, and the dev-panel `m` path saves the new mode immediately
  so later snapshots reflect the configured state. Remaining `MP-243` closure
  is now concentrated on trust/privacy UX beyond `--dev` (visible controls,
  receipts, and negative-memory affordances).
- Local proof-path revalidation is now green for the shipped Memory tab:
  `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test --bin voiceterm -- --nocapture`
  passes with the current cockpit slice, and the supporting Rust policy gates
  (`check_rust_test_shape`, `check_rust_lint_debt`,
  `check_rust_best_practices`, `check_structural_complexity`) also pass after
  splitting the overloaded formatter test surface into focused modules.

### Maintainability Track (Python + Rust)

- Add a `devctl memory` command group (`status`, `query`, `export-pack`, `validate`) so memory ops do not spread across unrelated scripts.
- Keep `devctl memory` and `devctl review-channel` interop explicit:
  review-channel posts should be able to attach memory packs by ref, and
  memory queries should accept review packet/task refs instead of forcing raw
  event-id discovery.
- Keep Rust memory runtime focused on capture/index/retrieve; move report-heavy compile/export helpers to Python tooling where possible.
- Keep one responsibility per module:
  - Rust runtime path: `ingest`, `retrieval`, `context_pack`, `governance`, `action_audit`
  - Python tooling path: audits, quality scoring, benchmark reports, release evidence aggregation
- Prefer one shared scoring/config surface so retrieval weights are not duplicated across Rust and Python.

### Operator Cockpit Proof Path (2026-03-08)

Goal: prove that memory, review, control-plane, git/tooling artifacts, and
safe action routing can work together incrementally inside the Rust operator
surface instead of landing as disconnected subsystems.

Principles:

- use the shipped canonical memory event model and JSONL store now
- treat the current in-memory index / SQLite contract as the proving substrate
  rather than waiting for every later retrieval feature
- expose memory read/query/export value in the operator cockpit before letting
  memory steer writes or autonomous actions
- route any memory-derived action suggestion through the same typed action
  router and approval path as buttons and review packets

Current shipped proof is intentionally narrower than the end-state:

- live today: Control-tab memory status/mode visibility, a dedicated read-only
  Memory tab backed by ingest/review/boot-pack/handoff previews, Boot-pack-
  backed Handoff prompt generation, and repo-visible JSON/Markdown exports for
  `boot_pack`, `task_pack`, `session_handoff`, and the first
  `survival_index` preview
- not landed yet: attach-by-ref `context_pack_refs` consumption,
  packet-outcome ingest parity, and the fuller Memory Browser / Action Center
  overlays

Piece-by-piece ladder:

1. Memory visibility first
   - show memory mode, event counts, last ingest/recovery status, and pack
     availability inside `--dev`
2. Read/query/export next
   - surface `boot_pack`, `task_pack`, `session_handoff`, and
     `survival_index` previews in the operator cockpit and handoff flows
3. Cross-system linking
   - ingest review/control/git/devctl outputs as canonical memory events and
     attach memory packs by `context_pack_refs` from review/control packets
4. Suggestion phase
   - let memory help propose prompts, next slices, and candidate actions, but
     keep execution gated by the shared policy engine
5. Stronger persistence later
   - promote live SQLite-backed query/index execution only after the first four
     layers are stable and the current JSONL + index-contract path proves the
     operator workflows end to end

Required proving outputs:

- operator-visible memory status page
- handoff/resume bundle generation backed by canonical packs
- review/control packet attachments that resolve back to memory evidence IDs
- audit rows showing when memory influenced a suggestion vs when an action was
  actually approved/executed

## Research Intake (2026-03-07): Nontraditional Memory Structures

The goal of this intake is to improve memory quality beyond a standard
`events + lexical + vector` stack. These items are additive and mapped to
existing MP scopes.

### Candidate structures to evaluate

| Structure | What changes in VoiceTerm | Expected gain | Land under |
|---|---|---|---|
| Associative memory graph + Personalized PageRank retrieval | Add typed nodes/edges (`event`, `entity`, `task`, `decision`) and graph-walk scoring. | Better multi-hop recall and relationship-aware context. | `MP-231`, `MP-240`, `MP-250` |
| Hierarchical memory tree (multi-resolution summaries) | Build `event -> segment -> summary` layers and retrieve from multiple levels. | Better long-context quality and less token waste. | `MP-231`, `MP-240`, `MP-250` |
| Tiered hot/warm/cold memory manager | Split retrieval into working set, recent task packs, and full archive. | Faster retrieval and cleaner prompt injection. | `MP-235`, `MP-237`, `MP-243` |
| Late-interaction retrieval index (token-level signals) | Add optional token-level rerank path for technical strings (flags, paths, symbols). | Stronger exact technical recall than single-vector chunks. | `MP-231`, `MP-237`, `MP-252` |
| Learned memory operation policy (`add/update/delete/noop`) | Replace fixed save heuristics with guarded policy decisions + audit traces. | Lower memory noise and better long-term quality. | `MP-240`, `MP-247`, `MP-250` |
| Forgetting-curve retention (recency x reinforcement) | Promote/demote memory by usefulness signals, not only fixed TTL days. | More stable long-term memory without manual cleanup overhead. | `MP-235`, `MP-237`, `MP-243` |

### Execution constraints for all candidates

- Keep canonical event history immutable and auditable.
- Keep deterministic mode available and default-safe.
- Require citation parity for any compacted or transformed output.
- Fail closed when validation/expansion checks fail.
- Keep user controls first-class (`off`, `paused`, `incognito`, explicit delete/forget).

### Recommended execution order

1. Graph retrieval prototype + replay fixtures (`MP-231`).
2. Hierarchical summary tree prototype + deterministic pack comparison (`MP-250`).
3. Tiered hot/warm/cold retrieval policy with clear UX controls (`MP-243`).
4. Optional late-interaction reranker for technical queries (`MP-252`).
5. Learned memory-operation policy only after telemetry and approval loops are stable (`MP-247`).

## Research Intake (2026-03-07): Compaction Survival Layer

Context: KV cache compaction techniques (Attention Matching, 50x compression
without accuracy loss) solve model-internal memory. This intake addresses the
complementary problem: how VoiceTerm's external memory survives any context
disruption (compaction, new session, new agent, handoff) and gives AI fast
context recovery.

Industry signals driving this intake:

- OpenAI Stateful Runtime Environment (Feb 2026): persistent working context
  including memory, tool state, workflow history across multi-step tasks. Hosted
  solution; VoiceTerm builds the local-first equivalent.
- Google Always-On Memory Agent (March 2026): open-sourced LLM-driven persistent
  memory using structured storage instead of vector databases. Validates
  JSON-first structured memory over embedding-heavy retrieval.
- MIT Attention Matching (arXiv:2602.16284, Feb 2026): 50x KV cache compaction
  in seconds. Solves model-internal memory; external structured memory is the
  complement that ensures nothing is lost when the model's working memory is
  compressed.

### Gap analysis: what the current plan is missing

The plan has `boot_pack` and `task_pack` (`context_pack.rs`) but these are
generated on demand. There is no continuously-maintained compact index that
exists specifically for AI context recovery after compaction events.

| Current capability | Gap |
|---|---|
| `boot_pack` (on-demand, 100 recent events) | Not continuously maintained; stale between generations |
| `task_pack` (query-driven) | Requires knowing the right query; no "catch me up on everything" mode |
| Memory Units (task_segment, debug_episode) | Defined but not yet compiled; no auto-compilation pipeline |
| Memory Cards (validated durable truths) | Defined but no continuous distillation from events to cards |
| Retrieval states (eligible/quarantined/deprecated) | Exist but not wired into a persistent compact index |

### Proposed addition: Compaction Survival Index

A persistent, auto-maintained compact JSON document (~2K tokens) designed to
be injected into any new AI conversation to restore full project context.

#### Architecture position

```
events.jsonl (immutable log, full history)
    |
    v  ingest + index
index.sqlite (fast queries, full metadata)
    |
    v  continuous compilation  <-- NEW LAYER
compaction_index.json (~2K tokens, always current)
    |
    v  inject on: new session, context approaching limit, handoff, compaction
AI context window
```

#### Compaction index schema (draft)

```json
{
  "schema_version": 1,
  "project_id": "sha256:...",
  "last_compiled_at": "2026-03-07T14:30:00Z",
  "compilation_trigger": "event_count_threshold",
  "active_work": [
    {
      "task": "MP-346",
      "title": "WriterState decomposition",
      "status": "post-release backlog",
      "key_decisions": ["PtyAdapter enum pattern"],
      "last_activity": "2026-03-07T14:00:00Z",
      "evidence_refs": ["evt_001", "evt_002"]
    }
  ],
  "recent_decisions": [
    {
      "claim": "Split WriterState into sub-structs with PtyAdapter enum",
      "decided_at": "2026-03-07T14:00:00Z",
      "evidence_refs": ["evt_003"]
    }
  ],
  "code_evolution": [
    {
      "file": "writer/state.rs",
      "trajectory": [["2026-03-01", 2750], ["2026-03-05", 448]],
      "driver": "MP-346 Phase 2"
    }
  ],
  "open_blockers": [],
  "user_context": {
    "skill_level": "architect, learning Rust",
    "explanation_style": "top-down, junior-to-mid level",
    "preferences": ["no dumb comments", "split not long", "modules and helpers"]
  },
  "drill_down": {
    "full_context_query": "sqlite://index.sqlite?recent=200",
    "session_log": ".voiceterm/memory/events.jsonl"
  }
}
```

#### Compilation triggers

- Every N events ingested (default: 25)
- Time interval (default: 5 minutes of active session)
- On session end / graceful shutdown
- On explicit user request (slash command or overlay action)

#### Injection triggers

- New session startup (inject before first AI interaction)
- Context token count approaching model limit (proactive injection before
  model-internal compaction)
- Agent handoff (include in handoff pack)
- User explicitly requests context refresh

#### New Memory Unit type: CodeEvolution

Extends MP-240 unit types with project evolution tracking:

```
code_evolution_segment:
  - file: String (repo-relative path)
  - metric: String ("lines", "functions", "complexity")
  - trajectory: Vec<(timestamp, value)>
  - driver: String (MP reference or description)
  - evidence_ids: Vec<String>
```

This supports multi-aspect audit ingestion where the same history is viewable
from different angles: chronological events, code evolution, decision history,
quality trajectory.

### Candidate structures to evaluate (additive to existing research intake)

| Structure | What changes in VoiceTerm | Expected gain | Land under |
|---|---|---|---|
| Compaction survival index (continuous compilation) | Auto-maintained ~2K token JSON index with links to full store. | AI context recovery after any disruption; cross-session continuity. | `MP-231`, `MP-240`, `MP-243` |
| Code evolution tracking units | New `code_evolution_segment` unit type with file/metric/trajectory. | Multi-aspect audit and progress visibility. | `MP-240`, `MP-250` |
| Proactive injection trigger | Monitor context token budget; inject compact index before model compaction. | Prevents information loss during long conversations. | `MP-231`, `MP-243` |
| LLM-driven memory compilation (Google AOMA approach) | Use the model itself to decide what belongs in compact index vs archive. | Higher-quality compact index than heuristic-only compilation. | `MP-240`, `MP-247` |

### Execution constraints (same as existing research intake)

- Keep canonical event history immutable and auditable.
- Keep deterministic mode available and default-safe.
- Require citation parity for any compacted or transformed output.
- Fail closed when validation/expansion checks fail.
- Keep user controls first-class.
- Compact index must round-trip to full evidence via drill-down refs.

### Recommended execution order (extends existing order)

1. Compaction survival index prototype with static compilation rules (`MP-231`).
2. Wire injection triggers into session startup and context-budget monitor
   (`MP-243`).
3. Add `code_evolution_segment` unit type and compiler (`MP-240`, `MP-250`).
4. Evaluate LLM-driven compilation vs heuristic-only on quality metrics
   (`MP-247`).
5. Integration with proactive context-budget injection in runtime event loop
   (`MP-231`, `MP-243`).

### Architecture relationship to KV cache compaction

KV cache compaction (Attention Matching) operates inside the model at inference
time. VoiceTerm cannot hook into that layer. Instead, VoiceTerm operates at the
application layer using the MemGPT virtual-context-management approach:

- Monitor context token usage from the application side.
- Proactively inject the compact index when approaching limits.
- Let the model's internal compaction handle the rest, knowing that the
  structured external memory preserves everything important.

This is complementary, not competing. The model compresses its working memory;
VoiceTerm ensures the external knowledge survives.

### Evaluation protocol: Compaction Survival Index

Without measurable proof that the survival index helps, it is architecture
fiction. This section defines how to test it at every level.

#### Industry benchmarks informing this protocol

| Benchmark | What it tests | VoiceTerm relevance |
|---|---|---|
| [LongMemEval](https://github.com/xiaowu0162/LongMemEval) (ICLR 2025) | 500 multi-session questions across 115K–1.5M tokens; 5 memory abilities (extraction, multi-session reasoning, temporal reasoning, knowledge updates, abstention) | Directly applicable — our survival index must pass the same ability categories |
| [LOCOMO](https://mem0.ai/blog/benchmarked-openai-memory-vs-langmem-vs-memgpt-vs-mem0-for-long-term-memory-here-s-how-they-stacked-up) | Single-hop, temporal, multi-hop, open-domain QA against conversation history | A/B scoring methodology (Mem0 beat OpenAI by 26% using this) |
| [MemoryBench](https://arxiv.org/abs/2510.17281) | Continual learning from feedback; procedural + declarative memory | Key finding: naive RAG outperformed many sophisticated systems — complexity does not equal quality |
| [Letta Memory Benchmark](https://www.letta.com/blog/benchmarking-ai-agent-memory) | Filesystem-based retrieval vs specialized memory tools | Simple approaches can win; our index must beat "dump last 100 events" baseline |
| [MemoryAgentBench](https://github.com/HUST-AI-HYZ/MemoryAgentBench) (ICLR 2026) | Incremental multi-turn memory evaluation | Tests whether memory updates correctly over time, not just initial recall |

#### Level 1: Deterministic unit tests (extend existing Rust tests)

Prove the mechanics work — compilation produces correct output, injection
fires at the right time, drill-down references resolve. Same fixture style
as existing `context_pack.rs` tests (`sample_event()`, inline helpers).

| Test | What it proves |
|---|---|
| `compile_empty_index` | No crash on zero events |
| `compile_produces_valid_schema` | Output matches JSON schema |
| `compile_includes_recent_decisions` | Decisions from last N events appear in index |
| `compile_respects_token_budget` | Output stays under ~2K tokens |
| `compile_drill_down_refs_resolve` | Every `evidence_ref` maps to a real event in store |
| `compile_is_idempotent` | Same events in same order produce identical index |
| `compile_updates_on_new_events` | Index changes when new events are ingested |
| `compile_triggers_at_threshold` | Fires after 25 events, not 24 |
| `inject_on_session_start` | New session receives index in first prompt |
| `inject_on_context_budget_warning` | Fires when token count exceeds 80% of model limit |

#### Level 2: A/B recall tests (the critical proof)

This is the industry-standard test that proves the index actually helps.
Without this, we cannot claim the feature works.

**Replay fixture**: A scripted multi-session conversation with known facts
("needles") embedded at specific points.

```
Session 1: User discusses MP-346, decides on PtyAdapter enum pattern
Session 2: User works on theme colors, mentions preferring dark mode
Session 3: User debugs a JetBrains rendering bug, identifies root cause
[--- COMPACTION EVENT (context wiped) ---]
Session 4: Ask questions about Sessions 1-3
```

**Test matrix**:

| Condition | What is injected after compaction |
|---|---|
| A (no memory) | Nothing — fresh context |
| B (boot_pack) | Current `boot_pack` (on-demand, 100 recent events) |
| C (survival index) | `compaction_index.json` (~2K tokens) |
| D (both) | Survival index + boot_pack |

**Questions** (covering all 5 LongMemEval abilities):

| ID | Question | Ability tested |
|---|---|---|
| Q1 | "What pattern did we decide on for WriterState?" | information extraction |
| Q2 | "When did we identify the JetBrains rendering bug?" | temporal reasoning |
| Q3 | "What is the connection between MP-346 and the dark mode preference?" | multi-session reasoning |
| Q4 | "Did we decide to use React for the overlay?" | abstention (answer is no) |
| Q5 | "What changed about our approach after the Session 3 debug?" | knowledge update |

**Scoring**: Each answer scored against a gold answer using two-tier method
(industry consensus from Google, Mem0, LongMemEval):

1. Exact match first (deterministic, fast, no false positives)
2. LLM-as-Judge fallback for fuzzy answers (semantically correct?)
3. Score: 0 (wrong), 0.5 (partial), 1.0 (correct)

**Pass criteria**: Condition C must score ≥ 20% higher than Condition A
across all questions. If it does not, the index is not helping.

#### Level 3: Compaction simulation (end-to-end proof)

Simulates the actual failure mode — context is wiped, only the survival
index remains, and we verify all key facts are recoverable.

```
1. Build a 50-event history with 5 embedded "needles" (key facts)
2. Ingest all events, compile survival index
3. Simulate compaction: wipe the context (fresh session)
4. Inject ONLY the survival index (~2K tokens)
5. For each needle:
   a. Verify the index contains a reference to the needle's event_id
   b. Verify the drill-down ref resolves to the actual event in store
   c. Verify the resolved event contains the key fact text
6. Pass: all 5 needles recoverable. Fail: any needle lost.
```

#### Level 4: Cross-IDE continuity test (VoiceTerm-specific)

No existing benchmark tests this because no existing product has this
problem. VoiceTerm is used across different IDEs and backends, so the
survival index must work across that boundary.

```
1. Session in JetBrains + Claude: 20 events, compile index
2. New session in Cursor + Codex: inject index
3. Ask: "What was I working on in my last session?"
4. Score against gold answer (same two-tier method)
5. Pass: AI correctly identifies prior work context
```

#### Level 5: CI regression gate

Add a guard script (same pattern as existing `check_rust_*` scripts) that:

1. Runs Level 2 A/B recall test on every PR touching `memory/`
2. Fails if Condition C scores lower than Condition A
3. Tracks score over time as a non-regression metric (growth-based, same
   as existing guard policy)

Acceptance threshold:

```
SURVIVAL_INDEX_LIFT_MINIMUM = 0.20  # 20% improvement over no-memory baseline
ABSTENTION_ACCURACY_MINIMUM = 0.90  # 90% correct "I don't know" responses
DRILL_DOWN_RESOLUTION_RATE  = 1.00  # 100% of evidence_refs must resolve
```

#### Level 6: Human spot-check (release gate)

For v1 launch, manually test 10 times:

1. Have a real 30-minute VoiceTerm session
2. Let context compact (or simulate it)
3. Ask "what were we working on?" in a fresh session
4. Rate: Did the survival index give the AI enough to continue meaningfully?

Pass: 8/10 sessions produce useful context recovery. If not, iterate on
compilation logic before shipping.

#### Metrics to track (survival index specific)

| Metric | How to measure | Target |
|---|---|---|
| Recall accuracy | % of embedded facts recoverable post-compaction | > 80% |
| Recall lift | `(with_index - without_index) / without_index` | > 20% |
| Temporal accuracy | % of "when" questions answered correctly | > 70% |
| Abstention rate | % correct "I don't know" for unknown facts | > 90% |
| Index freshness | Seconds since last compilation when queried | < 300s |
| Token efficiency | Facts recovered per token in the index | maximize |
| Drill-down resolution | % of `evidence_refs` resolving to real events | 100% |
| Cross-IDE recall | Accuracy when switching IDE between sessions | > 75% |

#### Key lesson from industry benchmarks

MemoryBench found that many sophisticated memory systems were outperformed
by naive RAG baselines that stored everything. The survival index must be
tested against the simplest possible baseline ("dump last 100 events into
context") to prove it compresses information intelligently rather than
adding overhead. If the ~2K token index cannot beat a 100-event raw dump
on recall accuracy, the compilation logic needs work — not more features.

### Retrieval Router (Strategy Selector)

No single retrieval method wins all the time. MemoryBench showed naive RAG
outperforms sophisticated memory on specific fact recall, while the survival
index wins on overview/synthesis after context disruption. The retrieval
router picks the best strategy (or combination) for each situation.

#### Architecture position

```
Context needed (session start, user query, compaction, handoff)
        |
        v
┌─────────────────────┐
│  RetrievalRouter     │  picks strategy based on context signals
│                     │
│  Signals:           │
│  - query type       │
│  - context state    │
│  - token budget     │
│  - session gap      │
└────────┬────────────┘
         |
    ┌────┴─────┬──────────┬───────────────┐
    v          v          v               v
 RAG        boot_pack  survival_idx   task_pack
 (text      (recent    (compact       (MP-ref
  search)    100)       ~2K JSON)      focused)
    |          |          |               |
    └────┬─────┴──────────┴───────────────┘
         v
   ┌─────────────┐
   │  Merge +     │  combine, deduplicate by event_id, trim to budget
   │  Score +     │
   │  Budget      │
   └──────┬──────┘
          v
    Final context pack → inject into AI prompt
```

#### When each strategy wins

| Situation | Best strategy | Why |
|---|---|---|
| "What exact command did I run?" | RAG (TextSearch) | Specific fact — lexical search finds exact matches |
| Fresh session startup | boot_pack | Recent 100 events give immediate context, cheap to generate |
| After compaction / long session gap | survival_index | Only thing with compressed overview of everything |
| "What have we done on MP-346?" | task_pack | Task-ref query is purpose-built for this |
| Cross-IDE handoff | survival_index + RAG | Index gives overview, RAG fills specific details |
| "What were we working on?" (vague) | survival_index | Structured overview beats dumping raw events |
| "Find all times I used cargo test" | RAG (TextSearch) | Pure keyword recall — unbeatable for exact text |

#### Strategy selection logic

```rust
enum ContextStrategy {
    Rag,
    BootPack,
    SurvivalIndex,
    TaskPack,
    Hybrid,  // merge multiple strategies
}

fn select_strategy(signal: &ContextSignal) -> ContextStrategy {
    match signal {
        // Post-compaction or new session after gap → hybrid
        ContextSignal::SessionStart { gap_seconds }
            if *gap_seconds > 3600 => ContextStrategy::Hybrid,

        // Normal session start → boot pack is enough
        ContextSignal::SessionStart { .. } => ContextStrategy::BootPack,

        // Specific query → RAG or task pack
        ContextSignal::UserQuery { text }
            if text.starts_with("MP-") => ContextStrategy::TaskPack,
        ContextSignal::UserQuery { .. } => ContextStrategy::Rag,

        // Context budget warning → survival index (most compact)
        ContextSignal::ContextBudgetWarning => ContextStrategy::SurvivalIndex,

        // Agent handoff → survival index + task context
        ContextSignal::Handoff { .. } => ContextStrategy::Hybrid,
    }
}
```

#### Hybrid merge protocol

When `Hybrid` is selected, the router runs multiple strategies and merges:

1. Start with survival index as baseline (~2K tokens).
2. Run RAG or task_pack for the specific query.
3. Deduplicate by `event_id` (survival index refs overlap with RAG results).
4. Score merged results using existing `RetrievalResult.score`.
5. Trim to token budget using existing `trim_to_budget()`.

This requires no new infrastructure — `retrieval.rs` already scores and
deduplicates, `context_pack.rs` already trims to budget.

#### Implementation path (minimal changes)

1. `types.rs`: add `SurvivalIndex` and `Hybrid` to `ContextPackType`.
2. `retrieval.rs`: add `ContextSignal` enum and `select_strategy()`.
3. `context_pack.rs`: add `generate_hybrid_pack()` that merges strategies.
4. No changes to `ingest.rs`, `store/`, `governance.rs`, or `schema.rs`.

#### Evaluation requirement

The router must be A/B tested against each individual strategy to prove
the hybrid approach outperforms any single method. If the router adds
complexity without measurably improving recall, remove it and default to
the single best strategy per situation.

Extends: `MP-231`, `MP-237`, `MP-243`

## Design Principles (Required)

1. Local-first by default
2. Structured-first storage (JSON/SQLite), markdown as export
3. Deterministic retrieval with traceable scoring
4. Bounded memory and CPU budgets
5. Safe execution model for write/destructive commands
6. Explicit provenance on all recalled context
7. Validation-before-injection for durable repo claims
8. Immutable event history + curated active retrieval index (selective promotion/demotion)
9. Query-intent-aware retrieval planning, not one fixed retrieval path

## Research-Backed Upgrades (Plan Delta)

1. Multi-store memory model (episodic + semantic + procedural + execution logs)  
   Why: Agent memory literature and production systems show that one flat memory stream
   underperforms against typed stores.
2. Hybrid retrieval (lexical + semantic + graph/task links)  
   Why: Pure vector retrieval misses exact identifiers/commands; pure lexical misses semantic similarity.
3. "Lost-in-the-middle" aware context packing  
   Why: Long-context models can miss information in middle segments; ordering policy matters.
4. Reflection layer for durable learnings  
   Why: Distilling repeated outcomes into stable "lessons" improves reuse and reduces noise.
5. Action-grounded memory events  
   Why: Storing only chat text is weaker than storing executed actions + observable outcomes.
6. Safety-first tooling policy aligned with MCP best practices  
   Why: Tool execution without strong policy/approval boundaries increases prompt-injection risk.
7. Symbolic compaction candidates for repeated memory structures (ZGraph-inspired, evidence-locked)
   Why: Short symbolic aliases can reduce token and scan cost, but only if transforms are reversible and citation-equivalent.

## Information Model (AI-Usable Formats)

### Memory Types (Required)

- Episodic memory: chronological events (who said/did what and when)
- Semantic memory: topic/entity/task summaries and links
- Procedural memory: reusable workflows/templates/rules
- Execution memory: command runs, exit codes, test/lint outcomes, artifacts

### Memory Units (Compression + Consolidation Layer, Required)

Memory Units sit between raw events and Memory Cards:

- events: immutable, high-volume, fully auditable history
- units: compressed, queryable work segments with preserved citations
- cards: validated durable truths used for deterministic prompt injection

Required unit types:

- `task_segment`: one task over time
- `debug_episode`: failure -> investigation -> fix -> verification
- `release_segment`: release prep/publish evidence chain
- `procedure_run`: one repeatable workflow execution

Each unit must include:

- `summary` (short, citation-backed)
- `entities[]` (files, symbols, commands, errors)
- `outcomes` (tests/status, pass/fail, notable deltas)
- `evidence[]` (event IDs + artifact refs)
- `validation_grade` (`validated_strong` | `validated_weak` | `stale` | `contradicted`)
- `retrieval_state` (`eligible` | `quarantined` | `deprecated`)
- `lineage` (parent/child links for drill-down back to raw events)

### Memory Cards (Derived Truth Layer, Required)

Event logs are canonical history. Memory Cards are validated derived truths that
the assistant can safely reuse across sessions.

Card types:

- `decision`: architecture choices and constraints
- `project_fact`: stable repo facts (modules, workflows, ownership)
- `procedure`: reproducible step sequences (build/test/release tasks)
- `gotcha`: known failure modes, sharp edges, env caveats
- `task_state`: active work status, blockers, acceptance evidence
- `glossary`: project-specific terms and aliases

Each card must include:

- `claim` (short, testable statement)
- `scope` (`project_id`, optional `branch`, optional `path`)
- `evidence[]` (event IDs, file refs, command/result refs)
- `validation` (`status`, `grade`, `last_checked_at`, `validator`)
- `ttl_policy` (`decay_days`, optional `max_age_days`)
- `retrieval_state` (`eligible` | `quarantined` | `deprecated`)
- optional `quarantine_reason`
- optional `contradiction_refs[]` (newer evidence that conflicts)
- `owner` + `edit_history`

Example:

```json
{
  "card_id": "card_01JBCD...",
  "card_type": "decision",
  "claim": "Use SQLite FTS5 as lexical retrieval baseline before vector search.",
  "scope": {
    "project_id": "sha256:/Users/.../codex-voice",
    "branch": "develop"
  },
  "evidence": [
    {
      "kind": "file",
      "ref": "dev/active/memory_studio.md:1"
    },
    {
      "kind": "event",
      "ref": "evt_20260219_01JABC..."
    }
  ],
  "validation": {
    "status": "pass",
    "grade": "validated_strong",
    "last_checked_at": "2026-02-19T21:08:00Z",
    "validator": "memory.validate_card"
  },
  "retrieval_state": "eligible",
  "ttl_policy": {
    "decay_days": 28
  }
}
```

### Validation Grades (Required)

- `validated_strong`: citations match current branch + recent execution evidence
- `validated_weak`: citations match but no recent execution evidence
- `stale`: citation drift or expired validation window
- `contradicted`: newer evidence conflicts with claim

Deterministic pack mode must fail closed on `stale` and `contradicted` unless explicitly overridden.

### Canonical Event Envelope

All memory ingestion must normalize to one event schema:

```json
{
  "event_id": "evt_20260219_01JABC...",
  "session_id": "sess_20260219_01JABC...",
  "project_id": "sha256:/Users/.../codex-voice",
  "ts": "2026-02-19T19:04:12.442Z",
  "source": "assistant_output",
  "event_type": "chat_turn",
  "role": "assistant",
  "text": "I updated transcript history rendering and tests.",
  "topic_tags": ["overlay", "transcript-history", "tests"],
  "entities": ["rust/src/bin/voiceterm/transcript_history.rs"],
  "task_refs": ["MP-229"],
  "artifacts": [
    {
      "kind": "file",
      "ref": "rust/src/bin/voiceterm/transcript_history.rs"
    }
  ],
  "importance": 0.72,
  "confidence": 0.95,
  "retrieval_state": "eligible",
  "hash": "sha256:..."
}
```

Review/control-plane normalization rule:

- `review_event` / `controller_state` artifacts must compile losslessly into
  this envelope instead of defining competing near-duplicate headers.
- Freeze explicit mappings for `event_id`, `session_id`, `project_id`,
  `trace_id`, `source`, `event_type`, and `timestamp_utc -> ts`.
- Keep routing fields such as `from_agent` / `to_agent` as additional metadata;
  they do not replace the canonical envelope's `source`.

### Storage Layers

1. Append log: `.voiceterm/memory/events.jsonl`  
   Immutable, line-delimited JSON for replay/audit.
2. Query index: `.voiceterm/memory/index.sqlite`  
   Fast lookup for topic/task/time/source queries.
3. Optional semantic index in SQLite (`sqlite-vec` or `sqlite-vss`)
   Local embedding search without requiring external infra.
4. Human export: `.voiceterm/session-memory.md`  
   Readable session summary/export, not primary truth.

### Event Type Taxonomy (v1)

- `chat_turn`
- `voice_transcript`
- `command_intent`
- `command_run`
- `file_change`
- `test_result`
- `decision`
- `handoff`
- `summary`

### Required SQLite Tables (initial)

- `sessions`
- `events`
- `topics`
- `event_topics`
- `entities`
- `event_entities`
- `tasks`
- `event_tasks`
- `artifacts`
- `action_runs`
- `event_fts` (FTS5 virtual table for lexical search)
- `memory_cards`
- `card_evidence`
- `card_validations`
- `memory_units`
- `unit_events`
- `unit_entities`
- `compiled_summaries`

### Selective Addition + Deletion Policy (Required)

Event history stays immutable. Retrieval eligibility is actively managed.

- all events are written to immutable JSONL + indexed metadata
- only high-signal events/units/cards are `retrieval_state=eligible`
- low-confidence or drifted items move to `quarantined` with reason tracking
- superseded items move to `deprecated` but remain auditable
- active index GC compacts/drops low-signal stale rows from fast indexes while retaining JSONL audit history
- deterministic pack mode excludes `quarantined` and `deprecated` items by default

## Retrieval Contract (Accuracy + Efficiency)

### Query Intent Planner (Required)

Every query is first classified to choose retrieval shape:

- `recall_exact_command`
- `find_decision_or_rule`
- `debug_failure`
- `understand_architecture`
- `continue_task`

Strategy matrix:

- lexical-heavy (FTS5/BM25) for exact commands/flags/file paths/IDs
- semantic-heavy for fuzzy concept recall
- graph-bridge boosted retrieval for multi-hop links across tasks/files/errors
- procedural-first when user asks for workflow/how-to guidance
- execution-first when debugging needs latest test/exit evidence

### Query Types

- `recent(n, filters)`
- `by_topic(topic, n)`
- `by_task(mp_or_issue, n)`
- `semantic(query, n)`
- `timeline(start, end, filters)`

### Ranking Formula (v1)

`score = 0.40 * semantic + 0.25 * lexical + 0.20 * recency + 0.15 * importance`

Rules:

- intent classification selects per-intent weight profile and filter policy
- always return source/provenance metadata with each hit
- dedupe near-identical events by `hash` + text similarity window
- cap retrieval to bounded token budget before pack generation
- reject stale/failed-validation cards from deterministic pack mode unless explicitly requested

### Retrieval Pipeline (v1)

1. Intent planner: classify query and select retrieval strategy profile
2. Fast prefilter: project/session/time/source constraints
3. Lexical candidate pass: SQLite FTS5/BM25 on exact tokens (files, flags, IDs, commands)
4. Semantic rerank: embedding similarity (local-first backend)
5. Graph/task boost: linked task/artifact/entity relationship signals
6. Final dedupe + diversity pass: avoid repetitive near-duplicate context rows

### Context Packing Rules (Lost-in-the-Middle Aware)

- place highest-priority facts at pack head and tail (not only middle)
- include short "critical facts" block before detailed evidence
- enforce max tokens per section to avoid one noisy source dominating pack
- emit citations/provenance for every summary claim

### Distraction Guard (Required)

Pack builder must run a deterministic anti-noise pass:

- drop near-duplicates after rerank
- enforce diversity across source classes (chat, terminal, git, files, docs, cards, units)
- cap any single source class token share
- require at least one `validated_strong` evidence item for claim-heavy packs
- downrank stale/unvalidated evidence unless user explicitly opts in

### Context Pack Output

Each retrieval request can produce:

1. `context_pack.json` (machine)
2. `context_pack.md` (human)

`context_pack.json` minimum fields:

- `query`
- `generated_at`
- `pack_type` (`boot` | `task`)
- `retrieval_plan` (intent + strategy profile + filters)
- `summary`
- `active_tasks`
- `recent_decisions`
- `changed_files`
- `open_questions`
- `token_budget` (`target`, `used`, `trimmed`)
- `validation_report` (`checked`, `failed`, `stale`)
- `validation_grades` (counts by `validated_strong`/`validated_weak`/`stale`/`contradicted`)
- `contradiction_flags[]` (cards/units/events with conflicting evidence)
- `source_mix` (counts by source type: chat/terminal/git/files/docs)
- `evidence[]` (event references with scores)
- `inclusion_reason[]` (why each top item was selected)

### Contradiction Detection (Required)

When new evidence conflicts with existing cards/units:

- emit contradiction flags in retrieval and context-pack outputs
- mark conflicted cards/units as `contradicted` validation grade
- require review before contradicted items can return to `eligible`

### Memory Compiler Outputs (Primary Product Surface)

Always-on compiler outputs for agent workflows:

1. `boot_pack`: tiny safe startup context (repo identity, core commands, operating rules)
2. `task_pack(query)`: evidence-rich working set for the current request
3. `handoff_pack`: what changed, what failed, what to do next with citations
4. `survival_index`: continuously maintained compact recovery pack for new
   sessions, compaction recovery, and cross-agent handoff (default compact
   attachment only after `MS-G18` passes)

These outputs are the default context contract for Codex/Claude adapters and MCP tools.

Review/control-plane interop rules:

- Review packets and controller artifacts may attach these outputs by ref
  through `context_pack_refs`; they should not duplicate pack bodies inline.
- Bridge-era markdown/JSON handoff bundles are transitional projections only;
  `MP-238` does not count this path as closed until structured
  `review_state` / `controller_state` artifacts emit and consume the same
  pack references.
- When memory capture is active, review outcomes (`packet_posted`,
  `packet_acked`, `packet_dismissed`, `packet_applied`) must ingest as
  normalized memory events so handoff/decision history survives compaction,
  restart, and cross-agent relay.
- Retrieval usefulness telemetry should incorporate explicit review outcomes
  with reason-coded mappings instead of treating review resolution as invisible
  to ranking.

## Overlay Surfaces (Memory + Actions)

### 1) Memory Browser

The Memory Browser is a visual overlay that lets users navigate the entire
memory system — events, RAG results, survival index, decisions, tasks —
the same way they navigate files on a computer. It runs inside the existing
VoiceTerm overlay system and works across Codex, Claude, and any backend.

#### Design goal

Users should be able to visually work their way through all stored memory,
filter by day/topic/task/source, drill into any event, and then inject
selected context directly into the current AI conversation. This replaces
"hope the AI remembers" with "I can see what it knows and point it at
what matters."

#### UI layout (reuses TranscriptHistory overlay pattern)

```
┌─────────────────── Memory Browser (Ctrl+M) ───────────────────┐
│  🔍 Search: cargo test___                                     │
│  ◀ 2026-03-07 ▶   [All] [Decisions] [Commands] [Tasks]       │
├───────────────────────────────────────────────────────────────┤
│    14:32  Decision   MP-346: Use PtyAdapter enum pattern      │
│  > 14:15  Command    cargo test --bin voiceterm (passed)      │
│    13:58  ChatTurn   Discussed WriterState coupling            │
│    13:40  ChatTurn   Code smell audit started                  │
│    13:22  Decision   GuardContext consolidation approved       │
│    12:01  FileChange rust/src/bin/voiceterm/writer/state.rs    │
│    11:45  Command    git diff dev/scripts/checks/             │
├───────────────────────────────────────────────────────────────┤
│  Preview: cargo test --bin voiceterm                          │
│  Result: 47 tests passed, 0 failed (1.2s)                    │
│  Tags: [testing] [voiceterm]  Task: MP-346                   │
├───────────────────────────────────────────────────────────────┤
│  [Enter] Inject  [Tab] Expand  [R] RAG search  [I] Index     │
│  [←→] Day  [↑↓] Navigate  [/] Filter  [Esc] Close            │
└───────────────────────────────────────────────────────────────┘
```

#### Component structure (follows existing overlay patterns)

| Component | Existing pattern to reuse | Source |
|---|---|---|
| State container | `TranscriptHistoryState` | `transcript_history.rs:210-219` |
| Scroll + selection | `move_up/down()` + `clamp_scroll()` | `transcript_history.rs:238-284` |
| Frame rendering | `overlay_frame.rs` utilities | `overlay_frame.rs` |
| Input dispatch | `overlay.rs` key handler | `event_loop/input_dispatch/overlay.rs` |
| Overlay mode | `OverlayMode` enum | `overlays.rs:27-36` |
| Theme integration | `ThemeColors` + `BorderSet` | `theme/mod.rs` |

#### State struct

```rust
pub struct MemoryBrowserState {
    // Navigation
    pub selected: usize,
    pub scroll_offset: usize,

    // Filtering
    pub search_query: String,
    pub date_cursor: chrono::NaiveDate,        // ←→ to change day
    pub active_filter: EventTypeFilter,        // All, Decisions, Commands, Tasks, etc.
    pub filtered_events: Vec<usize>,           // indices into full event list

    // Views
    pub view_mode: BrowserViewMode,            // Timeline, ByTask, ByTopic, SurvivalIndex
    pub expanded_item: Option<usize>,          // Tab to expand full detail

    // Selection for injection
    pub selected_for_injection: Vec<String>,    // event_ids user has marked
}

pub enum BrowserViewMode {
    Timeline,       // chronological, filterable by day
    ByTask,         // grouped by MP-ref
    ByTopic,        // grouped by topic_tag
    SurvivalIndex,  // shows the compact index with drill-down
    RagSearch,      // full-text search results with scoring
}

pub enum EventTypeFilter {
    All,
    Decisions,
    Commands,
    ChatTurns,
    FileChanges,
    TestResults,
}
```

#### User workflows

**1. "What did I do yesterday?"**
- Open browser (Ctrl+M)
- Press ← to go back one day
- Scroll through timeline of events
- See decisions, commands, file changes in chronological order

**2. "Find that cargo test I ran"**
- Open browser → type "cargo test" in search
- RAG search runs against event store
- Results ranked by relevance score
- Select result → preview shows full output + pass/fail

**3. "Show the AI what I mean"**
- Browse to relevant events
- Press Enter on each to mark for injection
- Selected events highlighted with checkmark
- Press Ctrl+Enter to inject all selected into current conversation
- AI receives: "User selected the following context: [events]"

**4. "What does the survival index know?"**
- Press [I] to switch to SurvivalIndex view
- Shows the compact JSON rendered as readable cards
- Each card shows: active work, recent decisions, code evolution
- Drill-down: Enter on any card expands to full event evidence

**5. "Show me everything about MP-346"**
- Press [Tab] to switch to ByTask view
- Tasks listed with event counts
- Select MP-346 → shows all related events grouped and scored

#### Injection mechanism

When the user selects events and presses inject:

```
User selects events in Memory Browser
        |
        v
Build injection pack (same format as context_pack.json)
        |
        v
RetrievalRouter receives ContextSignal::UserSelection
        |
        v
Pack injected into next AI prompt as system context
        |
        v
AI sees: "The user pointed you at this context: [selected events]"
```

This uses the existing `ContextPack` format and `WriterMessage` pipeline.
No new rendering infrastructure needed — the injection is a formatted
string sent through the same channel as boot_pack.

#### Implementation path

1. Add `MemoryBrowser` to `OverlayMode` enum in `overlays.rs`.
2. Add `MemoryBrowserState` struct (follows `TranscriptHistoryState` pattern).
3. Add `memory_browser.rs` (state + logic) and `memory_browser/render.rs`
   (formatting, reusing `overlay_frame.rs` utilities).
4. Add `InputEvent::MemoryBrowserToggle` (Ctrl+M) in `input/event.rs`.
5. Wire input dispatch in `event_loop/input_dispatch/overlay.rs`.
6. Add `ContextSignal::UserSelection` to retrieval router.
7. Connect to existing `MemoryIndex` for queries.

All rendering reuses existing `OverlayPanel`, `overlay_frame`, and
`WriterMessage::ShowOverlay`. No new terminal rendering primitives needed.

#### Responsive layout

```
Browser width  = terminal_cols.clamp(50, 100) - 2
Visible rows   = 7 (matches TranscriptHistory)
Preview rows   = 3 (selected item detail)
Chrome rows    = 8 (title + search + date/filter bar + separator + footer)
Total height   = 18 rows
```

Extends: `MP-233`, `MP-234`

### 2) Session Review

- what changed, what shipped, what failed
- generated handoff block
- export to `dev/active/HANDOFF_*.md`

### 3) Action Center

- command palette for common workflows (git/test/docs/release checks)
- action templates + parameters
- preview + approval before execution
- run results logged as `action_run` memory events

## Safety Model (Required)

### Command Policy Tiers

- `read_only`: execute directly (for safe commands)
- `confirm_required`: preview + explicit user approval
- `blocked`: cannot execute from overlay

### Prompt Injection + Tool Safety Rules

- default all non-read actions to `confirm_required`
- require explicit allowlists for project-local automation templates
- never execute opaque model-suggested shell without preview + policy classification
- persist full action audit trail (input, policy tier, approval, result)
- support emergency global action disable switch
- escalate policy tier for risky command chains (for example repo mutation + network + shell exec)

### Execution Isolation Profiles (Required for Action Paths)

Automation and action execution must run under explicit isolation mode, selectable
by policy and user setting:

- `host_read_only` (default baseline)
  - read-only command set only
  - no mutation commands
  - retrieval and indexing only
- `container_strict` (recommended for autonomous/semi-autonomous action paths)
  - rootless container runtime
  - project mount read-only by default
  - explicit write mount only for approved workspace outputs
  - network disabled by default
  - seccomp/AppArmor/SELinux profile applied
  - cgroup cpu/memory/pid limits
- `host_confirmed` (expert/manual mode)
  - broader command surface
  - explicit per-action approval required
  - full audit + replay trail retained

Non-negotiable guardrails:

- never expose host docker socket inside execution containers
- never allow hidden shell expansion from model text without policy parsing
- action runner uses argument arrays, not shell-concatenated command strings
- memory DB writes go through audited append/index APIs only (no ad hoc SQL writes)

### SQLite + Memory Store Safety Posture

- WAL mode + checkpoint policy for crash resilience
- bounded write queues and backpressure
- parameterized SQL everywhere (no raw string interpolation)
- read-only DB handles for retrieval paths
- migration/version checks before runtime writes

### Memory Control Modes (User Trust + Safety)

- `off`: no memory capture, no memory retrieval
- `capture_only`: write events/cards, do not inject into prompts
- `assist`: capture + retrieval enabled (default)
- `paused`: keep store immutable until resumed
- `incognito`: ephemeral session; no durable writeback
- Current implementation is a dev-panel runtime toggle only; closure requires
  persisted config, startup restore, visible controls outside `--dev`, and
  negative-control / receipt UX.

## Evaluation + Quality Metrics (Mandatory)

### Retrieval Quality

- `precision@k` for known task/topic queries
- `evidence coverage`: percent of context-pack claims backed by source events
- `hallucination guard`: percent of unsupported claims (target: 0 in deterministic pack mode)

### Runtime Budgets

- ingestion latency p95
- retrieval latency p95/p99
- memory footprint bounds for long sessions
- storage growth under retention policy scenarios

### Regression Harness

- golden query fixtures with expected ranked evidence IDs
- deterministic context-pack snapshots
- chaos tests for partial-write recovery and index rebuild

## Memory Compaction Research + Experiment Track

Goal: prove that compaction improves real agent outcomes, not just token count.

### Compaction strategies to evaluate

- `extractive`: retain top evidence spans/cards only (no rewriting)
- `abstractive_with_citations`: summarize, but every claim must cite source IDs
- `hierarchical`: short summary + expandable evidence blocks
- `hybrid`: extractive head + abstractive tail with citation validation

### Evaluation protocol (required before default-on)

Offline A/B matrix:

- A: no memory
- B: raw retrieval (no compaction)
- C: compacted retrieval (candidate strategy)

Primary metrics:

- task success rate
- citation-valid claim rate
- unsupported-claim rate (target trending to zero)
- token usage reduction
- end-to-end latency impact

Secondary metrics:

- human approval rate of generated packs
- replay consistency across repeated runs
- failure-mode taxonomy (what compaction dropped incorrectly)

### Bench and replay sources

- internal task-replay fixtures from VoiceTerm sessions
- long-context retrieval stress suites (for example LongBench/RULER style tasks)
- long-conversation memory scenarios (for example LoCoMo-style tasks)

### Compaction release gate

Compaction can move from experimental to default only if:

- task success is non-inferior or better vs raw retrieval
- unsupported-claim rate does not regress
- citation-valid claim rate remains above policy threshold
- latency/token budgets improve against baseline

### ZGraph-Inspired Symbolic Compaction (Concept Audit Track)

Goal: evaluate whether symbolic pattern encoding can improve retrieval/packing
efficiency for memory artifacts without harming correctness.

What transfers from the concept:

- pattern-first representation for repeated structures
- alias dictionary for repeated high-entropy strings (paths, commands, errors)
- explicit lineage links so compressed forms can be expanded deterministically

What does not transfer:

- unsupported speedup/compression claims without controlled baselines
- lossy or citation-dropping summaries represented as "compression"
- any optimization that cannot prove branch-validated evidence parity

Candidate memory-domain symbolic forms:

- `SYM_PATH_*`: canonicalized file/symbol aliases
- `SYM_CMD_*`: normalized command-shape aliases
- `SYM_ERR_*`: recurring error-signature aliases
- `SYM_FLOW_*`: repeated workflow sequence aliases

Constraints (non-negotiable):

- canonical event log stays immutable and uncompressed
- symbolic layer applies only to derived units/context packs
- every symbolic token must round-trip to original evidence references
- deterministic mode must fail closed if expansion parity check fails

Experiment protocol:

1. Build reversible alias dictionaries during pack generation only.
2. Emit packs with explicit `symbol_table` + expanded evidence references.
3. Compare raw vs symbolic packs on:
   - task success / claim correctness
   - citation-valid claim rate
   - unsupported-claim rate
   - token count and p95 generation latency
4. Reject symbolic strategy if any quality metric regresses beyond non-inferiority bounds.

## Hardware Acceleration Track (Apple Silicon, Future)

Goal: increase memory/retrieval/compaction throughput on Apple Silicon without
regressing answer quality, citation fidelity, or safety behavior.

### Candidate acceleration paths

- CPU SIMD via Accelerate/vDSP for:
  - token/byte scanning
  - dedupe similarity primitives
  - ranking feature precompute
- GPU acceleration via Metal/MPS for:
  - embedding/rerank kernels
  - optional local summarization pipelines
- ANE-oriented path via Core ML compute-unit routing for local model inference
  where compatible models are available.

### Performance-first but quality-locked policy

Acceleration is optimization, not a quality bypass:

- no acceleration path can become default unless non-inferior on quality metrics
- deterministic retrieval/citation contracts stay identical across backends
- fall back to stable CPU reference path on runtime mismatch/errors

### Benchmark methodology (required)

1. Microbenchmarks
   - parser/normalizer throughput (MB/s)
   - retrieval ranking throughput (queries/s)
   - compaction/summarization throughput (tokens/s)
   - energy profile and memory footprint
2. End-to-end benchmarks
   - full context-pack generation latency p50/p95/p99
   - replay-task success rate over fixed fixtures
   - citation-valid claim rate and unsupported-claim rate
3. Backend comparison matrix
   - CPU reference
   - CPU + SIMD
   - GPU/ANE path (where supported)
4. Statistical protocol
   - repeated runs with fixed seeds and warm/cold cache separation
   - report confidence intervals for latency and task metrics

### Initial non-inferiority targets (draft)

- task success delta >= -1.0% vs CPU reference
- citation-valid claim rate delta >= -0.5%
- unsupported-claim rate delta <= +0.5%
- p95 latency improvement >= 20% or throughput improvement >= 1.5x

## Rust Implementation Architecture (Modular + Clean)

Proposed module tree under `rust/src/bin/voiceterm/`:

- `memory/mod.rs`
- `memory/schema.rs`
- `memory/types.rs`
- `memory/store/jsonl.rs`
- `memory/store/sqlite.rs`
- `memory/ingest.rs`
- `memory/retrieval.rs`
- `memory/context_pack.rs`
- `memory/governance.rs`
- `memory/action_audit.rs`

Rust best-practice constraints:

- typed enums/structs for event schema (no ad hoc maps in runtime path)
- versioned schema with explicit migration functions
- transactional writes for index updates
- bounded queues and backpressure-safe ingestion
- no `unwrap/expect` in non-test memory paths
- trait-based store abstraction to keep retrieval/index backends swappable

### Privacy + Governance

- per-project memory root (`.voiceterm/memory/`)
- redaction hooks before persistence (`secrets/tokens/path scrubbing`)
- retention policy options (`7d`, `30d`, `90d`, `forever`)
- opt-in export/sharing only

## Codebase Integration Map

Initial integration points:

- ingest hooks:
  - `rust/src/bin/voiceterm/event_loop.rs`
  - `rust/src/bin/voiceterm/event_loop/output_dispatch.rs`
  - `rust/src/bin/voiceterm/voice_control/drain/transcript_delivery.rs`
- current memory/history:
  - `rust/src/bin/voiceterm/transcript_history.rs`
  - `rust/src/bin/voiceterm/session_memory.rs`
- overlays/input:
  - `rust/src/bin/voiceterm/overlays.rs`
  - `rust/src/bin/voiceterm/input/event.rs`
  - `rust/src/bin/voiceterm/input/parser.rs`
- config flags:
  - `rust/src/config/mod.rs`

## Dev Tool + Git Intelligence Audit (2026-02-19)

Local tooling already exposes machine-usable signals we should ingest directly:

- `python3 dev/scripts/devctl.py status --format json [--ci]`
  - branch state, changed files, changelog/master-plan update flags, CI run summaries
- `python3 dev/scripts/devctl.py report --format json [--ci]`
  - machine-readable governance snapshot for handoff/review memory
- `python3 dev/scripts/devctl.py release-notes <version> --output <path>`
  - structured commit range summary + changed-file tables from `generate-release-notes.sh`
- `git diff --name-status <since>...<head>` + `git log --no-merges`
  - high-signal change timeline and major feature extraction candidates

Integration requirement:

- every `devctl` JSON output should map to canonical memory event types (`command_run`, `summary`, `decision`, `handoff`)
- release-note artifacts must be stored as immutable artifact refs and linked to tasks/releases
- change digests should emit both `*.json` (machine) and `*.md` (human) in `.voiceterm/memory/exports/`
- temporary review/control-plane coordination must ingest cleanly too: today's `code_audit.md` bridge, and later `review_state` / `controller_state`, should compile into `session_handoff` and compaction-survival inputs so active blockers, decisions, and next action survive context compaction or agent handoff

### Git History Compilers (New Memory Outputs)

1. `project_synopsis` compiler
   - sources: README/dev docs + recent validated cards + release-note deltas
   - output: stable "what this repo is/how to run it" summary for agent boot
2. `session_handoff` compiler
   - sources: event stream + devctl status/report + active task refs
   - output: what changed/what failed/what's next with citations
3. `change_digest` compiler
   - sources: git range + release-notes + test/CI outcomes
   - output: major additions/regressions/risks as provenance-backed cards

## Repetition Mining + Automation Suggestions

Goal: detect repeated asks/commands that should become reusable automation
instead of ad hoc chat repetition.

Why this is a strong product direction:

- agent terminals already expose reusable workflow controls (slash commands/hooks)
- repository instruction files (`AGENTS.md`-style) are now mainstream control points
- workflow products already prove demand for repeatable command recipes
- our memory + provenance model can make suggestions safer than ad hoc copy/paste

### Inputs

- canonical memory events (`chat_turn`, `command_intent`, `command_run`, `decision`)
- `devctl` and git summary artifacts
- optional external chat imports (opt-in only; see below)

### Codebase fit (already available)

- `devctl` produces machine-readable governance/CI/git snapshots we can ingest now
- `generate-release-notes.sh` already emits structured change-range artifacts
- macros and script surfaces already exist (`scripts/macros.sh`, `dev/scripts/`)
- `AGENTS.md` is already an accepted repo-level instruction interface

### Mining pipeline (v1)

1. Frequent-pattern detection on command/intent sequences
   - support threshold (for example: repeated 3+ times within rolling window)
   - recency weighting (recent repeats prioritized)
2. Success-rate filter
   - candidate must show stable completion (`exit_code == 0` or explicit success evidence)
3. Scriptability scoring
   - detects parameterizable patterns (same command skeleton, variable args)
4. Safety classification
   - map to action tiers (`read_only`, `confirm_required`, `blocked`)

### Pattern normalization contract

For each command/intent event:

1. parse to normalized command shape (verb + stable flags)
2. parameterize variable arguments (branch names, versions, paths)
3. compute strict fingerprint + templated fingerprint
4. track adjacent sequence windows (single, pair, short chains)

### Candidate data model (required)

- `automation_candidate`
  - `candidate_id`
  - `candidate_type` (`script`, `instruction_patch`, `workflow`)
  - `normalized_pattern`
  - `support_count`
  - `success_rate`
  - `confidence`
  - `safety_tier`
  - `estimated_time_saved_ms`
  - `status` (`proposed`, `accepted`, `rejected`, `expired`)
- `candidate_evidence` (`candidate_id`, `event_id`, `weight`)
- `candidate_reviews` (reviewer, decision, rationale, timestamp)

### Suggestion outputs

- `script_candidate`
  - proposed script/template with explicit parameters and evidence links
- `instruction_candidate`
  - proposed `AGENTS.md`/workflow instruction patch when the same guidance is repeatedly requested
- `workflow_candidate`
  - proposed integration with existing automation surfaces (`devctl`, macro packs, optional hooks)

Each suggestion must include:

- evidence count + source IDs
- estimated time-saved score
- confidence and safety tier
- preview diff and explicit accept/reject action
- policy rationale for safety classification

### Human-in-the-loop policy (required)

- never auto-edit `AGENTS.md` or scripts without explicit approval
- never auto-promote a candidate to executable action path
- accepted candidates are versioned as auditable events with reviewer identity

### Promotion flow (required)

On accept:

- emit `automation_candidate_accepted` event
- preserve patch/script artifact refs + evidence links
- create implementation follow-up task reference

On reject:

- emit `automation_candidate_rejected` event with reason
- downrank similar future candidates
- preserve rejected candidate for audit/learning

## External Conversation Import (Opt-In)

User can optionally import external assistant transcripts (for example
ChatGPT export files) into the same canonical event schema.

Requirements:

- explicit per-import consent with source labeling
- redaction pass before persistence
- provenance tags (`source_system`, `imported_at`, `source_path_hash`)
- import-only mode support (indexable, but excluded from action execution suggestions by default)
- retrieval-only default until user explicitly enables mining participation

### Automation quality metrics

- suggestion `precision@k`
- acceptance rate
- accepted candidate post-adoption success rate
- false-positive rejection rate
- safety-incident count (target: zero)

### Risks and mitigations

- noisy candidate spam
  - mitigation: support/confidence thresholds, cooldown, rejection learning
- unsafe command recommendations
  - mitigation: safety tiering + blocked class + mandatory approval
- imported-data contamination
  - mitigation: retrieval-only default + provenance tags + redaction gates
- stale/brittle instruction suggestions
  - mitigation: diff preview + reviewer identity + evidence-citation requirement

## Phased Rollout

### M0 Foundation (Schema + Storage)

- canonical event schema + validators
- jsonl writer + sqlite indexer
- SQLite FTS5 lexical baseline + deterministic ranking fixtures
- migration path from markdown-only memory

### Iteration 1 (Now) - Buildable Slice

Goal: ship machine-usable memory without introducing heavy agent automation yet.

In-scope:

1. `memory_store` module with canonical event envelope + JSONL append
2. SQLite index for `events`, `topics`, `tasks`, `artifacts`, and `event_fts`
3. ingestion wiring from:
   - transcript deliveries
   - PTY user input
   - PTY assistant output
   - `devctl status/report` JSON snapshots
   - git change-range summaries for handoff context
4. query commands (deterministic lexical + metadata retrieval):
   - `recent`
   - `topic`
   - `task`
5. export command:
   - `--memory-export-context-pack <query>`
6. first compiler output:
   - `boot_pack.{json,md}` and `session_handoff.{json,md}` from canonical events + devctl/git artifacts
7. retrieval lifecycle controls:
   - `retrieval_state` and `quarantine_reason` fields on units/cards
   - validation grades (`validated_strong`/`validated_weak`/`stale`/`contradicted`)
8. active-index GC scaffold:
   - explicit policy for dropping/deprioritizing low-signal stale retrieval rows while retaining immutable JSONL history

Out-of-scope for Iteration 1:

- vector embeddings
- autonomous action execution
- automatic summarization jobs

Iteration 1 acceptance:

- all events stored in canonical JSON schema
- deterministic query results with provenance
- context-pack export available in JSON + markdown
- tooling snapshots (`devctl`/git) preserved as linked memory artifacts
- no regression to existing transcript-history overlay behavior

### M1 Retrieval Engine

- lexical + semantic retrieval APIs
- query-intent planner + strategy matrix
- ranking + provenance + contradiction flags
- distraction guard in pack selection
- deterministic context pack generator
- memory-unit compiler + indexing (`task_segment`, `debug_episode`, `procedure_run`)
- memory-card CRUD + evidence linking + validation grade checks

### M2 Memory Overlay UX

- memory browser with filters/expand/scroll
- session review/handoff export
- card inspection/edit flow (claim, evidence, validation, TTL)
- read-only MCP memory tools enabled for boot/task/search/validation-report flows

### M3 Action Center

- action templates + safe execution policy
- command preview, approval, and audit logging
- sequence-aware risk escalation across multi-command workflows

### M4 Agentic Workflows

- topic auto-tagging, task linking, decision extraction
- project synopsis auto-refresh for AI boot context
- change digest compiler from git range + release-note artifacts
- repeated-intent mining and automation opportunity scoring

### M5 Release Hardening

- perf and memory budgets
- security policy checks
- docs and operator runbooks

### M6 Interop + Model Adapters

- backend adapters for Codex/Claude context-pack injection formats, including
  receiver-shaped review/control-plane handoff attachments
- optional export/import for project memory snapshots
- `devctl memory` / `devctl review-channel` interop for attach-by-ref and
  packet/task lookup flows
- read-only MCP remains default while action tools stay gated behind explicit safety evidence
- staged action-tool MCP exposure after safety + isolation gates are green

### M7 Automation Intelligence

- script/instruction/workflow candidate generation from repeated patterns
- `AGENTS.md` patch suggestions with preview + approval gate
- optional external chat-export import adapters and normalization

### M8 Isolation + Compaction Validation

- container/host isolation profiles for action execution
- compaction A/B harness and benchmark suite
- policy thresholds for promotion from experimental to default

### M9 Acceleration + Quality-Lock

- Apple Silicon acceleration prototypes (SIMD/GPU/ANE-capable paths)
- backend comparison harness with quality non-inferiority checks
- guarded rollout flags with automatic fallback to CPU reference path

### M10 Symbolic Compression (Concept-to-Product)

- reversible symbolic compaction prototype for Memory Units/context packs
- dictionary governance (scope, TTL, invalidation, contradiction handling)
- branch-aware citation-equivalence checker for symbolic packs
- default-off rollout with non-inferiority + reversibility evidence gates

## Memory Studio Gates

| Gate | Pass Criteria | Fail Criteria | Evidence |
|---|---|---|---|
| `MS-G01 Schema` | Events validate against canonical schema | Ad hoc/partial event formats in runtime | schema tests + fixtures |
| `MS-G02 Storage` | JSONL + SQLite stay in sync under load | Missing/duplicate events | ingest + recovery tests |
| `MS-G03 Retrieval` | Query APIs use intent-aware strategy planning and return relevant, provenance-tagged results | One-shape retrieval that returns opaque or untraceable context | ranking tests + retrieval-plan fixtures + golden packs |
| `MS-G04 Boundedness` | Retention, size limits, and active-index GC policies are enforced | Unbounded growth or stale/noisy active index | stress tests + budget checks + GC policy fixtures |
| `MS-G05 Safety` | Policy tiers gate risky actions | Write/destructive actions run without guard | execution-policy tests |
| `MS-G06 UX` | Memory browser and action center keyboard/mouse usable | Unnavigable/ambiguous controls | overlay integration tests |
| `MS-G07 Docs` | Architecture/usage/troubleshooting updated together | behavior ships without docs parity | docs-check output |
| `MS-G08 Release` | CI profile + memory-specific tests green | Any mandatory lane missing/failing | CI evidence bundle |
| `MS-G09 Validation` | Card/context claims are citation-backed, branch-validated, grade-labeled, and contradiction-checked before injection | Stale/contradicted/unverified claims included silently | card-validation tests + validation-grade fixtures + pack validation report |
| `MS-G10 Tooling` | `devctl`/git/release-note outputs ingest cleanly into canonical memory events/artifacts | Tool outputs dropped or non-deterministically parsed | ingestion fixtures + compiler golden files |
| `MS-G11 Interop` | MCP read-only memory resources/tools (`boot_pack`, `task_pack`, `search`, `validation_report`) are deterministic and policy-safe by default | Client-specific drift, missing provenance contract, or unsafe default exposure | MCP integration tests + policy snapshots |
| `MS-G12 Automation` | Repetition-mined suggestions meet quality/safety thresholds and require explicit approval | Noisy/unsafe suggestions auto-applied or weakly evidenced | suggestion precision metrics + approval-flow tests |
| `MS-G13 Import Privacy` | External transcript imports are opt-in, provenance-tagged, and redaction-validated | Silent import, missing provenance, or unsafe storage of sensitive content | import fixtures + redaction tests + policy checks |
| `MS-G14 Isolation` | Action execution respects selected isolation profile and policy boundaries | Commands escape profile boundaries or bypass policy checks | isolation integration tests + escape-attempt fixtures |
| `MS-G15 Compaction` | Compaction improves or preserves task quality while reducing context cost | Accuracy regresses or citations break under compaction | A/B benchmark reports + threshold checks |
| `MS-G16 Acceleration` | Hardware-accelerated paths improve throughput/latency without quality regressions | Speedups reduce task success/citation fidelity or bypass safety contracts | benchmark matrix + non-inferiority report + fallback tests |
| `MS-G17 Symbolic` | Symbolic compaction is reversible, citation-equivalent, and non-inferior vs raw packs | Aliasing drops distinctions, breaks evidence parity, or regresses quality | round-trip fixtures + citation-equivalence tests + non-inferiority report |
| `MS-G18 Survival Index` | Compaction survival index achieves ≥ 20% recall lift over no-memory baseline, 100% drill-down resolution, ≥ 90% abstention accuracy, and passes cross-IDE continuity | Index does not beat raw event dump, evidence refs break, or cross-IDE recall fails | A/B recall fixtures + compaction simulation tests + cross-IDE replay + human spot-check (8/10) |
| `MS-G19 Retrieval Router` | Hybrid strategy matches or beats best single strategy on every query class; router adds no measurable latency regression | Hybrid loses to single strategy on any class, or router overhead exceeds 50ms p95 | per-class A/B benchmarks + latency profiling + fallback-to-single tests |
| `MS-G20 Memory Browser` | All 5 view modes navigable via keyboard, injection delivers selected events into AI context, cross-IDE rendering consistent | Overlay crashes, injection drops events, or rendering breaks on any supported terminal | overlay integration tests + injection roundtrip fixtures + multi-terminal render checks |

## Interop Contract (Codex + Claude + Future)

Primary contract is model-neutral `context_pack.json`.  
Adapter layers may emit backend-friendly text prompts, but canonical memory stays JSON.

Required adapter properties:

- deterministic formatting
- provenance retained
- token-budget aware truncation
- no hidden mutation of canonical evidence ordering without explicit policy
- every tool response includes source IDs suitable for downstream citations
- review/control-plane attachments pick the receiver adapter profile
  (`canonical`, `codex`, `claude`, `gemini`) at projection time while the
  canonical JSON pack remains the source of truth
- `context_pack_refs` used by review/control-plane packets must resolve back to
  canonical pack artifacts and evidence IDs without lossy rewriting

## Verification Bundle (per Memory PR)

```bash
python3 dev/scripts/devctl.py check --profile ci
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py hygiene
cd rust && cargo test --bin voiceterm
```

Additional memory gates (to add with implementation):

```bash
cd rust && cargo test memory::
cd rust && cargo test action_center::
cd rust && cargo test memory::survival_index::   # Level 1-3 survival index tests
python3 dev/scripts/checks/check_survival_index_recall.py  # Level 4-5 A/B recall gate
```

## Open Decisions (Track Early)

1. Vector backend priority after FTS baseline (local embedding engine choice + fallback path)?
2. Card TTL defaults by type (`decision` vs `task_state` vs `gotcha`)?
3. Card update policy: manual approval only or optional auto-propose with explicit accept/reject?
4. Should action templates be project-local (`.voiceterm/actions.yaml`) and signed/hashed?
5. MCP rollout shape after read-only default: which action tools unlock first and under what isolation evidence?
6. Should automation suggestions target `AGENTS.md` only, or also generate optional `CLAUDE.md`/macro-pack snippets?
7. What minimum support/confidence thresholds gate script candidate surfacing?
8. Should imported external chats participate in automation mining by default, or stay retrieval-only until approved?
9. Should `container_strict` become mandatory for any non-read-only autonomous action mode?
10. What non-inferiority threshold defines compaction "safe to enable by default"?
11. Which compaction strategy is default candidate first: extractive, abstractive-with-citations, or hybrid?
12. Which acceleration backend ships first on macOS (`Accelerate` vs `Metal` vs `Core ML`)?
13. Do we require acceleration to stay deterministic with CPU reference at evidence ordering level?
14. What minimum hardware matrix is required before enabling acceleration outside opt-in mode?
15. What deterministic segmentation rules define Memory Unit boundaries (`task_ref`, time-gap, phase transitions)?
16. What contradiction-resolution policy is required before returning conflicted cards to `eligible`?
17. What active-index GC thresholds keep retrieval quality high without dropping necessary minority signals?
18. What symbolic dictionary scope should be default (`session`, `project`, or `task_pack` only)?
19. Should symbolic compaction stay export-only first, or be allowed in live prompt injection once `MS-G17` is green?

## Progress Log

- 2026-03-09: Tightened the boot-pack proving substrate so summary fields stay
  provenance-aligned under token pressure. `generate_boot_pack()` now derives
  `active_tasks` and `recent_decisions` from the same budget-included evidence
  slice it renders, so packs no longer mention trimmed-out tasks or decisions
  that are absent from the actual evidence block.
- 2026-03-09: Landed a bounded live-ingest metadata slice under the existing
  retrieval/context-pack lane. `memory/ingest.rs` now auto-extracts normalized
  `MP-*` task refs, obvious repo file-path entities, and a small deterministic
  topic-tag set from transcript / PTY input / PTY output text before events hit
  the index, so real runtime `ByTask` / `ByTopic` queries and `task_pack`
  generation no longer depend on the manual low-level ingest path to populate
  metadata.
- 2026-03-09: Reconciled the Memory Studio spec with
  `dev/active/MASTER_PLAN.md` and the adjacent MP-340 / MP-355 / MP-359 plan
  docs so the memory lane now states the shipped proof path honestly. Current
  live proof is limited to operator-cockpit memory mode/status visibility, the
  read-only Memory tab fed by ingest/review/boot-pack/handoff previews, and
  Boot-pack-backed handoff prompt generation; `task_pack`,
  `session_handoff`, and `survival_index` query/export closure still remain
  open along with persisted `memory_mode`, `context_pack_refs`, and packet-
  outcome ingest.
- 2026-03-09: Closed the bounded operator-cockpit query/export sub-slice in
  the Rust runtime. Memory-tab refresh and visible-tab polling now emit
  repo-visible `.voiceterm/memory/exports/*.{json,md}` artifacts for
  `boot_pack`, `task_pack`, `session_handoff`, and `survival_index`, and the
  Memory tab now labels those refs honestly as real JSON/Markdown outputs
  instead of planned paths.
- 2026-03-09: Landed the first attach-by-ref review/control bridge over those
  exports. Event-backed review packets now carry structured `context_pack_refs`
  end-to-end, `actions.json` and `latest.md` preserve the same attachments, the
  Rust review surface renders them from structured artifacts, and the Operator
  Console approval path round-trips them through typed JSON/Markdown decision
  artifacts. Remaining bridge work is packet-outcome ingest into canonical
  memory events plus broader `controller_state` parity across Rust/phone/desktop.
- 2026-03-09: Landed the first attach-by-ref `context_pack_refs` bridge slice
  across the structured review path. Event-backed `devctl review-channel`
  packets now preserve typed pack refs into reduced `review_state` plus
  `actions.json`, the Rust review artifact parser/operator lane/fresh bootstrap
  prompt now consume those refs read-only, and the PyQt6 Operator Console now
  keeps the same refs lossless through approval loading, decision-command JSON,
  operator-decision artifacts, and approval detail rendering. Remaining
  `MP-238` scope is controller-state parity plus packet-outcome ingest back into
  canonical memory events.
- 2026-03-09: Restored clean tracker ownership for the memory lane by fixing
  the unrelated `MP-230` numbering collision in `MASTER_PLAN`; Memory Studio
  now consistently owns `MP-230..MP-255` again across the index, tracker, and
  spec surfaces.
- 2026-03-09: Landed the bounded `MP-243` memory-mode persistence slice in the
  runtime path: startup now restores the persisted mode instead of defaulting,
  runtime config snapshots preserve/write `memory_mode`, and the dev-panel mode
  toggle saves immediately so later snapshots reflect the configured state.
  This closes the persistent-config/startup-restore sub-slice while leaving
  broader trust/privacy UX outside `--dev` open.
- 2026-03-09: Landed the first deterministic survival-index retrieval-trace
  slice for compaction/recovery continuity. Added `memory/survival_index.rs`
  with bounded task-focus + recent-context query plans, per-query token-budget
  traces, deduplicated scored evidence rows, and markdown/JSON rendering. The
  Memory cockpit now exports `survival_index.json` from that structured payload
  (instead of count-only preview lines), and refresh polling coverage now
  asserts the export carries both `query_traces` and `evidence`.

## Audit Evidence

Scope note: this evidence block covers the plan-sync and tooling-doc checks for
the 2026-03-09 memory-lane alignment slice. Broader repo-wide tooling/runtime
failures remain tracked outside this spec.

| Check | Evidence | Status |
|---|---|---|
| `python3 dev/scripts/checks/check_active_plan_sync.py` | `ok: True` after recording the 2026-03-09 Memory Studio progress/audit entries; registry/tracker/spec sync stayed clean (`active_markdown_files=19`, `registry_paths=19`). | done |
| `python3 dev/scripts/checks/check_multi_agent_sync.py` | `ok: True` after the memory-lane plan-state update; required/master/coordination agent sets still match and no sync errors were reported. | done |
| `python3 dev/scripts/devctl.py docs-check --strict-tooling` | `ok: True` after the memory-lane plan-state update; tooling-policy, active-plan sync, multi-agent sync, workflow-shell hygiene, and bundle/workflow parity all remained green. | done |
| `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test --bin voiceterm memory_page -- --nocapture` + `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test --bin voiceterm background_review_poll_refreshes_memory_when_memory_tab_visible -- --nocapture` | Targeted Rust proof for the Memory cockpit export slice passed (`6` focused tests across cockpit rendering, Enter refresh, visible-tab polling, and `m`-key mode refresh). `guard-run` post-check needed one host-access rerun of `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel` because sandboxed `ps` access blocked the required host-process hygiene step; elevated rerun exited `0` after cleaning one stale repo-related process. | done |
| `python3 dev/scripts/devctl.py process-cleanup --verify --format md` | `ok: True`; no orphaned/stale repo processes, cleanup target count `0`, and verify stayed green while one recent active Operator Console process was left running and reported as a warning instead of being killed. | done |
| `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test --bin voiceterm memory::context_pack:: -- --nocapture` | `14 passed`; verified the boot-pack budget-alignment fix so `active_tasks` / `recent_decisions` no longer leak trimmed-out retrieval results beyond the rendered evidence slice. | done |
| `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test --bin voiceterm memory:: -- --nocapture` | `109 passed`; verified the deterministic metadata extraction slice across ingest, retrieval, context-pack, governance/store/type regressions, plus the new task-pack proof from live-ingested `MP-*` refs. | done |
| `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test --bin voiceterm persistent_config::tests -- --nocapture` | `16 passed`; verified the persistent-config memory-mode path after the MP-243 startup/persistence slice landed. | done |
| `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test --bin voiceterm memory_mode -- --nocapture` | `10 passed`; verified runtime memory-mode behavior and regression coverage after wiring persisted startup restore + immediate save. | done |
| `cargo test memory::survival_index:: -- --nocapture` | `5 passed`; verifies deterministic survival-index query planning, fallback retrieval behavior, task/decision extraction, and markdown rendering for compaction-recovery exports. | done |
| `cargo test dev_panel_overlay::refresh_poll::memory_page_enter -- --nocapture` | `2 passed`; validates Memory cockpit Enter-refresh path and confirms `survival_index.json` includes structured `query_traces` + `evidence` payload keys. | done |
| `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel` | passed after rerunning with host-process access when the initial guard-run follow-up hit sandboxed `ps`; final quick profile finished green. | done |

## Research References (2026-02-19)

Product docs:

- Anthropic Claude Code memory: https://docs.anthropic.com/en/docs/claude-code/memory
- Anthropic Claude Code slash commands: https://docs.anthropic.com/en/docs/claude-code/slash-commands
- Anthropic Claude Code hooks: https://docs.anthropic.com/en/docs/claude-code/hooks
- OpenAI ChatGPT memory controls: https://help.openai.com/en/articles/8590148-memory-faq
- OpenAI memory announcement: https://openai.com/index/memory-and-new-controls-for-chatgpt
- OpenAI ChatGPT data export: https://help.openai.com/en/articles/7260999-how-do-i-export-my-chatgpt-history-and-data
- Google Gemini memory controls: https://support.google.com/gemini/answer/16276260?hl=en
- GitHub Copilot coding-agent memory guidance: https://docs.github.com/en/copilot/customizing-copilot-coding-agent/adding-custom-instructions-for-github-copilot
- GitHub Copilot custom repository instructions (`.github/copilot-instructions.md`, `AGENTS.md` support): https://docs.github.com/en/copilot/how-tos/agents/copilot-coding-agent/customizing-the-development-environment-for-copilot-coding-agent
- Warp Workflows (reusable command automation UX): https://docs.warp.dev/features/workflows
- OpenAI Codex product overview: https://openai.com/codex/
- OpenAI Introducing Codex (multi-agent workflow context): https://openai.com/index/introducing-codex/
- ZGraph concept source (local): `/Users/jguida941/Zygraph_Visualizer/ZGraph-Notation/README.md`
- ZGraph notation whitepaper draft (local): `/Users/jguida941/Zygraph_Visualizer/ZGraph-Notation/ZGraph Notation- A Student-Invented Framework for Adjacency Data Compression and Graph Analysis.txt`
- ZGraph scientific analysis notes (local): `/Users/jguida941/Zygraph_Visualizer/ZGraph-Notation/ZGraphVisualizer/ZGRAPH_SCIENTIFIC_ANALYSIS_WHITEPAPER.md`

Industry memory architecture (2026):

- OpenAI Stateful Runtime Environment: https://openai.com/index/introducing-the-stateful-runtime-environment-for-agents-in-amazon-bedrock/
- OpenAI + AWS stateful agent architecture: https://venturebeat.com/orchestration/openais-big-investment-from-aws-comes-with-something-else-new-stateful
- Google Always-On Memory Agent (open-source): https://venturebeat.com/orchestration/google-pm-open-sources-always-on-memory-agent-ditching-vector-databases-for
- Google ADK Memory docs: https://google.github.io/adk-docs/sessions/memory/
- Mem0 universal memory layer: https://mem0.ai/
- Attention Matching KV cache compaction (MIT, arXiv:2602.16284): https://arxiv.org/abs/2602.16284
- VentureBeat coverage of Attention Matching: https://venturebeat.com/orchestration/new-kv-cache-compaction-technique-cuts-llm-memory-50x-without-accuracy-loss
- OpenAI context engineering for personalization: https://developers.openai.com/cookbook/examples/agents_sdk/context_personalization/
- OpenAI session memory management: https://cookbook.openai.com/examples/agents_sdk/session_memory

Memory/retrieval research:

- Retrieval-Augmented Generation (RAG): https://arxiv.org/abs/2005.11401
- LLM Prompt Compression (LLMLingua): https://aclanthology.org/2023.emnlp-main.825/
- Long-context Prompt Compression (LongLLMLingua): https://aclanthology.org/2024.acl-long.91/
- ReAct (reason + act): https://arxiv.org/abs/2210.03629
- Reflexion (self-correction memory loop): https://arxiv.org/abs/2303.11366
- MemGPT (virtual context management): https://arxiv.org/abs/2310.08560
- RAPTOR (hierarchical retrieval): https://arxiv.org/abs/2401.18059
- Lost in the Middle (long-context ordering effect): https://arxiv.org/abs/2307.03172
- LongBench (long-context benchmark): https://arxiv.org/abs/2308.14508
- RULER (what real context windows retain): https://arxiv.org/abs/2404.06654
- LoCoMo (long-form conversational memory benchmark): https://arxiv.org/abs/2402.17753
- Generative Agents (memory, reflection, planning): https://arxiv.org/abs/2304.03442
- PrefixSpan (sequential pattern mining baseline for repeated workflow detection): https://dl.acm.org/doi/10.1145/335191.335372
- HippoRAG (knowledge-graph retrieval for RAG): https://arxiv.org/abs/2405.14831
- HippoRAG 2 (agentic graph-memory evolution): https://arxiv.org/abs/2502.14802
- A-MEM (agentic memory architecture): https://arxiv.org/abs/2502.12110
- Memory-R1 (reasoning-driven memory operations): https://arxiv.org/abs/2508.19828
- ColBERT (late interaction retrieval): https://arxiv.org/abs/2004.12832
- ColBERTv2 (lightweight late interaction retrieval): https://arxiv.org/abs/2112.01488
- kNN-LM (nearest-neighbor language modeling): https://arxiv.org/abs/1911.00172
- RETRO (retrieval-enhanced transformer): https://arxiv.org/abs/2112.04426

Graph + indexing + safety:

- GraphRAG project: https://github.com/microsoft/graphrag
- GraphRAG research write-up: https://www.microsoft.com/en-us/research/blog/graphrag-new-tool-for-complex-data-discovery-now-on-github/
- SQLite FTS5 docs: https://sqlite.org/fts5.html
- SQLite WAL mode: https://sqlite.org/wal.html
- SQLite isolation details: https://sqlite.org/isolation.html
- sqlite-vec (SQLite vector extension): https://github.com/asg017/sqlite-vec
- sqlite-vss (SQLite vector search extension): https://github.com/asg017/sqlite-vss
- MCP security best practices: https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices
- Anthropic developer mode (tool safety warning context): https://docs.anthropic.com/en/docs/claude-code/features/developer-mode
- Process Mining Manifesto (event-log mining governance baseline): https://link.springer.com/article/10.1007/s13740-011-0004-7
- Event-log foundations for process mining (case/activity/time model): https://link.springer.com/chapter/10.1007/978-3-662-49851-4_2
- NIST Application Container Security Guide (SP 800-190): https://doi.org/10.6028/NIST.SP.800-190
- OWASP Docker Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html
- Apple Accelerate framework docs: https://developer.apple.com/documentation/accelerate
- Apple Metal Performance Shaders docs: https://developer.apple.com/documentation/metalperformanceshaders
- Apple Core ML docs: https://developer.apple.com/documentation/coreml
