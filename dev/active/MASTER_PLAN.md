# Master Plan (Active, Unified)

## Canonical Plan Rule

- This file is the single active plan for strategy, execution, and release tracking.
- `dev/active/INDEX.md` is the canonical active-doc registry and read-order map for agents.
- `dev/active/theme_upgrade.md` is the consolidated Theme Studio specification + gate catalog + overlay visual research + redesign appendix, but not a separate execution tracker; implementation tasks stay in this file.
- `dev/active/memory_studio.md` is the Memory + Action Studio specification + gate catalog, but not a separate execution tracker; implementation tasks stay in this file.
- `dev/active/devctl_reporting_upgrade.md` is the phased `devctl` reporting/CIHub specification, but not a separate execution tracker; implementation tasks stay in this file under `MP-306`.
- `dev/active/autonomous_control_plane.md` is the autonomous loop + mobile control-plane execution spec; implementation tasks stay in this file under `MP-325..MP-338, MP-340`.
- `dev/active/loop_chat_bridge.md` is the loop artifact-to-chat suggestion coordination runbook; execution evidence and operator handoffs for this path stay there under `MP-338`.
- `dev/active/rust_workspace_layout_migration.md` is the Rust workspace path migration execution spec; implementation tasks stay in this file under `MP-339`.
- `dev/active/naming_api_cohesion.md` is the naming/API cohesion execution spec; implementation tasks stay in this file under `MP-267`.
- `dev/active/MULTI_AGENT_WORKTREE_RUNBOOK.md` is the current-cycle parallel orchestration/reviewer protocol and must be refreshed per execution cycle.
- Deferred work lives in `dev/deferred/` and must be explicitly reactivated here before implementation.

## Status Snapshot (2026-03-01)
- Last tagged release: `v1.0.98` (2026-03-01)
- Current release target: `post-v1.0.98 planning`
- Active development branch: `develop`
- Release branch: `master`
- Strategic focus: sequential execution with one primary product lane at a
  time: release stability first, then Theme completion, then Memory completion.
- In-flight: release-channel stability fix for Homebrew formula manifest-path
  compatibility (`libexec/src/Cargo.toml` -> `libexec/rust/Cargo.toml`) plus
  Theme GA baseline execution (`MP-161`, `MP-162`, `MP-174`, `MP-166`,
  `MP-167`, `MP-173`).
- Execution mode: keep autonomy/tooling/runtime reliability in maintenance-only
  mode while Theme and Memory product lanes are completed in order.
- Maintainer-doc clarity update: `dev/DEVELOPMENT.md` now includes an end-to-end lifecycle flowchart plus check/push routing sections while `AGENTS.md` remains the canonical policy router.
- Tooling docs-governance update: `devctl docs-check --strict-tooling` now enforces markdown metadata-header normalization for `Status`/`Last updated`/`Owner` blocks via `check_markdown_metadata_header.py`.
- Loop architecture clarity update: `dev/ARCHITECTURE.md` and
  `dev/DEVELOPMENT.md` now document the custom repo-owned Ralph/Wiggum loop
  path and the federated-repo import model in simple flowchart form.
- Loop comment transport hardening update: shared workflow-loop `gh` helpers now
  avoid invalid `--repo` usage for `gh api` calls so summary-and-comment mode
  can publish and upsert commit/PR comments reliably.
- Audit-remediation update: Round-2 high-severity audit fixes landed for prompt
  detection hot-path queue behavior, transcript merge-loop invariants,
  persistent-config duplication reduction, and devctl release/comment/report
  helper hardening with expanded unit coverage.
- Runtime cleanup update: startup splash logo coloring now uses a single
  theme-family accent (no rainbow line rotation), and the stale orphan
  `rust/src/bin/voiceterm/progress.rs` module has been removed.
- CI compatibility hotfix update: release-binary workflow runner labels now use
  actionlint-supported macOS targets, latency guard script path resolution now
  supports `rust/` with `src/` fallback, and explicit `devctl triage --cihub`
  opt-in now preserves capability probing when PATH lookup misses the binary.
- Release workflow stability update: `release_attestation.yml` action pins were
  refreshed to valid GitHub-owned SHAs, and `scorecard.yml` now keeps
  workflow-level permissions read-only with write scopes isolated to the
  scorecard job so OpenSSF publish verification succeeds.
- Control-plane simplification update: MP-340 is now Rust-first only (Rust
  overlay + `devctl` + phone/SSH projections). The optional `app/pyside6`
  command-center track is retired from active execution scope.

## Multi-Agent Coordination Board

This board remains the execution tracker for lane ownership/status.
`dev/active/MULTI_AGENT_WORKTREE_RUNBOOK.md` is the single coordination
surface for instructions, ACKs, progress updates, and handoff evidence.

Branch guards for all agents:

1. Start from `develop` (never from `master`).
2. Use dedicated worktrees and dedicated feature branches per agent.
3. Rebase each active agent branch after every merge to `origin/develop`.
4. Update this board before and after each execution batch.
5. Keep `master` release-only (merge/tag/publish only).

| Agent | Lane | Active-doc scope | MP scope (authoritative) | Worktree | Branch | Status | Last update (UTC) | Notes |
|---|---|---|---|---|---|---|---|---|
| `AGENT-1` | Theme runtime visual pass | `dev/active/theme_upgrade.md` + runtime pack | `MP-161, MP-162, MP-174` | `../codex-voice-wt-a1` | `feature/a1-theme-runtime-surface` | `planned` | `2026-02-24T06:21:38Z` | `scaleout-20260224`; lane initialized for style-pack runtime parity and non-regression guards. |
| `AGENT-2` | Theme Studio control parity | `dev/active/theme_upgrade.md` + runtime pack | `MP-166` | `../codex-voice-wt-a2` | `feature/a2-theme-studio-parity` | `planned` | `2026-02-24T06:21:38Z` | `scaleout-20260224`; lane initialized for full Studio field/control mapping parity. |
| `AGENT-3` | Theme GA gates and advanced interactions | `dev/active/theme_upgrade.md` + docs | `MP-167, MP-173, MP-177, MP-178, MP-181` | `../codex-voice-wt-a3` | `feature/a3-theme-ga-gates` | `planned` | `2026-02-24T06:21:38Z` | `scaleout-20260224`; lane initialized for GA validation, policy gates, and inspector/interaction work. |
| `AGENT-4` | Memory foundation and retrieval core | `dev/active/memory_studio.md` + runtime pack | `MP-231, MP-233, MP-234` | `../codex-voice-wt-a4` | `feature/a4-memory-foundations` | `planned` | `2026-02-24T06:21:38Z` | `scaleout-20260224`; lane initialized for memory ingestion/retrieval and context-pack foundation. |
| `AGENT-5` | Memory compaction and quality gates | `dev/active/memory_studio.md` + tooling/docs | `MP-235, MP-243, MP-244` | `../codex-voice-wt-a5` | `feature/a5-memory-compaction` | `planned` | `2026-02-24T06:21:38Z` | `scaleout-20260224`; lane initialized for compaction workflow and quality/evidence harness. |
| `AGENT-6` | Memory acceleration and rollout gates | `dev/active/memory_studio.md` + benchmark scripts | `MP-237, MP-250, MP-251, MP-252, MP-253, MP-254, MP-255` | `../codex-voice-wt-a6` | `feature/a6-memory-acceleration` | `planned` | `2026-02-24T06:21:38Z` | `scaleout-20260224`; lane initialized for acceleration prototypes and guarded rollout policy. |
| `AGENT-7` | Autonomy service and phone adapter track | `dev/active/autonomous_control_plane.md` + tooling/docs | `MP-330, MP-331` | `../codex-voice-wt-a7` | `feature/a7-autonomy-service` | `planned` | `2026-02-24T06:21:38Z` | `scaleout-20260224`; lane initialized for mobile control-plane service scaffolding. |
| `AGENT-8` | Autonomy guardrails and loop bridge | `dev/active/autonomous_control_plane.md`, `dev/active/loop_chat_bridge.md` | `MP-332, MP-336, MP-338` | `../codex-voice-wt-a8` | `feature/a8-autonomy-guardrails` | `planned` | `2026-02-24T06:21:38Z` | `scaleout-20260224`; lane initialized for policy/traceability hardening and loop handoff safety. |
| `AGENT-9` | Tooling performance and maintainer UX | `dev/active/devctl_reporting_upgrade.md` + tooling pack | `MP-297, MP-298, MP-257` | `../codex-voice-wt-a9` | `feature/a9-tooling-hardening` | `planned` | `2026-02-24T06:21:38Z` | `scaleout-20260224`; lane initialized for `devctl` speed/readability improvements and docs clarity. |
| `AGENT-10` | Runtime send/reliability fixes | `dev/active/MASTER_PLAN.md` + runtime/voice pack | `MP-301, MP-322, MP-323, MP-335` | `../codex-voice-wt-a10` | `feature/a10-runtime-reliability` | `planned` | `2026-02-24T06:21:38Z` | `scaleout-20260224`; lane initialized for send-intent, wake-word, and input-edit reliability fixes. |

## Strategic Direction

- Protect current moat: terminal-native PTY orchestration, prompt-aware queueing, local-first voice flow.
- Close trust gap: latency metrics must match user perception and be auditable.
- Build differentiated product value in phases:
  1. Visual-first UX pass (telemetry, motion, layout polish, theme ergonomics)
  2. Workflow differentiators (voice navigation, history, CLI workflow polish)
  3. Theme-systemization (visual surfaces first, then full Theme Studio control parity)
  4. Advanced expansion (streaming STT, tmux/neovim, accessibility)

## Unified Active-Docs Phased Map (Execution Order)

This is the cross-plan execution map so agents and developers stay aligned on
main goal and sequence across all active docs.

### Phase A - Governance + Scope Integrity

1. Keep one execution tracker (`MASTER_PLAN`) and strict active-doc sync.
2. Enforce repeat-to-automate and audit evidence as default operating mode.

Mapped scopes:

- `MP-333`, `MP-337`
- `dev/active/INDEX.md`
- `dev/active/MULTI_AGENT_WORKTREE_RUNBOOK.md`

### Phase B - Runtime and Workspace Reliability Baseline

1. Keep runtime safety/perf/teardown/wake-word hardening green.
2. Complete workspace layout migration so path contracts are stable.

Mapped scopes:

- `MP-127..MP-138`, `MP-339`, `MP-341`, runtime hardening + workspace migration docs.

### Phase C - Tooling Control Plane + Loop Foundations

1. Keep `devctl` reporting/control-plane lane as the automation backbone.
2. Keep Ralph + mutation loops bounded, source-correlated, and policy-gated.
3. Keep external federation bridges pinned and governed.

Mapped scopes:

- `MP-306`, `MP-325..MP-329`, `MP-334`
- `dev/active/devctl_reporting_upgrade.md`
- `dev/active/autonomous_control_plane.md` (Phases 1-2/5/6)

### Phase D - Theme/Visual Platform Completion

1. Finish resolver-first Theme Studio migration.
2. Keep visual parity gates strict before any GA expansion.

Mapped scopes:

- `MP-148..MP-182`
- `dev/active/theme_upgrade.md`

### Phase E - Memory + Action Studio Platform

1. Build semantic memory + retrieval + action governance without runtime regressions.
2. Promote only with quality, isolation, and compaction gates passing.

Mapped scopes:

- `MP-230..MP-255`
- `dev/active/memory_studio.md`

### Phase F - Architect Controller (Rust TUI + iPhone + Agent Relay)

1. Deliver unified controller state model consumed by Rust Dev panel and phone.
2. Deliver guarded remote controls and reviewer-agent packet relay.
3. Keep branch/CI/replay policy gates mandatory before promote/write actions.

Mapped scopes:

- `MP-330..MP-332`, `MP-336`, `MP-338`
- `MP-340`
- `dev/active/autonomous_control_plane.md` (Phase 3 + 3.5 + 3.7 + 6.1)
- `dev/active/loop_chat_bridge.md`

### Phase G - Release Hardening + Template Extraction

1. Complete rollout soak, policy hardening, and full audit loops.
2. Extract reusable template package only after governance parity is proven.

Mapped scopes:

- `autonomous_control_plane` rollout/template phases
- release/tracker governance bundles and CI lanes.

## ADR Program Backlog (Cross-Plan, Pending)

Create these ADRs in order so agents/dev do not lose architectural scope.

1. `ADR-0027` Unified Controller State Contract:
   schema + projections (`full/compact/trace/actions`) used by TUI and phone.
2. `ADR-0028` Agent Relay Packet Protocol:
   reviewer/assistant packet format, confidence model, and evidence refs.
3. `ADR-0029` Operator Action Policy Model:
   action classes, approval gates, replay/nonce rules, and deny semantics.
4. `ADR-0030` Phone Adapter Architecture:
   SSH-first, push/SMS/chat adapters, auth boundaries, and fallback strategy.
5. `ADR-0031` Rust Dev-Panel Control-Plane Boundary:
   what stays runtime-local vs control-plane-fed; non-interference guarantees.
6. `ADR-0032` Autonomous Loop Stage Machine:
   triage/plan/fix/verify/review/promote transitions and stop conditions.
7. `ADR-0033` Autonomy Metrics + Scientific Audit Method:
   KPI definitions, experiment protocol, and promotion criteria.
8. `ADR-0034` Template Extraction Contract:
   what must be standardized before reuse across repositories.

## Phase 0 - Completed Release Stabilization (v1.0.51-v1.0.52)

- [x] MP-072 Prevent HUD/timer freeze under continuous PTY output.
- [x] MP-073 Improve IDE terminal input compatibility and hidden-HUD discoverability.
- [x] MP-074 Update docs for HUD/input behavior changes and debug guidance.
- [x] MP-075 Finalize latency display semantics to avoid misleading values.
- [x] MP-076 Add latency audit logging and regression tests for displayed latency behavior.
- [x] MP-077 Run release verification (`cargo build --release --bin voiceterm`, tests, docs-check).
- [x] MP-078 Finalize release notes, bump version, tag, push, GitHub release, and Homebrew tap update.
- [x] MP-096 Expand SDLC agent governance: post-push audit loop, testing matrix by change type, CI expansion policy, and per-push docs sync requirements.
- [x] MP-099 Consolidate overlay research into a single reference source (now consolidated under `dev/active/theme_upgrade.md`) and mirror candidate execution items in this plan.

## Phase 1 - Latency Truth and Observability

- [x] MP-079 Define and document latency terms (capture, STT, post-capture processing, displayed HUD latency).
- [x] MP-080 Hide latency badge when reliable latency cannot be measured.
- [x] MP-081 Emit structured `latency_audit|...` logs for analysis.
- [x] MP-082 Add automated tests around latency calculation behavior.
- [x] MP-097 Fix busy-output HUD responsiveness and stale meter/timer artifacts (settings lag under Codex output, stale REC duration/dB after capture, clamp meter floor to stable display bounds).
- [x] MP-098 Eliminate blocking PTY input writes in the overlay event loop so queued/thinking backend output does not stall live typing responsiveness.
- [x] MP-083 Run and document baseline latency measurements with `latency_measurement` and `dev/scripts/tests/measure_latency.sh` (`dev/archive/2026-02-13-latency-baseline.md`).
- [x] MP-084 Add CI-friendly synthetic latency regression guardrails (`.github/workflows/latency_guard.yml` + `measure_latency.sh --ci-guard`).
- [x] MP-194 Normalize HUD latency severity using speech-relative STT speed (`rtf`) while preserving absolute STT delay display and audit logging fields (`speech_ms`, `rtf`) to reduce false "slow" signals on long utterances.
- [x] MP-195 Stop forwarding malformed/fragmented SGR mouse-report escape bytes into wrapped CLI input during interrupts so raw `[<...` fragments do not leak to users.
- [x] MP-196 Expand non-speech transcript sanitization for ambient-sound hallucination tags (`siren`, `engine`, `water` variants) before PTY delivery.
- [x] MP-111 Add governance hygiene automation for archive/ADR/script-doc drift (`python3 dev/scripts/devctl.py hygiene`) and codify archive/ADR lifecycle policy.
- [x] MP-122 Prevent mutation-lane timeout by sharding scheduled `cargo mutants` runs and enforcing one aggregated score across shards.

