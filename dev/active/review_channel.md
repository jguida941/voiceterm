# Review Channel + Shared Screen Plan

Status: execution mirrored in `dev/active/MASTER_PLAN.md` (MP-355)
Execution plan contract: required
Owner lane: Control-plane/operator surfaces

## Scope

Build one shared review/control channel for Codex, Claude, VoiceTerm operator
surfaces, and later provider/front-end adopters so agents can coordinate
through a visible, structured lane instead of ad-hoc chat copy/paste or hidden
state.

This plan covers:

1. One canonical machine-readable review packet/event contract aligned to the
   broader `controller_state` direction already tracked under MP-340 and broad
   enough to carry code-review, plan-review, and operator-decision packets
   without forking the transport.
2. Multiple projections over that contract (`json`, `ndjson`, `md`,
   overlay/terminal-packet views) using the same projection shape already used
   by `phone-status`.
3. One top-level `devctl review-channel` command surface with action-based
   verbs for posting, reading, watching, acknowledging, and replaying review
   packets in a way that fits the current flat `devctl` CLI architecture.
4. A shared-screen VoiceTerm surface where the user can watch Codex, Claude,
   and operator lanes together as one collaborative terminal-native
   workflow rather than three disconnected panes.
5. A phased path toward richer shared-session workflows without allowing unsafe
   concurrent writes into one live terminal too early.

This plan is an execution slice of the broader control-plane/operator-surface
program in `dev/active/autonomous_control_plane.md` and the full-system
extraction tracked under `dev/active/ai_governance_platform.md`, but it is
tracked separately because the schema, command surface, overlay UX, and guard
model need their own phased delivery and iteration loop. The current
Codex/Claude markdown-swarm operating mode is a temporary projection over this
contract, not the long-term product boundary.

## Execution Protocol (Required)

1. Schema-affecting work must update `Cross-Plan Dependencies`, `Schema Draft`,
   and `Integrity Model` in this file before code lands.
2. MP-355 implementation must keep `dev/active/MASTER_PLAN.md` status aligned
   with actual phase completion; hidden memory-only coordination is not
   acceptable execution state.
3. Any deviation from the current `devctl`-first control-plane model or the
   current read-only MCP posture must be recorded here and in
   `dev/active/autonomous_control_plane.md` before implementation.
4. Multi-agent experiments for this track must capture packet samples,
   projection outputs, and shared-screen evidence in repo-visible artifacts or
   this file's `Progress Log` / `Audit Evidence`, not hidden side channels.
5. The current operator-facing markdown loop should minimize required user
   intervention: once scope is set, the reviewer/coder pair should continue
   autonomously and ask the user only for ambiguous product intent,
   destructive/external actions, credentials/auth, push/publish approval, or
   required physical/manual validation. Routine review handoffs and next-slice
   coordination belong in the bridge artifact plus reviewer chat pings, not as
   repeated orchestration requests to the operator.
6. In that autonomous mode, `MASTER_PLAN.md` remains the canonical tracker and
   `INDEX.md` remains the router for loading the minimal required active docs.
   Reviewer/coder agents should descend through that active-plan chain, update
   the relevant active markdown authority as work progresses, and keep
   executing until the current scoped checklist items and live review findings
   are closed, rather than waiting for the operator to restate the next step.
7. Until Phase 1 replaces the markdown bridge with structured artifacts,
   `check_review_channel_bridge.py` must guard the `bridge.md` bootstrap
   contract, section layout, and operator-visible heartbeat requirements in
   the same governance lane as the other plan-sync checks.
8. For today's markdown bridge, "current slice accepted" is not a terminal
   stop if scoped plan work remains. The reviewer must promote the next
   highest-priority unchecked scoped plan item into the bridge and keep the
   loop moving until the scoped plan is exhausted or a real blocker/approval
   boundary is hit.
8.1 In `active_dual_agent` markdown-bridge mode, the temporary live loop must
    be explicit and repeatable: Codex starts polling immediately after
    bootstrap, Claude starts in polling mode immediately after bootstrap,
    Claude codes one bounded slice at a time, then returns to wait/poll mode,
    Codex re-reviews that slice and rewrites the bridge, and the pair keeps
    cycling until the scoped plan is exhausted or a real blocker/approval
    boundary is hit. When the scoped slice is plan hardening rather than code
    change, the same loop applies through plan-review packets against typed
    plan targets, and only the intake-selected canonical-plan writer may patch
    the reviewed plan markdown.
9. The same backend must serve developers, solo agents, and dual-agent loops.
   Any future PyQt6/mobile toggle should switch `reviewer_mode` on the shared
   backend (`active_dual_agent`, `single_agent`, `tools_only`, `paused`,
   `offline`) instead of inventing a separate dev-only control plane.

## Locked Decisions

1. `controller_state` remains the umbrella operator/control-plane contract for
   MP-340. MP-355 may define `review_state` and `review_event`, but shared
   fields must reuse MP-340 naming and semantics instead of inventing parallel
   authority.
2. Structured state/events are canonical. Markdown is a projection, not an
   authority.
3. The canonical write path is `devctl`. MCP may later expose additive
   read-only snapshots for review-channel state, but Phase 0-2 do not add MCP
   write tools or bypass `devctl` policy/validation.
4. Initial shared-screen delivery uses separate PTY/session ownership per
   agent. Shared visibility does not require shared live write ownership, but
   the user-facing surface should still read as one collaborative terminal
   workflow.
5. Before true shared-write ownership exists, packet exchange, staged drafts,
   current task state, and last-seen/apply state should make it obvious to the
   operator that both agents are working inside one system and are aware of
   each other's latest state.
6. The end-state may include a guarded shared target session, but concurrent
   free-form writes into one live terminal are out of scope until explicit
   lock/lease, ack/apply, and audit controls are proven.
7. Overlay integration must preserve the default VoiceTerm single-backend voice
   path unless the user explicitly enters a review/monitor surface.
8. Any agent-to-agent or agent-to-operator handoff must be packetized and
   replayable; hidden memory-only coordination is not acceptable execution
   state.
9. Initial refresh for Rust review surfaces should use local artifact polling
   and existing periodic task hooks rather than a new filesystem-watcher
   dependency.
10. Planning review must reuse this packet/event transport instead of creating
    a second authoritative `plan.md` bridge. When packets target mutable plan
    authority, the canonical plan stays authoritative and packet state is
    proposal/coordination only.
11. The long-term human-facing markdown bridge is one backend-fed
    `CollaborationSession` projection over `WorkIntakePacket`, review packets,
    reviewer state, and writer leases. It must expose role assignment,
    current slice, peer findings/responses, disagreement/arbitration,
    delegated-worker receipts, restart packet, and ready gates without
    becoming a second authority for plans, queues, or review truth.
12. The review backend must preserve the startup-authority boundary:
    `WorkIntakePacket` stays the bounded startup/work-routing contract and
    `CollaborationSession` stays the live shared-work projection. Do not
    collapse those contracts inside MP-355 just to simplify bridge prose.
13. Concurrency controls are additive, not substitutive: intake-backed writer
    authority decides who may mutate canonical plan/session state, while
    `expected_revision`, `version_counter`, and `state_hash` style checks
    decide when a stale reader must re-read before acting.

## Cross-Plan Dependencies

1. `dev/active/autonomous_control_plane.md` owns the umbrella
   `controller_state` direction, phone/SSH parity, Rust Dev-panel parity,
   operator action governance, and ADR backlog for MP-340.
2. MP-355 owns review-specific packet semantics, inbox/ack/watch/history
   behavior, shared-screen layout, and review-channel guard/test coverage.
3. `ADR-0027` is the accepted authority for shared controller-state field
   names and projection strategy across MP-340 and MP-355.
4. `ADR-0028` is the accepted authority for agent relay packet semantics;
   `review_event` must remain its concrete packetized realization rather than
   a competing protocol.
5. Shared fields must retain exact names and meanings across MP-340 and MP-355:
   `event_id`, `session_id`, `project_id`, `trace_id`, `timestamp_utc`,
   `source`, `event_type`, `plan_id`, `controller_run_id`, `from_agent`,
   `to_agent`, `evidence_refs`, `confidence`, `requested_action`,
   `idempotency_key`, `nonce`, `expires_at_utc`.
6. MP-336 owns explicit `--monitor` / `--mode monitor` startup-mode routing.
   MP-355 should attach to the existing `--dev` panel first or stage against
   the future MP-336 monitor selector; it should not alter the default startup
   voice path on its own.
7. MP-356 host-process hygiene is required validation for any review-channel
   work that increases concurrent PTY/session visibility or packet-to-PTY
   staging behavior.
8. `dev/active/memory_studio.md` owns durable recall, handoff, and
   compaction-survival outputs. MP-355 review artifacts should compile cleanly
   into `session_handoff` / survival-index inputs so active blockers, current
   decisions, and next action survive context loss, session restart, or
   cross-agent handoff without hidden side channels.
9. Review packets may attach memory-produced context by reference only:
   `task_pack`, `handoff_pack`, and `survival_index` stay canonical under
   Memory Studio and are linked through `context_pack_refs` rather than copied
   inline into review artifacts. Bridge-era markdown/JSON handoff bundles are
   transitional projections only and do not count as this contract landing
   until structured `review_state` / `controller_state` artifacts emit and
   consume the same references.
10. When memory capture is active, `packet_posted`, `packet_acked`,
    `packet_dismissed`, and `packet_applied` must emit corresponding normalized
    memory events through the existing ingest path so handoff/decision history
    survives outside the review-channel artifact root.
11. Provider-specific formatting of attached context belongs to Memory Studio
    adapter profiles (`MP-238`); review-channel routing selects the target
    backend/profile but does not invent a second pack format.
12. Unified timeline/replay remains an MP-340 umbrella projection over
    controller, review, and memory traces once Phase-1/2 artifacts are stable;
    MP-355 must keep timestamps, trace ids, and header fields compatible with
    that later merge view.
13. `dev/active/platform_authority_loop.md` under `MP-377` owns
    `PlanRegistry`, `PlanTargetRef`, and `WorkIntakePacket`. Any planning-
    review packet in MP-355 must resolve target plans through that startup-
    authority stack instead of hard-coded repo paths, exact line numbers, or
    whole-block markdown matching.
14. `MP-377` owns continuation-budget and push-readiness authority
    (`push_enforcement`, `checkpoint_required`,
    `safe_to_continue_editing`, `review_gate_allows_push`, and successor
    push-decision contracts such as `push_eligible_now`). MP-355 may surface
    that state in `review-channel status`, bridge projections, and live wait
    reasons, but it must not redefine the governing decision logic locally.
15. MP-355 owns the live review projection for typed
    `ReviewCurrentSessionState`, while `MP-377` owns startup/push/preflight
    consumers that use `current_session`, reviewer acceptance, and checkpoint
    state to decide whether a new implementation slice or governed push may
    proceed. Keep that producer/consumer split explicit in docs and runtime
    contracts so the review channel does not become a second startup-
    authority source.

## Transitional Markdown Bridge (Current Operating Mode)

Until Phase 1 lands in code, the sanctioned live coordination bridge for the
current Codex-reviewer / Claude-coder loop is this repo's `bridge.md`
compatibility projection. Typed `review_state` remains the canonical
machine-readable authority; `bridge.md` is the temporary coordination surface
for the work happening now, not an accident or an off-book workaround.

Rules for the markdown bridge:

1. `bridge.md` is current-state coordination only. Keep live verdicts,
   open findings, reviewer instructions, coder status/questions/acks, and the
   latest non-audit worktree hash there; do not turn it into an endless chat
   transcript dump.
2. Codex owns reviewer-state sections (`Poll Status`, `Current Verdict`,
   `Open Findings`, `Current Instruction For Claude`). Claude owns
   coder-state sections (`Claude Status`, `Claude Questions`, `Claude Ack`).
3. Codex polls non-`bridge.md` worktree deltas every 2-3 minutes while
   code is moving, or sooner after a meaningful code chunk / explicit user
   request. Poll cadence is part of the protocol, not ad-hoc reviewer choice.
4. Each meaningful reviewer update must record the latest reviewed non-audit
   worktree hash so both agents know which state was actually reviewed.
5. Reviewer findings must reference concrete files/checks/tests when possible
   and must distinguish still-blocking items from accepted / resolved ones.
6. Claude must acknowledge each live finding with short state markers such as
   `fixed`, `acknowledged`, `needs-clarification`, `blocked`, or `deferred`.
6.1 Multi-agent specialization is allowed, but bridge writes stay
    conductor-owned: only one Codex conductor updates the Codex-owned bridge
    sections and only one Claude conductor updates the Claude-owned bridge
    sections. Specialist reviewer/fixer workers must report back to their
    conductor instead of editing `bridge.md` directly.
6.2 Bridge behavior is mode-aware. When `Reviewer mode` is `active_dual_agent`,
    Claude must treat `bridge.md` as the live reviewer/coder coordination
    surface for this compatibility mode and keep polling it instead of waiting
    for the operator to restate the process. The typed `review_state`
    projection remains the canonical machine authority for current-session
    truth. When the structured review queue is available, Claude must also
    poll the Claude-targeted `review-channel inbox/watch` surface on the same
    cadence so direct reviewer packets are consumed through the canonical
    event/projection path instead of relying on operator chat relay. When
    `Reviewer mode` is `single_agent`, `tools_only`, `paused`, or `offline`,
    Claude must not assume a live Codex review loop unless a reviewer-owned
    bridge section explicitly reactivates it.
6.2.1 In that active mode, the live cycle is:
    `bootstrap -> poll bridge + inbox/watch -> acknowledge -> code one bounded
    slice -> update coder state -> wait/poll for re-review -> receive next
    reviewer bridge write or direct packet -> repeat`.
    Claude must not treat one landed patch as permission to self-promote the
    next task; Codex must not stop polling just because one slice turned green.
6.2.2 When the active scoped slice is plan hardening, the same live cycle
    routes through typed plan targets instead of raw code diffs:
    `select WorkIntakePacket -> post plan_gap_review against PlanTargetRef +
    anchor_refs -> designated plan writer patches canonical plan -> re-review
    updated target_revision -> emit plan_ready_gate or next gap`.
    Match mutable plan targets by typed target refs and stable
    heading/checklist/progress anchors, not by raw line numbers or brittle
    surrounding prose, so adjacent markdown edits do not strand the loop.
    `plan_gap_review` identifies a missing/wrong plan element,
    `plan_patch_review` proposes one typed canonical-plan mutation but is not
    itself the canonical edit, and `plan_ready_gate` records reviewer
    acceptance that the targeted plan slice is coherent enough to proceed.
6.3 If reviewer-owned bridge state says `hold steady`, `waiting for reviewer
    promotion`, `Codex committing/pushing`, or equivalent wait-state language,
    Claude must stay in polling mode. It must not mine plan docs for side work
    or self-promote the next slice until a reviewer-owned section changes.
7. The markdown bridge is a temporary projection path for today's workflow. It
   does not replace the Phase-1 `review_event` / `review_state` artifact model;
   once the real `devctl review-channel` path exists, `bridge.md` should
   become a backend-fed, repo-pack-portable projection/example/fallback mode
   instead of remaining live authority or a VoiceTerm-only branch of the
   architecture.
8. In the current operator-facing loop, each meaningful Codex reviewer write to
   `bridge.md` must also emit a concise operator-visible chat update that
   summarizes the reviewed non-audit worktree hash, whether the blocker set
   changed, and any new instruction for Claude. The chat ping is observability
   for the human operator, not a second execution authority.
8.1 While code is moving, Codex should also emit a lightweight operator-visible
    heartbeat every five minutes even when the blocker set is unchanged so the
    human can tell the loop is still alive.
8.2 This observability requirement must graduate out of chat habit and into the
    shared backend: the same heartbeat/findings/next-action stream should feed
    chat summaries, CLI status, PyQt6, phone/mobile, and overlay projections
    automatically so the operator does not need to keep asking whether the loop
    is still running.
9. Until structured `review_event` / `review_state` artifacts land, the
   markdown bridge contract itself must stay machine-checked so a fresh convo
   can bootstrap safely from the attached `bridge.md` file without relying
   on hidden session memory.
10. The bridge guard is conditional on the bridge being active. If repo-root
    `bridge.md` is absent, `check_review_channel_bridge.py` should treat
    that as "bridge inactive" instead of failing clean checkouts or unrelated
    branches.
11. For truly hands-off checklist progression, the repo-native runner is
    `devctl swarm_run --continuous`; the markdown bridge should mirror that
    same next-step promotion behavior during live Codex/Claude sessions rather
    than stopping at one accepted slice.
12. Default multi-agent wakeups should be change-routed instead of brute-force:
    the Codex conductor polls the full non-audit tree every 2-3 minutes while
    specialist workers wake on owned-path changes or explicit conductor
    re-review requests rather than every worker re-scanning the entire tree on
    the same cadence.
13. The transitional local bootstrap command is
    `python3 dev/scripts/devctl.py review-channel --action launch`. It must:
    stay bridge-gated, seed prompts that route both conductors back through
    `AGENTS.md`, `dev/scripts/README.md`, and `dev/guides/DEVCTL_AUTOGUIDE.md`,
    and be retired or migrated once the markdown bridge is inactive or the
    overlay-native review launcher becomes canonical.
14. Header metadata must include `Reviewer mode`. `active_dual_agent` keeps the
    live reviewer/implementer freshness contract on; `single_agent`,
    `tools_only`, `paused`, and `offline` keep the same bridge/runtime surfaces
    but suspend stale dual-agent enforcement until the reviewer resumes active
    mode.
15. Repo-owned writer actions must keep bridge truth honest:
    `review-channel --action reviewer-heartbeat` updates liveness only, while
    `review-channel --action reviewer-checkpoint` is the only sanctioned path
    for advancing reviewed hash, verdict, findings, instruction, and reviewed
    scope together. For AI-generated markdown or other shell-sensitive bodies,
    reviewer checkpoints should prefer one typed
    `--checkpoint-payload-file` (or the existing per-section `--*-file` flags
    when bodies intentionally stay split) instead of inline shell text.
    Guards validate these fields but must not auto-write reviewer truth.
16. Human-facing controls may offer simple aliases such as `agents` and
    `developer`, but review artifacts and projections must normalize those
    inputs to the canonical reviewer-mode values (`active_dual_agent`,
    `single_agent`, `tools_only`, `paused`, `offline`).

Minimum bridge state:

1. The current markdown bridge should always expose the equivalent of:
   `state`, `task_id_or_scope`, `owner`, `last_reviewed_worktree_hash`,
   `review_status`, `blockers`, `next_action`, and `last_poll_utc`, even if the
   human-readable file spells those out through section names instead of one
   literal key/value table.
2. For the current `bridge.md` projection, those fields map to:
   `Poll Status` + `Current Verdict` + `Open Findings` + `Current Instruction
   For Claude` + `Claude Ack` + header metadata (`Last Codex poll`,
   `Reviewer mode`, `Last non-audit worktree hash`).
3. The important property is not markdown vs JSON. The important property is
   that the current coordination file behaves like a lightweight coordination
   log with explicit current state, ownership, and next action instead of loose
   notes.

Temporary bridge state machine:

1. The current operating loop should behave like:
   `idle -> coding -> review_pending -> findings_posted -> claude_ack_pending
   -> fix_in_progress -> verify_pending -> resolved -> next_slice_selected -> coding`
   or `blocked` / `scope_exhausted`.
2. `bridge.md` does not need one literal `state=` line yet, but the live
   sections must make that state inferable without rereading chat transcript or
   hidden memory.
3. Any reviewer update that moves the loop into `blocked` or `resolved` must
   refresh `blockers`, `next_action`, `last_reviewed_worktree_hash`, and
   `last_poll_utc` in the same write so both agents are looking at the same
   current state.
4. For the current human-observed loop, the reviewer should also expose
   `last_poll_local` in the markdown header and repeat the same review summary
   in chat so the operator can see reviewer activity without reopening the
   markdown file.
5. When the loop reaches `resolved` and scoped plan work still exists, the
   reviewer must update `next_action` to the next unchecked scoped plan item
   instead of leaving the bridge in a completed-but-idle state.

Temporary bridge failure modes:

1. Stale reads: reviewer comments applied to the wrong repo state. Current
   guard path is reviewed-hash + poll timestamp recording on each meaningful
   Codex update.
2. Section clobbering: one agent overwrites the other's state. Current guard
   path is strict section ownership inside `bridge.md`.
3. Blocking-state ambiguity: Claude cannot tell which findings are blockers vs
   advisory notes. Current guard path is keeping only live blockers in
   `Open Findings` and putting accepted direction in `Current Verdict`.
4. Markdown/repo drift: the file says one thing while the repo says another.
   Current guard path is reviewer updates citing concrete files/checks/tests
   plus the latest reviewed non-audit worktree hash.
5. Context-loss drift: active blockers disappear after compaction, session
   restart, or agent handoff. The forward path is reducing this same state into
   Phase-1 `review_state` / `controller_state` artifacts and memory-backed
   `session_handoff` / survival-index inputs instead of inventing a separate
   hidden memory channel.
6. Completion stall: one accepted slice finishes and both agents stop even
   though scoped plan work remains. Current guard path is explicit next-slice
   promotion in `bridge.md`, operator-visible reviewer chat pings, and the
   repo-native fallback of `devctl swarm_run --continuous` for fully hands-off
   plan progression.
7. Fixed-offset polling: the implementer re-reads one unchanged bridge line or
   stale section range and misses reviewer changes that landed elsewhere in the
   same file. Current guard path is requiring `Poll Status` + `Current Verdict`
   + `Open Findings` + `Current Instruction For Claude` to be re-read together,
   plus generated prompt/autoguide instructions that force timestamp-first
   repolls instead of cached line-range polling.

## Repo Wiring Constraints

1. `review-channel` must ship as one flat top-level `devctl` command wired
   through a dedicated parser module and command handler registration, then
   listed in the command inventory. Do not grow `cli_parser/reporting.py`
   further for MP-355; this track should use a dedicated parser file such as
   `dev/scripts/devctl/review_channel/parser.py` or a similarly isolated
   builder path.
2. `review-channel` must receive an explicit audit-events area mapping on first
   implementation day; do not let the command fall through to `misc`.
3. Review-channel policy must extend the existing
   `dev/config/control_plane_policy.json` contract. Do not add a second ad-hoc
   policy file for actor routing, ack/apply permissions, or packet-staging
   behavior.
4. Any new review-channel guard must land in all three places together:
   command/test code, `bundle_registry.py`, and the mirrored
   `tooling_control_plane.yml` / `release_preflight.yml` workflow gates.
5. Any new review-channel runtime artifact root must be added to protected-path
   retention governance in the same implementation change.
6. Any direct/raw `cargo test` usage for this track must be followed by
   `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel`
   per repo process-hygiene policy.

## Canonical Artifact Layout

Phase-1 artifact layout should live under `dev/reports/review_channel/`:

1. `state/latest.json`
   latest reduced `review_state` snapshot.
2. `events/trace.ndjson`
   append-only `review_event` stream used for replay/history rebuild.
3. `projections/latest/full.json`
4. `projections/latest/compact.json`
5. `projections/latest/trace.ndjson`
6. `projections/latest/actions.json`
7. `projections/latest/latest.md`
8. `registry/agents.json`
   local review-lane agent registry snapshot and script-backed job-board state.
9. `history/<timestamp-or-label>/...`
   optional dated replay bundles for debugging/demo evidence.

Retention rule:

1. `state/`, `events/`, `projections/`, and `registry/` are protected runtime
   artifacts and must be added to the report-retention protected-path policy in
   the same implementation change.
2. Only dated `history/` bundles may be treated as managed ephemeral report
   output for retention cleanup.

## Schema Draft

### Contract Relationship

1. `review_event` is the append-only write authority.
2. `review_state` is the latest reduced snapshot derived from the validated
   event stream.
3. `review_state` is a review-focused profile over the broader
   `controller_state` direction, not a second competing control-plane root.

### Shared Event Header Contract

1. `review_event` headers must be losslessly normalizable into Memory Studio's
   canonical event envelope and MP-340 controller audit fields.
2. Phase 0 must freeze the normalization map:
   `event_id -> event_id`, `session_id -> session_id`,
   `project_id -> project_id`, `timestamp_utc -> ts` for memory ingest,
   `source -> source`, `event_type -> event_type`, and
   `trace_id -> trace_id`.
3. `from_agent` and `to_agent` are routing fields, not substitutes for
   `source`. `source` identifies the emitting subsystem/command path (for
   example `review_channel`), while agent ids remain explicit payload fields.
4. Review-specific fields may extend the header, but they must not force Memory
   Studio or MP-340 to maintain a second parallel alias table for the same
   semantics.

### `review_state` Fields

- `schema_version: int`
  required; starts at `1`.
- `command: "review-channel"`
  required; matches current `devctl` reporting style.
- `project_id: string`
  required stable repo identity hash/path key shared with Memory Studio.
- `timestamp: string`
  required UTC ISO-8601 `Z` timestamp for snapshot generation time.
- `ok: bool`
  required reducer/projection health bit.
- `review: object`
  required; contains:
  - `plan_id: string`
  - `controller_run_id: string`
  - `session_id: string`
  - `surface_mode: string`
  - `active_lane: string`
  - `refresh_seq: int`
- `agents: array<object>`
  required; each row contains:
  - `agent_id: string`
  - `display_name: string`
  - `role: string`
  - `status: active|idle|waiting|offline`
  - `capabilities: array<string>`
  - `lane: codex|claude|review|operator`
  - `session_ref: string?`
  - `last_seen_utc: string?`
  - `assigned_job: string?`
  - `job_status: queued|reading|implementing|reviewing|blocked|waiting|done`
  - `waiting_on: string?`
  - `last_packet_id_seen: string?`
  - `last_packet_id_applied: string?`
  - `script_profile: string?`
  - `editable_fields: array<string>?`
- `packets: array<object>`
  required; latest pending/recent review packet state with:
  - `packet_id: string`
  - `trace_id: string`
  - `latest_event_id: string`
  - `from_agent: string`
  - `to_agent: string`
  - `kind: finding|question|draft|action_request|approval_request|decision|system_notice|plan_gap_review|plan_patch_review|plan_ready_gate`
    planning-kind semantics:
    `plan_gap_review` = reviewer finding against plan authority,
    `plan_patch_review` = proposed typed plan mutation for the designated
    writer to apply or reject,
    `plan_ready_gate` = reviewer acceptance/closure for the targeted plan
    slice.
  - `target_kind: string?`
    optional enum `code|plan|policy|artifact|runbook|runtime`; required as
    `plan` for planning-review kinds.
  - `target_ref: string?`
    optional typed target reference; plan targets should resolve through
    `PlanTargetRef`. Required for planning-review kinds.
  - `target_revision: string?`
    optional expected revision/hash of the referenced authority surface;
    required for planning-review kinds.
  - `anchor_refs: array<string>?`
    ordered stable anchors for plan mutations; required for planning-review
    kinds. Initial grammar is registry-generated ids only:
    `checklist:<id>`, `section:<id>`, `session_resume:<id>`, `progress:<id>`,
    `audit:<id>`. Resolve from most-specific to least-specific; the first
    resolvable anchor must match `target_ref`, and ambiguity, mismatch, or
    missing highest-precedence anchors fails closed with no fuzzy fallback.
  - `summary: string`
  - `body: string`
  - `evidence_refs: array<string>`
  - `confidence: number`
  - `requested_action: string`
  - `mutation_op: string?`
    optional typed mutation operation for mutable plan targets. Initial
    allowed values:
    `rewrite_section_note|set_checklist_state|rewrite_session_resume|append_progress_log|append_audit_evidence`.
  - `intake_ref: string?`
    optional `WorkIntakePacket` reference that selected the target, canonical
    writer, and required write-back sinks. Required for planning-review kinds;
    missing, expired, or lease-mismatched intake makes the packet invalid.
  - `policy_hint: review_only|stage_draft|operator_approval_required|safe_auto_apply`
  - `approval_required: bool`
  - `status: pending|acked|dismissed|applied|expired`
  - `acked_by: string?`
  - `acked_at_utc: string?`
  - `applied_at_utc: string?`
  - `expires_at_utc: string?`
  - `context_pack_refs: array<object>?`
    optional attached memory context bundles:
    - `pack_kind: task_pack|handoff_pack|survival_index`
    - `pack_ref: string`
    - `adapter_profile: canonical|codex|claude|gemini`
    - `generated_at_utc: string?`
  - `terminal_packet: object?`
    optional; exact v1 shape mirrors Rust `DevTerminalPacket`:
    - `packet_id: string`
    - `source_command: string`
    - `draft_text: string`
    - `auto_send: bool`
    no additional keys in Phase 1.
- `queue: object`
  required; summary counts by target/status plus `stale_packet_count`.
- `warnings: array<string>`
- `errors: array<string>`

### `review_event` Fields

- `schema_version: int`
  required; starts at `1`.
- `event_id: string`
  required unique append identifier.
- `session_id: string`
  required stable review/session correlation id.
- `project_id: string`
  required stable repo identity hash/path key shared with Memory Studio.
- `packet_id: string`
  required stable packet identifier across transitions.
- `trace_id: string`
  required correlation id linking one review packet to later actions.
- `timestamp_utc: string`
  required UTC ISO-8601 `Z` timestamp.
- `source: string`
  required emitting subsystem/command path, for example `review_channel`.
- `plan_id: string`
- `controller_run_id: string`
- `event_type: string`
  required enum:
  `packet_posted|packet_acked|packet_dismissed|packet_applied|packet_expired|projection_rebuilt|toast_emitted`
- `from_agent: string`
- `to_agent: string`
- `kind: string`
  same enum as `review_state.packets[*].kind`.
  Planning-kind semantics are identical to `review_state.packets[*].kind`.
- `target_kind: string?`
  optional enum `code|plan|policy|artifact|runbook|runtime`; required as
  `plan` for planning-review kinds.
- `target_ref: string?`
  optional typed target reference; plan targets should resolve through
  `PlanTargetRef`. Required for planning-review kinds.
- `target_revision: string?`
  optional expected revision/hash of the referenced authority surface;
  required for planning-review kinds.
- `anchor_refs: array<string>?`
  ordered stable anchors for plan mutations; required for planning-review
  kinds. Initial grammar is registry-generated ids only:
  `checklist:<id>`, `section:<id>`, `session_resume:<id>`, `progress:<id>`,
  `audit:<id>`. Resolve from most-specific to least-specific; the first
  resolvable anchor must match `target_ref`, and ambiguity, mismatch, or
  missing highest-precedence anchors fails closed with no fuzzy fallback.
- `summary: string`
- `body: string`
- `evidence_refs: array<string>`
- `confidence: number`
- `requested_action: string`
- `mutation_op: string?`
  optional typed mutation operation for mutable plan targets. Initial allowed
  values:
  `rewrite_section_note|set_checklist_state|rewrite_session_resume|append_progress_log|append_audit_evidence`.
- `intake_ref: string?`
  optional `WorkIntakePacket` reference that selected the target, canonical
  writer, and required write-back sinks. Required for planning-review kinds;
  missing, expired, or lease-mismatched intake makes the event invalid.
- `policy_hint: string`
  same enum as `review_state.packets[*].policy_hint`.
- `approval_required: bool`
- `status: string`
  same enum as `review_state.packets[*].status`.
- `context_pack_refs: array<object>?`
  optional attached memory context bundles using the same shape as
  `review_state.packets[*].context_pack_refs`.
- `terminal_packet: object?`
  optional; must align exactly with the current Rust `DevTerminalPacket`
  staging contract:
  - `packet_id: string`
  - `source_command: string`
  - `draft_text: string`
  - `auto_send: bool`
  no additional keys in Phase 1.
- `idempotency_key: string`
  required; stable duplicate-suppression key.
- `nonce: string`
  required replay-protection nonce.
- `expires_at_utc: string`
  required for pending packets.
- `metadata: object`
  optional extensibility bag for projection/debug fields only.

### Example `review_event`

```json
{
  "schema_version": 1,
  "event_id": "rev_evt_0001",
  "session_id": "local-review",
  "project_id": "sha256:/Users/jguida941/testing_upgrade/codex-voice",
  "packet_id": "rev_pkt_0001",
  "trace_id": "trace_20260308_codex_001",
  "timestamp_utc": "2026-03-08T01:10:00Z",
  "source": "review_channel",
  "plan_id": "MP-355",
  "controller_run_id": "mp355-r1",
  "event_type": "packet_posted",
  "from_agent": "claude",
  "to_agent": "codex",
  "kind": "finding",
  "summary": "Refactor review-channel schema before Rust wiring",
  "body": "Shared field names must align with controller_state and ADR-0028.",
  "evidence_refs": ["dev/active/autonomous_control_plane.md#L337"],
  "context_pack_refs": [
    {
      "pack_kind": "survival_index",
      "pack_ref": ".voiceterm/memory/exports/survival_index.json",
      "adapter_profile": "codex",
      "generated_at_utc": "2026-03-08T01:09:40Z"
    }
  ],
  "confidence": 0.88,
  "requested_action": "review_only",
  "policy_hint": "review_only",
  "approval_required": false,
  "status": "pending",
  "idempotency_key": "e3e4f8d4f8d4a2b1c9aa0011",
  "nonce": "29c2f0aee77f77cb65eaa7d3",
  "expires_at_utc": "2026-03-08T01:15:00Z"
}
```

### Example `review_state`

```json
{
  "schema_version": 1,
  "command": "review-channel",
  "project_id": "sha256:/Users/jguida941/testing_upgrade/codex-voice",
  "timestamp": "2026-03-08T01:10:01Z",
  "ok": true,
  "review": {
    "plan_id": "MP-355",
    "controller_run_id": "mp355-r1",
    "session_id": "local-review",
    "surface_mode": "dev-panel",
    "active_lane": "review",
    "refresh_seq": 1
  },
  "agents": [
    {"agent_id": "codex", "display_name": "Codex", "role": "worker", "status": "active", "capabilities": ["implementation"], "lane": "codex"},
    {"agent_id": "claude", "display_name": "Claude", "role": "reviewer", "status": "active", "capabilities": ["review", "planning"], "lane": "claude"},
    {"agent_id": "operator", "display_name": "Operator", "role": "approver", "status": "waiting", "capabilities": ["approval"], "lane": "operator"}
  ],
  "packets": [
    {
      "packet_id": "rev_pkt_0001",
      "trace_id": "trace_20260308_codex_001",
      "latest_event_id": "rev_evt_0001",
      "from_agent": "claude",
      "to_agent": "codex",
      "kind": "finding",
      "summary": "Refactor review-channel schema before Rust wiring",
      "body": "Shared field names must align with controller_state and ADR-0028.",
      "evidence_refs": ["dev/active/autonomous_control_plane.md#L337"],
      "context_pack_refs": [
        {
          "pack_kind": "survival_index",
          "pack_ref": ".voiceterm/memory/exports/survival_index.json",
          "adapter_profile": "codex",
          "generated_at_utc": "2026-03-08T01:09:40Z"
        }
      ],
      "confidence": 0.88,
      "requested_action": "review_only",
      "policy_hint": "review_only",
      "approval_required": false,
      "status": "pending"
    }
  ],
  "queue": {"pending_total": 1, "pending_codex": 1, "stale_packet_count": 0},
  "warnings": [],
  "errors": []
}
```

## Data Flow

1. Agent or operator submits one review packet through
   `python3 dev/scripts/devctl.py review-channel --action post ...`.
2. The command validates required fields, policy hints, target ids, and
   idempotency before writing one `review_event`.
3. The event writer appends to `events/trace.ndjson`, then rebuilds
   `state/latest.json` through one deterministic reducer.
4. The reducer emits the standard projection bundle:
   `full.json`, `compact.json`, `trace.ndjson`, `actions.json`, `latest.md`.
5. `devctl review-channel --action status|watch|inbox|history` reads only those
   canonical artifacts; it never invents alternate state.
6. Rust review surfaces poll the same artifacts and render Codex, Claude, and
   Operator lanes from the same reduced state.
7. Attached `context_pack_refs` travel as references only; canonical memory
   packs stay in the Memory artifact roots and are not recopied into
   review-channel state.
8. When memory capture is active, `post`/`ack`/`dismiss`/`apply` must also emit
   one normalized memory event through the existing ingest path so review
   outcomes survive compaction, restart, and cross-agent handoff.
9. Any packet-to-PTY staging uses the existing `terminal_packet` contract and
   remains a separate ack/apply step with audit evidence; Phase 1-2 do not
   inject silently into a live shared terminal.
10. Optional MCP exposure, if added later, serves review-channel snapshots
   through the existing additive `devctl mcp` adapter after the CLI/state
   contract is stable; it does not become a parallel write authority.
