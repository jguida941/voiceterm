# Voice Input

Use VoiceTerm's standalone capture path when the operator wants one-shot voice
input without the full overlay.

## Command

```bash
voiceterm --capture-once --format text
```

## Behavior

- Run the command once per `/voice` request.
- If it exits `0` and prints non-empty stdout, treat that transcript as the
  next prompt draft.
- If it exits non-zero or produces no transcript, show the failure text and
  stop instead of sending an empty prompt.
- Do not rewrite the transcript beyond trimming the trailing newline from
  stdout.
