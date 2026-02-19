# Memory + Action Studio Plan (Semantic Memory + Agent Overlay)

Date: 2026-02-19  
Status: Activated planning track (execution mirrored in `dev/active/MASTER_PLAN.md` as MP-230..MP-253)  
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

## Design Principles (Required)

1. Local-first by default
2. Structured-first storage (JSON/SQLite), markdown as export
3. Deterministic retrieval with traceable scoring
4. Bounded memory and CPU budgets
5. Safe execution model for write/destructive commands
6. Explicit provenance on all recalled context
7. Validation-before-injection for durable repo claims

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

## Information Model (AI-Usable Formats)

### Memory Types (Required)

- Episodic memory: chronological events (who said/did what and when)
- Semantic memory: topic/entity/task summaries and links
- Procedural memory: reusable workflows/templates/rules
- Execution memory: command runs, exit codes, test/lint outcomes, artifacts

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
- `validation` (`status`, `last_checked_at`, `validator`)
- `ttl_policy` (`decay_days`, optional `max_age_days`)
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
    "last_checked_at": "2026-02-19T21:08:00Z",
    "validator": "memory.validate_card"
  },
  "ttl_policy": {
    "decay_days": 28
  }
}
```

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
  "entities": ["src/src/bin/voiceterm/transcript_history.rs"],
  "task_refs": ["MP-229"],
  "artifacts": [
    {
      "kind": "file",
      "ref": "src/src/bin/voiceterm/transcript_history.rs"
    }
  ],
  "importance": 0.72,
  "confidence": 0.95,
  "hash": "sha256:..."
}
```

### Storage Layers

1. Append log: `.voiceterm/memory/events.jsonl`  
   Immutable, line-delimited JSON for replay/audit.
2. Query index: `.voiceterm/memory/index.sqlite`  
   Fast lookup for topic/task/time/source queries.
3. Optional semantic index: `.voiceterm/memory/vectors.*`  
   Pluggable vector store for embedding search.
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
- `compiled_summaries`

## Retrieval Contract (Accuracy + Efficiency)

### Query Types

- `recent(n, filters)`
- `by_topic(topic, n)`
- `by_task(mp_or_issue, n)`
- `semantic(query, n)`
- `timeline(start, end, filters)`

### Ranking Formula (v1)

`score = 0.40 * semantic + 0.25 * lexical + 0.20 * recency + 0.15 * importance`

Rules:

- always return source/provenance metadata with each hit
- dedupe near-identical events by `hash` + text similarity window
- cap retrieval to bounded token budget before pack generation
- reject stale/failed-validation cards from deterministic pack mode unless explicitly requested

### Retrieval Pipeline (v1)

1. Fast prefilter: project/session/time/source constraints
2. Lexical candidate pass: SQLite FTS5/BM25 on exact tokens (files, flags, IDs, commands)
3. Semantic rerank: embedding similarity (local-first backend)
4. Graph/task boost: linked task/artifact/entity relationship signals
5. Final dedupe + diversity pass: avoid repetitive near-duplicate context rows

### Context Packing Rules (Lost-in-the-Middle Aware)

- place highest-priority facts at pack head and tail (not only middle)
- include short "critical facts" block before detailed evidence
- enforce max tokens per section to avoid one noisy source dominating pack
- emit citations/provenance for every summary claim

### Context Pack Output

Each retrieval request can produce:

1. `context_pack.json` (machine)
2. `context_pack.md` (human)

`context_pack.json` minimum fields:

- `query`
- `generated_at`
- `pack_type` (`boot` | `task`)
- `summary`
- `active_tasks`
- `recent_decisions`
- `changed_files`
- `open_questions`
- `token_budget` (`target`, `used`, `trimmed`)
- `validation_report` (`checked`, `failed`, `stale`)
- `source_mix` (counts by source type: chat/terminal/git/files/docs)
- `evidence[]` (event references with scores)
- `inclusion_reason[]` (why each top item was selected)

## Overlay Surfaces (Memory + Actions)

### 1) Memory Browser

- filter by topic/source/task/date
- expandable rows (preview + full payload)
- jump to related files/tasks
- replay user-safe entries only

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