11. Every `devctl review-channel` invocation still emits the normal
   `devctl_events.jsonl` audit record through the existing CLI wrapper; the
   review-channel artifacts supplement that log and do not replace it.

## Command Interface

Phase-1 CLI shape:

1. Add one flat top-level command registered as `review-channel`.
2. Use `--action` to fit current `devctl` parser/handler architecture instead
   of introducing nested subcommand trees as a side effect of MP-355.
3. Mirror current `devctl` output conventions:
   `--format`, `--output`, `--json-output`, `--pipe-command`, `--pipe-args`.

Planned actions:

1. `post`

   ```bash
   python3 dev/scripts/devctl.py review-channel \
     --action post \
     --from-agent claude \
     --to-agent codex \
     --kind finding \
     --summary "Refactor schema before Rust wiring" \
     --body-file /tmp/review-body.md \
     --evidence-ref dev/active/autonomous_control_plane.md#L337 \
     --requested-action review_only \
     --format md
   ```

2. `status`

   ```bash
   python3 dev/scripts/devctl.py review-channel \
     --action status \
     --state-json dev/reports/review_channel/state/latest.json \
     --view compact \
     --emit-projections dev/reports/review_channel/projections/latest \
     --format md
   ```

   Transitional bridge-backed slice now available:

   ```bash
   python3 dev/scripts/devctl.py review-channel \
     --action status \
     --terminal none \
     --format md
   ```

   The current implementation writes latest projections under
   `dev/reports/review_channel/latest/` (`review_state.json`, `compact.json`,
   `full.json`, `actions.json`, `latest.md`, `registry/agents.json`) while the
   event-backed `state/latest.json` + `watch|inbox|history` path remains open.

3. `watch`

3. `promote`

   ```bash
   python3 dev/scripts/devctl.py review-channel \
     --action promote \
     --promotion-plan dev/active/continuous_swarm.md \
     --terminal none \
     --format md
   ```

   Transitional bridge-backed slice now available:

   - Reads the configured active-plan checklist and derives the first unchecked
     scoped task.
   - Fails closed unless `Current Verdict` is resolved, `Open Findings` are
     clear, and the current Claude instruction already looks idle/completed.
   - Rewrites only `Current Instruction For Claude` and refreshes the latest
     bridge-backed projection bundle so desktop/mobile clients see the same
     repo-owned queue source.

4. `watch`

   ```bash
   python3 dev/scripts/devctl.py review-channel \
     --action watch \
     --target operator \
     --follow \
     --max-follow-snapshots 0 \
     --stale-minutes 30 \
     --format json
   ```

5. `inbox`

   ```bash
   python3 dev/scripts/devctl.py review-channel \
     --action inbox \
     --target codex \
     --status pending \
     --limit 20 \
     --format json
   ```

6. `ack`

   ```bash
   python3 dev/scripts/devctl.py review-channel \
     --action ack \
     --packet-id rev_pkt_0001 \
     --ack-state acked \
     --actor operator \
     --format md
   ```

7. `history`

   ```bash
   python3 dev/scripts/devctl.py review-channel \
     --action history \
     --trace-id trace_20260308_codex_001 \
     --limit 50 \
     --format md
   ```

Exit codes:

1. `0`
   success.
2. `1`
   state/schema/projection or stale-state failure.
3. `2`
   CLI usage error or policy denial.

## Visual Design

Initial shared-screen target is a read-first three-lane layout with one shared
status strip at the top and one shared process/timeline strip at the bottom:

```text
+--------------------------------------------------------------------------------+
| Current Slice: reducer fix     Branch: develop     Writer: Claude   q=exit     |
| Shared Goal: Claude implements, Codex reviews, operator watches approvals      |
+--------------------------------+----------------------+-------------------------+
| Claude Code                    | Shared Relay         | Codex Review            |
| state: reading review packet   | pkt-184 posted       | state: reviewing diff   |
| task: implement reducer fix    | pkt-184 acked        | verdict: 1 blocker      |
| file: review_channel.py        | next: run tests      | waiting on patch        |
| last seen: Codex finding #12   | approval: none       | last seen: Claude ack   |
| last applied: pkt-183          | heartbeat: live      | last applied: pkt-182   |
| draft: patch staged            | writer: session-local| note: retest after fix  |
+--------------------------------+----------------------+-------------------------+
| Timeline: posted -> read -> acked -> implementing -> tests -> reviewed -> apply |
| Next action: Claude patch + Codex re-review                                    |
+--------------------------------------------------------------------------------+
```

Collaborative-surface rules:

1. The first shared screen should feel like one live collaboration surface, not
   two unrelated terminals shown side by side.
2. Each lane should expose enough packet/task context that the operator can see
   what each agent is doing, what it most recently received from the other
   side, and what remains staged vs applied.
3. Cross-agent communication should appear in-context inside the shared
   surface, so packet handoffs read as part of one terminal-native workflow
   rather than an off-screen side channel.
4. The surface must always show who currently owns write authority for any
   shared target or, before Phase 4 lands, that write ownership is still
   session-local and packet-mediated.
5. The screen should also include an always-visible agent board summarizing all
   active agents, their current jobs, current job status, and what or whom they
   are waiting on, so the user can understand the whole swarm without opening a
   second control tool.
6. Any editable job/agent controls shown on screen must be thin projections over
   typed repo-owned commands or typed registry updates; the UI must not invent
   hidden job-routing logic outside `devctl` and the sanctioned artifact set.
7. Preferred visual hierarchy is:
   one shared goal/status strip, two actor lanes, a narrow relay/approval spine,
   and one shared process timeline so the operator sees one workflow instead of
   separate tools competing for attention.
8. The actor lanes should expose both `last seen` and `last applied` markers so
   the user can tell that Codex and Claude are mutually aware of each other's
   latest state instead of merely running in parallel.

Empty-state rules:

1. Empty Codex/Claude lane shows session status plus last-seen timestamp.
2. Empty Operator Bridge State lane shows "no pending review packets" plus the exact
   `devctl review-channel --action post` example to seed the channel.
3. Arrival of a new targeted packet while the normal voice overlay is active
   should raise a toast only; it must not force a mode switch.

## Keyboard Navigation

Phase-2 keyboard contract:

1. `Tab` / `Shift-Tab`
   cycle active lane.
2. `Up` / `Down` or `j` / `k`
   move within packet list/history rows.
3. `Enter`
   expand selected packet body/evidence.
4. `a`
   acknowledge selected packet.
5. `d`
   dismiss selected packet.
6. `p`
   preview staged `terminal_packet` draft only.
7. `r`
   manual refresh.
8. `q`
   exit review surface and return to the prior overlay mode.

Phase-3 voice contract:

1. `next review`
2. `ack review`
3. `show me what Claude found`
4. `open review lane`

## Integrity Model

1. Every artifact carries `schema_version`.
2. Append-only event writes must be idempotent by `packet_id` +
   `idempotency_key`.
3. `state/latest.json` and projection files must be written through
   temp-file-and-rename atomic replacement.
4. `events/trace.ndjson` appends must flush immediately; on restart/rebuild,
   the reducer may ignore only one trailing partial/corrupt line and must emit
   a warning rather than silently truncating valid history.
5. If `state/latest.json` is missing or stale, `status/watch/inbox/history`
   must rebuild from the append-only event log before reporting success.
6. Replay protection must reuse the current control-plane pattern:
   `idempotency_key`, `nonce`, and `expires_at_utc`.
7. Phase-1 event stream rotation should mirror the existing Rust memory JSONL
   pattern unless there is a documented reason not to:
   rotate at roughly 10 MB, keep one rotated backup (`trace.1.ndjson`), and
   preserve deterministic replay order across current + rotated files.
8. Pending packets older than the configured expiry window must surface as
   stale in both `status/watch` output and the guard script.
9. Packet staging is never auto-applied in Phase 1-2, even if a
   `terminal_packet` is present.
10. Canonical plan/session mutations must carry freshness proof
    (`expected_revision`, `state_hash`, or an equivalent reducer-visible
    revision token) and fail closed on mismatch instead of relying on stale
    local reads.
11. Freshness checks supplement writer ownership; they do not grant write
    authority to a caller that is not the intake-selected writer or an
    explicitly transferred replacement.

## Execution Checklist

### Phase 0 - Schema + Architecture Design

- [ ] Reconcile MP-355 with MP-340, `ADR-0027`, and `ADR-0028`, and record the
      final ownership split in both active plan docs.
- [ ] Freeze the shared event-header map with Memory Studio so
      `review_event` can normalize losslessly into the canonical memory
      envelope (`event_id`, `session_id`, `project_id`, `timestamp_utc -> ts`,
      `source`, `event_type`, `trace_id`) without alias drift.
- [ ] Freeze canonical artifact layout and protected-path expectations under
      `dev/reports/review_channel/`.
- [ ] Draft complete `review_state` and `review_event` schemas with field
      names, types, required/optional status, enums, and example payloads.
- [ ] Draft the local agent registry shape (`registry/agents.json`) with lane,
      capabilities, status, and session reference fields.
- [ ] Define the primary ingestion path as `devctl review-channel --action post`
      with optional additive read-only MCP exposure later; do not add MCP write
      tools in Phase 0/1.
- [ ] Freeze the exact `terminal_packet` sub-object contract to the current Rust
      `DevTerminalPacket` fields (`packet_id`, `source_command`, `draft_text`,
      `auto_send`) so Phase 1 does not drift into an unbounded nested blob.
- [ ] Freeze the planning-review extension on that same packet model:
      `plan_gap_review`, `plan_patch_review`, and `plan_ready_gate` plus
      `target_kind`, `target_ref`, `target_revision`, `anchor_refs`,
      `mutation_op`, and `intake_ref` must be part of the canonical schema
      rather than a second plan-only side channel. `intake_ref`,
      `target_ref`, `target_revision`, and `anchor_refs` are mandatory for
      planning-review packets.
- [ ] Define end-to-end data flow from agent post -> append-only event ->
      reduced state -> projection bundle -> `devctl`/Rust render.
- [ ] Define integrity semantics: atomic writes, idempotency, replay window,
      crash recovery, and event-stream rotation.
- [ ] Reuse the repo's existing JSONL rotation pattern where practical:
      approximately 10 MB max file size with one rotated backup unless a
      documented review-channel-specific reason requires a different limit.
- [ ] Define initial CLI signatures, outputs, and exit codes for
      `post|status|watch|inbox|ack|history`.
- [ ] Define the `control_plane_policy.json` extension for review-channel
      actor/target allowlists, ack/apply permissions, packet-staging rules, and
      the default prohibition on auto-send promotion in early phases.
- [ ] Freeze the cross-plan interop contract for `context_pack_refs`,
      memory-event bridge rules (`packet_posted|packet_acked|packet_dismissed|
      packet_applied`), and provider-profile selection so review routing reuses
      Memory Studio pack/rendering authority instead of inventing a second
      handoff channel.
- [x] Keep the temporary markdown bridge machine-guarded until Phase 1 lands:
      add `check_review_channel_bridge.py`, wire it into the same
      tooling/release governance path as the other active-plan guards, and
      require it to validate the `bridge.md` bootstrap contract for fresh
      Codex/Claude sessions.

Acceptance:

1. `review_channel.md` and `autonomous_control_plane.md` no longer disagree
   about who owns schema and packet semantics.
2. One engineer can implement Phase 1 without inventing missing fields or disk
   layout details.
3. The plan names every required guard/test/doc follow-up before code starts.

### Phase 1 - Canonical Review Channel

- [x] Land the first bridge-gated `devctl review-channel` surface as
      `--action launch` for the current markdown-swarm cycle: read the merged
      8+8 lane table, generate Codex/Claude conductor prompts that restate the
      repo's `AGENTS.md`/`devctl` policy path, optionally open local
      Terminal.app sessions, and fail closed once the markdown bridge is
      inactive so this launcher cannot outlive the transitional bridge by
      accident.
- [x] Land the first typed current-session read-authority cutover for the live
      bridge-backed loop: one `current_session` block in `ReviewState` /
      `review_state.json` is now the canonical read-side current-status
      authority for reviewer mode, instruction revision, reviewed hash, live
      findings, and peer ACK state; `latest.md` and other current-status
      markdown projections render from that typed block instead of reading
      append-only `Claude Ack` / status history prose directly.
- [ ] Keep the transitional `bridge.md` compatibility projection push-safe
      once typed `current_session` exists. `startup-context`,
      `check_tandem_consistency`, and guarded push/checkpoint paths must not
      block committed validated work merely because tracked bridge prose is
      dirty; they should consume typed current-session / push-preflight /
      liveness state, and any temporary bridge exclusion must live in repo
      policy rather than operator habit or hidden hardcoded filtering.
      Loop-control rule: once typed `push_enforcement` or other blocking
      startup/guard state says the slice is over budget or not review-safe,
      the review-channel controller must stop issuing new implementer work,
      switch attention to checkpoint/review, and surface that state to the
      operator without waiting for a human reminder in chat.
- [ ] Keep the temporary markdown-bridge validator semantically fail-closed
      while `bridge.md` remains live: `check_review_channel_bridge.py`,
      `review-channel status`, and mobile/review projections must flag
      resolved/fixed bridge verdicts that do not promote the next scoped task,
      so a reviewer-complete bridge cannot look healthy while implementer
      routing state is stale. The same validator lane must now also reject
      oversize compatibility bridges, duplicate/unsupported H2 sections,
      transcript/ANSI contamination, and overgrown live owned sections
      (`Claude Status`, `Claude Ack`) so a 4000-line mixed transcript cannot
      masquerade as current reviewer authority.
- [ ] Keep bridge repair repo-owned while the compatibility projection still
      exists: `review-channel --action render-bridge` should remain the
      sanctioned rebuild path for `bridge.md`, regenerating the bounded
      template plus sanitized live sections from repo-owned state instead of
      relying on manual bridge surgery after a bad session.
- [ ] Keep the markdown bridge portable if it survives the authority migration:
      `bridge.md` should remain an optional repo-pack-owned frontend over the
      same typed `review_state` / queue / registry backend so another repo can
      enable the bridge surface without inheriting VoiceTerm-only runtime
      assumptions or treating markdown as canonical state.
- [ ] Remove VoiceTerm-local bridge assumptions from prompts, guards, and
      projections while that migration is in flight: bridge path, review plan
      path, promotion plan path, and status artifact roots must resolve
      through `ProjectGovernance` / repo-pack state, and bootstrap text should
      describe the bridge as a repo-pack-owned compatibility projection over
      typed `review_state` rather than teaching agents to hardcode repo-root
      `bridge.md`.
- [ ] Promote continuation-budget / checkpoint gating to a first-class live
      wait reason in the same typed attention/liveness contract. When
      `push_enforcement.checkpoint_required` or
      `push_enforcement.safe_to_continue_editing=false`, the bridge/runtime
      surfaces should not collapse implementer state to generic
      `waiting_on_peer`; they should emit an explicit checkpoint-gate pause
      reason, keep reviewer/implementer ACK synchronization live, and carry
      the same typed summary/recommended action through `review-channel
      status`, `latest.md`, `review_state.json`, and bridge projections so
      Claude can keep polling/ACKing without looking stalled or offline.
      Partial: a bounded same-lane follow-up now also emits
      `review_follow_up_required` when the implementer changes the live tree
      under active reviewer supervision and `reviewed_hash_current=false`, so
      reviewer-owned follow-up no longer degrades into a vague done-looking
      stale state while Codex still owes a semantic review refresh.
- [ ] Generalize that typed current-session and queue contract just far enough
      for compatibility beyond the current named reviewer/implementer pair:
      replace named queue counters (`pending_codex`, `pending_claude`,
      `pending_cursor`, `pending_operator`) and `claude_*` / `codex_*`
      bridge-state fields with per-agent or per-lane collections plus
      compatibility projections during migration so the backend can represent
      more than one implementer or reviewer without schema forks. Keep this
      slice limited to compatibility collections/projections; full
      registry-driven topology and native multi-item routing remain Phase 3.
- [ ] Turn the live status projections into controller inputs, not only
      display surfaces. Queue and attention already drive current-focus and
      wait behavior, so the remaining gap is narrower: startup/work-intake
      routing and reviewer/implementer scheduling must also consume
      `agent_registry` plus the typed queue/attention state instead of routing
      off `current_session` alone.
- [ ] Separate live current status from history in the same slice: keep
      append-only bridge/event history in trace/history projections only, and
      make the markdown-authority demotion gate explicit for MP-355. The live
      bridge is not retired until current-status readers stop depending on
      mixed prose/history sections and can prove parity from typed current
      session state alone.
- [ ] Add `devctl review-channel` command + parser/handler wiring using the
      flat `--action` contract.
- [ ] Register parser/command wiring in isolated files that do not further grow
      `dev/scripts/devctl/cli_parser/reporting.py`; expected touchpoints include
      `dev/scripts/devctl/cli.py`, a dedicated review-channel parser module, and
      `dev/scripts/devctl/commands/listing.py`.
- [ ] Implement `post`, `status`, `watch`, `inbox`, `ack`, `dismiss`,
      `apply`, and `history` actions.
- [ ] Keep planning review on the same reducer/action path: plan-gap, plan-
      patch, and ready-gate packets must use the same `post|status|watch|
      inbox|ack|dismiss|apply|history` surface rather than a second plan-only
      command family.
- [ ] Expose the operator-facing typed action surface the thin GUI wrappers
      need: `ack|dismiss|apply` for packet decisions plus the typed
      pause/resume/stop/health hooks that future Operator Console buttons will
      call instead of writing desktop-only placeholder artifacts.
- [ ] When `target_kind=plan`, resolve mutations through `PlanTargetRef` plus
      `anchor_refs` and fail closed if the canonical target revision no longer
      matches, the intake lease is missing/expired, or the first resolvable
      anchor is ambiguous; do not patch plan markdown by approximate line-
      number or surrounding-block matching.
- [ ] Add a repo-owned reviewer heartbeat scheduler/write path for inactive
      modes so `single_agent`, `tools_only`, `paused`, and `offline` stay
      visibly current without mutating review truth. The later PyQt6/phone
      controls should call the same typed action, not invent surface-local
      liveness files.
- [ ] Add repo-owned stale-bridge demotion/recovery so docs/process validation
      is not blocked by abandoned live markdown state. When the bridge is
      marked active but the writer lease/session proof is gone or
      irrecoverably stale, the backend should emit a typed
      `runtime_missing` / repair receipt and keep workflow mode unchanged
      until an explicit reviewer or operator action pauses/offlines the
      session, instead of requiring manual `bridge.md` edits before unrelated
      validation can go green.
