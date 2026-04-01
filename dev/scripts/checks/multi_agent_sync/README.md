# multi_agent_sync

Package-owned implementation for the `check_multi_agent_sync.py` guard.

Why this package exists:

- the public `dev/scripts/checks/` root is crowded and reserved for stable
  entrypoints
- multi-agent sync now validates both markdown-lane parity and typed runtime
  truth, which is too much implementation to keep growing in the flat root

Public entrypoint:

- `dev/scripts/checks/check_multi_agent_sync.py`
