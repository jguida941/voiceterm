"""devctl CLI argument parsing and dispatch."""

import argparse
import sys

from .commands import (
    check,
    docs_check,
    homebrew,
    hygiene,
    listing,
    mutation_score,
    mutants,
    pypi,
    release,
    release_notes,
    report,
    ship,
    status,
)
from .config import DEFAULT_CI_LIMIT, DEFAULT_MEM_ITERATIONS, DEFAULT_MUTANTS_TIMEOUT, DEFAULT_MUTATION_THRESHOLD


def build_parser() -> argparse.ArgumentParser:
    """Create the top-level argparse parser for devctl."""
    parser = argparse.ArgumentParser(description="VoiceTerm Dev CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # check
    check_cmd = sub.add_parser("check", help="Run fmt/clippy/tests/build (and optional extras)")
    check_cmd.add_argument(
        "--profile",
        choices=["ci", "prepush", "release", "maintainer-lint", "quick"],
    )
    check_cmd.add_argument("--ci", action="store_true", help="Match rust_ci.yml scope (alias for --profile ci)")
    check_cmd.add_argument("--prepush", action="store_true", help="Run CI + perf/mem loop (alias for --profile prepush)")
    check_cmd.add_argument("--skip-fmt", action="store_true")
    check_cmd.add_argument("--skip-clippy", action="store_true")
    check_cmd.add_argument("--skip-tests", action="store_true")
    check_cmd.add_argument("--skip-build", action="store_true")
    check_cmd.add_argument("--fix", action="store_true", help="Run cargo fmt (not --check)")
    check_cmd.add_argument("--with-perf", action="store_true", help="Run perf smoke + verify")
    check_cmd.add_argument("--with-mem-loop", action="store_true", help="Run memory guard loop")
    check_cmd.add_argument("--mem-iterations", type=int, default=DEFAULT_MEM_ITERATIONS)
    check_cmd.add_argument("--with-wake-guard", action="store_true", help="Run wake-word regression + soak guard")
    check_cmd.add_argument(
        "--wake-soak-rounds",
        type=int,
        default=4,
        help="Wake-word soak iterations when wake guard is enabled",
    )
    check_cmd.add_argument("--with-mutants", action="store_true", help="Run mutants after checks")
    check_cmd.add_argument("--with-mutation-score", action="store_true", help="Check mutation score")
    check_cmd.add_argument("--mutation-score-path", help="Path to outcomes.json")
    check_cmd.add_argument("--mutation-score-threshold", type=float, default=DEFAULT_MUTATION_THRESHOLD)
    check_cmd.add_argument("--mutants-module", help="Mutants module filter")
    check_cmd.add_argument("--mutants-all", action="store_true")
    check_cmd.add_argument("--mutants-timeout", type=int, default=DEFAULT_MUTANTS_TIMEOUT)
    check_cmd.add_argument("--mutants-shard", help="Mutants shard spec like 1/8")
    check_cmd.add_argument("--mutants-offline", action="store_true")
    check_cmd.add_argument("--mutants-cargo-home")
    check_cmd.add_argument("--mutants-cargo-target-dir")
    check_cmd.add_argument("--mutants-plot", action="store_true")
    check_cmd.add_argument("--mutants-plot-scope", choices=["file", "dir"])
    check_cmd.add_argument("--mutants-plot-top-pct", type=float)
    check_cmd.add_argument("--mutants-plot-output")
    check_cmd.add_argument("--mutants-plot-show", action="store_true")
    check_cmd.add_argument("--keep-going", action="store_true")
    check_cmd.add_argument("--dry-run", action="store_true")
    check_cmd.add_argument("--format", choices=["text", "json", "md"], default="text")
    check_cmd.add_argument("--output", help="Write report to a file")
    check_cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    check_cmd.add_argument("--pipe-args", nargs="*", help="Extra args for pipe command")
    check_cmd.add_argument("--offline", action="store_true")
    check_cmd.add_argument("--cargo-home")
    check_cmd.add_argument("--cargo-target-dir")

    # mutants
    mutants_cmd = sub.add_parser("mutants", help="Run mutation testing helper")
    mutants_cmd.add_argument("--all", action="store_true")
    mutants_cmd.add_argument("--module")
    mutants_cmd.add_argument("--timeout", type=int, default=DEFAULT_MUTANTS_TIMEOUT)
    mutants_cmd.add_argument("--shard", help="Run one shard, e.g. 1/8")
    mutants_cmd.add_argument("--results-only", action="store_true")
    mutants_cmd.add_argument("--json", action="store_true")
    mutants_cmd.add_argument("--offline", action="store_true")
    mutants_cmd.add_argument("--cargo-home")
    mutants_cmd.add_argument("--cargo-target-dir")
    mutants_cmd.add_argument("--plot", action="store_true")
    mutants_cmd.add_argument("--plot-scope", choices=["file", "dir"])
    mutants_cmd.add_argument("--plot-top-pct", type=float)
    mutants_cmd.add_argument("--plot-output")
    mutants_cmd.add_argument("--plot-show", action="store_true")
    mutants_cmd.add_argument("--top", type=int)
    mutants_cmd.add_argument("--dry-run", action="store_true")

    # mutation score
    score_cmd = sub.add_parser("mutation-score", help="Check mutation score threshold")
    score_cmd.add_argument("--path", help="Path to outcomes.json (optional)")
    score_cmd.add_argument("--threshold", type=float, default=DEFAULT_MUTATION_THRESHOLD)
    score_cmd.add_argument("--dry-run", action="store_true")

    # release
    release_cmd = sub.add_parser("release", help="Run tag + notes release flow (legacy-compatible)")
    release_cmd.add_argument("--version", required=True)
    release_cmd.add_argument("--homebrew", action="store_true")
    release_cmd.add_argument("--yes", action="store_true", help="Skip confirmation prompts")
    release_cmd.add_argument("--allow-ci", action="store_true")
    release_cmd.add_argument("--dry-run", action="store_true")

    # ship
    ship_cmd = sub.add_parser("ship", help="Run release/distribution steps from one control-plane command")
    ship_cmd.add_argument("--version", required=True)
    ship_cmd.add_argument("--verify", action="store_true", help="Run release verification checks")
    ship_cmd.add_argument("--verify-docs", action="store_true", help="Include docs-check in verify step")
    ship_cmd.add_argument("--tag", action="store_true", help="Create/push git tag")
    ship_cmd.add_argument("--notes", action="store_true", help="Generate release notes markdown")
    ship_cmd.add_argument("--github", action="store_true", help="Create GitHub release")
    ship_cmd.add_argument("--github-fail-on-no-commits", action="store_true", help="Pass --fail-on-no-commits to gh release create")
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
    notes_cmd.add_argument("--output", help="Output markdown path (default: /tmp/voiceterm-release-vX.Y.Z.md)")
    notes_cmd.add_argument("--end-ref", help="End ref for compare range (default: vX.Y.Z if tag exists, else HEAD)")
    notes_cmd.add_argument("--previous-tag", help="Explicit previous tag (default: latest prior v* tag)")
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

    # docs-check
    docs_cmd = sub.add_parser("docs-check", help="Verify user-facing docs are updated")
    docs_cmd.add_argument("--user-facing", action="store_true", help="Enforce user-facing doc updates")
    docs_cmd.add_argument("--strict", action="store_true", help="Require all user docs when --user-facing")
    docs_cmd.add_argument(
        "--strict-tooling",
        action="store_true",
        help="Require all canonical maintainer docs for tooling/release changes",
    )
    docs_cmd.add_argument(
        "--since-ref",
        help="Use commit-range mode by comparing changes from this ref (e.g. origin/develop, HEAD~1)",
    )
    docs_cmd.add_argument(
        "--head-ref",
        default="HEAD",
        help="Range-mode head ref used with --since-ref (default: HEAD)",
    )
    docs_cmd.add_argument("--format", choices=["json", "md"], default="md")
    docs_cmd.add_argument("--output")
    docs_cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    docs_cmd.add_argument("--pipe-args", nargs="*", help="Extra args for pipe command")

    # status
    status_cmd = sub.add_parser("status", help="Summarize git + mutation status")
    status_cmd.add_argument("--ci", action="store_true", help="Include recent GitHub runs")
    status_cmd.add_argument("--ci-limit", type=int, default=DEFAULT_CI_LIMIT)
    status_cmd.add_argument(
        "--require-ci",
        action="store_true",
        help="Exit non-zero when CI fetch fails (implies --ci)",
    )
    status_cmd.add_argument("--format", choices=["json", "md", "text"], default="text")
    status_cmd.add_argument("--output")
    status_cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    status_cmd.add_argument("--pipe-args", nargs="*", help="Extra args for pipe command")

    # report
    report_cmd = sub.add_parser("report", help="Generate a JSON/MD report")
    report_cmd.add_argument("--ci", action="store_true", help="Include recent GitHub runs")
    report_cmd.add_argument("--ci-limit", type=int, default=DEFAULT_CI_LIMIT)
    report_cmd.add_argument("--format", choices=["json", "md"], default="md")
    report_cmd.add_argument("--output")
    report_cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    report_cmd.add_argument("--pipe-args", nargs="*", help="Extra args for pipe command")

    # list
    list_cmd = sub.add_parser("list", help="List devctl commands and profiles")
    list_cmd.add_argument("--format", choices=["json", "md"], default="md")
    list_cmd.add_argument("--output")

    # hygiene
    hygiene_cmd = sub.add_parser("hygiene", help="Audit archive/ADR/scripts governance hygiene")
    hygiene_cmd.add_argument("--format", choices=["json", "md"], default="md")
    hygiene_cmd.add_argument("--output")
    hygiene_cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    hygiene_cmd.add_argument("--pipe-args", nargs="*", help="Extra args for pipe command")

    return parser


def main() -> int:
    """Entry point for devctl CLI."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "check":
        if args.ci:
            args.profile = "ci"
        if args.prepush:
            args.profile = "prepush"
        return check.run(args)
    if args.command == "mutants":
        return mutants.run(args)
    if args.command == "mutation-score":
        return mutation_score.run(args)
    if args.command == "docs-check":
        return docs_check.run(args)
    if args.command == "release":
        return release.run(args)
    if args.command == "ship":
        return ship.run(args)
    if args.command == "release-notes":
        return release_notes.run(args)
    if args.command == "homebrew":
        return homebrew.run(args)
    if args.command == "pypi":
        return pypi.run(args)
    if args.command == "status":
        return status.run(args)
    if args.command == "report":
        return report.run(args)
    if args.command == "list":
        return listing.run(args)
    if args.command == "hygiene":
        return hygiene.run(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
