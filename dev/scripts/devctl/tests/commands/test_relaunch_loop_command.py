"""CLI tests for the typed relaunch-loop controller."""

from __future__ import annotations

from dev.scripts.devctl import cli


def test_relaunch_loop_command_is_registered() -> None:
    args = cli.build_parser().parse_args(["relaunch-loop", "--action", "status"])

    assert args.command == "relaunch-loop"
    assert cli.COMMAND_HANDLERS["relaunch-loop"].__name__ == "run"


def test_relaunch_loop_emit_watch_and_dispatch_dry_run(tmp_path, capsys) -> None:
    trace_path = tmp_path / "trace.ndjson"
    queue_path = tmp_path / "queue.jsonl"
    receipts_path = tmp_path / "receipts.jsonl"

    emit_args = cli.build_parser().parse_args(
        [
            "relaunch-loop",
            "--action",
            "emit-closure",
            "--trace-path",
            str(trace_path),
            "--queue-path",
            str(queue_path),
            "--receipts-path",
            str(receipts_path),
            "--emitter-actor",
            "claude",
            "--target-actor",
            "codex",
            "--closed-slice-id",
            "rev-pkt-2972",
            "--next-slice-id",
            "rev-pkt-2975-review",
            "--plan-ref",
            "MP-377",
            "--intent",
            "review relaunch plan",
            "--packet-id",
            "rev_pkt_2975",
            "--format",
            "json",
        ]
    )
    assert cli.COMMAND_HANDLERS["relaunch-loop"](emit_args) == 0

    watch_args = cli.build_parser().parse_args(
        [
            "relaunch-loop",
            "--action",
            "watch-once",
            "--trace-path",
            str(trace_path),
            "--queue-path",
            str(queue_path),
            "--receipts-path",
            str(receipts_path),
            "--format",
            "json",
        ]
    )
    assert cli.COMMAND_HANDLERS["relaunch-loop"](watch_args) == 0

    dispatch_args = cli.build_parser().parse_args(
        [
            "relaunch-loop",
            "--action",
            "dispatch-once",
            "--queue-path",
            str(queue_path),
            "--receipts-path",
            str(receipts_path),
            "--dry-run",
            "--format",
            "md",
        ]
    )
    assert cli.COMMAND_HANDLERS["relaunch-loop"](dispatch_args) == 0
    output = capsys.readouterr().out

    assert trace_path.exists()
    assert queue_path.exists()
    assert receipts_path.exists()
    assert "Dispatch Preview" in output
    assert "review-channel --action launch --role reviewer" in output


def test_relaunch_loop_dispatch_without_dry_run_fails_closed(tmp_path, capsys) -> None:
    trace_path = tmp_path / "trace.ndjson"
    queue_path = tmp_path / "queue.jsonl"
    receipts_path = tmp_path / "receipts.jsonl"

    emit_args = cli.build_parser().parse_args(
        [
            "relaunch-loop",
            "--action",
            "emit-closure",
            "--trace-path",
            str(trace_path),
            "--queue-path",
            str(queue_path),
            "--receipts-path",
            str(receipts_path),
            "--emitter-actor",
            "codex",
            "--target-actor",
            "claude",
            "--closed-slice-id",
            "rev-pkt-2975-review",
            "--next-slice-id",
            "rev-pkt-2975-dogfood",
            "--plan-ref",
            "MP-377",
            "--intent",
            "verify relaunch queue without spawning",
            "--packet-id",
            "rev_pkt_2978",
            "--format",
            "json",
        ]
    )
    assert cli.COMMAND_HANDLERS["relaunch-loop"](emit_args) == 0

    watch_args = cli.build_parser().parse_args(
        [
            "relaunch-loop",
            "--action",
            "watch-once",
            "--trace-path",
            str(trace_path),
            "--queue-path",
            str(queue_path),
            "--receipts-path",
            str(receipts_path),
            "--format",
            "json",
        ]
    )
    assert cli.COMMAND_HANDLERS["relaunch-loop"](watch_args) == 0
    receipts_before = receipts_path.read_text(encoding="utf-8")

    dispatch_args = cli.build_parser().parse_args(
        [
            "relaunch-loop",
            "--action",
            "dispatch-once",
            "--queue-path",
            str(queue_path),
            "--receipts-path",
            str(receipts_path),
            "--format",
            "md",
        ]
    )
    assert cli.COMMAND_HANDLERS["relaunch-loop"](dispatch_args) == 2
    output = capsys.readouterr().out

    assert "provider spawning is fail-closed" in output
    assert receipts_path.read_text(encoding="utf-8") == receipts_before
