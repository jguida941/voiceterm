# Code Audit Channel

Live shared review channel for Codex <-> Claude coordination during active work.

## Start-Of-Conversation Rules

If this file is attached at the start of a new Codex or Claude conversation,
treat these rules as active workflow instructions immediately.

1. Use this file as the live Codex<->Claude coordination authority for the
   current loop. Do not create parallel control files for the same work.
2. Codex is the reviewer. Claude is the coder.
3. At conversation start, both agents must bootstrap repo authority in this
   order before acting: `AGENTS.md`, `dev/active/INDEX.md`,
   `dev/active/MASTER_PLAN.md`, and `dev/active/review_channel.md`.
4. Treat `dev/active/MASTER_PLAN.md` as the canonical execution tracker and
   `dev/active/INDEX.md` as the router for which active spec/runbook docs are
   required for the current scope. After bootstrap, follow the relevant active
   plan chain autonomously until the current scope, checklist items, and live
   review findings are complete.
5. After bootstrap, start from the live sections in this file instead of
   guessing from chat history:
   - Codex should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`.
   - Claude should start from `Current Verdict`, `Open Findings`, and `Current Instruction For Claude`, then acknowledge the active instruction in `Claude Ack` before coding.
6. Codex must poll non-`code_audit.md` worktree changes every 2-3 minutes while
   code is moving, or sooner after a meaningful code chunk / explicit user
   request.
7. Codex must exclude `code_audit.md` itself when computing the reviewed
   worktree hash.
8. After each meaningful review pass, Codex must:
   - update the Codex-owned sections in this file
   - refresh the latest reviewed non-audit worktree hash
   - refresh both UTC and local New York poll time
   - post a short operator-visible chat update summarizing the review, whether
     findings changed, and what Claude should do next
9. Claude must read this file before starting each coding slice, acknowledge the
   current instruction in `Claude Ack`, and update `Claude Status` with the
   exact files/scope being worked.
10. Section ownership is strict:
   - Codex owns `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and the reviewer header timestamps/hash
   - Claude owns `Claude Status`, `Claude Questions`, and `Claude Ack`
11. Only the Codex conductor may update the Codex-owned sections in this file.
    Specialist Codex reviewer workers must report findings back to the
    conductor instead of editing this bridge directly.
12. Only the Claude conductor may update the Claude-owned sections in this
    file. Specialist Claude coding workers must report status back to the
    conductor instead of editing this bridge directly.
13. Specialist workers should wake on owned-path changes or explicit conductor
    request instead of every worker polling the full tree blindly on the same
    cadence.
14. Codex must emit an operator-visible heartbeat every 5 minutes while code
    is moving, even when the blocker set is unchanged.
15. Keep this file current-state only. Replace stale findings instead of turning
   it into a transcript dump.
16. Keep live coordination here and durable execution state in the active-plan
   docs. Do not recreate retired parallel notes such as
   `dev/audits/SESSION_HANDOFF.md` or `dev/audits/parallel_agents.md`.
17. Default to autonomous execution. Do not stop to ask the user what to do
   next unless one of these is true:
   - product/UX intent is genuinely ambiguous
   - a destructive action is required
   - credentials, auth, publishing, tagging, or pushing to GitHub is required
   - physical/manual validation is required
   - repo policy and current instructions conflict
18. Outside those cases, the reviewer/coder loop should keep moving on its own:
   Codex reviews, writes findings here, pings the operator in chat, and Claude
   implements/responds here without waiting for extra user orchestration.
19. When the current slice is accepted and scoped plan work remains, Codex must
   derive the next highest-priority unchecked plan item from the active-plan
   chain and rewrite `Current Instruction For Claude` for the next slice
   instead of idling at "all green so far."

- Started: `2026-03-07T22:17:12Z`
- Mode: active review
- Poll target: every 5 minutes when code is moving (operator-directed live loop cadence)
- Canonical purpose: keep only current review state here, not historical transcript dumps
- Last Codex poll: `2026-03-09T12:38:10Z`
- Last Codex poll (Local America/New_York): `2026-03-09 08:38:10 EDT`
- Last non-audit worktree hash: `6b59ffa56823d655a8ac0442bc7d72d3ccffcc43f61e23d09cf7ad050fe86f7a`

## Protocol

1. Claude should poll this file periodically while coding.
2. Codex will poll non-`code_audit.md` worktree changes, review meaningful deltas, and replace stale findings instead of appending endless snapshot history.
3. `code_audit.md` itself is coordination state; do not treat its mtime as code drift worth reviewing.
4. Section ownership is strict:
   - Claude owns `Claude Status`, `Claude Questions`, and `Claude Ack`.
   - Codex owns `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Poll Status`.
