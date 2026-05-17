# Standalone Slash Command Plan

**Status**: active standalone delivery lane  |  **Last updated**: 2026-03-21 | **Owner:** Runtime/tooling voice surfaces
Execution plan contract: required

## Scope

- Deliver `/voice` in native Codex CLI and Claude Code sessions without
  requiring the full VoiceTerm PTY overlay.
- Keep runtime voice behavior sourced from existing VoiceTerm voice pipeline
  code (`rust/src/voice.rs`) and avoid duplicate STT implementations.
- Cover both linked MP scopes:
  - `MP-352`: standalone `/voice` and MCP delivery path.
  - `MP-353`: hold-to-talk behavior control through settings/config surfaces.

In scope:

- Phase A: one-shot subprocess capture path (`--capture-once`) and slash
  command templates for Codex/Claude.
- Phase B: standalone runtime MCP server binary (`voiceterm-mcp`) exposing
  voice tools.
- Phase C: packaging/distribution wiring (release artifacts, docs, launcher
  awareness).
- Phase D: MP-353 hold-to-talk setting and runtime behavior wiring.

Out of scope:

- PTY-level slash-menu injection into Codex/Claude UIs.
- Replacing `devctl` with MCP.
- A separate TypeScript "VoiceTerm Lite" product track.

## Architecture Alignment Baseline

Current codebase facts this plan is aligned to:

- Slash command parsing for IPC wrapper mode already supports `/voice` via
  `WrapperCmd::Voice` in `rust/src/ipc/router.rs`.
- Voice capture entrypoint is `start_voice_job()` in `rust/src/voice.rs`.
- JSON IPC command surface already includes `StartVoice` in
  `rust/src/ipc/protocol.rs`.
- `devctl mcp` exists and is intentionally read-only/additive per
  `dev/guides/MCP_DEVCTL_ALIGNMENT.md`.

Non-negotiable architecture constraints:

1. `devctl mcp` remains read-only; it is not extended with write/runtime voice
   actions.
2. Runtime voice MCP is implemented as a separate server binary
   (`voiceterm-mcp`) under Rust runtime ownership.
3. Existing overlay and IPC behavior remain non-regressive (`voiceterm`,
   `--json-ipc`, and `/voice` in wrapper mode keep current behavior).
4. New slash/plugin assets are template/install artifacts, not hidden runtime
   coupling to repo-local `.claude/` or `~/.codex/` paths.

## Implementation Strategy

### Phase A: Standalone `/voice` quick path (MP-352)

Deliverables:

- Add one-shot capture mode:
  - `voiceterm --capture-once --format text`
  - records once, transcribes once, prints output, exits non-interactive.
- Keep implementation in existing binary path (`rust/src/bin/voiceterm/`) and
  reuse `voiceterm::voice`.
- Add installable slash templates in-repo (for example under
  `dev/templates/slash/`) for:
  - Claude skill (`SKILL.md`)
  - Codex slash markdown command
- Add user docs for installation/usage in `guides/USAGE.md` and
  `guides/CLI_FLAGS.md`.

Alignment notes:

- This phase delivers `/voice` picker presence immediately.
- No MCP protocol required in Phase A.
- No changes to `devctl mcp`.

### Phase B: Runtime MCP server (MP-352)

Deliverables:

- Add Rust binary target `voiceterm-mcp` in `rust/Cargo.toml`.
- Implement MCP stdio JSON-RPC server in dedicated runtime path (new module/bin)
  with tool surface:
  - `voice_capture`
  - `voice_status`
  - `voice_mode_set`
- Reuse capture/transcription logic from `rust/src/voice.rs` and existing config
  structures (`rust/src/config/mod.rs`) where practical.
- Add Codex/Claude MCP registration templates and docs.

Alignment notes:

- `voiceterm-mcp` is runtime-level MCP, separate from `devctl mcp`.
- Keep `devctl` as canonical control plane for governance/release automation.

### Phase C: Packaging + distribution alignment (MP-352)

Deliverables:

- Release artifacts:
  - extend `.github/workflows/publish_release_binaries.yml` to publish
    `voiceterm-mcp` artifacts/checksums alongside `voiceterm`.
- Optional launcher support:
  - extend `pypi/src/voiceterm/cli.py` for `voiceterm-mcp` discovery/bootstrap
    only if Phase B UX depends on launcher-managed install.
- Homebrew path:
  - ensure formula update path includes installed `voiceterm-mcp` binary when
    Phase B ships.
- Documentation:
  - add setup instructions for Codex and Claude MCP registration and slash
    template install flow.

Alignment notes:

- Do not ship Phase B without a deterministic install story for both binaries.

### Phase D: Hold-to-talk setting and slash mode control (MP-353)

Deliverables:

- Add hold-to-talk preference to settings/config/CLI surfaces.
- Preserve current default toggle behavior unless explicitly enabled.
- Ensure `voice_mode_set` semantics map cleanly to manual/auto/idle plus
  momentary PTT behavior.
- Add runtime and physical validation guidance for hotkey/press-hold behavior.

Alignment notes:

- MP-353 is a first-class track, not implicit follow-up.

## Decision Log

| Date | Decision | Rationale |
|---|---|---|
| 2026-03-06 | PTY slash-menu injection rejected | File-based slash menus cannot safely callback into PTY wrapper state. |
| 2026-03-06 | Runtime MCP + slash templates selected | Works for both Codex and Claude with one shared voice runtime. |
| 2026-03-06 | `devctl mcp` boundary locked read-only | Prevents duplicate authority and policy drift. |
| 2026-03-06 | MP-353 explicitly added as Phase D | Ensures hold-to-talk behavior is planned, gated, and testable. |

## Execution Checklist

Governance readiness:

- [ ] `check_active_plan_sync` passes for this plan.
- [ ] `docs-check --strict-tooling` passes with this plan updates.
- [ ] MP-352 and MP-353 tracker text remains synchronized in
      `dev/active/MASTER_PLAN.md`.

Phase A (runtime + docs):

- [x] Add `--capture-once` CLI/config wiring.
- [x] Implement one-shot capture execution path.
- [x] Add slash template assets for Claude/Codex.
- [x] Update user docs (`guides/USAGE.md`, `guides/CLI_FLAGS.md`).
- [ ] Run `bundle.runtime` because runtime behavior changes.
- [ ] Run risk add-on: `cd rust && cargo test --bin voiceterm`.

Phase B (runtime MCP server):

- [ ] Add `voiceterm-mcp` binary target and implementation.
- [ ] Implement `voice_capture`, `voice_status`, `voice_mode_set`.
- [ ] Add runtime tests for MCP transport/tool behavior.
- [ ] Add Codex/Claude MCP registration docs/templates.
- [ ] Run `bundle.runtime` and required risk-matrix add-ons.

Phase C (distribution):

- [ ] Extend release binary workflow for `voiceterm-mcp` artifacts/checksums.
- [ ] Update PyPI/Homebrew paths if required by install UX.
- [ ] Update release/docs references for new binary assets.
- [ ] Run `bundle.tooling` for workflow/tooling surface changes.

Phase D (MP-353):

- [ ] Add hold-to-talk setting/config/CLI behavior.
- [ ] Wire behavior into runtime capture controls and mode transitions.
- [ ] Add regression tests for toggle vs hold behavior.
- [ ] Run runtime + input/lifecycle risk tests per AGENTS risk matrix.

Closure gates:

- [ ] Manual validation on Codex and Claude sessions:
  - `/voice` command availability
  - capture success/failure messaging
  - mode switching behavior
  - hold-to-talk behavior (MP-353)
- [ ] Record evidence in this document under `Audit Evidence`.

## Progress Log

- 2026-03-06: Initial research and option matrix documented; confirmed PTY
  menu injection is not viable and selected slash-template + MCP path.
- 2026-03-06: Alignment pass added explicit architecture boundaries, MP-353
  execution track, and release/devctl integration constraints.
