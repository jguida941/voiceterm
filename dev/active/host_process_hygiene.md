# Host Process Hygiene Plan

**Status**: reopened for follow-up hardening  |  **Last updated**: 2026-03-09 | **Owner:** Tooling/runtime hygiene
Execution plan contract: required
This spec remains execution mirrored in `dev/active/MASTER_PLAN.md` under `MP-356`.

## Scope

Close the host-process visibility gap between repo-local guard runs and the
actual machine state visible in Activity Monitor / `ps`.

This plan covers six outcomes:

1. Make `devctl` process sweeps descendant-aware so leaked PTY child processes
   (for example test harness `cat` children) are reported and cleaned up with
   their parent runtime/test runners.
2. Add one explicit host audit surface in `devctl` so maintainers and AI agents
   can verify that no repo-related processes remain after risky local work.
3. Add one explicit host cleanup surface in `devctl` so orphaned/stale
   repo-related process trees can be reaped safely and re-verified against
   the host process table.
4. Update SDLC docs so post-test and pre-handoff process cleanup/audits become
   an explicit repeatable step instead of relying on manual Activity Monitor
   checks.
5. Extend detection beyond VoiceTerm PTY trees to include orphaned repo-tooling
   wrapper roots and their descendants when those processes are clearly owned by
   this repo's automation surface.
6. Wire the routed runtime/tooling/release bundles so host cleanup is an
   explicit automatic step instead of a handoff-only reminder.

## Execution Checklist

- [x] Add a tracked `devctl` host-process audit command for repo-related
      runtime/test/tooling process trees.
- [x] Add a tracked `devctl` host-process cleanup command that reaps orphaned
      and stale repo-related process trees, then optionally reruns strict
      verification.
- [x] Expand the shared process sweep to follow descendants of matched
      `cargo test --bin voiceterm`, `voiceterm-*`, and stress-session roots.
- [x] Update cleanup ordering so descendant PTY children are terminated before
      parent test runners.
- [x] Expand cleanup targets so orphaned/stale roots bring along their full
      descendant tree, even when some children are newer than the age gate.
- [x] Add regression coverage for descendant detection, strict host-audit
      behavior, cleanup verification, and CLI wiring.
- [x] Teach the host audit/cleanup path to catch orphaned repo-tooling wrapper
      roots (for example stale `zsh -c python3 dev/scripts/...` bundles) and
      their descendants.
- [x] Broaden repo-related detection so repo-cwd background helpers such as
      `python3 -m unittest`, direct shell-script wrappers, and generic helper
      descendants are still classified when their command line no longer says
      `voiceterm` or `dev/scripts`.
- [x] Exclude the current audit command's own process subtree plus ancestor
      tree so repo-tooling detection does not self-report the shell, python
      runner, or `lsof` children launched by `process-audit` /
      `process-cleanup`.
- [x] Update `AGENTS.md`, `dev/guides/DEVELOPMENT.md`,
      `dev/scripts/README.md`, and `dev/README.md` with the new host-audit
      workflow.
- [x] Add `process-cleanup --verify --format md` to the routed
      runtime/tooling/release/post-push bundle authority so the AI/dev default
      lane runs host cleanup without relying only on handoff memory.
- [x] Trace why the still-live `cargo test --bin voiceterm theme` host tree can
      keep detaching orphaned `voiceterm-*` workers / PTY children while the
      parent runner remains active, then land and verify the PTY/watchdog fix.
- [ ] Re-close the reopened false-negative follow-up: catch orphaned
      non-allowlisted repo-cwd descendants after their matched parent exits,
      treat tty-attached repo helpers (`python3 -m pytest`,
      `python3 -m unittest`) as blocking when they detach or linger, and make
      out-of-repo `guard-run --cwd` sweeps clean/audit the actual target repo
      instead of only this checkout.

## Phase 1 Delivery

Phase 1 delivered the descendant-aware host audit/cleanup surfaces, bundle
integration, and runtime leak closure tracked under `MP-356`.

## Progress Log

- 2026-03-09: Codex re-review reopened MP-356 follow-up hardening. Current
  code still has three verified blind spots relative to the earlier
  "pending archive" claim: orphaned non-allowlisted repo-cwd descendants can
  slip once the originally matched parent exits, tty-attached repo helpers
  such as `python3 -m pytest` / `python3 -m unittest` are still
  under-classified, and `guard-run --cwd <other-repo>` still audits/cleans
  this repo instead of the actual target cwd. Keep the doc active until those
  shapes are covered by automation or explicitly retired with focused
  regression proof.
