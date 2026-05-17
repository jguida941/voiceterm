# Commands

Owns executable `devctl` command handlers.

- Keep the root for stable command entrypoints and thin compatibility wrappers.
- When a flat family gets crowded, move implementation into a topical
  namespace such as `check/`, `autonomy/`, `docs/`, `review_channel/`,
  `release/`, `governance/`, or `process/`.
- Parser-only code belongs in `../cli_parser/`.
- Shared domain logic belongs in the owning subpackage, not here.
