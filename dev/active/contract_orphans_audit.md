# Contract Orphans Audit

Reference-only follow-up scope for the `check_contract_consumer_coverage_sweep`
guard. This doc is not durable plan authority; it bundles the orphan
remediation backlog for typed contracts that have no external reader or writer
seam so a future PlanRow can plan the work.

## Context

`python3 dev/scripts/checks/check_contract_consumer_coverage_sweep.py
--format md` scans dataclasses under
`dev/scripts/devctl/{runtime,review_channel,platform}` and flags contracts that
lack external constructor/writer references (`contract_without_external_writer`)
and/or external reader/consumer references (`contract_without_external_reader`).
At baseline the sweep reports **60 orphan contract classes producing 97
violations** (most contracts produce two violations: one writer, one reader).

## Top offending modules (orphan count per module)

These modules carry the most orphan dataclasses; each module is a candidate
target for collapsing private models into typed seams or wiring missing
consumers through `runtime/__init__.py` style export surfaces.

| Module | Orphan-violation count |
|---|---|
| `dev/scripts/devctl/runtime/development_collaboration_profiles.py` | 22 |
| `dev/scripts/devctl/runtime/control_decision_obedience.py` | 10 |
| `dev/scripts/devctl/review_channel/packet_contract.py` | 8 |
| `dev/scripts/devctl/runtime/peer_spawn.py` | 8 |
| `dev/scripts/devctl/runtime/relaunch_loop_models.py` | 6 |
| `dev/scripts/devctl/runtime/role_profile.py` | 6 |
| `dev/scripts/devctl/review_channel/handoff.py` | 5 |
| `dev/scripts/devctl/platform/coordination_topology_models.py` | 4 |
| `dev/scripts/devctl/review_channel/topology.py` | 4 |
| `dev/scripts/devctl/runtime/role_topology.py` | 4 |

## Follow-up plan items

The 60 orphan contracts are out of scope for the current session's "register
missing contracts" work. They require a separate planned slice that:

1. Audits each orphan to decide whether it should be (a) wired to typed
   consumers and exposed via the appropriate runtime/review_channel `__init__`,
   (b) collapsed into an existing typed seam (when redundant), or (c) demoted
   to a private `_PrivateModel` if it is genuinely internal.
2. Emits a `FeatureProofReceipt` proving each orphan now has at least one
   external reader and one external writer reference.
3. Re-runs `check_contract_consumer_coverage_sweep --scope all` to ratchet the
   violation count down to zero.

Until that follow-up slice is planned and tracked in `dev/state/plan_index.jsonl`,
the sweep should be treated as a budget signal, not an immediate blocker.

## Surface provenance

- contract_id: `ContractOrphansAuditReference`
- projection_only: true
- source_command: `python3 dev/scripts/checks/check_contract_consumer_coverage_sweep.py --format md`
