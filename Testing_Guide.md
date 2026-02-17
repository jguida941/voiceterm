# VoiceTerm Audit Runbook (Post v1.0.64, current release candidate)

Use this as the manual test script before release.
Run in order. Mark each step `PASS` or `FAIL`.

## 0. Scope

This runbook verifies:

- User-facing behavior added in `v1.0.64` through the current release candidate (`v1.0.70` and newer).
- Backend worker lifecycle hardening (`v1.0.70`) for normal exit and abrupt termination paths.
- Phase 2B hardening closure (`FX-001..FX-012`) remains tracked.
- Built-in voice navigation and `responding` behavior.
- Macro system behavior (packs + wizard + precedence + GitHub integration).
- Cursor-specific known-open regressions tracked in backlog (`MP-145`, `MP-146`, `MP-147`).
- Local release-quality gates, release-note tooling, and workflow status.

## 1. Preflight (once)

1. Confirm repo/branch and version:

```bash
pwd
git branch --show-current
git status --short
rg -n '^version\s*=\s*"' src/Cargo.toml pypi/pyproject.toml
```

1. Build release binary:

```bash
cd src
cargo build --release --bin voiceterm
cd ..
```

1. Confirm CLI/auth tooling state:

```bash
codex --version || true
claude --version || true
gh --version || true
gh auth status -h github.com || true
```

1. Test matrix minimum (physical):

- Cursor + Codex backend
- Cursor + Claude backend
- JetBrains terminal (PyCharm/IntelliJ/CLion/WebStorm) for non-regression checks

Expected:

- Build succeeds.
- Missing `gh` auth is acceptable for warning-path tests.

## 2. Launch + Backend Matrix

Run both backend launch paths from `src/`:

```bash
./target/release/voiceterm --codex
./target/release/voiceterm --claude
```

For each backend, confirm:

- HUD renders correctly.
- No startup corruption.
- Prompt is usable.
- Help/settings/theme overlays open and close cleanly.

## 3. Backend Worker Lifecycle (Critical)

This section validates the orphan-worker fix for repeated sessions and abrupt terminal death.

1. Baseline process snapshot before launch:

```bash
ps -axo pid,ppid,pgid,command | rg 'voiceterm|codex-aarch64-apple-darwin|claude' || true
```

1. Start one session in Terminal A:

```bash
cd src
./target/release/voiceterm --codex
```

1. In Terminal B, capture PID/PGID for that session:

```bash
VOICE_PID="$(pgrep -fn 'target/release/voiceterm --codex')"
VOICE_PGID="$(ps -o pgid= -p "$VOICE_PID" | tr -d ' ')"
echo "voice_pid=$VOICE_PID voice_pgid=$VOICE_PGID"
ps -axo pid,ppid,pgid,command | awk -v pg="$VOICE_PGID" '$3==pg {print}'
```

1. Normal exit path (graceful):

- Quit VoiceTerm with `Ctrl+Q` in Terminal A.
- Re-check process group:

```bash
sleep 2
ps -axo pid,ppid,pgid,command | awk -v pg="$VOICE_PGID" '$3==pg {print}'
```

Expected:

- No `voiceterm` or `codex` workers remain in that PGID.

1. Abrupt termination path (simulates terminal trash / crash):

- Relaunch VoiceTerm (`--codex`) in Terminal A.
- Re-capture `VOICE_PID` / `VOICE_PGID`.
- Kill VoiceTerm from Terminal B:

```bash
kill -9 "$VOICE_PID"
sleep 3
ps -axo pid,ppid,pgid,command | awk -v pg="$VOICE_PGID" '$3==pg {print}'
```

Expected:

- PTY child/descendants in that process group are gone within a few seconds.
- No long-lived orphan `codex-aarch64-apple-darwin` process tied to that killed session remains.

1. Multi-session isolation check (matches your 3-terminal concern):

