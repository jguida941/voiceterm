# Postmortem: 2026-04-14/15 Remote-Control Dogfood Session Failures

## Observed Failures Today (Timeline)

- **b374610d** (20:09:21Z): Commit self-invalidated 3 times via `attention_revision_stale` during guard bundle. Workaround: tight session-resume + startup-context + commit with zero intervening activity.
- **671dfff3** (20:12:16Z): Push preflight auto-synced bridge.md, dirtying worktree immediately post-commit. Broke snapshot receipt-commit path (rev_pkt_0489).
- **c6ef4054** (post-20:12Z): Codex reviewer never launched. `ps` showed no reviewer process. `reviewer_mode=single_agent` until minutes before postmortem.
- **Unreviewed commits sitting local**: 3 commits (b374610d, 671dfff3, c6ef4054) ahead of origin without Codex review gate.
- **Typed PID state lie**: `review-channel --action ensure` returned `reviewer_supervisor.pid=26851`. OS had no such process. State populated without verification.
- **Operator manual intervention**: Caught unreviewed push, forced session recovery, re-synced typed state after PID discrepancy.

## Failure Modes (Structural)

| Mode | Symptom | Structural Cause | Eliminating Change |
|------|---------|------------------|-------------------|
| **Commit self-invalidation** | `attention_revision_stale` 3× in 1 commit cycle | Shared `attention_revision` field between reviewer heartbeat stream (bumps on inbox reads, findings-priority updates, publisher writes) and commit approval state machine (holds approval at revision N, but final check reads live N+1) | Implement attention_revision lease: snapshot revision at approval time, hold it through guard bundle, release only on pipeline state transition to `commit_recorded` or `push_blocked`. Changes: `commit.py`, `commit_pipeline.py`, `attention_revision_source.py` |
| **Reviewer never launched** | No supervisor process. Mode read as `single_agent` until operator noticed. | Launch gated on clean worktree + no-ahead-commits. But reviewer launch is idempotent-only on explicit operator command; no auto-start on session-resume or startup-context. Mode toggle is advisory, not enforcing. | Add launch auto-trigger to `session-resume --role reviewer` if `effective_reviewer_mode != single_agent` and no live reviewer found. Make mode transition trigger supervisor restart, not just update typed field. Changes: `launcher/ensure_reviewer_supervisor`, `session_resume.py` |
| **Bridge re-sync dirties worktree** | `push --execute` preflight synced bridge.md, immediately creating dirty state. Blocked snapshot receipt-commit (which requires clean tree). | Push preflight calls `sync_bridge_state()` unconditionally. Publisher daemon continuously rewrites bridge.md as part of normal operation. Preflight doesn't know bridge.md is compatibility-projection, not code. Creates mutual exclusion: push needs clean tree but its own preflight dirties it. | Exclude bridge.md (+ audit artifacts) from push preflight's worktree-clean check and from receipt-commit's `non_snapshot_paths_dirty` validation. Treat bridge.md as typed-state-derived projection, not owned code. Changes: `push_preflight`, `receipt_commit_gate`, `sync_bridge_state` |
| **Typed state PID mismatch** | `reviewer_supervisor.pid` returned value that OS had no process for. No verification before populating field. | PID written to typed state without OS verification. State reads from session registry/publisher snapshot, not live `ps`. Detection lag ~30s (publisher cycle time). No heartbeat kill-validation. | Add OS-side PID verification before writing to state: check process exists and is responsive (e.g., send signal 0). Add TTL-based liveness timeout: if heartbeat not refreshed within 5 min, mark participant dead. Changes: `runtime_supervision.py`, `participant_liveness.py`, `heartbeat_validation` |
| **Role boundary not enforced** | Claude pushed unreviewed commits. No gate on `devctl push` for caller role. | `devctl push` is a governed command but doesn't read caller role from session context. No typed role contract on command entry point. Reviewer gate is optional via `reviewer_mode=single_agent` but caller can still be non-reviewer. | Add caller-role gate to `push` command: require `role=operator` or `role=codex_reviewer` or explicit `--developer-override` flag. Fail if `role=implementer` and `reviewer_mode=active_dual_agent`. Wire role from session context. Changes: `push.py`, `command_authorization.py` (new), `session_context` |
| **Launch deadlock** | Can't launch reviewer (needs clean tree + no ahead), can't commit (needs review), can't clean tree (needs commit). | Three mutual-exclusion gates with no circuit-breaker: (1) launch gated on clean worktree; (2) commit gated on review; (3) push preflight/bridge-sync creates dirty state. When bridge.md sync is mandatory preflight, the gates form: launch ← clean ← commit ← review, but review is blocked on no reviewer running. | Add circuit-breaker to launch gate: allow launch in `single_agent` + repair mode even with dirty tree or ahead commits. Add `--force-repair-mode` flag to `session-resume --role reviewer` and `startup-context` that suppresses launch mutual-exclusion checks. Decouples repair path from code-review path. Changes: `launcher/gate_logic.py`, `session_resume.py`, `startup_context.py` |