## Phase 2 - Overlay Quick Wins

- [x] MP-085 Voice macros and custom triggers (`.voiceterm/macros.yaml`).
- [x] MP-086 Runtime macros ON/OFF toggle (settings state + transcript transform gate).
- [x] MP-087 Restore baseline send-mode semantics (`auto`/`insert`) without an extra review-first gate.
- [x] MP-112 Add CI voice-mode regression lane for macros-toggle and send-mode behavior (`.github/workflows/voice_mode_guard.yml`).
- [x] MP-088 Persistent user config (`~/.config/voiceterm/config.toml`) for core preferences (landed runtime load/apply/save flow with CLI-precedence guards, explicit-flag detection for default-valued args, and status-state restore coverage for macros toggle).

## Phase 2A - Visual HUD Sprint (Current Priority)

- [x] MP-101 Add richer HUD telemetry visuals (sparkline/chart/gauge) with bounded data retention.
- [x] MP-100 Add animation transition framework for overlays and state changes (TachyonFX or equivalent).
- [x] MP-054 Optional right-panel visualization modes in minimal HUD.
- [x] MP-105 Add adaptive/contextual HUD layouts and state-driven module expansion.
- [x] MP-113 Tighten startup splash ergonomics and IDE compatibility (shorter splash duration, reliable teardown in IDE terminals, corrected startup tagline centering, and better truecolor detection for JetBrains-style terminals).
- [x] MP-114 Polish startup/theme UX in IDE terminals (remove startup top-gap, keep requested themes on 256-color terminals, and render Theme Picker neutral when current theme is `none`).
- [x] MP-115 Stabilize terminal compatibility regressions (drop startup arrow escape noise during boot, suppress Ctrl+V idle pulse dot beside `PTT`, and restore conservative ANSI fallback when truecolor is not detected).
- [x] MP-116 Fix JetBrains terminal HUD duplication by hardening scroll-region cursor restore semantics.
- [x] MP-117 Prevent one-column HUD wrap in JetBrains terminals (status-banner width guard + row truncation safety).
- [x] MP-118 Harden cross-terminal HUD rendering and PTY teardown paths (universal one-column HUD safety margin, writer-side row clipping to terminal width, and benign PTY-exit write error suppression on shutdown).
- [x] MP-119 Restore the stable `v1.0.53` writer/render baseline for Full HUD while retaining the one-column layout safety margin to recover reliable IDE terminal rendering.
- [x] MP-120 Revert unstable post-release scroll-region protection changes that reintroduced severe Full HUD duplication/corruption during active Codex output.
- [x] MP-121 Harden JetBrains startup/render handoff by auto-skipping splash in IDE terminals and clearing stale HUD/overlay rows on resize before redraw.
- [x] MP-123 Harden PTY/IPC backend teardown to signal process groups and reap child processes, with regression tests that verify descendant cleanup.
- [x] MP-183 Add a PTY session-lease guard that reaps backend process groups from dead VoiceTerm owners before spawning new sessions, without disrupting concurrently active sessions.
- [x] MP-190 Restore Full HUD shortcuts-row trailing visualization alignment so the right panel remains anchored to the far-right corner in full-width layouts.
- [x] MP-124 Add Full-HUD border-style customization (including borderless mode) and keep right-panel telemetry explicitly user-toggleable to `Off`.
- [x] MP-125 Fix HUD right-panel `Anim only` behavior so idle state keeps a static panel visible instead of hiding the panel until recording.
- [x] MP-126 Complete product/distribution naming rebrand to VoiceTerm across code/docs/scripts/app launcher, and add a PyPI launcher package scaffold (`pypi/`) for `voiceterm`.
- [x] MP-139 Tighten user-facing docs information architecture (entrypoint clarity, navigation consistency, and guide discoverability).
- [x] MP-104 Add explicit voice-state visualization (idle/listening/processing/responding) with clear transitions.
- [x] MP-055 Quick theme switcher in settings.
- [x] MP-102 Add toast notification center with auto-dismiss, severity, and history review (landed runtime status-to-toast ingestion with severity mapping, `Ctrl+N` notification-history overlay toggle, periodic auto-dismiss/re-render behavior, and input/parser/help/docs coverage for toast-history control flow).
- [x] MP-226 Fix Claude-mode command/approval prompt occlusion in active overlay sessions: when Claude enters interactive Bash approval or sandbox permission prompts (for example `Do you want to proceed?` while running `Bash(...)` or cross-worktree read prompts), VoiceTerm HUD/overlay rows can obscure prompt text and controls; implement a Claude-specific prompt-state rendering policy (overlay layering, temporary HUD suppression/resume, or reserved prompt-safe rows) so prompts remain readable/actionable without losing runtime status clarity, with non-regression validation for Codex, Cursor, and JetBrains terminals. (2026-02-27 follow-up hardening: suppression now targets high-confidence interactive approval/permission contexts only; low-confidence generic/composer text no longer triggers HUD suppression to avoid disappear/reappear flicker during normal Codex runs. Additional 2026-02-27 resilience update: terminal row/col resolution now normalizes zero-size IDE probes and writer startup redraw uses normalized size fallback so HUD resume/startup does not wait for a keypress. 2026-02-28 targeted overlay follow-up: numbered approval-card detection now suppresses HUD for sparse `1/2/3` option cards, suppression transitions synchronize normalized geometry with writer redraw, and Cursor transition pre-clear now scrubs stale border fragments during `ClearStatus` handoff paths. 2026-02-28 anti-cycle follow-up: Cursor non-rolling hosts no longer engage suppression from tool-activity text alone, and now use explicit/numbered approval-card hints for suppression engagement to prevent keypress-triggered HUD disappearance in normal composer flow.)
  - Repro note (2026-02-19): issue severity appears higher for local/worktree permission prompts during multi-tool explore batches (`+N more tool uses`), while some single-command Claude prompt flows appear acceptable.
  - Additional repro signal (2026-02-19): severity appears correlated with vertical UI density (long wrapped absolute command paths, larger active task list sections, and multi-line tool-batch summaries), suggesting row-budget/stacking pressure near bottom prompt rows.
  - Repro note (2026-02-19, screenshot evidence): during parallel/background-agent orchestration in Claude, long "workaround options" + permission-wall text can exceed available row budget and push prompt/action rows into unreadable overlap, while equivalent Codex sessions remain readable; treat this as a Claude-specific layout compaction/reserved-row failure case.
  - Evidence to capture per repro: terminal rows/cols, HUD mode/style, prompt type (single-command approval vs local/worktree permission), command preview line-wrap count, tool-batch summary presence (`+N more tool uses`), and screenshot before/after prompt render.
  - 2026-02-28 diagnostic follow-up: added gated Claude HUD tracing (`VOICETERM_DEBUG_CLAUDE_HUD=1`) across prompt-occlusion transitions and writer redraw/defer decisions to isolate a new Cursor+Claude normal-typing regression where HUD disappears after the first keypress (non-approval flow).
  - 2026-02-28 writer follow-up: tightened tool-activity suppression overmatch for plain transcript headings, added explicit stale-banner-anchor clearing in writer redraw, and added a short delayed Cursor+Claude typing repair redraw path to recover minimal-HUD line clobber without reintroducing per-keystroke flash.
  - 2026-02-28 minimal-HUD follow-up: Cursor+Claude typing-hold deferral now bypasses for active one-row HUD frames so minimal-HUD redraw is not postponed behind typing bursts, while full-HUD deferral policy remains unchanged.
  - 2026-02-28 traceability follow-up: Cursor+Claude writer debug logs now emit explicit user-input activity scheduling and enhanced-status render decisions (`prev/next banner height`, `hud_style`, `prompt_suppressed`), and pre/post transition flags are now computed from pre-apply state to prevent false-no-change traces while reproducing the remaining disappearance/overwrite regressions.
  - 2026-02-28 repaint follow-up: pre-clear transition redraws now force full banner repaint (no previous-line diff reuse) in Cursor+Claude paths, with explicit `transition redraw mode` debug traces to prove redraw mode on failing keypress/tool-output sequences.
  - 2026-02-28 non-rolling approval-window follow-up: Cursor non-rolling prompt suppression now keeps a short ANSI-stripped rolling approval window so split approval cards (`Do you want to proceed?` + later `1/2/...` options) still suppress HUD deterministically, while debug traces now log chunk/window match sources (`chunk_*` vs `window_*`) to distinguish real prompt hits from missed detections. Writer repair scheduling was also hardened so future Cursor+Claude repair deadlines are not cleared by unrelated redraws before they fire, reducing one-row HUD “disappear until refresh” loops during typing.
  - 2026-02-28 non-rolling release-gate + row-budget tracing follow-up: Cursor non-rolling suppression now requires explicit input-resolution arming plus drained approval window before release (prevents debounce-only unsuppress while approval context remains live), prompt-context fallback markers now keep detection active when backend label routing is noisy (`Tool use`, `Claude wants to`, `What should Claude do instead?`), Cursor Claude extra gap rows increased (`8 -> 10`), and `apply_pty_winsize` debug traces now emit backend/mode/rows/cols/reserved-rows/PTY-rows so overlay overlap can be diagnosed from logs instead of screenshots alone.
  - 2026-02-28 high-confidence guard follow-up: explicit/numbered approval hints now promote `prompt_guard_enabled` in non-rolling paths, so approval cards can suppress HUD even when backend-label guard signals are noisy; runtime debug chunk logs now include `backend_label` + `prompt_guard` booleans for direct branch tracing; non-rolling suppression semantics are now covered by deterministic thread-local test overrides (no shared env mutation races under parallel test execution).
  - 2026-03-01 stress-loop traceability follow-up: added deterministic Cursor+Claude stress artifact capture under `dev/reports/audits/claude_hud_stress/*` (frame snapshots + log counters + anomaly summaries), narrowed non-rolling release-arm consumption to substantial post-input activity, deferred release-arm relatch on window-only stale hints, and hardened writer typing-hold urgency detection for post-`ClearStatus` suppression transitions so approval/HUD churn can be diagnosed via logs and artifact IDs instead of screenshot-only loops. Current status remains partial (approval overlap reduced but not eliminated; see `dev/audits/2026-02-27-terminal-overlay-regression-audit.md` A2.10).
  - 2026-03-01 rapid-approval hold + frame/log correlation follow-up: non-rolling input-resolution now arms an explicit sticky suppression hold window to avoid unsuppress gaps between consecutive approval cards, and `claude_hud_stress.py` now records frame timestamps plus bottom-row HUD visibility and correlates each frame to suppression-transition/redraw-commit log events for deterministic overlap attribution (see `dev/audits/2026-02-27-terminal-overlay-regression-audit.md` A2.11). Local stress execution in this sandbox remains blocked by detached `screen` session startup failure, so fresh artifact generation is still pending a full terminal host.
  - 2026-03-01 wrapped-approval depth + anomaly-capture follow-up: expanded non-rolling approval scan depth (`2048 -> 8192` bytes, `12 -> 64` lines) so long wrapped option cards in Cursor prompt UIs continue matching numbered approval semantics, and added explicit anomaly logging for `explicit approval hint seen without numbered-match` to surface residual detector misses in runtime logs instead of relying on screenshots alone (see `dev/audits/2026-02-27-terminal-overlay-regression-audit.md` A2.12).
  - 2026-03-01 overlay occlusion closure follow-up: PTY startup winsize is now derived from measured terminal geometry before backend spawn (HUD-aware from frame 1), writer HUD rendering now fences PTY scrolling above reserved HUD rows via scroll-region controls, and resize transitions now force immediate redraw after pre-clear so grow/shrink cycles do not leave input rows hidden until another keypress.
  - 2026-03-01 JetBrains+Claude rendering follow-up: status/banner clear-to-EOL paths now reset ANSI attributes before trimming trailing columns so dark HUD style attributes cannot leak into typed prompt text, and JetBrains Claude extra gap rows now default to `2` for safer startup prompt/HUD separation.
- [x] MP-285 Standardize HUD policy across all backends: removed Gemini-specific compaction logic to ensure a consistent 4-row Full HUD experience and unified flicker-reduction behavior across Codex, Claude, and Gemini backends.

## Phase 2B - Rust Hardening Audit (Pre-Execution + Implementation)

- [x] MP-127 Replace IPC `/exit` hard process termination with graceful shutdown orchestration and teardown event guarantees (FX-001).
- [x] MP-128 Add explicit runtime ownership and bounded shutdown/join semantics for overlay writer/input threads (FX-002).
- [x] MP-129 Add voice-manager lifecycle hardening for quit-while-recording paths, including explicit stop/join policy and tests (FX-003).
- [x] MP-130 Consolidate process-group signaling/reaping helpers into one canonical utility with invariants tests (FX-004).
- [x] MP-131 Add security/supply-chain CI lane with policy thresholds and failing gates for high-severity issues (FX-005).
- [x] MP-132 Add explicit security posture/threat-model documentation and risky flag guidance (including permission-skip behavior) (FX-006).
- [x] MP-133 Enforce IPC auth timeout + cancellation semantics using tracked auth start timing (FX-007).
- [x] MP-134 Replace IPC fixed-sleep scheduling with event-driven receive strategy to reduce idle CPU jitter (FX-008).
- [x] MP-135 Decompose high-risk event-loop transition/wiring complexity to reduce change blast radius (FX-009).
- [x] MP-136 Establish unsafe-governance checklist for unsafe hotspots with per-invariant test expectations (FX-010).
- [x] MP-137 Add property/fuzz coverage lane for parser and ANSI/OSC boundary handling (FX-011).
- [x] MP-138 Enforce audit/master-plan traceability updates as a mandatory part of each hardening fix (FX-012).
- [x] MP-152 Consolidate hardening governance to `MASTER_PLAN` as the only active tracker: archive `RUST_GUI_AUDIT_2026-02-15.md` under `dev/archive/` and retire dedicated audit-traceability CI/tooling.

## Phase 2C - Theme System Upgrade (Architecture + Guardrails)

Theme Studio execution gate: MP-148..MP-182 are governed by the checklist in
this section. A Theme Studio MP may move to `[x]` only with documented pass
evidence for its mapped gates.

Theme/modularization integration rule: when refactors or fixes touch visual
runtime modules (`theme/*`, `theme_ops.rs`, `theme_picker.rs`, `status_line/*`,
`hud/*`, `writer/*`, `help.rs`, `banner.rs`), update or add the
corresponding `MP-148+` item here in `MASTER_PLAN` and attach mapped
`TS-G*` gate evidence from this section.

Settings-vs-Studio ownership matrix:

| Surface | Owner |
|---|---|
| Theme tokens/palettes, borders, glyph/icon packs, layout/motion behavior, visual state scenes, notification visuals, command-palette/autocomplete visuals | Theme Studio |
| Auto-voice/send-mode/macros, sensitivity/latency display mode, mouse mode, backend/pipeline, close/quit operations | Settings |
| Quick theme cycle and picker shortcuts | Shared entrypoint; deep editing still routes to Theme Studio |