- [ ] Emit projection files from the same reduced state source:
      `full.json`, `compact.json`, `trace.ndjson`, `actions.json`, and
      `latest.md`.
- [ ] Add a terminal-packet projection for safe staging into a target PTY or
      overlay draft lane using the existing `DevTerminalPacket` shape.
- [x] Allow packets to carry `context_pack_refs` for `task_pack`,
      `handoff_pack`, and `survival_index`, keeping canonical pack bodies in
      Memory Studio artifact roots.
- [ ] When memory capture is active, emit normalized memory-ingest events for
      `packet_posted`, `packet_acked`, `packet_dismissed`, and
      `packet_applied` through the existing ingest path.
- [ ] Add `check_review_channel.py` guard coverage for:
      schema validation, shared-field parity against controller-state naming,
      stale pending packets, projection consistency, and protected artifact-root
      policy.
- [ ] Extend `dev/scripts/devctl/audit_events.py` so `review-channel` maps to a
      deliberate metrics area on day one.
- [ ] Extend `dev/config/control_plane_policy.json` with the review-channel
      section defined in Phase 0; do not create parallel policy config.
- [ ] Emit a typed `registry/agents.json` view that includes current job,
      job-state, waiting-on, last-packet-seen/applied, and script-profile
      fields for each visible agent.
- [ ] Replace hardcoded agent-routing tables in the packet/attention/handoff
      path (`VALID_AGENT_IDS`, rollover ACK prefixes, attention-owner maps,
      reviewer-only liveness helpers) with agent-registry / `TandemProfile` /
      repo-policy-derived routing so MP-355 does not claim N-agent support
      while the middle layer still rejects new agents.
- [ ] Make the current compatibility-only middle layer explicit in the runtime
      contract too: provider-shaped fields such as `pending_codex`,
      `pending_claude`, `claude_ack`, and `codex_poll_state` may remain as
      adapters during migration, but they must not widen into the canonical
      agent-registry/multi-agent state surface.
- [ ] Replace ad hoc bridge-section headers/markers with one typed section
      registry shared by parser, writer, projection, mutation, and guard code.
      `bridge.md` stays a compatibility projection, but section ids/names must
      resolve from one canonical mapping instead of 8+ duplicated literals and
      regex targets spread across the review-channel path.
- [ ] Keep packet state honest until writeback exists: `packet_applied` /
      `apply` is currently a queue/event transition, not proof that a plan
      mutation executed. Do not treat review-channel `apply` as real plan
      authority until repo-owned mutation handlers land with typed receipts.
- [ ] Extend promotion from `first unchecked item -> one bridge instruction`
      to multi-item extraction and lane assignment once typed current-session
      / per-agent queue authority is in place. Until that lands, keep
      multi-agent specialization conductor-coordinated and do not pretend the
      backend already does parallel work routing.
- [ ] Keep burning down the remaining review-channel Python hotspots instead of
      freezing current size debt in place. Owner/phase: `MP-355` Phase 1
      maintainability closure. Current live hotspots include
      `event_reducer.py` (~497 lines), `handoff.py` (461), `core.py` (356),
      and the giant `test_review_channel.py` suite; continue splitting by
      reducer / projection / prompt / fixture responsibility, drive the
      module family down toward a smaller stable review-channel core, and
      split `test_review_channel.py` into feature-scoped suites before
      MP-355 claims maintainability closure. (audit mapping:
      `SYSTEM_AUDIT.md` A15, T1)
- [ ] Extend `dev/scripts/devctl/reports_retention.py` protected paths for
      `dev/reports/review_channel/`.
- [ ] Wire `check_review_channel.py` into `dev/scripts/devctl/bundle_registry.py`
      and the mirrored `.github/workflows/tooling_control_plane.yml` /
      `.github/workflows/release_preflight.yml` gates.
- [ ] Add targeted unit coverage for parser wiring, schema validation,
      append-only event writing, projection rendering, `history`, and ack
      semantics.
- [ ] Land repo docs + command inventory updates in the same change:
      `dev/scripts/README.md`, `dev/guides/DEVCTL_AUTOGUIDE.md`,
      `.github/workflows/README.md`, `dev/history/ENGINEERING_EVOLUTION.md`,
      `devctl list`, audit-event area mapping, and retention-policy updates.
- [ ] Once the reducer-backed path is authoritative, run a clean-sheet
      simplification pass on the review-channel implementation itself: collapse
      follow/projection/attach-auth/command satellites into the smallest
      readable module set that preserves the typed contract, and remove event /
      CQRS-style indirection that does not buy present operational value for
      the current two-agent shared-work problem.

Acceptance:

1. One posted packet can be rendered consistently as JSON, markdown, trace
   stream, actions view, and terminal-packet projection.
2. `devctl review-channel --action inbox --target codex` returns only targeted
   pending packets with deterministic status fields.
3. `check_review_channel.py` passes on a valid bundle and fails on schema drift,
   stale pending packets, or projection mismatch.

Expected Phase-1 tests:

1. `python3 -m unittest dev.scripts.devctl.tests.test_review_channel`
2. `python3 -m unittest dev.scripts.devctl.tests.test_check_review_channel`

### Phase 2 - Read-First Shared Screen

- [ ] Start with the existing Rust Dev-panel / overlay path instead of changing
      the default startup mode. Expected touchpoints:
      `rust/src/bin/voiceterm/dev_panel.rs`,
      `rust/src/bin/voiceterm/overlays.rs`,
      `rust/src/bin/voiceterm/event_state.rs`,
      `rust/src/bin/voiceterm/event_loop/periodic_tasks.rs`,
      `rust/src/bin/voiceterm/event_loop/dev_panel_commands.rs`,
      and related `event_loop/tests.rs` coverage.
- [ ] Show at least three visible lanes: `Codex`, `Claude`, and
      `Operator Bridge State`.
- [ ] Add a compact all-agents job board that stays visible above or alongside
      the main lanes and shows every active agent, assigned job, current state,
      waiting-on target, and freshness/heartbeat state.
- [ ] Use the main visual hierarchy shown above: shared goal/status strip,
      Claude lane, relay spine, Codex lane, then shared process timeline.
- [ ] Keep the screen sourced from the canonical review/controller artifacts
      rather than bespoke overlay-only state.
- [ ] Render both a parsed review state and a raw artifact view:
  - [ ] parsed current verdict/findings/instruction/ack/poll state
  - [ ] raw `bridge.md` / projection markdown view while the bridge is the
        sanctioned temporary operator surface
- [ ] Add polling-based refresh behavior that does not interfere with the
      standard VoiceTerm overlay lifecycle.
- [ ] Add a toast notification when a new review packet arrives during normal
      voice mode.
- [ ] Make the user-facing review surface read as one collaborative
      terminal-native workspace even while Codex and Claude remain separate
      PTY/session owners under the hood.
- [ ] Keep per-agent PTY/session ownership separate in this phase.
- [ ] Show peer-awareness cues in the shared screen:
  - [ ] last packet received / last packet applied
  - [ ] current task or draft intent
  - [ ] current writer/target status for any staged terminal action
  - [ ] shared-goal header and current-slice summary
  - [ ] bottom-of-screen workflow timeline
- [ ] Make agent/job details adjustable from the surface through typed controls
      that call repo-owned scripts and command handlers rather than bespoke UI
      business logic:
  - [ ] update assigned job / priority
  - [ ] pause or resume an agent
  - [ ] request re-review or reroute a packet
  - [ ] trigger launch / rollover / checks through existing `devctl` surfaces
- [ ] Define empty-state rendering and keyboard navigation exactly as specified
      above.
- [ ] Add bounded operator edit/generate affordances inside the review surface:
  - [ ] rewrite current instruction
  - [ ] promote next scoped slice
  - [ ] append operator note / request re-review
  - [ ] generate fresh-conversation prompts / resume bundle
  - [ ] preview staged `terminal_packet` output without blind auto-send
- [ ] If a dedicated monitor selector is needed, coordinate with MP-336 instead
      of introducing an MP-355-only startup flag.

Acceptance:

1. The user can watch both agent lanes and the current review queue on one
   VoiceTerm screen.
2. The shared screen is read-first and does not degrade the normal voice
   overlay path.
3. The same state is visible through both `devctl` and the Rust review surface.
4. The operator can tell, from one screen, what each agent knows about the
   other agent's latest work without opening a separate coordination tool.
5. The operator can inspect and adjust agent jobs from that same screen, but
   every adjustment is traceable to a typed command or typed artifact update.

Expected Phase-2 tests:

1. `cd rust && cargo test --bin voiceterm dev_panel`
2. `cd rust && cargo test --bin voiceterm periodic_tasks`
3. `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel`

### Phase 3 - Routed Review + Guarded Handoffs

- [ ] Add per-target inbox filtering so packets can be routed to `codex`,
      `claude`, or `operator`.
- [ ] Replace the fixed provider-shaped queue/current-session state with a
      registry-driven topology: pending counts, heartbeat freshness, ACK
      state, and lane ownership must derive from `TandemProfile` / the agent
      registry instead of `pending_codex`, `pending_claude`, `claude_ack`,
      and `codex_poll_state` remaining first-class runtime fields forever.
      Keep compatibility projections while current consumers migrate.
- [ ] Add explicit `acked|dismissed|applied|expired` transitions and
      stale-packet watch behavior.
- [ ] Add policy-aware action hints so packets can express `review_only`,
      `stage_draft`, `operator_approval_required`, or `safe_auto_apply`.
- [ ] Route any `requested_action` through the same typed action catalog used by
      overlay buttons and controller surfaces; review packets must not invent a
      parallel raw-command bypass.
- [ ] Allow packets to carry high-level intents (`push`, `run checks`,
      `dispatch workflow`, `generate handoff`) that the planner resolves to a
      concrete approved playbook, but only within the shared typed action
      catalog.
- [ ] Keep Git/GitHub/CI/script/memory requests typed and catalog-backed
      (`git_push`, `gh_run_view`, `memory_export_pack`, etc.) rather than
      arbitrary shell or arbitrary HTTP/API text emitted by an agent.
- [ ] When a packet asks for a blocked or approval-gated action, surface the
      full warning/precondition bundle back into the review lane so Claude,
      Codex, and the operator can all see why the action stopped.
- [ ] Add explicit operator-override/waiver recording for action requests whose
      policy contract permits a bounded override; the waiver must stay visible
      in packet history and audit refs.
- [ ] `Unsafe Direct` remains operator-owned only: packets may request it or
      explain why guarded mode is inconvenient, but they may not silently
      switch execution profile or bypass the shared policy engine.
- [ ] Reuse existing audit/event logging so every review-channel action is
      traceable in `devctl_events.jsonl`.
- [ ] Add review-channel status/watch outputs that integrate with orchestration
      status surfaces. (`2026-03-09` partial: `review-channel --action status`
      now writes bridge-backed latest projections under
      `dev/reports/review_channel/latest/`; event-backed rebuild semantics plus
      `watch|inbox|ack|dismiss|apply|history` remain open. A later same-day
      launcher follow-up also writes per-session metadata + live transcript
      logs under `dev/reports/review_channel/latest/sessions/` so desktop
      read-only consumers can tail real conductor output without taking PTY
      ownership away from Terminal.app.)
- [ ] Add optional additive read-only MCP exposure for review snapshots only
      after the `devctl` contract is stable; any write-capable MCP surface
      requires an explicit policy change outside this phase.
- [ ] If read-only MCP exposure lands, wire it through the existing
      `devctl mcp` extension path: allowlist entry, `test_mcp.py` coverage, and
      docs updates in `dev/scripts/README.md` + `dev/guides/DEVCTL_AUTOGUIDE.md`.
- [ ] Add `trace_id` linking across review packets, acknowledgements, staged
      PTY drafts, and resulting actions.
- [ ] Add `devctl memory` / `devctl review-channel` interop:
      `review-channel --action post` may attach a selected memory pack by ref,
      and `devctl memory` should support queries by `packet_id`, `trace_id`, or
      task ref without requiring raw event-id discovery.
- [ ] Feed review outcomes back into memory usefulness telemetry with explicit
      reason-coded mappings (`applied -> accepted`, `dismissed -> ignored|wrong`,
      `acked-without-apply -> neutral`) instead of leaving review resolution
      disconnected from retrieval quality learning.
- [ ] Route cross-provider handoffs through Memory Studio adapter profiles so
      packets sent from Claude to Codex (or later Gemini) attach the
      receiver-shaped pack projection while the canonical JSON pack stays
      unchanged.
- [ ] Add conflict-resolution UX for competing agent recommendations.
- [ ] Generalize agent validation and attention ownership from hardcoded
      provider names to profile/policy-driven ids and roles: `VALID_AGENT_IDS`,
      `ATTENTION_OWNER_ROLE`, rollover rules, and stale-peer attention should
      stop assuming only Codex/Claude/Operator lanes once the typed
      current-session path is ready.
- [ ] Generalize promotion from one unchecked item -> one `Current Instruction
      For Claude` rewrite into multi-item typed packet routing. Native N-agent
      review should be able to promote distinct scoped items to different
      target agents while bridge markdown becomes a projection over packet /
      current-session authority rather than the only live routing surface.
- [ ] Add typed agent-board actions so the operator can retask or tune agents
      from the shared surface without bypassing script/policy ownership:
  - [ ] `assign`
  - [ ] `reprioritize`
  - [ ] `pause-agent`
  - [ ] `resume-agent`
  - [ ] `request-rereview`
  - [ ] `launch`
  - [ ] `rollover`
- [ ] Keep those actions as thin wrappers around repo-owned `devctl` handlers
      and typed registry updates; the review surface may render and invoke them,
      but it must not become an unscripted orchestration engine.

Acceptance:

1. One agent can watch/review another agent through the review channel with
   explicit packet state transitions.
2. Guarded PTY staging is possible without silent auto-injection.
3. Operator-visible audit output can reconstruct who sent, acknowledged, and
   applied each packet.
4. The user can understand the full agent roster, current jobs, and operator
   changes from one screen without losing typed-command/audit ownership.

### Phase 4 - Deferred Shared Target Session

- [ ] Design a shared target session mode with explicit writer lease/lock
      semantics.
- [ ] Require one active writer at a time for any shared live terminal target.
- [ ] Require ack/apply semantics before cross-agent injection into a shared
      target session.
- [ ] Add collision handling, timeout recovery, and full audit evidence for
      lease transitions.
- [ ] Preserve the same single collaborative surface when lease-based shared
      writing lands so the operator does not have to switch to a second
      debugging-only UI to understand who is talking to whom.
- [ ] Gate promotion of this phase on successful soak evidence from Phases 1-3.

Acceptance:

1. Shared-target-session mode never allows ambiguous simultaneous writers.
2. The user can see which agent currently owns write authority.
3. Every shared-session write is attributable and reversible at the workflow
   level.
4. Shared-write mode still reads as one collaborative terminal experience
   instead of exposing raw lease mechanics without context.

### Out Of Scope Until Later Phases

- [ ] Full desktop GUI client resurrection.
- [ ] Free-form concurrent writes from Codex and Claude into one live target
      terminal.
- [ ] Any release/tag/publish actions routed through the review channel without
      separate controller-policy hardening.

## 0) Current Execution Mode

This merged section replaces the retired standalone multi-agent worktree
runbook for the current markdown-swarm cycle.

Coordination contract:

1. `dev/active/review_channel.md` is the canonical static swarm plan: lane
   ownership, worktree/branch map, signoff template, and governance policy live
   here.
2. `bridge.md` is the only live cross-team coordination surface during the
   active 8+8 run. Codex lanes post findings, poll summaries, and next actions
   there; Claude lanes read it, acknowledge it, and code against it.
3. `dev/active/MASTER_PLAN.md` remains the execution tracker for lane status.
4. `AGENT-1..AGENT-8` are the Codex reviewer/auditor swarm.
5. `AGENT-9..AGENT-16` are the Claude coding/fix swarm.
6. When no fresh diff is ready for review, the Codex integration lane polls
   every 5 minutes, reports status in chat, and resumes review as soon as
   Claude work advances.

Bootstrap workflow for the current live cycle:

1. Dry-run the bridge-gated launcher first:

   ```bash
   python3 dev/scripts/devctl.py review-channel \
     --action launch \
     --terminal none \
     --dry-run \
     --format md
   ```

2. When the dry-run output looks correct, open the two conductor sessions:

   ```bash
   python3 dev/scripts/devctl.py review-channel \
     --action launch \
     --format md
   ```

3. The launched Codex conductor owns the `AGENT-1..AGENT-8` reviewer lanes and
   Claude owns the `AGENT-9..AGENT-16` coding lanes. The conductors may fan out
   specialist workers internally, but only the conductors update `bridge.md`.
   Missing listed worktrees are not permission to improvise live-repo fallback
   workers; if a lane worktree is unavailable, stay conductor-only for that
   lane until the repo-owned worktree contract is repaired.
4. Terminal.app launch defaults to the `auto-dark` profile selector on macOS so
   the conductor windows come up on a dark profile when a known one is
   available. Use `--terminal-profile default` only when you explicitly want to
   keep Terminal.app unchanged.
5. Before either conductor hits compaction, the active threshold is 20%
   remaining context. At or below that line, the current conductor finishes the
   atomic step, updates its owned `bridge.md` sections, and triggers:

   ```bash
   python3 dev/scripts/devctl.py review-channel \
     --action rollover \
     --rollover-threshold-pct 20 \
     --await-ack-seconds 180 \
     --format md
   ```

6. `--action rollover` writes a repo-visible handoff bundle under
   `dev/reports/review_channel/rollovers/`, relaunches fresh Codex/Claude
   conductor sessions, and requires the new sessions to write exact rollover
   ACK lines into `bridge.md` before the retiring session exits.

