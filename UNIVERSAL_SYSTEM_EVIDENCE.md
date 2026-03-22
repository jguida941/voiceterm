# Universal System Evidence — Complete Reference

## DO NOT DELETE, REFORMAT, OR CONDENSE THIS FILE

This is reference-only evidence. NOT a tracked execution plan. NOT a second
authority. The disposition table is in UNIVERSAL_SYSTEM_PLAN.md. This file
contains the DETAILED FINDINGS behind each disposition. Codex: leave this
file intact. The companion summary exists separately.

---

## Part 1: Root Directory Cleanup

### Current State (11 .md files at root, industry standard: 2-4)

| File | Size | Keep at Root? | Action |
|------|------|--------------|--------|
| README.md | 12KB | YES | User entry point |
| QUICK_START.md | 6KB | YES | Fast onboarding |
| AGENTS.md | 116KB | YES | Industry standard for AI agents |
| CLAUDE.md | 8KB | YES | Generated AI bootstrap |
| bridge.md | 319KB | YES | Live review state (operational) |
| Makefile | 12KB | YES | Build shortcuts |
| SYSTEM_AUDIT.md | 97KB | Reference | Large audit doc |
| SYSTEM_FLOWCHART.md | 86KB | Reference | Architecture diagram |
| ZGRAPH_RESEARCH_EVIDENCE.md | 50KB | Reference | Research artifact |
| GUARD_AUDIT_FINDINGS.md | 10KB | Reference | Guard audit |
| UNIVERSAL_SYSTEM_PLAN.md | Disposition | Reference | Intake review |
| DEV_INDEX.md | 2KB | DELETE | Shim redirect |
| cvelist (5 files) | 0 bytes | DELETE | Empty orphans |

### Orphan files at root
- cvelist, cvelist-html, cvelist-our, cvelist-our-html, cvelist.diff (all 0 bytes)
- DEV_INDEX.md (40 lines, just says "see dev/README.md instead")

---

## Part 2: Documentation Organization

### Docs currently in 4 places
- root/ — 11 .md files
- guides/ — 7 user-facing guides (INSTALL, USAGE, etc.)
- dev/guides/ — 13 internal guides (ARCHITECTURE, DEVELOPMENT, etc.)
- dev/active/ — 27 execution plans

### Rules for where docs go
| Doc Type | Location | Metadata Required? | Guard Enforced? |
|----------|----------|-------------------|-----------------|
| User guides | guides/ | Optional | No |
| AI agent policy | root (AGENTS.md) | Optional | check_agents_contract |
| Execution plans | dev/active/ | YES | check_active_plan_sync |
| Internal guides | dev/guides/ | YES | check_markdown_metadata_header |
| Config | dev/config/ | N/A (JSON/YAML) | Schema guards |

---

## Part 3: Markdown Format Consistency

### Current compliance
| Category | Total | With Metadata | Gap |
|----------|-------|--------------|-----|
| dev/active/ execution-plans | 17 | 17 | NONE |
| dev/active/ reference docs | 10 | 5 | 5 missing |
| dev/guides/ | 13 | 1 | 12 missing |
| Root non-user-facing | 6 | 0 | 6 missing |

### Current standard (NOT YAML frontmatter)
The repo uses inline markdown metadata per PLAN_FORMAT.md:
```
**Status**: active | **Last updated**: 2026-03-22 | **Owner:** area
```
This is the accepted standard. YAML frontmatter is optional future ingest
support, not the mandatory migration target.

---

## Part 4: Portability — Score 3-4/10

### Critical blockers

**1. Module-level path freezing**: ~51 references to active_path_config()
called at module import time freeze VoiceTerm defaults permanently. Custom
repos can never override paths.

**2. Dead portability API**: set_active_path_config() defined but has ZERO
external callers. The escape hatch is unused.

**3. VoiceTerm hardcoding**: ~350 references to "voiceterm" across ~89
Python files. Core subsystems assume operator console, autonomy, iOS relay,
daemon contracts exist.

**4. Incomplete bootstrap**: governance-bootstrap generates minimal starter
policy — missing review-channel, governance, platform-contracts sections.

**5. Check router hardcoded**: RELEASE_EXACT_PATHS references Cargo.toml,
VoiceTerm.app plist. RISK_ADDONS reference overlay/hud, wake-word.

**6. Portable presets too minimal**: portable_python.json is 1.4K vs
voiceterm.json at 11.3K.

---

## Part 5: Self-Governance

### The principle
If the governance system can't keep its OWN repo organized, it can't claim
to work for anyone else.

### What "passing" looks like
- Root has minimal .md files
- Zero orphan files
- All docs have metadata headers
- All execution plans pass guards
- No hardcoded VoiceTerm paths in portable modules
- devctl init works on a fresh empty repo
- New developer can find any doc in ≤2 directory traversals

---

## Part 6: Universal Doc Ingestion

### Approach: Normalize on Ingest, Not on Source

Don't force users to reformat their docs. Instead:
1. Detect format (frontmatter? inline metadata? none?)
2. Extract structure (title, status, sections, cross-references)
3. Normalize to internal model (canonical DocRecord format)
4. Index in context-graph (create nodes with extracted metadata)
5. Generate compliance report

### What already exists
- check_markdown_metadata_header.py has --fix mode
- doc_authority_rules.py classifies docs by role/authority
- doc_authority_metadata.py parses first 10 lines
- INDEX.md registry tracks all active docs

### What's needed
- Format detection (recognize YAML frontmatter, inline metadata, none)
- Multi-format parser
- Auto-classify (guide? spec? runbook? reference?)
- devctl docs-ingest command for batch normalization

---

## Part 7: Industry Standards

### Already landed (Codex confirmed)
- OpenSSF Scorecard (.github/workflows/scorecard.yml)
- SECURITY.md (.github/SECURITY.md)
- --offline flag (cli_parser/builders_checks.py:132)
- disabled_guards (SYSTEM_ARCHITECTURE_SPEC.md:833)

### Still applicable
- markdownlint for structural consistency (optional layer)
- Vale for prose quality (optional layer)
- MADR for ADR format standardization
- AGENTS.md nesting for per-directory AI instructions

---

## Part 8: Proving It Works

### Validation sequence (subordinate to authority spine)
1. Authority spine closure first (blocker tranche → startup → repo-pack)
2. Then self-hosting proof (own repo passes portable governance checks)
3. Then external repo proof (3+ repos, different languages)
4. Then template repo and onboarding flow
5. Then pip-installable package

---

## Part 11: Architecture Gap Analysis

### Plans vs Reality (verified claims only)

| Claim | Reality | Gap |
|-------|---------|-----|
| "Reusable for arbitrary repos" | 350 voiceterm refs in 89 files | Architecture aspires, runtime doesn't |
| "Module-level frozen defaults banned" | ~51 call sites still frozen | Problem identified, not fixed |
| "Second repo works without patches" | 1 pilot tested (ci-cd-hub) | Not production-proven |
| "VoiceTerm stops being hidden default" | set_active_path_config() zero callers | Dead API |
| "Don't make VoiceTerm mandatory" | Review-channel, autonomy assumed | Subsystems not opt-in |

### Typed authority spine exists
ProjectGovernance, DocPolicy, DocRegistry, PlanRegistry all exist as typed
contracts in dev/scripts/devctl/runtime/project_governance_contract.py.
The spine is: ProjectGovernance → RepoPack → DocPolicy/DocRegistry →
PlanRegistry → PlanTargetRef → startup-context → WorkIntakePacket →
CollaborationSession → TypedAction → ActionResult/RunRecord/Finding →
ContextPack

---

## Part 14: Cross-Plan Conflicts

### 8 conflicts/gaps found (some partially resolved per Codex review)

1. MP-376 ownership split between review_probes and portable_code_governance
   (partially resolved in INDEX.md but fragmented)