Proposed module tree under `src/src/bin/voiceterm/`:

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
  - `src/src/bin/voiceterm/event_loop.rs`
  - `src/src/bin/voiceterm/event_loop/output_dispatch.rs`
  - `src/src/bin/voiceterm/voice_control/drain/transcript_delivery.rs`
- current memory/history:
  - `src/src/bin/voiceterm/transcript_history.rs`
  - `src/src/bin/voiceterm/session_memory.rs`
- overlays/input:
  - `src/src/bin/voiceterm/overlays.rs`
  - `src/src/bin/voiceterm/input/event.rs`
  - `src/src/bin/voiceterm/input/parser.rs`
- config flags:
  - `src/src/config/mod.rs`

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
   - `session_handoff.{json,md}` from canonical events + devctl/git artifacts

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
- ranking + provenance
- deterministic context pack generator
- memory-card CRUD + evidence linking + validation status checks

### M2 Memory Overlay UX

- memory browser with filters/expand/scroll
- session review/handoff export
- card inspection/edit flow (claim, evidence, validation, TTL)

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

- backend adapters for Codex/Claude context-pack injection formats
- optional export/import for project memory snapshots
- read-only MCP server for memory resources + context-pack tools
- staged action-tool MCP exposure after safety gates are green

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

## Memory Studio Gates

| Gate | Pass Criteria | Fail Criteria | Evidence |
|---|---|---|---|
| `MS-G01 Schema` | Events validate against canonical schema | Ad hoc/partial event formats in runtime | schema tests + fixtures |
| `MS-G02 Storage` | JSONL + SQLite stay in sync under load | Missing/duplicate events | ingest + recovery tests |
| `MS-G03 Retrieval` | Query APIs return relevant, provenance-tagged results | Opaque, untraceable context | ranking tests + golden packs |
| `MS-G04 Boundedness` | Retention and size limits enforced | Unbounded growth | stress tests + budget checks |
| `MS-G05 Safety` | Policy tiers gate risky actions | Write/destructive actions run without guard | execution-policy tests |
| `MS-G06 UX` | Memory browser and action center keyboard/mouse usable | Unnavigable/ambiguous controls | overlay integration tests |
| `MS-G07 Docs` | Architecture/usage/troubleshooting updated together | behavior ships without docs parity | docs-check output |
| `MS-G08 Release` | CI profile + memory-specific tests green | Any mandatory lane missing/failing | CI evidence bundle |
| `MS-G09 Validation` | Card/context claims are citation-backed and branch-validated before injection | Stale/unverified claims included silently | card-validation tests + pack validation report |
| `MS-G10 Tooling` | `devctl`/git/release-note outputs ingest cleanly into canonical memory events/artifacts | Tool outputs dropped or non-deterministically parsed | ingestion fixtures + compiler golden files |
| `MS-G11 Interop` | MCP read-only memory resources/tools are deterministic and policy-safe | Client-specific drift or unsafe default exposure | MCP integration tests + policy snapshots |
| `MS-G12 Automation` | Repetition-mined suggestions meet quality/safety thresholds and require explicit approval | Noisy/unsafe suggestions auto-applied or weakly evidenced | suggestion precision metrics + approval-flow tests |
| `MS-G13 Import Privacy` | External transcript imports are opt-in, provenance-tagged, and redaction-validated | Silent import, missing provenance, or unsafe storage of sensitive content | import fixtures + redaction tests + policy checks |
| `MS-G14 Isolation` | Action execution respects selected isolation profile and policy boundaries | Commands escape profile boundaries or bypass policy checks | isolation integration tests + escape-attempt fixtures |
| `MS-G15 Compaction` | Compaction improves or preserves task quality while reducing context cost | Accuracy regresses or citations break under compaction | A/B benchmark reports + threshold checks |
| `MS-G16 Acceleration` | Hardware-accelerated paths improve throughput/latency without quality regressions | Speedups reduce task success/citation fidelity or bypass safety contracts | benchmark matrix + non-inferiority report + fallback tests |

## Interop Contract (Codex + Claude + Future)

Primary contract is model-neutral `context_pack.json`.  
Adapter layers may emit backend-friendly text prompts, but canonical memory stays JSON.

Required adapter properties:

- deterministic formatting
- provenance retained
- token-budget aware truncation
- no hidden mutation of canonical evidence ordering without explicit policy
- every tool response includes source IDs suitable for downstream citations

