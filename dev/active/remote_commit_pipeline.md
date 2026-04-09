# Remote Commit Pipeline Plan

**Status**: active  |  **Last updated**: 2026-04-09 | **Owner:** Tooling/control plane/review runtime
Execution plan contract: required
This spec remains execution mirrored in `dev/active/MASTER_PLAN.md` under
`MP-377`. It freezes the Phase-0 design for the typed remote-session
commit/push pipeline that phone-steered and remote-control sessions must use
instead of raw terminal git mutation, prose approval, or shell-first rituals.

## Scope

Design one repo-owned typed pipeline that moves remote-control work from staged
changes to governed commit and governed push without requiring a local keyboard
or operator shell intervention.

This plan covers:

1. one canonical pipeline owner and lifecycle state machine for
   `drafted -> staged -> guards_running -> guards_passed|guards_failed ->
   operator_approval_pending -> approved|rejected -> commit_pending ->
   commit_recorded -> push_pending -> push_completed|push_blocked`
2. one action graph for `stage -> guard -> approve -> commit -> push ->
   recover`
3. reuse of existing repo-owned contracts:
   `ReviewerRuntimeContract`, `TypedAction -> ActionResult`,
   `PacketPostRequest`, existing guard bundles, and the current governed
   `vcs.push` flow
4. one phone/dashboard projection path where the remote-control session reads a
   doctor/status view and the operator approves through typed packets
5. fail-closed rules and a migration path away from the current ad hoc remote
   commit flow

Out of scope in this phase:

1. a second commit/push implementation path; the existing governed VCS
   implementation already exists, and this plan only changes typed lifecycle,
   projection, and approval behavior around that executor
2. a new shell-only recovery path
3. a second approval authority outside repo-owned typed packets and runtime
   artifacts

## Locked Decisions

1. The repo owns commit/push lifecycle truth. Bridge prose, chat prose, and
   terminal text may explain state but may not advance it.
2. `ReviewerRuntimeContract` remains the lifecycle gate. No remote commit/push
   path is valid while the repo-owned publisher or reviewer-supervisor runtime
   is missing, stale, or not publish-clear.
3. The remote-control session is a read-mostly dashboard over typed state. The
   phone/operator approves by emitting a typed packet, not by editing markdown
   or pasting a shell sequence.
4. Commit and push remain separate governed actions. `vcs.push` stays the
   canonical push executor; remote mode adds a typed commit stage in front of
   it instead of inventing a parallel publish path.
5. One active commit pipeline per worktree/branch is the safe default. If a
   second request appears, the repo must reject it or force explicit recovery
   instead of carrying competing pending approvals.
6. Approval is bound to a staged tree hash plus pipeline generation. Any diff
   drift, branch change, guard rerun, or runtime-generation mismatch invalidates
   the approval and forces recovery.
7. `doctor` is a projection. It may summarize readiness and recommended next
   action, but it must derive from typed owners rather than recomputing a
   second decision layer.
8. Guarded commit creation must be structural, not advisory. Remote-control
   work may not rely on agent discipline or chat instructions to remember guard
   runs; a repo-owned commit gate must enforce the same guard freshness that
   the typed pipeline and operator surfaces project.
9. Validation tier selection must be deterministic repo policy, not actor
   judgment. Agents and humans may ask for a fast or full proof, but governed
   checkpoint/commit/push must consume a tree-bound validation plan/receipt
   emitted by repo-owned routing. Missing, stale, or mismatched quality
   evidence is `unknown` or blocked; it is never equivalent to green.

## Cross-Plan Dependencies

1. `dev/active/ai_governance_platform.md` keeps product-boundary ownership for
   the shared governance runtime and the "same backend, different clients"
   rule.
2. `dev/active/platform_authority_loop.md` owns `TypedAction`, `ActionResult`,
   repo-pack push policy, typed checkpoint/push artifacts, and startup/work-
   intake authority.
3. `dev/active/review_channel.md` owns `PacketPostRequest`, review-state
   projection, doctor/status transport, and `ReviewerRuntimeContract`.
4. `dev/active/continuous_swarm.md` owns the phone-steered remote-control proof
   harness that will consume this pipeline once implemented.
5. `dev/active/operator_console.md` may later project the same pipeline, but
   it does not own a second approval path or an alternate VCS backend.
6. `dev/audits/architecture_hardening_plan.md` is ReviewSnapshot audit intake,
   not a peer plan. This file owns the raw-commit hook proof, override
   receipt enforcement, additional git-hook, `PushAuthorizationRecord`
   integrity, and generated publish/commit traceability findings from that
   audit; path/default and adopter-diagnostic findings route to
   `platform_authority_loop.md` / `portable_code_governance.md`.

## Data Contracts

### Canonical Owner

The new top-level runtime owner is `RemoteCommitPipelineContract`. It belongs in
the same `governance_runtime` ownership domain as `ReviewerRuntimeContract`,
persists as a repo-owned artifact, and is mirrored into `review_state.json`
plus the doctor projection rather than living only in the bridge or a wrapper
script.

Canonical surfaces:

1. durable artifact:
   `dev/reports/review_channel/latest/commit_pipeline.json`
2. compatibility mirror:
   `review_state.json.commit_pipeline`
3. compact readiness projection:
   `review-channel --action doctor`

### Reused Contracts

| Contract | Reuse in this plan |
|---|---|
| `ReviewerRuntimeContract` | gates remote commit/push readiness; `publish_clear` and daemon health are preconditions for approval, commit, and push |
| `TypedAction -> ActionResult` | every stageable action emits the same governed request/receipt pair instead of terminal-only text |
| `PacketPostRequest` | carries operator approval request and operator decision through the existing review-channel transport |
| Existing guard bundles | the `guard` node reuses the repo-routed task bundle plus risk-matrix add-ons instead of inventing a second validation stack |
| `check-router` / task routing | emits the selected bundle, risk add-ons, changed-path evidence, and escalation reasons that the validation-plan follow-up must bind to staged tree identity |
| Current `vcs.push` flow | remains the only publish executor; the new pipeline records and projects its existing staged truth (`validation_ready`, `published_remote`, `post_push_green`) |
| `LocalServiceEndpoint` + `CallerAuthorityPolicy` | define which backend path is allowed to execute commit/push and which callers may request, approve, or recover pipeline state |

