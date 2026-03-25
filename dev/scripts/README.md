# Developer Scripts

Canonical maintainer control plane:

```bash
python3 dev/scripts/devctl.py ...
```

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
For MCP-as-adapter rules and extension policy, see
`dev/guides/MCP_DEVCTL_ALIGNMENT.md`.
For portable-governance exports, benchmark planning, and multi-repo adoption,
see `dev/guides/PORTABLE_CODE_GOVERNANCE.md`.
For the broader standalone-governance product architecture, repo-pack
extraction, and frontend/runtime convergence plan, see
`dev/active/ai_governance_platform.md` and
`dev/guides/AI_GOVERNANCE_PLATFORM.md`.
For plain-language CI lane docs, see `.github/workflows/README.md`.

For workflow routing (what to run for a normal push vs tooling/process changes vs tagged release), follow `AGENTS.md` first.
Canonical command-bundle lists live in `dev/scripts/devctl/bundle_registry.py`.
Check scripts now live under `dev/scripts/checks/`, with centralized path
registry wiring in `dev/scripts/devctl/script_catalog.py`.
Organization is now part of the quality surface too: `check_package_layout.py`
enforces repo-policy layout contracts for flat roots, helper-family namespaces,
docs coverage, crowded-family baseline/adoption reporting, and crowded-directory
freeze/baseline reporting instead of relying on informal cleanup norms.
Compatibility shims inside that layout surface are now governed too: the
portable engine validates shim wrapper shape structurally, repo policy can
require metadata such as `owner`/`reason`/`expiry`/`target`, and crowded-root
reports can exclude approved shims from implementation density while still
surfacing the shim count explicitly.

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
python3 dev/scripts/devctl.py review-channel --action reviewer-heartbeat --reviewer-mode single_agent --reason local-dev-pass --terminal none --format md
python3 dev/scripts/devctl.py review-channel --action reviewer-checkpoint --reviewer-mode active_dual_agent --reason review-pass --checkpoint-payload-file /tmp/reviewer-checkpoint.json --expected-instruction-revision <live-revision> --terminal none --format md
python3 dev/scripts/devctl.py launcher-check
python3 dev/scripts/devctl.py launcher-probes
python3 dev/scripts/devctl.py launcher-policy
python3 dev/scripts/devctl.py render-surfaces --format md
python3 dev/scripts/devctl.py platform-contracts --format md
python3 dev/scripts/checks/check_platform_contract_closure.py
python3 dev/scripts/devctl.py doc-authority --format md
python3 dev/scripts/devctl.py governance-draft --format md
python3 dev/scripts/devctl.py governance-bootstrap --target-repo /tmp/copied-repo --format md
python3 dev/scripts/devctl.py governance-bootstrap --target-repo /tmp/copied-repo --force-starter-policy --format md
python3 dev/scripts/devctl.py governance-export --format md
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/devctl.py process-cleanup --verify --format md
python3 dev/scripts/devctl.py list
```

Use the long command catalog below as the full reference, not the first thing to
read end to end.

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
- Keep stale-bridge repair portable as well: `review-channel` auto-refresh must
  use the bridge snapshot/liveness contract instead of depending only on
  `check_review_channel_bridge.py` freshness output, because that guard
  intentionally relaxes live heartbeat enforcement on `GITHUB_ACTIONS=true`
  runners.
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
- `platform-contracts` exposes the broader shared backend blueprint so another
  repo, frontend, or AI installer can see the intended package/runtime/repo-pack
  boundary without reverse-engineering it from active-plan prose alone.
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
- `tandem-validate` is the repo-owned tandem-session validator: it resolves the
  lane and risk add-ons through `check-router`, runs the routed bundle, then
  re-runs final bridge/tandem guards so Codex/Claude sessions do not rely on a
  hand-maintained checklist.
- `review-channel --action reviewer-heartbeat` is the repo-owned liveness write
  for solo-dev / tools-only / paused tandem states. It updates heartbeat and
  mode metadata without claiming a new reviewed hash.
- `review-channel --action reviewer-checkpoint` is the repo-owned review-truth
  write. Use it only after a real review pass to advance the reviewed hash,
  verdict, findings, instruction, and reviewed scope together. Prefer one
  typed `--checkpoint-payload-file` for AI-generated markdown or any shell-
  sensitive body, use `--verdict-file` / `--open-findings-file` /
  `--instruction-file` only when you intentionally keep the bodies split, and
  reserve inline body flags for short plain strings. In `active_dual_agent`,
  pass the live `--expected-instruction-revision` from `review-channel
  --action status` or `bridge-poll`.
- `review-channel --action implementer-wait` is the repo-owned Claude-side
  wait path. It polls the bridge on the normal cadence, wakes only on
  meaningful reviewer-owned bridge changes, fails closed when the reviewer
  loop is unhealthy, and times out after one hour by default instead of
  lingering as a raw shell `sleep` loop.
- `review-channel --action reviewer-wait` is the symmetric Codex-side wait
  path. It sleeps on cadence too, but wakes on meaningful implementer-side
  changes (`reviewer_worker` hash drift plus typed current-session / ACK
  updates) instead of treating passive supervisor freshness as equivalent to
  new review work. It reads the real `status` report shape (`reviewer_worker`
  + `bridge_liveness`) and loads typed `current_session` state from the
  generated `review_state.json` / `compact.json` projections rather than from
  an invented top-level status payload block.
- `review-channel --action status|ensure|reviewer-heartbeat|reviewer-checkpoint`
  now emit machine-readable `reviewer_worker` state, and
  `review-channel --action ensure --follow` cadence frames also surface a
  `review_needed` signal without claiming semantic review completion.
- `review-channel --action status` also surfaces bridge-backed
  `push_enforcement` state so operator/read-only consumers can see
  `checkpoint_required`, `safe_to_continue_editing`, `recommended_action`,
  and `raw_git_push_guarded` without running `startup-context` separately; the
  same path escalates attention to `checkpoint_required` when the worktree is
  over the continuation budget.
- That same `review-channel --action status` path now emits a typed
  `current_session` block in `dev/reports/review_channel/latest/review_state.json`
  and `compact.json`; prefer it for live current instruction / implementer ACK
  reads while the bridge migration remains in progress. `latest.md` renders
  its current-session section from that typed state.
- For reviewer-owned automation, treat the `status` report shape honestly:
  live read APIs expose `bridge_liveness` plus projection paths, and typed
  `current_session` comes from the generated `review_state.json` projection
  rather than from an invented top-level status payload block.
- `startup-context` is the typed startup packet for AI sessions. It composes
  compact repo governance, reviewer gate, push/checkpoint advice, and a
  bounded `WorkIntakePacket` with typed continuity plus startup-routing
  hints; when `dev/reports/review_channel/latest/review_state.json` is
  available it prefers typed `bridge.review_accepted` state, and it falls
  back to parsing `bridge.md` only while the bridge-backed migration is still
  incomplete. The underlying `ProjectGovernance` payload now also carries a typed
  governed-markdown baseline (`DocPolicy`, `DocRegistry`, parsed
  `PlanRegistry` entries) so startup no longer depends only on hard-coded
  path roots, but `## Session Resume` content is still markdown-only restart
  state. Generated bootstrap surfaces now make `startup-context --format md`
  the mandatory Step 0 gate before edits, validation, or repo-owned launcher
  work, with the slim bootstrap packet remaining the bounded graph companion
  for discovery after that startup receipt is refreshed.
- Repo-governance checkpoint policy may exclude compatibility projections such
  as `bridge.md` from advisory dirty-path budgeting so live review-channel
  compatibility writes do not force false `checkpoint_required` states. Raw
  git state and reviewer-owned status remain canonical for real push/review
  truth.
