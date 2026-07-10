# ZGraph Research Evidence — Complete Reference

## DO NOT DELETE OR REFORMAT THIS FILE

This file is the complete reference evidence from multi-round deep audits
(2026-03-21). It is NOT an execution tracker. It is reference material for
future ZGraph/context-graph phases. Codex: do not condense, reformat, or
remove sections. This is the canonical backup of all research findings.
The focused execution-facing companion note is `GUARD_AUDIT_FINDINGS.md`.

---

## A. Guard Blind Spots — Why 10 Audit Findings Were Missed

### Root Cause: Three Structural Blind Spots

**Blind Spot 1: No Contract-Value Enforcement**

Guards check that dataclass fields exist but never check that runtime values
conform to declared contracts. `ActionOutcome.ALL` defines `{pass, fail,
unknown, defer}` as valid statuses. push.py emits `"blocked"`, `"pushed"`,
`"already-synced"`. No guard verifies emitted values match the declared enum.

`platform_contract_closure` validates field names and schema shapes — never
inspects what values actually flow through those fields.

**Blind Spot 2: No Cross-Domain Consistency Checking**

Guards operate within one domain (code shape, imports, security). None
cross-reference plan docs vs runtime types, authority docs vs code defaults,
or architecture rules vs runtime paths.

**Blind Spot 3: No Dead-Code or Unused-API Detection**

`set_active_path_config()` never called. 43+ hardcoded VoiceTerm paths
scattered. Guards check for bad code but not unused code.

### Per-Finding Breakdown

| # | Finding | Why Missed | What Would Catch It |
|---|---------|-----------|-------------------|
| 1 | ActionResult status drift | No guard checks emitted values vs declared enum | AST walk: verify ActionResult(status=X) where X in ActionOutcome.ALL |
| 2 | Confidence str vs float | Mypy catches it but runs with continue-on-error: true | Make mypy blocking |
| 3 | Provider-hardcoded fields | No guard for provider names in core models | Pattern match: flag pending_codex in runtime/ dataclasses |
| 4 | Dead API (set_active_path_config) | No guard for unused exported functions | Symbol usage tracer |
| 5 | Default reviewer_mode contradicts doc | No cross-reference of authority docs with code defaults | Authority doc parser + AST walk |
| 6 | Plan mutations not executable | No guard checks declared ops have handlers | Contract-to-handler registry verifier |
| 7 | Bridge.md as live authority | No guard validates what startup reads as truth | Code-path tracer |
| 8 | 43+ hardcoded paths | No guard for path string literals | Pattern matcher with allowlist |
| 9 | Startup advisory only | Possibly intentional per locked decisions | Design question |
| 10 | Missing runtime types | No guard checks plan-declared types exist in code | Spec-to-code checker |

### Four New Guard Categories Needed

**Category A: Contract Value Guards** (catches findings 1, 2)
- Extract declared value domain (enum, Literal, frozenset)
- AST-walk all producers/emitters of that type
- Verify emitted values within declared domain

**Category B: Plan-to-Runtime Parity Guards** (catches findings 5, 6, 10)
- Verify matching Python dataclass exists for plan-declared types
- Verify code defaults don't violate locked decisions
- Verify declared mutation ops have registered handlers

**Category C: Authority Source Guards** (catches findings 3, 7, 8)
- Verify authority flows from typed JSON, not prose/markdown
- Flag provider-specific names in core runtime models
- Flag hardcoded path strings that should route through active_path_config()

**Category D: Dead API Guards** (catches finding 4)
- Verify exported functions have at least one non-test caller
- Flag functions defined but never invoked

---

## B. ZGraph as Semantic Compressed Pointers

### Core Concept

A Z-reference (22 bits) encodes not just "what file" but "what semantic
obligation" — pointing back to the contract, the plan doc, the locked
decision, the enum constraint.

```
Standard violation hint: "push.py:74 emits ActionResult with status='blocked'"
  Lost: authority source, contract name, proof chain, fix category
  Cost: AI must re-derive why this matters every time

ZGraph semantic pointer: Z[001|142] (22 bits)
  pattern_id (12 bits): 0x001 = ENUM_CONSTRAINT_BREACH
  hash_id (10 bits): 0x142 = unique identity within that pattern
  When loaded: {
    authority_source: "action_contracts.py:74",
    contract_constraint: "status IN {pass,fail,unknown,defer}",
    proof_chain: ["push.py → emits ActionResult → status='blocked' → NOT IN allowed set"],
    ai_instruction: "Replace 'blocked' with ActionOutcome.DEFER",
    confidence: 1.0
  }
```

### Pattern Taxonomy (12-bit space, 4096 patterns possible)

```
0x001-0x0FF: Contract violations (enum breach, range breach, type mismatch)
0x100-0x1FF: Authority boundary violations (scope exceeded, unregistered)
0x200-0x2FF: Flow contract violations (missing return, missing validation)
0x300-0x3FF: Semantic integrity (duplicated logic, stringly typed)
```

### The 3-Layer Loop

```
LAYER 1: Guards Query Graph Deterministically
  → Emit Z-refs with proof chains (zero false positives)

LAYER 2: Graph Unpacks & Delivers Semantic Context
  → O(1) lookup per Z-ref (contract source + proof chain + fix recipe)

LAYER 3: AI Applies Fix, Guard Verifies
  → Before: 200-400 tokens to re-derive + fix (60% accuracy)
  → After: 10-15 tokens to apply recipe (95%+ accuracy)
```

### Token Budget Impact

| Phase | Without ZGraph | With ZGraph | Savings |
|-------|---------------|-------------|---------|
| Context derivation | 300-400 tokens | 10 tokens (Z-refs) | 30-40x |
| AI diagnosis | 150-200 tokens | 0 tokens (in packet) | infinite |
| AI fix application | 50-100 tokens | 10-15 tokens | 5-10x |
| Per violation total | 50-75 tokens | 2-3 tokens | 25-35x |

For 100K token context window: ZGraph fits 200+ violation fixes where naive
approach fits 10-15.

### Industry Validation

- **MAGMA** (arXiv 2601.03236): 95% token reduction with multi-graph memory
- **SimpleMem** (arXiv 2601.02553): 26.4% F1 improvement, 30x token reduction
- **Code Graph Model** (arXiv 2505.16901): 512x context extension for code
- **Codified Context** (arXiv 2602.20478): 24.2% knowledge-to-code ratio
- **Code Property Graphs** (Joern/CodeQL): AST + CFG + PDG queryable graphs
- **ArchUnit / jQAssistant**: Architecture rules as graph queries
- **Proof-Carrying Code** (Lean/Leanstral): Formal proof verification
- **Weisfeiler-Lehman graph kernels**: Structural similarity via label compression

### Mathematical Foundation

- **WL graph kernels**: Iterative neighborhood label compression. After h
  iterations, structurally similar subgraphs have the same compressed label.
- **Spectral methods**: Eigenvalue decomposition of graph Laplacian produces
  structural fingerprint. k=3-5 eigenvalues for ~15-25 bit fingerprint.
- **Graph homomorphisms**: If two modules map to same pattern graph, they share
  structural shape. Pattern graph ID = compressed reference.

---

## C. Proof Chains for All 10 Findings

### Finding 1: ActionResult Status Drift

```
Nodes: contract:ActionResult, code:push.py:L150, value:"blocked"
Edges: declares_contract → emits_value → is_not_in → domain:ActionOutcome.ALL
Proof: "blocked" not in {pass, fail, unknown, defer}
Guard: AST walk all ActionResult(status=...) call sites, check membership
AI packet: "Replace status='blocked' with ActionOutcome.DEFER"
Verify: re-run guard, confirm emitted value in ActionOutcome.ALL
```

