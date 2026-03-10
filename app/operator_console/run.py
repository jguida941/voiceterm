#!/usr/bin/env python3

"""Entrypoint for the optional PyQt6 Operator Console."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

def _resolve_repo_root() -> Path:
    """Return the repo root for both module and direct script execution."""
    return Path(__file__).resolve().parents[2]


def _ensure_repo_root_on_sys_path() -> Path:
    """Make the repo package importable when ``run.py`` is executed directly."""
    repo_root = _resolve_repo_root()
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)
    return repo_root


REPO_ROOT = _ensure_repo_root_on_sys_path()

from app.operator_console.help_render import render_operator_console_help
from app.operator_console.launch_support import ensure_pyqt6_installed


def build_parser() -> argparse.ArgumentParser:
    """Return the CLI parser for the optional desktop Operator Console."""
    from app.operator_console.theme import available_theme_ids
    from app.operator_console.views.layout.ui_layouts import available_layout_ids

    default_log_root = "dev/reports/review_channel/operator_console"
    parser = argparse.ArgumentParser(
        add_help=False,
        description=(
            "Launch the optional PyQt6 VoiceTerm Operator Console for the "
            "current Codex/Claude workflow."
        )
    )
    parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        help="Show themed launcher help and exit.",
    )
    parser.add_argument(
        "--dev-log",
        action="store_true",
        help=(
            "Persist structured diagnostics under the repo-visible "
            "review-channel report tree."
        ),
    )
    parser.add_argument(
        "--log-dir",
        default=default_log_root,
        help=(
            "Repo-relative diagnostics directory used when --dev-log is enabled "
            f"(default: {default_log_root})."
        ),
    )
    parser.add_argument(
        "--theme",
        default=None,
        choices=available_theme_ids(),
        help=(
            "Force a builtin desktop theme at startup. When omitted, the console "
            "reuses the last saved active theme and otherwise falls back to codex."
        ),
    )
    parser.add_argument(
        "--layout",
        default=None,
        choices=available_layout_ids(),
        help=(
            "Open the console directly into one layout mode at startup. When "
            "omitted, the default workbench layout is used."
        ),
    )
    parser.add_argument(
        "--ensure-pyqt6",
        action="store_true",
        help="Install PyQt6 with pip on demand before launching the console.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Launch the optional PyQt6 Operator Console."""
    repo_root = REPO_ROOT
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    if args.help:
        print(render_operator_console_help(args.theme, repo_root=repo_root))
        return 0

    from app.operator_console.logging_support import OperatorConsoleDiagnostics

    diagnostics = OperatorConsoleDiagnostics.create(
        repo_root,
        enabled=args.dev_log,
        root_rel=args.log_dir,
    )
    diagnostics.log(
        level="INFO",
        event="startup",
        message="Launching VoiceTerm Operator Console entrypoint",
        details={
            "dev_log": args.dev_log,
            "log_dir": args.log_dir,
            "theme": args.theme or "saved-or-default",
            "layout": args.layout or "default",
            "ensure_pyqt6": args.ensure_pyqt6,
            "repo_root": repo_root,
        },
    )
    if args.ensure_pyqt6:
        ensure_pyqt6_installed(diagnostics=diagnostics)

    try:
        from app.operator_console.views.main_window import run

        return run(
            repo_root,
            diagnostics=diagnostics,
            dev_log_enabled=args.dev_log,
            theme_id=args.theme,
            layout_mode=args.layout,
        )
    except SystemExit as exc:
        diagnostics.log(
            level="ERROR",
            event="system_exit",
            message="Operator Console exited before normal completion",
            details={"exit": str(exc)},
        )
        raise
    except Exception as exc:  # broad-except: allow reason=startup crash logging must capture fatal diagnostics before re-raising fallback=re-raise after diagnostics are recorded
        diagnostics.log(
            level="ERROR",
            event="fatal_exception",
            message="Operator Console crashed before or during startup",
            details={
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