Theme Studio Definition of Done (authoritative checklist):

| Gate | Pass Criteria | Fail Criteria | Required Evidence |
|---|---|---|---|
| `TS-G01 Ownership` | Theme Studio vs Settings ownership matrix is implemented and documented. | Any deep visual edit path remains in Settings post-migration. | Settings menu tests + docs diff. |
| `TS-G02 Schema` | `StylePack` schema/version/migration tests pass for valid + invalid inputs. | Parsing/migration panic, silent drop, or invalid pack applies without fallback. | Unit tests for parse/validate/migrate + fallback tests. |
| `TS-G03 Resolver` | All render paths resolve styles through registry/resolver APIs. | Hardcoded style constants bypass resolver on supported surfaces. | Coverage + static policy gate outputs. |
| `TS-G04 Component IDs` | Every renderable component/state has stable style IDs and defaults. | Unregistered component/state renders in runtime. | Component registry parity tests + snapshots. |
| `TS-G05 Studio Controls` | Every persisted style field is editable in Studio. | Any persisted field has no Studio control mapping. | Studio mapping parity test results. |
| `TS-G06 Snapshot Matrix` | Snapshot suites pass for widths, states, profiles, and key surfaces. | Layout overlap/wrap/clipping regressions vs expected fixtures. | Snapshot artifacts for narrow/medium/wide + state variants. |
| `TS-G07 Interaction UX` | Keyboard-only and mouse-enhanced flows both work with correct focus/hitboxes. | Broken focus order, unreachable controls, or hitbox mismatch. | Interaction integration tests + manual QA checklist output. |
| `TS-G08 Edit Safety` | Apply/save/import/export/undo/redo/rollback flows are deterministic. | User edits can be lost/corrupted or cannot be reverted safely. | End-to-end workflow tests across restart boundaries. |
| `TS-G09 Capability Fallback` | Terminal capability detection + fallback chains behave as specified. | Unsupported capability path crashes or renders unreadable output. | Compatibility matrix tests (truecolor/ansi, graphics/no-graphics). |
| `TS-G10 Runtime Budget` | Render/update paths remain within bounded allocation/tick budgets. | Unbounded buffers, allocation spikes, or frame-thrash in hot paths. | Perf/memory checks + regression benchmarks. |
| `TS-G11 Docs/Operator` | Architecture, usage, troubleshooting, and changelog are updated together. | User-visible behavior changes without aligned docs. | `docs-check` + updated docs references. |
| `TS-G12 Release Readiness` | Full Theme Studio GA validation bundle is green. | Any mandatory gate is missing evidence or failing. | CI report bundle + signoff checklist. |
| `TS-G13 Inspector` | Any rendered element can reveal style path and jump to Studio control. | Inspector cannot locate style ID/path for a rendered element. | Inspector integration tests + state preview tests. |
| `TS-G14 Rule Engine` | Conditional style rules are deterministic and conflict-resolved. | Rule priority conflicts or nondeterministic style outcomes. | Rule engine unit/property tests + scenario snapshots. |
| `TS-G15 Ecosystem Packs` | Third-party widget packs are allowlisted, version-compatible, and parity-mapped. | Dependency added without compatibility matrix or style/studio parity mapping. | Compatibility matrix + parity tests + allowlist audit. |

Theme Studio MP-to-gate mapping:

| MP | Required Gates |
|---|---|
| `MP-148` | `TS-G01`, `TS-G11` |
| `MP-149` | `TS-G02`, `TS-G06`, `TS-G09` |
| `MP-150` | `TS-G02`, `TS-G03` |
| `MP-151` | `TS-G11` |
| `MP-161` | `TS-G03`, `TS-G06`, `TS-G07` |
| `MP-162` | `TS-G03`, `TS-G05` |
| `MP-163` | `TS-G03` |
| `MP-172` | `TS-G04`, `TS-G06` |
| `MP-174` | `TS-G03`, `TS-G05`, `TS-G06` |
| `MP-175` | `TS-G09`, `TS-G15` |
| `MP-176` | `TS-G09`, `TS-G06` |
| `MP-179` | `TS-G15` |
| `MP-180` | `TS-G15`, `TS-G05`, `TS-G06` |
| `MP-182` | `TS-G14`, `TS-G05`, `TS-G06` |
| `MP-164` | `TS-G07` |
| `MP-165` | `TS-G01`, `TS-G07` |
| `MP-166` | `TS-G05`, `TS-G08`, `TS-G07` |
| `MP-167` | `TS-G06`, `TS-G09`, `TS-G10`, `TS-G11`, `TS-G12` |
| `MP-173` | `TS-G03`, `TS-G05`, `TS-G15` |
| `MP-177` | `TS-G15`, `TS-G05` |
| `MP-178` | `TS-G13`, `TS-G07` |
| `MP-181` | `TS-G07`, `TS-G10` |

Theme Studio mandatory verification bundle (per PR):

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py docs-check --user-facing`
- `python3 dev/scripts/devctl.py hygiene`
- `cd rust && cargo test --bin voiceterm`
- use `.github/PULL_REQUEST_TEMPLATE/theme_studio.md` for `TS-G01`..`TS-G15` evidence capture.

- [x] MP-148 Activate the Theme Studio phased track in `MASTER_PLAN` and lock the IA boundary: dedicated `Theme Studio` mode (not `Settings -> Studio`) plus Settings-vs-Studio ownership matrix (landed gate catalog + MP-to-gate map + ownership matrix directly in Phase 2C so visual modularization/fix work now maps to one canonical tracker).
- [x] MP-149 Implement Theme Upgrade Phase 0 safety rails (golden render snapshots, terminal compatibility matrix coverage, and style-schema migration harness) before any user-visible editor expansion (landed style-schema migration harness in `theme/style_schema.rs`, terminal capability matrix tests in `color_mode`, and golden snapshot-matrix coverage for startup banner, theme picker, and status banner render outputs).
- [x] MP-150 Implement Theme Upgrade Phase 1 style engine foundation (`StylePack` schema + resolver + runtime), preserving current built-in theme behavior and startup defaults (landed runtime resolver scaffold `theme/style_pack.rs`, routed `Theme::colors()` through resolver with palette-parity regression tests, enabled runtime schema parsing/migration (`theme/style_schema.rs`) for pack payload ingestion, and hardened schema-version mismatch/invalid-payload fallback to preserve base-theme palettes instead of dropping to `none`).
- [x] MP-151 Ship docs/architecture updates for the new theme system (`dev/ARCHITECTURE.md`, `guides/USAGE.md`, `guides/TROUBLESHOOTING.md`, `dev/CHANGELOG.md`) in lockstep with implementation, including operator guidance, settings-migration guidance, and fallback behavior (landed runtime resolver path docs, schema payload operator guidance, explicit settings-migration notes, and invalid-pack fallback behavior across architecture/usage/troubleshooting/changelog docs).

## Phase 2D - Visual Surface Expansion (Theme Studio Prerequisite)

- [ ] MP-161 Execute a visual-first runtime pass before deep Studio editing: with MP-102 complete, promote MP-103, MP-106, MP-107, MP-108, and MP-109 from Backlog into active execution order with non-regression gates (in progress: toast-history overlay row-width accounting and title rendering were hardened so unicode/ascii glyph themes keep border alignment without stale right-edge artifacts).
- [ ] MP-162 Extend `StylePack` schema/resolver so each runtime visual surface is style-pack addressable (widgets/graphs, toasts, voice-state scenes, command palette, autocomplete, dashboard surfaces), even before all Studio pages ship (in progress: schema/resolver now supports runtime visual overrides for border glyph sets, indicator glyph families, and glyph-set profile selection (`glyphs`: `unicode`/`ascii`) via style-pack payloads, including compact/full/minimal/hidden processing/responding indicator lanes in status rendering while preserving default processing spinner animation unless explicitly overridden).
- [x] MP-163 Add explicit coverage tests/gates that fail if new visual runtime surfaces bypass theme resolver paths with hardcoded style constants (landed `theme::tests::runtime_sources_do_not_bypass_theme_resolver_with_palette_constants`, a source-policy gate that scans runtime Rust modules and fails when `THEME_*` palette or `BORDER_*` border constants are referenced outside theme resolver/style-ownership allowlist files).
- [ ] MP-172 Add a styleable component registry and state-matrix contract for all renderable control surfaces (buttons, tabs, lists, tables, trees, scrollbars, modal/popup/tooltip, input/caret/selection) with schema + resolver + snapshot coverage.
- [ ] MP-174 Migrate existing non-HUD visual surfaces into `StylePack` routing (startup splash/banner, help/settings/theme-picker chrome, calibration/mic-meter visuals, progress bars/spinners, icon/glyph sets) so no current visual path is left outside Theme Studio ownership (in progress: processing/progress spinner rendering paths now resolve through theme/style-pack indicators instead of hardcoded frame constants, glyph-family routing now drives HUD queue/latency/meter symbols + status-line waveform placeholders/pulse dots + progress bar/block/bounce glyphs, `components.progress_bar_family` now routes progress/meter glyph profiles through style-pack resolution, audio-meter calibration/waveform rendering resolves bar/wave/marker glyphs from the shared theme profile, overlay chrome/footer/slider glyphs across help/settings/theme-picker now route through the active glyph profile with footer close hit-testing parity for unicode/ascii separators, startup banner/footer separators now honor glyph-set overrides (`unicode`/`ascii`) across full/compact/minimal banner variants, explicit spinner-style overrides now fall back to ASCII-safe animation frames when glyph profile is ASCII, theme-switch interactions now surface explicit style-pack lock state (read-only/dimmed picker + locked status messaging) when schema payload `base_theme` is active, and component-level border routing now resolves `components.overlay_border` across overlay surfaces including transcript-history plus `components.hud_border` for Full-HUD `Theme` border mode through style-pack resolver paths.)
- [x] MP-175 Add a framework capability matrix + parity gate for shipped framework versions (Ratatui widget/symbol families and Crossterm color/input/render capabilities, including synchronized updates + keyboard enhancement flags), and track upgrade deltas before enabling new Studio controls (landed `theme/capability_matrix.rs` with `RatatuiWidget`/`RatatuiSymbolFamily`/`CrosstermCapability` enums, `FrameworkCapabilitySnapshot` pinned at ratatui 0.26 + crossterm 0.27, `check_parity()` gate detecting unregistered widgets and unmapped symbols, `compute_upgrade_delta()` for version transition tracking, `theme_capability_compatible()` for theme/terminal validation, and 18 passing tests covering snapshot parity, delta detection, and breaking-change gates; TS-G09 + TS-G15 evidence).
- [x] MP-176 Implement terminal texture/graphics capability track (`TextureProfile` + adapter policy): symbol-texture baseline for all terminals plus capability-gated Kitty/iTerm2 image paths with enforced fallback chain tests (landed `theme/texture_profile.rs` with `TextureTier` fallback chain (KittyGraphics > ITermInlineImage > Sixel > SymbolTexture > Plain), `SymbolTextureFamily` enum (shade/braille/block/line), `TextureProfile` with max/active tier + terminal detection, `TerminalId` enum covering Kitty/iTerm2/WezTerm/Foot/Mintty/VsCode/Cursor/JetBrains/Alacritty/Warp/Generic/Unknown, environment-based detection via TERM_PROGRAM/TERMINAL_EMULATOR/KITTY_WINDOW_ID/ITERM_SESSION_ID, `resolve_texture_tier()` enforcing fallback chain, and `texture_profile_with_override()` for style-pack tier overrides; 20 passing tests covering fallback ordering, tier resolution, terminal detection, and profile construction; TS-G09 + TS-G06 evidence).
- [x] MP-179 Add dependency baseline strategy for Theme Studio ecosystem packs (Ratatui/Crossterm version pin policy + compatibility matrix + staged upgrade plan) so third-party widget adoption does not fragment resolver/studio parity (landed `theme/dependency_baseline.rs` with `DependencyPin` structs for ratatui 0.26 and crossterm 0.27, `CompatibilityEntry`/`CompatibilityStatus` matrix covering tui-textarea/tui-tree-widget/throbber-widgets-tui/tui-popup/tui-scrollview/tui-big-text/tui-prompts/ratatui-image/tuirealm with per-dep ratatui+crossterm compat status, `UpgradeStep` staged plan (crossterm 0.28 before ratatui 0.27), `check_crate_compatibility()`/`check_pack_compatibility()` policy gates blocking unknown/incompatible crates, and `validate_pin_against_cargo()` for CI pin verification; 19 passing tests covering pin validation, matrix queries, compatibility semantics, and upgrade ordering; TS-G15 evidence).
- [x] MP-180 Pilot a curated widget-pack integration lane (`tui-widgets` family, `tui-textarea`, `tui-tree-widget`, `throbber-widgets-tui`) under style-ID/allowlist gates, with parity tests before feature flags graduate (landed `theme/widget_pack.rs` with `PackMaturity` lifecycle (Candidate > Pilot > Graduated > Retired), `WidgetPackEntry` registry with per-pack `StyleIdScope` namespaces and `ParityRequirement` gates, 6-entry `WIDGET_PACK_REGISTRY` (tui-textarea/tui-tree-widget/throbber-widgets-tui at Pilot; tui-popup/tui-scrollview/tui-big-text at Candidate), `GraduationCheckResult`-based gate blocking pilot packs with unmet parity requirements, `find_pack()`/`active_packs()`/`packs_at_maturity()` queries, `style_id_is_pack_owned()`/`owning_pack_for_style_id()` ownership resolution, and scope overlap detection; 21 passing tests covering registry integrity, scope isolation, maturity ordering, graduation gates, and ownership queries; TS-G15 + TS-G05 + TS-G06 evidence).
- [x] MP-182 Add `RuleProfile` no-code visual automation (threshold/context/state-driven style overrides) with deterministic priority semantics, preview tooling, and snapshot coverage (landed `theme/rule_profile.rs` with `RuleCondition` tagged-union supporting VoiceState/Threshold/Backend/Capability/ColorMode/All/Any conditions, `ThresholdMetric` enum (queue-depth/latency-ms/audio-level-db/terminal-width/terminal-height), `StyleOverride`/`OverrideEntry` for property-level style mutations, `StyleRule` with priority-based conflict resolution and enable/disable toggle, `RuleProfile` with add/remove/toggle operations and `active_rules()` priority-sorted accessor, `evaluate_condition()`/`evaluate_rules()` engine with deterministic first-match-per-key semantics, `preview_rules()` for Studio preview tooling, `parse_rule_profile()` JSON deserialization with nested condition support, and `RuleProfileError` for duplicate/not-found rule operations; 33 passing tests covering condition evaluation, priority semantics, conflict resolution, nested conditions, JSON parsing, and preview output; TS-G14 + TS-G05 + TS-G06 evidence).

## Phase 2E - Theme Studio Delivery (After Visual Surface Expansion)

- [x] MP-164 Implement dedicated `Theme Studio` overlay mode entry points/navigation and remove deep theme editing from generic Settings flows (landed `OverlayMode::ThemeStudio` with dedicated renderer/state selection, routed `Ctrl+Y`/theme-button entrypoints and cross-overlay theme hotkey flows into Theme Studio, added keyboard/mouse navigation (`Enter` action routing to Theme Picker/close plus arrow/ESC handling), wired periodic resize rerender + PTY reserved-row budgeting for Theme Studio mode, and covered interaction/status-row updates with new event-loop/theme-studio/status-line regression tests; TS-G07 evidence: `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `cd rust && cargo test --bin voiceterm`).
- [x] MP-165 Migrate legacy visual controls out of settings list (`SettingsItem::Theme`, `SettingsItem::HudStyle`, `SettingsItem::HudBorders`, `SettingsItem::HudPanel`, `SettingsItem::HudAnimate`) so Settings keeps non-theme runtime controls only (landed by removing those rows from `SETTINGS_ITEMS`, preserving quick visual controls via `Ctrl+Y`/`Ctrl+G` theme paths plus `Ctrl+U` HUD-style cycling outside Settings).
- [ ] MP-166 Deliver Studio page control parity for all `StylePack` fields (tokens, layout, widgets, motion, behavior, notifications, command/discovery surfaces, voice-state scenes, startup/wizard/progress/texture surfaces, accessibility, keybinds, profiles) with undo/redo + rollback (in progress: Theme Studio now includes interactive visual-control rows for existing runtime styling (`HUD style`, `HUD borders`, `Right panel`, `Panel animation`) plus live `StylePack` runtime overrides for `Glyph profile`, `Indicator set`, `Progress spinner`, `Progress bars`, `Theme borders`, `Voice scene`, `Toast position`, `Startup splash`, `Toast severity`, and `Banner style`, all adjustable with Enter and Left/Right controls and live current-value labels; overlay rendering now uses settings-style `label + [ value ]` rows with selected-row highlighting, a dedicated `tip:` description row, wider studio-width clamps (`60..=82`), and footer hints that expose left/right adjustment controls; runtime style-pack override edit safety is now wired with dedicated `Undo edit`, `Redo edit`, and `Rollback edits` rows backed by bounded in-session history; deep multi-page style-pack parity (`tokens`, `layout/motion`, broader field mapping) remains pending).
- [ ] MP-167 Run Theme Studio GA validation and docs lockstep updates (snapshot matrix, terminal compatibility matrix, architecture docs, user docs, troubleshooting guidance, changelog entry).
- [ ] MP-173 Add CI policy gates for future visuals: fail if a new renderable component lacks style-ID registration, and fail if post-parity a style-pack field lacks Studio control mapping (in progress: framework capability parity now fails on any newly added Ratatui widget/symbol without registration/mapping coverage, component-registry tests now require exact inventory parity plus unique stable style IDs, and Theme Studio now enforces explicit style-pack field classification (`mapped` vs `deferred`) with the post-parity gate enabled (`STYLE_PACK_STUDIO_PARITY_COMPLETE = true`) so mapping tests now require zero deferred style-pack fields).
- [ ] MP-177 Add widget-pack extensibility parity (first-party plus allowlisted third-party widgets) so newly adopted widget families must register style IDs + resolver bindings + Studio controls before GA.
- [ ] MP-178 Add Theme Studio element inspector parity so users can select any rendered element and jump directly to component/state style controls (with state preview and style-path tracing).
- [ ] MP-181 Add advanced Studio interaction parity (resizable splits, drag/reorder, scrollview-heavy forms, large text/editor fields) with full keyboard fallback and capability-safe mouse behavior.

