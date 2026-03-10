# Operator Console Agents Guide

This file is the local execution guide for `app/operator_console/**`.
Repo-wide policy still comes from the root [AGENTS.md](/Users/jguida941/testing_upgrade/codex-voice/AGENTS.md).
When instructions conflict, follow the root policy first and this file second.

## Purpose

The Operator Console is an optional PyQt6 desktop wrapper around repo-owned
`devctl` workflows, review-channel artifacts, and bounded operator actions.

It is:

- a thin desktop surface over typed repo-owned commands and artifacts
- a read-first control room for review-channel, swarm, and repo state
- allowed to summarize, stage, and guide

It is not:

- a second runtime
- a private command backend
- a place to re-implement PTY/session ownership
- a junk drawer for mixed UI/state/theme/workflow code

## Read Order

When working in this subtree, read in this order:

1. [AGENTS.md](/Users/jguida941/testing_upgrade/codex-voice/AGENTS.md)
2. [dev/active/INDEX.md](/Users/jguida941/testing_upgrade/codex-voice/dev/active/INDEX.md)
3. [dev/active/MASTER_PLAN.md](/Users/jguida941/testing_upgrade/codex-voice/dev/active/MASTER_PLAN.md)
4. [dev/active/operator_console.md](/Users/jguida941/testing_upgrade/codex-voice/dev/active/operator_console.md)
5. [README.md](/Users/jguida941/testing_upgrade/codex-voice/app/operator_console/README.md)
6. The package map for the area you are touching:
   [state/README.md](/Users/jguida941/testing_upgrade/codex-voice/app/operator_console/state/README.md),
   [views/README.md](/Users/jguida941/testing_upgrade/codex-voice/app/operator_console/views/README.md),
   [theme/README.md](/Users/jguida941/testing_upgrade/codex-voice/app/operator_console/theme/README.md),
   [tests/README.md](/Users/jguida941/testing_upgrade/codex-voice/app/operator_console/tests/README.md)

## Package Layout Rules

Organize by responsibility, not by file type.

- `views/` is for Qt widgets, dialogs, window assembly, and UI-only helpers.
- `theme/` is for theme registry, styling runtime, editor widgets, and QSS.
- `state/` is for shared non-Qt data shaping, parsing, snapshots, and models.
- `workflows/` is for command construction, presets, and workflow launch state.
- `collaboration/` is for conversation/task/timeline/context-pack behavior.
- `layout/` is for persisted workbench layout state.
- `tests/` should mirror the runtime package shape.

## Root Package Rules

Keep the package root small.

Allowed to stay at `app/operator_console/` root:

- `run.py` for app entry
- `help_render.py` for launcher/help rendering
- `launch_support.py` for launch/bootstrap helpers
- `logging_support.py` for shared diagnostics/logging
- `README.md` and this file

If a new file sounds like a feature, panel, workflow, state parser, theme
helper, or test target, it should go into a subpackage instead of the root.

## Common Placement Decisions

- Command previews, command builders, and workflow presets go in `workflows/`.
- Repo snapshot readers, lane parsing, activity reports, and session shaping go
  in `state/`.
- Theme editor controls and preview widgets go in `theme/editor/`.
- QSS fragment builders go in `theme/qss/`.
- Shared status cards and reusable widgets go in `views/shared/`.
- Home/Activity workspace surfaces go in `views/workspaces/`.
- Action-button mixins go in `views/actions/`.

## Change Rules

- Keep Qt-free parsing/state logic out of `views/` when practical.
- Keep subprocess/command policy inside typed workflow helpers, not random
  button handlers.
- Prefer extracting helpers before files become large enough to need a shape
  waiver.
- When moving files, update imports to the new package path instead of leaving
  long-term compatibility clutter behind.
- Update the package map README for any directory whose ownership changed.
- Add or move matching tests when you add a new runtime package.

## Validation

For Operator Console changes, prefer these local checks while iterating:

```bash
python3 -m pytest app/operator_console/tests/ -q --tb=short
python3 dev/scripts/checks/check_code_shape.py --format md
python3 dev/scripts/checks/check_active_plan_sync.py
```

If you changed discovery/governance docs, also run:

```bash
python3 dev/scripts/devctl.py docs-check --strict-tooling
```
