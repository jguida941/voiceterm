# Devctl Autoguide

This guide explains how to run the `devctl` control plane end-to-end with
minimal manual intervention.

Use this with:

- `AGENTS.md` for policy, required bundles, and release SOP
- `dev/guides/DEVCTL_ARCHITECTURE.md` for the plain-language whole-system map,
  stable command language, portable naming-contract guard direction, and
  future `map` command shape
- `dev/guides/DEVELOPMENT.md` for lifecycle flow and verification matrix
- `dev/guides/AGENT_COLLABORATION_SYSTEM.md` for the current Codex/Claude collaboration flowchart and command-stack map
- `dev/scripts/README.md` for full command inventory

## What It Controls

`devctl` is the maintainer entrypoint for:

1. Quality gates (`check`, `docs-check`, `render-surfaces`, `hygiene`, security guards)
   plus host-process/report-retention cleanup (`process-cleanup`,
   `reports-cleanup`)
2. Triage and reporting (`status`, `report`, `data-science`, `triage`, `triage-loop`, `mutation-loop`, `swarm_run`, `autonomy-report`, `phone-status`, `mobile-status`, `controller-action`, `review-channel`, `autonomy-swarm`, `autonomy-benchmark`)
3. Release verification and distribution (`ship`, `release`, `pypi`, `homebrew`)
4. Orchestration guardrails (`orchestrate-status`, `orchestrate-watch`)
5. External federation guardrails (`integrations-sync`, `integrations-import`)
6. Optional MCP read-only adapter (`mcp`) for tool clients that need MCP transport

Naming note: `swarm_run` is the canonical command name for the guarded
plan-scoped swarm pipeline.

## Fast Paths

### Normal push path

```bash
python3 dev/scripts/devctl.py check-router --since-ref origin/develop --execute
# Optional local-only sanity lane while iterating
python3 dev/scripts/devctl.py check --profile fast
# Run this when hygiene warns about stale report growth
python3 dev/scripts/devctl.py reports-cleanup --dry-run
python3 dev/scripts/devctl.py triage --ci --format md
```

`check-router` executes lane commands from
`dev/scripts/devctl/bundle_registry.py` and escalates unknown paths to the
stricter tooling lane.

### Tooling/process/CI path

```bash
python3 dev/scripts/devctl.py render-surfaces --format md
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/devctl.py orchestrate-status --format md
python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 120 --format md
python3 dev/scripts/devctl.py triage --ci --no-cihub --emit-bundle \
  --bundle-dir .cihub/coderabbit --bundle-prefix tooling-pass --format md
```

If the slice changes repo-pack templates or starter-surface policy context,
run `python3 dev/scripts/devctl.py render-surfaces --write --format md` before
`docs-check --strict-tooling` so generated instruction/starter outputs stay in
sync.

### Current review swarm bootstrap

```bash
# Read the live reviewer/coder state first
python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json

# Dry-run first: validate the bridge is active and inspect generated launch scripts
# while auto-repairing stale/missing reviewer heartbeat metadata when that is
# the only blocker.
python3 dev/scripts/devctl.py review-channel --action launch --terminal none --dry-run --format md --refresh-bridge-heartbeat-if-stale

# Read the current bridge-backed review status and refresh latest projections
python3 dev/scripts/devctl.py review-channel --action status --terminal none --format md

# Claude-side bounded wait path after a completed slice; exits on reviewer-owned
# bridge changes or timeout instead of leaving a raw shell sleep loop behind.
python3 dev/scripts/devctl.py review-channel --action implementer-wait --terminal none --format json

# Promote the next repo-owned active-plan item into Current Instruction For Claude
python3 dev/scripts/devctl.py review-channel --action promote --terminal none --format md

# Live launch: open the Codex conductor terminal and the Claude conductor terminal
python3 dev/scripts/devctl.py review-channel --action launch --format md --refresh-bridge-heartbeat-if-stale

# Planned anti-compaction rollover: relaunch fresh conductors before context gets bad
python3 dev/scripts/devctl.py review-channel --action rollover --rollover-threshold-pct 50 --await-ack-seconds 180 --format md

# Canonical tandem post-edit validator once code changes land
python3 dev/scripts/devctl.py tandem-validate --format md

# Honest solo-mode liveness writes when only one agent or tools are active
python3 dev/scripts/devctl.py review-channel --action reviewer-heartbeat --reviewer-mode single_agent --reason local-dev-pass --terminal none --format md

# Reviewer-owned truth update after a real accepted review pass
python3 dev/scripts/devctl.py review-channel --action reviewer-checkpoint --reviewer-mode active_dual_agent --reason review-pass --verdict "- reviewer accepted" --open-findings "- none" --instruction "- continue" --reviewed-scope-item code_audit.md --terminal none --format md
```

