---
description: Govern Claude's built-in /remote-control and record typed lifecycle state
allowed-tools: Bash(python3 dev/scripts/devctl.py remote-control:*)
---

Primary operator workflow: type Claude's built-in `/remote-control` or `/rc`.
The project `.claude/settings.json` `UserPromptExpansion` hook, with
`UserPromptSubmit` as fallback, mirrors that real Claude prompt into
`devctl remote-control hook`, waits for a fresh same-session provider session
URL in the transcript, and records typed lifecycle state automatically.
Restart existing Claude sessions after this project hook is first added or
changed so Claude loads the settings.

Claude project slash commands cannot programmatically invoke the built-in
`/remote-control` command. If the phone/app connection is not already active
and the hook is unavailable, the operator must run Claude's built-in
remote-control flow manually:

`/remote-control`

After the real remote-control session exposes a provider session URL or remote
session id, this advanced/manual recovery command records typed state so
startup-context, review-channel, and SessionPosture all agree on operator
location:

```bash
python3 dev/scripts/devctl.py remote-control enter --provider claude --entrypoint /project:typed-remote-control --launcher-source claude_project_slash $ARGUMENTS
```

This is a heartbeat / reattach attempt, not an unconditional promotion.
When invoked without ``--remote-session-id`` / ``--session-url``, the
backend fails closed with ``state_change=evidence_missing`` because project
slash transcript evidence is not physical remote-control evidence. The
``--launcher-source claude_project_slash`` flag records a CLAIMED source kind
in the receipt for audit narrative; non-user-controllable transcript
correlation supplies slash-origin proof, while ``--session-url`` or
``--remote-session-id`` supplies the physical remote-control identity.
Direct ``--physical-remote-control-confirmed`` is only an
``operator_assertion`` recovery hint; the physical dogfood gate requires
``physical_confirmation_method=claude_hook_transcript`` from the hook and
fresh transcript URL.

This file is only an adapter. Do not place remote-control policy here. The
authority lives in `devctl remote-control`,
`runtime/remote_control_attachment_models.RemoteControlAttachmentState`,
`SessionPosture`, review-channel typed state, and repo-pack governance.

Use `heartbeat` only when the typed output asks for a refresh:

```bash
python3 dev/scripts/devctl.py remote-control heartbeat --provider claude --entrypoint /project:typed-remote-control --launcher-source claude_project_slash --format md
```

No project `/remote-control` or `/bridge-loop` alias is installed. Claude's
provider-owned `/remote-control` and `/rc` must win the unqualified command
names, while this project command remains the manual typed-state recovery path.
