# Multi-Agent Worktree Execution Runbook

Use this file as the single coordination surface for multi-agent execution.
All agents and the reviewer update this file while work is in progress.

## 1) Goal

Complete the active open `MASTER_PLAN` scope in controlled parallel lanes using
separate git worktrees, explicit stop gates, and reviewer approval tokens.

## 2) Scope For This Cycle

In scope now:

- Theme Studio / visual surface track:
  - `MP-102`
  - `MP-161`, `MP-162`, `MP-172`, `MP-174`
  - `MP-175`, `MP-176`, `MP-179`, `MP-180`, `MP-182`
  - `MP-164`, `MP-165`, `MP-166`
  - `MP-167`, `MP-173`, `MP-177`, `MP-178`, `MP-181`
- Non-theme open items:
  - `MP-091`
  - `MP-226`
  - `MP-088` (keep last; `MASTER_PLAN` marks it deferred until visual sprint complete)
- `MP-161` prerequisite plan hygiene:
  - Promote `MP-103`, `MP-106`, `MP-107`, `MP-108`, `MP-109` from `dev/BACKLOG.md`
    into active execution placement in `dev/active/MASTER_PLAN.md`.

Out of scope in this cycle:

- `MP-015` mutation hardening (handled by separate agent)
- Phase 4 items (`MP-092`..`MP-095`)
- Backlog-only items not explicitly promoted

## 3) Ordered Next Steps (Execute In This Order)

1. Branch alignment (sync `develop` to current `master`).
2. Create worktrees and area branches from `develop`.
3. Execute `AREA-A` and stop for review.
4. Execute `AREA-B` and stop for review.
5. Execute `AREA-C` and stop for review.
6. Execute `AREA-D` and stop for review.
7. Execute `AREA-E` and stop for review.
8. Final integration pass on `develop` (all checks + docs policy + hygiene + CI status).
9. Promote `develop` -> `master` only when green.

No skipping. No parallel advancement across major areas without reviewer token.

## 4) Branch And Worktree Setup

### 4.1 Branch alignment (run once)

```bash
cd /Users/jguida941/testing_upgrade/codex-voice
git fetch origin
git checkout master
git pull --ff-only origin master
git checkout develop
git pull --ff-only origin develop
git merge --ff-only master
git push origin develop
git checkout master
```

### 4.2 Worktree creation

```bash
cd /Users/jguida941/testing_upgrade/codex-voice
git worktree add -b feature/area-a-runtime ../codex-voice-wt-area-a develop
git worktree add -b feature/area-b-capability ../codex-voice-wt-area-b develop
git worktree add -b feature/area-c-studio-core ../codex-voice-wt-area-c develop
git worktree add -b feature/area-d-studio-ga ../codex-voice-wt-area-d develop
git worktree add -b feature/area-e-non-theme ../codex-voice-wt-area-e develop
```

## 5) Area Ownership And Deliverables

Each area has one owner agent. Only that area owner edits its assigned MP lines.

### AREA-A (runtime visual foundation)

MP items:

- `MP-102`
- `MP-161` (including promotion of `MP-103`, `MP-106`, `MP-107`, `MP-108`, `MP-109`)
- `MP-162`
- `MP-172`
- `MP-174`

Required outcomes:

- Runtime surfaces are style-pack routed (`TS-G03`).
- Component registry/state-matrix foundations are in place (`TS-G04`, `TS-G06`).
- `MASTER_PLAN` active execution ordering reflects promoted `MP-103/106/107/108/109`.

Stop token:

- Agent must stop and output exactly: `READY FOR REVIEW AREA-A`

### AREA-B (capability and ecosystem track)

MP items:

- `MP-175`
- `MP-176`
- `MP-179`
- `MP-180`
- `MP-182`

Required outcomes:

- Capability/fallback matrix and dependency compatibility are explicit (`TS-G09`, `TS-G15`).
- Rule profile semantics are deterministic (`TS-G14`).

Stop token:

- Agent must stop and output exactly: `READY FOR REVIEW AREA-B`

### AREA-C (studio core delivery)

MP items:

- `MP-164`
- `MP-165`
- `MP-166`

Required outcomes:

- Dedicated Theme Studio flow and settings/studio ownership migration (`TS-G01`, `TS-G07`, `TS-G08`).

Stop token:

- Agent must stop and output exactly: `READY FOR REVIEW AREA-C`

### AREA-D (studio GA + policy gates)

MP items:

- `MP-167`
- `MP-173`
- `MP-177`
- `MP-178`
- `MP-181`

Required outcomes:

- GA validation bundle and policy gates are green (`TS-G06`, `TS-G09`, `TS-G10`, `TS-G11`, `TS-G12`, `TS-G13`, `TS-G15`).

Stop token:

- Agent must stop and output exactly: `READY FOR REVIEW AREA-D`

### AREA-E (remaining non-theme open items)

MP items:

- `MP-091`
- `MP-226`
- `MP-088` (must remain last)

Required outcomes:

- Transcript history/replay + Claude prompt-occlusion fix + persistent config land with tests/docs parity.
- `MP-226` repro coverage must include:
  - single-command Claude approval prompts
  - local/worktree permission prompts (`Do you want to proceed?`) triggered by cross-worktree reads
  - multi-tool/explore batches where UI reports `+N more tool uses`
  - pass condition: prompt content/actions remain fully readable without HUD overlap/occlusion
  - diagnostic capture fields for each repro:
    - terminal size (`rows x cols`)
    - HUD style/mode (`full`, `minimal`, `hidden`) and border mode
    - task-list block size (visible task lines above prompt)
    - command preview wrap depth (how many lines the command occupies)
    - whether absolute worktree paths are present in prompt text
    - screenshot pair (`before prompt`, `during prompt`)