2. MP-375 Phase 5 no clear single owner
3. Phase 5b evaluation gate no explicit policy owner
4. Cross-repo proof required but no plan owns the concrete work
5. Operator console migration required but not in authority loop checklist
6. autonomous_control_plane.md doesn't acknowledge MP-377 subordination
7. Memory studio contract boundary undefined
8. Probes shipped locally but not made portable

---

## Part 15: Missing Plan Categories

### 7 categories that should exist (as bounded follow-ups, not new master plan)

1. Onboarding / Bootstrap / Init — devctl init flow
2. Universal doc ingestion — format-agnostic normalization
3. Guard/probe lifecycle — graduation, deprecation, removal policy
4. AI code quality feedback loop — teaching AI, not just catching AI
5. Metrics & observability — measuring if governance works
6. Multi-language expansion — beyond Python/Rust (deferred)
7. Cross-repo policy presets — preset library for rapid adoption

---

## Part 16: AI Code Quality — The Feedback Loop Gap

### The system DETECTS bad AI code but doesn't TEACH AI to write better code.

**Break 1: AI Never Sees Fix Guidance**
- Probes generate ai_instruction fields with specific fix strategies
- But ralph_ai_fix.py loads backlog-medium.json (CodeRabbit findings), NOT
  probe findings with their ai_instruction fields
- The wire exists but is not connected

**Break 2: AI Doesn't Learn From Failure**
- When AI's fix fails, changes are reverted
- Next round starts with SAME finding, ZERO knowledge of prior failure
- AI likely tries the SAME fix again
- No mechanism to say "Previous attempt failed because X — try Y instead"

**Break 3: Quality Feedback Improves Guards, Not AI**
- Quality feedback tracks FP rates, cleanup rates, improvement deltas
- Recommendations are for TUNING GUARDS, not TEACHING AI
- AI gets ZERO feedback on its own accuracy

### What the system needs (from industry research)

1. Attribution tracking on probe findings (CodeRabbit: 49.2% precision)
2. Fix strategy archive (Darwin Godel Machine: 20%→50% SWE-bench)
3. Mutation testing against guards (Meta ACH: 73% acceptance)
4. Fix quality judge (Spotify Honk: catches 25% of problematic changes)
5. Longitudinal telemetry (guard failure rates across weeks/months)

---

## Part 17: Package Modularization — Score C/75.8%

### 24 packages with proper __init__.py (95% coverage)
### Zero circular dependencies (clean DAG)
### 79 root-level modules — MAJOR blocker (should be ~20)
### 19 packages import from repo_packs (should be ≤5)

### Extraction readiness
- Would work cleanly: runtime, platform, probe_topology, loops, triage, security
- Needs refactoring: commands (94 files), review_channel (62), governance (32)
- Would break: data_science, context_graph, publication_sync (repo_packs coupling)

---

## Part 20: Deferred Work & Decision Tracking

### 15 deferred items with NO reactivation gate
- 3 files in dev/deferred/ (DEV_MODE_PLAN, LOCAL_BACKLOG, phase2)
- 14+ "post-release" markers in pre_release_architecture_audit.md
- Only LOCAL_BACKLOG has explicit reactivation rule
- No guard flags stale deferred items

### ADR System — Good Structure, No Enforcement
- 99 ADRs across 3 directories (29 VoiceTerm, 70 CI/CD Hub, 7 Code-Link)
- Hygiene guards validate structure (status, date, index, numbering)
- But NO guard verifies ADR decisions are followed in code
- Locked Decisions in plan docs are prose — not machine-parseable
- VoiceTerm ADRs lack owner/reviewer/last-reviewed dates

---

## Part 21: Rust Code Organization — B+/82%

### Significantly cleaner than Python (C/75.8%)
- 58 modules, 23 directories, 20 mod.rs files — all proper
- Zero orphaned directories, zero circular dependencies
- Clean lib/bin separation (lib.rs exports 9 reusable modules)
- Feature gates properly structured
- Rust→Python boundary clean (JSONL-based, async)

### Cleanup items
- 6 files in 700-830 line range (theme modules)
- 4 thin-wrapper modules — consolidate to mod.rs pattern
- Naming inconsistency (handlers vs operators vs commands)

---

## Part 22: 10 Critical Gaps Before Extraction

### Verified gaps (after removing already-landed features)

1. **Migration & Legacy Support** — Zero migration strategy for existing repos
2. **Guard Versioning** — No version metadata, no deprecation policy
3. **Offline** — --offline flag EXISTS but limited scope
4. **Performance** — No performance budget or per-guard telemetry
5. **Error Recovery** — Guard crashes take down entire check suite
6. **Security** — SECURITY.md EXISTS but render-surfaces not sandboxed
7. **Guard Testing** — No regression test suite, no mutation testing
8. **Guard Documentation** — No devctl list-guards, no per-guard guide
9. **Rollback** — disabled_guards DOCUMENTED but not wired into check.py
10. **Community** — CONTRIBUTING.md silent on guards/probes

---

## Part 23: devctl init Design

### Best practices from industry (ESLint, Terraform, Trunk, Renovate, Copier)

1. Auto-detect repo shape (Trunk/Renovate) — zero questions
2. Phased init, idempotent (Terraform) — detect→configure→install→verify
3. Preview before commit (Renovate) — show diff of what will change
4. Store generation metadata (Copier) — enable three-way merge on update
5. Hermetic versioning (Trunk) — pin guard versions in config
6. Respect existing config (Trunk/pre-commit) — don't stomp existing files
7. Team vs personal mode (Trunk) — --share vs --local
8. Guards as packages (pre-commit) — manifest with entry, patterns, severity
9. Guided + gate modes (commitlint) — wizard for local, strict for CI
10. Doc registration phase (UNIQUE to devctl) — index architecture docs

### Concrete flow
```
$ devctl init
Phase 1: Detect (auto, no questions)
Phase 2: Configure (generate config from detected shape)
Phase 3: Install (register applicable guards)
Phase 4: Verify (dry run, baseline report)
```

---

## Corrected Facts (from Codex review)

- Root .md count: 11 (not 10 as originally stated)
- VoiceTerm references: ~350 in ~89 files (not 425 in 111)
- --offline flag: EXISTS in cli_parser/builders_checks.py:132
- disabled_guards: DOCUMENTED in SYSTEM_ARCHITECTURE_SPEC.md:833
- OpenSSF Scorecard: EXISTS in .github/workflows/scorecard.yml
- SECURITY.md: EXISTS in .github/SECURITY.md
- Markdown standard: inline metadata (not YAML frontmatter)
- MP-375/376 ownership: partially explicit (fragmented but documented)
- ProjectGovernance/DocPolicy/DocRegistry: EXIST as typed contracts
- Operator-console/memory boundaries: DECLARED in plan docs

---

---

## Part 12: What the Plans SHOULD Add

### Organization & Self-Governance
- [ ] Clean own repo root: delete orphans, consolidate reference docs
- [ ] Add metadata headers to all files currently missing them
- [ ] Build and register check_repo_organization.py guard
- [ ] Add check_doc_metadata_coverage.py for metadata enforcement
- [ ] VoiceTerm must pass all portable governance checks as a consumer

### Portability Closure
- [ ] Eliminate module-level active_path_config() frozen defaults
- [ ] Wire set_active_path_config() into devctl CLI startup
- [ ] Make review-channel, autonomy, operator console opt-in via policy
- [ ] Move check router constants to repo policy JSON
- [ ] Create graduated quality presets: starter, standard, full-governance

### Onboarding
- [ ] Build devctl init command (interactive onboarding)
- [ ] Create template repo skeleton
- [ ] Document onboarding flow: "5 steps to adopt AI governance"
- [ ] Test devctl init on 3+ repos (Python-only, Rust-only, mixed)

### Proof
- [ ] Multi-repo benchmark suite (not just 1 pilot)
- [ ] Prove VoiceTerm works as portable governance consumer
- [ ] Measure: "mid-level engineer can onboard new repo in <1 hour"

### The Backwards Proof Problem
Plans say "test on external repos" (done: 1 pilot). Plans DON'T say
"VoiceTerm must use the same portable contracts." VoiceTerm = embedded
version with special privileges. Portable engine = separate code path.
Proof should be INTERNAL first (clean own repo), then EXTERNAL.

