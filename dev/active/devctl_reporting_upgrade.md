# Devctl Reporting Upgrade (User-Story Driven, Production-Ready)

Status: Activated planning track (execution mirrored in `dev/active/MASTER_PLAN.md` as MP-306)

## Purpose

Build a production-grade reporting platform on top of `devctl` so maintainers,
team leads, and CI platform engineers can move from signal to action quickly.
The design must stay modular, support optional extras, and integrate deeply with
`ci-cd-hub` while remaining compatible with mixed local `cihub` versions.

## Why This Exists

Current `devctl status/report/triage` outputs are useful but still too narrow
for multi-format diagnostics, richer charts, and large-team handoff workflows.
Key gaps in the current tooling:

1. Voice session data (latency, transcript quality, error rates) is collected
   by VoiceTerm Dev Mode but never surfaces in devctl reports.
2. All outputs are point-in-time snapshots with no trend tracking, so
   maintainers cannot answer "are we getting better or worse?"
3. Sixteen CI workflows produce results (perf benchmarks, coverage, memory
   soak, security scans) but only pass/fail status flows into reports.
4. Terminal output is plain text with no color coding, tables, or visual
   hierarchy for quick scanning.
5. Triage issues suggest next actions as prose but provide no executable
   playbooks or remediation commands.
6. No environment health check exists, so onboarding new contributors
   requires tribal knowledge of required tooling.

This plan defines a phased path to deliver utility-first reporting without
breaking existing command behavior.

## Personas and User Stories

### Persona 1: Repo maintainer (first delivery priority)

1. As a maintainer, I want one command to generate triage + dashboard artifacts
   so I can move from CI failure to next action fast.
2. As a maintainer, I want owner-aware issue routing and severity rollups so I
   can assign follow-up work without manual spreadsheet triage.
3. As a maintainer, I want JSON/MD/HTML/PNG outputs from the same run so I can
   use local debugging, async handoff, and PR evidence without extra tooling.
4. As a maintainer, I want voice session quality metrics (avg latency, error
   rate, dropped frames, transcript word counts) in my report so I can detect
   transcription regressions without manual log analysis.
5. As a maintainer, I want executable playbooks attached to triage issues so I
   can fix common failures with a single copy-paste command instead of
   researching each issue from scratch.

### Persona 2: Team lead

1. As a team lead, I want category/severity/owner trends over time so I can
   spot repeated process failures and prioritize fix investment.
2. As a team lead, I want reproducible artifact bundles that can onboard new
   contributors quickly without local setup guesswork.
3. As a team lead, I want cross-repo-ready structures that can evolve into hub
   workflows across multiple projects.
4. As a team lead, I want DORA-inspired project metrics (release frequency,
   commit-to-release lead time, CI failure rate, mean time to recovery) so I
   can measure delivery health over time.

### Persona 3: CI platform engineer

1. As a platform engineer, I want schema-stable machine outputs so bots can
   consume triage/report data safely.
2. As a platform engineer, I want version-aware CIHub adapters so mixed CLI
   environments still produce useful outputs.
3. As a platform engineer, I want deterministic artifacts and strict validation
   gates so process governance remains auditable.
4. As a platform engineer, I want AI-assisted triage that classifies CI
   failures and suggests fixes so automated pipelines can self-heal common
   issues without human intervention.

### Persona 4: New contributor

1. As a new contributor, I want a single `devctl doctor` command that checks my
   environment (Rust toolchain, Python version, system audio deps, gh CLI,
   cihub version) and tells me exactly what to install or configure.
2. As a new contributor, I want onboarding-oriented report summaries that
   explain project health in plain language without requiring tribal knowledge.

## Product Utility Goals

1. Fast triage: reduce time from failure detection to owner-assigned action.
2. Better release confidence: make go/no-go quality risk visible in one bundle.
3. Better visibility: provide both operator-detail and leadership summaries.
4. Better adoption: keep outputs easy to use even when optional chart/GUI extras
   are not installed.
5. Better automation: expose stable schemas for downstream tools and AI agents.
6. Voice quality visibility: surface transcription latency, error rates, and
   session health as first-class project metrics.
7. Trend awareness: track key metrics over time so teams can see direction, not
   just current state.
8. Environment confidence: verify developer setup correctness with one command.

