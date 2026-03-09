# ADR 0027: Unified Controller State Contract

Status: Accepted
Date: 2026-03-08

## Context

MP-340 is growing one operator/control-plane surface across the Rust Dev panel,
`devctl phone-status`, the temporary markdown bridge, future review-channel
artifacts, and memory-backed handoff outputs. Without one canonical state
contract, each surface could drift into its own field names, projection shape,
and replay rules.

The active plans already converged on a shared envelope:

- `controller_state` is the umbrella control-plane state.
- Structured JSON is the authority; markdown and terminal views are
  projections.
- Review-channel and memory handoff work must normalize into the same header
  semantics instead of creating parallel state roots.

## Decision

Adopt one canonical `controller_state` contract with these rules:

- Structured state is authoritative. Markdown, compact summaries, terminal
  packets, and phone/SSH views are projections over the same source state.
- Shared event/header fields must keep stable names and meanings across MP-340
  and MP-355:
  `event_id`, `session_id`, `project_id`, `trace_id`, `timestamp_utc`,
  `source`, `event_type`, `plan_id`, `controller_run_id`, `from_agent`,
  `to_agent`, `evidence_refs`, `confidence`, `requested_action`,
  `idempotency_key`, `nonce`, and `expires_at_utc`.
- Review-channel state (`review_state`) is a review-focused profile over this
  contract, not a separate competing authority.
- Memory-backed attachments travel by reference through `context_pack_refs`.
  Canonical pack bodies stay owned by Memory Studio; receiver-specific text
  shaping happens only in projections.
- Rust Dev panel, `devctl` projections, and future phone/SSH surfaces must read
  the same reduced state rather than maintaining surface-local copies.

## Consequences

**Positive:**

- Field naming stays stable across Dev panel, review-channel, and phone/SSH
  surfaces.
- Projection drift becomes easier to detect and test.
- Future replay/timeline work can merge controller, review, and memory events
  without translation glue.

**Negative:**

- New control-plane features now owe schema discipline up front.
- Canonical reducers/projection builders become critical integration points and
  need active size/ownership guardrails.

## Alternatives Considered

- **Per-surface state models**: rejected because Rust, phone, review, and
  memory surfaces would drift into parallel naming and replay rules.
- **Markdown-first authority**: rejected because machine validation,
  projection parity, and replay guarantees are weaker than with structured
  state.

## Links

- `dev/active/autonomous_control_plane.md` (`MP-340`)
- `dev/active/review_channel.md` (`MP-355`)
- `dev/active/memory_studio.md`

