# devctl JSON Contracts

**Status**: active reference  |  **Last updated**: 2026-03-15 | **Owner:** Tooling/control plane

This guide documents the current machine-readable JSON and JSONL surfaces that
`devctl`, the review loop, and their thin clients already emit or consume.

Scope rules:

1. This is implementation-grounded. It describes current files, emitters, and
   readers in this repo.
2. JSON/JSONL/NDJSON surfaces are listed only when code reads or writes them
   directly today.
3. Markdown companions such as `latest.md` and `handoff.md` are human
   projections unless the code path still uses markdown as a live fallback.

## How To Read This

There are three kinds of machine surfaces in the current tree:

1. Append-only ledgers:
   long-lived JSONL/NDJSON logs that accumulate rows over time.
2. Reduced state and projection bundles:
   latest-state JSON files rebuilt from live inputs for CLI, PyQt6, mobile, or
   agent consumption.
3. Wrapper-local artifacts:
   machine-readable files used by one frontend or transitional path, but not
   yet the canonical shared control-plane contract.

## Canonical Path Registry

The current repo-owned path registry lives in
`dev/scripts/devctl/repo_packs/voiceterm.py` as `VOICETERM_PATH_CONFIG`.

That registry is the current path-authority seam for:

- `dev/reports/audits/devctl_events.jsonl`
- `dev/reports/governance/finding_reviews.jsonl`
- `dev/reports/governance/external_pilot_findings.jsonl`
- `dev/reports/autonomy/watchdog/episodes/guarded_coding_episode.jsonl`
- `dev/reports/review_channel/events/trace.ndjson`
- `dev/reports/review_channel/state/latest.json`
- `dev/reports/review_channel/projections/latest/`
- `dev/reports/review_channel/latest/` legacy mirrors
- `dev/reports/mobile/latest/full.json`
- `dev/reports/autonomy/queue/phone/latest.json`

## Append-Only Ledgers

### 1. devctl command telemetry

- Path: `dev/reports/audits/devctl_events.jsonl`
- Writer: `dev/scripts/devctl/audit_events.py`
- Current owner: the `devctl` command wrapper itself
- Current consumers:
  - `dev/scripts/devctl/data_science/metrics.py`
  - autonomy/status reporting and audit metrics
  - active-plan evidence references
- Current role:
  one row per `devctl` command execution, including command name, area, step,
  success, duration, argv, and optional `machine_output`
- Versioning seam:
  row shape is currently owned by `build_audit_event_payload()`. There is no
  explicit row `schema_version` yet, so that function is the natural version
  choke point.

### 2. Governance review ledger

- Path: `dev/reports/governance/finding_reviews.jsonl`
- Writer: `devctl governance-review` via
  `dev/scripts/devctl/governance_review_log.py`
- Current owner: governance review/adjudication flow
- Current consumers:
  - `devctl governance-review` summary output
  - `devctl governance-import-findings` coverage metrics
  - `dev/scripts/devctl/data_science/metrics.py`
- Current role:
  durable adjudication ledger for guard/probe/audit findings
- Versioning seam:
  `build_governance_review_row()` is the current row-shape owner. The row does
  not carry an explicit `schema_version`.

### 3. External finding intake ledger

- Path: `dev/reports/governance/external_pilot_findings.jsonl`
- Writer: `devctl governance-import-findings` via
  `dev/scripts/devctl/commands/governance/import_findings.py`
- Current owner: raw external-finding intake before adjudication
- Current consumers:
  - `devctl governance-import-findings` summary output
  - `dev/scripts/devctl/data_science/metrics.py`
  - coverage comparison against `finding_reviews.jsonl`
- Current role:
  raw imported findings from pilot or external scans, kept separate from the
  adjudicated ledger
- Versioning seam:
  `build_external_finding_row()` in the governance external-findings layer owns
  the row shape. Like the review ledger, it currently versions by row contract
  rather than an explicit `schema_version` field.

### 4. Watchdog guarded-coding episodes

- Path: `dev/reports/autonomy/watchdog/episodes/guarded_coding_episode.jsonl`
- Writer: `devctl guard-run` via
  `dev/scripts/devctl/watchdog/episode.py`
- Current owner: watchdog analytics path
- Current consumers:
  - `dev/scripts/devctl/data_science/metrics.py`
  - watchdog/data-science summaries
- Current role:
  one normalized episode row per guard-run execution, plus per-episode
  `summary.json` under `dev/reports/autonomy/watchdog/episodes/<episode_id>/`
- Versioning seam:
  `GuardedCodingEpisode` and `build_guarded_coding_episode()` are the current
  shape owners. The JSONL row itself does not carry an explicit
  `schema_version`; the typed model is the real contract seam today.

### 5. Review-channel event log

- Path: `dev/reports/review_channel/events/trace.ndjson`
- Writer: `dev/scripts/devctl/review_channel/events.py`
- Current owner: event-backed review-channel flow
- Current consumers:
  - `dev/scripts/devctl/review_channel/event_reducer.py`
  - `review-channel` history/watch/inbox reducers
  - projection rebuilds