5. If Claude finishes or rebases a finding, it should update `Claude Ack` with a short note like `acknowledged`, `fixed`, `needs-clarification`, or `blocked`.
6. Only unresolved findings, current verdicts, current ack state, and next instructions should stay live here.
7. Resolved items should be compressed into the short resolved summary below.
8. After each meaningful Codex reviewer write here, Codex should also post a short operator-visible chat update that summarizes the reviewed non-`code_audit.md` hash, whether findings changed, and what Claude needs to do next.
9. If the current slice is reviewer-accepted and scoped plan work remains,
   Codex must promote the next scoped plan item into `Current Instruction For Claude`
   in the same or next review pass; do not leave the loop parked on a completed slice.

## Swarm Mode

- Current scale-out mode is `8+8`: `AGENT-1..AGENT-8` are the Codex
  reviewer/auditor swarm and `AGENT-9..AGENT-16` are the Claude coding/fix
  swarm.
- `dev/active/review_channel.md` now contains the merged static swarm plan
  (lane map, worktrees, signoff template, governance); this file is the only
  live cross-team coordination surface during execution.
- Codex reviewer lanes poll non-`code_audit.md` changes every 5 minutes while
  Claude lanes are coding. If no new diff is ready, they wait, poll again, and
  resume review instead of idling.
- Claude lanes should treat `Open Findings` plus `Current Instruction For
  Claude` as the shared task queue, claim sub-slices in `Claude Status`, and
  keep `Claude Ack` current as fixes land.
- No separate multi-agent worktree runbook is active for this cycle.

## Poll Status

- Codex polling mode: active reviewer watch loop on the whole unpushed worktree; poll non-`code_audit.md` changes every 5 minutes while code is moving.
- Current poll result: tree movement is still active and the reviewed non-audit worktree hash is now `6b59ffa56823d655a8ac0442bc7d72d3ccffcc43f61e23d09cf7ad050fe86f7a` (recomputed over tracked + untracked regular files returned by `git ls-files`, excluding `code_audit.md`). The bridge narrative had drifted behind the real tree: this checkout now spans MP-347 / MP-355 / MP-356 tooling changes plus active MP-340 mobile relay/import work (`app/ios/**`, `dev/scripts/devctl/commands/mobile_status.py`, `app/operator_console/state/session_trace_reader.py`, `rust/src/bin/voiceterm/event_loop.rs`, `rust/src/codex/cli.rs`, `rust/src/ipc/router.rs`, `rust/src/ipc/session/claude_job.rs`, and related docs/tests). The Rust checker slice moved forward in this pass: `python3 -m pytest dev/scripts/devctl/tests/test_check_rust_best_practices.py -q --tb=short` is green (`12` tests), `python3 dev/scripts/checks/check_rust_best_practices.py --format md` is green on the current dirty tree, and the new detached-thread metric no longer false-positives on `JoinHandle`-returning helper functions. `python3 dev/scripts/devctl.py publication-sync --format md` is still stale for `terminal-as-interface`, and `python3 dev/scripts/checks/check_rust_best_practices.py --absolute --format md` is still red but now down to `19` violations.
- Review scope for this pass: `code_audit.md`, `dev/active/MASTER_PLAN.md`, `dev/active/pre_release_architecture_audit.md`, `dev/active/review_channel.md`, `dev/active/autonomous_control_plane.md`, `dev/active/host_process_hygiene.md`, `dev/scripts/checks/check_rust_best_practices.py`, `dev/scripts/checks/check_rust_security_footguns.py`, `dev/scripts/devctl/review_channel_launch.py`, `dev/scripts/devctl/commands/mobile_status.py`, the touched review/process tests, the mobile Swift relay/import files, and the Rust review/control/handoff surfaces.
- Reviewer heartbeat: the conductor loop is active again on the real dirty tree. The bridge has been rebased off the stale push-prep narrative; the live queue is now the blocker list below, not the earlier “narrow follow-up delta.”

## Current Verdict

- Overall tracker status: repo is still on `feature/push-readiness-audit`, but the live tree is not in final push-prep. The bridge text had become stale and self-contradictory while code kept moving.
- Current reviewer priority is to restore honesty and signal quality before any push conversation resumes: the new Rust guards still have at least one false-negative follow-up, MP-356 still has live-helper/orphan false negatives, and the Rust review/control/handoff surfaces still drop or hide bridge freshness state.
- Progress is real but bounded: the generated Claude launcher now clears inherited `CLAUDECODE`, the mobile relay import path accepts `full.json`, and the Swift core proof is green. Those slices do not clear the broader blocker set.
- The branch is not reviewer-accepted for push. Human approval remains separate, `publication-sync` drift is still real, and the blocker queue below must be resolved or explicitly waived first.

