# Remote-Control Slash Adapter Catalog

Provider slash files are thin adapters over `devctl remote-control`.
They do not own lifecycle policy, role maps, launch authority, or approval rules.

| Provider | Slash command | Backend command | Alias |
|---|---|---|---|
| claude | `/project:typed-remote-control` | `python3 dev/scripts/devctl.py remote-control enter --provider claude --entrypoint /project:typed-remote-control` | no |

