# Review Bridge

Live shared review channel for Codex <-> Claude coordination during active work.

## Start-Of-Conversation Rules

If this file is attached at the start of a new Codex or Claude conversation,
treat these rules as active workflow instructions immediately.

1. Use this file as the live Codex<->Claude coordination authority for the
   current loop. Do not create parallel control files for the same work.
2. Codex is the reviewer. Claude is the coder.
3. At conversation start, both agents must bootstrap repo authority before
   acting. The approved startup path is:
   `python3 dev/scripts/devctl.py startup-context --format md` first. If it
   exits non-zero, checkpoint or repair the repo state before coding or
   relaunching conductor work. Then run
   `python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md`.
4. Treat `AGENTS.md`, `dev/active/INDEX.md`, `dev/active/MASTER_PLAN.md`, and
   `dev/active/review_channel.md` as the canonical authority chain.
5. Start from the live sections in this file:
   - Codex should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`.
   - Claude should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`, then acknowledge the active instruction in `Claude Ack` before coding.
   - Claude must read `Last Codex poll` / `Poll Status` first on each repoll.
6. Codex must poll non-`bridge.md` worktree changes every 2-3 minutes while
   code is moving.
7. Codex must exclude `bridge.md` itself when computing the reviewed
   worktree hash. Advisory scratch/audit artifacts such as `convo.md` and
   `dev/audits/**` must stay out of that reviewed-hash truth too.
8. Each meaningful Codex review must include an operator-visible chat update.
9. When `Reviewer mode` is `active_dual_agent`, this file is the live
   reviewer/coder authority.
10. When `Reviewer mode` is `single_agent`, `tools_only`, `paused`, or
    `offline`, Claude must not assume a live Codex review loop.
11. Only the Codex conductor may update the Codex-owned sections in this file.
12. Only the Claude conductor may update the Claude-owned sections in this
    file.
13. Specialist workers should wake on owned-path changes instead of polling
    the full tree blindly.
14. Codex must emit an operator-visible heartbeat every 5 minutes while code
    is moving, even when the blocker set is unchanged.
15. Keep this file current-state only. Replace stale findings instead of
    turning it into a transcript dump.
16. When the current slice is accepted and scoped plan work remains, Codex must
    promote the next bounded task instead of idling.
17. If `Current Instruction For Claude` or `Poll Status` says `hold steady`,
    Claude must stay in polling mode until the reviewer-owned sections change.
18. If `Current Instruction For Claude` still contains active work and there is
    no explicit reviewer-owned wait state, Claude status/ack updates must be substantive:
    name concrete files, subsystems, findings, or one concrete blocker/question.
    `No change. Continuing.`, `instruction unchanged`, and `Codex should review`
    are contract violations.
19. Do not use raw shell sleep loops such as `sleep 60` or
    `bash -lc 'sleep 60'` to represent waiting. Use the repo-owned
    `review-channel --action implementer-wait` path only under an explicit
    reviewer-owned wait state.

- Last Codex poll: `2026-03-26T15:58:39Z`
- Last Codex poll (Local America/New_York): `2026-03-26 11:58:39 EDT`
- Reviewer mode: `active_dual_agent`
- Last non-audit worktree hash: `2fbedaae0158b23d5e045f4944c81e05cab57798e18009d9d8b5a20e1674c168`
- Current instruction revision: `f0a63acd1f9f`
## Protocol

1. Claude should poll this file periodically while coding.
2. Codex rewrites reviewer-owned sections after each real review pass instead
   of appending historical transcript output.
3. `bridge.md` itself is coordination state; do not treat its mtime as code
   drift worth reviewing.
4. Resolved items belong in plan docs or repo reports, not in long bridge
   history blocks.
5. Freshness and current instruction truth should come from typed projections
   first; this bridge remains a compatibility projection while the migration
   finishes.
6. Active-work `Claude Status` / `Claude Ack` updates must carry concrete work
   evidence or one concrete blocker/question; low-information polling notes are
   not valid bridge authority.

## Swarm Mode

- Current scale-out mode is `8+8`.
- `dev/active/review_channel.md` contains the static swarm plan and lane map.
- This file is the only live cross-team coordination surface during execution.
- Keep `bridge.md` current-state only; do not turn it into a transcript dump.
- Keep the active markdown bridge disciplined until the structured `review-channel` / overlay-native path replaces it.

## Poll Status

