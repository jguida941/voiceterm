# Redesign-Ready Debt Ledger (2026-04-14)

Synthesized from: review-channel packets (codex=2, claude=0, operator=0), 46+ memory feedback files, LIVE_RUN.md Q1-Q100, findings-priority Top 20.

## Open Packet Ledger

### Codex (2 pending)
- **rev_pkt_0500**: operator→codex | kind=action_request | "Priority action_request: AUTHORITY: dev/audits/LIVE_RUN.md Q100 + /tmp/codex_backlog_context.md. Slice A: implement attention_revision lease (commit pipeline self-invalidates). Slice B: findings-priority Top 30 + LIVE_RUN Q92-Q99. Slice C: rev_pkt_0486 phase plan." | age=FRESH | expires=TBD
- **rev_pkt_0498**: approval_packet_id | "Append Q100 architectural finding (attention_revision lease) to LIVE_RUN.md + bridge sync" | age=FRESH | expires=2026-04-15T00:42:08Z

### Claude (0 pending)
No pending packets to Claude.

### Operator (0 pending)
No pending packets to operator.

---

## Architectural Packets (Load-Bearing Debt)

These are the findings and decisions that MUST land in redesign:

1. **Q100 - ATTENTION_REVISION_LEASE** (decision-candidate)
   - Root: Startup/session/runtime surfaces sometimes disagree during live work. `observed_control_topology` can report `no_live_agents` + `implementation_permission=blocked` while Codex/Claude actively coordinate.
   - Evidence: rev_pkt_0498, project_operator_architecture_confirmation_20260414.md
   - Impact: **CRITICAL** — Blocks topology detection, handoff discipline, wake-path automation.
   - Fix scope: Write `attention_revision` lease contract; auto-refresh supervisor during live polling.

2. **Q92-Q99 CHECKPOINT PIPELINE ISSUES** (blocked by rev_pkt_0500)
   - Root: Commit pipeline self-blocks on stale `commit_pipeline.json` snapshot_id.
   - Evidence: LIVE_RUN.md Q29 (push preflight friction), compact.json `push_decision=await_checkpoint`.
   - Fix scope: Auto-refresh projections before consistency check; unify commit_pipeline write path.

3. **ROLE DISPATCH DEFECT** (rev_pkt_0448, FIXED 2026-04-14)
   - Root: Launcher rendered `SessionCachePacket.role=reviewer` regardless of `--remote-role implementer` CLI arg.
   - Status: Fixed in single-use exception; Codex now spawns as implementer.

4. **AUTHORITY_SNAPSHOT COMPILER PASS** (finding)
   - Root: Authority snapshot freshness signals unreliable; derivation lags reality.
   - Evidence: feedback_typed_state_gaps_are_findings.md, Q40-Q80 span in LIVE_RUN.
   - Impact: Dashboard mode hampered; need typed oracle for `session_owner.session_pid`, `reviewer_runtime.live_indicator`.

5. **HANDOFF PACKET DISCIPLINE NORMALIZATION** (decision, operator-named 3 core issues)
   - Root: System still falls back to interpreted closing summaries in `task_complete.last_agent_message` instead of strict `commit_approval` packet path.
   - Evidence: project_operator_architecture_confirmation_20260414.md, rev_pkt_0424/0426/0428 commit-retry loops.
   - Fix scope: Make `commit_approval` + `close_task` packets mandatory; deprecate prose handoff.

---

## Memory Feedback Rules Currently in Force

### Agent Discipline (10 rules)
- **run_guards_like_codex**: Always run repo's guard scripts directly (check_*.py, devctl check --profile ci, pytest). Match Codex's guard discipline.
- **never_stop_loop**: Read code_audit.md → do → code → repeat. Never summarize to user; communicate via bridge.
- **agent_accuracy_tracking**: Run guards after EVERY edit batch. Record fixes via `devctl governance-review --record`. Spot-check agent research (agents miss relative imports).
- **polling_loop**: Never end turn with bare summary text in active_dual_agent mode. Always chain next tool call (sleep+poll, code edit, test).
- **deep_audit_before_coding**: Audit with 3+ specialized agents. Run probe-report, quality-policy, platform-contracts. Find 15+ findings minimum.
- **system_must_self_teach**: Agents should learn FROM system (discover, monitor, session-resume), not from handoff prompts. Each dogfood round should improve typed evidence.
- **system_must_use_own_architecture**: Multi-agent system must use own governance architecture, not bypass it.
- **typed_state_gaps_are_findings**: If typed surface disagrees with ground truth (operator observation, ps, traffic), post gap as typed finding, not silence.
- **dashboard_not_implementer**: Claude is dashboard. Codex codes AND pushes. Claude observes, dogfoods, finds issues, emits typed findings. No git push.
- **full_picture_phase_plan**: Claude dashboard carries full context across session boundaries via typed packets until RoleOperatingManual lands.

