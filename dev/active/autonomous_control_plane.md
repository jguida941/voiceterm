# Autonomous Loop + Mobile Control Plane

Status: execution mirrored in `dev/active/MASTER_PLAN.md` (MP-325..MP-338, MP-340)
Execution plan contract: required
Owner lane: Control-plane/governance

## Scope

Build a production-grade autonomous control plane in this repo first, then
extract a reusable template for other projects.

This plan covers:

1. Ralph loop run-correlation correctness.
2. Real `summary-and-comment` notifications.
3. Bounded mutation remediation loop.
4. Rust containerized mobile control service with SMS-first pilot and richer
   channel support next.
5. Guardrail and traceability hardening for autonomous execution.
6. One unified operator system across Rust overlay and iPhone/SSH surfaces
   using the same controller-state contract.
7. Deterministic learning so repeated loop work is reused through
   artifact-backed playbooks instead of hidden memory.
8. An overlay-native live guard watchdog that can observe Codex/Claude PTY
   traffic plus typed repo actions, derive structured "what the agent is doing
   now" state, and trigger the right repo guard bundle without giving the
   overlay unsafe freeform write authority.

Together with `dev/active/memory_studio.md` and
`dev/active/review_channel.md`, this is one local-first operator system:
Memory supplies durable recall, Review supplies structured coordination, and
the Control Plane supplies execution surfaces plus governance.

## Execution Protocol (Required)

1. Every non-trivial agent run must be anchored to this file or another active
   `dev/active/*.md` execution-plan doc with `Execution plan contract: required`.
2. Agents must not run from memory-only plans. They must:
   - update checklist state before/after major execution steps
   - append dated entries to `## Progress Log`
   - keep `dev/active/MASTER_PLAN.md` MP status aligned with actual completion
3. Multi-agent runs must communicate through the shared active-plan doc updates
   (checklist/progress/audit sections), not ad-hoc hidden state.
4. Any scope drift, policy denial, or blocked automation path must be logged in
   this file with reason and mitigation.

## Locked Decisions

1. Rollout is phased by lane.
2. Template path is staged: repo-first, then standalone template.
3. Safety posture is allowlisted and policy-gated; no unrestricted free-form
   command execution.
4. Mobile strategy defaults to SMS backup first, then richer interactive chat.
5. Rust overlay stays the primary runtime/rendering surface for VoiceTerm.
6. Desktop and phone GUI clients are secondary clients only; operator control
   authority stays on Rust + `devctl`, and PyQt6 now plus any later
   iPhone/Electron/Tauri shell must consume the shared backend rather than
   becoming it.
7. Learning logic must be artifact-driven, replayable, and auditable.
8. SSH is a valid read/debug transport, but it is not the push-notification
   system; true phone pings must ride on notifier adapters over the same
   shared payload the GUI clients render.
9. Overlay-native guard enforcement is allowed only as a typed control-plane
   action. The overlay may observe PTY/session tails, packet artifacts, repo
   diffs, and guard outputs, but it must dispatch bounded `devctl` guard runs
   or controller actions instead of injecting raw shell text into Codex/Claude
   sessions.
10. PTY interception is evidence, not authority. The system should infer
    states such as "editing Python", "running tests", "idle", "awaiting
    review", or "guard failed" from provider I/O plus repo-visible artifacts,
    then project that state into `controller_state` / `review_state` rather
    than treating scraped terminal text as the only source of truth.

## External Inputs

1. OpenClaw-style serialized loop with run lifecycle IDs.
2. GitHub Actions dispatch/event semantics for controlled remote execution.
3. Twilio webhook patterns for inbound/outbound SMS control.
4. Telegram Bot API patterns for interactive control loops.
5. `ntfy` pub/sub patterns for low-friction push updates.
6. `network-monitor-tui` runtime throughput panel patterns for dev-mode
   observability surfaces:
   `https://github.com/jguida941/network-monitor-tui`.
7. `code-link-ide` pairing/notifier ideas for future phone transport adapters,
   without displacing `devctl`/`controller_state` as the source of truth.
8. Local FileHasher-style PyQt theme/chart work plus the `gitui-main/app`
   design reference as visual-density inputs for later phone/desktop shells,
   not runtime dependencies.

## Phase 1 - Harden Existing CodeRabbit Ralph Loop

### 1.1 Run Correlation Fix

- [x] Extend `devctl triage-loop` parser and command with:
  - [x] `--source-run-id`
  - [x] `--source-run-sha`
  - [x] `--source-event` (`workflow_run|workflow_dispatch`)
- [x] Update loop core:
  - [x] Attempt #1 consumes `source-run-id` artifacts when provided.
  - [x] Validate artifact `headSha` matches `source-run-sha` when provided.
  - [x] Fail with explicit reason `source_run_sha_mismatch` on mismatch.
- [x] Update `.github/workflows/coderabbit_ralph_loop.yml`:
  - [x] Pass `github.event.workflow_run.id` and
        `github.event.workflow_run.head_sha` to `triage-loop`.
  - [x] Keep branch fallback behavior for `workflow_dispatch`.

Acceptance:

1. Loop run does not consume unrelated newer triage runs under concurrent
   branch pushes.
2. Report includes `source_run_id`, `source_run_sha`, and correlation result.

### 1.2 Real `summary-and-comment` Behavior

- [x] Add to `devctl triage-loop`:
  - [x] `--notify summary-only|summary-and-comment`
  - [x] `--comment-target auto|pr|commit`
  - [x] `--comment-pr-number` (optional explicit target)
- [x] Implement comment publishing:
  - [x] `auto` resolves PR from backlog artifact metadata when available.
  - [x] `pr` requires an explicit/resolved PR number.
  - [x] `commit` posts commit comment for source SHA.
- [x] Update workflow permissions for comment mode:
  - [x] `pull-requests: write`
  - [x] `contents: write`
- [x] Add idempotency marker to avoid comment spam:
  - [x] Stable marker includes run context (`run_id` + `sha`).
  - [x] Update existing marker comment when present.

Acceptance:

1. `summary-and-comment` produces one canonical updatable comment per target.
2. `summary-only` does not publish comments.

### 1.3 Policy-Gated Triage Fixes + Review Escalation

- [x] Add triage fix-policy evaluation mirroring mutation safety gates:
  - [x] `AUTONOMY_MODE=operate` required for live fix execution.
  - [x] Branch must be in `triage_loop.allowed_branches`.
  - [x] Fix command must match allowlisted prefixes (with optional
        `TRIAGE_LOOP_ALLOWED_PREFIXES` env override).
- [x] Pass `fix_block_reason` into loop core and attempt rows for explicit
      deny-path reason codes.
- [x] Add review-escalation comment upsert path with dedicated marker
      (`coderabbit-ralph-loop-escalation`) so escalation comments coexist with
      status comments.
- [x] Set `escalation_needed=true` when attempts exhaust unresolved medium/high
      backlog so reviewer action requests are deterministic.

Acceptance:

1. No triage fix command executes unless policy gates pass.
2. Policy-denied loops emit explicit reason codes in reports/attempts.
3. Exhausted loops publish one idempotent escalation comment per target.

## Phase 2 - Mutation Remediation Loop (Bounded)

### 2.1 New Command: `devctl mutation-loop`

- [x] Add command interface:
  - [x] `devctl mutation-loop --branch <branch>`
  - [x] `--mode report-only|plan-then-fix|fix-only`
  - [x] `--max-attempts N --threshold 0.80 --emit-bundle ...`
- [x] Inputs:
  - [x] Mutation outcomes artifacts.
  - [x] Optional policy-gated fix command.
- [x] Outputs:
  - [x] `mutation-loop.md`
  - [x] `mutation-loop.json`
  - [x] `mutation-loop-playbook.md`

Behavior:

1. `report-only`:
   - Compute score, freshness/stale age, hotspot list, survivor categories.
   - Emit remediation playbook without executing fixes.
2. `plan-then-fix` / `fix-only`:
   - Execute only allowlisted fix steps.
   - Wait for new mutation run.
   - Stop on max attempts or threshold success.

### 2.2 New Workflow: `.github/workflows/mutation_ralph_loop.yml`

- [x] Trigger on `workflow_run` completion of `Mutation Testing`.
- [x] Add `workflow_dispatch` path.
- [x] Support variables:
  - [x] `MUTATION_LOOP_MODE=report-only|always|failure-only`
  - [x] `MUTATION_EXECUTION_MODE=report-only|plan-then-fix|fix-only`
  - [x] `MUTATION_LOOP_MAX_ATTEMPTS`
  - [x] `MUTATION_LOOP_POLL_SECONDS`
  - [x] `MUTATION_LOOP_TIMEOUT_SECONDS`
  - [x] `MUTATION_LOOP_FIX_COMMAND`
  - [x] `MUTATION_NOTIFY_MODE=summary-only|summary-and-comment`
- [x] Gates:
  - [x] Default mode remains report-only.
  - [x] Auto-fix requires explicit allowlist pass.
  - [x] Emit artifact bundle + summary + optional comment.

Acceptance:

1. Mutation lane is non-blocking by default until explicit promotion.
2. Optional auto-fix mode is bounded and auditable.

### 2.3 Autonomy Controller Loop (Bounded)

- [x] Add `devctl autonomy-loop` command:
  - [x] bounded rounds/hours/tasks controls
  - [x] nested `triage-loop` + `loop-packet` orchestration
  - [x] run-scoped checkpoint packet artifacts
  - [x] queue inbox outputs (`dev/reports/autonomy/queue/inbox`)
  - [x] terminal/action trace lines for phone-forwardable status payloads
  - [x] phone-ready status snapshots (`dev/reports/autonomy/queue/phone/latest.json` + `latest.md`)
  - [x] policy-aware mode downgrade when `AUTONOMY_MODE != operate`
- [x] Add `.github/workflows/autonomy_controller.yml`:
  - [x] `workflow_dispatch` + schedule triggers
  - [x] guarded `devctl autonomy-loop` execution
  - [x] summary + artifact upload (`packets` + `queue`)
  - [x] optional PR promote step (PR create/update + auto-merge request) when
        source branch exists remotely
- [ ] Full branch lifecycle enforcement remains follow-up:
  - [ ] hard fail when branch does not enter merge queue
  - [ ] branch-protection/required-check introspection before promote
  - [ ] phone approval handshake before release-publish actions

## Phase 3 - Rust Containerized Mobile Control Plane

### 3.1 New Service: `voiceterm-control` (Rust)

- [ ] Add read-only endpoints for:
  - [ ] Current loop states (CodeRabbit + mutation).
  - [ ] Latest mutation score and freshness.
  - [ ] CI summaries and failing lanes.
  - [ ] `devctl report/status/triage` snapshots.
- [ ] Add controlled actions for:
  - [ ] Workflow dispatch with constrained inputs.
  - [ ] Pause/resume loop mode toggles.
  - [ ] Re-run report-only loops.
- [ ] Require explicit approval gates for:
  - [ ] Fix-mode execution.
  - [ ] Branch/tag/release-impacting actions.
- [ ] Add client transports over the same shared service instead of separate
      phone/desktop backends:
  - [ ] same-network live mode for trusted local Wi-Fi/LAN clients
  - [ ] secure remote mode for off-LAN/cellular clients through a guarded
        private-network/tunnel adapter; do not expose raw PTY or devctl ports
        directly to the public internet
  - [ ] reconnect/resume semantics so the host Mac keeps controller state,
        session tails, approvals, and long-running plans alive while the phone
        disconnects/reconnects between Wi-Fi and cellular
- [ ] Keep PyQt6, Rust overlay/dev panels, and the iPhone app on this same
      service contract; no GUI surface may become a peer backend for another.

### 3.2 Control API

- [ ] `GET /v1/health`
- [ ] `GET /v1/loops`
- [ ] `GET /v1/mutation`
- [ ] `GET /v1/ci`
- [ ] `POST /v1/actions/dispatch`
- [ ] `POST /v1/actions/mode`
- [ ] `GET /v1/audit`

Security baseline:

- [ ] Signed short-lived session tokens.
- [ ] Role-based scopes (`read`, `operate`, `approve`).
- [ ] Mandatory audit log entries per action.
- [ ] Policy gate before shell/workflow operations.

### 3.3 Phone Adapters

- [ ] First proof path: simple phone ping/alert delivery over the emitted
      `mobile-status` payload so operator-visible state changes can reach the
      iPhone before richer live-control work starts.
- [ ] Keep SSH as a read/debug path and add a real notifier bridge for alerts;
      do not treat SSH polling alone as "push notifications".
- [ ] v1: SMS adapter (Twilio webhook in/out) for backup/pilot.
- [ ] v1.5: `ntfy`/APNs-style push adapter for richer alerts.
- [ ] v2: interactive chat adapter (Telegram-style).

### 3.4 iPhone-First MVP (Single Operator)

Goal: prove the phone path against real repo data and a real notification
signal first, then expand into full typed control.

Scope for MVP:

1. First-party iPhone/iPad app over the same repo-owned mobile bundle and
   later live Rust service used by other controller clients.
2. Simple ping/alert delivery before richer phone-control claims.
3. Real-data parity with the PyQt/Rust operator surfaces where practical so
   the phone is not a toy admin screen with different meanings.
4. Auditable and policy-gated command execution only.

#### MVP Architecture (Current Direction)

- [x] First-party Swift package + generated iOS app shell over the emitted
      `mobile-status` bundle.
- [x] Simulator live-bundle sync path from the current repo state.
- [ ] Backend: Rust `voiceterm-control` service exposes read endpoints and one
      guarded dispatch path, and remains the long-term shared live source for
      Rust, PyQt6, and iPhone clients.
- [ ] Add the first simple ping proof path that alerts the phone when
      Codex/Claude/operator state materially changes, using the same
      `mobile-status` payload and not a second ad-hoc summary format.
- [ ] Keep notification content aligned with the same bundle fields rendered in
      the desktop and phone UI so pings and screens never disagree.
- [ ] Add richer same-data phone views: left-rail plan/work items, agent
      cards, approvals, findings, and repo health that match the PyQt/Rust
      control surfaces closely enough that operators can move between screens
      without relearning the model.
- [ ] Add split/combined terminal-style lane monitoring sourced from
      repo-visible session artifacts first, then from the live Rust service
      once it owns session tails.
- [ ] Add typed phone actions for approve/deny/ack/apply plus bounded
      operator-note / message dispatch, using the same action catalog/policy
      engine as Rust and PyQt6.
- [ ] Add typed plan-item / agent-assignment flows so a phone user can pick a
      plan item and stage it to the right agent through `devctl` /
      `controller_state` instead of freeform chat.
