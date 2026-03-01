# Dev Mode Guide

Use this guide when you run VoiceTerm with `--dev` and want to use the in-session Dev panel safely.

## Purpose

Dev mode is for maintainers and power users who need quick runtime diagnostics and guarded tooling access without leaving the active terminal session.

It is not required for normal voice-to-chat usage.

## Start Dev Mode

```bash
voiceterm --dev
voiceterm --dev --dev-log
voiceterm --dev --dev-log --dev-path ~/.voiceterm/dev
```

Expected sign that Dev mode is active:

- Full HUD shows a `DEV` badge.

Important:

- `Ctrl+D` opens the Dev panel only when `--dev` is active.
- Without `--dev`, `Ctrl+D` is forwarded as EOF (`0x04`) to the wrapped CLI and may close/exit that session.

## Dev Panel Controls

- `Ctrl+D`: open/close Dev panel
- `Up`/`Down`: move command selection
- `1-9`: direct command select
- `Enter`: run selected command
- `X`: cancel a running command
- `Esc`: close panel

Guard behavior:

- `sync` is mutating and requires pressing `Enter` twice (confirm + run).

## What Each Dev Tool Does

| Tool | devctl command | Mutating | What to use it for |
|---|---|---|---|
| `status` | `python3 dev/scripts/devctl.py status --ci --format json` | no | Quick CI + repo status snapshot |
| `report` | `python3 dev/scripts/devctl.py report --ci --format json` | no | Richer project report with rollups |
| `triage` | `python3 dev/scripts/devctl.py triage --ci --format json --no-cihub` | no | Summarize issues by severity/category/owner |
| `loop-packet` | `python3 dev/scripts/devctl.py loop-packet --format json` | no | Generate loop feedback packet text for guided next-step planning |
| `security` | `python3 dev/scripts/devctl.py security --format json --offline` | no | Run local security policy checks |
| `sync` | `python3 dev/scripts/devctl.py sync --format json` | yes | Branch sync automation (`develop`/`master` + current branch) |

## How To Read The Panel

- `Session stats`: counters from current VoiceTerm session (`transcript`, `empty`, `error`, average latency, buffered events).
- `Active`: current command state (`idle`, `running`, or confirmation state).
- `Last`: summary of the most recent command result plus a short output excerpt.

Why `Last` can look noisy:

- Dev tools return machine-readable JSON, so excerpts can include JSON fragments.
- This is expected and is meant to show what the command returned without leaving the panel.

## Loop-Packet Behavior

`loop-packet` can generate draft text intended for planning/remediation prompts.

Current behavior:

- The draft may be staged into the active terminal input area, which can look like VoiceTerm is typing into chat.

Use it when you explicitly want that draft text.
Skip it during normal prompt composition if you do not want staged planning text.

## Troubleshooting

### `Ctrl+D` closes backend instead of opening Dev panel

- You launched without `--dev`.
- Restart with `voiceterm --dev`.

### `json-error` appears for a command

- The command returned output that was not parseable JSON.
- Run the same command directly in terminal to inspect full output, for example:

```bash
python3 dev/scripts/devctl.py security --format json --offline
```

### Dev panel shows command output but not enough context

- Re-run the command directly in terminal for full output.
- For CI snapshots, also run:

```bash
python3 dev/scripts/devctl.py triage --ci --format md --output /tmp/dev-triage.md
```