- Open 3 terminals and run `voiceterm --codex` in all three.
- In a fourth terminal, map each session:

```bash
for pid in $(pgrep -f 'target/release/voiceterm --codex'); do
  pgid="$(ps -o pgid= -p "$pid" | tr -d ' ')"
  echo "session pid=$pid pgid=$pgid"
  ps -axo pid,ppid,pgid,command | awk -v pg="$pgid" '$3==pg {print "  " $0}'
done
```

- Kill only one terminal/session (UI trash/right-click kill or `kill -9 <that voice pid>`).
- Verify only that session PGID disappears; the other two remain alive.

Expected:

- Cleanup is per-session, not global.
- Remaining active sessions continue functioning.

## 4. Core UX Checks

1. Theme quick-cycle:

- Press `Ctrl+G` 5-10 times.
- Expected: theme changes every press, no stuck state.

1. Send mode labels:

- Press `Ctrl+T` and confirm status switches between auto/edit messaging.
- Expected: left mode lane remains stable (`PTT`/`AUTO`/`IDLE`) while active state text appears in status message lane.

1. Empty-capture status text:

- Press `Ctrl+R`, do not speak, stop capture.
- Expected: `No speech detected` appears without Rust/Python pipeline label text.

## 5. Voice State + Responding

1. Insert mode should not show false responding:

- Set send mode to insert (`Ctrl+T` until insert/edit).
- Press `Ctrl+R`, speak: `insert mode test`.
- Stop recording.
- Expected: transcript injects, `responding` does not appear yet.

1. Submit path should show responding:

- Press `Enter` once.
- Expected: `responding` appears, then clears to idle/ready when backend output arrives.

1. Auto mode should show responding on send:

- Toggle to auto.
- Press `Ctrl+R`, speak short phrase.
- Expected: auto-send occurs, `responding` appears, then clears.

## 6. Built-in Voice Navigation

1. Create scrollable output:

```bash
seq 1 200
```

1. Speak exact phrases:

- `scroll up`
- `scroll down`

Expected:

- PageUp/PageDown behavior in correct direction.

1. Force an error line (for error commands):

```bash
git checkout definitely-not-a-real-branch
```

1. Speak:

- `show last error` -> HUD status shows captured error line.
- `copy last error` -> verify clipboard:

```bash
pbpaste
```

- `explain last error` -> submits prompt and shows `responding`.

Linux clipboard note: verify `wl-copy`/`xclip`/`xsel` fallback path.

## 7. Macro Engine Semantics

1. Confirm default safety behavior:

- Open settings (`Ctrl+O`).
- Confirm `Macros` starts `OFF` after startup.

1. Precedence test (macro beats built-in):

```bash
mkdir -p .voiceterm
cat > .voiceterm/macros.yaml <<'YAML'
macros:
  scroll up: echo macro_won
YAML
```

- Set `Macros` = `ON`.
- Speak `scroll up`.
- Expected: macro expansion wins (built-in navigation does not fire).

1. Explicit built-in override phrase:

- Speak `voice scroll up`.
- Expected: built-in navigation executes.

1. Mode override behavior (insert-safe macro):

```bash
cat > .voiceterm/macros.yaml <<'YAML'
macros:
  commit with message:
    template: "git commit -m '{TRANSCRIPT}'"
    mode: insert
YAML
```

- Keep global send mode on auto.
- Speak `commit with message test message`.
- Expected: text inserts but does not auto-submit.

## 8. Wizard + Pack Validation

Run from repo root.

1. List packs:

```bash
./scripts/macros.sh list
```

1. Install each pack and validate:

```bash
./scripts/macros.sh install --pack safe-core --project-dir . --output /tmp/voiceterm-safe.yaml --overwrite
./scripts/macros.sh install --pack power-git --project-dir . --output /tmp/voiceterm-power.yaml --overwrite
./scripts/macros.sh install --pack full-dev --project-dir . --output /tmp/voiceterm-full.yaml --overwrite

./scripts/macros.sh validate --output /tmp/voiceterm-safe.yaml --project-dir .
./scripts/macros.sh validate --output /tmp/voiceterm-power.yaml --project-dir .
./scripts/macros.sh validate --output /tmp/voiceterm-full.yaml --project-dir .
```