Use this only for the current markdown-bridge cycle:

1. It reads `AGENTS.md`, `dev/active/INDEX.md`, `dev/active/MASTER_PLAN.md`,
   `dev/active/review_channel.md`, and `code_audit.md`.
2. Codex is the reviewer conductor for `AGENT-1..AGENT-8`.
3. Claude is the coding conductor for `AGENT-9..AGENT-16`.
4. Terminal.app launch defaults to `--terminal-profile auto-dark`, which picks
   a known dark macOS Terminal profile when one is available.
5. At 50% remaining context or lower, the active conductor should finish the
   current atomic step and run `review-channel --action rollover` instead of
   relying on compaction recovery summaries.
6. `--action status` writes the latest bridge-backed projections under
   `dev/reports/review_channel/latest/` (`review_state.json`, `compact.json`,
   `full.json`, `actions.json`, `latest.md`, `registry/agents.json`).
7. `--action promote` is the typed queue-advance path: it reads the configured
   promotion-plan checklist, refuses to overwrite a still-live instruction, and
   rewrites `Current Instruction For Claude` only when the current slice is
   resolved and findings are clear.
8. `--action rollover` writes a handoff bundle under
   `dev/reports/review_channel/rollovers/`, relaunches fresh conductors, and
   waits up to the configured `--await-ack-seconds` window for visible rollover
   ACK lines in `code_audit.md`.
9. The launcher fails closed if `review_channel.md` no longer marks the
   markdown bridge as the active operating mode.
10. Live `--action launch` sessions now auto-relaunch on clean provider exits so
   a conductor that posts one summary and quits is restarted from repo state in
   the same terminal; non-zero exits still stop fail-closed so real CLI/auth
   failures remain visible.
11. After code edits in the dual-agent lane, `tandem-validate` is the
    canonical validator. Do not replace it with an ad hoc subset unless you
    are debugging one known failing command and then returning to the routed
    validator.
12. In `single_agent` or `tools_only`, keep the same backend/check flow and
    write the honest mode via `reviewer-heartbeat`; do not pretend the bridge
    is stale just because a second live agent is absent.
13. After a real reviewer acceptance pass, use `reviewer-checkpoint` to move
    reviewed hash, verdict, findings, and instruction together instead of
    hand-editing partial reviewer state.
14. Implementer polling is full-section, not fixed-offset: read `Last Codex poll`
    / `Poll Status` first, then reread `Current Verdict`, `Open Findings`, and
    `Current Instruction For Claude` together. If those reviewer-owned sections
    are unchanged after the current bounded work is done, that is a live wait
    state; wait on cadence instead of hammering one unchanged line range.

### Release path

```bash
python3 dev/scripts/devctl.py check --profile release
python3 dev/scripts/devctl.py release-gates --branch master --sha "$(git rev-parse HEAD)" --format md
python3 dev/scripts/devctl.py ship --version X.Y.Z --prepare-release --verify --tag --notes --github --yes
```

`release-gates` enforces same-SHA release policy checks (CodeRabbit triage,
release-preflight, Ralph loop) before publish/tag flow. `ship --verify`
aggregates its independent verify subchecks in parallel and then applies the
same declared substep order when deciding the first failure to surface.

## System Coverage Map

`DEVCTL_AUTOGUIDE.md` is the operator playbook, not the full command reference.
Keep `dev/scripts/README.md` authoritative for the exhaustive inventory and use
this section to keep the whole system in scope when you are steering VoiceTerm,
the PyQt6 console, phone/mobile flows, or agent-only/dev-only modes.

This guide is also protected by `python3 dev/scripts/checks/check_guide_contract_sync.py`
so the core system surfaces below cannot silently disappear from the operator
playbook when the control plane grows.

### Policy, contract, and portability surfaces

Use these when the task is about understanding or exporting the platform, not
only running one local guard bundle:

- `python3 dev/scripts/devctl.py render-surfaces --format md`
- `python3 dev/scripts/devctl.py quality-policy --format md`
- `python3 dev/scripts/devctl.py platform-contracts --format md`
- `python3 dev/scripts/checks/check_platform_contract_closure.py`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py governance-export --format md`
- `python3 dev/scripts/devctl.py governance-bootstrap --help`
- `python3 dev/scripts/devctl.py governance-import-findings --help`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py launcher-check --help`
- `python3 dev/scripts/devctl.py launcher-probes --help`
- `python3 dev/scripts/devctl.py launcher-policy --help`