## Role-Boundary Gaps

1. **No command-level role enforcement**: `devctl push` should check `role != implementer` when `reviewer_mode=active_dual_agent`. Claude should not be able to invoke `devctl push --execute` directly.
   - **Gap location**: `dev/scripts/devctl/commands/vcs/push.py` — missing role check before `execute=True` path.
   - **Missing contract**: `PushCommandAuthorization` dataclass with fields `caller_role`, `reviewer_mode`, `allowed_action`.

2. **Mode field is advisory, not enforcing**: `reviewer_mode=active_dual_agent` is written to typed state but does not gate supervisor launch or approval flow.
   - **Gap location**: `dev/scripts/devctl/commands/launcher/` — mode read for display, not for gating.
   - **Missing enforcement**: supervisor launch should check mode and refuse launch if `mode != single_agent` AND `supervisor_running == false`.

3. **No role on session context**: Session objects carry `interaction_mode` (operator terminal vs remote control) but not `caller_role` (which agent is invoking commands).
   - **Gap location**: `dev/scripts/devctl/runtime/session_context.py` — missing `caller_role: Literal['claude', 'codex', 'operator']`.

## Gate-Deadlock Analysis

The specific chain that produced "can't launch, can't commit, can't clean":

```
Desired state: Launch Codex reviewer
Precondition A: worktree_clean == True
Precondition B: no commits ahead of origin

Current state:
  - Bridge.md is dirty (publisher wrote it during normal operation)
  - Commit b374610d landed; b374610d was unreviewed by Codex (mode=single_agent earlier)
  - Codex launch blocked on: gate checks worktree_clean AND no_ahead
  - Worktree can only be cleaned by: git commit
  - Commit requires: Codex review (mode = active_dual_agent now, but Codex not running)
  - Codex can't run because: launch gate unsatisfied

Cycle:
  1. Try `launcher ensure-follow --role reviewer` → blocked: worktree dirty
  2. Try `commit -m cleanup` → blocked: mode=active_dual_agent, Codex not reviewing
  3. Try `push --execute` to clean branch → blocked: mode=active_dual_agent, unreviewed commits
  4. Manual: operator kills all conductors, reruns `startup-context` + `session-resume`, mode reverts to `single_agent`, Codex still not auto-launched

Circuit-breaker needed:
  - When mode=`active_dual_agent` AND supervisor not found (live_participant_count=0), allow launcher to proceed in `single_agent` + `repair_mode=true`.
  - Repair mode suppresses mutual-exclusion checks for 5 minutes or until first successful launch detected.
  - Default gate logic requires: `launcher_mode(mode, supervisor_alive, repair_window)` returning permission, not just advisory.
```

No circuit-breaker exists. The launch gate is a boolean check, not a state machine with fallback. Missing: `--repair-mode-auto-recovery` flag on launcher or `repair_deadline` timestamp in typed state.

## Automation Targets (Manual Steps That Should Be Hands-Off)

| Manual Step | Why Operator Did It | Should Have Been |
|-------------|-------------------|------------------|
| Kill Claude/Codex conductors after they hung | Mode reverted to `single_agent` but supervisor stayed "running" per typed state; liveness detection lag ~30s | Auto-detect stale PIDs; `review-channel` should emit `participant_liveness_expired` event; launcher should auto-cleanup stale conductor on re-launch |
| Re-run `startup-context --role implementer` + `startup-context --role reviewer` | Session resumed but typed state was inconsistent; no auto-bootstrap | `session-resume` should auto-run both roles' startup-context if any prior step failed; make bootstrap idempotent |
| Re-run `review-channel --action ensure` after PID mismatch | Typed state lied about supervisor PID; needed manual re-sync | `review-channel --action ensure` should verify OS PIDs before populating state; add `--verify-os-state` flag; gate on process signals |
| Manually edit bridge.md / REVIEW_SNAPSHOT.md to fix stale timestamps | Dashboard showed stale liveness; no refresh on demand | `push --execute` should not call `sync_bridge_state` unconditionally; bridge.md should be projection-only; add `review-channel --action refresh-projection` |
| Re-run `devctl commit` with tight session-resume pre-step | `attention_revision_stale` kept invalidating. Workaround was session-resume immediately before commit. | Implement attention_revision lease; no more retry loops needed |
| Switch mode from `active_dual_agent` back to `single_agent` to unblock | Once Codex wouldn't launch, only way to unblock was demoting mode, losing review gate | Add `launcher --force-repair` that suppresses precondition checks; don't require mode demotion to recover |