## Success Metrics

1. Triage-to-action time under 2 minutes for common CI failure categories.
2. Single command produces complete multi-format health view (JSON + MD + Rich
   terminal output).
3. New contributor can go from clone to passing `devctl doctor` in under 10
   minutes.
4. Voice session regression detected within one report cycle after introduction.
5. Team leads can see 30-day trend for any tracked metric in one command.

## Command Surface and Interfaces

### Existing commands to enhance

1. `python3 dev/scripts/devctl.py status`
2. `python3 dev/scripts/devctl.py report`
3. `python3 dev/scripts/devctl.py triage`

### New commands

1. `python3 dev/scripts/devctl.py dashboard`
2. `python3 dev/scripts/devctl.py doctor`
3. `python3 dev/scripts/devctl.py health`

### Unified reporting flags (target)

1. `--format text|json|md|html|rich|tui`
2. `--emit-bundle`
3. `--bundle-dir <path>`
4. `--bundle-prefix <name>`
5. `--chart-engine auto|plotly|matplotlib`
6. `--with-charts`
7. `--tui-mode off|viewer|live`
8. `--cihub-mode auto|legacy|modern|off`
9. `--require-cihub-modern` (strict mode where needed)
10. `--with-voice` (include voice session metrics in output)
11. `--trend-window <days>` (default 30, lookback for trend calculations)
12. `--ai` (enable AI-assisted triage classification)
13. `--desktop-mode off|pyqt6` (optional heavy desktop dashboard)

### Artifact bundle contract (target)

1. `<prefix>.json` (canonical report payload)
2. `<prefix>.md` (human digest)
3. `<prefix>.html` (dashboard)
4. `<prefix>.png` (chart pack index or summary panel)
5. `<prefix>.ai.json` (AI-friendly handoff payload)
6. `artifacts/index.json` (manifest with schema, generator metadata, checksums)

## Data Sources (expanded)

### Currently integrated

1. Git status (branch, changes, changelog/master-plan tracking).
2. Mutation testing (score, outcomes, freshness from `mutants.out/`).
3. GitHub Actions run status via `gh run list`.
4. Dev Mode JSONL sessions (transcript events, latency, errors).
5. Code shape violations (`check_code_shape.py`).
6. Rust lint debt (`check_rust_lint_debt.py`).
7. Rust best practices (`check_rust_best_practices.py`).

### New collectors to add

1. **Voice session quality**: aggregate latency, error rate, dropped frame
   rate, words-per-session, and session quality score from Dev Mode JSONL
   files in `~/.voiceterm/dev/sessions/`.
2. **Coverage**: parse coverage percentage from `coverage.yml` artifacts or
   local `grcov`/`llvm-cov` output.
3. **Performance benchmarks**: ingest latency guard and perf smoke results
   from CI workflow artifacts.
4. **Memory soak**: parse peak memory and leak detection from
   `memory_guard.yml` results.
5. **Security scan**: pull vulnerability counts and severities from
   `cargo audit` JSON and `security_guard.yml` output.
6. **Dependency health**: run `cargo outdated --depth 1` and `cargo machete`
   to detect stale and unused dependencies.
7. **Unsafe code ratio**: run `cargo geiger` (when available) to track safe
   vs unsafe code percentages over time.
8. **DORA-inspired metrics**: compute from `gh` and `git log` data:
   - Release frequency (tags per month).
   - Lead time for changes (median commit-to-tag time).
   - CI failure rate (failed runs / total runs over window).
   - Mean time to recovery (avg time from red CI to next green).
9. **Environment health**: probe Rust toolchain version, required components
   (clippy, rustfmt), Python version, system audio dependencies (portaudio),
   `gh` auth status, and `cihub` version/capabilities.
10. **AI review bot signals**: normalize PR review findings from tools like
    CodeRabbit into the existing issue schema (`category`, `severity`,
    `owner`, `summary`) so triage/report outputs stay unified. Emit medium/high
    backlog artifacts in CI and feed a bounded remediation loop controller for
    optional auto-fix retries (`run_coderabbit_ralph_loop.py`).

## Trend Tracking Model

Store metric snapshots locally for trend computation:

1. Storage location: `~/.voiceterm/dev/metrics/` (or override with
   `--metrics-dir`).
