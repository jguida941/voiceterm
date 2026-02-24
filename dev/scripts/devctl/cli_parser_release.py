"""Parser registration helpers for release/distribution commands."""

from __future__ import annotations

import argparse


def add_release_parsers(sub: argparse._SubParsersAction) -> None:
    """Register release/ship/release-notes/homebrew/pypi parsers."""
    # release
    release_cmd = sub.add_parser("release", help="Run tag + notes release flow (legacy-compatible)")
    release_cmd.add_argument("--version", required=True)
    release_cmd.add_argument(
        "--prepare-release",
        action="store_true",
        help="Auto-update release metadata files before tag/notes steps",
    )
    release_cmd.add_argument("--homebrew", action="store_true")
    release_cmd.add_argument("--yes", action="store_true", help="Skip confirmation prompts")
    release_cmd.add_argument("--allow-ci", action="store_true")
    release_cmd.add_argument("--dry-run", action="store_true")

    # ship
    ship_cmd = sub.add_parser("ship", help="Run release/distribution steps from one control-plane command")
    ship_cmd.add_argument("--version", required=True)
    ship_cmd.add_argument(
        "--prepare-release",
        action="store_true",
        help="Auto-update release metadata files before verify/tag/publish steps",
    )
    ship_cmd.add_argument("--verify", action="store_true", help="Run release verification checks")
    ship_cmd.add_argument("--verify-docs", action="store_true", help="Include docs-check in verify step")
    ship_cmd.add_argument("--tag", action="store_true", help="Create/push git tag")
    ship_cmd.add_argument("--notes", action="store_true", help="Generate release notes markdown")
    ship_cmd.add_argument("--github", action="store_true", help="Create GitHub release")
    ship_cmd.add_argument(
        "--github-fail-on-no-commits",
        action="store_true",
        help="Pass --fail-on-no-commits to gh release create",
    )
    ship_cmd.add_argument("--pypi", action="store_true", help="Publish PyPI package")
    ship_cmd.add_argument("--homebrew", action="store_true", help="Update Homebrew tap")
    ship_cmd.add_argument("--verify-pypi", action="store_true", help="Verify PyPI JSON endpoint version")
    ship_cmd.add_argument("--notes-output", help="Release notes output file path")
    ship_cmd.add_argument("--yes", action="store_true", help="Skip confirmation prompts")
    ship_cmd.add_argument("--allow-ci", action="store_true")
    ship_cmd.add_argument("--dry-run", action="store_true")
    ship_cmd.add_argument("--format", choices=["text", "json", "md"], default="text")
    ship_cmd.add_argument("--output")
    ship_cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    ship_cmd.add_argument("--pipe-args", nargs="*", help="Extra args for pipe command")

    # release-notes
    notes_cmd = sub.add_parser("release-notes", help="Generate markdown release notes from git diff history")
    notes_cmd.add_argument("--version", required=True)
    notes_cmd.add_argument(
        "--output",
        help="Output markdown path (default: /tmp/voiceterm-release-vX.Y.Z.md)",
    )
    notes_cmd.add_argument(
        "--end-ref",
        help="End ref for compare range (default: vX.Y.Z if tag exists, else HEAD)",
    )
    notes_cmd.add_argument(
        "--previous-tag",
        help="Explicit previous tag (default: latest prior v* tag)",
    )
    notes_cmd.add_argument("--dry-run", action="store_true")

    # homebrew
    homebrew_cmd = sub.add_parser("homebrew", help="Run Homebrew tap update flow")
    homebrew_cmd.add_argument("--version", required=True)
    homebrew_cmd.add_argument("--yes", action="store_true", help="Skip confirmation prompts")
    homebrew_cmd.add_argument("--allow-ci", action="store_true")
    homebrew_cmd.add_argument("--dry-run", action="store_true")

    # pypi
    pypi_cmd = sub.add_parser("pypi", help="Run PyPI build/check/upload flow")
    pypi_cmd.add_argument("--upload", action="store_true", help="Upload package to PyPI")
    pypi_cmd.add_argument("--yes", action="store_true", help="Skip confirmation prompts")
    pypi_cmd.add_argument("--allow-ci", action="store_true")
    pypi_cmd.add_argument("--dry-run", action="store_true")