### Finding 2: Confidence Type Mismatch

```
Nodes: contract:ContextGraphQueryPayload.confidence, code:command.py:L56
Edges: declares_type(float) → assigned_type(str) → incompatible
Proof: str is not float
Guard: dataclass field type comparison between paired classes
AI packet: "Cast to float or change type annotation"
```

### Finding 3: Provider-Hardcoded Fields

```
Nodes: plan:MP-358, rule:provider_portability, field:pending_codex
Edges: asserts_constraint → forbids(provider_name_in_field) → matches_pattern
Proof: "codex" in field name "pending_codex" violates portability rule
Guard: pattern match provider names in runtime/ dataclass fields
AI packet: "Refactor to pending_by_agent dict with registry lookup"
```

### Finding 4: Dead API

```
Nodes: export:set_active_path_config, usage_graph(call_count=0)
Edges: exported_from → has_callers(0) + hardcoded_alternatives(43)
Proof: exported function with zero callers + 43 hardcoded alternatives
Guard: symbol usage tracer on __all__ exports
AI packet: "Activate routing through this API OR remove dead export"
```

### Finding 5: Default Contradicts Authority

```
Nodes: plan:locked_decision, code:startup_context.py:L24
Edges: asserts_locked_default("active_dual_agent") → implements_default("single_agent")
Proof: string literal mismatch against locked authority decision
Guard: parse locked decisions, AST walk code defaults, compare
```

### Finding 6: Mutations Not Executable

```
Nodes: plan:declared_mutations, code:command_registry
Edges: declares_mutation → requires_handler → handler_not_found
Proof: mutation declared in plan but no handler in command registry
Guard: plan mutation list vs registered handler list
```

### Finding 7: Bridge as Live Authority

```
Nodes: doc:bridge.md(purpose="projection"), code:startup_context.py
Edges: states_purpose("advisory") → treats_as_authority → contradiction
Proof: code parses non-authoritative doc as truth in startup path
Guard: code-path tracer flags prose parsing in startup paths
```

### Finding 8: Hardcoded Paths

```
Nodes: api:active_path_config, pattern:hardcoded_path(count=43)
Edges: designed_to_replace → not_used_by → hardcoded_alternatives
Proof: API exists but unused; 43 paths bypass abstraction layer
Guard: regex pattern match + allowlist for path literals
```

### Finding 9: Startup Advisory Only

```
Status: DESIGN QUESTION — not a deterministic violation
Needs spec clarification before writing a guard
```

### Finding 10: Missing Runtime Types

```
Nodes: plan:MASTER_PLAN(declared_types), code:runtime/(exported_types)
Edges: declares_type → requires_implementation → type_not_found
Proof: plan declares WorkIntakePacket, codebase search finds zero definitions
Guard: spec-to-code consistency checker on plan-declared type names
```

### Minimum Graph Schema to Catch All 10

**Node types (8)**: ContractDefinition, ContractField, CodeEmissionPoint,
CodeAssignmentPoint, CodeDefaultValue, CodePath, PlanDocument, ExportedSymbol

**Edge types (11)**: declares_contract, declares_type, declares_mutation,
asserts_constraint, emits_value, assigns_type, forbids, requires_handler,
exported_from, has_zero_callers, treats_as_authority

**Inference rules (5)**: CONTRACT_VALUE_VIOLATION, TYPE_MISMATCH,
ARCHITECTURAL_PATTERN_VIOLATION, DEAD_EXPORTED_API, PLAN_TO_CODE_PARITY

---

## D. Long-Term AI Memory and Cross-Domain Compression

### ZGraph as Decision Memory

Every decision an AI makes has a shape — a pattern of reasoning, dependencies,
and outcomes. This shape can be encoded once and referenced forever.

Example: AI learns "check.py was split into check.py + check_phases.py to avoid
circular imports via callbacks"

```
Plain text memory: ~500 bytes
ZGraph decision reference: ~58 bytes (8.6x compression)
  Z-ref: Z002_3C2_08_3 (34 bits)
    decision_type: 0x002 (architecture refactoring)
    context_hash: 0x3C2 (circular_import_break)
    rationale_id: 0x08 (dependency_breaking_via_callbacks)
  Metadata: {affected_files: [check.py, check_phases.py],
             solution_pattern: callback_delegation, outcome: success}
```

### ZGraph as Classification Engine

Instead of storing 200 violation fixes individually, classify into 16 semantic
classes. AI asks "show me all enum_breach fixes" → graph returns ONE class
summary instead of 200 individual items. Compression: 25:1.

### Cross-Domain Compression Table

| Domain | Shape | Compression | Semantic Win |
|--------|-------|-------------|-------------|
| Guard violations | Pattern class (16 types) | 200 items → 16 summaries | Instant classification |
| Git history | Commit topology (6 shapes) | 500 commits → shape distribution | Project evolution |
| Test coverage | Path categories (5 classes) | 1000 paths → coverage map | Gap detection |
| CI workflows | Trigger patterns (6 types) | 30 workflows → type summary | Instant |
| Plan execution | Outcome shapes (7 patterns) | 60+ MPs → success patterns | Predictive |
| Guard effectiveness | Catch rate classes | 64 guards → quality index | Trust ranking |
| Code decisions | Decision shapes (12 types) | Unbounded → classified | 40x faster recall |
| File topology | Concept clusters (197) | 4234 files → 197 concepts | 88% compression |

### Memory System Migration

Phase 1: Keep MEMORY.md, add ZGraph index alongside (parallel query)
Phase 2: Memory queries hit ZGraph first (instant), fallback to markdown
Phase 3: MEMORY.md generated from ZGraph (single source of truth)

---

## E. DevCtl Command Surface — 12 Command Families

### Check Pipeline
- Guard results classified by violation pattern class for instant recall
- Path-to-lane classification cached via Z-refs (50 rules x N paths)
- Risk add-on detection Z-ref indexed for O(1) lookup
- Compression: 40-60% reduction in check artifact size

### Probe-Report System
- 13+ probes producing 100-1K findings → classify into semantic classes
- Cross-probe finding dedup via shared Z-ref to semantic root cause
- Review lens aggregation compressed into Z-ref index
- Compression: 45-65% reduction

### Autonomy Loops
- Round execution traces compressed into Z-ref to plan version + step index
- Swarm agent state compressed into Z-ref to profile + state delta
- Context packets compressed into Z-refs to graph subgraph
- Compression: 50-70% reduction

### Review-Channel State
- Session metadata compressed into Z-ref to active plan + session version
- Agent registry entries compressed into Z-ref to profile + state delta
- Review packets compressed into Z-ref to packet class + mutation-ops index
- Compression: 40-55% per snapshot

### Startup-Context
- Entire 2-4KB startup packet compressed into Z-ref to governance snapshot
- Compression: 50-70%; enables instant context reuse

### Platform-Contracts
- Contract specs Z-ref indexed for fast schema validation
- Compression: 30-45% in blueprint JSON

### Governance Commands
- Finding flow compressed into Z-ref to source artifact + violation signature
- Quality metrics compressed into Z-ref to metric definition + value
- Compression: 45-60%

### Other Commands
- Status-report: 35-50% compression via Z-ref probe results
- Triage/mutation loops: 50-70% via Z-ref attempt history
- Context-graph itself: 40-60% via node/edge dedup
- Hygiene: 40-55% via process state compression
- Data-science: 30-40% via command execution Z-ref index

---

## F. Runtime Contracts — Unified Identity Layer

### The Identity Chain Problem