- Keep the mode model simple: `active_dual_agent` means live reviewer/implementer
  freshness is enforced; `single_agent`, `tools_only`, `paused`, and `offline`
  keep the same backend and checks but suspend stale dual-agent warnings until
  the reviewer resumes active mode.
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
python3 dev/scripts/devctl.py tandem-validate --format md
python3 dev/scripts/devctl.py launcher-check
python3 dev/scripts/devctl.py launcher-probes
python3 dev/scripts/devctl.py launcher-policy
python3 dev/scripts/devctl.py render-surfaces --format md
python3 dev/scripts/devctl.py render-surfaces --write --format md
python3 dev/scripts/devctl.py platform-contracts --format md
python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md
python3 dev/scripts/devctl.py context-graph --query '<term>' --format md
python3 dev/scripts/devctl.py context-graph --query '<term>' --save-snapshot --format md
python3 dev/scripts/devctl.py context-graph --mode diff --from previous --to latest --format md
python3 dev/scripts/devctl.py context-graph --format mermaid
python3 dev/scripts/checks/check_platform_contract_closure.py
python3 dev/scripts/devctl.py doc-authority --format json
python3 dev/scripts/devctl.py governance-bootstrap --target-repo ../ci-cd-hub-copy --format md
python3 dev/scripts/devctl.py governance-export --export-base-dir ../portable_snapshot_exports --format md
python3 dev/scripts/devctl.py check --profile ci --quality-policy dev/config/devctl_repo_policy.json
python3 dev/scripts/devctl.py check --profile ci --quality-policy /tmp/pilot-policy.json --adoption-scan
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
# Optional: disable automatic orphaned/stale test-process cleanup sweep
python3 dev/scripts/devctl.py check --profile ci --no-process-sweep-cleanup
# Optional: path-aware pre-push routing from changed files
python3 dev/scripts/devctl.py check-router --since-ref origin/develop --execute
python3 dev/scripts/devctl.py check-router --since-ref origin/develop --quality-policy /tmp/pilot-policy.json
# Canonical guarded branch-push validation path (non-mutating by default)
python3 dev/scripts/devctl.py push
# Execute the real short-lived branch push plus the configured post-push bundle
python3 dev/scripts/devctl.py push --execute