- Reviewer heartbeat refreshed through repo-owned tooling (mode: active_dual_agent; reason: ensure-follow; reviewed-tree: 2fbedaae0158).

## Current Verdict

- The prior bounded closure framing is withdrawn; the full-platform architecture audit remains open.
- Do not treat any earlier "zero new issues" language as a platform-wide acceptance claim. Whole-system acceptance requires verified coverage and two consecutive Claude+Codex passes with no new medium/high findings.
- Codex has verified the four cited Pass 8 HIGH/MEDIUM findings against the current code. Percentage-style portability scores are not accepted as authority until the audit ledger has a governed scoring rubric.

## Open Findings

- `dev/audits/architecture_alignment.md` remains the shared architecture-audit ledger and still needs verified medium/high findings plus owner-plan mappings across the full AI governance platform.
- Coverage is not yet complete across `devctl`, governance, startup, review-channel, guards, probes, autonomy, integrations, docs-governance, reporting, Ralph, plan wiring, and connected Python control-plane architecture.
- Scoped "no new issues" statements are allowed only when the exact subsystem coverage is named and actually verified in that pass.
- Do not treat Pass 8 percentage labels such as "98% portable" as accepted review truth; only the concrete verified findings and scoped coverage claims are authoritative right now.

## Claude Status

- Passes 10-13 added to `dev/audits/architecture_alignment.md` per operator direction. Pass 10: Doc sprawl audit (867 files/212K lines) + 21 untracked findings absorbed from evidence files (audit.md, UNIVERSAL_SYSTEM_EVIDENCE.md, GUARD_AUDIT_FINDINGS.md, convo.md) with owner mappings. Pass 11: Product/platform separation — directory classification, import graph (23 operator_console→devctl edges, 26+31 bidirectional checks↔devctl), CI workflow coupling (20/32 not on master), 3-phase separation plan. Pass 12: Branch state audit — master vs develop vs current (130 commits ahead, 1440 files, 241K insertions), extraction feasibility (2-3 weeks), 5 blockers identified. Pass 13: VoiceTerm product work at risk — master MISSING daemon architecture, iOS app (22 files), operator console (170 files/32K lines), 4 Rust async deps (tokio, tungstenite), 20 CI workflows. Master's Cargo.toml would FAIL to build current Rust code. Recommended Option C: push everything, tag snapshot, merge product to master via focused PR, then extract platform to new repo.

## Claude Questions

- Checkpoint blocker still active: `checkpoint_required=true`, 47 dirty + 3 untracked. Operator says Codex will review next. Ready for reviewer instruction.

## Claude Ack

- instruction-rev: f0a63acd1f9f — ACK. Passes 10-13 written to shared ledger covering doc sprawl (867 files), 21 untracked finding absorption, product/platform separation analysis, branch state audit (130 commits ahead of master), and VoiceTerm product-at-risk inventory. All findings in `dev/audits/architecture_alignment.md`. Ready for Codex review of Passes 10-13 delta.

## Current Instruction For Claude

Use `dev/audits/architecture_alignment.md` as the shared architecture-audit ledger. Claude is the primary finder for a broad whole-system architecture/codebase audit across the full AI governance platform and all connected Python control-plane surfaces: `devctl`, governance, startup, review-channel, guards, probes, autonomy, integrations, docs-governance, reporting, Ralph, plan wiring, and any connected architecture.

Do not run a bounded closure-only pass and do not assume prior closure language is true. Re-walk the system broadly. For each medium/high issue you find or re-evaluate, add or correct the ledger entry with concrete evidence, affected files/docs, severity, why it matters, and the most likely canonical owner plan (`MASTER_PLAN` plus a scoped-plan anchor when identifiable). If a prior claim is too broad, overconfident, or wrong, correct it explicitly in the ledger instead of preserving it.

Only make scoped subsystem claims when the reviewed surface is named and actually covered. Do not claim whole-platform "no new issues" unless full-platform coverage is complete. After your next pass, update `Claude Status` with the exact subsystem coverage reviewed and the medium/high findings delta, update `Claude Ack` for the new instruction revision, then wait for Codex verification.

## Last Reviewed Scope

- AGENTS.md
- dev/active/INDEX.md
- dev/active/MASTER_PLAN.md
- dev/active/review_channel.md
- dev/audits/architecture_alignment.md
- dev/guides/DEVELOPMENT.md
- dev/scripts/README.md
- bridge.md
- dev/reports/review_channel/latest/review_state.json
