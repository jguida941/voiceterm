# ReviewSnapshot Architecture Hardening Plan

**Status**: draft — synthesizing audit findings for Codex review  |  **Last updated**: 2026-04-07 | **Owner:** operator + Codex (planned)
**Purpose**: Multi-agent audit of the ReviewSnapshot + install-git-hooks subsystem identifying gaps between the current architecture and a maximally portable, deterministic, typed, load-bearing governance surface. This document is audit intake for the tracked MP-377 / MP-376 owner plans, not canonical execution authority by itself.

## Authority and routing

This file intentionally stays under `dev/audits/`. It is not a governed
`dev/active/` execution plan until a future slice rewrites it onto the full
active-plan contract and registers it in `dev/active/INDEX.md`. Accepted work
must be mirrored into the canonical owner docs before implementation:

| Intake | Canonical owner | Routing rule |
|---|---|---|
| ReviewSnapshot path defaults, `DocPolicy` / `ArtifactRoots` diagnostics, missing roots, policy-load source, and hardcoded verification commands | `dev/active/platform_authority_loop.md` | Treat as MP-377 startup / repo-pack / doc-authority closure. |
| Raw commit gating, pre-commit hook proof, override receipt enforcement, `PushAuthorizationRecord`, additional git hooks, and publication override integrity | `dev/active/remote_commit_pipeline.md` | Treat as MP-377 governed commit/push pipeline closure. |
| Cross-surface consistency, contract registration, schema/version coverage, suggested-command execution, WhyRecord consumers, generated-artifact integrity, MCP / Agent SDK surfaces, and ecosystem adapters | `dev/active/ai_governance_platform.md` | Treat as MP-377 product/runtime contract work, with narrow checklist items in the subordinate owner when implementation starts. |
| Adopter portability matrix, repo-pack distribution, fresh-adopter diagnostics, and cross-repo fixture proof | `dev/active/portable_code_governance.md` | Treat as MP-376 companion proof, with MP-377 blockers routed back to the authority-loop plan. |

`dev/audits/REVIEW_SNAPSHOT.md` is a generated report projection. Do not hand
edit it and do not treat it as a plan; regenerate it with
`python3 dev/scripts/devctl.py review-snapshot --write` when the snapshot must
change.

## Codex handoff summary (read this first)

**What's done and live on GitHub** (branch `feature/governance-quality-sweep`, tip `f9388da`):
- ReviewSnapshot builder, renderer, freshness guard, devctl command (5 commits)
- Pre-commit refresh hook via `governed_executor_phases` (for `devctl vcs.commit`) AND via installable git hook (for raw `git commit`)
- `devctl install-git-hooks` command with worktree-aware install + idempotent + tamper-resistant
- 27 + 12 = 39 unit tests passing
- Typed override chain walked end-to-end (PushBypassPolicy + PushAuthorizationRecord + markdown receipt)
- `dev/audits/REVIEW_SNAPSHOT.md` rendering from typed sources, published on GitHub

**What's open and needs Codex attention**, in priority order:

1. **Tier 1 load-bearing gaps** (6 items) — unify the six-site hardcoded fallback into one resolver, move VoiceTerm literals to repo-pack, close the suggested-commands / WhyRecord / gaps decoration gaps, add ReviewSnapshot to the cross-surface consistency guard, add the raw-git-commit end-to-end regression lock. **Estimated size:** 3 slices, each ~400-600 lines.

2. **Tier 2 adopter portability + diagnostics** (5 items) — policy-load diagnostic, missing-artifact-roots detection, pre-commit-framework conflict detection, devctl install-claude-commands, devctl install-claude-code-hooks. **Estimated size:** 2 slices, each ~300-500 lines.

3. **Tier 3 stronger invariants with strict-xfail locks** (4 items) — make suggested_commands executable, make WhyRecord consumed, make ReviewSnapshot stamp part of cross-surface consistency, make override receipts enforced. **Estimated size:** 4 slices, each ~200-400 lines, each landing with its paired strict-xfail trace.

4. **Tier 4 tamper resistance** (4 items) — HMAC signatures on PushAuthorizationRecord, content-hash anchoring on snapshot freshness, content-hash on managed hook detection, bypass_expires_at_utc auto-revert. **Estimated size:** 2 slices, each ~500-700 lines.

5. **Tier 5 ecosystem integration** (5 items) — MCP server, Agent SDK reviewer daemon, additional git hooks, snapshot history time series, GitHub Actions pre-receive enforcement. **Estimated size:** 5 slices, each a separate MP with its own design doc.

6. **Appendices G–J deep patterns** — snapshot lifecycle as state machine, ContractSpec registration, typed refresh action, packet-based override, typed snapshot diff, Rust-side parity, cross-repo pack distribution, property-based test scaffolding. **Estimated size:** 4 slices over multiple MPs.

**Recommended first Codex slice:** Tier 1.1 (unified path resolver) + Tier 1.6 (raw-git-commit regression lock) together as one commit. That's the smallest closure that makes the existing architecture internally consistent and adds the regression lock this session demonstrated is missing.

**Reading order for Codex:**
1. Executive summary (below)
2. This summary (handoff)
3. Tier 1 findings in detail (Lens 1 and Lens 2 CRITICAL sections)
4. Strict-xfail regression locks section (so the fix shape is clear)
5. Appendix G (deterministic-typed idioms — reinforces why Tier 3 matters)
6. Appendices A, B, C (slash commands, settings.json, Operator Console) when picking up Tier 2 and Tier 5
7. Appendices H, I, J (Rust parity, cross-repo distribution, property tests) as standalone MPs

---


## Executive summary

The newly-landed ReviewSnapshot surface (commits `5978dce` → `f9388da` on `feature/governance-quality-sweep`) successfully established an external-review projection readable from GitHub by ChatGPT Pro. End-to-end proof exists:

- **27/27 unit tests** locking the typed-projection builder and the publish-semantics regression
- **12/12 unit tests** locking the install-git-hooks command (worktree-aware, idempotent, tamper-resistant)
- **Pre-commit refresh hook** proven to auto-stage `dev/audits/REVIEW_SNAPSHOT.md` during raw `git commit` via the Bash tool (verified in `f9388da`)
- **Typed override chain** walked end-to-end for the first time (`PushBypassPolicy` + typed `PushAuthorizationRecord` + markdown receipt + paired commits)

However, a four-lens audit identifies **significant hardening opportunities** grouped into four categories:

| Lens | Critical | High | Medium |
|---|---|---|---|
| Adopter portability | 7 | 2 | 1 |
| Modeled vs load-bearing | 4 | 2 | 5 |
| Security / integrity / tamper resistance | 3 | 4 | 2 |
| Integration seams + test coverage | 2 | 5 | 3 |
| **Total** | **16** | **13** | **11** |

The strongest findings cluster around two root causes: **(1)** hardcoded VoiceTerm-shaped defaults scattered across six resolution sites instead of one canonical path helper, and **(2)** decorative typed fields that flow into rendered markdown but feed zero production decisions — the "modeled truth vs load-bearing truth" failure mode a prior reviewer already named.

The plan also identifies **orthogonal architectural opportunities** not captured by the audit agents: slash commands for Claude Code, settings.json hooks for automatic snapshot refresh at session boundaries, MCP server integration so any agent can query governance state as tool calls, Agent SDK integration for a persistent reviewer-loop daemon, and additional git-hook surfaces (post-commit, post-merge, prepare-commit-msg) that could strengthen the invariant chain.

## Scope

### In scope
- All `dev/scripts/devctl/runtime/review_snapshot_*.py` files
- `dev/scripts/devctl/commands/governance/review_snapshot.py`
- `dev/scripts/devctl/commands/governance/install_git_hooks.py`
- `dev/scripts/checks/check_review_snapshot_freshness.py`
- `dev/config/git_hooks/pre-commit-review-snapshot.sh`
- `dev/scripts/devctl/commands/vcs/governed_executor_phases.py` (pre-commit hook addition)
- `dev/scripts/devctl/runtime/project_governance_contract.py` (`ArtifactRoots.review_snapshot_path`)
- Transitively: `ProjectGovernance`, `PushBypassPolicy`, `PushAuthorizationRecord`, `RemoteCommitPipelineContract`

### Out of scope for this plan
- Fixing the stale reviewer loop (separate MP)
- Repairing the 7 orphaned agent worktrees
- Any changes to existing tests outside the ReviewSnapshot subsystem
- Raw `git push` as a fallback (explicitly forbidden by `CLAUDE.md`)

## Methodology

Four parallel `Explore` audit agents were spawned with distinct lenses:

1. **Fresh-adopter portability lens**: walks the code as a brand-new adopter installing codex-voice governance as a dependency on a non-VoiceTerm repo. Returned 7 CRITICAL, 2 HIGH, 1 MEDIUM.
2. **Modeled-vs-load-bearing lens**: identifies fields/contracts/records that are populated but never consumed by a production decision. Returned 4 CRITICAL, 2 HIGH, 5 MEDIUM.
3. **Security / integrity / tamper-resistance lens**: audits the override receipt and generation-stamp chain for forge-ability, bypass-on-bypass, and audit-trail gaps. *(Synthesis below — agent cut short; operator will finalize.)*
4. **Integration seams + test coverage lens**: walks every new seam and reports which ones have invariant tests, which ones don't. *(Synthesis below — agent cut short; operator will finalize.)*

All audits were report-only. No code was edited during the audit phase. This document is the deliverable.

## Findings — Lens 1: Fresh-adopter portability

### CRITICAL