### New Typed Records

Two typed records were sufficient for Phase 0:

1. `RemoteCommitPipelineContract`
   Purpose: singular orchestration owner for the remote commit/push lifecycle.
   Required fields:
   - `pipeline_id`
   - `state`
   - `requested_by`
   - `branch`
   - `remote`
   - `intent: CommitIntentState`
   - `guard_action_id`
   - `guard_result`
   - `reviewer_runtime_generation`
   - `approval_packet_id`
   - `decision_packet_id`
   - `approval_state`
   - `commit_action_id`
   - `commit_result`
   - `commit_sha`
   - `push_action_id`
   - `push_result`
   - `push_report_path`
   - `blocked_reason`
   - `recovery_action_allowed`
   - `generation_id`
   - `approval_expires_at_utc`
   - `approved_target_identity`
   - `override_state`
   - `override_request_packet_id`
   - `override_decision_packet_id`
   - `override_reason_code`
   - `override_scope`
   - `override_expires_at_utc`
   - `override_approved_target_identity`
   - `override_approved_by`
   - `override_rationale`
2. `CommitIntentState`
   Purpose: immutable staged-work snapshot consumed by guard, approval, and
   commit steps.
   Required fields:
   - `staged_tree_hash`
   - `staged_path_count`
   - `staged_paths`
   - `diff_summary`
   - `commit_message_draft`
   - `push_requested`
   - `guard_profile`
   - `work_intake_ref`

Validation-gate follow-up:

3. `ValidationPlan`
   Purpose: immutable repo-selected proof contract for one worktree or staged
   tree, replacing actor-selected "fast vs full" judgment.
   Required fields:
   - `validation_plan_id`
   - `source_tree_hash` or `staged_tree_hash`
   - `changed_paths`
   - `selected_bundle`
   - `required_addons`
   - `proof_level`
   - `escalation_reason`
   - `sufficient_for_checkpoint`
   - `sufficient_for_push`
   - `policy_hash`
   - `expires_at_utc`
   - `invalidation_reasons`
4. `ValidationReceipt`
   Purpose: executed proof evidence bound to one `ValidationPlan` and exact
   tree identity.
   Required fields:
   - `validation_receipt_id`
   - `validation_plan_id`
   - `tree_hash`
   - `executed_commands`
   - `action_results`
   - `status`
   - `failure_summary`
   - `artifact_paths`
   - `sufficient_for_checkpoint`
   - `sufficient_for_push`

If implementation promotes the top-level record into the platform contract
catalog, it should follow `platform/contracts.py` and land as a `ContractSpec`
row under `runtime_state_contract_rows.py` with startup tokens derived from the
compact readiness surface, not from full diff text.

### Canonical State Machine

| State | Meaning | Allowed next state |
|---|---|---|
| `drafted` | request exists but nothing is staged yet | `staged`, `push_blocked` |
| `staged` | git index matches `CommitIntentState.staged_tree_hash` | `guards_running`, `push_blocked` |
| `guards_running` | routed guard bundle is executing | `guards_passed`, `guards_failed` |
| `guards_passed` | guard bundle returned green receipt | `operator_approval_pending`, `push_blocked` |
| `guards_failed` | guard bundle returned fail/unknown/defer | `recover` |
| `operator_approval_pending` | typed approval packet is live and waiting on operator decision | `approved`, `rejected`, `recover` |
| `approved` | typed operator decision accepted current staged hash | `commit_pending`, `recover` |
| `rejected` | operator denied the current request | `recover` |
| `commit_pending` | governed executor has lease to create the commit | `commit_recorded`, `push_blocked` |
| `commit_recorded` | commit SHA exists and matches the approved staged hash | `push_pending`, `push_blocked` |
| `push_pending` | canonical `vcs.push` flow is executing | `push_completed`, `push_blocked` |
| `push_completed` | commit is published and post-push truth is recorded | terminal |
| `push_blocked` | executor or publish path failed closed | `recover` |

`recover` is an explicit action, not an implicit downgrade. It may reopen a
fresh pipeline, restage the same work, rerun guards, or clear a stale pending
request, but it must emit typed receipts and keep the old failed pipeline
artifact for auditability.

### Action Graph

| Step | Typed surface | Owner | Success transition | Fail-closed behavior |
|---|---|---|---|---|
| `stage` | `TypedAction(action_id="vcs.stage")` | governance runtime | `drafted -> staged` | reject if worktree is dirty beyond the selected scope, if another active pipeline exists, or if runtime is not healthy enough to supervise the rest of the flow |
| `guard` | routed guard bundle recorded as `ActionResult(action_id="quality.guard_bundle")` | existing repo guard stack | `staged -> guards_passed` | `guards_failed` on `fail`, `unknown`, or `defer`; no approval request is posted |
| `approve` | `PacketPostRequest(kind="commit_approval")` for both request and operator decision packets | review-channel transport | `guards_passed -> approved` or `rejected` | no packet, stale packet, mismatched target revision, or prose-only approval keeps state at `operator_approval_pending` or forces `recover` |
| `commit` | `TypedAction(action_id="vcs.commit")` executed by governed VCS executor | local repo-owned executor | `approved -> commit_recorded` + emit `PushAuthorizationRecord` bound to the exact commit/check/review proof | `push_blocked` with `commit_failed` reason and `ActionResult` evidence; never tell the operator to run raw `git commit` |
| `push` | existing `TypedAction(action_id="vcs.push")` consuming the current `PushAuthorizationRecord` | existing canonical push path | `commit_recorded -> push_completed` | `push_blocked` with existing push report + `ActionResult`; publication and post-push green remain separate truths |
| `override_push` | typed `override_push` decision packet bound to the current pipeline generation and approved target identity | review-channel transport + existing canonical push path | `push_blocked -> push_pending` by rerunning normal `TypedAction(action_id="vcs.push")` under the recorded override receipt | no packet, expired approval, target drift, or operator rejection keeps `push_blocked` or forces `recover`; never tell the operator to run raw `git push` |
| `recover` | `TypedAction(action_id="vcs.pipeline.recover")` | governance runtime | blocked state -> fresh `drafted` or `staged` pipeline | if recovery cannot prove current repo state, return typed blocked receipt and stop |