- [ ] Add simple/technical read modes on phone with identical provenance and
      source artifacts behind both modes.
- [ ] Add reconnect/resume semantics so the phone can keep following the same
      long-running host plan across Wi-Fi/cellular changes.
- [ ] Keep Apple-app polish as an explicit product requirement after the simple
      ping proof: dense agent-first UI, high-quality cards, and the same
      underlying repo-owned data model as desktop.
- [ ] Future desktop-web shell work (Electron/Tauri) stays deferred until the
      PyQt6/iPhone/backend contracts are proven stable and must reuse the same
      backend when it happens.
- [ ] Optional dev-mode adapter: import/port `network-monitor-tui` sampling
      model for local throughput/latency panels in `--dev` and phone status
      snapshots (read-only in MVP).
- [ ] Mode-router surface: add isolated runtime mode flags so monitor/tooling
      features do not interfere with default Whisper overlay behavior:
  - [ ] Add a dedicated monitor selector (`--monitor` and/or `--mode monitor`).
  - [ ] Keep default launch path as voice overlay mode unless an explicit mode
        flag is provided.
  - [ ] Route mode-specific initialization (audio/Whisper/backend vs monitor
        sampler/UI) through separate startup branches.

#### Phone Capability Expansion (After Read-First MVP)

- [ ] Replace import-only bundle flow with live phone sessions against the same
      Mac-hosted Rust control service used by the overlay/dev surfaces.
- [ ] Add iPhone voice input as transcript-to-action, not raw terminal
      ownership:
  - [ ] push-to-talk captures speech on iPhone
  - [ ] STT result becomes a typed `action_request`, staged note, or review
        packet
  - [ ] no blind freeform PTY injection in the first live phone release
- [ ] Add yes/no approval UX for `operator_approval_required` packets:
  - [ ] one-tap `Approve`
  - [ ] one-tap `Deny`
  - [ ] optional short operator note attached to the decision
- [ ] Add structured operator messaging from phone:
  - [ ] send operator note to Codex/Claude lane
  - [ ] stage re-review request / next-slice prompt / packet draft
  - [ ] keep all messages replayable and auditable under the same review/control
        artifact model
- [ ] Add live terminal/session visibility on phone from the same repo-backed
      session-tail artifacts or later `controller_state` stream used by the
      overlay and desktop clients.
- [ ] Preserve overlay parity: phone controls and overlay controls must resolve
      through the same typed action router, policy engine, and audit trail.

#### Overlay-Native Live Guard Watchdog Intake

- [ ] Add a passive activity collector for Codex/Claude sessions that fuses PTY
      output, repo-visible session artifacts, and typed action packets into one
      structured `agent_activity` / `controller_state` view.
- [ ] Define the first activity states the watchdog can classify without
      guessing: `editing`, `running_guard`, `running_tests`, `waiting_on_peer`,
      `awaiting_operator`, `idle`, `guard_failed`, `guard_passed`.
- [ ] Add a deterministic guard router that maps those states plus changed-path
      signals to the right repo guard family (`python`, `rust`, `docs`,
      `tooling`, or focused single-check paths) instead of running the whole
      bundle on every token.
- [ ] Keep the first watchdog mode advisory/read-only: surface findings in the
      overlay/review channel and require typed follow-up actions before any
      automatic remediation or session interruption.
- [ ] If/when automatic enforcement is promoted, route it through the same
      allowlisted `devctl`/controller-action catalog and approval policy used
      by Ralph/operator actions; no raw PTY command injection as the primary
      enforcement path.
- [ ] Record guard-trigger provenance in repo-visible artifacts: what activity
      was observed, which guard ran, what files/scopes triggered it, and what
      outcome was projected back to the overlay.
- [ ] Prove the watchdog does not thrash: debounce repeated triggers, avoid
      rerunning the same guard on unchanged state, and pause enforcement while
      the same task/hash/command is already being validated.
- [ ] Add a scientific impact-study protocol for the watchdog:
  - [ ] capture matched before/after artifacts for each guarded coding episode:
        prompt/task id, provider, files changed, guard family triggered,
        pre-guard diff, post-guard diff, guard result, test result, and final
        reviewer verdict
  - [ ] define primary outcome metrics before implementation claims:
        first-pass guard pass rate, time-to-green, escaped-review findings per
        task, rework loops per task, mutation-score delta where available, and
        duplicate/shape/guard violation counts before vs after watchdog action
  - [ ] use paired/matched analysis by task or coding episode instead of
        comparing unrelated sessions
  - [ ] report effect size plus confidence interval, not only p-values
  - [ ] prefer robust non-parametric analysis for small or non-normal samples
        (for example probability of superiority or Cliff's delta with 95%
        confidence intervals, plus Wilcoxon/Brunner-Munzel style hypothesis
        tests when appropriate)
  - [ ] set practical-significance thresholds up front so "statistically
        significant but operationally tiny" results do not count as success
  - [ ] require repeated runs across providers/tasks before promotion claims:
        Codex-only, Claude-only, and shared review-channel loop episodes
- [ ] Add a repo-owned analytics version of the watchdog study:
  - [ ] define a canonical episode schema for `guarded_coding_episode.json`
        / `.jsonl` rows with:
        episode id, task id, provider, session id, reviewed hash, prompt
        fingerprint, changed files, guard family, before/after diff stats,
        terminal-derived timing metrics, guard/test outcomes, and reviewer
        verdict
  - [ ] capture terminal-derived speed/latency metrics when available:
        time from first edit to first guard trigger, time from guard trigger to
        result, time from first edit to green, idle gaps, retry count,
        command/test/guard runtime, and review-to-fix turnaround
  - [ ] capture code-shape/productivity metrics:
        lines added/removed, files touched, diff churn, duplicate violations,
        shape violations, lint/guard counts before vs after, and pass/fail
        sequence count
  - [ ] capture collaboration metrics for the shared Codex/Claude system:
        reviewer findings per episode, coder rework loops, stale-peer pauses,
        handoff count, and escaped findings found only after the coding episode
        supposedly finished
  - [ ] define dashboard/report outputs for the analytics layer:
        speed delta, quality delta, guard-hit heatmaps, provider comparison,
        per-guard win rate, false-positive rate, and time-to-green trend lines
  - [ ] separate exploratory metrics from decision metrics:
        only predeclared primary metrics can justify promotion claims; all
        other pulled terminal signals stay exploratory until validated
  - [ ] add a minimum-sample/power rule for claims:
        do not ship "watchdog improves coding" claims from a tiny anecdotal
        sample; keep a staged threshold for pilot, provisional, and promotion
        evidence
- [ ] Add a learning-corpus lane for future model/ranker work:
  - [ ] store the matched before/after guarded episodes under a repo-visible
        learning dataset root with provenance and privacy controls
  - [ ] keep first-generation learning deterministic and retrieval-based
        (fingerprint -> playbook -> confidence) before training any ML model
  - [ ] treat ML as a later ranking/prediction layer over the same corpus:
        predict likely guard family, likely failure mode, likely remediation
        playbook, or expected time-to-green
  - [ ] require offline evaluation against held-out episodes before any live ML
        promotion, using the same primary outcome metrics and confidence
        intervals as the deterministic watchdog study

##### Guarded Coding Episode Schema Draft

Repo-visible artifact roots:

- `dev/reports/autonomy/watchdog/episodes/guarded_coding_episode.jsonl`
- `dev/reports/autonomy/watchdog/episodes/<episode_id>/summary.json`
- `dev/reports/autonomy/watchdog/episodes/<episode_id>/before.patch`
- `dev/reports/autonomy/watchdog/episodes/<episode_id>/after.patch`
- `dev/reports/autonomy/watchdog/analytics/latest/`

Canonical row fields for `guarded_coding_episode.jsonl`:

- `episode_id`
- `task_id`
- `plan_id`
- `controller_run_id`
- `provider`
  Allowed values for v1: `unknown | codex | claude | shared`
- `session_id`
- `peer_session_id`
- `reviewed_worktree_hash_before`
- `reviewed_worktree_hash_after`
- `prompt_fingerprint`
- `activity_state_before`
- `activity_state_after`
- `guard_family`
  Allowed values for v1: `python | rust | docs | tooling | mixed | targeted`
- `guard_command_id`
  Examples: `check_python_global_mutable`, `check_code_shape`,
  `devctl check --profile quick`
- `trigger_reason`
  Examples: `python_edit_detected`, `review_finding_posted`,
  `retry_after_guard_fail`, `pre_handoff_validation`
- `files_changed`
- `file_count`
- `lines_added_before_guard`
- `lines_removed_before_guard`
- `lines_added_after_guard`
- `lines_removed_after_guard`
- `diff_churn_before_guard`
- `diff_churn_after_guard`
- `guard_started_at_utc`
- `guard_finished_at_utc`
- `episode_started_at_utc`
- `episode_finished_at_utc`
- `first_edit_at_utc`
- `first_guard_failure_at_utc`
- `first_green_at_utc`
- `terminal_active_seconds`
- `terminal_idle_seconds`
- `guard_runtime_seconds`
- `test_runtime_seconds`
- `review_to_fix_seconds`
- `time_to_green_seconds`
- `retry_count`
- `guard_fail_count_before_green`
- `test_fail_count_before_green`
- `review_findings_count`
- `escaped_findings_count`
- `handoff_count`
- `stale_peer_pause_count`
- `shape_violations_before`
- `shape_violations_after`
- `duplication_violations_before`
- `duplication_violations_after`
- `lint_or_guard_violations_before`
- `lint_or_guard_violations_after`
- `mutation_score_before`
- `mutation_score_after`
- `guard_result`
  Allowed values for v1: `pass | fail | skipped | noisy`
- `test_result`
  Allowed values for v1: `pass | fail | not_run`
- `reviewer_verdict`
  Allowed values for v1: `accepted | accepted_with_followups | rejected | deferred`
- `evidence_refs`
- `notes`

Derived metric formulas for reports/dashboards:

- `diff_churn = lines_added + lines_removed`
- `guard_latency_seconds = guard_started_at_utc - first_edit_at_utc`
- `post_guard_settle_seconds = first_green_at_utc - guard_finished_at_utc`
- `episode_cycle_seconds = episode_finished_at_utc - episode_started_at_utc`
- `guard_failure_density = guard_fail_count_before_green / max(file_count, 1)`
- `review_escape_rate = escaped_findings_count / max(review_findings_count + escaped_findings_count, 1)`
- `rework_loop_rate = retry_count / max(1, file_count)`
- `violation_reduction_abs = lint_or_guard_violations_before - lint_or_guard_violations_after`
- `violation_reduction_pct = violation_reduction_abs / max(lint_or_guard_violations_before, 1)`
- `shape_reduction_abs = shape_violations_before - shape_violations_after`
- `duplication_reduction_abs = duplication_violations_before - duplication_violations_after`
- `mutation_delta = mutation_score_after - mutation_score_before`
- `productivity_to_green = diff_churn_after_guard / max(time_to_green_seconds, 1)`

Primary promotion metrics for the watchdog:

1. `time_to_green_seconds`
2. `guard_fail_count_before_green`
3. `escaped_findings_count`
4. `lint_or_guard_violations_after`
5. `reviewer_verdict` mapped to binary success:
   `accepted | accepted_with_followups = success`, everything else = not success

Secondary/exploratory metrics:

- `terminal_idle_seconds`
- `handoff_count`
- `stale_peer_pause_count`
- `productivity_to_green`
- `mutation_delta`
- provider-to-provider deltas
- per-guard-family false-positive/noise rates

Minimum evidence tiers for claims:

1. `pilot`: at least `20` paired episodes, no release/publicity claims
2. `provisional`: at least `50` paired episodes across `codex`, `claude`, and
   `shared` episodes, with confidence intervals excluding zero for at least two
   primary metrics
3. `promotion`: at least `100` paired episodes with repeated wins across
   providers/task classes and no major regression in any primary metric

Decision rule for "watchdog helps":

1. At least two primary metrics improve with predefined practical-significance
   thresholds.
2. No primary metric regresses materially.
3. Confidence intervals support the direction of improvement.
4. The result repeats across more than one provider/task family.

Planned analytics outputs:

- `watchdog_summary.json`
- `watchdog_summary.md`
- `speed_delta.json`
- `quality_delta.json`
- `provider_comparison.json`
- `guard_family_heatmap.json`
- `time_to_green_timeseries.json`
- `false_positive_report.json`
- later dashboard/chart renderers over the same artifacts

#### Off-LAN / Cellular Remote Access

- [ ] Support remote iPhone access when the Mac is online at home and the phone
      is off the local Wi-Fi network.
- [ ] Preferred architecture: private-network / zero-trust adapter in front of
      `voiceterm-control` (WireGuard/Tailscale-class topology first; public
      tunnel/reverse-proxy only after equivalent auth, audit, and rate-limit
      guarantees are proven).
- [ ] Required remote behavior:
  - [ ] phone can reconnect over cellular and see the same live controller
        state, session tails, approvals, and plan progress already running on
        the host Mac
  - [ ] long-running review/autonomy plans continue on the host even while no
        client is connected
  - [ ] reconnect does not create a second controller session or fork hidden
        state
- [ ] Required remote security:
  - [ ] short-lived signed sessions/tokens
  - [ ] explicit device/operator identity
  - [ ] replay protection
  - [ ] audit log for every remote action
  - [ ] operator approval remains mandatory for risky/destructive actions even
        over remote access
- [ ] Explicitly out of scope for the first remote slice:
  - [ ] direct public exposure of raw terminal/PTY ports
  - [ ] unrestricted shell access from phone
  - [ ] bypassing the typed action router because the client is remote

#### MVP Command Set

- [ ] Read-only commands:
  - [ ] View current loop status.
  - [ ] View latest unresolved medium/high count.
  - [ ] View last 5 attempts with run URL + conclusion.
- [ ] One write command:
  - [ ] Dispatch `triage-loop` in `report-only` mode only.
- [ ] Explicitly out-of-scope for MVP:
  - [ ] `plan-then-fix` remote triggering.
  - [ ] Release/tag/branch mutating operations.

#### Notification Contract

- [ ] Add notifier plumbing to `triage-loop`:
  - [ ] `summary-only` sends final result push.
  - [ ] optional attempt updates (`attempt-start`, `attempt-done`).
- [ ] Required message fields:
  - [ ] repo
  - [ ] branch
  - [ ] run URL
  - [ ] unresolved count
  - [ ] mode
  - [ ] reason/status
- [ ] Delivery safety:
  - [ ] idempotency key per loop run
  - [ ] retry with capped backoff
  - [ ] failure audit record when notify send fails

#### Security and Ops for MVP