#### portability-voiceterm-hardcoded-cargo-command
- **Where**: `dev/scripts/devctl/runtime/review_snapshot_hints.py:231`
- **Breaks for adopter**: Reviewer hints suggest `cd rust && cargo test --bin voiceterm` as a runtime verification command. Adopter with a different binary name (or no Rust at all) gets nonsensical guidance in the rendered snapshot.
- **Fix**: Move hardcoded command table into repo-pack policy (e.g., `BuildCommands` section on `ProjectGovernance`, or `bundle_overrides.suggested_verification_commands`). Fall back to a minimal universal default: `["python3 dev/scripts/devctl.py check --profile ci"]`.

#### portability-hardcoded-review-snapshot-path-across-six-sites
- **Where**: Six independent sites each carry their own copy of the `"dev/audits/REVIEW_SNAPSHOT.md"` default:
  1. `project_governance_contract.py:184` (dataclass default)
  2. `project_governance_parse.py:88` (parser fallback)
  3. `review_snapshot_refresh.py:156` (refresh fallback)
  4. `review_snapshot.py:304` (builder fallback)
  5. `check_review_snapshot_freshness.py:37` (guard fallback)
  6. `pre-commit-review-snapshot.sh:87` (hook fallback)
- **Breaks for adopter**: Each layer has its own default. An adopter configuring `artifact_roots.review_snapshot_path = "proj/governance/snapshot.md"` must verify that six different code paths all honor the override. If one is missed, the system silently falls back in some paths but not others — snapshot refreshes to one place, CI guard reads another.
- **Fix**: Create a shared resolver `ArtifactRoots.resolve_review_snapshot_path(repo_root, governance, *, default="dev/audits/REVIEW_SNAPSHOT.md")` in the contract module. Every caller invokes this one function. Default lives in exactly one place.

#### portability-pre-commit-hook-hardcodes-devctl-entry-path
- **Where**: `dev/config/git_hooks/pre-commit-review-snapshot.sh:57, 64, 73`
- **Breaks for adopter**: The shell hook calls `python3 dev/scripts/devctl.py`. If an adopter customizes `PathRoots.scripts = "tooling/governance"`, the hook invocation still hardcodes `dev/scripts/devctl.py` and breaks. The hook is not re-templated per adopter — it's copied verbatim.
- **Fix**: During `install-git-hooks`, write a sidecar `.git/hooks/devctl-env.sh` (or `git config --local devctl.entrypoint <path>`) that carries the resolved entry point. The hook sources it before invoking `python3 "$DEVCTL_ENTRYPOINT"`. Adopter's custom layout is captured once at install time.

#### portability-why-extractor-hardcodes-three-dev-paths
- **Where**: `dev/scripts/devctl/runtime/review_snapshot_why.py:22-24`
  ```python
  _MASTER_PLAN_REL = "dev/active/MASTER_PLAN.md"
  _INDEX_REL = "dev/active/INDEX.md"
  _EVOLUTION_REL = "dev/history/ENGINEERING_EVOLUTION.md"
  ```
- **Breaks for adopter**: An adopter with `docs/roadmap.md` and `docs/rationale.md` instead gets an empty Reasoning section because the three hardcoded paths don't match their layout. The module gracefully returns empty tuples when files are missing, so the failure is silent.
- **Fix**: Move the three paths into `DocPolicy` (which already has `tracker_path` and `index_path`). Add `evolution_path` field. Pass the resolved `ProjectGovernance` into `load_plan_index`, `load_evolution_entries`, and `active_mp_summaries_from_master_plan`. Emit a warning in `build_review_snapshot` if any of the three files are missing so the adopter knows they should populate them.

#### portability-governance-log-path-silent-fallback
- **Where**: `review_snapshot.py:304` in `_resolve_governance_log_path`
- **Breaks for adopter**: The governance-review log path defaults to `"dev/reports/governance/finding_reviews.jsonl"` if not configured. No validation that the file actually exists at the resolved path. If the adopter misconfigured, the governance quality signals section is silently empty.
- **Fix**: Add a `path_source` field in the returned payload (`"configured"` vs `"fallback"` vs `"missing"`). Render `"path_source: fallback"` visibly in the snapshot's Quality signals section so the adopter sees they haven't configured the path. Same pattern for probe report and context-graph paths.

#### portability-missing-devctl-repo-policy-json-silent
- **Where**: `dev/scripts/devctl/governance/draft.py:152–155`
- **Breaks for adopter**: When the adopter hasn't created `dev/config/devctl_repo_policy.json`, `scan_repo_governance` silently returns an empty policy. The governance scan reports no error, so the adopter doesn't know they need to configure anything.
- **Fix**: Add a `policy_load_diagnostic` field to `ProjectGovernance` with values `loaded`, `missing`, `empty`, `parse_error`. Surface the diagnostic in every command that calls `scan_repo_governance`. On `install-git-hooks`, check the diagnostic and refuse to install if the policy is missing (with a clear error pointing the user at the config file template).

#### portability-no-artifact-directory-validation
- **Where**: `ArtifactRoots` + `DocPolicy` + `PathRoots` across `ProjectGovernance`
- **Breaks for adopter**: A fresh adopter repo has none of `dev/active/`, `dev/audits/`, `dev/history/`, `dev/guides/`, `dev/reports/`. The snapshot builder gracefully returns empty sections, but the adopter sees a half-populated snapshot without knowing why.
- **Fix**: Add a `missing_artifact_roots: tuple[str, ...]` field to `ProjectGovernance`. Scanner populates it with every expected directory that doesn't exist. `build_review_snapshot` renders this into the Known Gaps section as "Expected artifact directories not found: …" so the adopter has actionable feedback.

### HIGH

#### portability-pre-commit-framework-tool-conflict-silent
- **Where**: `install_git_hooks.py` (no detection)
- **Breaks for adopter**: If the adopter uses the `pre-commit` Python framework (`.pre-commit-config.yaml`), installing the managed hook into `.git/hooks/pre-commit` creates a conflict: the `pre-commit` tool installs its own hook at the same path. Only one wins; the other is silently dropped.
- **Fix**: Detect `.pre-commit-config.yaml` before installing. If found, emit a warning + suggest integrating the snapshot refresh as a custom hook in the YAML. Provide a ready-to-paste YAML snippet in the warning output.

#### portability-freshness-guard-reports-no-path-source
- **Where**: `check_review_snapshot_freshness.py:115-131`
- **Breaks for adopter**: When the guard fails with `snapshot_missing`, the error message says the file is missing but doesn't distinguish "configured path is wrong" from "file legitimately absent". Adopter doesn't know if they misconfigured or if the snapshot wasn't generated.
- **Fix**: Include the resolved path AND the source (`configured` vs `fallback`) in every error the guard emits. `"snapshot_missing: dev/audits/REVIEW_SNAPSHOT.md (fallback default; no repo-pack override found)"`.

### MEDIUM

#### portability-graceful-empty-sections-hide-misconfiguration
- The snapshot builder is *too* tolerant of missing inputs. An adopter with every path misconfigured still gets a rendered file, just with empty sections. This hides configuration errors behind "everything works" UX.
- **Fix**: Add a "Diagnostics" section at the bottom of the rendered snapshot listing which source paths were resolved, which fell back, which were missing entirely. This makes onboarding self-documenting.

## Findings — Lens 2: Modeled vs load-bearing

### CRITICAL: Modeling-only with no production consumer

#### load-bearing-suggested-commands-are-decorative
- `SnapshotReviewerHints.suggested_commands` is populated by `build_suggested_commands()` but *only* rendered as markdown. No production code reads the tuple. The reviewer must manually copy-paste and run each command. This is the exact "modeled but not load-bearing" pattern the prior session's reviewer flagged.
- **Fix**: Add a `devctl review-snapshot --verify-suggested-commands` mode that actually executes each suggested command against the delta and reports which ones passed. Then wire that mode into the CI freshness guard so the suggested commands become part of the push-time gate, not just reviewer hints.

#### load-bearing-why-records-are-markdown-only
- `SnapshotReasoning.commit_why_records` stitches commit → MP → plan doc → evolution entry per commit. Every field is rendered but none is consumed by any downstream decision. The "why" is narrative, not a machine-readable source of truth for anything.
- **Fix**: Add a `check_commit_reasoning_complete.py` guard that fails CI if any commit in the delta has *no* MP reference AND *no* plan-doc link. This makes the extraction load-bearing: a commit without traceability blocks the push.

#### load-bearing-known-gaps-is-pure-markdown
- `SnapshotKnownGaps.gaps` is populated from open governance findings but *only* rendered. The count is shown, but no decision path blocks a push when the count is high.
- **Fix**: Add a repo-pack policy `max_open_governance_findings: int` and a guard that blocks push when `gaps.open_governance_findings > max_open_governance_findings`. Makes the count load-bearing.

#### load-bearing-generation-stamp-only-used-for-comparison
- `SnapshotIdentity.generation_stamp` is computed by `build_surface_snapshot_id()` and embedded in markdown. The freshness guard compares on-disk stamp vs live-recompute. But if both are wrong in the same way, nothing catches it. The stamp is a self-consistency check, not an independent validator.
- **Fix**: Add the ReviewSnapshot's stamp to the cross-surface consistency audit (`check_review_surface_consistency.py`). When startup_context, review_state, commit_pipeline, and bridge_poll all carry the same `snapshot_id`, ReviewSnapshot must align too or the consistency check fails.

### HIGH: Partially load-bearing (one consumer, fragile)

#### load-bearing-risk-addons-detected-but-only-suggested
- `SnapshotDelta.risk_addons_triggered` is detected by `detect_risk_addons()` based on path globs. It's both rendered AND fed into `build_suggested_commands`, but since the suggested commands are decorative (see above), the risk detection ultimately has no teeth.
- **Fix**: Same as suggested-commands fix — make the suggested commands executable so risk addons trigger real checks.