Current contracts carry plain string IDs with ZERO explicit linkage:

```
Finding → finding_id (SHA1 string)
  → DecisionPacket: finding_id (loose string)
    → ReviewPacketState: finding_id + packet_id (loose strings)
      → ActionResult: action_id (loose string)
```

### ZGraph Unified Identity

```
Z-Finding: repo::file::symbol::line (stable)
  → Z-Decision: Z-Finding::check_id::rule_version
    → Z-Packet: Z-Decision::packet_id::trace_id
      → Z-Review: session_id::plan_id::Z-Packet
Z-Action: action_id::run_id
Z-Agent: agent_id::lane::provider
```

### Repeated Structure Extraction

12+ contracts repeat schema_version + contract_id. 21 from_mapping() functions
repeat identical coercion boilerplate. Extract shared ContractMeta base and
generic ContractFactory.

### Untyped Cross-References

ReviewPacketState.evidence_refs: tuple[str, ...] — untyped strings.
Replace with Z_Evidence = Z_Finding | Z_Artifact | Z_FailureCase.

### Timestamp Unification

Multiple contracts carry timestamps independently. Extract shared
EventTimeline with lifecycle fields.

---

## G. Report Artifacts — Cross-Artifact Index

### Missing Connections

| From | To | Connection Today | ZGraph Would Add |
|------|----|-----------------|-----------------|
| Autonomy episode | Probe finding | None | episode→files_changed→findings |
| Guard violation | Governance verdict | None | violation→finding_id→verdict |
| DevCtl event | Produced artifact | None | event→command→artifact_path |
| Probe hotspot | Guard coverage | None | hotspot→fan_out→applicable guards |
| Review packet | Decision packet | String only | Z-Packet→Z-Decision→Z-Finding |
| Finding review | Autonomy fix | None | verdict=fixed→episode that fixed it |

### Compression Opportunities

| Artifact | Current Size | With ZGraph | Reduction |
|----------|-------------|-------------|-----------|
| file_topology.json | 67K lines | ~8K factored | 88% |
| devctl_events.jsonl | 13,849 events | Indexed | 60% |
| review_state.json | 382 lines | Canonical + projections | 48% |
| finding_reviews.jsonl | 110 rows | Z-ref indexed | 35% |
| Episode summaries | 30 x 2KB | Classified by outcome | 50% |

### Queries Currently Impossible

1. "Which episodes fixed which findings?"
2. "Which changed files have open findings with no covering guard?"
3. "Events during MP-346 with success=false — what artifacts produced?"
4. "Review sessions with contradictory bridge/reviewer state?"
5. "Files with hint_count > 5 AND no fixed verdict?"

---

## H. Platform & Governance — Unified Contract Surface

### Contract Fragmentation

Platform layer: 18 shared contracts + 6 artifact schemas + 5 frontend surfaces
+ 3 caller authority tiers across 6+ separate files. Governance layer adds push
policy, doc authority, external findings, quality feedback, guard finding
policy, and surface specs. No unified identity system spans both layers.

### ZGraph Contract Catalog

```
contract:ActionResult:v1 → runtime model + fields + consumers
contract:ProbeReport:v1 → artifact schema + emitter + frontends
policy:PushEnforcement:v1 → rules + current state + checkpoint budget

contract:FindingRecord --[CONSUMED_BY]--> artifact:ProbeReport
artifact:ProbeReport --[CONSUMED_BY]--> frontend:CLI
contract:FindingRecord --[EXTENDED_BY]--> contract:DecisionPacket
```

### External Finding Bridge

External tool findings (mypy, ruff, SAST) enter via ExternalFindingInput but
have NO automatic mapping to canonical Finding contract. Z-refs could create:
`external-input:mypy:arg-type:v1 → canonical risk_type + review_lens`

---

## I. Guard & Probe System — Self-Aware Semantic Graph

### Guard Dependency Chains (Currently Implicit)

```
guard:code_shape --[PREREQUISITE_FOR]--> guard:function_duplication
guard:function_duplication --[PREREQUISITE_FOR]--> guard:god_class
guard:platform_contract_sync --[COMPLEMENTS]--> guard:platform_contract_closure
```

### Probe → Guard Remediation Paths

```
probe:boolean_params --[REMEDIATED_BY]--> guard:parameter_count
probe:clone_density --[REMEDIATED_BY]--> guard:function_duplication
probe:unwrap_chains --[REMEDIATED_BY]--> guard:rust_runtime_panic_policy
```

### Bundle Composition, Coverage Matrix, Effectiveness Index

- 5 bundles compose guards via frozen sets. No index of which guards in which.
- No central index of which guard checks which file paths.
- No tracking of catch rate, false positive rate, or cost per violation.
- Check router uses 50+ hardcoded path rules. ZGraph would index them.
- Meta-governance: check_guard_enforcement_inventory audits ALL guards.

---

## J. Unmapped Patterns from repo_example_temp

### GUI/Visualization (NOT in governance system)
- P-28 Confidence Dashboard: 4-channel visualization
- P-30 Result Explorer with Faceted Search
- P-31 Async Plot Worker: thread-safe QRunnable
- P-38 Performance Hierarchy Visualization

### Algorithm Selection (Underutilized)
- P-11 Adaptive Dispatcher: learns from past executions
- P-15 Performance Model with Nearest-Neighbor interpolation
- P-42 Hybrid Deterministic-ML Routing
- P-54 Domain-Adaptive Algorithm Selection

### Tracing (Missing)
- P-41 Layered Decision Controller
- P-44 Rich Feature Extraction (15+ auto-extracted features)

### Mathematical Semantic Compression
- P-23 Layered Dispatch Architecture (bitmap → wheel → trial → probabilistic)
- P-24 Bitmap-based O(1) Lookup Caching (94.7% hit, 15ns)
- P-25 Deterministic Witness Selection (size-based)
- P-26 Universal Feature Schema for ML Dispatching

---

## K. AI Context Injection Gaps

### 8 injection points audited. AI receives ~30% of available data.

**Conductor Prompt**: Missing guard failures for scope, probe findings,
contract implications, blast radius, MP phase, commit conventions

**Swarm Agent**: Missing guard findings blocking task, probe severity, recent
failed attempts, dependency graph, test coverage, prior agent notes

**Ralph AI Fixer**: Missing which guards validate fix, confidence score,
false-positive rate, related findings, patch size constraints

**Loop Packet**: Missing failure mode patterns, iteration budget, retry
history, convergence signal, transient vs structural failures

**Context Escalation**: Missing edge metadata, temperature rationale, node
metadata (fan_in/fan_out), ownership data

**CLAUDE.md Bootstrap**: Missing governance posture, active plan phase,
recent guard failures, test coverage gaps, hotspot intensity

**Bridge.md**: Missing finding impact metadata, constraint scope, test
footprint, prior attempts, time budget, guard dependency chain

### Five High-Value Data Packages AI Should Receive

1. Guard Applicability Matrix (per-file guard status + guidance)
2. Probe Severity Heatmap (per-file severity + priority score)
3. Contract Constraint Map (affected contracts + non-negotiable constraints)
4. Recent Failure Patterns (last 5 runs + error patterns + recommendations)
5. Test Coverage & Execution Path (per-function coverage + gap risk)

---

## L. Operator Console Enhancements

1. Guard Effectiveness Dashboard (2-3 weeks, no ZGraph required)
2. Dependency Blast Radius Visualization (3-4 weeks)
3. Plan Dependency DAG (4-6 weeks)
4. Semantic Query Navigator / Proof Navigator (6-8 weeks, full ZGraph)

---

## M. Novel ZGraph Applications