| Agent | Lane | Primary active docs | MP scope | Worktree | Branch |
|---|---|---|---|---|---|
| `AGENT-1` | Codex architecture contract review | `dev/active/review_channel.md`, `dev/active/autonomous_control_plane.md` | `MP-340, MP-355` | `../codex-voice-wt-a1` | `feature/a1-codex-architecture-review` |
| `AGENT-2` | Codex clean-code and state-boundary review | `dev/active/review_channel.md` + runtime pack | `MP-267, MP-340, MP-355` | `../codex-voice-wt-a2` | `feature/a2-codex-clean-code-review` |
| `AGENT-3` | Codex runtime and handoff review | `dev/active/review_channel.md`, `dev/active/memory_studio.md` + runtime pack | `MP-233, MP-238, MP-243, MP-340, MP-355` | `../codex-voice-wt-a3` | `feature/a3-codex-runtime-handoff-review` |
| `AGENT-4` | Codex CI and workflow reviewer | `dev/active/review_channel.md` + tooling pack | `MP-297, MP-298, MP-303, MP-306, MP-355` | `../codex-voice-wt-a4` | `feature/a4-codex-ci-workflow-review` |
| `AGENT-5` | Codex devctl and process-hygiene reviewer | `dev/active/devctl_reporting_upgrade.md`, `dev/active/host_process_hygiene.md` | `MP-297, MP-298, MP-300, MP-303, MP-306, MP-356` | `../codex-voice-wt-a5` | `feature/a5-codex-devctl-process-review` |
| `AGENT-6` | Codex overlay and UX reviewer | `dev/active/review_channel.md`, `dev/active/autonomous_control_plane.md` + runtime pack | `MP-340, MP-355` | `../codex-voice-wt-a6` | `feature/a6-codex-overlay-ux-review` |
| `AGENT-7` | Codex guard and test reviewer | `dev/active/review_channel.md`, `dev/active/host_process_hygiene.md` + tooling pack | `MP-303, MP-355, MP-356` | `../codex-voice-wt-a7` | `feature/a7-codex-guard-review` |
| `AGENT-8` | Codex integration and re-review loop | `dev/active/MASTER_PLAN.md`, `dev/active/review_channel.md` | `MP-340, MP-355, MP-356` | `../codex-voice-wt-a8` | `feature/a8-codex-integration-review` |
| `AGENT-9` | Claude bridge push-safety fixes | `dev/active/review_channel.md` + tooling pack | `MP-303, MP-306, MP-355` | `../codex-voice-wt-a9` | `feature/a9-claude-bridge-push-safety` |
| `AGENT-10` | Claude live Git-context fixes | `dev/active/review_channel.md`, `dev/active/autonomous_control_plane.md` + runtime pack | `MP-340, MP-355` | `../codex-voice-wt-a10` | `feature/a10-claude-git-context-fixes` |
| `AGENT-11` | Claude refresh, redraw, and footer fixes | `dev/active/review_channel.md` + runtime pack | `MP-340, MP-355` | `../codex-voice-wt-a11` | `feature/a11-claude-refresh-redraw-fixes` |
| `AGENT-12` | Claude broker and clipboard fixes | `dev/active/review_channel.md`, `dev/active/autonomous_control_plane.md` + runtime pack | `MP-340, MP-355` | `../codex-voice-wt-a12` | `feature/a12-claude-broker-clipboard-fixes` |
| `AGENT-13` | Claude handoff and bootstrap fixes | `dev/active/review_channel.md`, `dev/active/memory_studio.md` + runtime pack | `MP-233, MP-238, MP-243, MP-340, MP-355` | `../codex-voice-wt-a13` | `feature/a13-claude-handoff-bootstrap-fixes` |
| `AGENT-14` | Claude workflow and publication-sync fixes | `dev/active/devctl_reporting_upgrade.md` + tooling pack | `MP-297, MP-298, MP-300, MP-303, MP-306` | `../codex-voice-wt-a14` | `feature/a14-claude-workflow-publication-fixes` |
| `AGENT-15` | Claude clean-code refactors | `dev/active/naming_api_cohesion.md`, `dev/active/review_channel.md` + runtime/tooling packs | `MP-267, MP-340, MP-355` | `../codex-voice-wt-a15` | `feature/a15-claude-clean-code-refactors` |
| `AGENT-16` | Claude proof and regression closure | `dev/active/review_channel.md`, `dev/active/host_process_hygiene.md` + runtime/tooling packs | `MP-303, MP-340, MP-355, MP-356` | `../codex-voice-wt-a16` | `feature/a16-claude-proof-regression-closure` |

## 14) Orchestrator Instruction Log (Append-Only)

All orchestrator-to-agent instructions must be logged here for governance, but
the live reviewer/coder chatter and five-minute poll loop stay in
`bridge.md`.

| UTC issued | Instruction ID | From | To | Summary | Due (UTC) | Ack token | Ack UTC | Status |
|---|---|---|---|---|---|---|---|---|

## 15) Shared Ledger (Append-Only)

This ledger is the durable merge/readiness record for the swarm. Dynamic
finding churn still belongs in `bridge.md`.

| UTC | Actor | Area | Worktree | Branch | Commit | MP scope | Verification summary | Status | Reviewer token | Next action |
|---|---|---|---|---|---|---|---|---|---|---|

## 16) End-of-Cycle Signoff (Required)

Complete this table only after all active swarm lanes are merged.

| Signer | Date (UTC) | Result | Isolation verified | Bundle reference | Signature |
|---|---|---|---|---|---|
| `AGENT-1` | `pending` | `pending` | `pending` | `pending` | `pending` |
| `AGENT-2` | `pending` | `pending` | `pending` | `pending` | `pending` |
| `AGENT-3` | `pending` | `pending` | `pending` | `pending` | `pending` |
| `AGENT-4` | `pending` | `pending` | `pending` | `pending` | `pending` |
| `AGENT-5` | `pending` | `pending` | `pending` | `pending` | `pending` |
| `AGENT-6` | `pending` | `pending` | `pending` | `pending` | `pending` |
| `AGENT-7` | `pending` | `pending` | `pending` | `pending` | `pending` |
| `AGENT-8` | `pending` | `pending` | `pending` | `pending` | `pending` |
| `AGENT-9` | `pending` | `pending` | `pending` | `pending` | `pending` |
| `AGENT-10` | `pending` | `pending` | `pending` | `pending` | `pending` |
| `AGENT-11` | `pending` | `pending` | `pending` | `pending` | `pending` |
| `AGENT-12` | `pending` | `pending` | `pending` | `pending` | `pending` |
| `AGENT-13` | `pending` | `pending` | `pending` | `pending` | `pending` |
| `AGENT-14` | `pending` | `pending` | `pending` | `pending` | `pending` |
| `AGENT-15` | `pending` | `pending` | `pending` | `pending` | `pending` |
| `AGENT-16` | `pending` | `pending` | `pending` | `pending` | `pending` |
| `ORCHESTRATOR` | `pending` | `pending` | `pending` | `pending` | `pending` |

## Progress Log