### Packet Vocabulary For Remote Approval

Remote approval uses the existing review-channel event path with stricter typed
vocabulary:

1. Runtime approval packet kind
   - `kind="commit_approval"`
2. Approval request packet
   - `from_agent="system"`
   - `to_agent="operator"`
   - request-scoped `requested_action`
   - `policy_hint="operator_approval_required"`
   - `approval_required=true`
   - `trace_id=<pipeline_id>`
   - `target_kind="runtime"`
   - `target_ref="remote_commit_pipeline:<pipeline_id>"`
   - `target_revision=<generation_id or staged_tree_hash>`
   - `pipeline_generation=<generation_id>`
   - `staged_snapshot_hash=<staged_tree_hash>`
   - `guard_results_summary=<typed guard summary>`
3. Operator decision packet
   - `kind="commit_approval"`
   - `from_agent="operator"`
   - `to_agent="system"`
   - `requested_action="approve_commit_pipeline"` or
     `requested_action="reject_commit_pipeline"`
   - `policy_hint="operator_approval_required"`
   - `approval_required=false`
   - same `trace_id`, `target_ref`, `target_revision`,
     `pipeline_generation`, `staged_snapshot_hash`, and
     `guard_results_summary`

Rules:

1. Packet body is explanatory only. Authority comes from packet kind,
   requested-action vocabulary, target ref, target revision, and the resulting
   pipeline transition.
2. `PacketPostRequest` must gain runtime-target support plus typed
   `pipeline_generation`, `staged_snapshot_hash`, and
   `guard_results_summary` fields for these approval packets. Reusing
   plan-only target validation or prose body parsing would be incorrect.
3. The phone/dashboard never flips a boolean directly in `review_state.json`;
   it emits the decision packet and waits for the repo-owned pipeline owner to
   record the state transition.

### Governed Operator Push Override

The current blocked-vs-approved boundary is already meaningful: the governed
pipeline must try `vcs.push`, surface the typed block, and stop. If a human
chooses to override that block, the override should remain inside the same
pipeline instead of falling back to raw `git push`.

Design rule:

1. The override targets one exact pipeline generation and one exact publish
   identity. It is a bounded `override_push` decision, not a blanket bypass.
2. The operator approves the override through the existing typed packet path.
3. The repo-owned executor still performs the canonical
   `TypedAction(action_id="vcs.push")`; the override changes policy state, not
   the executor path.
4. Raw `git push` remains outside the desired control plane and should not be
   normalized as the standard operator-override workflow.

### Push Authorization Boundary

Publication authority is separate from startup/edit authority.

Design rule:

1. `startup-context` may still decide whether editing, relaunch, or repair is
   safe, but it must not be the final proof object for publishing a finished
   artifact.
2. `vcs.commit` emits one typed `PushAuthorizationRecord` bound to the exact
   `commit_sha`, staged snapshot hash, approved target identity, guard/check
   receipt, and review decision packet that authorized publication.
3. `vcs.push` consumes that `PushAuthorizationRecord`; reviewer heartbeat
   freshness may block new editing or relaunch, but it does not invalidate an
   already-authorized unchanged head by itself.
4. `PushAuthorizationRecord` may expire by policy or be replaced by a bounded
   override authorization, but drift in `HEAD`, staged target identity, or
   required check proof must fail closed.

Reserved first fields for that extension on `RemoteCommitPipelineContract`:

- `override_state`: `not_requested|pending|approved|rejected|expired`
- `override_request_packet_id`
- `override_decision_packet_id`
- `override_reason_code`
- `override_scope`
- `override_expires_at_utc`
- `override_approved_target_identity`
- `override_approved_by`
- `override_rationale`

### Executor Boundary

Commit and push must cross the sandbox/keyboard boundary through one governed
executor, not through copied shell instructions in the remote session.

Design rule:

1. Remote clients request `vcs.commit` and `vcs.push` as typed actions.
2. A repo-owned `GovernedVcsExecutor` attached to the existing local service
   lifecycle (`LocalServiceEndpoint`) owns host-capable execution.
3. The executor returns `ActionResult` plus artifact paths and updates
   `RemoteCommitPipelineContract`.
4. If the executor is unavailable, policy-forbidden, or cannot satisfy the
   host capability needed for git mutation, it returns a typed blocked result
   such as `status="fail", reason="executor_unavailable"` and leaves the
   pipeline in a blocked state. It must not fall back to "run this shell
   command locally."

### Doctor/Dashboard Projection

`review-channel --action doctor` should become the primary phone health/readiness
surface for remote sessions. It should project:

1. reviewer lifecycle health
   - `status`
   - `reviewer_freshness`
   - `publish_clear`
   - `publisher_running`
   - `reviewer_supervisor_running`
   - `recommended_command`
2. commit pipeline readiness
   - `pipeline_id`
   - `pipeline_state`
   - `guard_status`
   - `approval_state`
   - `commit_ready`
   - `push_ready`
   - `blocked_reason`
3. staged-work summary
   - `staged_tree_hash`
   - `staged_path_count`
   - `diff_summary`
   - `commit_message_draft`
4. approval and receipt refs
   - `approval_packet_id`
   - `decision_packet_id`
   - `guard_artifact_paths`
   - `push_report_path`
5. final publication truth
   - `commit_sha`
   - `published_remote`
   - `post_push_green`
6. recovery posture
   - `recovery_action_allowed`
   - `approval_expires_at_utc`
   - `override_state`
   - `override_expires_at_utc`
   - `override_approved_by`
   - `generation_id`

### Fail-Closed Rules

1. No pipeline may advance beyond `guards_passed` while
   `ReviewerRuntimeContract.publish_clear` is false.