2. Format: one JSONL file per metric source (e.g., `mutation.jsonl`,
   `voice.jsonl`, `ci.jsonl`, `coverage.jsonl`).
3. Each record: `{"timestamp": <ISO>, "values": {...}}`.
4. Append on every `devctl report`, `devctl triage`, or `devctl dashboard`
   run when `--track-metrics` is set (default: on).
5. Trend queries use `--trend-window <days>` to compute deltas, averages,
   and direction indicators.
6. Renderers display trend sparklines (`▁▃▅▇█`) and delta arrows (`↑12%`,
   `↓4`) alongside current values.
7. Prune records older than 90 days by default (`--metrics-retain-days`).

## Playbook Remediation Model

Attach executable remediation to triage issue categories:

1. Playbooks live in `dev/scripts/devctl/playbooks/` as YAML files.
2. Each playbook maps an issue category + pattern to a remediation:

   ```yaml
   - id: cargo-lock-conflict
     match:
       category: infra
       pattern: "Cargo.lock conflict"
     summary: "Regenerate Cargo.lock after dependency update"
     commands:
       - "cd rust && cargo update"
       - "cd rust && cargo check"
     auto_fixable: true
   ```

3. `devctl triage` output includes playbook ID and commands for each
   matched issue.
4. Future: `devctl fix <playbook-id>` runs the remediation interactively.

## AI-Assisted Triage Model

Optional LLM-powered failure classification for CI log analysis:

1. Enabled via `--ai` flag on `triage` and `dashboard` commands.
2. Preprocessing pipeline:
   - Fetch CI log via `gh run view --log-failed`.
   - Strip ANSI escape codes and timestamp prefixes.
   - Extract error boundary sections (lines around first failure).
   - Truncate to token budget (configurable, default 4000 tokens).
3. Structured prompt includes project-specific context (known failure
   patterns, component map, recent changes).
4. Output schema per classified failure:
   ```json
   {
     "type": "compile_error|test_failure|lint|infra|flaky|timeout",
     "component": "audio_pipeline|pty|voice_control|...",
     "file": "src/voice/mod.rs",
     "line": 42,
     "root_cause": "...",
     "suggested_fix": "...",
     "confidence": 0.85,
     "matched_playbook": "cargo-lock-conflict"
   }
   ```
5. Results merge into the triage issue list with `source: "ai"` tag.
6. Failure knowledge base: store fingerprints + resolutions in
   `~/.voiceterm/dev/failure_kb.jsonl` for pattern matching before
   invoking the LLM.

## CIHub Integration Model

### Capability-first adapter design

1. Probe available `cihub` commands and flags at runtime.
2. If modern `cihub triage/report/dashboard` capabilities exist, use them.
3. If only legacy capabilities exist, fall back to compatible ingestion paths.
4. Normalize all CIHub and local signals into one internal issue/report schema.

### Compatibility baseline

1. Local environments with older binaries (for example `cihub 0.2.0`) must not
   hard-fail by default.
2. Strict workflows may opt into fail-fast using explicit strict flags.
3. All fallback behavior must emit clear warnings and remediation guidance.

## CIHub Security/Quality Port (MP-306 Active Slice)

Port CIHUB's proven toggle model into VoiceTerm so we keep broad coverage
without forcing every expensive scanner on every run.

### Core default-on checks (fast, always practical)

1. RustSec policy (`cargo audit` + policy gate)
2. Workflow security scan (`zizmor`)
3. CodeQL alert gate (open high/critical alert query)
4. Python quality checks scoped to changed files (`black`, `isort`)
5. Python security static scan scoped to repo Python paths (`bandit`)

### Opt-in expensive checks (scheduled/release/security profile)

1. Semgrep SAST
2. Full CodeQL analysis workflow
3. Dependency/license policy checks (`cargo deny`)
4. Unsafe ratio/debt tracking (`cargo geiger`)
5. Fuzzing/soak expansion (`cargo fuzz` targets beyond existing property tests)

### Threshold policy baseline (port from CIHUB style)

1. Core checks: fail on any regression/blocking finding.
2. Expensive checks: default advisory on local runs, fail-fast in strict CI
   profiles.
3. Every scanner emits machine-readable output so `status/report/triage` can
   aggregate findings consistently.

