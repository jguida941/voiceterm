"""Parser registration for the context-graph command."""

from __future__ import annotations

import argparse

from ..common import add_standard_output_arguments


def add_context_graph_parser(sub: argparse._SubParsersAction) -> None:
    """Register the ``context-graph`` parser."""
    cmd = sub.add_parser(
        "context-graph",
        help=(
            "Query the repo-understanding context graph built from "
            "canonical pointer refs and typed edges"
        ),
    )
    cmd.add_argument(
        "--mode",
        choices=("query", "bootstrap", "concept-view", "diff"),
        default="query",
        help=(
            "Operating mode: 'query' searches the graph (default), "
            "'bootstrap' emits a slim AI startup context packet, "
            "'concept-view' renders subsystem-level concept diagrams, and "
            "'diff' compares two saved ContextGraphSnapshot artifacts."
        ),
    )
    cmd.add_argument(
        "--query",
        default="",
        help=(
            "Search term: file path, MP number, guard name, or keyword. "
            "Empty returns the hot-index summary with top-20 hottest nodes. "
            "Only used in query mode."
        ),
    )
    cmd.add_argument(
        "--save-snapshot",
        action="store_true",
        help=(
            "Write a versioned ContextGraphSnapshot artifact under "
            "dev/reports/graph_snapshots/. Bootstrap mode saves one by "
            "default; this flag extends that behavior to other modes."
        ),
    )
    cmd.add_argument(
        "--from",
        dest="from_snapshot",
        default="",
        help=(
            "Snapshot ref/path used as the diff baseline in diff mode. "
            "Accepts a path, basename, 'latest', or 'previous'."
        ),
    )
    cmd.add_argument(
        "--to",
        dest="to_snapshot",
        default="",
        help=(
            "Snapshot ref/path used as the diff target in diff mode. "
            "Defaults to the latest saved snapshot."
        ),
    )
    cmd.add_argument(
        "--trend-window",
        type=int,
        default=5,
        help=(
            "Rolling snapshot window used for diff-mode trend summary "
            "(default: 5)."
        ),
    )
    add_standard_output_arguments(cmd, format_choices=("json", "md", "mermaid", "dot"))