## Phase 3 - Overlay Differentiators

- [x] MP-090 Voice terminal navigation actions (scroll/copy/error/explain).
- [x] MP-140 Define and enforce macro-vs-navigation precedence (macros first, explicit built-in phrase escape path).
- [x] MP-141 Add Linux clipboard fallback support for voice `copy last error` (wl-copy/xclip/xsel).
- [x] MP-142 Add `devctl docs-check` commit-range mode for post-commit doc audits on clean working trees.
- [x] MP-156 Add release-notes automation (`generate-release-notes.sh`, `devctl release-notes`, `release.sh` notes-file handoff) so each tag has consistent diff-derived markdown notes for GitHub releases.
- [x] MP-144 Add macro-pack onboarding wizard hardening (expanded developer command packs, repo-aware placeholder templating, and optional post-install setup prompt).
- [x] MP-143 Decompose `voice_control/drain.rs` and `event_loop.rs` into smaller modules to reduce review and regression risk (adjacent runtime architecture debt; tracked separately from tooling-control-plane work).
  - [x] MP-143a Extract shared settings-item action dispatch in `event_loop.rs` so Enter/Left/Right settings paths stop duplicating mutation logic.
  - [x] MP-143b Split `event_loop.rs` overlay/input/output handlers into focused modules (`overlay_dispatch`, `input_dispatch`, `output_dispatch`, `periodic_tasks`) and move tests to `event_loop/tests.rs` while preserving regression coverage.
  - [x] MP-143c0 Move `voice_control/drain.rs` tests into `voice_control/drain/tests.rs` so runtime decomposition can land in smaller, reviewable slices.
  - [x] MP-143c1 Extract `voice_control/drain/message_processing.rs` for macro expansion, status message handling, and latency/preview helpers.
  - [x] MP-143c Split `voice_control/drain.rs` into transcript-delivery (`transcript_delivery.rs`), status/latency updates (`message_processing.rs`), and auto-rearm/finalize components (`auto_rearm.rs`) with unchanged behavior coverage.