- 2026-03-10: Closed one of the reopened MP-356 false-positive slices. The
  shared skip-pid logic now excludes same-session repo-tooling sibling trees
  when they are clearly part of the active hygiene/check/test run
  (`dev/scripts/devctl.py ...`, `dev/scripts/checks/*.py`, and
  `python -m pytest|unittest` siblings under the current parent shell), and
  the skip now covers each sibling's descendant tree instead of only the root
  pid. Live proof: `python3 dev/scripts/devctl.py hygiene --strict-warnings
  --format md` no longer reports the active local pytest/check subprocesses as
  leaked repo tooling; the remaining publication-sync drift stays informational
  without producing a host-process false positive.
- 2026-03-10: Narrowed the same-parent self-hygiene sibling exemption after a
  follow-up integration review. The skip no longer blanket-matches every
  `python3 dev/scripts/devctl.py ...` sibling under the same shell; it is now
  constrained to the hygiene/check/doc-governance helper shapes that were the
  actual false positives. This keeps same-shell `guard-run`, `review-channel`,
  `data-science`, `process-watch`, and future watchdog/controller helpers
  visible to host-process audits instead of silently exempting them.
- 2026-03-08: Investigated host process leaks after repeated Activity Monitor
  findings. Live host snapshot confirmed orphaned
  `rust/target/debug/deps/voiceterm-*` test runners and descendant PTY child
  `cat` processes were still alive outside the repo sandbox. Code-path review
  found the shared Python sweep only matched a narrow command allowlist and did
  not follow descendant trees, while sandboxed runs could silently skip true
  host inspection.
- 2026-03-08: Landed `devctl process-audit`, descendant-aware process-sweep
  expansion, descendant-first cleanup ordering, regression coverage, and doc
  updates that make host-side process audits explicit after PTY/runtime tests
  and before handoff when host process access is available.
- 2026-03-08: Extended the automation with `devctl process-cleanup
  --verify --format md`, which safely kills orphaned/stale repo-related
  process trees on the real host, expands cleanup roots to their full
  descendant tree so leaked PTY children do not survive age-gated sweeps, and
  turns cleanup plus strict host verification into one repeatable AI/dev step.
- 2026-03-09: Tightened the host-process contract for the live review-channel
  loop. The shared process sweep now classifies attached Codex/Claude conductor
  trees under a dedicated `review_channel_conductor` scope so long-running
  supervised sessions stay visible in `process-audit` / `hygiene` reports but
  no longer fail strict host cleanliness once they cross the 600-second stale
  threshold. Detached/backgrounded conductor trees still fail read-only strict
  audit and cleanup verification as leaked repo processes.
- 2026-03-08: Verification confirmed the new audit surface sees the real host
  leak pattern. `hygiene --strict-warnings` now reports orphaned/stale
  VoiceTerm process trees including descendant PTY children, while
  `process-audit --strict` fails against the current machine state until those
  pre-existing leftovers are cleaned. `docs-check --strict-tooling` remains
  blocked by unrelated pre-existing publication-sync bundle/render drift in the
  dirty worktree.
- 2026-03-08: Ran `devctl process-cleanup --verify --format md` against the
  live host. The first guarded pass reaped 554 stale/orphaned VoiceTerm-owned
  processes and left one still-live recent `cargo test --bin voiceterm theme`
  tree (18 processes) untouched; a second guarded pass reaped 2 newly detached
  orphan children from that same live tree, leaving 14 recent active
  processes visible. Strict verify stayed red for the live tree, which is the
  intended safety stop instead of another stale-process blind spot.
- 2026-03-08: Follow-up strict host audits during that same live `cargo test
  --bin voiceterm theme` run still show newly detached orphaned
  `voiceterm-63464fef37043f6a theme` workers appearing while the parent root
  remains active. The cleanup loop now catches those orphans on repeat passes,
  but the runtime/test-harness root cause remains open under this plan.
- 2026-03-08: Root-caused the remaining runtime leak to the PTY lifeline
  watchdog fork in `rust/src/pty_session/pty.rs`. The helper inherited the
  current `voiceterm-*` test binary image, waited only on the lifeline pipe,
  and could outlive the PTY child when event-loop `build_harness("cat", ...)`
  tests let `cat` exit before the owning session dropped and closed the
  lifeline write fd. Fixed the watchdog to poll for both lifeline closure and
  parent reparenting, then added regression tests that cover both parent-exit
  and pipe-close paths.
