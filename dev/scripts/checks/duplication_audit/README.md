# Duplication Audit

Helper logic for `check_duplication_audit.py`.

- Keep the public guard entrypoint at
  `dev/scripts/checks/check_duplication_audit.py`.
- Keep report parsing, candidate discovery, and jscpd execution helpers under
  `dev/scripts/checks/duplication_audit/` so the crowded checks root stays
  reserved for stable runnable entrypoints.