## Rust Overlay Parity Boundary (Execution Contract)

Do not build a full duplicate Rust+Python control plane. Use a split boundary:

1. Rust overlay/runtime keeps ownership of latency-sensitive or session-critical
   behavior (event loop, PTY lifecycle, wake/runtime guards, UI safety paths).
2. Python `devctl` keeps ownership of CI/reporting orchestration, artifact
   aggregation, scanner adapters, and governance workflows.
3. When a `devctl` signal must affect runtime decisions, promote only that
   specific contract into Rust with tests/ADR evidence (no whole-stack rewrite).

## Dev-Mode Overlay Integration Track (MP-306)

Use the Rust overlay as a guarded UI shell for control-plane automation while
keeping command execution and policy logic in `devctl`.

### Scope

1. Add a Dev Tools panel/tab available only with `--dev`.
2. Panel actions call allowlisted `devctl`/`cihub` commands with JSON output.
3. Voice intents are enabled only in Dev Mode for approved control-plane tasks.
4. Normal listen/send mode must stay behavior-identical when `--dev` is off.

### Current sprint activation (2026-02-23)

`MP-306` is running in 3-agent mode with strict no-overlap ownership:

1. `AGENT-1` (Rust runtime lane): `rust/src/bin/voiceterm/**` only for Dev Tools
   panel/tab bridge and async command broker wiring.
2. `AGENT-2` (control-plane lane): `dev/scripts/devctl/**` plus
   `.github/workflows/security_guard.yml` and
   `.github/workflows/release_preflight.yml` for scanner tiers, JSON outputs,
   command allowlists, and CIHUB setup flow primitives.
3. `AGENT-3` (governance/safety lane): `dev/active/**`,
   `dev/DEVELOPMENT.md`, `dev/scripts/README.md`, and tooling tests/docs for
   non-interference checks, CI guard updates, and merge-readiness audit.

Execution order is fixed:

1. `AGENT-2` lands control-plane primitives.
2. `AGENT-1` integrates Rust `--dev` bridge to those primitives.
3. `AGENT-3` finalizes non-interference gates, docs, and audit pass.

Coordination model for this sprint:

1. Use `dev/active/MULTI_AGENT_WORKTREE_RUNBOOK.md` as the only instruction,
   ACK, progress, and handoff surface.
2. Keep `dev/active/MASTER_PLAN.md` as the execution tracker.
3. Run orchestrator loop every 30 minutes:
   - `python3 dev/scripts/devctl.py orchestrate-status --format md`
   - `python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 30 --format md`
   - `python3 dev/scripts/checks/check_multi_agent_sync.py --format md`

## MP-306 Hardening Checklist (Temporary Execution Block)

This block is the active implementation checklist for the current automation
hardening slice. Keep it while the slice is open; retire it once all items are
landed and reflected in `MASTER_PLAN`.

Current status (2026-02-23): local implementation + verification complete;
pending merge/push promotion.

### Scope

1. Security scanner-tier CI behavior must not skip Python checks due to
   changed-file detection assumptions in CI.
2. Failure triage automation must not execute untrusted workflow revisions from
   forked PR contexts.
3. Failure cleanup must be constrained to failure-artifact paths by default and
   support CI-gated scoped cleanup decisions.
4. AI guard failures must emit one canonical remediation scaffold so humans and
   agents can coordinate fixes from a shared active document.

### Required Acceptance Gates

1. `.github/workflows/security_guard.yml` and
   `.github/workflows/release_preflight.yml` run:
   `python3 dev/scripts/devctl.py security --scanner-tier core --python-scope all ...`
2. `.github/workflows/failure_triage.yml` enforces same-repo + trusted-event
   + allowlisted-branch guards before checkout/triage, with branch policy
   configurable via repo variable `FAILURE_TRIAGE_BRANCHES`.
3. Failure-triage command step exports `GH_TOKEN` so CI run collection behaves
   deterministically.
4. `devctl failure-cleanup` deletes only within `dev/reports/failures` unless
   an explicit override flag is used.
5. `devctl failure-cleanup --require-green-ci` supports optional run filters
   (`branch`, `workflow`, `event`, `sha`) and fails safe when filters produce
   no candidate runs.