#### load-bearing-review-snapshot-outside-cross-surface-consistency
- The cross-surface consistency guard aligns `startup_context`, `review_state`, `compact`, `commit_pipeline`, `bridge_poll`, `turn_authority`. ReviewSnapshot has its own generation_stamp but is absent from this guard. A stamp drift between ReviewSnapshot and the rest of the typed state is invisible.
- **Fix**: Extend `check_review_surface_consistency.py` to pull the ReviewSnapshot stamp (via a helper that reads the file's front-matter) and include it in the alignment check.

## Findings — Lens 3: Security / integrity / tamper resistance

### CRITICAL

#### integrity-override-receipt-not-enforced
- The override receipt directory `dev/audits/push_override_receipts/` contains markdown files that *document* an override happened. But no code reads the directory before accepting an override push. A malicious or careless override can happen with zero receipt file present — the receipt is purely courtesy documentation.
- **Fix**: Make the override path in `publication_authorization_decision` validate that a receipt file exists matching the authorized_head_sha AND the receipt contains the required fields (override_id, approval_mode, approved_by, override_reason). Without a matching receipt, the override is refused. Turns documentation into enforcement.

#### integrity-managed-marker-is-string-not-signature
- `install_git_hooks.py:28` uses a plain string `"devctl-install-git-hooks: managed hook"` to detect "managed" hooks. Anyone can copy the marker into any arbitrary hook body to bypass the overwrite protection. The marker is a courtesy, not a signature.
- **Fix**: Upgrade to a stronger detection: embed a content-hash of the template file in the hook header as a `# managed-hook-sha256: <hex>` line; `current_install_status` recomputes the template hash and compares. Editing the hook body to spoof a marker won't match the hash. Not cryptographically secure but raises the bar significantly.

#### integrity-freshness-guard-can-be-bypassed-by-hand-edit
- `check_review_snapshot_freshness.py` compares the embedded HEAD/stamp in the file against live git. If someone manually edits `dev/audits/REVIEW_SNAPSHOT.md` to carry a matching embedded HEAD + a hand-computed stamp, the guard passes even if the content is fabricated.
- **Fix**: Add content-hash anchoring. The generation stamp computation should include a hash of the entire file body except the stamp line itself. Editing the body without recomputing the stamp produces a mismatch. `check_review_snapshot_freshness.py` recomputes and compares.

### HIGH

#### integrity-typed-authorization-record-no-integrity-check
- The `PushAuthorizationRecord` persisted to `dev/reports/review_channel/latest/commit_pipeline.json` is an untyped JSON blob on disk. Anyone with write access to the repo can hand-craft a file with `approval_mode="override_push"` and a valid-looking structure. No signature, no HMAC, no chain-of-custody.
- **Fix**: Add a `record_signature: str` field to `PushAuthorizationRecord` computed as HMAC-SHA256 over the serialized record body, keyed by a per-repo secret from `dev/config/devctl_repo_policy.json` (never committed — added to `.gitignore`). Validation on read: recompute HMAC, compare. Raises the bar for tampering substantially.

#### integrity-override-window-not-time-bounded
- The `allow_skip_preflight: true` state can remain in the repo-policy JSON indefinitely if someone forgets to revert it. Nothing enforces that the window closes within a certain time after opening.
- **Fix**: Add a `bypass_expires_at_utc` field to `PushBypassPolicy`. When `allow_skip_preflight` is set to `true`, the expiration timestamp must be within 24h. The push path refuses `--skip-preflight` if the expiration has passed. Auto-reverts the flag when any future `devctl` command detects expiration.

#### integrity-env-opt-out-too-permissive
- The `DEVCTL_NO_REVIEW_SNAPSHOT_REFRESH=1` opt-out in the pre-commit hook is honest but broad. A developer who sets it to "debug" a flaky commit then forgets leaves the hook silently disabled for all future commits in that shell session.
- **Fix**: Log a warning to stderr every time the opt-out is honored, naming the commit SHA that's about to land without refresh. Raises the signal without blocking the workflow.

#### integrity-git-hook-not-verified-on-each-commit
- After `install-git-hooks` runs, the hook file sits in `.git/hooks/pre-commit` forever. If it's deleted or corrupted, subsequent commits silently run without the refresh. Nothing verifies the hook is still present and correct on each use.
- **Fix**: Add `check_git_hooks_installed.py` to the routed CI bundle (bundle.tooling). Fails CI if the managed pre-commit hook is absent on the developer's clone that attempted the push. Pair with `devctl install-git-hooks --check` in `CLAUDE.md` bootstrap.

### MEDIUM

#### integrity-override-receipt-directory-not-restricted
- The override receipt directory is world-writable by any repo committer. Anyone can drop a forged receipt. Low severity because git history tracks who added the file.
- **Fix**: Nothing at the filesystem layer (git is the audit trail), but the `install-git-hooks` tool could also install a pre-receive hook that validates override receipts have valid signatures before accepting a push. Full server-side enforcement.

#### integrity-snapshot-commit-not-required-for-push
- Even with the pre-commit hook installed, someone could `git commit --no-verify` to skip it. The snapshot in the committed tree would be stale but the commit would still be pushable.
- **Fix**: `check_review_snapshot_freshness.py` already catches this in CI, so the push gate closes it. But document this path explicitly in `CLAUDE.md` so developers know `--no-verify` bypasses the local hook while CI catches the drift.

## Findings — Lens 4: Integration seams + test coverage

### CRITICAL

#### coverage-no-test-for-raw-git-commit-hook-firing
- `test_governed_commit_includes_review_snapshot_in_committed_tree` proves the governed-executor pre-commit hook fires. But there's **no test** proving the `.git/hooks/pre-commit` script actually fires on raw `git commit` and stages the snapshot. Today the proof is only that `f9388da` happens to show it working — no regression lock.
- **Fix**: New test `test_install_git_hooks_fires_on_raw_git_commit`:
  1. Spin up tmp_path git repo
  2. Install the hook via the install command
  3. Create a fake `dev/scripts/devctl.py` that writes a known string to the snapshot file
  4. Make a file change
  5. Run `subprocess.run(["git", "commit", "-m", "test"])`
  6. Assert the committed tree contains the known string (proving the hook ran and staged)

#### coverage-install-git-hooks-does-not-cover-linked-worktree-install-path
- The resolver function has a test. But the *install* flow hasn't been exercised against a real linked-worktree layout — `shutil.copy2` could behave differently when the target is through an indirect path.
- **Fix**: Extend test to actually exercise `run(Namespace(...))` against a `_make_linked_worktree` fixture and verify the hook lands in the right location.

### HIGH

#### coverage-portability-resolver-has-no-integration-test
- Multiple files (six) fall back to the hardcoded default. No test asserts all six agree when governance is configured OR when it isn't.
- **Fix**: `test_review_snapshot_path_resolves_consistently_across_all_six_sites` — parameterize across all resolver call sites, assert they return the same path given the same governance input.

#### coverage-no-test-for-pre-commit-skip-during-rebase
- The hook has logic to bail out during rebase/merge/cherry-pick/bisect. No test covers this logic.
- **Fix**: `test_hook_bails_out_during_git_rebase` using a tmp_path with `.git/REBASE_HEAD` touched.

#### coverage-no-test-for-opt-out-env-vars
- `DEVCTL_NO_REVIEW_SNAPSHOT_REFRESH` and `DEVCTL_NO_ARTIFACT_WRITES` are claimed to work. No test exercises them.
- **Fix**: Two tests that set the env var and assert the hook exits 0 without writing.

#### coverage-governed-executor-hook-not-tested-with-foreign-refresh-failures
- `refresh_and_stage_review_snapshot` returns warnings instead of raising. The governed executor phases module folds those warnings into `ActionResult.warnings`. No test asserts the warning pathway actually propagates.
- **Fix**: `test_governed_commit_folds_refresh_warnings_into_action_result` — stub the refresh to return a warning, assert the commit succeeds but `ActionResult.warnings` contains the message.

#### coverage-cross-surface-consistency-missing-review-snapshot
- `check_review_surface_consistency.py` doesn't include ReviewSnapshot in its audit. No test asserts the inclusion.
- **Fix**: After adding ReviewSnapshot to the consistency check, add a test that drifts the ReviewSnapshot stamp and asserts the consistency guard fails.

### MEDIUM

#### coverage-snapshot-renderer-has-no-golden-file-test
- The renderer emits markdown. No test asserts the output matches a golden file. A regression that changes the section order or removes a field would pass unit tests but corrupt the reviewer-facing contract.
- **Fix**: Golden-file test with a fixed fixture input producing a fixed markdown output. Update the golden when the shape legitimately changes.

## Additional architecture opportunities (beyond the audit lenses)

### Slash commands for Claude Code

Slash commands (`.claude/commands/*.md`) are prompts triggered by `/<name>` in the Claude Code CLI. They can encapsulate the full typed-governance workflow so developers (and future Claude sessions) don't have to remember the command shape. Each is a markdown file with frontmatter and a prompt body.

Concrete commands to build:

| Command | Scope | What it does |
|---|---|---|
| `/review-snapshot` | project | Runs `devctl review-snapshot --write --format terminal` and summarizes what changed in the refreshed file. Shows the new generation stamp and delta. |
| `/governance-state` | project | Runs `devctl startup-context --format summary` + `devctl governance-review --format md` + `devctl probe-report --format md` and synthesizes a one-screen governance readout. |
| `/commit-governed <msg>` | project | Launches the full `devctl vcs.stage` → guard bundle → approval → `devctl vcs.commit` flow with the given message, instead of raw `git commit`. Forces the governed path. |
| `/push-with-receipt` | project | Walks the operator through building a typed override receipt before running `devctl push --execute --skip-preflight`. Stops if the override window isn't explicitly opened. |
| `/install-governance` | project | First-time adopter setup: runs `devctl install-git-hooks`, verifies `devctl_repo_policy.json` is present, creates missing artifact directories, runs a first `devctl review-snapshot --write`. |
| `/audit-freshness` | project | Runs the freshness guard + cross-surface consistency check + code_shape guard in one command. Returns a go/no-go verdict. |
| `/verify-hook` | project | Runs `devctl install-git-hooks --check` + smoke-tests the hook by touching a fake file and running `git commit --dry-run` with the opt-out disabled. |
| `/reviewer-heartbeat` | project | Refreshes the Codex reviewer heartbeat via `devctl review-channel --action reviewer-heartbeat` when the loop is stale. |
| `/session-start` | user | Runs the `CLAUDE.md` bootstrap sequence (`startup-context`, `context-graph --mode bootstrap`, `quality-policy`). Used at the start of every session so no Claude session has to remember. |
| `/session-end` | user | Runs the post-session closeout: freshness guard, push decision, summary of what landed. |

**Why this matters architecturally**: slash commands are *compiled workflows*. They turn operator discipline into repo-owned artifacts. The commands themselves can be committed to the repo (`.claude/commands/`) so every adopter gets the same set. Combined with settings.json hooks (see below), they close the loop from "discipline" to "mechanism".

**Implementation slice**: one markdown file per command under `.claude/commands/`, each with a frontmatter header declaring allowed tools + working directory + description. A new `devctl install-claude-commands` devctl command that copies them from the repo template into the user's `.claude/commands/` directory, analogous to `install-git-hooks`. Unit tests verify each command's frontmatter is valid.

### Claude Code settings.json hooks

The Claude Code harness supports typed hooks in `settings.json` that fire on specific events. This is a far cleaner integration than slash commands for automation, because the hooks are enforced by the harness, not by operator discipline.

| Hook event | What to wire |
|---|---|
| `SessionStart` | Auto-run `devctl install-git-hooks --check` and warn if the pre-commit hook isn't installed on the current clone. Prevents "I forgot to run install" from silently breaking the refresh invariant for an entire session. |
| `SessionStart` | Auto-run `devctl startup-context --format summary` and surface the result in the chat buffer. Removes the need for every session to remember to run bootstrap. |
| `PreToolUse` filter on `Bash` tool when command starts with `git commit` | Verify the hook is present; if not, emit a warning and optionally refuse the tool use. Closes the `--no-verify` bypass gap. |
| `PreToolUse` filter on `Bash` tool when command starts with `git push` | Refuse raw `git push`; redirect to `devctl push --execute`. Closes the raw-push forbidden-fallback escape hatch. |
| `PostToolUse` filter on `Bash` tool matching `git commit` | Auto-run `devctl review-snapshot --check` and warn if the snapshot didn't refresh. Catches the case where someone set `DEVCTL_NO_REVIEW_SNAPSHOT_REFRESH=1` and forgot to unset it. |
| `Stop` | Auto-run the freshness guard + governance-review and report any drift before the session ends. Final checkpoint. |

**Implementation slice**: a new `devctl install-claude-code-hooks` devctl command that writes or updates `~/.claude/settings.json` (user scope) or `.claude/settings.json` (project scope) with the typed hook entries. Tests assert the hooks are present and the command shape is valid.

### MCP server integration (tool-surface for any agent)

An MCP (Model Context Protocol) server exposed at `dev/scripts/devctl/mcp_server.py` could turn every `devctl` command into an MCP tool any agent (Claude, Codex, ChatGPT, etc.) can call directly — no shelling out, no CLI parsing, typed inputs and outputs.

Concrete tools to expose:

- `governance_state()` → returns the typed `StartupContext` as a structured dict
- `review_snapshot_current()` → returns the current `ReviewSnapshot.to_dict()`
- `review_snapshot_freshness()` → returns the freshness guard's typed report
- `push_eligibility()` → returns the current `PushDecisionState`
- `commit_governed(staged_paths, message, guard_profile)` → runs the full governed pipeline end-to-end
- `push_governed(skip_preflight, override_reason)` → runs governed push with optional typed override
- `install_hooks()` → runs `devctl install-git-hooks`
- `verify_hooks()` → runs `install-git-hooks --check`

**Why this matters**: it lets ChatGPT Pro and other non-Claude agents participate in the governance loop without needing to parse devctl CLI output or understand the repo layout. They call tools, get structured responses, make decisions. Closes the "only Claude can drive the governance loop" assumption.

**Implementation slice**: new file `dev/scripts/devctl/mcp_server.py` using the Anthropic MCP SDK. Registers each devctl command as an MCP tool. A companion `devctl mcp-server` subcommand starts the server. Operator adds it to their `.claude/mcp_servers.json` or the equivalent for other MCP-aware clients.

### Agent SDK integration (persistent reviewer daemon)

The Anthropic Agent SDK could drive a long-running agent process that acts as the Codex-role reviewer — the reviewer loop that's been stale for this entire session because Codex isn't running.

Concrete design:

- New command `devctl review-daemon --start` launches an Agent SDK worker that polls the review channel every 60 seconds
- Daemon subscribes to `PacketPostRequest` events posted by implementer agents
- For each packet, the daemon runs `devctl check --profile ci`, reads the diff, makes a decision, emits a `DecisionPacket` back through the review channel
- Daemon heartbeat refreshes the reviewer_runtime state so `check_review_channel_bridge` stays green
- On stall/exit, the daemon writes an `implementer_wait` packet so downstream tools know the reviewer is offline

**Why this matters**: eliminates the "need to bring Codex online manually" problem that blocked this whole session's pushes. The reviewer becomes a typed background process, not an interactive terminal.

**Implementation slice**: `dev/scripts/devctl/review_daemon/` package with Agent SDK scaffolding. Agent SDK reads from repo governance state, makes decisions using the existing typed contracts, writes back through the review channel. Operator launches once via `launchd` / `systemd` / similar.

### Additional git hooks beyond pre-commit

The `install-git-hooks` command currently installs only `pre-commit`. There are other git hooks that could close additional gaps:

| Hook | Purpose |
|---|---|
| `prepare-commit-msg` | Inject the current generation stamp into the commit message body automatically, so every commit message carries traceability to its snapshot state. No manual copy-paste. |
| `commit-msg` | Validate the commit message references an MP (`MP-NNN`) or checkpoint marker (`FNN`), rejecting commits without traceability. Makes the MP-reference extraction load-bearing. |
| `post-commit` | Verify the snapshot was committed correctly. If not, log a loud warning. Last line of defense against a broken `pre-commit` hook. |
| `post-merge` | After `git pull` or `git merge`, re-run the freshness guard. Catches cases where pulling in new commits drifts the snapshot relative to the new tree. |
| `pre-push` | Local-client-side equivalent of the governed push preflight. Runs `devctl push --execute --dry-run` locally before the actual push reaches the remote. Redundant with the governed push path but catches developers who accidentally type raw `git push`. |

**Implementation slice**: extend `install-git-hooks` to install any subset of these via `--hooks <list>` flag. Each hook template lives in `dev/config/git_hooks/`.

### Other deterministic-typed-system opportunities

#### Typed commit intent at raw-git-commit level
Currently, `devctl vcs.commit` produces a typed `CommitIntentState`. Raw `git commit` produces nothing typed — the commit just lands in git with a free-form message. A `prepare-commit-msg` hook could parse the staged diff and build a typed `CommitIntentState` inline, writing it to `dev/reports/commit_intents/<sha>.json` as the commit lands. Then every commit on the repo — raw or governed — has a typed intent record downstream tools can consume.

#### Snapshot history as a typed time series
Right now `REVIEW_SNAPSHOT.md` is overwritten on every refresh. A companion `dev/reports/review_snapshot_history/<timestamp>.json` file that archives each generated snapshot creates a typed time series. Future agents can diff snapshots across time to find regressions. Storage is cheap (snapshot is ~40KB), git LFS or a rolling window keeps it bounded.

#### Typed doctor command for ReviewSnapshot
Mirror the existing `review-channel --action doctor` pattern: add `review-snapshot --action doctor` that returns a typed `ReviewSnapshotDoctor` record with health fields (`file_exists`, `stamp_matches_live`, `path_source`, `missing_inputs`, `governance_configured`, etc). Downstream tools query the doctor instead of inferring state from multiple sources.

#### Contract-level schema versioning for ReviewSnapshot
`ReviewSnapshot` has `schema_version=1` but no migration path. A schema bump would break any adopter who already installed v1. Add a `schema_version_compatibility_window` to the contract and a `migrate_review_snapshot(payload, target_version)` helper that routes old payloads through versioned migrators.

#### Webhook for GitHub push events
A GitHub Actions workflow that fires on `push` to `feature/**` and runs `devctl review-snapshot --check` + posts a comment on the associated PR if the snapshot is stale. Closes the "adopter pushes raw git without the local hook installed" case by catching it on the server side.

#### Binary hash check for repo-local generated artifacts
Add a `check_generated_artifact_integrity.py` guard that reads each file under `dev/audits/` and `dev/reports/` with a `.generated-by:` header, recomputes the hash, and fails if any file was modified out-of-band. Makes hand-editing a generated file an audit-blocking action.

## Prioritized plan for Codex

### Tier 1: Load-bearing gaps (must close before calling the slice done)

1. **Unify the review_snapshot_path resolver** — six hardcoded fallback sites collapsed into one `ArtifactRoots.resolve_review_snapshot_path` helper, all six callers updated.
2. **Move hardcoded verification commands to repo-pack policy** — remove `voiceterm`-shaped defaults from `review_snapshot_hints.py:231`.
3. **Move MASTER_PLAN / INDEX / EVOLUTION paths into DocPolicy** — fix `review_snapshot_why.py:22-24`.
4. **Enforce override receipt existence at publication_authorization_decision** — make the receipt load-bearing instead of courtesy.
5. **Add ReviewSnapshot to cross-surface consistency guard** — close the "isolated island" finding.
6. **Add `test_install_git_hooks_fires_on_raw_git_commit` end-to-end regression lock** — the most important missing test.

### Tier 2: Portability + diagnostics (ship alongside Tier 1)

7. **Policy-load diagnostic field** — surface "missing/empty/parse-error" config to every consumer.
8. **Missing artifact roots diagnostic** — detect `dev/active/`, `dev/audits/`, etc. and render into Known Gaps.
9. **Pre-commit framework (tool) conflict detection** in `install-git-hooks`.
10. **`devctl install-claude-commands` command** — ship the slash commands from `.claude/commands/` as a repo-owned adopter install.
11. **`devctl install-claude-code-hooks` command** — ship the `settings.json` hooks as a repo-owned adopter install.

### Tier 3: Stronger invariants (strict-xfail lock + fix)

12. **Strict-xfail: suggested_commands are executable** — fix by adding `--verify-suggested-commands` mode.
13. **Strict-xfail: WhyRecord has a production consumer** — fix by adding `check_commit_reasoning_complete.py`.
14. **Strict-xfail: ReviewSnapshot participates in cross-surface consistency** — fix by extending the consistency guard.
15. **Strict-xfail: override receipt is validated** — fix by the Tier 1 enforcement.

### Tier 4: Tamper resistance (raise the floor)

16. **Add HMAC signature field to `PushAuthorizationRecord`** — with per-repo secret in gitignored config.
17. **Add content-hash anchoring to the freshness guard** — make hand-edits detectable.
18. **Upgrade managed marker to content-hash detection** in `install_git_hooks.py`.
19. **Add `bypass_expires_at_utc` auto-revert** to `PushBypassPolicy`.

### Tier 5: Ecosystem integration (long-term)

20. **MCP server exposing devctl commands as tools** — `dev/scripts/devctl/mcp_server.py`.
21. **Agent SDK reviewer daemon** — eliminates the "Codex must be running manually" blocker.
22. **Additional git hooks**: `prepare-commit-msg`, `commit-msg`, `post-commit`, `post-merge`, `pre-push`.
23. **Snapshot history time series** under `dev/reports/review_snapshot_history/`.
24. **GitHub Actions workflow** that re-runs freshness on every push.

## Strict-xfail regression locks

These are the hard traces that should land alongside the plan so the gaps are caught the moment the fix drops. Follow the `test_work_intake.py::test_alignment_status_is_consumed_by_a_production_decision` pattern.

```python
# 1. ReviewSnapshot path resolution is unified
@pytest.mark.xfail(strict=True, reason="Tier 1.1 — six callers still have their own hardcoded fallback")
def test_review_snapshot_path_resolves_through_single_helper():
    """Every fallback site in the codebase delegates to one helper."""
    # Grep for the literal "dev/audits/REVIEW_SNAPSHOT.md" across
    # the six known sites; assert only ArtifactRoots has it hardcoded.

# 2. Suggested commands are executed, not just rendered
@pytest.mark.xfail(strict=True, reason="Tier 3.12 — suggested_commands still decorative")
def test_suggested_commands_are_executed_by_verify_mode():
    """`devctl review-snapshot --verify-suggested-commands` actually runs them."""

# 3. Override receipt is required for override_push
@pytest.mark.xfail(strict=True, reason="Tier 3.15 — receipts are courtesy-only")
def test_override_push_refused_without_matching_receipt():
    """publication_authorization_decision refuses override_push when no receipt exists."""

# 4. ReviewSnapshot participates in cross-surface consistency
@pytest.mark.xfail(strict=True, reason="Tier 3.14 — ReviewSnapshot not in consistency guard")
def test_cross_surface_consistency_includes_review_snapshot():
    """check_review_surface_consistency detects drift of ReviewSnapshot stamp."""

# 5. Raw git commit triggers the hook end-to-end
@pytest.mark.xfail(strict=True, reason="Tier 1.6 — no regression lock for the raw-git path")
def test_install_git_hooks_fires_on_raw_git_commit():
    """A subprocess.run(['git', 'commit', ...]) against a tmp_path repo actually stages the snapshot."""

# 6. Hooks verified on every session start
@pytest.mark.xfail(strict=True, reason="Tier 2.10 — no SessionStart hook installed yet")
def test_session_start_hook_verifies_git_hooks_installed():
    """Claude Code settings.json has the SessionStart hook calling install-git-hooks --check."""

# 7. MP reference extraction is enforced
@pytest.mark.xfail(strict=True, reason="Tier 3.13 — WhyRecord rendering-only")
def test_commit_without_mp_reference_blocks_push():
    """check_commit_reasoning_complete.py fails when a commit in the delta has no MP ref."""
```

## Notes for Codex

- **Order matters.** Tier 1 must land before Tier 2 because Tier 2's diagnostics depend on Tier 1's unified resolver.
- **Each strict-xfail should land alongside its fix.** Don't land the fix without unlocking the xfail trace.
- **Preserve the test `test_governed_commit_includes_review_snapshot_in_committed_tree`.** It's the canonical proof for the existing governed-executor hook. Don't modify or remove it.
- **The slash commands / settings.json hooks section is not optional.** They are the mechanism that turns operator discipline into repo-owned artifacts. Without them, adopters have to remember to do things manually, which is exactly the gap the ReviewSnapshot slice was supposed to close.
- **Raw `git push` remains forbidden.** Every push must route through `devctl push --execute`. The typed override chain (Tier 4) is the escape hatch, not raw git.

## Appendix A: Concrete slash-command file shapes

Slash commands live in `.claude/commands/*.md` (project scope) or `~/.claude/commands/*.md` (user scope) and follow this shape. Each file defines a single command triggered by `/<filename>` in Claude Code. The slice that ships these should put them under `dev/config/claude_commands/` in the repo, then `devctl install-claude-commands` copies them into the developer's `.claude/commands/` directory.

### `.claude/commands/review-snapshot.md`

```markdown
---
description: Regenerate dev/audits/REVIEW_SNAPSHOT.md and report what changed.
allowed_tools:
  - Bash
argument_hint: "[--dry-run]"
---

Refresh the ReviewSnapshot external-review surface so the GitHub-visible
projection tracks current HEAD.

Run:
  python3 dev/scripts/devctl.py review-snapshot --write --format terminal

Then report:
- the new generation_stamp
- whether the embedded HEAD matches git HEAD
- any warnings from the refresh helper
- the delta vs the previous snapshot

If the worktree is dirty after the refresh, explicitly call it out and
suggest either committing the refresh or running `git stash`.
```

### `.claude/commands/commit-governed.md`

```markdown
---
description: Commit through the governed pipeline instead of raw git commit.
allowed_tools:
  - Bash
  - Read
  - Edit
argument_hint: "<commit message>"
---

Run the full typed commit pipeline rather than raw git commit:

1. Verify the worktree has staged changes via `git status --short`
2. Build a stage action: `devctl vcs.stage` with the current staged paths
3. Run the routed CI guard bundle: `devctl check --profile ci`
4. Submit the commit action: `devctl vcs.commit` with the user's message
5. Verify the pre-commit hook ran by checking git show HEAD for dev/audits/REVIEW_SNAPSHOT.md

Report the commit SHA, the generation_stamp embedded in the committed
snapshot, and any warnings from the pipeline.

**Do not fall back to raw git commit if any step fails.** Stop at the
typed decision surface and report which step failed.
```

### `.claude/commands/push-with-receipt.md`

```markdown
---
description: Walk the operator through a typed override push with full receipt.
allowed_tools:
  - Bash
  - Read
  - Write
  - Edit
argument_hint: "<override reason>"
---

Execute the typed override push chain when the reviewer loop is stale.
This is NOT raw git push — every step lives in repo-owned typed state.

1. Verify the reviewer loop is actually stale. Run:
     devctl review-channel --action status --terminal none --format json
   If the reviewer is live, refuse and point at `devctl push --execute` instead.

2. Open the bypass window: edit dev/config/devctl_repo_policy.json to set
   bypass.allow_skip_preflight: true. Include a bypass_expires_at_utc
   value 1 hour in the future.

3. Write the override receipt at dev/audits/push_override_receipts/
   <ISO8601-UTC>_<slug>.md with the required fields: override_id,
   approval_mode, review_verdict, bypassed_guards, session_context,
   override_reason, recovery_commitments.

4. Commit the bypass + receipt as one atomic commit.

5. Rebuild the typed PushAuthorizationRecord for current HEAD via the
   devctl helper. Persist it through
   dev/reports/review_channel/latest/commit_pipeline.json.

6. Run `devctl push --execute --skip-preflight`. Verify the push lands
   by comparing local and origin HEAD.

7. Immediately flip the bypass back to false and commit the revert.

8. Update the receipt with the published commit range and the close time.

If any step fails, stop and report. Do NOT fall back to raw git push.
```

### `.claude/commands/governance-state.md`

```markdown
---
description: Full one-screen governance readout for the current repo.
allowed_tools:
  - Bash
---

Gather and summarize the current typed governance state:

1. `devctl startup-context --format summary` — action/reason/blockers
2. `devctl review-channel --action status --terminal none --format json`
3. `devctl governance-review --format md`
4. `devctl probe-report --format md`
5. `devctl review-snapshot --format terminal`

Synthesize a single summary with:
- push_decision + next_step_command
- reviewer_mode + freshness + publish_clear
- pipeline state + approval state
- governance findings count (open/fixed/total)
- probe hints count + top 3 by severity
- current ReviewSnapshot generation_stamp vs live
- any stale warnings from startup_advisory

Focus on what blocks the next action, not on successes.
```

### `.claude/commands/install-governance.md`

```markdown
---
description: One-shot adopter onboarding for the codex-voice governance platform.
allowed_tools:
  - Bash
  - Read
  - Write
argument_hint: ""
---

First-time adopter setup. Run once per fresh clone:

1. Verify dev/config/devctl_repo_policy.json exists. If not, copy from
   dev/config/templates/devctl_repo_policy.template.json.

2. Create any missing artifact directories the governance scan expects:
   dev/active/, dev/audits/, dev/history/, dev/guides/, dev/reports/.

3. Install the managed pre-commit hook:
     devctl install-git-hooks

4. Verify the install:
     devctl install-git-hooks --check

5. Install Claude Code slash commands:
     devctl install-claude-commands

6. Install Claude Code settings.json hooks:
     devctl install-claude-code-hooks

7. Run the first snapshot refresh:
     devctl review-snapshot --write

8. Run the cross-surface consistency check to verify nothing is stale:
     python3 dev/scripts/checks/check_review_surface_consistency.py

9. Report the adopter's repo as ready OR list remaining configuration gaps.
```

## Appendix B: Concrete settings.json hook schemas

The Claude Code harness supports typed hooks in `settings.json`. The hook payload shape for each event is documented in the Claude Code guide. Here is a ready-to-paste hook configuration block that `devctl install-claude-code-hooks` would write into `.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 dev/scripts/devctl.py install-git-hooks --check",
            "timeout": 10
          },
          {
            "type": "command",
            "command": "python3 dev/scripts/devctl.py startup-context --format summary",
            "timeout": 15
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 dev/scripts/devctl.py review-snapshot --check-if-command-is-git-commit",
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 dev/scripts/devctl.py review-snapshot --verify-if-command-was-git-commit",
            "timeout": 10
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 dev/scripts/checks/check_review_snapshot_freshness.py",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

Two new `devctl review-snapshot` subflags are needed:
- `--check-if-command-is-git-commit`: reads the pending tool-use command via `stdin` (the hook payload includes the Bash command), detects if it's a `git commit`, and warns if the pre-commit hook is missing. Doesn't block — the hook event is observational unless explicitly refused.
- `--verify-if-command-was-git-commit`: reads the completed command via `stdin`, detects if it was a `git commit`, and recomputes the freshness guard. Logs a warning if the snapshot didn't refresh.

The `Stop` hook runs `check_review_snapshot_freshness.py` so every session closure verifies the snapshot tracks HEAD before the operator walks away.

## Appendix C: Operator Console integration surfaces

Per the project memory, there's already a `PyQt6` Operator Console at `app/operator_console/` that reads `dev/reports/` artifacts and launches `devctl` commands. The ReviewSnapshot surface should integrate with it:

### Existing Operator Console capabilities
- Reads `dev/reports/review_channel/latest/*.json` to show reviewer state
- Launches `devctl` commands via subprocess
- Displays governance findings

### New integration surfaces for ReviewSnapshot

| Panel | What it shows |
|---|---|
| **Snapshot freshness widget** | Current snapshot's generation_stamp vs live; green/yellow/red indicator; one-click "Refresh now" button that runs `devctl review-snapshot --write` |
| **Override receipt manager** | List of `dev/audits/push_override_receipts/*.md` files; shows which are closed (paired revert commit exists) and which are still open; one-click "Close window" button for open receipts |
| **Install-hooks status panel** | Shows current `.git/hooks/pre-commit` state (managed / non_managed / absent); one-click "Install" button |
| **Governance diagnostics panel** | Shows `missing_artifact_roots`, `policy_load_diagnostic`, path_source for each resolved input; surfaces adopter misconfigurations visually |
| **ReviewSnapshot delta preview** | Shows the delta section of the current snapshot as a file-change list; filterable by bundle class and risk addon |

### Implementation slice
- New PyQt6 panel classes under `app/operator_console/panels/review_snapshot/`
- Each panel reads from typed JSON artifacts, not from parsing markdown
- Requires a new `devctl review-snapshot --format json` output mode (already partially present — needs completion)
- Panels subscribe to filesystem events on `dev/audits/REVIEW_SNAPSHOT.md` so they auto-refresh when the file changes

## Appendix D: Deterministic seams inventory

One of the most important invariants in a typed deterministic system is **every source of truth has a typed reader AND a typed writer**, and the reader is the canonical path used by consumers. Seams that break this invariant are the worst kind of drift source.

### Seams that are currently broken or asymmetric

| Seam | Typed writer? | Typed reader? | Gap |
|---|---|---|---|
| `dev/audits/REVIEW_SNAPSHOT.md` | ✅ `review_snapshot_render.py` | 🟡 Partially — freshness guard reads two fields (HEAD + stamp) via regex; nothing reads the full structured body | Need a `review_snapshot_parse.py` that reads the markdown and returns a typed `ReviewSnapshot` — symmetric with the render. |
| `dev/config/devctl_repo_policy.json` | ❌ No typed writer — manually hand-edited | ✅ `project_governance_parse.py` | Need a typed writer so the policy can be programmatically updated without hand-editing JSON (which is fragile). |
| `dev/reports/review_channel/latest/commit_pipeline.json` | ✅ `persist_remote_commit_pipeline_contract` | ✅ `load_remote_commit_pipeline_contract` | Symmetric — no gap. |
| `dev/audits/push_override_receipts/*.md` | ❌ No typed writer — hand-authored in the override flow | ❌ No typed reader | Need a typed `PushOverrideReceipt` contract + writer + reader. Close the symmetry so receipts are load-bearing (see Tier 1.4). |
| `.git/hooks/pre-commit` | ✅ `install_git_hooks.py` | 🟡 Partially — detection via magic marker string | Upgrade the detection to content-hash so the reader is a real integrity check. |
| `dev/config/git_hooks/pre-commit-review-snapshot.sh` | ❌ No typed writer — hand-authored shell | 🟡 Partially — install command copies it verbatim | Consider generating the shell script from a typed template at install time so adopter config can parameterize it. |

### Recommended inventory guard

Add a new check `check_typed_seam_symmetry.py` that for every file matching `dev/audits/**/*.md` and `dev/reports/review_channel/**/*.json` verifies there exists a typed writer AND typed reader in the codebase. Fails CI if a new file appears without symmetric typed handlers.

## Appendix E: Pre-receive server-side enforcement (long-term)

Every hardening opportunity discussed so far is client-side — the developer's local clone must be configured, the adopter must install hooks, the review receipt must exist locally. A truly hardened architecture moves enforcement to the remote: a pre-receive hook on the GitHub side that rejects pushes violating the invariants.

### What server-side enforcement would catch

| Invariant | Client-side | Server-side |
|---|---|---|
| Snapshot matches HEAD | Freshness guard in CI | Pre-receive hook rejects push |
| Override receipt exists for override_push | None (courtesy only) | Pre-receive validates the receipt in the push contents |
| Managed git hook is present | `devctl install-git-hooks --check` | Can't verify (server doesn't see local hooks) |
| Commit messages reference MPs | `commit-msg` hook (not installed yet) | Pre-receive scans push log |
| `bypass.allow_skip_preflight` is false in the tree | Manual revert discipline | Pre-receive fails if the pushed HEAD has it `true` |

### Implementation slice

- GitHub Actions workflow at `.github/workflows/pre-receive-enforcement.yml` that runs on every `push` event
- Workflow runs the same guards the local CI runs, but against the pushed SHA
- If any guard fails, the workflow marks the push red and posts a PR comment explaining what failed
- For the truly hardened case: a self-hosted runner with pre-receive hook semantics that can *reject* a push before it lands. Requires GitHub Enterprise or a self-hosted git frontend.

This is the "move from guard to gate" transition — guards report, gates block.

## Appendix F: Further reading the Codex session should do

- `dev/active/platform_authority_loop.md` — the canonical typed-authority plan that the ReviewSnapshot slice implements one slice of
- `dev/active/remote_commit_pipeline.md` — the design doc for the full governed commit/push pipeline that the pre-commit hook extends
- `dev/active/ai_governance_platform.md` — the portable governance product direction this plan aligns with
- `feedback_modeling_vs_load_bearing.md` in the operator's memory — the original articulation of the failure mode this plan targets
- `dev/guides/AI_GOVERNANCE_PLATFORM.md` — the durable architecture version of the governance model

## Appendix G: Deterministic-typed idioms the subsystem is missing

Your governance stack has a strong set of deterministic typed patterns it already uses — `ContractSpec`, `TypedAction → ActionResult → RunRecord`, generation stamps, surface projections, bridge-as-projection, publication authorization records. The ReviewSnapshot subsystem adopts some of these but misses several that would make it structurally stronger. Each is a concrete slice shape for Codex.

### G.1 — Snapshot lifecycle as a typed state machine

Right now a `ReviewSnapshot` is a point-in-time value. It doesn't have a lifecycle. But thinking about what actually happens:

```
proposed → built → rendered → written → staged → committed → published → audited
```

Each transition is a discrete event. Each could produce a typed record. Today only "built" is typed (via `ReviewSnapshot`); the rest are implicit side effects. A typed `SnapshotLifecycleEvent` contract tracks every transition through a shared `SnapshotJournal` sidecar at `dev/reports/review_snapshot_journal.jsonl`. Then:
- Every consumer can query "when was this snapshot committed?" as a typed lookup
- Diff across snapshots becomes a typed operation
- The reviewer can ask "how long between build and publication for the last 10 snapshots?" as a typed query
- Each transition carries a generation stamp so cross-surface alignment is automatic

Implementation: `dev/scripts/devctl/runtime/snapshot_lifecycle_models.py` with `SnapshotLifecycleEvent` dataclass + `SnapshotJournal` tuple. Every event emitter (builder, renderer, refresh helper, install-hooks command) writes an event. A new `devctl snapshot-journal` command reads the journal.

### G.2 — Contract spec registration for ReviewSnapshot

Per the existing pattern in `dev/scripts/devctl/platform/runtime_state_contract_rows.py`, every typed contract has a `ContractSpec` row registered in the shared platform catalog. This gives the contract:
- `owner_layer` (governance_runtime, governance_commands, etc.)
- `runtime_model` (import path to the dataclass)
- `startup_surface_tokens` (field names visible at startup time)

`ReviewSnapshot` currently has NONE of this — it's a typed contract that lives outside the `ContractSpec` catalog. That means:
- `StartupContext.contract_ownership_map` doesn't know about it
- The cross-surface consistency guard can't find it
- No typed policy governs what fields are required

**Fix**: Add a new `review_snapshot_contract_rows.py` that registers `ReviewSnapshot` in the shared catalog with:
- `contract_id = "ReviewSnapshot"`
- `owner_layer = "governance_runtime"`
- `runtime_model = "dev.scripts.devctl.runtime.review_snapshot_models:ReviewSnapshot"`
- `required_fields = ("identity", "governance_state", "delta", "quality", "architecture", "reviewer_hints", "reasoning", "known_gaps")`
- `startup_surface_tokens = ("generation_stamp", "head_sha", "push_action")`

After registration, `contract_ownership_map` carries it, and the cross-surface consistency guard can audit it alongside `StartupContext`, `ReviewerRuntimeContract`, `RemoteCommitPipelineContract`, etc.

### G.3 — Typed action for snapshot refresh

Today the refresh runs via a direct function call (`refresh_review_snapshot_file`). The rest of the governance system runs through `TypedAction → ActionResult → RunRecord`. Wrapping the refresh in a typed action:

- Creates an audit trail: every refresh is a `RunRecord` with typed inputs (`repo_root`, `previous_head_sha`) and outputs (`snapshot_id`, `generation_stamp`, `warnings`)
- Makes the refresh retryable, replayable, and inspectable
- Lets the governed executor invoke it through the same action-dispatch mechanism as stage/commit/push
- Surfaces refresh failures in the same `ActionResult.warnings` channel every other action uses

**Slice shape**: new `REFRESH_REVIEW_SNAPSHOT_ACTION_ID = "review_snapshot.refresh"` registered in the action contract catalog. `devctl action --id review_snapshot.refresh` dispatches it. The pre-commit hook and the `devctl review-snapshot --write` command both route through the action instead of calling the helper directly.

### G.4 — Packet-based override authorization

The typed override push currently uses a hand-crafted `PushAuthorizationRecord` written directly to the pipeline JSON. The rest of the review channel uses `PacketPostRequest` → `post_packet()` → `ReviewPacketState` flow for reviewer decisions. An override push should follow the same pattern:

1. Operator posts a typed `PacketPostRequest` with `kind="override_decision"` and `body=<override_reason>`
2. Packet flows through the review channel like any other decision
3. `sync_pipeline_push_authorization` picks it up (it already supports `request_kind="override_decision"` at line 129 of `governed_executor_sync.py`) and builds the authorization
4. No hand-crafted JSON files, no direct persistence

**Why this matters**: the hand-crafted approach I used in this session only works because I understand the internal JSON shape. A regular operator shouldn't need that knowledge. Routing through packets means `devctl push --override --reason "..."` does the whole thing via one command, writing a packet and letting the existing sync function build the typed record.

**Slice shape**: new `devctl push --override --reason "<text>" --expires-hours 1` command that posts the packet and runs the push in one step. Receipt file is generated from the packet content automatically so it's never missing.

### G.5 — Snapshot diff as a typed primitive

Today, comparing two snapshots means reading two markdown files and diffing them visually. A typed `SnapshotDiff` primitive would let:
- CI regress on "too many new HIGH probe findings since last snapshot"
- The reviewer ask "what governance findings appeared between my last review and now?"
- An automated agent detect "architecture hotspot X moved from LOW to CRITICAL"
- Alerts fire when the delta exceeds a repo-pack-configured threshold

**Slice shape**: `dev/scripts/devctl/runtime/review_snapshot_diff.py` with `diff_review_snapshots(left, right) -> SnapshotDiff` returning a typed record of added/removed/changed commits, findings, authority surfaces, etc. New `devctl review-snapshot --diff <other>` command.

### G.6 — Bridge-as-projection for ReviewSnapshot

Per the existing architectural principle "typed state is authority, bridge is projection", every external-facing surface should be a read-only projection of typed state. ReviewSnapshot already is a projection (from startup_context + governance-review + probes + context-graph), but it doesn't document that — the markdown file looks like a standalone artifact.

Add a `## Projection source` section to the rendered snapshot listing every typed source it was built from, with the generation stamp from each. This makes the projection relationship explicit and auditable.

## Appendix H: Rust-side governance parity

The governance platform is Python-first today, but VoiceTerm ships a Rust runtime (`rust/src/bin/voiceterm/`). The ReviewSnapshot surface has no integration with the Rust side, which creates an asymmetry:

- Python tooling knows about the governance state
- Rust runtime knows about... nothing from the governance layer

### Opportunities for Rust-side integration

| Opportunity | What it looks like |
|---|---|
| **Rust-readable snapshot JSON** | Emit `dev/audits/REVIEW_SNAPSHOT.json` alongside the markdown. Rust can read it via `serde_json` for any runtime decisions that should depend on governance state. |
| **Rust-side freshness check at startup** | When `voiceterm` binary starts, it can open the snapshot JSON and refuse to run with a warning if the stamp is stale. Analogous to `devctl startup-context` for the Rust side. |
| **Rust-generated probe findings** | Rust probes (`cargo clippy --all-targets`) currently produce findings outside the typed governance review log. Add a `cargo xtask governance-review --record` invocation that pipes Rust findings into `dev/reports/governance/finding_reviews.jsonl` with proper typed fields. Makes Rust findings first-class citizens in the ReviewSnapshot quality section. |
| **Shared contract codegen** | Generate Rust structs from Python dataclasses (or vice versa) so `ReviewSnapshot` has a typed Rust reader without hand-maintenance. Tools like `quicktype`, `prost`, or a custom `dev/scripts/codegen/typed_contracts_to_rust.py` can produce the Rust types from the existing Python dataclasses. |

### Why this matters for deterministic-typed-system hardening

The governance platform's promise is *cross-language* portability. Right now it's Python-only. Adopter repos that are primarily Rust, Go, or other languages have to re-implement the runtime integration in their own language. Providing first-class generated types for at least one other language proves the contract layer is actually language-independent.

**Slice shape**: `dev/scripts/codegen/` package with a `python_dataclass_to_rust.py` script that reads `review_snapshot_models.py` via `inspect` + `typing` and emits `rust/src/governance/review_snapshot.rs`. A `cargo xtask typed-contract-parity` check verifies the generated Rust stays in sync.

## Appendix I: Cross-repo pack distribution model

Right now the "governance platform" is the codex-voice repo itself. An adopter who wants to use it either:
- Forks codex-voice and strips VoiceTerm-specific code (painful, creates divergence)
- Copies `dev/scripts/devctl/` + `dev/config/` into their repo manually (loses updates)
- Runs codex-voice as a subdirectory and symlinks (fragile)

None of these scale. The architecturally correct answer is **repo-pack distribution** — the governance platform ships as a distributable pack that adopter repos install.

### Proposed distribution model

| Layer | What ships | Where it lives |
|---|---|---|
| **Core platform** | `dev/scripts/devctl/` runtime + commands + typed contracts + checks + probes | Published as a PyPI package `devctl-governance-platform` |
| **Adopter pack** | `dev/config/devctl_repo_policy.json` template, hook templates, slash command templates, claude code hook templates | Published as `devctl-governance-adopter-pack` with a `cookiecutter` or similar scaffolding shape |
| **Client-specific glue** | `rust/src/bin/voiceterm/` and anything VoiceTerm-specific | Stays in the VoiceTerm repo; references the platform via requirements file |

### New commands to support this model

- `devctl pack-version` — reports the currently-installed platform version
- `devctl pack-upgrade` — pulls the latest platform package and runs any migration shims
- `devctl pack-install` — first-time install into an empty adopter repo, copies templates and runs the install-git-hooks + install-claude-commands sequence
- `devctl pack-verify` — checks that every file the platform expects is present, correctly configured, and has no adopter-local drift

### Why this matters

Without the distribution model, the "portable AI governance platform" claim in the product thesis is aspirational. Every adopter integration requires manual effort. With the distribution model, a fresh adopter can `pip install devctl-governance-platform && devctl pack-install` and have the full typed surface running in their repo in minutes.

This is the largest slice in the plan and should be scoped as its own MP with its own design doc.

## Appendix J: Deterministic-typed test scaffolding

The test pattern for the ReviewSnapshot slice uses fixture-based unit tests and some integration tests (`test_governed_commit_includes_review_snapshot_in_committed_tree`). But the testing surface has a specific gap: **there's no property-based test harness** for the typed contracts.

### Property-based testing opportunity

Hypothesis (Python) or `proptest` (Rust) can generate random inputs for every dataclass field and verify invariants:

- `ReviewSnapshot.to_dict()` always produces JSON-serialisable output
- `build_surface_snapshot_id()` is deterministic (same input → same output)
- The freshness guard correctly detects drift for any simulated HEAD change
- The refresh helper never writes a dirty worktree when the file is absent
- `classify_bundle_lane()` returns one of the known lane values for any path

**Slice shape**: `dev/scripts/devctl/tests/runtime/test_review_snapshot_properties.py` using `hypothesis` to generate random snapshots and assert invariants. Hundreds of test cases per property, zero hand-crafted fixtures needed.

### Why this matters for deterministic-typed systems

Property-based tests catch the bugs unit tests miss: edge cases at the boundary of the type space. For a governance system claiming typed determinism, this is the highest-value test shape. A single property test that generates 1000 random snapshots and asserts "to_dict → json.loads → equals original" is worth more than 10 hand-written unit tests.

## Appendix K: Observability — what isn't measured

The governance platform writes a lot of typed state, but observability of that state is weak. You can't easily answer questions like:
- How long does a snapshot refresh take, and is that getting worse?
- How many pushes have used the override chain in the last 30 days?
- How often does the CI freshness guard fail, and which kind of drift is most common?
- What's the distribution of lag between pre-commit refresh start and actual git commit?
- Which typed contracts are the most actively mutated per week?

None of these are visible today. A deterministic typed system deserves typed observability.

### What to add

1. **`dev/reports/metrics/snapshot_refresh_timings.jsonl`** — every refresh invocation writes a typed `SnapshotRefreshTiming` record: start/end timestamps, duration_ms, delta_commit_count, governance_findings_count, source_input_sizes, result (success/warning/failure).

2. **`dev/reports/metrics/push_override_events.jsonl`** — every `override_push` action writes a typed `PushOverrideEvent` record: timestamp, operator, override_reason, bypassed_guards, authorized_head_sha, window_open_duration_seconds, was_revert_committed.

3. **`devctl metrics --format md --range 30d`** — a new command that aggregates the jsonl files into a typed report. Categories: governance health (finding counts over time), push patterns (override frequency), performance (snapshot refresh p50/p95/p99), contract mutation rate.

4. **`check_observability_not_stale.py`** — CI guard that fails if the metrics files haven't been written in the last 24h (catches metrics pipeline rot).

### Why this matters

Metrics are the difference between "I think the governance stack is working" and "I can prove it's working and know which parts are regressing." Without typed observability, every claim about system health is anecdotal. The ReviewSnapshot slice is the perfect time to add this because the snapshot itself is already a time-series artifact — adding the metrics jsonl is a modest extension.

### Slice shape

- `dev/scripts/devctl/runtime/metrics_contracts.py` with `SnapshotRefreshTiming`, `PushOverrideEvent`, `CommitMetadataEvent` dataclasses
- `dev/scripts/devctl/runtime/metrics_writer.py` with `append_metric(kind, payload)` helper
- Every hook point that matters (refresh, override, commit, push) calls `append_metric`
- New `devctl metrics` command reads and aggregates
- Unit tests with Hypothesis generating random metric payloads and asserting round-trip

## Appendix L: Determinism proofs

The plan's core promise is "deterministic typed system". That's a claim that needs proof, not just a label. Specific determinism properties to lock with tests:

### L.1 — Refresh determinism

For any given repo state, running `devctl review-snapshot --write` twice in a row should produce byte-identical output.

**Test**: `test_review_snapshot_refresh_is_byte_deterministic` — run the refresh twice, diff the file, assert zero delta except for `generated_at_utc` (which must be excluded because it legitimately changes). Better yet: make `generated_at_utc` derived from a typed fingerprint so even the timestamp is deterministic.

### L.2 — Generation stamp determinism

`build_surface_snapshot_id()` must return identical stamps for identical inputs. This is already asserted in code via `json.dumps(payload, sort_keys=True)`, but there's no test.

**Test**: `test_generation_stamp_is_order_independent` — build two snapshots with the same fields in different insertion orders, assert the stamps match.

### L.3 — Path classification determinism

`classify_bundle_lane()` must return the same class for the same path across runs and across platforms (case-insensitive filesystems could trip it up).

**Test**: `test_classify_bundle_lane_is_case_sensitive_and_deterministic` — parameterize across a known path table, assert identical outputs on repeat.

### L.4 — Render determinism

The markdown renderer must produce identical output for identical input. Section order, bullet order, table column order — all stable.

**Test**: `test_review_snapshot_render_is_byte_deterministic` — golden-file test with a fixed fixture ReviewSnapshot producing a fixed markdown blob.

### L.5 — Serialization round-trip determinism

`snapshot.to_dict()` → `json.dumps` → `json.loads` → [hypothetical] `review_snapshot_from_dict()` → another `to_dict` must produce identical dicts.

**Test**: `test_review_snapshot_json_roundtrip_is_fixed_point` — if a `from_dict` exists (it should — see Appendix D), this is the round-trip property. Otherwise flag as blocked on D.

### Why this matters

A typed deterministic system that fails its determinism tests isn't deterministic. These tests turn the "determinism" label into a contract. They're also the foundation for property-based testing (Appendix J) because Hypothesis can generate random snapshots and assert the determinism properties hold for all inputs.

### Slice shape

`dev/scripts/devctl/tests/runtime/test_review_snapshot_determinism.py` with all five determinism tests. Land them together so the suite proves the whole subsystem is deterministic. Pair with the property-based tests from Appendix J for double coverage.

## Appendix M: Plan-level meta questions for Codex

Questions the plan doesn't answer, where Codex's judgment is needed:

1. **Should the override receipt be a typed contract or stay markdown?** The plan argues for typed validation (Tier 1.4), but typed means losing human readability. A hybrid approach is possible: markdown for humans, typed JSON sidecar for validation. Codex decides.

2. **How aggressive should the content-hash anchoring (Appendix G.6 / Tier 4.2) be?** A simple SHA-256 is cheap but breaks when someone legitimately hand-edits a section. A "stamp + structured sections" approach lets structured fields participate but prose stays mutable. Codex chooses the line.

3. **Should the MCP server (Appendix C) be in the same package as devctl or a separate one?** Same package is easier; separate is cleaner boundary. Codex picks.

4. **Is Rust-side parity (Appendix H) worth the complexity?** Cross-language codegen adds maintenance burden. For a single-language adopter, it's pure overhead. For the platform's "works with any repo" claim, it's mandatory. Codex weighs.

5. **What's the right default `bypass_expires_at_utc` window?** 1 hour is operator-friendly. 5 minutes is hardened. 24 hours is forgiving. Codex picks based on threat model.

6. **Should `devctl install-git-hooks` be opt-in or auto-install on first devctl invocation?** Auto-install is friction-free but surprising. Opt-in is explicit but forgettable. Codex decides the UX balance.

7. **Does the cross-repo pack distribution model (Appendix I) ship as PyPI or as a git submodule?** PyPI is clean but slow to update. Submodule is fast but messy. Codex weighs.

## Appendix N: Anti-patterns to avoid in the Codex slices

A catalog of specific failures the previous session's reviewer caught. These are things the Codex slices should NOT do. If Codex catches itself doing any of these, stop and rewrite.

### N.1 — Landing a closure without a consumer

The exact failure the previous reviewer named as "modeling truth vs load-bearing truth": mark a plan checkbox as done because the field is typed/parsed/rendered, when nothing downstream actually consumes it. **Fix**: every closure commit must include a test that asserts a production decision path reads the field. No test → no close.

### N.2 — Raw `git commit` through Claude's Bash tool

Every commit in this session went through raw `git commit`, which is exactly why the pre-commit refresh hook never fired for any of them. Codex should **route every commit through `devctl vcs.commit`** in the governed commit pipeline. Slash command `/commit-governed` (Appendix A) is the mechanism.

### N.3 — Raw `git push` as a fallback

CLAUDE.md forbids it. The typed override chain (Tier 4) is the escape hatch. If the override chain fails, stop and report — don't fall back.

### N.4 — Silent fallback to hardcoded defaults

Every "fallback to the VoiceTerm-shaped default" is a silent adopter failure. **Fix**: every fallback site must log which source was used (configured vs fallback vs missing) so adopters can see misconfiguration at a glance.

### N.5 — Tests that only test the happy path

Property-based tests (Appendix J) catch the edge cases that fixture-based tests miss. Every new contract should get a property test alongside its unit tests.

### N.6 — Commits that don't reference an MP

Every commit must carry an `MP-NNN` reference in the message body. The WhyRecord extractor depends on this. Future slices should add a `commit-msg` hook that rejects commits without the reference (Tier 5 item).

### N.7 — Amending published commits

Use `git reset --hard` or amend only on local branches. Never on branches that have been pushed to origin. The typed override chain is designed around this — the revert is always a new commit, never an amend.

## Commit history for this plan document

- **2026-04-07 initial**: synthesized 4-agent audit (2 agents returned full findings; 2 were synthesized by operator), prioritized into 5 tiers, drafted 7 strict-xfail regression locks.
- **2026-04-07 expansion**: added Appendix A (concrete slash-command file shapes), Appendix B (settings.json hook schemas), Appendix C (Operator Console integration surfaces), Appendix D (deterministic seams inventory), Appendix E (pre-receive server-side enforcement), Appendix F (further reading pointers).
- **2026-04-07 deep-pass**: added Appendix G (six deterministic-typed idioms the subsystem is missing — lifecycle events, contract spec registration, typed refresh action, packet-based override, typed snapshot diff, bridge-as-projection documentation), Appendix H (Rust-side governance parity including cross-language contract codegen), Appendix I (cross-repo pack distribution model for adopter packages), Appendix J (property-based test scaffolding with Hypothesis).
- **2026-04-07 handoff-and-observability**: added Codex handoff summary at the top so Codex doesn't have to read the whole document to understand priority, Appendix K (observability metrics jsonl pipeline), Appendix L (five determinism proofs with concrete tests), Appendix M (plan-level meta questions that need Codex judgment), Appendix N (anti-patterns to avoid based on failures from the prior session).

---

*This document is living audit intake. Add findings here only as supporting
evidence, and mirror accepted work into the tracked owner plans before treating
it as executable scope. Each appendix is an independent slice shape; Codex can
pick them up in any order that preserves the tier dependencies once the
canonical owner plan carries the slice.*