1. Check placeholder rendering:

```bash
rg '__[A-Z0-9_]+__' /tmp/voiceterm-safe.yaml /tmp/voiceterm-power.yaml /tmp/voiceterm-full.yaml || true
```

Expected:

- No unresolved placeholder tokens for this repo context.

1. GH readiness behavior:

- If unauthenticated: wizard/validate warns to run `gh auth login`.
- If authenticated: validates repo access via `gh repo view <owner/name>`.

1. Interactive wizard path:

```bash
./scripts/macros.sh wizard --pack full-dev
```

Expected:

- Prompts for project/repo values.
- Writes `.voiceterm/macros.yaml`.
- Ends with structure validation success.

## 9. Install Flow Macro Onboarding

1. Check install command help includes wizard flags:

```bash
./scripts/setup.sh --help
```

Expected options:

- `--with-macros-wizard`
- `--macros-pack <safe-core|power-git|full-dev>`

1. Optional live test:

```bash
./scripts/install.sh --with-macros-wizard --macros-pack full-dev
```

Expected:

- Install completes.
- Wizard launches and writes macro file.

## 10. Pack Smoke Tests (Voice Phrases)

With `Macros = ON`, test at least these phrases.

### safe-core

- `show git status`
- `show changed files`
- `list pull requests`
- `list review requests`
- `show workflow failures`

### power-git

- `create feature branch test-voice-branch`
- `commit with message test commit`
- `open pull request test pr title`
- `approve pull request looks good`
- `rerun failed checks`

### full-dev

- `run ci checks`
- `run docs check`
- `check mutation score`
- `run security audit`
- `build release binary`

Expected:

- Trigger phrases map to intended commands.
- Risky actions remain insert mode where defined.

## 11. Cursor/JetBrains Open-Issue Tracking (Physical)

These checks are required for backlog tracking and non-regression evidence.

1. `MP-145` startup handoff artifact check:

- Run in Cursor for both `--codex` and `--claude`.
- Observe the exact window after splash teardown and before full HUD readiness.
- Record whether cursor/ANSI escape artifacts appear.

1. `MP-146` controls bracket readability:

- In each theme, verify `[` `]` control brackets remain visible.
- In arrow/focus-selected state, verify contrast is strong enough to scan quickly.

1. `MP-147` mouse-mode scroll conflict + JetBrains non-regression:

- In Cursor with mouse mode `ON`, test wheel/trackpad scroll in chat output.
- Toggle mouse mode `OFF` and compare scroll behavior.
- In JetBrains with mouse mode `ON`, verify scrolling still works (must not regress).

Expected:

- Cursor findings are logged with backend + terminal + screenshot evidence.
- JetBrains remains a non-regressed baseline.

## 12. Rust Hardening Closure Status

1. Verify active/follow-up items are tracked in `MASTER_PLAN`:

```bash
rg -n 'MP-127|MP-128|MP-129|MP-130|MP-131|MP-132|MP-133|MP-134|MP-135|MP-136|MP-137|MP-138' dev/active/MASTER_PLAN.md
rg -n 'MP-015|MP-145|MP-146|MP-147|MP-157|MP-158|MP-159|MP-160' dev/active/MASTER_PLAN.md
```

Expected:

- `MP-127..MP-138` are present and completed in plan history.
- `MP-015` present as current mutation-hardening execution focus.
- `MP-145`, `MP-146`, `MP-147` present in backlog.
- `MP-157..MP-160` present as active tooling-consolidation work.

1. Verify archived audit record exists (reference only):

```bash
ls -la dev/archive/2026-02-15-rust-gui-audit.md
```