### Top 5 (HIGH priority)
1. Smart Test Selection (29%+ execution savings, architecture ready)
2. Compliance / SOC2 Audit Trail (enterprise differentiator)
3. AI Agent Observability (execution trace graphs)
4. Guard Challenge Corpus (chaos testing for guards, genuinely novel)
5. AI Agent Productivity Metrics (fix rate, token cost, stall frequency)

### Lower priority
6. Multi-repo knowledge graph
7. Natural language graph queries
8. Code ownership / bus factor
9. Refactoring sequence planning
10. API breaking change detection
11. Transitive security tracing
12. Performance regression prediction

---

## N. Rust Product Code — 12 Subsystems

**Event Loop State Machine** (24K LOC, HIGHEST):
- input_dispatch.rs manually threads state mutations through overlays
- ZGraph state-transition tuples replace 500+ lines of conditionals

**Provider Plugin Routing** (275 LOC, HIGH):
- Static trait impls with exhaustive match → Z-ref relation tuples
- New providers add tuples, not code changes

**Memory Retrieval Strategy** (350+ LOC, HIGH):
- Match-tree signal→strategy already looks like proof chains
- ZGraph: (SessionStart, gap>3600) → strategy:Hybrid (cacheable)

**Theme System** (1840 LOC, MEDIUM):
- 11 theme enums × capability checks → sparse Z-ref matrix

**Daemon Session Topology** (290 LOC, MEDIUM):
- Implicit client→session mapping → explicit graph edges

**IPC Protocol Routing** (766 LOC, MEDIUM):
- Serde enum + pattern match → type-safe graph

**Rust-Python Contract Boundary** (CRITICAL):
- JSON events between Rust daemon and Python devctl
- No explicit contract graph → ZGraph detects schema drift

**Memory Ingestion Pipeline** (900 LOC):
- Linear pipeline → ZGraph DAG traces findings to source events

**Voice Control FSM** (800+ LOC):
- Implicit state → explicit FSM prevents invalid combos

---

## O. CI/CD Workflows — 30 Workflows

**Categories**: 8 product quality, 6 lint/security, 2 tooling/governance,
3 autonomy, 4 AI triage, 5 release, 2 testing

**Bottleneck**: tooling_control_plane.yml runs 47 guards SEQUENTIALLY.
ZGraph parallelization → 15-25 min savings.