Stop token:

- Agent must stop and output exactly: `READY FOR REVIEW AREA-E`

## 6) Required Checks Per Area Before Review

Run from repo root unless noted:

```bash
cd /Users/jguida941/testing_upgrade/codex-voice
python3 dev/scripts/devctl.py check --profile ci
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py hygiene
cd /Users/jguida941/testing_upgrade/codex-voice/src
cargo test --bin voiceterm
```

If area touches specialized risk classes, also run required tests from `AGENTS.md`.

## 7) Pull/Rebase Protocol Across Worktrees

Before starting an area:

```bash
git -C /Users/jguida941/testing_upgrade/codex-voice-wt-area-<x> fetch origin
git -C /Users/jguida941/testing_upgrade/codex-voice-wt-area-<x> rebase origin/develop
```

After each area merge to `develop`, all not-yet-merged worktrees must rebase:

```bash
git -C /Users/jguida941/testing_upgrade/codex-voice-wt-area-b fetch origin && git -C /Users/jguida941/testing_upgrade/codex-voice-wt-area-b rebase origin/develop
git -C /Users/jguida941/testing_upgrade/codex-voice-wt-area-c fetch origin && git -C /Users/jguida941/testing_upgrade/codex-voice-wt-area-c rebase origin/develop
git -C /Users/jguida941/testing_upgrade/codex-voice-wt-area-d fetch origin && git -C /Users/jguida941/testing_upgrade/codex-voice-wt-area-d rebase origin/develop
git -C /Users/jguida941/testing_upgrade/codex-voice-wt-area-e fetch origin && git -C /Users/jguida941/testing_upgrade/codex-voice-wt-area-e rebase origin/develop
```

## 8) Master Plan Update Contract

`dev/active/MASTER_PLAN.md` remains canonical. Apply these rules:

1. Only the area owner edits MP lines assigned to that area.
2. `MP-103/106/107/108/109` must be promoted into active placement as part of `AREA-A`.
3. Keep `[ ]` until implementation + verification + reviewer approval are complete.
4. Flip to `[x]` only in the final area-ready commit (or reviewer-directed follow-up commit).
5. Add concise landed evidence on the MP line (same style as existing entries).
6. Do not mark unrelated MP items.

## 9) Reviewer Gate Protocol (Codex Reviewer)

When agent posts `READY FOR REVIEW AREA-X`, reviewer returns one token only:

- `REVIEW-OK AREA-X`
- `REVIEW-CHANGES AREA-X`

Rules:

1. No merge to `develop` without `REVIEW-OK AREA-X`.
2. If `REVIEW-CHANGES AREA-X`, agent patches and stops again.
3. After merge, reviewer records outcome in this file ledger and triggers rebases.

## 10) Merge Sequence

Use this merge order:

1. `AREA-A`
2. `AREA-B`
3. `AREA-C`
4. `AREA-D`
5. `AREA-E`

Rationale:

- Runtime/style foundations before capability matrix gates.
- Capability gates before Studio UX and GA parity.
- Deferred non-theme config item (`MP-088`) remains last.

## 11) Agent Prompt Template (Copy/Paste)

```text
You are assigned AREA-<X> from dev/active/MULTI_AGENT_WORKTREE_RUNBOOK.md.

Hard constraints:
1) Work only on MP items assigned to AREA-<X>.
2) Use only this worktree: <ABSOLUTE_WORKTREE_PATH>
3) Branch is fixed: <BRANCH_NAME>
4) Follow the Master Plan Update Contract in the runbook.
5) Run required verification commands before review.
6) Update the runbook ledger after each push.
7) When done, STOP and output exactly: READY FOR REVIEW AREA-<X>
8) Do not start another area until reviewer returns REVIEW-OK AREA-<X>.
```

## 12) Shared Ledger (Append-Only)

All agents append rows here; reviewer appends decisions.

| UTC | Actor | Area | Worktree | Branch | Commit | MP scope | Verification summary | Status | Reviewer token | Next action |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-02-19T00:00:00Z | reviewer | setup | `n/a` | `n/a` | `n/a` | orchestration | runbook created | ready | pending | launch AREA-A |
| 2026-02-19T16:15:00Z | agent | MP-015 | `n/a` | `master` | `8ac097e6a0fd75f0f5be3e42fd252d86ceb7c137` (stash) | MP-015 event_loop mutation hardening | parked in stash@{0}; do not pop during area cycle | blocked | n/a | resume after area sequence or on dedicated MP-015 branch |

Status values:

- `in-progress`
- `ready-for-review`
- `changes-requested`
- `approved`
- `merged`
- `blocked`

## 13) Worktree Cleanup (After All Areas Merge)

```bash
cd /Users/jguida941/testing_upgrade/codex-voice
git worktree remove ../codex-voice-wt-area-a
git worktree remove ../codex-voice-wt-area-b
git worktree remove ../codex-voice-wt-area-c
git worktree remove ../codex-voice-wt-area-d
git worktree remove ../codex-voice-wt-area-e
git branch -d feature/area-a-runtime
git branch -d feature/area-b-capability
git branch -d feature/area-c-studio-core
git branch -d feature/area-d-studio-ga
git branch -d feature/area-e-non-theme
```