2. `publisher.running=false` or `reviewer_supervisor.running=false` is a hard
   stop, not a warning, for remote commit/push execution.
3. `ActionResult.status in {fail, unknown, defer}` from the guard bundle is not
   green. Only `pass` may advance to approval.
4. Operator approval is valid only for the exact `pipeline_id` plus
   `target_revision` that was approved. Any diff drift invalidates it.
5. `approved` does not imply commit-ready if the reviewer runtime generation,
   staged tree hash, or guard artifact set changed after approval.
6. No bridge prose section, markdown checkbox, or chat message may count as
   approval, commit receipt, or publish receipt.
7. Raw `git commit` and raw `git push` are forbidden in remote-control mode.
   The only mutating path is the governed executor returning `ActionResult`.
8. `push_completed` requires both remote publication truth and explicit
   post-push result projection. "Remote updated" is not enough.
9. If doctor, status, and pipeline artifacts disagree on generation, surface
   `unknown` and require `recover`; never silently pick one source.
10. Rejected or expired approvals never auto-reopen. Recovery must mint a new
    packet with a new generation-bound request.
11. Any future operator push override must stay generation-bound and target-
    bound, then execute through the normal governed `vcs.push` path. It must
    not become a shell-only bypass around the pipeline owner.

### Migration Plan

1. Land `RemoteCommitPipelineContract` and `CommitIntentState` as read-only
   runtime artifacts plus `review_state.json` / doctor projection fields.
   Phase-0 success criterion: the phone/dashboard can see a truthful blocked
   state without shell spelunking.
2. Extend `PacketPostRequest` targeting for runtime approval packets and make
   the phone/dashboard emit typed `approval_request` / `decision` packets for
   commit pipelines instead of prose approval.
3. Add `vcs.stage` and `vcs.commit` governed actions plus the host-capable
   `GovernedVcsExecutor`, while keeping `vcs.push` as the existing canonical
   push action.
4. Wire automatic guard execution into the pipeline so `stage` immediately
   routes through the existing bundle/risk matrix and records the resulting
   `ActionResult`.
5. Make `review-channel --action doctor` the primary phone health/readiness
   surface and project the new pipeline fields there. `status` remains the
   full snapshot; bridge prose stays compatibility-only.
6. Remove ad hoc remote instructions that tell the operator to run manual
   commits/pushes, and reject raw remote git mutation in the caller-authority
   policy once the typed executor path is proven.

## Execution Checklist

- [x] Freeze the canonical pipeline owner and lifecycle state machine.
- [x] Freeze the action graph for stage, guard, approve, commit, push, and
      recover.
- [x] Freeze the reused-contract list and the minimum new typed records.
- [x] Freeze the packet vocabulary for phone/operator approval.
- [x] Freeze the executor boundary, doctor projection fields, fail-closed
      rules, and migration steps.
- [x] Implement `RemoteCommitPipelineContract` + `CommitIntentState` in runtime
      models, contract rows, and review-state projections.
- [x] Implement runtime-target approval packets and doctor projection updates.
- [x] Implement `vcs.stage`, `vcs.commit`, and `vcs.pipeline.recover` through a
      governed executor path.
- [x] Reuse the existing guarded push flow from the new pipeline and prove end-
      to-end remote approval -> commit -> push without local keyboard input.
- [ ] Freeze the default-push cutover matrix for `devctl push`: governed
      executor path when the active pipeline owns the branch, bounded
      compatibility path while callers migrate, single report-persistence /
      preflight ownership, and explicit retirement conditions for
      `run_push_action()`.
- [ ] Fix missing quality evidence to fail closed as `unknown` / `stale`
      before using automated validation-tier routing as a push or checkpoint
      proof; a missing push/guard report must not project `last_guard_ok=true`.
- [ ] Add a typed `ValidationPlan` / `ValidationReceipt` contract emitted from
      `check-router` or a sibling router command, bound to current worktree or
      staged tree hash, with selected bundle, risk add-ons, escalation reason,
      and checkpoint/push sufficiency flags.
- [ ] Bind `vcs.stage`, `vcs.commit`, and governed `vcs.push` to a fresh
      matching validation receipt for the exact staged tree or approved commit
      target, instead of trusting `guard_profile` strings or actor memory.
- [ ] Add a repo-owned commit gate on top of that validation contract: before
      any remote-control or governed local commit is created, require a fresh
      matching validation receipt for the staged tree, record current proof
      freshness in typed state, and block raw unguarded commit attempts.
- [ ] Treat governed-mutation anti-bypass as the primary architecture guard
      for this lane: `devctl commit`, `devctl push`, managed hooks, and repo
      test helpers must all route through the governed executor plus typed
      receipts. `package_layout` remains only a coarse self-hosting backstop
      and does not count as mutation closure.
- [x] Keep this graph-backed slice narrowly scoped: the accepted work here is
      one query over the existing graph substrate plus a small codeshape
      ingestion pass, not a new graph backend or a generic semantic-engine
      buildout. The first deliverable is the raw-git bypass proof for this
      lane; richer schema-diff or lineage work belongs to the downstream
      owner docs after this substrate is proven.
- [x] Land the first graph-backed mutation-bypass proof for this lane:
      compose `dev/scripts/devctl/context_graph/models.py` with a codeshape
      ingestor over `dev/scripts/devctl/commands/vcs/`,
      `dev/scripts/devctl/commands/governance/install_git_hooks.py`, the
      managed git hooks, and repo test helpers; index every raw git
      subprocess/env-override mutation callsite, walk caller hops back to
      entrypoints, and emit `dev/reports/governance/mutation_bypass_proof.json`.
- [ ] Promote that proof into the permanent anti-bypass guard only after it is
      replay-stable on this repo: `check_mutation_bypass_graph_closure`
      should fail when a raw-git mutation callsite can be reached without
      `GovernedVcsExecutor.execute` in the ancestor chain, and it should keep
      the still-untyped git backlog visible as explicit debt instead of
      hidden helper behavior.
