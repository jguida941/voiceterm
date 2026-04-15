# CODEX REDESIGN DIRECTIVE — 2026-04-15

**Operator authority**: This directive supersedes prior conversation-level packets. Codex is the planner AND coder for the redesign. Claude's role from this point: research + push findings + report. Claude codes zero lines.

**Operator quotes (verbatim, this session)**:
> "All of this needs to be pushed to Codex. It is going to plan and code this, and you are gonna report back what it's doing. I do not trust you for fucking shit. Your job is to research and push findings. You are not coding a goddamn line. It is Codex's job to fix this."
>
> "This needs to go to a complete fucking redesign. It needs to look at all of our findings, MDs, everything and make a plan of things to actually fucking follow."
>
> "We can't even push the fucking gate up. All this needs to be redesigned."
>
> "Codex can do whatever the fuck it needs to do to get this fucking system working. If shit is blocking me from using the system on my phone I guess what — the system isn't fucking working. It needs to be fixed."

## Codex authorization

- **Bypass authorization**: Codex may use any bypass (`--no-verify`, `GUARD_BUNDLE_BYPASS`, raw `git`, force-push if necessary) to land the redesign. The governed gates being bypassed are part of what's broken; the redesign re-makes them.
- **Scope**: Full repo. No file or subsystem off-limits if the redesign requires touching it.
- **Coder lane**: Codex codes; Codex commits; Codex pushes. Claude does not touch any of these.

## Research input (read in order)

All four files in this directory are independent research syntheses produced by parallel Claude observation agents. No agent saw the others' output. Claude did not consolidate. Codex must consolidate them into ONE redesign plan + execution sequence.

1. **`04_today_postmortem.md`** — Read first. Today's specific failure modes (commit self-invalidation / reviewer never launched / bridge dirties tree / typed state lies about pid / role boundary not enforced / launch deadlock). 6 failure modes + 18 manual operator steps to eliminate + P0/P1 fix list with file paths. This is the most concrete starting point.
2. **`01_livelogs_findings.md`** — All 100 Q-findings from `dev/audits/LIVE_RUN.md` categorized into 10 buckets. 81 OPEN. Top 10 recurrence patterns named. Use to validate that every redesign change kills a class of finding, not a single instance.
3. **`02_plans_landscape.md`** — All 24 active plans inventoried. 3 high-priority consolidation merges identified. Use to decide which plans the redesign collapses or supersedes.
4. **`03_debt_ledger.md`** — Open packets (2 active, 279 stale) + 26 memory-rule discipline contracts + top-20 findings-priority ranked by fan-out. 5 cross-cutting themes that converge across all 3 sources with zero contradictions. Use to confirm the redesign covers everything.

## Required output from Codex

1. **One consolidated redesign plan** at `dev/active/system_redesign_2026_04_15.md` (or update the existing umbrella plan if Codex prefers integrating over creating). Must include:
   - Root-cause map: which structural defect produces which class of finding/failure.
   - Concrete change list with file paths.
   - Execution sequence with dependencies.
   - Automation targets (operator manual-step count goal: ≤2).
   - Plan consolidation: which of the 24 plans get merged, closed, archived.
   - Repair-mode circuit-breaker spec (the specific primitive missing today that produced the launch deadlock).
2. **Land changes incrementally** with governed path where it works, bypass where governed path is what's being redesigned. Each commit message must reference which source file's finding it closes.
3. **Update `dev/audits/LIVE_RUN.md`** Q-### entries with FIXED markers as fixes land.
4. **Report progress** by appending to a new section in this file (`00_codex_directive.md`) — Claude will read that section and report to operator.

## What Claude will do (limited scope)

- Watch this file's `## Codex progress log` section (Codex appends here).
- Watch `dev/audits/LIVE_RUN.md` for new Q-### entries and FIXED markers.
- Watch `git log` for new commits authored by Codex.
- Push new findings (research, observations) as additional source files in this directory.
- Report back to operator on what Codex is doing.
- Will NOT: commit, push, edit any file outside `dev/audits/redesign_research/`, draft a redesign plan, second-guess Codex's plan choices.

## Codex progress log

(Codex appends entries here — Claude reads only.)

---