## 13. Release Tooling Validation (No-Push Safe Checks)

1. Verify release-notes generation via devctl:

```bash
python3 dev/scripts/devctl.py release-notes --version <VERSION> --output /tmp/voiceterm-release-v<VERSION>.md
rg -n '^## Range|^## Diff Summary|^## Changelog Section|^## Commits|^## Changed Files' /tmp/voiceterm-release-v<VERSION>.md
```

1. Verify direct script path is still functional:

```bash
./dev/scripts/generate-release-notes.sh <VERSION> --output /tmp/voiceterm-release-script-v<VERSION>.md
```

1. Verify release/homebrew wrappers are callable in dry-run mode:

```bash
python3 dev/scripts/devctl.py release --version <VERSION> --dry-run --yes
python3 dev/scripts/devctl.py homebrew --version <VERSION> --dry-run --yes
```

Expected:

- Release notes markdown is generated and structured.
- devctl wrappers execute dry-run successfully without mutating git/tags.

## 14. Local Release Gates

Run before shipping:

```bash
python3 dev/scripts/devctl.py check --profile ci
python3 dev/scripts/devctl.py check --profile prepush
python3 dev/scripts/devctl.py check --profile release
python3 dev/scripts/devctl.py mutation-score --threshold 0.80
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py hygiene

cd src
cargo test pty_session::tests::pty_cli_session_drop_terminates_descendants_in_process_group -- --nocapture
cargo test pty_session::tests::pty_overlay_session_drop_terminates_descendants_in_process_group -- --nocapture
cargo test pty_session::tests::pty_overlay_session_parent_sigkill_terminates_child -- --nocapture
cd ..
```

Expected:

- All pass.
- Mutation score `>= 0.80`.
- PTY lifecycle regression tests pass for descendant cleanup and parent-crash paths.

## 15. GitHub Workflow Audit

1. Check release commit SHA:

```bash
git rev-parse --short HEAD
```

1. Verify workflow results for that SHA:

```bash
gh run list --branch master --limit 50 --json headSha,workflowName,status,conclusion,url | jq -r '.[] | select(.headSha|startswith("<SHA>")) | "\(.workflowName) | \(.status) | \(.conclusion // "-") | \(.url)"'
```

Minimum required green:

- Rust TUI CI
- Security Guard
- Voice Mode Guard
- Parser Fuzz Guard
- Perf Smoke
- Memory Guard
- Latency Guardrails
- docs_lint

Mutation lane check (scheduled/manual):

```bash
gh run list --workflow "Mutation Testing" --branch master --limit 5
```

## 16. Restart/Reset Behavior

1. Quit with `Ctrl+Q`.
2. Relaunch VoiceTerm.
3. Confirm:

- No stale `responding`/recording state.
- HUD/status is clean.
- Macros default to startup-safe `OFF` unless toggled.

## 17. Pass/Fail Template

Copy this per run:

```text
Date:
Tester:
Version:
Commit:
Terminal(s):
Backend(s):

Worker lifecycle normal-exit cleanup: PASS/FAIL
Worker lifecycle abrupt-kill cleanup: PASS/FAIL
Worker lifecycle multi-session isolation: PASS/FAIL
Core UX: PASS/FAIL
Responding state: PASS/FAIL
Built-in voice nav: PASS/FAIL
Macro precedence: PASS/FAIL
Wizard + packs: PASS/FAIL
Install wizard flow: PASS/FAIL
Cursor startup artifacts (MP-145): PASS/FAIL
Bracket readability (MP-146): PASS/FAIL
Mouse-mode scroll conflict (MP-147): PASS/FAIL
JetBrains non-regression: PASS/FAIL
Release notes generation: PASS/FAIL
FX-001..FX-012 closure check: PASS/FAIL
Local release gates: PASS/FAIL
GitHub workflows: PASS/FAIL

Notes / failures:
```