- [ ] Surface commit-gate freshness / last-guard truth through doctor, status,
      and auto-mode so approval-ready state cannot be inferred from stale or
      bypassed guard runs.
- [ ] Make staged-index state first-class in the same startup/push authority
      path: `PushEnforcement`, startup receipts, review-channel status/doctor,
      and review snapshots must distinguish staged vs unstaged paths instead of
      collapsing everything into one dirty-path count. Large staged sets must
      be visible as explicit checkpoint/publish blockers and, when no governed
      pipeline owns them, they must fail closed as unowned staged work rather
      than reading as a generic dirty worktree.
- [ ] Surface validation-plan reasons through doctor/status/dashboard: selected
      bundle, triggering paths, required add-ons, why the tier escalated or did
      not escalate, and whether the proof is enough for checkpoint or push.
- [ ] Policy-gate the remaining mutation bypasses: startup-authority bypass
      env overrides, hook self-mutation, override-push escape semantics, and
      retry paths that remain authorized without a fresh typed decision.
- [ ] Split publication authority from startup/edit gating by emitting one
      typed `PushAuthorizationRecord` after the governed commit is recorded and
      making direct `devctl push` consume that exact-head authorization instead
      of `startup-context` / live reviewer-heartbeat freshness.
- [ ] Add one typed `override_push` extension for operator-approved publish
      exceptions so a blocked governed push can stay inside
      `RemoteCommitPipelineContract`, typed packets, and the canonical
      `vcs.push` executor instead of falling back to raw `git push`.
- [ ] Land `PushAuthorizationRecord` as the canonical publication receipt for
      governed push so `vcs.push` depends on exact head/check/review proof
      instead of rerunning startup/edit gates or reviewer-liveness checks.
- [ ] Absorb the ReviewSnapshot hardening audit's commit/push tranche without
      adding a parallel plan: add the raw `git commit` hook regression lock,
      make override receipts load-bearing for `override_push`, move stronger
      managed-hook integrity and additional hook families through
      `install-git-hooks`, and bind ReviewSnapshot freshness/traceability into
      the same validation and push-authorization proof rather than relying on
      courtesy markdown receipts.
- [ ] Treat hook expansion as a trigger-layer closure, not a second VCS policy:
      pre-commit, post-commit receipt, pre-push, prepare-commit-msg,
      commit-msg, session start, and session stop hooks may call typed
      `devctl` actions, refresh projections, and block bypasses. Validation
      selection, override authorization, publication proof, and path
      resolution must remain in `ValidationPlan`, `ValidationReceipt`,
      `PushAuthorizationRecord`, `override_push`, repo-pack policy, and
      guards.
- [ ] Define the managed git-hook / enforcement model explicitly: which hooks
      are blocking vs receipt-only, how pre-commit vs pre-push
      responsibilities divide, and which exception cases are allowed when raw
      `git commit` / `git push` are forced back through typed `devctl`
      actions.
- [ ] Keep remote-control approval and retry promptless by contract: phone-
      steered or `remote_control` flows may emit typed approval or
      `action_request` packets, but they may not depend on hidden terminal
      prompts or raw shell retry rituals once the governed lane owns the
      branch.
- [ ] Record the mutation backlog boundary for still-untyped git operations
      (`revert`, `rebase`, `reset`, `tag push`, `stash`, `worktree add`, and
      `submodule` flows) so they cannot silently sit outside typed action
      space.
- [ ] Add the layered publish proof program for this lane: post-approval
      publish smoke harness, runtime-death recovery proof, and typed recover
      path evidence must pass before the mutation lane is marked closed.
- [x] Accept snapshot-only trailing commits as a first-class freshness state:
      when the latest commit changes only `dev/audits/REVIEW_SNAPSHOT.md`, the
      freshness guard may bind the generated snapshot to that commit's parent
      code state instead of requiring an impossible self-referential commit SHA.
- [x] Add the raw-git receipt fast path: `review-snapshot --receipt-commit`
      stages and commits only the generated snapshot, while
      `install-git-hooks` installs the pre-commit projection hook, the
      post-commit receipt hook that invokes that typed command with recursion
      disabled, and the managed blocking pre-push hook that forces raw
      publication back through `devctl push --execute` while allowing the
      governed executor's own nested `git push`.
- [x] Keep snapshot receipts and single-agent push receipts aligned:
      `devctl push` accepts a snapshot-only HEAD when its parent matches the
      active `PushAuthorizationRecord`, and it ignores stale detached pipeline
      records in `single_agent` mode instead of letting an old override block a
      newer checkpoint-clean governed push. Active dual-agent and current
      pipeline targets still require exact typed authorization.

## Progress Log

- 2026-04-09: Absorbed the repo-specific graph-backed convergence slice into
  this owner doc instead of leaving it as free prose. The first concrete
  proof here is now explicit: build a codeshape-hop mutation-bypass graph
  over `context_graph` plus the governed VCS surfaces, emit
  `mutation_bypass_proof.json`, and only then promote the no-bypass
  invariant into a permanent guard.
- 2026-04-09: Landed the bounded A1 mutation-bypass proof in repo code. The
  new `context_graph.codeshape` ingestion plus
  `governance_graph.mutation_bypass` report/guard surface now emits
  `dev/reports/governance/mutation_bypass_proof.json`, and the first replay on
  this repo found a real ungoverned path:
  `dev/scripts/devctl/commands/vcs/commit.py::run_commit` could still reach
  `dev/scripts/devctl/runtime/review_snapshot_refresh.py::refresh_and_stage_review_snapshot`
  outside `GovernedVcsExecutor.execute`. The fix removed that direct pre-stage
  refresh from `vcs.commit` so staging now stays owned by the governed phase
  hook. Keep the next graph step ordered behind the current live blocker set:
  after this lane is checkpoint-clean, the next graph-backed work is
  identity-tuple parity in `platform_authority_loop.md`, not a wider graph
  backend or dispatcher port from this doc.
