# MP-377 Codesmell 042-044 and 052 Plan Ingestion Source

This source binds the remaining Claude-identified codesmell observations from
cycle 129-133 into typed MP-377 plan authority. It does not create a new
mega-plan. Existing owner rows remain authority because each smell maps to an
already-owned MP-377 domain.

Required existing-row composition anchors:

- `MP377-P0-CHECKPOINT-AUTOMATION-S1`, `MP377-P0-CHECKPOINT-STAGED-SNAPSHOT-RESTAGE-S1`, `MP377-P0-PIPELINE-SCOPE-VALIDATION-S1`
- `MP377-P0-DEVELOP-NEXT-DMA-S1`, `MP377-P0-PACKET-DISPOSITION-LEDGER-S1`, `MP377-P0-COMMAND-MANIFEST-LOOP-S1`
- `MP377-P0-GUARD-CADENCE-S1`, `MP377-P0-GUARD-DEFERRAL-S1`
- `MP377-P0-EXC-S1`, `MP377-P0-EXC-S1B`, `MP377-P0-EXC-S1C`, `MP377-P0-EXC-S1D`
- `MP377-P0-T22AD-A`, `MP377-P0-T22AN-A`, `MP377-P1-T05`, `MP377-P1-T06`, `MP377-P1-T07`, `MP377-P1-T08`

Required packet-binding citations:

- `PKT-BIND-REV-PKT-3596`
- `PKT-BIND-REV-PKT-3599`

Evidence refs: `codesmells.md#smell-042`, `codesmells.md#smell-043`,
`codesmells.md#smell-044`, `codesmells.md#smell-052`, `packet:rev_pkt_3602`,
and `packet:rev_pkt_3606`.

Rows to ingest from this plan:

- `MP377-P0-CHECKPOINT-AUTOMATION-S1` Amend with codesmell #042: dirty-tree checkpoint pressure must distinguish receipt-backed typed pipeline output from raw scratch edits before blocking bootstrap work.
- `MP377-CHECKPOINT-AUTOMATION-RECEIPT-INVARIANTS-S1` Amend with codesmell #042: checkpoint budget decisions must consume receipt-backed repo-state fingerprints and typed checkpoint evidence instead of only path counts.
- `MP377-OPERATOR-OVERRIDE-LIFECYCLE-S1` Amend with codesmell #042: edit-only override state must be a lifecycle input to startup authority when checkpoint pressure blocks legitimate governed repair.
- `MP377-OPERATOR-OVERRIDE-ATTESTATION-S1` Amend with codesmell #042: override attestation must carry scope, expiry, blocked actions, and required guard replay so edit-only repair cannot imply staging, commit, or push authority.
- `MP377-MULTI-SESSION-TARGET-DISAMBIGUATION-S1` Amend with codesmell #043 and #052: inbox, launch, and restart flows must resolve provider, role, session id, and selected live executor deterministically.
- `MP377-PACKET-MATCHING-ROLE-SCOPE-S1` Amend with codesmell #043: review-channel inbox filters must match pending packets by provider, role, session id, target kind, and route metadata without requiring the operator to know a packet id first.
- `MP377-DEVELOP-NEXT-CANONICAL-S1` Amend with codesmell #044: blocked agent-loop cadence must route to one canonical typed next action instead of recursively naming agent-loop as the next command.
- `MP377-NEXT-COMMAND-AUTHORITY-GUARD-S1` Amend with codesmell #044: advisory next_command output must not become a self-recursive mutation authority when a typed packet/action is the real next work.
- `MP377-CORRELATION-ID-SPINE-S1` Amend with codesmell #044: agent-loop decisions need action_id, correlation_id, causation_id, packet id, and run id so the next command can point at the concrete typed action to resolve.
- `MP377-SESSION-LIVENESS-WATCHDOG-S1` Amend with codesmell #052: multi-session restarts must produce typed liveness/election evidence for the live executor instead of leaving multiple sessions ambiguous.
- `MP377-COLLABORATION-MODE-TOPOLOGY-S1` Amend with codesmell #052: topology snapshots must model multiple same-provider sessions and expose the elected implementer/reviewer lanes to downstream reducers.

Aspirational until implemented by the named phases:

```bash
python3 dev/scripts/checks/check_checkpoint_budget_shape.py --format json
python3 dev/scripts/checks/check_review_channel_inbox_routing.py --format json
python3 dev/scripts/checks/check_agent_loop_next_command_authority.py --format json
python3 dev/scripts/checks/check_session_liveness_election.py --format json
```