### Portability Score Breakdown

| Aspect | Score | Evidence |
|--------|-------|---------|
| Architecture direction | 8/10 | Plans describe correct abstractions |
| RepoPathConfig abstraction | 7/10 | API exists, presets exist |
| Actual path portability | 2/10 | ~51 frozen import-time defaults |
| Bootstrap completeness | 3/10 | Generates minimal policy |
| Subsystem opt-in | 3/10 | Frontends optional, loops assumed |
| Onboarding flow | 2/10 | No devctl init, scattered commands |
| Own repo as proof | 1/10 | Root cluttered, guides unformatted |
| External repo proof | 4/10 | 1 pilot tested |
| **Overall** | **3.5/10** | Architecture strong, implementation weak |

---

## Part 13: Universal System Architecture

### Three scenarios a universal system must handle

**Scenario 1: New empty repo** — devctl init scaffolds everything.
**Scenario 2: Existing repo** — devctl docs-ingest normalizes existing docs.
**Scenario 3: This repo (VoiceTerm)** — same engine, no special privileges.

### Standard directory convention (configurable via repo_policy.json)
```
any-repo/
├── AGENTS.md
├── README.md
├── dev/
│   ├── active/ (execution plans with INDEX.md registry)
│   ├── guides/ (internal docs)
│   ├── archive/ (completed plans)
│   ├── config/ (repo_policy.json + quality_presets/)
│   ├── reports/ (generated artifacts)
│   └── scripts/ (checks, probes, devctl)
├── docs/ or guides/ (user-facing)
└── src/ (source code)
```

---

## Part 14: Cross-Plan Conflicts (8 found)

1. MP-376 ownership split (review_probes vs portable_code_governance)
2. MP-375 Phase 5 no clear single owner
3. Phase 5b evaluation gate no explicit policy owner
4. Cross-repo proof required but no plan owns the work
5. Operator console migration not in authority loop checklist
6. autonomous_control_plane.md doesn't know it's subordinate to MP-377
7. Memory studio contract boundary undefined
8. Probes shipped locally but not made portable

---

## Part 15: 7 Missing Plan Categories

1. Onboarding / Bootstrap / Init
2. Universal doc ingestion / knowledge import
3. Guard/probe lifecycle (graduation, deprecation, removal)
4. AI code quality feedback loop (teaching AI, not just catching)
5. Metrics & observability
6. Multi-language expansion (beyond Python/Rust)
7. Cross-repo policy presets

---

## Part 16: AI Feedback Loop — 3 Critical Breaks

**Break 1**: Probes generate ai_instruction but ralph_ai_fix.py loads
CodeRabbit findings instead. Wire exists but not connected.

**Break 2**: Failed fixes are reverted, next round has ZERO knowledge
of prior failure. AI tries same fix again.

**Break 3**: Quality feedback tunes GUARDS, not AI. AI gets zero
feedback on its own accuracy.

**Industry solutions**: CodeRabbit attribution (49.2% precision), Darwin
Godel Machine (20%→50% SWE-bench), Meta ACH mutation testing (73%
acceptance), Spotify Honk fix quality judge (25% catch rate).

---

## Part 17: Package Modularization — C/75.8%

- 24 packages, 95% __init__.py coverage
- Zero circular dependencies
- 79 root-level modules (should be ~20) — MAJOR blocker
- 19 packages import repo_packs (should be ≤5)
- Extraction: runtime/platform/security would work; commands/review_channel
  need refactoring; data_science/context_graph would break

---

## Part 20: Deferred Work — 15 Items with No Reactivation Gate

- 3 files in dev/deferred/, 14+ "post-release" markers
- Only LOCAL_BACKLOG has explicit promotion rule
- No guard flags stale deferred items
- 99 ADRs with good structure but NO enforcement of decisions in code
- Locked Decisions in plan docs are prose, not machine-parseable

---

## Part 21: Rust Organization — B+/82%

- 58 modules, zero orphans, zero circular deps
- Clean lib/bin separation, proper feature gates
- Rust→Python boundary clean (JSONL-based)
- 6 files in 700-830 range need splitting
- 4 thin wrappers need consolidation

---

## Part 22: 10 Critical Gaps Before Extraction (corrected)

1. Migration & legacy support (no migration strategy)
2. Guard versioning (no version metadata, no deprecation policy)
3. Offline — --offline EXISTS but limited scope
4. Performance (no budget, no per-guard telemetry)
5. Error recovery (guard crash takes down whole suite)
6. Security — SECURITY.md EXISTS but render-surfaces not sandboxed
7. Guard testing (no regression suite, no mutation testing)
8. Guard documentation (no list-guards command, no per-guard guide)
9. Rollback — disabled_guards DOCUMENTED but not wired into check.py
10. Community (CONTRIBUTING.md silent on guards/probes)

---

## Part 23: devctl init Design (from industry research)

1. Auto-detect repo shape (Trunk/Renovate) — zero questions
2. Phased init, idempotent (Terraform) — detect→configure→install→verify
3. Preview before commit (Renovate) — show diff
4. Store generation metadata (Copier) — three-way merge on update
5. Hermetic versioning (Trunk) — pin guard versions
6. Respect existing config (Trunk/pre-commit) — don't stomp
7. Team vs personal mode — --share vs --local
8. Guards as packages (pre-commit) — manifest with entry/patterns/severity
9. Guided + gate modes (commitlint) — wizard for local, strict for CI
10. Doc registration phase (UNIQUE to devctl) — index architecture docs

---

## Part 24: Priority Order (reference only — tracked order in MASTER_PLAN)

Phase 0: Prove on own repo (cleanup, metadata, guard pass)
Phase 1: Organization guards (check_repo_organization, metadata coverage)
Phase 2: AI feedback loop (wire ai_instruction, failure context, archives)
Phase 3: Guard quality & security (test registry, crash isolation, audit)
Phase 4: Portability (lazy eval, path config, packages, opt-in subsystems)
Phase 5: Onboarding (devctl init, template repo, docs-ingest)
Phase 6: Cross-plan closure (8 conflicts, lifecycle policy, ADR guards)
Phase 7: Publish (pip package, multi-repo benchmark, documentation)

NOTE: This priority order is REFERENCE ONLY. The accepted execution order
is in MASTER_PLAN.md: blocker tranche → startup authority → repo-pack →
typed registries → WorkIntakePacket → CollaborationSession. Items from
this list must be sequenced BEHIND the authority spine, not ahead of it.

---

---

## Part 25: AI Code Production Flow — 10 Feedback Loop Breakpoints

### Complete end-to-end trace of how AI writes code in this system.

**Step 1: Bootstrap** — AI reads CLAUDE.md → AGENTS.md → context-graph bootstrap.
BREAK: Typed StartupContext (ProjectGovernance, ReviewerGateState, push
enforcement) is NOT routed into bootstrap. AI gets prose, not machine state.

**Step 2: Task Discovery** — 3 separate entry points (bridge.md, autonomy-loop,
swarm_run) with different context loading and task selection. No single
WorkIntakePacket unifies "what should AI do now?"

**Step 3: Pre-Write Guidance** — Quality policy exists but is read by CHECK, not
routed to AI. ai_instruction from probes is advisory and generated AFTER code
exists. DecisionPacket created AFTER review. AI writes code with ZERO
machine-readable pre-write guidance.

**Step 4: Guard Check** — 32 hard guards + 23 probes run. Findings captured as
typed FindingRecord. BUT findings are bifurcated: hard guard → governance JSONL,
probes → advisory report. No unified finding packet routed back to AI.

**Step 5: Finding Routing** — Findings land in 4 SEPARATE SINKS: episodes
(watchdog JSONL), PR comments (triage), checkpoint packets (autonomy rounds),
feedback reports (governance). None become INPUT to next coding session.

**Step 6: Finding Enrichment** — ai_instruction field exists in FindingRecord but
is EMPTY for ~90% of findings. review_lens is empty. validation_plan is empty.
AI gets raw finding without knowing HOW to fix or HOW to verify.

