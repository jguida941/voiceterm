# Remote Control Runtime Closure Plan

**Status**: active  |  **Last updated**: 2026-04-04 | **Owner:** Tooling/control plane/review runtime/dashboard
Execution plan contract: required
This spec is mirrored in `dev/active/MASTER_PLAN.md` under `MP-380..MP-385`.
It closes the remote-control/operator-surface gaps found in the 2026-04-04
architecture review of commits `5bed0fa..4094c39`.

## Scope

Close the remaining phone/remote-control architecture gaps without creating a
second bridge-only authority path. The target is one typed remote-control
runtime that drives reviewer lifecycle, action requests, dashboard projections,
and auto-poll behavior across CLI, bridge compatibility text, and later
phone/operator-console clients.

Out of scope for this tranche: a second VCS executor, a second packet/action
transport, or any new frontend that parses raw bridge markdown once a typed
contract exists.

## Execution Checklist

- [x] Architecture-review the 8 commits ahead of the tracked upstream and map
      the gaps onto existing owner contracts.
- [ ] MP-380 Add one typed operator-interaction mode (`local_terminal` vs
      `remote_control`) and project it through `ProjectGovernance`,
      `StartupContext`, `ReviewState`, and reviewer-runtime surfaces.
- [ ] MP-381 Add one typed `CheckResult` / `ViolationRecord` contract family
      plus one shared renderer/JSON projection for checks, probes,
      governance-review, startup summaries, and dashboard consumers.
- [ ] MP-382 Finish headless session lifecycle closure so launch, recovery,
      and rollover honor typed operator mode, survive non-zero conductor exit,
      and do not recommend `Terminal.app` in remote-control mode.
- [ ] MP-383 Converge bridge `## Action Requests` onto the existing
      `PacketPostRequest(kind="action_request")` event path and keep bridge
      action rows as projection-only compatibility text.
- [ ] MP-384 Make `devctl dashboard` the single operator surface over typed
      review/runtime/check state instead of bridge regex and `format_steps_text`
      parsing.
- [ ] MP-385 Add repo-owned remote-control auto-poll/update cadence for
      reviewer, implementer, and operator-facing surfaces using the same typed
      runtime state and packet queue.

## Data Contracts

1. Operator-mode authority
   - Declared owner: extend `ProjectGovernance.BridgeConfig` with one typed
     operator-interaction mode (`local_terminal` or `remote_control`).
   - Live projection: mirror the same value into `ReviewState` collaboration /
     reviewer-runtime surfaces and `StartupContext.reviewer_gate`.
   - All launch, recovery, dashboard, and auto-poll decisions must read that
     value instead of hardcoding `terminal-app` vs headless behavior.
2. Remote-control mutation/approval transport
   - Authoritative transport: the existing review-channel packet/event path,
     specifically `PacketPostRequest(kind="action_request")` with typed target
     metadata and reduced packet state.
   - `bridge.md` `## Action Requests` remains compatibility projection only. It
     may summarize pending action packets, but it must not become a second
     execution queue or parser-owned authority surface.
3. Check and violation evidence
   - Add one typed `CheckResult` owner for per-check execution state plus one
     typed `ViolationRecord` row for normalized file/line/policy/fix detail.
   - `ViolationRecord` is the only structured violation row rendered by
     dashboard, CI summaries, startup summaries, and compact AI-facing status
     output. `Finding` remains the escalated governance-review record derived
     from a violation when richer review/probe evidence is required.
4. Frontend rule
   - `devctl dashboard`, bridge projections, phone/mobile surfaces, and the
     Operator Console consume typed `ReviewState`, reduced packet state, and
     typed check-result artifacts.
   - Raw bridge regex and `format_steps_text()` scraping are transitional debt
     to remove during `MP-384`, not long-term frontend/runtime contracts.

## Progress Log

- 2026-04-04: Reviewed the 8 commits ahead of
  `origin/feature/governance-quality-sweep`
  (`5bed0fa`, `437008d`, `a534e3e`, `25f458c`, `aa26749`, `8c3f032`,
  `76f5401`, `4094c39`). Accepted the portability/push-truth slices and logged
  four blocking architecture gaps: remote-control state is not typed through
  startup/runtime owners, bridge `Action Requests` creates a second action
  transport, headless lifecycle still stops on non-zero exit and recommends
  `terminal-app`, and dashboard/check-detail surfaces still parse compatibility
  text instead of typed records.
- 2026-04-04: Bound those gaps to `MP-380..MP-385` so the closure path stays
  under the existing `MP-377` owner chain instead of becoming bridge-local
  review lore.