| UTC | Actor | Action | Result | Next step |
|---|---|---|---|---|
| `2026-03-26T11:45:00Z` | `CODEX` | Audited the live tandem regression after Claude fell back to low-value polling/no-op wait behavior. The repo already had partial anti-stall teaching, but the contract was split across prompt surfaces and did not fail closed on two live shapes: active work plus `No change. Continuing.`-style implementer parking, and `active_dual_agent` with detached publisher/supervisor heartbeats but no repo-owned conductors. Closed that gap by sharing stall markers across review-channel runtime/checks, tightening bridge + generated `CLAUDE.md` + conductor prompt wording, hard-failing bridge validation on no-op implementer parking under active work, and making `status` surface the no-conductor state as a bridge-contract error instead of healthy loop freshness. Updated maintainer docs in the same slice so the repo teaches the same contract it now enforces. | `partial-pass` | Keep verifying live Claude deltas against code/docs, but now treat any future no-op polling or detached-daemon-only dual-agent state as contract errors to repair before trusting the loop. |
| `2026-03-26T08:10:00Z` | `CODEX` | Restored the live architecture-audit operating mode after an interrupted session and an overly narrow reviewer instruction. Rewrote the reviewer-owned bridge/current-session instruction through the repo-owned `reviewer-checkpoint` path so Claude is again the primary broad whole-system finder, Codex stays the verifier/controller, and the shared audit ledger is `dev/audits/architecture_alignment.md` instead of a hidden chat state. Also verified that the typed `current_session` / push-decision split remains an MP-355 producer -> MP-377 consumer contract and promoted the missing dependency notes into this plan. | `partial-pass` | Keep reviewing Claude deltas against real code/docs, correct overbroad ledger claims before accepting them, and promote only verified findings into `MASTER_PLAN` plus the scoped owner plans. Do not reintroduce Codex-side broad audit swarms. |
| `2026-03-26T05:05:00Z` | `CODEX` | Re-audited the live bridge/current-session lane against the portable-platform architecture after the latest startup/tandem bug fixes. The design direction remains correct: typed `review_state` is the live authority and `bridge.md` is already supposed to become a repo-pack-owned compatibility projection. The concrete remaining gap is mixed teaching and mixed consumers: some runtime/guard paths now resolve bridge/review state through governance, while prompts, templates, and a few guards still encode repo-root `bridge.md` or VoiceTerm plan-path assumptions directly. | `planned` | Keep the typed `current_session` cutover bounded, then remove literal bridge/path assumptions from prompts/guards/projections and add non-VoiceTerm fixture coverage before claiming the bridge path is portable. |
| `2026-03-26T01:50:00Z` | `CODEX` | Closed the worst current markdown-bridge failure mode after the live bridge grew into a 4164-line mixed transcript with duplicate report headings and raw terminal/test output. Landed `review-channel --action render-bridge` as the repo-owned repair path, rebuilt the live `bridge.md` down to a bounded 117-line compatibility projection, expanded bridge hygiene enforcement so `check_review_channel_bridge.py` now rejects oversize bridges, duplicate/unsupported headings, transcript/ANSI contamination, and overgrown live sections, and tightened reviewer checkpoint contamination patterns so repo-owned reviewer writes reject obvious terminal/test output earlier. | `partial-pass` | Re-run the focused review-channel/tooling bundles on the cleaned bridge, keep the remaining stale-ACK state explicit, and continue the broader typed writer/mutation cutover so bridge repair becomes exceptional instead of routine. |
| `2026-03-25T14:05:00Z` | `CODEX` | Closed the next live stale-implementer orchestration gap without widening bridge authority. Active attention now distinguishes `implementer_relaunch_required`, `review-channel --action recover --recover-provider claude` replaces only the stale Claude conductor, and reviewer-follow now escalates repeated unchanged stale-implementer state through that narrower repo-owned recovery path instead of full rollover or passive sleep-loop polling. The same slice also keeps startup gating honest: `launch|rollover` still fail closed on checkpoint-budget or real startup-authority errors, but they no longer fail solely because the reviewer loop is stale on the implementer side. | `partial-pass` | Run the focused runtime/review-channel proofs plus docs/guard bundles, then checkpoint the slice and exercise the live recover path against a stale Claude ACK session. |
| `2026-03-25T04:45:00Z` | `CODEX` | Re-ran the focused MP-355 regression suite and reopened one exact bridge-contract guard. `test_check_review_channel_bridge.py` now shows that `check_review_channel_bridge.py` no longer flags resolved bridge verdicts without a promoted next task. The broader typed-current-session direction still holds, but the temporary fail-closed bridge validator regressed and can again let a semantically incomplete bridge read as healthy. | `planned` | Restore guard + projection parity so resolved/fixed bridge states require promoted next-task routing, then continue the typed `current_session` / `agent_registry` cutover without widening bridge authority. |
| `2026-03-24T16:30:00Z` | `CODEX` | Folded the remaining aligned review-channel intake into canonical MP-355 state after re-checking it against live code. The correction is explicit: queue/attention are not wholly unread because current-focus and wait surfaces already use them; the actual missing consumer path is `agent_registry` plus wider typed review status not yet steering startup/work-intake routing or reviewer/implementer scheduling. | `planned` | Keep the typed current-session cutover bounded, then make startup/work-intake and scheduling consume `agent_registry` plus typed queue/attention state before claiming the review channel is a live routing surface rather than a display bundle. |
| `2026-03-22T18:10:00Z` | `CODEX` | Finished the remaining `SYSTEM_AUDIT` mapping for the MP-355 lane. The previously unmapped structural-debt/test tranche is now explicit in canonical plan state: the review-channel family must keep collapsing toward a smaller stable core and `test_review_channel.py` must split into feature-scoped suites before MP-355 can claim maintainability closure. | `planned` | Keep the current-session/push-safe authority work bounded, then land the maintainability tranche in the same Phase-1 closure path instead of deferring it to another audit note. |
| `2026-03-22T04:45:00Z` | `CODEX` | Landed the reviewer-side parity slice for the planned repo-owned wait path. `review-channel --action reviewer-wait` now exports typed wait attention fields plus state-specific timeout/unhealthy/update messages, markdown wait rendering handles reviewer-wait payloads instead of only implementer-wait, and the reviewer launch prompt now explicitly tells Codex to use `reviewer-wait` instead of ad-hoc sleep loops when parking on Claude-owned progress. This closes the immediate "stay watching Claude through repo-owned wait semantics" step without pretending semantic review is fully automated yet. | `partial-pass` | Keep the broader reviewer-worker/service blocker open: the next loop-hardening slice still needs repo-owned semantic re-review/checkpoint behavior instead of chat-prompted polling. |
| `2026-03-22T04:15:00Z` | `CODEX` | Closed the next live-loop messaging gap after typed attention was already correct but the implementer-facing wait surface still printed generic "Holding for Codex review" text. `review-channel --action implementer-wait` now carries typed attention status/summary/recommended-action fields in its stable report, timeout/reviewer-update messages specialize for `review_follow_up_required` and `claude_ack_stale`, and the markdown wait projection renders the same attention context instead of a bare stop reason. Focused review-channel proof is green (`232` tests); full `devctl check --profile ci` is only waiting on the normal reviewer checkpoint hash refresh for the current tree. | `partial-pass` | Keep the checkpoint-gate pause projection follow-up open, then continue parity so every live wait surface exposes the same typed reason without making operators infer state from generic hold text. |
| `2026-03-22T03:35:00Z` | `CODEX` | Closed the next bounded live-loop clarity gap after the reviewer bridge kept looking "done" whenever Claude changed the tree between polls. Active-dual-agent attention and implementer bridge-poll state now emit `review_follow_up_required` when `review_needed=true`, the reviewer supervisor is alive, and `reviewed_hash_current=false`; bridge-poll next-turn routing now points back to the reviewer explicitly instead of collapsing that state into generic stale/done-looking output. Focused review-channel proof is green (`231` tests) and `devctl check --profile ci` is green on the current local diff. | `partial-pass` | Keep the broader checkpoint-gate pause work open, then continue the remaining projection parity so the same typed wait/follow-up reasons stay aligned across `status`, `latest.md`, `review_state.json`, and bridge compatibility text. |
| `2026-03-22T01:57:00Z` | `CODEX` | Promoted the live reviewer/implementer communication stall into tracked MP-355 state after the current dual-agent loop kept presenting a continuation-budget pause as generic `waiting_on_peer`. Runtime truth already raises `attention.status=checkpoint_required` with `safe_to_continue_editing=false`, but the bridge/liveness layer still makes Claude look like it is merely waiting on the peer instead of paused on a typed checkpoint gate. | `planned` | Land one bounded MP-355 follow-up that elevates checkpoint-gate/continuation-budget pause to a first-class typed wait reason across `review-channel status`, `latest.md`, `review_state.json`, and bridge projections so Codex/Claude can keep synchronized communication while edits are intentionally paused. |
| `2026-03-22T01:20:00Z` | `CODEX` | Closed the repeated shell-mangling failure mode on reviewer checkpoints by adding one typed file-backed payload path to the repo-owned writer. `review-channel --action reviewer-checkpoint` now accepts `--checkpoint-payload-file` with `verdict`, `open_findings`, `instruction`, and `reviewed_scope_items`, the CLI/docs now prefer that path (or the existing per-section `--*-file` flags) over inline shell bodies for AI-generated markdown, and the maintained examples now also carry the live `--expected-instruction-revision` required for active dual-agent stale-write safety. | `partial-pass` | Keep future reviewer/controller writes on typed/file-backed payloads, then continue the broader writer/mutation cutover so bridge compatibility text stops sitting in the middle of machine authority. |
| `2026-03-22T00:25:00Z` | `CODEX` | Reconfirmed the live reviewer-service/operator-notification gap against repo-owned runtime truth instead of chat impressions. In the current lane the reviewer supervisor stays alive and updates `review_needed` / `waiting_on_peer`, but publisher state can still sit at `detached_exit`, so bridge/runtime status knows Claude is stale or waiting without auto-surfacing that state to the operator. | `planned` | Treat sticky reviewer ownership plus live publisher/notification delivery as the same MP-355 blocker: the repo-owned reviewer worker/supervisor must poll, write checkpoints, and emit operator-visible updates without waiting for user prompts. |
| `2026-03-21T23:59:00Z` | `CODEX` | Reconciled the latest cross-agent audit against live MP-355 plan state. The urgent push-safe bridge issue was already tracked, but two real review-channel follow-ups were still missing from the checklist: a typed bridge-section registry to kill magic-string section parsing/writes and an explicit maintainability burn-down item for the remaining review-channel Python hotspots instead of treating the current file sizes as invisible debt. | `planned` | Keep the current-session/push-safe authority work bounded, then land the bridge-section registry and continue shrinking the review-channel hotspots without widening bridge authority again. |
| `2026-03-21T23:55:00Z` | `CODEX` | Recorded the newly-proved push-coupling bug after the typed `current_session` cutover. The read side is now healthier: current reviewer/implementer truth comes from typed review-state projections, but the guarded push path still blocks on raw tracked-file dirtiness, so live `bridge.md` compatibility writes can strand validated committed work even though push logic never actually consumes bridge prose. | `planned` | Keep `bridge.md` as a compatibility projection only, add the push-safe policy/preflight closure in `MP-377`, and do not let write/push paths keep treating bridge dirtiness as canonical authored state once typed current-session authority exists. |
| `2026-03-21T23:40:00Z` | `CODEX` | Landed the first typed `current_session` authority cutover for MP-355 without widening into the full bridge replacement. `ReviewState` now carries a dedicated current-session block, both bridge-backed and event-backed projections populate it, `latest.md` / `compact.json` read it for live current-focus rendering, and the legacy bridge fields are still projected for compatibility. This keeps current-status readers off append-only bridge prose while preserving the existing runtime/reporting surfaces. | `partial-pass` | Finish the broader guard bundle for this slice, keep `bridge.md` out of the checkpoint, and then continue the remaining bridge-authority replacement through writer/mutation paths instead of re-expanding current-status reads. |
| `2026-03-21T22:15:00Z` | `CODEX` | Re-ran the "is this already N-agent?" audit against the current MP-355 runtime instead of relying on older scratch conclusions. The answer is mixed: packet routing, `TandemProfile.implementers`, the event lane, and `autonomy-swarm` already support more than two workers, but the middle review-channel layer is still singular in the places that matter most for live authority (`pending_codex` / `pending_claude`, `claude_ack`, `codex_poll_state`, provider-name allowlists, and one `Current Instruction For Claude` promotion path). | `planned` | Keep the current 8+8 run conductor-managed for now, then generalize queue/current-session/attention/promotion to registry-driven N-agent state before claiming the backend itself is natively multi-agent. |
| `2026-03-21T20:25:00Z` | `CODEX` | Landed the first stale-write containment on the live markdown bridge after the operator-visible regression where an older reviewer checkpoint replaced a newer in-flight instruction. Instruction-mutating bridge writes now carry an expected instruction revision precondition through the reviewer-checkpoint and promotion paths, and the write fails closed under the existing file lock if the live bridge revision no longer matches. Auto-promotion/scope paths now thread the live revision they validated, while active dual-agent reviewer checkpoints require an explicit expected revision instead of silently overwriting newer state. | `partial-pass` | Keep the bounded `UNKNOWN/DEFER` slice in place, then land the typed `current_session` authority cutover so current-status readers stop depending on append-only bridge prose for live instruction/ACK truth. |
| `2026-03-21T16:35:00Z` | `CODEX` | Promoted the bridge-read authority cleanup into the active MP-355 lane after another operator-visible confusion round. The immediate bounded fix is to make one typed `current_session` block authoritative in `review_state.json`, render `latest.md` from that typed state instead of append-only `Claude Ack` prose, and keep history in trace/event surfaces instead of mixing it into current-status reads. This is the smallest same-repo slice that moves toward `CollaborationSession` authority without colliding with the current `context_graph` work. | `planned` | Land the typed `current_session` projection on both bridge-backed and event-backed review-state paths, switch `latest.md` / compact readers to that block, and keep append-only bridge/event history explicitly out of live current-status rendering before widening into full writer-authority replacement. |
| `2026-03-21T15:50:00Z` | `CODEX` | Captured the round-duration operating constraint for the live dual-agent loop. Bounded rounds and restartable handoff state are already the architectural direction, but the plan now also treats roughly 30 minutes as the target fresh-session budget for reviewer/coder rounds so the controller prefers explicit rollover/restart over long-lived drifting sessions. | `planned` | Encode a concrete max-round-duration / rollover budget into the controller contract and keep handoff state rich enough that restarting is cheaper than letting one session go stale. |
| `2026-03-21T21:35:00Z` | `CODEX` | Promoted the missing controller/handoff follow-up from discussion into tracked MP-355 state. The current bridge loop still polls passively even after the `runtime_missing` containment fix; the next reliability slice must switch to bounded rounds with fresh re-prompts, ACK deadlines, explicit no-progress circuit breaking, and rollover/session-restart behavior that uses repo-visible handoff state instead of hoping two long-lived sessions keep polling forever. The same follow-up must also enrich rollover/handoff bundles with the bounded context packet so fresh conductor sessions restart informed instead of blind. | `planned` | Land the round-based controller contract in the backend, keep `bridge.md` generated/truthful, and thread the same generated context packet into handoff bundles and restart prompts before widening into UI-only conveniences. |
| `2026-03-21T18:40:00Z` | `CODEX` | Accepted the next bounded context-graph follow-up for MP-355 after the first conductor-path injection landed. The remaining high-value backend gaps are now explicit: repo-owned next-task promotion still emits plain text, event-backed `derived_next_instruction` is still summary-only, and the fresh `swarm_run` prompt path still starts blind. | `planned` | Keep the packet generated from the canonical graph, then widen it through promotion/event/startup prompt emitters with parity tests instead of inventing UI-local or chat-local context side channels. |
| `2026-03-21T16:10:00Z` | `CODEX` | Landed the first bounded context-escalation policy for the live conductor path. `build_conductor_prompt()` now teaches the `context-graph --query` trigger rules explicitly (unread file/subsystem scope, repeated failed attempts, unclear blast radius) and preloads one small context packet for the active lane scopes instead of forcing either full cold-doc reads or blind guessing. | `partial-pass` | Keep the prompt policy bounded and honest, then reuse the same typed packet shape in other agent-control surfaces so context recovery is one reusable repo-owned behavior instead of prompt-by-prompt prose drift. |
| `2026-03-21T13:25:00Z` | `CODEX` | Closed the stale-runtime authority bug in the live dual-agent loop. `review-channel status` was auto-demoting abandoned runtime state to `paused`, which suppressed pending review work even when Claude had already ACKed the live instruction and the tree had changed. The accepted containment path removes daemon-driven mode mutation, reports `runtime_missing` instead, and records the daemon boundary explicitly: publisher/supervisor processes publish runtime health only and must not change collaboration mode authority. | `partial-pass` | Keep the immediate containment green in tests/guards, then move the broader runtime/event-store reducer toward a single typed session authority so `bridge.md` can become a generated view instead of live state. The next daemon/controller slice should also switch from passive bridge polling to bounded round control: fresh agent invocations, ACK deadlines, and no-progress circuit breakers. |
| `2026-03-20T06:20:00Z` | `CODEX` | Closed the next MP-355 packet-consumption gap in the live dual-agent loop. The event-backed Claude inbox proved real but unconsumed, so the repo-owned implementer wait path now includes the newest pending Claude-targeted packet in its wake token, and the shared Claude prompt contract now requires polling `inbox/watch` alongside bridge state on the same cadence. This keeps reviewer packets in the canonical reducer/projection path instead of relying on bridge-only coordination or operator chat relay. | `partial-pass` | Keep the direct packet lane honest in live use, then decide whether the next bounded follow-up is default-inbox view cleanup or a stricter Claude-side conductor bootstrap that proves packet polling is part of the normal repoll loop. |
| `2026-03-19T22:15:00Z` | `CODEX` | Final architecture review reconciled the validated runtime slice with the broader proposal set for MP-355. The accepted backend contract keeps `CollaborationSession` as the long-term bridge/state projection over intake + review state, preserves intake-backed writer authority for canonical plan/session mutation, and treats revision/state-hash checks as stale-read protection rather than a substitute for ownership. Startup auto behavior is also now constrained at the plan level: resume one valid session and auto-demote stale abandoned state, but do not auto-guess plan scope or auto-enter dual-agent mode. | `in-progress` | Land the remaining runtime/reducer fields and guards so stale-read rejection, bridge demotion, and projection parity are enforced by backend state rather than operator habit. |
| `2026-03-19T21:20:00Z` | `CODEX` | Captured the stale-bridge-validation issue as explicit MP-355 architecture work instead of leaving it as session trivia. The plan now requires repo-owned stale-bridge recovery so abandoned `bridge.md` heartbeats surface a typed `runtime_missing` / repair receipt without rewriting collaboration mode, rather than forcing manual bridge edits before unrelated docs/process validation can go green. | `in-progress` | Land that recovery path through the backend/guard surface so bridge freshness failures become self-healing or cleanly quarantined instead of recurring manual cleanup debt. |
| `2026-03-19T21:05:00Z` | `CODEX` | Ran the first proof pass against the new planning-review protocol and tightened the spec where it was still underspecified. Planning-review packets now require intake-backed writer authority, `anchor_refs` now use a fail-closed registry-id grammar instead of loose strings, `plan_patch_review` is explicitly a proposed typed mutation rather than the canonical edit itself, and the schema now carries `mutation_op` so cross-repo adopters cannot claim support while mutating plan targets incompatibly. | `in-progress` | Keep the runtime slice honest: the next implementation step must make reducer/validation code reject planning packets with missing leases, ambiguous anchors, or unsupported mutation ops before claiming cross-repo portability. |
| `2026-03-19T20:35:00Z` | `CODEX` | Extended MP-355 so the same review-channel transport can carry portable plan hardening instead of only code review. The schema/phase/protocol surfaces now reserve `plan_gap_review`, `plan_patch_review`, and `plan_ready_gate`, route plan targets through `PlanTargetRef` plus `WorkIntakePacket`, and state explicitly that mutable plan edits must bind to stable heading/checklist/progress anchors with target-revision checks rather than brittle surrounding-block matching. Canonical plan docs stay single-writer authority; packet/bridge state is proposal and coordination only. | `in-progress` | Prove the same packet path against the active `MP-377` plan loop, then land runtime resolution/guarding so planning review works on another repo without hard-coded VoiceTerm plan paths. |
| `2026-03-17T03:20:00Z` | `CODEX` | Accepted the bounded daemon-event to runtime-state reducer slice in the Python `devctl/review_channel` seam. `review-channel ensure --follow` and `reviewer-heartbeat --follow` now append `daemon_started` / `daemon_heartbeat` / `daemon_stopped` rows through a dedicated daemon-events helper, bridge-backed `status` now derives both `runtime.daemons.publisher` and `runtime.daemons.reviewer_supervisor` from persisted lifecycle heartbeat truth instead of hard-coding an empty supervisor, `latest.md` renders the same runtime block, and auto event-backed status stays gated on materialized `state.json` so daemon-only event logs do not silently flip authority. Focused proof is green (`145` review-channel tests, `check_code_shape.py`, `check_parameter_count.py`, `check_python_dict_schema.py`, `check_facade_wrappers.py`, `check_function_duplication.py`). | `partial-pass` | Treat daemon-event runtime truth plus markdown runtime visibility as the accepted same-scope baseline, then promote the next bounded follow-up to the VoiceTerm-local action-brokerage retirement / shared-backend attachment path unless a fresh runtime-truth regression appears. |
| `2026-03-17T02:14:01Z` | `CODEX` | Accepted the bounded post-`M69` service-identity plus attach/auth contract slice in the Python `devctl/review_channel` seam. Bridge-backed `status`, reviewer reports, `review_state.json`, `compact.json`, `full.json`, and `latest.md` now expose both repo/worktree-scoped `service_identity` and machine-readable `attach_auth_policy`, with caller-authority buckets sourced from the platform contract surface and the current backend policy fixed to repo/worktree-local attach over the filesystem markdown bridge (`off_lan_allowed=false`, `token_required=false`, `key_required=false`). Focused proof is green (`135` review-channel tests, `check_code_shape.py`, `check_parameter_count.py`, `check_python_dict_schema.py`, `check_facade_wrappers.py`, `check_review_channel_bridge.py`, `check_active_plan_sync.py`). Full `devctl check --profile ci` still lands only on the unrelated Rust failure `event_loop::tests::dev_panel_overlay::refresh_poll::memory_page_enter_refreshes_memory_cockpit_snapshot`. | `partial-pass` | Treat service identity/discovery and attach/auth semantics as accepted baselines on the current local diff, then promote the next bounded same-scope slice to the daemon-event to runtime-state reducer in the Python control-plane seam before widening into VoiceTerm-local action brokerage retirement or Rust/UI work. |
| `2026-03-17T01:30:39Z` | `CODEX` | Accepted the bounded detached-heartbeat truth fix inside `M69`. Lifecycle heartbeats now persist both the canonical shared file and a per-PID variant, and lifecycle reads select the freshest live publisher/supervisor writer before falling back to the freshest stopped/dead record so a dead shared-file writer no longer masks an active follow loop. Focused proof is green (`133` review-channel tests, `check_code_shape.py`, `check_parameter_count.py`, `check_facade_wrappers.py`, `check_review_channel_bridge.py`). Full `devctl check --profile ci` is back to the existing unrelated Rust failure `event_loop::tests::dev_panel_overlay::refresh_poll::memory_page_enter_refreshes_memory_cockpit_snapshot`. | `partial-pass` | Treat `M69` as closed on the current local diff and promote the next bounded same-scope slice to repo/worktree-scoped service identity/discovery in the Python control-plane seam before widening into attach/auth semantics, reducer work, or Rust/VoiceTerm ownership. |
| `2026-03-17T01:00:54Z` | `CODEX` | Re-reviewed the current `M69` local diff while Claude’s lifecycle/follow extraction was landing and found one new bounded regression in the extracted follow loops: `output_error` exits returned before they persisted final stopped publisher/supervisor heartbeat state. Fixed both follow paths, made lifecycle reads treat explicit `stop_reason` / `stopped_at_utc` records as not running even if the writer PID is still briefly alive, and added focused regression coverage for both publisher and reviewer-supervisor `output_error` exits. Current local proof is green (`129` review-channel tests, `check_code_shape.py`, `check_parameter_count.py`, `check_review_channel_bridge.py`, `check_active_plan_sync.py`). Full `devctl check --profile ci` is still blocked only by unrelated Rust tests (`banner::tests::logo_line_color_uses_single_theme_accent`, `event_loop::tests::dev_panel_overlay::refresh_poll::memory_page_enter_refreshes_memory_cockpit_snapshot`). | `partial-pass` | Keep `M69` active on detached reviewer-supervisor lifecycle/status truth, but treat the stop-state contract as part of the accepted baseline now; the next follow-up should widen only if a fresh detached-supervisor truth gap appears. |
| `2026-03-17T00:52:09Z` | `CODEX` | Closed the open medium reviewer-worker regression on the current MP-355 local diff. Bridge-backed `status` and `_build_reviewer_state_report()` now reuse `status_snapshot.reviewer_worker` instead of re-running `check_review_needed()`, and the follow/lifecycle seams were split into focused helper modules so `check_code_shape.py` stays green after the fix. Current focused proof is green (`127` review-channel tests, `docs-check --strict-tooling`, `check_review_channel_bridge.py`, `check_active_plan_sync.py`, `check_code_shape.py`). Full `devctl check --profile ci` now fails only on the unrelated Rust test `event_loop::tests::dev_panel_overlay::refresh_poll::memory_page_enter_refreshes_memory_cockpit_snapshot`. | `partial-pass` | Keep `M69` active on detached reviewer-supervisor lifecycle/status truth, but do not reopen the reviewer-worker duplicate-hash path unless a fresh regression appears. |
| `2026-03-17T00:06:42Z` | `CODEX` | Accepted the bounded `M68` report-only reviewer supervisor/watch slice. `reviewer-heartbeat --follow` now polls on cadence, refreshes reviewer heartbeat through the repo-owned Python `devctl/review_channel` seam, and emits operator-visible `reviewer_worker` frames without claiming semantic review completion. Current local re-review is green (`122` review-channel tests), and `check_review_channel_bridge.py` is green. | `partial-pass` | Promote the next bounded follow-up to `M69`: add repo-owned detached lifecycle/status truth for that supervisor path so it can stay alive and observable outside the current terminal/chat session before widening into semantic-review automation or Rust/VoiceTerm host ownership. |
| `2026-03-16T23:55:00Z` | `CODEX` | Accepted the bounded `M67` reviewer-worker status seam. The repo-owned Python `devctl/review_channel` backend now emits machine-readable `reviewer_worker` state from `review-channel status`, `ensure`, `reviewer-heartbeat`, `reviewer-checkpoint`, and the bridge-backed `full.json` projection, while `ensure --follow` cadence frames also surface `review_needed` without claiming semantic review completion. Focused proof is green (`138` tests), `check_review_channel_bridge.py` is green, and `check_active_plan_sync.py` is green. | `partial-pass` | Keep the broader reviewer-worker blocker explicit, but promote the next bounded follow-up to a report-only supervisor/watch path that can keep polling and publishing operator-visible updates outside chat before widening into semantic-review automation or Rust/VoiceTerm ownership. |
| `2026-03-16T23:05:00Z` | `CODEX` | Recorded the real reviewer-lane failure class explicitly after the long operator-observed stall: Claude can keep acting like a persistent worker in its own terminal session, but the Codex reviewer still is not a repo-owned persistent worker/service and still depends on this chat session staying alive. Heartbeat/checkpoint helpers exist, but semantic re-review/promotion still is not owned by an external reviewer worker yet. | `partial-pass` | Keep Claude on the current bounded `M66` coding slice, but treat the reviewer-worker/service implementation as a separate architecture blocker: add a repo-owned Codex reviewer worker/supervisor path that polls on cadence, writes reviewer checkpoints, and emits operator-visible updates without waiting for user prompts. |
| `2026-03-16T23:00:00Z` | `CODEX` | Accepted the bounded `M65` detached publisher durability slice. The detached-start path now records `failed_start` when the spawned publisher is dead on arrival, and runtime reads now infer `detached_exit` when a previously started publisher dies before the next controller read. The focused review-channel/runtime bundle is green (`133` tests). | `partial-pass` | Promote the next bounded lifecycle follow-up to explicit publisher lifecycle attention: differentiate `failed_start` / `detached_exit` from generic `publisher_missing` in shared attention/runtime outputs before widening into auto-restart or broader cleanup semantics. |
| `2026-03-16T12:55:00Z` | `CODEX` | Accepted the bounded `M64` clean-stop slice. Direct `review-channel ensure --follow` now emits explicit stop reasons (`timed_out`, `manual_stop`, `completed`, `output_error`), supports `--timeout-minutes`, and writes final publisher state with `stopped_at_utc`; the focused review-channel/runtime bundle is green (`131` tests). | `partial-pass` | Promote the next bounded lifecycle follow-up to the detached publisher durability seam: `--start-publisher-if-missing` must either keep the publisher alive under controller supervision or fail/write truthful stop state instead of leaving a dead heartbeat ambiguity. |
| `2026-03-16T14:10:00Z` | `CODEX` | Tightened the markdown-bridge protocol so the live Claude/Codex loop is explicit instead of implied: in `active_dual_agent`, both sides now start polling immediately after bootstrap, Claude codes exactly one bounded slice before returning to wait/poll mode, Codex re-reviews and rewrites the bridge, and that back-and-forth repeats until the scoped plan is exhausted or a real blocker/approval boundary is hit. | `in-progress` | Keep the live bridge and conductor prompts aligned to this closed-loop rule, then preserve the same semantics when the markdown bridge is replaced by structured review-state/runtime authority. |
| `2026-03-16T12:45:32Z` | `CODEX` | Accepted the bounded `M63` timeout-escalation slice. `review-channel status` now escalates stale reviewer heartbeat to `reviewer_overdue` above the configured threshold, the threshold is CLI-configurable, and the focused review-channel/runtime bundle is green (`129` tests). The current session still honestly shows `publisher_missing` because no controller-owned publisher is running; that is runtime truth, not a false-green code defect. | `partial-pass` | Promote the next bounded lifecycle follow-up to `M64`: land the first clean stop/shutdown contract for follow-backed controller runs with explicit stop reason, timeout budget, and final state write before widening into pause/resume or cleanup verification. |
| `2026-03-16T12:16:30Z` | `CODEX` | Accepted the bounded `M55` lifecycle-truth slice. `review-channel ensure` now fails closed when the publisher is missing, shared status/runtime outputs emit `publisher_missing`, and the focused proof bundle is green. The current session still honestly shows `publisher_missing` because no controller-owned publisher is running; that is runtime truth, not a false-green code defect. | `partial-pass` | Promote the next bounded lifecycle follow-up to `M63`: add configurable overdue-timeout escalation to the shared review/controller path before tackling full stop/shutdown semantics. |
| `2026-03-16T12:15:00Z` | `CODEX` | Recorded the live 5-hour Claude wait as a control-plane failure class instead of treating it as mere operator friction. The bridge/publisher path still allows an implementer to sit in a wait state when reviewer cadence does not advance, so timeout budgets, overdue escalation, and clean stop/cleanup semantics are now explicit requirements of the same controller-owned lifecycle slice. | `partial-pass` | Keep `M55` bounded to the active publisher/status truth fix, then land the next lifecycle follow-up as controller-owned timeout/escalation/stop semantics with cleanup verification. |
| `2026-03-16T10:34:39Z` | `CODEX` | Re-reviewed the next `M55` lifecycle step after the new `--start-publisher-if-missing` seam landed. Focused tests are green and the backend can now spawn the follow publisher on demand, but the controller truth is still false-green because `review-channel ensure` continues to report healthy success when active dual-agent mode requires a publisher and none is running. | `partial-pass` | Keep `M55` open and land the smallest backend-only lifecycle truth patch next: thread publisher-missing state into attention/runtime projections and make `ensure` degrade unless auto-start actually recovers the publisher. |
| `2026-03-16T06:57:00Z` | `CODEX` | Landed the first backend-owned reviewer publisher slice behind the current bridge-backed loop: `review-channel ensure --follow` now refreshes reviewer heartbeat on cadence, emits NDJSON status frames through the normal output contract, and has focused tests proving follow-lifetime/output behavior plus heartbeat metadata emission. | `partial-pass` | Keep this slice honest as a publisher path only, then land the next controller-owned ensure/watch supervision step so active dual-agent mode no longer depends on a manually started follow command. |
| `2026-03-16T15:20:00Z` | `CODEX` | Landed the next MP-355 hotspot-cleanup tranche driven by the new code-shape probes. The publisher/reviewer-supervisor follow actions now share one repo-owned cadence/lifecycle runner instead of carrying duplicated heartbeat/output loops, and the bridge-backed status/projection builders now assemble from smaller helpers while preserving the existing `review_channel.state` compatibility exports used by downstream runtime/parser/test callers. Targeted `test_review_channel.py` coverage stayed green after the split. | `partial-pass` | Re-run the full `devctl check --profile ci` bundle, then use the refreshed probe output to decide whether the next cleanup should stay in review-channel state/event reducers or move to the remaining bridge-render command hubs. |
| `2026-03-15T23:50:00Z` | `CODEX` | Re-audited the current bridge-backed loop after landing repo-owned reviewer heartbeat/checkpoint writes. Confirmed the correct direction is one shared backend with explicit inactive modes instead of a dev-only fork, recorded that human-facing aliases like `agents` / `developer` should normalize to canonical reviewer modes, and promoted the remaining gaps: persistent liveness emission, JSON-first authority, and final provider-specific cleanup in downstream clients/docs. | `partial-pass` | Keep the bridge contract honest for now, but move the live authority to typed JSON state/projections and route later desktop/mobile mode toggles through the same backend actions. |
| `2026-03-08T00:00:00Z` | `CODEX` | Initialized dedicated review-channel/shared-screen execution plan from active user request; split this scope out from the broader control-plane plan and locked the initial phase model (canonical structured state first, shared screen second, guarded shared-session later). | `in-progress` | Wire this plan into `INDEX` + `MASTER_PLAN`, then iterate schema and phase details with the user before implementation. |
| `2026-03-08T00:20:00Z` | `CODEX` | Wired the new plan into `INDEX`, `MASTER_PLAN`, and discovery docs (`AGENTS.md`, `DEV_INDEX.md`, `dev/README.md`); ran active-plan governance checks. | `partial-pass` | Iterate the plan content with the user, then clear the unrelated strict-tooling blocker caused by pre-existing bundle/workflow parity drift in the in-flight publication-sync governance changes before merge. |
| `2026-03-08T01:35:00Z` | `CODEX` | Refined MP-355 from a scope/checklist draft into an implementation-grade plan: added Phase 0 schema/architecture work, explicit MP-340/ADR dependency ownership, concrete schema draft fields/examples, artifact layout, `devctl`-first command interface, polling/shared-screen design, keyboard contract, and integrity/guard expectations; also aligned the MCP note to the current repo rule that MCP remains additive/read-only. | `in-progress` | Back-reference the refined ownership split in `autonomous_control_plane.md` and `MASTER_PLAN`, then run plan-governance checks. |
| `2026-03-08T04:27:00Z` | `CODEX` | Extended the temporary markdown-bridge protocol so reviewer activity stays visible to the operator as well as Claude: each meaningful reviewer write to `bridge.md` now also owes a concise chat ping, and the bridge header now carries both UTC and local poll time for the current human-observed loop. | `in-progress` | Keep the live watcher and reviewer writes aligned to this operator-visible contract until the structured review-channel artifact path replaces the markdown bridge. |
| `2026-03-08T02:07:11Z` | `CODEX` | Incorporated the current markdown-based Codex<->Claude operating loop into the canonical MP-355 plan as a sanctioned temporary bridge: `bridge.md` is now explicitly treated as the interim coordination projection with ownership, polling cadence, hash-tracking, and sunset rules while the real `devctl review-channel` infrastructure is still being built. | `in-progress` | Keep using `bridge.md` for the live loop now, then replace it with the structured `review_event` / `review_state` path as Phase 1 implementation lands. |
| `2026-03-08T02:16:38Z` | `CODEX` | Promoted the stronger protocol framing for the current markdown bridge: the active shared markdown file is now explicitly treated as a lightweight coordination log with minimum required current-state fields (`owner`, reviewed hash, poll time, blockers, next action) rather than loose notes. | `in-progress` | Keep the temporary bridge disciplined now, then preserve the same state semantics when migrating to structured `review_event` / `review_state` artifacts. |
| `2026-03-08T02:25:00Z` | `CODEX` | Ran a second architecture/guard review against the live repo surfaces and folded the useful scratch-audit findings back into this canonical plan: tightened the exact `terminal_packet` v1 schema, added repo wiring constraints (dedicated parser module, audit-area mapping, bundle/workflow parity, policy ownership, retention updates), and recorded MCP-extension + post-`cargo test` hygiene expectations. The temporary scratch audit file was retired after promotion. | `in-progress` | Keep MP-355 implementation scoped to these repo-native constraints and avoid reintroducing MCP-first or cross-plan-bus scope creep during code landing. |
| `2026-03-08T02:31:00Z` | `CODEX` | Folded the latest markdown-loop architecture note back into the canonical plan: the temporary `bridge.md` bridge is now explicitly modeled as a lightweight coordination-log state machine with named failure modes (stale reads, section clobber, blocker ambiguity, markdown/repo drift, context-loss drift), and the plan now states that the same review state must later compile into control-plane and memory handoff/survival artifacts instead of remaining a standalone side channel. | `in-progress` | Keep the live markdown bridge disciplined for current Claude/Codex work, then preserve the exact same state fields when reducing into `review_state`, `controller_state`, and memory handoff outputs. |
| `2026-03-08T03:08:00Z` | `CODEX` | Reconciled the plan with Memory Studio and MP-340 after a cross-plan architecture pass: added a shared event-header contract, `context_pack_refs` for memory-backed handoffs, capture-active memory-event emission for review outcomes, provider-aware pack routing, and a deferred unified timeline/replay dependency so MP-355 no longer reads like an isolated side protocol. | `in-progress` | Mirror the same contract in `autonomous_control_plane.md`, `memory_studio.md`, `MASTER_PLAN.md`, and the developer index, then rerun active-plan governance checks. |
| `2026-03-08T03:34:00Z` | `CODEX` | Re-ran plan/tooling governance after the interop alignment patch. `check_active_plan_sync`, `check_multi_agent_sync`, `docs-check --strict-tooling`, `check_agents_contract`, and `check_bundle_workflow_parity` all pass. The remaining red checks are repo-pre-existing and unrelated to MP-355 wording (`hygiene --strict-warnings` / `check_publication_sync` stale external publication drift, `check_code_shape.py` growth in `dev/scripts/devctl/process_sweep.py`, and Rust allow-attr debt growth in `rust/src/bin/voiceterm/theme/mod.rs`). | `partial-pass` | Keep MP-355 doc state as-is; resolve the unrelated publication/code-shape/lint debt in their owning scopes before claiming a full bundle.tooling green run. |
| `2026-03-08T04:55:00Z` | `CODEX` | Closed the remaining bootstrap-enforcement gap for the temporary markdown bridge: added `check_review_channel_bridge.py` plus unit coverage, wired it into bundle/workflow governance, and tightened the `bridge.md` start rules so a fresh Codex or Claude conversation knows exactly which authority files to read and which live sections to start from. | `in-progress` | Keep using the markdown bridge for today’s reviewer/coder loop, but treat the new guard as the floor so fresh-convo repeatability no longer depends on hidden memory or manual reminder prompts. |
| `2026-03-08T06:12:00Z` | `CODEX` | Tightened the markdown-bridge autonomy protocol after an operator review of loop stalls: the bridge now explicitly forbids stopping at a resolved slice when scoped plan work remains, adds `resolved -> next_slice_selected -> coding` semantics, documents `completion stall` as a named failure mode, and points to `devctl swarm_run --continuous` as the repo-native fully hands-off progression path. | `in-progress` | Keep reviewer writes promoting the next unchecked scoped plan item instead of idling at "all green," and use `swarm_run --continuous` when the execution mode should be script-driven rather than chat-driven. |
| `2026-03-08T07:05:00Z` | `CODEX` | Aligned MP-355 with the broader operator-cockpit direction: review packets now explicitly route `requested_action` through the same typed command catalog and policy engine as overlay buttons, with warning/approval/waiver results surfaced back into the lane instead of letting agents bypass policy through freeform shell/API text. | `in-progress` | Keep Phase 3 implementation typed-action-first so Git/GitHub/CI/memory requests remain auditable and approval-aware across both button clicks and AI-issued requests. |
| `2026-03-08T18:10:00Z` | `CODEX` | Landed `ADR-0027` and `ADR-0028` from the active cross-plan backlog, so MP-355 now cites accepted architectural authority for the shared controller envelope and relay-packet protocol instead of a pending placeholder. The same cleanup also made the markdown-bridge guard conditional on `bridge.md` being present, which keeps clean checkouts and unrelated branches push-safe while preserving guard coverage when the bridge is active. | `in-progress` | Keep Phase 0/1 implementation aligned to the accepted ADRs, and retire the markdown bridge once the structured `review_event` / `review_state` path replaces it. |
| `2026-03-08T18:21:48Z` | `CODEX` | Merged the standalone multi-agent worktree runbook into this MP-355 execution plan so the current scale-out cycle uses one static markdown swarm plan here and one live coordination bridge in `bridge.md`. Defined the 16-lane 8+8 Codex-reviewer/Claude-coder swarm, moved the instruction/ledger/signoff templates into this file, and retired the old separate runbook path. | `in-progress` | Start the 8+8 swarm from `bridge.md`, keep five-minute reviewer poll updates flowing in chat, and let the merged sync guard enforce parity against this file instead of a second runbook. |
| `2026-03-08T18:15:33Z` | `CODEX` | Tightened the live markdown-bridge operating model for the current multi-agent reviewer/coder loop: bridge writes are now explicitly conductor-owned, specialist workers are read-only against `bridge.md`, the operator heartbeat is locked to a five-minute cadence while code is moving, and specialist wakeups are change-routed instead of every worker polling the full tree blindly. | `in-progress` | Keep the current bridge disciplined under this conductor/specialist model, then preserve the same ownership and wakeup semantics when Phase 1 replaces the markdown bridge with structured `review_event` / `review_state` artifacts. |
| `2026-03-08T18:46:05Z` | `CODEX` | Added the first bridge-gated `devctl review-channel` implementation slice: `--action launch` now reads the merged 8+8 lane table, emits Codex/Claude conductor launch scripts/prompts that explicitly route through `AGENTS.md` plus the repo-owned `devctl`/check surfaces, optionally opens local Terminal.app sessions, records a dedicated audit-events area mapping, and fails closed once the markdown bridge is inactive so the launcher cannot silently outlive the transitional bridge. | `in-progress` | Use the launcher for the current markdown swarm only, keep the retirement trigger explicit in backlog/docs, and evolve or remove it when overlay-native review launch becomes canonical. |
| `2026-03-08T19:55:00Z` | `CODEX` | Hardened the launcher against context-loss drift: conductors now get a repo-owned `review-channel --action rollover` path with a 50% threshold, repo-visible handoff bundles, default dark Terminal.app profile selection, exact visible ACK lines for fresh Codex/Claude conductors, and structured failure reporting for terminal-launch errors. | `in-progress` | Exercise the live rollover loop in a real Codex/Claude session, then add the remaining peer-liveness and automatic next-task promotion guards tracked in `continuous_swarm.md`. |
| `2026-03-09T05:40:00Z` | `CODEX` | Reconciled MP-355 wording with the current Memory Studio/runtime truth after a multi-agent docs/code audit: review-channel packets still only project bridge-era markdown/JSON handoff bundles today, so `context_pack_refs`, provider-shaped attachments, and packet-lifecycle memory ingest are now explicitly documented as not-landed until structured `review_state` / `controller_state` artifacts exist and are consumed by repo surfaces. | `in-progress` | Keep the bridge path explicit as transitional only, then prove the structured artifact path before counting memory-backed handoff attach-by-ref work as closed. |
| `2026-03-08T20:35:00Z` | `CODEX` | Folded the current blunt architecture read back into repo-visible execution guidance: the collaboration system is now explicitly framed in maintainer docs as repo-visible, plan-scoped, role-separated, bounded, policy-gated, and CI-mirrored control-plane infrastructure rather than a retry-until-green loop, while the markdown bridge plus split state across plan/bridge/report artifacts are called out as the main current weakness. | `in-progress` | Keep Phase 0/1 focused on replacing the bridge authority with `dev/reports/review_channel/events/trace.ndjson` + `state/latest.json`, and retain markdown only as an operator-friendly projection once the structured path lands. |
| `2026-03-08T23:40:18Z` | `CODEX` | Clarified the MP-355 user-facing target from the active operator discussion: even before true shared-write ownership exists, the review surface should read as one collaborative terminal-native workflow where Codex and Claude visibly talk through packets, share state, and expose peer awareness on one screen instead of looking like unrelated side-by-side terminals. | `in-progress` | Preserve separate PTY ownership plus packet/ack/apply safety in early phases, then only promote to lease-based shared-target writes once the visually unified collaborative surface is already proven. |
| `2026-03-08T23:40:18Z` | `CODEX` | Extended the user-facing shared-surface target with an explicit all-agents job board and script-backed operator controls: the future review surface should show every active agent, current job, waiting-on state, and last packet activity, while any retask/customize action from the UI must remain a thin wrapper around typed repo-owned commands and typed registry state. | `in-progress` | Carry the agent-board fields into `review_state` / `registry/agents.json`, then stage Rust/shared-screen controls against existing `devctl` handlers instead of inventing hidden UI orchestration. |
| `2026-03-09T05:12:00Z` | `CLAUDE` | Hardened the transitional launcher/bridge contract in the active dirty tree: `devctl review-channel` now rejects `--await-ack-seconds <= 0` for rollover so the fresh-session ACK path stays fail-closed, and `check_review_channel_bridge.py` now requires live `Last Reviewed Scope` plus a non-idle `Current Instruction For Claude` section whenever the markdown bridge is active. | `partial-pass` | Keep the bridge files tracked/staged when appropriate so the guard can move from expected-red untracked status to full green, then continue on the remaining bridge-contract and peer-freshness follow-up. |
| `2026-03-09T05:46:00Z` | `CLAUDE` | Closed the remaining bounded Worker-A follow-up in the active dirty tree: `review-channel --action launch` now fails closed on untracked bridge files, stale reviewer poll state beyond the five-minute heartbeat contract, and idle/missing next-action bridge state; freshness now distinguishes `poll_due` vs `stale`; rollover ACK validation now requires the exact ACK line in the provider-owned section (`Poll Status` for Codex, `Claude Ack` for Claude) instead of raw substring search. `check_review_channel_bridge.py` now shares the same five-minute freshness limit, imports the shared live-state validator, and flags resolved verdicts that do not promote the next scoped task. | `partial-pass` | Keep the bridge files tracked/staged when appropriate so the direct launcher/guard proofs can move from expected-red untracked status to full green, then continue on the remaining governance-routing and Dev-panel/runtime honesty slices. |
| `2026-03-09T06:05:00Z` | `CLAUDE` | Closed the bounded workflow-parity follow-up for the tooling lane: `check_bundle_workflow_parity.py` now parses per-job run scopes, requires the main tooling bundle sequence to stay in `docs-policy`, requires the operator-console pytest lane to stay in `operator-console-tests`, and fails on wrong-job or out-of-order regressions instead of only proving command text appears somewhere in YAML. | `partial-pass` | Keep the tooling workflow path filters and job split aligned with the canonical bundle shape, then continue on the remaining Dev-panel/runtime honesty and operator-console live-path proof slices. |
| `2026-03-09T05:45:00Z` | `CODEX` | Landed the first bridge-backed read surface for MP-355: `devctl review-channel --action status` now writes repo-visible latest projections under `dev/reports/review_channel/latest/` (`review_state.json`, `compact.json`, `full.json`, `actions.json`, `latest.md`, `registry/agents.json`) from the current lane table + `bridge.md`, and rollover ACK detection now normalizes markdown list items correctly so visible ACK lines are actually observed in live relaunch tests. | `partial-pass` | Keep the transitional `status` slice stable, then implement the remaining typed/event-backed `watch|inbox|ack|dismiss|apply|history` path without overstating Phase-3 completion. |
| `2026-03-09T07:21:00Z` | `CODEX` | Re-ran the Python review-channel validation from the operator side in the current dirty tree: `python3 -m unittest dev.scripts.devctl.tests.test_review_channel -q` passed (`31` tests), `review-channel --action status --terminal none --format md` passed and wrote the latest projection bundle, and both `launch`/`rollover` dry-runs failed closed exactly as intended because `bridge.md` and `dev/active/review_channel.md` are still untracked bridge files in this checkout. | `partial-pass` | Keep the bridge files tracked/staged when the launcher path needs a green fresh-bootstrap proof, then continue on the event-backed `watch|inbox|ack|dismiss|apply|history` implementation path. |
| `2026-03-09T07:35:00Z` | `CODEX` | Ran a second live multi-agent re-review against the current dirty-tree bridge state and synced the results back into repo-visible plan state. The zero-second ACK bypass is genuinely closed, `status` projections are still landing correctly, and the bridge guard now enforces `Last Reviewed Scope` plus a non-idle instruction, but MP-355 remains open: `launch` still does not invoke the full bridge guard before bootstrap, freshness enforcement is still split between the five-minute heartbeat contract and a looser guard threshold, some handoff parsing paths still fall back to overly broad whole-file matching, generated rollover prompts still hardcode the default ACK timeout instead of threading the selected value end-to-end, and `test_review_channel.py` still has a duplicate test name that shadows intended coverage. | `in-progress` | Keep the bridge findings mirrored into `bridge.md` plus this plan, then close the remaining launch/freshness/ACK/coverage gaps before counting the markdown-bridge hardening slice as green. |
| `2026-03-09T09:04:05Z` | `CODEX` | Closed the next fail-closed bridge-status gap from the live re-review. `validate_launch_bridge_state()` now blocks fresh bootstrap when `Claude Status` or `Claude Ack` is missing, review-channel status projections/report payloads now set `ok: false` whenever bridge liveness is `waiting_on_peer` or `stale`, and the review/mobile consumer path no longer reports Claude as `active` just because the rendered bridge field holds the `"(missing)"` sentinel. | `partial-pass` | Keep the bridge files tracked/staged when operator-side dry-run proofs need a green launcher path, then continue on the remaining handoff-parser breadth and ACK-timeout threading follow-ups. |
| `2026-03-09T10:10:00Z` | `CODEX` | Added the first real live-session projection bridge for the desktop shell without changing PTY ownership: `review-channel --action launch|rollover` now writes per-session metadata plus live-flushed conductor transcript logs under `dev/reports/review_channel/latest/sessions/`, with script-wrapped Terminal launches preserving the existing Codex/Claude flow while giving repo-visible session tails to downstream read-only consumers. | `partial-pass` | Keep the launcher Codex/Claude-specific for the current swarm contract, then decide later whether MP-355 should generalize the same session-artifact format for more providers after the current review/event action surface is fully closed. |
| `2026-03-09T12:20:00Z` | `CODEX` | Closed the next live-launch blocker from operator testing: generated Claude conductor scripts now clear the inherited `CLAUDECODE` marker before exec so Terminal-launched `review-channel` sessions do not abort as forbidden nested Claude Code launches when started from a Claude-owned shell. | `partial-pass` | Re-run the live `terminal-app` launch path from the desktop shell and keep the Operator Console open so the new session-log tail panes can prove the fix end-to-end. |
| `2026-03-09T13:06:00Z` | `CODEX` | Re-ran the bridge/tooling proof against the current dirty tree and reconciled plan state with the actual checkout. Focused `test_review_channel` coverage, `review-channel --action status`, and `mobile-status --view full` are green on the current worktree, and custom `--await-ack-seconds` threading is already covered by the live test pack, so the older ACK-timeout blocker is no longer part of MP-355's open set. The conductor queue has shifted to bridge-honesty/docs-state refresh plus the current operator-console/serde-guard findings mirrored in `bridge.md`. | `partial-pass` | Keep the bridge current-state honest, sync the workflow/bridge docs to the fail-closed launcher contract, and close the remaining event-backed `watch|inbox|ack|dismiss|apply|history` path without re-introducing stale blocker text. |
| `2026-03-09T13:12:00Z` | `CODEX` | Live operator audit found the new Terminal launch can still self-stale even when both conductor windows are up: the Codex conductor can spend its first minutes spawning reviewer lanes and waiting on approval-bound subagent/tool prompts before it rewrites `Last Codex poll`, which leaves the bridge failing the five-minute freshness guard despite an active session log. Hardened the Codex conductor prompt so every fresh launch must stamp `Last Codex poll` / `Last non-audit worktree hash` / `Poll Status` before fan-out and must not sit on unanswered approval prompts without reflecting that blocked state in the bridge. | `partial-pass` | Re-run the live `terminal-app` launch path and confirm the reviewer heartbeat lands immediately on fresh bootstrap instead of aging out while the conductor is still gathering worker context. |
| `2026-03-09T13:32:00Z` | `CODEX` | Fixed the next operator-facing launcher footgun after live desktop testing opened duplicate Codex/Claude windows. `review-channel --action launch --terminal terminal-app` now checks the repo-owned `dev/reports/review_channel/latest/sessions/*.json` / `*.log` artifacts before launch and fails closed when they still look active, instead of silently opening a second live pair that races on the same session-tail files. The command docs now say that explicitly. | `partial-pass` | Keep this duplicate-launch guard aligned with the session-artifact contract, then continue on the remaining event-backed `watch|inbox|ack|dismiss|apply|history` path plus any later headless/background-PTY replacement for Terminal.app. |
| `2026-03-09T13:28:15Z` | `CODEX` | Landed the first overlay-side event-backed read path for MP-355 without changing default startup mode: the Rust Dev-panel review loader now prefers structured review-channel artifacts (`dev/reports/review_channel/projections/latest/full.json`, `state/latest.json`, or the older `latest/*.json` projections) whenever event-backed sentinels exist, parses those JSON projections into the existing `ReviewArtifact` shape, and falls back to `bridge.md` only when structured state is absent. The review surface copy now reflects generic review artifacts/projections rather than only markdown, which keeps the current overlay honest while proving the long-term migration path. | `partial-pass` | Keep markdown as transitional fallback for now, then normalize the remaining event-backed `watch|inbox|ack|dismiss|apply|history` reducer/projection flow so all review/mobile/operator surfaces read the same structured authority. |
| `2026-03-09T15:05:00Z` | `CODEX` | Landed the first real attach-by-ref `context_pack_refs` slice without adding more MP-355-only state paths: event-backed `packet_posted|acked|applied` artifacts now preserve structured context-pack attachments, `actions.json` and `latest.md` project them, the Rust review-artifact reader/surface renders them, and the Operator Console approval path now round-trips the same refs in typed JSON/markdown artifacts. The work also started paying down the god-file problem by moving context-pack normalization/resolution into focused helper modules instead of growing `review_channel.py` or the giant review-channel test file further. | `partial-pass` | Keep the remaining open scope on packet-outcome ingest and broader `controller_state` parity, and continue decomposing the oversized review/operator files instead of feeding them more mixed concerns. |
| `2026-03-10T02:00:00Z` | `CODEX` | Reduced MP-355 bridge-status red-noise without weakening the fail-closed launch path. `review-channel --action status` now honors the existing `--refresh-bridge-heartbeat-if-stale` self-heal path, so operator/read-only status refreshes can repair a stale `Last Codex poll` / worktree-hash heartbeat when the rest of the bridge contract is already valid. Added regression coverage and confirmed the real repo status command now refreshes the stale heartbeat and emits a green latest projection bundle instead of forcing a manual bridge edit first. | `partial-pass` | Keep the self-heal explicit to the typed flag, preserve fail-closed launch/rollover behavior, and continue on the remaining event-backed state/reducer closure. |
| `2026-03-14T12:40:00Z` | `CODEX` | Closed the next Claude/Codex instruction-drift gap for MP-355. The review-channel conductor prompt now reads the same repo-pack post-edit verification intro/steps/done-criteria contract that generates `CLAUDE.md`, so live launcher scripts and local Claude bootstrap instructions share one blocking definition of when checks are required and what counts as done. Added regression coverage for prompt-level policy injection plus dry-run launcher script output. | `in-progress` | Keep the remaining architecture gap explicit: `AGENTS.md` itself is still only partially generated, so the next cross-AI portability step is to move more of the canonical instruction surface under the same repo-pack renderer/guard path instead of leaving only the bundle reference section generated. |
| `2026-03-13T21:40:00Z` | `CODEX` | Closed the next live-launch honesty gap and the matching desktop read gap. `review-channel --action launch --terminal terminal-app` now waits for `Last Codex poll` to advance after launch and fails closed if a fresh reviewer heartbeat never appears, so opening Terminal windows no longer counts as a successful live reviewer loop by itself. The bridge-backed `review_state` projection now also emits a compact machine-readable `attention` contract (`status`, `owner`, `summary`, `recommended_action`, `recommended_command`) for stale reviewer / poll-due / waiting-on-peer states, and the Operator Console snapshot path now carries those structured warnings forward instead of silently dropping them after JSON load. | `partial-pass` | Keep the launch path fail-closed on real reviewer liveness, then extend the same typed attention contract into any later event-backed/state-store review path so restart/recovery/UI surfaces all read the same stale-peer truth. |
| `2026-03-13T22:05:00Z` | `CODEX` | Followed that liveness slice through the repo-owned structure and the default desktop view. The bridge-attention policy now lives in `review_channel/attention.py`, bridge-backed payload assembly in `status_projection.py`, and Terminal.app launch behavior in `terminal_app.py`, which brings the review-channel state/launch path back under shape policy instead of leaving the honesty logic in crowded files. The PyQt6 follow-up now promotes non-healthy review attention into Codex/operator lane health plus session stats, so the default session-first layout goes visibly stale instead of burying the problem only in the warning list. | `partial-pass` | Keep future stale-peer recovery and event-backed review state on the same typed attention contract instead of reintroducing lane-specific heuristics or prompt-only reminders. |
| `2026-03-27T05:10:00Z` | `CODEX` | Closed the bounded MP-355 producer -> MP-377 consumer freshness splice for the typed `current_session` lane. The shared review-state locator can now refresh the bridge-backed typed projection before startup/tandem consumers read it, so `startup-context`, `check_tandem_consistency`, and the governed push gate stop trusting stale `latest/review_state.json` snapshots while `bridge.md` remains a compatibility projection. Added focused regression proof for locator refresh, startup gate refresh, and tandem guard refresh. | `partial-pass` | Keep the remaining writer/mutation cutover bounded: stale-write preconditions, reviewer checkpoint/promotion paths, and the last bridge-text-only tandem checks still need typed/current-session or later collaboration-session authority before bridge prose can retire from live truth entirely. |
| `2026-03-26T00:38:51Z` | `CODEX` | Live operator review found the conductor contract was still too loose in two concrete places: reviewer prompts allowed lane fanout without fail-closed worktree checks, and reviewer freshness/hash truth still absorbed advisory artifacts like `convo.md` and `dev/audits/**` into live follow-up scope. Tightened the runtime so non-audit reviewer hash comparisons ignore those advisory artifacts, the conductor prompt now stays conductor-only when listed lane worktrees are missing instead of improvising live-repo fallback lanes, and the default planned anti-compaction rollover threshold moved from 50% to 20% remaining context. | `in-progress` | Re-run focused review-channel proof plus tooling/docs governance, then confirm a fresh launch/rollover dry-run advertises the tightened worktree and rollover contract. |