6. Regression tests cover parser flags and command-gate behavior.
7. Failure/security workflow jobs define explicit `timeout-minutes` budgets.
8. `devctl check --profile ai-guard` auto-generates `dev/active/RUST_AUDIT_FINDINGS.md`
   when AI guard steps fail, and `.github/workflows/tooling_control_plane.yml`
   generates/uploads the same scaffold on docs-policy failure paths.

### Verification Bundle For This Slice

1. `python3 -m unittest dev.scripts.devctl.tests.test_security`
2. `python3 -m unittest dev.scripts.devctl.tests.test_failure_cleanup`
3. `python3 dev/scripts/devctl.py security --scanner-tier core --python-scope all --dry-run --format json`
4. `python3 dev/scripts/devctl.py failure-cleanup --dry-run --require-green-ci --format md`
5. `python3 dev/scripts/devctl.py docs-check --strict-tooling`
6. `python3 dev/scripts/devctl.py hygiene`
7. `python3 -m unittest dev.scripts.devctl.tests.test_audit_scaffold dev.scripts.devctl.tests.test_check`
8. `python3 dev/scripts/devctl.py audit-scaffold --force --yes --format md`

### Command broker constraints

1. No free-form shell execution from voice intents.
2. Allowlist only explicit subcommands/flags.
3. Run subprocesses asynchronously with timeout + cancellation.
4. Require preview + confirm for mutating actions (repo setup, sync/push, release prep).
5. Persist command/audit ledger entries for every action.

### Repo bootstrap workflow (inside Dev Mode)

1. Capability probe: detect `cihub` version and supported commands.
2. Plan preview: show what setup steps will run for this repo.
3. Confirmed apply: run `cihub detect/init/update/validate` wrappers.
4. Post-check: run `devctl docs-check --strict-tooling`, `hygiene`, and key
   sync/security guards before marking setup complete.

### Compatibility note

Current local baseline includes legacy CIHub variants (for example `cihub 0.2.0`).
The bridge must degrade gracefully with explicit operator guidance instead of
hard-failing unless strict flags are enabled.

## Architecture Plan

Create a shared reporting engine under `dev/scripts/devctl/reporting/`:

1. `model.py`: canonical report model + schema version.
2. `collectors/`: git, CI, mutation, dev-log, voice, coverage, perf, memory,
   security, dependency, environment, and CIHub probes.
3. `capabilities.py`: CIHub feature detection and cache helpers.
4. `compat.py`: legacy/modern normalization layer.
5. `renderers/`: json, md, rich (terminal), html, png, tui, and pyqt emitters.
6. `bundles.py`: deterministic artifact writing and manifest generation.
7. `dashboard.py`: command orchestration for dashboard-focused output packs.
8. `trends.py`: metric storage, trend computation, sparkline generation.
9. `playbooks.py`: playbook loader, issue-to-playbook matcher, fix runner.
10. `doctor.py`: environment probe logic and remediation suggestions.
11. `ai_triage.py`: log preprocessing, LLM prompt construction, failure
    knowledge base queries, and structured result parsing.
12. `desktop.py`: PyQt6 dashboard shell (dock layout, panels, and live wiring).

Command wrappers should stay thin and delegate logic to shared reporting
modules to prevent output drift and reduce maintenance risk.

## Dependency Model

Keep base tooling dependency-light and use optional extras:

1. Base mode: JSON + MD + text always available (zero extra deps).
2. Rich extra: color-coded tables, tree views, progress bars, and panels for
   terminal output. Lightweight single dependency.
3. Textual extra: interactive TUI dashboard with tabbed panels, sparkline
   widgets, and live-updating Workers. Built on Rich.
4. PyQt6 extra: heavy desktop dashboard with dockable panes, split views,
   saved layouts, and action panels.
5. PyQt6-WebEngine extra: embedded browser panels for rich Plotly/HTML widgets.
6. PyQt6-Charts/PyQt6-Graphs extra: native chart widgets for 2D/3D views.
7. Plotly extra: richer interactive HTML dashboards (heavier dep).
8. Matplotlib extra: static PNG chart generation.

Missing optional dependencies must produce actionable warnings and fallback
outputs, not command crashes. Fallback chains:

1. CLI mode: `tui -> rich -> md -> text`.
2. Desktop mode: `pyqt6 -> tui -> rich -> md -> text`.

