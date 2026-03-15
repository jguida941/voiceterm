"""Parser wiring for `devctl swarm_run` arguments."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any

from ..repo_packs.voiceterm import VOICETERM_PATH_CONFIG as _PC


@dataclass(frozen=True, slots=True)
class ArgumentDef:
    flags: tuple[str, ...]
    kwargs: dict[str, Any]


def _arg(*flags: str, **kwargs: Any) -> ArgumentDef:
    return ArgumentDef(flags=tuple(flags), kwargs=kwargs)


BASE_ARGUMENTS: list[ArgumentDef] = [
    _arg("--repo", help="owner/repo (optional; falls back to env/repo detection)"),
    _arg("--run-label", help="Optional explicit run label"),
    _arg("--plan-doc", default=_PC.autonomy_plan_doc_rel),
    _arg("--index-doc", default=_PC.active_index_doc_rel),
    _arg("--master-plan-doc", default=_PC.active_master_plan_doc_rel),
    _arg("--mp-scope", default="MP-338"),
    _arg("--next-steps-limit", type=int, default=8),
    _arg(
        "--question",
        help="Optional explicit swarm prompt (default: derived from unchecked plan steps)",
    ),
    _arg(
        "--run-root",
        default=_PC.autonomy_run_root_rel,
        help="Root directory for swarm_run bundles",
    ),
    _arg(
        "--swarm-output-root",
        default=_PC.autonomy_swarm_root_rel,
        help="Root directory for nested autonomy-swarm bundles",
    ),
    _arg("--branch-base", default="develop"),
    _arg(
        "--mode",
        choices=["report-only", "plan-then-fix", "fix-only"],
        default="report-only",
    ),
    _arg(
        "--fix-command",
        help=(
            "Nested fix command forwarded to autonomy-swarm/autonomy-loop when "
            "--mode is plan-then-fix/fix-only"
        ),
    ),
    _arg("--agents", type=int, help="Explicit agent count override"),
    _arg(
        "--adaptive",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Use metadata-driven agent sizing when --agents is not set",
    ),
    _arg("--min-agents", type=int, default=4),
    _arg("--max-agents", type=int, default=20),
    _arg("--token-budget", type=int, default=0),
    _arg("--per-agent-token-cost", type=int, default=12000),
    _arg("--parallel-workers", type=int, default=4),
    _arg("--agent-timeout-seconds", type=int, default=1800),
    _arg("--max-rounds", type=int, default=1),
    _arg("--max-hours", type=float, default=1.0),
    _arg("--max-tasks", type=int, default=1),
    _arg("--checkpoint-every", type=int, default=1),
    _arg("--loop-max-attempts", type=int, default=1),
    _arg("--dry-run", action="store_true"),
    _arg("--diff-ref", default="origin/develop"),
    _arg(
        "--target-paths",
        nargs="*",
        default=[],
        help="Optional path filters for metadata diff scoring",
    ),
]

AUDIT_ARGUMENTS: list[ArgumentDef] = [
    _arg(
        "--charts",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Generate swarm and digest charts",
    ),
    _arg(
        "--audit-source-root",
        default=_PC.autonomy_source_root_rel,
        help="Source root for nested post-audit autonomy-report runs",
    ),
    _arg(
        "--audit-library-root",
        default=_PC.autonomy_library_root_rel,
        help="Library root for nested post-audit autonomy-report bundles",
    ),
    _arg(
        "--audit-event-log",
        default=_PC.audit_event_log_rel,
        help="Event log for nested post-audit autonomy-report runs",
    ),
    _arg(
        "--stale-minutes",
        type=int,
        default=120,
        help="Stale threshold for nested orchestrate-watch audit",
    ),
    _arg(
        "--skip-governance",
        action="store_true",
        help="Skip governance guard commands (not recommended)",
    ),
    _arg(
        "--skip-plan-update",
        action="store_true",
        help="Do not append progress/audit evidence to the plan doc",
    ),
]

CONTINUOUS_ARGUMENTS: list[ArgumentDef] = [
    _arg(
        "--continuous",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            "Keep running swarm cycles over plan checklist items until limits are hit "
            "or a cycle fails governance/safety checks"
        ),
    ),
    _arg(
        "--continuous-max-cycles",
        type=int,
        default=10,
        help="Maximum swarm cycles when --continuous is enabled",
    ),
    _arg(
        "--feedback-sizing",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable closed-loop agent sizing in continuous mode",
    ),
    _arg(
        "--feedback-stall-rounds",
        type=int,
        default=2,
        help="Downshift when unresolved totals stall for this many cycles",
    ),
    _arg(
        "--feedback-no-signal-rounds",
        type=int,
        default=2,
        help="Downshift when all workers report no-signal triage reasons",
    ),
    _arg(
        "--feedback-downshift-factor",
        type=float,
        default=0.5,
        help="Multiplier for feedback downshift decisions",
    ),
    _arg(
        "--feedback-upshift-rounds",
        type=int,
        default=2,
        help="Upshift after this many improving cycles",
    ),
    _arg(
        "--feedback-upshift-factor",
        type=float,
        default=1.25,
        help="Multiplier for feedback upshift decisions",
    ),
]

OUTPUT_ARGUMENTS: list[ArgumentDef] = [
    _arg("--format", choices=["json", "md"], default="md"),
    _arg("--output"),
    _arg("--json-output"),
    _arg("--pipe-command", help="Pipe report output to a command"),
    _arg("--pipe-args", nargs="*", help="Extra args for pipe command"),
]


def _register_arguments(cmd: argparse.ArgumentParser, arguments: list[ArgumentDef]) -> None:
    for arg_def in arguments:
        cmd.add_argument(*arg_def.flags, **arg_def.kwargs)


def add_autonomy_run_parser(sub) -> None:
    """Register the `swarm_run` command parser."""
    run_cmd = sub.add_parser(
        "swarm_run",
        help=(
            "Run one guarded autonomy pipeline: load active-plan scope, execute "
            "swarm+reviewer lane, run governance checks, and append plan evidence"
        ),
    )
    for group in (
        BASE_ARGUMENTS,
        AUDIT_ARGUMENTS,
        CONTINUOUS_ARGUMENTS,
        OUTPUT_ARGUMENTS,
    ):
        _register_arguments(run_cmd, group)
