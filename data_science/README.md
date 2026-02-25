# Data Science Workspace

Purpose: keep one visible home for long-range productivity analytics and
agent-sizing research in this repo.

## What runs automatically

- Every `python3 dev/scripts/devctl.py <command>` invocation now appends an
  audit event (existing behavior) and refreshes a data-science snapshot
  (new behavior).
- Auto snapshot output path (local, generated):
  `dev/reports/data_science/latest/`.

Generated artifacts include:

- `summary.md` and `summary.json`
- command-frequency chart (`command_frequency.svg`)
- agent recommendation charts (`agent_recommendation_score.svg`,
  `agent_tasks_per_minute.svg`)
- rolling history log (`dev/reports/data_science/history/snapshots.jsonl`)

## Manual rebuild command

```bash
python3 dev/scripts/devctl.py data-science --format md
```

Useful flags:

- `--max-events <n>`: cap sampled devctl events
- `--swarm-root <path>`: choose swarm summary root
- `--benchmark-root <path>`: choose benchmark summary root
- `--output-root <path>`: write generated outputs elsewhere

## Environment controls

- `DEVCTL_DATA_SCIENCE_DISABLE=1` disables auto refresh.
- `DEVCTL_DATA_SCIENCE_OUTPUT_ROOT=<path>` overrides auto output root.
- `DEVCTL_DATA_SCIENCE_EVENT_LOG=<path>` overrides event-log source.
- `DEVCTL_DATA_SCIENCE_SWARM_ROOT=<path>` overrides swarm-summary source root.
- `DEVCTL_DATA_SCIENCE_BENCHMARK_ROOT=<path>` overrides benchmark source root.
- `DEVCTL_DATA_SCIENCE_MAX_EVENTS=<n>` overrides event sample cap.
- `DEVCTL_DATA_SCIENCE_MAX_SWARM_FILES=<n>` overrides swarm file cap.
- `DEVCTL_DATA_SCIENCE_MAX_BENCHMARK_FILES=<n>` overrides benchmark file cap.

## Agent-sizing method (current)

Current recommendation score is a weighted blend:

- success rate (45%)
- tasks/minute (35%)
- tasks/agent efficiency (20%)

This is intentionally simple and auditable. We can evolve weights and models
as we collect more benchmark history.
