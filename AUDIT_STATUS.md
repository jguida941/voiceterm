# Remote Orchestration Audit Status

**Branch:** `feature/governance-quality-sweep`
**Last updated:** 2026-04-02 ~5:30pm EDT
**Purpose:** Temporary file for ChatGPT Pro review. Delete when done.

## Summary

24 commits pushed. 235+ tests passing. Guards green.
Started with 0 fixes, ended with 10 landed and pushed.
115 governance findings tracked: 68 fixed, 47 open.

## What Was Fixed and Pushed Today

| # | Fix | File(s) | Commit |
|---|---|---|---|
| 1 | Idle reviewer masked by fake heartbeats | `reviewer_follow_guard.py`, `reviewer_follow_heartbeat_guard.py` | dde6c2d |
| 2 | Dedupe one-shot bug (restore packet fires only once) | `reviewer_follow_packet_guard.py` | 91fd388 |
| 3 | Dry-run contract violation (auth + caffeinate in preview) | `remote-bridge-loop.sh` | dde6c2d |
| 4 | Push gate: `startup_advisory_decision.py:38` | `startup_advisory_decision.py` | e3ce4fd |
| 5 | Push gate: `startup_push_decision.py:223` | `startup_push_decision.py` | e3ce4fd |
| 6 | Push gate: `runtime_checks.py:67` | `startup_authority_contract/runtime_checks.py` | e7c4898 |
| 7 | Acceptance regex (push approved not recognized) | `bridge_validation_acceptance.py` | 26c76ec |
| 8 | Bridge guard rejects Operator Direction | `bridge_sanitize.py` | 80cc2e8 |
| 9 | Docs governance drift (dangling remote_orchestration.md refs) | `AGENTS.md`, `INDEX.md`, `MASTER_PLAN.md` | e068d7a |
| 10 | Automated reviewer rollover | `reviewer_follow_recovery.py` (+192 lines) | 09349aa |
| 11 | Terminal lifecycle cleanup | `terminal_app.py` (+143 lines), `launch_records.py`, `session_probe.py` | 37f683d |
| 12 | Bridge projection silently dropped Operator Direction | `bridge_projection_state.py`, `bridge_sanitize.py`, `handoff_constants.py` | 801349f |

## What's Still Open

### Architecture Gaps (from ChatGPT Pro + 8-agent verification)

**1. No unified ReviewerRuntimeContract**
- Reviewer truth is fragmented across 5+ modules: `peer_liveness.py`, `handoff.py`, `bridge_validation_acceptance.py`, `session_state_hints.py`, `attention_classify.py`
- No single owner for: detect stale → kill/reap → relaunch → ACK → poll → clear → publish
- The pieces exist but nobody composes them into one typed contract
- `reviewer_follow.py` now has rollover (commit 09349aa) but lifecycle ownership is still distributed

**2. No doctor/health surface**
- No `review-channel --action doctor` command exists
- Health data scattered across `bridge_liveness`, `peer_recovery.py` (20+ recovery recipes), `bridge_validation.py`
- Need ONE surface that answers: bridge clean? reviewer current? implementer ACK? recovery needed? stale terminals? one recovery command?
- Agent designed full spec — needs `_doctor.py` handler + parser registration

**3. Startup contract ownership map missing**
- `StartupContext` (startup_context.py:49-71) has no `contract_ownership_map`
- All 14 `ContractSpec` rows have empty `startup_surface_tokens = ()`
- Agents get state at bootstrap but not ownership metadata
- Need 3 new fields on ContractSpec: `authoritative_artifact`, `allowed_projections`, `recovery_surface`

**4. Bridge is still active decision gate, not just projection**
- `bridge_review_accepted()` reads bridge prose sections to determine push eligibility
- Push fails without bridge.md existing — no fallback to typed state
- The docs say bridge should be compatibility projection, but runtime still depends on it

**5. Push invalidation cycle (FIXED but architecturally fragile)**
- `push_state.py:111-120` does exact HEAD equality check
- Each bridge commit creates new HEAD, invalidating previous acceptance
- P0 fixes break the cycle by making `review_gate_allows_push` bypass `implementation_blocked`
- But the underlying HEAD-equality design is still fragile

## Verified Findings (8-agent verification x3 rounds)

All fixes use existing typed contracts — no ad hoc bypasses:
- `PacketPostRequest` pipeline for restore packets
- `ReviewerGateState` for push gate decisions
- `PushDecisionInputs` for push decision threading
- `HandoffBundle` + rollover ACK for reviewer recovery
- `BRIDGE_ALLOWED_H2` / `BRIDGE_SECTION_ORDER` for bridge contracts
- `PreparedSessionRecord` for terminal tracking

ChatGPT Pro's diagnosis confirmed by agents:
- "You have contracts for the pieces, but not one owner for the lifecycle"
- "The system is better at describing blocked states than recovering from them fluently"
- "You do not mainly have a modeling problem anymore. You have a recovery-and-discoverability problem"

## Governance Findings (from `governance-review --format md`)

**115 total findings | 68 fixed | 47 open**

Key open findings:
- `bridge_projection_drops_operator_direction` — FIXED in 801349f
- `bridge_still_active_gate_not_projection` — open, architectural
- `need_review_channel_doctor_surface` — open, needs implementation
- `startup_surface_tokens_unpopulated` — open, all 14 contracts empty
- `reviewer_truth_distributed_no_owner` — open, architectural
- `push_invalidation_head_equality` — open but cycle broken by P0
- `manual_codex_rollover` — FIXED in 09349aa (automated rollover landed)
- `zombie_terminal_cleanup` — FIXED in 37f683d (terminal cleanup landed)
- `agent_architecture_bypass` — open, root cause of all agent misbehavior
- `agent_tooling_contract_ignorance` — open, agents don't know typed vocabulary

## Key Architecture Files

| Purpose | File |
|---|---|
| Push decision | `dev/scripts/devctl/runtime/startup_push_decision.py` |
| Startup advisory | `dev/scripts/devctl/runtime/startup_advisory_decision.py` |
| Startup context | `dev/scripts/devctl/runtime/startup_context.py` |
| Launch truth | `dev/scripts/devctl/review_channel/launch_truth.py` |
| Bridge validation | `dev/scripts/devctl/review_channel/bridge_sanitize.py` |
| Bridge acceptance | `dev/scripts/devctl/review_channel/bridge_validation_acceptance.py` |
| Bridge projection | `dev/scripts/devctl/review_channel/bridge_projection_state.py` |
| Handoff/rollover | `dev/scripts/devctl/review_channel/handoff.py` |
| Peer recovery | `dev/scripts/devctl/review_channel/peer_recovery.py` |
| Status projection | `dev/scripts/devctl/review_channel/state.py` |
| Terminal launch/cleanup | `dev/scripts/devctl/review_channel/terminal_app.py` |
| Reviewer follow | `dev/scripts/devctl/review_channel/reviewer_follow.py` |
| Reviewer recovery | `dev/scripts/devctl/review_channel/reviewer_follow_recovery.py` |
| Startup authority | `dev/scripts/checks/startup_authority_contract/runtime_checks.py` |
| Platform contracts | `dev/scripts/devctl/platform/contracts.py` |
| Contract rows | `dev/scripts/devctl/platform/runtime_*_contract_rows.py` |

## Next Steps

1. Build doctor surface (`review-channel --action doctor`)
2. Populate startup contract ownership map
3. Continue reducing 47 open governance findings
4. Prove one clean end-to-end cycle: launch → review → ACK → push
5. Prove one rescue cycle: stale reviewer → auto-rollover → recovery → green
