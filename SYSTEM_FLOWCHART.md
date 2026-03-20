# VoiceTerm / AI Governance Platform — System Flowchart

> **Purpose**: Complete system map grounded in codebase audit (2026-03-19).
> All numbers are exact counts from the repo. Feed this to any AI agent for full context.

---

## 1. HIGH-LEVEL ARCHITECTURE (Current State)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        VOICETERM SYSTEM (codex-voice)                       │
│                                                                             │
│  Rust Binary          Python Tooling (devctl)       Surfaces                │
│  ~87K LOC             ~141K LOC                     ~20K LOC                │
│  rust/src/bin/        dev/scripts/devctl/           app/operator_console/   │
│  voiceterm/           65 commands                   app/ios/VoiceTermMobile/│
│                       22 subsystems                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Guards & Probes      CI/CD                         Plan Docs               │
│  64 hard guards       30 workflows                  25 active docs          │
│  27 review probes     .github/workflows/            dev/active/             │
│  dev/scripts/checks/                                                        │
│                                                                             │
│  Data Artifacts       Config                        Tests                   │
│  11 report dirs       4 quality presets             95 test files           │
│  dev/reports/         dev/config/                   dev/scripts/devctl/tests│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. BOOTSTRAP FLOW (How an AI Agent Enters the System)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         SESSION START                                     │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  1. Read CLAUDE.md            │  Generated from repo-pack policy
              │     (bootstrap instructions)  │  4 required steps
              └──────────────┬───────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  2. Read AGENTS.md            │  ~1300 lines
              │     (12-step SOP)             │  80% universal / 20% voiceterm
              │     (task router)             │  5 task classes
              │     (bundle definitions)      │  6 bundles
              └──────────────┬───────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  3. Read dev/active/INDEX.md  │  Plan registry table
              │     (role, authority, scope)  │  25 active plan docs
              └──────────────┬───────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  4. Read MASTER_PLAN.md       │  ~307KB canonical tracker
              │     (find task's MP scope)    │  All MP execution state
              └──────────────┬───────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  5. Determine Mode            │
              └──────┬───────────────┬───────┘
                     │               │
          ┌──────────▼──┐    ┌───────▼──────────┐
          │ Single Agent │    │ Dual Agent Mode   │
          │ / Tools Only │    │ (active_dual_     │
          │              │    │  agent)            │
          └──────┬───────┘    └───────┬────────────┘
                 │                    │
                 │                    ▼
                 │          ┌─────────────────────┐
                 │          │ Read code_audit.md   │
                 │          │ (live bridge)        │
                 │          │ Poll Status          │
                 │          │ Current Verdict      │
                 │          │ Open Findings        │
                 │          │ Current Instruction   │
                 │          └─────────┬─────────────┘
                 │                    │
                 └────────┬───────────┘
                          │
                          ▼
              ┌──────────────────────────────┐
              │  6. Classify Task             │
              │     (Task Router Table)       │
              ├──────────────────────────────┤
              │  runtime  → bundle.runtime    │
              │  docs     → bundle.docs       │
              │  tooling  → bundle.tooling    │
              │  release  → bundle.release    │
              │  bootstrap→ bundle.bootstrap  │
              └──────────────┬───────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  7. Load Context Pack         │
              │     (task-class-specific docs)│
              │     ARCHITECTURE.md           │
              │     DEVELOPMENT.md            │
              │     DEVCTL_AUTOGUIDE.md       │
              │     (conditionally loaded)    │
              └──────────────┬───────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  8. EXECUTE (12-step SOP)     │
              │     Implement → Test →        │
              │     Run Bundle → Risk Addons →│
              │     Self-Review → Push →      │
              │     Handoff                   │
              └──────────────────────────────┘
```

---

## 3. GUARD & GOVERNANCE PIPELINE (The "Box Around AI")

```
                         ┌──────────────────────┐
                         │   AI Agent Edits Code │
                         └──────────┬───────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                     LAYER 1: HARD GUARDS (64 checks)                      │
│                     Deterministic — blocks merge on violation              │
│                                                                           │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌──────────────────┐  │
│  │ Code Shape (11)      │  │ Python Analysis (15) │  │ Rust Analysis(12)│  │
│  │ • function length    │  │ • broad_except       │  │ • best_practices │  │
│  │ • file size          │  │ • cyclic_imports     │  │ • panic_policy   │  │
│  │ • duplication        │  │ • global_mutable     │  │ • security       │  │
│  │ • nesting_depth      │  │ • subprocess_policy  │  │ • serde_compat   │  │
│  │ • god_class          │  │ • design_complexity  │  │ • lint_debt      │  │
│  │ • parameter_count    │  │ • dict_schema        │  │ • test_shape     │  │
│  │ • structural_sim     │  │ • suppression_debt   │  │ • clippy_signal  │  │
│  └─────────────────────┘  └─────────────────────┘  └──────────────────┘  │
│                                                                           │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌──────────────────┐  │
│  │ Governance (10)      │  │ Architecture (8)     │  │ Platform (8)     │  │
│  │ • agents_contract    │  │ • boundary           │  │ • contract_close │  │
│  │ • active_plan_sync   │  │ • package_layout     │  │ • layer_boundary │  │
│  │ • instruction_sync   │  │ • ide_provider_iso   │  │ • tandem_consist │  │
│  │ • multi_agent_sync   │  │ • release_version    │  │ • daemon_state   │  │
│  │ • governance_closure │  │ • cli_flags_parity   │  │ • mobile_relay   │  │
│  └─────────────────────┘  └─────────────────────┘  └──────────────────┘  │
│                                                                           │
│  Portability: 37 PORTABLE | 30 CONFIGURABLE (via JSON) | 16 COUPLED      │
│  Registration: script_catalog.py (hardcoded tuples) → bundle_registry.py  │
│  Policy: dev/config/quality_presets/*.json (4 presets)                     │
│  Router: check_router.py classifies lane → selects bundle → runs guards   │
└───────────────────────────────┬───────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                     LAYER 2: REVIEW PROBES (27 probes)                    │
│                     Advisory — soft hints, always exit 0                   │
│                                                                           │
│  concurrency        design_smells      boolean_params     stringly_typed  │
│  unwrap_chains      clone_density      type_conversions   magic_numbers   │
│  dict_as_struct     unnecessary_intermediates             vague_errors    │
│  defensive_overchecking   single_use_helpers              cognitive_cplx  │
│  ... and 13 more                                                          │
│                                                                           │
│  Runner: python3 dev/scripts/checks/run_probe_report.py --format md       │
│  Output: RiskHint with severity + ai_instruction                          │
│  Portability: 100% PORTABLE (language-level analysis, no repo coupling)   │
└───────────────────────────────┬───────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                     LAYER 3: GOVERNANCE (Persistence + Learning)           │
│                                                                           │
│  ┌──────────────────────────────┐  ┌─────────────────────────────────┐   │
│  │ Finding Ledger (JSONL)        │  │ Quality Feedback Snapshot (JSON) │   │
│  │ finding_reviews.jsonl         │  │ quality_feedback_snapshot.json   │   │
│  │ external_pilot_findings.jsonl │  │ QualityFeedbackSnapshot:        │   │
│  │ Append-only, dedup by ID     │  │  • MaintainabilityResult        │   │
│  │ 5000-row bounded reads       │  │  • HalsteadSummary              │   │
│  └──────────────────────────────┘  │  • FPAnalysis                   │   │
│                                     │  • CheckQualityScore[]          │   │
│  ┌──────────────────────────────┐  │  • ImprovementDelta             │   │
│  │ Finding Identity              │  └─────────────────────────────────┘   │
│  │ identity.py: SHA1 hash from   │                                        │
│  │  repo_name + repo_path +      │  ┌─────────────────────────────────┐   │
│  │  check_id + file_path +       │  │ Governance Review Models         │   │
│  │  symbol → stable finding_id   │  │ GovernanceReviewInput (11 flds)  │   │
│  └──────────────────────────────┘  │ FindingRecord (21+ flds, v1)     │   │
│                                     │ DecisionPacketRecord             │   │
│  Data flow:                         └─────────────────────────────────┘   │
│  Guard/Probe output → FindingRecord → JSONL ledger → QualityFeedback      │
│  → ImprovementDelta → proves quality trend over time                      │
└───────────────────────────────┬───────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                     LAYER 4: CI ORCHESTRATION (30 workflows)              │
│                                                                           │
│  rust_ci.yml              coverage.yml            perf_smoke.yml          │
│  pre_commit.yml           docs_lint.yml           latency_guard.yml       │
│  memory_guard.yml         parser_fuzz_guard.yml   voice_mode_guard.yml    │
│  wake_word_guard.yml      tooling_control_plane.yml                       │
│  orchestrator_watchdog.yml publish_pypi.yml       publish_homebrew.yml    │
│  publish_release_binaries.yml release_preflight.yml                       │
│  ... and 13 more                                                          │
│                                                                           │
│  All route through: python3 dev/scripts/devctl.py <command>               │
│  Bundle execution: check --profile ci | check --profile quick             │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 4. REVIEW CHANNEL (Multi-Agent Coordination)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                     REVIEW CHANNEL SYSTEM (54 files)                      │
│                     dev/scripts/devctl/review_channel/                     │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ BRIDGE (code_audit.md)                                             │   │
│  │ Human-readable markdown at repo root                               │   │
│  │ Sections: Poll Status | Current Verdict | Open Findings |          │   │
│  │           Current Instruction | Last Reviewed Scope                 │   │
│  │ Written by: Reviewer (Codex/Claude/Human)                          │   │
│  │ Read by: Coder agent + Operator Console                            │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────┐     │
│  │ State Hub        │  │ Event Sourcing   │  │ Peer Liveness        │     │
│  │ state.py         │  │ event_reducer.py │  │ peer_liveness.py     │     │
│  │ Reconciles       │  │ JSONL → snapshot │  │ AttentionStatus enum │     │
│  │ bridge + events  │  │ event_store.py   │  │ ReviewerMode enum    │     │
│  │ into unified     │  │ Append-only      │  │ Freshness classify   │     │
│  │ ReviewState      │  │ trace logs       │  │                      │     │
│  └─────────────────┘  └─────────────────┘  └──────────────────────┘     │
│                                                                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────┐     │
│  │ Follow Loop      │  │ Heartbeat        │  │ Promotion            │     │
│  │ follow_loop.py   │  │ heartbeat.py     │  │ promotion.py         │     │
│  │ follow_          │  │ Worktree hash    │  │ plan_resolution.py   │     │
│  │  controller.py   │  │ Reviewer alive?  │  │ What's next to       │     │
│  │ Event subscribe  │  │ Stale detection  │  │ promote?             │     │
│  └─────────────────┘  └─────────────────┘  └──────────────────────┘     │
│                                                                           │
│  Reviewer Modes: active_dual_agent | single_agent | tools_only |          │
│                  paused | offline                                          │
│                                                                           │
│  Actions: launch | status | ensure | wait | rollover | attach |           │
│           reviewer-heartbeat | reviewer-checkpoint | reviewer-follow       │
│                                                                           │
│  Portability: 48/54 files PORTABLE (89%)                                  │
│  Coupling: 5 files use active_path_config() (10 LOC total)               │
│  Fix: Accept RepoPathConfig as parameter instead of frozen defaults       │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 5. AUTONOMY & AI REMEDIATION LOOP

```
┌───────────────────────────────────────────────────────────────────────────┐
│                     AUTONOMY SYSTEM                                        │
│                                                                           │
│  ┌──────────────────────────────┐   ┌──────────────────────────────────┐ │
│  │ autonomy-loop (single)       │   │ autonomy-swarm (parallel)        │ │
│  │ One agent, one MP            │   │ Multiple agents, fan-out         │ │
│  │ triage → fix → verify        │   │ Adaptive sizing:                 │ │
│  │                               │   │  stall → downshift agents       │ │
│  │ guard-run wraps all fixes:    │   │  improve → upshift agents       │ │
│  │  git diff → hygiene →        │   │                                  │ │
│  │  watchdog episode             │   │ swarm_run (continuous mode)      │ │
│  └──────────────────────────────┘   └──────────────────────────────────┘ │
│                                                                           │
│  ┌──────────────────────────────┐   ┌──────────────────────────────────┐ │
│  │ Triage                        │   │ Watchdog                         │ │
│  │ triage/support.py             │   │ watchdog/episode.py              │ │
│  │ Risk classification           │   │ GuardedCodingEpisode (36 flds)  │ │
│  │ Finding → priority → assign   │   │ Times, retries, diffs, verdicts │ │
│  │ Approval modes                │   │ Telemetry collection             │ │
│  └──────────────────────────────┘   └──────────────────────────────────┘ │
│                                                                           │
│  Ralph Loop (AI-driven remediation):                                      │
│  CodeRabbit finding → triage → agent fix → guard-run verify → commit      │
│                                                                           │
│  Mutation Testing:                                                        │
│  mutants | mutation-score | mutation-loop                                  │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 6. DATA FLOW & PERSISTENCE

```
┌───────────────────────────────────────────────────────────────────────────┐
│                     INGESTION (Any Repo)                                   │
│                                                                           │
│  Source Code ──────→ AST Scanning ──────→ Guard/Probe Findings            │
│  Plan Docs ────────→ Markdown Parse ────→ MP Scope Resolution             │
│  Config (JSON) ────→ Policy Resolve ────→ Quality Policy                  │
│  External Tools ───→ Import Findings ───→ External Finding Ledger         │
│                                                                           │
│  Current formats:                                                         │
│  • JSONL (append-only ledgers): governance findings, events, episodes     │
│  • JSON (point-in-time snapshots): quality feedback, review state, status │
│  • Markdown (human-readable): plans, bridge, audit trails                 │
│  • Python dataclasses (in-memory contracts): 16+ model families           │
└───────────────────────────────┬───────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                     PERSISTENCE (dev/reports/)                             │
│                                                                           │
│  dev/reports/                                                             │
│  ├── governance/                                                          │
│  │   ├── finding_reviews.jsonl          (governance ledger)               │
│  │   ├── external_pilot_findings.jsonl  (external findings)               │
│  │   ├── quality_feedback_latest/       (snapshot JSON + markdown)         │
│  │   └── latest/                        (summary renders)                 │
│  ├── review_channel/                                                      │
│  │   ├── events/trace.ndjson            (event sourcing log)              │
│  │   ├── state/latest.json              (review state snapshot)           │
│  │   └── operator_decisions/            (operator approvals)              │
│  ├── autonomy/                                                            │
│  │   └── runs/*/summary.json            (swarm run summaries)             │
│  ├── probes/                            (probe report artifacts)          │
│  ├── check/                             (guard run artifacts)             │
│  ├── audits/                            (devctl event log)                │
│  ├── clippy/                            (Rust lint output)                │
│  ├── data_science/                      (metrics, analysis)               │
│  ├── duplication/                       (duplication reports)             │
│  └── research/                          (agent research output)           │
└───────────────────────────────┬───────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                     AGGREGATION & PROJECTION                              │
│                                                                           │
│  JSONL ledger rows                                                        │
│    → latest_rows_by_finding() deduplication                               │
│    → build_governance_review_stats() → GovernanceReviewStats              │
│    → build_quality_feedback_report() → QualityFeedbackSnapshot            │
│       • MaintainabilityResult (7 sub-scores)                              │
│       • HalsteadSummary (per-language metrics)                            │
│       • FPAnalysis (false-positive classification)                        │
│       • ImprovementDelta (vs previous snapshot)                           │
│       • Recommendation[] (AI tuning suggestions)                          │
│    → 120s TTL in-process cache (threading.Lock)                           │
│                                                                           │
│  Review channel events                                                    │
│    → event_reducer.py → ReviewStateSnapshot                               │
│    → status_projection.py → StatusProjectionPayload                       │
│    → projection_bundle.py → bundled JSON + markdown                       │
└───────────────────────────────┬───────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                     SURFACES (Read Artifacts, Shell to devctl)             │
│                                                                           │
│  ┌──────────────────────┐  ┌──────────────────┐  ┌────────────────────┐  │
│  │ Operator Console      │  │ Mobile App        │  │ CLI (devctl)       │  │
│  │ PyQt6 desktop         │  │ SwiftUI iOS       │  │ 65 commands        │  │
│  │ 161 Python files      │  │ JSON decode only  │  │ --format md|json   │  │
│  │ Reads: code_audit.md, │  │ Reads: full.json  │  │ Terminal output    │  │
│  │  review_state.json,   │  │  (mobile bundle)  │  │                    │  │
│  │  quality snapshots    │  │                    │  │ Key commands:      │  │
│  │ Executes: devctl cmds │  │ Same artifact     │  │  check --profile   │  │
│  │ Never bypasses devctl │  │  contract as       │  │  probe-report      │  │
│  │                        │  │  desktop           │  │  review-channel    │  │
│  └──────────────────────┘  └──────────────────┘  │  status             │  │
│                                                    │  triage             │  │
│                                                    │  autonomy-loop      │  │
│                                                    └────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 7. CONFIGURATION HIERARCHY

```
┌───────────────────────────────────────────────────────────────────────────┐
│                     CONFIGURATION STACK                                    │
│                                                                           │
│  dev/config/devctl_repo_policy.json          ← Repo-level switchboard     │
│  │  schema_version: 1                                                     │
│  │  repo_name, capabilities (python/rust)                                 │
│  │  repo_governance:                                                      │
│  │    check_router: bundle_by_lane, runtime_prefixes, risk_addons         │
│  │    docs_check: user_docs_list, tooling_change_triggers                 │
│  │    surface_generation: repo_pack_metadata, bootstrap_steps             │
│  │                                                                        │
│  └──→ dev/config/quality_presets/                                         │
│       ├── voiceterm.json          ← Extends portable + adds 8 AI guards   │
│       ├── portable_python_rust.json  ← Inherits both below                │
│       ├── portable_python.json    ← 15 guards + 16 probes (generic)       │
│       └── portable_rust.json      ← 16 guards + 14 probes (generic)      │
│                                                                           │
│  Resolution chain:                                                        │
│  quality_policy_defaults.py                                               │
│    → 35 DEFAULT_AI_GUARD_SPECS (all guards with metadata)                 │
│    → 29 DEFAULT_ENABLED (excludes 6 voiceterm-only IDs)                   │
│    → Preset JSON overrides enabled list                                   │
│    → Repo policy overrides preset                                         │
│                                                                           │
│  Path resolution:                                                         │
│  repo_packs/voiceterm.py                                                  │
│    → RepoPathConfig (37 fields, frozen dataclass)                         │
│    → VOICETERM_PATH_CONFIG singleton                                      │
│    → active_path_config() returns it (51 call sites across codebase)      │
│    → set_active_path_config() exists but rarely used                      │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 8. DEVCTL SUBSYSTEM MAP (22 Subsystems, 65 Commands)

```
dev/scripts/devctl/
├── cli.py                  ← Entry point (65 commands in COMMAND_HANDLERS)
├── common.py               ← Command runner, live output, failure aggregation
├── common_io.py            ← I/O, subprocess, JSON, path handling
├── config.py               ← Repo root resolution (runtime override support)
├── bundle_registry.py      ← 6 bundles (bootstrap, runtime, docs, tooling, release, post-push)
├── script_catalog.py       ← Guard/probe registration (hardcoded tuples)
├── quality_policy_defaults.py  ← Default guard/probe specs
│
├── commands/               ← 65 command implementations
│   ├── check_router.py     ← Lane classification → bundle selection
│   ├── governance/         ← bootstrap, export, import-findings, quality-feedback, review
│   ├── review_channel/     ← launch, status, ensure, wait actions
│   ├── review_channel_bridge_*.py  ← Bridge handlers (4 files)
│   ├── review_channel_command/     ← Constants, helpers, models, reviewer support
│   ├── listing.py          ← devctl list
│   └── mobile_status.py    ← Phone/mobile status
│
├── review_channel/         ← 54 files: event sourcing, state, coordination
├── governance/             ← 14 files: findings, identity, quality feedback, ledgers
├── platform/               ← 15 files: contracts, definitions, blueprints, renders
├── runtime/                ← 12 files: action/finding/control contracts, review state
├── autonomy/               ← Agent loops, swarm, benchmark, feedback sizing
├── triage/                 ← Risk classification, approval modes
├── watchdog/               ← Episode tracking, metrics, telemetry
├── data_science/           ← Source rows, metrics analysis
├── loops/                  ← Packet parsing for loop coordination
├── repo_packs/             ← Path config (VOICETERM_PATH_CONFIG singleton)
├── mutation_loop/          ← Mutation testing orchestration
├── probe_report/           ← Probe report rendering
├── process_sweep/          ← Process cleanup
├── publication_sync/       ← Release publication sync
├── integrations/           ← External tool integrations
├── security/               ← Security scanning
├── rust_audit/             ← Rust-specific audit patterns
├── path_audit_support/     ← Path audit helpers
├── quality_backlog/        ← Quality backlog tracking
├── cli_parser/             ← CLI argument parsing helpers
└── tests/                  ← 95 test files
```

---

## 9. PORTABILITY ASSESSMENT (Current State)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                     WHAT'S PORTABLE TODAY                                  │
│                                                                           │
│  PORTABLE (works on any repo, zero changes):                              │
│  ├── 37/64 hard guards (58%)                                              │
│  ├── 27/27 review probes (100%)                                           │
│  ├── 48/54 review channel files (89%)                                     │
│  ├── Core utilities: jsonl_support, ledger_helpers, identity.py           │
│  ├── Quality feedback: halstead metrics, FP classifier, models            │
│  ├── Service identity: git-based, repo-agnostic                           │
│  └── Bootstrap: 80% of AGENTS.md is universal process                     │
│                                                                           │
│  CONFIGURABLE (needs JSON config, no code changes):                       │
│  ├── 30/64 guards (via quality_presets/*.json)                            │
│  ├── Bundle routing (via devctl_repo_policy.json)                         │
│  ├── Scope resolution (TARGET_ROOTS from config)                          │
│  └── Docs check rules (user_docs_list from policy)                        │
│                                                                           │
│  COUPLED (voiceterm-specific, needs extraction):                          │
│  ├── 16/64 guards (mobile_relay, cli_flags, IDE provider, etc.)           │
│  ├── 51 active_path_config() call sites                                   │
│  ├── RepoPathConfig frozen to VOICETERM_PATH_CONFIG                       │
│  ├── Review channel provider names (Codex/Claude hardcoded)               │
│  ├── Operator console (161 files, bridge format coupling)                 │
│  ├── Memory system (.voiceterm/ paths, embedded in Rust binary)           │
│  └── Session scripts (provider-specific launch templates)                 │
│                                                                           │
│  OVERALL: ~85% portable in logic, ~15% coupled at boundaries              │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 10. PROPOSED EXTRACTION: PLATFORM AUTHORITY LOOP

```
The closed loop that must work end-to-end before anything else:

┌──────────────────┐
│ ProjectGovernance │  project.governance.md + .json
│ (Startup Auth)    │  Declares: repo identity, repo-pack id, path roots,
│                    │  tracker, plan registry, workflow profiles,
│                    │  artifact roots, memory roots, bridge mode,
│                    │  guard/probe enablement, bundle overrides
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ RepoPack          │  Loaded at runtime (not frozen singleton)
│ (Path Authority)  │  RepoPathConfig with 37+ fields
│                    │  Callers receive RepoPack/RepoPathConfig explicitly
│                    │  VoiceTerm pack is ONE implementation
│                    │  Artifact/memory roots replace .voiceterm literals
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ PlanRegistry      │  Typed, not prose-scraped
│ (Execution Auth)  │  Multiple active plans/scopes
│                    │  Machine-readable artifacts alongside markdown
│                    │  INDEX.md stays human-facing
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ TypedAction       │  Schema-versioned action contracts
│ (Runtime Contract)│  ActionResult / RunRecord
│                    │  Guard execution through typed pipeline
│                    │  Provider-specific inference lives in adapters
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Finding / Evidence│  Unified schema: guard + probe + external
│ (Evidence Contract)  finding_id (deterministic hash)
│                    │  schema_version, contract_id, provenance
│                    │  One ledger format for all finding types
│                    │  Cost telemetry: model_id, token_count,
│                    │  context_budget, cost_usd when available
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ ContextPack       │  Portable, schema-versioned
│ (Context Contract)│  id, version, repo identity
│                    │  Memory as provider/store behind contract
│                    │  Not .voiceterm/ convention
└────────┬─────────┘
         │
         └──────────→ feeds back into ProjectGovernance (loop closes)


Extraction Phases (execution order: 0 → 1 → [2, 3, 5a] → 4 → 5b → 6 → 7 → 8):

  Phase 0:  Scope freeze, contract freeze, monorepo-first decision
  Phase 1:  Startup authority (project.governance.md/json + guard)
  ┌─── run in parallel after Phase 1 ───────────────────────────┐
  │ Phase 2:  RepoPack runtime (compatibility-first rollout,     │
  │           51 call sites + ~15 .voiceterm roots + MP-359      │
  │           console migration as dependency)                    │
  │ Phase 3:  Typed plan registry (stop prose scraping)          │
  │ Phase 5a: Evidence identity freeze (backfill 107 legacy rows,│
  │           unify finding_id scheme, compatibility window)      │
  └─── Phase 5a must complete before Phase 4 ───────────────────┘
  Phase 4:  Runtime closure (one slice: TypedAction → ActionResult;
            provider inference → adapters; _compat removal)
  Phase 5b: Provenance/ledger closure (versioned contracts,
            quality-to-cost telemetry, ledger integrity rules)
  Phase 6:  Context contract (portable ContextPack)
  Phase 7:  Cross-repo proof (2 repos, no core patches;
            portable guards pass, repo-structure guards optional)
  Phase 8:  Deferred (plugins, multi-reviewer, language packs)

TACTICAL PRECISIONS NOW EXPLICIT IN THE PLAN:
  • Phase 2 staged compatibility-first: get_repo_pack() coexists with old defaults
  • Phase 2 owns all 51 active_path_config() rewrites plus ~15 .voiceterm roots
  • Phase 2 requires MP-359 (operator console) snapshot/logging migration
  • RepoPack migration uses explicit DI: callers receive RepoPack/RepoPathConfig
  • Guard/probe enablement and bundle overrides become config-driven first
  • Provider-specific review inference moves behind the adapter layer
  • Phase 5a backfills 107 legacy governance-review rows before schema enforcement
  • Provenance now includes quality-to-cost telemetry where available
  • Authority-loop closure guards require direct test coverage
  • Phase 7 distinguishes portable guards from VoiceTerm repo-structure guards
```

---

## 11. KEY NUMBERS SUMMARY

| Metric | Count | Location |
|--------|-------|----------|
| Rust LOC | ~87,000 | `rust/src/bin/voiceterm/` |
| Python LOC (devctl) | ~141,000 | `dev/scripts/devctl/` |
| Python LOC (checks) | ~49,000 | `dev/scripts/checks/` |
| Python LOC (console) | ~20,000 | `app/operator_console/` |
| devctl commands | 65 | `cli.py COMMAND_HANDLERS` |
| Hard guards | 64 | `dev/scripts/checks/check_*.py` |
| Review probes | 27 | `dev/scripts/checks/probe_*.py` |
| CI workflows | 30 | `.github/workflows/*.yml` |
| Active plan docs | 25 | `dev/active/*.md` |
| devctl subsystems | 22 | `dev/scripts/devctl/*/` |
| Review channel files | 54 | `dev/scripts/devctl/review_channel/` |
| RepoPathConfig fields | 37 | `repo_packs/voiceterm.py` |
| active_path_config() calls | 51 | Across all devctl modules |
| Quality presets | 4 | `dev/config/quality_presets/` |
| Report artifact dirs | 11 | `dev/reports/` |
| Test files | 95 | `dev/scripts/devctl/tests/` |
| Operator console files | 161 | `app/operator_console/` |
| Portable guards | 37 (58%) | No config needed |
| Configurable guards | 30 (47%) | JSON config needed |
| Coupled guards | 16 (25%) | VoiceTerm-specific |
| Portable review-channel | 48/54 (89%) | 5 files need path params |

---

## 12. DEFINITION OF DONE (For Universal Portability)

```
The system is "truly portable" when ALL of these are true:

  [ ] A repo boots from project.governance.md/json (not CLAUDE.md copy-paste)
  [ ] A real repo-pack loads without VoiceTerm fallback
  [ ] Plans resolve from typed registry, not prose scraping
  [ ] One runtime slice executes through typed contracts end-to-end
  [ ] One unified finding/evidence identity exists across guard+probe+external
  [ ] One schema-versioned context pack exists
  [ ] A second repo works without patching any core engine code
  [ ] Guards are discoverable via config (not hardcoded tuples)
  [ ] Bundles are customizable per-repo (not hardcoded registry)
  [ ] Finding provenance traces back to guard version + policy + run context
  [ ] Provider-specific runtime naming exists only in adapters
  [ ] .voiceterm path roots are replaced by repo-pack-declared roots
  [ ] Evidence captures model_id/token_count/context_budget/cost_usd when available
  [ ] Authority-loop guards/checks have direct test coverage
  [ ] Legacy governance-review ledger backfilled with schema_version
  [ ] Operator console (MP-359) migrated off VOICETERM_PATH_CONFIG
  [ ] Phase 7 proof distinguishes portable guards from repo-structure guards
```

---

## 13. TARGET STATE: After Full Extraction (What the System Becomes)

### 13a. Package Architecture (Lego Pieces)

```
Each package works ALONE or TOGETHER. VoiceTerm is just one consumer.

┌───────────────────────────────────────────────────────────────────────────┐
│                     INDEPENDENT PACKAGES (pip install)                     │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  codex-governance-core                                              │  │
│  │  The engine. Works on any repo. Zero product coupling.              │  │
│  │                                                                     │  │
│  │  Contains:                                                          │  │
│  │  ├── Guards (64+ portable hard checks)                              │  │
│  │  ├── Probes (27+ advisory review probes)                            │  │
│  │  ├── Guard plugin registry (config-driven discovery, not tuples)    │  │
│  │  ├── Quality policy engine (presets, defaults, resolution)          │  │
│  │  ├── Bundle engine (customizable per-repo, not hardcoded)           │  │
│  │  ├── Check router (lane classify → bundle select → execute)         │  │
│  │  ├── Finding contracts (unified schema, versioned, provenance)      │  │
│  │  ├── Evidence ledger (JSONL append, dedup, bounded reads)           │  │
│  │  ├── Identity system (deterministic finding_id, repo-agnostic)      │  │
│  │  ├── Quality feedback (Halstead, FP classifier, maintainability)    │  │
│  │  └── Governance commands (bootstrap, export, review, import)        │  │
│  │                                                                     │  │
│  │  Entry point: codex-governance check --profile ci                   │  │
│  │  Config: project.governance.json (repo-level, schema-validated)     │  │
│  │  Presets: portable_python.json | portable_rust.json | custom        │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  codex-review-channel                                               │  │
│  │  Multi-agent coordination loop. Provider-agnostic.                  │  │
│  │                                                                     │  │
│  │  Contains:                                                          │  │
│  │  ├── Bridge I/O (markdown read/write, any bridge format)            │  │
│  │  ├── Event sourcing (JSONL events → state snapshots)                │  │
│  │  ├── State machine (formal transitions, recovery procedures)        │  │
│  │  ├── Follow loop (event subscription, stall detection)              │  │
│  │  ├── Peer liveness (heartbeat, freshness, attention routing)        │  │
│  │  ├── Promotion engine (plan resolution, candidate validation)       │  │
│  │  ├── Service identity (git-based, works on any repo)                │  │
│  │  └── Session launcher (terminal automation, any provider)           │  │
│  │                                                                     │  │
│  │  Entry point: codex-review launch | status | ensure | wait          │  │
│  │  Config: RepoPathConfig (injected, not frozen singleton)            │  │
│  │  Providers: Codex, Claude, Gemini, custom (via ProviderAdapter)     │  │
│  │  Canonical state stays provider-neutral; adapters own provider      │  │
│  │  status inference and provider-specific field naming                │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  codex-plan-registry                                                │  │
│  │  Universal plan ingestion. Typed, not prose-scraped.                │  │
│  │                                                                     │  │
│  │  Contains:                                                          │  │
│  │  ├── Plan schema (machine-readable contract for plan docs)          │  │
│  │  ├── Plan parser (markdown → typed PlanSpec with validation)        │  │
│  │  ├── Plan registry (INDEX.md stays human-facing; typed .json twin)  │  │
│  │  ├── MP scope resolver (plan → active scope → execution routing)    │  │
│  │  ├── Cross-plan dependency graph                                    │  │
│  │  └── Plan sync guard (validates registry ↔ tracker consistency)     │  │
│  │                                                                     │  │
│  │  Entry point: codex-plans resolve | validate | export               │  │
│  │  Input: Any markdown plan with required sections + typed twin       │  │
│  │  Output: PlanRegistry JSON for runtime consumption                  │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  codex-memory                                                       │  │
│  │  Portable AI project memory. Works with any repo.                   │  │
│  │                                                                     │  │
│  │  Contains:                                                          │  │
│  │  ├── Context pack contract (schema-versioned, portable)             │  │
│  │  ├── Memory store (pluggable backend: SQLite, JSON, JSONL)          │  │
│  │  ├── Knowledge base (topic-keyed chapters, searchable)              │  │
│  │  ├── Session state (cross-conversation persistence)                 │  │
│  │  ├── Artifact registry (checksums, retention, lifecycle)            │  │
│  │  └── Z-graph compression (optional, for large context packs)        │  │
│  │                                                                     │  │
│  │  Entry point: codex-memory store | recall | export | prune          │  │
│  │  Config: ContextPackConfig (repo identity, memory roots, TTL)       │  │
│  │  Storage: NOT .voiceterm/ — configurable per-repo path              │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  codex-autonomy                                                     │  │
│  │  AI agent orchestration loops. Triage, fix, verify.                 │  │
│  │                                                                     │  │
│  │  Contains:                                                          │  │
│  │  ├── Autonomy loop (single agent: triage → fix → verify)            │  │
│  │  ├── Swarm engine (parallel agents, adaptive sizing)                │  │
│  │  ├── Guard-run wrapper (git diff → hygiene → watchdog episode)      │  │
│  │  ├── Triage engine (risk classify → priority → assign)              │  │
│  │  ├── Feedback sizing (stall → downshift, improve → upshift)         │  │
│  │  ├── Watchdog (episode tracking, telemetry, metrics)                │  │
│  │  ├── Mutation testing (mutants, mutation-score, mutation-loop)       │  │
│  │  └── Ralph adapter (CodeRabbit → triage → fix, pluggable)           │  │
│  │                                                                     │  │
│  │  Entry point: codex-auto loop | swarm | triage | guard-run          │  │
│  │  Depends on: codex-governance-core (for guards)                     │  │
│  │  Depends on: codex-review-channel (for coordination)                │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  codex-surfaces (optional)                                          │  │
│  │  UI layers. Thin wrappers over typed contracts.                     │  │
│  │                                                                     │  │
│  │  Contains:                                                          │  │
│  │  ├── Operator console (PyQt6 desktop, reads artifacts only)         │  │
│  │  ├── Mobile relay (SwiftUI, JSON decode only)                       │  │
│  │  ├── CLI renderer (terminal markdown/JSON output)                   │  │
│  │  ├── Web dashboard (future: observability, trends, SLA tracking)    │  │
│  │  └── Slash command hooks (abstractions for agent coders)            │  │
│  │                                                                     │  │
│  │  Surfaces NEVER bypass the engine. All execution → codex-governance │  │
│  │  Surfaces read typed artifacts, shell to engine commands             │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────┘
```

### 13b. Target Data Pipeline (Universal, Any Repo)

```
ANY REPO                                          THE SYSTEM
─────────                                         ──────────

┌──────────────┐     ┌───────────────────────────────────────────────────┐
│ Source Code   │────→│ INGESTION LAYER                                   │
│ (any language)│     │                                                   │
│              │     │  1. project.governance.json detected at repo root  │
│ Plan Docs    │────→│  2. Repo-pack loaded (NOT frozen VoiceTerm default)│
│ (markdown)   │     │  3. Quality policy resolved (preset → repo policy) │
│              │     │  4. Plans parsed → typed PlanRegistry              │
│ Config       │────→│  5. Source scanned → AST → standardized metrics    │
│ (JSON)       │     │  6. External findings imported → unified schema    │
│              │     │                                                   │
│ External     │────→│  ALL DATA NOW IN CONSISTENT INTERNAL FORMAT       │
│ Tools        │     │  (schema-versioned, finding_id'd, provenance'd)   │
└──────────────┘     └────────────────────┬──────────────────────────────┘
                                          │
                                          ▼
                     ┌───────────────────────────────────────────────────┐
                     │ GUARD LAYER (The "Box Around AI")                  │
                     │                                                   │
                     │  Hard guards fire → PASS or BLOCK                 │
                     │  Review probes fire → advisory hints              │
                     │  Each finding carries:                            │
                     │   • finding_id (deterministic, stable across runs)│
                     │   • schema_version + contract_id                  │
                     │   • provenance (guard_version, policy_version,    │
                     │     run_id, timestamp)                            │
                     │   • severity, ai_instruction, remediation hint    │
                     │                                                   │
                     │  Guards are deterministic:                        │
                     │  Same code + same policy = same findings          │
                     │  AI cannot bypass guards. Guards ARE the authority.│
                     └────────────────────┬──────────────────────────────┘
                                          │
                                          ▼
                     ┌───────────────────────────────────────────────────┐
                     │ EVIDENCE LAYER (Persistence + Learning)           │
                     │                                                   │
                     │  Findings → unified JSONL ledger                  │
                     │   • Append-only, bounded reads (deque)            │
                     │   • Dedup by finding_id                           │
                     │   • Track lifecycle: new → deferred → fixed       │
                     │                                                   │
                     │  Quality feedback → JSON snapshot                  │
                     │   • Maintainability score (7 sub-scores)          │
                     │   • Halstead metrics (per-language)               │
                     │   • False-positive analysis                       │
                     │   • ImprovementDelta (vs previous run)            │
                     │   • Proves quality trend with data                │
                     │                                                   │
                     │  Episodes → telemetry JSONL                       │
                     │   • Times, retries, diffs, verdicts               │
                     │   • model_id, token_count, context_budget         │
                     │   • cost_usd where provider/runtime can supply it │
                     └────────────────────┬──────────────────────────────┘
                                          │
                                          ▼
                     ┌───────────────────────────────────────────────────┐
                     │ CONTEXT LAYER (Memory + Knowledge)                │
                     │                                                   │
                     │  ContextPack (schema-versioned, portable):        │
                     │   • Repo identity + repo-pack id                  │
                     │   • Active plan state (from typed registry)       │
                     │   • Recent findings + quality trend               │
                     │   • Knowledge base (topic-keyed chapters)         │
                     │   • Session memory (cross-conversation state)     │
                     │                                                   │
                     │  Fed to AI agents as structured context           │
                     │  Compressed if needed (Z-graph, token budgets)    │
                     │  Gives AI the full picture of system health       │
                     └────────────────────┬──────────────────────────────┘
                                          │
                                          ▼
                     ┌───────────────────────────────────────────────────┐
                     │ COORDINATION LAYER (Multi-Agent Loop)             │
                     │                                                   │
                     │  Review channel (provider-agnostic):              │
                     │   • Any AI backend (Codex, Claude, Gemini, custom)│
                     │   • Multi-reviewer support (not just 1:1)         │
                     │   • Event-sourced state machine                   │
                     │   • Peer liveness, stall detection, recovery      │
                     │                                                   │
                     │  Autonomy engine:                                  │
                     │   • Single loop or parallel swarm                 │
                     │   • Triage → prioritize → assign → fix → verify   │
                     │   • Guard-run wrapper on every AI edit             │
                     │   • Feedback sizing (adaptive agent count)         │
                     │                                                   │
                     │  AI is ALWAYS inside the guard box.                │
                     │  Every edit → guards → findings → evidence.        │
                     │  The loop never runs without governance.           │
                     └────────────────────┬──────────────────────────────┘
                                          │
                                          ▼
                     ┌───────────────────────────────────────────────────┐
                     │ SURFACE LAYER (Two Audiences)                     │
                     │                                                   │
                     │  FOR AGENT CODERS (simple):                       │
                     │  ┌─────────────────────────────────────────────┐  │
                     │  │ /check          — run guards, see pass/fail │  │
                     │  │ /fix            — auto-fix findings          │  │
                     │  │ /status         — see quality trend          │  │
                     │  │ /review         — start review loop          │  │
                     │  │ Slash commands, hooks, simple CLI             │  │
                     │  │ Don't need to understand internals            │  │
                     │  │ System "just works" behind abstractions       │  │
                     │  └─────────────────────────────────────────────┘  │
                     │                                                   │
                     │  FOR SENIOR DEVS (full detail):                   │
                     │  ┌─────────────────────────────────────────────┐  │
                     │  │ Operator console — full system dashboard     │  │
                     │  │ Finding ledgers — raw JSONL, query anything  │  │
                     │  │ Quality reports — Halstead, FP analysis      │  │
                     │  │ Episode telemetry — every agent action logged│  │
                     │  │ Plan registry — typed execution state        │  │
                     │  │ Guard source — read/modify any check         │  │
                     │  │ Full data available, nothing hidden           │  │
                     │  └─────────────────────────────────────────────┘  │
                     └───────────────────────────────────────────────────┘
```

### 13c. Target Onboarding Flow (Any New Repo)

```
NEW REPO WANTS TO USE THE SYSTEM:

Step 1: Install
  $ pip install codex-governance-core
  $ pip install codex-review-channel    # optional: if using multi-agent
  $ pip install codex-memory            # optional: if using memory system
  $ pip install codex-autonomy          # optional: if using AI remediation

Step 2: Bootstrap
  $ codex-governance bootstrap
  ┌──────────────────────────────────────────────────┐
  │ Scans repo → detects languages, layout, CI       │
  │ Auto-drafts project.governance.json              │
  │ Auto-drafts project.governance.md                │
  │ Selects quality preset (python, rust, both)      │
  │ Creates dev/active/INDEX.md + MASTER_PLAN.md     │
  │ Generates CLAUDE.md / AGENTS.md from templates   │
  └──────────────────────────────────────────────────┘

Step 3: Validate
  $ codex-governance check --profile ci
  $ codex-governance probe-report --format md
  $ codex-governance quality-policy --format md

Step 4: Customize (if needed)
  Edit project.governance.json:
  ├── Override guard list (add/remove specific checks)
  ├── Override bundle commands (your CI, not ours)
  ├── Set path roots (where your source lives)
  ├── Set artifact roots (where reports go)
  ├── Add custom guards (JSON registry, not code edit)
  └── Add risk add-ons (perf, security, etc.)

Step 5: Run
  AI agents read project.governance.json at session start
  → Guards constrain every edit
  → Findings tracked in unified ledger
  → Quality trend measured over time
  → System proves it improves code (or doesn't)

NO CORE CODE PATCHES. NO VOICETERM ASSUMPTIONS.
EVERYTHING CONFIGURED VIA project.governance.json + presets.
```

### 13d. Target Dependency Graph (Packages)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│                    codex-surfaces (optional)                              │
│                    Operator console, mobile, web, CLI                     │
│                    ↓ reads artifacts from ↓                               │
│                                                                          │
│          ┌─────────┴──────────────────────┴─────────┐                    │
│          │                                           │                    │
│    codex-autonomy                          codex-memory                   │
│    Loops, swarm, triage,                   ContextPack, knowledge base,   │
│    guard-run, watchdog                     session state, artifacts       │
│          │                                           │                    │
│          └─────────┬──────────────────────┬──────────┘                    │
│                    │                      │                                │
│          codex-review-channel    codex-plan-registry                      │
│          Multi-agent coord,      Typed plans, MP scope,                   │
│          event sourcing,         plan sync guard                          │
│          peer liveness                    │                                │
│                    │                      │                                │
│                    └──────────┬───────────┘                                │
│                               │                                           │
│                    codex-governance-core                                   │
│                    Guards, probes, policy engine,                          │
│                    finding contracts, evidence ledger,                     │
│                    identity, quality feedback                              │
│                    (THE FOUNDATION — everything depends on this)           │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

VoiceTerm becomes:
┌──────────────────────────────────────────────────────────────────────────┐
│  voiceterm (product repo)                                                │
│  ├── rust/src/bin/voiceterm/          (Rust binary — unchanged)          │
│  ├── project.governance.json          (repo-level config)                │
│  ├── voiceterm-repo-pack              (VoiceTerm-specific paths/guards)  │
│  │   ├── 16 coupled guards            (mobile_relay, cli_flags, etc.)    │
│  │   ├── RepoPathConfig override      (voiceterm paths)                  │
│  │   └── Provider session templates   (Codex/Claude launch scripts)      │
│  ├── pip install codex-governance-core  (the engine)                     │
│  ├── pip install codex-review-channel   (multi-agent)                    │
│  ├── pip install codex-autonomy         (AI remediation)                 │
│  └── pip install codex-memory           (project memory)                 │
│                                                                          │
│  VoiceTerm is just another consumer. The engine doesn't know about it.   │
└──────────────────────────────────────────────────────────────────────────┘
```

### 13e. Target Data Consistency Contract

```
EVERY piece of data in the system follows these rules:

┌───────────────────────────────────────────────────────────────────────────┐
│                     UNIVERSAL DATA CONTRACTS                              │
│                                                                           │
│  1. EVERY artifact has:                                                   │
│     • schema_version (int, monotonic)                                     │
│     • contract_id (string, globally unique)                               │
│     • created_at_utc (ISO-8601)                                           │
│     • repo_identity (org/repo, deterministic hash)                        │
│                                                                           │
│  2. EVERY finding has:                                                    │
│     • finding_id (SHA1 from repo + check + file + symbol)                 │
│     • schema_version + contract_id                                        │
│     • provenance: guard_version, policy_version, run_id                   │
│     • severity (enum: critical, high, medium, low, info)                  │
│     • signal_type (enum: guard, probe, external, manual)                  │
│     • ai_instruction (remediation guidance for AI agents)                 │
│     • lifecycle: new → acknowledged → deferred → fixed → regressed        │
│                                                                           │
│  3. EVERY plan doc has:                                                   │
│     • Typed JSON twin (alongside human-readable markdown)                 │
│     • Role (tracker | spec | runbook | reference)                         │
│     • Authority (canonical | mirrored | supporting | reference-only)      │
│     • MP scope (validated against registry)                               │
│     • Required sections: Scope, Execution Checklist, Progress Log,        │
│       Audit Evidence                                                      │
│                                                                           │
│  4. EVERY config file has:                                                │
│     • JSON Schema validation (policy, presets, repo-pack)                 │
│     • schema_version for migration                                        │
│     • Inheritance chain (preset → repo policy → runtime override)         │
│                                                                           │
│  5. EVERY episode/run has:                                                │
│     • run_id (unique per execution)                                       │
│     • policy_snapshot_hash (which policy was active)                       │
│     • timing (start, end, duration)                                       │
│     • verdict (pass, fail, partial, skipped)                              │
│     • artifact receipts (what was produced, checksums)                     │
│     • model_id, token_count, context_budget, cost_usd (when available)    │
│                                                                           │
│  6. EVERY context pack has:                                               │
│     • pack_id + schema_version                                            │
│     • repo_identity                                                       │
│     • content manifest (what's included, estimated tokens)                │
│     • freshness (when generated, TTL)                                     │
│                                                                           │
│  VALIDATION:                                                              │
│  Guards enforce these contracts. If data doesn't match schema, the        │
│  guard blocks it. This is what makes the system deterministic.            │
│  Same input + same policy = same output. Always.                          │
└───────────────────────────────────────────────────────────────────────────┘
```

### 13f. Before vs After Summary

```
┌─────────────────────────────────┬─────────────────────────────────────────┐
│         BEFORE (Current)        │         AFTER (Target)                  │
├─────────────────────────────────┼─────────────────────────────────────────┤
│ One monolith repo               │ 6 independent packages + 1 product repo│
│ 51 frozen path config calls     │ 0 frozen calls; injected RepoPathConfig│
│ Guards in hardcoded tuples      │ Guards discoverable via JSON registry   │
│ Bundles hardcoded in registry   │ Bundles customizable per-repo via JSON  │
│ Plans parsed from prose         │ Plans have typed JSON twins             │
│ 3 different finding schemas     │ 1 unified finding contract             │
│ No schema versioning            │ Every artifact schema-versioned         │
│ No provenance on findings       │ Full provenance chain on every finding  │
│ Memory embedded in .voiceterm/  │ Memory as portable ContextPack          │
│ Review loop tied to Codex/Claude│ Review loop provider-agnostic           │
│ Provider status hardcoded       │ Provider inference isolated in adapters │
│ No quality-to-cost telemetry    │ Quality proof includes cost/context     │
│ 107 legacy ledger rows unversioned│ All rows carry schema_version + migrated│
│ Console imports raw devctl paths │ Console reads typed contracts via DI    │
│ CI one-shot cutover risk         │ Compatibility-first staged migration    │
│ Bootstrap = copy 4 markdown files│ Bootstrap = pip install + auto-draft   │
│ External repos need code patches│ External repos need only JSON config    │
│ Quality claims are anecdotal    │ Quality proven by ImprovementDelta data │
│ Vibe coders see raw complexity  │ Vibe coders see /check, /fix, /status  │
│ Senior devs dig through files   │ Senior devs get full dashboards + data  │
│ 85% portable, 15% coupled       │ 100% portable core, repo-packs optional│
│ AI is a black box               │ AI is constrained by deterministic      │
│                                 │  guards — no longer a black box          │
└─────────────────────────────────┴─────────────────────────────────────────┘
```

---

*Updated 2026-03-19 after the authority-loop plan consolidation and validator pass. Numbers remain tied to the audited live tree; target-state rows now reflect the explicit `MP-377` authority-loop commitments.*