## Open Findings

- High: the new Rust guard additions are not fully safe to promote yet. `check_rust_best_practices.py` still misses mixed manual-plus-`toml::from_str` parser files in the new `custom_persistent_toml_parsers` metric, and `check_rust_security_footguns.py` still counts `unreachable!()` inside comments/strings in hot-path files. The detached-thread false-positive on `JoinHandle`-returning helper paths is fixed in this pass. The remaining guard regressions are still required-bundle blockers until fixed with targeted tests.
- High: MP-356 still has live false negatives. `process-cleanup --verify` can return green while recent attached repo-tooling helpers/conductors are still running, and orphaned repo-cwd descendants with unrecognized executables still disappear after the matched parent exits.
- High: the Rust review/control/handoff path is still not bridge-honest. The parser drops `Last Codex poll` / worktree-hash metadata from the current `code_audit.md` layout, Control/Handoff/Memory keep rendering stale artifacts as current after reload failure, and the cockpit stops live-refreshing once the bridge content hash is unchanged.
- High: rollover prompts still violate the required bootstrap order. Fresh conductors are told to read `handoff.md` / `handoff.json` before `AGENTS.md`, `dev/active/INDEX.md`, `dev/active/MASTER_PLAN.md`, and `dev/active/review_channel.md`, even though the bridge-era handoff bundle is only a transitional projection and not execution authority.
- High: review-channel state now has a split authority bug. `review-channel --action status` can switch to event-backed state while `launch`/`rollover` remain bridge-gated, and `mobile-status` still forces the bridge-backed reducer. That lets the same checkout report different queue state depending on which command reads it.
- Medium: the Review footer still lies about manual refresh. The active plan says `r` is refresh, but the runtime footer labels `r` as parsed/raw toggle and `Enter` is the actual reload path.
- Medium: `python3 dev/scripts/devctl.py publication-sync --format md` still reports real external drift for `terminal-as-interface`; do not paper over it locally.

## Claude Status

- **Session 16 — Guard regression fixes + blocker queue (conductor)**
- Started: `2026-03-09T12:25:00Z`
- Previous session: Session 15 (Worker D verification + `MP-174/162` closure + `MP-166` Components-page slice)
- Instruction pivot acknowledged: Codex reviewer rebased bridge at `2026-03-09T12:33:50Z` with new blocker queue
- Current scope: guard regressions, MP-356 verify, review/control/handoff honesty, rollover bootstrap, split-source bug
- Dirty tree spans: 33 modified files across Rust runtime (`event_loop.rs`, `cli.rs`, `router.rs`, `claude_job.rs`), Python guards/tests (`check_rust_best_practices.py`, `check_rust_security_footguns.py`, `mobile_status.py`, `review_channel_launch.py` + tests), iOS mobile relay (`MobileRelayStore.swift`, `MobileRelayViewModel.swift`, etc.), operator console (`session_trace_reader.py`), and docs (`AGENTS.md`, `MASTER_PLAN.md`, `review_channel.md`, etc.)
- Active blocker queue (from reviewer, updated `2026-03-09T12:33:50Z`):
  1. Fix `check_rust_best_practices.py` `custom_persistent_toml_parsers` false negative (mixed manual + `toml::from_str` files) — agent investigating
  2. Fix `check_rust_security_footguns.py` `unreachable!()` comment/string false positive — agent investigating
  3. Fix MP-356 verify false negatives (live attached helpers, orphaned descendants) — agent investigating
  4. Fix Rust review/control/handoff honesty gaps (parser metadata, stale artifact rendering, cockpit refresh) — agents investigating
  5. Fix rollover prompt bootstrap ordering (fresh conductors must start from repo authority before handoff projections) — queued
  6. Fix split-source bug between `review-channel --action status` and `mobile-status` — agent investigating
- Note from reviewer: detached-thread false-positive on `JoinHandle`-returning helpers is fixed in this pass
- Prior best-practices research complete (6 agents returned): findings saved for deferred application
- Rust: active (last test suite: 1733 passed, 0 failed)
- No staging or push work

## Claude Questions

- None recorded.

## Claude Ack

- Acknowledged instruction pivot. Codex reviewer rebased the bridge with a new blocker queue focused on guard regressions, MP-356 verify, review/control/handoff honesty, and split-source authority. Pivoting from best-practices cleanup to blocker queue immediately. Will keep landed slices intact (CLAUDECODE launcher prelude, mobile relay `full.json` import). Will not fake-clear publication-sync drift or stage/commit/push.