- Current role:
  append-only packet/event history for the event-backed review path
- Versioning seam:
  each event already carries `schema_version: 1`, so this is one of the few
  row-level versioned machine surfaces already in place.

## Reduced State And Projection Bundles

### 6. Reduced event-backed review state

- Path: `dev/reports/review_channel/state/latest.json`
- Writer: `dev/scripts/devctl/review_channel/event_reducer.py`
- Current owner: review-channel event reducer
- Current consumers:
  - `load_or_refresh_event_bundle()` in the review-channel layer
  - event-backed status/projection refresh
- Current role:
  reduced latest review state rebuilt from `events/trace.ndjson`
- Versioning seam:
  top-level `schema_version: 1` in the reduced state payload

### 7. Review-channel latest projection bundle

- Canonical root:
  `dev/reports/review_channel/projections/latest/`
- Legacy compatibility mirror:
  `dev/reports/review_channel/latest/`
- Writer: `dev/scripts/devctl/review_channel/projection_bundle.py`
- Current owner: review-channel projection bundle
- Files:
  - `review_state.json`
  - `full.json`
  - `compact.json`
  - `actions.json`
  - `trace.ndjson`
  - `registry/agents.json`
  - `latest.md` human projection
- Current consumers:
  - CLI: `devctl review-channel --action status`
  - runtime: `dev/scripts/devctl/runtime/review_state_parser.py`
  - PyQt6: `app/operator_console/state/review/review_state.py`
  - mobile merge path: `dev/scripts/devctl/repo_packs/review_helpers.py`
  - Rust/other readers that prefer structured review artifacts over markdown
- Current role:
  the current shared latest-state handoff bundle for review-loop consumers
- Authority note:
  this is the most reusable current review-loop JSON surface. It is the one
  the runtime parser and thin clients actually normalize.
- Versioning seam:
  `schema_version: 1` exists on `review_state.json`, `full.json`,
  `compact.json`, `actions.json`, and `registry/agents.json`.

### 8. Review-channel runtime normalization contract

- Source files:
  - `dev/scripts/devctl/runtime/review_state_models.py`
  - `dev/scripts/devctl/runtime/review_state_parser.py`
- Current role:
  these modules are not artifact writers themselves, but they define the
  normalization contract for `review_state.json` and `full.json`
- Current consumers:
  - PyQt6 review/session/collaboration readers
  - any code that calls `review_state_from_payload()`
- Versioning seam:
  the typed `ReviewState` model is the compatibility choke point for all
  review-state consumers.

### 9. Review rollover handoff bundles

- Path root: `dev/reports/review_channel/rollovers/<timestamp>/`
- Machine file: `handoff.json`
- Writer: `dev/scripts/devctl/review_channel/handoff.py`
- Current owner: review-channel rollover path
- Current consumers:
  - collaboration/timeline readers such as
    `app/operator_console/collaboration/timeline_builder.py`
  - continuous-swarm handoff flow
- Current role:
  repo-visible rollover/resume payload for fresh-session handoff
- Versioning seam:
  the JSON shape is owned by the handoff writer; it is not yet a broader shared
  runtime contract like `ReviewState` or `ControlState`.

### 10. phone-status source artifact and emitted bundle

- Source artifact path:
  `dev/reports/autonomy/queue/phone/latest.json`
- Emitter for projection bundle:
  `dev/scripts/devctl/phone_status_views.py`
- Current owner:
  autonomy/controller reporting path for phone-safe read surfaces
- Current consumers:
  - CLI: `devctl phone-status`
  - `devctl mobile-status` input
  - PyQt6 fallback path in
    `app/operator_console/state/snapshots/phone_status_snapshot.py`
  - mobile preview/demo scripts
- Emitted projection files when `--emit-projections` is used:
  - `full.json`
  - `compact.json`
  - `trace.ndjson`
  - `actions.json`
  - `latest.md`
- Versioning seam:
  the emitted bundle is versioned by the payload builder in the
  `phone_status_views` / `phone_status_projection` layer. The raw
  `queue/phone/latest.json` source is treated more as controller output than as
  a separately versioned shared runtime contract.

### 11. mobile-status merged bundle

- Canonical emitted root:
  `dev/reports/mobile/latest/`
- Writer: `dev/scripts/devctl/commands/mobile_status.py` plus
  `dev/scripts/devctl/mobile_status_views.py`
- Current owner:
  merged read-only mobile bundle over controller state plus review state
- Files:
  - `full.json`
  - `compact.json`
  - `alert.json`
  - `actions.json`
  - `latest.md`
- Current consumers:
  - PyQt6 preferred phone/control snapshot path
  - iOS app loader in
    `app/ios/VoiceTermMobile/Sources/VoiceTermMobileCore/MobileRelayStore.swift`
  - simulator/device sync scripts
- Current role:
  first-party merged bundle for mobile/desktop thin clients