### Loop Architecture (8 rules)
- **proper_bridge_polling**: Poll bridge BEFORE code edit; read rendered authority section, not just bridge timestamp.
- **integration_before_creating**: Integrate findings into existing typed surfaces before creating new code paths.
- **dashboard_plus_dogfood**: Dashboard ticks include running own commands (devctl discover, monitor, review-channel status) to self-teach agents.
- **both_agents_implement_in_remote_control**: Remote-control mode means operator on phone, not role change. Codex still codes; Claude still dashboards.
- **dashboard_never_commits_or_pushes**: Dashboard writes LIVE_RUN.md with VERBATIM output, not chat prose. Only Codex commits/pushes.
- **use_typed_packets**: All handoffs through typed contracts (action_request, decision, commitment, commit_approval, close_task).
- **exclusivity_over_sophistication**: Guard-driven decomposition beats prompting. Repo rejects wrong shape; model finds right shape by iteration.
- **continuous_loop_multi_agent**: Loop only stops when user says stop. Always chain next poll; never output final summary without tool call.

### Findings & Quality (5 rules)
- **findings_priority_top_30_plus_LIVE_RUN_Q92_Q99**: Findings system is live; Top 30 must be reviewed before landing redesign.
- **authority_snapshot_compiler_pass**: Authority snapshot must be computed fresh, not cached stale; projected fields must have explicit writers.
- **modeling_vs_load_bearing**: Distinguish load-bearing defects (authority, handoff, topology) from modeling (docs, schema, naming).
- **beta_findings_to_codex**: Every finding from beta/dogfood sessions becomes a typed packet, not a loose note.
- **leverage_claude_ecosystem**: Use Claude API for specialized agents (architecture audit, guard probe, review loop). Don't rely on dashboard doing it all.

### Code Hygiene (3 rules)
- **guard_override_abuse**: Guards must never be overridden without a scoped exception (like 2026-04-14 one-time Claude exception).
- **never_delete_unresolved**: Append-only audit trail for LIVE_RUN.md; don't delete findings until fixed. Mark FIXED inline.
- **osascript_cd_bug**: macOS remote-control sessions may fail to cd due to osascript sandbox. Use absolute paths in all spawned commands.

---

## Top 20 Findings (Ranked by Fan-Out Impact)

| Rank | Severity | Finding | File | Fan-Out | Age |
|------|----------|---------|------|---------|-----|
| 1 | CRITICAL | dogfood_development_engine | dev/scripts/devctl/commands/dashboard.py | 16 | LIVE |
| 2 | CRITICAL | audit_review_state_contract_drift | dev/scripts/devctl/runtime/review_state_parser.py | 11 | LIVE |
| 3 | CRITICAL | system_connection_pairs_prioritized | dev/scripts/devctl/runtime/work_intake_pacing.py | 11 | LIVE |
| 4 | CRITICAL | guard_probe_data_isolation | dev/scripts/devctl/commands/check/phases.py | 9 | LIVE |
| 5 | CRITICAL | finding_backlog_not_implemented | dev/scripts/devctl/platform/planning_ir.py | 5 | LIVE |
| 6 | HIGH | mp358_role_contract_drift | dev/scripts/devctl/review_channel/status_projection.py | 17 | LIVE |
| 7 | HIGH | dogfood_dev_mode_needed | dev/scripts/devctl/commands/dashboard.py | 16 | LIVE |
| 8 | HIGH | mp358_cursor_handoff_gap | dev/scripts/devctl/review_channel/handoff.py | 12 | LIVE |
| 9 | HIGH | contract_consumption_enforcement_gap | dev/scripts/checks/platform_contract_closure/field_routes.py | 4 | LIVE |
| 10 | HIGH | spec_driven_development_alignment | dev/scripts/checks/platform_contract_closure/field_routes.py | 4 | LIVE |