- 2026-04-09: Closed the post-approval staged-tree drift uncovered while
  dogfooding the governed lane locally. `devctl commit` now refreshes and
  stages `REVIEW_SNAPSHOT.md` before the pipeline mints the staged tree hash
  and before `commit_approval` is requested, instead of mutating the index
  inside `vcs.commit` after approval. That keeps the approved target stable:
  remote approval now binds the exact staged tree that will be committed, and
  `staged_snapshot_changed` remains reserved for real out-of-band drift rather
  than self-inflicted snapshot refresh.
- 2026-04-09: Closed the missing raw-push trigger-layer seam in the managed
  hook path. `install-git-hooks` now installs a real blocking `pre-push`
  hook instead of leaving `raw_git_push_guarded` dependent on a hook family
  the installer never wrote. The hook refuses raw `git push` and points the
  caller at `python3 dev/scripts/devctl.py push --execute`, while the
  governed push executor now sets a narrow internal bypass env for its own
  nested `git push` subprocess so the managed hook does not deadlock the
  canonical path. The same tranche also fixes the governed checkpoint
  contradiction: `devctl commit` now allows `vcs.stage` to proceed when
  startup authority is blocking continued editing specifically because a
  checkpoint is required, so the system no longer blocks the governed commit
  that it is telling the operator to cut.
- 2026-04-08: Absorbed the typed-authority convergence Phase-0 map into this
  owner doc instead of leaving it in standalone prose. The governed CLI path
  is now treated as partially landed: `devctl commit` and active-pipeline
  `devctl push` route through the typed executor, but the lane remains open
  until the default-push cutover matrix, blocking hook model, bypass removal,
  validation-plan/receipt, untyped-git backlog boundary, and the post-
  approval publish smoke harness are all closed here.
- 2026-04-08: Closed the bounded Phase-1 enforcement/convergence slice for
  this lane. `devctl commit` no longer uses a raw `git commit` happy path
  once the governed pipeline exists: it now stages from the existing index,
  records the routed guard result on `RemoteCommitPipelineContract`, posts or
  auto-applies typed approval packets depending on operator mode, and executes
  the final commit through `GovernedVcsExecutor`. `devctl push` now routes
  through the same typed executor whenever the active pipeline owns the
  current branch, while direct push stays available for branches with no
  matching pipeline instead of letting unrelated stale pipeline artifacts
  hijack the command. Publication authorization now fails closed on declared
  or effective dual-agent review until an exact typed authorization exists,
  while already-approved exact-head publication can still complete through the
  governed executor after runtime degradation. This closes
  the governed `devctl commit` / `devctl push` path, but it does not yet close
  raw `git commit` / hook bypasses; that trigger-layer closure remains in the
  open hook-expansion work above. Focused and bundled pytest coverage for
  governed commit/push, push authorization, dashboard, review-state, and
  packet queue surfaces passed in this session.
- 2026-04-07: Closed the immediate ReviewSnapshot publication-freshness bug
  exposed by the packet/action-request checkpoint. The pre-commit hook cannot
  embed the final commit SHA because the SHA changes when the file content
  changes, so the guard now accepts a final snapshot-only commit whose
  generated snapshot is bound to the parent code commit. This gives the fast
  planning path a publishable GitHub HEAD: code commit first, generated
  snapshot refresh commit second, then governed push.
- 2026-04-07: Added the repo-owned receipt automation for that two-phase shape:
  `review-snapshot --receipt-commit` refuses non-snapshot dirty state, commits
  only the generated snapshot with hook recursion disabled, and the managed
  post-commit hook calls that command after ordinary raw git commits.
- 2026-04-07: Closed the matching publish-authority follow-up. `devctl push`
  now treats a snapshot-only receipt HEAD as the authorized parent when the
  active `PushAuthorizationRecord` points at that parent, and stale detached
  override pipelines no longer block a clean single-agent push. Dual-agent and
  current-pipeline publication still fail closed on missing, stale, expired,
  guard-failed, or drifted typed authorization.
- 2026-04-07: Routed the ReviewSnapshot architecture hardening audit into this
  lane for commit/push ownership. The accepted items here are raw `git commit`
  hook proof, override receipt enforcement, managed-hook integrity, additional
  git-hook families, and `PushAuthorizationRecord` / ReviewSnapshot
  traceability hardening. Path/default cleanup stays in
  `platform_authority_loop.md`, and the generated
  `dev/audits/REVIEW_SNAPSHOT.md` remains a report projection rather than a
  mutable plan.
- 2026-04-07: Clarified the hook-layer sequencing for this lane: hooks can
  force raw git and session/provider entrypoints back into typed `devctl`
  actions, but hook bodies must not decide validation tiers, publication
  authority, override approval, or ReviewSnapshot paths locally.
- 2026-04-07: Accepted the validation-cadence architecture review for this
  lane. The answer is not "run the whole world on every local edit" and not
  "let the model choose a fast path"; it is to keep enforcement depth while
  compiling proof-tier selection into repo-owned typed artifacts. Code review
  confirmed the current seam: `build_stage_action()` carries scoped paths,
  `guard_profile`, and `work_intake_ref`, and `execute_stage()` enforces dirty
  path scope plus staged tree hash, but the pipeline does not yet require a
  tree-bound validation plan/receipt. `resolve_quality()` also treats a missing
  push report as `last_guard_ok=true`, which is too fail-open for automated
  tier routing. The accepted follow-up is one `ValidationPlan` /
  `ValidationReceipt` contract emitted from routed check policy, bound to the
  worktree/staged-tree identity, consumed by stage/commit/push, and projected
  with reasons in doctor/status/dashboard.
- 2026-04-05: Accepted the operator-override publish review for this lane. The
  current system did the important part correctly: it attempted the governed
  push, surfaced the typed block, and required explicit human intervention
  before publication continued. The remaining architecture gap is narrower
  than "AI ignored governance": human override still escaped the typed control
  plane. The next follow-up here is one generation-bound `override_push`
  decision/receipt path that keeps operator authority inside
  `RemoteCommitPipelineContract` and the existing `vcs.push` executor instead
  of normalizing raw `git push`.