Use `quality-policy` as the canonical live inventory of the enabled
guards/probes, and use `render-surfaces` right after policy/template changes
to confirm the AI/dev instruction surfaces still describe the same system.
When the shared platform blueprint, runtime contract models, durable
probe/report schema constants, or startup-surface routing text changes, pair
`platform-contracts --format md` with
`python3 dev/scripts/checks/check_platform_contract_closure.py`.

### Review, runtime, and operator loop surfaces

These are the shared backend/operator commands that keep the same review,
queue, and attention signals visible across VoiceTerm, the PyQt6 console,
phone/mobile clients, and agent-only or developer-only flows:

- `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format md`
- `python3 dev/scripts/devctl.py tandem-validate --format md`
- `python3 dev/scripts/devctl.py review-channel --action reviewer-heartbeat --reviewer-mode single_agent --reason local-dev-pass --terminal none --format md`
- `python3 dev/scripts/devctl.py review-channel --action reviewer-checkpoint --reviewer-mode active_dual_agent --reason review-pass --verdict "- reviewer accepted" --open-findings "- none" --instruction "- continue" --reviewed-scope-item code_audit.md --terminal none --format md`
- `python3 dev/scripts/devctl.py swarm_run --help`
- `python3 dev/scripts/devctl.py phone-status --help`
- `python3 dev/scripts/devctl.py mobile-status --help`
- `python3 dev/scripts/devctl.py controller-action --help`
- `python3 dev/scripts/devctl.py orchestrate-status --format md`
- `python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 120 --format md`
- `python3 dev/scripts/devctl.py integrations-sync --status-only --format md`
- `python3 dev/scripts/devctl.py integrations-import --list-profiles --format md`
- `python3 dev/scripts/devctl.py mcp --format md`

### Mutation, compatibility, and publication helpers

These are still part of the same system even when the current task is focused
on review-channel or tandem work:

- `python3 dev/scripts/devctl.py mutants --help`
- `python3 dev/scripts/devctl.py mutation-score --help`
- `python3 dev/scripts/devctl.py compat-matrix --format md`
- `python3 dev/scripts/devctl.py publication-sync --help`
- `python3 dev/scripts/devctl.py release-notes --help`
- `python3 dev/scripts/devctl.py ralph-status --help`

### Queue, device, and recovery helpers

These keep the queue/controller/device side of the platform in scope:

- `python3 dev/scripts/devctl.py loop-packet --help`
- `python3 dev/scripts/devctl.py mobile-app --help`
- `python3 dev/scripts/devctl.py cihub-setup --help`
- `python3 dev/scripts/devctl.py failure-cleanup --help`
- `python3 dev/scripts/devctl.py path-audit --help`
- `python3 dev/scripts/devctl.py path-rewrite --help`

## Check Profile Picker

Use this table when you are not sure which `check` profile to run.

| Profile | Run it when | What it adds |
|---|---|---|
| `ci` | Normal runtime/UI/tooling changes before push | `fmt` + `clippy` + AI guards + full test lane (no release-only gates). |
| `prepush` | Perf/latency/parser/wake-word/memory-sensitive changes | CI profile plus perf smoke and memory loop checks. |
| `ai-guard` | Large refactors or guard-only audit passes | Runs guard scripts without full test/build cycle for fast iteration. |
| `maintainer-lint` | Strict lint review and debt cleanup passes | Clippy hardening lane (`redundant_clone`, closure method-call redundancy, wrap-cast and dead-code drift). |
| `pedantic` | Intentional lint-hardening sweeps, usually after large refactors or as optional pre-release cleanup | Runs advisory `clippy::pedantic`, writes structured artifacts under `dev/reports/check/`, and intentionally stays out of required bundles or release gates. |
| `release` | Release/tag readiness checks on `master` | Adds wake-word coverage, non-blocking mutation-score reminder output, and strict remote release gates. |
| `fast` | Local fast sanity pass while iterating | Alias of `quick`; local-only lane, not a replacement for required pre-push bundles. |
| `quick` | Local fast sanity pass while iterating | Minimal fmt/clippy path without full tests/build. |

Heavy-check placement policy:

1. Keep strict/heavy validation in `prepush` and `release` profiles (plus CI/scheduled workflows).
2. Keep `fast`/`quick` minimal for local iteration only.
3. Never skip release/CI gates by substituting `fast`/`quick`.
4. Run `pedantic` only when you explicitly want broader style/maintainability feedback; do not promote it into required merge/release flow without a deliberate lint-debt reduction project.

### Pedantic advisory flow

Use one deterministic path for pedantic lint review:

1. Run `python3 dev/scripts/devctl.py check --profile pedantic`, or use `python3 dev/scripts/devctl.py report --pedantic --pedantic-refresh --format md` when you want refresh + review in one command.
2. Review the repo-owned summary with `python3 dev/scripts/devctl.py report --pedantic --format md`.
3. Generate an AI-friendly cleanup packet with `python3 dev/scripts/devctl.py triage --pedantic --no-cihub --emit-bundle --format md` (add `--pedantic-refresh` only when you intentionally want triage to regenerate the artifacts inline).
4. Record promote/defer/ignore decisions in `dev/config/clippy/pedantic_policy.json`; do not make per-release ad hoc decisions from raw pedantic output.

For full Rust guard audits with charts and hotspot summaries, use:

`python3 dev/scripts/devctl.py report --rust-audits --with-charts --emit-bundle --format md`

Current AI guard pack in `check`:

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
11. `check_rust_runtime_panic_policy.py`
12. `check_rust_audit_patterns.py`
13. `check_rust_security_footguns.py`

## Guard Failure Playbook

When any AI guard fails, use this order:

1. Run the failing guard directly with `--format md` for focused output.
2. Run `python3 dev/scripts/devctl.py audit-scaffold --force --yes --format md`.
3. Apply fixes from `dev/reports/audits/RUST_AUDIT_FINDINGS.md`.
4. Re-run `python3 dev/scripts/devctl.py check --profile ai-guard`.
5. Re-run your target profile (`ci`, `prepush`, or `release`) before push.

## Report Retention Guard

`hygiene` now warns when managed report artifacts become stale or oversized.

Cleanup flow:

```bash
python3 dev/scripts/devctl.py reports-cleanup --dry-run
python3 dev/scripts/devctl.py reports-cleanup --max-age-days 30 --keep-recent 10 --yes
```

Safety model:

1. cleanup is restricted to managed ephemeral run roots under `dev/reports/**`
2. protected paths (`audits`, `data_science/latest`, queue/controller-state) are never deleted
3. retention keeps the newest `--keep-recent` directories per managed root even if they are old

## Host Process Hygiene

Use this after raw `cargo test` runs, manual test-binary execution, manual
tooling bundles, or any local PTY/runtime/process work that could leak host
processes outside the repo sandbox.

```bash
# preferred AI path for raw cargo/test-binary commands
python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test --bin voiceterm banner::tests -- --nocapture
# raw cargo/test-binary follow-up; includes host-side cleanup by default
python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel
# manual tooling-bundle / pre-handoff host cleanup
python3 dev/scripts/devctl.py process-cleanup --verify --format md
# Read-only fallback / diagnosis
python3 dev/scripts/devctl.py process-audit --strict --format md
# Periodic host watch during long-running leak reproduction
python3 dev/scripts/devctl.py process-watch --cleanup --strict --stop-on-clean --iterations 6 --interval-seconds 15 --format md
```

Safety model:

1. Prefer `guard-run` for AI-operated raw cargo/test-binary commands. It runs the command directly, forbids shell `-c` wrappers, and picks the right post-run hygiene follow-up automatically.
2. `check --profile quick|fast` already calls `process-cleanup --verify` by default after raw cargo/test-binary follow-ups.
3. Cleanup expands matched stale/orphaned roots to their full descendant tree so leaked PTY children, repo-cwd background helpers, and orphaned tooling descendants are not left behind.
4. Recent active processes are reported but skipped by default; `--verify` fails if anything blocking/stale is still alive after cleanup, and it now also fails immediately when a repo-related process is already detached (`PPID=1`) even if it has not aged into the orphan bucket yet.
5. If verify is red only because current local work is still running, rerun `process-cleanup --verify --format md` once that work finishes; repeated passes can catch freshly detached orphans from the same live tree.
6. `process-watch` is the bounded periodic version of the same host audit/cleanup path. Use it when reproducing leaks or when local work is expected to keep shedding host processes for more than one pass; it now exits zero once the host actually becomes clean even if earlier iterations were dirty.

## Optional MCP Adapter

`devctl` remains the canonical enforcement path. MCP is additive, not a
replacement layer.

Use MCP surface only when a client needs MCP protocol transport:

```bash
# Render MCP contract + allowlisted tools/resources
python3 dev/scripts/devctl.py mcp --format md

# Call one read-only tool directly
python3 dev/scripts/devctl.py mcp --tool release_contract_snapshot --format json

# Serve MCP JSON-RPC over stdio (Content-Length framing)
python3 dev/scripts/devctl.py mcp --serve-stdio
```

CLI note:

- `--tool-args-json` is only valid with `--tool`.
- If you are not integrating an MCP-native client, use native `devctl`
  commands directly.

Guardrails:

1. Tool/resource exposure is controlled by `dev/config/mcp_tools_allowlist.json`.
2. Non-read-only tool entries are rejected.
3. Release and cleanup safety remains enforced by `devctl` command contracts.
4. Contract tests lock in `check --profile release`, `ship --verify`, cleanup
   path restrictions, and MCP allowlist behavior.

See `dev/guides/MCP_DEVCTL_ALIGNMENT.md` for extension rules and rationale.

## Always-On Ralph Loop

`CodeRabbit Ralph Loop` runs after `CodeRabbit Triage Bridge` completes on
`develop` and `master` branches.

Runtime controls are repo variables:

- `RALPH_LOOP_MODE`: `always` | `failure-only` | `disabled`
- `RALPH_EXECUTION_MODE`: `report-only` | `plan-then-fix` | `fix-only`
- `RALPH_LOOP_MAX_ATTEMPTS`
- `RALPH_LOOP_POLL_SECONDS`
- `RALPH_LOOP_TIMEOUT_SECONDS`
- `RALPH_LOOP_FIX_COMMAND`
- `RALPH_NOTIFY_MODE`: `summary-only` | `summary-and-comment`
- `RALPH_COMMENT_TARGET`: `auto` | `pr` | `commit`
- `RALPH_COMMENT_PR_NUMBER`: optional explicit PR target
- `TRIAGE_LOOP_ALLOWED_PREFIXES`: optional semicolon-delimited command-prefix override

Default operating mode:

1. `RALPH_LOOP_MODE=always`
2. `RALPH_EXECUTION_MODE=plan-then-fix`

In `plan-then-fix`, the loop reports backlog state first, then runs bounded
fix attempts when a fix command is configured and policy gates pass.

## Local Ralph/Triage Loop

Use `triage-loop` to run the same logic locally or in custom automation.

```bash
python3 dev/scripts/devctl.py triage-loop \
  --repo owner/repo \
  --branch develop \
  --mode plan-then-fix \
  --max-attempts 3 \
  --poll-seconds 20 \
  --timeout-seconds 1800 \
  --source-event workflow_dispatch \
  --notify summary-and-comment \
  --comment-target auto \
  --fix-command "python3 dev/scripts/devctl.py check --profile ci" \
  --emit-bundle \
  --bundle-dir .cihub/coderabbit \
  --bundle-prefix coderabbit-ralph-loop \
  --mp-proposal \
  --format md \
  --output /tmp/coderabbit-ralph-loop.md \
  --json-output /tmp/coderabbit-ralph-loop.json
```

Output includes:

- attempt-by-attempt status (`run_id`, `sha`, `conclusion`, `backlog_count`)
- unresolved medium/high count
- final reason
- source run correlation fields (`source_run_id`, `source_run_sha`, `source_correlation`)
- fix policy block reasons (`fix_block_reason`) when a command is denied
- review escalation comment path when max attempts exhaust unresolved backlog
- optional MASTER_PLAN proposal artifact

Triage fix mode policy gates:

- `AUTONOMY_MODE` must be `operate`
- branch must be allowlisted in `dev/config/control_plane_policy.json`
- fix command must match allowlisted prefixes (or `TRIAGE_LOOP_ALLOWED_PREFIXES`)

## Mutation Ralph Loop

`Mutation Ralph Loop` runs after `Mutation Testing` and can stay report-only by
default until policy gates are promoted.

Runtime controls are repo variables:

- `MUTATION_LOOP_MODE`: `always` | `success-only` | `failure-only` | `disabled`
- `MUTATION_EXECUTION_MODE`: `report-only` | `plan-then-fix` | `fix-only`
- `MUTATION_LOOP_MAX_ATTEMPTS`
- `MUTATION_LOOP_POLL_SECONDS`
- `MUTATION_LOOP_TIMEOUT_SECONDS`
- `MUTATION_LOOP_THRESHOLD`
- `MUTATION_LOOP_FIX_COMMAND`
- `MUTATION_NOTIFY_MODE`: `summary-only` | `summary-and-comment`
- `MUTATION_COMMENT_TARGET`: `auto` | `pr` | `commit`
- `MUTATION_COMMENT_PR_NUMBER`: optional explicit PR target

Local command:

```bash
python3 dev/scripts/devctl.py mutation-loop \
  --repo owner/repo \
  --branch develop \
  --mode report-only \
  --threshold 0.80 \
  --max-attempts 3 \
  --emit-bundle \
  --bundle-dir .cihub/mutation \
  --bundle-prefix mutation-ralph-loop \
  --format md \
  --output /tmp/mutation-ralph-loop.md \
  --json-output /tmp/mutation-ralph-loop.json
```

Fix mode policy gates:

- `AUTONOMY_MODE` must be `operate`
- branch must be allowlisted in `dev/config/control_plane_policy.json`
- fix command must match allowlisted prefixes

## MASTER_PLAN Proposal Loop

`triage-loop --mp-proposal` emits a proposal markdown file. It does not edit
`dev/active/MASTER_PLAN.md` directly.

Recommended automation pattern:

1. loop generates proposal artifact
2. reviewer agent validates evidence + policy gates
3. only allowlisted plan/status sections are updated

## Failure Handling

If the loop is blocked or fails:

1. Read the generated `*.md` and `*.json` artifacts.
2. Run `devctl triage --ci` for a current owner/severity snapshot.
3. Run `devctl audit-scaffold --force --yes --format md` for guard-driven
   remediation scaffolding.
4. Re-run `triage-loop` after fixes land.

## Human-Readable Loop Digest

Use `autonomy-report` when you want one dated operator bundle with readable
markdown, structured JSON, copied source artifacts, and charts.

```bash
python3 dev/scripts/devctl.py autonomy-report \
  --source-root dev/reports/autonomy \
  --library-root dev/reports/autonomy/library \
  --run-label daily-ops \
  --format md \
  --output /tmp/autonomy-report.md \
  --json-output /tmp/autonomy-report.json
```

Output bundle:

1. `dev/reports/autonomy/library/<run-label>/summary.md`
2. `dev/reports/autonomy/library/<run-label>/summary.json`
3. `dev/reports/autonomy/library/<run-label>/sources/*` (copied input artifacts)
4. `dev/reports/autonomy/library/<run-label>/charts/*` (when matplotlib is available)

## Phone Status Read Surface

Use `phone-status` when you want an iPhone/SSH-safe snapshot from autonomy loop
queue artifacts.

```bash
python3 dev/scripts/devctl.py phone-status \
  --phone-json dev/reports/autonomy/queue/phone/latest.json \
  --view compact \
  --emit-projections dev/reports/autonomy/controller_state/latest \
  --format md \
  --output /tmp/phone-status.md \
  --json-output /tmp/phone-status.json
```

Views:

1. `full`: original queue payload
2. `compact`: small operator summary
3. `trace`: terminal trace and draft context
4. `actions`: loop next-actions plus guarded operator shortcuts

## Mobile Status Read Surface

Use `mobile-status` when you want one SSH-safe phone payload that already merges
controller state with current Codex/Claude review state.

```bash
python3 dev/scripts/devctl.py mobile-status \
  --phone-json dev/reports/autonomy/queue/phone/latest.json \
  --review-status-dir dev/reports/review_channel/latest \
  --view compact \
  --emit-projections dev/reports/mobile/latest \
  --format md \
  --output /tmp/mobile-status.md \
  --json-output /tmp/mobile-status.json
```

Views:

1. `full`: merged raw controller + review payload
2. `compact`: one small summary with current instruction, findings, worktree hash, and next actions
3. `alert`: short ping-oriented severity + why summary
4. `actions`: read-safe shortcuts plus guarded controller actions

Projection bundle output (optional):

1. `full.json`
2. `compact.json`
3. `alert.json`
4. `actions.json`
5. `latest.md`

Projection bundle output (optional):

1. `full.json`
2. `compact.json`
3. `trace.ndjson`
4. `actions.json`
5. `latest.md`

## Controller Actions (Guarded)

Use `controller-action` for one bounded operator action at a time.

```bash
python3 dev/scripts/devctl.py controller-action \
  --action dispatch-report-only \
  --repo owner/repo \
  --branch develop \
  --dry-run \
  --format md \
  --output /tmp/controller-action-dispatch.md \
  --json-output /tmp/controller-action-dispatch.json
```

Supported actions:

1. `refresh-status`: read-only projection from phone-status artifacts
2. `dispatch-report-only`: workflow dispatch with `report-only` mode
3. `pause-loop`: request `AUTONOMY_MODE=read-only`
4. `resume-loop`: request `AUTONOMY_MODE=operate`

Guard behavior:

1. Dispatch requires workflow + branch allowlist pass from
   `dev/config/control_plane_policy.json`
2. All write actions are blocked when `AUTONOMY_MODE=off`
3. `--dry-run` shows intended remote command without executing it
4. JSON/markdown reports include a stable `typed_action` contract for agent and
   frontend consumers

## Adaptive Swarm (Metadata + Budget)

Use `autonomy-swarm` to auto-size agent count from multiple signals:

1. change size (`files_changed`, `lines_changed`)
2. problem complexity keywords (`refactor`, `parser`, `security`, etc.)
3. prompt complexity (`prompt_tokens` or estimate from question text)
4. optional token-budget cap (`token_budget / per_agent_token_cost`)

