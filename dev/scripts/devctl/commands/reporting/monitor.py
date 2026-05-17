"""devctl monitor command implementation."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from ...common import (
    add_standard_output_arguments,
    emit_output,
    pipe_output,
    resolve_repo_path,
    write_output,
)
from ...config import REPO_ROOT
from ...runtime.provider_registry import (
    is_valid_provider_id,
    known_provider_help,
    normalize_provider_id,
    provider_id_error,
)
from ...runtime.monitor_snapshot import (
    build_monitor_snapshot,
    render_monitor_snapshot_markdown,
    render_monitor_snapshot_terminal,
)


def add_parser(sub) -> None:
    """Register the ``monitor`` subcommand."""
    cmd = sub.add_parser(
        "monitor",
        help="Canonical single-pass remote phone monitor over typed runtime state",
    )
    add_standard_output_arguments(
        cmd,
        format_choices=("json", "md", "terminal", "simple"),
        default_format="md",
    )
    cmd.add_argument(
        "--mode",
        choices=["remote_phone", "standard"],
        default="remote_phone",
        help="Render mode for the monitor snapshot",
    )
    cmd.add_argument(
        "--agent",
        default="operator",
        metavar="PROVIDER",
        help=(
            "Provider perspective recorded in the snapshot. Known providers "
            f"include {known_provider_help()}, and future provider ids are "
            "accepted when they use provider-id syntax."
        ),
    )
    cmd.add_argument(
        "--review-status-dir",
        help="Optional review-status root override for alternate monitor bundles",
    )
    cmd.add_argument(
        "--follow",
        action="store_true",
        help="Stream NDJSON monitor snapshots on a fixed cadence",
    )
    cmd.add_argument(
        "--interval",
        default="30s",
        help="Follow cadence for `--follow` (seconds by default, or suffix with s/m/h)",
    )
    cmd.add_argument(
        "--max-follow-snapshots",
        type=int,
        default=0,
        help="Maximum follow snapshots to emit (0 = unbounded)",
    )


def run(args) -> int:
    """Render one monitor snapshot or stream NDJSON follow frames."""
    agent = _normalize_agent_arg(args)
    if agent is None:
        return 2
    interval_seconds, error = _parse_interval_seconds(str(getattr(args, "interval", "30s")))
    if error is not None:
        print(error, file=sys.stderr)
        return 1
    review_status_dir = _resolve_review_status_dir(getattr(args, "review_status_dir", None))
    if bool(getattr(args, "follow", False)):
        if args.format != "json":
            print("monitor --follow requires --format json", file=sys.stderr)
            return 1
        return _run_follow(
            args=args,
            agent=agent,
            interval_seconds=interval_seconds,
            review_status_dir=review_status_dir,
        )

    snapshot = build_monitor_snapshot(
        repo_root=REPO_ROOT,
        mode=str(getattr(args, "mode", "remote_phone")),
        agent=agent,
        review_status_dir=review_status_dir,
    )
    return emit_output(
        _render_snapshot(snapshot, args.format),
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
        piper=pipe_output,
    )


def _normalize_agent_arg(args) -> str | None:
    agent = normalize_provider_id(getattr(args, "agent", "operator") or "operator")
    if not is_valid_provider_id(agent):
        print(provider_id_error("--agent"), file=sys.stderr)
        return None
    return agent


def _run_follow(
    *,
    args,
    agent: str,
    interval_seconds: int,
    review_status_dir: Path | None,
) -> int:
    output_path = getattr(args, "output", None)
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
    emitted = 0
    seq = 0
    max_snapshots = max(0, int(getattr(args, "max_follow_snapshots", 0) or 0))
    try:
        while max_snapshots == 0 or emitted < max_snapshots:
            snapshot = build_monitor_snapshot(
                repo_root=REPO_ROOT,
                mode=str(getattr(args, "mode", "remote_phone")),
                agent=agent,
                review_status_dir=review_status_dir,
            )
            frame = snapshot.to_dict()
            frame["follow"] = True
            frame["snapshot_seq"] = seq
            pipe_rc = _emit_follow_line(
                line=json.dumps(frame, sort_keys=True),
                output_path=output_path,
                pipe_command=getattr(args, "pipe_command", None),
                pipe_args=getattr(args, "pipe_args", None),
            )
            if pipe_rc != 0:
                return pipe_rc
            emitted += 1
            seq += 1
            if max_snapshots and emitted >= max_snapshots:
                break
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        return 130
    return 0


def _emit_follow_line(
    *,
    line: str,
    output_path: str | None,
    pipe_command: str | None,
    pipe_args: list[str] | None,
) -> int:
    if output_path:
        with Path(output_path).open("a", encoding="utf-8") as handle:
            handle.write(line)
            handle.write("\n")
    else:
        print(line)
    return 0 if not pipe_command else pipe_output(line, pipe_command, pipe_args)


def _render_snapshot(snapshot, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(snapshot.to_dict(), indent=2)
    if output_format == "terminal":
        return render_monitor_snapshot_terminal(snapshot)
    if output_format == "simple":
        from ...runtime.session_posture_simple_render import (
            render_simple_posture_snapshot,
        )

        runtime_state = snapshot.canonical_runtime_state
        return render_simple_posture_snapshot(
            title="Monitor",
            next_action=runtime_state.get("next_action"),
            top_blocker=runtime_state.get("top_blocker"),
            session_posture=runtime_state.get("session_posture"),
        )
    return render_monitor_snapshot_markdown(snapshot)


def _resolve_review_status_dir(raw_path: str | None) -> Path | None:
    if raw_path is None or not str(raw_path).strip():
        return None
    return resolve_repo_path(raw_path, repo_root=REPO_ROOT)


def _parse_interval_seconds(raw_value: str) -> tuple[int, str | None]:
    raw = raw_value.strip().lower()
    if not raw:
        return 30, None
    suffix = raw[-1]
    number_text = raw[:-1] if suffix in {"s", "m", "h"} else raw
    multiplier = {"s": 1, "m": 60, "h": 3600}.get(suffix, 1)
    try:
        number = int(number_text)
    except ValueError:
        return 0, f"invalid monitor interval `{raw_value}`"
    if number <= 0:
        return 0, "monitor interval must be greater than zero"
    return number * multiplier, None
