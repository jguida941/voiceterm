# /develop Role Adapters

This generated catalog is the shared source for provider slash surfaces that
want role-specific `/develop` entrypoints. Provider command files may wrap one
row from this catalog, but they must not carry policy, provider defaults,
permissions, polling cadence, or repo-local path authority.

Provider-neutral role adapter catalog.

Canonical source: `CollaborationModeTopology` plus `development_role_adapters.py`.
Codex and Claude consume the same role-to-mode map; provider slash files are thin adapters only.

## codex

- `dashboard` -> `python3 dev/scripts/devctl.py develop --actor codex --role-preset dashboard --collaboration-mode dashboard_led $ARGUMENTS`
- `implementer` -> `python3 dev/scripts/devctl.py develop --actor codex --role-preset implementer --collaboration-mode pair_review $ARGUMENTS`
- `reviewer` -> `python3 dev/scripts/devctl.py develop --actor codex --role-preset reviewer --collaboration-mode pair_review $ARGUMENTS`
- `architect` -> `python3 dev/scripts/devctl.py develop --actor codex --role-preset architect --collaboration-mode research_fanout $ARGUMENTS`
- `researcher` -> `python3 dev/scripts/devctl.py develop --actor codex --role-preset researcher --collaboration-mode research_fanout $ARGUMENTS`
- `intake` -> `python3 dev/scripts/devctl.py develop --actor codex --role-preset intake --collaboration-mode intake_fanout $ARGUMENTS`
- `tester` -> `python3 dev/scripts/devctl.py develop --actor codex --role-preset tester --collaboration-mode review_fanout $ARGUMENTS`
- `watcher` -> `python3 dev/scripts/devctl.py develop --actor codex --role-preset watcher --collaboration-mode watcher_fanout $ARGUMENTS`
- `operator` -> `python3 dev/scripts/devctl.py develop --actor codex --role-preset operator --collaboration-mode dashboard_led $ARGUMENTS`

## claude

- `dashboard` -> `python3 dev/scripts/devctl.py develop --actor claude --role-preset dashboard --collaboration-mode dashboard_led $ARGUMENTS`
- `implementer` -> `python3 dev/scripts/devctl.py develop --actor claude --role-preset implementer --collaboration-mode pair_review $ARGUMENTS`
- `reviewer` -> `python3 dev/scripts/devctl.py develop --actor claude --role-preset reviewer --collaboration-mode pair_review $ARGUMENTS`
- `architect` -> `python3 dev/scripts/devctl.py develop --actor claude --role-preset architect --collaboration-mode research_fanout $ARGUMENTS`
- `researcher` -> `python3 dev/scripts/devctl.py develop --actor claude --role-preset researcher --collaboration-mode research_fanout $ARGUMENTS`
- `intake` -> `python3 dev/scripts/devctl.py develop --actor claude --role-preset intake --collaboration-mode intake_fanout $ARGUMENTS`
- `tester` -> `python3 dev/scripts/devctl.py develop --actor claude --role-preset tester --collaboration-mode review_fanout $ARGUMENTS`
- `watcher` -> `python3 dev/scripts/devctl.py develop --actor claude --role-preset watcher --collaboration-mode watcher_fanout $ARGUMENTS`
- `operator` -> `python3 dev/scripts/devctl.py develop --actor claude --role-preset operator --collaboration-mode dashboard_led $ARGUMENTS`