## PyQt6 Heavy Dashboard Concepts (discussion backlog)

Use this list for roadmap discussion and prioritization:

1. Dockable incident workspace (`QMainWindow` + `QDockWidget`) with movable,
   floatable panes for triage, logs, trends, and playbooks.
2. Persistent workspace layouts (`saveState`/`restoreState` + `QSettings`) so
   each maintainer can keep a preferred operator layout across restarts.
3. High-volume issue grid (`QAbstractTableModel` + `QSortFilterProxyModel`)
   with instant filtering, sorting, and severity/owner drill-down.
4. Embedded web analytics panels (`QWebEngineView`) for Plotly charts and
   HTML artifacts without leaving the desktop app.
5. Bi-directional UI actions (`Qt WebChannel`) so browser widgets can trigger
   native Python actions like playbook execution or bundle export.
6. Live artifact auto-refresh (`QFileSystemWatcher`) for CI artifacts and local
   report bundles as files change.
7. Parallel refresh workers (`QThreadPool`) so heavy data collection does not
   freeze the UI.
8. Playbook command center (`QProcess`) with dry-run mode, streaming logs,
   cancellation, and captured exit status.
9. Side-by-side run comparison mode (current vs baseline) for fast regression
   investigation during release readiness reviews.
10. Native graph track with Qt Graphs (preferred long-term) and compatibility
    bridge for Qt Charts where migration is still pending.

## Devctl Doctor Command

`devctl doctor` checks environment readiness and reports actionable fixes:

### Probes

1. Rust toolchain: version, required components (clippy, rustfmt, llvm-tools).
2. Cargo subcommands: audit, deny, machete, geiger, outdated (optional).
3. Python: version, required packages for devctl scripts.
4. System dependencies: portaudio/coreaudio headers (for voice/audio features).
5. `gh` CLI: installed, authenticated (`gh auth status`).
6. `cihub` CLI: installed, version, available capabilities.
7. Git: version, remote connectivity.
8. Optional tools: markdownlint, grcov, cargo-mutants.

### Output

Color-coded checklist (pass/warn/fail) with install commands for each
failing probe. Machine-readable JSON output via `--format json`.

## Devctl Health Command

`devctl health` runs Rust-specific project health checks in parallel and
produces a unified scorecard:

### Checks

1. `cargo audit` — known vulnerability count by severity.
2. `cargo deny` — license compliance, banned crates, duplicate deps.
3. `cargo machete` — unused dependency count.
4. `cargo geiger` — safe vs unsafe code ratio (when available).
5. `cargo outdated --depth 1` — stale dependency count.
6. `cargo clippy --message-format json` — warning count by category.
7. Mutation score from `mutants.out/outcomes.json`.
8. Coverage percentage from latest run.

### Output

Single terminal table with pass/warn/fail color coding per check.
Trend indicators when historical data is available.
JSON and markdown formats for CI consumption.

## Phased Delivery Plan

### Phase 1a: Engine foundation and Rich terminal output

1. Introduce shared reporting model and modular reporting engine under
   `dev/scripts/devctl/reporting/`.
2. Add Rich-based terminal renderer (color tables, status indicators, tree
   views) as the default `--format rich` output path.
3. Wire voice session quality collector into `build_project_report()` using
   existing Dev Mode JSONL data.
4. Enhance `status/report/triage` to consume shared engine paths.
5. Add `devctl doctor` with environment probes and remediation output.
6. Land Dev Tools read-only panel slice in Rust Dev Mode (`--dev` only) that
   surfaces `devctl status/report/triage/security` JSON summaries.

Exit criteria:

1. `devctl report --format rich` produces color-coded terminal output.
2. Voice session metrics appear in report when `--with-voice` is set.
3. `devctl doctor` detects and reports missing tooling with install commands.
4. Existing `--format json` and `--format md` outputs remain stable.

### Phase 1b: Bundles, health scorecard, and CIHub baseline

1. Add `devctl health` with parallel Rust health checks and scorecard output.
2. Add `devctl dashboard` with JSON/MD/HTML bundle output.
3. Implement CIHub capability detection plus legacy/modern adapter baseline.
4. Add deterministic bundle manifest and regression test coverage.
5. Integrate orphaned CI workflow data (coverage, perf, memory, security)
   into the collector pipeline.