- [ ] Auth: short-lived signed tokens for phone client sessions.
- [ ] Policy gate: only allowlisted workflow/action inputs from phone.
- [ ] Audit: persist all phone-originated actions with actor + timestamp +
      outcome.
- [ ] Kill switch: `AUTONOMY_MODE=read-only` default until soak window passes.

#### MVP Success Criteria

1. Phone can reliably view live Ralph state and latest artifacts.
2. Phone can trigger only `report-only` loop dispatch and receive status push.
3. Every remote action and notify attempt is traceable in audit logs.
4. No uncontrolled shell execution paths are introduced.

### 3.5 Unified Architect Controller Plan (Ralph + Agents + Rust TUI + iPhone)

Target outcome:

1. Architect can run and steer the autonomous loop from either Rust TUI Dev
   mode or iPhone controller with the same underlying state model.
2. Loop can execute bounded multi-agent remediation cycles (plan -> implement
   -> review -> verify -> retry) until acceptance criteria are met or policy
   limits stop execution.
3. Every decision/action remains policy-gated, replay-safe, and audit-traceable.

Execution model:

1. Loop producer:
   - `triage-loop` + `mutation-loop` + `autonomy-loop` emit canonical state and
     checkpoint packets.
2. Agent relay:
   - reviewer/secondary-agent suggestions are ingested as structured packets,
     never free-form hidden state.
3. Operator surfaces:
   - Rust TUI `--dev` panel consumes local control-plane snapshots.
   - iPhone controller consumes the same snapshots via SSH/API adapters.
4. Policy enforcement:
   - all write actions flow through command/workflow allowlists + bounded
     attempt/hour/task caps + `AUTONOMY_MODE` gating.

Unified data contract backlog:

- [ ] Add canonical `controller_state` payload schema with stable fields for:
  - shared header (`event_id`, `session_id`, `project_id`, `trace_id`,
    `timestamp_utc`, `source`, `event_type`),
  - run identity (`plan_id`, `controller_run_id`, branch, mode),
  - loop status (`phase`, `reason`, unresolved/hotspot score state),
  - agent relay messages (`from_agent`, `to_agent`, `recommendation`,
    `evidence_refs`, `confidence`),
  - operator actions (`requested_action`, `policy_result`, `approval_required`),
  - audit refs (`event_id`, `idempotency_key`, `nonce`, `expires_at`).
- [ ] Keep MP-355 (`dev/active/review_channel.md`) as the review-focused schema
      slice of this contract rather than a parallel authority: MP-340 retains
      umbrella `controller_state` naming/projection ownership plus the pending
      `ADR-0027`/`ADR-0028` backlog, while MP-355 owns the concrete
      `review_event`/`review_state` packet details, inbox/ack/watch/history
      semantics, and shared-screen layout. Shared fields must stay name- and
      meaning-compatible across both plans.
- [ ] Keep control-plane and review artifacts memory-compatible: the temporary
      `bridge.md` bridge today, and `review_state` / `controller_state`
      later, must compile into Memory `session_handoff` / compaction-survival
      inputs so current blockers, next action, and audit refs survive agent
      restart or context loss without hidden memory-only coordination.
- [ ] Freeze one shared event-header mapping with Memory Studio so
      review/control artifacts normalize losslessly into the canonical memory
      envelope instead of each subsystem inventing near-duplicate header names.
- [ ] Add memory-backed handoff attachments: review/control packets may carry
      `context_pack_refs` for `task_pack`, `handoff_pack`, and `survival_index`;
      after `MS-G18` is green, `survival_index` becomes the default compact
      cross-agent handoff attachment.
- [ ] Route cross-provider handoffs through Memory adapter profiles
      (`codex`, `claude`, `gemini`) so the receiving backend gets a
      provider-shaped projection while canonical JSON provenance stays shared.
- [ ] Emit multi-view projections from one source state:
  - `full.json`, `compact.json`, `trace.ndjson`, `actions.json`, `latest.md`.
- [ ] Add a unified timeline/replay projection that merges controller,
      review-channel, and memory traces into one time-sorted operator view once
      the base Phase-1/2 artifacts are stable.
- [ ] Add chart-ready metric snapshots:
  - loop throughput, cycle success rate, unresolved-count trend, mutation-score
    trend, script-only vs AI-assisted vs manual mix.

Operator experience backlog:

- [x] Add `devctl phone-status` command (`--view full|compact|trace|actions`)
      for iPhone SSH-first usage.
- [x] Add `devctl controller-action` command with safe subset first:
  - `dispatch-report-only`
  - `pause-loop`
  - `resume-loop`
  - `refresh-status`
- [ ] Add Rust TUI Dev panel widgets for:
  - current controller phase/reason,
  - latest source run URL/SHA,
  - recent agent relay packets,
  - policy denials and required approvals,
  - all-agent job board state (job, status, waiting-on, freshness, owner).
- [ ] Land an operator-cockpit MVP on top of the existing Rust Dev panel first,
      then let MP-336 add a dedicated monitor startup path once the mode router
      exists:
  - [ ] `--dev` can open the cockpit immediately with read-first pages while
        preserving the current voice-first default path when the user does not
        opt in.
  - [ ] `--monitor` / `--mode monitor` later route directly into the same
        cockpit without booting normal audio/Whisper startup, but they must
        reuse the same page/view models rather than fork a second UI.
  - [ ] Control page reads the same controller projections already produced for
        `phone-status` (`phase`, `reason`, unresolved count, next actions,
        branch/run URL, pause/resume state, latest action result).
  - [ ] Review page reads the sanctioned live review artifact for the current
        phase: `bridge.md` in the temporary bridge era, then
        `review_state`/`review_event` projections once MP-355 Phase 1 lands.
  - [x] Actions page exposes the existing safe operator verbs first
        (`refresh-status`, `pause-loop`, `resume-loop`, `dispatch-report-only`)
        and now also carries review launch dry-run/live plus rollover actions
        with review/controller JSON summaries, before any broader write path is
        added.
  - [ ] Add an agent-board section that shows all active agents plus current
        job, packet/activity freshness, waiting-on state, and current script
        profile from the same typed registry/projection used by review-channel
        surfaces.
  - [ ] Handoff page renders generated fresh-conversation prompts, next-slice
        packets, and resume bundles from current plan/review/controller state.
  - [ ] Packet/application behavior stays staged-first: the overlay may preview
        or draft packets for a PTY, but it must not bypass the current explicit
        staging/confirmation rules.
- [ ] Add developer-facing visibility on top of the operator cockpit so `--dev`
      becomes a practical live-debug surface rather than only a command menu:
  - [ ] raw artifact inspector for current `controller_state`, `phone-status`,
        `bridge.md`, and later `review_state` payloads
  - [ ] change badges/toasts when review or controller artifacts update
  - [ ] command/audit tail showing recent `devctl` actions, policy denials, and
        packet/apply outcomes
  - [ ] packet-draft preview lane with explicit `stage only` / `copy prompt`
        affordances
  - [ ] typed agent controls that call repo-owned handlers for retask/pause/
        resume/rereview actions instead of embedding unscripted orchestration
        logic in the UI
  - [ ] geometry/runtime diagnostics (host, rows/cols, reserved-row state,
        prompt suppression state, backend/provider identity)
  - [ ] dev-log/session playback shortcuts using the existing dev-event JSONL
        store
  - [ ] throughput/latency mini-panels once MP-336 imports the
        `network-monitor-tui` primitives
- [ ] Add iPhone controller read-first surface parity with Rust Dev panel
      fields, then stage guarded write controls. (`2026-03-09` partial:
      added `devctl mobile-status` as the first merged SSH-safe read surface;
      it refreshes bridge-backed review-channel state, combines it with
      autonomy `phone-status`, and emits compact/full/alert/actions mobile
      projections for future phone UI and notifier clients.)
- [ ] Add an explicit simulator/device proving harness around the same shared
      control contract so phone work stays testable and honest during the
      transition:
  - [x] `devctl mobile-app --action simulator-demo` builds, installs, syncs,
        and launches the real iPhone app against repo-backed bundle data.
  - [x] `devctl mobile-app --action simulator-demo --live-review` refreshes
        the current review-channel state first, then syncs that live
        Ralph/review projection bundle into the simulator so testing is not
        limited to sample data.
  - [x] `devctl mobile-app --action device-install` is the real signed
        `xcodebuild` + `devicectl` install/launch path when a trusted iPhone
        and Apple Development Team are available.
  - [ ] Extend the proving harness so one command can verify controller-state
        parity across Rust `--dev`, the mobile app, and the future live phone
        transport before any broader write path is promoted.

Autonomous loop orchestration backlog:

- [ ] Add explicit loop stage machine:
  - `triage` -> `plan` -> `fix` -> `verify` -> `review` -> `promote` ->
    `report`.
- [ ] Add reviewer-agent feedback packet lane so reviewer output can be consumed
      by the running loop without chat-copy/manual glue.
- [ ] Add stop/retry policy by stage:
  - max retries per stage,
  - escalation to architect on repeated deny/failure,
  - required green CI + gate checks before promote.

Acceptance criteria for this unified plan:

1. Same run state and action history is visible from Rust Dev panel and iPhone.
2. Architect can safely trigger/stop bounded loops from phone without shelling
   into ad-hoc commands.
3. Agent-review feedback is packetized and consumed by loop automation with no
   hidden memory-only handoff.
4. Audit output can reconstruct every loop stage transition and operator action.

### 3.6 ADR Backlog (Required for Scope Control)

Accepted control-plane ADRs for unified controller state contract and agent
relay packet protocol have landed (see `dev/adr/0027-*` and `dev/adr/0028-*`).

Remaining ADR backlog required to keep AI + dev execution aligned as autonomy grows:

- [ ] `ADR-0029` Operator action policy model (approval + replay + deny semantics).
- [ ] `ADR-0030` Phone adapter architecture (SSH-first + push/SMS/chat layering).
- [ ] `ADR-0030` must now also lock the live phone transport story:
  - [ ] same-network Rust-hosted client mode
  - [ ] off-LAN/cellular secure adapter mode
  - [ ] reconnect/resume semantics for long-running plans and live session tails
  - [ ] why public raw PTY exposure remains forbidden
- [ ] `ADR-0031` Rust Dev panel control-plane boundary (non-interference contract).
- [ ] `ADR-0032` Autonomy stage machine (triage/plan/fix/verify/review/promote).
- [ ] `ADR-0033` Metrics + scientific audit method (KPI definitions + promotion gates).
- [ ] `ADR-0034` Template extraction contract (what must be standardized before reuse).

ADR delivery rule for this track:

1. No major autonomy/mobile feature is marked complete without the corresponding
   ADR landing (or an explicit temporary waiver entry in this file + MASTER_PLAN).
2. ADRs must include guardrails, failure modes, rollback path, and test evidence
   requirements.
3. ADR IDs and MP scope linkage must be reflected in both this file and
   `dev/active/MASTER_PLAN.md`.

### 3.7 Unified Operator Surfaces (Rust Overlay + iPhone/SSH)

Goal: one control system, multiple clients, no behavior drift.

Implementation scope:

- [ ] Keep one canonical `controller_state` source artifact and API projection.
      Current `phone-status` / `controller-action` payloads plus Rust Dev-panel
      snapshot builders are interim projections only and do not satisfy this
      closure target by themselves.
- [ ] Rust `--dev` panel reads local `controller_state` projections directly.
- [ ] Keep iPhone surfaces (SSH read + API/PWA) bound to the same projections.
- [ ] Keep iPhone, Rust overlay, and desktop operator surfaces on the same
      Rust-owned state model and typed action router, with markdown reduced to
      derived/operator-facing coordination only.
- [ ] Keep desktop GUI clients out of active scope unless a new MP reactivation
      item lands with explicit policy and parity gates.
- [ ] Require parity tests across Rust + phone projections before enabling new
      write actions.
- [ ] Pull the Memory Studio proving outputs directly into this closure path:
  `task_pack`, `session_handoff`, `survival_index`, and provider-shaped
  `context_pack_refs` must be attachable from the same `controller_state` /
  `review_state` flow so phone, Rust, and future desktop clients all see the
  same handoff evidence and next-task context.
- [ ] Keep provider choice typed and shared instead of hardcoded per client:
  the canonical state/action model must carry provider profile and lane/job
  routing (`codex`, `claude`, `gemini`, later others) so the phone can steer
  "AI of choice" through the same allowlisted host execution path the overlay
  and operator surfaces use.

Implementation order:

1. Land `controller_state` schema and projection files (`full`, `compact`,
   `trace`, `actions`) as source of truth.
2. Wire Rust Dev panel and `devctl phone-status` to that schema first.
3. Expose the same schema through Mac-hosted live phone transport on the local
   network so the iPhone can stop depending on imported bundles.
4. Add one guarded write action (`dispatch-report-only`) and verify parity.
5. Add secure off-LAN/cellular connectivity through the approved remote
   adapter path; prove reconnect/resume behavior against the same host session.
6. Expand write actions only after replay/auth/rate-limit gates are green.
7. Promote provider-aware retask/continue flows only after the same request can
   be expressed and audited identically from Rust, mobile, and review-channel
   surfaces.

Acceptance:

1. A state change appears the same in Rust Dev panel and iPhone/SSH surfaces.
2. Action outcomes and denials are identical across clients.
3. No client bypasses policy gates for workflow/shell actions.
4. Operator can monitor and steer bounded loops from any client safely.
5. Memory-backed handoff artifacts and provider-shaped task context resolve the
   same way from Rust, phone, and review surfaces.

### 3.7.1 Operator Cockpit MVP (`--dev` first, `--monitor` next)

Goal: give the operator one in-repo cockpit for live review/control/handoff
without waiting for the full long-range shared-screen stack.

Implementation scope:

- [ ] Reuse the existing Dev panel shell, broker, and periodic refresh loop as
      the MVP host surface; do not invent a second Rust-side control console.
- [ ] Add page/tab routing inside the Dev panel for `Control`, `Ops`,
      `Review`, `Actions`, and `Handoff`.
- [ ] Use the new `Ops` page as the Rust-first operational telemetry lane for
      host-process hygiene, triage summaries, and future external monitor
      adapters; do not bolt those readouts into Theme Studio or a parallel
      control surface.
- [ ] Keep the first delivery read-first by default, with guarded action rows
      and explicit staged packet previews for any PTY-targeted output.
- [ ] Make the cockpit read as one collaborative terminal-native system even
      while Codex/Claude keep separate PTY ownership underneath: the operator
      should be able to see packet handoffs, staged drafts, current target
      state, and who is waiting on whom without leaving the shared surface.