# Docs + governance checks
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/devctl.py docs-check --strict-tooling --quality-policy /tmp/pilot-policy.json
python3 dev/scripts/devctl.py hygiene
# Optional: fail when hygiene emits warnings
python3 dev/scripts/devctl.py hygiene --strict-warnings
# Optional: keep mutation-badge freshness visible without failing strict hygiene
python3 dev/scripts/devctl.py hygiene --strict-warnings --ignore-warning-source mutation_badge
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
# CodeRabbit release gates (strict local verification mode).
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
python3 dev/scripts/checks/check_code_shape.py
python3 dev/scripts/checks/check_duplicate_types.py
python3 dev/scripts/checks/check_structural_complexity.py
python3 dev/scripts/checks/check_workflow_shell_hygiene.py
python3 dev/scripts/checks/check_workflow_action_pinning.py
python3 dev/scripts/checks/check_guard_enforcement_inventory.py
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
# `docs-check --strict-tooling` enforces ENGINEERING_EVOLUTION updates for tooling/process/CI shifts and runs active-plan + multi-agent sync gates, markdown metadata-header style checks, workflow-shell hygiene checks, bundle/workflow parity checks, plus stale-path audit (using `dev/scripts/devctl/script_catalog.py` as canonical check-script path registry). Use `path-rewrite` to auto-fix stale path references.
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
# Policy-gated controller actions (safe subset: refresh, report-only dispatch, pause/resume)
python3 dev/scripts/devctl.py controller-action --action refresh-status --view compact --format md --output /tmp/controller-action-refresh.md
python3 dev/scripts/devctl.py controller-action --action dispatch-report-only --repo owner/repo --branch develop --dry-run --format md --output /tmp/controller-action-dispatch.md
python3 dev/scripts/devctl.py controller-action --action pause-loop --repo owner/repo --mode-file dev/reports/autonomy/queue/phone/controller_mode.json --dry-run --format md --output /tmp/controller-action-pause.md
python3 dev/scripts/devctl.py controller-action --action resume-loop --repo owner/repo --mode-file dev/reports/autonomy/queue/phone/controller_mode.json --dry-run --format md --output /tmp/controller-action-resume.md
# Bridge-gated review swarm bootstrap (dry-run first, then live conductor launch)
python3 dev/scripts/devctl.py review-channel --action launch --terminal none --dry-run --format md --output /tmp/review-channel-launch.md
python3 dev/scripts/devctl.py review-channel --action launch --approval-mode balanced --terminal none --dry-run --format md --output /tmp/review-channel-launch-balanced.md
python3 dev/scripts/devctl.py review-channel --action launch --approval-mode trusted --terminal none --dry-run --format md --output /tmp/review-channel-launch-trusted.md
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
needs more repo context. Before edits, validation, or repo-owned launcher
work, run `python3 dev/scripts/devctl.py startup-context --format md` first
and treat a non-zero exit as a hard stop to checkpoint or repair the repo
state. After that Step 0 receipt is fresh, use the slim bootstrap packet for
additional discovery and targeted `--query` reads.
Current graph routing now includes first-pass `guards` and `scoped_by`
edges, so targeted file/path queries can surface active guard coverage and
plan-scope ownership from the generated graph before escalating to fuller
startup-context reads. Non-guard queries now suppress generic guard-edge
fan-out, and `scoped_by` ownership can come from docs-policy rules or bounded
derived plan-to-directory matches instead of raw substring adjacency alone.
Bootstrap mode also now writes a typed
`ContextGraphSnapshot` artifact under `dev/reports/graph_snapshots/`; use
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
| `dev/scripts/checks/check_agents_contract.py` | AGENTS contract gate | Verifies required AGENTS SOP sections, bundles, and routing rows are present. |
| `dev/scripts/checks/check_agents_bundle_render.py` | AGENTS bundle render gate | Verifies AGENTS rendered command-bundle section matches canonical output from `dev/scripts/devctl/bundle_registry.py`; supports `--write` to regenerate the section. |
| `dev/scripts/checks/check_bootstrap.py` | Check bootstrap helper | Shared import-resolution and UTC runtime-error/timestamp helpers used by standalone guard scripts; not invoked directly by bundles. |
| `dev/scripts/checks/check_active_plan_sync.py` | Active-plan sync gate | Verifies `dev/active/INDEX.md` registry coverage, tracker authority, mirrored-spec phase headings, cross-doc links, execution-plan metadata/marker/section parity (including `Session Resume`), `MP-*` scope parity between index/spec docs and `MASTER_PLAN`, archive-vs-active doc boundaries for the required active set, and `MASTER_PLAN` Status Snapshot release metadata freshness. |
| `dev/scripts/checks/check_architecture_surface_sync.py` | Architecture-surface sync guard | Scans newly added files and fails when active-plan docs, new check scripts, new `devctl` commands, new `app/**` surfaces, or new workflow files are not wired into the repo's owning authority docs/bundles/workflow docs. Supports `--since-ref`/`--head-ref` for branch diffs and `--paths` for targeted local verification. |
| `dev/scripts/checks/check_guide_contract_sync.py` | Durable guide contract sync guard | Verifies repo-policy-owned durable guide/playbook coverage contracts (for example `dev/guides/DEVCTL_AUTOGUIDE.md`) so major control-plane surfaces cannot silently fall out of the operator docs while code keeps moving. |
| `dev/scripts/checks/check_instruction_surface_sync.py` | Generated-surface sync guard | Verifies policy-owned instruction/starter surfaces still match the current repo-pack templates/context without writing files, so `render-surfaces --write` stays paired with a real enforcement lane in tooling/release validation. |
| `dev/scripts/checks/check_platform_layer_boundaries.py` | Platform-layer boundary guard | Stable shim entrypoint for the architecture-boundary guard that blocks forbidden imports across reusable-backend, surface, and mobile/frontend layers while the implementation lives under `dev/scripts/checks/architecture_boundary/`. |
| `dev/scripts/checks/check_multi_agent_sync.py` | Multi-agent coordination gate | Verifies `MASTER_PLAN` board parity with the merged markdown-swarm tables in `dev/active/review_channel.md` for dynamic `AGENT-<N>` lanes (lane/MP/worktree/branch alignment, instruction/ack protocol checks, lane-lock + MP-collision handoff checks, status/date formatting, ledger traceability, and required end-of-cycle signoff when all agent lanes are merged). |
| `dev/scripts/checks/check_review_channel_bridge.py` | Markdown-bridge contract gate | Verifies the active `bridge.md` bridge exposes the required bootstrap sections/markers, tracked-file safety, and current poll/hash heartbeat metadata while `dev/active/review_channel.md` still declares the transitional markdown bridge active. |
| `dev/scripts/checks/check_tandem_consistency.py` | Tandem role-profile consistency gate | Verifies tandem review/code loop consistency across peer-liveness, event-reducer, status-projection, launch, prompt, and handoff modules. Checks prefer typed `review_state.json` authority (`current_session`, `bridge` block) when available; bridge-text fallback is used only for `reviewed_hash_honesty`, `plan_alignment`, and `launch_truth` where no typed equivalent exists yet. |
| `dev/scripts/checks/check_release_version_parity.py` | Release version parity gate | Ensures Cargo, PyPI, and macOS app plist versions match before tagging/publishing. |
| `dev/scripts/checks/check_coderabbit_gate.py` | Workflow release gate helper | Verifies the latest run for a target workflow/branch+commit SHA is successful before release/publish steps proceed (`--workflow` override + optional `--wait-seconds`/`--poll-seconds` for asynchronous gate arrival). |
| `dev/scripts/checks/check_coderabbit_ralph_gate.py` | CodeRabbit Ralph release gate | Verifies the latest `CodeRabbit Ralph Loop` run is successful for a target branch+commit SHA before release/publish steps proceed. |
| `dev/scripts/checks/run_coderabbit_ralph_loop.py` | CodeRabbit remediation loop | Runs a bounded retry loop over CodeRabbit medium/high backlog artifacts and optional auto-fix command hooks. |
| `dev/scripts/checks/mutation_ralph_loop_core.py` | Mutation remediation loop core helpers | Shared run/artifact/score/hotspot logic used by `devctl mutation-loop`. |
| `dev/scripts/checks/check_cli_flags_parity.py` | CLI docs/schema parity gate | Compares clap long flags in Rust schema files against `guides/CLI_FLAGS.md`. |
| `dev/scripts/checks/check_markdown_metadata_header.py` | Markdown metadata header style gate | Normalizes `Status`/`Last updated`/`Owner` doc metadata to one canonical line style. |
| `dev/scripts/checks/check_screenshot_integrity.py` | Screenshot docs integrity gate | Validates markdown image references and reports stale screenshot age. |
| `dev/scripts/checks/check_publication_sync.py` | External publication drift gate | Compares tracked papers/sites against watched repo source paths and fails when synced public artifacts lag behind the recorded source baseline. |
| `dev/scripts/checks/check_code_shape.py` | Source-shape drift guard | Blocks new Rust/Python God-file growth using language-level soft/hard limits (Rust: 900/1400, Python: 350/650), path-level hotspot budgets, **function-length guardrails** (Rust: 100 lines, Python: 150 lines) with expiry-tracked exceptions for existing oversized functions, stale loose path-override detection, override-cap ratcheting (untouched legacy over-cap overrides stay visible as warnings; touched, newly introduced, or worsened over-cap overrides fail), touched-file mixed-concern ratcheting for Python files with 3+ independent function clusters, repo-policy-owned namespace/layout rules, and audit-first remediation guidance (modularize/consolidate before merge, with Python/Rust best-practice links). |
| `dev/scripts/checks/check_package_layout.py` | Package-layout organization guard | Enforces repo-policy placement rules for flat roots, crowded namespace families, docs sync, crowded-directory freeze/baseline reporting, and portable compatibility-shim governance so self-hosting repo structure stays legible and external adopters can see layout debt early without treating thin wrapper seams as invisible or ad hoc. |
| `dev/scripts/checks/check_duplicate_types.py` | Duplicate Rust type-name guard | Detects duplicate `struct`/`enum` names across Rust files (with explicit allowlist for known transitional duplicates) so new cross-file type-shadowing does not slip in. |
| `dev/scripts/checks/check_structural_complexity.py` | Structural-complexity guard | Flags Rust functions whose structural complexity score (branch points + nesting) exceeds policy limits, with expiry-bound exceptions for active MP-346 transition hotspots. |
| `dev/scripts/checks/check_workflow_shell_hygiene.py` | Workflow-shell anti-pattern guard | Blocks fragile inline shell patterns in workflow run blocks (single-match find/head chains, inline Python snippets) across `.yml`/`.yaml` workflows; supports auditable line-level suppressions via `workflow-shell-hygiene: allow=inline-python-c` (or `allow=all`) when a justified exception is required. |
| `dev/scripts/checks/check_workflow_action_pinning.py` | Workflow action pinning guard | Fails when third-party `uses:` refs are not pinned to full 40-character SHAs (with optional auditable suppressions for justified exceptions). |
| `dev/scripts/checks/check_guard_enforcement_inventory.py` | Guard enforcement inventory gate | Verifies cataloged quality scripts still have a real enforcement lane through bundle/workflow invocation or an explicit helper/manual/advisory exemption. The guard recognizes the current `docs-check --strict-tooling` family, the AI-guard family owned by `devctl check`, and the review-probe family owned by `devctl check` / `devctl probe-report`, and keeps manual-only/report-only surfaces explicit instead of letting catalog drift silently. |
| `dev/scripts/checks/check_governance_closure.py` | Governance self-closure guard | Verifies the governance stack proves itself by requiring registered guards/probes to have tests, requiring default guards to appear in CI workflows, and checking CI workflows for timeout coverage. Supports `--format` and `--output`. |
| `dev/scripts/checks/check_bundle_workflow_parity.py` | Bundle/workflow parity guard | Verifies registry commands for `bundle.tooling` and `bundle.release` remain present in the owning CI workflows so policy bundles and workflow execution do not silently drift. |
| `dev/scripts/checks/check_bundle_registry_dry.py` | Bundle-registry DRY guard | Verifies canonical bundle definitions in `bundle_registry.py` are composed through shared command groups instead of duplicated command lists. |
| `dev/scripts/checks/check_ide_provider_isolation.py` | IDE/provider coupling audit | Blocks mixed host/provider executable statements outside explicit policy-owner allowlists (default blocking mode; optional `--report-only`). Scanner ignores import blocks and `#[cfg(test)]` sections so enforcement stays runtime-focused. |
| `dev/scripts/checks/check_compat_matrix.py` | Compatibility matrix schema gate | Validates `dev/config/compat/ide_provider_matrix.yaml` required hosts/providers, per-cell coverage, duplicate/missing entries, and provider IPC-mode policy labels. |
| `dev/scripts/checks/compat_matrix_smoke.py` | Compatibility matrix runtime smoke gate | Cross-checks matrix coverage against runtime host/provider enums (`runtime_compat`) plus IPC provider enum (`ipc/protocol`) and enforces explicit non-IPC labeling for runtime-visible non-IPC providers. |
| `dev/scripts/checks/check_naming_consistency.py` | Host/provider naming consistency gate | Verifies host/provider IDs and provider-token labels stay aligned across runtime enums/registry, compatibility-matrix IDs, and tooling-owned token contracts (matrix policy, smoke policy map, and isolation scanner token regex). |
| `dev/scripts/checks/check_repo_url_parity.py` | Repository URL parity guard | Verifies canonical repository URL consistency across Cargo/PyPI/docs metadata surfaces. |
| `dev/scripts/checks/check_python_broad_except.py` | Python broad-except rationale guard | Fails when newly added `except Exception` / `except BaseException` handlers appear in repo-owned Python tooling or Operator Console code without a nearby `broad-except: allow reason=...` comment. The guard is diff-aware by default, excludes tests, and supports `--paths` for targeted local verification. |
| `dev/scripts/checks/check_python_subprocess_policy.py` | Python subprocess policy guard | Fails when repo-owned Python tooling or Operator Console code calls `subprocess.run(...)` without an explicit `check=` keyword. Tests are excluded so intentional fixture/process assertions can stay flexible, and `--since-ref/--head-ref` support lets AI-guard/post-push lanes scope the scan to changed files. |
| `dev/scripts/checks/check_command_source_validation.py` | Command-source validation guard | Fails when Python command construction uses `shlex.split(...)` on CLI/env/config input, forwards raw `sys.argv` into subprocess argv, or threads env-controlled command values into command runners without a validator helper. The initial rollout is intentionally focused on the selectable launcher lane (`scripts/` + `pypi/src`) so the rule can stay low-noise before any broader promotion. |
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
| `dev/scripts/checks/check_platform_contract_closure.py` | Platform contract-closure guard | Fails when the current executable platform contract families drift across the `platform-contracts` blueprint, shared runtime dataclass models, durable artifact schema metadata, or startup-surface contract-routing tokens. The first bounded scope covers `TypedAction`, `RunRecord`, `ArtifactStore`, `ControlState`, `ReviewState`, `Finding`, `DecisionPacket`, `ProbeReport`, `ReviewPacket`, `ReviewTargets`, `FileTopology`, and `ProbeAllowlist`; the next closure expansion is live AI-consumer authority integrity so field-route proofs, single-authority artifact reads, and structured routing keys do not silently fall back to dead or prose-only seams. Supports `--format`. |
| `dev/scripts/checks/check_startup_authority_contract.py` | Startup-authority contract guard | Validates the live `ProjectGovernance` bootstrap payload by requiring the core startup authority files, non-empty repo identity, plan-registry roots/order, fail-closed checkpoint-budget truth, working-tree-to-index Python import atomicity, and committed-tree (`HEAD`)-to-`HEAD` importer coherence; fresh repos without a first commit skip the committed-tree layer until `HEAD` exists. Supports `--format`. |
| `dev/scripts/checks/check_mobile_relay_protocol.py` | Mobile relay projection contract guard | Fails when the shared mobile relay payload shape drifts across the Rust/controller emitters, Python projection tooling, and iOS consumer contract. Supports `--since-ref/--head-ref` and `--format`. |
| `dev/scripts/checks/check_daemon_state_parity.py` | Daemon-state parity guard | Validates the Rust daemon lifecycle/state seam against the Python runtime models by checking lifecycle-event coverage plus required daemon-state and agent-info fields. Supports `--format`. |
| `dev/scripts/checks/check_nesting_depth.py` | Nesting-depth non-regression guard | Fails when changed Rust or Python files introduce functions with deeply nested control flow (Python: >4 indent levels, Rust: >5 brace-depth levels). Uses the same function scanners as `check_code_shape.py`; tests are excluded; supports `--since-ref/--head-ref` and `--format`. |
| `dev/scripts/checks/check_parameter_count.py` | Parameter-count non-regression guard | Fails when changed Rust or Python files introduce functions with excessive parameter counts (Python: >6 params, Rust: >7 params, excluding `self`/`cls`/`&self`/`&mut self`). Tests are excluded; `#[cfg(test)]` blocks are stripped for Rust scans; supports `--since-ref/--head-ref` and `--format`. |
| `dev/scripts/checks/check_python_dict_schema.py` | Python dict-schema non-regression guard | Fails when changed Python files grow large untyped dict literals (>= 6 string keys suggesting a missing dataclass) or weak `dict[str, Any]` type aliases. Tests are excluded; supports `--since-ref/--head-ref` and `--format`. |
| `dev/scripts/checks/check_python_global_mutable.py` | Python default-state trap non-regression guard | Fails when changed Python files introduce new `global` statements, mutable default arguments (`list`, `dict`, `set`, `defaultdict`, `deque`), function-call default arguments, or dataclass fields that evaluate mutable/call defaults eagerly instead of using `field(default_factory=...)`. Tests are excluded; supports `--since-ref/--head-ref` and `--format`. |
| `dev/scripts/checks/check_python_design_complexity.py` | Python design-complexity non-regression guard | Fails when changed Python files add functions whose branch count or return-statement count crosses the repo-policy thresholds (portable defaults: branches >30, returns >10 so another repo can ratchet from a conservative baseline), or when already-over-limit functions become even more branchy/return-heavy. Tests are excluded; supports `--since-ref/--head-ref` and `--format`. |
| `dev/scripts/checks/check_python_cyclic_imports.py` | Python cyclic-import non-regression guard | Fails when changed Python files introduce new top-level local import cycles inside the configured Python guard roots. Cycle allowlists are repo-policy owned so another repo can adopt the same engine without editing script code. Tests are excluded; supports `--since-ref/--head-ref` and `--format`. |
| `dev/scripts/checks/check_python_suppression_debt.py` | Python suppression-debt non-regression guard | Fails when changed Python files add more lint/type suppression comments than the base version (`# noqa`, `# type: ignore`, `# pylint: disable`, `# pyright: ignore`). Uses tokenized comment scanning so string literals and prose examples do not count; supports `--since-ref/--head-ref` and `--format`. |
| `dev/scripts/checks/check_structural_similarity.py` | Structural-similarity non-regression guard | Fails when changed Rust or Python files introduce cross-file function pairs with identical control-flow shape but different variable names (copy-paste-and-rename detection). Unlike `check_function_duplication` which catches identical normalized bodies, this guard normalizes identifiers and literals to detect structurally equivalent functions (>= 8 body lines). Tests are excluded; supports `--since-ref/--head-ref` and `--format`. |