## Verification Bundle (per Memory PR)

```bash
python3 dev/scripts/devctl.py check --profile ci
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py hygiene
cd src && cargo test --bin voiceterm
```

Additional memory gates (to add with implementation):

```bash
cd src && cargo test memory::
cd src && cargo test action_center::
```

## Open Decisions (Track Early)

1. Vector backend priority after FTS baseline (local embedding engine choice + fallback path)?
2. Card TTL defaults by type (`decision` vs `task_state` vs `gotcha`)?
3. Card update policy: manual approval only or optional auto-propose with explicit accept/reject?
4. Should action templates be project-local (`.voiceterm/actions.yaml`) and signed/hashed?
5. MCP rollout shape: read-only memory in first cut, action tools in second cut?
6. Should automation suggestions target `AGENTS.md` only, or also generate optional `CLAUDE.md`/macro-pack snippets?
7. What minimum support/confidence thresholds gate script candidate surfacing?
8. Should imported external chats participate in automation mining by default, or stay retrieval-only until approved?
9. Should `container_strict` become mandatory for any non-read-only autonomous action mode?
10. What non-inferiority threshold defines compaction "safe to enable by default"?
11. Which compaction strategy is default candidate first: extractive, abstractive-with-citations, or hybrid?
12. Which acceleration backend ships first on macOS (`Accelerate` vs `Metal` vs `Core ML`)?
13. Do we require acceleration to stay deterministic with CPU reference at evidence ordering level?
14. What minimum hardware matrix is required before enabling acceleration outside opt-in mode?

## Research References (2026-02-19)

Product docs:

- Anthropic Claude Code memory: https://docs.anthropic.com/en/docs/claude-code/memory
- Anthropic Claude Code slash commands: https://docs.anthropic.com/en/docs/claude-code/slash-commands
- Anthropic Claude Code hooks: https://docs.anthropic.com/en/docs/claude-code/hooks
- OpenAI ChatGPT memory controls: https://help.openai.com/en/articles/8590148-memory-in-chatgpt
- OpenAI memory announcement: https://openai.com/index/memory-and-new-controls-for-chatgpt
- OpenAI ChatGPT data export: https://help.openai.com/en/articles/7260999-how-do-i-export-my-chatgpt-history-and-data
- Google Gemini memory controls: https://support.google.com/gemini/answer/16276260?hl=en
- GitHub Copilot coding-agent memory guidance: https://docs.github.com/en/copilot/customizing-copilot-coding-agent/adding-custom-instructions-for-github-copilot
- GitHub Copilot custom repository instructions (`.github/copilot-instructions.md`, `AGENTS.md` support): https://docs.github.com/en/copilot/how-tos/agents/copilot-coding-agent/customizing-the-development-environment-for-copilot-coding-agent
- Warp Workflows (reusable command automation UX): https://docs.warp.dev/features/workflows
- OpenAI Codex product overview: https://openai.com/codex/
- OpenAI Introducing Codex (multi-agent workflow context): https://openai.com/index/introducing-codex/

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

Graph + indexing + safety:

- GraphRAG project: https://github.com/microsoft/graphrag
- GraphRAG research write-up: https://www.microsoft.com/en-us/research/blog/graphrag-new-tool-for-complex-data-discovery-now-on-github/
- SQLite FTS5 docs: https://sqlite.org/fts5.html
- SQLite WAL mode: https://sqlite.org/wal.html
- SQLite isolation details: https://sqlite.org/isolation.html
- MCP security best practices: https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices
- Anthropic developer mode (tool safety warning context): https://docs.anthropic.com/en/docs/claude-code/features/developer-mode
- Process Mining Manifesto (event-log mining governance baseline): https://link.springer.com/article/10.1007/s13740-011-0004-7
- Event-log foundations for process mining (case/activity/time model): https://link.springer.com/chapter/10.1007/978-3-662-49851-4_2
- NIST Application Container Security Guide (SP 800-190): https://doi.org/10.6028/NIST.SP.800-190
- OWASP Docker Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html
- Apple Accelerate framework docs: https://developer.apple.com/documentation/accelerate
- Apple Metal Performance Shaders docs: https://developer.apple.com/documentation/metalperformanceshaders
- Apple Core ML docs: https://developer.apple.com/documentation/coreml
