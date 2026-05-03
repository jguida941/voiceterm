Translate this slash command into the typed repo command:

```bash
python3 dev/scripts/devctl.py develop --actor claude $ARGUMENTS
```

This file is only an adapter. Do not place /develop policy here. The authority
lives in `DevelopmentModeTopology`, `DevelopmentLoopReport`, MP-377 active
plans, review-channel typed state, and repo-pack governance.

Role-specific slash entries must use the shared role adapter matrix from
`dev/scripts/devctl/runtime/development_role_adapters.py`; the generated
provider-neutral catalog is `dev/templates/slash/develop/roles.md`. Codex and
Claude role shortcuts must not fork their own role-to-mode map.

`/develop watch` may render peer `agent-mind` context, but that context is
auxiliary only. Runtime authority remains the packet lifecycle, work-board,
sync-status, session posture, and repo-pack governance rows.

Use the command as read-only unless the typed output gives a governed next
command. For a default status pass, run:

```bash
python3 dev/scripts/devctl.py develop --actor claude --status --format md
```