## Devctl Command Set

Machine-first output note:

- JSON-canonical report/packet surfaces (`governance-*`, `platform-contracts`,
  `probe-report`, `data-science`, `loop-packet`) now treat stdout as a compact
  control channel when you run `--format json --output <path>`: the full
  compact JSON artifact is written to the file, while stdout emits only a
  compact JSON receipt with artifact metadata such as path/hash/size/token
  estimate. This keeps agent loops small and lets automation decide whether it
  needs to reread the artifact.

- `check`: fmt/clippy/tests/build profiles (`ci`, `prepush`, `release`, `maintainer-lint`, `pedantic`, `quick`, `fast`, `ai-guard`)
  - Runs setup gates (`fmt`, `clippy`, AI guard scripts) and test/build phases in parallel batches by default.
  - Tune parallelism with `--parallel-workers <n>` or force sequential execution with `--no-parallel`.
  - Runs an automatic orphaned/stale repo-related process sweep before/after checks (VoiceTerm PTY/test trees, repo-runtime cargo/target trees, repo-tooling wrappers, detached `PPID=1`, plus stale active runners aged `>=600s`).
  - Disable only when needed with `--no-process-sweep-cleanup`.
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
  - The six-row `AGENTS.md` router table and the generated `CLAUDE.md`
    task-router quick map render from the same typed authority in
    `dev/scripts/devctl/governance/task_router_contract.py`.
  - `--execute` runs the routed bundle commands plus add-ons from `bundle_registry.py`; unknown paths escalate to the stricter tooling lane.
- `mutants`: mutation test helper wrapper
- `mutation-score`: threshold/freshness checker for outcomes (strict by default; use `--report-only` for non-blocking reminders)
- `docs-check`: docs coverage + tooling/deprecated-command policy guard (`--strict-tooling` also runs active-plan sync + multi-agent sync + markdown metadata-header + workflow-shell hygiene + guide-contract sync + bundle/workflow parity + stale-path audit)
  - Canonical doc sets and deprecated-reference patterns resolve from
    `repo_governance.docs_check` in the active repo policy; use
    `--quality-policy <path>` to point the same command at another repo's
    governance contract.
