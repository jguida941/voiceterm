Translate this slash command into the typed repo command:

```bash
python3 dev/scripts/devctl.py develop $ARGUMENTS
```

This file is only an adapter. Do not place /develop policy here. The authority
lives in `DevelopmentModeTopology`, `DevelopmentLoopReport`, MP-377 active
plans, review-channel typed state, and repo-pack governance.

Use the command as read-only unless the typed output gives a governed next
command. For a default status pass, run:

```bash
python3 dev/scripts/devctl.py develop --status --format md
```
