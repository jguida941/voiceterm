# MP-377 Codesmell 048-051 Plan Ingestion Source

This source binds the latest codesmell discoveries back into typed plan authority
without creating a new mega-plan. Existing MP-377 owner rows remain the authority
when they already own the domain. Only the CLI/test parity gap receives a new
closure row because no existing row owns that exact drift class.

Required existing-row composition anchors:

- `MP377-P0-EXC-S1`, `MP377-P0-EXC-S1B`, `MP377-P0-EXC-S1C`, `MP377-P0-EXC-S1D`
- `MP377-P0-CHECKPOINT-AUTOMATION-S1`, `MP377-P0-CHECKPOINT-STAGED-SNAPSHOT-RESTAGE-S1`, `MP377-P0-PIPELINE-SCOPE-VALIDATION-S1`
- `MP377-P0-DEVELOP-NEXT-DMA-S1`, `MP377-P0-PACKET-DISPOSITION-LEDGER-S1`, `MP377-P0-COMMAND-MANIFEST-LOOP-S1`
- `MP377-P0-GUARD-CADENCE-S1`, `MP377-P0-GUARD-DEFERRAL-S1`
- `MP377-P0-T22AD-A`, `MP377-P0-T22AN-A`, `MP377-P1-T05`, `MP377-P1-T06`, `MP377-P1-T07`, `MP377-P1-T08`

Required packet-binding citations:

- `PKT-BIND-REV-PKT-3596`

Evidence refs: `codesmells.md#smell-048`, `codesmells.md#smell-049`,
`codesmells.md#smell-050`, `codesmells.md#smell-051`, `packet:rev_pkt_3596`,
and `packet:rev_pkt_3597`.

Rows to ingest from this plan:

- `MP377-STALE-EVIDENCE-POLICY-GUARD-S1` Amend with codesmell #048: projection-producing tests must bind one frozen event-backed projection snapshot or typed stale-evidence result.
- `MP377-BRIDGE-PROJECTION-ONLY-GUARD-S1` Amend with codesmell #048: projection files remain display-only and projection races must not become authority drift.
- `MP377-AUTOINVAL-EVENT-SUBSCRIBER-S1` Amend with codesmell #048 and #051: projection refreshes and packet arrivals must invalidate or wake the affected derived-state consumers.
- `MP377-OPERATOR-OVERRIDE-LIFECYCLE-S1` Amend with codesmell #049: edit-only operator overrides need request, approval, active, expiry, revocation, and audit lifecycle states.
- `MP377-OPERATOR-OVERRIDE-ATTESTATION-S1` Amend with codesmell #049: startup authority must consume durable override attestation instead of chat prose for scoped edit-only repair.
- `MP377-GUARD-MATURITY-MODEL-S1` Amend with codesmell #049: override guards must distinguish edit-only repair from staging, commit, push, or publication authority.
- `MP377-DEVCTL-IMPORT-SMOKE-GUARD-S1` Amend with codesmell #050: CLI and focused pytest paths for a check must share one report builder or emit a typed parity failure.
- `MP377-CHECK-CLI-TEST-PARITY-S1` Add a guard row requiring check CLI output and focused pytest invocation to agree for registered governance checks.
- `MP377-SESSION-LIVENESS-WATCHDOG-S1` Amend with codesmell #051: stale session plus pending typed packet must produce watchdog evidence, not require operator-paste wakeup.
- `MP377-PUSH-BASED-EVENTBUS-SUBSTRATE-S1` Amend with codesmell #051: packet delivery must become a producer-backed wake/recompute event for runtime controllers.

Aspirational until implemented by the named phases:

```bash
python3 dev/scripts/checks/check_check_cli_test_parity.py --format json
python3 dev/scripts/checks/check_session_wake_controller.py --format json
```