- `hygiene`: archive/ADR/scripts governance checks plus orphaned/stale repo-related host-process detection (matched `cargo test --bin voiceterm`, `target/debug/deps/voiceterm-*`, stress sessions, repo-runtime cargo/target trees, orphaned repo-tooling wrappers that execute `dev/scripts/**`, repo-owned review-channel conductor trees, and repo-cwd background helpers such as `python3 -m unittest`, direct `bash dev/scripts/...` wrappers, or `qemu/node/make` descendants that outlive their repo-owned parent; stale active threshold: `>=600s`; attached supervised review-channel conductors remain visible but are no longer promoted into stale failures unless they detach/background); ADR checks include numbering-gap governance (`Retired ADR IDs`, `Reserved ADR IDs`), `next:` pointer validation, active backlog parity checks between `MASTER_PLAN` and `autonomous_control_plane`, and stale ADR reference-pattern detection (hard-coded ADR counts/ranges) in long-lived governance docs; includes automatic report-retention drift warnings for stale `dev/reports/**` run artifacts and tracked external-publication drift warnings when watched repo paths outpace synced papers/sites; `--strict-warnings` promotes warnings to failures (used by CI governance/release lanes), while `--ignore-warning-source mutation_badge` keeps stale mutation-badge freshness visible without failing non-release tooling lanes; optional `--fix` removes detected `dev/scripts/**/__pycache__` directories and re-audits scripts hygiene
- `process-cleanup`: host-side cleanup for orphaned/stale repo-related process trees; expands cleanup roots to full descendant trees so leaked PTY children, repo-cwd background helpers, and orphaned tooling descendants are reaped with their parent wrappers when possible, skips recent active processes by default, and `--verify` reruns strict host audit after cleanup
- `process-audit`: read-only host-side Activity Monitor equivalent for repo-related process trees; reports matched roots plus descendants, includes repo-cwd runtime/tooling helpers that would otherwise look generic in Activity Monitor, fails fast when `ps` access is unavailable, preserves attached supervised review-channel conductors as visible non-blocking rows, and `--strict` turns leftover runtime/test trees or stale/orphaned repo-related helpers into a blocking failure before handoff
- `publication-sync`: tracked external publication report/record surface that compares watched repo paths against the last synced source commit for papers/sites and records a new baseline after external publish
- `push`: policy-driven guarded push wrapper for the current branch; resolves branch/remote rules from `repo_governance.push`, runs the configured preflight path, defaults to non-mutating validation, and uses the configured post-push bundle after `--execute`
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
- `governance-review`: adjudicated finding ledger for hard-guard/probe outcomes; records reviewed findings plus their systemic disposition into `dev/reports/governance/finding_reviews.jsonl`, writes refreshed `review_summary.{md,json}` artifacts under `dev/reports/governance/latest/`, and gives the repo a durable scoreboard for false-positive rate, fixed findings, deferred debt, architectural absorption choices, and optional probe-guidance adoption (`guidance_id` / `guidance_followed`)
- Shared context-escalation packets now also consume bounded recent
  `review_summary.json` history plus the latest quality-feedback
  recommendations so Ralph/autonomy/review-channel prompt families can read
  fix history and repo-quality tuning hints without loading those artifacts
  separately. The same packet family now also carries bounded watchdog-episode
  digests, command-reliability lines from `data_science summary.json`, and
  decision constraints derived from matched `DecisionPacket` metadata.
- `probe-report`: aggregated review-probe surface that runs every registered `probe_*.py` script, renders markdown/terminal/json summaries, writes stable `dev/reports/probes/review_targets.json`, and refreshes `dev/reports/probes/latest/summary.{md,json}` plus `file_topology.json`, `review_packet.{json,md}`, and hotspot `hotspots.{mmd,dot}` artifacts for agent coaching, AI/human design review, and audit. The probe catalog now includes cohesion-heavy mixed-concern detection via `probe_mixed_concerns` and naming cleanup hints via `probe_term_consistency`, so both split-brain structure and legacy public vocabulary show up in the same packet.
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
    bootstrap surfaces such as `CLAUDE.md`.
- `render-surfaces`: policy-owned repo-pack surface generator and drift checker
  for instruction files and starter artifacts such as local `CLAUDE.md`,
  slash/skill templates, and portable governance stubs
  - `--write` rewrites drifted outputs in place, while plain read mode is a
    safe check surface for local validation and `docs-check --strict-tooling`.
  - `--quality-policy <path>` lets another repo reuse the same generator
    against its own `repo_governance.surface_generation` contract.
  - The local `CLAUDE.md` output is the first-hop AI awareness surface. Keep
    it in sync so it advertises `ai_instruction`, `decision_mode`,
    `governance-review --record`, packet-level operational feedback, saved
    graph snapshots, and points agents back to `dev/guides/DEVELOPMENT.md`
    plus this command guide for "which tool should I run now?" routing.
  - The same render pass now derives `CLAUDE.md`'s task-router quick map from
    `governance/task_router_contract.py` and derives the guard-limit block from the
    live code-shape policy modules, so repo policy JSON no longer needs to
    carry a second hardcoded copy of those limits.
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
    autonomy-loop, and `guard-run` consumers together, and
    `DecisionPacket.decision_mode` must gate those same routes, so one
    surviving consumer no longer masks a dropped sibling.
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
    repo so an AI or maintainer has one obvious first-read onboarding file.
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
- `triage`: combined human/AI triage output with optional `cihub triage` artifact ingestion, optional external issue-file ingestion (`--external-issues-file` for CodeRabbit/custom bot payloads), optional review-probe rollup ingestion via `--probe-report` / `--probe-since-ref` / `--probe-head-ref`, and bundle emission (`<prefix>.md`, `<prefix>.ai.json`); extracts priority/triage records into normalized issue routing fields (`category`, `severity`, `owner`), supports optional category-owner overrides via `--owner-map-file`, emits rollups for severity/category/owner counts, and stamps reports with UTC timestamps
  - when local or downloaded CI artifacts contain pytest JUnit XML, `triage` / `report` / `status` now surface one shared `FailurePacket` section with the primary failing test, assertion/error message, and artifact paths instead of only listing failed workflow names
  - `--quality-policy <path>` lets triage classify probe debt against another
    repo policy/preset without editing the engine.