**Step 7: Fix Guidance** — Finding + ai_instruction are NEVER ROUTED TO AI.
Ralph loads CodeRabbit findings, not probe findings. Autonomy loop checkpoint
packets sit in filesystem. Guard-run reports are written, not pushed.

**Step 8: Failure Handling** — Failures ARE captured (typed episodes, failure
packets, feedback streaks). Feedback sizing adapts agent count. BUT failure
data is NOT fed back to AI prompt. AI doesn't know WHY previous fix failed.

**Step 9: Next Round** — Context between rounds is NOT cumulative. AI gets
"here's the next checklist item" not "you tried X last round, it caused Y
failure, here's the diagnosis." Watchdog episodes are persisted but never
summarized for AI.

**Step 10: Session End** — Evidence scattered across 5+ artifact trees (bridge,
governance JSONL, episodes, probe reports, plan markdown, checkpoint packets).
No unified SessionResume packet. Next session is COLD START.

### The Core Issue

The repo has TYPED CONTRACTS (Finding, FailurePacket, StartupContext,
DecisionPacket) but NO CLOSED LOOP to route them back to AI.

What's missing at each step:
1. Bootstrap: route StartupContext typed state to AI
2. Task: unify entry points into WorkIntakePacket
3. Pre-write: route quality policy + prior findings to AI BEFORE coding
4. Post-check: route findings + ai_instruction to AI (not just reports)
5. Failure: carry failure context + diagnosis into retry prompt
6. Session: auto-generate SessionResume packet from all evidence

---

## Part 26: Unexplored Areas — 5 Critical Gaps Found

### Final sweep found 5 areas not in any evidence doc.

**1. Slash Command Surface** — dev/templates/slash/ contains Phase-A voice
capture templates for Codex and Claude. Primary human-facing entry point into
VoiceTerm from AI chat. Not documented in any MP or authority doc.

**2. PyPI Bootstrap & Distribution** — pypi/ has complete pip package scaffold
(pyproject.toml, cli.py, bootstrap.py). Downloads native Rust binary from
GitHub Releases. Supports binary-only, binary-then-source, source-only modes.
Not mentioned in architecture docs. Critical user-facing surface.

**3. Mobile Projection Protocol** — mobile_status_projection.py has typed
projection dataclasses (CompactMobileStatusProjection, AlertMobileStatusProjection).
Intended portable interface for phone/SSH views. Not documented as standalone
portable contract.

**4. Data Science & Agent Sizing** — dev/scripts/devctl/data_science/ auto-
generates snapshots on every devctl invocation. Recommendation scoring with
weighted formula (success 45% + tasks/min 35% + efficiency 20%). Operational
but not documented as an MP.

**5. Rendering Surface Architecture** — Rendering logic distributed across
commands, mobile views, and repo packs with no unified documentation. Surface
rendering (instruction generation, mobile projections) split across 3+ modules.

### Document Duplication Issue

UNIVERSAL_SYSTEM_EVIDENCE.md has 8 DUPLICATED Part sections (14-17, 20-23
appear twice — once condensed, once detailed). Parts 9, 10, 18, 19 are absent
(correctly dropped per Codex disposition: "stale context" and "superseded").

---

---

## Part 27: ai_instruction Wire Break — Exact Code Path

### The smoking gun: probes CREATE ai_instruction, ralph NEVER READS it.

**Where ai_instruction IS created (works correctly):**
- 13 probes in dev/scripts/checks/probe_*.py each define AI_INSTRUCTIONS
  dicts mapping signal types to explicit fix guidance
- probe_concurrency.py lines 54-76: AI_INSTRUCTIONS dict with 13 entries
- probe_boolean_params.py lines 69-127: similar
- RiskHint dataclass (probe_bootstrap.py line 32) carries ai_instruction field
- finding_from_probe_hint() in finding_contracts.py line 291 correctly
  extracts ai_instruction from RiskHint into FindingRecord

**Where the wire BREAKS:**
- ralph_ai_fix.py line 56-66: load_backlog() ONLY reads backlog-medium.json
- backlog-medium.json comes from CodeRabbit's external triage
- Items contain: severity, category, summary — NO ai_instruction
- build_prompt() lines 120-124 constructs prompt from severity+category+summary
- NO reference to item.get('ai_instruction') anywhere in ralph_ai_fix.py

**What exists but is never called:**
- decision_packet_from_finding() in finding_contracts.py lines 298-325
- DecisionPacketRecord includes ai_instruction field
- ZERO callers anywhere in the codebase

**To connect the wire (4 options):**
1. Merge probe findings into CodeRabbit backlog with ai_instruction
2. Enrich backlog items from governance ledger before passing to ralph
3. Update ralph prompt builder to include ai_instruction
4. Replace backlog with DecisionPacketRecord (typed, with ai_instruction)

---

## Part 28: Session Handoff — Every Session Is Cold Start

### Verified: NO mechanism carries session context forward.

**What exists but doesn't work:**
- 19 plan files have ## Session Resume sections (markdown prose)
- has_session_resume boolean flag set in PlanRegistry — but NEVER READ
- Review channel handoff.json has resume_state — but NOT consumed by startup
- ReviewCurrentSessionState carries instruction/ACK — from bridge only
- AGENTS.md line 164-167 says "keep restart state in Session Resume"

**Why every session is cold:**
- has_session_resume is boolean detection only (line 147 of draft_governed_docs.py)
- ZERO code paths deserialize Session Resume content
- build_startup_context() reads git state, NOT prior session state
- No auto-population of Session Resume sections
- 5+ artifact trees with no unified handoff packet

**What would fix it:**
1. Parse ## Session Resume into typed SessionResumeState
2. Augment StartupContext with plan registry resume state
3. AI sessions load SessionContinuityPacket on bootstrap
4. rewrite_session_resume mutation handler (contract exists, handler missing)
5. Guard: plan Session Resume must be consistent with bridge instruction

---

## Part 29: Organization Guards — Confirmed Missing

### No guard enforces repo organization. Verified against all 65 guards.

**What exists:**
- check_package_layout.py — Python package structure, NOT repo organization
- check_markdown_metadata_header.py — metadata normalization, NOT coverage
- hygiene command — archive audit, scripts cleanup, process sweep, NOT org

**What does NOT exist:**
- Root .md file count enforcement
- Empty/zero-byte file detection
- Documentation existence validation (INDEX.md entries → actual files)
- Orphan file detection in governed directories
- Complete doc metadata coverage enforcement

**What check_repo_organization.py would need:**
1. Root .md count ≤ configurable limit
2. No files with 0 bytes (exclude .gitkeep)
3. All INDEX.md paths → files actually exist
4. All docs with execution markers → registered in INDEX.md
5. Required directories exist (dev/active, dev/config, dev/reports)
6. No files at wrong hierarchy level

**Integration: register in script_catalog.py + quality_policy_defaults.py,
add to bundle.tooling, auto-appears in check --profile ci.**

---

## Part 30: Code Quality Sweep — Production Ready

### Python codebase is clean. Zero blockers for universal use.

| Metric | Count | Assessment |
|--------|-------|-----------|
| TODO comments | 0 | CLEAN |
| HACK/FIXME | 1 | Minimal (config var name) |
| print() statements | 89 | UI layer only (common_io.py) |
| Star imports | 16 | All documented re-exports |
| Broad exceptions | 12 | ALL with recovery + documented reason |
| Hardcoded localhost | 0 | CLEAN |
| Files >1000 lines | 0 | CLEAN |
| Module docstrings | 478/478 | 100% |
| sleep() calls | 11 | All injectable/configurable |
| Test coverage | 192/478 files (40.2%) | Solid baseline |

**Production-ready strengths:**
- Zero hardcoded hosts/ports (fully portable)
- All exception handling documented with recovery paths
- Injected sleep_fn pattern (testable)
- 100% module docstrings
- Zero TODO sprawl

---

---

