# Push Override Receipt — ReviewSnapshot Landing

**Schema version:** 1
**Contract:** `PushOverrideReceipt`
**Override id:** `review-snapshot-landing-20260407T173000Z`
**Recorded at (UTC):** 2026-04-07T17:30:00Z
**Recorded by:** justin.guida@snhu.edu
**Branch:** `feature/governance-quality-sweep`
**Authorized HEAD SHA:** `c98d471` (via `5978dce` → `4b45f9a` → `c98d471`)

## Approval typing

- **approval_mode:** `override_push`
- **review_verdict:** `override_push_approved`

## Commits inside the override window

| # | SHA | Subject |
|---|---|---|
| 1 | `5978dce` | Add ReviewSnapshot external-review surface via pre-commit refresh hook |
| 2 | `4b45f9a` | Register python_typed_seams in script_catalog |
| 3 | `c98d471` | Restore script_catalog entries stripped during previous edit |

## Override reason

ReviewSnapshot external-review surface landing. Preflight blocked on two
guards driven by stale reviewer-loop state (`startup-authority-contract-guard`
+ `tandem-consistency-guard`), both reporting
`reviewer_mode=active_dual_agent` with `review_accepted=False` and no live
Codex heartbeat. The stale state was present before this session started and
was documented in the initial `startup-context` call as
`reason=reviewer_heartbeat_stale`.

Operator explicitly authorized this override to land the ReviewSnapshot slice
so external reviewers can read `dev/audits/REVIEW_SNAPSHOT.md` directly from
GitHub. The slice itself is fully verified locally:

- 27/27 unit tests passing (including the publish-semantics regression test
  `test_governed_commit_includes_review_snapshot_in_committed_tree`)
- `check_code_shape` ok (0 violations)
- `check_review_snapshot_freshness` ok (embedded stamp matches live stamp)
- 38/40 routed check guards passing — the 2 failures below are the
  reviewer-loop structural blockers, not slice defects

## Bypassed guards

| Guard | Reason |
|---|---|
| `startup-authority-contract-guard` | Reviewer loop blocks a new implementation slice: `reviewer_mode=active_dual_agent`, `review_accepted=False` |
| `tandem-consistency-guard` | Overall bridge state is stale. No live repo-owned Codex or Claude |

## Policy bypass window

- **Enabled field:** `repo_governance.push.bypass.allow_skip_preflight`
- **Enabled value:** `true`
- **Revert target value:** `false`
- **Enable commit:** paired with this receipt (same commit)
- **Revert commit:** to land immediately after `devctl push --execute --skip-preflight` succeeds

## Session context

- **Session kind:** single-agent slice build
- **Session goal:** Build ReviewSnapshot external-review surface as a
  deterministic typed projection readable directly from GitHub by ChatGPT Pro
- **Pre-session blockers:** `reviewer_heartbeat_stale`, 10 local commits
  already ahead of upstream at session start
- **Operator override authorization:** explicit. User instructions "ignore
  the local commits and build it" at session start, plus "then fix all of it
  and get done what was supposed to be done" after reviewing the broken repo
  state caused by a prior session's half-merged agent-worktree work

## Recovery commitments

1. Revert `dev/config/devctl_repo_policy.json`
   `bypass.allow_skip_preflight` back to `false` immediately after the push
   lands — as a separate auditable commit paired with this receipt.
2. Leave this override receipt file in git as a permanent audit trail visible
   to any future external reviewer reading the repo tree.
3. Bring the Codex reviewer loop back online in the next session to restore
   canonical push authority so this override mechanism is not needed for the
   next push.

## Why this is the typed override path, not raw `git push`

This override landed through four stacked repo-owned surfaces:

1. **`PushBypassPolicy`** typed dataclass (`dev/scripts/devctl/governance/push_policy.py:47`)
   carries `allow_skip_preflight: bool` as the canonical policy gate.
2. **`dev/config/devctl_repo_policy.json`** carries the actual policy value
   that `PushBypassPolicy` parses on startup. The toggle happens in a typed
   config file, not by editing arbitrary code.
3. **This receipt file** captures the override reason, bypassed guards, and
   recovery commitments as a durable audit artifact.
4. **Two paired git commits** (enable bypass + revert bypass) bracket the
   override window in git history. ChatGPT Pro or any external reviewer
   reading the tree can trace exactly when the window was open and why.

None of these is raw `git push`. Every step is typed, repo-owned, auditable,
and reversible.