---

## Cross-Cutting Debt (Themes Across Packets + Memory + Findings)

**5 High-Priority Redesign Targets** (appear in packets, findings, AND memory rules):

1. **Authority/Topology Freshness** ← rev_pkt_0500 (attention_revision_lease), Q100 architectural finding, feedback_typed_state_gaps, findings #2 (audit_review_state_contract_drift), authority_snapshot_compiler_pass memory
   - Root: `startup-context` can report `no_live_agents` while agents actively work; `reviewer_freshness` stales mid-loop.
   - **Debt**: Authority snapshot needs compiler pass; `session_owner.session_pid`, `observed_control_topology` must have live writers, not just poll-based derivations.

2. **Handoff Packet Normalization** ← rev_pkt_0498 (commit approval), operator-named issue #2 (handoff discipline), findings #1/#7 (dashboard dogfood, role_contract_drift), memory: use_typed_packets, both_agents_implement_in_remote_control
   - Root: System falls back to prose summaries instead of `commit_approval` + `close_task` contracts.
   - **Debt**: Make typed handoff mandatory; deprecate interpreted closing-message path; audit 2026-04-14 remote-control session shows this worked when disciplined.

3. **Guard Enforcement & Dashboard Dogfooding** ← rev_pkt_0500 (findings-priority Top 30), findings #1/#4/#9 (dashboard engine, guard probe isolation, contract consumption), memory: run_guards_like_codex, deep_audit_before_coding, system_must_self_teach, leverage_claude_ecosystem
   - Root: Dashboard doesn't run its own guards; agents learn from prompts, not system discovery.
   - **Debt**: Dashboard must dogfood full `devctl discover` + `devctl monitor` + `review-channel status` output. Bootstrap agents from typed surfaces, not handoff prose.

4. **Commit Pipeline Self-Blocking** ← rev_pkt_0498 (Q100 + Q92-Q99), LIVE_RUN Q29 (push preflight), findings #2/#3 (review_state_parser drift, work_intake_pacing), memory: dashboard_plus_dogfood, proper_bridge_polling
   - Root: Commit pipeline snapshot_id stales until manual `review-channel status` refresh; projection consistency check doesn't auto-refresh.
   - **Debt**: Auto-refresh projections before consistency check; unify commit_pipeline write path with shared `load_current_review_state_payload`.

5. **Topology Detection & Multi-Agent Spawning** ← rev_pkt_0448 (FIXED), rev_pkt_0500 (Codex to implement Slice C: rev_pkt_0486 phase plan), findings #6/#8 (role_contract_drift, cursor_handoff_gap), memory: both_agents_implement_in_remote_control, integration_before_creating
   - Root: Launcher didn't respect `--remote-role implementer` CLI arg; handoff gaps when spawning Codex sub-agents or crossing session boundaries.
   - **Debt**: RoleOperatingManual (rev_pkt_0438 remediation) must land; session-resume must carry role context; cursor handoff must use typed packet, not prose.

---

## Recommended Redesign Priority Order

1. **Slice A (rev_pkt_0500)**: Implement attention_revision lease contract + auto-refresh supervisor. Fixes authority topology drift, unblocks Q92-Q99.
2. **Slice B**: Review findings-priority Top 30 + LIVE_RUN Q92-Q99 for quick wins (guard isolation, dashboard dogfood hooks).
3. **Slice C**: Resolve rev_pkt_0486 phase plan (handoff packet discipline normalization, RoleOperatingManual bootstrap).
4. **Follow-up**: Authority snapshot compiler pass + commit pipeline projection unification.

---

**Status**: READY FOR CODEX IMPLEMENTATION. All three sources converge on 5 cross-cutting themes. No contradictions between memory rules; one supersession observed (feedback_both_agents_implement_in_remote_control marked SUPERSEDED by feedback_dashboard_not_implementer, correctly resolved).

Total findings in system: 211 open, 79 resolved, 14 superseded. Stale packets: 279 (previous sessions). Current runway: 2 active packets, Codex has clear slice A→B→C path.