- 2026-03-08: Verified the root-cause fix against the actual host workflow on a
  clean baseline. `devctl process-cleanup --verify --format md` first reaped a
  stale 14-process leftover theme tree from the earlier leak; after that,
  `cargo test --bin voiceterm theme -- --nocapture` passed cleanly (`269`
  tests), `devctl process-audit --format md` stayed empty during the live run,
  the required `devctl check --profile quick --skip-fmt --skip-clippy
  --no-parallel` passed post-run, and `devctl process-audit --strict --format
  md` returned zero detected host processes.
- 2026-03-08: Manual host review beyond the VoiceTerm regexes found one missed
  class: an orphaned repo-owned `zsh -c` tooling bundle wrapper (`PPID=1`,
  cwd in this repo) plus a stale `qemu-system-riscv64` descendant still using
  CPU/RSS. The previous automation correctly reported zero VoiceTerm leaks but
  missed this broader repo-tooling orphan tree.
- 2026-03-08: Expanded the shared host sweep to merge two scopes:
  `voiceterm` PTY/runtime roots and `repo_tooling` wrapper roots that execute
  `dev/scripts/**`. The scan now excludes the current audit command's own
  ancestor tree, carries scope labels through descendants, and lets
  `process-audit`, `process-cleanup`, `hygiene`, and `check --profile quick`
  report/clean the same repo-related orphan classes.
- 2026-03-08: Verified the new repo-tooling coverage on the live host.
  `process-audit --strict --format md` reproduced the orphaned `zsh -> qemu`
  tree (`2` processes total, `1` orphaned root + `1` stale active descendant),
  and `process-cleanup --verify --format md` killed `PID 2558` (`qemu`) and
  `PID 1154` (orphaned `zsh`) with a clean strict verify afterward.
- 2026-03-08: Closed the remaining repo-cwd classification gaps for
  non-VoiceTerm helpers. The shared sweep now treats direct shell-script
  wrappers plus repo-cwd background helpers (`python3`, `node`/`npm`, `make`,
  `just`, `screen`/`tmux`, `qemu`, `cat`) as repo-related when they detach
  from their parent tree, and the routed runtime/tooling/release/post-push
  bundle authority now includes `process-cleanup --verify --format md` so the
  default AI/dev execution lane automatically re-runs strict host cleanup.
- 2026-03-08: Hardened the remaining blind spots around non-`--bin voiceterm`
  Rust tests and host-audit false positives. The shared sweep now classifies
  repo-runtime cargo roots plus repo `target/debug|release` test binaries under
  a blocking `repo_runtime` scope, `check --profile quick|fast` automatically
  runs host-side cleanup/verify after raw cargo/test-binary follow-ups, routed
  risk add-ons append that quick follow-up (or direct host cleanup for latency
  / wake-word scripts), and the cwd parser now accepts only real `fcwd`
  entries so unrelated system daemons are not misattributed to this repo.
- 2026-03-08: Final live host verification found and reaped one additional
  orphaned repo-owned helper outside the original VoiceTerm screenshots:
  `python3 -c import subprocess, time; subprocess.Popen(['cat'], cwd=<repo>)`
  (`PID 1988`) plus its `<defunct>` child. `process-cleanup --verify --format
  md` killed both and a follow-up strict host audit returned zero detected
  repo-related processes.
- 2026-03-08: Added one more strictness pass after synthetic live repros
  showed a silent hole: a freshly detached repo-owned helper (`PPID=1`,
  elapsed under the orphan age gate) could make `process-cleanup --verify`
  return success while Activity Monitor would still show it. `process-audit
  --strict` now fails immediately on `recent_detached` repo-related rows
  regardless of scope, `process-cleanup --verify` reports that state
  explicitly and points operators/AI to `process-watch`, and `process-watch`
  now exits zero once it actually recovers to a clean host instead of staying
  red because earlier dirty iterations were preserved in history.
- 2026-03-08: Traced a fresh stale-process report back to two linked causes:
  active AI sessions launched raw `cargo test` commands after the last
  successful host cleanup/watch pass, and one dirty-tree banner test deadlocked
  itself on the shared environment mutex introduced by `test_env.rs`. Sampled
  live stacks showed `banner::tests::with_banner_env_vars` holding the env
  lock while the test body re-entered style-pack env reads. Fixed the banner
  tests to use shared `with_env_overrides` helpers instead of nested local
  lock wrappers, added `devctl guard-run` as the required AI/raw-test path so
  post-run hygiene always runs, and narrowed generic repo-tooling detection so
  attached interactive helpers like a live `python3 -` stdin reader are not
  promoted into stale-failure noise unless they detach/background.