- 2026-04-05: Absorbed the pushed-branch architecture review through
  `b819efa`. The governed stage/commit/push path exists, but the repo still
  allows raw `git commit` to bypass the guard path entirely. That is a
  structural failure, not an operator-discipline problem. The accepted follow-
  up for this lane is one repo-owned commit gate (hook and/or `devctl commit`)
  plus typed guard-freshness projection into doctor, status, and auto-mode so
  the remote-control pipeline can prove whether a commit was created under the
  same guarded authority it claims to use.
- 2026-04-04: Corrected the plan boundary after the governed push/runtime
  slices landed. This file is not design-only anymore: the executor, typed
  push stages, and doctor/status projections already exist, so the remaining
  work here is parity and projection honesty. The active follow-up is to keep
  current-head publication matching and operator-visible receipt rendering
  explicit instead of treating any branch/target-matching `published_remote`
  artifact as proof that the latest local HEAD is already published.
- 2026-04-03: Implemented the first Phase-1 daemon-liveness follow-up for the
  remote commit lane. Live `review-channel --action launch|rollover` now
  starts the persistent ensure-follow publisher from the actual launch router
  instead of hiding daemon ownership inside the terminal helper, the checked-in
  launchd template/wrapper pair under `dev/config/launchd/` maps publisher
  stop reasons into restart-vs-stop exit classes for login-time remote-control
  sessions, and the compact doctor projection now carries publisher/supervisor
  running state plus last heartbeat/stop-reason fields so phone dashboards can
  see daemon readiness from the same reduced surface as `commit_pipeline`.
- 2026-04-03: Implemented the Phase-2 authority cleanup for this lane. The
  reviewer-runtime contract now owns implementer ACK-current plus
  implementation-block state, startup/status push gates consume those typed
  fields instead of bridge-liveness `reviewer_mode` / `claude_ack_current`,
  `bridge_review_accepted()` is typed-only, and governed push recovery now
  compares the reviewer-approved
  `tree-receipt-<timestamp>:<staged_tree_hash>` identity instead of raw
  `HEAD` equality. Focused pytest coverage for startup-context, review-state,
  governed push, governed executor, and platform-contract surfaces passed in
  the same session.
- 2026-04-02: Wrote the Phase-0 design for the typed remote-session
  commit/push pipeline. The design binds remote approval to review-channel
  packets, keeps reviewer runtime health as a hard precondition, keeps
  `vcs.push` as the canonical publish executor, and adds one new runtime owner
  instead of another bridge/script-first path.
- 2026-04-03: Implemented Phase-0 Slice 1 as a read-only runtime/projection
  slice. Added `CommitIntentState` plus the
  `RemoteCommitPipelineContract` contract row/model with required
  `approval_expires_at_utc` and `approved_target_identity` fields, threaded
  `commit_pipeline` through typed `review_state` parsing and projection
  artifacts, added the shared doctor/status projection surface plus
  `review-channel --action doctor`, and kept recovery as an action-only follow-
  up rather than a durable pipeline state. Focused pytest coverage passed for
  platform/runtime/review-channel suites, and the live doctor command now
  projects the default blocked placeholder state plus `commit_pipeline.json`.
- 2026-04-03: Implemented Phase-0 Slice 2 for runtime approval packets.
  `PacketPostRequest` now accepts the dedicated `commit_approval` kind for
  runtime targets, validates and records typed
  `pipeline_generation` / `staged_snapshot_hash` /
  `guard_results_summary` fields, and preserves those fields through the
  existing `review-channel --action post|ack|apply` event lifecycle plus
  `actions.json` / typed review-state parsing. Focused pytest coverage for
  review-channel packet plumbing and runtime parsing passed in the session.
  The remaining repo-wide `check --profile ci` failures are external to this
  slice: live review runtime is currently missing, and startup-authority import-
  index checks cannot be cleared here because this chat session must not stage
  or commit new files.
- 2026-04-03: Implemented the Phase-3/4 surface-convergence slice locally.
  `StartupContext` now derives a bounded `contract_ownership_map` from the
  shared `ContractSpec` registry, startup/status/doctor/commit-pipeline
  projections now stamp one shared `snapshot_id`, two new guards
  (`check_review_surface_consistency.py` and `check_audit_status_sync.py`)
  enforce projection drift plus audit/doc truth, and focused integration tests
  now cover the clean path, rescue path, startup/doctor/bridge-projection
  convergence, and remote approval packets staying generation-bound through the
  governed commit path.

## Session Resume

- 2026-04-08 typed-authority convergence absorption: resume this lane as the
  explicit Phase-0 mutation/publish closure, not as generic VCS cleanup.
  Governed `devctl commit` plus active-pipeline `devctl push` are landed, but
  the phase is not done until the default-push cutover matrix, blocking hook
  / enforcement model, bypass removal, untyped-git backlog boundary, and the
  post-approval publish smoke harness all land here.
- 2026-04-09 governed-mutation-first review:
  treat this lane as the primary blocking architecture guard for the current
  convergence program. Approval issuance or refresh still requires live
  reviewer-runtime / publish-clear readiness, but once an exact approved
  target is recorded, publication must complete through typed `vcs.push` or
  fail as typed `push_blocked` / `recover`, never by normalizing a raw-git
  fallback. Raw-git patterns in tests or helper scripts are architecture debt,
  not an acceptable convenience path.
- 2026-04-09 codeshape-hop intake:
  the next smallest proof in this lane is not broader hook work; it is one
  graph-backed bypass-discovery slice over `dev/scripts/devctl/context_graph/`
  plus the governed VCS, hook, and helper callsites. Land the proof artifact
  first, then promote the no-bypass invariant into the permanent guard once
  the query is stable on this repo.
- Current status: Phases 0 through 4 for the remote commit pipeline are
  implemented locally for this lane, including the governed stage/commit/push
  path, shared surface `snapshot_id`, bounded startup ownership map, the
  focused Phase-4 proof tests, and the remote/local `devctl commit` path now
  lowers through the typed executor by default when the active pipeline owns
  the branch. Raw `git commit` trigger-layer closure is still open, so the
  remaining gaps in this lane are hook/bypass closure plus
  proof/exception closure around the governed path itself:
  `ValidationPlan` / `ValidationReceipt`, typed override publication, and a
  repo-owned remote-lane smoke harness that proves stage -> guard -> approve
  -> commit -> push survives reviewer death or fails closed with typed
  recovery.
