"""CLI command for packet PKT-BIND completeness."""

from __future__ import annotations

import argparse
import json
import sys

try:
    from check_bootstrap import REPO_ROOT, emit_runtime_error
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, emit_runtime_error

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from .constants import COMMAND, DEFAULT_EVENT_LOG_REL, DEFAULT_GRACE_MINUTES
from .constants import DEFAULT_PLAN_INDEX_REL
from .core import evaluate_packet_pkt_bind_completeness
from .render import render_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-log", default=DEFAULT_EVENT_LOG_REL)
    parser.add_argument("--plan-index", default=DEFAULT_PLAN_INDEX_REL)
    parser.add_argument("--grace-minutes", type=int, default=DEFAULT_GRACE_MINUTES)
    parser.add_argument(
        "--strict-legacy",
        action="store_true",
        help="Fail historical Codex task_started packets that predate the configured mandate.",
    )
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    try:
        report = evaluate_packet_pkt_bind_completeness(
            repo_root=REPO_ROOT,
            event_log_path=REPO_ROOT / args.event_log,
            plan_index_path=REPO_ROOT / args.plan_index,
            grace_minutes=args.grace_minutes,
            strict_legacy=args.strict_legacy,
        )
    # broad-except: allow reason=defensive-cli-boundary fallback=emit-runtime-error
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        emit_runtime_error(COMMAND, exc)
        return 1
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_markdown(report), end="")
    return 0 if report["ok"] else 1