- 2026-04-04: Claude 8-agent audit (AUD-1..AUD-11) mapped to slices:
  - Slice A (MP-380/382): AUD-3 (no typed remote_control/device/available), AUD-6 (zero device awareness), AUD-8 (3 disconnected permission layers), AUD-9 (operator mode-switching)
  - Slice B (MP-383): AUD-4 (post_packet() doesn't exist), AUD-8 (permission routing dispatcher)
  - Slice C (MP-381): AUD-2 (errors to stderr only), AUD-7 (guards format differently, no universal schema)
  - Slice D (MP-384): AUD-1 (session_state_hints never called), AUD-2 (no errors in dashboard), AUD-5 (5/6 quality gates always n/a, pending_packets hardcoded 0)
  - Slice E (MP-385): dependent on A-D
  - AUD-10: full explainability — surface reasoning chains, not summaries
  - AUD-11: build lifecycle hooks, notification channels, permission relay, scheduled tasks as OUR typed contracts (agent-agnostic), not Claude-specific features. External tools are surface adapters, not authority.
  - AUD-12 (DISCOVERABILITY + SYSTEM MAP — 3-AGENT AUDIT COMPLETE):
    - context-graph ALREADY catalogs 69 guards, 25 probes, all commands, plans, guides. 4 modes (bootstrap/query/concept-view/diff). Mermaid + Graphviz output. 360+ saved snapshots. Token-efficient bootstrap (~2250 tokens).
    - SLIM MAP feasible: `startup-context` (82 tok) + `context-graph` top section (400 tok) + `dashboard` now block (150 tok) + `check-router` lane (500 tok) = ~1130 tokens. Gives 80% operational context. `quality-policy` (4663 tok) and `platform-contracts` (7336 tok) stay on-demand.
    - 67 commands, 20+ desktop console views, matplotlib/SVG/mermaid charts, MCP adapter, phone-status — all exist but NONE discoverable to new agents/operators.
    - 5 GAPS in context-graph: (1) named guard/probe roster in bootstrap (shows counts not names), (2) IMPACT TRAVERSAL — changed files → applicable guards (THE missing piece that caused Claude to skip CI), (3) surfaces as first-class graph nodes, (4) per-command argument schemas, (5) guard dependency edges.
    - Codex: add these as Slice F (MP-386) or integrate into existing slices:
  - AUD-12a (AGENT DISPATCH ORACLE): `resolve_agent_dispatch(changed_paths, scan_mode) → AgentDispatchPacket` in `task_router_contract.py`. Composes existing `classify_lane` + `QualityStepSpec.languages` filter + `StartupContext` advisory. Returns named guards, preflight command, context level. This is THE fix for AI agents skipping guards.
  - AUD-12b (VIEW ADAPTER): `devctl view --surface phone --mode dashboard`. ONE snapshot → `RENDERERS[(surface, mode)]` dispatch. `dashboard_render.py` already proves the pattern. Add `("phone", "summary")`, `("ai", "slim")`, `("cli", "flowchart")`. `surface_definitions.py` already names 4 surfaces.
  - AUD-12c (SYSTEM CATALOG): `devctl discover` command. Typed `SystemCatalog` (commands + guards + probes + surfaces + report_types). Builds from existing registries (`QualityStepSpec`, `COMMANDS`, `frontend_surfaces`). Formats: slim (~500 tok for AI), full (markdown), interactive (JSON for PyQt6). `--filter guards-for-file:X` returns deterministic guard list. Feeds context-graph as capability nodes.
  - Design rule: `SystemCatalog` owns WHAT EXISTS (static). `context-graph` owns RELATIONSHIPS (dynamic). `AgentDispatchPacket` owns WHAT TO RUN (derived). `view` owns HOW TO SHOW IT (rendering). Same data, different views.

## Session Resume

- Current status: architecture review is complete and the closure plan is now
  the active authority for this remote-control/runtime tranche.
- Next action: land `MP-380` and `MP-382` together first, because packet,
  dashboard, and auto-poll behavior need one typed operator-mode / headless
  lifecycle contract before they can converge cleanly.
- Context rule: read `dev/guides/AI_GOVERNANCE_PLATFORM.md`,
  `dev/active/ai_governance_platform.md`,
  `dev/active/platform_authority_loop.md`,
  `dev/active/remote_commit_pipeline.md`, and this plan before editing
  review-channel runtime, dashboard, or remote-control surfaces.
- Scope note: the bounded review scope for this session is the 8 commits ahead
  of `@{upstream}`. `git log origin/master..HEAD` currently returns 313 commits
  on this repo and is not the narrow review range for this branch.

## Audit Evidence

- `python3 dev/scripts/devctl.py startup-context --role reviewer --format summary`
- `python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md`
- `python3 dev/scripts/devctl.py platform-contracts --format md`
- `git log --oneline origin/master..HEAD`
- `git log --oneline @{upstream}..HEAD`
- Key contract/code review inputs:
  `dev/scripts/devctl/runtime/project_governance_contract.py`,
  `dev/scripts/devctl/runtime/startup_context.py`,
  `dev/scripts/devctl/runtime/reviewer_runtime_models.py`,
  `dev/scripts/devctl/review_channel/packet_contract.py`,
  `dev/scripts/devctl/review_channel/action_request.py`,
  `dev/scripts/devctl/review_channel/launch_script.py`,
  `dev/scripts/devctl/review_channel/peer_recovery.py`,
  `dev/scripts/devctl/commands/dashboard.py`,
  `dev/scripts/devctl/commands/dashboard_data.py`.