## Part 31: DecisionPacket System — Fully Typed, Never Used by AI

### Architecturally sound. Wired for human rendering. Zero AI consumption.

**What exists (fully implemented):**
- DecisionPacketRecord: typed packet with decision_mode (auto_apply /
  recommend_only / approval_required), rationale, invariants, validation_plan,
  precedent, ai_instruction, research_instruction
- DecisionPacketPolicy: governance metadata for allowlist entries
- decision_packet_from_finding(): creates packet from Finding + Policy
- Allowlist system (.probe-allowlist.json) marks findings as "design_decision"
- build_design_decision_packets(): creates packets from allowlist-filtered findings
- Full pipeline: probe → allowlist → packet → review_packet → markdown render

**Where it flows:**
- Probe report aggregation (review_probe_report.py line 257)
- Review packet builder (probe_topology_builder.py line 252)
- Markdown renderers (probe_topology_render.py line 60, decision_render.py)

**Where it DOESN'T flow:**
- Zero references in review_channel/ (no agent consumption)
- Zero references in autonomy/ (no loop consumption)
- Zero references in commands/guard_run.py (no fix-loop consumption)
- decision_mode is NEVER used to gate AI behavior
- "auto_apply" mode exists but no code acts on it
- "approval_required" mode exists but no approval gate exists

**The gap:** Human reviewers see decision packets in probe report markdown.
AI agents have zero awareness of them. The contracts that were DESIGNED to
tell AI "you can auto-fix this" vs "wait for approval" are rendered to
markdown for human eyes and ignored by the AI fix loops.

---

## Part 32: Authority Spine — 9/15 Concepts Implemented (60%)

### What the plans declare vs what code exists.

**IMPLEMENTED (9 types with real dataclasses):**
1. ProjectGovernance (project_governance_contract.py:209)
2. RepoPackRef (project_governance_contract.py:24) — reference only, not full pack
3. PlanRegistry (project_governance_contract.py:148)
4. PlanRegistryEntry (project_governance_contract.py:128)
5. TypedAction (action_contracts.py:18)
6. ActionResult (action_contracts.py:90)
7. RunRecord (action_contracts.py:29)
8. FindingRecord (finding_contracts.py:138)
9. ContextPack (Rust: memory/types.rs + Python: ContextPackRef)

**PLAN-ONLY (6 concepts with ZERO code):**
1. RepoPack (full config — only RepoPackRef exists)
2. PlanTargetRef (0 matches in codebase)
3. WorkIntakePacket (0 matches — mentioned 11 times in plans)
4. CollaborationSession (0 matches — mentioned 9 times in plans)
5. DocPolicy (exists in project_governance_contract.py:59 — ACTUALLY EXISTS)
6. DocRegistry (exists as part of PlanRegistry — PARTIALLY EXISTS)

**Corrected count: 11/15 have some code (73%), but the critical ROUTING
types (WorkIntakePacket, CollaborationSession, PlanTargetRef) are missing.
These are the ones that would carry AI fix guidance through the system.**

---

## Part 33: Bootstrap Cold-Start — What AI Actually Receives

### Traced the exact code path. 9 data sources checked.

**LOADED on bootstrap (what AI gets):**
- Repo identity (name, branch)
- Active plans (from INDEX.md: path, role, authority, scope)
- Hotspot files (top-10 by temperature — if probe artifacts < 6 hours old)
- Key commands (from governance policy)
- Deep links (AGENTS.md, MASTER_PLAN.md, INDEX.md, bridge.md)
- Push enforcement state
- Bridge liveness (boolean only)
- Probe hint counts + severity (if artifacts fresh)

