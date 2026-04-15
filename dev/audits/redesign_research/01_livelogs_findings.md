# LIVE_RUN.md Synthesis: Q1–Q100 Categorization for Repo-Wide Redesign

## Summary counts by category × status

| Category | OPEN | PARTIAL/HOTFIXED | FIXED | SUPERSEDED | Total |
|---|---|---|---|---|---|
| **drift-lockout** | 8 | 1 | 1 | 0 | 10 |
| **bridge-prose** | 11 | 0 | 0 | 0 | 11 |
| **typed-state-lies** | 7 | 1 | 0 | 0 | 8 |
| **role-topology** | 6 | 0 | 0 | 0 | 6 |
| **authority-scatter** | 9 | 0 | 0 | 1 | 10 |
| **emitted-not-consumed** | 12 | 1 | 0 | 0 | 13 |
| **gate-deadlock** | 8 | 0 | 0 | 0 | 8 |
| **dogfood-coverage** | 6 | 0 | 0 | 0 | 6 |
| **dashboard-contract** | 8 | 0 | 0 | 0 | 8 |
| **other** | 6 | 0 | 0 | 0 | 6 |
| **TOTALS** | 81 | 3 | 1 | 1 | 86 |

## Open findings grouped by category

### drift-lockout (self-invalidating approval loops, commit-pipeline races)
- **Q100** — Commit pipeline self-invalidates approval via shared `attention_revision` (structural)
- **Q41** — `devctl commit` + `devctl push` trigger `process-sweep-post` reaping live conductors
- **Q39** — Reviewer loop blocks when conductors die (stale heartbeat gates all commits)
- **Q38** — Uncommitted work lost when conductors die silently
- **Q33** — `receipt-commit` deadlock: cannot succeed while publisher is live
- **Q32** — Headless launch still blocked after Q4 tactical revert
- **Q4** — `operator_interaction_mode` hardcoded constant (roots remote_control failure)
- **Q1** — `devctl commit` self-blocks via `check --profile quick` (PARTIAL via Q1-FIXED tactical bypass)

### bridge-prose (bridge.md sync, parser gaps, generated files)
- **Q92-C** — Dashboard render layer misreads bridge prose (6 HIGH + 2 MEDIUM)
- **Q92-B** — Bridge parser layer (10 findings: markdown sections parsed as bare `str`)
- **Q92-A** — Startup coordination read model (6 HIGH findings, bridge projection stale)
- **Q89** — Codex's `broad-except: allow` comments are repo guard contract, not prose
- **Q87** — `contract_nodes.py` is smart-but-transitional; authority source leaks shadow schema
- **Q84** — `context-graph` now resolves contracts but consumer visibility still open
- **Q7** — `review-channel status` JSON and `bridge.md` disagree on `last_codex_poll_utc` by 36 min
- **Q3** — Dashboard projection shows wrong-file code_shape failures (F1 instance)
- **Q85** — State surfaces contradict at field level; same contract contradicts itself
- **Q83** — Four state surfaces disagree on state vocabulary for "implementation blocked?"
- **Q29** — Push preflight fails on stale `commit_pipeline.json` until manual refresh

### typed-state-lies (fields populated but unverified, phantom PIDs, stale claims)
- **Q61** — `claude_conductor_active` reports True after PID killed 5 min ago
- **Q51** — Update cadence drift: surfaces refresh on different schedules
- **Q45** — Activity data under `bridge_liveness.*` despite name implying "is bridge alive"
- **Q43** — Publisher survives 4+ conductor generations with no session identity tracking
- **Q37** — Headless conductor pair runs unsupervised; `process-cleanup` reports 0 orphans
- **Q35** — `reviewer_mode` and `effective_reviewer_mode` silently diverge
- **Q12** — Packet deserialization drops typed hydration (dict vs ReviewPacketState)
- **Q11** — `review-channel status` AttributeError on dict-shaped packets (HOTFIXED)

### role-topology (single vs dual-agent, reviewer/implementer dispatch, role gaps)
- **Q57** — `--claude-workers 0` flag is a no-op on `review-channel launch`
- **Q53** — Bootstrap guidance missing: system doesn't teach AI agents which commands to run
- **Q46** — Governance only activates for dual-agent mode, not all modes of use
- **Q31** — Role drift: Claude-Code wrote fixes (Q1, Q18, Q30) that should be implementer work
- **Q2** — `check --profile quick` reaps live conductor shells (kills review loops)
- **Q9** — Mode promotion decoupled from supervisor liveness (state-machine contract violation)