- `triage-loop`: bounded CodeRabbit medium/high loop with mode controls (`report-only`, `plan-then-fix`, `fix-only`), source-run correlation (`--source-run-id`, `--source-run-sha`, `--source-event`), policy-gated fix execution (`AUTONOMY_MODE=operate`, branch allowlist, command-prefix allowlist), notify/comment targeting (`--notify`, `--comment-target`, `--comment-pr-number`), automatic review-escalation comment upserts when max attempts are exhausted with unresolved backlog, attempt-level reporting, a bounded structured backlog slice for downstream autonomy consumers, structured file/line/symbol identity for probe-guidance matching when the source payload has it, optional bundle emission, and optional MASTER_PLAN proposal output
- `mutation-loop`: bounded mutation remediation loop with report-only default, threshold controls, hotspot/freshness reporting, optional policy-gated fix execution, optional summary comment updates, and bundle/playbook outputs
- `autonomy-loop`: bounded autonomy controller wrapper around `triage-loop` + `loop-packet` with hard caps (`--max-rounds`, `--max-hours`, `--max-tasks`), run-scoped packet artifacts, queue inbox outputs, phone-ready status snapshots (`dev/reports/autonomy/queue/phone/latest.{json,md}`), canonical probe-guidance injection from `review_targets.json` into the loop draft when the triage report carries a bounded structured backlog slice, explicit `guidance_adoption_required` packet metadata when that guidance is attached, live `decision_mode` gating that blocks auto-send for approval-required guidance, and strict policy gating for write modes (`AUTONOMY_MODE=operate` required for non-dry-run fix modes; dry-run still downgrades to `report-only`)
- `phone-status`: iPhone/SSH-safe read surface for autonomy controller snapshots; renders one selected projection view (`full|compact|trace|actions`) from `dev/reports/autonomy/queue/phone/latest.json` and can emit controller-state files (`full.json`, `compact.json`, `trace.ndjson`, `actions.json`, `latest.md`)
- `mobile-status`: merged iPhone/SSH-safe read surface for the future phone app; refreshes latest review-channel projections from `dev/active/review_channel.md` + `bridge.md`, combines them with autonomy `phone-status` when present, falls back to review-only live data when the phone artifact is missing, renders one selected mobile view (`full|compact|alert|actions`), and can emit merged projection files (`full.json`, `compact.json`, `alert.json`, `actions.json`, `latest.md`) for downstream clients/notifiers
- `mobile-app`: wrapper over the first-party iPhone/iPad app flow; can run the real simulator demo against the live repo bundle, optionally refresh live Ralph/review state first (`--live-review`), list available simulator/physical devices, open an honest physical-device install wizard, and attempt a real signed physical-device install/launch when an Apple Development Team is provided
- `ralph-status`: Ralph guardrail analytics surface; reads `ralph-report*.json` artifacts, aggregates fix/open counts plus architecture breakdowns, now also surfaces probe-guidance attachment/adoption/waiver counts from Ralph runs, and can emit SVG charts for CLI/reporting/mobile consumers
- `controller-action`: policy-gated control surface for `refresh-status`, `dispatch-report-only`, `pause-loop`, and `resume-loop`; dispatch/mode actions enforce allowlisted workflows/branches, respect `AUTONOMY_MODE=off` kill-switch behavior, and emit auditable action reports plus a stable `typed_action` runtime contract and optional local controller-mode state artifact
- `startup-context`: typed startup packet for AI agent sessions; composes compact repo governance, reviewer gate, push/checkpoint state, and a bounded `WorkIntakePacket` carrying the selected `PlanTargetRef`, typed continuity reconciliation, startup-order warm refs, and live routing defaults; prefers typed review-state acceptance when present, falls back to bridge compatibility reads only when the typed projection is unavailable, resolves typed `review_state.json` through repo-pack/governance candidate-path authority instead of one fixed `dev/reports/.../latest` literal, loads probe startup signals from the managed `dev/reports/probes/latest/summary.json` artifact under that same governed root, renders continuity roots only when the canonical memory/context directories actually exist, persists a managed startup receipt under the repo-owned reports root, returns non-zero when the typed checkpoint budget says another implementation slice must stop and checkpoint first, and is guarded by `check_startup_authority_contract.py` so over-budget continuation or worktree-only module splits fail closed instead of slipping through as local-only state
- `review-channel`: current bridge-gated review-swarm bootstrap surface; `--action launch` reads `dev/active/review_channel.md` + `bridge.md`, emits Codex/Claude conductor launch scripts, defaults live macOS launches to an `auto-dark` Terminal profile when available, auto-relaunches a conductor in the same terminal when the provider exits cleanly, and now requires a fresh `startup-context` receipt before repo-owned launch/rollover work can begin; after that receipt gate, it enforces the existing bridge launch contract: first the `check_review_channel_bridge.py` guard must pass (required bootstrap sections, tracked-file safety, heartbeat metadata), then the live bridge state must show active Codex poll and Claude status within the five-minute heartbeat window and must not report `checkpoint_required` / `safe_to_continue_editing=false` from the typed push-enforcement budget; `--refresh-bridge-heartbeat-if-stale` is the typed self-heal flag for launch/rollover paths and will refresh the reviewer heartbeat metadata plus the non-audit worktree hash when stale/missing heartbeat metadata is the only blocker; non-zero provider exits still stop visibly so auth/CLI failures do not spin forever; `--action status` writes the latest bridge-backed projections under `dev/reports/review_channel/latest/` (`review_state.json`, `compact.json`, `full.json`, `actions.json`, `latest.md`, `registry/agents.json`) and now includes the derived next unchecked plan item, machine-readable `reviewer_worker` state, typed `current_session` live instruction / ACK state, shared context-packet `guidance_refs` when probe guidance is in scope, and bridge-backed `push_enforcement` fields (`checkpoint_required`, `safe_to_continue_editing`, `recommended_action`, `raw_git_push_guarded`), with attention escalating to `checkpoint_required` when the worktree is over budget; `latest.md` now renders the current-session summary from that typed block while the bridge stays a compatibility projection; `--action ensure`, `--action reviewer-heartbeat`, and `--action reviewer-checkpoint` emit the same reviewer-worker contract, while `--action ensure --follow` cadence frames add `review_needed` signals without claiming semantic review completion; active reviewer checkpoints should prefer one typed `--checkpoint-payload-file` or the existing per-section `--*-file` flags for AI-generated markdown / shell-sensitive content instead of inline shell bodies, and `active_dual_agent` writes must carry the live `--expected-instruction-revision`; `--action implementer-wait` is the repo-owned bounded Claude-side polling path and replaces ad-hoc `sleep` shell loops by waking on meaningful reviewer-owned bridge changes, failing closed on reviewer-loop breakage, and timing out after one hour by default; `--action reviewer-wait` is the symmetric Codex-side wait path that wakes on meaningful implementer-owned state changes over top-level `reviewer_worker` / `bridge_liveness` status truth plus projected `current_session` ACK/status fields from `review_state.json`; `--action promote` is the typed repo-owned queue-advance path that rewrites `Current Instruction For Claude` from the next unchecked active-plan checklist item when the current slice is resolved and findings are clear; `--action rollover` writes a repo-visible handoff bundle, relaunches fresh conductors before compaction, and can wait for visible ACK lines in `bridge.md`
- `autonomy-benchmark`: active-plan-scoped swarm benchmark matrix runner (`swarm-counts x tactics`) that launches `autonomy-swarm` batches, captures per-swarm/per-scenario productivity metrics, and writes benchmark bundles under `dev/reports/autonomy/benchmarks/<label>` (non-report modes require `--fix-command`)
- `swarm_run`: guarded autonomy pipeline wrapper around `autonomy-swarm` that loads plan scope context, derives next unchecked plan steps into one prompt, enforces reviewer lane + post-audit digest, runs governance checks (`check_active_plan_sync`, `check_multi_agent_sync`, `docs-check --strict-tooling`, `orchestrate-status/watch`), and appends run evidence to the active plan doc (`Progress Log` + `Audit Evidence`); supports optional continuous multi-cycle execution (`--continuous --continuous-max-cycles`) plus feedback sizing controls (`--feedback-sizing`, `--feedback-no-signal-rounds`, `--feedback-stall-rounds`, `--feedback-downshift-factor`, `--feedback-upshift-rounds`, `--feedback-upshift-factor`) for hands-off checklist progression (non-report modes require `--fix-command`)
- `autonomy-report`: human-readable autonomy digest builder that scans loop/watch artifacts, writes dated bundles under `dev/reports/autonomy/library/<label>`, and emits summary markdown/json plus optional matplotlib charts
- `autonomy-swarm`: adaptive swarm orchestrator that sizes agent count from change/question metadata (with optional token-budget cap), runs per-agent bounded `autonomy-loop` lanes in parallel, reserves a default `AGENT-REVIEW` lane for post-audit review when execution runs with >1 lane, writes one dated swarm bundle under `dev/reports/autonomy/swarms/<label>`, and by default runs a post-audit digest bundle under `dev/reports/autonomy/library/<label>-digest` (use `--no-post-audit` and/or `--no-reviewer-lane` to disable; non-report modes require `--fix-command`)
- `failure-cleanup`: guarded cleanup for local failure triage bundles (`dev/reports/failures`) with default path-root enforcement, optional override constrained to `dev/reports/**` (`--allow-outside-failure-root`), optional scoped CI gate filters (`--ci-branch`, `--ci-workflow`, `--ci-event`, `--ci-sha`), plus dry-run/confirmation controls
- `reports-cleanup`: retention-based cleanup for stale run artifacts under managed `dev/reports/**` roots (default `max-age-days=30`, `keep-recent=10`) with protected paths, preview mode (`--dry-run`), and explicit confirmation/`--yes` before deletion
- `audit-scaffold`: build/update `dev/reports/audits/RUST_AUDIT_FINDINGS.md` from guard findings (with safe output path and overwrite guards)
- `list`: command/profile inventory

## Quick command guide (plain language)

