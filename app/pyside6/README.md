# VoiceTerm Command Center (PySide6)

This directory contains an optional desktop command center for VoiceTerm
control-plane operations.

The Rust overlay remains the primary runtime UI. This app is for operator
control and visibility:

- run `devctl` control-plane commands
- inspect recent GitHub workflow runs
- run guarded git workflows from one place
- execute ad-hoc terminal commands in a dedicated tab

Current tabs:

- `Quick Ops`: one-click high-frequency commands
- `Catalog`: searchable command inventory across repo workflows
- `GitHub Runs`: workflow-run table for key CI lanes
- `Git`: common branch sync/push/pull operations
- `Terminal`: ad-hoc command execution

## Status

This is an initial scaffold for `MP-340` (operator surfaces parity track).
It is intentionally focused on read-first operations plus explicit command
execution.

## Install

```bash
python3 -m pip install PySide6
```

## Run

From repo root:

```bash
python3 app/pyside6/run.py
```

## Notes

- Commands run with repository root as working directory.
- Command execution is non-blocking (`QProcess`) so the UI stays responsive.
- This client does not replace policy gates in `devctl`; it sits on top of
  existing tooling contracts.