- [x] MP-182 Decompose `ipc/session.rs` by extracting non-blocking codex/claude/voice/auth event processors into `ipc/session/event_processing/`, keeping command-loop orchestration in `session.rs` and preserving IPC regression coverage.
- [x] MP-170 Harden IPC test event capture isolation so parallel test runs remain deterministic under `cargo test` and `devctl check --profile ci`.
- [x] MP-091 Searchable transcript history and replay workflow (landed `Ctrl+H` overlay with bounded history storage, type-to-filter search, and replay-to-PTY integration plus event-loop/help wiring).
- [x] MP-229 Upgrade transcript-history from transcript-only snippets to source-aware conversation memory capture (`mic`/`you`/`ai`) with wider rows, selected-entry preview, control-sequence-safe search input (`\x1b[0[I`/focus noise no longer leaks into query text), non-replayable guardrails for assistant-output rows, and opt-in markdown session memory logging (`--session-memory`, `--session-memory-path`) for project-local conversation archives.
- [x] MP-199 Add wake-word runtime controls in settings/config (`OFF`/`ON`, sensitivity, cooldown), defaulting to `OFF` for release safety (landed overlay config flags `--wake-word`, `--wake-word-sensitivity`, `--wake-word-cooldown-ms`; settings overlay items + action handlers for wake toggle/sensitivity/cooldown; regression coverage in `settings_handlers::tests`).
- [x] MP-200 Add low-power always-listening wake detector runtime with explicit start/stop ownership and bounded shutdown/join semantics (landed `wake_word` runtime owner with local detector thread lifecycle, settings-driven start/stop reconciliation, bounded join timeout on shutdown, and periodic capture-active pause sync to avoid recorder contention).
- [x] MP-201 Route wake detections through the existing `Ctrl+R` capture path so wake-word and manual recording share one recording/transcription pipeline (landed shared trigger handling in `event_loop/input_dispatch.rs` so wake detections and manual `Ctrl+R` use the same start-capture path; wake detections ignore active-recording stop toggles by design).
- [x] MP-202 Add debounce and false-positive guardrails plus explicit HUD privacy indicator while wake-listening is active (landed explicit Full-HUD wake privacy badge states `Wake: ON`/`Wake: PAUSED`, plus stricter short-utterance wake phrase gating so long/background mentions are ignored before trigger delivery).
- [x] MP-203 Add wake-word regression + soak validation gates (unit/integration/lifecycle tests and long-run false-positive/latency checks) and require passing evidence before release/tag (landed deterministic wake runtime lifecycle tests via spawn-hooked listener ownership checks, expanded detection-path regression tests, long-run hotword false-positive/latency soak test, reusable guard script `dev/scripts/tests/wake_word_guard.sh`, `devctl check --profile release` wake-guard integration, and dedicated CI lane `.github/workflows/wake_word_guard.yml`).
- [x] MP-286 Add an image-capture interaction mode for Codex sessions: expose a persistent ON/OFF mode, show a concise HUD indicator, support click/hotkey capture triggers, and inject a capture prompt with saved image path into the active PTY so users can run picture-assisted chats without leaving VoiceTerm (landed `image_mode.rs` capture pipeline with platform-default command fallback + configurable `--image-capture-command`, added persistent `--image-mode` runtime toggle in CLI/settings/config, added `IMG` status badge, and routed manual trigger paths (`Ctrl+R` + rec button) to image capture only when image mode is enabled while preserving normal voice-record behavior when disabled; capture injects `Please analyze this image file: <path>` into active PTY respecting send mode (`auto` send with newline vs `insert` staged text); docs/changelog/help/flags updated in `README.md`, `QUICK_START.md`, `guides/USAGE.md`, `guides/CLI_FLAGS.md`, `dev/CHANGELOG.md`; verification evidence: `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `cd rust && cargo test --bin voiceterm`).
- [x] MP-287 Resume a scoped slice of deferred Dev Mode behind a guarded launch flag: add `--dev` activation (with `--dev-mode`/`-D` aliases), keep default runtime behavior unchanged when absent, and surface explicit in-session mode visibility for dev-only experimentation (landed guarded CLI gate `--dev` with aliases in `config/cli.rs`, wired runtime state to `StatusLineState`, and added a `DEV` Full-HUD badge path so guarded mode is explicit only when enabled; default launch behavior remains unchanged when flag is absent; docs/changelog/help groups updated in `README.md`, `QUICK_START.md`, `guides/USAGE.md`, `guides/CLI_FLAGS.md`, `dev/CHANGELOG.md`, and `custom_help.rs`; verification evidence: `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `cd rust && cargo test --bin voiceterm`).
- [x] MP-288 Start deferred Dev Mode foundation by introducing a shared `rust/src/devtools/` core (stable event schema + bounded in-memory session aggregator) and wiring guarded `--dev` runtime capture events into that shared model without changing non-dev runtime behavior (landed new shared `voiceterm::devtools` module with schema-versioned `DevEvent` model + bounded `DevModeStats` ring buffer/session snapshot aggregation in `rust/src/devtools/events.rs` and `rust/src/devtools/state.rs`, exported via `rust/src/devtools/mod.rs` and `rust/src/lib.rs`; runtime bridge now instantiates guarded in-memory dev stats only when `--dev` is enabled (`main.rs`) and records transcript/empty/error voice-job events from the existing drain path without affecting default mode (`event_state.rs`, `event_loop.rs`, `voice_control/drain.rs`); verification evidence: `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `cd rust && cargo test --bin voiceterm`).
- [x] MP-289 Add guarded Dev Mode logging controls and on-disk event persistence: introduce `--dev-log` + `--dev-path`, enforce `--dev` guardrails, and append captured dev events to session JSONL files under the configured dev path without changing non-dev behavior (landed guarded CLI flags `--dev-log` and `--dev-path` in `config/cli.rs` with startup validation gates in `main.rs` (`--dev-log`/`--dev-path` now require `--dev`, and `--dev-path` requires `--dev-log`), added shared dev-event JSONL persistence in `rust/src/devtools/storage.rs` (`DevEventJsonlWriter`, per-session `session-*.jsonl` files under `<dev-root>/sessions/`, default dev root `$HOME/.voiceterm/dev` with `<cwd>/.voiceterm/dev` fallback), and wired runtime logging through the existing guarded voice-drain path so captured dev events append on transcript/empty/error messages only when guarded logging is enabled (`event_state.rs`, `event_loop.rs`, `voice_control/drain.rs`); default non-dev runtime behavior remains unchanged; docs/help/changelog updated in `guides/CLI_FLAGS.md`, `guides/USAGE.md`, `README.md`, `QUICK_START.md`, `custom_help.rs`, and `dev/CHANGELOG.md`; verification evidence: `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `cd rust && cargo test --bin voiceterm`).
- [x] MP-290 Extend Dev CLI reporting with guarded Dev Mode session telemetry summaries: add optional `--dev-logs` support to `devctl status`/`devctl report` (plus `--dev-root` and `--dev-sessions-limit`) so maintainers can inspect recent `session-*.jsonl` event counts/latency/error summaries without opening raw files (landed `collect_dev_log_summary()` in `dev/scripts/devctl/collect.py`, wired CLI flags in `dev/scripts/devctl/cli.py`, rendered markdown/json summary blocks in `dev/scripts/devctl/commands/status.py` and `dev/scripts/devctl/commands/report.py`, and added regression coverage in `dev/scripts/devctl/tests/test_collect_dev_logs.py`, `dev/scripts/devctl/tests/test_status.py`, and `dev/scripts/devctl/tests/test_report.py`; verification evidence: `python3 -m unittest dev.scripts.devctl.tests.test_collect_dev_logs dev.scripts.devctl.tests.test_status dev.scripts.devctl.tests.test_report`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`).
- [x] MP-291 Add a guarded `Ctrl+D` Dev panel overlay for `--dev` sessions: landed new `dev_panel.rs` formatter/render contract (read-only guard/logging/session-counter view), added `InputEvent::DevPanelToggle` parsing for raw `Ctrl+D` (`0x04`) and CSI-u `Ctrl+D`, wired guarded toggle behavior (`--dev` opens/closes panel; non-dev forwards `Ctrl+D` EOF byte to PTY so legacy behavior is preserved), introduced `OverlayMode::DevPanel` rendering/open/close/resize/mouse/reserved-row handling (`event_loop.rs`, `overlay_dispatch.rs`, `periodic_tasks.rs`, `overlay_mouse.rs`, `terminal.rs`, `overlays.rs`), and updated shortcut/help docs (`help.rs`, `guides/USAGE.md`, `guides/CLI_FLAGS.md`, `README.md`, `QUICK_START.md`, `dev/CHANGELOG.md`); verification evidence: `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `cd rust && cargo check --bin voiceterm`, `cd rust && cargo test --bin voiceterm`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [x] MP-295 Harden prompt-occlusion guardrails for Codex/Claude reply boxes: extend `prompt/claude_prompt_detect.rs` detection beyond approval-only patterns to include reply/composer prompt markers (including Unicode prompt glyphs and Codex command-composer hint text), enable the guard for both Codex and Claude backend labels during startup (`main.rs`), preserve zero-row HUD suppression + PTY row-budget restore behavior when suppression toggles (`prompt/mod.rs`, `event_loop` suppression path), and keep reply/composer suppression active while users type (clear only on submit/cancel input instead of every typed byte); docs/changelog updated in `guides/TROUBLESHOOTING.md`, `dev/ARCHITECTURE.md`, and `dev/CHANGELOG.md`; verification evidence: `cd rust && cargo test claude_prompt_detect --bin voiceterm`, `cd rust && cargo test reply_composer_ --bin voiceterm`, `cd rust && cargo test set_claude_prompt_suppression_updates_pty_row_budget --bin voiceterm`, `cd rust && cargo test periodic_tasks_clear_stale_prompt_suppression_without_new_output --bin voiceterm`, `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [ ] MP-301 Investigate intermittent wake/send reliability for real-world speech variants (for example `hate codex`, `hate cloud`, and while-speaking submit attempts) using targeted matcher tests plus transcript-level debug evidence.
  - [x] Initial slice: expand wake alias/send-intent coverage (`hate`/`pay` -> `hey`, `cloud`/`clog` -> `claude`, plus `send it` / `sending` / `sand`) and emit wake transcript decision traces in debug logs (`voiceterm --logs --log-content`).
  - [x] Reliability slice (2026-02-27): align wake-listener VAD threshold to live mic-sensitivity baseline (plus wake headroom) so wake detection tracks the same voice setup users already tuned for normal capture; also relaxed short wake-capture bounds (`min speech`, `lookback`, `silence tail`) and expanded `claude` alias normalization (`claud`, `clawed`) for lower-effort phrase pickup without shouting.
  - [ ] Follow-up slice: collect reproducible field log samples and tune mid-utterance submit heuristics without increasing false positives from background conversation.

## Phase 3B - Tooling Control Plane Consolidation

- [x] MP-157 Execute tooling-control-plane consolidation (archived at `dev/archive/2026-02-17-tooling-control-plane-consolidation.md`): implement `devctl ship`, deterministic step exits, dry-run behavior, machine-readable step reports, and adapter conversion for release entry points.
- [x] MP-158 Harden `devctl docs-check` policy enforcement so docs requirements are change-class aware and deprecated maintainer command references are surfaced as actionable failures.
- [x] MP-159 Add a dedicated tooling CI quality lane for `devctl` command behavior and maintainer shell-script integrity (release, release-notes, PyPI, Homebrew helpers).
- [x] MP-160 Canonicalize maintainer docs and macro/help surfaces to `devctl` first (`AGENTS.md`, `dev/DEVELOPMENT.md`, `dev/scripts/README.md`, maintainer macro packs, and `Makefile` help), keeping legacy wrappers documented as transitional adapters.
- [x] MP-230 Expand docs-governance control plane and process traceability: enforce strict tooling docs checks plus conditional strict user-facing docs checks in CI, add markdown/image/CLI-flag integrity guards, block accidental root `--*` artifact files, and document handoff/source-of-truth workflow for both human and AI contributors.
- [x] MP-239 Reorganize `AGENTS.md` into an agent-first execution router (task classes, context packs, normal-push vs release workflows, branch sync policy, command bundles, and explicit autonomy/guardrail rules) so AI contributors can deterministically choose the right docs, tools, and checks for each task.
- [x] MP-245 Refine `AGENTS.md` and `dev/DEVELOPMENT.md` into an index-first, user-story-driven execution system: add explicit start-up bootstrap steps, dirty-tree protocol, single-source command bundles, CI lane mapping by risk/path, release version-parity checks (`Cargo.toml` + `pyproject.toml` + macOS `Info.plist` + changelog) with a dedicated parity guard (`dev/scripts/checks/check_release_version_parity.py`), add an AGENTS-structure guard (`dev/scripts/checks/check_agents_contract.py`), and add an active-plan registry/sync guard (`dev/scripts/checks/check_active_plan_sync.py` + `dev/active/INDEX.md`) so SOP/router/bundle and active-doc discovery contracts fail early in local/CI governance checks.
- [x] MP-256 Add an orphaned-test process guardrail to tooling governance by extending `devctl hygiene` to detect leaked `target/debug/deps/voiceterm-*` binaries (error on detached `PPID=1` candidates, warning on active runs), then harden `devctl check` with automatic pre/post orphaned-test cleanup sweeps so interrupted local runs do not accumulate stale test binaries across worktrees.
- [x] MP-258 Automate PyPI publish in release flow by adding `.github/workflows/publish_pypi.yml` (triggered on `release: published`) and aligning maintainer docs so release runs publish through GitHub Actions while `devctl pypi --upload --yes` remains an explicit fallback path.
- [x] MP-259 Automate Codecov coverage uploads by adding `.github/workflows/coverage.yml` (Rust `cargo llvm-cov` LCOV generation + Codecov OIDC upload) and aligning maintainer docs/lane mapping so the README coverage badge is backed by current CI reports instead of `unknown`.
- [x] MP-260 Add non-regressive source-shape guardrails for Rust/Python so oversized files cannot silently drift into new God-file debt: add `dev/scripts/checks/check_code_shape.py` (working-tree + commit-range modes with soft/hard file-size limits and oversize-growth budgets), wire it into `tooling_control_plane.yml`, and add bundle/docs coverage for local maintainer runs.
- [x] MP-261 Refresh README brand banner with a new VoiceTerm hero logo asset (`img/logo-hero.png`) based on the finalized artwork while keeping subtitle/icon identity and removing redundant platform chips from the banner artwork itself (README remains the only consumer; generation script exploration was one-off and not retained in repo tooling).
- [x] MP-282 Consolidate visual planning docs by folding `dev/active/overlay.md` and `dev/active/theme_studio_redesign.md` into `dev/active/theme_upgrade.md`, then update active-index/sync-governance references so one canonical visual spec remains.
- [x] MP-283 Harden release distribution automation by adding a CI release preflight lane (`release_preflight.yml`), a Homebrew publish workflow path (`publish_homebrew.yml`), and safety guards for Homebrew tarball/SHA validation plus `devctl ship` release-version parity enforcement before CI/local publish steps.
- [x] MP-284 Reconcile ADR inventory to runtime truth: remove stale unimplemented proposal ADRs, promote architecture ADRs that match shipped behavior (overlay mode, runtime config precedence, session history boundaries, writer render invariants), and add missing ADR coverage for wake-word ownership, voice-macro precedence, and Claude prompt-safe HUD suppression.
- [x] MP-292 Refactor `devctl` internals to reduce module size, remove command-output drift, and harden missing-binary behavior: extracted shared process-sweep helpers (`dev/scripts/devctl/process_sweep.py`) for `check`/`hygiene`, shared `check` profile normalization (`dev/scripts/devctl/commands/check_profile.py`), shared status/report payload+markdown rendering (`dev/scripts/devctl/status_report.py`), split ship orchestration from step/runtime helpers (`dev/scripts/devctl/commands/ship.py`, `dev/scripts/devctl/commands/ship_common.py`, `dev/scripts/devctl/commands/ship_steps.py`), extracted hygiene audit helpers (`dev/scripts/devctl/commands/hygiene_audits.py`), updated `run_cmd`/ship command checks to return structured failures instead of uncaught Python exceptions when required binaries are missing, and rewrote helper/module docstrings in plain language so junior developers and AI agents can quickly understand when/why each helper exists; verification evidence: `python3 -m unittest discover -s dev/scripts/devctl/tests -p 'test_*.py'`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_agents_contract.py`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_release_version_parity.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [x] MP-293 Add a dedicated `devctl security` command so maintainers can run a local security gate aligned with CI policy: landed `dev/scripts/devctl/commands/security.py` (RustSec JSON capture + policy enforcement + optional `zizmor` workflow scan with `--require-optional-tools` strict mode), extracted security CLI parser wiring into `dev/scripts/devctl/security_parser.py` to keep `dev/scripts/devctl/cli.py` below code-shape growth limits, wired list output in `dev/scripts/devctl/commands/listing.py`, added regression coverage in `dev/scripts/devctl/tests/test_security.py`, expanded plain-language process-sweep context for interrupted/stalled test cleanup in `dev/scripts/devctl/process_sweep.py`, and updated maintainer/governance docs (`AGENTS.md`, `dev/DEVELOPMENT.md`, `dev/scripts/README.md`, `dev/history/ENGINEERING_EVOLUTION.md`); verification evidence: `python3 -m unittest discover -s dev/scripts/devctl/tests -p 'test_*.py'`, `python3 dev/scripts/devctl.py security --dry-run --with-zizmor --require-optional-tools --format json`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_agents_contract.py`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_release_version_parity.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [x] MP-294 Consolidate engineering narrative docs into a single canonical history source by folding `dev/docs/TECHNICAL_SHOWCASE.md` and `dev/docs/LINKEDIN_POST.md` into appendices in `dev/history/ENGINEERING_EVOLUTION.md`, then retiring the duplicated `dev/docs/` source files so updates only target one document; verification evidence: `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [ ] MP-297 Execute a focused `devctl check` usability/performance hardening sequence from maintainer review findings in ordered slices:
  - [x] `#5` failure-output diagnostics: `run_cmd` now streams subprocess output while preserving bounded failure excerpts for non-zero exits (`dev/scripts/devctl/common.py`), `check` prints explicit failed-step summaries with captured context (`dev/scripts/devctl/commands/check.py`), markdown reports include a dedicated failure-output section (`dev/scripts/devctl/steps.py`), and regression coverage/docs were updated (`dev/scripts/devctl/tests/test_common.py`, `dev/scripts/README.md`, `dev/history/ENGINEERING_EVOLUTION.md`); verification evidence: `python3 -m unittest discover -s dev/scripts/devctl/tests -p 'test_*.py'`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_agents_contract.py`, `python3 dev/scripts/checks/check_release_version_parity.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
  - [x] `#1` check-step parallelism: `devctl check` now runs independent setup gates (`fmt`, `clippy`, AI guard scripts) and the test/build phase through deterministic parallel batches with stable report ordering (`dev/scripts/devctl/commands/check.py`), includes maintainer controls for sequential fallback and worker tuning (`--no-parallel`, `--parallel-workers` in `dev/scripts/devctl/cli.py`), and adds regression coverage for parser wiring, parallel-path selection, and ordered aggregation (`dev/scripts/devctl/tests/test_check.py`); verification evidence: `python3 -m unittest dev.scripts.devctl.tests.test_check`.
  - [x] `#7` profile-vs-flag conflict validation: extracted `validate_profile_flag_conflicts()` into `check_profile.py` with `PROFILE_PRESETS` single source of truth, added 12 regression tests in `test_check.py`.
  - [x] `#4` explicit progress feedback: extracted `count_quality_steps()` and `emit_progress()` into `check_progress.py` with serial `[N/M]` and parallel `[N-M/T]` formats, added 10 regression tests in `test_check.py`.
  - [x] `#2` runaway-process containment: `run_cmd` now starts child steps in isolated process groups and tears down the full subprocess tree on interrupt (`dev/scripts/devctl/common.py`), while process sweep now treats stale active `voiceterm-*` test runners as cleanup/error candidates in both `check` and `hygiene` (`dev/scripts/devctl/process_sweep.py`, `dev/scripts/devctl/commands/check.py`, `dev/scripts/devctl/commands/hygiene.py`); regression coverage added in `dev/scripts/devctl/tests/test_common.py`, `dev/scripts/devctl/tests/test_process_sweep.py`, `dev/scripts/devctl/tests/test_check.py`, and `dev/scripts/devctl/tests/test_hygiene.py`.
- [ ] MP-298 Parallelize independent `devctl status`/`report` collection probes and `ship --verify` subchecks with deterministic aggregation so I/O-heavy control-plane workflows run faster without changing pass/fail policy semantics.
- [x] MP-299 Add a `devctl triage` workflow that emits both human-readable markdown and AI-friendly JSON, with optional CIHub ingestion: landed new command surface (`dev/scripts/devctl/commands/triage.py`) plus parser/command inventory wiring (`dev/scripts/devctl/cli.py`, `dev/scripts/devctl/commands/listing.py`), optional `cihub triage` execution + artifact ingestion (`triage.json`, `priority.json`, `triage.md`) under configurable emit directories, and bundle emission mode (`--emit-bundle` writes `<prefix>.md` + `<prefix>.ai.json`) for project handoff/automation use; regression coverage/docs updated in `dev/scripts/devctl/tests/test_triage.py` and `dev/scripts/README.md`; verification evidence: `python3 -m unittest discover -s dev/scripts/devctl/tests -p 'test_*.py'`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_agents_contract.py`, `python3 dev/scripts/checks/check_release_version_parity.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [x] MP-300 Deepen `devctl triage` CIHub integration with actionable routing data: map `cihub` artifact records (`priority.json`, `triage.json`) into normalized issues (`category`, `severity`, `owner`, `summary`) via shared enrichment helpers (`dev/scripts/devctl/triage_enrich.py`), add configurable category-owner overrides (`--owner-map-file`) in parser wiring (`dev/scripts/devctl/triage_parser.py`), include rollup counts by severity/category/owner in report payload + markdown output (`dev/scripts/devctl/triage_support.py`), and extend regression coverage for severity/owner routing + owner-map overrides (`dev/scripts/devctl/tests/test_triage.py`) with docs updates in `dev/scripts/README.md`; verification evidence: `python3 -m unittest discover -s dev/scripts/devctl/tests -p 'test_*.py'`, `python3 dev/scripts/devctl.py triage --format md --no-cihub --emit-bundle --bundle-dir /tmp --bundle-prefix vt-triage-smoke --output /tmp/vt-triage-smoke.md`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_agents_contract.py`, `python3 dev/scripts/checks/check_release_version_parity.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [x] MP-306 Add proactive report-retention governance to the `devctl` control plane: landed `devctl reports-cleanup` with retention safeguards (`--max-age-days`, `--keep-recent`, protected-path exclusions, dry-run preview, confirmation/`--yes` delete path), wired `hygiene` to always surface stale report-growth warnings with direct cleanup guidance, and added parser/command/hygiene regression coverage plus maintainer docs updates (`dev/scripts/README.md`, `dev/DEVCTL_AUTOGUIDE.md`).
- [x] MP-339 Migrate repository Rust workspace path from `src/` to `rust/` and update runtime/tooling/CI/docs path contracts in one governed pass (`dev/active/rust_workspace_layout_migration.md`), preserving behavior while removing the `src/src` naming pattern (landed filesystem rename + path-contract rewrites across scripts/checks/workflows/docs; follow-up guard hardening landed rename-aware baseline mapping for Rust debt/security checks, active-root discovery + fail-fast behavior for `check_rust_audit_patterns.py`, and an explicit non-regressive `mem::forget` policy in `check_rust_best_practices.py`; sync/tooling gates and Rust build smoke from `rust/` succeeded).
- [x] MP-303 Add automated release-metadata preparation to the `devctl` control plane so maintainers can run one command path before verify/tag: added `--prepare-release` support on `devctl ship`/`devctl release` (`dev/scripts/devctl/cli.py`, `dev/scripts/devctl/commands/release.py`, `dev/scripts/devctl/commands/ship.py`), implemented canonical metadata updaters for Cargo/PyPI/macOS app plist plus changelog heading rollover under `dev/scripts/devctl/commands/release_prep.py` and `ship_steps.py`, and covered step wiring + idempotent prep behavior in `dev/scripts/devctl/tests/test_ship.py` and `dev/scripts/devctl/tests/test_release_prep.py`; docs/governance updates in `AGENTS.md`, `dev/DEVELOPMENT.md`, `dev/scripts/README.md`, and `dev/history/ENGINEERING_EVOLUTION.md`; verification evidence: `python3 -m unittest dev.scripts.devctl.tests.test_ship dev.scripts.devctl.tests.test_release_prep`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_agents_contract.py`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_release_version_parity.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [ ] MP-257 Run a plain-language readability pass across primary `dev/` entry docs (`dev/README.md`, `dev/DEVELOPMENT.md`, `dev/ARCHITECTURE.md`) so new developers can follow workflows quickly without losing technical accuracy.
  - [x] 2026-02-25 workflow readability slice: added `.github/workflows/README.md` with plain-language explanations for all workflow lanes (what runs, when it runs, and local reproduce commands) and added short purpose headers to every `.github/workflows/*.yml` file so intent is visible without opening full YAML bodies.
  - [x] 2026-02-25 core-dev-doc readability slice: simplified workflow/process language in `dev/README.md`, `dev/DEVELOPMENT.md`, and `dev/ARCHITECTURE.md` so operators can scan what to run and why without policy-heavy wording.
  - [x] 2026-02-25 user-guide readability slice: simplified wording across `guides/README.md`, `guides/INSTALL.md`, `guides/USAGE.md`, `guides/CLI_FLAGS.md`, `guides/TROUBLESHOOTING.md`, and `guides/WHISPER.md` while preserving command/flag behavior and technical accuracy.
  - [x] 2026-02-25 root-entry readability slice: simplified wording in `README.md`, `QUICK_START.md`, and `DEV_INDEX.md` so first-time users and maintainers can scan setup/docs links quickly without changing any commands, flags, or workflow behavior.
  - [x] 2026-02-25 follow-up dev-entry readability slice: refined plain-language wording in `dev/README.md`, `dev/DEVELOPMENT.md`, and `dev/ARCHITECTURE.md`, and replaced the outdated `src/src` tree in `dev/DEVELOPMENT.md` with the current `rust/` layout summary so docs are both easier to scan and accurate.

## Phase 3C - Codebase Best-Practice Consolidation (Active Audit Track)

- [x] MP-184 Publish a dedicated execution record for full-repo Rust best-practice cleanup and keep task-level progress scoped to that audit track.
- [x] MP-185 Decompose settings action handling for lower coupling and clearer ownership (`settings_handlers` runtime/test separation, enum-cycle consolidation, constructor removal, status-helper extraction, and `SettingsActionContext` sub-context split landed; adjacent `ButtonActionContext::new` constructor removal also landed for consistent context wiring).
- [x] MP-186 Consolidate status-line rendering/button logic (`status_line/buttons.rs` and `status_line/format.rs`) to remove duplicated style/layout decisions and isolate legacy compatibility paths (landed: shared button highlight + queue/ready/latency badge helpers; legacy row helpers are `#[cfg(test)]`-gated with shared framing/separator helpers and reduced dead-code surface; tests split into `status_line/buttons/tests.rs` and `status_line/format/tests.rs`).
- [x] MP-187 Consolidate PTY lifecycle internals into canonical spawn/shutdown helpers and harden session-guard identity/cleanup throttling to reduce stale-process risk without blocking concurrent sessions (landed shared PTY lifecycle helpers in `pty_session/pty.rs`, plus session-lease start-time identity validation and atomic cleanup cadence throttling in `pty_session/session_guard.rs`; additional detached-orphan sweep fallback now reaps stale backend CLIs with `PPID=1` when they are not lease-owned and no longer share a TTY with a live shell, with deterministic unit coverage for elapsed-time parsing and candidate filtering).
- [x] MP-188 Decompose backend orchestration hotspots (`codex/pty_backend.rs`, `ipc/session.rs`) into narrower modules with explicit policy boundaries and lower test/runtime coupling (completed in v1.0.80: landed `codex/pty_backend/{output_sanitize,session_call,job_flow,test_support}.rs` plus `ipc/session/{stdin_reader,claude_job,auth_flow,loop_control,state,event_sink,test_support}.rs`, keeping parent orchestrators focused on runtime control flow).
- [x] MP-189 Add a focused maintainer lint-hardening lane (strict clippy profile + targeted allowlist) and burn down high-value warnings (`must_use`, error docs, redundant clones/closures, risky casts, dead-code drift) (completed in v1.0.80: landed `devctl check --profile maintainer-lint` + `.github/workflows/lint_hardening.yml`, burned down targeted warnings, added Linux ALSA dependency setup for the lane, and documented intentional deferral of precision/truncation DSP cast families).
- [x] MP-191 Fix Homebrew `opt` launcher path detection in `scripts/start.sh` + `scripts/setup.sh` so upgrades reuse persistent user model storage (`~/.local/share/voiceterm/models`) instead of redownloading into versioned Cellar `libexec/whisper_models`.
- [x] MP-192 Fix Full HUD ribbon baseline rendering by padding short waveform history at floor level (`-60 dB`) so right-panel visuals ramp upward instead of drawing a full-height block.
- [x] MP-193 Restore insert-mode early-send behavior for `Ctrl+E` while recording so noisy-room captures can stop early and submit immediately (one-shot force-send path + regression tests + docs alignment).
- [x] MP-197 Make hidden-HUD idle launcher visuals intentionally subdued (dull/muted text and `[open]`) so hidden mode remains non-intrusive.
- [x] MP-198 Align insert-mode `Ctrl+E` dispatch semantics (send staged text, finalize+submit while recording, consume idle/no-staged input) and apply the same muted hidden-launcher gray to hidden recording output.
- [x] MP-204 Refine hidden-HUD idle launcher controls for lower visual noise and better explicitness (remove inline `Ctrl+U` hint from hidden launcher text, add muted `[hide]` control next to `[open]`, support collapsing hidden launcher chrome to `[open]` only, and make `open` two-step from collapsed mode: restore launcher first, then switch HUD style on the next open).
- [x] MP-205 Harden discoverability + feedback ergonomics (expand startup hints for `?`/settings/mouse discoverability, add grouped help overlay sections, and surface explicit idle `Ctrl+E` feedback with `Nothing to send`).
- [x] MP-206 Add first-run onboarding hint persistence (`~/.config/voiceterm/onboarding_state.toml`) so a `Getting started` hint remains until the first successful transcript capture.
- [x] MP-207 Extract shared overlay frame rendering helpers (`overlay_frame`) and route help/settings/theme-picker framing through the shared path to reduce duplicated border/title/separator logic.
- [x] MP-208 Standardize overlay/HUD width accounting with Unicode-aware display width and add HUD module `priority()` semantics so queue/latency indicators survive constrained widths ahead of lower-priority modules.
- [x] MP-209 Replace opaque runtime status errors with log-path-aware messages (`... (log: <path>)`) across capture/transcript failure paths.
- [x] MP-210 Keep splash unchanged, but move discoverability/help affordances into runtime HUD/overlay surfaces (hidden HUD idle hint now includes `? help` + `^O settings`; help overlay adds clickable Docs/Troubleshooting OSC-8 links).
- [x] MP-211 Replace flat clap default `--help` output with a themed, grouped renderer backed by clap command metadata (manual `-h`/`--help` interception, sectioned categories, single-accent hacker-style scan path with dim borders + bracketed headers, theme/no-color parity, and coverage guard so new flags cannot silently skip grouping).
- [x] MP-212 Remove stale pre-release/backlog doc references, align `VoiceTerm.app` Info.plist version with `rust/Cargo.toml`, and sync new `voiceterm` modules in changelog/developer structure docs.
- [x] MP-213 Add a Rust code-review research pack and wire it into the code-quality execution track with an explicit closure/archive handoff path into Theme Upgrade phases (`MP-148+`).
- [x] MP-218 Fix overlay mouse hit-testing for non-left-aligned coordinate spaces so settings/theme/help row clicks and slider adjustments still apply when terminals report centered-panel `x` coordinates.
- [x] MP-219 Clarify settings overlay footer control hints (`[×] close · ↑/↓ move · Enter select · Click/Tap select`) and add regression coverage so footer close click hit-testing stays intact after copy updates.
- [x] MP-220 Fix settings slider click direction handling so pointer input on `Sensitivity`/`Wake sensitivity` tracks can move left/right by click position, with regression tests for backward slider clicks.
- [x] MP-221 Fix hidden-launcher mouse click redraw parity so `[hide]` and collapsed `[open]` clicks immediately repaint launcher state (matching arrow-key `Enter` behavior), with regression tests for both click paths.
- [x] MP-222 Resolve post-release `lint_hardening` CI failures by removing redundant-closure clippy violations in `custom_help.rs` and restoring maintainer-lint lane parity on `master`.
- [x] MP-223 Unify README CI/mutation badge theming to black/gray endpoint styling and enforce red failure states via renderer scripts (`render_ci_badge.py`, `render_mutation_badge.py`) plus CI workflow auto-publish on `master`.
- [x] MP-224 Harden Theme Studio style-pack test determinism by isolating unit tests from ambient shell `VOICETERM_STYLE_PACK_JSON` exports (tests now ignore runtime style-pack env unless explicit opt-in is set, and lock-path tests opt in intentionally), preventing cross-shell snapshot/render drift during `cargo test --bin voiceterm`.
- [x] MP-225 Fix Enter-key auto-mode flip regression: when stale HUD button focus is on `ToggleAutoVoice`, pressing `Enter` now submits PTY input (no mode flip), backed by a focused event-loop regression test and docs sync.
- [x] MP-228 Audit user-doc information architecture and seed screenshot-refresh governance: rebalance `QUICK_START.md` to onboarding scope, move deep runtime semantics to guides, document transcript-history mouse behavior and env parity (`VOICETERM_ONBOARDING_STATE`), and add a maintainer capture matrix for pending UI surfaces.
- [x] MP-214 Close out the active code-quality track by triaging remaining findings, archiving audit records, and continuing execution from Theme Upgrade (`MP-148+`).
- [x] MP-215 Standardize runtime status-line width/truncation on Unicode-aware display width in remaining char-count paths (`rust/src/bin/voiceterm/writer/render.rs` and `rust/src/bin/voiceterm/status_style.rs`) with regression coverage for wide glyphs (landed Unicode-aware width/truncation in writer sanitize/render/status-style paths, preserved printable Unicode status text, and added regression tests for wide-glyph truncation and width accounting).
- [x] MP-216 Consolidate duplicate transcript-preview formatting logic shared by `rust/src/bin/voiceterm/voice_control/navigation.rs` and `rust/src/bin/voiceterm/voice_control/drain/message_processing.rs` into a single helper with shared tests (landed shared `voice_control/transcript_preview.rs` formatter and removed duplicated implementations from navigation/drain paths with focused unit coverage).
- [x] MP-217 Enable settings-overlay row mouse actions so row clicks select and apply setting toggles/cycles (including click paths for `Close` and `Quit`) instead of requiring keyboard-only action keys.
- [x] MP-262 Publish a full senior-level engineering audit baseline in `dev/archive/2026-02-20-senior-engineering-audit.md` with measured code-shape, lint-debt, CI hardening, and automation findings mapped to executable follow-up MPs.
- [x] MP-263 Harden GitHub Actions supply-chain posture: pin third-party actions by commit SHA, define explicit least-privilege `permissions:` on every workflow, and add `concurrency:` groups where duplicate in-flight runs can race or waste minutes (landed by pinning all workflow action refs to 40-char SHAs across `.github/workflows/*.yml`, adding explicit `permissions:`/`concurrency:` blocks to every workflow, and narrowing write scope to job-level where badge-update pushes require `contents: write`).
- [x] MP-264 Add repository ownership and dependency automation baseline by introducing `.github/CODEOWNERS` and `.github/dependabot.yml` (grouped update policies + review routing) so tooling/runtime changes always have accountable reviewers and timely dependency refresh cadence (landed with explicit ownership coverage for runtime/tooling/distribution paths and weekly grouped update policies for GitHub Actions, Cargo, and PyPI packaging surfaces).
- [ ] MP-265 Decompose oversized runtime modules with explicit shape budgets and staged extraction plans (top hotspots: `event_loop/input_dispatch.rs`, `status_line/format.rs`, `status_line/buttons.rs`, `theme/rule_profile.rs`, `theme/style_pack.rs`, `transcript_history.rs`) while preserving non-regression behavior coverage (in progress: `dev/scripts/checks/check_code_shape.py` now enforces path-level non-growth budgets for the hotspot files so decomposition work is CI-measurable instead of policy-only; `event_loop/input_dispatch.rs` overlay-mode handling was extracted into `event_loop/input_dispatch/overlay.rs` + `event_loop/input_dispatch/overlay/overlay_mouse.rs`; prior slice extracted status-line right-panel formatting/animation helpers from `status_line/format.rs` into `status_line/right_panel.rs`; latest slices move minimal-HUD right-panel scene/waveform/pulse helpers from `status_line/buttons.rs` into `status_line/right_panel.rs` and extract queue/wake/latency badge formatting into `status_line/buttons/badges.rs`, reducing `status_line/buttons.rs` from 1059 to 801 lines while keeping focused status-line tests green).
- [ ] MP-266 Burn down Rust lint-debt hotspots by reducing `#[allow(...)]` surface area and non-test `unwrap/expect` usage, then add measurable gates/reporting so debt cannot silently regress (in progress: landed `dev/scripts/checks/check_rust_lint_debt.py` with working-tree + commit-range modes, wired governance bundles/docs references, and added tooling-control-plane CI enforcement so changed Rust files cannot add net-new lint debt without an explicit failure signal; latest slice removes 22 `#[allow(dead_code)]` suppressions by scoping PTY counter helper APIs/re-exports to tests in `pty_session/counters.rs` + `pty_session/mod.rs`, with full `devctl check --profile ci` and lifecycle matrix test coverage green).
- [ ] MP-267 Run a naming/API cohesion pass across theme/event-loop/status/memory surfaces to remove ambiguous names, tighten public API intent, and consolidate duplicated helper logic into shared modules (`dev/active/naming_api_cohesion.md`; in progress: canonical `swarm_run` command naming now enforced in parser/dispatch/workflow/docs with no legacy alias in active command paths, duplicate triage/mutation policy engines consolidated into shared `loop_fix_policy.py` helper with tests, duplicated devctl numeric parsing consolidated into `dev/scripts/devctl/numeric.py` (`to_int`/`to_float`/`to_optional_float`) with callsite rewiring, Theme Studio list navigation consolidated under shared `theme_studio/nav.rs` with consistent `select_prev`/`select_next` naming across page state + input-dispatch call paths, and prompt-occlusion suppression transitions extracted into `event_loop/prompt_occlusion.rs` so output/input/periodic dispatchers share one runtime owner for suppression side effects).
- [x] MP-268 Codify a Rust-reference-first engineering quality contract in `AGENTS.md` and `dev/DEVELOPMENT.md`, including mandatory official-doc reference pack links and handoff evidence requirements for non-trivial Rust changes.
- [ ] MP-269 Add Theme Studio style-pack hot reload (`notify` watcher + debounce + deterministic rollback-safe apply path) so theme iteration does not require restarting VoiceTerm.
- [ ] MP-270 Add algorithmic theme generation mode (`palette`-backed seed-color derivation with contrast guards) and expose it in Theme Studio as an optional starting point, not a replacement for manual edits.
- [ ] MP-271 Replace ad-hoc animation transitions with a deterministic easing profile layer (`keyframe`-style easing contracts or equivalent) and benchmark frame-cost impact on constrained terminals.
- [ ] MP-272 Define and implement Memory Studio context-injection contract for Codex/Claude handoff flows (selection policy, token budget, provenance formatting, failure rollback).
- [ ] MP-273 Produce an overlay architecture ADR evaluating terminal-only vs hybrid desktop overlay (`egui_overlay`/window-layer path) with explicit capability matrix, migration risk, and phased rollout recommendation.
- [x] MP-274 Add AI coding guardrails for Rust best-practice drift by introducing `dev/scripts/checks/check_rust_best_practices.py` (working-tree + commit-range non-regression checks for reason-less `#[allow(...)]`, undocumented `unsafe { ... }`, and public `unsafe fn` without `# Safety` docs), wiring it into `devctl check` (`--profile ai-guard` plus automatic `prepush`/`release` guard steps), and enforcing commit-range execution in `.github/workflows/tooling_control_plane.yml` with docs/bundle parity updates.
- [x] MP-275 Normalize `--input-device` values before runtime recorder lookup by collapsing wrapped whitespace/newline runs and rejecting empty normalized names so wake/manual capture initialization stays resilient to terminal line-wrap paste artifacts.
- [x] MP-276 Harden wake-word runtime diagnostics/ownership handoff: HUD now reflects listener-startup failures (`Wake: ERR` + status/log-path message) instead of false `Wake: ON` state when listener init fails, and wake detection now self-pauses listener capture before triggering shared capture startup to reduce microphone ownership races.
- [x] MP-277 Expand wake-word matcher alias normalization for common STT token-split variants (`code x` -> `codex`, `voice term` -> `voiceterm`) while preserving short-utterance guardrails and updating troubleshooting phrase guidance.
- [x] MP-278 Correct wake-trigger capture origin labeling end-to-end so wake-detected recordings flow through the shared capture path with explicit `WakeWord` trigger semantics (logs/status no longer misreport wake-initiated captures as manual starts).
- [x] MP-279 Reduce wake-state confusion and listener churn: keep `Wake: ON` badge styling steady (no pulse redraw), remove periodic wake-badge animation ticks, and extend wake-listener capture windows to reduce frequent microphone open/close cycling on macOS.
- [x] MP-280 Harden wake re-arm reliability after first trigger by decoupling wake detections from the auto-voice pause latch, allowing longer command tails when wake phrases lead the transcript, and adding no-audio retry backoff to reduce rapid microphone indicator churn on transient capture failures.
- [x] MP-281 Add built-in voice submit intents for insert mode (`send`, `send message`, `submit`) so staged transcripts can be submitted hands-free through the same newline path as Enter, including one-shot wake tails (`hey codex send` / `hey claude send`).
- [x] MP-296 Keep latency visibility stable in auto mode by preserving the last successful latency sample across auto-capture `Empty` cycles and allowing the shortcuts-row latency badge to remain visible during auto recording/processing (manual mode continues hiding during active capture); coverage added in `status_line/buttons/tests.rs` and `voice_control/drain/tests.rs`.

## Phase 3D - Memory + Action Studio (Planning Track)

Memory Studio execution gate: MP-230..MP-255 are governed by
`dev/active/memory_studio.md`. A Memory MP may move to `[x]` only with
documented `MS-G*` pass evidence.

- [x] MP-230 Establish canonical memory event schema + storage foundation (JSONL append log + SQLite index) for machine-usable local memory (`MS-G01`, `MS-G02`).
- [ ] MP-231 Implement deterministic retrieval APIs (topic/task/time/semantic) with provenance-tagged ranking and bounded token budgets (`MS-G03`, `MS-G04`).
- [x] MP-232 Ship context-pack generation (`context_pack.json` + `context_pack.md`) for AI boot/handoff workflows with explicit evidence references (`MS-G03`, `MS-G07`).
- [ ] MP-233 Deliver Memory Browser overlay (filter/expand/scroll/replay-safe controls) with keyboard+mouse parity (`MS-G06`).
- [ ] MP-234 Deliver Action Center overlay with policy-tiered command execution (read-only/confirm-required/blocked), preview/approval flow, and action-run audit logging (`MS-G05`, `MS-G06`).
- [ ] MP-235 Add memory governance controls (retention, redaction hooks, per-project isolation) and regression tests for bounded growth/privacy invariants (`MS-G04`, `MS-G05`).
- [ ] MP-236 Complete docs + release readiness for Memory Studio (architecture/user docs/changelog + CI evidence bundle) (`MS-G07`, `MS-G08`).
- [ ] MP-237 Add memory-evaluation harness and quality gates (`precision@k`, evidence coverage, deterministic pack snapshots, latency budgets) for release blocking (`MS-G03`, `MS-G04`, `MS-G08`).
- [ ] MP-238 Add model-adapter interop for context packs (Codex/Claude-compatible pack rendering while preserving canonical JSON provenance) (`MS-G03`, `MS-G07`, `MS-G08`).
- [ ] MP-240 Add validated Memory Cards as a derived-truth layer (decision/project_fact/procedure/gotcha/task_state/glossary) with evidence links, TTL policies, and branch-aware validation-before-injection (`MS-G03`, `MS-G09`).
- [x] MP-241 Wire dev tooling and git intelligence into memory ingestion (`devctl status/report`, release-notes artifacts, git range summaries) and ship compiler outputs (`project_synopsis`, `session_handoff`, `change_digest`) in JSON+MD (`MS-G02`, `MS-G10`).
- [ ] MP-242 Ship read-only MCP memory exposure (resources + tools for search/context packs/validation) with deterministic provenance payloads and policy-safe defaults (`MS-G03`, `MS-G11`).
- [ ] MP-243 Add user memory-control modes (`off`, `capture_only`, `assist`, `paused`, `incognito`) with UI/state persistence and regression coverage for trust/privacy invariants (`MS-G05`, `MS-G06`).
- [ ] MP-244 Add sequence-aware action safety escalation so multi-command workflows increase policy tier when risk patterns combine (mutation + network + shell exec) and require explicit confirmation evidence (`MS-G05`, `MS-G11`).
- [ ] MP-246 Implement repetition-mining over memory events/command runs to detect high-frequency scriptable workflows, with support+confidence thresholds and provenance-scored candidates (`MS-G03`, `MS-G10`, `MS-G12`).
- [ ] MP-247 Ship automation suggestion flow that proposes script templates + `AGENTS.md` instruction patches + workflow snippets with preview/approve/reject UX (no auto-apply) and acceptance telemetry (`MS-G05`, `MS-G06`, `MS-G12`).
- [ ] MP-248 Add opt-in external transcript import adapters (for example ChatGPT export files) normalized into canonical memory schema with source tagging/redaction and retrieval-only defaults for safety (`MS-G01`, `MS-G05`, `MS-G13`).
- [ ] MP-249 Implement isolation profiles for action execution (`host_read_only`, `container_strict`, `host_confirmed`) with policy wiring, audit logging, and escape-attempt regression tests (`MS-G05`, `MS-G14`).
- [ ] MP-250 Build compaction experiment harness (A/B against no-compaction baseline) with replay fixtures, benchmark adapters, and report artifacts covering quality/citation/latency/token metrics (`MS-G03`, `MS-G15`).
- [ ] MP-251 Gate compaction default-on rollout behind non-inferiority/evidence thresholds and publish operator guidance for safe enablement strategy (`MS-G07`, `MS-G08`, `MS-G15`).
- [ ] MP-252 Prototype Apple Silicon acceleration paths (SIMD/Metal/Core ML where applicable) for memory retrieval/compaction workloads and publish backend benchmark matrix vs CPU reference (`MS-G03`, `MS-G16`).
- [ ] MP-253 Gate acceleration rollout behind non-inferiority quality checks, deterministic-evidence parity checks, and runtime fallback guarantees (`MS-G08`, `MS-G16`).
- [ ] MP-254 Evaluate ZGraph-inspired symbolic compaction for memory units/context packs (pattern aliases for repeated paths/commands/errors), with reversible transforms and deterministic citation-equivalence checks (`MS-G03`, `MS-G15`, `MS-G17`).
- [ ] MP-255 Gate any symbolic compaction rollout behind non-inferiority quality thresholds, round-trip parity fixtures, and explicit default-off operator guidance until `MS-G17` passes (`MS-G07`, `MS-G08`, `MS-G17`).

## Phase 3A - Mutation Hardening (Parallel Track)

- [ ] MP-015 Improve mutation score with targeted high-value tests (promoted from Backlog).
  - [ ] Build a fresh shard-by-shard survivor baseline on `master` and rank hotspots by missed mutants.
  - [x] Add mutation outcomes freshness visibility and stale-data gating in local tooling (`check_mutation_score.py` + `devctl mutation-score` now report source path/age and support `--max-age-hours`).
  - [x] Add targeted mutation-killer coverage for `theme_ops::cycle_theme` ordering/wrap semantics so default-return/empty-list/position-selection mutants are caught deterministically.
  - [x] Add targeted mutation-killer coverage for `Theme::from_name` alias arms (`tokyonight`/`tokyo-night`/`tokyo`, `gruvbox`/`gruv`) and `Theme::available()` list parity so empty/placeholder return mutants are caught.
  - [x] Add targeted mutation-killer coverage for `status_style::status_display_width` arithmetic and `terminal::take_sigwinch` clear-on-read semantics so constant-return/math mutants are caught.
  - [x] Add targeted mutation-killer coverage for `main.rs` runtime guards (`contains_jetbrains_hint`, `is_jetbrains_terminal`, `resolved_meter_update_ms`, and `join_thread_with_timeout`) and eliminate focused survivors (`cargo mutants --file src/bin/voiceterm/main.rs`: 18 caught, 0 missed, 1 unviable).
  - [x] Add targeted mutation-killer coverage for `input/mouse.rs` protocol guards/parsers (SGR/URXVT/X10 prefix+length boundaries and dispatch detection), eliminating focused survivors (`cargo mutants --file src/bin/voiceterm/input/mouse.rs`: 76 caught, 0 missed, 17 unviable).
  - [x] Remove the equivalent survivor path in `config/theme.rs` (`theme_for_backend` redundant `NO_COLOR` branch), keep explicit env-behavior regression coverage, and re-verify focused mutants (`cargo mutants --file src/bin/voiceterm/config/theme.rs`: 6 caught, 0 missed) plus `devctl check --profile ci` green.
  - [x] Eliminate `event_loop.rs` helper/boundary survivors by adding direct coverage for drain/winsize/overlay rendering/button-registry/picker reset paths, hardening settings-direction boundary assertions, and refactoring slider sign math to non-equivalent `is_negative()` checks (`cargo mutants --file src/bin/voiceterm/event_loop.rs`: 58 caught, 0 missed, 2 unviable) with `devctl check --profile ci` green.
  - [x] Remove `config/backend.rs` argument-length equivalent survivors in backend command resolution (`command_parts.len() > 1`) by refactoring to iterator-based split (`next + collect`) and re-verifying focused mutants (`cargo mutants --file src/bin/voiceterm/config/backend.rs`: 1 caught, 0 missed, 1 unviable) with `devctl check --profile ci` green.
  - [x] Add targeted `config/util.rs` path-shape boundary coverage for `is_path_like` (absolute/relative path positives, bare binary and empty-value negatives) and re-verify focused mutants (`cargo mutants --file src/bin/voiceterm/config/util.rs`: 11 caught, 0 missed) with `devctl check --profile ci` green.
  - [x] Add targeted regression coverage for runtime utility hotspots `auth.rs` and `lock.rs` (login command validation + exit-status mapping paths and mutex poison-recovery paths) so low-coverage utility modules stay protected without introducing lint-debt growth.
  - [x] Harden `event_loop/input_dispatch/overlay/overlay_mouse.rs` boundary predicates and add focused Theme Studio/settings mouse regression coverage (footer non-close area, border columns, option-row activation/out-of-range guards), eliminating the focused survivor cluster (`cargo mutants --file src/bin/voiceterm/event_loop/input_dispatch/overlay/overlay_mouse.rs --re 'overlay_mouse\\.rs:(32|39|99|100|119|142|143|144|145):'`: 8 caught, 0 missed).
  - [ ] Add targeted tests for top survivors in current hotspots (`src/bin/voiceterm/config/*`, `src/bin/voiceterm/hud/*`, `src/bin/voiceterm/input/mouse.rs`) and any new top offenders.
  - [ ] Ensure shard jobs always publish outcomes artifacts even when mutants survive.
  - [ ] Re-run mutation workflow until aggregate score holds at or above `0.80` on `master` for two consecutive runs (manual + scheduled).
  - [ ] Keep non-mutation quality gates green after each hardening batch (`python3 dev/scripts/devctl.py check --profile ci`, `Security Guard`).
- MP-015 acceptance gates:
  1. `.github/workflows/mutation-testing.yml` passes on `master` with threshold `0.80`.
  2. Aggregated score gate passes via `python3 dev/scripts/checks/check_mutation_score.py --glob "mutation-shards/**/shard-*-outcomes.json" --threshold 0.80`.
  3. Shard outcomes artifacts are present for all 8 shards in each validation run.
  4. Added hardening tests remain stable across two consecutive mutation workflow runs.

## Phase 4 - Advanced Expansion

- [ ] MP-092 Streaming STT and partial transcript overlay.
- [ ] MP-093 tmux/neovim integration track.
- [ ] MP-094 Accessibility suite (fatigue hints, quiet mode, screen-reader compatibility).
- [ ] MP-095 Custom vocabulary learning and correction persistence.

## Backlog (Not Scheduled)

- [ ] MP-016 Stress test heavy I/O for bounded-memory behavior.
- [ ] MP-031 Add PTY health monitoring for hung process detection.
- [ ] MP-032 Add retry logic for transient audio device failures.
- [ ] MP-033 Add benchmarks to CI for latency regression detection.
- [ ] MP-034 Add mic-meter hotkey for calibration.
- [ ] MP-037 Consider configurable PTY output channel capacity.
- [ ] MP-145 Eliminate startup cursor/ANSI escape artifacts shown in Cursor (Codex and Claude backends), with focus on the splash-screen teardown to VoiceTerm HUD handoff window where artifacts appear before full load. (in progress: writer pre-clear is now constrained to JetBrains terminals to reduce Cursor typing-time HUD flash while preserving JetBrains scroll-ghost mitigation.)
- [x] MP-146 Improve controls-row bracket styling so `[` `]` tokens track active theme colors and selected states use stronger contrast/readability (especially for arrow-mode focus visibility) (landed controls-row bracket tint routing so unfocused pills inherit active button highlight colors instead of always dim brackets, plus focused button emphasis via bold+info-bracket rendering for stronger keyboard focus visibility; covered by `status_line::buttons` regressions `format_button_brackets_track_highlight_color_when_unfocused`, `focused_button_uses_info_brackets_with_bold_emphasis`, and existing focus-bracket parity tests).
- [x] MP-147 Fix Cursor-only mouse-mode scroll conflict: with mouse mode ON, chat/conversation scroll should still work in Cursor for both Codex and Claude backends; preserve current JetBrains behavior (works today in PyCharm/JetBrains), keep architecture/change scope explicitly Cursor-specific, and require JetBrains non-regression validation so the Cursor fix does not break JetBrains scrolling. (landed Cursor-specific scroll-safe mouse handling in writer mouse control: Cursor keeps wheel scrollback available while settings can remain `Mouse: ON - scroll preserved in Cursor`, while JetBrains and other terminals retain existing mouse behavior.) Regression note (2026-02-25): users still report Cursor touchpad/wheel scrolling failing while `Mouse` is ON, with scrollbar drag still working; follow-up tracked in `MP-344`.
- [ ] MP-227 Explore low-noise progress-animation polish for task/status rows (inspired by Claude-style subtle shimmer/accent transitions during active thinking), including optional tiny accent pulses/color sweeps with strict readability/contrast bounds and no distraction under sustained usage; keep as post-priority visual refinement (not current execution scope).
- [x] MP-153 Add a CI docs-governance lane that runs `python3 dev/scripts/devctl.py docs-check --user-facing --strict` for user-facing behavior/doc changes so documentation drift fails early (completed via MP-230 docs-policy lane hardening in `.github/workflows/tooling_control_plane.yml`).
- [ ] MP-154 Add a governance consistency check for active docs + macro packs so removed workflows/scripts are not referenced in non-archive content.
- [ ] MP-155 Add a single pre-release verification command/profile that aggregates CI checks, mutation threshold, docs-governance checks, and hygiene into one machine-readable report artifact.
- [ ] MP-322 Investigate and fix wake-word + send intent "nothing to send" false negative: when using `Hey Claude, send` or `Hey Codex, send` voice commands, VoiceTerm sometimes reports "Nothing to send" even though there is staged text in the PTY input buffer; reproduce with both Claude and Codex backends, capture transcript decision traces (`voiceterm --logs --log-content`), verify send-intent detection timing relative to transcript staging, add targeted matcher/integration tests for the wake-tail send flow, and ensure the send intent checks for staged PTY content (not just VoiceTerm internal staged text state). Physical testing required alongside automated coverage.
- [ ] MP-323 Restore keyboard left/right caret navigation while editing staged text: currently Left/Right (and equivalent arrow-key paths) are captured by tab/button focus navigation instead of moving the text cursor inside the transcript/input field, which blocks correction of Whisper transcription mistakes before submit. Reproduce in active VoiceTerm sessions with staged text, route Left/Right to caret movement whenever text input/edit mode is active, preserve existing tab/control navigation when text edit mode is not active, and add focused keyboard/mouse regression coverage to prevent future text-edit lockouts. (2026-02-27 input-path hardening landed for related navigation regressions: shared arrow parser now accepts colon-parameterized CSI forms used by keyboard-enhancement modes, preventing settings/theme/overlay arrow-navigation dropouts after backend prompt-state transitions.)
- [ ] MP-324 Finalize Ralph loop rollout evidence on default branch: after the workflow lands on the default branch, run one `workflow_dispatch` `CodeRabbit Ralph Loop` execution on `develop` (`execution_mode=report-only`) and confirm `check_coderabbit_ralph_gate.py --branch develop` resolves by workflow-run evidence rather than fallback logic; capture run URL and gate output in tooling handoff notes so release gating assumptions are explicit for all agents.
- [x] MP-325 Harden Ralph loop source-run correlation: pin `triage-loop` execution to authoritative source run id/sha when launched from `workflow_run`, fail safely on source mismatch, and preserve manual-dispatch fallback behavior (landed `--source-run-id/--source-run-sha/--source-event` parser+command+core wiring, source-run attempt pinning, run/artifact SHA mismatch detection with explicit `source_run_sha_mismatch` reason codes, and workflow source-run id/sha forwarding in `.github/workflows/coderabbit_ralph_loop.yml`).
- [x] MP-326 Implement real `summary-and-comment` notify semantics for `triage-loop`: add comment-target resolution (`auto|pr|commit`), idempotent marker updates, and workflow permission hardening so comment mode is deterministic and non-spammy (landed comment target flags, PR/commit target resolver, marker-based upsert behavior via GitHub API, and workflow permission updates including `pull-requests: write` + `issues: write`).
- [x] MP-327 Add bounded mutation remediation command surface (`devctl mutation-loop`) with report-only default, scored hotspot outputs, freshness checks, and optional policy-gated fix attempts (landed `dev/scripts/devctl/commands/mutation_loop.py`, `mutation_loop_parser.py`, `mutation_ralph_loop_core.py`, bundle/playbook outputs, and targeted unit coverage).
- [x] MP-328 Add `.github/workflows/mutation_ralph_loop.yml` orchestration: mutation-loop mode controls, bounded retry parameters, artifact bundling, and optional notify surfaces with default non-blocking behavior (landed workflow_run + workflow_dispatch wiring, mode/threshold/notify/comment inputs, summary output, and artifact upload).
- [x] MP-329 Add mutation auto-fix command policy gate: enforce allowlisted commands/prefixes, explicit reason codes on deny paths, and auditable action traces for each attempt (landed `control_plane_policy.json` baseline, `AUTONOMY_MODE` + branch allowlist + command-prefix gating, and policy-deny reason surfacing in mutation loop reports).
- [ ] MP-330 Scaffold Rust containerized mobile control-plane service (`voiceterm-control`) with read-only health/loop/ci/mutation endpoints and constrained workflow-dispatch controls.
- [ ] MP-331 Add phone adapter track (SMS-first pilot + push/chat follow-up) with policy-gated action routing, webhook auth, response/audit persistence, and bounded remote-operation scope. (partial: `devctl autonomy-loop` now emits phone-ready status snapshots under `dev/reports/autonomy/queue/phone/latest.{json,md}` including terminal trace, draft text, and source run context for read-first mobile surfaces; `devctl phone-status` now provides SSH/iPhone-safe projection views (`full|compact|trace|actions`) with optional projection bundle emission for controller-state files; `devctl controller-action` now provides a guarded safe subset (`refresh-status`, `dispatch-report-only`, `pause-loop`, `resume-loop`) with allowlist/kill-switch policy checks and auditable outputs.)
- [ ] MP-332 Add autonomy guardrails and traceability controls (`control_plane_policy.json`, replay protection, mode kill-switch, branch-protection-aware action rejection, duplicate/stale run suppression). (partial: `control_plane_policy.json` added, `AUTONOMY_MODE` + branch/prefix policy gate wired for both mutation and triage fix modes, triage loop now emits dedicated review-escalation comment upserts when retries exhaust unresolved backlog, marker-based duplicate comment suppression landed, `devctl check --profile release` now enforces strict remote release gates (`status --ci --require-ci` + CI-mode CodeRabbit/Ralph checks), and bounded controller surfaces now ship via `devctl autonomy-loop` + `.github/workflows/autonomy_controller.yml` with run-scoped checkpoint packet queue artifacts; replay protection + deeper branch-protection/merge-queue enforcement remain pending.)
- [x] MP-333 Enforce active execution-plan traceability governance: non-trivial agent work must be anchored to a `dev/active/*.md` execution-plan doc (with checklist/progress/audit sections), and tooling guardrails must fail when contract markers/required sections drift (landed enforcement updates in `check_active_plan_sync.py` for required execution-plan docs + marker + required sections, plus AGENTS contract references).
- [x] MP-334 Add external-repo federation bridge for reusable autonomy components: pin `code-link-ide` + `ci-cd-hub` in `integrations/`, provide one-command sync path, and document governed selective-import workflow for this repo template path. (landed submodule links + shell helper + `devctl integrations-sync`/`integrations-import` command surfaces, policy allowlists in `control_plane_policy.json` (`integration_federation`), destination-root guards, and JSONL audit logging for sync/import actions.)
- [ ] MP-335 Fix wake word send intent not triggering in auto mode: when VoiceTerm is in auto-listen mode and actively listening, saying "Hey Codex send" (or "Hey Claude send") does not trigger the send action — the wake word is effectively ignored while the mic is already open. Expected behavior: the wake-word detector should remain active during auto-mode listening so that saying the send wake phrase finalizes and submits the current transcript. Distinct from MP-322 (which covers "nothing to send" false negatives when the wake word does fire); this issue is that the wake word never fires at all in auto mode. Reproduce by enabling auto mode, speaking a transcript, then saying "Hey Codex send" without pausing — observe that the message is not sent. Physical testing required.
- [ ] MP-336 Add `network-monitor-tui` to the external federation + dev-mode bridge scope: link a pinned `integrations/network-monitor-tui` source, define allowlisted import profile(s) for throughput/latency sampler primitives, expose a read-only metrics surface for `--dev` + phone status views without introducing remote-control side effects, and add isolated runtime mode flags (`--monitor` and/or `--mode monitor`) so monitor/tooling startup does not interfere with the default Whisper voice-overlay path.
- [x] MP-337 Add repeat-to-automate governance and baseline scientific audit program: require repeated manual work to become guarded automation or explicit debt, add tracked `dev/audits/` runbook/register/schema artifacts, ship analyzer tooling (`dev/scripts/audits/audit_metrics.py`) that quantifies script-only vs AI-assisted vs manual execution share with optional chart outputs, and auto-emit per-command `devctl` audit events (`dev/reports/audits/devctl_events.jsonl`) for continuous trend data.
- [ ] MP-338 Stand up a loop-output-to-chat coordination lane: maintain a dedicated runbook for loop suggestion handoff (`dev/active/loop_chat_bridge.md`), define dry-run/live-run evidence capture, and keep operator decisions/next actions append-only so loop guidance can be promoted safely into autonomous execution. (partial: added `devctl autonomy-report` dated digest bundles, upgraded `devctl autonomy-swarm` to one-command execution with default post-audit digest + reserved `AGENT-REVIEW` lane for live runs, added `devctl swarm_run` for guarded plan-scoped swarm + governance + plan-evidence append, added bounded continuous cycle support via `--continuous/--continuous-max-cycles` so runs keep advancing unchecked checklist items until `plan_complete`, `max_cycles_reached`, or `cycle_failed`, wired workflow-dispatch lane `.github/workflows/autonomy_run.yml`, and added `devctl autonomy-benchmark` matrix reports for plan-scoped swarm-size/tactic tradeoff evidence.)
- [ ] MP-340 Deliver one-system operator surfaces + deterministic autonomy learning: keep Rust overlay as runtime primary, keep iPhone/SSH surfaces over one `controller_state` contract, and implement artifact-driven playbook learning (fingerprints, confidence, promotion/decay gates) so repeated loop tasks are reused safely with auditable evidence. (2026-02-26 reset: retired the optional `app/pyside6` desktop command-center scaffold to keep operator execution Rust-first; all active scope now routes through Rust Dev panel + `devctl phone-status` + policy-gated `controller-action`. 2026-02-26 federation follow-up: completed fit-gap audit and added narrow import profiles for targeted `code-link-ide`/`ci-cd-hub` reuse instead of broad tree imports.)
- [ ] MP-341 Runtime architecture hardening pass for product-grade boundaries: tighten `rust/src/lib.rs` public surface (remove legacy re-export drift and prefer internal/facade boundaries), replace stringly `VoiceJobMessage::Error(String)` with typed error categories at subsystem boundaries, harden command parsing (`CustomBackend` quoting-safe parsing), reduce global-side-effect risk in Whisper stderr suppression path, and modernize PyPI launcher distribution flow away from clone+local-build bootstrap toward verified binary delivery. (partial 2026-02-25: hardened SIGWINCH registration via `sigaction` + `SA_RESTART`, removed production `unreachable!()` fallback in Theme Studio non-home renderer path, and reduced silent PTY-output drop risk with explicit unexpected-branch diagnostics.)
- [ ] MP-342 Increase push-to-talk startup grace by about 1 second to prevent early cutoff when users do not speak immediately after pressing PTT: currently first-press captures can end too quickly if there is a short delay before speech starts. Reproduce in Codex/Claude sessions, tune initial-silence/warmup handling for natural speech onset, add regression coverage for delayed speech starts, and verify no regressions for intentional short taps.
- [ ] MP-343 Stabilize screenshot button reliability: screenshot capture currently succeeds intermittently and can stop unexpectedly after some successful attempts. Reproduce repeated capture attempts in active sessions, harden button-triggered capture lifecycle/error handling, add regression coverage for repeated runs, and verify physical behavior with screenshot evidence.
- [ ] MP-344 Re-investigate Cursor mouse-mode scroll behavior and restore reliable wheel/touchpad scrolling when `Mouse` is ON: current reports indicate wheel/touchpad scrolling does not move chat history in Cursor while the draggable scrollbar still works. Document and preserve current workaround (`Mouse` ON + drag scrollbar, or set `Mouse` OFF for touchpad/wheel scrolling and use keyboard button focus with `Enter`), reproduce on Codex/Claude sessions, harden input-mode handling, and add regression coverage for Cursor-specific scroll paths. Scientific baseline seeded on 2026-02-25 via `devctl autonomy-benchmark` run `mp342-344-baseline-matrix-20260225` (covers `MP-342/MP-343/MP-344`; artifacts under `dev/reports/autonomy/benchmarks/mp342-344-baseline-matrix-20260225/`); live control-vs-swarm A/B run captured via `mp342-344-live-baseline-matrix-20260225` plus graph bundle `dev/reports/autonomy/experiments/mp342-344-swarm-vs-solo-20260225/`.
- [x] MP-345 Stand up a visible `data_science` telemetry workspace and continuous devctl metrics refresh so every devctl command contributes to long-run productivity/agent-sizing research: landed `data_science/README.md` workspace docs, new `devctl data-science` command (`summary.{md,json}` + SVG charts), automatic post-command refresh hook in `dev/scripts/devctl/cli.py` (disable with `DEVCTL_DATA_SCIENCE_DISABLE=1`), and weighted agent recommendation scoring from swarm/benchmark history (`success`, `tasks/min`, `tasks/agent`) under `dev/reports/data_science/latest/`; docs/history updated in `AGENTS.md`, `dev/scripts/README.md`, `dev/DEVCTL_AUTOGUIDE.md`, and `dev/history/ENGINEERING_EVOLUTION.md`.

Control-plane program sequencing (maps to MP-330/331/332/336/338/340):

1. Ship canonical multi-view controller state projections (`full/compact/trace/actions`) from one packet source.
2. Add SSH-first/iPhone-safe read surfaces (`phone-status`) and Rust Dev-panel parity for run/agent/policy visibility.
3. Keep desktop GUI clients deferred; route all operator actions through Rust
   surfaces (`--dev`, `phone-status`, `controller-action`) and `devctl` APIs.
4. Add guarded operator actions (`dispatch-report-only`, `pause`, `resume`, `refresh`) with full audit logging.
5. Add reviewer-agent packet ingestion lane so loop-review feedback is machine-consumable, not manual copy/paste.
6. Add charted KPI trend surfaces (loop throughput, unresolved trend, mutation trend, automation-vs-AI mix) for architect decisions.
7. Add deterministic learning loop (`fingerprint -> playbook -> confidence -> guarded promote/decay`) with explicit evidence.
8. Promote staged write controls only after replay protection + branch-protection-aware promotion guards are verified.

## Deferred Plans

- `dev/deferred/DEV_MODE_PLAN.md` (paused until Phases 1-2 outcomes are complete).
- MP-089 LLM-assisted voice-to-command generation (optional local/API provider) is deferred; current product focus is Codex/Claude CLI-native flow quality, not an additional LLM mediation layer.

## Release Policy (Checklist)

1. `rust/Cargo.toml` version bump
2. `dev/CHANGELOG.md` entry finalized
3. Verification pass for change scope
4. Tag + push from `master`
5. GitHub release creation
6. PyPI package publish
7. PyPI publish verification (`https://pypi.org/pypi/voiceterm/<version>/json`)
8. Homebrew tap formula update + push

## Execution Gate (Every Feature)

1. Create or link an MP item before implementation.
2. Implement the feature and add/update tests in the same change.
3. Run SDLC verification for scope:
   `python3 dev/scripts/devctl.py check --profile ci`
4. Run docs coverage check for user-facing work:
   `python3 dev/scripts/devctl.py docs-check --user-facing`
5. Update required docs (`dev/CHANGELOG.md` + relevant guides) before merge.
6. Push only after checks pass and plan/docs are aligned.

## References

- Execution + release tracking: `dev/active/MASTER_PLAN.md`
- Theme Studio architecture + gate checklist + consolidated overlay research/redesign detail: `dev/active/theme_upgrade.md`
- Memory + Action Studio architecture + gate checklist: `dev/active/memory_studio.md`
- Autonomous loop + mobile control-plane execution spec: `dev/active/autonomous_control_plane.md`
- Loop artifact-to-chat suggestion coordination runbook: `dev/active/loop_chat_bridge.md`
- SDLC policy: `AGENTS.md`
- Architecture: `dev/ARCHITECTURE.md`
- Changelog: `dev/CHANGELOG.md`

## Archive Log

- `dev/archive/2026-01-29-claudeaudit-completed.md`
- `dev/archive/2026-01-29-docs-governance.md`
- `dev/archive/2026-02-01-terminal-restore-guard.md`
- `dev/archive/2026-02-01-transcript-queue-flush.md`
- `dev/archive/2026-02-02-release-audit-completed.md`
- `dev/archive/2026-02-17-tooling-control-plane-consolidation.md`
- `dev/archive/2026-02-20-senior-engineering-audit.md`