- [ ] Render both parsed and raw review artifacts:
  - [ ] parsed view for current verdict/findings/instruction/ack/poll status
  - [ ] raw markdown view for the literal `bridge.md` bridge while it
        remains the sanctioned temporary authority projection
- [ ] Add controlled overlay editing only for bounded fields/actions:
  - [ ] rewrite `Current Instruction For Claude`
  - [ ] promote next unchecked scoped plan item
  - [ ] append operator note / request re-review
  - [ ] generate fresh-conversation prompts / resume bundle
- [ ] Keep packet output staged into the existing terminal-draft path first;
      no blind auto-send into live Codex/Claude sessions in the MVP.
- [ ] When MP-336 lands, let `--monitor` / `--mode monitor` open this same
      cockpit directly with voice/audio startup skipped.

Acceptance:

1. The user can stay inside VoiceTerm to see review state, controller state,
   next-slice direction, handoff prompts, and cross-agent packet flow as one
   collaborative surface.
2. The MVP reuses existing Dev panel/broker/periodic-task primitives instead
   of introducing a parallel control UI.
3. Any instruction or packet emitted from the cockpit remains auditable and
   staged before injection.

### 3.7.2 Developer-Only Surface Backlog

Goal: make `--dev` valuable for active debugging and operator trust-building,
not just for autonomy control.

Backlog:

- [ ] Add a Git lane with read-first repo state that mirrors existing guarded
      repo tooling instead of shelling out ad hoc:
  - [ ] branch, dirty-tree, ahead/behind, changed-file, and recent-commit views
  - [ ] diff/log/status summaries sourced from existing `devctl`/git report
        helpers where possible
  - [ ] commit-range summaries and release-note/change-digest previews for
        current work
- [ ] Add a guarded Git write lane only after read-first flows are stable:
  - [ ] explicit stage/commit/push/sync actions with preview + confirm steps
  - [ ] branch-policy, clean-tree, and local-validation gates preserved from
        repo policy; push/publish/tag paths remain operator-approval-required
  - [ ] no destructive git operations (`reset --hard`, checkout discards, etc.)
        without a separate explicit policy decision
- [ ] Add a GitHub/CI lane on top of the existing `gh` + workflow tooling:
  - [ ] `gh auth status` and auth-health rendering first
  - [ ] device-flow/login-helper guidance before any embedded auth UX attempt
  - [ ] workflow/run status, failed-lane inspection, and guarded rerun/dispatch
        affordances for approved workflows
  - [ ] PR/release gate summaries and CI deep links using existing
        `devctl status`, `orchestrate-status`, `orchestrate-watch`, and
        release-gate outputs
- [ ] Add an allowlisted script/catalog lane rather than arbitrary command
      execution:
  - [ ] surface catalogued `devctl` commands and approved Python/script
        wrappers with labels, docs, mutating/read-only markers, and JSON output
        expectations
  - [ ] route execution through the existing Dev broker/packet path or a typed
        successor, not through freeform `python3 <anything>` entry
  - [ ] preserve dry-run and audit logging for any mutating action
- [ ] Add a memory proving lane that uses the shipped foundations before more
      advanced memory automation is turned on:
  - [x] current memory mode/capture health/event-count/status
  - [x] dedicated read-only Memory tab with visible-tab refresh plus
        ingest/review/boot-pack/handoff preview sections
  - [ ] on-demand `boot_pack`, `task_pack`, `session_handoff`, and
        `survival_index` previews
  - [ ] packet/handoff attachment by `context_pack_refs`
  - [ ] read-only query/browse path before any memory-driven action suggestion
        is allowed to steer write behavior
- [ ] Add a live artifact explorer for the latest markdown/JSON projections and
      protected runtime report roots.
- [ ] Add command profiler rows showing last run duration, failure reason, and
      recent stderr excerpts for brokered commands.
- [ ] Add HUD/render diagnostics useful during overlay bugs:
      prompt-occlusion state, reserved-row budget, geometry churn, repaint
      counters, and backend-specific compatibility flags.
- [ ] Add voice/debug diagnostics useful during capture bugs:
      active voice mode, VAD state, meter summary, wake-word state, last
      transcript/send decision reason.
- [ ] Add packet and handoff tooling:
      copy prompt, copy packet JSON/markdown, stage to draft, and inspect last
      applied packet outcome.
- [ ] Add retention-safe links/shortcuts into dev-session logs, memory/handoff
      outputs, and autonomy digest bundles.
- [ ] Add read-only throughput/latency charts after MP-336 imports the monitor
      primitives.

### 3.7.3 Staged Proof Plan For One Operator System

Goal: prove the combined review/control/git/CI/script/memory architecture a
piece at a time using existing repo primitives before expanding write power.

Execution ladder:

1. Read-only cockpit:
   - controller/review status, git state, CI state, artifact explorer, memory
     status, and generated handoff prompts
2. Guarded action cockpit:
   - existing safe controller actions plus allowlisted script/catalog actions
     with preview, dry-run, and audit evidence
3. Guarded repo-ops cockpit:
   - staged commit/push/sync helpers, GitHub workflow dispatch/rerun helpers,
     and CI drill-down under explicit approval/policy gates
4. Memory-backed handoff cockpit:
   - `session_handoff`, `task_pack`, and `survival_index` generation attached
     into review/control packets and fresh-conversation prompts
5. Advanced learning/automation:
   - repetition mining, playbook proposals, and memory-informed suggestions
     only after the first four stages are stable and auditable

Delivery rules:

- [ ] Favor typed/allowlisted actions over arbitrary shell access.
- [ ] Favor generated packets/prompts/drafts over blind live-session injection.
- [ ] Reuse existing Rust memory/runtime state and `devctl` JSON outputs before
      inventing parallel artifact paths.
- [ ] Any Git push, publish, login, or other external side effect remains
      approval-gated even when launched from inside the cockpit.

### 3.7.4 Typed Action Router (Buttons + AI Use The Same Execution Path)

Goal: let the operator, Codex, Claude, and future control surfaces trigger the
same repo-native automation without giving any surface unrestricted shell/API
power.

Core model:

- [ ] Every button press, review packet, or AI suggestion that wants something
      done becomes one typed `action_request` with structured params, not a raw
      shell string.
- [ ] The system may use an AI planner/resolver to map a high-level user intent
      (`push`, `push release`, `check CI`, `run cleanup`, `generate handoff`)
      onto the correct repo-native playbook, but the planner may only choose
      from the approved command catalog and policy graph.
- [ ] `action_request` resolves through one command catalog that maps intent to
      canonical repo handlers:
  - [ ] `devctl` commands
  - [ ] approved git helpers
  - [ ] approved GitHub/CI helpers
  - [ ] approved memory/export/handoff compilers
- [ ] The executor returns structured result payloads plus any staged
      `terminal_packet`, warnings, and audit refs back into the same review /
      controller / memory system.

Initial request classes:

- [ ] `git_status`, `git_diff`, `git_commit_prepare`, `git_push`
- [ ] `gh_auth_status`, `gh_workflow_list`, `gh_run_view`, `gh_workflow_dispatch`
- [ ] `ci_status`, `ci_watch`, `release_gates`
- [ ] `memory_status`, `memory_query`, `memory_export_pack`, `memory_handoff`
- [ ] `review_promote_next_slice`, `review_generate_prompt`, `review_stage_packet`

Policy outcomes (shared across buttons and AI):

- [ ] `safe_auto_apply`
- [ ] `stage_draft`
- [ ] `operator_approval_required`
- [ ] `blocked`

Required behavior:

- [ ] Buttons and AI use the same policy/result path; a button must not bypass
      the checks that would block the same request from an AI packet.
- [ ] Overlay buttons may emit coarse intents (`push`, `commit`, `ship
      release`, `run checks`) and let the planner choose the exact guarded
      playbook, but the final execution plan must be shown in structured form
      before the action runs.
- [ ] GitHub/API access should ride through approved helpers (`gh`, workflow
      dispatch, repo wrappers), not arbitrary model-issued HTTP calls.
- [ ] If the operator or AI asks for `git push`, the system should derive the
      right repo-native flow (`status`/validation/branch policy/push gate) and
      explain blockers before any push occurs.
- [ ] Warnings must be first-class results, not hidden stderr: the surface
      should show what is wrong, why it is blocked/risky, and what approval or
      fix is required next.
- [ ] Execution should preserve pipeline visibility: selected playbook,
      preflight checks, current step, warnings, final outcome, and audit refs
      should all be visible in the overlay/review lane.

### 3.7.5 Override + Waiver Model

Goal: permit explicit human overrides without erasing the guardrails or the
audit trail.

Rules:

- [ ] Expose explicit execution profiles inside the cockpit:
  - [ ] `Guarded` (default): always run the canonical prechecks / policy gates
        / approval flow for the selected action
  - [ ] `AI-assisted Guarded`: AI/planner chooses the right approved playbook,
        but the same guards still run unchanged
  - [ ] `Unsafe Direct` (dev-only): skip selected non-critical checks for local
        iteration, show a red warning state, and emit a stronger audit trail
        that this action bypassed normal safety steps
- [ ] Default behavior stays fail-closed: when policy says `blocked` or
      `operator_approval_required`, no action runs silently.
- [ ] A human operator may grant a bounded override only for actions whose
      policy contract explicitly allows override.
- [ ] `Unsafe Direct` must be an explicit session-scoped mode toggle chosen by
      the human operator; agents may request it, but they may not silently
      switch themselves into it.
- [ ] The override flow must render:
  - [ ] the command/action that would run
  - [ ] the exact warnings / failed preconditions
  - [ ] the risk tier and why it is risky
  - [ ] the smallest approval scope available
- [ ] Every override emits audit evidence with approver, rationale, timestamp,
      affected action, and resulting outcome.
- [ ] Some classes stay non-overridable until a future explicit policy change:
  - [ ] destructive git cleanup
  - [ ] release/tag/publish steps without release-lane gates
  - [ ] arbitrary shell/python execution outside the allowlisted catalog
  - [ ] arbitrary outbound API/HTTP calls outside the approved helper set

Acceptance:

1. The same request made by button, AI packet, or operator command yields the
   same policy decision and the same warnings.
2. Overrides are explicit, narrow, and fully auditable.
3. The system remains script-first and policy-first rather than model-first.
4. `Unsafe Direct` is visible, noisy, and intentionally worse than the guarded
   path, not a hidden convenience bypass.

### 3.8 Claude Swarm Worker Mode + Codex Audit Observer

Goal: allow high-parallel coding execution (up to 20 workers) while keeping one
auditable orchestrator contract.

Execution model:

- [x] Use `devctl autonomy-swarm` for agent-count planning and bounded loop fanout
      (`--max-agents 20` cap).
- [x] Keep execution as one command by default: worker fanout + post-audit
      digest + reserved reviewer slot (`AGENT-REVIEW` when lane count >1).
- [x] Add one guarded wrapper (`devctl swarm_run`) that loads plan scope,
      drives swarm execution, runs governance checks, and appends plan evidence
      (`Progress Log` + `Audit Evidence`) without manual glue steps.
- [x] Add one matrix benchmark wrapper (`devctl autonomy-benchmark`) that
      validates plan scope and runs swarm-count/tactic tradeoff batches with
      consolidated productivity reports/charts.
- [ ] Use Claude workers only inside dedicated worktrees/branches mapped in
      `MASTER_PLAN` + runbook tables.
- [ ] Keep Codex (orchestrator) in audit-observer mode:
  - [ ] run `orchestrate-status` + `orchestrate-watch` cadence.
  - [ ] run sync guards and post-run digest (`autonomy-report`).
  - [ ] enforce policy denials/stop conditions before any promote actions.
- [ ] Require every worker instruction/ack/progress to land in the merged
      `dev/active/review_channel.md` swarm tables and the live `bridge.md`
      bridge.
- [ ] Treat any lane with missing ACK, stale updates, or failed required bundle
      as blocked until resolved.
- [ ] Add a swarm-efficiency governor so fanout adapts to useful throughput
      instead of raw lane count:
  - [ ] capture normalized per-cycle metrics:
    `lane_utilization_pct`, `acceptance_yield_pct`, `duplicate_work_pct`,
    `stall_pct`, `review_backlog_pct`, and `token_pressure_pct`
    (exact token usage when providers expose it, otherwise estimated from
    prompt/completion metadata already tracked by the planner).
  - [ ] compute one operator-readable `efficiency_score` from those metrics so
    the system can explain why it is shrinking, holding, or expanding.
  - [ ] downshift automatically when low-efficiency signals persist across
    consecutive cycles instead of letting idle or duplicative workers keep
    burning tokens.
  - [ ] repurpose lanes intentionally rather than blindly deleting them:
    convert weak coding lanes into review, audit, cleanup, or backlog triage
    lanes when that increases throughput.
  - [ ] freeze coding fanout to a minimal safe pair when review coverage is
    stale or the review backlog is saturated.
  - [ ] only upshift when review capacity, backlog depth, and token headroom
    all remain healthy for multiple cycles.

Swarm efficiency model:

- `lane_utilization_pct = active_lane_time / reserved_lane_time`
- `acceptance_yield_pct = accepted_outputs / total_outputs`
- `duplicate_work_pct = duplicate_or_rejected_outputs / total_outputs`
- `stall_pct = stalled_or_no_signal_lanes / total_lanes`
- `review_backlog_pct = review_queue_items / active_lanes`
- `token_pressure_pct = estimated_tokens_spent / token_budget`
- `efficiency_score =
  0.30 * acceptance_yield_pct +
  0.20 * lane_utilization_pct +
  0.15 * (1 - duplicate_work_pct) +
  0.15 * (1 - stall_pct) +
  0.10 * (1 - review_backlog_pct) +
  0.10 * (1 - token_pressure_pct)`

Default control policy:

1. `efficiency_score < 0.35` for 2 consecutive cycles: downshift fanout by at
   least 25% and reassign the weakest lanes to audit/backlog/review work.
2. `efficiency_score < 0.20` or reviewer stale: pause new coding work and keep
   only the minimal reviewer/coder recovery pair alive until signals recover.
3. `efficiency_score > 0.75` for 2 consecutive cycles with healthy review headroom:
   allow a bounded upshift if unchecked plan work still exists.
4. High `duplicate_work_pct` should bias re-scope/reassignment before any
   further upshift.
5. High `token_pressure_pct` should bias smaller swarms even when raw backlog
   remains large.

Operator checklist (per run):

1. `python3 dev/scripts/devctl.py swarm_run --plan-doc <plan.md> --mp-scope <MP-XXX> --mode report-only --run-label <label> --format md`
2. Update `MASTER_PLAN` board + runbook section 0 with selected `AGENT-<N>` lanes.
3. Start Claude workers with the runbook prompt template + lane scope.
4. Run auditor loop every 15-30 minutes (`orchestrate-status`, `orchestrate-watch`, `check_multi_agent_sync`).
5. Review `swarm_run` bundle + nested swarm post-audit bundle and ensure
   `AGENT-REVIEW` lane is healthy before merges.

