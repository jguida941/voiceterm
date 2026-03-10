# Operator Console State Map

This directory is no longer meant to be a junk drawer.

Use `state/` for shared data models and grouped parsing/snapshot helpers that
are still used across multiple Operator Console surfaces.

Current layout:

- `core/`: shared dataclasses, readability, coercion
- `activity/`: human-readable activity report builders
- `bridge/`: bridge-section parsing and lane assembly
- `jobs/`: background refresh job coordination
- `presentation/`: banner/status/analytics presentation shaping
- `repo/`: repo-state snapshots
- `review/`: approvals, artifact lookup, operator decision state
- `sessions/`: session builders and trace readers
- `snapshots/`: analytics, phone, quality, merged snapshot builders

`state/` root itself should stay small: `README.md`, `__init__.py`, and
subdirectories only.

Do not add new files to the root when they clearly belong somewhere more
specific.

- Put workflow launch/report logic in `app/operator_console/workflows/`.
- Put conversation/task/timeline/context-pack logic in
  `app/operator_console/collaboration/`.
- Put persisted layout helpers in `app/operator_console/layout/`.

Current rule: if a file name starts to sound like a product feature or a user
workflow instead of shared state, it probably should not live in `state/`.

Keep the root of `state/` limited to:

- `README.md`
- `__init__.py`
- subdirectories only

If you feel tempted to add a new root file here, that is usually a sign the
package boundary is wrong.
