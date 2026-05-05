# Remote Bridge Prompt Compatibility Note

`dev/scripts/remote-bridge-loop.sh` no longer syncs this file into Claude slash
commands. Remote-control lifecycle policy lives in:

```bash
python3 dev/scripts/devctl.py remote-control --help
```

Tracked slash adapters are generated from repo-pack surface policy:

- `.claude/commands/typed-remote-control.md`
- `dev/templates/slash/remote-control/commands.md`