Acceptance:

1. Up to 20 workers can run concurrently with deterministic lane ownership.
2. All worker actions are reconstructable from runbook + autonomy artifacts.
3. Auditor can halt promotion safely when policy/gate evidence is incomplete.
4. No worker runs outside tracked MP scope and branch/worktree boundaries.
5. Swarm size changes are explainable from logged metrics rather than hidden
   intuition or model whim.

## Phase 4 - Guardrails and Data Quality

- [x] Add policy file `dev/config/control_plane_policy.json`:
  - [x] Allowlisted workflows, refs, inputs, rate limits.
- [ ] Add replay protection (nonce + timestamp window).
- [x] Add kill switch `AUTONOMY_MODE=off|read-only|operate`.
- [x] Add branch-protection-aware action rejection (initial branch allowlist in policy gate).
- [ ] Add loop safety checks:
  - [x] stale-run detection (source-run correlation + timeout reasons)
  - [x] duplicate suppression (idempotent marker-based comment upserts)
  - [ ] max update/comment rate
- [x] Add decision traceability:
  - [x] reason code
  - [x] source evidence pointers

## Test Plan

### Unit

- [x] Source-run correlation for overlapping run timelines.
- [x] Notify target resolution + idempotent comment update.
- [x] Mutation hotspot extraction + reason-code surface.
- [x] Policy gate allowlist/denylist evaluation.
- [ ] Mobile command parser normalization + auth checks.
- [ ] Controller-state projection parity checks (Rust + phone/SSH surfaces).
- [ ] Fingerprint and playbook-confidence scoring determinism checks.

### Integration

- [ ] `coderabbit_ralph_loop` under overlapping source runs.
- [ ] `summary-and-comment` PR + commit targets.
- [ ] `mutation_ralph_loop` report-only on real artifacts.
- [ ] Fix-mode dry-run allowlisted vs blocked command paths.
- [ ] Twilio webhook roundtrip command dispatch.
- [ ] API auth + replay rejection.
- [ ] Rust/phone projection adapter parity for action behavior.
- [ ] Learning-loop promotion/decay policy behavior on mixed outcomes.

### End-to-End

- [ ] Phone status request returns accurate run-linked state.
- [ ] Phone-triggered report-only mutation loop returns artifact summary.
- [ ] Blocked command attempt yields policy deny + audit trace.
- [ ] No repeated comment spam across repeated loop runs on same target.
- [ ] Same loop packet appears identically in Rust Dev panel and phone surfaces.
- [ ] Learned playbook recommendation appears in next loop cycle with evidence.

## Rollout Plan

1. Milestone A: correlation fix + notify implementation (`summary-only` default).
2. Milestone B: mutation report-only workflow + 1-2 week evidence window.
3. Milestone C: guarded auto-fix enablement for selected branches.
4. Milestone D: deploy Rust control service container + SMS pilot.
5. Milestone E: add richer interactive chat control path.
6. Milestone F: extract reusable standalone template.

## Template Extraction (Stage 2)

- [ ] Package reusable workflows, policy schema, loop scaffolds, adapters, and
      docs playbook.
- [ ] Add bootstrap installer for new repos.
- [ ] Publish adoption guide with safety-first defaults.

## Phase 5 - External Repo Federation Bridge

- [x] Link external upstream sources into this repo via pinned integration
      paths:
  - [x] `integrations/code-link-ide`
  - [x] `integrations/ci-cd-hub`
- [x] Add governed import playbook:
  - [x] `dev/integrations/EXTERNAL_REPOS.md`
  - [x] `dev/scripts/sync_external_integrations.sh`
- [x] Add selective import automation for reusable surfaces
      (workflow snippets, control-plane adapters, mobile/control clients):
  - [x] `devctl integrations-sync` (policy-guarded source sync/status)
  - [x] `devctl integrations-import` (allowlisted source/profile importer)
  - [x] Policy allowlists in `dev/config/control_plane_policy.json`
        (`integration_federation` section with source/profile mappings, destination-root guards, and audit log path).
- [ ] Add `network-monitor-tui` as a third federated source for dev/inner-mode
      observability:
  - [ ] Link `integrations/network-monitor-tui` as a pinned input.
  - [ ] Add allowlisted import profile(s) for throughput/latency sampling
        helpers and TUI panel primitives.
  - [ ] Keep imported surfaces read-only in MVP (`--dev` + phone status only;
        no remote-action coupling), with unique monitor mode flags that keep
        Whisper/voice runtime untouched unless explicitly selected.

Acceptance:

1. External repos are version-pinned and auditable from this repository.
2. Reuse/import flow is documented and aligned to active-plan governance.
3. Updates/imports can be run in one command path without memory-only steps.

## Phase 6 - Scientific Audit + Learning Loop

- [x] Add repeat-to-automate governance policy:
  - [x] `AGENTS.md` continuous-improvement rule.
  - [x] Guard enforcement via `check_agents_contract.py` markers.
- [x] Add audit program directory and baseline artifacts:
  - [x] `dev/audits/README.md`
  - [x] `dev/audits/AUTOMATION_DEBT_REGISTER.md`
  - [x] `dev/audits/2026-02-24-autonomy-baseline-audit.md`
- [x] Add metric schema and event template:
  - [x] `dev/audits/METRICS_SCHEMA.md`
  - [x] `dev/audits/templates/audit_events_template.jsonl`
- [x] Add analyzer script for KPI + chart outputs:
  - [x] `python3 dev/scripts/audits/audit_metrics.py ...`
  - [x] KPI output includes script-only vs AI-assisted vs human-manual share.
  - [x] Optional matplotlib charts by area/source/trend.
- [x] Auto-emit audit events from `devctl` command executions:
  - [x] policy path `audit_metrics.event_log_path`
  - [x] env overrides for cycle/source/area labels
  - [x] unit + CLI emission tests

Acceptance:

1. Audit cycles can quantify what automation handled vs AI/manual intervention.
2. Repeated manual workaround debt is visible and tracked with closure criteria.
3. The audit program supports iterative script improvement over time.
4. `devctl` usage generates audit data automatically with minimal manual logging.

### 6.1 Deterministic Learning Loop (No Hidden Memory)

- [ ] Add loop-task fingerprinting from packet fields
      (`task_type`, `risk_class`, `paths`, `failure_reason`, `policy_outcome`).
- [ ] Add playbook-memory store
      (`dev/reports/autonomy/learning/playbooks.jsonl`) with:
  - [ ] fingerprint key
  - [ ] attempted strategy
  - [ ] outcome metrics (success/failure/revert count)
  - [ ] confidence score and last-seen timestamp
- [ ] Add promotion rules:
  - [ ] auto-suggest after 2 successful repeats
  - [ ] auto-apply only after guarded threshold (for example 5/5 success)
  - [ ] always require policy gate pass before execution
- [ ] Add decay/quarantine rules:
  - [ ] lower confidence on regressions
  - [ ] auto-disable playbooks after repeated failures
- [ ] Add `devctl autonomy-learn` digest to emit:
  - [ ] most reused playbooks
  - [ ] automation win-rate by task class
  - [ ] candidate manual tasks to automate next
- [ ] Feed learned playbook suggestions back into `autonomy-loop` plan stage as
      ranked options (with evidence refs and confidence).

Acceptance:

1. Repeated task classes converge to stable playbooks with measurable win-rate.
2. Failed/unsafe playbooks are quarantined automatically.
3. Every learned decision is explainable from stored artifacts and metrics.
4. Architect can disable learning globally without disabling core loop execution.

## Assumptions and Defaults

1. `develop` remains integration branch; `master` remains release branch.
2. Auto-fix is disabled by default until explicitly enabled by policy.
3. SMS is the first remote control channel; richer chat follows.
4. Autonomous write actions are auditable and policy-gated.
5. No destructive operations are introduced without explicit policy gates.

## Execution Checklist

- [x] INDEX row is present and synced.
- [x] MASTER_PLAN scope is linked.
- [x] Governance docs updated (`AGENTS`, `DEV_INDEX`, `dev/README`).
- [x] Guard checks updated and passing.
- [ ] Handoff includes evidence and unresolved risks.

## Progress Log

- 2026-03-21: Accepted the next bounded graph-injection follow-up for
  `swarm_run`/autonomy. The carry-forward checkpoint packet is now real, but
  fresh autonomy sessions still start from plain checklist text. The next
  backend slice is to prepend the same bounded `context-graph` packet to the
  generated `swarm_run` prompt and then measure repeated-failure scenarios
  with and without the packet (retry count, wrong-file edits, and
  check-selection accuracy) before widening to operator/mobile rendering.
- 2026-03-21: Added the first repo-owned context recovery packet to the
  bounded autonomy loop. `loop-packet` now derives small `context-graph`
  packets from triage commands, issue summaries, and mutation hotspots, and
  `build_checkpoint_packet()` carries that structured packet into the durable
  autonomy inbox/checkpoint artifact instead of leaving recovery context as an
  operator-only guess. Next: decide whether phone/overlay surfaces should
  render the packet directly or stay summary-only while the controller loop is
  still stabilizing.
- 2026-03-17: Accepted the next mobile/backend architecture correction from a
  focused iPhone/runtime review. The current mobile relay guard is not yet a
  trustworthy live-seam guard: it compares Rust structs against bundle-only
  Swift models, can still report `ok` with zero matched pairs, and does not
  cover the live `DaemonWebSocketClient` path. The plan now explicitly
  prioritizes a typed daemon-state/runtime contract plus an executable Rust ↔
  Python ↔ Swift parity guard before more phone UI work, then projects that
  typed daemon state through `mobile-status` so iPhone can move off
  `controller_payload` / `review_payload` as primary inputs.
- 2026-03-10: Refactored the first watchdog analytics slice onto a shared typed
  package instead of letting `guard-run`, data-science reducers, and Operator
  Console views each grow their own schema/parser logic. The canonical
  watchdog contract now lives under `dev/scripts/devctl/watchdog/`
  (`GuardedCodingEpisode`, `WatchdogMetrics`, `WatchdogSummaryArtifact`),
  compatibility shims preserve the old import paths, and JSON serialization now
  emits list-shaped provider/guard-family rows so chart/rendering consumers do
  not silently diverge from the reducer's in-memory typed tuples.
- 2026-03-10: Hardened the first `guard-run`-backed watchdog producer after a
  self-review pass. The emitted episode rows now carry repo diff/file snapshots
  before and after the guarded command, optional typed metadata overrides
  (`provider`, `session_id`, `peer_session_id`, `trigger_reason`,
  `retry_count`, `escaped_findings_count`, `guard_result`,
  `reviewer_verdict`), and the reducer no longer lets failed/no-green episodes
  artificially improve `time_to_green_seconds`. This keeps the initial MP-340
  analytics slice honest enough for real pilot data instead of only synthetic
  tests.
- 2026-03-10: Landed the first repo-visible guarded-episode producer for the
  watchdog study. `devctl guard-run` now emits canonical
  `dev/reports/autonomy/watchdog/episodes/guarded_coding_episode.jsonl` rows
  plus per-episode `summary.json` artifacts, which closes the reducer-only gap
  in MP-340 and gives the analytics pipeline real episode input without waiting
  for the full overlay activity collector. Initial producer scope is typed and
  bounded to explicit `guard-run` sessions; richer provider/session/activity
  attribution remains follow-up work under the same plan.
- 2026-03-10: Added the analytics-specific follow-up for the watchdog study.
  MP-340 now requires a repo-owned episode schema and dashboard/report layer so
  the system can measure not just "better/worse" but speed, latency, churn,
  retries, review escapes, per-guard win rate, provider differences, and other
  terminal-derived signals we may need later. The plan also now separates
  exploratory metrics from promotion metrics and requires minimum-sample/power
  discipline before the project claims the guards materially improve AI coding.
- 2026-03-10: Expanded the MP-340 watchdog intake into a scientific measurement
  plan. The overlay-native guard system should not just "feel better"; it must
  emit matched before/after guarded coding episodes and be evaluated with a
  proper empirical protocol: predefined primary outcomes, paired analysis by
  task, effect sizes with confidence intervals, and practical-significance
  thresholds before any promotion claim. The same artifact corpus is also now
  the planned substrate for later learning work, but the order stays strict:
  deterministic retrieval/playbook learning first, offline ML/ranking later.
- 2026-03-10: Recorded the overlay-native live guard-watchdog intake under
  MP-340. The intended model is not "overlay scrapes text and blindly types
  fixes back into Codex/Claude"; it is "overlay observes PTY/session-tail
  activity plus typed packets, classifies what the agent is doing, routes the
  matching repo guard through a bounded `devctl` action, and projects the
  result back into `controller_state` / review surfaces." This keeps the
  overlay in a real-time watchdog role while preserving the repo's typed
  policy/approval boundary and avoiding raw freeform shell authority as the
  default enforcement mechanism.
- 2026-03-09: Expanded MP-340 to capture the post-simulator/mobile feedback
  explicitly before more implementation starts. The plan now locks backend
  ownership to Rust + `devctl` rather than PyQt6, treats SSH as read/debug and
  not the real push path, prioritizes a simple phone ping proof before richer
  control claims, and adds the concrete iPhone backlog for same-data parity
  with the desktop shell: split/combined terminal lane mirrors, typed
  approvals/notes/instructions, plan-to-agent assignment, simple/technical
  modes, and reconnect/resume behavior over one shared backend contract. It
  also records `code-link-ide`, `network-monitor-tui`, local FileHasher-style
  theme/chart work, and the `gitui-main/app` design reference as reference
  inputs only rather than control-plane authority.
- 2026-03-09: Turned the phone-client scaffold into a real iOS app target.
  `app/ios/VoiceTermMobileApp` now exists as an XcodeGen-backed SwiftUI shell
  over `VoiceTermMobileCore`, starts with built-in sample relay data, imports a
  real emitted `mobile-status` bundle from Files, persists the selected bundle
  folder, and builds cleanly for generic iOS via unsigned `xcodebuild`.
- 2026-03-09: Cleaned up the iOS package/app boundary after local simulator
  confusion. `app/ios/VoiceTermMobileApp` is now documented everywhere as the
  runnable iPhone/iPad app, `app/ios/VoiceTermMobile` is explicitly the shared
  Swift package that app imports, a guided simulator demo script now builds +
  installs + syncs + launches the app while printing the real manual test
  flow, and the older "client scaffold" wording is archived so future docs do
  not present the package as a second stale app.