- Next action: land the validation-contract slice first. Fix fail-open missing
  quality evidence to `unknown` / `stale`, add `ValidationPlan` /
  `ValidationReceipt`, and bind stage/commit/push to a fresh matching receipt
  projected in doctor/status/dashboard. Immediately after that, add the
  generation-bound `override_push` receipt/approval path and the phone-steered
  remote-lane smoke harness so governed publish exceptions and runtime-death
  recovery still execute through canonical `vcs.push`.
- Context rule: read `dev/active/platform_authority_loop.md`,
  `dev/active/review_channel.md`, and `dev/active/continuous_swarm.md` with
  this plan before changing remote commit/push behavior.

## Audit Evidence

- `python3 dev/scripts/devctl.py startup-context --format summary`
  - 2026-04-02 local run failed closed with
    `action=checkpoint_before_continue`, `reason=runtime_missing`,
    `blockers=startup_authority,runtime_missing`.
- `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
  - 2026-04-02 local run reported `publisher.running=false`,
    `reviewer_supervisor.running=false`,
    `reviewer_runtime.stale_reason=runtime_missing`, and
    `reviewer_runtime.publish_clear=false`.
- `python3 -m pytest dev/scripts/devctl/tests/platform/test_platform_contracts.py dev/scripts/devctl/tests/runtime/test_review_state.py dev/scripts/devctl/tests/review_channel/test_reviewer_wait.py`
  - 2026-04-03 local run passed (`39 passed`).
- `python3 -m pytest dev/scripts/devctl/tests/review_channel/test_review_channel.py -x`
  - 2026-04-03 local run passed (`244 passed`) after fixing two stale
    refactor call sites in `commands/review_channel/status.py`.
- `python3 dev/scripts/devctl.py review-channel --action doctor --terminal none --format json`
  - 2026-04-03 local run succeeded and projected
    `doctor.pipeline_state=push_blocked`,
    `doctor.blocked_reason=pipeline_unavailable`, and
    `projection_paths.commit_pipeline_path=.../dev/reports/review_channel/latest/commit_pipeline.json`
    while the live reviewer runtime still reported
    `attention.status=runtime_missing`.
- `python3 dev/scripts/devctl.py check --profile ci`
  - 2026-04-03 local run now fails only on
    `startup-authority-contract-guard` and `tandem-consistency-guard` because
    the live review runtime is missing and the newly added files are not in the
    git index yet. No stage/commit was performed in this session.
- 2026-04-08 executor-routing and typed-surface validation:
  - `python3 -m pytest dev/scripts/devctl/tests/vcs/test_commit_gate.py dev/scripts/devctl/tests/vcs/test_governed_executor.py dev/scripts/devctl/tests/runtime/test_push_authorization.py dev/scripts/devctl/tests/vcs/test_push.py dev/scripts/devctl/tests/review_channel/test_packet_queue_cleanup.py dev/scripts/devctl/tests/runtime/test_review_state.py dev/scripts/devctl/tests/review_channel/test_pending_packet_guards.py dev/scripts/devctl/tests/test_dashboard.py -q --tb=short`
    passed (`289 passed`).
  - `python3 -m pytest dev/scripts/devctl/tests/runtime/test_operator_mode_fail_closed.py dev/scripts/devctl/tests/runtime/test_control_plane_read_model.py dev/scripts/devctl/tests/runtime/test_startup_context.py dev/scripts/devctl/tests/governance/test_session_resume.py dev/scripts/devctl/tests/test_dashboard.py -q --tb=short`
    passed (`459 passed`).
  - `python3 dev/scripts/checks/check_active_plan_sync.py`
    passed.
  - `python3 dev/scripts/checks/check_review_channel_bridge.py`
    still fails on live repo metadata with
    ``bridge_metadata_errors: `Last Codex poll` is stale``; this remains an
    operator/runtime cadence issue outside the governed VCS executor slice.
- 2026-04-07 reviewer architecture intake for validation cadence:
  - `python3 dev/scripts/devctl.py startup-context --format summary`
    failed closed with `action=checkpoint_before_continue`,
    `reason=dirty_path_budget_exceeded`, and
    `blockers=startup_authority,checkpoint_required,runtime_missing`.
  - `python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md`
    confirmed the same dirty/checkpoint blockers plus `ahead_of_upstream=7`.
  - Code inspection covered
    `dev/scripts/devctl/commands/vcs/governed_executor_actions.py`,
    `dev/scripts/devctl/commands/vcs/governed_executor_phases.py`,
    `dev/scripts/devctl/runtime/remote_commit_pipeline_models.py`,
    `dev/scripts/devctl/runtime/control_plane_resolve.py`, and
    `dev/scripts/devctl/commands/check/router.py`.
- Design inputs read for this plan:
  - `AGENTS.md`
  - `AUDIT_STATUS.md`
  - `.pre-commit-config.yaml`
  - `.github/workflows/pre_commit.yml`
  - `dev/active/PLAN_FORMAT.md`
  - `dev/active/INDEX.md`
  - `dev/active/MASTER_PLAN.md`
  - `dev/active/ai_governance_platform.md`
  - `dev/active/platform_authority_loop.md`
  - `dev/active/review_channel.md`
  - `dev/active/continuous_swarm.md`
  - `dev/scripts/devctl/platform/contracts.py`
  - `dev/scripts/devctl/platform/runtime_identity_contract_rows.py`
  - `dev/scripts/devctl/platform/runtime_state_contract_rows.py`
  - `dev/scripts/devctl/runtime/action_contracts.py`
  - `dev/scripts/devctl/review_channel/packet_contract.py`
  - `dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`
  - `dev/scripts/devctl/review_channel/reviewer_runtime_doctor.py`
