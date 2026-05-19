# bridge.md - Deprecated Projection Stub

This file is not authority.

`bridge.md` is a generated compatibility projection and prompt hazard. It may be
stale, contradictory, incomplete, or intentionally stubbed during GuardIR
extraction.

Durable authority lives in typed state, contracts, receipts, repo policy, source
code, and guards. Agents must not use this file to decide:

- actor or provider roles
- reviewer/coder assignment
- launch permission
- mutation or edit permission
- proof, commit, push, or publication status
- plan closure or task completion

If this file conflicts with typed state, typed state wins.

If runtime logic depends on this file for backend authority, that is a bug.

If this file is stale or empty, report `projection_stale`; do not report
`missing_backend_authority`, and do not block implementation solely from this
projection.

Current extraction rule: VoiceTerm product-shell quarantine and the bridge
authority kill-switch are blocking before Phase 1 proof-integrity.