- 2026-03-09: Folded the iPhone launch path into `devctl` instead of leaving
  it as shell-script trivia. The new `mobile-app` command can run the real
  simulator demo over the live repo bundle, list simulator/physical devices,
  and open an honest physical-device wizard for Xcode/signing. The app itself
  now prefers a synced live bundle on startup and shows a short first-run
  tutorial that explains the real-data path and the current read-first action
  boundary.
- 2026-03-09: Extended `devctl mobile-app` from a wizard-only wrapper into a
  real device-aware launcher surface. `mobile-app --action device-install`
  now attempts the actual signed `iphoneos` build/install/launch path through
  `xcodebuild` plus `xcrun devicectl` when a physical device and Apple
  Development Team are present, while still failing honestly with the exact
  missing prerequisite when no phone is connected or signing is unset. The
  simulator demo was also rerun after fixing its walkthrough heredoc so the
  final live test output stays clean and copyable.
- 2026-03-09: Expanded the active plan so the phone path is not trapped as a
  bundle-only sidecar. The control-plane plan now explicitly ties mobile
  proving to the Rust-owned `controller_state` closure, Memory Studio pack
  attachments (`task_pack`, `session_handoff`, `survival_index`,
  `context_pack_refs`), provider-aware lane routing, and a shared simulator /
  device test harness. The new `mobile-app --action simulator-demo
  --live-review` path now proves the current repo-backed Ralph/review state in
  Simulator while the plan makes clear that true task execution still belongs
  to the shared host-side typed action router.
- 2026-03-09: Expanded the active phone/control-plane target beyond the
  read-first bundle client. The plan now explicitly requires one Mac-hosted
  Rust control service shared by overlay/dev/phone surfaces, live same-network
  iPhone connectivity, staged phone voice-to-action flows, yes/no approval
  actions, structured operator-note messaging, and a secure off-LAN/cellular
  reconnect path so long-running plans can continue at home while the phone
  later reconnects to the same host state.
- 2026-03-09: Fixed the first simulator usability regression in the iOS shell.
  The import path now accepts either a bundle folder or `full.json`, and the
  top control strip is stacked into larger phone-width tap targets so `Import
  Bundle`, `Reload`, and `Use Sample Bundle` stay usable on narrow screens.
- 2026-03-09: Added a real simulator live-data bridge instead of treating
  sample/import as the only path. `devctl mobile-status` now falls back to
  review-channel live data when the autonomy phone artifact is missing, the app
  auto-detects `Documents/LiveBundle/` as a first-party live source, and
  `app/ios/VoiceTermMobileApp/sync_live_bundle_to_simulator.sh` can push the
  current repo-backed bundle into the booted simulator so the iPhone shell
  shows real Codex/Claude/operator state.
- 2026-03-09: Replaced one-off no-prompt launcher behavior with a shared
  approval-policy path. `review-channel` now accepts `--approval-mode
  strict|balanced|trusted`, the legacy `--dangerous` path is treated as a
  compatibility alias for `trusted`, `mobile-status` now emits the same
  approval policy into phone-safe projections for future PyQt/iPhone surfaces,
  and the Ralph Claude wrapper now reads `RALPH_APPROVAL_MODE` instead of
  hardcoding `--dangerously-skip-permissions`. The current provider boundary is
  explicit: destructive/publish-class actions still require typed approval even
  when provider CLI prompts are relaxed.
- 2026-03-09: Moved the iPhone UI one step closer to the operator-console
  target instead of leaving it as a plain viewer. The shared Swift models now
  decode the emitted approval-policy fields from `mobile-status`, the dashboard
  surfaces approval mode/summary plus confirmation-required classes alongside
  the lane console, and the shell styling now reads more like a control panel
  with terminal-relay cards than a generic document reader. Real local proofs
  from this slice are in the audit table: `swift test` for the shared package
  and unsigned `xcodebuild` for the runnable app both passed after the UI/model
  update.
- 2026-03-09: Added a terminal-style phone lane view over the same live bundle.
  The iOS shell now exposes a `Terminal` section with split/combined
  monospaced panels for Codex, Claude, and Operator so the phone can show what
  each lane is doing without leaving the app. This remains read-only for now;
  direct instruction dispatch is still a later guarded backend slice.
- 2026-03-09: Tightened the first-party phone client around the emitted mobile
  bundle contract instead of a one-off JSON reader. `app/ios/VoiceTermMobile`
  now loads `full.json` plus optional `compact.json` / `actions.json` from
  `dev/reports/mobile/latest/`, builds a sectioned SwiftUI dashboard with
  multi-agent lane cards and safe action cards, and stays explicitly aligned
  with the same `mobile-status` projection bundle the PyQt6 console now
  prefers before any on-the-fly fallback path.
- 2026-03-09: Started the first first-party iPhone client scaffold against the
  shared mobile relay contract. `app/ios/VoiceTermMobile` is now a bounded
  Swift package that decodes the merged `mobile-status` full projection,
  renders a read-first SwiftUI dashboard, and shows multiple agent lanes from
  the same review/control payload the PyQt6 console already consumes.
- 2026-03-09: Added `devctl mobile-status` as the first explicit phone-app
  contract shim for MP-340. The new read-only command refreshes the latest
  bridge-backed review-channel projections, merges them with autonomy
  `phone-status`, emits compact/full/alert/actions mobile projections, and
  gives SSH or future notifier/phone clients one canonical payload that
  already includes Codex/Claude/review state plus controller state.
- 2026-03-09: Recorded the current MP-340 convergence boundary after the
  memory/review/control-plane doc audit. The plan now states explicitly that
  today's `phone-status` / `controller-action` payloads and Rust Dev-panel
  snapshot builders are interim projections only; true MP-340 closure still
  requires one emitted `controller_state` projection set consumed with parity
  across Rust, phone, review, and memory surfaces.
- 2026-03-09: Revalidated the MP-340 Rust operator-cockpit proof path after
  the memory-tab/action-catalog slice and the follow-up Rust test split. The
  local guarded runtime path is green again (`cargo test --bin voiceterm`
  under `devctl guard-run`), the Rust policy gates
  (`check_rust_test_shape`, `check_rust_lint_debt`,
  `check_rust_best_practices`, `check_structural_complexity`) all pass, and
  the local governance/doc sync checks (`check_active_plan_sync`,
  `check_multi_agent_sync`, `docs-check --strict-tooling`,
  `process-cleanup --verify --format md`) are back in evidence for the
  control-plane slice instead of being implied.
- 2026-03-09: Landed the next Rust-first MP-340 cockpit slice. The Dev panel
  now has a dedicated read-only Memory tab that refreshes with the visible-tab
  path and renders memory-ingest plus review/boot-pack/handoff preview state
  inside the same operator surface as `Control` / `Ops` / `Review` /
  `Actions` / `Handoff`, keeping the memory proof path inside the one-system
  control surface instead of spawning a parallel UI.
- 2026-03-09: Expanded the typed Rust action catalog beyond the initial safe
  controller subset. Review launch dry-run/live, review rollover, pause-loop,
  and resume-loop now render through the same JSON-summary-backed operator path
  as the existing controller actions, tightening MP-340's shared action-router
  direction before any freer-form write surface is allowed.
- 2026-03-08: Extended the swarm-control plan from simple token-aware sizing to
  a governed efficiency model. MP-340/338 now explicitly tracks the metrics,
  score, and control policy that should decide when to hold, downshift,
  upshift, freeze to a recovery pair, or repurpose weak lanes into
  review/audit/backlog work instead of letting idle swarms burn tokens.
- 2026-03-08: Expanded the MP-340 operator-cockpit direction after a full
  repo/plan review of the Dev panel, control-plane tooling, review bridge, and
  memory foundations. The plan now explicitly stages Git/GitHub/CI/script lanes
  as allowlisted operator surfaces, adds a memory proving lane on top of the
  shipped JSONL + index-contract memory substrate, and locks a typed action
  router so buttons, AI-issued requests, and future controller clients all hit
  the same command catalog, warning surfaces, and approval/waiver policy path.
- 2026-03-08: Added a concrete operator-cockpit MVP slice for MP-340/336/355
  coordination after the live Codex/Claude loop exposed a visibility/control
  gap: the plan now says the existing Rust Dev panel should grow into
  `Control`/`Ops`/`Review`/`Actions`/`Handoff` pages first, then pick up a
  dedicated `--monitor` entry path later without forking a second UI. The same
  update also added a broader developer-only surface backlog (artifact
  inspector, audit tail, geometry/runtime diagnostics, packet/handoff tools,
  and monitor panels) so `--dev` becomes a practical operator/debug cockpit
  rather than a narrow command launcher.
- 2026-03-09: Started the first `Ops`-page implementation slice in the Rust
  Dev panel so host-process hygiene (`process-audit` / `process-cleanup`) and
  triage visibility can live beside `Control`/`Review`/`Actions`/`Handoff`
  under the same typed action router. This keeps operational telemetry in the
  Rust-first control surface instead of leaking into Theme Studio or a
  separate ad hoc monitor UI.
- 2026-03-08: Reconciled MP-340 with MP-355 and Memory Studio so the three
  plans now share one event/header envelope, memory-backed context-pack refs,
  provider-aware pack shaping, and a future unified timeline/replay direction
  instead of drifting into separate state models.
- 2026-03-08: Landed `ADR-0027` and `ADR-0028` so the active control-plane and
  review-channel plans now point at accepted architectural authority for the
  shared `controller_state` contract and the relay-packet protocol instead of
  relying on a pending backlog placeholder.
  active pillars read as one system instead of parallel plans: locked shared
  event-header mapping, memory-backed `context_pack_refs`, provider-aware
  handoff routing, and a deferred unified timeline/replay projection under the
  umbrella controller contract.
- 2026-02-25: Implemented triage-loop fix execution parity with mutation policy
  gates (new `triage/loop_policy.py`, `control_plane_policy.json`
  `triage_loop.allowed_fix_command_prefixes`, workflow env wiring for
  `AUTONOMY_MODE`/`TRIAGE_LOOP_ALLOWED_PREFIXES`, and `fix_block_reason`
  propagation into dry-run/live reports).
- 2026-02-25: Added review escalation flow for exhausted triage loops:
  `coderabbit_ralph_loop_core.py` now sets `escalation_needed=true` on
  max-attempt exhaustion, `triage/loop_support.py` now upserts dedicated
  escalation comments with a separate marker, and `devctl triage-loop` now
  publishes escalation comments when unresolved backlog remains.
- 2026-02-24: Plan created under `dev/active/` with execution-contract marker,
  staged phases, acceptance criteria, and audit checklist.
- 2026-02-24: Added iPhone-first MVP execution path (read-first UI, one guarded
  write action, push+SMS fallback contract) and aligned it with MP-331 scope.
- 2026-02-24: Implemented MP-325/326 loop hardening (`triage-loop` source-run
  pinning + sha validation + comment-target upsert support) and wired
  `.github/workflows/coderabbit_ralph_loop.yml` source id/sha passing.
- 2026-02-24: Implemented MP-327/328/329 bounded mutation automation (`devctl
  mutation-loop`, `mutation_ralph_loop.yml`, policy-gated fix mode with
  `AUTONOMY_MODE` and allowlisted command prefixes).
- 2026-02-24: Implemented MP-333 enforcement updates in
  `check_active_plan_sync.py` (required execution-plan doc + marker + required
  sections validation) and added policy scaffold file
  `dev/config/control_plane_policy.json` for MP-332 baseline.
- 2026-02-24: Governance/tooling validation pass completed (`check_agents_contract`,
  `check_active_plan_sync`, `check_multi_agent_sync`,
  `docs-check --strict-tooling`, `hygiene`, `check_code_shape`,
  `check_coderabbit_gate`, `check_coderabbit_ralph_gate`, `markdownlint`,
  targeted `unittest` suites for triage/mutation loop modules).
- 2026-02-24: Added external federation bridge with pinned integration links
  (`integrations/code-link-ide`, `integrations/ci-cd-hub`) plus governed sync
  helper (`dev/scripts/sync_external_integrations.sh`) and import playbook
  (`dev/integrations/EXTERNAL_REPOS.md`).
- 2026-02-24: Added `devctl integrations-sync` and
  `devctl integrations-import` command surfaces with policy-gated source/profile
  allowlists, destination-root guards, and JSONL audit logging.
- 2026-02-24: Added `network-monitor-tui` linkage scope (MP-336 planning) for
  optional dev/inner-mode throughput + latency observability reuse, aligned with
  read-only `--dev` and phone-status surfaces.
- 2026-02-24: Added plan direction for unique monitor-mode flags (`--monitor`
  and/or `--mode monitor`) so dev/inner-mode observability can share the Rust UI
  framework without interfering with default Whisper/voice overlay startup.
- 2026-02-24: Added MP-337 repeat-to-automate governance policy and first-cycle
  audit-program scaffolding (`dev/audits/README.md`,
  `AUTOMATION_DEBT_REGISTER.md`, baseline audit checklist).
- 2026-02-24: Added audit metric schema/template and analyzer script
  (`dev/scripts/audits/audit_metrics.py`) to compute scientific audit KPIs
  (automation coverage, script-only share, AI-assisted share, manual share,
  success rate) and generate optional matplotlib charts.
- 2026-02-24: Added automatic `devctl` event emission into
  `dev/reports/audits/devctl_events.jsonl` (policy/env configurable) so every
  control-plane run contributes to KPI trend analysis by default.
- 2026-02-24: Added bounded autonomy controller surfaces (`devctl autonomy-loop`
  and `.github/workflows/autonomy_controller.yml`) with checkpoint packet queue
  artifacts, terminal/action trace payloads for phone-forwardable status, and
  optional guarded PR promote flow when working branch refs exist remotely.
- 2026-02-24: Added first-pass phone-status feed emission to `autonomy-loop`
  (`dev/reports/autonomy/queue/phone/latest.json` + `latest.md`) including
  terminal trace lines, loop draft text, run URL/SHA context, and next-action
  summaries for iPhone/SMS/push adapter consumption.
- 2026-02-24: Added `devctl autonomy-report` for operator-readable autonomy
  summaries: command scans loop/watch artifacts, writes dated bundles under
  `dev/reports/autonomy/library/<label>`, emits summary markdown/json, copies
  source artifacts, and generates matplotlib charts when available.
- 2026-02-24: Added explicit unified architect-controller phase map + required
  ADR backlog (`ADR-0027..ADR-0034`) so autonomy/mobile execution has a
  tracked architectural decision path and does not drift into memory-only scope.