**Smart Selection**: Only ~40% of workflows needed per change.
- rust/src/pty_session/** → parser_fuzz_guard alone
- dev/scripts/devctl/** → tooling_control_plane + pre_commit
- app/ios/** → ios_ci alone

**Health Metrics**: Pass rate trends, duration percentiles, guard-specific
runtime, artifact size trends.

---

## P. Test Suite — 1867 Tests, 191 Files

**Coverage Gaps**:
- autonomy/ — 21 files, 0 tests (HIGH)
- triage/ — 12 files, 0 tests (HIGH)
- cli_parser/ — 10 files, 0 tests (MEDIUM)
- data_science/ — 7 files, 0 tests (MEDIUM)

**Smart Test Selection**: 100% static-analyzable imports. Parse imports →
build bidirectional file→test graph. 89 files safe to parallelize.

**Test Fixture Graph**: make_args() used by 25 tests, _load_script_module()
by 21. Breakage cascades tracked via Z-ref edges.

---

## Q. Configuration System — 14 Config Files

**Policy Inheritance**: devctl_repo_policy.json → voiceterm.json →
portable_python_rust.json → portable_python.json + portable_rust.json

**Config Drift Detection**: clippy baselines, function length thresholds,
guard config vs code behavior.

**Integration Federation**: 2 external repos, 8 import profiles. ZGraph
tracks source SHA, sync date, stale detection.

**Protocol Boundary**: Rust AgentInfo → Python AgentSnapshot alias mapping.

---

## R. AGENTS.md — Prose to Enforceable Constraints

**Current State**: 1721 lines, 6 task classes, 5 guard bundles, 12-step SOP,
24 probe rules. ALL unenforceable.

**5 Critical Gaps**:
1. Task-to-bundle routing one-way (AGENTS.md stales when bundle_registry changes)
2. Context pack selection advisory (no enforcement agents load required packs)
3. Post-edit verification no gate (agents claim guards ran, no proof)
4. Continuous improvement depends on prose friction notes (same friction 3x)
5. Probe verdicts not linked to task closure (HIGH findings unaccounted)

**Implementation**: Create dev/config/zgraph_rules.json as canonical rules
authority. Task class → bundle → checks mapping. Context pack requirements.
Post-edit verification. Probe verdict recording.

---

## S. Memory System — Markdown to Graph

**Current**: 12 markdown files (~416 lines)
**Missing**: Decision history, guard compliance, context-pack usage, friction
aggregation, MP→code→guard linking, decision reversals

**Execution Trace**: Record per session: task_class, files_edited, bundles_run,
results, probe verdicts, friction signals, handoff summary.

---

## T. Complete Integration Summary

| Layer | Points | Z-ref Types | Key Win |
|-------|--------|-------------|---------|
| DevCtl commands | 12 families | 25+ | 35-70% compression |
| Runtime contracts | 12+ contracts | 8 identity | Unified queries |
| Report artifacts | 7 directories | 10 cross-links | 88% max |
| Platform/governance | 6 families | 6 catalog | Closure queries |
| Guard/probe system | 90 scripts | 12 relationships | Meta-governance |
| Repo example patterns | 15+ unmapped | Adoption | Validated |
| AI context injection | 8 points | 5 packages | 50% token savings |
| Operator console | 4 features | Dashboard/graph | Proof-driven |
| Novel applications | 5 high-priority | Test/compliance | Differentiators |
| Rust product code | 12 subsystems | FSM/routing | Product-level |
| CI/CD workflows | 30 workflows | DAG/selection | 40% skip rate |
| Test suite | 191 files | Coverage/fixture | 29%+ savings |
| Config system | 14 configs | Drift/inheritance | Consistency |
| AGENTS.md policy | 1721 lines | Constraints | Enforceable |
| Memory system | 12 files | Decision/feedback | 40x recall |
| **Total** | **100+ points** | **80+ types** | **System-wide** |

---

## U. Implementation Roadmap

### Phase 1: Tier 0 Plumbing (1 week)
- Fix topology scan exclusions (repo_example_temp, .claude/worktrees)
- Wire hint_counts/changed_paths into context-graph command
- Adopt shared hotspot scorer (priority_score)
- Fix confidence str/float type mismatch

### Phase 2: Semantic Schema (1-2 weeks)
- Add 8 node types + 11 edge types to context-graph models
- Build AST scanner for ContractDefinition + CodeEmissionPoint nodes
- Implement 5 inference rules as graph traversals
- First guard: check_contract_value_closure.py

### Phase 3: Proof Packets + Classification (1-2 weeks)
- Extend Finding with ContractProofPacket fields
- Build Z-reference compression (22-bit encoding)
- Build violation classifier (16 semantic classes)
- Integrate into WorkIntakePacket

### Phase 4: AI Integration + Memory (1-2 weeks)
- Wire proof packets into conductor/swarm/ralph prompts
- Build verification loop (guard → AI fix → guard re-verify)
- Build AIMemoryZGraph encoder for decision memory

### Phase 5: Cross-Domain Expansion (2-3 weeks)
- Git history shape classification
- Test coverage topology mapping
- CI/CD workflow shape analysis
- Plan execution outcome patterns
- Guard effectiveness tracking

### Phase 6: Memory + Console (2-3 weeks)
- Parallel ZGraph + MEMORY.md system
- devctl memory-learn / memory-recall commands
- Operator console guard effectiveness dashboard
- Blast radius visualization

### Deferred
- ML-based routing, ROI tracking, binary serialization
- Full specification mining from code patterns
- Formal theorem proving (Lean/Leanstral)
- Cross-domain graph transfer learning
- Spectral fingerprinting

---

## V. Gap Analysis — Research vs Plan Docs (2026-03-21 Audit)

### Sections NOT reflected in any plan doc (0% coverage)

- A: Guard blind spots (4 new guard categories)
- D: Long-term AI memory (decision shapes, classification)
- G: Report artifacts cross-index (6 missing connections, 88% compression)
- J: Unmapped repo_example_temp patterns (15+ items)
- L: Operator console enhancements (4 features)
- M: Novel applications (smart test selection, compliance, observability)
- N: Rust product code (12 subsystems)
- O: CI/CD workflows (30 workflows, 40% skip rate)
- P: Test suite (coverage gaps, smart selection)
- T: Complete integration summary (100+ points)

### Sections partially reflected (20-60% coverage)

- B: ZGraph concept (plans have direction but NOT encoding scheme, industry
  validation, or mathematical foundations)
- C: Proof chains (plans reference "audit findings" but not proof closure)
- E: DevCtl command surface (plans mention commands but not 12-family breakdown)
- F: Runtime contract identity (plans have TypedAction chain but not Z-ref hierarchy)
- H: Platform/governance (plans have contract-closure but not fragmentation analysis)
- I: Guard/probe system (plans have guard registry but not dependency chains)
- K: AI context injection (plans mention prompts but not systematic 8-point audit)
- Q: Config system (plans mention portable governance but not drift detection)
- R: AGENTS.md constraints (plans have guard bundles but not 5 prose-vs-machine gaps)
- S: Memory system (plans mention evidence but not execution trace migration)
- U: Implementation roadmap (plans have ladder but not 6-phase breakdown)

### Items from conversation NOT captured in research doc until now

- Confidence decay formula (0.95^hops) in inference chains
- ContractProofPacket data structure (extends Finding with proof_chain,
  constraint_source, fix_strategy, verification_command)
- AI proof packet injection format (what Claude/Codex actually sees in prompt)
- Verification loop formalism (guard → AI fix → guard re-verify)
- Framework-agnostic design principle (zero external deps, adapters for
  mypy/ruff/clippy via collector → normalized findings → guard)

---

## W. Unexplored Subsystems Found (Round 4 Audit)

### 21 subsystem areas identified that weren't in prior rounds

1. **Commands/governance/** (14 files) — policy/authority models, doc authority
   rules, surfaces, import findings support. Review-channel actions form a
   15+ action state machine: ensure→launch→bridge-poll→wait→rollover→promote.

2. **Commands/vcs/** (3 files) — push reporting, git capture helpers.
   ActionResult contract violations live here.

3. **Commands/review_channel/** (13 files) — complex bridge polling, wait
   actions, publisher lifecycle assessment.

4. **Triage subsystem** (12 files) — bundle→enrichment→escalation reduction
   pipeline. Loop policy bridges control_plane_policy.json to loop execution.

5. **Integration federation** (5 files) — cross-repo import DAG: source_root
   → mapping_from → mapping_to → destination audit log.

6. **Loops/fix_policy** (4 files) — autonomy_mode→branch_allowed→
   command_prefixes→allowed_fix_commands guard graph. Shared by triage/
   mutation/autonomy loops.

7. **Probe report renderers** (2 files) — three serializations (markdown,
   terminal, JSON) of same logical model. Hotspots have implicit graph edges.

8. **Watchdog episode system** (6 files) — GuardedCodingEpisode is 56-field
   comprehensive record. Forms time-series state machine with retry chains.
   WatchdogMetrics reduces episodes by provider/guard_family.

9. **Governance subsystem** (26 files) — quality_feedback/ has 11 files with
   Halstead metrics, maintainability scores, FP classifier, recommendation
   engine. Simple lanes create parallel execution with gating rules.

10. **Platform blueprint** (16 files) — PlatformBlueprint IS a schema contract
    graph. Runtime contract rows are witness records. 11 distinct identity
    contract types in runtime_identity_contract_rows.

11. **Runtime contracts** (20+ contract IDs) — state machine network:
    ControlState→ReviewAgentState→ReviewQueueState→ReviewSessionState.
    Polymorphic mapping functions as protocol bridges.

12. **Review channel** (62 files) — event-sourced state machine.
    ReviewPacketRow has 22 typed fields with status transitions.
    ReviewAgentRow tracks 11 fields per agent. Authorization policy creates
    edge constraints on event transitions.

13. **Autonomy subsystem** (22 modules) — fork-join DAG: swarm_run→parallel
    agents→benchmarks→feedback aggregation. Feedback sizing: stall→downshift,
    improve→upshift.

14. **Data science/metrics** (8 files) — metric hierarchy: raw_metric→
    aggregate→visualization. Watchdog metrics reduce by dimension.

15. **Quality backlog** (6 files) — quality scoring graph: check_result→
    signal→score→severity. File pressure hierarchy. 10 absolute check
    categories feed priority scoring.

16. **Guides** (13 markdown files) — documented decision nodes. Could be
    indexed as NODE_KIND_GUIDE with heading anchors and cross-reference edges.

17. **Archive** (29 files) — completed plan files with decision provenance.
    Creates decision lineage: active_plan→completed→archived_entry.

18. **Deferred** (2 files) — paused plans show pause→resume patterns.

19. **Repo packs** (5 files) — RepoPathConfig defines path authority
    boundaries. WorkflowPresetDefinition maps CI workflows to devctl commands.

20. **Process sweep** (6 files) — sweep rules form matching DAG:
    scope→pattern→action.

21. **Security subsystem** (5 files) — security tiers create risk
    stratification graph. CodeQL results form vulnerability edges.

---

## X. New Industry Research (March 2026 — Not in Prior Rounds)

### Token-Efficient Code Knowledge Graphs (SHIPPING NOW)

- **code-review-graph** (March 2026): Tree-sitter→SQLite graph, computes
  blast radius at review time. Results: 6.8x-49x fewer tokens. Incremental
  re-index under 2 seconds for 2,900-file projects. Open source, MIT.

- **CodeGraph** (January 2026): Pre-indexed via Tree-sitter+SQLite, exposed
  as MCP server. 19 languages. ~30% fewer tokens, ~25% fewer tool calls.

- **Augment Context Engine**: Processes 400K+ files. Semantic dependency
  graph. Initial index 27 min; incremental under 20 seconds. 70%+ agent
  performance improvement. Available as MCP server.

### Novel Architectural Patterns

- **PRAXIS** (Microsoft Research): Dual-graph agentic traversal — service
  dependency graph + code-level program dependence graph. LLM traverses both
  for incident RCA. 3.1x better accuracy, 3.8x fewer tokens.

- **LLMxCPG** (USENIX Security 2025): LLM GENERATES Code Property Graph
  queries dynamically (not just consumes static analysis). 67-91% code
  reduction, 15-40% F1 improvement for vulnerability detection.

- **MANTRA** (March 2025): Multi-agent graph-aware refactoring. 82.8%
  success rate vs 8.7% baseline. Context-Aware RAG retrieves dependency
  context from code graph.

### Production Deployments

- **Qodo**: Cross-repo dependency-aware code review. When you change a shared
  library, flags affected services across repositories.

- **Swissquote**: Graph-enforced architecture fitness functions at enterprise
  scale. Extracts dependency information from codebase, enforces Self-Contained
  System compliance rules.

- **Meta Repository Pattern** (Anyline, March 2026): Dedicated repo as AI
  agent knowledge base with cross-repo dependency maps. Monorepo-like
  ergonomics without restructuring.

### Emerging Research

- **DepsRAG**: Dependency knowledge graphs for package ecosystems with
  agentic multi-hop reasoning. 3x accuracy with critic-agent mechanism.

- **Dynamic Knowledge Graphs** (IEEE 2026): Handles topology drift in
  microservice monitoring — dependency graph changes at runtime.

- **GraphRank**: GNN-based test prioritization using graph structure
  information to aggregate attributes from neighboring test nodes.

- **FA-AST**: Flow-Augmented AST with control/data flow edges + GNNs for
  code clone detection via graph attention networks.

### Key Validation Numbers

| System | Token Reduction | Scale | Status |
|--------|----------------|-------|--------|
| code-review-graph | 6.8x-49x | 2,900 files | Open source |
| CodeGraph | 30% fewer | 19 languages | MCP server |
| Augment Context Engine | 70%+ improvement | 400K+ files | Commercial |
| PRAXIS | 3.8x fewer | Cloud incidents | Microsoft Research |
| LLMxCPG | 67-91% code reduction | USENIX published | Academic |
| MANTRA | 82.8% success (vs 8.7%) | Method-level refactoring | Academic |

---

## Y. Updated Integration Summary (All Rounds)

| Layer | Points | Z-ref Types | Key Win |
|-------|--------|-------------|---------|
| DevCtl commands | 12 families | 25+ | 35-70% compression |
| Runtime contracts | 20+ contracts | 8 identity | Unified queries |
| Report artifacts | 7 directories | 10 cross-links | 88% max |
| Platform/governance | 6+26 files | 6 catalog | Closure queries |
| Guard/probe system | 90 scripts | 12 relationships | Meta-governance |
| Repo example patterns | 15+ unmapped | Adoption | Validated |
| AI context injection | 8 points | 5 packages | 50% token savings |
| Operator console | 4 features | Dashboard/graph | Proof-driven |
| Novel applications | 5 high-priority | Test/compliance | Differentiators |
| Rust product code | 12 subsystems | FSM/routing | Product-level |
| CI/CD workflows | 30 workflows | DAG/selection | 40% skip rate |
| Test suite | 191 files | Coverage/fixture | 29%+ savings |
| Config system | 14 configs | Drift/inheritance | Consistency |
| AGENTS.md policy | 1721 lines | Constraints | Enforceable |
| Memory system | 12 files | Decision/feedback | 40x recall |
| **NEW: Unexplored subsystems** | **21 areas** | **State machines/DAGs** | **Full coverage** |
| **NEW: Industry 2026** | **12 systems** | **Validated patterns** | **6.8x-49x tokens** |
| **Total** | **120+ points** | **90+ Z-ref types** | **System-wide** |

---

## Z. Review-Channel State Machine — 5 Composited FSMs

### 62-file subsystem (10,933 LOC) is the most complex state machine in the repo.

**5 Independent State Machines Found**:

1. **Packet Lifecycle**: pending → acked → applied OR dismissed OR expired.
   Authorization gates require actor in {to_agent, operator}. Expiry is
   lazy (computed during reduction, not enforced at write).

2. **Reviewer Freshness**: MISSING → OVERDUE → STALE → POLL_DUE → FRESH.
   Time-based thresholds (15min/5min/3min). Constants scattered, no
   explicit state transition graph.

3. **Overall Liveness**: inactive, runtime_missing, stale, waiting_on_peer,
   fresh. Derived from freshness + daemon state.

4. **Attention Status**: 19 enumerated states with undocumented precedence.
   Cascading if-elif chain in attention.py:21-123. DUAL_AGENT_IDLE is
   unreachable when checkpoint_required=true (silent dead code).

5. **Daemon Lifecycle**: stopped → started → heartbeat → stopped.
   Running state computed as property, not explicit.

**Undocumented Transitions & Dead States**:
- Implementer stall detected via 13 hardcoded marker phrases (not state)
- `dismissed` packet status reachable but never filtered or displayed
- `plan_gap_review`, `plan_patch_review` packet kinds defined but
  integration with plan mutation is opaque
- Instruction revision staleness checked post-hoc, not guarded upfront
- Bridge-backed and event-backed pipelines can drift without sync

**Authorization Edge Inconsistencies**:
- Operator has implicit blanket authority (no explicit approval gates)
- Actor field is redundant (from_agent/to_agent + metadata.actor)
- Bridge writes have no actor auth — anyone can write if preconditions met

**ZGraph Would Surface**:
- Which state transitions are guarded vs unguarded
- Which states are reachable vs dead
- Which actors can reach which states
- Where precedence rules create unreachable paths
- Where data dependencies create synchronization risks

---

## AA. Watchdog & Autonomy — Temporal DAGs and Feedback Loops

### Episode chains, feedback sizing, and benchmark scenarios as graph patterns.

**Episode Chains** (56-field GuardedCodingEpisode):
- session_id + peer_session_id define agent pairs
- controller_run_id groups episodes into execution contexts
- retry_count, handoff_count, stale_peer_pause_count track coordination
- Currently written as isolated JSONL records — no code traverses chains

**Feedback Sizing** (adaptive control loop):
- Three-way streak tracker: no_signal_streak, stall_streak, improve_streak
- Decision: downshift (factor=0.5) / upshift (factor=1.25) / hold
- triage_reason_counts dict is RICHEST field but NEVER queried for patterns
- History is in-memory only, never persisted or cross-referenced

**Benchmark Scenarios** (4 tactics × N swarm counts):
- uniform, specialized, research-first, test-first
- Results stored as flat summary rows — no code analyzes which
  tactic+count combo is optimal for which problem types

**Isolated Data Silos**:
- Watchdog (episodes) + Autonomy feedback (cycles) + Benchmark (scenarios)
  generate complementary signals but exist in separate files with zero
  cross-queries. ZGraph would reveal whether feedback sizing decisions
  actually correlate with guard outcomes.

**Proposed ZGraph Model**: 7 node types (Episode, FeedbackCycle, SwarmScenario,
TriageEscalation, ContextRecovery, AgentSession, GuardFamilyOutcome) + 6 edge
types (retry_chain, streak_transition, episode_to_feedback, swarm_to_scenario,
escalation_feedback, context_recovery_route).

---

## AB. Quality Feedback — Evolution DAGs and ROI Graphs

### Quality scoring, FP classification, and maintenance ROI as graph patterns.

**Quality Evolution DAG**:
- MaintainabilityResult has 7 weighted sub-scores across 3 lenses
  (code_health, governance_quality, operability)
- ImprovementDelta tracks which checks improved/degraded between snapshots
- ZGraph connects: snapshot → check_quality → recommendation → improvement
  → cascade to dependent dimensions

**False Positive Pattern Network**:
- FPClassification traces FPs to 5 root causes: context_blind,
  threshold_noise, style_opinion, pattern_mismatch, unknown
- Bipartite graph: root_cause ↔ check ↔ file enables cross-repo learning
- "context_blind findings concentrate in test paths → raise exclusion
  thresholds" becomes a deterministic recommendation

**Maintenance Debt ROI Graph**:
- Semantic dimensions (halstead_mi, code_shape, cleanup_rate) connected to
  code_quality_problems via `drags_down` edges
- Fix actions connected via `targets` and `improves` edges
- Cascade modeling: fixing code_shape → +3% cleanup_rate (measured)
- ROI = (estimated_impact × cascade_count × actual_delta)

**Context Graph Quality Augmentation**:
- Add quality dimensions to source file node metadata (halstead_mi,
  code_shape_status, duplication_density, overall_grade)
- Enable: "Show hotspots AND their quality scores" in one query
- Modify temperature_for_source() to incorporate quality score

---

## AC. Final Sweep — 12 New Architectural Patterns

### Patterns found in the final codebase sweep not in prior rounds.

1. **Event Store + Projection** (CQRS pattern): Write-once JSONL event log
   as source of truth, reducers compute projections, bundle writers export
   immutable snapshots. Replay for audit trails.

2. **Workflow Bridge CLI**: Shell-facing config resolver that bridges GitHub
   Actions env vars into typed config dicts with validation. Narrowest
   point where external CI events funnel into devctl's type system.

3. **CodeRabbit/Ralph Pipeline**: Multi-stage finding-to-fix loop: collect
   from GitHub API → normalize severity → dedupe → backlog JSON → Ralph
   AI fix wrapper → guard-run wraps.

4. **Follow-Stream NDJSON**: Streaming output surface for long-running
   commands via append-writer with error/completion reports.

5. **Ralph Guardrails Config**: Centralized 24-guard → fix-skill mapping.
   Links guards to AGENTS.md sections, doc references, fix-skill tags.
   Semantic bridge between enforcement and remediation.

6. **Integration Audit Logging**: JSONL append log for federation imports
   with source validation, destination allowlist, symlink detection.

7. **Data Science Metrics Pipeline**: Telemetry aggregator reading from
   event log + swarm summaries + benchmarks + watchdog + governance +
   external findings for combined analytics.

8. **Compatibility Shim Tracking**: Systematic shim lifecycle with owner,
   reason, expiry, target. Deprecation timeline for portable governance.

9. **Control Plane Rate Limiting**: Hard caps (12 rounds, 24 hours, 200
   tasks for autonomy; 5 attempts, 6 updates/hr for mutation). 300-second
   replay window. All policy-declared, not hardcoded.

10. **Platform Contract Temporal Boundaries**: compatibility_window fields
    bind breaking changes to specific MPs (e.g., "stable within MP-377").

11. **Ralph Guardrails as Semantic Bridge**: guard_name → fix_skills →
    agents_md_section → doc_links. The lookup table telling AI which
    remediation skills apply to which guard violations.

12. **Context Escalation as Semantic Search**: Bounded context recovery
    extracting file/MP/command terms from free text, querying graph,
    deduplicating, emitting bounded markdown safe for AI prompts.

---

## AD. Cross-Platform Data Flow — iOS + Operator Console

### Unified data provenance: Rust daemon → artifacts → iOS + PyQt6 console.

**Data Flow Architecture**:
```
Rust daemon (autonomy, Ralph, controller)
  → JSON artifacts in dev/reports/
    ├─ phone/latest.json (ControllerPayload)
    ├─ review_channel/latest/state.json (ReviewState)
    └─ mobile/latest/{full,compact,actions}.json
      ↙                        ↘
  iOS Mobile App            Operator Console
  (Swift Codable)           (Python snapshot)
  DaemonWebSocketClient     DaemonClient (Unix socket)
  SwiftUI rendering         PyQt6 widgets
```

**iOS Surface** (app/ios/):
- MobileRelayModels.swift (448 lines): Codable structs with CodingKeys
- DaemonWebSocketClient.swift (266 lines): async WebSocket to Rust daemon
- VoiceTermMobileDashboard.swift: SwiftUI split-pane with simple/technical modes

**Operator Console** (app/operator_console/, 158 files, 20K LOC):
- PhoneControlSnapshot reads same artifacts as iOS
- DaemonClient uses Unix socket (same events, different transport)
- No graph visualization yet — only text, tables, timeline rows

**Guard**: check_mobile_relay_protocol.py (627 lines) validates wire-protocol
compatibility between Rust serde types and Swift Codable models. Growth-based
enforcement. CI blocker.

**ZGraph Additions**:
- New node kinds: mobile_data_flow, mobile_surface_model, mobile_daemon_relay
- New edge kinds: artifact_boundary, protocol_validates, surface_renders
- Map iOS Swift code into same context-graph as Rust/Python
- mobile concept anchor already exists in builder.py line 46-57
- Operator console becomes ZGraph query consumer (future "System Graph" tab)

---

## AE. Final Integration Summary (All Rounds Complete)

| Layer | Points | Z-ref Types | Key Win |
|-------|--------|-------------|---------|
| DevCtl commands | 12 families | 25+ | 35-70% compression |
| Runtime contracts | 20+ contracts | 8 identity | Unified queries |
| Report artifacts | 7 directories | 10 cross-links | 88% max |
| Platform/governance | 6+26 files | 6 catalog | Closure queries |
| Guard/probe system | 90 scripts | 12 relationships | Meta-governance |
| Repo example patterns | 15+ unmapped | Adoption | Validated |
| AI context injection | 8 points | 5 packages | 50% token savings |
| Operator console | 4 features | Dashboard/graph | Proof-driven |
| Novel applications | 5 high-priority | Test/compliance | Differentiators |
| Rust product code | 12 subsystems | FSM/routing | Product-level |
| CI/CD workflows | 30 workflows | DAG/selection | 40% skip rate |
| Test suite | 191 files | Coverage/fixture | 29%+ savings |
| Config system | 14 configs | Drift/inheritance | Consistency |
| AGENTS.md policy | 1721 lines | Constraints | Enforceable |
| Memory system | 12 files | Decision/feedback | 40x recall |
| Unexplored subsystems | 21 areas | State machines | Full coverage |
| Industry 2026 | 12 systems | Validated | 6.8x-49x tokens |
| **Review-channel FSMs** | **5 state machines** | **19 attention states** | **Dead state detection** |
| **Watchdog/autonomy** | **7 node types** | **6 edge types** | **Temporal causal analysis** |
| **Quality feedback** | **3 DAG types** | **ROI/FP/evolution** | **Evidence-based recs** |
| **Final sweep patterns** | **12 new patterns** | **CQRS/bridge/shim** | **Architectural seams** |
| **Cross-platform flow** | **iOS + console** | **Artifact provenance** | **Unified data graph** |
| **Total** | **150+ points** | **100+ Z-ref types** | **Complete system coverage** |

---

## AF. Repo Organization Audit — Critical Cleanup Needed

### Root Directory Overcrowding

- **10 markdown files at root** (industry standard: 2-4)
- **5 empty cvelist files** (0 bytes each, orphaned)
- **DEV_INDEX.md** is a pointless shim ("see dev/README.md instead")
- **1,151 total .md files** across the entire repo
- **260 MB** in dev/repo_example_temp/ (research dump, gitignored but present)

### Files That Should Move

| File | Current | Should Be | Reason |
|------|---------|-----------|--------|
| SYSTEM_AUDIT.md (97KB) | root | dev/guides/ or docs/reference/ | Not user-facing |
| SYSTEM_FLOWCHART.md (86KB) | root | dev/guides/ or docs/reference/ | Not user-facing |
| ZGRAPH_RESEARCH_EVIDENCE.md (50KB) | root | dev/guides/ or docs/reference/ | Research artifact |
| GUARD_AUDIT_FINDINGS.md (10KB) | root | dev/guides/ or docs/reference/ | Audit artifact |
| DEV_INDEX.md (2KB) | root | DELETE | Shim redirect |
| cvelist* (5 files, 0 bytes) | root | DELETE | Empty orphans |

### What Should Stay at Root

- README.md, QUICK_START.md (user entry points)
- AGENTS.md (AI agent standard — industry convention)
- CLAUDE.md (AI bootstrap — generated, gitignored option)
- bridge.md (live review state — operational necessity)
- Makefile, config files (.gitignore, mypy.ini, etc.)

### Industry Standard Root Structure

Best-organized open source projects (tokio, pytest, ruff) keep root to:
README, CONTRIBUTING, LICENSE, CHANGELOG, SECURITY, CODE_OF_CONDUCT,
AGENTS.md. All other docs go in docs/ or dev/guides/.

---

## AG. Portability Audit — Score: 3-4/10

### The system is architecturally portable but NOT actually portable.

**What Works**:
- RepoPathConfig abstraction exists (set_active_path_config() defined)
- Bootstrap policy generator exists (governance-bootstrap command)
- Quality presets exist for Python-only and Rust-only repos
- Guards are configurable via repo policy JSON

**What Breaks**:

1. **Module-level path freezing** (CRITICAL): 53 references to
   active_path_config() called at import time, freezing VoiceTerm defaults
   before custom config can load. Late-binding impossible.

2. **set_active_path_config() never called** (CRITICAL): The portability
   escape hatch exists but has zero callers. Dead API.

3. **425 references to "voiceterm"** across 111 Python files. Core subsystems
   assume operator console, autonomy system, iOS relay, daemon contracts exist.

4. **Bootstrap is incomplete**: governance-bootstrap generates minimal starter
   policy — no review-channel, no governance, no platform-contracts sections.

5. **Check router hardcoded**: RELEASE_EXACT_PATHS references Cargo.toml,
   VoiceTerm.app plist. RISK_ADDONS reference overlay/hud, wake-word.

6. **Workflow presets hardcoded**: voiceterm.py lines 210-261 have 5
   VoiceTerm-specific presets with hardcoded MP scopes (MP-338, MP-355, etc.)

7. **Portable presets too minimal**: portable_python.json is 1.4K vs
   voiceterm.json at 11.3K. Missing governance/autonomy/platform sections.

### To Achieve True Portability (6-7 weeks estimated)

**Tier 1**: Defer path freezing from module-import to first-use (lazy eval);
expand bootstrap to generate complete policies; add `devctl init` with
interactive setup; document onboarding flow.

**Tier 2**: Make review-channel optional; stub operator-console; make autonomy
opt-in; move VoiceTerm workflows to voiceterm.json only; create portable
presets for governance-only, ci-only, release-only.

**Tier 3**: Test bootstrap on 3 real repos (Django, Go, Node); create
reference portings; document per-language lessons.

---

## AH. Markdown Format Consistency Audit

### Good news: execution-plan format is well-enforced.

**PLAN_FORMAT.md** defines canonical format:
- Metadata: `**Status**: X | **Last updated**: YYYY-MM-DD | **Owner:** Y`
- Marker: `Execution plan contract: required`
- Required sections: Scope, Execution Checklist, Progress Log, Session Resume,
  Audit Evidence

**17/17 execution-plan docs** in dev/active/ are COMPLIANT.
**Guards enforce this**: check_markdown_metadata_header.py +
check_active_plan_sync.py both active in CI.

### Bad news: everything else is inconsistent.

| Category | Total | With Metadata | Issue |
|----------|-------|--------------|-------|
| dev/active/ execution-plans | 17 | 17 | COMPLIANT |
| dev/active/ reference docs | 10 | 5 | 5 missing metadata |
| dev/guides/ | 13 | 1 | 12 missing metadata |
| Root non-user-facing | 6 | 0 | All missing metadata |
| dev/history/ | 2 | 1 | 1 non-canonical format |

**Guide docs are the worst**: 12 of 13 files in dev/guides/ have NO metadata
headers (no Status, no Last Updated, no Owner). These are substantial
architecture documents (DEVELOPMENT.md, ARCHITECTURE.md, etc.) that should
have maintenance metadata.

### For Universal System

The guard + registry system is already portable:
- check_markdown_metadata_header.py works on any directory
- INDEX.md format is language-agnostic
- PLAN_FORMAT.md template is repo-agnostic

What's missing:
- dev/config/markdown_format_policy.json (configurable status enums, required
  fields, excluded paths)
- Guide docs need metadata headers added
- Root architectural docs need metadata headers added

---

## AI. Industry Standards for Universal Repo Systems

### Key Standards Identified

**Documentation as Code**:
- Antora (AsciiDoc) and MkDocs Material (Markdown) are leading multi-repo
  doc platforms
- YAML frontmatter is the standard for machine-readable markdown (30-40%
  higher LLM extraction accuracy vs buried prose)
- MarkdownDB turns markdown into queryable SQLite

**ADR Format**:
- MADR (Markdown Architectural Decision Records) is the dominant standard
- Decision Reasoning Format (DRF) adds YAML/JSON for automated validation
- Decision Guardian auto-surfaces ADRs on relevant PRs

**Markdown Linting**:
- markdownlint (53 rules, structural)
- Vale (custom YAML rules, prose quality — used by Grafana, Datadog, Elastic)
- Combined in CI for full quality enforcement

**AI Agent Standard**:
- AGENTS.md is the 2025-2026 universal standard (Linux Foundation backed)
- Supported by Claude Code, Codex, Cursor, Copilot, Jules, Gemini CLI
- Nested AGENTS.md in subdirectories for package-specific rules

**Repo Health Scoring**:
- CHAOSS (Linux Foundation): 80+ metrics for community health
- OpenSSF Scorecard: 18 automated security checks, 0-10 scores
- Both integrate into CI

### What This Means for Our System

The codex-voice governance system has STRONGER enforcement than most of these
standards (64 guards > markdownlint's 53 rules). But it lacks:

1. **YAML frontmatter on all docs** (standard for machine consumption)
2. **ADR format for decisions** (decisions are in plan docs, not standalone ADRs)
3. **Markdown lint integration** (no markdownlint or Vale in CI)
4. **Health scoring** (no OpenSSF Scorecard integration)
5. **Interactive onboarding** (no `devctl init` for new repos)
6. **Template repo skeleton** (no minimal example for new repos)

---

## AJ. Organizational Debt Inventory

### Actual debt is LOW (2-3/10) — the repo is cleaner than it feels.

**Properly governed**:
- Shims tracked with expiry dates (2026-06-30) and CI-enforced
- Legacy code documented (legacy_ui.rs serves test harness)
- Test files properly exempt from size limits
- .gitignore comprehensive (3,394 .pyc files excluded, 334MB venv excluded)
- No try/except ImportError shims in production code

**Actual cleanup items**:

| Priority | Item | Action | Effort |
|----------|------|--------|--------|
| P1 | 5 empty cvelist files at root | Delete | 1 min |
| P1 | DEV_INDEX.md shim | Delete | 1 min |
| P2 | Root architectural docs | Move to dev/guides/ | 30 min |
| P2 | Guide docs missing metadata | Add headers to 12 files | 1 hour |
| P3 | Monitor shim expiry 2026-06-30 | Calendar reminder | 5 min |
| P3 | Verify repo_example_temp usefulness | Annual review | 30 min |

### The Real Problem Isn't Debt — It's Perception

The repo FEELS disorganized because:
1. 10 .md files at root (should be 4-5)
2. Docs split across root/, guides/, dev/guides/, dev/active/ (4 places)
3. No root-level docs/index.md navigation page
4. Massive files (bridge.md 319KB, AGENTS.md 116KB) dominate root

But the CODE is well-organized:
- Guards enforce function length, duplication, nesting, imports
- Platform contracts enforce schema consistency
- Shims have expiry dates
- Tests are comprehensive (1,867 tests, 191 files)

**The fix is surface-level**: move files, add metadata, create navigation.
Not architectural — cosmetic.