This is usually smarter than using only token count.

```bash
python3 dev/scripts/devctl.py autonomy-swarm \
  --question "large runtime refactor touching parser/security/workspace" \
  --prompt-tokens 48000 \
  --token-budget 120000 \
  --max-agents 20 \
  --parallel-workers 6 \
  --dry-run \
  --no-post-audit \
  --run-label swarm-plan \
  --format md \
  --output /tmp/autonomy-swarm.md \
  --json-output /tmp/autonomy-swarm.json
```

Live one-command execution example (default reviewer + digest behavior):

```bash
python3 dev/scripts/devctl.py autonomy-swarm \
  --agents 10 \
  --question-file dev/active/autonomous_control_plane.md \
  --mode report-only \
  --run-label swarm-live \
  --format md \
  --output /tmp/autonomy-swarm-live.md \
  --json-output /tmp/autonomy-swarm-live.json
```

Execution mode (not plan-only) runs parallel bounded `autonomy-loop` lanes,
reserves one default reviewer slot (`AGENT-REVIEW`) when agent count is >1, and
then automatically runs a post-audit digest (`autonomy-report`) unless you pass
`--no-post-audit` (or `--no-reviewer-lane` to disable reviewer-slot behavior).
For `--mode plan-then-fix` or `--mode fix-only`, pass `--fix-command "<cmd>"`.

1. `dev/reports/autonomy/swarms/<run-label>/summary.md`
2. `dev/reports/autonomy/swarms/<run-label>/summary.json`
3. `dev/reports/autonomy/swarms/<run-label>/AGENT-*/` per-lane artifacts/logs
4. `dev/reports/autonomy/swarms/<run-label>/charts/*`
5. `dev/reports/autonomy/library/<run-label>-digest/summary.md`
6. `dev/reports/autonomy/library/<run-label>-digest/summary.json`

## Swarm Benchmark Matrix (Tradeoff Reports)

Use `autonomy-benchmark` when you want measurable throughput/quality tradeoffs
across different swarm sizes and tactics before running live write-mode flows.

The command enforces active-plan scope first (`plan-doc`, `INDEX`,
`MASTER_PLAN`, `mp-scope`) and then runs a matrix of swarm batches by:

1. swarm counts (`--swarm-counts`, for example `10,15,20,30,40`)
2. tactic profiles (`--tactics`, for example
   `uniform,specialized,research-first,test-first`)

```bash
python3 dev/scripts/devctl.py autonomy-benchmark \
  --plan-doc dev/active/autonomous_control_plane.md \
  --mp-scope MP-338 \
  --swarm-counts 10,15,20,30,40 \
  --tactics uniform,specialized,research-first,test-first \
  --agents 4 \
  --parallel-workers 4 \
  --max-concurrent-swarms 10 \
  --dry-run \
  --format md \
  --output /tmp/autonomy-benchmark.md \
  --json-output /tmp/autonomy-benchmark.json
```

If you use `--mode plan-then-fix` or `--mode fix-only`, you must also pass
`--fix-command "<cmd>"`.

Continuous mode (hands-off checklist progression until failure/limit):

```bash
python3 dev/scripts/devctl.py swarm_run \
  --plan-doc dev/active/autonomous_control_plane.md \
  --mp-scope MP-338 \
  --mode report-only \
  --continuous \
  --continuous-max-cycles 10 \
  --feedback-sizing \
  --feedback-no-signal-rounds 2 \
  --feedback-stall-rounds 2 \
  --run-label swarm-continuous \
  --format md \
  --output /tmp/swarm-run-continuous.md \
  --json-output /tmp/swarm-run-continuous.json
```

Continuous runs stop when one of these happens:

1. no unchecked checklist items remain in the plan doc
2. a cycle fails swarm/governance/plan-update checks
3. `--continuous-max-cycles` is reached

When feedback sizing is enabled, each cycle also records worker triage signals
and adjusts the next cycle's `--agents` target:

1. downshift after repeated no-signal cycles (`--feedback-no-signal-rounds`)
2. downshift after repeated unresolved stalls (`--feedback-stall-rounds`)
3. upshift after repeated improvements (`--feedback-upshift-rounds`)

Output bundle:

1. `dev/reports/autonomy/benchmarks/<run-label>/summary.md`
2. `dev/reports/autonomy/benchmarks/<run-label>/summary.json`
3. `dev/reports/autonomy/benchmarks/<run-label>/scenarios/*/summary.{md,json}`
4. `dev/reports/autonomy/benchmarks/<run-label>/charts/*`

## Guarded Plan-Scoped Swarm Pipeline

