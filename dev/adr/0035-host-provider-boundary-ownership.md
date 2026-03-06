# ADR 0035: Host/Provider Boundary Ownership and Extension Policy

Status: Accepted
Date: 2026-03-05

## Context

MP-346 identified repeated host/provider coupling across runtime paths
(`writer/state.rs`, `event_loop.rs`, and related modules). Direct mixed
conditionals made behavior hard to reason about, hard to test, and easy to
regress when adding hosts/providers.

The runtime now has canonical ownership surfaces:

- Host/runtime compatibility policy in `runtime_compat.rs`.
- Provider behavior contracts in `provider_adapter.rs`.
- Isolation enforcement in `check_ide_provider_isolation.py`.

## Decision

Adopt strict ownership boundaries for host/provider behavior:

- `runtime_compat.rs` owns terminal host detection, host capabilities, and
  host-scoped timing/compat policy.
- `provider_adapter.rs` owns provider identity mapping and provider-specific
  strategy contracts.
- Cross-product host+provider policy is allowed only in explicit policy-owner
  modules (`runtime_compat.rs`, `writer/state/profile.rs`, `writer/timing.rs`)
  and must remain guarded by isolation checks.
- Runtime/UI modules outside policy owners must consume typed helpers or
  adapter outputs; they must not add new inline host+provider branching.

Extension policy:

- Adding a new host requires canonical host detection/update in
  `runtime_compat.rs` and matrix coverage updates.
- Adding a new provider requires adapter contract updates in
  `provider_adapter.rs` and matrix/provider-mode updates.
- Any exception to isolation boundaries must be temporary, explicitly
  allowlisted with owner/expiry, and removed in follow-up scope.

## Consequences

**Positive:**

- Reduces ad-hoc host/provider branching drift.
- Keeps ownership explicit and reviewable.
- Makes matrix coverage and policy checks meaningful release gates.

**Negative:**

- New host/provider onboarding has more up-front governance steps.
- Policy-owner modules can become concentrated hotspots and need active size
  budget enforcement.

## Alternatives Considered

- **Allow host/provider branching in any runtime module**: rejected because it
  recreates coupling drift and weakens isolation enforcement.
- **Move all host/provider policy into one mega module**: rejected because it
  over-centralizes unrelated behavior and increases hotspot risk.

## Links

- `rust/src/bin/voiceterm/runtime_compat.rs`
- `rust/src/bin/voiceterm/provider_adapter.rs`
- `rust/src/bin/voiceterm/writer/state/profile.rs`
- `rust/src/bin/voiceterm/writer/timing.rs`
- `dev/scripts/checks/check_ide_provider_isolation.py`
- `dev/active/ide_provider_modularization.md` (`MP-346`)