6. Add CIHub repo bootstrap flow behind explicit confirmation in Dev Mode and
   expose it in both keyboard and voice-triggered paths.

Exit criteria:

1. One command run can emit a complete multi-format bundle.
2. CIHub fallback path works in mixed capability environments.
3. `devctl health` produces a unified Rust project scorecard.
4. Coverage, perf, and security data appear in reports when available.
5. Strict test suite and docs governance checks pass.

### Phase 2: Trends, DORA metrics, and playbook remediation

1. Implement metric trend storage and sparkline rendering.
2. Add DORA-inspired project metrics (release frequency, lead time,
   failure rate, mean time to recovery).
3. Add playbook remediation system with YAML-defined runbooks.
4. Improve next-action generation with linked playbook commands.
5. Add onboarding-oriented summaries for new maintainers.
6. Add Textual-based interactive TUI viewer mode for `devctl dashboard`.
7. Add PyQt6 heavy desktop viewer mode with dockable panes and saved layouts.
8. Add cross-view parity checks so TUI and PyQt6 show identical core metrics.
9. Expand dev-mode voice intents for safe control-plane orchestration with
   confirmation and allowlist enforcement.

Exit criteria:

1. `devctl report` shows 30-day trend sparklines for key metrics.
2. DORA metrics are computable and displayed in team lead views.
3. Triage issues include matched playbooks with copy-paste commands.
4. `devctl dashboard --tui-mode viewer` launches an interactive TUI.
5. `devctl dashboard --desktop-mode pyqt6` launches a desktop dashboard when
   extras are installed.
6. Handoff bundles are repeatable and easy to consume.
7. Core metric values match across TUI and PyQt6 viewer surfaces.

### Phase 3: AI triage, automation, and platform depth

1. Implement AI-assisted triage with log preprocessing and LLM integration.
2. Add failure knowledge base for pattern matching before LLM invocation.
3. Expand modern CIHub report/dashboard integration paths.
4. Add strict schema validation modes (`warn`/`strict`) and compat gates.
5. Add `devctl fix <playbook-id>` for interactive remediation execution.
6. Add PyQt6 live mode with operator action panels and run-comparison views.
7. Add Textual live mode and automation hooks as lightweight fallback.
8. Add full non-interference certification proving default Whisper/listen mode
   behavior remains unchanged by all Dev Tools additions.

Exit criteria:

1. `devctl triage --ai` produces structured failure classifications.
2. Failure knowledge base matches repeat issues without LLM calls.
3. Machine outputs are stable for bot/agent integrations.
4. `devctl fix` can execute playbook remediations interactively.
5. Optional PyQt6 live mode supports real-time updates and playbook actions.
6. Optional TUI live mode works without degrading base CLI utility.

## Production-Readiness Requirements

1. Deterministic output ordering and stable artifact manifests.
2. Versioned schema with compatibility tests.
3. Unit + integration coverage for all command/format paths.
4. Failure-path coverage for missing tools, bad JSON, partial artifacts, and
   unsupported capability sets.
5. Runtime budget checks for no-network and CIHub-enabled modes.
6. Clear operator docs for defaults, fallbacks, and strict modes.
7. Backward-compatible behavior for existing core command outputs unless a
   change is explicitly documented and versioned.
8. Trend storage corruption resilience (malformed JSONL lines skipped with
   warning, not crash).
9. AI triage respects token budgets and gracefully degrades when LLM is
   unavailable.
10. Doctor probes must not modify system state (read-only checks only).
11. PyQt6 desktop mode remains optional and degrades to TUI/Rich mode with
    actionable warnings when extras are missing.
12. Desktop chart paths prefer Qt Graphs for new work; Qt Charts usage must be
    documented as migration compatibility only.

## Validation and Evidence Plan

Local validation bundle for this track:

1. `python3 dev/scripts/checks/check_active_plan_sync.py`
2. `python3 dev/scripts/devctl.py docs-check --strict-tooling`
3. `python3 dev/scripts/devctl.py hygiene`
4. `python3 -m unittest discover -s dev/scripts/devctl/tests -p 'test_*.py'`
5. `python3 dev/scripts/checks/check_code_shape.py`
6. `python3 dev/scripts/checks/check_rust_lint_debt.py`
7. `python3 dev/scripts/checks/check_rust_best_practices.py`
8. `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`

