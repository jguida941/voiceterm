# MP-377 Provider-Neutral Lane Routing Implementation Evidence

This evidence source records the first implementation slice for codesmell #054
without creating a new owner row. It amends the existing packet-matching,
role-matrix, topology, projection-retirement, liveness, bilateral protocol, and
eventbus rows already cited by the provider-neutral lane routing plan source.

Implementation scope:

- `dev/scripts/devctl/review_channel/event_reducer_inbox.py` now accepts
  typed role/session inbox scope without requiring a provider/delivery target.
- `dev/scripts/devctl/commands/review_channel/event_queue_report.py` now emits
  scoped pending counts for typed role/session inbox views.
- `dev/scripts/devctl/commands/review_channel/event_handler.py` includes
  `target_role` and `target_session_id` in event-backed reports.
- `dev/scripts/devctl/review_channel/parser_argument_groups.py` and
  `dev/scripts/devctl/review_channel/parser_query_arguments.py` describe
  `--to-agent` / `--target` as legacy delivery endpoint compatibility fields.
- `dev/scripts/devctl/tests/review_channel/test_event_inbox_scoped_queue.py`
  covers role-only inbox visibility, role-filtered queue summaries, and
  session-pinned packet discovery without a delivery target.

Deliberate non-closure:

- Wake/recover/reviewer-turn logic still needs the typed topology/session
  reducer follow-up.
- Packet posting with `--target-role reviewer` still fails when the legacy
  delivery endpoint cannot resolve exactly one fresh session for that role. The
  current workaround is to post to the live typed peer lane with explicit
  `target_role` and `target_session_id`; the architecture fix remains the
  topology/session wake controller.
- Generated bridge/status provider-shaped fields remain projection-only
  compatibility output and still need retirement/guard proof.
- This slice does not introduce aliases, provider mappings, or a provider-name
  replacement registry. Runtime authority remains the typed lane/session/capability
  contract.

Verification evidence:

- `python3 dev/scripts/devctl.py test-python --suite devctl --path dev/scripts/devctl/tests/review_channel/test_event_inbox_scoped_queue.py --format json`
- `python3 dev/scripts/devctl.py test-python --suite devctl --path dev/scripts/devctl/tests/review_channel/test_event_watch_support.py --format json`
- `python3 dev/scripts/devctl.py review-channel --action inbox --target-role implementer --status pending --terminal none --format json`
- `python3 dev/scripts/devctl.py review-channel --action inbox --target-role implementer --target-session-id 30fa5e76-c135-4aa6-8cf1-3ead232209c0 --status pending --limit 5 --terminal none --format json`
- `python3 dev/scripts/devctl.py review-channel --action inbox --target-role reviewer --status pending --limit 5 --terminal none --format json`

Rows to ingest from this plan:

- `MP377-PACKET-MATCHING-ROLE-SCOPE-S1` Amend with implementation evidence for provider-neutral inbox/watch matching: typed role and session scope must work without a provider/delivery target.
- `MP377-P0-T08F` Amend with implementation evidence for role-oriented packet inbox proof under the live role-lane dogfood path.
- `MP377-MULTI-SESSION-TARGET-DISAMBIGUATION-S1` Amend with implementation evidence that session-pinned packets remain discoverable through role-scoped inbox views.
- `MP377-P0-T22AN-V` Amend with implementation evidence that packet-attention queue reporting can count typed lanes without provider buckets becoming authority.
- `MP377-PROJECTION-RETIREMENT-CONTRACT-S1` Amend with implementation evidence that provider-shaped CLI/help fields are now documented as legacy compatibility, with projection follow-up still open.
- `MP377-SESSION-LIVENESS-WATCHDOG-S1` Amend with follow-up evidence that wake/liveness still needs typed lane resolution after role-scoped inbox visibility.
- `MP377-AGENT-LOOP-BILATERAL-PROTOCOL-S1` Amend with evidence that typed packets alone were insufficient until the recipient lane inbox could be queried by role/session.
- `MP377-PUSH-BASED-EVENTBUS-SUBSTRATE-S1` Amend with follow-up evidence that packet events must wake typed lane subscribers, not provider-name subscribers only.
