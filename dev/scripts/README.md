# Developer Scripts

Canonical maintainer control plane:

```bash
python3 dev/scripts/devctl.py ...
```

Runtime scope-path parsing (`dev/scripts/devctl/runtime/scope_path_claims.py`) recognizes both `.json` and `.jsonl` extensions in the `_PATH_RE` regex, so typed-state files such as `dev/state/plan_index.jsonl` referenced in instruction or reviewed-scope text are matched by `extract_scope_paths()` and `path_matches_scope_claim()`. Focused regression coverage lives in `dev/scripts/devctl/tests/runtime/test_scope_path_claims.py`.

Runtime note:
- Repo-owned Python subprocesses launched by `devctl` now inherit the
  interpreter used to start `dev/scripts/devctl.py`. On machines where
  `python3` is older than the repo baseline, run `python3.11
  dev/scripts/devctl.py ...` so `check`, `probe-report`, and `guard-run`
  follow-ups stay on the same runtime.

Use `devctl` first for release, verification, docs-governance, and reporting.
Legacy shell scripts remain as compatibility adapters that route into `devctl`.
For active-doc discovery, use `dev/active/INDEX.md`.
For current execution scope, use `dev/active/MASTER_PLAN.md`.
For loop output to chat-suggestion coordination, use
`dev/active/loop_chat_bridge.md`.
For consolidated visual planning context (Theme Studio + overlay research +
redesign), use `dev/active/theme_upgrade.md`.
For IDE/provider adapter modularization execution scope, use
`dev/active/ide_provider_modularization.md`.
For pre-release architecture/tooling remediation execution scope, use
`dev/active/pre_release_architecture_audit.md`.
Closed execution plans belong in `dev/archive/`, not `dev/active/`, once their
scoped work is complete and registry/discovery docs are updated in the same
change. If a plan doc still contains unfinished or deferred backlog, keep it
active.
For a quick lifecycle/check/push guide, see `dev/guides/DEVELOPMENT.md` sections
`End-to-end lifecycle flow`, `What checks protect us`, and `When to push where`.
For the plain-language whole-system `devctl` map, including the portable
naming-contract guard direction and future `map` command shape, see
`dev/guides/DEVCTL_ARCHITECTURE.md`.
For automation-first `devctl` routing and Ralph loop controls, see
`dev/guides/DEVCTL_AUTOGUIDE.md`.
For a plain-language map of how `review-channel`, `autonomy-swarm`, and
`swarm_run` fit together inside the larger Codex/Claude collaboration model,
see `dev/guides/AGENT_COLLABORATION_SYSTEM.md`.
Review-channel packet posts deliberately remain no-wake communication events:
their packet-attention receipt records `PacketArrivalDerivedStateInvalidation`
for the existing event-backed projections and controller consumers, while
provider launch/replacement stays owned by scheduler/runtime controllers.
For typed collaboration repair work, keep actor route and packet route
separate: `review-channel show` must carry `--actor`, `--actor-role`, and
`--session-id` for the reader while preserving packet `--target-role` /
`--target-session-id` as route metadata. `task_produced`, `task_progress`, and
artifact evidence posts require exact `ControlDecisionObeyedGuard` allowed
actions (`review-channel.post_task_produced`,
`review-channel.post_task_progress`, or `review-channel.post_evidence`); do not
authorize them through a broad post/finding action.
During GuardIR extraction, `bridge.md` is intentionally rendered as a
deprecated projection-only stub. Use typed state, contracts, receipts, repo
policy, source code, and guards for authority; bridge stale/empty state is
`projection_stale` and must not block backend work by itself.
For MCP-as-adapter rules and extension policy, see
`dev/guides/MCP_DEVCTL_ALIGNMENT.md`.
For portable-governance exports, benchmark planning, and multi-repo adoption,
see `dev/guides/PORTABLE_CODE_GOVERNANCE.md`.
For MP-377 fixture-adopter gate evidence, use the dated section in
`dev/active/portable_code_governance.md`; it records the two non-VoiceTerm
fixture reruns, the source-repo probe wrapper fix, and the remaining
Step-0/full-stack authority blockers.
For MP-377 bilateral agent-loop policy, use
`dev.scripts.devctl.runtime.agent_loop_bilateral_protocol.AgentLoopBilateralProtocol`;
it records the seven typed-state properties and composes with existing
session, command-evidence, and receipt contracts before eventbus/session
automation is allowed to rely on it.
For MP377 plan-targeted edit-only repair, `agent-loop` may project
`continue_scoped_implementation_edit` when the operator override is active and
no scoped packet is claimable. That decision grants only `implementation.edit`:
`next_command` stays empty, while stage, commit, and push remain blocked until
their own typed proof gates pass.
For the broader standalone-governance product architecture, repo-pack
extraction, and frontend/runtime convergence plan, see
`dev/active/ai_governance_platform.md` and
`dev/guides/AI_GOVERNANCE_PLATFORM.md`.
For the typed remote-session commit/push pipeline that phone-steered and
remote-control sessions must eventually use, see
`dev/active/remote_commit_pipeline.md` after
`dev/active/platform_authority_loop.md`.
For the follow-on remote-control reviewer/runtime closure work that converges
typed operator mode, packet-backed action requests, dashboard projections, and
repo-owned auto-poll/update cadence, see
`dev/active/remote_control_runtime.md` after
`dev/active/remote_commit_pipeline.md`.
Operator directive source ids live in
`dev/scripts/devctl/runtime/role_profile.py::OperatorRole`; keep
`human_operator`, `agent_runtime`, `automation_loop`, and `remote_operator`
typed there before projecting operator text through packets or dashboards.
For the bounded loop-v2 convergence work that must turn
`startup-context` / `WorkIntakePacket`, `PlanningIRSnapshot`,
`findings-priority`, `ControlPlaneReadModel`, `AutoModeState`, `monitor`,
graph-backed discoverability, and governed commit/push into one autonomous
controller, see `dev/active/autonomous_governance_loop_v2.md` after
`dev/active/ai_governance_platform.md` and
`dev/active/platform_authority_loop.md`. That lane is composition-first: it
must consume existing typed surfaces instead of inventing a provider-specific
verdict-file controller or operator-prose authority.
That Phase-2 authority follow-up now keeps review/push truth on typed runtime
contracts too: `reviewer_runtime` owns `implementer_ack_current`,
`implementation_blocked`, and `implementation_block_reason`, bridge review
acceptance is typed-only instead of prose-regex fallback, and governed push
recovery keys approval identity to the reviewer-owned
`approved_target_identity` tree receipt instead of raw HEAD equality. The later
approved-target identity finding path consumes that same managed receipt-chain
decision so preflight-created receipt commits do not contradict the publication
authorization gate.
Current governed-mutation rule: `devctl commit` only self-applies typed
approval in resolved `local_terminal` or `single_agent` mode, and
`remote_control` may auto-satisfy the same typed approval step only when
runtime state proves an active `remote_control_attachment` with
`role=operator` for the current lane. `remote_control` without that
delegation, plus dual-agent and unresolved sessions, must keep the approval
request live until an applied operator decision exists. The 2026-04-09 F1
closure entry in `dev/history/ENGINEERING_EVOLUTION.md` ("Remote-control
commit now waits for typed approval") restored the fail-closed boundary after
an earlier slice drifted `_should_auto_approve` to include
`OperatorInteractionMode.REMOTE_CONTROL.value`, and the 2026-04-18 follow-up
now narrows the promptless case back to typed operator delegation instead of a
blanket mode string. `devctl push` now reuses the repo-policy
remote/current approved target when an active pipeline owns the branch, and
packet-queue truth only clears commit-approval requests on applied decisions,
not on `acked` rows or unrelated packet history. In `remote_control` and
other non-auto-approved lanes without that typed operator delegate,
`devctl commit` now also stops at `operator_approval_pending` before it enters
`vcs.commit`; posting a new approval request is not license to let that same
invocation cross the commit boundary. The same governed push path now also
carries the preflight-resolved branch diff base into diff-sensitive post-push
commands, so follow-up checks stay scoped to the just-published delta instead
of resetting to `origin/develop` after publication. If the current execution
sandbox cannot create
`.git/index.lock` before a fresh commit pipeline exists, `devctl commit`
posts a typed `action_request` with `requested_action=stage_commit_pipeline`
to the active remote-control attachment provider and binds it to
`devctl_commit:<head_sha>` instead of asking the local operator to click
through a hidden prompt. That packet must carry full guard evidence and now
emits `AgentSessionOutcome(outcome=completed_handoff)` so publication repair
can distinguish a clean handoff from a dead session.
Transient `.git/index.lock` contention is handled separately: shared git helpers
back off and retry index-writing commands when git reports a temporary
"File exists" / "Another git process" lock, while `Operation not permitted`
continues down the typed remote-control handoff path.
`devctl push` also enforces live execution identity before it can report
publication: `vcs.push` branch parameters are forced from
`git rev-parse --abbrev-ref HEAD`, approved target identity comes from live
publication authorization bound to current worktree and `HEAD`, stale proof is
rejected, and `published_remote` requires populated fetch/preflight/push
evidence plus remote-ref equality with current `HEAD`. Terminal post-push
states require `post_push_steps`; the in-flight `post_push_bundle_pending`
snapshot is publication proof only, not a post-push-green claim.
Commit
authority is separate from implementation evidence now too: before staging or
running guards, `devctl commit` reads the typed `CommitPermissionDecision` and
blocks when startup authority reports `implementation_permission=blocked` or
`implementation_permission=suspended`. The bounded checkpoint exception is
executor-only: if startup explicitly says
`advisory_action=checkpoint_allowed` and `push_decision=await_checkpoint`
with `reviewer_gate.checkpoint_permitted=true`, `devctl commit` may still cut
the governed checkpoint for the staged tree, but raw `git commit` remains
blocked until the wider implementation-authority issue is repaired. Push
cleanliness now blocks only on unstaged or untracked dirt, so staged-only
"next commit" intent does not deadlock `devctl push` or the preflight
auto-commit repair path. Governed staging also fails closed if the managed
ReviewSnapshot refresh drops already-staged user paths, and governed commit
also blocks `staged_scope_missing_dirty_work` when that refresh leaves only
receipt artifacts staged while real dirty work remains outside the index.
When the intended files are not already staged, pass
`--paths <repo-relative-path>...` to `devctl commit`; the command feeds those
paths into the same typed `vcs.stage` action used by remote-control pipelines
and refuses to proceed if other non-artifact dirty paths are still outside the
selected scope.
Governed commit reports may expose the approved content SHA separately from a
trailing ReviewSnapshot `receipt_commit_sha`. Repo-owned
review-channel conductors now also export their typed lane as
`DEVCTL_CALLER_ROLE`, and `devctl commit --role <lane>` remains available for
wrappers/tests, so dashboard, observer, and default reviewer lanes fail closed
before staging instead of reaching a mid-flight approval or git-index prompt.
Successful governed commits now also emit
`dev/reports/feature_proof_receipts/<sha>.json` as a `FeatureProofReceipt`.
That artifact is the operator-facing proof bundle for shipped feature work:
it ties the feature id and commit SHA to review-fleet roles, tests,
connectivity guards, dogfood evidence, real-life test status, bypass refs, and
supporting artifacts. Raw-git bypass commits must create the same proof shape
manually before they are treated as shipped.
Generated bootstrap surfaces are part of that same architecture boundary:
`AGENTS.md` is the shared tracked boot card, `CLAUDE.md` is ignored local-only,
and `CODEX.md` is not generated as a repo surface. Keep them synced with
`render-surfaces`, and make sure they explain the compiler-style control model plus the
`TypedAction -> ActionResult -> RunRecord` path instead of relying on chat
memory or stale starter prose. Generated boot cards must also enumerate the
valid session roles (`reviewer`, `implementer`, `dashboard`, `observer`) and
show help-discovery commands so fresh agents do not guess invalid role names.
They must preserve typed packet-target guidance (`--target-kind` /
`--target-ref`) and direct agents to run `Operator Command Wrappers` verbatim
instead of reconstructing shell-sensitive commands from prose.
`AGENTS.md` also states the canonical memory-is-continuity rule enforced by
`check_memory_not_authority.py`.
Reviewer bootstrap note: repo-owned Codex conductors still begin with
`python3 dev/scripts/devctl.py startup-context --role reviewer --format summary`,
but a non-zero receipt with `action=continue_editing` / `reason=review_pending`
or `action=await_review` / `reason=review_pending_before_push` is still a
normal reviewer-owned bootstrap state while the live loop is healthy.
Continue into `review-channel --action status` plus the reviewer-owned
heartbeat/bridge refresh; reserve relaunch/repair for
`action=repair_reviewer_loop`, checkpoint/budget blockers, or typed stale /
non-live reviewer runtime. After that Step 0 receipt, the canonical role-bound
starter command for a fresh Codex or Claude conversation is
`python3 dev/scripts/devctl.py session --role reviewer|implementer|observer --include-review-status always --format md`;
`dashboard` is accepted as the user-facing alias for the same read-only
observer lane. It emits a typed `SessionOrientationPacket` by running
`startup-context`, `session-resume`, `review-channel --action status --terminal none`,
and `context-graph --mode bootstrap` in order, then reducing the preferred
`AuthoritySnapshot` into the next command. Use that repo-owned packet instead
of hand-written mode prompts, manual git inspection, or operator memory.
When stale runtime attachments survive a process exit, run
`python3 dev/scripts/devctl.py session reconcile --kill-stale --format md`.
It emits `SessionLivenessReconciler`, detaches expired or process-dead
remote-control attachment artifacts through the existing session artifact
writer, and refreshes review-channel status so stale implementer counts are
not preserved in the next startup packet.
When that preferred authority is blocked or explicitly lists `vcs.push` in
`blocked_actions`, the session packet must keep the authority/status next
command instead of promoting a stale startup `run_devctl_push` hint.
A fresh provider session can prove typed rehydration with
`python3 dev/scripts/devctl.py session-resume --role <role> --format json --provider <provider> --write-resume-receipt`.
That command records `AgentResumeReceipt`; its exit code only proves the
resume command ran. Consumers must read `agent_resume_receipt.authority_result`
before acting because `load_result=loaded` can still pair with
`authority_result=blocked` when the typed state carries blockers such as
unknown dirty paths. The Step-0 summary now also carries bounded coordination
truth
(`coordination`, `safe_to_fanout`, `resync_required`, `current_slice`,
`active_target`) and may direct the operator or launcher back to
    `review-channel --action status` when resync is required before a fresh
    implementation slice. When a typed `reviewer_runtime.remote_control_attachment`
    is present, remote-control launchers should treat that attachment as the live
    external Claude session record, elevate fallback interaction-mode reads to
    `remote_control`, and route commit-class mutations through governed
    `devctl commit` so the phone-steered session does not stall on a separate
    approval prompt. Review-channel relaunch checks must treat a running
    conductor script process as live even when its prepared launch metadata is
    stale; stale authority may reclaim only dead or unprobeable sessions, so one
    stale typed-state classification cannot recursively spawn replacement
    conductors.
    reviewer/implementer launch.
For plain-language CI lane docs, see `.github/workflows/README.md`.

For workflow routing (what to run for a normal push vs tooling/process changes vs tagged release), follow `AGENTS.md` first.
Canonical command-bundle lists live in `dev/scripts/devctl/bundle_registry.py`.
Check scripts now live under `dev/scripts/checks/`, with centralized path
registry wiring in `dev/scripts/devctl/script_catalog.py`.
Organization is now part of the quality surface too: `check_package_layout.py`
enforces repo-policy layout contracts for flat roots, helper-family namespaces,
docs coverage, crowded-family baseline/adoption reporting, and crowded-directory
freeze/baseline reporting instead of relying on informal cleanup norms. The
same report now distinguishes blocking violations from baseline organization
debt, so freeze-mode crowded roots cannot be misread as a clean layout just
because no new flat file was added in the current edit. The
`--fail-on-baseline-debt` flag promotes baseline debt to a hard failure; the
optional `--baseline-debt-root` filter scopes enforcement to specific
directories (the tooling and release bundles currently enforce
`dev/scripts/devctl/commands`). When filtered roots are supplied, dirty
working-tree and commit-range runs only hard-fail if the current diff touches
one of those roots; clean-worktree and adoption-scan runs still enforce the
selected roots globally. Repo policy can also ratchet known crowded
roots/families from `freeze` to `strict` when a self-hosting repo needs
touched flat-root files to stop behaving like normal healthy edits. For the
root-scoped release ratchet, flat-root and crowded-directory violations from
non-selected roots are rendered as visible layout debt without hard-blocking
the selected root's publication lane. For the
commands root specifically, the publish-safe repair shape is to move the live
implementation into an existing topical package and leave the flat command path
behind as a thin alias shim with `shim-target` metadata, rather than parking
more logic at `dev/scripts/devctl/commands/`. The same report now also emits `compatibility_redirects` from
valid `shim-target` metadata so agents can follow moved entrypoints through
one repo-owned surface instead of inferring the new path ad hoc.
Compatibility shims inside that layout surface are now governed too: the
portable engine validates shim wrapper shape structurally, repo policy can
require metadata such as `owner`/`reason`/`expiry`/`target`, and crowded-root
reports can exclude approved shims from implementation density while still
surfacing the shim count explicitly. Valid shim wrappers include thin re-export
modules and thin module-alias wrappers that keep legacy import/monkeypatch
paths resolving to the moved implementation; once a wrapper stops being that
thin, it should move back into a real package module instead of hiding extra
logic at the crowded root.

Engineering quality rule:

- For non-trivial Rust runtime/tooling changes, follow the Rust reference pack
  in `AGENTS.md` and `dev/guides/DEVELOPMENT.md` before coding:
  - `https://doc.rust-lang.org/book/`
  - `https://doc.rust-lang.org/reference/`
  - `https://rust-lang.github.io/api-guidelines/`
  - `https://doc.rust-lang.org/nomicon/`
  - `https://doc.rust-lang.org/std/`
  - `https://rust-lang.github.io/rust-clippy/master/`
- Capture references consulted in handoff notes for non-trivial changes.

Python module naming convention:

- `*_core.py` — business logic implementation (e.g. `coderabbit_gate_core.py`)
- `*_render.py` — output formatting and display (e.g. `check_router_render.py`)
- `*_parser.py` — CLI argument wiring and builders (e.g. `cli_parser/quality.py`)
- `*_support.py` — legacy suffix; prefer `_core.py` for new modules
- `*_helpers.py` — legacy suffix; prefer `_core.py` for new modules
- Test files: `test_*.py` in `devctl/tests/`, mirroring the module under test
- `dev/scripts/checks/` root remains intentionally flat only for public
  runnable entrypoints (`check_*.py`, `probe_*.py`, `run_*.py`); new helper
  modules should land in a documented family directory instead.

Documentation style rule:

- Write docs in plain language first.
- Keep steps short and concrete.
- Prefer "what to run and why" over policy-heavy wording.

## Start Here

Most maintainers only need a small set of commands:

```bash
python3 dev/scripts/devctl.py check --profile ci
python3 dev/scripts/devctl.py probe-report --format md
python3 dev/scripts/devctl.py quality-policy --format md
python3 dev/scripts/devctl.py tandem-validate --format md
python3 dev/scripts/devctl.py review-channel --action doctor --terminal none --format md
python3 dev/scripts/devctl.py review-channel --action reviewer-heartbeat --reviewer-mode single_agent --reason local-dev-pass --terminal none --format md
python3 dev/scripts/devctl.py review-channel --action reviewer-checkpoint --reviewer-mode active_dual_agent --reason review-pass --checkpoint-payload-file /tmp/reviewer-checkpoint.json --expected-instruction-revision <live-revision> --expected-implementer-state-hash <live-implementer-state-hash> --terminal none --format md
python3 dev/scripts/devctl.py review-channel --action stop --daemon-kind all --terminal none --format md
python3 dev/scripts/devctl.py bypass grant --scope edit-only --reason "<operator reason>" --format json
python3 dev/scripts/devctl.py raw-git commit --no-verify -m "<slice message>"
python3 dev/scripts/devctl.py raw-git push --no-verify
python3 dev/scripts/devctl.py launcher-check
python3 dev/scripts/devctl.py launcher-probes
python3 dev/scripts/devctl.py launcher-policy
python3 dev/scripts/devctl.py system-picture --format md
python3 dev/scripts/devctl.py system-picture --write-ledger --format md
python3 dev/scripts/devctl.py render-surfaces --format md
python3 dev/scripts/devctl.py platform-contracts --format md
python3 dev/scripts/devctl.py exceptions pending --format json
python3 dev/scripts/checks/check_platform_contract_closure.py
python3 dev/scripts/checks/check_contract_connectivity.py
python3 dev/scripts/devctl.py doc-authority --format md
python3 dev/scripts/devctl.py governance-draft --format md
python3 dev/scripts/devctl.py governance-bootstrap --target-repo /tmp/copied-repo --format md
python3 dev/scripts/devctl.py governance-bootstrap --target-repo /tmp/copied-repo --force-starter-policy --format md
python3 dev/scripts/devctl.py governance-export --format md
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/devctl.py test-python --suite devctl
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/devctl.py process-cleanup --verify --format md
python3 dev/scripts/devctl.py list
```

Use the long command catalog below as the full reference, not the first thing to
read end to end.

`review-channel --action stop` reclaims detached publisher and reviewer
supervisor daemons. It is not a way to interrupt the current `devctl`
controller: heartbeat state that resolves to the caller process is reported as
`current_process_not_detached` so reviewer checkpoint and heartbeat writes
cannot self-signal during governed preflight.

Compatibility note:
- When splitting or relocating Python tooling modules under `dev/scripts/**`,
  keep the old module exporting stable compatibility aliases or re-exports
  until all repo-owned imports, tests, workflows, and pre-commit entry points
  move to the new path. CI still exercises those older seams during staged
  refactors.
- Keep dry-run/report-only tooling paths portable too: review-channel script
  generation and local `triage-loop` preflight should still work on runners
  that do not have provider CLIs on `PATH` or cannot reach the GitHub API,
  unless the command is actually performing the live launch/fix step.
- Keep typed launch-bypass bootstrap on the real lifecycle contract. Use
  `devctl bypass grant` to evaluate and persist an active `BypassLifecycle`
  receipt before `review-channel launch|recover` consumes
  `--bypass-receipt-id`; do not recreate the old inline dangerous-launch
  shortcut in wrapper scripts. The grant path now also writes a
  `ClassifierSafetyAttestation` projection into `.claude/settings.local.json`;
  use `devctl bypass attest --receipt-id <id>` to refresh that projection for
  an already-active receipt.
- `dev/scripts/bootstrap_bypass_lifecycle.py` and
  `dev/scripts/launch_codex_with_bootstrap_receipt.sh` are incident-specific
  launch-deadlock fallback adapters retained for audit/recovery continuity.
  Prefer `devctl bypass grant` for fresh bootstrap receipts and keep new
  operator-run commands short enough to avoid adding wrapper debt.
- Keep operator-authorized raw git visible to typed governance. Use
  `devctl raw-git commit|push` for raw cadence: it still runs the git verb, but
  appends `RawGitBypassReceipt` evidence to
  `dev/state/raw_git_bypass_receipts.jsonl` with the commit SHA or push range,
  skipped hooks, affected paths, actor, authority evidence, and the linked
  `GovernedExceptionLifecycle` id. Lifecycle-backed raw-git authority is
  validated against active `BypassLifecycle` state before the receipt is
  written. After a `FeatureProofReceipt` is written, the wrapper reduces any
  matching `PlanRow` ids in the commit body/FPR to applied state and appends a
  `PlanRowClosureReceipt` in `dev/state/plan_row_closure_receipts.jsonl`.
  No-op help/dry-run/unchanged-head executions do not emit receipts.
- Keep stale-bridge repair portable as well: `review-channel` auto-refresh must
  use the bridge snapshot/liveness contract instead of depending only on
  `check_review_channel_bridge.py` freshness output, because that guard
  intentionally relaxes live heartbeat enforcement on `GITHUB_ACTIONS=true`
  runners.
- Keep review-channel runtime truth portable too: conductor launch now derives
  session specs from a typed provider/lane map and writes role-tagged session
  metadata, packet actor validation resolves against typed
  collaboration/runtime state or repo-owned session metadata instead of parser
  choices, and `check_multi_agent_sync.py` now blocks planned `AGENT-*` rows
  from leaking back into runtime truth when a typed `review_state` snapshot
  exists.
- Bridge rendering portability: `heartbeat.py` worktree-hash exclusion,
  `bridge_projection_state.py` display timezone, `bridge_projection.py`
  swarm-mode plan path, `reviewer_state_support.py` metadata lines, and
  the `check_review_channel_bridge` guard parser all derive VoiceTerm-
  specific values from `RepoPathConfig` fields (`local_state_prefix_rel`,
  `display_timezone`, `review_channel_rel`) instead of hardcoded literals.
- Keep remote commit/push on that same repo-owned backend too: phone-steered
  and remote-control sessions may stage or request approval through typed
  review/runtime surfaces, but commit/push design authority now lives in
  `dev/active/remote_commit_pipeline.md` and must not regress into raw git,
  bridge prose, or wrapper-local shell sequences.
- Keep the rest of the remote-control operator surface on typed runtime too:
  packet-backed action requests, dashboard/operator projections, and auto-poll
  behavior now route through `dev/active/remote_control_runtime.md`, so bridge
  `## Action Requests` and text-only status summaries remain compatibility
  projections instead of a second execution path.
- Keep Terminal-host cleanup on the same repo-owned contract: live
  `review-channel` launch records the returned `terminal_window_id` in session
  metadata, and rollover cleanup must snapshot the retiring session pid plus
  that window id before the new launch rewrites the live metadata files so the
  old conductor is killed before its empty Terminal window is closed.
- Treat moved public scripts and compatibility shims as entrypoint smoke/
  integration coverage too: when script mode, package mode, or root-entrypoint
  routing changes, do not rely only on direct module unit tests.
- For `dev/scripts/checks/**` package moves, keep the legacy root
  `check_*.py` / `probe_*.py` shim runnable in direct script mode and rerun it
  explicitly before trusting the move. Package imports and unit tests can stay
  green while the public root entrypoint still has broken relative-import
  fallback. The same shim also needs a repo-package fallback for
  `dev.scripts.checks.<shim>` imports, because packaged checks can load root
  helpers through `check_bootstrap.import_attr()` without `dev/scripts/checks`
  itself sitting on `sys.path`.
- When a tooling/docs workflow invokes compile-time Rust guards, install the
  repo Rust toolchain and required Linux headers in that job first; the main
  Rust CI lane’s setup does not carry over automatically to `tooling_control_plane.yml`.

Directory layout rule:
- Keep top-level Python files rare.
- `dev/scripts/devctl.py` is the only canonical Python root entrypoint.
- Real implementation code and package-level entrypoints belong in owned
  subdirectories like `mutation/`, `coderabbit/`, `workflow_bridge/`,
  `badges/`, `rust_tools/`, `artifacts/`, and `devctl/`.
- Root shell scripts remain allowed when they are release/publish adapters.

Portability note:
- The guard/probe engine and quality-policy resolver are designed for reuse in
  another repo via policy/preset swaps.
- Deterministic validation contracts are the next portable trust layer under
  `MP-377`: keep the shared contract runner-agnostic, bind repo-local
  adapters such as pytest here where they fit, and route autonomy decisions
  through exact typed validator refs rather than generic "all tests passed"
  signals. Coverage and blast radius can weight trust, but they do not
  replace finding-scoped validator proof.
- `platform-contracts` exposes the broader shared backend blueprint so another
  repo, frontend, or AI installer can see the intended package/runtime/repo-pack
  boundary without reverse-engineering it from active-plan prose alone.
- Governed exceptions are modeled as typed receipt/lifecycle debt, not as a
  bypass path. `python3 dev/scripts/devctl.py exceptions pending --format json`
  reads the optional `dev/state/governed_exception_lifecycles.jsonl` authority
  store without creating it, and `exceptions validate <path>` validates
  JSON/JSONL `ExceptionReceipt` or `GovernedExceptionLifecycle` fixtures. For
  historical raw-git debt, `exceptions close-raw-git --backfill` composes
  `RawGitBypassReceipt` evidence with the governed transition typechecker and
  rewrites matching rows to `closed_via_commit_anchor` with resolution and
  closure proof evidence. CLI failures must preserve the typechecker's
  structured `GovernedTransitionErrorCode.code` values in JSON output and
  include the failing lifecycle and receipt ids; invalid inputs skip without
  rewriting the lifecycle store. The contracts live in
  `dev/scripts/devctl/runtime/governed_exception_contracts.py` and register
  through `platform-contracts`, SYSTEM_MAP connectivity, and context-graph
  typed-contract discovery.
- Governed-exception semantic links are typed registry metadata, not comments
  or Python-only annotations. `ContractSpec.cross_links` records field-level
  links such as `ExceptionReceipt.finding_id -> FindingBacklog` with the
  context-graph edge kind, target resolver/template, direction, and validation
  policy. The connectivity registry and context graph may project that
  metadata for discovery, but they do not become authority and they do not
  materialize lifecycle row nodes until the later `MP377-P0-EXC-S1B` graph
  slice.
- Packet-backed plan ingestion now retains full source bodies in
  `PlanSourceSnapshot` rows. For `MP377-P0-EXC-S1`, the snapshot validator
  requires the consolidated governed-exception plan anchors and rejects a short
  summary snapshot even when the hash matches. Current-source validation is
  bound to the latest accepted `PlanIntentIngestionReceipt` for the row, so an
  older full snapshot cannot mask a newer short-summary snapshot after packet
  expiry.
- R98 packet capture follows that same ingestion path for architectural
  findings before implementation. `dev/audits/r98_packet_4030_4038_plan_capture.md`
  is the retained source snapshot for `MP-NEW-001` through `MP-NEW-028`, and
  `dev/scripts/devctl/runtime/governance_proposed_contracts.py` plus
  `dev/scripts/devctl/platform/runtime_state_contract_rows_governance_proposed.py`
  hold the proposed contract stubs until each slice moves into its permanent
  owner module. Keep `contract_registry.jsonl`, `SYSTEM_MAP.md`, and
  `check_platform_contract_closure.py` green when adding or graduating one of
  those packet-proposed contracts.
- Major governance features need physical dogfood evidence in addition to green
  unit tests and guards. For governed exceptions and role/session packet routing,
  exercise the real `devctl` command surfaces and record dogfood rows; when the
  behavior depends on both supported providers, closure requires live
  Codex+Claude role-swap evidence, or an explicit blocked dogfood gate if a live
  peer is unavailable.
- Guard cadence is future typed work, not a local skip. `MP377-P0-GUARD-CADENCE-S1`
  owns graph-scoped validation scheduling over touched files,
  `ContextGraphSnapshot`, `ContractSpec.cross_links`, runtime contract
  ownership, and command catalog metadata. Safety/proof/authority checks stay
  immediate and non-deferrable; code-shape/refactor-only checks may become
  batched only through `MP377-P0-GUARD-DEFERRAL-S1` typed quality-debt receipts
  with owner, scope, reason, rerun command, expiry, follow-up row, and closure
  proof. Open deferrals block checkpoint, push, resolution, slice close, and
  success claims until rerun proof closes them.
- Operator architecture corrections are intake events, not prose cleanup.
  `MP377-P0-OPERATOR-CORRECTION-INTAKE-S1` owns the follow-up rule: when an
  operator correction changes a governance invariant, acceptance gate, closure
  blocker, or agent-process rule, run typed plan ingestion first and treat
  docs/markdown as projections after the `PlanIntentIngestionReceipt` and
  `PlanSourceSnapshot` exist.
- Worktree-orphan prevention is now represented as typed runtime contract
  surface too: `dev/scripts/devctl/runtime/worktree_orphan_contracts.py`
  re-exports the slice-one `OrphanSnapshot`, `OrphanSource`,
  `OrphanReconciliationDecision`, `CheckoutInventory`,
  `WorkPublicationLedger`, `SessionLease`, `WorktreeBaseline`, and
  accept-all override/receipt models plus the slice-two
  `OrphanInventoryReport`, while
  `dev/scripts/devctl/platform/worktree_orphan_contract_rows.py` registers
  them with the platform `ContractSpec` registry. Later scanner/gate slices
  should consume those models rather than inventing local dict shapes for
  current checkout, worktree, sibling-clone, deep-scan, stash, CI-root, or
  latent-state debt.
- `orphan-inventory` builds the report-only bounded scan for that surface. It
  observes the current checkout, registered/prunable worktrees, planned worker
  lanes, same-parent same-origin sibling clones, and stash sections without
  firing startup/push/fanout gates. Use `--repo-path <path>` for report-only
  portability proof against an external governed pilot checkout before adding
  gate semantics on top of the scanner.
- `startup-context` now includes a fresh `orphan_snapshot` field derived by
  `compute_orphan_snapshot()` from the bounded inventory report. Governed
  commit and push preflight also consult that snapshot as advisory-only warning
  evidence; enforcement remains in the later gate slice.
- `system-picture` is the generated external-review reducer for this repo: it
  composes startup, graph, review-runtime, governance-review, imported
  findings, telemetry signals, and the current bounded coordination posture
  into one snapshot under `dev/reports/system_picture/`, and `--write-ledger`
  refreshes the tracked proof ledger projection at
  `dev/audits/AI_GOVERNANCE_PLATFORM_PROOF_LEDGER.md`.
- Multi-agent topology/fanout truth now has dedicated platform reducers too:
  `dev/scripts/devctl/platform/coordination_snapshot.py` is the first
  repo-visible summary projection for declared-vs-observed topology, fanout
  posture, worktree strategy, and resync need, while
  `dev/scripts/devctl/platform/coordination_topology.py` is the richer shared
  contract for participant rows, delegated worktrees, ready gates, fanout
  safety, recommended topology, and resync command. Startup, status,
  dashboard, and remote-control follow-on work should consume one of those
  typed reducers instead of reconstructing coordination from scattered
  runtime/bridge fields or prose.
- Every coordination read surface must resolve its `CoordinationSnapshot`
  through the shared governed loader
  `dev/scripts/devctl/runtime/coordination_loader.py::load_coordination_snapshot`,
  not through a local `build_coordination_snapshot` wrapper.
  `build_startup_context`, `build_control_plane_read_model`, and
  `session_resume_support.build_from_sources` all delegate to the loader
  so `startup-context --format json`, `session-resume --format json`, and
  `dashboard --format json` cannot silently disagree on topology,
  ownership, or resync truth for a single tree. The MP-384/MP-387 parity
  regression in
  `dev/scripts/devctl/tests/runtime/test_coordination_loader_wiring.py`
  locks that invariant in.
- Read-only advisory roles share one next-command projection helper:
  `dev/scripts/devctl/runtime/advisory_next_action_role_filter.py`.
  `startup-context`, `AuthoritySnapshot`, `ControlPlaneReadModel`,
  `session-resume`, and `dashboard --role dashboard|observer` must use it so
  observer/dashboard surfaces show the read-only review-channel status command
  instead of mutating commit/push/pipeline commands.
- Repo-owned governance surfaces now live in
  `dev/config/devctl_repo_policy.json` too: `repo_governance.check_router`
  defines lane selection + risk add-ons, `repo_governance.docs_check` defines
  canonical docs + deprecated-reference policy for `docs-check`,
  `repo_governance.push` defines deterministic branch/remote/preflight/post-push
  behavior for the canonical `push` surface, and
  `repo_governance.surface_generation` defines policy-owned instruction/starter
  surfaces for `render-surfaces`.
- `check-router`, `docs-check`, and `render-surfaces` all accept
  `--quality-policy <path>` so another repo can replace those repo-owned
  contracts without patching command code.
- `check-router` and `docs-check` also accept `--validation-scope`. Normal
  standalone runs stay strict under `live_worktree`; governed publication uses
  `pipeline_authorized_phase` so docs-check and live projection guards remain
  planned evidence while unrelated live-worktree failures become annotated
  advisory data for the authorized push phase.
- `docs-check --strict-tooling` resolves required maintainer and canonical-plan
  docs from repo policy. When it reports `ai_governance_platform_plan`, update
  `dev/active/ai_governance_platform.md`; when tooling, workflow, release, or
  guard behavior changes, update `dev/guides/DEVELOPMENT.md`,
  `dev/scripts/README.md`, and `dev/history/ENGINEERING_EVOLUTION.md` before
  rerunning governed push.
- Path-scoped docs-governance helpers are expected to reuse one resolved
  docs/policy contract per repo + policy path. If `docs-check --since-ref ...`
  starts rescanning governance inside per-file loops, treat that as a bug in
  the control plane rather than normal commit-range cost.
- Tooling/process/governance architecture belongs in maintainer docs and
  generated repo-pack surfaces, not in VoiceTerm product docs unless
  end-user behavior changed.
- `tandem-validate` is the repo-owned tandem-session validator: it resolves the
  lane and risk add-ons through `check-router`, runs the routed bundle, then
  re-runs final bridge/tandem guards so Codex/Claude sessions do not rely on a
  hand-maintained checklist.
- The `reviewer_follow_guard` module treats `reviewer-follow` and
  `ensure-follow` as automation-only evidence. Those follow loops emit typed
  frames and queue `restore_reviewer_turn` packets through the existing
  `PacketPostRequest` pipeline, but they do not rewrite tracked `bridge.md`
  heartbeat projection state. Manual/semantic heartbeat and checkpoint actions
  remain the repo-owned projection writers. The dedupe is disk-based
  (`_existing_pending_trigger_packet_id`) so dismissed/applied packets allow
  re-queuing without a process restart.
- `review-channel --action post` now also carries the remote commit-pipeline
  approval path as a typed packet instead of bridge prose. Use
  `--kind commit_approval --target-kind runtime --target-ref remote_commit_pipeline:<pipeline_id>`
  with `--pipeline-generation`, `--staged-snapshot-hash`, and
  `--guard-results-summary` so the same approval payload survives
  `post|ack|apply`, `actions.json`, and typed review-state parsing. Discovery
  and workflow policy for that lane stay mirrored in `AGENTS.md`,
  `dev/guides/DEVELOPMENT.md`, and `dev/active/remote_commit_pipeline.md`.
  The staged snapshot hash is now minted only after any managed
  `REVIEW_SNAPSHOT.md` refresh has already been staged, so approval binds the
  exact tree `vcs.commit` will record instead of a pre-refresh approximation.
  When the operator is resuming that lane from the repo-owned CLI, prefer
  `python3 dev/scripts/devctl.py commit --approve-pending`: it reuses the
  current governed pipeline, posts/applies the matching typed
  `commit_approval` decision, and continues the same `vcs.commit` without
  reconstructing packet fields by hand. That explicit resume path is still the
  fail-closed contract whenever the remote-control lane lacks typed
  operator-role delegation; when an active `remote_control_attachment` already
  proves `role=operator`, the initial governed `devctl commit` may satisfy the
  approval step without stopping. The lower-level
  `review-channel --action post|apply` flow remains the raw escape hatch.
  Sandbox staging handoff is packet-backed too: when a remote-control
  checkpoint cannot mint the pipeline because `.git/index.lock` is denied,
  the command emits `requested_action=stage_commit_pipeline` to the attached
  remote-control provider with the commit message draft and current HEAD.
  When an active governed publish pipeline is already blocking a new commit,
  downstream commit surfaces should project the pipeline reducer's
  `next_command` directly instead of emitting free-form prose. Same-HEAD
  expired `push_blocked` pipelines now self-heal that authorization window in
  the block path and point operators straight at `devctl push --execute`.
  If a typed packet lands after the operator's last startup refresh, governed
  stage/commit preflight now reruns the existing `startup-context --format
  summary` receipt writer before failing on `attention_revision_stale`; the
  stale gate remains fail-closed only when that refresh cannot prove current
  packet attention.
  Guard replay also self-resolves the host-process age-out case: when the quick
  bundle fails only because `host-process-cleanup-post` reports recent detached
  repo processes, `devctl commit` runs one bounded `process-watch --cleanup
  --strict --stop-on-clean` retry and replays the same guard bundle once. The
  resulting `ActionResult` includes structured `errors`, `reason_chain`,
  `remediation`, and `auto_executable` fields for dashboard/AI readers.
  During the `vcs.commit` phase, eligible failed `ActionResult` envelopes are
  also passed through `failure_packet_router`, which emits the same
  event-backed `action_request` shape consumed by `safe_auto_apply`. The
  allowlist remains `SAFE_AUTO_APPLY_ACTION_REQUESTS`; commit failures that do
  not opt in continue to return ordinary fail-closed guidance.
- `review-channel --action post --kind action_request` is the event-backed
  source for bridge `## Action Requests`, but executable requests are
  fail-closed on typed runtime binding and non-runtime action requests require
  explicit route scope (`--target-role` or `--target-session-id`) so generic
  read-only guidance does not become an ambiguous active instruction. Use
  `--kind instruction` for unscoped guidance. Use `--requested-action run_check`,
  `kill_process`, or `stage_commit_pipeline` with `--target-kind runtime`,
  `--target-ref`, and `--target-revision`; `stage_commit_pipeline` also
  requires `--full-guard-bundle-evidence` naming the routed full-bundle proof
  (`bundle.runtime`, `bundle.tooling`, `bundle.docs`, `bundle.release`, or
	  `--profile ci`). A valid `stage_commit_pipeline` post also emits an
	  `ActionRequestRuntimeAuthorityEvidence` metadata payload when typed
	  collaboration authority is available from the reduced review state or the
	  configured raw state path. `safe_auto_apply` consumes that authority
	  evidence for actor-targeted handoff packets instead of limiting automatic
	  ACK/apply to system-authored packets; packets without target-actor
	  stage/commit capability evidence still remain pending. Governed commit
	  can then derive missing action-request caller identity, caller role,
	  capability grants, live
	  pipeline generation, and staged snapshot hash from typed state; stale
	  pipeline contracts are ignored, and packet body prose is never executable
	  authority. The same valid post also emits an
	  `AgentSessionOutcome(outcome=completed_handoff)` receipt; governed push may
	  use that receipt only when it matches the current prepared session, or when
	  no provider-matching conductor metadata exists and the receipt is bound to
	  the current `devctl_commit:<head>` / managed-receipt source chain. That
	  source-chain match uses the shared managed-receipt classifier, includes
	  every contiguous receipt ancestor above the current content commit, and
	  accepts the content commit's handoff parent only when the commit-pipeline
	  receipt resolves back to that same content commit. The startup blocker
	  must still be `runtime_missing` / `no_live_agents`,
	  otherwise the existing recovery loop still runs. Use `--requested-action commit` or
  `push` only with `--target-ref remote_commit_pipeline:<pipeline_id>` plus
  `--pipeline-generation`, `--staged-snapshot-hash`, and
  `--guard-results-summary`. Targeted `review-channel --action inbox|watch`
  polls now stamp `delivery_observed_at_utc` / `delivery_observed_by` only
  when `--actor` matches the target agent for live `action_request` packets,
  while `ack|apply` stamp
  `execution_started_at_utc` / `execution_started_by`; those receipt fields
  flow back into typed packet rows so dashboard/status/mobile surfaces can
  prove a remote lane actually saw and started the request instead of only
  inferring from queue length. Prose-only runtime requests stay in packet
  history but are not projected into the bridge execution queue.
- `review-channel --action post --kind automation_opportunity` is the typed
  carrier for advisory automation candidates found from plan sections,
  packet bodies, or guard evidence. It requires typed evidence via
  `--evidence-ref`, `--evidence-artifact-path`, `--action-result-id`,
  `--commit-sha`, or plan-revision refs, and may carry non-authoritative
  `--target-kind plan`, `--target-ref`, `--anchor-ref`, and `--intake-ref`
  metadata. It must not carry `--mutation-op` or runtime guard fields; promote
  accepted work through the existing plan-ingestion path instead.
- `review-channel --action apply` is evidence-bound when it claims work was
  completed. The apply event must carry `PacketGuardAttestation` through
  `--attestation-kind` plus the relevant `--run-record-id`,
  `--action-result-id`, `--commit-sha`, `--plan-revision-before`,
  `--plan-revision-after`, `--evidence-artifact-path`, or
  `--operator-signature` flags for the packet kind. Safe auto-apply paths fill
  that attestation from the run/check evidence they already validated. `ack`
  still means "seen/started"; only an attested apply can close a work claim.
- Codex launcher scripts run a session-end `task_complete` handoff guard. When
  the latest Codex rollout contains `task_complete` and no matching
  `stage_commit_pipeline` packet exists for the current `devctl_commit:<head>`,
  the guard posts the typed action_request to Claude before the supervised
  relaunch loop continues. The live Codex path should still post the packet
  before TASK_COMPLETE; the launcher guard is the crash/idle backup.
- Session-end continuation must be typed, not inferred from packet body text.
  `SessionTerminationPolicy` names whether a completed handoff should end on
  `task_complete`, keep the actor awake through a pending
  `continuation_anchor`, or stop when a `stop_anchor` is active.
  Continuation and stop anchors are route-scoped by `to_agent`, normalized
  `target_role`, and `target_session_id`, so one provider/role session cannot
  keep a different provider/role session alive. `TaskCompleteDecision` records
  the final decision and the canonical `develop next --actor <actor> --format md`
  next command. Anchor packet kinds are valid review-channel records but are not
  actionable inbox packets and should not be acked just to make prose "leave
  pending" semantics work. Anchors are also no-expiry by default: the generic
  review-packet TTL is not transport authority for `continuation_anchor` or
  `stop_anchor` unless `--expires-in-minutes` is explicitly set on the post.
  Generated boot cards require
  `develop next --actor <actor> --enforce-final-response-gate --format json`
  before final/TASK_COMPLETE prose; a false `allow_final_response` or
  `continuation_state=must_continue` means the next typed command must run
  instead of ending the session.
- `agent-supervise`
  (`agent-supervise --actor codex --provider codex --role reviewer --format json`)
  is the read-only outer-loop supervision reducer for MP-377 continuation
  failures. It composes the existing rollout/agent-mind activity age,
  continuation anchor, `LoopAutonomyState`, `BypassReceipt`, and
  `compute_spawn_authority()` gates; it reports process-exit or freeze evidence
  and the existing headless review-channel launch command. `--execute` crosses
  the report-to-action boundary only after `SpawnDeadAgentAction` is present,
  starts that command with `subprocess.Popen`, and emits
  `AgentSuperviseLaunchResult`; it does not create a second watchdog,
  heartbeat, dashboard, or relaunch loop.
- Runtime liveness is projected through `SessionLivenessSignal` in
  `devctl.runtime` with the states `alive`, `degraded`,
  `detached_runtime_only`, and `dead`. Review-channel status emits
  `session_liveness_signals` and keeps `participant_liveness` as a
  compatibility projection; DashboardSnapshot, mobile status, startup counts,
  and control-plane readers consume the typed signal instead of direct bridge
  conductor booleans when it is present.
- `SessionStatusProjection` is the single derived status answer for
  task-complete versus mid-task death. It does not write a new lifecycle store:
  bridge-backed and event-backed status producers derive it from
  `SessionLivenessSignal`, `AgentSessionOutcome`, `AgentMindSlice`,
  collaboration participants, HEAD, and worktree identity, then round-trip it
  through `ReviewState` addenda for status, doctor, startup, and resume
  consumers.
- `ClassifierSafetyAttestation` is the typed bridge from active
  `BypassLifecycle` authority into Claude Code project settings. It projects
  receipt-scoped launch and attest permission rules into
  `.claude/settings.local.json` while keeping `BypassReceipt` as the source of
  authority; the settings file is classifier-readable projection state, not a
  second safety system. The local settings file remains gitignored by policy.
  If an existing `Bash(*)` allow rule dominates the projection, the writer
  records `classifier_dominated_by_bash_wildcard` so the typed bridge does not
  imply narrower operational effect than the provider classifier is applying.
- Packet `ack` / `apply` / `dismiss` is only packet transport lifecycle. It
  does not write the implementer `Claude Ack` compatibility section and does
  not satisfy `current_session.implementer_ack_state=current`; that ACK still
  requires a machine-readable current-instruction revision in the implementer
  ACK surface. `review-channel --action check-ack-freshness --format json`
  is the on-demand typed health probe for comparing visible ACK projection
  text with typed `implementer_ack` event/current-session authority.
- `guard-run --check extend-discipline --format json` is the on-demand
  `ExtensionVsBuildVerificationAutomation` probe. It classifies current git
  dirt as tracked-path extension, new-path build, or mixed work and reports
  `extended`, `built`, `untracked_audit`, `diff_audit`, and `verdict`; pass
  `--extend-discipline-mode auto` when the caller wants new build paths to
  fail closed instead of reporting attention in manual mode.
- `review-channel --action operator-inbox` is the read-only operator queue
  alias over that same typed packet lane. It fixes `target=operator`,
  defaults to `--status pending`, and intentionally does not stamp
  `delivery_observed_at_utc` / `delivery_observed_by` on live
  `action_request` packets. Use it when the operator needs a bounded inbox
  view without mutating delivery receipts; read-only operator `system_notice`
  packets can remain pending there without becoming agent-loop wake debt. Keep
  `inbox|watch --target <agent>` for the active lane watchers that are
  supposed to acknowledge observation.
- `review-channel --action history --include-outcomes` attaches a bounded
  read-side `PacketOutcomeLedger` to the shown history rows. Packet rows also
  carry `PacketLifecycleHistory` and `PacketDisposition`: ack events stay in
  `acknowledged_events`, apply/dismiss/expire transitions stay in
  `acted_on_events`, and unresolved TTL-elapsed packets are classified as
  `archived` with
  `archive_classification:clock_expired_without_disposition` instead of
  disappearing as lost work. It is a report surface only: it does not satisfy
  implementer ACK. Plan-targeted `apply` transitions also append an idempotent
  `PlanRow` to the typed master-plan JSONL store resolved from
  `ProjectGovernance.master_plan` via `PacketPlanIntegration`; the markdown
  master plan is only the VoiceTerm human projection of that JSONL authority.
  New durable packets also pass through `PacketCreationBinding` during
  `post_packet` finalization when they carry explicit plan context, so a
  plan-scoped finding can become a `PlanRow` before TTL expiry instead of
  waiting for manual apply. Bound packets that later expire are classified as
  `expired_after_durable_binding` in both `PacketDisposition` and the
  read-side `PacketOutcomeLedger`, and do not become carry-forward debt.
  The pending-packet disposition guard remains a follow-on enforcement slice.
- Packet inbox and attention authority is role/session-first even while
  compatibility commands still expose provider-shaped flags. Use
  `target_role` and exact `target_session_id` when a live session is intended;
  resolve the current provider/actor from typed collaboration/session state.
  `to_agent` / `from_agent` are delivery labels only. A packet must stay
  visible until lifecycle state records acknowledgment, guard-attested apply,
  dismissal, supersession, archive, or durable ingestion into plan/finding /
  receipt state, so provider role swaps cannot hide packet debt.
- `review-channel --action show --packet-id <id>` is the exact packet-read
  surface for agents and operators. It uses the same event-backed reducer as
  `history`, requires `--packet-id`, renders the packet body plus matching
  packet events, and must not require raw artifact grep. `history
  --packet-id <id>` must also return that exact packet row rather than the
  newest global history page.
- `review-channel --action expire-packets --limit <n>` is the bounded
  write-side maintenance path for TTL-elapsed pending packets. It appends
  explicit `packet_expired` events through the existing packet lifecycle
  reducer, preserves target role/session fields, and refreshes history/inbox
  output so archived packets carry real acted-on event ids instead of
  read-side `clock_expired_without_disposition` placeholders. Read-only
  surfaces such as `sync-status`, `inbox`, and `history` must not append those
  lifecycle events themselves.
- The same event-backed queue now prioritizes live `action_request` packets
  over later commentary when it derives `queue.derived_next_instruction` for
  status/current-session projections. `derived_next_instruction_source` now
  also carries `selection_policy`, `control_state`, and `wake_required` /
  `delivery_required` hints, so remote-control/dashboard beta loops can tell
  the difference between "packet not seen yet" and "packet was seen but still
  has not started" from repo-owned typed state. The same priority selection
  also drives `current_session.current_instruction`, so read-only dashboard and
  status clients do not fall back to a later commentary packet while a live
  action request is still pending. That `action_request` selection stays
  authoritative even when the packet target is the implementer and single-agent
  mode resolves the active coding provider to Codex; packet-truth clear paths
  must preserve the handoff instruction.
- Dashboard-targeted instruction packets are also first-class queue authority.
  Current-session projections may canonicalize them as markdown bullets, so
  surface-consistency checks compare normalized instruction content. Runtime
  packet/AgentLoopDecision drift checks must scope by actor, role, and session
  before treating two packet ids as conflicting authority.
- The same review-channel/dashboard lane now keeps liveness and queue counts
  fail-closed on typed runtime state too: `pending_action_requests` counts only
  live pending `kind="action_request"` packets, dashboard terminal/markdown
  renderers keep a conductor row in `RUNNING` when the typed session says
  `alive=true` even if the PID is unavailable. `ensure --follow` may record
  typed attention for the newest unseen action-request packet, but packet
  delivery does not relaunch a Codex reviewer conductor or depend on a
  separately started watcher.
- Event-backed packet posts also distinguish role/session attention from
  process launch. A packet targeting any provider-backed `target_session_id`
  is not satisfied by launching another process; it records typed attention for
  that exact actor/session and remains pending until the bound session observes
  it on its polling cadence. Provider packet delivery without both
  `target_role` and `target_session_id` records typed attention only instead
  of launching a fresh headless provider process. `requested_session_visibility`
  is generic across roles: `dashboard_only` means typed poll only, `visible`
  means a new worker must be user-visible and capability-gated by a separate
  scheduler/runtime controller, and `headless` is suppressed until explicit
  typed approval/proof marks the route headless-approved. The reduced packet
  post JSON exposes `packet_attention` as the primary receipt; historical
  readers may still see the same payload under the compatibility alias
  `reviewer_wake`. Process ids such as `spawned_pids` and `delivered_to_pids`
  are only valid when a true launch controller, not packet delivery, produced
  them.
- Attention-priority parity is shared across producer paths too: bridge-backed
  `review-channel --action status` and event-backed `startup-context`,
  `session-resume`, and `dashboard` now all attach typed conductor session
  state before recovery assessment runs. Read `attention.status` as the
  runtime diagnosis and `advisory_action` / `push_decision` as the
  checkpoint/publication sequencing layer; one surface should not say
  `review_loop_relaunch_required` while another says `checkpoint_required`
  for the same runtime snapshot.
- The same lane no longer trusts bridge prose or raw HEAD equality for
  publish authority. `reviewer_runtime` owns implementer ACK/block truth,
  `bridge_review_accepted` is typed-only, and push recovery matches
  `approved_target_identity` tree receipts emitted from the approved staged
  snapshot instead of a bare current-HEAD comparison.
- `review-channel --action reviewer-heartbeat` is the repo-owned liveness write
  for solo-dev / tools-only / paused tandem states. It updates heartbeat and
  mode metadata without claiming a new reviewed hash, and it now rewrites
  reviewer-owned `Poll Status` as current-state-only bridge content instead of
  preserving older reviewer revision/ACK bullets.
  In Codex-only local-review mode, `single_agent` is the sanctioned reviewer
  state and this same repo-owned heartbeat/checkpoint path is the review-truth
  authority. When no typed remote-control attachment is active, startup and
  coordination consumers must read that state as local authority, not as an
  implicit request to relaunch headless review-channel conductors. In governed
  remote-control `single_agent` lanes, `review-channel status`, doctor, and
  downstream control-plane readers must also keep the attached remote provider
  live from typed `remote_control_attachment` authority instead of dropping
  Claude solely because recent typed packet activity has aged out.
  In remote-control dogfood runs, the explicit
  `review-channel --action status --refresh-bridge-heartbeat-if-stale` path
  also uses that typed attachment as continuity evidence when the compatibility
  bridge has drifted to stale `tools_only`: status may refresh the Codex
  heartbeat, count that refresh as reviewer activity for this typed
  remote-control continuity case, and reproject `bridge.md` back to
  `active_dual_agent`. Fresh launch/rollover still use the stricter
  live-bridge contract; this is a status-resync path, not a launcher bypass.
- `review-channel --action reviewer-checkpoint` is the repo-owned review-truth
  write. Use it only after a real review pass to advance the reviewed hash,
  verdict, findings, instruction, and reviewed scope together. Prefer one
  typed `--checkpoint-payload-file` for AI-generated markdown or any shell-
  sensitive body, use `--verdict-file` / `--open-findings-file` /
  `--instruction-file` only when you intentionally keep the bodies split, and
  reserve inline body flags for short plain strings. In `active_dual_agent`,
  pass the live `--expected-instruction-revision` plus
  `--expected-implementer-state-hash` from `review-channel --action status`
  or `bridge-poll`. Reviewer-owned checkpoint/promotion/render writes now also
  fail closed when pending reviewer-targeted packets still exist in the
  event-backed inbox, so earlier Codex findings cannot be silently overwritten
  by a later bridge rewrite.
- Keep the implementer ACK contract identical across prompts, validators, and
  typed status reads. In `Claude Ack`, acknowledge the current instruction
  revision with one machine-readable line such as
  `- acknowledged current instruction revision: <rev>` or
  `- acknowledged; instruction-rev: <rev>`. Bridge-backed `current_session`,
  live bridge validation, and `review-channel --action bridge-poll` now share
  that same parser. Bridge text is compatibility output, not ACK authority:
  bridge-backed current-session selection keeps ACK state missing unless
  typed `current_session` / `latest_implementer_ack` state backs the same
  instruction revision. Prefer provider-neutral bridge aliases
  (`implementer_ack*`, `implementer_status`, `reviewer_poll_state`,
  `last_reviewer_poll_*`) when present; legacy `claude_*` / `codex_*` fields
  remain compatibility outputs for bridge/render parity.
- `review-channel --action reset-implementer-state` is the repo-owned repair
  path when live attention says implementer-owned sections must return to
  canonical pending state. It rewrites `Claude Status`, `Claude Questions`,
  and `Claude Ack` to `- pending` and refreshes the typed review-channel
  projection without inventing a new reviewer instruction.
- `review-channel --action stop --daemon-kind <publisher|reviewer_supervisor|all>`
  is the repo-owned daemon reclaim path. Use it when detached follow daemons
  must be replaced by fresh repo-owned runtime, instead of sending raw shell
  signals by hand. `manual_stop` and `completed` reviewer-supervisor
  lifecycle states are non-restartable for implicit `ensure` /
  reviewer-heartbeat auto-start; use an explicit launch, rollover, or follow
  command to restore the supervisor after a governed stop. The launchd
  publisher wrapper also treats stale launch-authority exit `82` as a
  no-restart service exit.
- `review-channel --action implementer-wait` is the repo-owned Claude-side
  wait path. It polls the bridge on the normal cadence, wakes only on
  meaningful reviewer-owned bridge changes, fails closed when the reviewer
  loop is unhealthy, and times out after one hour by default instead of
  lingering as a raw shell `sleep` loop. Use it only under an explicit
  reviewer-owned wait state; if `Current Instruction For Claude` still
  assigns active work, `Claude Status` / `Claude Ack` must name concrete
  files, subsystems, findings, or one concrete blocker/question instead of
  parking on `No change. Continuing.` / `Codex should review` prose.
  Reviewer-owned hold-steady / checkpoint / governed-push-pending bridge
  state counts as that same valid wait posture, so Claude conductors should
  keep polling repo-owned wait/status paths instead of asking the operator to
  choose between polling, pushing, or side work.
- `review-channel --action reviewer-wait` is the symmetric Codex-side wait
  path. It sleeps on cadence too, but wakes on meaningful implementer-side
  changes (`reviewer_worker` hash drift plus typed current-session / ACK
  updates) instead of treating passive supervisor freshness as equivalent to
  new review work. The same wait path now also pivots on the newest
  Codex-targeted pending packet id, so reviewer-side packet delivery no longer
  depends on a separately started watcher during bounded waits; that pivot is
  typed attention only and does not launch or replace a conductor. It reads the
  real `status` report shape (`reviewer_worker` + `bridge_liveness`) and loads
  typed `current_session` state from the generated `review_state.json` /
  `compact.json` projections rather than from an invented top-level status
  payload block. The standalone packet watcher
  (`review-channel --action watch --target claude --status pending --follow
  --terminal none --format json` or
  `review-channel --action watch --target codex --status pending --follow
  --terminal none --format json`) remains useful for observer dashboards,
  queue inspection, and explicit cross-lane packet visibility; add
  `--actor <same-agent>` only when the live lane itself is polling and should
  stamp the delivery receipt. Packet
  visibility is not implicit across providers: if Claude or an operator needs
  to observe Codex-targeted packets, they must use the codex-targeted
  `inbox|watch` surface instead of assuming those packets will appear in the
  Claude lane automatically. Actor-matched watchers still mark observed
  `action_request` packets in the typed receipt path so remote-dashboard beta
  loops can prove packet delivery without bridge prose or queue-only
  heuristics, while observer/dashboard reads stay read-only. Prepared
  conductor-launch authority follows the same typed-source rule after launch:
  remote-control receipt-commit HEAD drift must be classified from typed
  governance/review-state evidence rather than a lone
  `DEVCTL_OPERATOR_INTERACTION_MODE` env var.
- `review-channel --action status|ensure|reviewer-heartbeat|reviewer-checkpoint`
  now emit machine-readable `reviewer_worker` state, and
  `review-channel --action ensure --follow` cadence frames also surface a
  `review_needed` signal without claiming semantic review completion.
  The nested `AuthoritySnapshot` and `CoordinationSnapshot` projections now
  also carry the shared proof-tick provenance tuple (`snapshot_id`, `zref`,
  source identity, source contract/command, and observed/inferred field
  lists) so startup, session-resume, status, and dashboard readers can verify
  producer identity without reconstructing it from surrounding payloads.
  `ensure --follow` also reclaims a missing detached reviewer supervisor when
  dual-agent mode is still active, so the recovery loop is corrective instead
  of status-only. The ensure orchestration delegates heartbeat refresh,
  supervisor-restart detail, recommended-command selection, and report
  construction to `_ensure_helpers.py`, keeping the main `run_ensure_action`
  focused on the phase sequence. Repo-owned reviewer writes also keep `bridge.md`
  current-state-only by replacing stale reviewer `Poll Status` prose on each
  write instead of stacking new notes over old revision bullets. Detached
  repo-owned `ensure --follow` and `reviewer-heartbeat --follow` launches now pin
  `--follow-inactivity-timeout-seconds 0` so the live runtime does not age out
  just because Claude progress is temporarily idle. When that same
  `reviewer-heartbeat --follow` loop sees repeated unchanged Claude progress
  under stale/missing implementer attention, it now escalates through the
  repo-owned `review-channel --action recover --recover-provider <provider>`
  path instead of leaving the loop parked on operator-visible polling prose
  forever. That recovery replaces only the stale implementer conductor for the
  requested provider, and it now fails closed unless the current repo-owned
  reviewer provider is already live. Repeated unchanged stale reviewer/runtime
  states now obey the typed recovery command too: reviewer-follow prefers repo-owned
  `review-channel --action launch` when the recovery contract says launch,
  only auto-executes that relaunch when the typed decision marks it
  auto-fixable, and otherwise fails closed back to the queued reviewer-turn
  packet path instead of silently degrading to `rollover`. If the reviewer
  side is not already live, use full `launch|rollover` instead of creating a
  hybrid provider loop. Full `rollover` still handles bounded round/context
  rotation.
  Fresh launch warmup is no longer treated as a manual-input stall either:
  session-state hints now require a real idle prompt with no active
  `esc to interrupt` progress marker and a short settled age window before
  they emit `waiting_for_user_input`, so visible Terminal recoveries do not
  immediately self-trigger another replacement.
  `active_dual_agent` with detached publisher/supervisor heartbeats but no
  repo-owned conductors is now a bridge-contract error instead of a healthy
  steady-state loop.
- `review-channel --action status` also surfaces bridge-backed
  `push_enforcement` state so operator/read-only consumers can see
  `checkpoint_required`, `safe_to_continue_editing`, `recommended_action`,
  `raw_git_push_guarded`, and the typed publication-backlog cadence fields
  without running `startup-context` separately; the same status path now also
  projects the shared typed `push_decision` used by startup into
  `review_state.json`, `full.json`, `compact.json`, and `latest.md`, so
  operators do not have to infer push timing from `recommended_action`
  strings alone. The same path still escalates attention to
  `checkpoint_required` when the worktree is over the continuation budget
  (reviewer follow-up takes priority when review is also pending on a stale
  hash). Push-state truth is now split explicitly too: raw on-disk
  `dev/reports/push/latest_push_report.json` artifact facts stay under
  `latest_push_report_*`, while startup/governed-push recovery logic consumes
  `selected_push_report_*` plus `selected_push_report_source` for the current
  publication target. Bridge-backed `_compat` payloads now carry
  `push_enforcement` directly, and review projection cache freshness also
  tracks the latest push artifact so read-only/mobile consumers invalidate
  when push-state advances instead of serving a stale compat projection. The
  same push-state snapshot now treats managed bridge/ReviewSnapshot receipt
  drift as projection-owned rather than source dirt and exposes
  source-vs-managed-receipt ahead counts for publication-backlog diagnosis.
- That same `review-channel --action status` path now emits a typed
  `current_session` block in `dev/reports/review_channel/latest/review_state.json`
  and `compact.json`; prefer it for live current instruction / implementer ACK
  reads while the bridge migration remains in progress. `latest.md` renders
  its current-session section from that typed state. The same status refresh
  now also emits a frozen `review_candidate` object when implementer state
  claims a review-ready slice, including candidate id, artifact kind, changed
  paths, worktree hash, checks run, and scope coverage. Reviewers and
  `session-resume` should consume that candidate first for dirty-tree review,
  and status fails closed when implementer-complete state has no valid
  candidate or the candidate omits the instructed scope. `review-channel --action
  bridge-poll` now follows the same rule by refreshing and preferring that
  typed `review_state` projection before deciding live ACK freshness. The same
  shared live loader order is now stricter too: canonical event-backed review
  state wins first, then an already-written typed projection, and only then
  does the repo fall back to bridge-backed status refresh for runtime reads.
  When governance still points at the legacy `.../review_channel/latest`
  compatibility root, the resolver now prefers the sibling
  `.../review_channel/projections/latest/review_state.json` bundle and keeps
  that event-backed path authoritative even for live-refresh callers instead
  of silently downgrading back to the stale bridge-era compatibility file.
  As of the 2026-04-21 `rev_pkt_1503` closure, bridge-contract-drift repair is
  also subordinate to that ordering: when the governed resolver selected the
  event-backed projections bundle, runtime loaders return or refresh that
  event-backed authority before any bridge-backed repair can run.
  The typed `bridge` block now also carries `effective_reviewer_mode`; use that
  field for live-authority decisions when declared bridge `reviewer_mode`
  still says `active_dual_agent` but typed `launch_truth` has already demoted
  the loop. Governed commit execution uses that same precedence when it must
  infer the writable lane from typed review state, so a stale declared
  collaboration mode cannot re-grant the implementer lane after local
  reviewer takeover. Event-backed liveness projections preserve explicit
  reviewer-owned bridge mode before daemon lifecycle rows and ignore stopped
  daemon mode hints; fresh reviewer heartbeat/checkpoint state can refresh
  typed `current_session`, but stale current-session drift warnings cannot
  reverse-overwrite a newer bridge write. The current handoff/recovery seam now stays shape-bounded through
  helper modules too: `review_candidate.py` orchestrates `candidate_parse.py`
  + `candidate_paths.py`, `recovery_assessment.py` orchestrates
  `recovery_decision.py` + `recovery_evidence.py`, and
  `review_state_models.py` re-exports collaboration dataclasses from
  `review_state_collaboration_models.py`.
  Reviewer runtime now also carries an optional typed
  `remote_control_attachment` sidecar for the external phone-steered Claude
  session. Write it through `review-channel --action attach-remote-control`;
  do not stash the live session URL only in chat memory or bridge prose.
  When persisted typed review state exists, status/compat projection now also
  prefers typed `reviewer_runtime.review_acceptance` for verdict/findings
  truth, so raw bridge verdict prose remains compatibility or drift evidence
  instead of retaking authority. Startup/work-intake now also emit a bounded
  ownership classification for dirty paths: `clear`,
  `in_scope_dirty_paths`, `scope_unknown_dirty_paths`,
  `outside_scope_dirty_paths`, or `concurrent_writer_activity`. Startup
  authority fails closed on `concurrent_writer_activity` when typed peer
  activity overlaps outside-scope dirt instead of collapsing the case into a
  generic dirty-budget block. The same intake packet also carries a bounded
  coordination reduction (`collaboration_topology`, `authority_mode`,
  `work_ownership_mode`, `sync_cadence_mode`) plus active participant /
  delegated-worker exemplars, and it now treats duplicated delegated
  worktrees as typed concurrent-writer evidence before overlapping edits land.
  the loop to an inactive read-only state.
- The same status projection now also emits `reviewer_runtime` as the single
  owner of reviewer lifecycle truth: reviewer mode/effective mode, freshness,
  stale reason, last poll, rollover state, session owner, allowed recovery
  action, review acceptance, and publish-clear state. Bridge
  `review_accepted` and doctor output are compatibility projections over that
  contract, not independent authority. Reviewer checkpoints also persist the
  accepted Claude-state baseline in
  `reviewer_runtime.review_acceptance.reviewer_accepted_implementer_state_hash`
  so bridge-only implementer progress still forces reviewer follow-up even
  when the non-bridge reviewed hash stays current.
- `review-channel --action doctor` is the compact readiness/read-only surface
  for that same lane. It reuses the canonical status refresh path, reports the
  reduced `doctor`, `reviewer_runtime`, and `commit_pipeline` payloads plus
  `projection_paths`, and writes the managed `commit_pipeline.json` artifact so
  phone/dashboard clients can see truthful blocked or ready pipeline state
  without scraping bridge prose. The reduced `doctor` payload also carries the
  projected publisher/supervisor running state plus the last heartbeat and
  stop-reason fields for both daemons. Status/doctor now also hoist one
  top-level `recommended_command`, preferring typed recovery commands and
  otherwise reusing `push_decision.next_step_command`, so hooks and launcher
  wrappers can consume one field instead of unpacking multiple nested
  compatibility projections. Startup push truth still comes from
  `reviewer_runtime.publish_clear` and the shared `push_decision` path, not a
  second doctor-only evaluator. A same-head `commit_recorded` pipeline is a
  continue-publication state, not a recovery state: `pipeline --action status`
  should therefore project `recommended_next_action=none` with
  `next_command=python3 dev/scripts/devctl.py push --execute`, while the
  superseded dirty-after-checkpoint path still overrides to `abandon` in the
  governed commit block report. When current HEAD is a governed
  bridge/ReviewSnapshot receipt commit whose parent is the pipeline
  `commit_sha` / `authorized_head_sha`, status reports
  `head_movement_classification=managed_receipt` and keeps
  `head_has_moved=false` instead of recommending recovery.
  The same status refresh now stamps one shared
  `snapshot_id` across `review_state.json`, `compact.json`, `commit_pipeline`,
  compact/compat doctor projections, and `_compat.bridge_projection.metadata`
  so startup, phone, and review-channel surfaces can prove they were generated
  from the same typed reviewer/pipeline snapshot. Event-backed
  `projections/latest/review_state.json` must preserve that same compat bridge
  payload too; when persisted `_compat.bridge_projection` is absent, the
  event-backed enrichment path now rebuilds it from typed bridge/current-
  session/runtime state before `check_review_surface_consistency.py` reads
  `review_state_bridge_projection`.
  For feature-branch release-lane preflight, the shared CodeRabbit gate is
  also publication-aware: when the current local SHA is not present in any
  local remote-tracking ref yet, the gate reports that state as non-blocking
  until publish instead of failing on an impossible "no workflow runs for this
  SHA yet" condition.
- For reviewer-owned automation, treat the `status` report shape honestly:
  live read APIs expose `bridge_liveness` plus projection paths, and typed
  `current_session` comes from the generated `review_state.json` projection
  rather than from an invented top-level status payload block.
- `startup-context` is the typed startup packet for AI sessions. It composes
  compact repo governance, reviewer gate, push/checkpoint advice, and a
  bounded `WorkIntakePacket` with typed continuity plus startup-routing
  hints; that same packet now also carries bounded `session_pacing` guidance
  computed from planning IR plus current graph adjacency so startup can name
  the initial authority refs, implementation refs, and first-patch research
  budget before ad hoc exploration widens. When
  `dev/reports/review_channel/latest/review_state.json` is available it prefers typed
  `reviewer_runtime.review_acceptance.review_accepted` and
  `reviewer_runtime.publish_clear` state, while `bridge.review_accepted`
  remains a compatibility projection over that same contract and `bridge.md`
  remains a compatibility projection instead of a startup-authority fallback.
  The underlying `ProjectGovernance` payload now also carries a typed
  governed-markdown baseline (`DocPolicy`, `DocRegistry`, parsed
  `PlanRegistry` entries) so startup no longer depends only on hard-coded
  path roots, but `## Session Resume` content is still markdown-only restart
  state. The same governed startup path now persists
  `PlanRegistry` / `PlanTargetRef` authority under
  `dev/reports/governance/plan_registry.json` and reuses that artifact while
  the governed doc set is unchanged, so startup/planning readers stop
  reparsing mutable plan markdown on every read. Authority readers that still
  need legacy MP/path/router views now project them from typed registry state
  through `dev/scripts/devctl/runtime/plan_registry_projection.py` before any
  compatibility fallback to raw `INDEX.md` parsing. Generated bootstrap surfaces
  now make
  `startup-context --format summary` the mandatory Step 0 gate before edits,
  validation, or repo-owned launcher work. User summaries, stale chat
  continuity, or remembered prior state are not substitutes for that
  receipt. Keep chat bootstrap acknowledgements to blocker state plus next
  step by default; inspect the repo-owned artifacts or terminal output for the
  richer packet detail. For launch/recovery choices, read
  `startup-context.action`, `interaction_mode`,
  `reviewer_runtime.conductor_visibility`, and
  `reviewer_runtime.session_owner.session_visibility` together before picking
  `--terminal terminal-app` vs `--terminal none`. Startup also projects
  `observed_control_topology` and `implementation_permission` from supervised
  conductor counts, bridge liveness, and runtime counts instead of relying on
  planned bridge topology as live implementation authority. Startup now also
  projects deterministic action-routing fields (`next_command`,
  `allowed_actions`, `blocked_actions`, `control_recovery_action`,
  `escalation_action`) and typed `agent_lane` permissions so hooks, launchers,
  and AI sessions can execute the repo-owned next step rather than inferring
  it from partial state. `startup-context --defer-publication` is the explicit
  development escape hatch for long publication/preflight waits: when typed
  push state is blocked only by a dirty-checkpoint/publication gate, it
  re-allows only `implementation.edit` and records the deferred checkpoint or
  push command while keeping `vcs.stage`, `vcs.commit`, and `vcs.push`
  blocked. Destructive runtime recovery is projected separately through closed
  `recovery_action` /
  `recovery_basis` / `recovery_scope`
  fields plus `lane_edit_gate`, so observer/dashboard lanes can emit findings
  or packets without gaining kill/relaunch/edit authority. Startup now also
  carries a bounded
  `contract_ownership_map` derived from the shared `ContractSpec` registry plus
  the same shared `snapshot_id` stamped onto its `push_decision`, so bootstrap
  consumers can see both startup-surface ownership and cross-surface snapshot
  alignment without reparsing the full runtime contract catalog. The slim
  bootstrap packet remains the bounded graph companion for discovery after that
  startup receipt is refreshed.
- Both `startup-context` and `context-graph` are classified as read-only
  commands for audit/telemetry purposes. `startup-context` always attempts the
  receipt write because the launcher validates it to gate subsequent actions,
  but degrades gracefully on `OSError` when `DEVCTL_NO_ARTIFACT_WRITES=1`.
  Normal `context-graph --mode bootstrap` runs persist the managed graph
  snapshot used by `system-picture` freshness checks; explicit external
  `DEVCTL_NO_ARTIFACT_WRITES=1` still suppresses that bootstrap snapshot on
  read-only mounts. Explicit `--save-snapshot` on `context-graph` still writes
  unconditionally.
- `observe_launch_state()` in `bridge_launch_control.py` uses a lightweight
  bridge-metadata + session-probe path instead of forcing the full status
  refresh on every launch poll iteration. The heavy path is kept as the
  `OSError` fallback.
- `wait_for_codex_poll_refresh()` in `handoff.py` has two satisfaction paths
  for the post-launch ACK gate: (1) reviewer-owned `Poll Status` text
  changed, or (2) `Last Codex poll` timestamp advanced past the pre-launch
  baseline AND typed session probes confirm both conductors are live. Neither
  path accepts BOTH unchanged timestamp AND unchanged status text.
- `dev/scripts/checks/check_review_surface_consistency.py`
  (`check_review_surface_consistency.py`) is the proof guard for startup /
  status / doctor convergence. It reads `startup-context`, `review_state.json`,
  `compact.json`, and `commit_pipeline.json`, then fails if their shared
  `snapshot_id` or pipeline `generation_id` values diverge. It also enforces
  attention-projection parity: when `recovery_assessment` is present,
  `review_state.attention` must match the canonical projection fields
  (`status`, `owner`, `summary`, `recommended_action`, `recommended_command`);
  field drift is a CI-blocking error. The same guard also reads
  `review_state_bridge_projection` from the event-backed
  `projections/latest/review_state.json` bundle and fails if that compat bridge
  payload is missing or stamped with a different snapshot family. Both
  `tooling_control_plane.yml` and `release_preflight.yml` now enforce it.
  The same guard now freezes the Phase 0 proof tick across coordination,
  authority, control-plane, startup-context, session-resume, review-channel
  status, persisted review-state, registry, and bridge-compat surfaces. Where
  a surface exposes proof-tick fields, reviewer mode, effective reviewer mode,
  operator interaction mode, topology, instruction revision, ownership,
  implementation permission, next command, snapshot/generation identity,
  HEAD/worktree identity, and `zref` must match the single producer tick and
  carry producer-owned `SurfaceProvenance`. Expected values come from the
  field's typed authority priority, not from first populated surface order, so
  compatibility projections cannot silently become canonical.
  The control-topology comparison is scoped to explicit
  `observed_control_topology` fields; `coordination.observed_topology` remains
  coordination evidence and is not a substitute for the active control
  posture.
- If a launched reviewer terminal is interrupted and status degrades into a
  Claude-only / hybrid loop, treat that as a runtime repair boundary instead of
  a coding invitation. Use `review-channel --action stop --daemon-kind all`
  followed by `review-channel --action reviewer-heartbeat --reviewer-mode single_agent`
  to record local takeover before inspecting or finishing the interrupted slice.
- `dev/scripts/checks/check_review_snapshot_freshness.py`
  (`check_review_snapshot_freshness.py`) keeps `dev/audits/REVIEW_SNAPSHOT.md`
  bound to the current HEAD + generation stamp by comparing the fields
  embedded in the file against the live typed projection. A final commit that
  changes the generated snapshot, the snapshot plus the governed
  `bridge.md` compatibility projection, or a tracked policy-owned
  generated surface from `render-surfaces`, is also accepted when the embedded
  snapshot binds to that receipt commit's parent code state, or to any
  ancestor in a contiguous governed bridge/ReviewSnapshot/generated-surface receipt chain,
  because a file inside a commit cannot contain its own final SHA. Whenever
  non-receipt HEAD moves or the typed generation stamp changes without a
  snapshot rewrite, the guard fails and instructs the caller to rerun
  `python3 dev/scripts/devctl.py review-snapshot --write --receipt-commit`. Both
  `tooling_control_plane.yml` and `release_preflight.yml` enforce it. The
  managed raw-git hook path is now explicit three-hook automation:
  `devctl install-git-hooks` installs the pre-commit
  commit-permission hook, the post-commit receipt hook, and
  a blocking pre-push hook. The pre-commit hook now fails closed when the
  existing typed `commit_permission` boundary says raw `git commit` is not
  allowed; it does not refresh or stage projections because it runs while git
  is preparing the commit index. The receipt hook delegates to
  `python3 dev/scripts/devctl.py review-snapshot --write --receipt-commit`
  so the final pushed branch can end with a governed ReviewSnapshot receipt
  instead of a manually refreshed dirty worktree. The post-commit receipt
  refresh is bounded by
  `DEVCTL_REVIEW_SNAPSHOT_TIMEOUT_SECONDS` (default 90 seconds, `0` to disable
  the timeout) and still fail open with a warning so a slow ReviewSnapshot
  cannot make an otherwise-allowed commit appear stuck. Governed
  `devctl commit` streams phase progress while the irreversible git commit is
  running, and the managed post-commit hook announces the trailing receipt
  refresh before and after its quiet `review-snapshot` call, while the
  pre-commit hook stays read-only and the pre-push hook
  refuses raw `git push` unless the nested push came from
  `python3 dev/scripts/devctl.py push --execute`. `devctl push` consumes that
  shape directly: a receipt HEAD may satisfy a current
  `PushAuthorizationRecord` through the contiguous managed
  bridge/ReviewSnapshot/generated-surface receipt chain back to the approved
  content commit, the authorization reader looks first at the canonical
  event-backed `projections/latest/commit_pipeline.json` artifact before
  falling back to legacy review-status roots, executor-routed push validates
  against its in-process `RemoteCommitPipelineContract` so an unrelated
  projection refresh cannot transiently erase the authorization during
  preflight, the approved-target identity
  finding path consumes the same chain proof instead of re-checking raw HEAD
  equality, and push preflight now
  runs `render-surfaces --write` plus
  a one-shot reviewer-heartbeat refresh before ReviewSnapshot refresh when
  active dual-agent `Last Codex poll` exceeds the bridge freshness threshold,
  creates managed generated
  surface/projection receipts when tracked repo-pack output or
  bridge/status/ReviewSnapshot reprojection leaves only governed receipt
  artifacts dirty, parses trimmed `git status --porcelain` rows so an
  unstaged managed artifact is still receipted when the shared git helper
  strips its leading status column, runs
  `review-snapshot --write --receipt-commit` when that batch moves `HEAD`
  unless `HEAD` is already a managed ReviewSnapshot/generated-surface receipt
  recognized through the shared receipt-prefix registry,
  refreshes the event-backed review-channel projection bundle plus
  startup/context-graph surfaces after managed receipt movement, and then runs
  the routed guard bundle against the committed freshness state. Selected
  generated-surface receipts use pathspec commits plus
  `DEVCTL_MANAGED_PROJECTION_RECEIPT_COMMIT=1` so the pre-commit hook can
  consume completed-handoff authority only after staged managed-projection
  paths are proven; staged-only next-commit intent stays out of the machine
  receipt. Nested push preflight uses
  `DEVCTL_NO_ARTIFACT_RECEIPT_WRITES=1` to suppress only dispatcher artifact
  receipt ledger rows; it must not use broad `DEVCTL_NO_ARTIFACT_WRITES=1`,
  because review-channel and other domain artifact writes are live dogfood
  evidence during check-router publication preflight. Push
  reporting, authorization, and pipeline-state
  sync then operate on the receipt HEAD while preserving the approved content
  commit as the parent target. `check_system_picture_freshness.py` is the
  companion pre-push guard: it fails stale `SystemPicture` sections and
  requires the startup and graph sections to be current. Stale detached
  pipeline records are ignored in `single_agent` mode so an older override
  cannot strand the branch. When preflight resolved a branch-aware diff base,
  the same runtime truth is reused for diff-sensitive post-push commands; hook
  wrappers should not re-derive `origin/develop` on their own. The typed
  snapshot now also carries first-class probe run state (`state`, `mode`,
  warning/error counts, summary artifact refs) plus current push
  receipt/authorization refs so review consumers can follow emitted evidence
  instead of inferring everything from suggested commands. Active dual-agent
  and current pipeline publication still require exact typed authorization.
- Portable-authority rule: new reusable runtime/tooling code should resolve
  plan docs, artifact roots, bridge/review state, and generated bootstrap
  instructions through `ProjectGovernance` / repo-pack state instead of
  reviving fixed VoiceTerm paths or `VOICETERM_PATH_CONFIG` as implicit
  universal defaults. Keep VoiceTerm-specific literals inside repo-pack or
  product-integration surfaces, and fail closed or stay in explicit
  compatibility mode when portable authority is missing.
- Repo-governance checkpoint policy may exclude compatibility projections such
  as `bridge.md` from advisory dirty-path budgeting so live review-channel
  compatibility writes do not force false `checkpoint_required` states. Raw
  git state and reviewer-owned status remain canonical for real push/review
  truth.
- The same checkpoint policy can also exclude repo-declared advisory scratch
  context such as `convo.md` so local reference files do not keep a reviewed
  branch from reaching the governed push path.
- Push-readiness rule: `worktree_clean` means only that the local worktree is
  checkpointed/clean enough to consider the next remote step. Final push
  eligibility still requires a current review gate plus governed
  `python3 dev/scripts/devctl.py push` validation. Read the typed
  `push_decision` answer (`await_checkpoint`, `await_review`,
  `run_devctl_push`, `no_push_needed`) instead of reconstructing remote
  readiness from mixed booleans. Clean local slices that are still waiting on
  reviewer acceptance should surface as `await_review`, not as implicitly
  push-ready. Dirty generated compatibility projections expose
  `managed_projection_drift=true` plus `managed_projection_dirty_paths`
  instead of hiding the raw `bridge.md` dirt or counting it as source work.
- Commit / review / push state machine:

| `push_decision` | Meaning | Next governed step |
|---|---|---|
| `await_checkpoint` | Local work is not yet checkpointed for remote action. | Cut a bounded checkpoint/commit, then rerun `python3 dev/scripts/devctl.py startup-context --format summary`. |
| `await_review` | Local checkpoint is clean, but reviewer-owned acceptance is not current yet. | Wait for the review gate to advance, then rerun `python3 dev/scripts/devctl.py startup-context --format summary`. `review-channel --action reviewer-checkpoint` updates review truth; it does not push by itself. |
| `run_devctl_push` | Repo policy now allows the governed push path. | Run `python3 dev/scripts/devctl.py push --execute`; do not substitute raw `git push`. |
| `no_push_needed` | The branch already matches its upstream. | Stop; no governed push is required. |
- If the governed push path blocks, stop there. Do not treat the block as a
  casual raw `git push` fallback; the planned operator exception path is a
  typed override inside the same governed control plane.
- Keep the mode model simple: `active_dual_agent` means live reviewer/implementer
  freshness is enforced; `single_agent`, `tools_only`, `paused`, and `offline`
  keep the same backend and checks but suspend stale dual-agent warnings until
  the reviewer resumes active mode. In sanctioned local-review takeover,
  `single_agent` remains local implementation authority when no typed
  `remote_control_attachment` is live; relaunch is only required when you
  intend to restore the live dual-agent pair, not when Codex is intentionally
  continuing locally.
- Human-facing shorthand is accepted on the CLI without changing the stored
  contract: `agents` normalizes to `active_dual_agent`, and `developer`
  normalizes to `single_agent`.
- When `tandem-validate` is red only because a release-lane CI/network/status
  check cannot reach an external service, treat that as a local environment
  blocker rather than a code-quality regression. Keep real CI/release lanes
  strict; do not silently downgrade those failures in automation.
- VoiceTerm also ships simple repo-local wrappers for policy-backed launcher
  scanning so vibecoders do not need to memorize policy paths:
  `launcher-check`, `launcher-probes`, and `launcher-policy` all target
  `dev/config/devctl_policies/launcher.json`.
- `remote-control` owns the repo-local phone/dashboard remote lifecycle.
  `start`, `enter`, `heartbeat`, `exit`, `status`, `doctor`, and `dry-run`
  all read or write the same typed `RemoteControlAttachmentState` artifact
  consumed by review-channel status, startup, session-resume, dashboard, and
  commit/push gates. Active non-expired attachments promote
  `operator_interaction_mode=remote_control`; detached, stale, expired, or
  missing attachments fall back to local-terminal operator truth when repo
  governance is local. Claude physical remote-control is a built-in Claude
  slash flow, not a `claude --remote-control` CLI launch. The primary local
  integration is the project `.claude/settings.json` `UserPromptExpansion`
  async hook, with `UserPromptSubmit` fallback: when Claude activates
  built-in `/remote-control` or `/rc`, the hook calls `remote-control hook`,
  devctl filters the prompt, reads Claude's live
  `~/.claude/sessions/<pid>.json` `bridgeSessionId` state for the matching
  `sessionId`/repo cwd, and records typed state with
  `proven_source_kind=claude_builtin_slash` and
  `physical_confirmation_method=claude_session_state_bridge`. The transcript
  `bridge_status` URL remains fallback activation evidence, not the primary
  liveness clock.
  The same project settings install a `SessionEnd` hook that detaches typed
  state when the local Claude process exits. Existing Claude sessions may need
  restart before a newly added project hook is loaded.
  `/project:typed-remote-control` is the only generated project slash adapter
  over this backend and contains no policy. Project `/remote-control` and
  `/bridge-loop` aliases are intentionally retired so Claude's provider-owned
  `/remote-control` and `/rc` commands win dispatch.
- `dev/scripts/remote-bridge-loop.sh` is compatibility wrapper glue only. It
  forwards existing wrapper flags into
  `python3 dev/scripts/devctl.py remote-control start --launcher-source
  remote-bridge-loop --entrypoint legacy_remote_bridge_loop`; it does not sync slash
  command content, own lifecycle policy, or create a second reviewer backend.
- Higher-level workflow helpers such as mutation, Ralph, process hygiene, and
  some docs-routing commands still include VoiceTerm repo policy and are not
  yet fully repo-agnostic.

## Canonical Commands

```bash
# Core quality checks
python3 dev/scripts/devctl.py check --profile ci
python3 dev/scripts/devctl.py check --profile maintainer-lint
python3 dev/scripts/devctl.py check --profile pedantic
python3 dev/scripts/devctl.py report --pedantic --format md
python3 dev/scripts/devctl.py report --rust-audits --with-charts --emit-bundle --format md
python3 dev/scripts/devctl.py report --python-guard-backlog --python-guard-backlog-top-n 15 --format md
python3 dev/scripts/devctl.py quality-policy --format md
python3 dev/scripts/devctl.py develop --status --format md
python3 dev/scripts/devctl.py develop next --format md
python3 dev/scripts/devctl.py develop campaign --format md
python3 dev/scripts/devctl.py develop audit-packets --max-packets 10 --format md
python3 dev/scripts/devctl.py develop design-preflight --topic "remote control active" --record-ground-truth-receipt --format md
python3 dev/scripts/devctl.py develop launch --dry-run --max-cycles 1 --format md
python3 dev/scripts/devctl.py relaunch-loop --action status --format md
python3 dev/scripts/devctl.py relaunch-loop --action watch-once --format md
python3 dev/scripts/devctl.py relaunch-loop --action dispatch-once --dry-run --format md
# `/develop next` continuation uses typed packet pressure, not watcher status
# alone. Missing PacketBacklogPressure evidence fails closed to the watcher
# report command; a stopped watcher closes only when pressure evidence exists
# and all watched packet-pressure counts are zero.
# Durable-owned findings and other non-command durable packets are no longer
# counted as live runtime pressure after typed plan ownership exists. Runtime
# command packets (`action_request`, `approval_request`, `commit_approval`) and
# explicit-expiry anchors still require ack/apply/dismiss/expire lifecycle
# handling before the controller treats them as resolved.
# `/develop next` selection is authority-first: active unbypassed startup,
# lifecycle, or checkpoint blockers map to typed owner rows before runnable
# plan rows. Packet ids are transport/provenance only after disposition; an
# untriaged packet can block selection for intake, but it is not selected as
# implementation work unless it has been ingested into typed plan/lifecycle
# state.
# `devctl commit` retries rebuild staging when non-receipt unstaged work exists,
# including same-file partial-index repairs after a guard failure. This prevents
# stale staged snapshots from committing while the actual fix remains dirty.
# `/develop audit-packets` consumes PacketAttentionIngestionDecision.next_command
# after classification so the controller advances to the selected packet action
# instead of asking the caller to rerun the audit reducer.
# `relaunch-loop` is the first scheduler-owned relaunch slice: it consumes
# typed SliceClosureEvent rows into an AgentRelaunchTrigger queue and can
# dry-run the dispatcher command. It records typed state only; packet delivery
# still records attention and never launches provider processes.
python3 dev/scripts/devctl.py view --surface ai --format md
python3 dev/scripts/devctl.py session --role implementer --format md
python3 dev/scripts/devctl.py startup-context --format summary
python3 dev/scripts/devctl.py push --execute
python3 dev/scripts/devctl.py tandem-validate --format md
python3 dev/scripts/devctl.py launcher-check
python3 dev/scripts/devctl.py launcher-probes
python3 dev/scripts/devctl.py launcher-policy
python3 dev/scripts/devctl.py render-surfaces --format md
python3 dev/scripts/devctl.py render-surfaces --write --format md
python3 dev/scripts/devctl.py platform-contracts --format md
python3 dev/scripts/devctl.py exceptions pending --format json
python3 dev/scripts/devctl.py exceptions validate <path> --format md
python3 dev/scripts/devctl.py system-picture --format md
python3 dev/scripts/devctl.py system-picture --write-ledger --format md
python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md
python3 dev/scripts/devctl.py context-graph --query '<term>' --format md  # file paths, typed contracts, and dataclass fields; suppresses Hot Index on no_match
python3 dev/scripts/devctl.py context-graph --query '<term>' --save-snapshot --format md
python3 dev/scripts/devctl.py context-graph --mode diff --from previous --to latest --format md
python3 dev/scripts/devctl.py context-graph --format mermaid
python3 dev/scripts/devctl.py graph-walk --from packet:rev_pkt_2210 --to command --format md
python3 dev/scripts/checks/check_platform_contract_closure.py
python3 dev/scripts/devctl.py doc-authority --format json
python3 dev/scripts/devctl.py governance-bootstrap --target-repo ../ci-cd-hub-copy --format md
python3 dev/scripts/devctl.py governance-export --export-base-dir ../portable_snapshot_exports --format md
python3 dev/scripts/devctl.py check --profile ci --quality-policy dev/config/devctl_repo_policy.json
python3 dev/scripts/devctl.py check --profile ci --quality-policy /tmp/pilot-policy.json --adoption-scan
python3 dev/scripts/devctl.py check --profile ci --repo-path /tmp/copied-repo --adoption-scan --format md
python3 dev/scripts/devctl.py probe-report --quality-policy dev/config/devctl_repo_policy.json --format md
python3 dev/scripts/devctl.py probe-report --quality-policy /tmp/pilot-policy.json --adoption-scan --format md
python3 dev/scripts/devctl.py probe-report --repo-path /tmp/copied-repo --adoption-scan --format md
python3 dev/scripts/devctl.py report --probe-report --since-ref origin/develop --head-ref HEAD --format md
python3 dev/scripts/devctl.py status --probe-report --format md
python3 dev/scripts/devctl.py triage --probe-report --probe-since-ref origin/develop --probe-head-ref HEAD --no-cihub --format md
python3 dev/scripts/devctl.py triage --pedantic --no-cihub --emit-bundle --format md
python3 dev/scripts/devctl.py check --profile ai-guard
python3 dev/scripts/devctl.py check --profile release
python3 dev/scripts/devctl.py check --profile fast
# `release` adds strict remote gates: `status --ci --require-ci` + CI-mode CodeRabbit/Ralph checks.
# Optional: force sequential check execution (parallel phases are default)
python3 dev/scripts/devctl.py check --profile ci --no-parallel
# Optional: add the orphaned/stale test-process cleanup sweep around checks
python3 dev/scripts/devctl.py check --profile ci --with-process-sweep-cleanup
# Optional: path-aware pre-push routing from changed files
python3 dev/scripts/devctl.py check-router --since-ref origin/develop --execute --keep-going
python3 dev/scripts/devctl.py check-router --since-ref origin/develop --execute --keep-going --parallel-workers 8
python3 dev/scripts/devctl.py check-router --since-ref origin/develop --execute --keep-going --command-timeout-seconds 300 --route-timeout-seconds 1800
python3 dev/scripts/devctl.py check-router --since-ref origin/develop --quality-policy /tmp/pilot-policy.json
# `check-router --execute --keep-going` reports serial-required projection/status
# commands separately from parallel-safe guard rows in `execution_plan`; timed-out
# routed commands fail with returncode 124 and remediation evidence.
# Read the latest typed progress event/heartbeat for a long-running devctl run.
python3 dev/scripts/devctl.py progress-status --format md --limit 10
# Canonical guarded branch-push validation path (non-mutating by default)
python3 dev/scripts/devctl.py push
# Execute the real short-lived branch push plus the configured post-push bundle
python3 dev/scripts/devctl.py push --execute

# Docs + governance checks
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py docs-check --user-facing --strict-release
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/devctl.py docs-check --strict-tooling --quality-policy /tmp/pilot-policy.json
python3 dev/scripts/devctl.py hygiene
# Optional: fail when hygiene emits warnings
python3 dev/scripts/devctl.py hygiene --strict-warnings
# Optional: release-lane strictness that only hard-blocks release-maintenance
# warnings on the configured release branch
python3 dev/scripts/devctl.py hygiene --strict-release-warnings
# Optional: keep mutation-badge freshness visible without failing strict hygiene
python3 dev/scripts/devctl.py hygiene --strict-warnings --ignore-warning-source mutation_badge
# Optional: also ignore long-standing publications drift (bundle.tooling default)
python3 dev/scripts/devctl.py hygiene --strict-warnings --ignore-warning-source mutation_badge --ignore-warning-source publications
# Host-side cleanup + strict verify for repo-related leftovers
python3 dev/scripts/devctl.py process-cleanup --verify --format md
# Read-only host-side Activity Monitor equivalent
python3 dev/scripts/devctl.py process-audit --strict --format md
# Optional: automatically clear detected dev/scripts/**/__pycache__ dirs
python3 dev/scripts/devctl.py hygiene --fix
# External paper/site drift against watched repo evidence
python3 dev/scripts/devctl.py publication-sync --format md
# After updating an external publication, record the new synced source ref
python3 dev/scripts/devctl.py publication-sync --publication terminal-as-interface --record-source-ref HEAD --record-external-ref <external-site-commit> --format md
python3 dev/scripts/devctl.py path-audit
python3 dev/scripts/devctl.py path-rewrite --dry-run
python3 dev/scripts/devctl.py path-rewrite
# Branch sync helper (repo-policy development/release/current by default)
python3 dev/scripts/devctl.py sync
# Also push local-ahead branches after sync
python3 dev/scripts/devctl.py sync --push
# Federated repo source pins (code-link-ide + ci-cd-hub)
python3 dev/scripts/devctl.py integrations-sync --status-only
python3 dev/scripts/devctl.py integrations-sync --remote
# Allowlisted selective import from pinned federated sources
python3 dev/scripts/devctl.py integrations-import --list-profiles --format md
python3 dev/scripts/devctl.py integrations-import --source code-link-ide --profile iphone-core --format md
python3 dev/scripts/devctl.py integrations-import --source ci-cd-hub --profile workflow-templates --apply --yes --format md
# CIHub setup helper (preview allowlisted steps + capability probe)
python3 dev/scripts/devctl.py cihub-setup --format md
# Strict-capability preview for selected steps
python3 dev/scripts/devctl.py cihub-setup --steps detect validate --strict-capabilities --format json
# Apply mode (use --dry-run first in new environments)
python3 dev/scripts/devctl.py cihub-setup --apply --dry-run --yes --format md
# Security guardrails (RustSec baseline + optional workflow scan)
python3 dev/scripts/devctl.py security
python3 dev/scripts/devctl.py security --scanner-tier core --python-scope all
python3 dev/scripts/devctl.py security --with-zizmor --require-optional-tools
python3 dev/scripts/devctl.py security --with-codeql-alerts --codeql-repo owner/repo --codeql-min-severity high
python3 dev/scripts/devctl.py security --with-zizmor --with-codeql-alerts --codeql-repo owner/repo --require-optional-tools
python3 dev/scripts/devctl.py orchestrate-status --format md
python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 30 --format md
python3 dev/scripts/checks/check_agents_contract.py
python3 dev/scripts/checks/check_active_plan_sync.py
python3 dev/scripts/checks/check_architecture_surface_sync.py --since-ref origin/develop --head-ref HEAD
python3 dev/scripts/checks/check_package_layout.py --since-ref origin/develop --head-ref HEAD
python3 dev/scripts/checks/check_multi_agent_sync.py
python3 dev/scripts/checks/check_release_version_parity.py
# CodeRabbit release gates (strict local verification mode on the release
# branch; off the release branch, `check --profile release` resolves the
# current branch and enables commit fallback).
CI=1 python3 dev/scripts/devctl.py release-gates --branch master --sha "$(git rev-parse HEAD)" --wait-seconds 1800 --poll-seconds 20 --format md
python3 dev/scripts/checks/run_coderabbit_ralph_loop.py --repo owner/repo --branch develop --max-attempts 3 --format md
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_markdown_metadata_header.py
# Auto-fix markdown metadata header style where Status/Last updated/Owner blocks exist
python3 dev/scripts/checks/check_markdown_metadata_header.py --fix
# Path collection skips directories whose names end in `.md`, so local research
# checkouts do not get misclassified as markdown files.
python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/checks/check_publication_sync.py
python3 dev/scripts/checks/check_publication_sync.py --release-branch-aware
python3 dev/scripts/checks/check_code_shape.py
python3 dev/scripts/checks/check_duplicate_types.py
python3 dev/scripts/checks/check_structural_complexity.py
python3 dev/scripts/checks/check_workflow_shell_hygiene.py
python3 dev/scripts/checks/check_workflow_action_pinning.py
python3 dev/scripts/checks/check_guard_enforcement_inventory.py
python3 dev/scripts/checks/check_devctl_cold_boot.py --format md
python3 dev/scripts/checks/check_system_picture_freshness.py
python3 dev/scripts/checks/check_bundle_workflow_parity.py
python3 dev/scripts/checks/check_ide_provider_isolation.py --fail-on-violations
python3 dev/scripts/checks/check_compat_matrix.py
python3 dev/scripts/checks/compat_matrix_smoke.py
python3 dev/scripts/checks/check_naming_consistency.py
python3 dev/scripts/checks/check_rust_test_shape.py
python3 dev/scripts/checks/check_rust_lint_debt.py
python3 dev/scripts/checks/check_rust_best_practices.py
python3 dev/scripts/checks/check_rust_compiler_warnings.py --format md
python3 dev/scripts/checks/check_serde_compatibility.py
python3 dev/scripts/checks/check_rust_runtime_panic_policy.py
python3 dev/scripts/checks/check_rust_audit_patterns.py
python3 dev/scripts/checks/check_rust_security_footguns.py
python3 dev/scripts/checks/check_duplication_audit.py --run-jscpd --format md
# Offline fallback when jscpd cannot be installed in the current environment:
python3 dev/scripts/checks/check_duplication_audit.py --run-jscpd --allow-missing-tool --run-python-fallback --format md
# Advisory shared-logic scan for newly added Python/tooling files:
python3 dev/scripts/checks/check_duplication_audit.py --check-shared-logic --since-ref origin/develop --head-ref HEAD --report-path /tmp/voiceterm-duplication.json --format md
# Optional clippy lint histogram + high-signal baseline check
python3 dev/scripts/rust_tools/collect_clippy_warnings.py --working-directory rust --output-lints-json /tmp/clippy-lints.json
python3 dev/scripts/checks/check_clippy_high_signal.py --input-lints-json /tmp/clippy-lints.json --format md
rg -n "^\\s*-?\\s*uses:\\s*[^@\\s]+@" .github/workflows/*.yml | rg -v "@[0-9a-fA-F]{40}$"
for f in .github/workflows/*.yml; do rg -q '^permissions:' \"$f\" || echo \"missing permissions: $f\"; rg -q '^concurrency:' \"$f\" || echo \"missing concurrency: $f\"; done
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md
find . -maxdepth 1 -type f -name '--*'
# `docs-check --strict-tooling` enforces ENGINEERING_EVOLUTION updates for tooling/process/CI shifts and runs active-plan + multi-agent sync gates, markdown metadata-header style checks, workflow-shell hygiene checks, bundle/workflow parity checks, plus stale-path audit (using `dev/scripts/devctl/script_catalog.py` as canonical check-script path registry and the stable `dev/scripts/devctl/path_audit.py` seam for stale-path scanning). Use `path-rewrite` to auto-fix stale path references.
# For UI behavior changes, refresh screenshot coverage in the same pass:
# see dev/guides/DEVELOPMENT.md -> "Screenshot refresh capture matrix".

# Triage output for humans + AI agents (optional CIHub ingestion)
python3 dev/scripts/devctl.py triage --ci --format md --output /tmp/devctl-triage.md
python3 dev/scripts/devctl.py triage --ci --cihub --emit-bundle --bundle-dir .cihub --bundle-prefix triage
# Optional: route categories to team owners via JSON map
python3 dev/scripts/devctl.py triage --ci --cihub --owner-map-file dev/config/triage_owner_map.json --format json
# Optional: advisory pedantic sweep -> report/triage flow
python3 dev/scripts/devctl.py check --profile pedantic
python3 dev/scripts/devctl.py report --pedantic --pedantic-refresh --format md --output /tmp/devctl-pedantic-report.md
python3 dev/scripts/devctl.py report --pedantic --format json --output /tmp/devctl-pedantic-report.json
python3 dev/scripts/devctl.py report --rust-audits --with-charts --emit-bundle --bundle-dir /tmp/devctl-rust-audit --bundle-prefix rust-audit --format md --output /tmp/devctl-rust-audit.md
python3 dev/scripts/devctl.py report --python-guard-backlog --python-guard-backlog-top-n 25 --since-ref origin/develop --head-ref HEAD --format md --output /tmp/devctl-python-guard-backlog.md
python3 dev/scripts/devctl.py report --probe-report --since-ref origin/develop --head-ref HEAD --format md --output /tmp/devctl-probe-summary.md
python3 dev/scripts/devctl.py status --probe-report --format md --output /tmp/devctl-status-probes.md
python3 dev/scripts/devctl.py triage --probe-report --probe-since-ref origin/develop --probe-head-ref HEAD --no-cihub --format md --output /tmp/devctl-probe-triage.md
python3 dev/scripts/devctl.py triage --pedantic --no-cihub --emit-bundle --bundle-dir .cihub --bundle-prefix pedantic-triage --format md --output /tmp/devctl-pedantic-triage.md
# Optional: ingest external AI-review findings (CodeRabbit, custom bots, etc.)
python3 dev/scripts/devctl.py triage --no-cihub --external-issues-file .cihub/coderabbit/priority.json --format md --output /tmp/devctl-triage-external.md
# Bounded CodeRabbit backlog loop (report/fix attempts + bundle evidence)
python3 dev/scripts/devctl.py triage-loop --repo owner/repo --branch develop --mode plan-then-fix --max-attempts 3 --source-event workflow_dispatch --notify summary-and-comment --comment-target auto --emit-bundle --bundle-dir .cihub/coderabbit --bundle-prefix coderabbit-ralph-loop --mp-proposal --format md --output /tmp/coderabbit-ralph-loop.md --json-output /tmp/coderabbit-ralph-loop.json
# Record operator-facing suggestion decisions in dev/active/loop_chat_bridge.md
# after each dry-run/live-run loop packet.
# Bounded mutation remediation loop (report-only default, optional policy-gated fix mode)
python3 dev/scripts/devctl.py mutation-loop --repo owner/repo --branch develop --mode report-only --threshold 0.80 --max-attempts 3 --emit-bundle --bundle-dir .cihub/mutation --bundle-prefix mutation-ralph-loop --format md --output /tmp/mutation-ralph-loop.md --json-output /tmp/mutation-ralph-loop.json
# Bounded autonomy controller loop (triage-loop + loop-packet + checkpoint queue + phone-status artifacts)
python3 dev/scripts/devctl.py autonomy-loop --repo owner/repo --plan-id acp-poc-001 --branch-base develop --mode report-only --max-rounds 6 --max-hours 4 --max-tasks 24 --checkpoint-every 1 --loop-max-attempts 1 --packet-out dev/reports/autonomy/packets --queue-out dev/reports/autonomy/queue --format json --output /tmp/autonomy-controller.json
# iPhone/SSH-safe controller status projection view from queue artifacts
python3 dev/scripts/devctl.py phone-status --phone-json dev/reports/autonomy/queue/phone/latest.json --view compact --emit-projections dev/reports/autonomy/controller_state/latest --format md --output /tmp/phone-status.md
# Merged mobile-safe control snapshot (controller + review-channel state) for SSH or future phone clients
python3 dev/scripts/devctl.py mobile-status --phone-json dev/reports/autonomy/queue/phone/latest.json --review-status-dir dev/reports/review_channel/latest --view compact --emit-projections dev/reports/mobile/latest --format md --output /tmp/mobile-status.md
python3 dev/scripts/devctl.py mobile-status --approval-mode balanced --view actions --format md --output /tmp/mobile-status-approval.md
# Real iPhone app simulator demo and physical-device wizard
python3 dev/scripts/devctl.py mobile-app --action simulator-demo --format md --output /tmp/mobile-app-simulator.md
python3 dev/scripts/devctl.py mobile-app --action simulator-demo --live-review --format md --output /tmp/mobile-app-live-review.md
python3 dev/scripts/devctl.py mobile-app --action device-wizard --format md --output /tmp/mobile-app-device.md
python3 dev/scripts/devctl.py mobile-app --action device-install --development-team TEAMID123 --format md --output /tmp/mobile-app-install.md
# Policy-gated controller actions (safe subset: refresh, report-only dispatch, pause/resume, typed conductor retirement)
python3 dev/scripts/devctl.py controller-action --action refresh-status --view compact --format md --output /tmp/controller-action-refresh.md
python3 dev/scripts/devctl.py controller-action --action dispatch-report-only --repo owner/repo --branch develop --dry-run --format md --output /tmp/controller-action-dispatch.md
python3 dev/scripts/devctl.py controller-action --action pause-loop --repo owner/repo --mode-file dev/reports/autonomy/queue/phone/controller_mode.json --dry-run --format md --output /tmp/controller-action-pause.md
python3 dev/scripts/devctl.py controller-action --action resume-loop --repo owner/repo --mode-file dev/reports/autonomy/queue/phone/controller_mode.json --dry-run --format md --output /tmp/controller-action-resume.md
python3 dev/scripts/devctl.py controller-action --action retire-stale-conductor --pid 35358 --dry-run --format md --output /tmp/controller-action-retire-conductor.md
# Bridge-gated review swarm bootstrap (dry-run first, then live conductor launch)
python3 dev/scripts/devctl.py review-channel --action launch --terminal none --dry-run --format md --output /tmp/review-channel-launch.md
python3 dev/scripts/devctl.py review-channel --action launch --approval-mode balanced --terminal none --dry-run --format md --output /tmp/review-channel-launch-balanced.md
python3 dev/scripts/devctl.py review-channel --action launch --approval-mode trusted --terminal none --dry-run --format md --output /tmp/review-channel-launch-trusted.md
# Note: when --approval-mode is unset and typed interaction_mode == "remote_control",
# the launcher auto-elevates to "trusted" via approval_mode.auto_elevated_approval_mode
# so headless launches do not silently wedge on local sandbox-escalation prompts.
# Rendering trusted provider args now requires an active edit-only
# BypassLifecycle receipt. Use --bypass-receipt-id to select the durable
# lifecycle row; a raw trusted mode string is not enough to emit dangerous
# provider/no-prompt flags.
# review-channel --action recover and the ensure-follow reviewer-wake path
# (reviewer_follow_guard.launch_waiting_reviewer_conductor) follow the same
# auto-elevation rule.
# The typed stall diagnostic treats caller-supplied replacement-session
# rollouts as stronger evidence than an old escalation-deadlock event, so a
# successfully relaunched conductor clears as new_session_spawned.
python3 dev/scripts/devctl.py review-channel --action status --terminal none --format md --output /tmp/review-channel-status.md
python3 dev/scripts/devctl.py review-channel --action promote --terminal none --format md --output /tmp/review-channel-promote.md
python3 dev/scripts/devctl.py review-channel --action launch --format md --output /tmp/review-channel-live.md
# Planned anti-compaction rollover for the current markdown bridge
python3 dev/scripts/devctl.py review-channel --action rollover --rollover-threshold-pct 50 --await-ack-seconds 180 --format md --output /tmp/review-channel-rollover.md
# Human-readable autonomy digest bundle (dated library + md/json + charts)
python3 dev/scripts/devctl.py autonomy-report --source-root dev/reports/autonomy --library-root dev/reports/autonomy/library --run-label daily-ops --format md --output /tmp/autonomy-report.md --json-output /tmp/autonomy-report.json
# Adaptive autonomy swarm (auto-select agent count from metadata + token budget)
python3 dev/scripts/devctl.py autonomy-swarm --question "large refactor across runtime/parser/security" --prompt-tokens 48000 --token-budget 120000 --max-agents 20 --parallel-workers 6 --dry-run --no-post-audit --run-label swarm-plan --format md --output /tmp/autonomy-swarm.md --json-output /tmp/autonomy-swarm.json
# Live swarm defaults (reserves AGENT-REVIEW when possible and auto-runs digest)
python3 dev/scripts/devctl.py autonomy-swarm --agents 10 --question-file dev/active/autonomous_control_plane.md --mode report-only --run-label swarm-live --format md --output /tmp/autonomy-swarm-live.md --json-output /tmp/autonomy-swarm-live.json
# Swarm benchmark matrix (active-plan-scoped tactics x swarm-size tradeoff report)
python3 dev/scripts/devctl.py autonomy-benchmark --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --swarm-counts 10,15,20,30,40 --tactics uniform,specialized,research-first,test-first --agents 4 --parallel-workers 4 --max-concurrent-swarms 10 --dry-run --format md --output /tmp/autonomy-benchmark.md --json-output /tmp/autonomy-benchmark.json
# Full guarded plan pipeline (scope load + swarm + reviewer + governance + plan evidence append)
python3 dev/scripts/devctl.py swarm_run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --agents 10 --mode report-only --run-label swarm-guarded --format md --output /tmp/swarm-run.md --json-output /tmp/swarm-run.json
# Optional continuous mode: keep cycling through checklist scope until failure/limit
python3 dev/scripts/devctl.py swarm_run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --mode report-only --continuous --continuous-max-cycles 10 --feedback-sizing --feedback-no-signal-rounds 2 --feedback-stall-rounds 2 --run-label swarm-continuous --format md --output /tmp/swarm-run-continuous.md --json-output /tmp/swarm-run-continuous.json
# Workflow helper bridges used by CodeRabbit/autonomy workflows
python3 dev/scripts/coderabbit/bridge.py collect
python3 dev/scripts/coderabbit/bridge.py enforce
python3 dev/scripts/workflow_bridge/autonomy.py export-controller --input-file /tmp/autonomy-controller.json --github-output "${GITHUB_OUTPUT}"
python3 dev/scripts/workflow_bridge/autonomy.py export-swarm --input-file /tmp/swarm-run.json --github-output "${GITHUB_OUTPUT}"
python3 dev/scripts/workflow_bridge/autonomy.py assert-swarm-ok --input-file /tmp/swarm-run.json
python3 dev/scripts/workflow_bridge/autonomy.py resolve-controller-config --github-output "${GITHUB_OUTPUT}" --default-plan-id acp-poc-001 --default-mode report-only
python3 dev/scripts/workflow_bridge/autonomy.py resolve-ralph-config --github-output "${GITHUB_OUTPUT}" --default-mode report-only
python3 dev/scripts/workflow_bridge/autonomy.py resolve-swarm-config --github-output "${GITHUB_OUTPUT}" --default-mode report-only
python3 dev/scripts/workflow_bridge/shell.py resolve-range --event-name push --push-before "$(git rev-parse HEAD~1)" --push-head "$(git rev-parse HEAD)" --changed-files-output /tmp/changed-files.txt --github-output /tmp/github-output.txt
# CI note: `.github/workflows/coderabbit_triage.yml` enforces a blocking
# medium/high severity gate for CodeRabbit findings, and `release_preflight.yml`
# verifies that gate passed for the exact release commit. Publish workflows
# (`publish_pypi`, `publish_homebrew`, `publish_release_binaries`,
# `release_attestation`) also enforce the same gate before distribution
# or attestation steps run.
# Scorecard note: keep workflow-level permissions read-only and place
# `id-token: write`/`security-events: write` at the scorecard job level so
# OpenSSF `publish_results` verification passes.
# Rust CI note: the dedicated MSRV lane in `.github/workflows/rust_ci.yml`
# currently pins `1.88.0` to stay compatible with transitive `edition2024`
# manifests in the active dependency graph.
# Rust CI also enforces a high-signal Clippy lint baseline by parsing lint-code
# histogram output from `collect_clippy_warnings.py` and running
# `check_clippy_high_signal.py`.
# Pinning note: keep GitHub-owned actions pinned to valid 40-character SHAs
# (for example `actions/attest-build-provenance`, `github/codeql-action/upload-sarif`).
# If your cihub binary doesn't support `triage`, devctl records an infra warning
# and still emits local triage output.
# Explicit `--cihub` now forces the capability probe path even when PATH lookup
# cannot resolve the binary during preflight checks.
# Loop comment publication uses API endpoints with explicit `/repos/{owner}/{repo}`
# paths and does not append `--repo` to `gh api` calls.
# Clean local failure triage bundles only after CI is green
python3 dev/scripts/devctl.py failure-cleanup --require-green-ci --dry-run
python3 dev/scripts/devctl.py failure-cleanup --require-green-ci --yes
# Clean stale run artifacts under dev/reports with retention safeguards
python3 dev/scripts/devctl.py reports-cleanup --dry-run
python3 dev/scripts/devctl.py reports-cleanup --max-age-days 30 --keep-recent 10 --yes
# Generate a guard-driven remediation scaffold for Rust modularity/pattern debt
python3 dev/scripts/devctl.py audit-scaffold --force --yes --format md
# Commit-range scoped scaffold generation (useful in CI/PR review lanes)
python3 dev/scripts/devctl.py audit-scaffold --since-ref origin/develop --head-ref HEAD --force --yes --format json
# Audit-cycle metrics (automation coverage, AI-vs-script share, chart outputs)
python3 dev/scripts/audits/audit_metrics.py \
  --input dev/reports/audits/baseline-events.jsonl \
  --output-md dev/reports/audits/baseline-metrics.md \
  --output-json dev/reports/audits/baseline-metrics.json \
  --chart-dir dev/reports/audits/charts
# Auto-emitted devctl event logging (default: dev/reports/audits/devctl_events.jsonl)
DEVCTL_AUDIT_CYCLE_ID=baseline-2026-02-24 \
DEVCTL_EXECUTION_SOURCE=script_only \
python3 dev/scripts/devctl.py check --profile ci
# These rows are machine-readable telemetry, not the narrative session-handoff
# surface. Keep "left off here" state in the active plan's `Session Resume`
# and `Progress Log`.
# Data-science snapshot (command telemetry + swarm/benchmark agent sizing stats)
python3 dev/scripts/devctl.py data-science --format md --output /tmp/data-science-summary.md
# Governance review ledger (adjudicated findings -> FP / cleanup rates +
# systemic disposition + optional probe-guidance adoption measurement)
python3 dev/scripts/devctl.py governance-review --format md
python3 dev/scripts/devctl.py governance-review --record --signal-type probe --check-id probe_exception_quality --verdict false_positive --path cihub/example.py --line 41 --finding-class rule_quality --recurrence-risk recurring --prevention-surface probe --guidance-id probe_exception_quality@cihub/example.py:41 --guidance-followed false --format md
# Dogfood coverage ledger/report plus default report-only auto-ingest
python3 dev/scripts/devctl.py dogfood --report --format md --output /tmp/dogfood.md
python3 dev/scripts/devctl.py dogfood --run-scenario plan41-tandem --fix-mode observe --format md --output /tmp/dogfood-plan41.md
python3 dev/scripts/devctl.py dogfood --record --dev-mode --run-scenario plan41-tandem --fix-mode observe --format md
python3 dev/scripts/devctl.py dogfood --record --dev-mode --target-kind command --target-id startup-context --status passed --actor codex --source-command "python3 dev/scripts/devctl.py startup-context --format summary" --format md
python3 dev/scripts/devctl.py dogfood --record --dev-mode --target-kind role --target-id reviewer --status passed --actor codex --campaign-id mp377-live-system --scenario-id voiceterm-baseline --repo-scope first_party --repo-label codex-voice --repo-path /Users/example/codex-voice --topology codex_reviewer_claude_remote --lane-role reviewer --live-run-ref Q83 --governance-finding-id 8865bf9544ddd82b --format md
python3 dev/scripts/devctl.py dogfood --record --record-governance --dev-mode --target-kind command --target-id review-channel --status blocked --actor codex --source-command "python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json" --format md
python3 dev/scripts/devctl.py dogfood --record --record-governance --dev-mode --target-kind guard --target-id code_shape --status failed --governance-check-id dogfood.code_shape_push_regression --finding-path dev/scripts/devctl/commands/vcs/push.py --finding-class local_defect --recurrence-risk recurring --prevention-surface guard --format md
# Slice A auto-ingest: failed non-read-only devctl commands now auto-record
# report-only dogfood rows/findings through PlatformFindingIngest by default.
# It remains fail-open and excluded for read-only, dogfood/governance-recursive,
# and artifact-only commands; both env forms below are opt-outs.
DEVCTL_PLATFORM_FINDING_INGEST_AUTO_RECORD=0 python3 dev/scripts/devctl.py push --format json
DEVCTL_PLATFORM_FINDING_INGEST_DISABLE=1 python3 dev/scripts/devctl.py push --format json
# External findings import / LIVE_RUN compatibility intake
python3 dev/scripts/devctl.py governance-import-findings --input dev/audits/LIVE_RUN.md --input-format md --repo-name codex-voice --repo-path /Users/example/codex-voice --scan-mode external --format md
# Aggregated review-probe packet (AI slop report + stable review_targets artifact)
python3 dev/scripts/devctl.py probe-report --format md --output /tmp/probe-report.md --json-output /tmp/probe-report.json
# Compatibility matrix governance bundle (schema + runtime smoke parity)
python3 dev/scripts/devctl.py compat-matrix --format md
# Optional read-only MCP adapter surface (additive to devctl, not replacement)
python3 dev/scripts/devctl.py mcp --format md
python3 dev/scripts/devctl.py mcp --tool release_contract_snapshot --format json
python3 dev/scripts/devctl.py mcp --serve-stdio
# Optional: gate cleanup against a scoped CI slice
python3 dev/scripts/devctl.py failure-cleanup --require-green-ci --ci-branch develop --ci-event push --ci-workflow "Rust TUI CI" --dry-run
# Optional: override the default cleanup root guard (still restricted to dev/reports/**)
python3 dev/scripts/devctl.py failure-cleanup --directory dev/reports/archive-failures --allow-outside-failure-root --dry-run
# Optional: tighten retention when report growth spikes
python3 dev/scripts/devctl.py reports-cleanup --max-age-days 14 --keep-recent 5 --dry-run
# Workflow note: failure-triage branch scope defaults to develop/master and can be overridden
# with GitHub repo variable FAILURE_TRIAGE_BRANCHES (comma-separated branch names, no spaces).

# Release notes from git diff range
python3 dev/scripts/devctl.py release-notes --version X.Y.Z

# Coverage workflow (mirrors .github/workflows/coverage.yml)
# Coverage runs on every push to develop/master (not only rust/src path changes)
# so Codecov branch-head badges stay fresh after docs/tooling/CI-only commits.
cd rust && cargo llvm-cov --workspace --all-features --lcov --output-path lcov.info
gh run list --workflow coverage.yml --limit 1

# Tag + notes (legacy release flow)
python3 dev/scripts/devctl.py release --version X.Y.Z
# Optional: auto-prepare release metadata before tag/notes
python3 dev/scripts/devctl.py release --version X.Y.Z --prepare-release

# Workflow-first release convenience (only after same-SHA preflight is green)
gh workflow run release_preflight.yml -f version=X.Y.Z
gh run list --workflow release_preflight.yml --limit 1
# gh run watch <run-id>
# `release_preflight.yml` exports GH_TOKEN for runtime bundle `gh` calls;
# set `GH_TOKEN="$(gh auth token)"` when reproducing `check --profile release` locally.
# Preflight workflow also requires `security-events: write` so zizmor SARIF
# uploads can reach GitHub code scanning.
# Preflight zizmor execution is pinned to `online-audits: false` to avoid
# cross-repo compare API permission failures in CI.
# Preflight security gate runs `devctl security` in changed-file scope
# (`--python-scope changed`) with the same resolved `--since-ref/--head-ref`
# range used by AI-guard.
# Preflight does not hard-fail on repository-wide open CodeQL backlog; keep
# CodeQL alert enforcement in dedicated security/triage lanes.
# Preflight keeps `cargo deny` as blocking and treats `devctl security`
# output as advisory evidence in this lane.
python3 dev/scripts/devctl.py ship --version X.Y.Z --verify --tag --notes --github --yes
# One-command prep + verify + tag + notes + GitHub release
# `ship --verify` runs its independent verify subchecks in parallel and then
# resolves failures in the declared substep order.
python3 dev/scripts/devctl.py ship --version X.Y.Z --prepare-release --verify --tag --notes --github --yes
# Optional explicit gate check (same check used by ship --verify and release CI)
CI=1 python3 dev/scripts/devctl.py release-gates --branch master --sha "$(git rev-parse HEAD)" --wait-seconds 1800 --poll-seconds 20 --format md
gh run list --workflow publish_pypi.yml --limit 1
gh run list --workflow publish_homebrew.yml --limit 1
gh run list --workflow publish_release_binaries.yml --limit 1
gh run list --workflow release_attestation.yml --limit 1

# Optional: run release preflight workflow in CI before tagging
gh workflow run release_preflight.yml -f version=X.Y.Z

# External integrations (pinned vendor bridges for reusable patterns)
bash dev/scripts/sync_external_integrations.sh --status-only
bash dev/scripts/sync_external_integrations.sh
bash dev/scripts/sync_external_integrations.sh --remote

# Optional: manually trigger Homebrew workflow for an existing tag/version
gh workflow run publish_homebrew.yml -f version=X.Y.Z -f release_branch=master
# Optional: manually trigger bounded CodeRabbit backlog remediation loop
gh workflow run coderabbit_ralph_loop.yml -f branch=develop -f max_attempts=3 -f execution_mode=plan-then-fix
# Optional auto-run config (repo variables):
# RALPH_LOOP_MODE=always              # always|failure-only|disabled
# RALPH_EXECUTION_MODE=plan-then-fix  # report-only|plan-then-fix|fix-only
# RALPH_LOOP_MAX_ATTEMPTS=3
# RALPH_LOOP_POLL_SECONDS=20
# RALPH_LOOP_TIMEOUT_SECONDS=1800
# RALPH_LOOP_FIX_COMMAND='<your auto-fix command that commits + pushes>'
# RALPH_NOTIFY_MODE=summary-and-comment
# RALPH_COMMENT_TARGET=auto
# RALPH_COMMENT_PR_NUMBER=<optional pr number>
# Optional: manually trigger bounded Mutation remediation loop
gh workflow run mutation_ralph_loop.yml -f branch=develop -f execution_mode=report-only -f threshold=0.80
# Optional: manually trigger bounded autonomy controller loop
gh workflow run autonomy_controller.yml -f plan_id=acp-poc-001 -f branch_base=develop -f mode=report-only -f max_rounds=6 -f max_hours=4 -f max_tasks=24 -f checkpoint_every=1 -f loop_max_attempts=1 -f notify_mode=summary-only -f promote_pr=false
# Optional: manually trigger guarded plan-scoped swarm pipeline
gh workflow run autonomy_run.yml -f plan_doc=dev/active/autonomous_control_plane.md -f mp_scope=MP-338 -f branch_base=develop -f mode=report-only -f agents=10 -f dry_run=true
# Optional auto-run config (repo variables):
# MUTATION_LOOP_MODE=success-only         # always|success-only|failure-only|disabled (unset disables workflow_run mode)
# MUTATION_EXECUTION_MODE=report-only     # report-only|plan-then-fix|fix-only
# MUTATION_LOOP_MAX_ATTEMPTS=3
# MUTATION_LOOP_POLL_SECONDS=20
# MUTATION_LOOP_TIMEOUT_SECONDS=1800
# MUTATION_LOOP_THRESHOLD=0.80
# Mutation threshold is advisory/report-only in workflow defaults; keep local evidence fresh with `devctl mutation-score`.
# MUTATION_LOOP_FIX_COMMAND='<allowlisted fix command that commits + pushes>'
# MUTATION_NOTIFY_MODE=summary-only
# MUTATION_COMMENT_TARGET=auto
# MUTATION_COMMENT_PR_NUMBER=<optional pr number>
# AUTONOMY_MODE=read-only                 # off|read-only|operate (unset disables scheduled autonomy_controller runs)
# ORCHESTRATOR_WATCHDOG_MODE=report-only  # enforce|report-only (unset/off disables scheduled watchdog runs)
# SECURITY_ZIZMOR_MODE=enforce            # enforce|report-only (unset/off disables security_guard zizmor job)
# MUTATION_LOOP_ALLOWED_PREFIXES='python3 dev/scripts/devctl.py check --profile ci;python3 dev/scripts/devctl.py mutants'
# TRIAGE_LOOP_ALLOWED_PREFIXES='python3 dev/scripts/devctl.py check --profile ci'

# Manual fallback (local PyPI/Homebrew publish)
python3 dev/scripts/devctl.py pypi --upload --yes
python3 dev/scripts/devctl.py homebrew --version X.Y.Z
```

`context-graph --mode bootstrap` is the slim warm-start packet. Keep it
bounded by default and use `context-graph --query '<term>'` when the task
needs more repo context. Query mode now resolves file-path terms plus typed
contract and dataclass-field symbols such as `AutoModeState`,
`PlanningIRSnapshot`, or `research_ref_budget` without already knowing the
owning file path. Before edits, validation, or repo-owned launcher
work, run `python3 dev/scripts/devctl.py session --role implementer --format md`
first when you need full fresh-session orientation. That command runs the
startup receipt, session resume, live review status, and bootstrap graph
snapshot in one typed sequence. If you only need the Step 0 authority receipt,
run `python3 dev/scripts/devctl.py startup-context --format summary` and treat
a non-zero exit as a hard stop to checkpoint or repair the repo state. After
that Step 0 receipt is fresh, use the slim bootstrap packet for additional
discovery and targeted `--query` reads.
When the startup receipt is red but the issue is still locally repairable,
prefer `python3 dev/scripts/devctl.py startup-context --repair --apply-safe-fixes --format md`
before falling back to operator nudges. That repo-owned path classifies the
current startup state from typed startup/review owner artifacts, applies at
most one bounded safe repair (`ensure`, `render-bridge`,
`reset-implementer-state`) per invocation, refreshes the managed startup
receipt, and still fails closed on checkpoint/approval boundaries. It also
surfaces typed `AuthoritySnapshot` / `CoordinationSnapshot` blockers such as
`coordination_resync_required` as explicit manual follow-up instead of
falsely reporting the startup state as healthy when review attention happens
to remain `healthy`. The same
repair adapter resolves the governed review-channel `rollover_dir` sibling
from the managed review root before dispatching repo-owned review-channel
actions, so startup repair stays coherent as review-channel command packages
move.
Current graph routing includes first-pass `guards`, `scoped_by`, plan-row,
packet/handoff, finding, receipt, test/workflow/config, and contract
read/write edges. It also seeds generated concept-intent anchors such as
`heartbeat`, `live-stream`, `post-edit-validation`, `dogfood-record`,
`packet-handoff`, and `graph-navigation` so agents can traverse from operator
intent to the typed commands that own the work. Targeted
file/path/packet/plan/intent queries can surface active guard coverage, plan
ownership, operational receipts, and typed authority neighbors before
escalating to fuller startup-context reads. Non-guard queries
now suppress generic guard-edge fan-out, and query output caps oversized
node/edge neighborhoods with explicit evidence counts so graph reads stay a
token reducer. Use `graph-walk --from <node-or-ref> --to <node-or-kind>` when
an agent or human needs a cited path such as packet -> command, finding ->
guard, or plan row -> contract. `graph-walk` is read-only and follows
canonical refs; it does not replace packet lifecycle, check routing, or typed
runtime authority.
Bootstrap mode also now writes a typed
`ContextGraphSnapshot` artifact under `dev/reports/graph_snapshots/` unless
external `DEVCTL_NO_ARTIFACT_WRITES=1` is set, in which case the automatic
snapshot save is suppressed for read-only mounts. The CLI no longer sets that
suppression automatically for normal `context-graph --mode bootstrap` runs,
and it also leaves snapshot writes enabled for `devctl session`, because the
fresh-session orientation packet depends on a current graph snapshot.
Explicit `--save-snapshot` still writes unconditionally. Use
`--save-snapshot` on other `context-graph` modes when you need the same
versioned graph baseline. `context-graph --mode diff --from ... --to ...`
now reads those saved artifacts back into a typed `ContextGraphDelta`,
rendering added/removed/changed node/edge samples plus a rolling trend
summary over the selected snapshot window.

## Scripts Inventory

| Script | Role | Notes |
|---|---|---|
| `dev/scripts/devctl.py` | Canonical maintainer CLI | Use this first. |
| `dev/scripts/generate-release-notes.sh` | Release-notes helper | Called by `devctl release-notes`/`devctl ship --notes`. |
| `dev/scripts/release.sh` | Legacy adapter | Routes to `devctl release`. |
| `dev/scripts/publish-pypi.sh` | Legacy adapter | Routes to `devctl pypi`; internal mode used by devctl. |
| `dev/scripts/sync_external_integrations.sh` | External integration sync helper | Syncs pinned `integrations/code-link-ide` and `integrations/ci-cd-hub` submodules (optional `--remote` tracking updates). |
| `dev/scripts/update-homebrew.sh` | Legacy adapter | Routes to `devctl homebrew`; internal mode syncs formula URL/version/SHA, canonical `desc`, and rewrites legacy Cargo manifest paths from `libexec/src/Cargo.toml` to `libexec/rust/Cargo.toml`. |
| `dev/scripts/reviewer_loop.sh` | Review-loop wrapper | Repo-local helper for the Markdown-swarm reviewer loop; prefer `devctl review-channel` for canonical governed launch/recovery/status flows, but keep this wrapper documented while the compatibility seam remains tracked. |
| `dev/scripts/remote-bridge-loop.sh` | Remote-control compatibility wrapper | Forwards legacy bridge-loop launches into `devctl remote-control start`; lifecycle policy and typed attachment writes live in the devctl backend. |
| `dev/scripts/remote_bridge_prompt.md` | Compatibility note | Documents that the old prompt source is retired and points to generated slash adapters plus `devctl remote-control`. |
| `dev/scripts/mutation/cli.py` | Mutation CLI | Canonical mutation entrypoint for this repo's mutation workflow. |
| `dev/scripts/mutation/config.py` | Mutation module registry | Module definitions, exclusion lists, shard validation, and interactive selection helpers. |
| `dev/scripts/mutation/git.py` | Mutation git targeting | Detects changed `.rs` files via `git diff` against a base branch for focused mutation runs. |
| `dev/scripts/mutation/runner.py` | Mutation cargo execution | Builds and runs `cargo mutants` commands with env/offline/shard support. Baseline skip is on by default. |
| `dev/scripts/mutation/results.py` | Mutation results parser | Parses outcomes JSON and renders markdown/JSON reports using shared repo helpers. |
| `dev/scripts/mutation/plot.py` | Mutation plot helper | Shared hotspot plotting helpers imported by the mutation CLI. |
| `dev/scripts/coderabbit/ralph_ai_fix.py` | Ralph AI fix workflow entrypoint | Canonical Ralph remediation entrypoint; still repo-local until guardrail policy extraction is finished. |
| `dev/scripts/coderabbit/bridge.py` | CodeRabbit triage workflow bridge | Canonical workflow helper for CodeRabbit collection/enforcement steps. |
| `dev/scripts/coderabbit/collect.py` | CodeRabbit triage collection helper | Fetches review/comment/check-run signals from GitHub API and emits normalized finding rows. |
| `dev/scripts/coderabbit/support.py` | CodeRabbit triage shared helpers | Shared categorization/severity parsing and repository/PR resolution helpers. |
| `dev/scripts/rust_tools/collect_clippy_warnings.py` | Clippy summary tool | Canonical lint-summary entrypoint for local and CI Rust guard flows. |
| `dev/scripts/rust_tools/dependency_graph_probe.py` | Dependency graph probe | Emits dependency-graph availability/status data for workflow gating. |
| `dev/scripts/workflow_bridge/autonomy.py` | Autonomy workflow bridge | Canonical CI-facing helper for autonomy-controller and Ralph workflow config/export steps. |
| `dev/scripts/workflow_bridge/mutation_ralph.py` | Mutation Ralph workflow bridge | Canonical workflow helper for mutation remediation loop steps. |
| `dev/scripts/workflow_bridge/shell.py` | Workflow shell bridge | Canonical helper for commit-range, coverage, and failure-artifact workflow plumbing; the top-level `workflow_shell_bridge.py` shim remains available for caller compatibility. |
| `dev/scripts/artifacts/sha256.py` | Checksum writer | Canonical helper for release/archive checksum generation. |
| `dev/scripts/checks/check_mutation_score.py` | Mutation score gate | Used in CI and local validation; prints outcomes source freshness and supports `--max-age-hours` stale-data gating. |
| `dev/scripts/checks/check_mutation_bypass_graph_closure.py` | Governed-mutation bypass graph guard | Stable shim entrypoint for the graph-backed mutation-bypass closure check while the packaged implementation lives under `dev/scripts/checks/mutation_bypass_graph_closure/`; proves raw-git mutation callsites still route through the governed executor surface. |
| `dev/scripts/checks/check_agents_contract.py` | AGENTS boot-card contract gate | Verifies `AGENTS.md` is a generated projection-only `InstructionBootCard` with the required bootstrap sections, command routes, valid role discovery, help-discovery commands, provenance markers, size budgets, and forbidden authority-claim/role-placeholder checks. |
| `dev/scripts/checks/check_agents_bundle_render.py` | AGENTS boot-card render compatibility gate | Backward-compatible guard for existing bundles; delegates to `render-surfaces` for the `agents_boot_card` projection instead of treating AGENTS as command-bundle authority. |
| `dev/scripts/checks/check_bootstrap.py` | Check bootstrap helper | Shared import-resolution and UTC runtime-error/timestamp helpers used by standalone guard scripts; not invoked directly by bundles. |
| `dev/scripts/checks/check_active_plan_sync.py` | Active-plan sync gate | Verifies `dev/active/INDEX.md` registry coverage, tracker authority, mirrored-spec phase headings, cross-doc links, execution-plan metadata/marker/section parity (including `Session Resume`), the typed umbrella-plan phase/task contract for `dev/active/ai_governance_platform.md`, `MP-*` scope parity between index/spec docs and `MASTER_PLAN`, archive-vs-active doc boundaries for the reduced active owner set, and `MASTER_PLAN` Status Snapshot release metadata freshness. |
| `dev/scripts/checks/check_architecture_surface_sync.py` | Architecture-surface sync guard | Scans newly added files and fails when active-plan docs, new check scripts, new `devctl` commands, new `app/**` surfaces, or new workflow files are not wired into the repo's owning authority docs/bundles/workflow docs. Supports `--since-ref`/`--head-ref` for branch diffs and `--paths` for targeted local verification. |
| `dev/scripts/checks/check_ground_truth_probe_gate.py` | Ground-truth probe gate | Blocks runtime/proof/architecture changes that introduce or extend authority surfaces without a current satisfied `GroundTruthProbeRunReceipt`; pairs with `develop design-preflight --record-ground-truth-receipt` so new design work starts from repo truth instead of sidecar assumptions. Supports `--format`. |
| `dev/scripts/checks/check_guide_contract_sync.py` | Durable guide contract sync guard | Verifies repo-policy-owned durable guide/playbook coverage contracts (for example `dev/guides/DEVCTL_AUTOGUIDE.md`) so major control-plane surfaces cannot silently fall out of the operator docs while code keeps moving. |
| `dev/scripts/checks/check_instruction_surface_sync.py` | Generated-surface sync guard | Verifies policy-owned instruction/starter surfaces still match the current repo-pack templates/context without writing files, so `render-surfaces --write` stays paired with a real enforcement lane in tooling/release validation. |
| `dev/scripts/checks/check_systemmap_covers_contract_registry.py` | SYSTEM_MAP contract-registry coverage guard | Verifies the generated SYSTEM_MAP block is current and renders every `dev/state/contract_registry.jsonl` contract id as a backticked token, so new platform contracts cannot stay invisible in architecture docs while registry closure passes. |
| `dev/scripts/checks/check_context_graph_snapshot_freshness.py` | ContextGraph snapshot freshness guard | Stable shim entrypoint for the packaged context-graph snapshot freshness guard, mirroring the ReviewSnapshot freshness pattern so generated graph evidence cannot drift silently after HEAD moves. |
| `dev/scripts/checks/check_action_result_status_domain.py` | ActionResult status-domain guard | Scans `ActionResult` / `ActionResultFields` construction for literal `status=` values outside `ActionOutcome.ALL`, surfacing typed-boundary lies while the baseline remains report-only. |
| `dev/scripts/checks/check_command_output_consumed.py` | Command-output consumption guard | Stable shim entrypoint for the packaged command-output consumption guard; verifies command-output receipts are consumed by the typed proof path instead of being treated as chat-prose evidence. Because it is subject-driven, CI covers the entrypoint with `--stdin --allow-empty`; live proof requires a command-output payload. |
| `dev/scripts/checks/check_control_decision_consistency.py` | Control-decision consistency guard | Stable shim entrypoint for the packaged control-decision consistency guard; checks controller decisions, allowed actions, and observed runtime authority stay internally coherent. Because it is subject-driven, CI covers the entrypoint with `--stdin --allow-empty`; live proof requires an `AgentLoopDecision` payload. |
| `dev/scripts/checks/check_control_decision_obeyed.py` | Control-decision obedience guard | Stable shim entrypoint for the packaged control-decision obedience guard; verifies governed review-channel actions obey the exact active controller decision rather than broad post authority. Because it is subject-driven, CI covers the entrypoint with `--stdin --allow-empty`; live proof requires decision and attempted-action payloads. |
| `dev/scripts/checks/check_packet_pkt_bind_completeness.py` | Packet PKT-BIND completeness guard | Verifies post-mandate Codex `task_started` review packets receive durable `PKT-BIND-REV-PKT-*` plan rows before the grace deadline or paired `task_produced` closure, while reporting historical packet-binding gaps separately. |
| `dev/scripts/checks/check_packet_absorption_required.py` | Packet absorption-required guard | Stable shim entrypoint for the packaged packet-absorption guard; surfaces packets that still require body observation, semantic ingestion, or clearance before controller closure. Because it is subject-driven, CI covers the entrypoint with `--stdin --allow-empty`; live proof requires a review-state payload. |
| `dev/scripts/checks/check_plan_index_commit_continuity.py` | Plan-index commit continuity guard | Verifies governed post-mandate `PlanRow` entries, task-start bindings, and guard charters carry a commit anchor plus `PlanIntentReceipt` and `TypedAction` evidence, with legacy gaps reported separately so new closure rows cannot regress to attention-only proof. |
| `dev/scripts/checks/check_plan_gold_claims_resolve.py` | Plan GOLD-claim resolver guard | Validates positive GOLD/proof promotion claims against live Python symbols, registered contracts, and repository files so plausible class names cannot be promoted as verified substrate without material evidence. Supports `--format`. |
| `dev/scripts/checks/check_plan_metric_freshness.py` | Plan metric freshness guard | Compares plan-cited metric counts against live repository counts for registered metrics such as P140, failing when drift exceeds the configured threshold so stale grep numbers cannot keep driving packet/plan conclusions. Supports `--format`. |
| `dev/scripts/checks/check_feature_has_proof_receipt.py` | Feature proof receipt guard | Verifies commits in a git range have valid `FeatureProofReceipt` artifacts keyed by commit SHA, with optional strict mode for `real_life_test_status=proven_passed`. |
| `dev/scripts/checks/check_plan_row_contract_refs_resolve.py` | Plan-row contract-ref resolver guard | Reports `PlanRow` provenance/contract refs that do not resolve in `dev/state/contract_registry.jsonl`, keeping plan authority from accumulating orphan contract ids. |
| `dev/scripts/checks/check_commit_body_packet_anchors.py` | Commit-body packet-anchor guard | Reports MP slice commits whose messages omit packet ids or `task_started` anchors, preserving review-channel provenance as commit-level evidence while historical backfill remains report-only. |
| `dev/scripts/checks/check_commit_message_row_id_resolves.py` | Commit-message row-id resolver guard | Enforces post-mandate commit-message references to durable plan rows, rejects PKT-BIND-only packet decomposition using the active mandate prefixes and policy-owned `valid_packet_dispositions` instead of hard-coded row families, catches corrupted row titles, requires applied/completed rows to carry `commit_anchor_ref` after the Phase 0c policy timestamp, supports strict `--since-ref/--head-ref` scans, and reports the scanned range plus active mandate prefixes. |
| `dev/scripts/checks/check_role_review_completed.py` | Role-review completion guard | Stable shim entrypoint for the packaged role-review completion guard while the implementation lives under `dev/scripts/checks/role_review_completed/`; verifies commits that require role-review proof have a completed role-review lifecycle before publication. |
| `dev/scripts/checks/check_task_started_adr_precedent_linking.py` | Task-started precedent-link guard | Reports `task_started` review packets that lack packet evidence, plan-family anchors, or ADR-style precedent markers, so implementation starts do not rely on body prose alone. |
| `dev/scripts/checks/check_typed_namespace_composition.py` | Typed namespace composition guard | Verifies typed namespace family files import or justify their canonical authority module, preventing parallel lifecycle/helper families from drifting away from their owning contract. |
| `dev/scripts/checks/check_launcher_authority_ordering.py` | Launcher authority-ordering guard | Stable shim entrypoint for the packaged launcher-authority ordering guard; keeps trusted provider launch paths behind typed bypass/session authority instead of raw launcher flags. |
| `dev/scripts/checks/check_substrate_is_repo_portable.py` | Repo-portability substrate guard | Scans repo-policy configured portable governance substrate paths for hardcoded packet ids, plan ids, session timestamps, local paths, product names, and operator identities so adopter repos provide those values through typed repo-pack policy instead of inherited VoiceTerm literals. |
| `dev/scripts/checks/check_substrate_commits_have_applied_plan_row.py` | Substrate commit plan-row guard | Requires substrate commits in a range to be covered by applied typed PlanRows, preserving plan/accountability linkage for governance-runtime changes. |
| `dev/scripts/checks/check_memory_not_authority.py` | Memory-not-authority guard | Blocks load-bearing architecture, process, runtime, or governance rules from living only in operator memory or scratch notes; durable rules must be promoted into typed contracts, repo policy, maintainer docs, active plan state, or guards. Supports `--format`. |
| `dev/scripts/checks/check_platform_layer_boundaries.py` | Platform-layer boundary guard | Stable shim entrypoint for the architecture-boundary guard that blocks forbidden imports across reusable-backend, surface, and mobile/frontend layers while the implementation lives under `dev/scripts/checks/architecture_boundary/`. |
| `dev/scripts/checks/check_multi_agent_sync.py` | Multi-agent coordination gate | Verifies `MASTER_PLAN` board parity with the merged markdown-swarm tables in `dev/active/review_channel.md` for dynamic `AGENT-<N>` lanes (lane/MP/worktree/branch alignment, instruction/ack protocol checks, lane-lock + MP-collision handoff checks, status/date formatting, ledger traceability, and required end-of-cycle signoff when all agent lanes are merged). |
| `dev/scripts/checks/check_review_channel_bridge.py` | Markdown-bridge contract gate | Verifies the active `bridge.md` bridge exposes the required bootstrap sections/markers, tracked-file safety, and current poll/hash heartbeat metadata while `dev/active/review_channel.md` still declares the transitional markdown bridge active. |
| `dev/scripts/checks/check_tandem_consistency.py` | Tandem role-profile consistency gate | Verifies tandem review/code loop consistency across peer-liveness, event-reducer, status-projection, launch, prompt, and handoff modules. The guard now refreshes the bridge-backed typed `review_state.json` projection before reading live `current_session` / review freshness, then falls back to bridge text only for `reviewed_hash_honesty`, `plan_alignment`, and `launch_truth` where no typed equivalent exists yet. |
| `dev/scripts/checks/check_release_version_parity.py` | Release version parity gate | Ensures Cargo, PyPI, and macOS app plist versions match before tagging/publishing. |
| `dev/scripts/checks/check_coderabbit_gate.py` | Workflow release gate helper | Verifies the latest run for a target workflow/branch+commit SHA is successful before release/publish steps proceed (`--workflow` override + optional `--wait-seconds`/`--poll-seconds` for asynchronous gate arrival). |
| `dev/scripts/checks/check_coderabbit_ralph_gate.py` | CodeRabbit Ralph release gate | Verifies the latest `CodeRabbit Ralph Loop` run is successful for a target branch+commit SHA before release/publish steps proceed. |
| `dev/scripts/checks/run_coderabbit_ralph_loop.py` | CodeRabbit remediation loop | Runs a bounded retry loop over CodeRabbit medium/high backlog artifacts and optional auto-fix command hooks. |
| `dev/scripts/checks/mutation_ralph_loop_core.py` | Mutation remediation loop core helpers | Shared run/artifact/score/hotspot logic used by `devctl mutation-loop`. |
| `dev/scripts/checks/check_cli_flags_parity.py` | CLI docs/schema parity gate | Compares clap long flags in Rust schema files against `guides/CLI_FLAGS.md`. |
| `dev/scripts/checks/check_markdown_metadata_header.py` | Markdown metadata header style gate | Normalizes `Status`/`Last updated`/`Owner` doc metadata to one canonical line style. |
| `dev/scripts/checks/check_screenshot_integrity.py` | Screenshot docs integrity gate | Validates markdown image references and reports stale screenshot age. |
| `dev/scripts/checks/check_publication_sync.py` | External publication drift gate | Compares tracked papers/sites against watched repo source paths and fails when synced public artifacts lag behind the recorded source baseline; `--release-branch-aware` keeps stale drift visible but non-blocking off the configured release branch. |
| `dev/scripts/checks/check_publication_scope_integrity.py` | Publication scope integrity guard | Fails closed when a publication candidate is contaminated by staged, unstaged, untracked, or ignored worktree state outside explicit candidate/deferral receipts. |
| `dev/scripts/checks/check_publication_scope_integrity_for_push.py` | Push publication-scope integrity adapter | Stable governed-push adapter that runs publication-scope integrity against explicit base/head refs from push preflight or workflow range resolution, avoiding ref-less upstream fallback on extraction branches. |
| `dev/scripts/checks/check_code_shape.py` | Source-shape drift guard | Blocks new Rust/Python God-file growth using language-level soft/hard limits (Rust: 900/1400, Python: 350/650), path-level hotspot budgets, **function-length guardrails** (Rust: 100 lines, Python: 150 lines) with expiry-tracked exceptions for existing oversized functions, stale loose path-override detection, override-cap ratcheting (untouched legacy over-cap overrides stay visible as warnings; touched, newly introduced, or worsened over-cap overrides fail), touched-file mixed-concern ratcheting for Python files with 3+ independent function clusters, repo-policy-owned namespace/layout rules, and audit-first remediation guidance (modularize/consolidate before merge, with Python/Rust best-practice links). |
| `dev/scripts/checks/check_package_layout.py` | Package-layout organization guard | Enforces repo-policy placement rules for flat roots, crowded namespace families, docs sync, crowded-directory freeze/baseline reporting, and portable compatibility-shim governance so self-hosting repo structure stays legible and external adopters can see layout debt early without treating thin wrapper seams as invisible or ad hoc. The report now also marks freeze-mode crowded roots/families as baseline debt (`status: baseline_debt_detected`, `layout_clean: false`), emits advisory root-role debt (`organization_review_clean`, `organization_role_debt_detected`) for helper-drawer roots that still mix public entrypoints with flat support/implementation files, and emits `compatibility_redirects` from valid `shim-target` metadata so moved entrypoints advertise where they now live. |
| `dev/scripts/checks/check_duplicate_types.py` | Duplicate Rust type-name guard | Detects duplicate `struct`/`enum` names across Rust files (with explicit allowlist for known transitional duplicates) so new cross-file type-shadowing does not slip in. |
| `dev/scripts/checks/check_structural_complexity.py` | Structural-complexity guard | Flags Rust functions whose structural complexity score (branch points + nesting) exceeds policy limits, with expiry-bound exceptions for active MP-346 transition hotspots. |
| `dev/scripts/checks/check_workflow_shell_hygiene.py` | Workflow-shell anti-pattern guard | Blocks fragile inline shell patterns in workflow run blocks (single-match find/head chains, inline Python snippets) across `.yml`/`.yaml` workflows; supports auditable line-level suppressions via `workflow-shell-hygiene: allow=inline-python-c` (or `allow=all`) when a justified exception is required. |
| `dev/scripts/checks/check_workflow_action_pinning.py` | Workflow action pinning guard | Fails when third-party `uses:` refs are not pinned to full 40-character SHAs (with optional auditable suppressions for justified exceptions). |
| `dev/scripts/checks/check_guard_enforcement_inventory.py` | Guard enforcement inventory gate | Verifies cataloged quality scripts still have a real enforcement lane through bundle/workflow invocation, an internal governed-pipeline lane, or an explicit helper/manual/contextual/advisory exemption. The guard recognizes the current `docs-check --strict-tooling` family, the AI-guard family owned by `devctl check`, the review-probe family owned by `devctl check` / `devctl probe-report`, and governed-push preflight adapters such as publication-scope validation, and keeps no-subject contextual guards explicit instead of letting catalog drift silently. When a guard graduates into the shared hard-guard family, wire the same script into typed quality-policy plus bundle/workflow parity in the same change. |
| `dev/scripts/checks/check_devctl_cold_boot.py` | Devctl cold-boot import smoke guard | Runs a fresh Python interpreter import smoke for `devctl.cli.main` so CLI/runtime import regressions are caught by the tooling workflow and by path-aware `check-router` devctl add-ons. |
| `dev/scripts/checks/check_registry_path_integrity.py` | Script registry path integrity gate | Fails when the canonical script catalog, quality-policy defaults, or top-level `check_*.py` / `probe_*.py` entrypoints drift apart. This catches missing registered files, quality-policy references to unknown script ids, and public probe/check shims that exist on disk but are invisible to `check` / `probe-report`. |
| `dev/scripts/checks/check_runtime_state_ignore_posture.py` | Runtime-state ignore-posture guard | Verifies local runtime receipt stores such as bypass lifecycles, governed exception lifecycles, and raw-git bypass receipts stay ignored and untracked so host-local evidence cannot be accidentally committed as durable source. |
| `dev/scripts/checks/check_bridge_projection_only.py` | Bridge projection-only guard | Stable shim entrypoint for the packaged bridge projection-only guard while the implementation lives under `dev/scripts/checks/bridge_projection_only/`; blocks repaired bridge/current-session/status projection compatibility surfaces from becoming backend authority again. It scans the known review-channel bridge projection seams for bridge-as-authority regressions, ACK compatibility literal misuse, and bridge-poll fallback violations. This guard is wired through the quality-policy defaults, `bundle.tooling`, `bundle.release`, `tooling_control_plane.yml`, and `release_preflight.yml`; do not leave it as catalog-only advisory state. |
| `dev/scripts/checks/check_runtime_bridge_projection_separation.py` | Runtime bridge projection-separation guard | Stable shim entrypoint for the runtime bridge projection-separation guard while the implementation lives under `dev/scripts/checks/runtime_bridge_projection_separation/`; report-only scan of runtime, review-channel, and command surfaces before bridge-reader migration can make projection-authority enforcement strict. |
| `dev/scripts/checks/check_check_cli_test_parity.py` | Check CLI/test parity guard | Verifies managed check CLI entrypoints and their focused tests share one evaluator contract so guard behavior cannot drift between command output and test fixtures. |
| `dev/scripts/checks/check_schema_fixture_handshake.py` | Schema fixture handshake guard | Verifies registered platform contracts have fixture roots with valid and invalid JSON examples, including required invalid cases for missing fields and schema-version mismatch, and fails when fixture JSON files are not git-tracked in a worktree. |
| `dev/scripts/checks/check_schema_migration_spine.py` | Schema migration spine guard | Validates durable state contracts declare migration/store-authority policy before later governance rows can treat schema and rollback semantics as authoritative. |
| `dev/scripts/checks/check_schema_version_monotonic.py` | Schema version monotonicity guard | Ensures registered schema fixture paths end in the registered schema version and reuse the fixture-handshake coverage so schema bumps cannot silently bypass fixtures. |
| `dev/scripts/checks/check_state_store_authority.py` | State-store authority guard | Validates registered durable stores route through the declared state-store authority writer instead of ad hoc JSON/JSONL writes. Planned policies remain visible without blocking until their owning row promotes them. |
| `dev/scripts/checks/check_provider_list_parity_graph.py` | Provider-list parity graph gate | Fails when agent-facing CLI flags such as `--agent` hardcode a provider `choices=[...]` list instead of using the shared provider registry and syntax validation. This keeps `agent-mind`, `monitor`, and future provider-aware commands from splitting their provider vocabularies. |
| `dev/scripts/checks/check_system_picture_freshness.py` | SystemPicture freshness gate | Fails stale generated `SystemPicture` sections and requires the startup and graph sections to be current before publication; refresh with `startup-context` plus `context-graph --mode bootstrap` when HEAD moves. |
| `dev/scripts/checks/check_orchestration_recommendation_closure.py` | Orchestration recommendation-closure guard | Fails when `/develop` orchestration signals carry action recommendations without structured `source_surface`, `severity`, `recommended_action`, and `closure_check_command` fields, so agents can verify closure instead of relying on prose. Pilot/manual until orchestration writers graduate. |
| `dev/scripts/checks/check_governance_closure.py` | Governance self-closure guard | Verifies the governance stack proves itself by requiring registered guards/probes to have tests, requiring default guards to appear in CI workflows, checking CI workflows for timeout coverage, and failing on newly orphaned typed contracts surfaced by `check_contract_connectivity.py`. Supports `--format` and `--output`. |
| `dev/scripts/checks/check_bundle_workflow_parity.py` | Bundle/workflow parity guard | Verifies registry commands for `bundle.tooling` and `bundle.release` remain present in the owning CI workflows so policy bundles and workflow execution do not silently drift. |
| `dev/scripts/checks/check_bundle_registry_dry.py` | Bundle-registry DRY guard | Verifies canonical bundle definitions in `bundle_registry.py` use explicit composition layers instead of repeated command lists, validates shim-target authority for the registry entrypoint, and enforces the budget for widely shared commands before composition becomes mandatory. |
| `dev/scripts/checks/check_ide_provider_isolation.py` | IDE/provider coupling audit | Blocks mixed host/provider executable statements outside explicit policy-owner allowlists (default blocking mode; optional `--report-only`). Scanner ignores import blocks and `#[cfg(test)]` sections so enforcement stays runtime-focused. |
| `dev/scripts/checks/check_compat_matrix.py` | Compatibility matrix schema gate | Validates `dev/config/compat/ide_provider_matrix.yaml` required hosts/providers, per-cell coverage, duplicate/missing entries, and provider IPC-mode policy labels. |
| `dev/scripts/checks/compat_matrix_smoke.py` | Compatibility matrix runtime smoke gate | Cross-checks matrix coverage against runtime host/provider enums (`runtime_compat`) plus IPC provider enum (`ipc/protocol`) and enforces explicit non-IPC labeling for runtime-visible non-IPC providers. |
| `dev/scripts/checks/check_naming_consistency.py` | Host/provider naming consistency gate | Verifies host/provider IDs and provider-token labels stay aligned across runtime enums/registry, compatibility-matrix IDs, and tooling-owned token contracts (matrix policy, smoke policy map, and isolation scanner token regex). |
| `dev/scripts/checks/check_repo_url_parity.py` | Repository URL parity guard | Verifies canonical repository URL consistency across Cargo/PyPI/docs metadata surfaces. |
| `dev/scripts/checks/check_python_broad_except.py` | Python broad-except rationale guard | Fails when newly added `except Exception` / `except BaseException` handlers appear in repo-owned Python tooling or Operator Console code without a nearby `broad-except: allow reason=...` comment. The guard is diff-aware by default, excludes tests, and supports `--paths` for targeted local verification. |
| `dev/scripts/checks/check_pytest_runtime_policy.py` | Pytest runtime policy guard | Fails when canonical bundles include raw pytest commands or the root pytest config loses bounded, fail-fast discovery defaults. |
| `dev/scripts/checks/check_python_subprocess_policy.py` | Python subprocess policy guard | Fails when repo-owned Python tooling or Operator Console code calls `subprocess.run(...)` without an explicit `check=` keyword. Tests are excluded so intentional fixture/process assertions can stay flexible, and `--since-ref/--head-ref` support lets AI-guard/post-push lanes scope the scan to changed files. |
| `dev/scripts/checks/check_command_source_validation.py` | Command-source validation guard | Fails when Python command construction uses `shlex.split(...)` on CLI/env/config input, forwards raw `sys.argv` into subprocess argv, or threads env-controlled command values into command runners without a validator helper. It is part of the default shared bundle guard floor; repo policy can still narrow target roots for external-adopter pilots. |
| `dev/scripts/checks/check_rust_test_shape.py` | Rust test-shape non-regression guard | Fails when changed Rust test files cross soft/hard size budgets or grow oversize hotspots beyond configured growth limits. |
| `dev/scripts/checks/check_rust_lint_debt.py` | Rust lint-debt non-regression guard | Fails when changed non-test Rust files increase `#[allow(...)]` usage, `#[allow(dead_code)]` usage, `unwrap/expect` calls, `unwrap_unchecked/expect_unchecked` calls, or panic-macro paths; supports dead-code inventory/report output and optional policy flags (`--fail-on-undocumented-dead-code`, `--fail-on-any-dead-code`). |
| `dev/scripts/checks/check_rust_best_practices.py` | Rust best-practices non-regression guard | Fails when changed non-test Rust files increase reason-less `#[allow(...)]`, undocumented `unsafe { ... }` blocks, public `unsafe fn` surfaces lacking `# Safety` docs, `unsafe impl` blocks missing nearby safety rationale, `std::mem::forget`/`mem::forget` usage, `Result<_, String>` surfaces, suppressed channel-send results (`let _ = tx.send(...)` / `_ = tx.try_send(...)`), suppressed event-emitter results (`let _ = sender.emit(...)`), bare detached `thread::spawn(...)` statements without a nearby `detached-thread: allow reason=...` note, `unwrap()`/`expect()` on `join`/`recv` paths, suspicious `OpenOptions::new().create(true)` chains that do not make overwrite semantics explicit via `append(true)`, `truncate(...)`, or `create_new(true)`, direct `==` / `!=` comparisons against float literals in runtime Rust code, app-owned persistent TOML writes that still use direct overwrite helpers (`fs::write`, `File::create`, truncate-open `OpenOptions`) instead of a temp-file swap, or hand-rolled persistent TOML parsers in config/state readers when the repo already has the `toml` crate available. Supports `--absolute` for full-tree Rust audits instead of changed-file-only non-regression scans. |
| `dev/scripts/checks/check_rust_compiler_warnings.py` | Changed-file Rust compiler warning guard | Runs a no-run `cargo test --message-format=json` compile and fails when rustc warnings resolve to changed repo-owned `.rs` files; catches warning-only debt such as `unused_imports` that Clippy histogram gating does not cover. Supports `--since-ref/--head-ref`, `--absolute`, and offline `--input-jsonl` replay. |
| `dev/scripts/checks/check_serde_compatibility.py` | Serde tagged-enum compatibility guard | Fails when changed non-test Rust files introduce internally or adjacently tagged `Deserialize` enums without either a `#[serde(other)]` fallback variant or a nearby `serde-compat: allow reason=...` comment documenting intentional fail-closed behavior. |
| `dev/scripts/checks/check_rust_runtime_panic_policy.py` | Runtime panic policy non-regression guard | Fails when changed non-test Rust files introduce net-new unallowlisted runtime `panic!` call-sites; allowlisted panic paths require nearby `panic-policy: allow reason=...` rationale comments. Supports `--absolute` for full-tree audits. |
| `dev/scripts/checks/check_rust_audit_patterns.py` | Rust audit regression guard | Scans runtime Rust sources under `rust/src` and fails when known critical audit anti-patterns reappear (UTF-8-unsafe prefix slicing, byte-limit truncation via `INPUT_MAX_CHARS`, single-pass `redacted.find(...)` secret redaction, deterministic timestamp-hash ID suffixes, and lossy `clamped * 32_768.0 as i16` VAD casts). |
| `dev/scripts/checks/check_rust_security_footguns.py` | Rust security-footguns non-regression guard | Fails when changed non-test Rust files add risky AI-prone patterns (`todo!/unimplemented!/dbg!`, `unreachable!()` in runtime hot paths, shell-style process spawns, permissive `0o777/0o666` modes, weak-crypto references like MD5/SHA1, PID wrap-prone casts such as `child.id() as i32` / `libc::getpid() as i32`, or syscall-return casts to unsigned integer types without an explicit sign guard first); `#[cfg(test)]` blocks are excluded from this runtime-focused scan. |
| `dev/scripts/checks/check_function_duplication.py` | Function-body duplication guard | Growth-based guard that detects identical normalized function bodies (>= 6 lines) across different source files; uses the same Rust/Python function scanners as `check_code_shape.py`; only flags duplications introduced by the current changeset. Registered as an AI guard in `devctl check --profile ci`. |
| `dev/scripts/checks/check_duplication_audit.py` | Periodic duplication audit | Runs/reads `jscpd` JSON reports, enforces report freshness, optionally fails when duplication percentage crosses the configured threshold, supports an explicit built-in fallback scanner (`--run-python-fallback`) when `jscpd` is unavailable in constrained environments, and now exposes advisory `--check-shared-logic` heuristics for newly added Python/tooling files (`new-file-vs-shared-helper`, `orchestration-pattern-clone`). |
| `dev/scripts/checks/check_duplication_audit_support.py` | Duplication-audit shared support helpers | Shared status derivation, markdown rendering, Python fallback-scanner helpers, and advisory shared-logic candidate detection used by `check_duplication_audit.py`; not invoked directly by command bundles. |
| `dev/scripts/checks/check_test_coverage_parity.py` | Check-script test coverage parity guard | Flags check scripts that are missing corresponding unit tests under `dev/scripts/devctl/tests/`. |
| `dev/scripts/checks/check_clippy_high_signal.py` | Clippy high-signal lint baseline guard | Compares observed lint histogram JSON against `dev/config/clippy/high_signal_lints.json` and fails on baseline growth for tracked lints. |
| `dev/scripts/badges/ci.py` | CI badge renderer | Canonical JSON badge renderer for CI status. |
| `dev/scripts/badges/clippy.py` | Clippy badge renderer | Canonical JSON badge renderer for clippy warning counts. |
| `dev/scripts/badges/mutation.py` | Mutation badge renderer | Canonical JSON badge renderer for mutation score output. |
| `dev/scripts/checks/check_rustsec_policy.py` | RustSec policy gate | Enforces advisory thresholds. |
| `dev/scripts/checks/check_facade_wrappers.py` | Python facade-wrapper non-regression guard | Fails when changed Python files grow facade-heavy modules (files with more than 3 pure-delegation wrappers that just forward all arguments to another function). Tests are excluded; supports `--since-ref/--head-ref` and `--format`. |
| `dev/scripts/checks/check_god_class.py` | God-class non-regression guard | Fails when changed Rust or Python files introduce classes/impl blocks with excessive method counts (Python: >20 methods or >10 instance vars, Rust: >20 impl methods). Tests are excluded; `#[cfg(test)]` blocks are stripped for Rust scans; supports `--since-ref/--head-ref` and `--format`. |
| `dev/scripts/checks/check_platform_contract_sync.py` | Platform-contract sync guard | Fails when the shared `platform-contracts` rows drift from the lifecycle/authority spec dataclasses used by the reusable backend blueprint, so field additions like `shutdown_entrypoints` or `forbidden_actions` cannot land in only one layer. Supports `--format`. |
| `dev/scripts/checks/check_platform_contract_closure.py` | Platform contract-closure guard | Fails when the current executable platform contract families drift across the `platform-contracts` blueprint, shared runtime dataclass models, durable artifact schema metadata, or startup-surface contract-routing tokens (`startup_surface_tokens`). The current bounded scope covers `TypedAction`, `RunRecord`, `ArtifactStore`, `ControlState`, `ReviewState`, `ReviewerRuntimeContract`, `Finding`, `FindingReview`, `FindingBacklog`, `PlatformFindingIngest`, `DecisionPacket`, `ProbeReport`, `ReviewPacket`, `ReviewTargets`, `FileTopology`, `ProbeAllowlist`, plus AST-backed consumer-route proofs for `PlanPhase`, `PlanTask`, and `FindingBacklog` so typed planning/backlog models cannot land as dead producer-only seams. Connectivity-registry reader verification emits typed `MissingConnectionFinding` rows instead of silently removing declared readers; `aspirational_gap_count` must stay `0` unless a committed override justifies `mistakenly_declared` or `deferred_consumer`. Supports `--format`. |
| `dev/scripts/checks/check_runtime_spine_closure.py` | Runtime-spine closure guard | Fails when `SYSTEM_MAP.md` section 0.6 stops carrying the closure rule, when the guard is not registered, or when a ❌/⚠️ runtime-spine object lacks an active owner reference in the active plan or typed plan store. This turns the documented "promote one gap per session" convention into executable pressure so compaction, ACK, or packet expiry cannot erase known architecture gaps without durable typed ownership. Supports `--format`. |
| `dev/scripts/checks/check_contract_connectivity.py` | Contract-connectivity guard | Scans `dev/scripts/devctl/runtime`, `governance`, `platform`, and `app/operator_console` dataclasses, traces importer reachability through Python AST import usage, flags unreferenced or internal-only contracts, purpose-guided semantic duplicates, and raw-dict stranded consumers, and blocks only new findings unless `--absolute` is requested. Supports `--absolute`, `--since-ref`, `--head-ref`, and `--format`. |
| `dev/scripts/checks/check_typed_enum_connectivity.py` | Typed enum connectivity guard | Warning-only first-pass guard that scans repo-owned Python `Enum` / `StrEnum` members and AST decision consumers so enum values cannot be added without a visible branch, policy map, comparison, or typed reference. Supports `--format`, `--include-tests`, and `--fail-on-disconnected` for later Slice C promotion. |
| `dev/scripts/checks/check_checkpoint_budget_shape.py` | Checkpoint-budget shape guard | Stable shim entrypoint for the startup-authority checkpoint-budget classifier; validates that over-budget work routes through typed checkpoint/repair state instead of raw continuation. Supports `--format`. |
| `dev/scripts/checks/check_startup_authority_contract.py` | Startup-authority contract guard | Validates the live `ProjectGovernance` bootstrap payload by requiring the core startup authority files, non-empty repo identity, plan-registry roots/order, fail-closed checkpoint-budget truth, working-tree-to-index Python import atomicity, and committed-tree (`HEAD`)-to-`HEAD` importer coherence; fresh repos without a first commit skip the committed-tree layer until `HEAD` exists. Supports `--format`. |
| `dev/scripts/checks/check_mobile_relay_protocol.py` | Mobile relay projection contract guard | Fails when the shared mobile relay payload shape drifts across the Rust/controller emitters, Python projection tooling, and iOS consumer contract. Supports `--since-ref/--head-ref` and `--format`. |
| `dev/scripts/checks/check_daemon_state_parity.py` | Daemon-state parity guard | Validates the Rust daemon lifecycle/state seam against the Python runtime models by checking lifecycle-event coverage plus required daemon-state and agent-info fields. Supports `--format`. |
| `dev/scripts/checks/check_nesting_depth.py` | Nesting-depth non-regression guard | Fails when changed Rust or Python files introduce functions with deeply nested control flow (Python: >4 indent levels, Rust: >5 brace-depth levels). Uses the same function scanners as `check_code_shape.py`; tests are excluded; supports `--since-ref/--head-ref` and `--format`. |
| `dev/scripts/checks/check_parameter_count.py` | Parameter-count non-regression guard | Fails when changed Rust or Python files introduce functions with excessive parameter counts (Python: >6 params, Rust: >7 params, excluding `self`/`cls`/`&self`/`&mut self`). Tests are excluded; `#[cfg(test)]` blocks are stripped for Rust scans; supports `--since-ref/--head-ref` and `--format`. |
| `dev/scripts/checks/check_python_dict_schema.py` | Python dict-schema non-regression guard | Fails when changed Python files grow large untyped dict literals (>= 6 string keys suggesting a missing dataclass) or weak `dict[str, Any]` type aliases. Tests are excluded; supports `--since-ref/--head-ref` and `--format`. |
| `dev/scripts/checks/check_python_typed_seams.py` | Python typed-seams guard | Stable shim entrypoint for the typed-seam guard that blocks configured `object` + repeated `getattr()` fixed-field bags on portable runtime seams while the implementation lives under `dev/scripts/checks/python_typed_seams/`. |
| `dev/scripts/checks/check_python_global_mutable.py` | Python default-state trap non-regression guard | Fails when changed Python files introduce new `global` statements, mutable default arguments (`list`, `dict`, `set`, `defaultdict`, `deque`), function-call default arguments, or dataclass fields that evaluate mutable/call defaults eagerly instead of using `field(default_factory=...)`. Tests are excluded; supports `--since-ref/--head-ref` and `--format`. |
| `dev/scripts/checks/check_python_design_complexity.py` | Python design-complexity non-regression guard | Fails when changed Python files add functions whose branch count or return-statement count crosses the repo-policy thresholds (portable defaults: branches >30, returns >10 so another repo can ratchet from a conservative baseline), or when already-over-limit functions become even more branchy/return-heavy. Tests are excluded; supports `--since-ref/--head-ref` and `--format`. |
| `dev/scripts/checks/check_python_cyclic_imports.py` | Python cyclic-import non-regression guard | Fails when changed Python files introduce new top-level local import cycles inside the configured Python guard roots. Cycle allowlists are repo-policy owned so another repo can adopt the same engine without editing script code. Tests are excluded; supports `--since-ref/--head-ref` and `--format`. |
| `dev/scripts/checks/check_python_suppression_debt.py` | Python suppression-debt non-regression guard | Fails when changed Python files add more lint/type suppression comments than the base version (`# noqa`, `# type: ignore`, `# pylint: disable`, `# pyright: ignore`). Uses tokenized comment scanning so string literals and prose examples do not count; supports `--since-ref/--head-ref` and `--format`. |
| `dev/scripts/checks/check_structural_similarity.py` | Structural-similarity non-regression guard | Fails when changed Rust or Python files introduce cross-file function pairs with identical control-flow shape but different variable names (copy-paste-and-rename detection). Unlike `check_function_duplication` which catches identical normalized bodies, this guard normalizes identifiers and literals to detect structurally equivalent functions (>= 8 body lines). Tests are excluded; supports `--since-ref/--head-ref` and `--format`. |

## Devctl Command Set

Machine-first output note:

- JSON-canonical report/packet surfaces (`governance-*`, `platform-contracts`,
  `system-picture`, `probe-report`, `data-science`, `loop-packet`) now treat
  stdout as a compact control channel when you run
  `--format json --output <path>`: the full compact JSON artifact is written
  to the file, while stdout emits only a compact JSON receipt with artifact
  metadata such as path/hash/size/token estimate. This keeps agent loops
  small and lets automation decide whether it needs to reread the artifact.

- `check`: fmt/clippy/tests/build profiles (`ci`, `prepush`, `release`, `maintainer-lint`, `pedantic`, `quick`, `fast`, `ai-guard`)
  - Runs setup gates (`fmt`, `clippy`, AI guard scripts) and test/build phases in parallel batches by default.
  - Tune parallelism with `--parallel-workers <n>` or force sequential execution with `--no-parallel`.
  - The orphaned/stale repo-related process sweep is opt-in with `--with-process-sweep-cleanup` (VoiceTerm PTY/test trees, repo-runtime cargo/target trees, repo-tooling wrappers, detached `PPID=1`, plus stale active runners aged `>=600s`).
  - `--no-process-sweep-cleanup` remains as an explicit compatibility spelling for preserving the default no-sweep behavior.
  - `quick` / `fast` also run host-side `process-cleanup --verify --format md` by default; use `--no-host-process-cleanup` only when a live process tree must be preserved and the exception is recorded.
  - Active AI guards now resolve from `dev/config/devctl_repo_policy.json`, so
    repo-local enablement/default arguments are policy-driven rather than
    hard-coded into the orchestration path.
  - Treat the repo policy file and any touched preset JSON files as committed
    source-of-truth config. If CI should see a policy change, commit
    `dev/config/devctl_repo_policy.json` and the relevant
    `dev/config/quality_presets/*.json` files in the same change.
  - Use `--quality-policy <path>` or `DEVCTL_QUALITY_POLICY` to resolve the
    same engine against another repo policy file without editing orchestration
    code.
  - AI guard pack includes shape (file + function length for Rust ≤100 / Python ≤150), duplicate type detection, structural complexity, Rust test-shape, IDE/provider isolation, compat matrix schema/smoke, naming consistency, Rust lint debt, Rust best practices, runtime panic policy, Rust audit patterns, Rust security footguns, Python default-state traps, Python design complexity, Python cyclic imports, Python suppression-debt growth, and function-body duplication (identical bodies ≥6 lines across files).
  - `pedantic` is advisory-only: use it for intentional lint-hardening sweeps, not as a default CI or release blocker.
  - `check --profile pedantic` writes structured artifacts to `dev/reports/check/clippy-pedantic-summary.json` and `dev/reports/check/clippy-pedantic-lints.json`; consume those through `report --pedantic` or `triage --pedantic`, and use `--pedantic-refresh` only when you explicitly want those commands to regenerate the artifacts inline.
  - `release` profile includes wake-word regression/soak guardrails, non-blocking mutation-score reporting (`--report-only` reminders), and strict remote release gates (`status --ci --require-ci`, CodeRabbit, Ralph).
  - Structured `check` report timestamps are UTC for consistent CI/local correlation.
- `check-router`: path-aware lane selector for `bundle.docs|bundle.runtime|bundle.tooling|bundle.release`
  - Uses changed files (working tree or `--since-ref/--head-ref`) to choose lane.
  - Reports required runtime risk add-ons and selection rationale.
  - Lane rules and add-ons resolve from `repo_governance.check_router` in the
    active repo policy; use `--quality-policy <path>` to reuse the same router
    in another repo without changing code.
  - Governed markdown now routes registry-first: plan/self-hosting/
    compatibility docs come from typed doc authority (`ProjectGovernance`
    `DocRegistry` plus surface context), so custom-layout repos do not need
    VoiceTerm-shaped `dev/active/*` buckets for tooling classification.
  - The shared `AGENTS.md` boot card and ignored local `CLAUDE.md` peer
    projection render from the same typed authority in
    `dev/scripts/devctl/governance/task_router_contract.py`.
  - `--execute` runs the routed bundle commands plus add-ons from `bundle_registry.py`; publication preflight omits `--keep-going` by default so the first blocking route stops before `git push` starts. Use `--keep-going` only for explicit audit/full-report proof when repo policy or an operator command asks for it. Reports include a typed `CheckRouterGuardCoverageReceipt` plus `GuardRemediationAction` rows, and `execution_plan` separates serial-required projection/status commands from parallel-safe guard rows so automation can prove both safety and coverage.
- `progress-status`: read-only view of typed `StageProgressEvent` artifacts
  written by long-running `run_cmd` child processes and governed VCS phases.
  Use it when a guard/preflight appears quiet; it reports the latest command
  start, no-output heartbeat, completion/failure, and recent event tail without
  launching conductors, waking packet handlers, or mutating typed queues.
  - Range-aware universal guards such as Python broad-except and command-source validation receive the router's `--since-ref/--head-ref` automatically, which keeps clean-worktree push preflight from missing already-committed Python changes.
  - Unknown paths escalate to the stricter tooling lane.
- `test-python`: bounded Python test adapter for repo-owned pytest suites
  (`devctl`, `operator-console`, or `root`), with fail-fast defaults plus
  session/per-test timeouts enforced by the repo pytest plugin. Explicit
  multi-path runs can shard by file with `--parallel-workers <n>` while still
  reporting ordered shard results; `--no-parallel` keeps a sequential
  fallback. `check-router` adds focused devctl tests for tooling changes and
  Operator Console tests only for touched `app/operator_console/**/*.py`
  paths; focused devctl add-ons split selected targets into serial
  single-target sessions with a 420s measured floor, measured per-target
  overrides for known-heavy files, and a bounded per-test cap.
  Generated instruction boot cards route agents through typed startup,
  session, graph, and `/develop` commands; the live command inventory remains
  owned by `SystemCatalog` / `devctl` listing surfaces, not AGENTS prose.
- `mutants`: mutation test helper wrapper
- `mutation-score`: threshold/freshness checker for outcomes (strict by default; use `--report-only` for non-blocking reminders)
- `docs-check`: docs coverage + tooling/deprecated-command policy guard (`--strict-tooling` also runs active-plan sync + multi-agent sync + markdown metadata-header + workflow-shell hygiene + guide-contract sync + bundle/workflow parity + stale-path audit)
  - Canonical doc sets and deprecated-reference patterns resolve from
    `repo_governance.docs_check` in the active repo policy; use
    `--quality-policy <path>` to point the same command at another repo's
    governance contract.
  - `tooling_required_doc_aliases` lets a generated required surface be
    satisfied by an explicit durable owner doc. VoiceTerm uses this for
    `AGENTS.md` -> `dev/active/MASTER_PLAN.md`, preventing docs-check from
    forcing manual edits to generated boot cards while still requiring owner
    documentation for tooling/process changes.
  - If you add or promote a shared guard, treat `quality-policy --format md`,
    `check_guard_enforcement_inventory.py`, and
    `check_bundle_workflow_parity.py` as one closure set before push so AI
    surfaces, bundle authority, CI workflows, and `check_governance_closure.py`
    do not drift. Subject-driven guards should use explicit CI smoke coverage
    with `--stdin --allow-empty`; the governed push adapter supplies real
    base/head refs for publication-scope integrity.
  - When `repo_governance.docs_check` is empty or partial, tooling-doc
    requirements now derive from typed governance authority (`DocRegistry`,
    tracker/docs-authority paths, and repo-owned surface docs) instead of
    silently falling back to VoiceTerm's `AGENTS.md` / `dev/active/*` set.
    The shared routing helper
    `dev/scripts/devctl/governance/governed_doc_routing.py` should prefer
    typed `ProjectGovernance` doc paths for process/development/architecture
    and scripts README surfaces before it consults surface-generation context
    fallbacks.
- `hygiene`: archive/ADR/scripts governance checks plus orphaned/stale repo-related host-process detection (matched `cargo test --bin voiceterm`, `target/debug/deps/voiceterm-*`, stress sessions, repo-runtime cargo/target trees, orphaned repo-tooling wrappers that execute `dev/scripts/**`, repo-owned review-channel conductor trees, and repo-cwd background helpers such as `python3 -m unittest`, direct `bash dev/scripts/...` wrappers, or `qemu/node/make` descendants that outlive their repo-owned parent; stale active threshold: `>=600s`; attached supervised review-channel conductors remain visible but are no longer promoted into stale failures unless they detach/background); ADR checks include numbering-gap governance (`Retired ADR IDs`, `Reserved ADR IDs`), `next:` pointer validation, active backlog parity checks between `MASTER_PLAN` and `autonomous_control_plane`, and stale ADR reference-pattern detection (hard-coded ADR counts/ranges) in long-lived governance docs; includes automatic report-retention drift warnings for stale `dev/reports/**` run artifacts and tracked external-publication drift warnings when watched repo paths outpace synced papers/sites; `--strict-warnings` promotes warnings to failures, `--strict-release-warnings` keeps release-branch strictness while auto-ignoring release-maintenance warning families on non-release branches, `--ignore-warning-source mutation_badge` keeps stale mutation-badge freshness visible without failing non-release tooling lanes; optional `--fix` removes detected `dev/scripts/**/__pycache__` directories and re-audits scripts hygiene
- `process-cleanup`: host-side cleanup for orphaned/stale repo-related process trees; expands cleanup roots to full descendant trees so leaked PTY children, repo-cwd background helpers, orphaned tooling descendants, and stale supervised review-channel conductors are reaped with their parent wrappers when possible, skips recent active processes by default, and `--verify` reruns strict host audit after cleanup
- `process-audit`: read-only host-side Activity Monitor equivalent for repo-related process trees; reports matched roots plus descendants, includes repo-cwd runtime/tooling helpers that would otherwise look generic in Activity Monitor, fails fast when `ps` access is unavailable, preserves registered supervised review-channel conductors as visible non-blocking rows only while their embedded resume/review-state `head_sha` matches current `HEAD`, and `--strict` turns leftover runtime/test trees or stale/orphaned repo-related helpers into a blocking failure before handoff
- `publication-sync`: tracked external publication report/record surface that compares watched repo paths against the last synced source commit for papers/sites and records a new baseline after external publish
- `push`: policy-driven guarded push wrapper for the current branch; resolves branch/remote rules from `repo_governance.push`, runs the configured preflight path, defaults to non-mutating validation, and uses the configured post-push bundle after `--execute`. Static bundle authority still advertises the template `--since-ref` values, but the governed runtime rewrites diff-sensitive post-push commands to the exact preflight-resolved base for the current branch. When an active compatibility bridge exists, preflight now refreshes typed review status and reprojects `bridge.md` before the blocking checks run, then auto-commits a managed projection receipt if the only remaining dirty paths are governed receipt/projection artifacts, so stale role-marker bridge text does not strand an otherwise valid push or leave a green push with tracked projection drift.
  Startup/work-intake next-step projections consume the same push-preflight
  policy and only append `--keep-going` for explicit audit mode
  (`audit_mode=true` or legacy `fail_fast_on_blocker=false`). Managed
  projection receipt commits also no-op when `HEAD` is already a managed
  ReviewSnapshot/generated-surface receipt, so generated-surface cleanup cannot
  create a receipt-on-receipt chain.
  Push preflight also passes policy-owned `parallel_workers` into
  `check-router`, so parallel-safe guard rows can run in bounded worker batches
  whenever router execution is in an audit/keep-going phase.
- `path-audit`: stale-reference scan for legacy check-script paths (skips `dev/archive/`)
- `path-rewrite`: auto-rewrite legacy check-script paths to canonical registry targets (use `--dry-run` first)
- `sync`: guarded branch-sync workflow (clean-tree preflight, remote/local ref checks, `--ff-only` pull, optional `--push` for ahead branches, and start-branch restore)
- `integrations-sync`: guarded submodule sync/status command for pinned federated integration sources defined in `control_plane_policy.json`
- `integrations-import`: allowlisted selective importer from pinned federated sources into controlled destination roots with JSONL audit logging
- `cihub-setup`: allowlisted CIHub repo-setup helper (`detect/init/update/validate`) with capability probing, preview/apply modes, and strict unsupported-step gating
- `security`: RustSec policy checks plus optional workflow/code-scanning security scans (`--with-zizmor`, `--with-codeql-alerts`) and Python-scope selection (`--python-scope auto|changed|all`)
- `release`: tag + notes flow (legacy release behavior)
- `release-gates`: shared release-gate helper (`check_coderabbit_gate` for triage + preflight workflows, plus `check_coderabbit_ralph_gate`) with common wait/poll defaults
- `release-notes`: git-diff driven markdown notes generation
- `ship`: full release/distribution orchestrator with step toggles and optional metadata prep (`--prepare-release`); `--verify` includes release-gate verification (CodeRabbit triage + Ralph), deterministic parallel aggregation for its independent subchecks, and version reads from TOML roots (`[package]`/`[project]`) with Python 3.10-compatible fallback parsing
- `homebrew`: Homebrew tap update flow (URL/version/SHA + canonical formula `desc` sync + legacy Cargo manifest path rewrite to `libexec/rust/Cargo.toml`)
- `pypi`: PyPI build/check/upload flow
- `orchestrate-status`: one-shot orchestrator accountability view (active-plan sync + multi-agent sync guard status with git context)
- `orchestrate-watch`: SLA watchdog for stale lane updates and overdue instruction ACKs
- `status` and `report`: machine-readable project status outputs (optional guarded Dev Mode session summaries via `--dev-logs`, `--dev-root`, and `--dev-sessions-limit`; both can now inline aggregated review-probe summaries via `--probe-report`, and `report` also supports Rust audit aggregation via `--rust-audits`, optional matplotlib charts via `--with-charts`, and bundle emission via `--emit-bundle`)
  - `--quality-policy <path>` lets the probe-backed status/report views resolve
    another repo policy without changing shared orchestration code.
- `data-science`: rolling telemetry snapshot builder that summarizes devctl event metrics plus swarm/benchmark agent-size productivity history, watchdog guarded-coding episodes, and governance-review false-positive/cleanup metrics; writes `summary.{md,json}` + SVG charts under `dev/reports/data_science/latest/` and supports local source/output overrides for experiments
- `dogfood`: explicit dev-mode coverage ledger over live commands, guards, probes, and role lanes; `--record` appends one `DogfoodRun` row to `dev/reports/dogfood/runs.jsonl`, plain `--report` (or no mode flag) refreshes `dev/reports/dogfood/latest/summary.{md,json}`, coverage derives from the live command catalog plus registered `check_*.py` / `probe_*.py` entrypoints instead of fixed counts, and `--record-governance` refreshes a linked `signal_type=dogfood` governance-review row through `PlatformFindingIngest` / `FindingBacklog` with a stable finding id using the live target path/default classification unless you override it with `--finding-path`, `--governance-check-id`, `--finding-class`, `--recurrence-risk`, or `--prevention-surface`
  - `--run-scenario plan41-tandem` emits a typed `DogfoodScenarioReport` over the existing `DashboardSnapshot`, review-state router projection, packet queue, agent-mind rows, coordination readiness, and dogfood backlog. It is report-only by default, and `--record --dev-mode --run-scenario plan41-tandem` persists a `target_kind=scenario` row with the scenario status instead of launching unmanaged mutation.
  - Campaign/system-test rows can also carry `--campaign-id`, `--scenario-id`, `--repo-scope`, `--repo-label`, `--repo-path`, `--topology`, `--lane-role`, repeatable `--live-run-ref`, and repeatable `--governance-finding-id`; the same linkage is rendered in dogfood summaries and copied into linked governance notes for later cross-surface audit.
  - Failed non-read-only devctl commands now run the Slice A finalization hook by default in report-only mode. The hook writes one `DogfoodRun` row plus a stable `signal_type=dogfood` FindingBacklog/governance-review row through the same `PlatformFindingIngest` seam after audit emission, skips read-only commands plus dogfood/governance recursion and artifact-only commands, and remains fail-open; use `DEVCTL_PLATFORM_FINDING_INGEST_AUTO_RECORD=0` for the compatibility opt-out or `DEVCTL_PLATFORM_FINDING_INGEST_DISABLE=1` as the kill switch.
  - Dogfood records development evidence only. Runtime collaboration roles still come from typed ownership (`CollaborationSession.mutation_owner`, `verification_owner`, `watcher_owner`) and the mirrored `AuthoritySnapshot` fields.
  - Repo mutation should be authorized through typed actor-authority grants (`repo.commit`, `repo.stage`, `repo.stage_handoff`) on the live mutation owner; approval grants (`approval.commit`) stay separate from repo-write authority.
- `governance-import-findings`: import external raw findings into the managed external ledger/summary from JSON, JSONL, or compatibility markdown. Use `--input-format md` for `LIVE_RUN.md` (or rely on `.md` / `.markdown` / `.mdown` auto-detection); markdown imports reuse the repo-owned `LIVE_RUN` parser and emit repo-scoped sync ids in the form `<repo_name>:Qnn` so repeated imports collapse by latest section instead of creating cross-repo collisions. `LIVE_RUN.md` stays compatibility evidence only; canonical triage and closeout still flow through the external findings ledger plus `governance-review`.
- `governance-review`: adjudicated finding ledger for hard-guard/probe outcomes; records reviewed findings plus their systemic disposition into `dev/reports/governance/finding_reviews.jsonl`, writes refreshed `review_summary.{md,json}` artifacts under `dev/reports/governance/latest/`, and gives the repo a durable scoreboard for false-positive rate, fixed findings, deferred debt, architectural absorption choices, observer/self-audit finding types (`signal_type=observer` plus optional `finding_type`), and optional probe-guidance adoption (`guidance_id` / `guidance_followed`). When `--record` uses `--prevention-surface guard` or `--prevention-surface probe`, it also appends a `GuardPromotionCandidate` row to the repo-pack-resolved promotion queue (default `dev/reports/governance/guard_promotion_candidates.jsonl`) and includes the candidate id/path in the refreshed JSON summary for that recorded row.
- Shared context-escalation packets now also consume bounded recent
  `review_summary.json` history plus the latest quality-feedback
  recommendations so Ralph/autonomy/review-channel prompt families can read
  fix history and repo-quality tuning hints without loading those artifacts
  separately. The same packet family now also carries bounded watchdog-episode
  digests, command-reliability lines from `data_science summary.json`, and
  decision constraints derived from matched `DecisionPacket` metadata.
- `probe-report`: aggregated review-probe surface that runs every registered `probe_*.py` script, renders markdown/terminal/json summaries, writes stable `dev/reports/probes/review_targets.json`, and refreshes `dev/reports/probes/latest/summary.{md,json}` plus `file_topology.json`, `review_packet.{json,md}`, and hotspot `hotspots.{mmd,dot}` artifacts for agent coaching, AI/human design review, and audit. The probe catalog now includes architecture-aware connectivity checks via `probe_architecture_connectivity`, review-channel event id uniqueness via `probe_event_id_uniqueness`, event-field naming drift via `probe_event_field_naming_consistency`, command-result JSON envelope checks via `probe_command_result_contract`, peer packet lag via `probe_inter_agent_communication_lag`, packet carry-forward and durable plan/finding ingestion debt via `probe_packet_carry_forward_debt`, cohesion-heavy mixed-concern detection via `probe_mixed_concerns`, hotspot-aware split recommendations via `probe_split_advisor`, and naming cleanup hints via `probe_term_consistency`, so typed contract-reader gaps, event-log integrity drift, command parsing drift, delayed Codex/Claude feedback, lifecycle carry-forward gaps, split-brain structure, and legacy public vocabulary show up in the same packet.
  - Use `--adoption-scan` for first-run/full-surface repo onboarding when there
    is no trustworthy baseline ref yet.
  - Repo-root `.probe-allowlist.json` entries shape this canonical path too:
    `design_decision` rows stay visible as typed decision packets instead of
    active debt, and matching is by `file` + `symbol` + `probe` when the entry
    declares a probe id. The root allowlist payload may carry
    `schema_version: 1` plus `contract_id: "ProbeAllowlist"`.
    `decision_mode` governs whether the AI may auto-apply,
    should recommend, or must explain and wait for approval.
- `quality-policy`: read-only resolver for the active guard/probe policy; shows
  resolved capabilities, scope roots, active steps, per-guard configs, and
  warnings, and accepts
  `--quality-policy <path>` so maintainers can validate portable presets before
  running `check`, `probe-report`, or the probe-backed status/report/triage
  surfaces
  - Active probes also resolve from `dev/config/devctl_repo_policy.json`, so a
    different repo can reuse the same engine by changing policy instead of
    editing the command implementation.
  - Treat this as the live enabled-inventory view. Numeric code-shape limits
    still come from the code-owned policy modules under `dev/scripts/checks/`,
    and `render-surfaces` is what projects those limits into generated
    bootstrap surfaces.
- `render-surfaces`: policy-owned repo-pack surface generator and drift checker
  for instruction files and starter artifacts such as tracked `AGENTS.md`,
  local `CLAUDE.md`, slash/skill templates, and portable governance stubs
  - `--write` rewrites drifted outputs in place, while plain read mode is a
    safe check surface for local validation and `docs-check --strict-tooling`.
  - `--quality-policy <path>` lets another repo reuse the same generator
    against its own `repo_governance.surface_generation` contract.
  - `AGENTS.md` is the shared first-hop AI boot card. `CLAUDE.md` remains an
    ignored local peer projection for provider-specific startup, but `CODEX.md`
    is not a repo surface; Codex uses `AGENTS.md`. The generated boot card owns
    role discovery, help-discovery commands, and the memory-continuity warning
    so local notes or generic AI role names cannot become process authority by
    omission.
  - The same render pass derives boot-card routing from typed startup and
    governance context, so repo policy JSON does not carry duplicate bootstrap
    prose or a local Codex boot-card target.
- `develop`: read-only typed `/develop` controller report. It composes
  `DevelopmentModeTopology`, `DevelopmentScalingContract`, typed master-plan
  rows, packet attention, runtime work-board rows, auxiliary `agent-mind`
  context, guard/probe learning counts, and system discovery into a
  `DevelopmentLoopReport` for `status`, `next`, `show`, `start`, `watch`,
  `verify`, `submit`, `close`, `rollback`, `pause`, `resume`, `audit-guards`,
  `audit-packets`, `campaign`, and `launch --dry-run --max-cycles 1`.
  `campaign` renders the `RemoteControlCollaborationCampaign` read model so
  Codex/Claude remote-control dogfood can see role lanes, attachment proof,
  governed-exception lifecycle debt, bypass-retirement push proof, Pass-C
  role-matrix tracking, packet blockers, mode drift, and mutation/publication
  gates without waking agents, approving commits, executing exceptions, or
  granting authority. `agent-mind` appears only as
  `authority_policy=auxiliary_context_only`; typed
  `AgentWorkBoardProjection` / `AgentSyncProjection` and packet lifecycle rows
  remain authority. `audit-packets` renders `PacketDebtRemediationReport` so
  ACKed or expired packets with durable intent are routed toward
  plan/finding/lifecycle ownership instead of living only in packet transport.
  The report also emits `DecidedPacketDebtDetector` and `PacketBatchTriage`
  summaries so ACKed-but-unbuilt packets are visible as detector debt and
  grouped by reason, target, and durable-ingestion action.
  When packet attention already required `audit-packets`, the continuation
  path now promotes `PacketAttentionIngestionDecision.next_command` into the
  report's `next_step_command` and first `next_commands` row, so automation can
  fire the selected bounded packet action without re-running the same reducer.
  Archived packet-history rows remain audit evidence: terminal
  `applied`/`dismissed`/`archived` rows may still count toward carry-forward
  and provenance reports, but they must not block `/develop`, startup, or
  current-session projection as live packet attention.
  `audit-packets --drain-packets` runs the existing guarded deterministic
  plan-row ingestion writer for eligible rows and emits durable-ingestion
  receipts; it does not grant repo mutation. Live runtime-actionable pending
  packets to a conductor-backed actor now show up as delivery attention in
  `packet_attention` (`pending_delivery_packet_ids` and
  `latest_attention_packet_id`), while actionable instruction/action-request
  packets remain separately identified in `pending_actionable_packet_ids`.
  Peer `agent-mind` rows render `attention_hint` and append concrete
  inbox/agent-mind poll commands to `next_commands`; these are polling and
  typed-state refresh prompts, not wake or launch authority.
  Operator-targeted read-only `system_notice` packets remain operator-inbox
  inventory and are not treated as agent-loop wake pressure by
  `check_multi_agent_sync.py`.
  `--collaboration-mode <solo|pair_review|dashboard_led|intake_fanout|research_fanout|review_fanout|watcher_fanout|isolated_builder_fanout|dogfood_campaign>`
  and `--role-preset <dashboard|implementer|reviewer|architect|researcher|intake|tester|watcher|operator>`
  select the read-model lens rendered in `collaboration_mode`; they do not
  grant repo mutation authority. `development_role_adapters.py` is the shared
  Codex/Claude role-to-mode adapter matrix; `render-surfaces` projects it into
  `dev/templates/slash/develop/roles.md`, and provider command files such as
  `.claude/commands/develop.md` only pass those typed request fields into this
  same backend surface. They carry no policy, provider defaults, permissions,
  independent polling cadence, or repo-local path authority.
  `develop ingest-plan` / `develop ingest-intent` is the explicit write path
  for agent-authored planning sources outside the packet-debt drain: pass
  `--packet-id`, `--source`, `--body-file`, or `--body` plus a `--plan-row-id`
  when the source is not already a checklist row. `--source` reads a markdown
  plan file directly and records `source_kind=markdown_plan_file` unless a
  narrower kind is supplied. It upserts typed `PlanRow` rows in the repo-pack
  master-plan store and appends a `PlanIntentIngestionReceipt` under
  `dev/state/plan_ingestion_receipts.jsonl`; duplicate, rejected, or obsolete
  sources still produce a terminal typed receipt so chat text and temp files
  remain evidence, not authority.
  For packet sources, the row builder now first decomposes packet text that
  explicitly names `MP-NEW-*` rows or bounded ranges such as
  `MP-NEW-P204-S1..S4`. Only packets without concrete closure ids fall back to
  a single `PKT-BIND-REV-PKT-*` intake row. Range tokens are represented as
  typed spans before row-title extraction; the reducer removes the matched
  `Sx..Sy` text from the candidate title line so expanded rows do not receive
  `..S*` suffixes or copied range literals as titles.
  Packet attention is not a launch signal and is not proof that a visible
  terminal resumed. Packet post, delivery, follow-loop attention, inbox/watch,
  and packet-backed control paths may record typed attention and feed plan or
  scheduler state, but they must not spawn, replace, clean up, or externally
  wake provider sessions. A packet scoped to any `target_session_id` must be
  observed by that bound actor/session through typed polling; an unbound
  provider packet remains typed attention only. Session starts, rollover,
  replacement, and worker fanout require separate scheduler/runtime authority
  at an explicit task boundary.
  The current launch action is a report-only cycle; it does not spawn workers
  or grant mutation.
- `view`: typed presentation adapter over catalog/read-model surfaces. For
  agents, `view --surface ai` defaults to the existing AI slim renderer so the
  no-mode command returns the token-efficient command/guard/probe catalog
  instead of an unsupported `ai/summary` placeholder.
- `platform-contracts`: read-only reusable-platform blueprint that renders the
  shared layer model, backend contracts, frontend/client expectations,
  repo-local boundaries, adoption flow, and current portability status in one
  machine-readable command surface
  - Pair it with `python3 dev/scripts/checks/check_platform_contract_closure.py`
    after changing shared runtime contract models, durable packet-schema
    metadata, or startup-surface contract routing so the executable platform
    spine stays aligned in code and docs.
  - The closure guard now also enforces declared field-route families. Current
    bounded scope: `Finding.ai_instruction` must survive the Ralph,
    autonomy-loop, and `guard-run` consumers together,
    `DecisionPacket.decision_mode` must gate those same routes, and the
    typed planning/backlog seams (`PlanPhase`, `PlanTask`,
    `FindingBacklog`) must prove executable startup/triage/planning
    consumers through AST-backed field-route checks, so one surviving
    consumer no longer masks a dropped sibling or a dead internal type.
  - The closure guard also runs the cross-surface control-plane parity proof
    (`dev/scripts/checks/platform_contract_closure/field_routes_parity.py`),
    which feeds one deterministic `ControlPlaneReadModel` fixture through
    dashboard `_assemble`, `inputs_from_read_model`, `build_from_sources`,
    and the pure phone/mobile `_control_plane_section` helpers and fails on
    any cross-surface disagreement. As of 2026-04-07 `PARITY_FIELDS` also
    covers `reviewer_mode` and `operator_interaction_mode`,
    `_extract_from_auto_mode` reads `next_action` straight from
    `inputs.push_decision_action` (no `model.next_action` fallback), and a
    regression test pins that a broken `inputs_from_read_model` mapping
    surfaces as a typed `next_action` divergence. The session-resume
    extractor intentionally omits `reviewer_mode` because `SessionCachePacket`
    has no direct slot for it; the comparator skips absent fields.
  - As of 2026-04-29, `SessionPosture` is the canonical typed posture surface
    for `interaction_mode`, `reviewer_mode`, `effective_reviewer_mode`, and
    `actors[].occupied_lane`. Review-channel status, startup-context,
    dashboard, and session-resume should read that posture instead of
    recomputing mode/lane values. `agent_lane.lane` remains a compatibility
    alias; `occupied_lane` is the current-seat field, and capability grants are
    reported separately. In `remote_control`, bootstrap renderers include the
    no-local-GUI, no-ad-hoc-kill, and no-local-commit/push routing boundary.
    Startup/session projections also expose `PacketIntentAnchor` /
    `PlanIterationSession` continuity hints for planning packets; pending or
    expired packets do not become MasterPlan execution authority.
  - As of 2026-04-06 the field-route proof helper
    `_source_contains_any` in
    `dev/scripts/checks/platform_contract_closure/field_routes_surface_state.py`
    is AST-backed: it parses the candidate consumer module, strips
    module/class/function docstrings, and matches exact identifier,
    attribute, dotted-chain, or string-literal references. Docstring or
    comment mentions no longer satisfy the proof, and a substring overlap
    like `push_eligible` vs `push_eligible_now` no longer masquerades as
    the same route. Add new field-route tokens explicitly when a consumer
    uses a renamed receipt projection.
  - The 2026-04-06 shared-`ViolationRecord` convergence slice adds two
    one-way adapters under `dev/scripts/devctl/runtime/`:
    `probe_report_violations.probe_report_to_violations(report)` projects
    enriched `probe-report` `risk_hints` into
    `tuple[ViolationRecord, ...]`, and
    `governance_review_violations.governance_review_recent_to_violations(report)`
    projects the **recent window** of `governance-review` findings (from
    `report["recent_findings"]`, with default include verdict
    `("confirmed_issue",)`) onto the same shared contract. Both adapters
    import `coerce_stripped_str`, `coerce_positive_int`, and
    `build_bounded_summary` from
    `dev/scripts/devctl/runtime/violation_adapter_support.py`. The
    governance helper is explicitly NOT a live-governance feed — it
    reads only the bounded recent window emitted by
    `build_governance_review_report`, so unresolved rows older than that
    window do not appear; widen the upstream `recent_limit` or use a
    different governance data source for full-open semantics.
- `system-picture`: generated startup-to-external-review reducer that composes
  the repo-owned typed ledgers into one bounded snapshot and proof-ledger
  projection
  - `--format md` renders the compact human projection under
    `dev/reports/system_picture/latest/`.
  - `--write-ledger` refreshes `dev/audits/AI_GOVERNANCE_PLATFORM_PROOF_LEDGER.md`
    from the generated snapshot instead of hand-editing proof prose.
  - Use it when you want one maintained evidence surface for startup, graph,
    review, governance-review, imported-findings, and telemetry state.
  - Treat it as the maintainer-facing proof refresh surface after
    platform/governance contract changes that affect external-review claims.
- `planning_ir`: scheduler-facing planning reducer module under
  `dev/scripts/devctl/platform/planning_ir.py`
  - There is no standalone CLI yet; maintainers use the module/tests directly
    while the bounded reducer surface settles.
  - `PlanningIRSnapshot` joins `PlanRegistry` / `PlanTargetRef`, recent
    governance-review findings, context-graph `scoped_by` ownership,
    `ReviewState`, `WorkIntakeOwnershipState`, and
    `WorkIntakeCoordinationState`.
  - The first bounded outputs are `next_best_slices`,
    `concurrent_writer_conflicts`, `unowned_hot_paths`, and
    `plan_finding_mismatches`.
  - Treat it as the typed multi-agent scheduling seam beside
    `system-picture`, not as something agents should re-infer from
    `bridge.md` prose or startup-summary text.
- `doc-authority`: read-only governed-markdown authority scan that derives the
  current doc-registry surface from the repo-pack/governance contract, reports
  active-doc registry coverage, class budgets, overlapping authority, and
  consolidation candidates, and gives `MP-377` one bounded docs-governance
  entrypoint before any write-mode normalization lands
  - Use `--quality-policy <path>` when validating the same command against a
    different repo-pack policy during portability work.
- `governance-draft`: deterministic repo-scan entrypoint for the governed-doc
  surface; it is the machine-readable/manual discovery command for checking the
  current command surface before write-mode docs or governance changes land
  - Use `--format md` for the maintainer-readable inventory summary.
- `governance-export`: exports the portable governance stack outside the repo
  root, copies the guard/probe engine plus docs/tests/workflows, and generates
  fresh `quality-policy`, `probe-report`, and `data-science` artifacts for
  external review or pilot-repo bootstrap
  - `--adoption-scan` generates the exported guard/probe artifacts from a full
    current-worktree onboarding pass instead of commit-range mode.
  - Fails closed when the destination is inside the repo so duplicate-source
    snapshots do not poison duplication audits.
- `governance-bootstrap`: repairs copied or submodule-backed pilot repos whose
  `.git` pointer no longer resolves in the new location, then reinitializes a
  standalone local git worktree and writes a starter
  `dev/config/devctl_repo_policy.json` when the target repo does not already
  have one
  - Also writes `dev/guides/PORTABLE_GOVERNANCE_SETUP.md` inside the target
    repo so an AI or maintainer has one obvious first-read onboarding file
    that states the target repo is the first-party client/product integration
    over the portable governance platform and that repo packs plus typed
    runtime contracts remain backend authority for arbitrary repos.
  - Exported onboarding templates live under `dev/config/templates/`,
    especially `portable_governance_repo_setup.template.md` and
    `portable_devctl_repo_policy.template.json`.
  - Starter policies now include `repo_governance.surface_generation`, so the
    target repo can render local instructions/starter stubs immediately with
    `render-surfaces` after tightening the seeded context values.
- `compat-matrix`: compatibility governance bundle wrapper that runs matrix schema validation (`check_compat_matrix.py`) plus runtime enum smoke parity (`compat_matrix_smoke.py`); use `--no-smoke` for schema-only checks
  - The underlying matrix loaders now share a minimal YAML fallback parser so
    tests/CI remain stable even when `PyYAML` is unavailable.
  - Fallback parsing fails closed for malformed inline collection scalars.
- `mcp`: optional read-only MCP adapter for `devctl` surfaces (allowlisted tools/resources + stdio JSON-RPC transport); enforcement authority remains in `devctl` command contracts
- `monitor`: canonical single-pass remote-phone monitor over the typed startup + control-plane contracts; emits one mobile-safe summary (`state`, `main_problem`, `can_work_continue`, `can_code_be_pushed`, `who_needs_to_act`, `what_should_happen_next`, `confidence`), classifies each input as `authority|telemetry|projection|diagnostic`, and surfaces one bounded `self_audit.should_emit_finding` decision for observer loops
  - `--follow --interval 3m --format json` streams NDJSON frames locally, while the detached `review-channel --action ensure --follow` publisher now also writes `monitor_snapshot.{json,md}` into the governed review-status root on each publisher cadence so remote phone mode has one canonical latest bundle to read.
- `triage`: combined human/AI triage output with optional `cihub triage` artifact ingestion, optional external issue-file ingestion (`--external-issues-file` for CodeRabbit/custom bot payloads), optional review-probe rollup ingestion via `--probe-report` / `--probe-since-ref` / `--probe-head-ref`, and bundle emission (`<prefix>.md`, `<prefix>.ai.json`); extracts priority/triage records into normalized issue routing fields (`category`, `severity`, `owner`), supports optional category-owner overrides via `--owner-map-file`, emits rollups for severity/category/owner counts, and stamps reports with UTC timestamps
  - when local or downloaded CI artifacts contain pytest JUnit XML, `triage` / `report` / `status` now surface one shared `FailurePacket` section with the primary failing test, assertion/error message, and artifact paths instead of only listing failed workflow names
  - `--quality-policy <path>` lets triage classify probe debt against another
    repo policy/preset without editing the engine.
- `findings-priority`: read-only ranking surface for canonical backlog findings; reads the governed `FindingBacklog` / `governance-review` summary state, normalizes severities through the shared triage order, derives graph blast radius from context-graph dependency fan-out, and emits one bounded ranked list for plan intake or operator review. `dev/audits/LIVE_RUN.md` remains compatibility evidence only.
- `triage-loop`: bounded CodeRabbit medium/high loop with mode controls (`report-only`, `plan-then-fix`, `fix-only`), source-run correlation (`--source-run-id`, `--source-run-sha`, `--source-event`), policy-gated fix execution (`AUTONOMY_MODE=operate`, branch allowlist, command-prefix allowlist), notify/comment targeting (`--notify`, `--comment-target`, `--comment-pr-number`), automatic review-escalation comment upserts when max attempts are exhausted with unresolved backlog, attempt-level reporting, a bounded structured backlog slice for downstream autonomy consumers, structured file/line/symbol identity for probe-guidance matching when the source payload has it, optional bundle emission, and optional MASTER_PLAN proposal output
- `mutation-loop`: bounded mutation remediation loop with report-only default, threshold controls, hotspot/freshness reporting, optional policy-gated fix execution, optional summary comment updates, and bundle/playbook outputs
- `autonomy-loop`: bounded autonomy controller wrapper around `triage-loop` + `loop-packet` with hard caps (`--max-rounds`, `--max-hours`, `--max-tasks`), run-scoped packet artifacts, queue inbox outputs, phone-ready status snapshots (`dev/reports/autonomy/queue/phone/latest.{json,md}`), canonical probe-guidance injection from `review_targets.json` into the loop draft when the triage report carries a bounded structured backlog slice, explicit `guidance_adoption_required` packet metadata when that guidance is attached, live `decision_mode` gating that blocks auto-send for approval-required guidance, and strict policy gating for write modes (`AUTONOMY_MODE=operate` required for non-dry-run fix modes; dry-run still downgrades to `report-only`)
- `phone-status`: iPhone/SSH-safe read surface for autonomy controller snapshots; renders one selected projection view (`full|compact|trace|actions`) from `dev/reports/autonomy/queue/phone/latest.json` and can emit controller-state files (`full.json`, `compact.json`, `trace.ndjson`, `actions.json`, `latest.md`)
- `claude-loop`: read-only Claude loop view backed by `DashboardSnapshot` v3; supports single-shot JSON/markdown output plus `--follow --interval` polling for typed pending packets, ACK freshness, active Codex sessions, agent-mind, and system-topology state
- `mobile-status`: merged iPhone/SSH-safe read surface for the future phone app; refreshes the latest review-channel projections through the governed review-channel plan/bridge/status roots (in VoiceTerm today: `dev/active/review_channel.md`, `bridge.md`, and `dev/reports/review_channel/latest/`), combines them with autonomy `phone-status` when present, falls back to review-only live data when the phone artifact is missing, exposes the shared `DashboardSnapshot` v3 payload, renders one selected mobile view (`full|compact|alert|actions`), and can emit merged projection files (`full.json`, `compact.json`, `alert.json`, `actions.json`, `latest.md`) for downstream clients/notifiers
- `mobile-app`: wrapper over the first-party iPhone/iPad app flow; can run the real simulator demo against the live repo bundle, optionally refresh live Ralph/review state first (`--live-review`), list available simulator/physical devices, open an honest physical-device install wizard, and attempt a real signed physical-device install/launch when an Apple Development Team is provided
- `ralph-status`: Ralph guardrail analytics surface; reads `ralph-report*.json` artifacts, aggregates fix/open counts plus architecture breakdowns, now also surfaces probe-guidance attachment/adoption/waiver counts from Ralph runs, and can emit SVG charts for CLI/reporting/mobile consumers
- `controller-action`: policy-gated control surface for `refresh-status`, `dispatch-report-only`, `pause-loop`, `resume-loop`, and local `retire-stale-conductor`; dispatch/mode actions enforce allowlisted workflows/branches, respect `AUTONOMY_MODE=off` kill-switch behavior, local conductor retirement validates the target PID against the repo process-audit snapshot before terminating a stale review-channel conductor tree, and all actions emit auditable reports plus a stable `typed_action` runtime contract and optional local controller-mode state artifact
- `startup-context`: typed startup packet for AI agent sessions; composes compact repo governance, reviewer gate, push/checkpoint state, and a bounded `WorkIntakePacket` carrying the selected `PlanTargetRef`, typed continuity reconciliation, startup-order warm refs, live routing defaults, and the active typed `plan_routing` phase/task projection from `dev/active/ai_governance_platform.md`; reads reviewer acceptance from typed `review_state.json`, treats `bridge.md` as a compatibility projection instead of a startup-authority fallback, resolves typed `review_state.json` through repo-pack/governance candidate-path authority instead of one fixed `dev/reports/.../latest` literal, loads probe startup signals from the managed `dev/reports/probes/latest/summary.json` artifact under that same governed root, reads the managed latest-push artifact at `dev/reports/push/latest_push_report.json` so recovered sessions can distinguish `published_remote=true` plus `post_push_green=false` from an unresolved push, now keys that recovery/rendering truth to the current branch, HEAD, approved target, and tracked upstream/default remote instead of stale raw artifact booleans, surfaces ahead-of-upstream publication backlog, source-vs-managed-receipt ahead counts, typed phase/task routing, and push timing guidance directly in the human-facing startup summary/markdown output, renders continuity roots only when the canonical memory/context directories actually exist, persists a managed startup receipt under the repo-owned reports root, returns non-zero when the typed checkpoint budget says another implementation slice must stop and checkpoint first, and is guarded by `check_startup_authority_contract.py` so over-budget continuation or worktree-only module splits fail closed instead of slipping through as local-only state
- `startup-context`: typed startup packet for AI agent sessions; composes compact repo governance, reviewer gate, push/checkpoint state, and a bounded `WorkIntakePacket` carrying the selected `PlanTargetRef`, typed continuity reconciliation, startup-order warm refs, live routing defaults, and a bounded ownership projection for the current dirty slice. The ownership projection classifies dirty paths as `clear`, `in_scope_dirty_paths`, `scope_unknown_dirty_paths`, `outside_scope_dirty_paths`, or `concurrent_writer_activity`; startup authority and the summary surface use that same typed state so outside-scope dirt with active peer activity fails closed as a concurrent-writer condition instead of surfacing as a generic dirty-budget warning. The same packet now also projects deterministic action routing (`next_command`, `allowed_actions`, `blocked_actions`, `control_recovery_action`, `escalation_action`), destructive recovery authority (`recovery_action`, `recovery_basis`, `recovery_scope`), and typed `agent_lane` / `lane_edit_gate` permissions for `dashboard`, `implementer`, `observer`, and `reviewer` callers. The rest of the startup contract is unchanged: it reads reviewer acceptance from typed `review_state.json`, treats `bridge.md` as a compatibility projection instead of a startup-authority fallback, resolves typed `review_state.json` through repo-pack/governance candidate-path authority instead of one fixed `dev/reports/.../latest` literal, loads probe startup signals from the managed `dev/reports/probes/latest/summary.json` artifact under that same governed root, reads the managed latest-push artifact at `dev/reports/push/latest_push_report.json` so recovered sessions can distinguish `published_remote=true` plus `post_push_green=false` from an unresolved push, keys recovery/rendering truth to the current branch, HEAD, approved target, and tracked upstream/default remote instead of stale raw artifact booleans, surfaces ahead-of-upstream publication backlog and push timing guidance directly in the human-facing startup summary/markdown output, renders continuity roots only when the canonical memory/context directories actually exist, persists a managed startup receipt under the repo-owned reports root, returns non-zero when the typed checkpoint budget says another implementation slice must stop and checkpoint first, and is guarded by `check_startup_authority_contract.py` so over-budget continuation or worktree-only module splits fail closed instead of slipping through as local-only state.
  - Delivery mode is explicit in `BridgeConfig.delivery_mode`:
    `git_push_required` preserves the current CI/CD/governed-push path,
    `local_edit_only` skips push pressure after local validation, and
    `library_import_only` supports embedded/in-memory governance without a git
    publication contract.
  - Agent-loop blocker selection normalizes legacy `open_findings` text through
    the typed pending-review packet count. A stale compatibility summary is
    rewritten to the current count, and if the typed count is zero it is cleared
    so stale packet prose cannot become wake pressure after `/develop next`
    has no scoped active packet.
  - When repo policy advertises a shared backlog doc (for this repo:
    `backlog.md`), the same intake packet may surface it in warm refs and
    writeback sinks so humans and AI can share one governed intake surface
    without turning backlog prose into execution authority.
  - Reviewer/implementer launch commands plus explicit reviewer takeover are
    runtime-owned `ConductorCapabilityState` facts now. Prompt/bootstrap/bridge
    projection surfaces render from that typed owner contract, and
    `check_platform_layer_boundaries.py` now blocks startup-authority/runtime
    capability modules from importing `dev.scripts.devctl.review_channel`
    orchestration directly.
  - Read-only artifact handling: `startup-context` always attempts the receipt
    write (the launcher validates it), but degrades gracefully on `OSError`
    when `DEVCTL_NO_ARTIFACT_WRITES=1` signals an intentional read-only
    context.  Bootstrap polling and read-only mounts get the typed packet
    output even if the on-disk receipt write fails.
- `session-resume`: compact cached role bootstrap packet over the same typed
  startup/review/runtime sources. `--format summary|md|json` stays available
  for status inspection, and `--format bootstrap` is the canonical fresh-
  conversation starter surface for reviewer, implementer, and observer
  sessions. `dashboard` is the accepted user-facing alias and currently
  normalizes to the same read-only observer lane until a distinct dashboard
  runtime contract exists. Run the matching role after `startup-context` to
  get the exact role commands,
  authority docs, review range/current instruction, frozen `review_candidate`
  when dirty-tree review is ready, the reduced `authority_snapshot`
  from the shared control-plane read model, and governance/review-state inputs
  threaded through `ControlPlaneReadModelOptions` rather than legacy direct
  builder kwargs.
  Dashboard/control-plane callers must pass those same typed inputs through
  `ControlPlaneReadModelOptions` so the builder keeps one compact typed input
  contract and one resolved `ControlPlaneReadModel`.
  Conductor liveness in that model may promote typed bridge
  `*_conductor_active` evidence only when reviewer mode plus fresh poll/session
  evidence prove the row is current.
  (`coordination_state`, `root_cause`, `required_action`, `next_command`,
  `safe_to_continue`), and next guard bundle from repo-owned state instead of
  operator memory or stale bridge prose. Reviewer bootstrap prefers that typed
  candidate over raw `last_reviewed_sha..head_sha` inference and falls back to
  commit-range review only when no valid candidate exists. It now shares the
  same promoted `active_target` / `CoordinationSnapshot` path as
  `startup-context` and dashboard so live findings can outrank stale
  continuity, and the same `AuthoritySnapshot` reducer so resume/startup/status
  do not silently disagree on handshake recovery. Observer bootstrap stays on
  the typed read-only status path and must not inherit implementer-lane
  ownership or mutation guidance. Implementer bootstrap now
  treats `Pending Inbox` / typed packet `required_command` as the next bounded
  step too, so remote-control Claude sessions poll
  `review-channel --action inbox --target claude --actor claude --status
  pending --format md` before asking whether to continue a permitted probe.
- The same operator-facing lane now has a packet-native read surface too:
  `review-channel --action operator-inbox --terminal none --format json`
  returns the typed operator queue directly, defaults to the live pending
  view, and stays read-only so phone/dashboard/operator receipts can inspect
  commit/action requests without silently mutating delivery observation state.
- `startup-context --repair`: repo-owned startup auto-triage/repair mode; reads typed
  `startup-context`, startup-authority, and the canonical typed review-state
  owner surfaced by `review-channel` status refresh,
  classifies current issues as approval-boundary vs safe-local-repair vs
  manual-follow-up, can apply at most one bounded safe fix with
  `--apply-safe-fixes` per invocation, refreshes the managed startup receipt
  after each pass, and intentionally keeps mutating review-channel ownership
  inside the existing repo-owned `review-channel` command surface instead of
  re-implementing those repairs in another package or round-tripping through
  CLI JSON as an internal API. The bounded runtime adapter now also carries
  the governed review-channel `rollover_dir` sibling derived from the managed
  review root, so bridge-backed status/ensure repair paths do not fail on
  missing runtime-path context after command-package refactors. The repair
  classifier also consumes typed authority/coordination blockers, so
  `coordination_resync_required` and similar non-attention startup stops show
  up as real manual follow-up issues instead of a false healthy receipt.
- `pipeline --action refresh-authorization`: same-HEAD authorization-window
  recovery for the remote commit/push pipeline. It refuses to refresh when
  current HEAD is unavailable or differs from the stored
  `authorized_head_sha`, and stale-HEAD cases should route the operator to
  `pipeline --action recover` instead of rewriting the existing authorization
  as if it still described the current commit.
  The typed status view now carries the exact `next_command` an operator or
  agent should run next, and commit/push consumers are expected to reuse that
  field instead of inventing a second prose-only recovery plan.
- `pipeline --action auto-recover`: typed stale-pipeline classifier and
  dispatcher for the remote commit/push pipeline. It reads the current
  pipeline artifact, decides between `recover`, `refresh-authorization`,
  `abandon`, no-op, or fail-closed `ambiguous`, invokes the existing sub-action
  when safe, and writes a `PipelineAutoRecoveryReceipt` alongside the
  sub-action receipt so follow-up commits no longer require manual
  abandon-vs-recover-vs-refresh selection. The classifier uses the same
  receipt-aware HEAD movement reducer as status, so trailing governed
  projection receipt commits are no-op evidence, not source drift.
- `agent-mind --since-cursor`: cursor-based cross-agent polling over rollout
  traces. When a cursor is supplied, the command must parse enough rollout
  history for the cursor filter to see every unseen decision event instead of
  first truncating to a fixed raw-line tail window; when the flag is supplied
  without a value, it resumes from the last persisted
  `agent_minds/<provider>_latest.json` cursor if available. This keeps decisions
  visible even after more than 400 intervening low-signal noise events. The
  typed slice now also summarizes `apply_patch` target files from rollout
  traces so remote-control dashboard observers can prove real edit progress
  without scraping raw JSONL or guessing from shell-command strings alone.
  Provider ids are syntax-validated rather than limited to Codex/Claude at
  argparse time, so `cursor`, `operator`, `system`, or a future repo-pack
  provider can reach runtime session discovery; providers without governed
  trace roots
  should pass `--sessions-root` until they have a governed default trace root.
- `review-channel`: current bridge-gated review-swarm bootstrap surface; it resolves the review plan, compatibility bridge, and status root through `ProjectGovernance` / repo-pack state (in VoiceTerm today: `dev/active/review_channel.md`, `bridge.md`, and `dev/reports/review_channel/latest/`). `--action launch` reads the governed review plan plus current compatibility bridge, derives reviewer/implementer ownership from the planned lane roles instead of a fixed `codex -> reviewer` / `claude -> implementer` assumption, emits the needed provider conductor launch scripts, defaults live macOS launches to an `auto-dark` Terminal profile when available, auto-relaunches a conductor in the same terminal when the provider exits cleanly, auto-starts the repo-owned ensure-follow publisher from the actual live launch/rollover router, and now requires a fresh `startup-context` receipt before repo-owned launch/rollover work can begin; the canonical bootstrap remains role-first through `startup-context --role <reviewer|implementer>` plus `session-resume --role <reviewer|implementer> --format bootstrap`, while Claude launch scripts still use the provider-default permission mode for balanced/strict sessions so repo-owned review loops stay portable across subscriptions where Claude `auto` mode is unavailable, and trusted mode still uses the explicit bypass flag. After that receipt gate, it enforces the existing bridge launch contract: first the `check_review_channel_bridge.py` guard must pass (required bootstrap sections, tracked-file safety, heartbeat metadata, live-section size caps, duplicate/unknown heading rejection, and transcript/ANSI contamination rejection), then the live bridge state must show active reviewer heartbeat and current implementer status within the five-minute heartbeat window and must not report `checkpoint_required` / `safe_to_continue_editing=false` from the typed push-enforcement budget; live Terminal-app launch/rollover also fail closed if that detached publisher does not come up; the publisher remains the long-lived service and reclaims the reviewer-supervisor runtime on its normal cadence, while the repo also ships `dev/config/launchd/review_channel_publisher.plist.template` plus `dev/config/launchd/review_channel_publisher_service.py` for login-time restart/backoff semantics outside the live launch path; terminal selection now routes through one shared policy: explicit `--terminal` wins, governed `remote_control` sessions stay headless, follow/recovery actions inherit an already-headless parent session, and otherwise live local launch/recovery defaults back to `--terminal terminal-app`; `--terminal none` means a real headless background conductor launch, not a render-only/report-only mode. `--refresh-bridge-heartbeat-if-stale` is the typed self-heal flag for launch/rollover paths and will refresh the reviewer heartbeat metadata plus the non-audit worktree hash when stale/missing heartbeat metadata is the only blocker; `--action render-bridge` is the repo-owned repair path for a polluted compatibility bridge and now rebuilds `bridge.md` from the typed `review_state` compatibility payload (`_compat.bridge_projection`) plus sanitized fixed sections instead of reparsing live markdown, preserving transcript junk, or hand-editing report blobs; the same render path rejects embedded markdown headings in flat bridge sections fail-closed so duplicate packet H2 blocks cannot leak back into `Current Instruction For Claude` on rerender; the startup gate still blocks `launch|rollover` on checkpoint-budget or other real authority failures, but it no longer blocks those actions solely because the reviewer loop is stale on the implementer side; `--action recover --recover-provider <provider>` is the narrower repo-owned stale-implementer replacement path and launches only a fresh conductor for the current implementer provider when attention says the implementer side is stale, but it now fails closed unless the current repo-owned reviewer provider session is already present; repeated unchanged stale reviewer/runtime states now also let `reviewer-heartbeat --follow` auto-trigger the repo-owned `--action rollover` path so remote-control recovery reuses the structured handoff bundle plus visible ACK contract instead of ad hoc restarts; `--action reset-implementer-state` is the repo-owned live-section repair path when attention says implementer-owned bridge state must return to canonical pending; it rewrites `Claude Status`, `Claude Questions`, and `Claude Ack`, then refreshes the typed review-channel projection without changing reviewer-owned instruction truth; non-zero provider exits still stop visibly so auth/CLI failures do not spin forever; `--action status` writes the latest bridge-backed projections under the governed review-channel status root (in VoiceTerm today: `dev/reports/review_channel/latest/`) as `review_state.json`, `compact.json`, `full.json`, `actions.json`, `latest.md`, and `registry/agents.json`, and now includes the derived next unchecked plan item, machine-readable `reviewer_worker` state, typed `current_session` live instruction / ACK state, canonical typed bridge freshness booleans (`bridge.reviewed_hash_current`, `bridge.review_needed`), typed conductor visibility state (`reviewer_runtime.conductor_visibility`, `reviewer_runtime.session_owner.session_visibility`), the typed `_compat.bridge_projection` payload used by repo-owned bridge repair, shared context-packet `guidance_refs` when probe guidance is in scope, bridge-backed `push_enforcement` fields (`checkpoint_required`, `safe_to_continue_editing`, `recommended_action`, `raw_git_push_guarded`), and the compact doctor projection with publisher/supervisor running state plus last heartbeat/stop-reason fields. The same status/doctor path now also projects one reduced `authority_snapshot` contract (`coordination_state`, `root_cause`, `required_action`, `next_command`, `safe_to_continue`) so callers can distinguish stale instruction/ACK handshake drift from broader resync or single-agent posture without manually reconciling five raw fields. Attention escalates to `checkpoint_required` when the worktree is over budget; instruction-shaped compatibility outputs stay flat here too, so `Current Instruction For Claude`, `current_session.current_instruction`, and queue `derived_next_instruction` use compact no-H2 summaries while the full `Context Recovery Packet` remains available in source metadata for prompt/audit consumers; `latest.md` now renders the current-session summary from that typed block while the bridge stays a compatibility projection, and `status` now also fails closed when it detects an implementer-only repo-owned session with no live repo-owned reviewer conductor because that hybrid loop is not trusted as steady-state reviewer authority, or `active_dual_agent` with no repo-owned conductors because detached follow heartbeats alone are not proof the loop is live; reviewer-owned instruction rewrites now also reset live `Claude Status` / `Claude Ack` sections to placeholder `- pending` state whenever the instruction revision changes so typed `current_session` stops mirroring stale implementer text until the implementer repolls and acknowledges the new revision; reviewer-owned hold-steady / checkpoint / governed-push-pending bridge state now counts as a valid implementer-side wait posture too, so conductors should keep polling repo-owned status/wait paths instead of asking operators to choose between polling, pushing, or side work; repo-owned heartbeat refresh also preserves a real reviewer checkpoint `Poll Status` instead of overwriting it with automation-only heartbeat text; active-work implementer polling is stricter now too: `--action implementer-wait` is only valid under an explicit reviewer-owned wait state, while active instructions require substantive `Claude Status` / `Claude Ack` updates that name concrete files, subsystems, findings, or one blocker/question instead of `No change. Continuing.` / reviewer-placeholder text; `--action ensure`, `--action reviewer-heartbeat`, and `--action reviewer-checkpoint` emit the same reviewer-worker contract, while `--action ensure --follow` cadence frames add `review_needed` signals without claiming semantic review completion; active reviewer checkpoints should prefer one typed `--checkpoint-payload-file` or the existing per-section `--*-file` flags for AI-generated markdown / shell-sensitive content instead of inline shell bodies, and `active_dual_agent` writes must carry the live `--expected-instruction-revision`; `--action implementer-wait` is the repo-owned bounded implementer-side polling path and replaces ad-hoc `sleep` shell loops by waking on meaningful reviewer-owned bridge changes, failing closed on reviewer-loop breakage, and timing out after one hour by default; `--action reviewer-wait` is the symmetric reviewer-side wait path that wakes on meaningful implementer-owned state changes over top-level `reviewer_worker` / `bridge_liveness` status truth plus projected `current_session` ACK/status fields from `review_state.json`; `reviewer-heartbeat --follow` now auto-escalates repeated unchanged stale-implementer state through the narrower `recover` path instead of a full-loop restart; `--action promote` is the typed repo-owned queue-advance path that rewrites `Current Instruction For Claude` from the next unchecked active-plan checklist item when the current slice is resolved and findings are clear; `--action rollover` writes a repo-visible handoff bundle, relaunches fresh conductors before compaction, and can wait for visible ACK lines in `bridge.md`
  - Remote-control recovery keeps local UI out of the path: if typed
    liveness proves an attached remote-control provider, status/doctor must
    recommend headless `--terminal none`, and launch/recover requests fail
    closed before opening Terminal.app prompts that the remote operator cannot
    see.
  - Development-mode launcher overrides are only trusted as durable audit
    evidence after the caller persists the returned `LauncherDisciplineBypass`
    as a `launcher_discipline_bypassed` event. The receipt records the bypass
    reason, requested terminal, interaction mode, and each bypassed verdict.
    Provider dangerous/no-prompt mode is separate authority now: trusted launch
    rendering requires an active edit-only `BypassLifecycle` selected from the
    governed lifecycle store, typically by `--bypass-receipt-id`. The lifecycle
    records `BypassRequest`, `BypassEvaluation`, `BypassReceipt`, and
    `BypassExpiry`, composes with `GovernedExceptionLifecycle`, and is projected
    through startup context and `AgentLoopOperatorOverride` instead of relying
    on raw provider flags or bridge text.
  - Launch orchestration has explicit module boundaries now:
    `bridge_action_prepare.py` owns action preparation, `bridge_scope.py` owns
    scope promotion helpers, `bridge_stale_refresh.py` owns stale heartbeat
    self-heal, `launcher_discipline_enforcement.py` owns bypass receipt
    enforcement, and `parser_launch_arguments.py` / `parser_types.py` own the
    launch CLI argument table. Keep new launch behavior inside the matching
    helper instead of regrowing the handler/support/parser modules beyond their
    guard budgets.
  - `--reviewer-mode active_dual_agent` is an authoritative launch override:
    if typed bridge metadata still says `single_agent`, launch rewrites it
    instead of silently ignoring the flag. Publisher and reviewer-supervisor
    lifecycle heartbeats plus daemon event rows also carry
    `invocation_provenance` with `parent_pid`, `process_pid`, `launchd_label`,
    `daemon_supervisor`, `trigger_reason`, and `command_line`; the launchd
    wrapper sets `launchd_label=com.voiceterm.review-channel.publisher` and
    `daemon_supervisor=launchd` so remote-control operators can prove why an
    auto-spawn occurred.
  - Event-backed `current_session` now preserves the prior typed instruction
    when the queue is blank and no explicit packet truth exists, but explicit
    live `packets` / persisted `packet_inbox` authority can still clear the
    lane when there is no live current-instruction packet. Queue
    `derived_next_instruction` only becomes Claude's live instruction when
    `derived_next_instruction_source.to_agent` is blank or `claude`;
    reviewer-targeted (`codex`) queue instructions remain reviewer
    attention/open-findings instead of leaking into the implementer lane.
  - Recovery precedence is typed now too: if `current_session` / bridge
    liveness already show a current Claude ACK but `launch_truth` degrades to
    `detached_runtime_only`, `automation_only`, or `hybrid_claude_only`,
    `status`, `doctor`, `startup-context`, and bridge-poll emit
    `review_loop_relaunch_required` plus the reviewer-owned
    `review-channel --action launch|rollover` command when checkpoint
    authority is otherwise clear. If the same snapshot also shows
    `reviewed_hash_current=true`, `review_needed=false`, and typed
    `push_enforcement` already says `checkpoint_required`, that stronger
    checkpoint authority preempts relaunch: the shared surfaces emit
    `checkpoint_required` / `cut_checkpoint`, route `next_command` to
    `python3 dev/scripts/devctl.py commit -m "<descriptive message>"`, and
    allow only checkpoint-safe VCS actions (`vcs.stage`, `vcs.commit`) while
    still blocking `implementation.edit`. Neither shape is a
    `reset-implementer-state` case because the live reviewer loop itself is no
    longer present enough to trust an implementer-only repair.
  - The startup gate reads `StartupReceipt.advisory_action` as a typed
    attribute and handles a missing (`None`) receipt without crashing. The
    reviewer-loop relaxation for `launch`/`rollover` is handled by the
    `reviewer_bootstrap` intent in the authority system, so `enforce_startup_gate`
    has no separate repair bypass — receipt freshness, checkpoint, and all
    non-reviewer-loop authority checks always apply.
  - Reviewer-owned `scope`, `promote`, `reviewer-checkpoint`, and
    `render-bridge` writes now fail closed when pending reviewer-targeted
    packets still exist in the event-backed inbox, so later bridge/projection
    refreshes cannot silently overwrite earlier Codex findings.
  - Compact doctor/dashboard/reporting surfaces now carry explicit runtime
    counts for live conductors, delegated receipts, planned lanes, worker
    budget, and running daemons so phone or remote dashboards can report how
    many agents are actually live without inferring from bridge prose.
  - Review-channel observability now closes the owner split too: dashboard and
    control-plane prefer the shared `session_probe` conductor view before
    falling back to static `session_pid` metadata, event-backed
    `current_session` preserves `implementer_session_state` /
    `implementer_session_hint`, and bridge-backed status/doctor/render guards
    count only unexpired pending packets while surfacing `stale_packet_count`
    so inbox/status/dashboard numbers stay aligned. `watch --follow` now
    re-emits when stale-count transitions change too, not only when the live
    packet-id set changes, so typed packet listeners do not look frozen after
    a pending packet ages into stale history.
  - Single-agent local-review visibility now has one more bounded proof path:
    when repo-owned packet activity goes quiet, fresh local rollout JSONL
    writes still count as live reviewer evidence for status/doctor/runtime
    counts/dashboard health, so a long Codex edit/test turn does not vanish
    just because no new packet was posted yet.
  - Promotion readiness now treats reviewer prose as compatibility text, not substring authority. Auto-promotion / follow paths may only trust explicit primary state markers (for example the first verdict bullet, explicit idle findings, or typed `current_session` truth), so text like `--terminal none`, `unresolved`, or a later `Accepted:` explanation cannot silently promote the next plan item.
  - Launch/replay authority is typed and fail-closed: launch/rollover resolves operator interaction mode once through governance/startup authority, session preparation and the live pre-spawn gate use that same value, and generated conductor scripts re-read `review_state.json` to reject stale prepared HEAD / instruction revision / turn-token state with a non-restartable headless exit before provider start.
  - Reviewer-supervisor restart policy is non-restartable after governed `manual_stop` / `completed` lifecycle state. `ensure` and reviewer-heartbeat auto-start leave that supervisor stopped until an explicit launch, rollover, or follow command restores it, and the launchd publisher wrapper maps launch-authority exit `82` to no restart.
- Reviewer-bootstrap note: `review-channel --action launch|rollover` keep the
  hard checkpoint, branch, and non-reviewer-authority blockers, but plain
  HEAD drift only blocks those actions when the diff since the startup
  receipt touches guarded quality-scope roots.
- `autonomy-benchmark`: active-plan-scoped swarm benchmark matrix runner (`swarm-counts x tactics`) that launches `autonomy-swarm` batches, captures per-swarm/per-scenario productivity metrics, and writes benchmark bundles under `dev/reports/autonomy/benchmarks/<label>` (non-report modes require `--fix-command` and typed fanout readiness)
- `swarm_run`: guarded autonomy pipeline wrapper around `autonomy-swarm` that loads plan scope context, derives next unchecked plan steps into one prompt, enforces reviewer lane + post-audit digest, runs governance checks (`check_active_plan_sync`, `check_multi_agent_sync`, `docs-check --strict-tooling`, `orchestrate-status/watch`), and appends run evidence to the active plan doc (`Progress Log` + `Audit Evidence`); supports optional continuous multi-cycle execution (`--continuous --continuous-max-cycles`) plus feedback sizing controls (`--feedback-sizing`, `--feedback-no-signal-rounds`, `--feedback-stall-rounds`, `--feedback-downshift-factor`, `--feedback-upshift-rounds`, `--feedback-upshift-factor`) for hands-off checklist progression (non-report modes require `--fix-command`)
- `autonomy-report`: human-readable autonomy digest builder that scans loop/watch artifacts, writes dated bundles under `dev/reports/autonomy/library/<label>`, and emits summary markdown/json plus optional matplotlib charts
- `autonomy-swarm`: adaptive swarm orchestrator that sizes agent count from change/question metadata (with optional token-budget cap), runs per-agent bounded `autonomy-loop` lanes in parallel, reserves a default `AGENT-REVIEW` lane for post-audit review when execution runs with >1 lane, writes one dated swarm bundle under `dev/reports/autonomy/swarms/<label>`, and by default runs a post-audit digest bundle under `dev/reports/autonomy/library/<label>-digest` (use `--no-post-audit` and/or `--no-reviewer-lane` to disable; non-report modes require `--fix-command` plus `CoordinationSnapshot.safe_to_fanout=true`; use `--plan-only` or `--mode report-only` for read-only review/allocation while fanout readiness is blocked)
- `failure-cleanup`: guarded cleanup for local failure triage bundles (`dev/reports/failures`) with default path-root enforcement, optional override constrained to `dev/reports/**` (`--allow-outside-failure-root`), optional scoped CI gate filters (`--ci-branch`, `--ci-workflow`, `--ci-event`, `--ci-sha`), plus dry-run/confirmation controls
- `reports-cleanup`: retention-based cleanup for stale run artifacts under managed `dev/reports/**` roots (default `max-age-days=30`, `keep-recent=10`) with protected paths, preview mode (`--dry-run`), and explicit confirmation/`--yes` before deletion
- `audit-scaffold`: build/update `dev/reports/audits/RUST_AUDIT_FINDINGS.md` from guard findings (with safe output path and overwrite guards)
- `list`: command/profile inventory

## Quick command guide (plain language)

| Command | Run it when | Why |
|---|---|---|
| `check --profile fast` | you need a very fast local sanity pass while iterating | alias of `quick`; runs local guard checks (including AI-guard scripts) and is not a substitute for pre-push validation |
| `check-router --since-ref origin/develop --execute --keep-going` | before push when changed files span multiple surfaces | auto-selects required lane + risk add-ons, phases serial-sensitive projection/status commands away from parallel-safe guards, applies command/route timeout policy, and emits guard coverage/remediation evidence (unknown paths escalate to tooling); add `--parallel-workers <n>` to tune, `--no-parallel` for sequential debugging, or `--command-timeout-seconds` / `--route-timeout-seconds` only with measured evidence |
| `progress-status --format md --limit 10` | a long devctl/check-router/commit/push run appears silent | reads the latest typed `StageProgressEvent` heartbeat/completion trail so agents and operators can inspect progress without manual process-table polling |
| `check-router --since-ref origin/develop --quality-policy /tmp/pilot-policy.json` | you are piloting the governance router in another repo clone | reuses the same lane-selection engine against another repo's policy-owned path/risk rules |
| `test-python --suite devctl --path dev/scripts/devctl/tests/commands/test_python_tests.py` | you need Python proof for a focused tooling slice | runs pytest through repo-owned fail-fast and timeout policy instead of a broad raw pytest command; add `--parallel-workers <n>` for multi-path or node-id shard progress, and use `--no-parallel` only for sequential debugging |
| `tandem-validate --format md` | a Codex/Claude tandem slice needs one canonical validator instead of a hand-written checklist | runs preflight policy/status, derives the real lane and risk add-ons from `check-router`, executes the routed bundle, then rechecks `check_review_channel_bridge.py` and `check_tandem_consistency.py` at the end |
| `develop design-preflight --topic "<state/proof topic>" --record-ground-truth-receipt --format md` | you are about to add or change a typed runtime contract, proof channel, architecture rule, or runtime-state reducer | runs the connected ground-truth pipeline first: ReviewState -> `RuntimeTruthSnapshot`, agent-mind projections, provider session state such as Claude `bridgeSessionId`, connectivity registry, command registry, startup quality signals, and existing contracts; records `GroundTruthProbeRunReceipt` so `check_ground_truth_probe_gate.py` can prove the design looked at upstream truth before creating or extending contracts |
| `check_ground_truth_probe_gate.py --format md` | runtime/proof/architecture files changed and the design may have introduced a new authority surface | blocks when trigger paths changed without a current satisfied `GroundTruthProbeRunReceipt`, preventing another proof-channel design that skips upstream UI/state-file ground truth |
| `check_memory_not_authority.py --format md` | an agent wants to preserve an AI/process/runtime rule in local memory or scratch notes | blocks load-bearing architecture/process authority from living only in operator memory, forcing it into repo contracts, policy, maintainer docs, or guards |
| `governance-draft --format md` | you need the current governed-doc discovery surface before a write-mode docs or governance change | renders the deterministic repo-scan entrypoint that should match the CLI inventory and maintainer docs |
| `check --profile ci` | before a normal push | catches build/test/lint issues early |
| `check --profile prepush` | runtime changes touch perf/latency/parser/wake-word/memory-sensitive paths | adds perf + memory-heavy validation before CI catches it |
| `check --profile maintainer-lint` | you are doing focused lint/debt cleanup | runs stricter maintainer lint policy without full runtime build/test loop |
| `check --profile pedantic` | you want a broader optional lint sweep after a large refactor or as explicit pre-release cleanup | runs advisory `clippy::pedantic`, writes structured artifacts under `dev/reports/check/`, and stays out of required bundle/release flow |
| `check --profile quick` | you need a fast local sanity pass while iterating | runs fmt/clippy plus the AI-guard script pack for structural/code-quality feedback without full test/build |
| `guard-run --cwd rust -- cargo test --bin voiceterm ...` | an AI/dev session needs to run raw Rust tests or test binaries directly | runs the command without a shell `-c` wrapper, then automatically executes the required post-run hygiene follow-up (`quick` for runtime/test commands, `process-cleanup --verify` for lower-risk repo tooling commands), and appends a repo-visible `guarded_coding_episode.jsonl` artifact for watchdog analytics; optional flags now carry typed provider/session/retry/verdict metadata for later controller/watchdog callers |
| `check --profile quick --skip-fmt --skip-clippy --no-parallel --with-process-sweep-cleanup` | you ran raw `cargo test` / manual test binaries and need orphan cleanup immediately after | runs the AI-guard script pack plus opt-in process-sweep pre/post and host-side `process-cleanup --verify`, so stale repo processes and structural regressions are caught before later runs |
| `process-cleanup --verify --format md` | after PTY/runtime tests, manual tooling bundles, or before handoff when host process access is available | safely kills orphaned/stale repo-related host process trees, including descendant PTY children, repo-cwd background helpers, and orphaned tooling descendants, then reruns strict host audit; freshly detached repo-related helpers now keep verify red immediately instead of slipping through as advisory-only noise |
| `process-audit --strict --format md` | when you need read-only host diagnosis or cleanup was intentionally skipped | audits the real host process table for repo leftovers, including descendant PTY children and repo-cwd runtime/tooling helpers that would otherwise look generic in Activity Monitor; registered review-channel conductors stay supervised even when headless launch wrappers detach to PID 1, while unregistered detached helpers still fail strict audit |
| `data-science --format md` | you want a fresh productivity/agent-sizing snapshot from current telemetry | builds `summary.{md,json}` + charts from devctl events, swarm/benchmark history, watchdog episodes, and governance-review adjudication metrics |
| `governance-review --format md` | you want the current false-positive / cleanup scoreboard for reviewed guard and probe findings | reads the governance review JSONL ledger, keeps the latest verdict per finding id, and writes refreshed `review_summary.{md,json}` artifacts |
| `check --profile release` | before release/tag verification on `master`, or when feature-branch work touches release-owned surfaces | adds strict remote CI-status + CodeRabbit/Ralph release gates plus non-blocking mutation-score reminders on top of local release checks; off the configured release branch it resolves the active branch and enables commit fallback instead of hardcoding `master` |
| `mcp --tool release_contract_snapshot --format json` | an MCP client needs a read-only control-plane contract view | exposes allowlisted, read-only snapshots without changing `devctl` as enforcement authority |
| `check --profile ai-guard` | after touching larger Rust/Python files or guard-owned governance files | runs the full AI guard pack without full test/build cycle for focused cleanup |
| `launcher-check` | you want the launcher/package Python guard lane without remembering a policy path or broader repo checks | delegates to a focused AI-guard-only run against `scripts/` + `pypi/src` using `dev/config/devctl_policies/launcher.json` |
| `launcher-probes` | you want one ranked review packet for launcher/package Python entrypoints | delegates to `probe-report` with the same focused launcher policy and normal probe artifacts |
| `launcher-policy` | you want to inspect what the focused launcher lane actually enables | renders the resolved launcher policy, scopes, and warnings without spelling out `--quality-policy` |
| `docs-check --user-facing` | you changed user docs or user behavior | keeps docs and behavior aligned |
| `docs-check --strict-tooling` | you changed tooling, workflows, or process docs | enforces governance, active-plan sync, and durable guide coverage contracts |
| `docs-check --strict-tooling --quality-policy /tmp/pilot-policy.json` | you want the same docs-governance contract in another repo without patching devctl | resolves canonical doc paths and deprecated-command policy from the supplied repo policy file |
| `commit --paths <path>... -m "message"` | real work is dirty but not staged and raw `git add` would bypass the governed lane | stages the selected repo-relative paths through the typed `vcs.stage` action, refreshes/stages the managed ReviewSnapshot artifact, blocks when other non-artifact dirty paths remain outside the selected scope, then runs the normal guard, approval, and `vcs.commit` pipeline |
| `push` | you want the canonical repo-owned short-lived branch push validator without mutating git state yet | resolves `repo_governance.push`, checks branch/remote policy, runs the configured preflight, emits typed push stages (`validation_ready`, `published_remote`, `post_push_green`) without mutating git state, persists the latest typed push result at `dev/reports/push/latest_push_report.json` for later recovery, and short-circuits to the existing already-published receipt when fetch/divergence proves the tracked branch is already at `ahead == 0` |
| `push --execute` | validation passed and you want the repo-owned push path instead of ad-hoc `git push` | runs the same policy-driven validation, writes phase-aware latest-push snapshots as the governed run starts (`push_preflight_running`) and becomes ready to publish (`push_pending`), runs `render-surfaces --write` before routed preflight, runs routed publication preflight fail-fast on the first blocker by default (`repo_governance.push.preflight.fail_fast_on_blocker=true`; audit-only policy may opt into `--keep-going`), auto-commits managed generated-surface/projection receipts when preflight leaves only governed receipt/projection artifacts dirty, parses trimmed porcelain status rows so unstaged managed `bridge.md` / `REVIEW_SNAPSHOT.md` drift cannot be mistaken for clean state, refreshes typed projection bundles after receipt movement, treats contiguous managed receipt commits above the authorized content commit as managed movement instead of stale HEAD drift, shares that managed-chain proof with approved-target identity findings so receipt HEADs do not self-invalidate current publication authorization, performs the branch push, writes a `published_remote` artifact snapshot as soon as `git push` succeeds, mirrors `published_remote` and `post_push_green` from `push_stages` onto the report root, executes the configured post-push bundle, matches the persisted branch/HEAD/approved-target record against the current tracked upstream or default remote during startup recovery so stale local upstream counts do not trigger duplicate pushes, binds the staged pipeline plus persisted authorization to the exact `worktree_identity` that requested publication so a worker-lane approval cannot be replayed from the primary control lane, emits stderr progress notices when publication is recorded and before each post-push step so long audit bundles stay visibly in the "published, still auditing" phase, writes `push_pipeline_phases` for pre-validation managed projection sync vs post-validation repair, auto-transitions non-destructive push failures to `delivered_locally_pending_publish` so the landed local commit no longer blocks new governed commits, and no-ops to the same already-published receipt when a rerun fetch proves `ahead == 0` without reconstructing a stale `push_blocked` commit-pipeline artifact into `push_completed`; destructive remote rejection/conflict evidence remains `push_blocked` for explicit operator reconciliation, `--skip-preflight` / `--skip-post-push` only work when repo policy explicitly allows those bypasses, and the repo-owned default keeps `allow_skip_preflight` closed unless a tracked temporary override is deliberately in force |
| `render-surfaces --format md` | you need to inspect repo-pack instruction/starter surfaces or validate drift without writing files | resolves `repo_governance.surface_generation`, reports current sync state for each governed surface, and includes the bounded connectivity-registry summary used by SYSTEM_MAP |
| `render-surfaces --write --format md` | you changed a repo-pack template, starter stub, or surface-generation policy context | regenerates governed outputs in place so `docs-check --strict-tooling` and the standalone guard stay green, including tracked non-local outputs such as `AGENTS.md`, `SYSTEM_MAP.md`, slash templates, and portable hook/workflow stubs plus local-only outputs such as `CLAUDE.md` |
| `system-map --format md` | you need the generated connectivity snapshot that feeds the managed SYSTEM_MAP block | renders the bounded `SystemMapSnapshot` over tracked architecture roots, governed surfaces, and the shared `ConnectivityRegistrySnapshot` consumed by context-graph, startup-context, session-resume, render-surfaces, and the platform closure guard |
| `hygiene` | before merge on tooling/process work | catches doc/process drift and leaked runtime test processes |
| `publication-sync --format md` | a paper/site depends on repo evidence and you need to know if it drifted | shows watched-path changes since the last recorded sync and the exact command to record a new baseline after publish |
| `hygiene --fix` | after local test runs leave Python caches | clears `dev/scripts/**/__pycache__` safely and re-checks hygiene |
| `reports-cleanup --dry-run` | hygiene warns that report artifacts are stale/heavy | previews what retention cleanup would remove without deleting anything |
| `security` | you changed dependencies or security-sensitive code | catches advisory/policy issues |
| `triage --ci` | CI failed and you need an actionable summary | creates a clean failure summary for humans/AI |
| `findings-priority --format md` | you need one repo-owned ranking over the current canonical findings backlog before plan intake or reviewer follow-up | reads the governed `FindingBacklog` / `governance-review` state, normalizes severities through triage, then sorts findings by severity and source-file dependency fan-out from the context graph |
| `report --pedantic --pedantic-refresh --format json` | you want one command that refreshes the advisory sweep and emits a structured repo-owned summary | reruns pedantic artifact generation, then reads those artifacts plus `dev/config/clippy/pedantic_policy.json` to emit ranked lint data for review/AI consumption |
| `report --rust-audits --with-charts --emit-bundle --format md` | you want one readable Rust guard audit pack with graphs and file hotspots instead of separate raw guard outputs | runs the Rust best-practices, lint-debt, and runtime-panic guards, explains why each signal is risky, writes `.md` + `.json` bundle files, and generates matplotlib charts when available |
| `report --python-guard-backlog --python-guard-backlog-top-n 25 --since-ref origin/develop --head-ref HEAD --format md` | you want one prioritized Python clean-code hotspot view before promoting stricter policy gates | aggregates dict-schema/global-mutable/parameter-count/nesting-depth/god-class plus broad-except/subprocess-policy guard outputs into one ranked backlog so teams can burn down debt in order |
| `report --probe-report --since-ref origin/develop --head-ref HEAD --format md` | you want the normal project report to include the current review-probe summary for agent/human handoff | runs the registered review probes, folds the aggregated `risk_hints` summary into the shared project snapshot, and scopes the probe scan to the provided commit range when `--since-ref` is set |
| `status --probe-report --format md` | you want a lighter-weight current status view that still surfaces AI-slop findings | runs the registered review probes against the worktree and appends the aggregated hint counts/top files to the standard status snapshot |
| `system-picture --format md` | you want one generated external-review reducer for startup, review, graph, governance-review, external-findings, and telemetry state | builds `dev/reports/system_picture/latest/summary.{json,md}` plus the proof-ledger preview under `dev/reports/system_picture/latest/proof_ledger.md` from typed ledgers and managed artifacts |
| `system-picture --write-ledger --format md` | you want to refresh the tracked proof ledger from the generated reducer | writes the same generated projection to `dev/audits/AI_GOVERNANCE_PLATFORM_PROOF_LEDGER.md` so the evidence doc stays synced with the machine snapshot |
| `triage --pedantic --no-cihub --emit-bundle --format md` | you want an AI-friendly pedantic cleanup packet without inventing a second triage system | folds the saved pedantic artifacts into normal `triage` output and bundle files; add `--pedantic-refresh` only when you intentionally want triage to regenerate the artifacts inline |
| `triage-loop --branch develop --mode plan-then-fix --max-attempts 3` | you want bounded automation over medium/high backlog | runs report/fix retry loop with deterministic md/json artifacts plus the bounded backlog slice consumed by `loop-packet` guidance |
| `mutation-loop --branch develop --mode report-only --threshold 0.80` | you want bounded mutation-score automation with hotspots and optional fixes | runs report/fix retry loop with deterministic md/json/playbook artifacts |
| `autonomy-loop --plan-id acp-poc-001 --branch-base develop --mode report-only --max-rounds 6 --max-hours 4 --max-tasks 24 --format json` | you want one bounded controller run that emits queue-ready checkpoint packets | orchestrates triage-loop/loop-packet rounds, writes run-scoped packet artifacts, and refreshes phone-ready `latest.json`/`latest.md` status snapshots |
| `phone-status --phone-json dev/reports/autonomy/queue/phone/latest.json --view compact --format md` | you want one iPhone/SSH-safe autonomy snapshot | renders a selected phone-status projection view and can emit controller-state projection files for downstream clients |
| `mobile-status --phone-json dev/reports/autonomy/queue/phone/latest.json --view compact --emit-projections dev/reports/mobile/latest --format md` | you want one SSH-safe snapshot that already includes Codex/Claude/review state plus controller state for a future phone app | refreshes the latest governed review-channel projections, merges them with autonomy phone-status when it exists, otherwise emits a review-only live bundle with warnings, and writes compact/alert/actions/full mobile projections for downstream clients or notifier adapters |
| `mobile-app --action simulator-demo --format md` | you want the real iPhone app built, installed in the simulator, synced with live repo data, and launched with a short walkthrough | runs the guided simulator flow over `app/ios/VoiceTermMobileApp`, prints the current live action preview, and points at the real bundle/app paths instead of sample-only data |
| `mobile-app --action simulator-demo --live-review --format md` | you want the simulator to reflect the current repo-backed Ralph/review loop state before launch | refreshes `review-channel --action status`, then runs the guided simulator flow and prints the exact host-side `devctl` commands that still own loop execution |
| `mobile-app --action device-wizard --format md` | you have a plugged-in iPhone/iPad and want the honest install path without guessing | detects connected physical devices, opens the Xcode project, and prints the signing/run/import steps required for real on-device installation |
| `mobile-app --action device-install --development-team <TEAM_ID> --format md` | you have a plugged-in iPhone/iPad and want devctl to attempt the real install instead of only opening Xcode | builds the signed `VoiceTermMobileApp` for `iphoneos`, installs it with `xcrun devicectl`, launches it on-device, and fails with explicit prerequisite errors when device trust or signing is not ready |
| `ralph-status --report-dir dev/reports/ralph --with-charts --format md` | you want one current view of Ralph guardrail progress before wiring phone or PyQt controls on top | aggregates `ralph-report*.json` artifacts, prints fix/open counts plus architecture breakdowns, and writes SVG charts when `--with-charts` is enabled |
| `controller-action --action dispatch-report-only --repo owner/repo --branch develop --dry-run --format md` | you want one guarded operator action without ad-hoc shell scripting | validates policy + mode gates and executes (or previews) bounded dispatch/pause/resume/status actions with structured output and a stable `typed_action` contract |
| `controller-action --action retire-stale-conductor --pid <pid> --format md` | a stale review-channel conductor is keeping host-process cleanup dirty by spawning fresh detached helper rows | validates the PID through `process-audit`, refuses non-conductor or too-recent targets, terminates the stale conductor tree through the typed controller-action surface, and points back to `process-cleanup --verify` for proof |
| `review-channel --action status --terminal none --format md` | you need the current bridge-backed review snapshot without relaunching anything | reads the governed review-channel plan plus compatibility bridge, refreshes the governed review-channel status root (in VoiceTerm today: `dev/reports/review_channel/latest/`), emits the typed runtime participant registry plus planned-topology compatibility projection, typed `current_session` live-status state, typed `reviewer_runtime.review_acceptance` verdict/findings truth, provider-neutral reviewer/implementer aliases (`reviewer_poll_state`, `last_reviewer_poll_*`, `implementer_ack*`) alongside the legacy bridge-shaped `codex_*` / `claude_*` compatibility fields, frozen `review_candidate` truth for dirty-tree review handoff, typed conductor visibility (`reviewer_runtime.conductor_visibility` plus reviewer `session_visibility`) for operator or tooling consumers, the reduced `authority_snapshot` contract for one-step recovery/next-action reads, keeps an attached remote-control provider live in `single_agent` remote-control lanes even after the typed packet recency window ages out, follows typed reviewer capability/provider assignment for local `single_agent` reviewer presence instead of silently assuming Codex, preserves explicit reviewer-owned bridge mode ahead of daemon lifecycle hints and prevents stale current-session drift warnings from reverse-overwriting a newer reviewer bridge heartbeat/checkpoint, auto-reprojects `bridge.md` from typed state during status refresh even when pending reviewer-targeted packets still exist, canonicalizes recovered `Last Codex poll` metadata to the whole-second UTC/local bridge format when typed state carries blanks or fractional seconds, and fails closed when `active_dual_agent` no longer has the repo-owned conductor pair behind it or implementer-complete state has no valid review candidate |
| `review-channel --action check-ack-freshness --format json` | bridge-visible implementer ACK text may have drifted from typed ACK authority and you need the event-backed truth without manual bridge polling | reads typed `implementer_ack` events plus `current_session`, compares them with the compatibility bridge projection, reports `ImplementerAckFreshnessProjection` with P152 modes (`on_demand`, `scheduled`, `disabled`), and fails closed on bridge-only or stale visible ACK claims |
| `review-channel --action status --recovery-probe --format json` | you need the R126 CLI recovery probe without manually correlating status, doctor, runtime-readiness, and authority fields | attaches `CLIHealthProbeAutomation` to status output, with P152 modes (`scheduled`, `on_error`, `disabled`), reports whether recovery evidence is active, and reuses the existing recommended-command, doctor, recovery-assessment, runtime-readiness, and authority surfaces instead of creating a parallel recovery path |
| `review-channel --action reviewer-heartbeat --reviewer-mode single_agent --terminal none --format md` | a dual-agent reviewer session was interrupted and you need to resume locally without trusting stale dual-agent metadata | records sanctioned local reviewer takeover, refreshes `Last Codex poll` / reviewer mode through the repo-owned bridge path, retires detached publisher/reviewer-supervisor daemons so they cannot reassert stale `active_dual_agent` metadata, and gives local review/repair work one consistent authority source before more code changes land |
| `review-channel --action implementer-wait --terminal none --format json` | Claude is under an explicit reviewer-owned wait state and needs to wait safely for the next Codex review/update without leaving a raw shell poller behind | polls the bridge on the normal cadence, exits immediately when reviewer-owned bridge content changes or a new instruction is already waiting, fails closed when the reviewer loop is unhealthy, times out after one hour by default, and is not a substitute for substantive `Claude Status` / `Claude Ack` updates while active work is still assigned |
| `review-channel --action reset-implementer-state --terminal none --format md` | live status/attention says the implementer-owned bridge sections need a clean pending reset without changing reviewer instruction truth | rewrites `Claude Status`, `Claude Questions`, and `Claude Ack` to canonical pending state, refreshes the typed review-channel projection, and leaves reviewer-owned instruction / verdict fields untouched |
| `review-channel --action recover --recover-provider claude --terminal none --format json` | typed status says `implementer_relaunch_required` in governed `remote_control` and you need to replace only the stale Claude implementer without relaunching the whole pair | prepares one fresh implementer conductor from the governed plan, enforces the same headless-launch discipline as other `remote_control` starts, actually spawns the detached implementer in `--terminal none` mode, and waits for the current instruction ACK instead of reporting success after script generation alone |
| `review-channel --action promote --terminal none --format md` | the current review slice is accepted and you want the next repo-owned task queued without hand-editing the bridge | reads the configured active-plan checklist, fail-closes unless the current verdict is resolved and findings are clear, rewrites `Current Instruction For Claude`, and refreshes the latest review projections from the same derived next-step source |
| `review-channel --action launch --terminal none --dry-run --format md --refresh-bridge-heartbeat-if-stale` | you want to bootstrap the current Codex-reviewer / Claude-implementer compatibility loop from a fresh conversation without hand-editing stale heartbeat metadata first | enforces the fail-closed launch contract, blocks launch when the typed checkpoint budget already says the slice must checkpoint first, auto-refreshes stale/missing reviewer heartbeat metadata only when the rest of the live bridge contract is already valid, accepts canonical reviewer-reset implementer placeholders (`Claude Status: - pending`, `Claude Ack: - pending`) for a fresh instruction revision, reads the static planned lane table from `dev/active/review_channel.md`, treats the emitted `registry/agents.json` as provider/session-backed runtime state, generates conductor launch scripts with clean-exit auto-relaunch supervision, and shows the exact bootstrap before opening any terminals. Use `--terminal none` for dry-run/script-only work, explicit headless launches, or governed `remote_control` sessions rather than as the casual local default. |
| `review-channel --action launch --terminal terminal-app --refresh-bridge-heartbeat-if-stale` | you want the live Codex + Claude conductor windows and the bridge heartbeat may have aged out | performs the same guarded bootstrap, refuses a fresh launch when the typed checkpoint budget is already over limit, repairs stale/missing reviewer heartbeat metadata when that is the only blocker, accepts canonical reviewer-reset implementer placeholders for a new instruction revision, then opens one Terminal.app window per provider; it still fails closed if the existing repo-owned session artifacts still look active so a second launch cannot silently race on the same `latest/sessions/` logs, and a successful plain launch now also reaps superseded stale conductor metadata/windows after the fresh pair comes up. In `local_terminal` sessions this is the default live launch/recovery path; typed recovery/doctor surfaces only recommend headless relaunch when the runtime is explicitly `remote_control`, and visible local launch/recover now also fail closed when the repo root is a transient temp clone (`/tmp`, `/private/tmp`, or the active system temp dir) so provider directory-trust prompts cannot stall automation before the conductor even starts. |
| `review-channel --action attach-remote-control --session-url https://claude.ai/code/session_... --terminal none --format json` | you need the external Claude phone session represented inside the typed runtime instead of only in chat memory | writes the canonical `remote_control_attachment` sidecar under the review status root, refreshes typed `review_state.json` when bridge/runtime paths are available, and projects the same attachment upward through reviewer runtime, session-resume, startup, and control-plane readers |
| `remote-control dry-run --provider claude --format md` | you want to preview typed phone/dashboard lifecycle state without launching Claude or mutating typed attachment state | shows current attachment status, TTL/expiry state, slash entrypoints, the provider built-in `/remote-control` command, and the operator mode that status/startup surfaces will derive |
| `remote-control hook --provider claude --format json` | Claude's project-level async `UserPromptExpansion` hook, or broad `UserPromptSubmit` fallback, fired after the operator typed built-in `/remote-control` or `/rc` | reads the hook JSON from stdin, fast-exits on non-remote-control prompts, prefers Claude's live `~/.claude/sessions/<pid>.json` `bridgeSessionId` proof for the matching `sessionId`/repo cwd, falls back to a same-session transcript `bridge_status` URL, dedupes multiple hook events for the same activation, then writes the identity-bound `RemoteControlAttachmentState` with `physical_confirmation_method=claude_session_state_bridge` or `claude_hook_transcript`; without trusted proof it records origin evidence but fails closed instead of promoting remote mode |
| `remote-control status --provider claude --format md` | you need the typed surface to agree with Claude's visible Remote Control active/inactive status | reads the current attachment, reconciles from live Claude session-state `bridgeSessionId` proof when present, and clears session-state-owned active state when that bridge id disappears so toggling built-in `/remote-control` off returns the typed mode to `local_terminal` |
| `remote-control enter --provider claude --entrypoint /project:typed-remote-control --session-url https://claude.ai/code/session_... --format md` | Claude built-in `/remote-control` is already active and exposed a real provider session URL that must be bound to typed runtime state | writes or refreshes the provider-scoped `RemoteControlAttachmentState` sidecar with launcher source, host pid/session label, heartbeat TTL, previous operator mode, entrypoint metadata, and remote-control identity, then refreshes review status when bridge/runtime paths are available |
| `remote-control heartbeat --provider claude --format md` | an active remote session needs to keep `operator_interaction_mode=remote_control` from expiring while work continues | refreshes `last_seen_utc` on the same typed attachment when trusted provider-owned proof exists; direct CLI heartbeats without proof still fail closed, and stale TTL expiry stops remote mode promotion until status, hook, heartbeat, or `enter` refreshes the attachment |
| `remote-control exit --provider claude --format md` | the remote session is closing and local-terminal operator truth should resume | marks the attachment detached and refreshes review status so startup, status, doctor, dashboard, and session-resume stop treating the phone lane as live |
| `./dev/scripts/remote-bridge-loop.sh --session-url https://claude.ai/code/session_...` | you need the legacy wrapper name while the provider-owned `/remote-control` surface is active | forwards to `devctl remote-control start --launcher-source remote-bridge-loop --entrypoint legacy_remote_bridge_loop`; lifecycle policy and typed attachment writes remain in `devctl remote-control` |

Primary-worktree note:
- In remote-control or other phone/dashboard-led `single_agent` lanes, keep
  the primary worktree as the control/dashboard lane and run mutating coding in
  reusable worker worktrees. The operator should interact with typed lane
  state, not manage git worktree paths from the phone.
| `review-channel --action rollover --rollover-threshold-pct 50 --await-ack-seconds 180 --format md` | the active conductor is nearing compaction and needs a clean relaunch instead of summary-only recovery | writes a repo-visible handoff bundle, relaunches fresh Codex/Claude conductors, and waits for visible rollover ACK lines in `bridge.md` before the retiring session exits |
| `autonomy-benchmark --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --swarm-counts 10,15,20,30,40 --tactics uniform,specialized,research-first,test-first --dry-run` | you want measurable swarm tradeoff data before scaling live runs | validates active-plan scope, runs tactic/swarm-size matrix batches, and emits one benchmark report with per-scenario metrics/charts |
| `swarm_run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --mode report-only --run-label <label>` | you want one fully-guarded plan-scoped swarm run without manual glue steps | loads active-plan scope, executes swarm with reviewer+post-audit defaults, runs governance checks, appends progress/audit evidence to the plan doc, and in continuous mode can auto-tune agent count with `--feedback-*` sizing controls |
| `autonomy-report --source-root dev/reports/autonomy --library-root dev/reports/autonomy/library --run-label daily-ops` | you want one human-readable autonomy digest | bundles latest loop/watch artifacts into a dated folder with summary markdown/json and optional charts |
| `autonomy-swarm --question \"<scope>\" --prompt-tokens <n> --token-budget <n>` | you want adaptive multi-agent autonomy execution | computes recommended agent count from metadata + budget, reserves one default reviewer lane (`AGENT-REVIEW`) when possible, runs bounded loops only when mutating modes also have typed fanout readiness, writes one swarm summary bundle, then auto-runs a post-audit digest bundle (unless `--no-post-audit`) |
| `probe-report --format md --output /tmp/probe-report.md --json-output /tmp/probe-report.json` | you want one repo-owned AI-slop review packet instead of running probe scripts one by one, especially after new modules, refactors, string dispatch, 3+ parameter signatures, or concurrency changes | runs every registered review probe, aggregates all emitted `risk_hints`, writes `dev/reports/probes/review_targets.json`, refreshes `summary.{md,json}`, `file_topology.json`, `review_packet.{json,md}`, and hotspot `hotspots.{mmd,dot}` views, then prints one human/agent-friendly report |
| `probe-report --quality-policy /tmp/pilot-policy.json --adoption-scan --format md` | you are onboarding a new repo and need the first probe packet to rank the whole current worktree instead of a meaningless empty diff | runs every registered review probe against the full current worktree using the supplied repo policy, then emits the normal aggregated packet/artifacts |
| `check --profile ci --repo-path /tmp/copied-repo --adoption-scan --format md` | you need the full routed AI-guard bundle against another local repo from this checkout | resolves the target repo through `--repo-path`, runs the normal routed check bundle against that repo, and keeps external-repo proof honest by skipping host-local cleanup lanes that only make sense for this checkout |
| `probe-report --repo-path /tmp/copied-repo --adoption-scan --format md` | you need to scan another local repo from this checkout without `cd`-ing into it first | resolves the target repo policy/scopes through `--repo-path`, runs the normal onboarding probe packet against that repo, and writes the packet under the target repo's `dev/reports/probes/` root by default |
| `governance-bootstrap --target-repo /tmp/copied-repo --format md` | a copied pilot repo or submodule snapshot has a broken `.git` pointer or no starter policy yet | repairs the broken gitdir indirection, reinitializes a standalone local git worktree when needed, writes a starter `dev/config/devctl_repo_policy.json`, seeds portable preset JSON files plus explicit `quality_scopes`, and writes a repo-local `dev/guides/PORTABLE_GOVERNANCE_SETUP.md` onboarding file; it does not make `startup-context` target-aware from the engine checkout, so real startup/push proof still needs the governance stack installed/exported into the target repo |
| `audit-scaffold` | AI-guard/tooling guards failed | creates one shared fix list file |
| `failure-cleanup --dry-run` | CI is green and you want to clean old failure artifacts | safely previews/removes stale failure bundles |

### AI guard pack details

`check --profile ai-guard` currently runs:

1. `check_code_shape.py`
2. `check_duplicate_types.py`
3. `check_structural_complexity.py`
4. `check_rust_test_shape.py`
5. `check_ide_provider_isolation.py --fail-on-violations`
6. `check_compat_matrix.py`
7. `compat_matrix_smoke.py`
8. `check_naming_consistency.py`
9. `check_rust_lint_debt.py`
10. `check_rust_best_practices.py`
11. `check_rust_compiler_warnings.py`
12. `check_serde_compatibility.py`
13. `check_rust_runtime_panic_policy.py`
14. `check_rust_audit_patterns.py`
15. `check_rust_security_footguns.py`

Use this profile for fast guard-focused iteration; run your target full profile
(`ci`, `prepush`, or `release`) before pushing.

### Review probe pack details

- `check --profile ci` is the default post-edit command when you need the hard
  guards and the full review-probe pack together.
- `probe-report --format md` is the default ranked handoff packet after new
  modules, refactors, string-based dispatch, 3+ parameter signatures, or
  concurrent/shared-state changes.
- If that packet shows `Design Decision Packets`, those entries came from
  repo-root `.probe-allowlist.json` rather than a silent suppression; use them
  as explicit architecture-review inputs for AI or human decision-makers, not
  as a reason to skip follow-up.
- `quality-policy --format md` is the canonical live inventory of which
  guards/probes are enabled for the current repo policy or a supplied portable
  policy override. On this repo, that resolved inventory now includes
  `startup_authority_contract`, so a branch with local unpublished commits and
  fresh dirty worktree state fails the normal `check --profile ci` quality lane
  instead of surfacing only at startup/push time.
- `probe_compatibility_shims.py` is now part of that pack. It uses the same
  portable shim primitive as package-layout to surface missing metadata,
  expired wrappers, broken shim-target convergence, and shim-heavy roots or
  crowded flat families. Normal working-tree runs only scan touched shim
  candidates; use
  `python3 dev/scripts/checks/probe_compatibility_shims.py --since-ref __DEVCTL_EMPTY_TREE_BASE__ --head-ref __DEVCTL_WORKTREE_HEAD__ --format md`
  for the full repo backlog. If a root helper wrapper is an intentional
  long-lived public seam, declare it in repo policy
  `probe_compatibility_shims.allowed_public_shims`; otherwise the probe will
  continue treating it as temporary migration debt.
- `probe_architecture_connectivity.py` is the architecture-aware probe family
  seed. It consumes `ConnectivityRegistrySnapshot` plus the registry reader
  verification pass and emits architecture-lens hints when a declared typed
  contract reader lacks evidence or the registry itself reports source-writer
  warnings.
- The promoted code-shape probe family now includes:
  `probe_blank_line_frequency.py`, `probe_identifier_density.py`,
  `probe_term_consistency.py`,
  `probe_cognitive_complexity.py`, `probe_fan_out.py`,
  `probe_side_effect_mixing.py`, `probe_mutable_parameter_density.py`,
  `probe_match_arm_complexity.py`, and `probe_tuple_return_complexity.py`.
  Together they surface fragmented flow, unreadable naming, branch overload,
  orchestration sprawl, legacy or mixed public terminology, mixed side
  effects, mutable-parameter overload, oversized `match` arms, and tuple-return
  debt before those patterns spread.
- The broader staged code-shape probe implementations now live under
  `dev/scripts/checks/code_shape_probes/`, with the stable root
  `probe_*.py` files kept as thin wrappers so the crowded checks root stays
  policy-compliant.
- When you add or retune a guard/probe, preset, or repo policy file, run
  `quality-policy --format md` and `render-surfaces --format md`; use
  `render-surfaces --write --format md` when the governed instruction surfaces
  need regeneration.
- When you change the shared platform blueprint, runtime contract models,
  durable probe/report schema constants, or startup-surface routing text, run
  `check_platform_contract_closure.py` together with
  `platform-contracts --format md`.
- Probe packet artifacts live under `dev/reports/probes/latest/` and include:
  `summary.{md,json}`, `review_targets.json`, `file_topology.json`,
  `review_packet.{json,md}`, and hotspot `hotspots.{mmd,dot}` views.

## `audit-scaffold` in plain language

What it does:

- Creates one fix list at `dev/reports/audits/RUST_AUDIT_FINDINGS.md`.
- Pulls findings from the guard scripts so you do not have to read many logs.

When it runs automatically:

- After `devctl check --profile ai-guard` fails.
- On tooling-control-plane CI failure paths that generate remediation artifacts.

When to run it yourself:

- You fixed part of the issues and want a fresh fix list.
- You want findings for only one commit range (`--since-ref` and `--head-ref`).
- You are about to split remediation work across multiple agents.

When to skip it:

- Guard checks are already green.
- The change is docs-only and does not touch source-quality guards.

What you should expect:

- A single markdown file with:
  - which guards failed,
  - which files are affected,
  - what to fix next,
  - what to re-run to confirm green.

## Devctl Internals

`devctl` keeps shared behavior in a few helper modules so command output stays
consistent:

- `dev/scripts/pyproject.toml`: local Python tooling configuration (ruff/mypy)
  for `dev/scripts/**` sources.
- `dev/scripts/devctl/process_sweep/`: shared process parsing/cleanup package
  used by `check`, `hygiene`, `process-cleanup`, and `process-audit`,
  including descendant-aware expansion for orphaned/stale cleanup trees.
- `dev/scripts/devctl/guard_run_core.py`: typed request, git snapshot, and
  render helpers behind `guard-run`, so raw test/fix command execution keeps
  one policy-aligned path for hygiene and watchdog metadata.
- `dev/scripts/devctl/quality_policy.py`: built-in guard/probe capability
  registry plus repo-capability detection (`python`, `rust`) and repo-policy
  resolution. Keep repo-local enablement/default args in
  `dev/config/devctl_repo_policy.json` instead of re-hard-coding tuples in the
  command layer.
- `dev/scripts/devctl/probe_topology_*.py`: shared topology scan, scoring,
  packet, render, and artifact helpers behind `probe-report`; these are what
  write `file_topology.json`, `review_packet.{json,md}`, and hotspot graph
  views.
- `dev/scripts/devctl/security/parser.py`: shared CLI parser wiring for the
  `security` command so `cli.py` stays smaller and easier to maintain.
- `dev/scripts/devctl/security/python_scope.py`: shared Python changed/all
  scope resolution and target derivation for core security scanners.
- `dev/scripts/devctl/governance/push_policy.py`: repo-governance push-policy
  loader and command builder shared by `push`, `sync`, `ship`, and
  `governance-draft`, including policy-gated bypass rules and staged
  publication truth. Parse/coerce helpers live in `push_policy_parse.py`.
- `dev/scripts/devctl/governance/bootstrap_push.py`: starter repo-pack push
  governance detection used by `governance-bootstrap` to seed default remote,
  branch, and guard-routing policy.
- `dev/scripts/devctl/sync_parser.py`: shared CLI parser wiring for the
  `sync` and `push` commands so `cli.py` stays within shape budgets.
- `dev/scripts/devctl/runtime/vcs.py`: shared git/vcs helper functions used by
  `push`, `sync`, and other repo-owned branch/release command surfaces.
- `dev/scripts/devctl/commands/vcs/push.py`: canonical `devctl push`
  implementation for policy-driven guarded branch pushes.
- `dev/scripts/devctl/commands/vcs/push_report.py`: shared report/render
  helpers for the guarded push surface.
- `dev/scripts/devctl/cihub_setup_parser.py`: shared CLI parser wiring for the
  `cihub-setup` command.
- `dev/scripts/devctl/orchestrate_parser.py`: shared CLI parser wiring for
  `orchestrate-status` and `orchestrate-watch`.
- `dev/scripts/devctl/script_catalog.py`: canonical check-script path registry
  used by commands to avoid ad-hoc path strings.
- `dev/scripts/devctl/review_channel/`: namespace package for review-channel
  helper modules; keep new review-channel helpers under this directory instead
  of adding more top-level `review_channel_*.py` files in `dev/scripts/devctl/`.
- `dev/scripts/devctl/path_audit.py`: shared stale-path scanner and rewrite
  engine used by `path-audit`, `path-rewrite`, and `docs-check --strict-tooling`.
  The public module now stays as a stable shim while implementation helpers live
  under `dev/scripts/devctl/path_audit_support/core.py` and
  `dev/scripts/devctl/path_audit_support/workspace.py`.
- `dev/scripts/devctl/triage/parser.py`: shared CLI parser wiring for the
  `triage` command so `cli.py` remains under shape limits.
- `dev/scripts/devctl/triage/loop_parser.py`: shared CLI parser wiring for the
  `triage-loop` command.
- `dev/scripts/devctl/loop_fix_policy.py`: shared fix-policy engine used by
  both `triage-loop` and `mutation-loop` wrappers.
- `dev/scripts/devctl/triage/loop_policy.py`: shared policy-gate evaluation
  for `triage-loop` fix execution (`AUTONOMY_MODE`, branch allowlist, command
  prefix allowlist).
- `dev/scripts/devctl/triage/loop_escalation.py`: shared review-escalation
  comment renderer/upsert helper for `triage-loop`.
- `dev/scripts/devctl/triage/loop_support.py`: shared connectivity/comment/
  bundle helper logic used by `triage-loop`.
- `dev/scripts/devctl/autonomy/loop_parser.py`: shared CLI parser wiring for
  the `autonomy-loop` controller command.
- `dev/scripts/devctl/autonomy/benchmark_parser.py`: shared CLI parser wiring
  for the `autonomy-benchmark` swarm-matrix command.
- `dev/scripts/devctl/autonomy/run_parser.py`: shared CLI parser wiring for
  the `swarm_run` guarded plan-scoped swarm command.
- `dev/scripts/devctl/autonomy/benchmark_helpers.py`: shared helpers for
  `autonomy-benchmark` scenario orchestration, tactic prompts, and metric
  aggregation.
- `dev/scripts/devctl/autonomy/benchmark_matrix.py`: swarm-matrix execution
  helpers for `autonomy-benchmark`.
- `dev/scripts/devctl/autonomy/benchmark_runner.py`: per-scenario runner and
  bundle helpers for `autonomy-benchmark`.
- `dev/scripts/devctl/autonomy/benchmark_render.py`: markdown/chart renderer
  for `autonomy-benchmark` bundles.
- `dev/scripts/devctl/autonomy/run_helpers.py`: shared helpers for
  `swarm_run` scope validation, prompt derivation, command fanout, and plan
  markdown section updates.
- `dev/scripts/devctl/autonomy/run_feedback.py`: closed-loop sizing helpers
  for `swarm_run` continuous mode (cycle signal extraction + downshift/upshift decisions).
- `dev/scripts/devctl/autonomy/run_render.py`: markdown renderer for
  `swarm_run` run bundles.
- `dev/scripts/devctl/autonomy/report_helpers.py`: data-collection helpers for
  `autonomy-report` source discovery, summarization, and bundle assembly.
- `dev/scripts/devctl/autonomy/report_render.py`: markdown/chart rendering
  helpers used by `autonomy-report` output bundles.
- `dev/scripts/devctl/autonomy/swarm_helpers.py`: adaptive swarm planning
  helpers (metadata scoring, agent-count recommendation, swarm report rendering/charts).
- `dev/scripts/devctl/autonomy/swarm_post_audit.py`: shared post-audit helper
  logic used by `autonomy-swarm` for digest payload normalization and bundle writes.
- `dev/scripts/devctl/autonomy/loop_helpers.py`: shared autonomy-loop
  policy/schema helpers (caps, packet refs, trace extraction, markdown render).
- `dev/scripts/devctl/autonomy/phone_status.py`: phone-status payload + markdown
  helpers used by `autonomy-loop` queue snapshots.
- `dev/scripts/devctl/phone_status_views.py`: projection/render helpers used by
  `phone-status` (`full|compact|trace|actions`) and controller-state bundle writes.
- `dev/scripts/devctl/autonomy/status_parsers.py`: shared parser wiring for
  `autonomy-report` and `phone-status`.
- `dev/scripts/devctl/controller_action_parser.py`: parser wiring for
  `controller-action`.
- `dev/scripts/devctl/controller_action_support.py`: policy/mode/dispatch
  helper logic used by `controller-action`.
- `dev/scripts/devctl/mutation_loop_parser.py`: shared CLI parser wiring for
  the `mutation-loop` command.
- `dev/scripts/devctl/failure_cleanup_parser.py`: shared CLI parser wiring for
  the `failure-cleanup` command.
- `dev/scripts/devctl/reports_cleanup_parser.py`: shared CLI parser wiring for
  the `reports-cleanup` command.
- `dev/scripts/devctl/reports_retention.py`: shared report-retention planning
  helpers used by both `hygiene` warnings and `reports-cleanup`.
- `dev/scripts/devctl/commands/python_tests.py`: bounded pytest adapter for
  repo-owned Python suites.
- `dev/scripts/devctl/commands/check_profile.py`: shared `check` profile
  toggles/normalization.
- `dev/scripts/devctl/commands/check_steps.py`: shared `check` step-spec
  builder plus serial/parallel execution helpers with stable result ordering.
- `dev/scripts/devctl/status_report.py`: shared payload collection and markdown
  rendering used by both `status` and `report`.
- `dev/scripts/devctl/commands/mcp.py`: optional read-only MCP adapter command
  that exposes allowlisted `devctl` snapshots and stdio JSON-RPC transport.
- `dev/scripts/devctl/triage/support.py`: shared triage classification,
  artifact-ingestion, markdown rendering, and bundle writers used by
  `dev/scripts/devctl/commands/triage.py`.
- `dev/scripts/devctl/triage/enrich.py`: normalization/routing helpers used to
  map triage issues and `cihub` artifact records into consistent severity +
  owner labels, including optional owner-map file overrides.
- `dev/scripts/devctl/commands/triage_loop.py`: bounded CodeRabbit loop command
  with source-run correlation controls and summary/comment notification wiring.
- `dev/scripts/devctl/commands/controller_action.py`: policy-gated operator
  action command (`refresh-status`, `dispatch-report-only`, `pause-loop`, `resume-loop`).
- `dev/scripts/devctl/commands/autonomy_loop.py`: bounded autonomy controller
  command that runs triage-loop/loop-packet rounds and emits packet/queue
  artifacts for phone/chat handoff paths.
- `dev/scripts/devctl/commands/autonomy_benchmark.py`: active-plan-scoped
  swarm matrix benchmark command that compares tactic/swarm-size tradeoffs.
- `dev/scripts/devctl/commands/autonomy_report.py`: autonomy digest command
  that writes dated human-readable summaries under `dev/reports/autonomy/library`.
- `dev/scripts/devctl/commands/autonomy_run.py`: guarded plan-scoped autonomy
  pipeline command that executes swarm + governance + plan-evidence append in
  one step.
- `dev/scripts/devctl/commands/autonomy_swarm.py`: adaptive swarm command that
  auto-sizes and runs parallel autonomy-loop lanes with one consolidated report bundle.
- `dev/scripts/devctl/commands/autonomy_loop_support.py`: validation and
  policy-deny report helpers used by `autonomy-loop`.
- `dev/scripts/devctl/commands/autonomy_loop_rounds.py`: per-round controller
  execution helper for `autonomy-loop` (triage-loop/loop-packet/checkpoint +
  phone snapshot emission).
- `dev/scripts/devctl/commands/mutation_loop.py`: bounded mutation loop command
  with report/fix modes, hotspot playbook output, and policy-gated fix paths.
- `dev/scripts/devctl/policy_gate.py`: shared JSON policy-script runner used by
  `docs-check` strict-tooling plus orchestrator accountability summaries
  (active-plan + multi-agent sync checks).
- `dev/scripts/devctl/commands/docs_check_support.py`: shared docs-check policy
  helpers (path classification, deprecated-reference scan, failure-reason and
  next-action builders).
- `dev/scripts/devctl/commands/docs_check_render.py`: shared docs-check
  markdown renderer used by `dev/scripts/devctl/commands/docs_check.py`.
- `dev/scripts/devctl/commands/ship_common.py` and
  `dev/scripts/devctl/commands/ship_steps.py`: shared ship step/runtime helpers
  used by `dev/scripts/devctl/commands/ship.py`.
- `dev/scripts/devctl/commands/security.py`: shared local security gate runner
  (RustSec policy + optional `zizmor` scanner behavior).
- `dev/scripts/devctl/commands/cihub_setup.py`: allowlisted CIHub setup command
  implementation (preview/apply flow with capability probing + strict mode).
- `dev/scripts/devctl/commands/failure_cleanup.py`: guarded cleanup command for
  local failure triage artifact directories with default root guard, optional
  scoped CI-green filters, and explicit override mode for non-default cleanup
  roots under `dev/reports/**`.
- `dev/scripts/devctl/commands/process_cleanup.py`: guarded host-process
  cleanup command for orphaned/stale repo-related trees with strict
  post-clean verification support.
- `dev/scripts/devctl/commands/reports_cleanup.py`: retention-based stale
  report cleanup command for managed run-artifact roots under `dev/reports/**`
  with protected paths, dry-run preview, and confirmation-safe deletion flow.
- `dev/scripts/devctl/publication_sync.py`,
  `dev/scripts/devctl/publication_sync_parser.py`, and
  `dev/scripts/devctl/commands/publication_sync.py`: tracked external
  publication registry helpers plus report/record command wiring used to keep
  papers/sites aligned with watched repo evidence.
- `dev/scripts/devctl/commands/audit_scaffold.py`: guard-driven remediation
  scaffold generator for Rust modularity/pattern drift; aggregates JSON outputs
  from `check_code_shape.py`, `check_rust_test_shape.py`,
  `check_rust_lint_debt.py`, `check_rust_best_practices.py`,
  `check_rust_compiler_warnings.py`,
  `check_serde_compatibility.py`, `check_rust_runtime_panic_policy.py`,
  `check_rust_audit_patterns.py`, and `check_rust_security_footguns.py` into
  one active markdown execution surface.
- `dev/scripts/devctl/collect.py`: shared git/CI collection helpers with
  compatibility fallback for older `gh run list --json` field support.
- `dev/scripts/devctl/commands/release_prep.py`: shared release metadata
  preparation helpers used by `ship/release --prepare-release` (Cargo/PyPI/app
  version fields, changelog heading rollover, and `MASTER_PLAN` Status
  Snapshot refresh).
- `dev/scripts/devctl/common.py`: shared command runner returns structured
  non-zero results (including missing-binary failures) instead of uncaught
  exceptions, streams live subprocess output, and keeps bounded failure-output
  excerpts for markdown/json report diagnostics.

Historical shard artifacts from previous CI runs are useful for hotspot triage,
but release gating should always use a full aggregated score generated from the
current commit's shard outcomes. Use `--max-age-hours` in local gates when you
need freshness enforcement instead of historical trend visibility.

## Markdown Lint Config

Markdown lint policy files live under `dev/config/`:

- `dev/config/markdownlint.yaml`
- `dev/config/markdownlint.ignore`

## Release Workflow (Recommended)

```bash
# 1) align release versions across Cargo/PyPI/macOS app plist + changelog
python3 dev/scripts/checks/check_release_version_parity.py
# Optional: auto-prepare these files in one step
python3 dev/scripts/devctl.py ship --version X.Y.Z --prepare-release

# 2) run release preflight for the exact version (publish workflows require this same-SHA gate)
gh workflow run release_preflight.yml -f version=X.Y.Z
# Optional: wait for the preflight run to complete before continuing
# gh run watch <run-id>

# 3) verify same-SHA release gates (preflight + triage + ralph)
CI=1 python3 dev/scripts/devctl.py release-gates --branch master --sha "$(git rev-parse HEAD)" --wait-seconds 1800 --poll-seconds 20 --format md

# 4) create tag + notes
python3 dev/scripts/devctl.py release --version X.Y.Z

# 5) publish GitHub release (triggers publish_pypi.yml + publish_homebrew.yml + publish_release_binaries.yml + release_attestation.yml)
gh release create vX.Y.Z --title "vX.Y.Z" --notes-file /tmp/voiceterm-release-vX.Y.Z.md

# 6) monitor publish workflows
gh run list --workflow publish_pypi.yml --limit 1
gh run list --workflow publish_homebrew.yml --limit 1
gh run list --workflow publish_release_binaries.yml --limit 1
gh run list --workflow release_attestation.yml --limit 1
# gh run watch <run-id>

# 7) verify published package
curl -fsSL https://pypi.org/pypi/voiceterm/X.Y.Z/json | rg '"version"'

# 8) fallback Homebrew update (if workflow path is unavailable)
python3 dev/scripts/devctl.py homebrew --version X.Y.Z
```

Manual fallback (if GitHub Actions publish lanes are unavailable):

```bash
python3 dev/scripts/devctl.py pypi --upload --yes
python3 dev/scripts/devctl.py homebrew --version X.Y.Z
```

Or run unified control-plane commands directly:

```bash
# Workflow-first release path
python3 dev/scripts/devctl.py ship --version X.Y.Z --verify --tag --notes --github --yes
# Workflow-first with auto metadata prep
python3 dev/scripts/devctl.py ship --version X.Y.Z --prepare-release --verify --tag --notes --github --yes
gh run list --workflow publish_pypi.yml --limit 1
gh run list --workflow publish_homebrew.yml --limit 1
gh run list --workflow publish_release_binaries.yml --limit 1
gh run list --workflow release_attestation.yml --limit 1

# Manual fallback (local PyPI/Homebrew publish)
python3 dev/scripts/devctl.py ship --version X.Y.Z --pypi --verify-pypi --homebrew --yes
```

## Test Scripts

| Script | Purpose |
|---|---|
| `dev/scripts/tests/benchmark_voice.sh` | Voice pipeline benchmarking |
| `dev/scripts/tests/measure_latency.sh` | Latency profiling + CI guardrails |
| `dev/scripts/tests/compare_python_rust_voice_latency.sh` | Interactive Rust-native vs Python-fallback voice-latency comparison |
| `dev/scripts/tests/compare_python_rust_stt_strict.sh` | Strict STT-only benchmark on one shared WAV clip (same model, Rust vs Python) |
| `dev/scripts/tests/audit_latency_math.py` | Validates `latency_audit` log math + badge rendering consistency |
| `dev/scripts/tests/integration_test.sh` | IPC integration testing |
| `dev/scripts/tests/wake_word_guard.sh` | Wake-word regression + soak guardrails |

Example latency guard command:

```bash
dev/scripts/tests/measure_latency.sh --ci-guard --count 3
dev/scripts/tests/compare_python_rust_voice_latency.sh --count 3
# Auto-install whisper CLI if missing (or accept the interactive install prompt)
dev/scripts/tests/compare_python_rust_voice_latency.sh --count 3 --auto-install-whisper
# Short-flag variant to avoid wrapped long options in narrow terminals
dev/scripts/tests/compare_python_rust_voice_latency.sh --count 3 --secs 3 --tail-ms 1500 --max-capture-ms 45000
# Strict same-audio/same-model STT benchmark
dev/scripts/tests/compare_python_rust_stt_strict.sh --count 3 --secs 3 --whisper-model base.en
# Verify HUD/log latency math consistency from collected logs
python3 dev/scripts/tests/audit_latency_math.py --log-path "${TMPDIR:-/tmp}/voiceterm_tui.log"
```

Workspace-path note:
- `dev/scripts/tests/measure_latency.sh` auto-detects `rust/` and falls back to
  legacy `src/` so CI/local guard commands remain stable across migration-era
  branches.
- `dev/scripts/tests/measure_latency.sh` uses `set -u`-safe empty-array
  expansion for optional args so voice-only and CI synthetic modes execute
  cleanly when optional arg arrays are unset/empty.
- `dev/scripts/tests/benchmark_voice.sh` and
  `dev/scripts/tests/compare_python_rust_voice_latency.sh` use the same
  `rust/`-first workspace detection with legacy `src/` fallback.

Governed-transition note:
- `dev/scripts/devctl/runtime/governed_transitions.py` owns the
  `@governed_transition` decorator and `TransitionContract` metadata.
- `dev/state/transition_modules.jsonl` is the manifest that imports transition
  owner modules for deterministic decorator registration.
- Transition contract additions should update platform-contract rows, registry
  rows, schema fixtures, and focused runtime tests before running
  `check_platform_contract_closure.py` and `check_schema_fixture_handshake.py`.
- `dev/scripts/checks/check_governed_transitions.py` verifies registered
  `TransitionContract` metadata by building lifecycle graph edges and walking
  required/produced state paths through `walk_context_graph`; it is part of
  the shared governance bundle and CI workflows.
- Runtime enforcement is opt-in per transition. When a transition declares
  `runtime_enforced=True`, its resolver functions must project pre/post state
  refs into the same string vocabulary used by `requires` and `produces`; an
  illegal ref raises `TransitionStateViolation`. Pre-state resolvers receive
  the wrapped function arguments, post-state resolvers receive only the
  reducer result, and resolver outputs must be derived from explicit typed
  state fields rather than hard-coded happy-path constants.

Receipt-state evidence note:
- `dev/scripts/devctl/runtime/validation_contracts.py` keeps
  `ValidationReceipt` backward-compatible while adding pre/post state evidence
  and snapshots for governed guard execution.
- `dev/scripts/devctl/runtime/commit_receipt.py` keeps `CommitReceipt` as the
  governed commit boundary and requires `validation_passed` evidence through
  `require_receipt_state()` before recording a commit SHA.
- Do not add a parallel attestation-path checker or alternate enforcement
  decorator unless a typed plan explicitly migrates the existing receipt
  lifecycle.

Feature-proof output truth note:
- `dev/scripts/devctl/runtime/feature_proof_receipt.py` owns
  `NonTrivialOutputProof` and the remediation finding payload for legacy FPRs.
  New FPR construction that has repo-root context must reject unresolved or
  circular evidence refs before the receipt is accepted.
- `dev/scripts/checks/check_non_trivial_output_proof.py` is the fail-closed
  guard over existing `proven_passed` FPR artifacts. It checks ref resolution,
  pytest-node evidence (`::` in `tests_run`), and circular FPR self-reference,
  then writes `dev/state/non_trivial_output_proof_remediation_findings.jsonl`
  when asked to backfill remediation findings.
- `commit_receipt.py` may mark `FeatureProofReceipt.real_life_test_status` as
  `proven_passed` only when the receipt builder selected a concrete pytest node
  id. Guard bundles, projection refreshes, and plan refs can pass validation, but
  they must stay `not_tested_with_rationale` instead of becoming real-life test
  proof.

Packet TTL and registry identity note:
- `dev/scripts/devctl/runtime/packet_transport_expiry.py` owns per-kind packet
  TTLs: `task_produced` is 30 days, `decision` is 14 days, and `question` plus
  `finding` are 7 days. `packet_kind_ttl.py` mirrors peer-heartbeat evidence
  for alive/expired/missing packet-kind status.
- `dev/scripts/checks/check_contract_registry_composite_key_uniqueness.py`
  guards `(contract_id, schema_version)` uniqueness in
  `dev/state/contract_registry.jsonl`. Same-owner artifact/runtime duplicates
  are deduped by `platform/contract_registry.py`; divergent owner forks remain
  explicit policy TODOs until operator direction chooses the canonical owner.

Remote Evidence Queue note:
- `dev/scripts/devctl/remote_evidence_queue/` owns the first async-proof
  reconciliation substrate: `RemoteValidationReceipt` plus
  `find_finding_affected_paths_in_current_tree()`.
- The path-freshness helper maps `FindingRecord.file_path` from an
  `applies_to_tree` to `current_tree` using the existing publication-sync git
  path-diff helpers. Present or renamed paths remain relevant; removed paths
  are superseded.
- `CommitReceipt` and `RunRecord` carry additive `tree_content_hash` fields so
  remote proof can bind to validation/commit tree identity without a parallel
  receipt universe.

Derived-state invalidation note:
- `dev/scripts/devctl/runtime/derived_state_invalidation.py` owns the shared
  payload helper for producer-side reload hints.
- Producers attach invalidation metadata to existing events and receipts,
  including packet arrival, packet lifecycle transition, packet durable
  ingestion, session liveness, and plan ingestion. Do not add a separate
  invalidation bus or authority store for these hints.
- `PlanIntentIngestionReceipt` carries `derived_state_invalidated` and
  `derived_state_invalidation` so plan-index, startup, `/develop next`, inbox,
  work-board, and agent-loop consumers can reload after typed plan state
  changes.

Typestate-result note:
- `dev/scripts/devctl/runtime/bypass_activation_result.py`,
  `dev/scripts/devctl/runtime/task_complete_result.py`, and
  `dev/scripts/devctl/commands/vcs/push_result_typestate.py` are the P102
  algebraic-result helpers for existing lifecycle outputs.
- Keep these helpers as typed projections over canonical contracts. Do not move
  authority out of `BypassLifecycle`, `TaskCompleteDecision`, or `ActionResult`.
- Add new result cases with frozen dataclasses, `Literal` discriminators, and
  `assert_never` coverage, then extend
  `dev/scripts/devctl/tests/runtime/test_typestate_exhaustiveness.py`.

Nominal ID note:
- `dev/scripts/devctl/runtime/typed_ids.py` owns `PacketId`, `ReceiptId`, and
  `PlanRowId` `NewType` wrappers plus normalizers and evidence-ref helpers.
- Use these wrappers at internal helper boundaries with real identifier-swap
  risk. Keep persisted contract fields string-compatible unless an explicit
  schema migration slice says otherwise.

Reviewer-mode authority note:
- `dev/scripts/devctl/runtime/reviewer_mode.py` fails closed to `tools_only`
  when reviewer mode text is missing or unknown. Callers that need a different
  fallback must pass an explicit `ReviewerMode` default.
- Bridge-state capability projections must pass the typed `TandemRole` into
  `build_conductor_capability_state()`. Provider ids such as `codex` and
  `claude` are adapter labels; collaboration role assignments decide which
  provider is the reviewer or implementer.

Governed push controller note:
- `dev/scripts/devctl/commands/vcs/push_control_decision.py` derives the
  controller-obedience report for `devctl.push.execute`.
- `dev/scripts/devctl/commands/vcs/push_authorization_control.py` projects the
  current remote commit pipeline `PushAuthorizationRecord` into the exact
  allowed actions `devctl.push.execute` and `vcs.push`. That record must still
  authorize the current HEAD; raw push and stale AgentLoopDecision projections
  are not publication authority.
- `dev/scripts/devctl/commands/vcs/push_attempted_command.py` keeps attempted
  push command rendering shared by the controller report and tests.
- `dev/scripts/devctl/commands/vcs/push_control_decision_report.py` owns the
  JSON/Markdown rendering for push controller-obedience failures.
- `dev/scripts/devctl/commands/vcs/push_preflight_flow.py` owns fetch,
  divergence, bridge-projection sync, and validation preflight routing so
  `push.py` stays a coordinator instead of accumulating preflight/controller
  concerns.
- `dev/scripts/checks/check_publication_scope_integrity_for_push.py` is the
  push-preflight adapter that resolves the same branch-aware base/head refs
  used by check-router before delegating to
  `check_publication_scope_integrity.py`; no-upstream extraction branches must
  not fall back to `@{u}` during governed publication. When check-router runs a
  range-scoped release bundle, direct `check_publication_scope_integrity.py`
  entries are routed through this adapter so the bundle keeps the same
  publication base/head refs as governed push.
- Keep branch allowlist updates in `dev/config/devctl_repo_policy.json` aligned
  with active extraction branches so governed push fails for real policy drift,
  not for an obsolete VoiceTerm-era branch prefix.

Check validation-scope note:
- `devctl check` accepts `--validation-scope` and forwards non-live scopes only
  to guards that declare validation-scope support in the quality policy
  registry.
- `check-router` also appends the same scope to nested `devctl check` commands
  during governed push preflight, so startup-authority and tandem-consistency
  stay visible as evidence without treating live collaboration freshness as a
  publication veto for an already authorized commit range.
