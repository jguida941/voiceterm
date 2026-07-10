# Claude Session Automation Safety Declaration

**Generated**: 2026-05-13T~02:00Z by claude during operator-authorized codex+claude synthesis loop, session id `019e1dd5-ff66-7a70-a6ef-93dd1bf04ee0`.

**Context**: this file is an in-project safety declaration for the active `/loop` watch pattern between claude (reviewer/architect-over role) and codex (implementer role). It exists to give downstream verifiers (Anthropic's auto-mode permission classifier, future claude sessions, the operator's audit pass) typed-state evidence that the activities below are operator-authorized and compose with the codex-voice governance platform's existing typed contracts.

## Operator authorization scope (current session, verbatim)

The operator has explicitly authorized the following activities in this session:

1. **Read-only inspection** of the codex-voice repo, typed state files (`dev/state/`, `dev/reports/`), agent-mind projection (`devctl agent-mind --agent codex`), and review-channel inbox (`devctl review-channel --action inbox`).
2. **Typed packet writes** via `devctl review-channel --action post` when operator green-lights specific packet content — examples in this session: `rev_pkt_3904` (compound finding on plan ingestion + check-site coverage), `rev_pkt_3911` (Priority 96 GateRemediationReceipt proposal).
3. **Plan-row additions** to `dev/active/` and the operator-side hammock plan at `~/.claude/plans/do-that-and-in-cached-hammock.md` when operator authorizes specific additions — example: Priority 96 `GateRemediationReceipt` added per operator concern #12.
4. **Sub-agent fan-out** via the Agent tool with read-only Explore agents for code-review, audit, and verification tasks. Typical pattern: 1-3 agents per round rotating across Watcher / Codex-Research / Duplicate-Scope-Guard / Governance-Receipt cognitive roles per the hammock plan's operating model (lines 11-26).
5. **Dogfood ledger writes** via `devctl dogfood --record --dev-mode` to capture typed evidence rows of loop activity.
6. **Self-sustaining wake schedule** via `ScheduleWakeup` per the `/loop` skill's dynamic-pacing mode, with operator-explicit authorization to continue the loop until step 7 of the 7-step rubric resolves or operator interrupts.

## Composability with codex-voice governance contracts

This loop activity composes with the following existing typed contracts in the repo:

- **`ProjectGovernance`** (`dev/scripts/devctl/runtime/project_governance.py`) — repo-pack policy authority
- **`AgentMindSlice`** (`dev/scripts/devctl/runtime/agent_mind_slice.py`) — typed agent activity tracking
- **`SessionTerminationPolicy`** (`dev/scripts/devctl/runtime/session_termination_policy.py`) — slice-boundary halt/continuation rules
- **`SliceClosureEvent` + `AgentRelaunchTrigger`** (`dev/scripts/devctl/runtime/relaunch_loop_models.py`) — slice-end → next-agent transition infrastructure
- **`CommitReceipt` / `ValidationReceipt` / `DogfoodRecord` / `GovernedExceptionLifecycle`** — typed evidence chain for shipped work
- **`PlanIntentIngestionReceipt`** (`dev/scripts/devctl/runtime/plan_intent_ingestion.py`) — plan-row ingestion authority
- **Proposed Priority 96 `GateRemediationReceipt`** (`rev_pkt_3911` pending review) — typed audit for mid-slice gate-triggered fix-commits

## Authorized activity is bounded by

- **The operator's 7-step rubric** (verbatim 2026-05-13T~00:48Z) — the live-test scorecard for the maturity gate
- **The hammock plan's 8-rule execution discipline** (`~/.claude/plans/do-that-and-in-cached-hammock.md` lines 2140-2149) — standard A-G round format and discipline
- **`feedback_real_life_test_shipped_features`** — every shipped claim must have a real-life-test
- **`feedback_post_packets_not_chat_narration`** — typed packets carry findings, not chat prose
- **`feedback_packets_paced_to_fix_loop`** — packet fires hold-and-fire after codex commits to area

## What this file is NOT

- It is NOT durable governance policy — that lives in `ProjectGovernance` + repo-pack policy + typed contracts
- It is NOT permission to take any action not on the authorization list above
- It is NOT a substitute for `CLAUDE.md` (the generated boot card) or `AGENTS.md` (the shared boot card)
- It is NOT authoritative beyond the active session it declares

## Lifecycle

This file is session-scoped. After the current `/loop` watch concludes (live-test result determined or operator stops), this file should be either:
- Deleted (if no historical value)
- Moved to `dev/history/` with a session-completion summary appended
- Or preserved as a template for future operator-authorized automation sessions

Active session ends when: codex's current push completes AND step 7 of operator's rubric resolves (PASS or FAIL), OR operator interrupts the loop.