### authority-scatter (multiple overlapping sources of truth)
- **Q77** — Scatter quantified: contract_connectivity unchanged at 130/69/20 baseline noisy
- **Q75** — RecoveryAuthorityState exported but not authoritative
- **Q70** — `action_routing` still depends on parallel coordination truth
- **Q65** — Systems not properly connected: duplication, orphaned contracts, parallel hierarchies
- **Q56** — Q54+Q55 compose from existing systems, minimal changes needed
- **Q55** — Authority-lane split: multiple read paths for coordination state, no canonical reader
- **Q20** — Packet transport `inbox`/`history` mismatch; 7 of 12 packets missing
- **Q17** — Adding `dev/audits/*.md` routes commit to `bundle.docs` instead of `bundle.tooling`
- **Q16** — `dev/reports/` gitignored; shared-with-reviewer pattern broken
- **Q23-legacy** — SUPERSEDED by Q23 (context graph missing plans → stale snapshot)

### emitted-not-consumed (typed contracts produced, no consumer reads them)
- **Q80** — "emitted-but-not-consumed" is a nameable pattern; guard system should detect it
- **Q79** — `autonomy-run` has no import edge to findings-priority, session pacing, recovery authority
- **Q78** — `context-graph` blind to typed-contract consumers (file-level import graph only)
- **Q76** — Q71/Q73/Q75 remain unconsumed at HEAD; Q70 only closed one downstream
- **Q73** — `findings-priority` has no consuming controller
- **Q71** — `session_pacing` emitted but not enforced
- **Q68** — `devctl push` detects itself as orphaned when backgrounded
- **Q67** — `check_contract_connectivity` guard too weak: misses known problems
- **Q66** — Hygiene guard blocks push on intentional Codex sessions
- **Q64** — Agent exhausts context on research before writing code
- **Q52** — AI agents don't know what's in typed state they're consuming (TOP-LEVEL FAILURE)
- **Q22** — `devctl discover --format md` crashes with KeyError
- **Q59** — UX: human-facing output dumps raw internal fields, conflicting terms

### gate-deadlock (startup/launch/commit gates blocking each other)
- **Q72** — `contract_connectivity` baseline too noisy for architectural decisions
- **Q69** — SUPERSEDED by Q74; autonomous governance loop design rejected by Codex
- **Q62** — Error system too coarse: `attention.status` doesn't distinguish severity
- **Q58** — Registry exists but is not sovereign dispatcher
- **Q40** — `check_tandem_consistency` blocks ALL commits when conductors die
- **Q13** — Governance does not auto-commit / auto-push in `remote_control` mode
- **Q8** — `reviewer-heartbeat` `auto_start` refuses `manual_stop` supervisor with no override
- **Q5** — `review-channel launch` reports false-negative timeout (launch succeeded)

### dogfood-coverage (commands unexercised, roles with 0 rows)
- **Q97** — Loop integration plan phase checklist
- **Q96** — Fix direction: unify two roots (three options analyzed)
- **Q95** — Q76-Q80 unpack into concrete implementation tasks
- **Q94** — Standalone quick-win (does NOT depend on Q95-Q97)
- **Q90** — Dashboard blindness: 5 ticks read "idle" when Codex marked TASK COMPLETE 37 min earlier
- **Q88** — `_EXTRA_DISCOVERY_CONTRACTS` exists; `shared_contracts()` missing three targets

### dashboard-contract (dashboard projection disagrees with reality)
- **Q86** — Q78 implementation review: transitional; authority source leaks shadow schema
- **Q82** — Q-ID collisions between LIVE_RUN.md and autonomous_governance_loop_v2.md
- **Q81** — Concrete Q76-Q80 evidence mapped onto loop v2 Phase checklist
- **Q74** — Autonomous governance loop should extend autonomy-run, not add verdict-file controller
- **Q63** — Dashboard operator committed without running full guard stack
- **Q60** — Guards run after coding, not during (missed live feedback opportunity)
- **Q50** — Claude-Code's dashboard used 5 fields of 200+ available
- **Q49** — Publisher daemon died silently during session

