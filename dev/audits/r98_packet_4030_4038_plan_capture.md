# R98 Packet 4030-4038 Plan Capture Source

This source converts the R98 reviewer-loop handoff and packet bodies
`rev_pkt_4030` through `rev_pkt_4038` into actionable `MP-NEW-*` plan rows.

Evidence read:

- `dev/reports/review_channel/events/trace.ndjson` packet bodies for
  `rev_pkt_4030` through `rev_pkt_4038`.
- `dev/reports/agent_minds/claude_latest.json`, refreshed 2026-05-14, which
  confirms the short-term loop plan and the push-first monitoring context.
- `dev/reports/agent_minds/codex_latest.json`, refreshed 2026-05-14, which
  records the raw push, packet-body read, and plan-capture sequence.
- `operator` agent-mind projection was unavailable: `agent-mind --agent
  operator` returned `no operator session JSONL found`, so the operator
  evidence source remains the current session briefing and packet bodies.

Rows to ingest from this plan:

- `MP-NEW-001` Class 1: apply ADR semantics manually to multi-packet synthesis until PacketADRReceipt and relationship graph contracts are implemented.
- `MP-NEW-002` Class 2: implement pivot-relevant packet timing so pivot_now findings preempt commit cadence while minor observations batch.
- `MP-NEW-003` Class 3: migrate memory-only behavioral and architectural rules into typed program authority, receipts, docs, and guards.
- `MP-NEW-004` Class 4: consolidate N-lane fanout into one comprehensive synthesis response with explicit lane evidence and duplicate suppression.
- `MP-NEW-005` Class 5: enforce that role assignment is not start-coding authorization; require fresh typed authority before mutation.
- `MP-NEW-006` Class 6: define multi-role agent fleet rotation for watcher, researcher, duplicate-check, architecture, reviewer, and implementer lanes.
- `MP-NEW-007` Class 7: replace rapid agent_mind polling with cadence rules keyed to immediate events, quiet windows, and typed wakeups.
- `MP-NEW-008` Class 8: require real-life dogfood execution before feature closure and bind dogfood receipts to applied rows.
- `MP-NEW-009` Class 9: type Codex CLI escape-valve flags and remote-control headless modes so bypass posture cannot be hidden in launch prose.
- `MP-NEW-010` Class 10: encode trusted Codex launch command patterns with dangerous flag receipts, bypass reason, scope, and expiry.
- `MP-NEW-011` Class 11: standardize loop response shape with a verbose evidence body plus a terse bullet summary.
- `MP-NEW-012` Class 12: define autonomous loop keep-awake policy with ScheduleWakeup receipts, continuation anchors, and stop anchors.
- `MP-NEW-013` Class 13: support raw git during plan execution while preserving governed-push proof at session end.
- `MP-NEW-014` Class 14: route architectural fixes inline under typed operator override instead of deferring them to future phases.
- `MP-NEW-015` Class 15: encode beta-session stop and wake policy so agents stop at the first safe point and avoid sleep instructions.
- `MP-NEW-016` Class 16: constrain round-close output to concise loop summaries suitable for long-running /loop work.
- `MP-NEW-017` Class 17: require guard or probe promotion each round when architectural problems are discovered.
- `MP-NEW-018` Class 18: add SystemAlignmentRole and system-improvement subrole scans to each round, including repo-portability checks from `rev_pkt_4030`.
- `MP-NEW-019` Class 19: require typed-output human_summary fields so `ok=true` cannot hide blind-pass or partial-proof cases.
- `MP-NEW-020` Class 20: run repo-portability checks on every new substrate and migrate hardcoded repo literals to repo-pack policy.
- `MP-NEW-021` Class 21: implement FeatureLifecycleProof receipts on every commit, including build, test, dogfood, review, portability, and push evidence.
- `MP-NEW-022` Class 22: implement queue-attention reducers and bypass reasoning for stalled queued rows.
- `MP-NEW-023` Class 23: implement composable toggle-receipt governance and assistant-guide mode without bypassing governance invariants.
- `MP-NEW-024` Class 24: implement skill-loading governance compatibility with SkillManifest, SkillLoadReceipt, and SkillCompatibilityValidator contracts.
- `MP-NEW-025` Class 25: enforce mandatory ingest-before-implement as an invariant and pre-commit guard candidate P40.
- `MP-NEW-026` Cross-cutting: consolidate the proposed R98 contracts into the platform contract registry, blueprint, fixtures, and closure checks.
- `MP-NEW-027` Cross-cutting: scaffold guards P17 through P41 as a guard-bundle backlog with dependencies on the MP-NEW class rows.
- `MP-NEW-028` Cross-cutting: migrate repo-pack policy and lifecycle-receipt backfill so raw push, governed push, and commit proof share one publication ledger.

## Proposed Guard Backlog

- P17 feature-lifecycle-proof receipt presence on commit.
- P18 capture-all-findings-in-MAIN-PLAN packet-to-plan-row check.
- P19 queue-attention age threshold.
- P20 priority, linking, and self-discovery on every plan row.
- P21 agent-as-typed-workflow heartbeat.
- P22 continuous-improvement-mode round-close scan.
- P23 unified error-handling surface.
- P24 toggle-receipt presence per behavioral flag.
- P25 assistant-guide-mode compose-with-governance.
- P26 skill-loading governance compatibility check.
- P27 agent_mind under-use detector.
- P28 parallel-surface dedupe.
- P29 role-capability dictation receipt.
- P30 receipts-on-every-commit chain.
- P31 observer-role typed-output human_summary.
- P32 repo-portability scan on every new substrate.
- P33 packet-to-plan-row freshness.
- P34 contract-proposed-but-not-built drift.
- P35 false-claimed-landed audit.
- P36 fleet-agent rotation discipline.
- P37 slice-vs-class one-to-one coverage.
- P38 review_only intake auto-promote criteria.
- P39 push-receipt presence in raw_git_bypass_receipts.jsonl.
- P40 mandatory-ingest-before-implement pre-commit hook.
- P41 governance-platform invariant scanner.