- 2026-02-24: Added one-system operator architecture decision: Rust overlay
  remains runtime primary and iPhone/SSH surfaces use the same projected
  controller state for parity.
- 2026-02-25: Added an initial `app/pyside6` command-center scaffold for
  MP-340 with modular tab surfaces (`Quick Ops`, `Catalog`, `GitHub Runs`,
  `Git`, `Terminal`) and non-blocking `QProcess` execution as an exploratory
  operator-client path.
- 2026-02-26: Retired the exploratory `app/pyside6` path from active scope and
  removed it from the tree to keep MP-340 Rust-first (`--dev` + `phone-status`
  + policy-gated `controller-action`), with desktop GUI clients explicitly
  deferred pending a future reactivation MP item.
- 2026-02-26: Completed a targeted federation fit-gap audit for
  `integrations/code-link-ide` + `integrations/ci-cd-hub` against
  `MP-297/298/330/331/332/340`, documented keep/take/avoid decisions in
  `dev/integrations/EXTERNAL_REPOS.md`, and added narrow
  `integration_federation` import profiles in `control_plane_policy.json`
  (`control-plane-guardrails-core`, `control-plane-contract-core`,
  `report-validator-core`, `triage-evidence-core`, `registry-sync-core`) to
  stop broad random imports.
- 2026-02-24: Added deterministic learning-loop scope (fingerprints, playbook
  memory, guarded promotion/decay, `autonomy-learn` digest) so repeated work
  can be automated over time with explicit auditability.
- 2026-03-08: Corrected MP-340/MP-355 doc wording so active plans stop citing
  `ADR-0027`/`ADR-0028` as existing authority before those ADRs are actually
  written; interim ownership stays in the active plan docs until the backlog
  lands.
- 2026-02-24: Added explicit Claude swarm worker mode + Codex audit-observer
  execution contract (up to 20 workers) with required runbook/guard cadence and
  stop conditions.
- 2026-02-24: Upgraded `devctl autonomy-swarm` to one-command execution mode:
  auto post-audit digest (`autonomy-report`) now runs by default, and execution
  reserves a default `AGENT-REVIEW` lane when selected lane count is greater
  than one (disable controls: `--no-post-audit`, `--no-reviewer-lane`).
- 2026-02-24: Added `devctl swarm_run` guarded wrapper so one command now
  covers plan-scope load, next-step prompt derivation, swarm+reviewer
  execution, governance checks, and plan-doc evidence append.
- 2026-02-24: Added workflow-dispatch lane `.github/workflows/autonomy_run.yml`
  so guarded plan-scoped swarm runs can be executed in CI with uploaded run
  artifacts and summary outputs.
- 2026-02-25: Canonical command name for this wrapper is now `swarm_run`.
  Historical log/evidence rows below that mention `autonomy-run` refer to runs
  executed before the rename.
- 2026-02-24: Added `devctl autonomy-benchmark` for active-plan-scoped swarm
  matrix runs (`swarm-counts x tactics`) with per-swarm/per-scenario metrics
  and charted tradeoff outputs under
  `dev/reports/autonomy/benchmarks/<run-label>/summary.{md,json}`.

- 2026-02-24: Ran `devctl autonomy-run` (`autonomy-run-live-20260224-091724Z`, `MP-338`); selected_agents=10, worker_agents=9, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/autonomy-run-live-20260224-091724Z/summary.md`.
- 2026-02-24: Ran `devctl autonomy-run` (`autonomy-run-live-20260224-092520Z`, `MP-338`); selected_agents=10, worker_agents=9, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/autonomy-run-live-20260224-092520Z/summary.md`.
- 2026-02-24: Ran `devctl autonomy-benchmark` (`matrix-10-15-20-30-40-20260224`, `MP-338`) across swarm counts `10,15,20,30,40` and tactics `uniform,specialized,research-first,test-first`; scenarios=20, swarms_total=460, swarms_ok=460, tasks_completed_total=1840; artifacts: `dev/reports/autonomy/benchmarks/matrix-10-15-20-30-40-20260224/summary.md`.
- 2026-02-24: Re-ran `devctl autonomy-benchmark` after benchmark module split (`matrix-10-15-20-30-40-20260224-r2`, `MP-338`) and confirmed the same matrix contract with `scenarios=20`, `swarms_total=460`, `swarms_ok=460`, `tasks_completed_total=1840`; artifacts: `dev/reports/autonomy/benchmarks/matrix-10-15-20-30-40-20260224-r2/summary.md`.
- 2026-02-25: Ran `devctl autonomy-benchmark` (`mp342-344-baseline-matrix-20260225`, `MP-338`) with an explicit runtime-reliability prompt covering `MP-342`, `MP-343`, and `MP-344`; baseline control used `swarm_count=1` and comparison tiers used `swarm_count=3,5` across `uniform,specialized,research-first,test-first`; outcomes: `scenarios=12`, `swarms_total=36`, `swarms_ok=36`, `tasks_completed_total=108`, `elapsed_seconds_total=10.079`; artifacts: `dev/reports/autonomy/benchmarks/mp342-344-baseline-matrix-20260225/summary.{md,json}`.
- 2026-02-25: Ran live `devctl autonomy-benchmark` A/B control-vs-swarm pass (`mp342-344-live-baseline-matrix-20260225`, `MP-338`) for the same runtime prompt using `swarm_count=1` control (no-swarm) and `swarm_count=5` swarm variant across `research-first,specialized`; outcomes: `scenarios=4`, `swarms_total=12`, `swarms_ok=12`, `tasks_completed_total=24`, `elapsed_seconds_total=3.81`; artifacts: `dev/reports/autonomy/benchmarks/mp342-344-live-baseline-matrix-20260225/summary.{md,json}`.
- 2026-02-25: Generated explicit graph bundle comparing swarm vs no-swarm outcomes for `MP-342/343/344` (`tasks_completed_total`, `work_output_score`, `tasks_per_minute`, `elapsed_seconds_total`, `success_pct`) under `dev/reports/autonomy/experiments/mp342-344-swarm-vs-solo-20260225/`.
- 2026-02-24: Added `devctl phone-status` read-surface command for iPhone/SSH usage with projection views (`full|compact|trace|actions`) and optional controller-state projection bundle output (`full.json`, `compact.json`, `trace.ndjson`, `actions.json`, `latest.md`); also fixed autonomy-report phone summary reason extraction to use top-level phone payload reason.
- 2026-02-24: Added `devctl controller-action` with safe subset (`refresh-status`, `dispatch-report-only`, `pause-loop`, `resume-loop`) plus policy gates (workflow/branch allowlist + `AUTONOMY_MODE=off` kill-switch block), dry-run support, and local controller-mode state artifact emission for phone surfaces.

- 2026-02-24: Ran `devctl autonomy-run` (`mp340-controller-state-r1`, `MP-340`); selected_agents=20, worker_agents=19, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/mp340-controller-state-r1/summary.md`.
- 2026-02-24: Ran `devctl autonomy-run` (`mp340-controller-state-r2-10workers`, `MP-340`); selected_agents=10, worker_agents=9, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/mp340-controller-state-r2-10workers/summary.md`.
- 2026-02-24: Ran `devctl autonomy-run` (`cont-fix-20260224-110234Z`, `MP-340`); selected_agents=2, worker_agents=1, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/cont-fix-20260224-110234Z/summary.md`.
- 2026-02-24: Ran `devctl autonomy-run` (`mp330-swarm-20260224a`, `MP-330`); selected_agents=10, worker_agents=9, reviewer_lane=True, governance_ok=False, status=blocked; artifacts: `dev/reports/autonomy/runs/mp330-swarm-20260224a/summary.md`.
- 2026-02-24: Ran `devctl autonomy-run` (`20260224-133052Z-c01`, `MP-338`); selected_agents=4, worker_agents=3, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/20260224-133052Z-c01/summary.md`.
- 2026-02-24: Ran `devctl autonomy-run` (`20260224-133052Z-c02`, `MP-338`); selected_agents=4, worker_agents=3, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/20260224-133052Z-c02/summary.md`.
- 2026-02-24: Ran `devctl autonomy-run` (`20260224-133052Z-c03`, `MP-338`); selected_agents=4, worker_agents=3, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/20260224-133052Z-c03/summary.md`.
- 2026-02-24: Ran `devctl autonomy-run` (`20260224-133052Z-c04`, `MP-338`); selected_agents=4, worker_agents=3, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/20260224-133052Z-c04/summary.md`.
- 2026-02-24: Ran `devctl autonomy-run` (`20260224-133052Z-c05`, `MP-338`); selected_agents=4, worker_agents=3, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/20260224-133052Z-c05/summary.md`.
- 2026-02-24: Ran `devctl autonomy-run` (`orchestrator-live-bounded-c01`, `MP-338`); selected_agents=4, worker_agents=3, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/orchestrator-live-bounded-c01/summary.md`.
- 2026-02-24: Ran `devctl autonomy-run` (`orchestrator-live-bounded-c02`, `MP-338`); selected_agents=4, worker_agents=3, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/orchestrator-live-bounded-c02/summary.md`.
- 2026-02-24: Ran `devctl autonomy-run` (`orchestrator-live-bounded-c03`, `MP-338`); selected_agents=4, worker_agents=3, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/orchestrator-live-bounded-c03/summary.md`.
- 2026-02-24: Ran `devctl autonomy-run` (`swarm10-20260224-085105-c01`, `MP-338`); selected_agents=10, worker_agents=9, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/swarm10-20260224-085105-c01/summary.md`.
- 2026-02-24: Ran `devctl autonomy-run` (`swarm10-20260224-085105-c02`, `MP-338`); selected_agents=10, worker_agents=9, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/swarm10-20260224-085105-c02/summary.md`.
- 2026-02-25: Ran `devctl autonomy-run` (`ralph-wiggum-max-swarm-20260225-c01`, `MP-338`); selected_agents=20, worker_agents=19, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/ralph-wiggum-max-swarm-20260225-c01/summary.md`.
- 2026-02-25: Ran `devctl autonomy-run` (`ralph-wiggum-max-swarm-20260225-c02`, `MP-338`); selected_agents=20, worker_agents=19, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/ralph-wiggum-max-swarm-20260225-c02/summary.md`.
- 2026-02-25: Ran `devctl autonomy-run` (`ralph-wiggum-max-swarm-20260225-c03`, `MP-338`); selected_agents=20, worker_agents=19, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/ralph-wiggum-max-swarm-20260225-c03/summary.md`.
- 2026-02-25: Ran `devctl autonomy-run` (`ralph-wiggum-max-swarm-20260225-c04`, `MP-338`); selected_agents=20, worker_agents=19, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/ralph-wiggum-max-swarm-20260225-c04/summary.md`.
- 2026-02-25: Ran `devctl autonomy-run` (`ralph-wiggum-max-swarm-20260225-c05`, `MP-338`); selected_agents=20, worker_agents=19, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/ralph-wiggum-max-swarm-20260225-c05/summary.md`.
- 2026-02-25: Ran `devctl autonomy-run` (`ralph-wiggum-max-swarm-20260225-c06`, `MP-338`); selected_agents=20, worker_agents=19, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/ralph-wiggum-max-swarm-20260225-c06/summary.md`.
- 2026-02-25: Ran `devctl autonomy-run` (`ralph-wiggum-max-swarm-20260225-c07`, `MP-338`); selected_agents=20, worker_agents=19, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/ralph-wiggum-max-swarm-20260225-c07/summary.md`.
- 2026-02-25: Ran `devctl autonomy-run` (`ralph-wiggum-max-swarm-20260225-c08`, `MP-338`); selected_agents=20, worker_agents=19, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/ralph-wiggum-max-swarm-20260225-c08/summary.md`.
- 2026-02-25: Ran `devctl autonomy-run` (`ralph-wiggum-max-swarm-20260225-c09`, `MP-338`); selected_agents=20, worker_agents=19, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/ralph-wiggum-max-swarm-20260225-c09/summary.md`.
- 2026-02-25: Ran `devctl autonomy-run` (`ralph-wiggum-max-swarm-20260225-c10`, `MP-338`); selected_agents=20, worker_agents=19, reviewer_lane=True, governance_ok=True, status=done; artifacts: `dev/reports/autonomy/runs/ralph-wiggum-max-swarm-20260225-c10/summary.md`.
## Audit Evidence