## Session Resume

- Current status: this plan remains active; start from the highest-priority
  open item in `## Execution Checklist` and the latest dated entry in
  `## Progress Log`.
- Next action: keep the remaining writer/mutation side of the typed
  `current_session` cutover bounded now that startup/tandem/push consumers
  refresh the typed projection first. Stale-write preconditions,
  reviewer-checkpoint/promotion paths, and the last bridge-text-only tandem
  checks still need typed or later `CollaborationSession` authority before
  `bridge.md` can stop acting like a live freshness source. Keep the newly
  mapped maintainability tranche explicit while doing that work: the phase is
  not done until the review-channel module family is materially smaller and
  `test_review_channel.py` has been split into feature-scoped suites. The
  next controller-consumer splice is explicit too: startup/work-intake and
  reviewer/implementer scheduling should stop reading `current_session` alone
  and start consuming `agent_registry` plus the typed queue/attention bundle
  that already powers the live status surfaces. The same slice must also stop
  prompts/guards/projections from teaching repo-root `bridge.md` or VoiceTerm
  plan paths as default authority while the bridge remains a compatibility
  projection. For the active architecture-audit loop running through this
  surface, keep Claude as the primary broad finder and Codex as the
  verifier/controller; `dev/audits/architecture_alignment.md` is the shared
  ledger, while `MASTER_PLAN` plus the scoped plans remain the execution
  owners.
