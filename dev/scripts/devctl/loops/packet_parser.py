"""Parser wiring for `devctl loop-packet` arguments."""

from __future__ import annotations


def add_loop_packet_parser(sub) -> None:
    """Register the `loop-packet` command parser on the given subparser group."""
    packet_cmd = sub.add_parser(
        "loop-packet",
        help=(
            "Build a guarded terminal feedback packet from triage/loop JSON "
            "artifacts for dev-mode draft injection"
        ),
    )
    packet_cmd.add_argument(
        "--source-json",
        action="append",
        default=[],
        help=(
            "Explicit JSON artifact path (repeatable). "
            "Defaults to common triage/loop bundle locations."
        ),
    )
    packet_cmd.add_argument(
        "--prefer-source",
        choices=["triage-loop", "mutation-loop", "triage"],
        default="triage-loop",
        help="Preferred source type when multiple valid artifacts are available",
    )
    packet_cmd.add_argument(
        "--max-age-hours",
        type=float,
        default=72.0,
        help="Maximum allowed source artifact age in hours before packet generation fails",
    )
    packet_cmd.add_argument(
        "--max-draft-chars",
        type=int,
        default=1600,
        help="Hard cap for generated terminal draft text length",
    )
    packet_cmd.add_argument(
        "--allow-auto-send",
        action="store_true",
        help=(
            "Mark packet as auto-send eligible when risk is low. Runtime still "
            "requires explicit guard opt-in."
        ),
    )
    packet_cmd.add_argument("--format", choices=["md", "json"], default="json")
    packet_cmd.add_argument("--output")
    packet_cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    packet_cmd.add_argument(
        "--pipe-args", nargs="*", help="Extra args for pipe command"
    )
