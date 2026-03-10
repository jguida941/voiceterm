# Operator Console View Map

This directory is now split by UI responsibility.

- top-level `views/` should stay small and mostly hold window assembly,
  cross-surface glue, and a few leaf dialogs
- `views/shared/`: reusable widgets, status/key-value primitives, and text
  scroll helpers
- `views/workspaces/`: guided Home and Activity workspace surfaces
- `views/actions/`: action mixins for command launch, review flows, swarm
  status, and process completion handling
- `views/collaboration/`: conversation, task board, timeline, and the signal
  handlers that post collaboration actions into the guarded command pipeline
- `views/workflow/`: workflow controls, launchpads, and shared workflow chrome
- `views/layout/`: layout registry, layout persistence, workbench assembly, and
  shell chrome
- `main_window.py`, `ui_pages.py`, `ui_refresh.py`: shared window assembly that
  stitches the feature packages together
- `agent_detail.py`, `approval_panel.py`, `help_dialog.py`,
  `tutorial_overlay.py`: standalone dialogs/panels that do not yet justify a
  deeper package

Rule: if a view file belongs to one obvious product surface, it should move
into a responsibility subpackage instead of staying flat forever.

Root `views/` is not a parking lot.

Keep files at the top only when they are:

- cross-surface window assembly
- a small standalone dialog/panel
- shared glue that would create circular imports if forced deeper

If a file is mainly about Home, Activity, commands, review, layout, workflow,
or collaboration, move it into the matching subpackage.
