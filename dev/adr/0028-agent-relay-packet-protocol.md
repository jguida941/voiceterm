# ADR 0028: Agent Relay Packet Protocol

Status: Accepted
Date: 2026-03-08

## Context

MP-355 introduces a dedicated shared review channel for Codex, Claude, and the
operator. The current `code_audit.md` loop works as a temporary bridge, but it
does not provide durable replay, explicit ack/apply semantics, idempotency, or
policy-aware action routing by itself.

The active plans already require:

- append-only `review_event` authority plus reduced `review_state`,
- typed action routing instead of free-form shell/API execution,
- memory-event normalization when capture is enabled,
- future timeline/replay merging with the broader MP-340 controller state.

## Decision

Adopt this relay protocol:

- `review_event` is the append-only write authority for reviewer/coder/operator
  packets.
- `review_state` is the latest reduced snapshot derived from validated
  `review_event` records.
- Relay packets reuse the shared controller header contract from ADR-0027 and
  add review-channel-specific status fields rather than inventing a second
  protocol family.
- Required packet lifecycle events are:
  `packet_posted`, `packet_acked`, `packet_dismissed`, `packet_applied`,
  `packet_expired`, `projection_rebuilt`, and `toast_emitted`.
- Every packet must carry replay/idempotency controls through
  `idempotency_key`, `nonce`, and `expires_at_utc`.
- Any `requested_action` emitted through the review channel must route through
  the same typed action catalog and approval/policy engine used by the Dev
  panel. The review channel does not authorize raw shell or API bypasses.
- The markdown bridge remains a temporary projection only. Once structured
  review artifacts land, `code_audit.md` stops being execution authority.

## Consequences

**Positive:**

- Reviewer/coder handoffs become replayable and machine-checkable.
- Action requests stay auditable and policy-aware across buttons and AI-issued
  packets.
- Memory ingest and future unified timeline work can consume review events
  without lossy translation.

**Negative:**

- Review-channel implementation now depends on reducer/projection correctness.
- Packet schema changes must be coordinated with control-plane and memory
  consumers.

## Alternatives Considered

- **Keep the markdown bridge as the long-term protocol**: rejected because it
  cannot provide durable replay, idempotency, or structured packet lifecycle
  guarantees.
- **Allow review packets to execute raw commands directly**: rejected because
  it bypasses the typed action catalog and weakens approval/audit controls.

## Links

- `dev/active/review_channel.md` (`MP-355`)
- `dev/active/autonomous_control_plane.md` (`MP-340`)
- `rust/src/bin/voiceterm/dev_command/action_catalog.rs`