**Total manual steps in session**: ~18 (per operator gesture log).
**Ideal**: 0. Redesign should achieve 90% automation (allowable: supervisor heartbeat poll, occasional dashboard refresh). 
**Target for redesign**: max 2 manual steps (initial session launch + final push confirmation).

## Minimum Viable Changes to Prevent Recurrence

Prioritized by blast radius and implementation effort:

### P0 — Atomic (must fix before multi-agent loop resumes)

1. **Attention_revision lease** (blocks commit+push). 
   - Where: `dev/scripts/devctl/commands/vcs/commit.py`, `dev/scripts/devctl/governance/commit_pipeline.py`, `dev/scripts/devctl/runtime/attention_revision_source.py`.
   - Owner: Codex (architecture fix, per Q100 dispatch).
   - Effort: ~3–4 hours. Snapshot revision in approval packet, hold through guard bundle, release on state transition.
   - Blocker removal: eliminates `attention_revision_stale` class entirely.

2. **Bridge.md excluded from push-preflight worktree-clean check** (blocks deadlock).
   - Where: `dev/scripts/devctl/commands/vcs/push_preflight.py`, `dev/scripts/devctl/commands/vcs/receipt_commit_gate.py`.
   - Owner: Claude (hygiene, ~30 min).
   - Effort: ~30 min. One-line exclusion list: `["bridge.md", "dev/audits/**"]`.
   - Blocker removal: breaks the "push dirties tree" cycle.

3. **Reviewer launch auto-trigger + repair-mode gate** (blocks launch deadlock).
   - Where: `dev/scripts/devctl/commands/launcher/ensure_follow.py`, `dev/scripts/devctl/runtime/launcher_gate_logic.py` (new file).
   - Owner: Codex (state machine).
   - Effort: ~2 hours. Add `repair_window` to session context; gate logic returns `permission(reason, deadline)` instead of bool.
   - Blocker removal: eliminates deadlock; launcher can proceed in repair mode.

4. **Role-aware push gate** (blocks unreviewed commits).
   - Where: `dev/scripts/devctl/commands/vcs/push.py`, new `dev/scripts/devctl/runtime/command_authorization.py`.
   - Owner: Claude (governance).
   - Effort: ~45 min. Add `caller_role` to command context; fail if `role==implementer` and `mode==active_dual_agent` and `--developer-override` absent.
   - Blocker removal: prevents Claude from pushing unreviewed.

### P1 — Safe (ships with P0, resolves secondary failures)

5. **PID liveness verification** (fixes typed state lying).
   - Where: `dev/scripts/devctl/runtime/participant_liveness.py`, `dev/scripts/devctl/commands/governance/review_channel.py`.
   - Owner: Codex (observability).
   - Effort: ~1.5 hours. Heartbeat validation checks `kill -0 <pid>` before writing state.
   - Blocker removal: no more stale PIDs in typed state.

6. **Mode field enforcement** (ensures mode changes gate supervisor).
   - Where: `dev/scripts/devctl/commands/launcher/ensure_follow.py`, `dev/scripts/devctl/runtime/supervisor_state_machine.py` (new).
   - Owner: Codex (state machine).
   - Effort: ~1 hour. Mode change triggers supervisor restart, not just field update.
   - Blocker removal: active_dual_agent actually enforces dual-agent requirement.

### P2 — Deferred (land after loop stability proven)

7. **Typed state role contract** (prevents future role-boundary bypasses).
   - Where: new `dev/scripts/devctl/platform/contracts/command_authorization_contract.py`.
   - Owner: Claude (governance).
   - Effort: ~30 min. Define `PushAuthorization`, `CommitAuthorization` typed contracts.
   - Blocker removal: future commands fail CI if they ignore role checks.

8. **Automatic typed-state bootstrap** (prevents liveness lag from burning sessions).
   - Where: `dev/scripts/devctl/runtime/session_resume.py`, `dev/scripts/devctl/commands/startup_context.py`.
   - Owner: Claude (automation).
   - Effort: ~1 hour. If either startup-context fails for a role, retry 3× with exponential backoff before returning.
   - Blocker removal: typed state always fresh when session resumes.

---

**Estimated total P0+P1 effort**: 9–10 hours of focused Codex + Claude work.
**Estimated blocker removal per fix**: see table above; all P0 fixes unblock multi-agent loop.
**Verification**: after each fix, run `devctl dogfood --record --actor <role>` for 3 push cycles with clean commits to confirm no regression.