Use `swarm_run` when you want one command to execute this full path:

1. load active plan scope (`plan-doc`, `INDEX`, `MASTER_PLAN` token checks)
2. derive next unchecked plan steps into a swarm prompt
3. run `autonomy-swarm` with default reviewer + post-audit behavior
4. run governance checks (`check_active_plan_sync`, `check_multi_agent_sync`,
   `docs-check --strict-tooling`, `orchestrate-status`, `orchestrate-watch`)
5. append run evidence to plan `Progress Log` + `Audit Evidence`

```bash
python3 dev/scripts/devctl.py swarm_run \
  --plan-doc dev/active/autonomous_control_plane.md \
  --mp-scope MP-338 \
  --mode report-only \
  --run-label swarm-guarded \
  --format md \
  --output /tmp/swarm-run.md \
  --json-output /tmp/swarm-run.json
```

If you use `--mode plan-then-fix` or `--mode fix-only`, you must also pass
`--fix-command "<cmd>"`.

Optional workflow-dispatch equivalent:

```bash
gh workflow run autonomy_run.yml \
  -f plan_doc=dev/active/autonomous_control_plane.md \
  -f mp_scope=MP-338 \
  -f branch_base=develop \
  -f mode=report-only \
  -f agents=10 \
  -f dry_run=true
```

Output bundle:

1. `dev/reports/autonomy/runs/<run-label>/summary.md`
2. `dev/reports/autonomy/runs/<run-label>/summary.json`
3. `dev/reports/autonomy/runs/<run-label>/autonomy-swarm.{md,json}`
4. `dev/reports/autonomy/runs/<run-label>/logs/*`

## Guardrail Checklist

Use these checks before promoting release commits:

```bash
python3 dev/scripts/devctl.py check --profile release
CI=1 python3 dev/scripts/checks/check_coderabbit_gate.py --branch master
CI=1 python3 dev/scripts/checks/check_coderabbit_ralph_gate.py --branch master
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/devctl.py hygiene
```

## External Federation (Guarded)

Use these commands when pulling reusable patterns from linked repos:

```bash
python3 dev/scripts/devctl.py integrations-sync --status-only --format md
python3 dev/scripts/devctl.py integrations-import --list-profiles --format md
python3 dev/scripts/devctl.py integrations-import --source code-link-ide --profile iphone-core --format md
python3 dev/scripts/devctl.py integrations-import --source ci-cd-hub --profile workflow-templates --apply --yes --format md
```

Policy rules are enforced from `dev/config/control_plane_policy.json`:

1. source names and profile mappings are allowlisted
2. import destinations must remain under allowlisted destination roots
3. each sync/import action is appended to `dev/reports/integration_import_audit.jsonl`

## Audit Metrics (Scientific Loop)

Use the audit metrics helper to quantify how much the workflow is script-driven
vs AI-assisted vs manual, then track trend lines over time.

```bash
python3 dev/scripts/audits/audit_metrics.py \
  --input dev/reports/audits/baseline-events.jsonl \
  --output-md dev/reports/audits/baseline-metrics.md \
  --output-json dev/reports/audits/baseline-metrics.json \
  --chart-dir dev/reports/audits/charts
```

Baseline schema and KPI definitions live in:

- `dev/audits/METRICS_SCHEMA.md`
- `dev/audits/templates/audit_events_template.jsonl`

`devctl` commands now auto-append one event row to the audit event log (default
`dev/reports/audits/devctl_events.jsonl`). Use env overrides to label cycles
and source type during experiments:

```bash
DEVCTL_AUDIT_CYCLE_ID=baseline-2026-02-24 \
DEVCTL_EXECUTION_SOURCE=ai_assisted \
python3 dev/scripts/devctl.py triage-loop --help
```

## Data Science Snapshots (Always-On)

`devctl` now refreshes a rolling data-science snapshot after every command
unless disabled (`DEVCTL_DATA_SCIENCE_DISABLE=1`).

Manual rebuild:

```bash
python3 dev/scripts/devctl.py data-science --format md
```

Default generated outputs:

- `dev/reports/data_science/latest/summary.md`
- `dev/reports/data_science/latest/summary.json`
- `dev/reports/data_science/latest/charts/*.svg`
- `dev/reports/data_science/history/snapshots.jsonl`

Use source/output overrides for focused experiments:

```bash
python3 dev/scripts/devctl.py data-science \
  --output-root dev/reports/data_science \
  --event-log dev/reports/audits/devctl_events.jsonl \
  --swarm-root dev/reports/autonomy/swarms \
  --benchmark-root dev/reports/autonomy/benchmarks \
  --max-events 20000 \
  --format md
```
