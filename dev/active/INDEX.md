# Active Docs Index

This file is the canonical registry for `dev/active/*.md`.
Agents must read this file first before loading active planning docs.

## Registry

| Path | Role | Execution authority | MP scope | When agents read |
|---|---|---|---|---|
| `dev/active/MASTER_PLAN.md` | `tracker` | `canonical` | all active MP execution state | always |
| `dev/active/README.md` | `reference` | `reference-only` | active-doc navigation helper (non-tracker) | when scanning `dev/active/` ownership/read-order context |
| `dev/active/theme_upgrade.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-099`, `MP-148..MP-151`, `MP-161..MP-167`, `MP-172..MP-182` | when Theme Studio, overlay visual research, or visual-surface redesign is in scope |
| `dev/active/memory_studio.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-230..MP-255` | only when memory/action/context-pack work is in scope |
| `dev/active/devctl_reporting_upgrade.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-297..MP-300`, `MP-303`, `MP-306` | when improving `devctl` reporting, dashboard outputs, CIHub integration, triage/status workflows, or control-plane collection/verify performance |
| `dev/active/autonomous_control_plane.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-325..MP-338, MP-340` | when implementing autonomous loop hardening, mutation remediation loop orchestration, mobile-control-plane surfaces, autonomy policy gates, or deterministic learning-loop automation |
| `dev/active/review_channel.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-355` | when designing or implementing the shared review channel, dual-agent shared-screen surfaces, reviewer/coder packet flows, overlay-visible Codex/Claude coordination, or the merged markdown-swarm multi-agent cycle |
| `dev/active/host_process_hygiene.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-356` | when tightening host-side process cleanup/audit flows, descendant PTY leak detection, or AI/operator post-test process-hygiene automation |
| `dev/active/continuous_swarm.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-358` | when hardening the continuous local Codex-reviewer / Claude-coder loop, launcher modularization, peer-liveness gating, context-rotation handoff, or the later proof-gated template-extraction path |
| `dev/active/operator_console.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-359` | when implementing or validating the optional VoiceTerm Operator Console thin-wrapper for the review-channel workflow, desktop launch/rollover controls, or operator approval/decision capture over repo-visible artifacts |
| `dev/active/loop_chat_bridge.md` | `runbook` | `supporting` | `MP-338` | when coordinating loop artifact-to-chat suggestion flow, operator handoff updates, or dry-run/live-run loop validation evidence |
| `dev/active/naming_api_cohesion.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-267` | when running naming/API cohesion cleanup across theme/event-loop/status/memory and related tooling surfaces |
| `dev/active/ide_provider_modularization.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-346`, `MP-354` | when modularizing active host IDE adapters (`cursor`, `jetbrains`, `other`), provider adapters (`codex`, `claude`, `gemini`), and God-file prevention/tooling gates (AntiGravity is deferred until runtime fingerprint evidence exists) |
| `dev/active/pre_release_architecture_audit.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-347`, `MP-349` | when running full-surface pre-release architecture/tooling audits, reviewing consolidated findings, and executing remediation intake |
| `dev/active/audit.md` | `reference` | `reference-only` | `MP-347`, `MP-349` | when reviewing consolidated full-surface findings and sequencing remediation work under the pre-release architecture audit plan |
| `dev/active/move.md` | `reference` | `reference-only` | `MP-347`, `MP-349` | when reviewing raw multi-agent merge transcript evidence that supports `dev/active/audit.md` findings |
| `dev/active/RUST_AUDIT_FINDINGS.md` | `reference` | `reference-only` | bridge pointer to canonical guard-driven remediation scaffold at `dev/reports/audits/RUST_AUDIT_FINDINGS.md` (supporting context, not execution authority) | when AI guard checks fail or guard findings are referenced; follow the bridge to canonical reports path |
| `dev/active/slash_command_standalone.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-352`, `MP-353` | when implementing standalone `/voice` slash command for Codex/Claude without overlay, MCP server extraction, or cross-platform plugin packaging |
| `dev/active/ralph_guardrail_control_plane.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-360..MP-367` | when implementing Ralph AI fix wrapper, cross-architecture guardrail enforcement, guardrail configuration registry, structured guard reports, ralph-status CLI/charts, operator console Ralph dashboard, phone/iOS Ralph metrics, or unified guardrail control surfaces |
| `dev/active/review_probes.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-368..MP-375` | when implementing heuristic review probes, non-blocking risk-hint collectors, or probe-fed AI review triage surfaces |
| `dev/active/portable_code_governance.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-376` | when extending the portable guard/probe engine, defining repo-policy vs engine boundaries, building measurement/eval corpora, exporting the governance stack for off-repo review, or piloting the system on other repositories |
| `dev/active/phase2.md` | `reference` | `reference-only` | bridge pointer to canonical phase-2 companion-platform research context at `dev/deferred/phase2.md` (not active MP execution state) | only when evaluating long-range terminal companion planning; follow the bridge to deferred research |

## Load Order (Agent Bootstrap)

1. Read this file (`dev/active/INDEX.md`).
2. Read `dev/active/MASTER_PLAN.md`.
3. Read only registry docs required by the task class.
4. Do not treat any non-tracker file as execution state authority.

## Process: Add A New `dev/active/*.md` File

1. Create the new markdown file under `dev/active/`.
2. Add one registry row in this file with path, role, authority, MP scope, and read trigger.
3. If the new file introduces execution state, wire that scope into `dev/active/MASTER_PLAN.md`.
4. Update links in `AGENTS.md`, `DEV_INDEX.md`, and `dev/README.md` when discovery/navigation changes.
5. Run sync/governance checks:
   - `python3 dev/scripts/checks/check_active_plan_sync.py`
   - `python3 dev/scripts/devctl.py docs-check --strict-tooling`
   - `python3 dev/scripts/devctl.py hygiene`
6. Commit docs and governance updates in the same change as the new file.
