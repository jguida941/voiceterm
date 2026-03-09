# Slash Templates

These Phase-A templates let Codex and Claude use VoiceTerm's standalone
one-shot capture path without launching the full PTY overlay.

Common command:

```bash
voiceterm --capture-once --format text
```

Behavior contract:

- On success, the command prints one trimmed transcript line to stdout.
- On empty capture or microphone/STT failure, the command exits non-zero and
  prints the reason to stderr.
- Callers should not auto-send anything when the command fails or returns no
  transcript.

Template assets:

- `codex/voice.md`: markdown command template for a native Codex `/voice` flow.
- `claude/SKILL.md`: skill template for Claude-side voice capture workflow.