### other (6 findings)
- **Q27** — 19 doc budget violations + 10 consolidation candidates invisible outside `doc-authority`
- **Q26** — `doc-authority` lifecycle classifier fails on 26 of 27 non-index docs
- **Q25** — `git diff --name-only` and `orchestrate-status` disagree on changed file count
- **Q24** — Many diagnostic commands silently return empty when upstream producer isn't running
- **Q18** — `docs-check` in push-preflight vs standalone give different results
- **Q6** — `review-channel doctor` emits no `recommended_command` (operator ergonomics)
- **Q19** — `review-channel launch` JSON returns `launched: false` after spawning processes
- **Q15** — `devctl push --format json` emits preflight markdown to stdout (unparseable)
- **Q14** — Publisher daemon ignores `SIGINT`/`SIGTERM` through 30s grace
- **Q10** — `reviewer_supervisor_running` flag possibly dead code (undocumented contract)

## Top 10 highest-recurrence architectural themes

1. **Typed-state discovery failure** (Q52, Q22, Q20, Q50, Q78, Q79, Q80, Q90)
   — AI agents and dashboards do not enumerate or honor the 200+ available typed fields; system produces contracts nobody reads

2. **Approval/commit self-invalidation races** (Q100, Q41, Q39, Q38, Q33, Q32)
   — Commit pipeline, guard bundles, and concurrent state mutations lock each other; no atomic approval-to-record window

3. **Authority scattered across read paths** (Q55, Q7, Q85, Q83, Q92, Q29)
   — Bridge prose, JSON status, dashboard projections, poll timestamps disagree on same field; no canonical reader

4. **Bridge.md prose as fallback source of truth** (Q92-A/B/C, Q87, Q89, Q84)
   — Typed contracts exist but are under-consumed; bridge markdown re-introduces the untyped-prose governance this thesis rejects

5. **Role topology not enforced** (Q31, Q53, Q57, Q46, Q9, Q2)
   — Single-agent vs dual-agent, reviewer vs implementer, mode-promotion coupling all lack typed contracts or dispatch logic

6. **Conductor/publisher lifecycle unsupervised** (Q41, Q43, Q37, Q61, Q49)
   — Multi-generation process survival, phantom PIDs in state, silent deaths with no recovery signal

7. **Gate deadlock on conductor health** (Q40, Q39, Q38, Q13, Q8, Q5)
   — Commit gates block on supervisor heartbeat stale; cannot commit docs or push while conductors recover

8. **Emitted-but-not-consumed contracts** (Q80, Q79, Q78, Q76, Q73, Q71)
   — Contract system produces findings-priority, session-pacing, recovery-authority, autonomy-run edges with no route to consumer

9. **Cadence and freshness drift** (Q51, Q35, Q24, Q25, Q45)
   — Multiple surfaces refresh on different schedules; agents read same file at same instant and see different values

10. **Dashboard laziness compounds ignorance** (Q50, Q90, Q52, Q46)
    — Dashboard templates lock to 5 fields via CronCreate; reduced visibility → reduced situational awareness → worse decision-making

## Explicit interdependencies

**Q-ID Chains (depends-on edges)**:
- Q100 depends on Q41 (conductor reaping triggers commit invalidation)
- Q41 depends on Q2 (process-sweep reaps shells)
- Q52 (meta-root) precedes Q22, Q20, F1 in Research Lane priority
- Q78 blocks Q79, Q80 (graph must resolve consumers before pipeline audits)
- Q97 integrates Q76–Q80 via loop v2 Phase checklist
- Q94 is standalone (no deps on Q95, Q96, Q97)
- Q87 extends Q78 (discoverability + implementation review)
- Q89 validates Q87 verdict (broad-except guards are repo-owned)
- Q84 depends on Q78 (graph now resolves contracts; visibility still open)

**Supersede edges**:
- Q69 SUPERSEDED by Q74 (autonomous governance loop design rejected)
- Q23-legacy SUPERSEDED by Q23 (context graph stale → live instance)

**Paired/Related clusters** (share root cause):
- Q37–Q46 (conductor lifecycle + role topology + state drift)
- Q38–Q44 (work-loss + gate-deadlock + publisher reaper)
- Q39–Q44 (reviewer loop liveness + tandem consistency)
- Q41–Q43 (conductor generation survival)
- Q47–Q48 (handoff latency + agent context exhaustion)
- Q52–Q55 (typed-state discovery + authority scatter)
- Q74–Q75 (autonomous governance design + recovery authority)

---

**Output timestamp**: 2026-04-14  
**Source document**: `/Users/jguida941/testing_upgrade/codex-voice/dev/audits/LIVE_RUN.md` (100 findings Q1–Q100)  
**Coverage**: 81 OPEN, 3 PARTIAL/HOTFIXED, 1 FIXED, 1 SUPERSEDED across 10 architectural buckets
