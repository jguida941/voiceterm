# Remote Orchestration Audit Status

**Branch:** `feature/governance-quality-sweep`
**Last updated:** 2026-04-02 ~7:00pm EDT
**Purpose:** Temporary file for ChatGPT Pro review. Delete when done.

## Summary

25 commits pushed. 235+ tests passing. Guards green.
Started with 0 fixes, ended with 12 landed and pushed.
115 governance findings tracked: 68 fixed, 47 open.

## Latest Verification Round (6 agents, ~7pm EDT)

ChatGPT Pro's latest review verified against pushed code:

| Claim | Verdict | Evidence |
|---|---|---|
| Bridge still active gate | **CONFIRMED** | `bridge_review_accepted()` regex-parses prose, no typed-only path |
| No ReviewerRuntimeContract | **CONFIRMED** | Lifecycle distributed across 87+ modules, no ContractSpec row |
| Startup ownership empty | **CONFIRMED** | All 14 ContractSpec have `startup_surface_tokens=()` |
| Rollover is behavioral patch | **REJECTED** | Rollover delegates through HandoffBundle/ACK, uses typed AttentionStatus enum |
| Terminal cleanup not contract-backed | **CONFIRMED** | Standalone helper, returns untracked `list[str]`, no typed state persisted |

ChatGPT Pro was right on 4 of 5 claims. The rollover IS real contract-backed work, not a patch.

## Concrete Next Steps (from 6-agent implementation assessment)

**Priority: Create ReviewerRuntimeContract + startup ownership, then make bridge a projection**

1. **Add ReviewerRuntimeContract** (~15 lines) to `runtime_state_contract_rows.py` with 5 fields: `review_accepted`, `current_verdict`, `open_findings`, `verdict_accepted_at_utc`, `findings_clear_count`

2. **Refactor bridge acceptance to typed state** (4-5 files):
   - `status_projection_bridge_state.py:142-149` — read from typed state
   - `state.py:97` — replace `bridge_review_accepted(bridge_snapshot)` with typed field
   - `bridge_validation.py:108` — typed field as source-of-truth
   - `handoff.py` — propagate typed `review_accepted`
   - Tests — verify typed path works

3. **Populate startup_surface_tokens** on all 14 contracts (one-line per contract, 2-3 field names each)

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

## ChatGPT Pro Architectural Direction (updated ~8:00pm EDT)

**Verdict: "You have enough mechanisms now. What you still lack is one owner."**

ChatGPT Pro reviewed the branch 3 times. Consistent finding each time: the landed work is real and on-architecture, but it's behavioral patches around a missing contract seam. The system is improving operationally but the architectural seam is still open.

**Key correction from latest review:** The proposed 5-field ReviewerRuntimeContract (review_accepted, current_verdict, open_findings, verdict_accepted_at_utc, findings_clear_count) is TOO SMALL. Those are bridge/verdict state only. The real lifecycle owner also needs: reviewer freshness, stale reason, rollover/ACK state, poll freshness, and session ownership. Without those, you just create a typed acceptance object while leaving the lifecycle fragmented.

### What to implement next (in order)

**1. ReviewerRuntimeContract (the missing owner — FULL lifecycle, not just acceptance)**

Not another helper file. The admitted typed owner of ALL reviewer runtime truth. Must own:
- reviewer mode + effective mode
- reviewer freshness (fresh/poll_due/stale/overdue/missing)
- stale reason (which attention state triggered)
- rollover state (rollover_id, pending ACK, trigger reason)
- last poll freshness (UTC timestamp + age)
- session/terminal ownership (PID, window_id, script_path)
- recovery action currently allowed (from peer_recovery dispatch)
- review acceptance (verdict + findings state)
- publish-clear condition (all of the above must be green)

Add as ContractSpec in `runtime_state_contract_rows.py` with ~10 fields.
Create companion dataclass as the runtime model.
This replaces the current fragmentation across 5+ modules.

**2. Demote bridge_review_accepted() from authority to projection**

Currently `bridge_review_accepted()` regex-parses bridge prose to determine push eligibility. That's markdown-driven authority, not typed-runtime authority. Refactor: 4-5 files need to read from typed `ReviewBridgeState.review_accepted` instead of calling `bridge_review_accepted(BridgeSnapshot)`.

Files: `status_projection_bridge_state.py:142`, `state.py:97`, `bridge_validation.py:108`, `handoff.py`, tests.

**3. Doctor surface as PROJECTION over the contract**

Do NOT make doctor another independent analyzer. Make it a projection over ReviewerRuntimeContract + ReviewerGateState + session truth. One surface, one source of truth.

**4. Startup ownership metadata**

Populate `startup_surface_tokens` on all 14 ContractSpec rows (2-3 tokens each, one-line per contract). Add `contract_ownership_map` to StartupContext so agents get ownership metadata at bootstrap, not by reading prose.

### Design rule

> typed state is authority, bridge is projection
> one owner per lifecycle, not distributed fragments
> doctor projects from the owner, doesn't independently analyze
> startup tells agents what exists, not just what's allowed

## Next Steps

1. Create ReviewerRuntimeContract ContractSpec (~15 lines)
2. Refactor bridge acceptance to typed state (4-5 files)
3. Build doctor as projection over the contract
4. Populate startup_surface_tokens on all 14 contracts
5. Prove clean path: launch → review → ACK → push (typed, no bridge prose)
6. Prove rescue path: stale reviewer → auto-rollover → recovery → green