| Command | Run it when | Why |
|---|---|---|
| `check --profile fast` | you need a very fast local sanity pass while iterating | alias of `quick`; runs local guard checks (including AI-guard scripts) and is not a substitute for pre-push validation |
| `check-router --since-ref origin/develop --execute` | before push when changed files span multiple surfaces | auto-selects required lane + risk add-ons and executes the routed command set from `bundle_registry.py` (unknown paths escalate to tooling) |
| `check-router --since-ref origin/develop --quality-policy /tmp/pilot-policy.json` | you are piloting the governance router in another repo clone | reuses the same lane-selection engine against another repo's policy-owned path/risk rules |
| `tandem-validate --format md` | a Codex/Claude tandem slice needs one canonical validator instead of a hand-written checklist | runs preflight policy/status, derives the real lane and risk add-ons from `check-router`, executes the routed bundle, then rechecks `check_review_channel_bridge.py` and `check_tandem_consistency.py` at the end |
| `governance-draft --format md` | you need the current governed-doc discovery surface before a write-mode docs or governance change | renders the deterministic repo-scan entrypoint that should match the CLI inventory and maintainer docs |
| `check --profile ci` | before a normal push | catches build/test/lint issues early |
| `check --profile prepush` | runtime changes touch perf/latency/parser/wake-word/memory-sensitive paths | adds perf + memory-heavy validation before CI catches it |
| `check --profile maintainer-lint` | you are doing focused lint/debt cleanup | runs stricter maintainer lint policy without full runtime build/test loop |
| `check --profile pedantic` | you want a broader optional lint sweep after a large refactor or as explicit pre-release cleanup | runs advisory `clippy::pedantic`, writes structured artifacts under `dev/reports/check/`, and stays out of required bundle/release flow |
| `check --profile quick` | you need a fast local sanity pass while iterating | runs fmt/clippy plus the AI-guard script pack for structural/code-quality feedback without full test/build |
| `guard-run --cwd rust -- cargo test --bin voiceterm ...` | an AI/dev session needs to run raw Rust tests or test binaries directly | runs the command without a shell `-c` wrapper, then automatically executes the required post-run hygiene follow-up (`quick` for runtime/test commands, `process-cleanup --verify` for lower-risk repo tooling commands), and appends a repo-visible `guarded_coding_episode.jsonl` artifact for watchdog analytics; optional flags now carry typed provider/session/retry/verdict metadata for later controller/watchdog callers |
| `check --profile quick --skip-fmt --skip-clippy --no-parallel` | you ran raw `cargo test` / manual test binaries and need orphan cleanup immediately after | runs the AI-guard script pack plus process-sweep pre/post and host-side `process-cleanup --verify`, so stale repo processes and structural regressions are caught before later runs |
| `process-cleanup --verify --format md` | after PTY/runtime tests, manual tooling bundles, or before handoff when host process access is available | safely kills orphaned/stale repo-related host process trees, including descendant PTY children, repo-cwd background helpers, and orphaned tooling descendants, then reruns strict host audit; freshly detached repo-related helpers now keep verify red immediately instead of slipping through as advisory-only noise |
| `process-audit --strict --format md` | when you need read-only host diagnosis or cleanup was intentionally skipped | audits the real host process table for repo leftovers, including descendant PTY children and repo-cwd runtime/tooling helpers that would otherwise look generic in Activity Monitor; attached interactive helper sessions are no longer promoted into stale failures unless they detach/background |
| `data-science --format md` | you want a fresh productivity/agent-sizing snapshot from current telemetry | builds `summary.{md,json}` + charts from devctl events, swarm/benchmark history, watchdog episodes, and governance-review adjudication metrics |
| `governance-review --format md` | you want the current false-positive / cleanup scoreboard for reviewed guard and probe findings | reads the governance review JSONL ledger, keeps the latest verdict per finding id, and writes refreshed `review_summary.{md,json}` artifacts |
| `check --profile release` | before release/tag verification on `master` | adds strict remote CI-status + CodeRabbit/Ralph release gates plus non-blocking mutation-score reminders on top of local release checks |
| `mcp --tool release_contract_snapshot --format json` | an MCP client needs a read-only control-plane contract view | exposes allowlisted, read-only snapshots without changing `devctl` as enforcement authority |
| `check --profile ai-guard` | after touching larger Rust/Python files or guard-owned governance files | runs the full AI guard pack without full test/build cycle for focused cleanup |
| `launcher-check` | you want the launcher/package Python guard lane without remembering a policy path or broader repo checks | delegates to a focused AI-guard-only run against `scripts/` + `pypi/src` using `dev/config/devctl_policies/launcher.json` |
| `launcher-probes` | you want one ranked review packet for launcher/package Python entrypoints | delegates to `probe-report` with the same focused launcher policy and normal probe artifacts |
| `launcher-policy` | you want to inspect what the focused launcher lane actually enables | renders the resolved launcher policy, scopes, and warnings without spelling out `--quality-policy` |
| `docs-check --user-facing` | you changed user docs or user behavior | keeps docs and behavior aligned |
| `docs-check --strict-tooling` | you changed tooling, workflows, or process docs | enforces governance, active-plan sync, and durable guide coverage contracts |
| `docs-check --strict-tooling --quality-policy /tmp/pilot-policy.json` | you want the same docs-governance contract in another repo without patching devctl | resolves canonical doc paths and deprecated-command policy from the supplied repo policy file |
| `push` | you want the canonical repo-owned short-lived branch push validator without mutating git state yet | resolves `repo_governance.push`, checks branch/remote policy, runs the configured preflight, and exits ready/blocked without doing the actual push |
| `push --execute` | validation passed and you want the repo-owned push path instead of ad-hoc `git push` | runs the same policy-driven validation, performs the branch push, then executes the configured post-push bundle |
| `render-surfaces --format md` | you need to inspect repo-pack instruction/starter surfaces or validate drift without writing files | resolves `repo_governance.surface_generation` and reports current sync state for each governed surface |
| `render-surfaces --write --format md` | you changed a repo-pack template, starter stub, or surface-generation policy context | regenerates the governed outputs in place so `docs-check --strict-tooling` and the standalone guard stay green |
| `hygiene` | before merge on tooling/process work | catches doc/process drift and leaked runtime test processes |
| `publication-sync --format md` | a paper/site depends on repo evidence and you need to know if it drifted | shows watched-path changes since the last recorded sync and the exact command to record a new baseline after publish |
| `hygiene --fix` | after local test runs leave Python caches | clears `dev/scripts/**/__pycache__` safely and re-checks hygiene |
| `reports-cleanup --dry-run` | hygiene warns that report artifacts are stale/heavy | previews what retention cleanup would remove without deleting anything |
| `security` | you changed dependencies or security-sensitive code | catches advisory/policy issues |
| `triage --ci` | CI failed and you need an actionable summary | creates a clean failure summary for humans/AI |
| `report --pedantic --pedantic-refresh --format json` | you want one command that refreshes the advisory sweep and emits a structured repo-owned summary | reruns pedantic artifact generation, then reads those artifacts plus `dev/config/clippy/pedantic_policy.json` to emit ranked lint data for review/AI consumption |
| `report --rust-audits --with-charts --emit-bundle --format md` | you want one readable Rust guard audit pack with graphs and file hotspots instead of separate raw guard outputs | runs the Rust best-practices, lint-debt, and runtime-panic guards, explains why each signal is risky, writes `.md` + `.json` bundle files, and generates matplotlib charts when available |
| `report --python-guard-backlog --python-guard-backlog-top-n 25 --since-ref origin/develop --head-ref HEAD --format md` | you want one prioritized Python clean-code hotspot view before promoting stricter policy gates | aggregates dict-schema/global-mutable/parameter-count/nesting-depth/god-class plus broad-except/subprocess-policy guard outputs into one ranked backlog so teams can burn down debt in order |
| `report --probe-report --since-ref origin/develop --head-ref HEAD --format md` | you want the normal project report to include the current review-probe summary for agent/human handoff | runs the registered review probes, folds the aggregated `risk_hints` summary into the shared project snapshot, and scopes the probe scan to the provided commit range when `--since-ref` is set |
| `status --probe-report --format md` | you want a lighter-weight current status view that still surfaces AI-slop findings | runs the registered review probes against the worktree and appends the aggregated hint counts/top files to the standard status snapshot |
| `triage --pedantic --no-cihub --emit-bundle --format md` | you want an AI-friendly pedantic cleanup packet without inventing a second triage system | folds the saved pedantic artifacts into normal `triage` output and bundle files; add `--pedantic-refresh` only when you intentionally want triage to regenerate the artifacts inline |
| `triage-loop --branch develop --mode plan-then-fix --max-attempts 3` | you want bounded automation over medium/high backlog | runs report/fix retry loop with deterministic md/json artifacts plus the bounded backlog slice consumed by `loop-packet` guidance |
| `mutation-loop --branch develop --mode report-only --threshold 0.80` | you want bounded mutation-score automation with hotspots and optional fixes | runs report/fix retry loop with deterministic md/json/playbook artifacts |
| `autonomy-loop --plan-id acp-poc-001 --branch-base develop --mode report-only --max-rounds 6 --max-hours 4 --max-tasks 24 --format json` | you want one bounded controller run that emits queue-ready checkpoint packets | orchestrates triage-loop/loop-packet rounds, writes run-scoped packet artifacts, and refreshes phone-ready `latest.json`/`latest.md` status snapshots |
| `phone-status --phone-json dev/reports/autonomy/queue/phone/latest.json --view compact --format md` | you want one iPhone/SSH-safe autonomy snapshot | renders a selected phone-status projection view and can emit controller-state projection files for downstream clients |
| `mobile-status --phone-json dev/reports/autonomy/queue/phone/latest.json --view compact --emit-projections dev/reports/mobile/latest --format md` | you want one SSH-safe snapshot that already includes Codex/Claude/review state plus controller state for a future phone app | refreshes the latest review-channel projections, merges them with autonomy phone-status when it exists, otherwise emits a review-only live bundle with warnings, and writes compact/alert/actions/full mobile projections for downstream clients or notifier adapters |
| `mobile-app --action simulator-demo --format md` | you want the real iPhone app built, installed in the simulator, synced with live repo data, and launched with a short walkthrough | runs the guided simulator flow over `app/ios/VoiceTermMobileApp`, prints the current live action preview, and points at the real bundle/app paths instead of sample-only data |
| `mobile-app --action simulator-demo --live-review --format md` | you want the simulator to reflect the current repo-backed Ralph/review loop state before launch | refreshes `review-channel --action status`, then runs the guided simulator flow and prints the exact host-side `devctl` commands that still own loop execution |
| `mobile-app --action device-wizard --format md` | you have a plugged-in iPhone/iPad and want the honest install path without guessing | detects connected physical devices, opens the Xcode project, and prints the signing/run/import steps required for real on-device installation |
| `mobile-app --action device-install --development-team <TEAM_ID> --format md` | you have a plugged-in iPhone/iPad and want devctl to attempt the real install instead of only opening Xcode | builds the signed `VoiceTermMobileApp` for `iphoneos`, installs it with `xcrun devicectl`, launches it on-device, and fails with explicit prerequisite errors when device trust or signing is not ready |
| `ralph-status --report-dir dev/reports/ralph --with-charts --format md` | you want one current view of Ralph guardrail progress before wiring phone or PyQt controls on top | aggregates `ralph-report*.json` artifacts, prints fix/open counts plus architecture breakdowns, and writes SVG charts when `--with-charts` is enabled |
| `controller-action --action dispatch-report-only --repo owner/repo --branch develop --dry-run --format md` | you want one guarded operator action without ad-hoc shell scripting | validates policy + mode gates and executes (or previews) bounded dispatch/pause/resume/status actions with structured output and a stable `typed_action` contract |
| `review-channel --action status --terminal none --format md` | you need the current bridge-backed review snapshot without relaunching anything | reads `dev/active/review_channel.md` + `bridge.md`, refreshes `dev/reports/review_channel/latest/`, and emits the current lane/bridge projection set plus typed `current_session` live-status state for operator or tooling consumers |
| `review-channel --action implementer-wait --terminal none --format json` | Claude has finished the current bounded slice and needs to wait safely for the next Codex review/update without leaving a raw shell poller behind | polls the bridge on the normal cadence, exits immediately when reviewer-owned bridge content changes or a new instruction is already waiting, fails closed when the reviewer loop is unhealthy, and times out after one hour by default |
| `review-channel --action promote --terminal none --format md` | the current review slice is accepted and you want the next repo-owned task queued without hand-editing the bridge | reads the configured active-plan checklist, fail-closes unless the current verdict is resolved and findings are clear, rewrites `Current Instruction For Claude`, and refreshes the latest review projections from the same derived next-step source |
| `review-channel --action launch --terminal none --dry-run --format md --refresh-bridge-heartbeat-if-stale` | you want to bootstrap the current Codex-reviewer / Claude-implementer 8+8 markdown swarm from a fresh conversation without hand-editing stale heartbeat metadata first | enforces the fail-closed launch contract, blocks launch when the typed checkpoint budget already says the slice must checkpoint first, auto-refreshes stale/missing reviewer heartbeat metadata only when the rest of the live bridge contract is already valid, reads the merged lane table from `dev/active/review_channel.md`, generates conductor launch scripts with clean-exit auto-relaunch supervision, and shows the exact bootstrap before opening any terminals |
| `review-channel --action launch --terminal terminal-app --refresh-bridge-heartbeat-if-stale` | you want the live Codex + Claude conductor windows and the bridge heartbeat may have aged out | performs the same guarded bootstrap, refuses a fresh launch when the typed checkpoint budget is already over limit, repairs stale/missing reviewer heartbeat metadata when that is the only blocker, then opens one Terminal.app window per provider; it still fails closed if the existing repo-owned session artifacts still look active so a second launch cannot silently race on the same `latest/sessions/` logs |
| `review-channel --action rollover --rollover-threshold-pct 50 --await-ack-seconds 180 --format md` | the active conductor is nearing compaction and needs a clean relaunch instead of summary-only recovery | writes a repo-visible handoff bundle, relaunches fresh Codex/Claude conductors, and waits for visible rollover ACK lines in `bridge.md` before the retiring session exits |
| `autonomy-benchmark --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --swarm-counts 10,15,20,30,40 --tactics uniform,specialized,research-first,test-first --dry-run` | you want measurable swarm tradeoff data before scaling live runs | validates active-plan scope, runs tactic/swarm-size matrix batches, and emits one benchmark report with per-scenario metrics/charts |
| `swarm_run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --mode report-only --run-label <label>` | you want one fully-guarded plan-scoped swarm run without manual glue steps | loads active-plan scope, executes swarm with reviewer+post-audit defaults, runs governance checks, appends progress/audit evidence to the plan doc, and in continuous mode can auto-tune agent count with `--feedback-*` sizing controls |
| `autonomy-report --source-root dev/reports/autonomy --library-root dev/reports/autonomy/library --run-label daily-ops` | you want one human-readable autonomy digest | bundles latest loop/watch artifacts into a dated folder with summary markdown/json and optional charts |
| `autonomy-swarm --question \"<scope>\" --prompt-tokens <n> --token-budget <n>` | you want adaptive multi-agent autonomy execution | computes recommended agent count from metadata + budget, reserves one default reviewer lane (`AGENT-REVIEW`) when possible, runs bounded loops, writes one swarm summary bundle, then auto-runs a post-audit digest bundle (unless `--no-post-audit`) |
| `probe-report --format md --output /tmp/probe-report.md --json-output /tmp/probe-report.json` | you want one repo-owned AI-slop review packet instead of running probe scripts one by one, especially after new modules, refactors, string dispatch, 3+ parameter signatures, or concurrency changes | runs every registered review probe, aggregates all emitted `risk_hints`, writes `dev/reports/probes/review_targets.json`, refreshes `summary.{md,json}`, `file_topology.json`, `review_packet.{json,md}`, and hotspot `hotspots.{mmd,dot}` views, then prints one human/agent-friendly report |
| `probe-report --quality-policy /tmp/pilot-policy.json --adoption-scan --format md` | you are onboarding a new repo and need the first probe packet to rank the whole current worktree instead of a meaningless empty diff | runs every registered review probe against the full current worktree using the supplied repo policy, then emits the normal aggregated packet/artifacts |
| `probe-report --repo-path /tmp/copied-repo --adoption-scan --format md` | you need to scan another local repo from this checkout without `cd`-ing into it first | resolves the target repo policy/scopes through `--repo-path`, runs the normal onboarding probe packet against that repo, and writes the packet under the target repo's `dev/reports/probes/` root by default |
| `governance-bootstrap --target-repo /tmp/copied-repo --format md` | a copied pilot repo or submodule snapshot has a broken `.git` pointer or no starter policy yet | repairs the broken gitdir indirection, reinitializes a standalone local git worktree when needed, writes a starter `dev/config/devctl_repo_policy.json`, seeds portable preset JSON files plus explicit `quality_scopes`, and writes a repo-local `dev/guides/PORTABLE_GOVERNANCE_SETUP.md` onboarding file |
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
  policy override.
- `probe_compatibility_shims.py` is now part of that pack. It uses the same
  portable shim primitive as package-layout to surface missing metadata,
  expired wrappers, broken shim-target convergence, and shim-heavy roots or
  crowded flat families.
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
  `governance-draft`.
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