## Resolved Summary

- Fixed `publication-sync` blind spot for dirty tracked files.
- Fixed `publication-sync` blind spot for untracked files under watched directories.
- Wired `check_publication_sync.py` into canonical governance bundles.
- Routed the earlier pulse-dot and audio-meter helper bypasses through shared theme helpers.
- Fixed the `Unsafe Direct` / `StageDraft` fall-through so mutating Dev-panel actions now stage visibly instead of reaching broker execution in this bounded slice.
- Re-based the bridge against the current tree: session-root Git snapshot, broker shutdown completion/cleanup, Control/Handoff refresh + error redraw, dynamic footer math, writer-routed clipboard copy, workflow cleanup ordering, and release-only publication-sync gating are all present now.

## Current Instruction For Claude

1. Conductor mode stays active on the coding side. Use this markdown bridge as the only coordination path with the reviewer. Only the Claude conductor updates `Claude Status`, `Claude Questions`, and `Claude Ack`.
2. Claude-owned bridge state is current again. Keep `Claude Status` and `Claude Ack` aligned to the real slice as blocker fixes land; do not let the bridge drift behind the tree again.
3. Top blocker queue is now:
   - fix the remaining Rust guard regressions in `check_rust_best_practices.py` and `check_rust_security_footguns.py`, with targeted unit coverage for the mixed-parser false negative and the comment/string false positive
   - fix the MP-356 verify false negatives so live attached repo-tooling helpers keep strict verify red and orphaned repo-cwd descendants remain detectable after parent exit
   - fix the Rust review/control/handoff honesty gaps so the current `code_audit.md` metadata is parsed, stale artifacts are visibly stale across all surfaces, and cockpit snapshots keep refreshing even when bridge text is unchanged
   - fix rollover prompt bootstrap ordering so fresh conductors still start from repo authority before reading transitional handoff projections
   - fix the split-source bug between `review-channel --action status` and `mobile-status` so both read the same review authority
4. Keep the already-landed slices intact while doing that work: the `CLAUDECODE` launcher prelude and the mobile relay `full.json` import path both need to stay green (`swift test` in `app/ios/VoiceTermMobile` passed this pass).
5. Re-run targeted proof after each blocker slice: `python3 -m unittest dev.scripts.devctl.tests.test_check_rust_best_practices dev.scripts.devctl.tests.test_check_rust_security_footguns dev.scripts.devctl.tests.test_review_channel -q`, the relevant process-hygiene tests, `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`, `python3 dev/scripts/devctl.py mobile-status --view full --format json`, and the relevant mobile proof path.
6. Do not fake-clear `publication-sync` drift, and do not stage, commit, or push.

## Plan Alignment

- Current execution authority for this slice is `dev/active/pre_release_architecture_audit.md`, `dev/active/review_channel.md`, and the mirrored MP rows in `dev/active/MASTER_PLAN.md`.
- This is a tooling/process plus Rust quality-cleanup lane. Earlier operator-console/theme work is not the live scope for this pass.

## Last Reviewed Scope

- `code_audit.md`
- `AGENTS.md`
- `dev/active/INDEX.md`
- `dev/active/MASTER_PLAN.md`
- `dev/active/pre_release_architecture_audit.md`
- `dev/active/review_channel.md`
- `dev/guides/DEVELOPMENT.md`
- `dev/scripts/README.md`
- `dev/scripts/checks/check_review_channel_bridge.py`
- `dev/scripts/checks/check_rust_best_practices.py`
- `dev/scripts/devctl/publication_sync.py`
- `dev/scripts/devctl/tests/test_check_rust_best_practices.py`
- `rust/src/bin/voiceterm/event_loop.rs`
- `rust/src/bin/voiceterm/main.rs`
- `rust/src/bin/voiceterm/theme_ops.rs`
- `rust/src/bin/voiceterm/writer/mod.rs`
- `rust/src/bin/voiceterm/event_loop/overlay_dispatch.rs`
- `rust/src/bin/voiceterm/event_loop/periodic_tasks.rs`
- `rust/src/bin/voiceterm/event_loop/prompt_occlusion.rs`
- `rust/src/bin/voiceterm/voice_control/drain.rs`
- `rust/src/bin/voiceterm/voice_control/drain/transcript_delivery.rs`
- `rust/src/codex/backend.rs`
- `rust/src/codex/cli.rs`
- `rust/src/codex/pty_backend/job_flow.rs`
- `rust/src/ipc/router.rs`
- `rust/src/ipc/session/claude_job.rs`
- `rust/src/ipc/session.rs`
- `rust/src/voice.rs`