- Authority note:
  this is the current cross-surface contract that includes both raw payloads
  and the typed runtime `control_state`
- Versioning seam:
  top-level `schema_version: 1` on the full payload, plus nested
  `control_state.schema_version: 1`

### 12. ControlState runtime contract

- Source files:
  - `dev/scripts/devctl/runtime/control_state.py`
- Current role:
  typed normalization contract for `mobile-status` payloads, including
  approvals, active run, review bridge state, agents, and source paths
- Current consumers:
  - `devctl mobile-status`
  - PyQt6 phone/control snapshot loader
- Versioning seam:
  explicit `schema_version` and `contract_id` fields on `ControlState`

## Wrapper-Local Machine Artifacts

These are machine-readable and important, but they are not the shared
cross-surface authority yet.

### 13. Operator Console decision artifacts

- Path root:
  `dev/reports/review_channel/operator_decisions/`
- Machine files:
  per-decision `*.json` plus `latest.json`
- Writer:
  `app/operator_console/state/review/operator_decisions.py`
- Current consumers:
  - Operator Console itself
  - repo-visible review of operator choices
- Current role:
  wrapper-local typed decision record while direct
  `review-channel ack|apply|dismiss` is not yet the shared path
- Versioning seam:
  top-level `schema_version: 1`
- Important boundary:
  this is transitional wrapper state, not the canonical shared review-channel
  action contract

### 14. Operator Console diagnostics

- Path root:
  `dev/reports/review_channel/operator_console/`
- Machine files:
  `latest.events.ndjson` and per-session `sessions/<stamp>/events.ndjson`
- Writer:
  `app/operator_console/logging_support.py`
- Current consumers:
  desktop debugging and triage
- Current role:
  structured frontend diagnostics only
- Important boundary:
  not a shared backend contract and not a canonical review/control authority

## Current Consumer Map

### PyQt6 Operator Console

The desktop app currently reads, in order:

1. `dev/reports/mobile/latest/full.json` when available
2. `review_state.json` / `full.json` review-channel projections
3. raw `dev/reports/autonomy/queue/phone/latest.json` fallback
4. wrapper-local decision and diagnostics artifacts

Key reader modules:

- `app/operator_console/state/snapshots/phone_status_snapshot.py`
- `app/operator_console/state/review/review_state.py`
- `app/operator_console/state/snapshots/snapshot_builder.py`

### iOS / mobile

The iOS app currently reads the emitted `mobile-status` bundle:

- required: `full.json`
- optional: `compact.json`, `alert.json`, `actions.json`

Key reader modules:

- `app/ios/VoiceTermMobile/Sources/VoiceTermMobileCore/MobileRelayStore.swift`
- simulator sync scripts under `app/ios/VoiceTermMobileApp/`

### CLI

The CLI owns most artifact writes:

- `devctl review-channel`
- `devctl governance-review`
- `devctl governance-import-findings`
- `devctl phone-status`
- `devctl mobile-status`
- `devctl guard-run`

### Agents and thin wrappers

Current agent-facing machine surfaces are:

- `dev/reports/review_channel/projections/latest/review_state.json`
- `dev/reports/review_channel/projections/latest/full.json`
- `dev/reports/review_channel/projections/latest/actions.json`
- `dev/reports/mobile/latest/full.json`
- `dev/reports/audits/devctl_events.jsonl`
- `dev/reports/governance/finding_reviews.jsonl`

The markdown bridge `code_audit.md` is still a live coordination surface for
the transitional loop, but it is not part of the JSON contract set.

## Current Versioning Pressure Points

These are the implementation seams where versioning pressure is already visible:

1. `ReviewState` and `ControlState` already carry explicit `schema_version`
   fields and are the cleanest current shared runtime contracts.
2. Review-channel event rows already carry row-level `schema_version: 1`, so
   the event log is ahead of the longer-lived JSONL ledgers here.
3. The long-lived ledgers (`devctl_events.jsonl`, `finding_reviews.jsonl`,
   `external_pilot_findings.jsonl`, `guarded_coding_episode.jsonl`) are still
   versioned by writer function and typed parser rather than explicit row
   version fields.
4. Review projection path compatibility is still active:
   consumers look through candidate paths under both
   `projections/latest/` and legacy `latest/`, so path layout itself is still
   part of the compatibility surface.
5. `mobile-status` currently carries both raw payloads
   (`controller_payload`, `review_payload`) and normalized `control_state`.
   That means the merged bundle is serving as both compatibility envelope and
   runtime-contract carrier at the same time.

## Practical Rule

If you need a current machine authority surface today:

1. Use the JSONL ledgers for durable history and metrics.
2. Use `review_channel/projections/latest/review_state.json` or `full.json`
   for current review-loop state.
3. Use `mobile-status` `full.json` for current cross-surface mobile/desktop
   control state.
4. Treat wrapper-local JSON such as Operator Console decisions or diagnostics
   as transitional or frontend-local unless the runtime layer starts consuming
   them directly.