## Session Resume

- Current status: this plan remains active; start from the highest-priority
  open item in `## Execution Checklist` and the latest dated entry in
  `## Progress Log`.
- Next action: keep current-slice decisions and blockers in this file instead
  of chat-only notes, then update this section when the promoted slice
  changes.
- Context rule: treat `dev/active/MASTER_PLAN.md` as tracker authority and
  load only the local sections needed for the active checklist item.

## Audit Evidence

- `python3 -m unittest dev.scripts.devctl.tests.test_process_sweep dev.scripts.devctl.tests.test_process_audit dev.scripts.devctl.tests.test_process_cleanup`
- `python3 dev/scripts/devctl.py list`
- `python3 dev/scripts/devctl.py process-cleanup --dry-run --format md`
- `python3 dev/scripts/devctl.py process-cleanup --verify --format md` (kills
  stale/orphaned repo-related trees; first pass killed 554 stale/orphaned
  processes, second pass killed 2 newly detached orphans, and verify remains
  red only while a recent live `cargo test --bin voiceterm theme` tree stays
  active)
- `python3 dev/scripts/devctl.py process-audit --strict --format json`
- `python3 dev/scripts/devctl.py hygiene --strict-warnings` (fails on real
  orphaned/stale host processes; expected and desired for this session)
- `cargo test lifeline_watch_event_ --manifest-path rust/Cargo.toml -- --nocapture`
- `cargo test pty_overlay_session_parent_sigkill_terminates_child --manifest-path rust/Cargo.toml -- --nocapture`
- `cargo test --bin voiceterm theme --manifest-path rust/Cargo.toml -- --nocapture`
- `python3 dev/scripts/devctl.py process-audit --format md` (during the live
  theme run; no detached VoiceTerm-owned host tree observed)
- `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel`
- `python3 dev/scripts/devctl.py process-audit --strict --format md`
- `python3 dev/scripts/devctl.py process-audit --strict --format md` (after
  widening detection; reproduced an orphaned repo-tooling `zsh -> qemu` tree)
- `python3 dev/scripts/devctl.py process-cleanup --verify --format md` (after
  widening detection; killed the stale orphaned repo-tooling `zsh -> qemu`
  tree and verified zero remaining host processes)
- `python3 -m unittest dev.scripts.devctl.tests.test_check dev.scripts.devctl.tests.test_check_router`
- `python3 dev/scripts/devctl.py process-audit --strict --format md` (after
  repo-runtime cargo/target detection + stricter cwd parsing; clean baseline)
- `python3 dev/scripts/checks/check_bundle_workflow_parity.py`
- `python3 dev/scripts/checks/check_agents_bundle_render.py --write`
- `python3 dev/scripts/devctl.py process-cleanup --verify --format md` (final
  live cleanup of orphaned `python3 -c ... Popen(['cat'], cwd=<repo>)` helper
  plus `<defunct>` child)
- `python3 -m unittest dev.scripts.devctl.tests.test_process_audit dev.scripts.devctl.tests.test_process_cleanup dev.scripts.devctl.tests.test_process_watch dev.scripts.devctl.tests.test_check dev.scripts.devctl.tests.test_check_router`
- `python3 dev/scripts/devctl.py process-audit --strict --format md` (fresh
  synthetic repo-runtime + repo-tooling detached orphans now fail immediately
  via `recent_detached` instead of passing as advisory state)
- `python3 dev/scripts/devctl.py process-watch --cleanup --strict
  --stop-on-clean --iterations 6 --interval-seconds 15 --format md` (live
  synthetic runtime/tooling detached-orphan repro aged into cleanup and
  stopped clean with exit 0)
- `python3 -m unittest dev.scripts.devctl.tests.test_guard_run`
- `python3 dev/scripts/devctl.py process-cleanup --verify --format md` (live
  cleanup of the stale deadlocked banner test trees traced from active
  `claude`/`codex` sessions)
- `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test --bin
  voiceterm build_startup_banner_for_cols_respects_payload_base_theme_lock_over_requested_none
  -- --nocapture`
- `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test --bin
  voiceterm banner::tests -- --nocapture`
- `python3 dev/scripts/checks/check_active_plan_sync.py`
- `python3 dev/scripts/checks/check_multi_agent_sync.py`
- `python3 dev/scripts/checks/check_agents_contract.py`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