- Context rule: treat `dev/active/MASTER_PLAN.md` as tracker authority and
  load only the local sections needed for the active checklist item.

## Audit Evidence

- Existing repo primitives this plan builds on:
  - `devctl phone-status` multi-view projections (`full`, `compact`, `trace`,
    `actions`, `latest.md`)
  - `devctl controller-action` guarded operator actions
  - `devctl loop-packet` packet generation and `terminal_packet` projection
  - Rust Dev panel async command broker and packet-to-PTY staging path
  - control-plane backlog already calling for one `controller_state` contract
    plus reviewer-agent packet ingestion
- Initial architectural constraints already verified:
  - VoiceTerm remains terminal-overlay-first and currently assumes a single
    backend PTY in normal operation
  - shared-screen UX is practical before shared-write session ownership is
    practical
  - multiple human/machine projections are practical as long as structured
    state stays canonical
  - current repo MCP policy remains additive and read-only; `devctl` remains
    the executable authority for write/policy paths
- Pending implementation evidence:
  - final schema draft embodied in code + parser validation
  - command parser/handler coverage
  - projection rendering coverage
  - `check_review_channel.py` guard coverage
  - Rust shared-screen render proof
  - policy/audit evidence for ack/apply routing
  - report-retention protected-path updates for any new review-channel roots
- `python3 -m pytest dev/scripts/devctl/tests/test_review_channel.py -q --tb=short`
  - 2026-03-09 local run: pass (`33` tests) after adding launcher-emitted
    session metadata/log artifacts and dry-run coverage for the new
    `sessions/*.json` + `sessions/*.log` contract
- 2026-03-09 overlay/event-backed read-path evidence:
  - `cargo test --manifest-path rust/Cargo.toml --bin voiceterm review_artifact -- --nocapture` -> pass (`33` tests)
  - `cargo test --manifest-path rust/Cargo.toml --bin voiceterm dev_panel_overlay::refresh_state -- --nocapture` -> pass (`19` tests)
  - `cargo test --manifest-path rust/Cargo.toml --bin voiceterm dev_panel_overlay::refresh_poll -- --nocapture` -> pass (`15` tests)
  - `cargo test --manifest-path rust/Cargo.toml --bin voiceterm review_surface -- --nocapture` -> pass (`18` tests)
- Governance results for plan onboarding:
  - `python3 dev/scripts/checks/check_active_plan_sync.py` -> pass
  - `python3 dev/scripts/checks/check_multi_agent_sync.py` -> pass
  - `python3 dev/scripts/devctl.py docs-check --strict-tooling` -> pass
  - `python3 dev/scripts/checks/check_agents_contract.py` -> pass
  - `python3 dev/scripts/checks/check_bundle_workflow_parity.py` -> pass
  - `python3 dev/scripts/devctl.py hygiene --strict-warnings` -> blocked only
- 2026-03-09 bridge-hardening evidence:
  - `python3 -m unittest dev.scripts.devctl.tests.test_check_review_channel_bridge dev.scripts.devctl.tests.test_review_channel -q` -> pass (`38` tests)
  - `python3 dev/scripts/devctl.py review-channel --action launch --terminal none --dry-run --format json` -> expected red while `bridge.md` and `dev/active/review_channel.md` remain untracked in the active dirty tree
  - `python3 -m pytest dev/scripts/devctl/tests/test_review_channel.py -q --tb=short` -> pass (`26 passed`)
  - `python3 dev/scripts/devctl.py review-channel --action status --terminal none --dry-run --format json` -> pass
  - `python3 dev/scripts/devctl.py review-channel --action rollover --terminal none --dry-run --format json` -> expected red in the current dirty tree because fresh conductor bootstrap fails closed while `bridge.md` and `dev/active/review_channel.md` remain untracked; green rollover bundle generation stays covered by `python3 -m unittest dev.scripts.devctl.tests.test_review_channel -q`
  - `python3 dev/scripts/devctl.py review-channel --action rollover --terminal none --dry-run --await-ack-seconds 0 --format json` -> expected fail-closed (`--await-ack-seconds must be greater than zero for rollover...`)
  - `python3 dev/scripts/checks/check_review_channel_bridge.py --format json` -> expected red while `bridge.md` and `dev/active/review_channel.md` remain untracked in the active dirty tree
  - `python3 -m unittest dev.scripts.devctl.tests.test_check_bundle_workflow_parity -q` -> pass (`14` tests)
  - `python3 dev/scripts/checks/check_bundle_workflow_parity.py` -> pass
    by pre-existing external publication drift for `terminal-as-interface`
  - Additional repo-pre-existing red guards during broader tooling pass:
    `python3 dev/scripts/checks/check_publication_sync.py`,
    `python3 dev/scripts/checks/check_code_shape.py`,
    `python3 dev/scripts/checks/check_rust_lint_debt.py`,
    `python3 dev/scripts/checks/check_rust_best_practices.py`
- 2026-03-09 operator validation evidence:
  - `python3 -m unittest dev.scripts.devctl.tests.test_review_channel -q` -> pass (`31` tests)
  - `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format md` -> pass; writes `review_state.json`, `compact.json`, `full.json`, `actions.json`, `latest.md`, and `registry/agents.json` under `dev/reports/review_channel/latest/`
  - `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format md` -> warning only: bridge liveness is `stale` because `Last Codex poll` is older than the five-minute heartbeat contract
  - `python3 dev/scripts/devctl.py review-channel --action launch --terminal none --dry-run --format json` -> expected red while `bridge.md` and `dev/active/review_channel.md` remain untracked in the active dirty tree
  - `python3 dev/scripts/devctl.py review-channel --action rollover --terminal none --dry-run --format json` -> expected red for the same untracked-bridge guard in the active dirty tree
- 2026-03-09 bridge-status fail-closed follow-up evidence:
  - `python3 -m pytest dev/scripts/devctl/tests/test_review_channel.py -q --tb=short` -> pass (`33 passed`; covers launch rejection on missing Claude ACK/status plus degraded `ok` status in review projections)
  - `python3 -m pytest dev/scripts/devctl/tests/test_mobile_status.py -q --tb=short` -> pass (`4 passed`; covers compact/mobile consumers after the Claude-lane status fix)
