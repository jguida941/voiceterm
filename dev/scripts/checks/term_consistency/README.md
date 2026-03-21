# Term Consistency

Helper logic for `probe_term_consistency.py`.

- Keep the public probe entrypoint at
  `dev/scripts/checks/probe_term_consistency.py`.
- Keep the implementation under
  `dev/scripts/checks/term_consistency/command.py` so the crowded
  `checks/` root stays a thin wrapper surface.
- Keep rule parsing in `config.py`, state/delta math in `state.py`, path
  matching in `path_rules.py`, and hint rendering in `hints.py`. The
  `analysis.py` module stays as a thin compatibility surface over those
  focused helpers.
- The probe has two lenses:
  inventory reports remaining terminology debt in the resulting file, and
  delta classifies whether the patch introduced, worsened, left unchanged, or
  improved that debt.
- Adoption scans are inventory-only. Commit-range and working-tree scans are
  before/after aware and use the rename-aware base-path map from
  `git_change_paths.py`.