## Risks and Mitigations

1. Risk: output sprawl and command complexity.
   Mitigation: shared engine + thin command wrappers + strict schema.
2. Risk: optional dependency drift.
   Mitigation: explicit extras, fallback chain (`tui -> rich -> md -> text`),
   and dependency health tests.
3. Risk: CIHub contract drift.
   Mitigation: capability probes, adapters, and compatibility test fixtures.
4. Risk: performance regressions in large bundles.
   Mitigation: runtime budgets and deterministic aggregation design.
5. Risk: trend storage grows unbounded.
   Mitigation: automatic pruning with configurable retention window (default
   90 days), corruption-resilient JSONL parsing.
6. Risk: AI triage produces hallucinated fixes.
   Mitigation: confidence scores, human-review-required flag on low-confidence
   results, failure knowledge base prioritized over LLM for known patterns.
7. Risk: doctor probes break on exotic environments.
   Mitigation: each probe is isolated with try/except, partial results always
   returned, unknown environments emit warnings not errors.
8. Risk: Rich/Textual/PyQt6 dependencies add installation friction.
   Mitigation: Rich/Textual/PyQt6 are all optional extras; base JSON/MD/text
   mode requires zero extras and follows explicit fallback chains.
9. Risk: PyQt6 licensing and packaging constraints are misapplied.
   Mitigation: document GPL/commercial licensing expectations and keep desktop
   mode opt-in behind explicit extras.
10. Risk: Qt Charts deprecation creates long-term maintenance debt.
    Mitigation: use Qt Graphs for new chart surfaces and keep Qt Charts only as
    compatibility fallback during migration.

## Iteration Protocol

1. Keep this file as the canonical spec for the reporting track.
2. Track execution state only in `dev/active/MASTER_PLAN.md`.
3. Append major strategy changes here with date-stamped notes.
4. Preserve backward compatibility expectations as phases land.

## External Reference Notes (2026-02-23, Deferred GUI Research)

The Qt/PyQt/PySide links below are archived research context only. Active
execution remains Rust-first and does not include desktop GUI delivery in the
current MP scope.

1. Main window and dock architecture:
   https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QMainWindow.html
2. Dock widgets:
   https://doc.qt.io/qt-6/qdockwidget.html
3. Persistent settings/layout:
   https://doc.qt.io/qt-6/qsettings.html
4. Large-table filtering/sorting:
   https://doc.qt.io/qt-6/qsortfilterproxymodel.html
5. Embedded web panels:
   https://doc.qt.io/qtforpython-6/PySide6/QtWebEngineWidgets/QWebEngineView.html
6. JS/native bridge:
   https://doc.qt.io/qtforpython-6/PySide6/QtWebChannel/index.html
7. Background worker pool:
   https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThreadPool.html
8. Process execution controls:
   https://doc.qt.io/qt-6/qprocess.html
9. File watch/live refresh:
   https://doc.qt.io/qt-6/qfilesystemwatcher.html
10. Chart direction note:
    Qt Charts deprecation in 6.10 and Qt Graphs direction:
    https://doc.qt.io/qtforpython-6/overviews/qtcharts-overview.html
11. Python package extras for desktop mode:
    https://pypi.org/project/PyQt6/
    https://pypi.org/project/PyQt6-WebEngine/
    https://pypi.org/project/PyQt6-Charts/

## Change Log

- 2026-02-23: Major revision. Added voice session data integration, trend
  tracking model, playbook remediation, AI-assisted triage, devctl doctor
  and devctl health commands, DORA-inspired metrics, Rich/Textual/PyQt6
  rendering strategy, expanded data sources (coverage, perf, memory, security,
  dependency health, unsafe ratio), new contributor persona, success metrics,
  failure knowledge base, and restructured phases (split Phase 1 into 1a/1b).
  Informed by codebase audit showing 16 CI workflows with orphaned data and
  existing Dev Mode JSONL infrastructure.
- 2026-02-23: Added guarded branch-sync control-plane utility planning context
  (`devctl sync`) under MP-306 execution slices so maintainers have one
  repeatable path for `develop`/`master`/current-branch sync with clean-tree
  and fast-forward safety checks before report/triage/release workflows.
