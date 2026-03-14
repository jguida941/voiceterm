# /voice

Capture one prompt with {{product_name}} and use the transcript as the next
Codex input draft.

## Command

```bash
{{voice_command}}
```

## Contract

- If the command exits `0` and prints non-empty stdout, use that text as the
  next prompt draft.
- If the command exits non-zero or prints no transcript, surface the stderr
  message and do not send anything automatically.
- Keep the transcript verbatim except for trimming the trailing newline added
  by stdout.
