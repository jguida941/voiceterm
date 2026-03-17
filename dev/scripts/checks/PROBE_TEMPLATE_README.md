# AI Code Quality Guard — Probe Template

> Deterministic code quality probes that catch AI-generated code smells.
> Like CodeRabbit, but based on real patterns — zero hallucination.

## Quick Start

```bash
# Run all probes and get a report
python3 dev/scripts/checks/run_probe_report.py --format md

# Terminal-friendly compact report
python3 dev/scripts/checks/run_probe_report.py --format terminal

# JSON for tooling integration
python3 dev/scripts/checks/run_probe_report.py --format json

# With source code snippets and git diffs
python3 dev/scripts/checks/run_probe_report.py --format md

# Without source/diffs (faster, smaller output)
python3 dev/scripts/checks/run_probe_report.py --format md --no-source --no-diffs
```

## What It Does

Scans your codebase for **design-quality patterns** that AI coding assistants
commonly produce. Each finding includes:

1. **What was detected** — the specific pattern found in your code
2. **Source context** — the actual code with a marker pointing at the issue
3. **Git diff** — what changed in the file (for review context)
4. **Best practice** — why this pattern is problematic
5. **How to fix** — step-by-step remediation with before/after examples
6. **References** — links to official documentation
7. **Suppression** — copy-paste JSON to mark findings as intentional

## Available Probes

### Python
| Probe | Detects |
|---|---|
| `probe_design_smells` | Excessive `getattr()`, untyped `object` params, format helper sprawl |
| `probe_boolean_params` | Functions with 3+ boolean parameters |
| `probe_stringly_typed` | String-literal dispatch chains (should be StrEnum) |
| `probe_magic_numbers` | Unnamed numeric literals in slice operations |
| `probe_dict_as_struct` | Functions returning dicts with 5+ keys (should be dataclass) |
| `probe_unnecessary_intermediates` | `result = expr; return result` with generic names |
| `probe_defensive_overchecking` | 3+ `isinstance()` checks on the same variable |
| `probe_single_use_helpers` | Private functions called only once (indirection without reuse) |

### Rust
| Probe | Detects |
|---|---|
| `probe_concurrency` | Nested locks, mutex+spawn, relaxed atomics, poison recovery |
| `probe_boolean_params` | Functions with 3+ boolean parameters |
| `probe_stringly_typed` | String match arms that should be enums |
| `probe_unwrap_chains` | `.unwrap()`/`.expect()` chains (should use `?`) |
| `probe_clone_density` | Excessive `.clone()` (ownership confusion) |
| `probe_type_conversions` | Redundant type conversion chains (`.as_str().to_string()`) |
| `probe_vague_errors` | `bail!()`/`anyhow!()` without runtime context variables |

## Suppressing Findings

If a finding is intentional, add it to `.probe-allowlist.json`:

```json
{
  "entries": [
    {
      "file": "src/lib.rs",
      "symbol": "my_function",
      "probe": "probe_clone_density",
      "disposition": "design_decision",
      "decision_mode": "recommend_only",
      "reason": "cloning is required here because the data is sent to a spawned task",
      "research_instruction": "Revisit if the spawn boundary disappears",
      "invariants": [
        "preserve the spawn boundary's ownership safety"
      ],
      "validation_plan": [
        "Run `python3 dev/scripts/devctl.py check --profile ci` after changing the boundary.",
        "Run `python3 dev/scripts/devctl.py probe-report --format md` to refresh the decision packet."
      ]
    }
  ]
}
```

The finding will move into the report's design-decision packet section instead
of disappearing. Entries are matched by `file` + `symbol`; `probe` is kept as
audit intent. Use `design_decision` when the current shape is an intentional
architecture boundary that should stay visible for AI and human decision-makers
with explicit `decision_mode`, invariants, and validation steps.

## Adding to Your Project

### Step 1: Copy probe files
Copy the `dev/scripts/checks/` directory to your project. Required files:
- `probe_bootstrap.py` — shared probe infrastructure
- `probe_report_render.py` — report renderer with best-practice library
- `run_probe_report.py` — one-command runner
- Individual `probe_*.py` files for each probe you want

### Step 2: Configure paths
Edit each probe's `TARGET_ROOTS` to match your source directories:
```python
PYTHON_ROOTS = (Path("src"), Path("lib"))
RUST_ROOTS = (Path("src"),)
```

### Step 3: Run after AI coding sessions
After using AI agents (Codex, Claude, Copilot, etc.) to write code:
```bash
python3 path/to/run_probe_report.py --format md --output quality_report.md
```

### Step 4: Share with your team
The generated report explains every finding at a level that junior devs
can use to explain to senior engineers why changes were made.

## Architecture

```
Three-layer quality model:

Layer A: Hard Guards (exit 0/1)     — blocks regressions at CI time
Layer B: Review Probes (exit 0)     — surfaces design smells (this tool)
Layer C: AI Review (advisory)       — deep contextual analysis (future)
```

Probes are **Layer B** — they never block CI, they inform humans and AI.
Every finding is deterministic (regex/AST pattern matching, not AI guessing).

## Creating New Probes

```python
#!/usr/bin/env python3
"""probe_my_pattern.py — detect [pattern description]."""

from probe_bootstrap import ProbeReport, RiskHint, build_probe_parser, emit_probe_report

def main() -> int:
    args = build_probe_parser(__doc__).parse_args()
    report = ProbeReport(command="probe_my_pattern")

    # ... scan files, detect patterns, append RiskHint objects ...

    report.risk_hints.append(RiskHint(
        file="path/to/file.py",
        symbol="function_name",
        risk_type="design_smell",
        severity="medium",
        signals=["description of what was found"],
        ai_instruction="what to do about it",
        review_lens="design_quality",
    ))

    return emit_probe_report(report, output_format=args.format)

if __name__ == "__main__":
    sys.exit(main())
```

Key rules:
1. Always exit 0 — probes emit hints, never block CI
2. Include `ai_instruction` for targeted remediation guidance
3. Skip test files — test code has different design rules
4. Use growth-based detection (compare against a ref) for CI