- 2026-03-06: Governance gap identified: this plan originally missed required
  `Progress Log` and `Audit Evidence` sections; corrected in this revision.
- 2026-03-06: Post-fix governance reruns are green for active-plan sync and
  strict-tooling docs checks.
- 2026-03-09: Landed the Phase A standalone capture slice in the existing
  `voiceterm` binary: added `--capture-once --format text`, a non-interactive
  one-shot capture path wired through `main.rs`, slash templates under
  `dev/templates/slash/`, and user docs updates in `guides/USAGE.md` and
  `guides/CLI_FLAGS.md`.
- 2026-03-09: Targeted validation is green for the new slice
  (`cargo test --bin voiceterm capture_once` via `devctl guard-run`), but the
  broader runtime gates remain blocked by unrelated branch state:
  `check --profile ci` fails on pre-existing working-tree code-shape and
  function-duplication violations, and `cargo test --bin voiceterm` currently
  fails on the existing theme test
  `theme::style_pack::tests::resolved_toast_severity_mode_returns_none_without_payload_or_override`.

## Session Resume

- Current status: this plan remains active; start from the highest-priority
  open item in `## Execution Checklist` and the latest dated entry in
  `## Progress Log`.
- Next action: keep current-slice decisions and blockers in this file instead
  of chat-only notes, then update this section when the promoted slice
  changes.
- Context rule: treat `dev/active/MASTER_PLAN.md` as tracker authority and
  load only the local sections needed for the active checklist item.

## Audit Evidence

Current session:

- `python3 dev/scripts/checks/check_active_plan_sync.py`:
  - before fix: failed (missing required sections in this file)
  - after fix: pass
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`:
  - before fix: failed due to same active-plan sync error
  - after fix: pass
- `python3 dev/scripts/checks/check_multi_agent_sync.py`:
  - pass

Phase implementation evidence placeholders:

- Phase A command/output bundle:
  - `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test --bin voiceterm capture_once -- --nocapture`
    - pass
  - `python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel`
    - pass
  - `cargo clippy --manifest-path rust/Cargo.toml --bin voiceterm --tests -- -D warnings`
    - fail due unrelated pre-existing warnings-as-errors in `src/legacy_ui.rs`,
      `src/bin/voiceterm/dev_command/broker/mod.rs`,
      `src/bin/voiceterm/dev_panel/mod.rs`,
      `src/bin/voiceterm/wake_word.rs`, and
      `src/bin/voiceterm/dev_command/action_catalog.rs`; after the local
      type-alias follow-up, no `capture_once.rs` clippy violations remained
      in the reported error set
  - `python3 dev/scripts/devctl.py check --profile ci`
    - fail due unrelated working-tree `code-shape-guard`,
      `function-duplication-guard`, and existing clippy blockers outside the
      slash-command slice
  - `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test --bin voiceterm -- --nocapture`
    - fail due existing unrelated runtime test
      `theme::style_pack::tests::resolved_toast_severity_mode_returns_none_without_payload_or_override`
- Phase B command/output bundle: pending.
- Phase C release artifact evidence: pending.
- Phase D hold-to-talk validation notes/screenshots/logs: pending.

## References

- MP-352 / MP-353 tracker entries: `dev/active/MASTER_PLAN.md`
- Active-doc registration: `dev/active/INDEX.md`
- IPC slash parsing: `rust/src/ipc/router.rs`
- IPC protocol: `rust/src/ipc/protocol.rs`
- Voice pipeline: `rust/src/voice.rs`
- App config model: `rust/src/config/mod.rs`
- Overlay CLI flags: `rust/src/bin/voiceterm/config/cli.rs`
- `devctl` MCP contract: `dev/guides/MCP_DEVCTL_ALIGNMENT.md`
- Devctl command surface: `dev/scripts/README.md`
- Release binary workflow: `.github/workflows/publish_release_binaries.yml`
- PyPI launcher: `pypi/src/voiceterm/cli.py`