**NOT LOADED (what AI doesn't get):**
- Prior session state (Session Resume sections never parsed)
- Prior guard failures (governance review log never loaded)
- Full probe findings (only hint counts, not details/names/confidence)
- Active finding list (finding_reviews.jsonl never loaded)
- Watchdog episode history (never loaded)
- Quality feedback scores (never loaded)
- Bridge instruction content (liveness checked, NOT instruction text)
- Open findings from bridge (NOT extracted)
- Last reviewed scope (NOT loaded)

**Critical cliff:** If probe artifacts are > 6 hours old
(ARTIFACT_INPUT_MAX_AGE), hint counts, changed paths, and severity all
become empty dicts. Temperature scores drop to baseline. Hotspot list
becomes less accurate. This happens SILENTLY — no warning to AI.

**CLAUDE.md vs reality:** CLAUDE.md line 30 says "read Current Instruction
For Claude" from bridge. The bootstrap CODE never loads this. Agent must
manually read bridge.md to discover the instruction. The bootstrap only
checks bridge LIVENESS (exists/doesn't), not CONTENT (what to do).

---

## Part 34: Test Coverage — 11% Overall (386 Untested Files)

### Comprehensive coverage matrix across all subsystems.

**Overall: 435 source files, 49 tested (11%)**

**By subsystem (worst gaps):**

| Subsystem | Source | Tests | Coverage |
|-----------|--------|-------|----------|
| commands | 93 | 0 | 0% |
| autonomy | 21 | 0 | 0% |
| triage | 12 | 0 | 0% |
| cli_parser | 10 | 0 | 0% |
| data_science | 7 | 0 | 0% |
| process_sweep | 7 | 0 | 0% |
| watchdog | 5 | 0 | 0% |
| quality_backlog | 5 | 0 | 0% |
| security | 5 | 0 | 0% |
| repo_packs | 4 | 0 | 0% |
| loops | 4 | 0 | 0% |
| platform | 15 | 1 | 7% |
| review_channel | 62 | 9 | 15% |
| context_graph | 11 | 4 | 36% |
| governance | 32 | 13 | 41% |
| runtime | 20 | 10 | 50% |

**19 of 24 subsystems have ZERO dedicated tests.**

**Guard coverage: 8 of 65 guards tested (12%)**
57 guards have no test verifying they catch what they claim to catch.

**Probe coverage: 4 of 28 probes tested (14%)**
24 probes have no test verifying their detection accuracy.

**Critical risk:** The governance system's foundation (guards + probes)
is 87% untested. If a guard silently stops catching violations after a
refactor, nothing detects it. This is the guard-testing-the-guards gap.

---

---

## Part 35: Guard-Run Is a Closed Loop (Corrects Earlier Finding)

### guard-run IS instrumented. The break is UPSTREAM, not in guard-run itself.

**What guard-run DOES (11-step flow):**
1. Captures pre-command git snapshot
2. Runs wrapped AI command in subprocess
3. Runs post-action hygiene (quick check or process cleanup)
4. Captures post-command git snapshot
5. Runs all 14 probes as quality scan
6. Emits GuardedCodingEpisode (56-field typed record)
7. Persists to episodes JSONL + per-episode JSON
8. Feeds probe_scan result back to autonomy-loop checkpoint
9. Autonomy-loop reads checkpoint and decides retry/stop
10. Metrics aggregate success_rate, avg_escaped_findings
11. Feedback sizing adapts agent count (stall→downshift, improve→upshift)

**What guard-run does NOT do:**
- Decide whether to retry (autonomy-loop owns this)
- Revert changes on failure (captured, not reverted)
- Route ai_instruction to AI (this is the upstream break)

**Corrected understanding:** The fix loop IS closed at the guard-run/autonomy
level. The break is that FINDINGS with ai_instruction never reach the AI's
PROMPT. Guard-run captures everything — the prompt builder never reads it.

**Fail-open risk:** Probe scan crashes are silently swallowed (by design,
with comment: "probe scan must fail open"). If probe scan fails, autonomy
continues without knowing about HIGH-severity escaped findings.

---

## Part 36: Error Handling — Inconsistent Across Command Layer

### 93 command files with no tests and inconsistent error patterns.

**Good patterns (follow these):**
- Governance commands: shared render_governance_value_error() helper, catches
  ValueError, returns exit code 2
- Review-channel: nested fallback chains with explicit error propagation
- Guard-run: captures all outcomes in JSON report, fail-open on subsystems

**Bad patterns (fix these):**
- cli.py main(): NO top-level exception handler. If any command raises
  uncaught exception, user sees raw Python traceback
- check.py: only catches RuntimeError. OSError, PermissionError,
  subprocess.CalledProcessError all crash to traceback
- autonomy_loop.py: ZERO outer exception wrapping. Policy loading,
  mode resolution, branch validation all unprotected
- Parallel check execution: worker thread crash can silently mask failures

**Missing:**
- No shared error-formatting module for all commands
- No standardized exit codes (1=logical failure, 2=input error)
- No structured JSON error output for crashed commands
- No test for any error path in any command

**Recommendation:** Add top-level try/except in cli.py main(), expand
check.py to catch (OSError, RuntimeError, ValueError, CalledProcessError),
wrap autonomy_loop.py with outer error handling.

---

## Part 37: Integration Testing Gap

### Unit tests exist (198 files). Integration tests are CI-only.

**What exists:**
- 198 test files with ~55K LOC in dev/scripts/devctl/tests/
- CI workflows serve as de facto integration tests (30 workflows)
- tooling_control_plane.yml runs real devctl commands (list, render-surfaces,
  ship --dry-run)
- Specialized behavioral tests (wake_word_guard, memory_guard, perf_smoke)

**What's missing:**
- No LOCAL integration test suite a developer can run pre-push
- No test that runs `devctl check --profile ci` on a real repo
- No test verifying guard → finding → report → AI flow end-to-end
- No test spawning devctl as subprocess validating exit codes + output
- No real repo fixture (all tests use mocks)
- No test for "does context-graph --mode bootstrap return valid JSON?"

**Impact:** Developers must push to GitHub to discover integration failures.
If CI is slow (tooling_control_plane = 30-40 min), feedback cycle is long.

---

## Part 38: 16 Disconnected Wires — Functions/Fields/Data Never Used

### Comprehensive inventory of typed contracts that exist but aren't consumed.

**CRITICAL: 8 AI guidance fields generated but never read by AI:**
1. ai_instruction (FindingRecord) — probes write it, ralph never reads it
2. ai_instruction (DecisionPacketRecord) — same disconnect
3. research_instruction — defined, serialized, never parsed
4. precedent — defined, rendered in markdown, never queried
5. invariants — defined, rendered in markdown, never enforced
6. validation_plan — defined, rendered in markdown, never executed
7. decision_mode (auto_apply/recommend_only/approval_required) — no code
   branches on this value. Designed to gate AI behavior, never used.
8. signals tuple — carried through pipeline, never analyzed

**HIGH: 6 configuration fields defined but never consulted:**
9. command_routing_defaults (ProjectGovernance) — serialized, never read
10. workflow_profiles (ProjectGovernance) — always empty tuple
11. startup_order (ProjectGovernance) — report-only, never used for
    actual startup sequencing
12. canonical_consumer (DocRegistryEntry) — tracking only, no enforcement
13. registry_managed (DocRegistryEntry) — tracking only, no enforcement
14. startup_order in startup_authority_contract — checked for existence,
    never used to ORDER anything

**MEDIUM: 4 data sinks written but never queried:**
15. dev/reports/integration_import_audit.jsonl — append-only, 0 readers
16. dev/reports/governance/finding_reviews.jsonl — read by data_science
    only for post-hoc analysis, never live decision routing
17. dev/reports/autonomy/queue/ — research/reporting only
18. dev/reports/autonomy/watchdog/ — research/reporting only

**Root cause:** Platform contracts were designed with rich AI guidance
fields (invariants, validation_plan, precedent, research_instruction).
The autonomy loops were built to capture findings and emit episodes.
But the BRIDGE between them — routing contract guidance INTO AI
prompts — was never built. The contracts produce. The loops consume.
Nothing connects production to consumption.

---

---

## Part 39: Governance Review Pipeline — Open Loop

### governance-review --record has ZERO automated callers.

110 entries in finding_reviews.jsonl were ALL manually recorded. No guard,
no autonomy loop, no guard-run, no triage command EVER invokes
governance-review --record. The governance review pipeline is:

**Current:** Finding → Detection → Fix → Verification → STOP
**Missing:** → Auto-record verdict ("fixed"/"waived"/"deferred") → Log

When guard-run wraps an AI fix and post-checks pass, NOTHING records
"this finding was fixed." When autonomy-loop completes a round, NOTHING
records verdicts. quality-feedback reads the review log to compute
cleanup_rate but can't trigger recording.

AGENTS.md lines 168-172 acknowledge governance-review exists for "manual
adjudication" but provide no guidance on auto-triggering.

**Impact:** cleanup_rate metrics are frozen at whatever was manually
adjudicated. System cannot track resolution rates automatically.

---

## Part 40: Code Organization Debt — 79 Root Files Need Grouping

### devctl/ has 79 files at root (should be ~20-25).

**9 feature domains have orphaned root files:**
- 8 governance_* files → should be in governance/
- 7 mobile/phone files → need new mobile/ subdir
- 5 status/ralph files → need new status/ subdir
- 3 loop files → should be in loops/
- 2 mutation_loop files → should be in mutation_loop/
- 2 publication files → should be in publication/
- 2 probe_report files → should be in probe_report/

**checks/ has 8 backward-compat shim probes** that duplicate
code_shape_probes/ implementations. Shims expire 2026-06-30.

**65 guard scripts at checks/ root** with no semantic grouping. Should
split into: architecture/, platform_contract/, code_shape/,
python/, rust/, data_sync/, compatibility/, foundational/.

**Cleanup effort:** ~7.5 hours total (3.5h safe migrations + 4h guard reorg).

---

## Part 41: First-User Adoption — tandem-consistency Is the Blocker

### A developer at another company trying to adopt this system will fail
### on Day 2 because tandem-consistency-guard ALWAYS runs and requires
### bridge.md + review-channel infrastructure.

**What works on day 1:**
- governance-bootstrap generates correct starter policy
- Portable presets (Python/Rust) have 15 guards + 17 probes that work
- docs-check, probe-report, quality-policy, platform-contracts all work
- Code-quality guards run fine on any Python/Rust codebase

**What fails on day 2:**
```
$ devctl check --profile quick
[FAIL] tandem-consistency-guard: Overall bridge state is stale.
```

tandem-consistency-guard is marked ALWAYS ON in quality policy. It checks:
- bridge.md presence and freshness
- Reviewer/implementer heartbeat
- Plan alignment with MASTER_PLAN.md
- Promotion state

**A Go project or any repo without bridge.md cannot pass check --profile
quick.** The adopter must either:
- (a) Create bridge.md + adopt full dual-agent review (1-3 days)
- (b) Edit policy to disable tandem-consistency (15 min, tech debt)
- (c) Fork the check command (not recommended)

**This is not documented in the setup guide.** The guide says "run check
--profile quick" as a next step but doesn't mention it will fail without
review infrastructure.

**Error message is confusing:**
```
[FAIL] launch_truth (role=system): Overall bridge state is stale.
```
A new adopter doesn't know what "launch truth" or "bridge state" means.

**Time to check --profile quick passing:**
- 1 day if adopter disables tandem-consistency
- 3-5 days if adopter commits to full review-channel setup
- tandem-consistency-guard is THE portability blocker

**Other adoption friction:**
- Docs layout assumes AGENTS.md + dev/guides/DEVELOPMENT.md at specific
  paths (fallbacks exist but not documented)
- Plan format is rigid (PLAN_FORMAT.md contract enforced, no alternatives)
- VoiceTerm jargon in error messages (bridge, launch_truth, tandem)
- No Go/TypeScript/Java language guards (honest but limiting)

---

---

## Part 42: AI Gets ZERO Data From 6 Major Report Sources

### Every prompt builder uses only static graph data or backlog items.
### NONE read dynamic quality/failure/governance data.

| Data Source | Written By | AI Sees It? | Contains |
|-------------|-----------|-------------|----------|
| review_packet.json | probe-report | **NEVER** | Hotspots, severity, priority scores, ai_instruction, connected files |
| review_summary.json | governance-review | **NEVER** | Cleanup rates, FP rates, verdict stats |
| finding_reviews.jsonl | governance-review | **NEVER** | 110 verdicts with notes, cleanup history |
| watchdog episodes | guard-run | **NEVER** | Retry counts, escaped findings, time-to-green |
| data_science summary | data-science | **NEVER** | Command success rates, execution stats |
| orchestrate-watch-end | orchestrate | **NEVER** | Queue status, agent states |

**All 6 prompt builders** (bootstrap, conductor, swarm, Ralph, loop packet,
escalation) use ONLY the context-graph escalation module, which returns a
bounded ~1200 char packet of matched node labels. None read the rich
operational data in dev/reports/.

**Impact:** AI makes fix decisions without knowing: which files are hottest
(review_packet), which guards have high FP rates (finding_reviews), what
failed in prior rounds (episodes), or which commands are reliable
(data_science). All this data EXISTS and is FRESH — just not routed.

---

## Part 43: ZGraph Is 13% Connected (20 of 150+ Planned Features)

### The graph infrastructure exists but is used ONLY for discovery, not decisions.

**What's built (7 node types, 5 edge types):**
- Source files, plans, guards, probes, commands, guides, concepts
- Imports, routes_to, documented_by, contains, related_to

**What's defined but DEAD CODE (2 edge types):**
- EDGE_KIND_GUARDS — would represent "this guard checks this file" — NEVER CREATED
- EDGE_KIND_SCOPED_BY — would represent "scoped by this plan" — NEVER CREATED

**What's MISSING entirely:**
- Test nodes (1098 tests not in graph)
- Workflow nodes (30 CI workflows not in graph)
- Config nodes (policy files not in graph)
- Contract/schema nodes (platform contracts not in graph)
- Finding/evidence nodes (probe output not in graph)

**Who USES the graph (6 consumers, all escalation-only):**
- review_channel/event_projection_context.py → escalation only
- review_channel/promotion.py → escalation only
- autonomy/run_helpers.py → escalation only
- commands/packets/loop_packet_context.py → escalation only
- commands/loop_packet_helpers.py → escalation only
- coderabbit/ralph_ai_fix.py → escalation only

**Who SHOULD use the graph but DOESN'T:**
- Autonomy system (0 graph usage — doesn't ask "what's related?")
- Startup context (0 graph usage — reads git diff, not graph)
- Guards (0 graph usage — 64 independent checkers, no shared context)
- Probes (0 graph usage — flat output, not prioritized by temperature)
- Operator console (0 graph usage — reads flat JSON reports)
- Review-channel core (escalation only, no routing decisions)

**Plans describe:** "typed relation families, staged query filtering,
bounded multi-hop inference, deterministic context router for
command goal + changed scope"

**Reality:** 1-hop substring matching, escalation packets only, no
decision routing, no guard skip logic, no temperature-driven prioritization.

**Connectivity score: ~13%** (20 of 150+ planned integration points)

---

## Part 44: Developer Experience — Information Exists But Isn't Accessible

### 5 critical developer-facing gaps.

**1. No `devctl guard-explain <name>` command**
When check fails, developer must read Python source + policy config to
understand why. No quick reference for "what does this guard enforce and
how do I fix my violation?" Slows first violation by 30-60 minutes.

**2. No `devctl which-tests <file>` command**
Developer can't answer "what tests should I run after editing foo.py?"
Must manually grep test directories. Context-graph has import edges but
doesn't surface test→source mapping.

**3. `devctl list` shows 81 commands with ZERO descriptions**
Most powerful commands (context-graph, platform-contracts, governance-draft)
are invisible. No categorization, no "recommended for common tasks" section.

**4. Check output shows "passed: 6, failed: 1" but NOT which checks passed**
No per-check status line, no timing per guard. Developer can't identify
slow guards or see incremental progress.

**5. No incremental check command**
No `devctl check-delta` that runs only guards affected by changed files.
check-router does this internally but doesn't expose "what would be checked"
as user-facing output.

### What developers DON'T know exists (but should)
- `context-graph --query <file>` — shows all plans, guards, imports for a file
- `probe-report --format md` — has the BEST remediation guidance in the system
- `quality-policy --format md` — reveals all active guards and probes
- `platform-contracts --format md` — shows the shared platform blueprint
- `check-router --dry-run` — shows exactly what will run before it runs

The information EXISTS. It's just not DISCOVERABLE.

---

---

## Part 45: Complete Data-Produced-Never-Consumed Inventory

### 7 artifact categories written but never consumed for decisions.

1. **DecisionPacket metadata** (research_instruction, precedent, invariants,
   validation_plan) — written to JSON, never read back after serialization
2. **QualityFeedback recommendations** — recommendation_engine builds 100+
   lines of prioritized recommendations. quality_feedback command just counts
   them (len(snapshot.recommendations)). NEVER RENDERED or acted upon.
3. **Research benchmark bundles** (dev/reports/research/) — 500+ JSON/MD files
   from swarm_vs_placebo experiments. No non-test code opens them.
4. **Data science / watchdog snapshots** — consumed only by operator console
   presentation layer. NEVER used for control decisions.
5. **Ralph guardrail reports** — displayed in operator console. NEVER
   re-analyzed or used to trigger automations.
6. **Audit event log** (devctl_events.jsonl, 13K+ events) — only consumed
   by test suite. NEVER queried for operational patterns.
7. **Review channel event trace** (NDJSON) — used for projections only.
   NEVER analyzed for session patterns or decision quality.

**Pattern:** Every reporting subsystem WRITES rich data and then only
the presentation layer (operator console, markdown render) ever READS it.
No decision system, no AI prompt builder, no guard, no autonomy loop
ever consumes this data for actual choices.

---

## Part 46: Four Separate Startup Systems (Should Be One)

### AI gets context from 4 uncoordinated systems that don't know about each other.

**System 1: startup-context** (10K tokens, undocumented in CLAUDE.md)
- Loads: ProjectGovernance, ReviewerGateState, PushEnforcement, advisory action
- Hidden from AI: CLAUDE.md bootstrap NEVER mentions this command

**System 2: context-graph bootstrap** (1.3K tokens, documented in CLAUDE.md)
- Loads: repo identity, active plans, hotspots, commands, push state, bridge liveness
- This is the ONLY system CLAUDE.md tells AI to use

**System 3: Claude memory** (.claude/projects/memory/, 12 files)
- Contains: repo facts, architecture, lessons, preferences, active execution notes
- Integration: ZERO — devctl never reads .claude/memory/. Not one import.

**System 4: Plan doc Session Resume** (manual markdown in dev/active/*.md)
- Contains: current status, next action, context for session restart
- Integration: boolean detection only (has_session_resume flag). Content NEVER parsed.

**Overlap:** startup-context and bootstrap both carry push_enforcement (different fields).
**Gaps:** Neither reads memory. Neither parses Session Resume content. Neither loads
prior episode history. Neither knows about the other.

**Result:** AI gets 1.3K tokens from bootstrap. 10K more tokens from startup-context
are available but invisible. Memory is decoupled by design. Session Resume is prose.
An AI session starts with ~1.3K when ~15K of context exists across the 4 systems.

**What a unified startup would look like (~3-5K tokens):**
- repo_identity (from startup)
- governance + push_enforcement (from startup, more detailed)
- active_plans + hotspots (from bootstrap)
- key_commands (from bootstrap)
- recent_changes (NEW: git diff + plan edits since last session)
- memory_state (NEW: load from .claude/projects/)
- session_resume (NEW: parse from plan docs)
- prior_episode_digest (NEW: load from watchdog episodes)
- advisory_action (from startup)

---

## Part 47: ZGraph Missing 5 Node Types + 2 Dead Edge Types

### Complete inventory of what the graph schema SHOULD have.

**Dead edges (defined in models.py, never created by builder.py):**
- EDGE_KIND_GUARDS — would map guard → files it validates. Data exists
  (quality_scopes in repo_policy, PATH_POLICY_OVERRIDES in code_shape_policy).
  Builder change: ~80 lines. HIGHEST priority — unlocks "what guards protect
  this file?"
- EDGE_KIND_SCOPED_BY — would map task/finding → plan scope. Data exists
  (INDEX.md scope column already parsed into metadata). Builder change: ~60
  lines. Unlocks plan-scope task routing.

**Missing node types (data exists, nodes don't):**
- Test nodes (~120 test files) — would enable "which tests cover this file?"
  Builder change: ~200 lines.
- Workflow nodes (30 CI workflows) — would enable "what CI checks fire for
  this change?" Builder change: ~200 lines.
- Config nodes (10+ policy files) — would enable "what happens if I change
  this policy?" Builder change: ~150 lines.
- Finding nodes (81 live findings) — would enable "which findings are blocking
  this plan?" Builder change: ~180 lines.
- Contract nodes (35+ platform contracts) — would enable "which contracts does
  this file implement?" Builder change: ~200 lines. CRITICAL for MP-377
  extraction.

**Quick wins (Tier 1, ~160 lines total):**
1. Parse plan scope metadata via regex (20 lines)
2. Add guard applicability helper function (60 lines)
3. Create EDGE_KIND_GUARDS edges in builder (80 lines)

**Total to build ALL missing types: ~1400-1600 lines of Python.**

---

## Part 48: Memory + Session Resume + Execution Traces Are Three Disconnected Silos

### Every session starts cold. Prior learning is invisible. Continuation is manual.

**The broken continuity loop:**
```
Session N starts → reads bridge NOW → makes decision NOW
  (does NOT query episodes from N-1..N-5)
  (does NOT read Session Resume from plan)
  (does NOT read MEMORY.md)

Session N runs → emits episodes to watchdog
  → updates bridge prose
  → agent manually writes Session Resume
  → user manually updates memory

Session N+1 starts → reads bridge NOW
  → makes SAME decision (no learning)
  → no access to episode(N) data
  → no typed Session Resume
```

**Key disconnections:**
- devctl NEVER reads .claude/memory/ (0 imports found)
- startup_context is stateless across sessions (reads NOW only)
- Episodes archived but never queried for bootstrap
- 3 separate session_id systems with no unified registry
- Handoff carries bridge state only, not episode data or learned patterns
- Session Resume never auto-populated, never auto-read

**What would fix it (6 incremental additions):**
1. Typed Session Resume — parse markdown into struct at startup
2. Episode aggregator — query JSONL by plan_id, return digest
3. Continuity packet — combine resume + digest + bridge liveness
4. Handoff enrichment — include episode digest in rollover bundles
5. Memory integration — auto-populate from episode digest
6. Guard confidence scoring — track FP rates, carry into next session

---

---

## Part 49: MCP Server Is the Agent-Agnostic Integration Layer

### Claude memory can integrate with ZGraph WITHOUT locking into Claude-only.

**Claude Code memory architecture (2 parts):**
- CLAUDE.md: operator-written instructions loaded at session start
- MEMORY.md: auto-saved observations (~every 5K tokens), first 200 lines
  injected into next session. Located at .claude/projects/<path>/memory/

**Integration surfaces (3 options, ordered by strategic value):**

1. **SessionStart Hook (Claude-only, simplest):**
   Run `devctl context-graph --mode bootstrap` automatically on session
   start via .claude/hooks.json. Replaces manual "step 1 in CLAUDE.md."
   Zero effort. But Claude-only — doesn't help Codex/Cursor/Gemini.

2. **MCP Server (agent-agnostic, strategic):**
   Build devctl-mcp server exposing ZGraph tools:
   - zgraph_query(term) — returns relevant subgraph nodes
   - governance_state() — returns StartupContext packet
   - plan_status(mp_id) — returns MP execution state
   - guard_results(profile) — returns latest check results
   - memory_sync(observations) — accepts session learnings back

   Works with: Claude Code, Cursor, Codex, Gemini CLI, Copilot, and any
   future MCP-capable agent. The existing context_graph/ module (builder,
   query, render, models) is 80% of what an MCP server needs internally.
   Gap is purely the MCP transport adapter.

   MCP Tool Search enables lazy loading — full ZGraph toolset costs
   near-zero tokens until actually invoked.

3. **Bidirectional Memory Bridge (most powerful):**
   ZGraph feeds INTO Claude's memory (SessionStart hook injects governance
   state). Claude's memory feeds BACK into ZGraph (SessionEnd hook exports
   learnings as observations). Creates learning loop: governance teaches
   agents → agents discover patterns → discoveries flow back.

**Agent-agnostic comparison:**

| Integration | Claude | Codex | Cursor | Gemini |
|-------------|--------|-------|--------|--------|
| SessionStart hooks | YES | NO | NO | NO |
| .claude/rules/ | YES | NO | NO | NO |
| AGENTS.md | YES | YES | YES | YES |
| MCP server | YES | YES | YES | YES |

**Recommendation:** MCP as primary (agent-agnostic), with thin Claude
adapters (hooks, rules) for Claude-optimized startup speed. AGENTS.md
remains cross-agent instruction surface. This doesn't lock into Claude.

**Existing infrastructure:** Engram (agent-agnostic memory, Go binary +
SQLite + FTS5) already works as MCP server for Claude/Cursor/Codex/Gemini.
92% accuracy on DMR benchmark using 96.6% fewer tokens than full context.

---

## Part 50: Implementation Paths for First 3 Fixes

### Exact files, functions, and line counts for each fix.

**Fix 1: Wire ai_instruction into ralph prompts (~100 lines)**
- Modify: ralph_ai_fix.py (add load_probe_findings(), modify build_prompt())
- Read from: dev/reports/probes/latest/review_packet.json → hotspots →
  representative_hints → ai_instruction
- Blocker: need CodeRabbit→probe finding mapper (file+symbol match)
- Tests: 2 new methods in test_ralph_ai_fix.py

**Fix 2: Create EDGE_KIND_GUARDS edges (~80 lines)**
- Modify: builder.py (add _collect_guard_governance_edges())
- Data: quality_policy scopes (python_guard_roots, rust_guard_roots)
- Blocker: guard→file mapping is implicit (language-based), needs
  optional guard_scope_overrides in repo policy
- Circular import risk: builder → quality_policy (use local import)

**Fix 3: Add guard-explain command (~500 lines, 4 new files)**
- Create: guard_explain.py, guard_explain_support.py,
  guard_explain_registry.py, guard_explain_parser.py
- Modify: cli.py (3 lines), quality_policy.py (optional 15 lines)
- Data: scattered across docstrings + code_shape_policy + guard configs
- Pattern: follow platform-contracts command structure
- Tests: 4 methods in new test_guard_explain.py

**Recommended order:** #3 first (lowest risk, no deps), then #2 (needs
scope formalization), then #1 (needs guard ai_instruction field decision).

**Total: 7 files, ~680 lines, 7-8 test methods, 3 design decisions.**

---

## Part 51: Parts 42-48 Integration Verified

All 7 parts confirmed integrated into plan docs:
- Part 42: ai_governance_platform.md:3340 (operational data routing)
- Part 43: ai_governance_platform.md:3056 (graph edges/nodes)
- Part 44: portable_code_governance.md:280 (dev experience)
- Part 45: ai_governance_platform.md:3335 (write-only artifacts)
- Part 46: platform_authority_loop.md:221 (unified startup)
- Part 47: ai_governance_platform.md:3049 (missing node types)
- Part 48: platform_authority_loop.md:757 (session continuity)

Parts 25-41 spot-checked — all intact.
4 evidence files intact at root.
No new plan docs created.

---

## Authority Rule (Repeated)

This file is reference-only. Canonical execution authority remains:
1. dev/active/MASTER_PLAN.md
2. dev/active/ai_governance_platform.md
3. dev/active/platform_authority_loop.md
4. dev/active/portable_code_governance.md
5. dev/active/review_probes.md

Do not use this file as a tracker. Promote accepted items into tracked docs.
