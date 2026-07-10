# MP-377 Provider-Neutral Lane Routing Plan Ingestion Source

This source binds the provider-hardcoding correction into typed MP-377 plan
authority without creating a new owner row. Existing role roster, topology,
packet matching, projection-retirement, and extraction rows already own the
domain. Provider or delivery labels are compatibility metadata only; typed
authority must come from role, session, elected executor, capability grants,
liveness, receipts, and guard evidence.

Required existing-row composition anchors:

- `MP377-P0-T08F`
- `MP377-P0-ROLE-MATRIX-DOGFOOD-S1`
- `MP377-P0-ROLE-MATRIX-ROSTER-S1`
- `MP377-P0-ROLE-MATRIX-ACK-S1`
- `MP377-P0-RC-PAIR-S1`
- `MP377-P0-T22AN-AM`
- `MP377-P0-T22AN-AM-S1`
- `MP377-P0-T22AN-V`
- `MP377-P0-T22AN-X`
- `MP377-COLLABORATION-MODE-TOPOLOGY-S1`
- `MP377-TOPOLOGY-REDUCER-DESIGN-S1`
- `MP377-MULTI-SESSION-TARGET-DISAMBIGUATION-S1`
- `MP377-PACKET-MATCHING-ROLE-SCOPE-S1`
- `MP377-PROJECTION-RETIREMENT-CONTRACT-S1`
- `MP377-VOICETERM-EXTRACTION-S1`
- `MP377-AUTHORITY-REVIEWER-MODE-SYMMETRY-S1`
- `MP377-SESSION-LIVENESS-WATCHDOG-S1`
- `MP377-AGENT-LOOP-BILATERAL-PROTOCOL-S1`
- `MP377-PUSH-BASED-EVENTBUS-SUBSTRATE-S1`

Required packet-binding citations:

- `PKT-BIND-REV-PKT-2619`
- `PKT-BIND-REV-PKT-2725`
- `PKT-BIND-REV-PKT-3373`
- `PKT-BIND-REV-PKT-3402`
- `PKT-BIND-REV-PKT-3471`
- `PKT-BIND-REV-PKT-3496`
- `PKT-BIND-REV-PKT-3504`

Evidence refs: `codesmells.md#smell-054`, `packet:rev_pkt_3608`,
`architecture-agent:019e1410-7404-7c81-9dd0-d667f4766b8b`,
`architecture-agent:019e1410-73d7-78f3-82f6-926de3b099c5`,
`architecture-agent:019e1413-3af0-79a0-9f86-d75a2afcc850`,
`dev/guides/SYSTEM_MAP.md`, `System_Connection_Flowchart.md`,
and `dev/scripts/devctl/review_channel/packet_contract.py`.

Rows to ingest from this plan:

- `MP377-P0-T08F` Amend with codesmell #054: role-oriented packet inbox proof must show packets remain visible when the delivery/provider label changes and when a query supplies only `target_role` or `target_session_id`.
- `MP377-P0-ROLE-MATRIX-DOGFOOD-S1` Amend with codesmell #054: dogfood must prove multiple AI providers can occupy the same typed role lane without changing authority code.
- `MP377-P0-ROLE-MATRIX-ROSTER-S1` Amend with codesmell #054: role/capability roster, not provider label, owns runtime lane authority and selected executor identity.
- `MP377-P0-ROLE-MATRIX-ACK-S1` Amend with codesmell #054: acknowledgement and consumption must bind to typed role/session scope rather than a provider-only queue.
- `MP377-P0-RC-PAIR-S1` Amend with codesmell #054: remote-control pairing must route through typed lane/session authority and keep provider defaults inside repo-pack compatibility metadata.
- `MP377-P0-T22AN-AM` Amend with codesmell #054: implementation and blocker packet targets must carry typed lane scope and must not require a concrete provider name to be actionable.
- `MP377-P0-T22AN-AM-S1` Amend with codesmell #054: lane watcher lease keys must be role/session/elected-executor keys, not provider watch keys.
- `MP377-P0-T22AN-V` Amend with codesmell #054: unified attention authority must count and wake typed lanes even when delivery labels are absent, swapped, or non-default.
- `MP377-P0-T22AN-X` Amend with codesmell #054: `/develop` packet-aware output must emit typed role/session lane commands instead of provider-first `--target` and `--actor` forms.
- `MP377-COLLABORATION-MODE-TOPOLOGY-S1` Amend with codesmell #054: topology snapshots must represent implementer, reviewer, watcher, dashboard, architect, tester, and operator lanes independently from provider labels.
- `MP377-TOPOLOGY-REDUCER-DESIGN-S1` Amend with codesmell #054: the topology reducer must expose provider/delivery labels only as metadata under typed lane authority.
- `MP377-MULTI-SESSION-TARGET-DISAMBIGUATION-S1` Amend with codesmell #054: provider-only target selection is insufficient when multiple sessions or arbitrary AI providers can serve the same role.
- `MP377-PACKET-MATCHING-ROLE-SCOPE-S1` Amend with codesmell #054: review-channel inbox, watch, status, and packet matching helpers must accept role/session scope without a provider target.
- `MP377-PROJECTION-RETIREMENT-CONTRACT-S1` Amend with codesmell #054: bridge, dashboard, and generated provider-specific fields must be declared projection-only compatibility output.
- `MP377-VOICETERM-EXTRACTION-S1` Amend with codesmell #054: portable governance paths must not encode VoiceTerm or provider names as runtime authority.
- `MP377-AUTHORITY-REVIEWER-MODE-SYMMETRY-S1` Amend with codesmell #054: reviewer/implementer defaults must be symmetric typed role assignments, not fixed provider assumptions.
- `MP377-SESSION-LIVENESS-WATCHDOG-S1` Amend with codesmell #054: liveness and wake evidence must resolve stale typed lanes by role/session/elected executor rather than by provider-only target.
- `MP377-AGENT-LOOP-BILATERAL-PROTOCOL-S1` Amend with codesmell #054: the bilateral protocol must require provider-neutral lane resumption evidence for any AI/runtime pair.
- `MP377-PUSH-BASED-EVENTBUS-SUBSTRATE-S1` Amend with codesmell #054: packet delivery events must wake/recompute typed lane subscribers and not provider-name subscribers only.

Aspirational until implemented by the named phases:

```bash
python3 dev/scripts/checks/check_provider_neutral_lane_routing.py --format json
python3 dev/scripts/checks/check_projection_provider_fields_display_only.py --format json
python3 dev/scripts/checks/check_typed_lane_wake_controller.py --format json
```