| Check | Evidence | Status |
|---|---|---|
| `check_active_plan_sync` | `ok: True` (2026-02-24 local run) | done |
| `check_agents_contract` | `ok: True` (2026-02-24 local run; repeat-to-automate markers enforced) | done |
| `check_multi_agent_sync` | `ok: True` (2026-02-24 local run) | done |
| `docs-check --strict-tooling` | `ok: True` (2026-02-24 local run) | done |
| `hygiene` | `ok: True` (2026-02-24 local run; non-blocking local warnings only) | done |
| `devctl integrations-sync --status-only --format md` | `ok: True` with pinned SHAs for both sources (2026-02-24 local run) | done |
| `devctl integrations-import --list-profiles --format md` | allowlisted source/profile matrix rendered (2026-02-24 local run) | done |
| `devctl integrations-import --source code-link-ide --profile iphone-core --format md` | preview mode planned import succeeded with destination-root policy guard (2026-02-24 local run) | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_integrations_sync dev.scripts.devctl.tests.test_integrations_import` | `Ran 7 tests ... OK` (2026-02-24 local run) | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_audit_metrics_script` | `Ran 2 tests ... OK` (2026-02-24 local run) | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_audit_events dev.scripts.devctl.tests.test_cli_audit_events` | `Ran 5 tests ... OK` (2026-02-24 local run) | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_autonomy_loop dev.scripts.devctl.tests.test_loop_packet dev.scripts.devctl.tests.test_triage_loop dev.scripts.devctl.tests.test_mutation_loop` | `Ran 18 tests ... OK` (2026-02-24 local run) | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_autonomy_loop` | updated phone-status artifact assertions passed (2026-02-24 local run) | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_autonomy_report` | parser + bundle generation tests passed (`Ran 3 tests ... OK`, 2026-02-24 local run) | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_autonomy_swarm` | reviewer-lane reservation + post-audit default behavior covered (`Ran 7 tests ... OK`, 2026-02-24 local run) | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_autonomy_run` | guarded `swarm_run` flow covered (scope checks, governance pass/fail behavior, plan-doc evidence append; `Ran 3 tests ... OK`, 2026-02-24 local run) | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_autonomy_benchmark` | autonomy-benchmark parser + matrix summary aggregation behavior covered (`Ran 2 tests ... OK`, 2026-02-24 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-loop --repo jguida941/voiceterm --plan-id acp-poc-001 --branch-base develop --mode report-only --max-rounds 1 --max-hours 1 --max-tasks 1 --checkpoint-every 1 --loop-max-attempts 1 --dry-run --format md --output /tmp/autonomy-controller-smoke.md` | dry-run controller emitted round packet + queue artifacts and summary markdown (2026-02-24 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-report --source-root dev/reports/autonomy --library-root dev/reports/autonomy/library --run-label live-human-report --format md --output dev/reports/autonomy/live-human-report.md --json-output dev/reports/autonomy/live-human-report.json` | generated dated operator bundle (`summary.md/json` + charts + copied sources) under `dev/reports/autonomy/library/live-human-report` (2026-02-24 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-swarm --agents 10 --question-file dev/active/autonomous_control_plane.md --mode report-only --run-label live-10-reviewlane-20260224-085045Z --format md --output dev/reports/autonomy/live-10-reviewlane-20260224-085045Z.md --json-output dev/reports/autonomy/live-10-reviewlane-20260224-085045Z.json` | one-command live swarm produced 9 worker lanes + `AGENT-REVIEW` and auto digest bundle under `dev/reports/autonomy/library/live-10-reviewlane-20260224-085045Z-digest` (`ok: True`, 2026-02-24 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-benchmark --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --swarm-counts 10,15,20,30,40 --tactics uniform,specialized,research-first,test-first --agents 4 --parallel-workers 4 --max-concurrent-swarms 20 --mode report-only --dry-run --run-label matrix-10-15-20-30-40-20260224 --format md --output /tmp/autonomy-benchmark-latest.md --json-output /tmp/autonomy-benchmark-latest.json` | plan-scoped matrix benchmark completed with consolidated tradeoff report (`scenarios=20`, `swarms_total=460`, `swarms_ok=460`, `tasks_completed_total=1840`) under `dev/reports/autonomy/benchmarks/matrix-10-15-20-30-40-20260224/` (2026-02-24 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-benchmark --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --swarm-counts 10,15,20,30,40 --tactics uniform,specialized,research-first,test-first --agents 4 --parallel-workers 4 --max-concurrent-swarms 20 --mode report-only --dry-run --run-label matrix-10-15-20-30-40-20260224-r2 --format md --output /tmp/autonomy-benchmark-latest-r2.md --json-output /tmp/autonomy-benchmark-latest-r2.json` | post-shape-refactor benchmark rerun passed with identical matrix totals and refreshed bundle/charts under `dev/reports/autonomy/benchmarks/matrix-10-15-20-30-40-20260224-r2/` (`swarms_total=460`, `swarms_ok=460`) (2026-02-24 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-benchmark --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --question-file /tmp/mp342-344-benchmark-question.md --swarm-counts 1,3,5 --tactics uniform,specialized,research-first,test-first --agents 3 --parallel-workers 3 --max-concurrent-swarms 3 --mode report-only --dry-run --run-label mp342-344-baseline-matrix-20260225 --format md --output dev/reports/autonomy/mp342-344-baseline-matrix-20260225.md --json-output dev/reports/autonomy/mp342-344-baseline-matrix-20260225.json` | baseline-first runtime backlog benchmark completed for `MP-342/343/344` (`scenarios=12`, `swarms_total=36`, `swarms_ok=36`, `tasks_completed_total=108`) with scenario bundles under `dev/reports/autonomy/benchmarks/mp342-344-baseline-matrix-20260225/` (2026-02-25 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-benchmark --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --question-file /tmp/mp342-344-benchmark-question.md --swarm-counts 1,5 --tactics research-first,specialized --agents 2 --parallel-workers 2 --max-concurrent-swarms 2 --mode report-only --run-label mp342-344-live-baseline-matrix-20260225 --format md --output dev/reports/autonomy/mp342-344-live-baseline-matrix-20260225.md --json-output dev/reports/autonomy/mp342-344-live-baseline-matrix-20260225.json` | live A/B benchmark completed with explicit no-swarm control vs swarm variant (`scenarios=4`, `swarms_total=12`, `swarms_ok=12`, `tasks_completed_total=24`) under `dev/reports/autonomy/benchmarks/mp342-344-live-baseline-matrix-20260225/` (2026-02-25 local run) | done |
| `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test --bin voiceterm -- --nocapture` | `ok: True`; `1731 passed` with quick post-run hygiene after the MP-340 memory/operator cockpit slice and adjacent dirty-tree coherence fixes needed to restore a fully compiling runtime surface (2026-03-09 local run) | done |
| `python3 dev/scripts/checks/check_rust_test_shape.py --format md` | `ok: True` after splitting `status_line/format/tests.rs` into focused submodules so the Rust proof path stays shape-clean (2026-03-09 local run) | done |
| `python3 dev/scripts/checks/check_rust_lint_debt.py --format md` | `ok: True` after the MP-340 action-router/broker follow-up (2026-03-09 local run) | done |
| `python3 dev/scripts/checks/check_rust_best_practices.py --format md` | `ok: True` after replacing dropped-send / `Result<String, _>` debt in the shared control-plane broker path (2026-03-09 local run) | done |
| `python3 dev/scripts/checks/check_structural_complexity.py --format md` | `ok: True` after splitting the Dev-panel overlay input handler into focused helpers (2026-03-09 local run) | done |
| `python3 dev/scripts/checks/check_active_plan_sync.py` | `ok: True` after the MP-340 memory/operator proof-path sync update (2026-03-09 local run) | done |
| `python3 dev/scripts/checks/check_multi_agent_sync.py` | `ok: True` after the MP-340 memory/operator proof-path sync update (2026-03-09 local run) | done |
| `python3 dev/scripts/devctl.py docs-check --strict-tooling` | `ok: True` after the MP-340 / MP-359 proof-path doc updates (2026-03-09 local run) | done |
| `python3 dev/scripts/devctl.py process-cleanup --verify --format md` | `ok: True`; zero repo-related processes detected before/after cleanup (2026-03-09 local run) | done |
| `python3 - <<'PY' ... -> dev/reports/autonomy/experiments/mp342-344-swarm-vs-solo-20260225/{summary.md,summary.json,*.svg}` | generated direct comparison table + SVG graphs for swarm (`swarm_count=5`) vs no-swarm control (`swarm_count=1`) across `research-first` and `specialized` tactics (2026-02-25 local run) | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_phone_status dev.scripts.devctl.tests.test_autonomy_report` | phone-status parser/command/projection bundle behavior covered and phone reason metric extraction fixed (`Ran 5 tests ... OK`, 2026-02-24 local run) | done |
| `python3 -m unittest dev.scripts.devctl.tests.test_controller_action` | controller-action parser/guard/action behavior covered (`refresh-status`, allowlist-reject, allowlist dry-run dispatch, pause-loop mode-file write) (`Ran 5 tests ... OK`, 2026-02-24 local run) | done |
| `python3 dev/scripts/checks/check_code_shape.py` | `ok: True` after autonomy-loop helper split (2026-02-24 local run) | done |
| `python3 dev/scripts/checks/check_code_shape.py` | `ok: True` after guarded `swarm_run` split + `dev/scripts/mutation/cli.py` compaction removed pre-existing growth-budget violation (2026-02-24 local run) | done |
| `python3 dev/scripts/audits/audit_metrics.py --input dev/audits/templates/audit_events_template.jsonl --output-md /tmp/audit-metrics.md --output-json /tmp/audit-metrics.json --chart-dir /tmp/audit-metrics-charts` | summary + JSON + chart outputs emitted (2026-02-24 local run) | done |
| `DEVCTL_AUDIT_CYCLE_ID=baseline-2026-02-24 DEVCTL_EXECUTION_SOURCE=script_only python3 dev/scripts/devctl.py list` | event row appended to `dev/reports/audits/devctl_events.jsonl` (2026-02-24 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --run-label autonomy-run-live-20260224-091724Z` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/autonomy-run-live-20260224-091724Z/summary.md` (2026-02-24 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --run-label autonomy-run-live-20260224-092520Z` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/autonomy-run-live-20260224-092520Z/summary.md` (2026-02-24 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-340 --run-label mp340-controller-state-r1` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/mp340-controller-state-r1/summary.md` (2026-02-24 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-340 --run-label mp340-controller-state-r2-10workers` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/mp340-controller-state-r2-10workers/summary.md` (2026-02-24 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-340 --run-label cont-fix-20260224-110234Z` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/cont-fix-20260224-110234Z/summary.md` (2026-02-24 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-330 --run-label mp330-swarm-20260224a` | swarm_ok=True, governance_ok=False, summary=`dev/reports/autonomy/runs/mp330-swarm-20260224a/summary.md` (2026-02-24 local run) | blocked |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --run-label 20260224-133052Z-c01` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/20260224-133052Z-c01/summary.md` (2026-02-24 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --run-label 20260224-133052Z-c02` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/20260224-133052Z-c02/summary.md` (2026-02-24 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --run-label 20260224-133052Z-c03` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/20260224-133052Z-c03/summary.md` (2026-02-24 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --run-label 20260224-133052Z-c04` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/20260224-133052Z-c04/summary.md` (2026-02-24 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --run-label 20260224-133052Z-c05` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/20260224-133052Z-c05/summary.md` (2026-02-24 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --run-label orchestrator-live-bounded-c01` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/orchestrator-live-bounded-c01/summary.md` (2026-02-24 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --run-label orchestrator-live-bounded-c02` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/orchestrator-live-bounded-c02/summary.md` (2026-02-24 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --run-label orchestrator-live-bounded-c03` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/orchestrator-live-bounded-c03/summary.md` (2026-02-24 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --run-label swarm10-20260224-085105-c01` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/swarm10-20260224-085105-c01/summary.md` (2026-02-24 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --run-label swarm10-20260224-085105-c02` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/swarm10-20260224-085105-c02/summary.md` (2026-02-24 local run) | done |
| `python3 -m compileall app/pyside6` | historical evidence from the retired 2026-02-25 exploratory GUI scaffold; path removed from active scope on 2026-02-26 | archived |
| `source ../../.venv-pyside6/bin/activate && QT_QPA_PLATFORM=offscreen python3 - <<'PY' ... CommandCenterWindow()` | historical offscreen smoke for the retired exploratory GUI path; `.venv-pyside6` and `app/pyside6` removed on 2026-02-26 | archived |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --run-label ralph-wiggum-max-swarm-20260225-c01` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/ralph-wiggum-max-swarm-20260225-c01/summary.md` (2026-02-25 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --run-label ralph-wiggum-max-swarm-20260225-c02` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/ralph-wiggum-max-swarm-20260225-c02/summary.md` (2026-02-25 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --run-label ralph-wiggum-max-swarm-20260225-c03` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/ralph-wiggum-max-swarm-20260225-c03/summary.md` (2026-02-25 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --run-label ralph-wiggum-max-swarm-20260225-c04` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/ralph-wiggum-max-swarm-20260225-c04/summary.md` (2026-02-25 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --run-label ralph-wiggum-max-swarm-20260225-c05` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/ralph-wiggum-max-swarm-20260225-c05/summary.md` (2026-02-25 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --run-label ralph-wiggum-max-swarm-20260225-c06` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/ralph-wiggum-max-swarm-20260225-c06/summary.md` (2026-02-25 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --run-label ralph-wiggum-max-swarm-20260225-c07` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/ralph-wiggum-max-swarm-20260225-c07/summary.md` (2026-02-25 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --run-label ralph-wiggum-max-swarm-20260225-c08` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/ralph-wiggum-max-swarm-20260225-c08/summary.md` (2026-02-25 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --run-label ralph-wiggum-max-swarm-20260225-c09` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/ralph-wiggum-max-swarm-20260225-c09/summary.md` (2026-02-25 local run) | done |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --run-label ralph-wiggum-max-swarm-20260225-c10` | swarm_ok=True, governance_ok=True, summary=`dev/reports/autonomy/runs/ralph-wiggum-max-swarm-20260225-c10/summary.md` (2026-02-25 local run) | done |
| `swift test` | pass in `app/ios/VoiceTermMobile` on 2026-03-09 local elevated run (`6` tests) confirming the shared mobile core package still decodes and renders the projection bundle contract | done |
| `xcodebuild -project VoiceTermMobileApp.xcodeproj -scheme VoiceTermMobileApp -destination generic/platform=iOS CODE_SIGNING_ALLOWED=NO build` | pass in `app/ios/VoiceTermMobileApp` on 2026-03-09 local elevated run (`** BUILD SUCCEEDED **`) confirming the runnable iOS app target builds cleanly | done |
| `python3 -m pytest dev/scripts/devctl/tests/test_mobile_app.py dev/scripts/devctl/tests/test_mobile_status.py dev/scripts/devctl/tests/test_controller_action.py -q --tb=short` | pass on 2026-03-09 local run (`18 passed`) covering the new `mobile-app` simulator/device parser + command paths alongside the shared controller/mobile status contract | done |
| `python3 dev/scripts/devctl.py mobile-app --action simulator-demo --format md` | pass on 2026-03-09 local elevated run; built `VoiceTermMobileApp`, installed it into simulator `2EBCD622-74DC-4A8B-93EF-339C5717CD82`, synced `Documents/LiveBundle/full.json`, launched the app, and printed the live mobile action preview plus manual tap flow | done |
| `python3 dev/scripts/devctl.py mobile-app --action device-install --development-team TEAM12345 --format md` | honest local no-device failure on 2026-03-09 (`no connected physical iPhone/iPad detected`), confirming the scripted install path fails closed instead of pretending a phone deploy happened without a plugged-in trusted device | done |
| `python3 -m pytest dev/scripts/devctl/tests/test_review_channel.py dev/scripts/devctl/tests/test_mobile_status.py -q --tb=short` | pass on 2026-03-09 local run (`54 passed`) covering approval-mode parsing, review-channel launch scripts/reports, and mobile-status approval-policy projections | done |
| `python3 dev/scripts/checks/check_active_plan_sync.py` | `ok: True` on 2026-03-09 local run after the approval-policy/control-plane doc update | done |
| `python3 dev/scripts/devctl.py docs-check --strict-tooling` | `ok: True` on 2026-03-09 local run after the `review-channel` / `mobile-status` / `README` approval-mode docs update | done |
| `swift test` | pass in `app/ios/VoiceTermMobile` on 2026-03-09 local elevated run (`6` tests) after the approval-policy decoding + operator-console-style control-panel UI update | done |
| `xcodebuild -project VoiceTermMobileApp.xcodeproj -scheme VoiceTermMobileApp -destination generic/platform=iOS CODE_SIGNING_ALLOWED=NO build` | pass in `app/ios/VoiceTermMobileApp` on 2026-03-09 local elevated run (`** BUILD SUCCEEDED **`) after the mobile shell control-strip/dashboard styling update | done |
