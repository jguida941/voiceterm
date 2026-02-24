"""Parser wiring for `devctl triage` arguments."""


def add_triage_parser(sub, default_ci_limit: int) -> None:
    """Register the `triage` command parser on the given subparser group."""
    triage_cmd = sub.add_parser(
        "triage",
        help="Generate human + AI triage outputs with optional CIHub ingestion",
    )
    triage_cmd.add_argument("--ci", action="store_true", help="Include recent GitHub runs")
    triage_cmd.add_argument("--ci-limit", type=int, default=default_ci_limit)
    triage_cmd.add_argument(
        "--dev-logs",
        action="store_true",
        help="Include guarded Dev Mode JSONL session summary",
    )
    triage_cmd.add_argument(
        "--dev-root",
        help="Override dev-log root (default: $HOME/.voiceterm/dev)",
    )
    triage_cmd.add_argument(
        "--dev-sessions-limit",
        type=int,
        default=5,
        help="Maximum recent session files to scan when --dev-logs",
    )
    triage_cmd.add_argument(
        "--cihub",
        action="store_true",
        help="Run cihub triage and ingest emitted artifacts (auto-enabled when cihub is installed)",
    )
    triage_cmd.add_argument(
        "--no-cihub",
        action="store_true",
        help="Skip cihub triage even if cihub is installed",
    )
    triage_cmd.add_argument(
        "--require-cihub",
        action="store_true",
        help="Exit non-zero if cihub triage command/artifacts are unavailable",
    )
    triage_cmd.add_argument("--cihub-bin", default="cihub")
    triage_run_group = triage_cmd.add_mutually_exclusive_group()
    triage_run_group.add_argument("--cihub-latest", action="store_true", help="Use latest run (default)")
    triage_run_group.add_argument("--cihub-run", help="Specific run id for cihub triage")
    triage_cmd.add_argument("--cihub-repo", help="owner/repo passed to cihub triage")
    triage_cmd.add_argument(
        "--cihub-emit-dir",
        default=".cihub",
        help="Directory where cihub triage emits triage.json/priority.json/triage.md",
    )
    triage_cmd.add_argument(
        "--emit-bundle",
        action="store_true",
        help="Also write triage bundle files (<prefix>.md and <prefix>.ai.json)",
    )
    triage_cmd.add_argument(
        "--bundle-dir",
        default=".cihub",
        help="Directory for --emit-bundle outputs",
    )
    triage_cmd.add_argument(
        "--bundle-prefix",
        default="devctl-triage",
        help="File prefix used by --emit-bundle",
    )
    triage_cmd.add_argument(
        "--owner-map-file",
        help="Optional JSON file mapping issue categories to owner labels",
    )
    triage_cmd.add_argument(
        "--external-issues-file",
        action="append",
        default=[],
        help=(
            "Optional JSON file with additional issue-like records "
            "(repeat flag for multiple files)"
        ),
    )
    triage_cmd.add_argument("--dry-run", action="store_true")
    triage_cmd.add_argument("--format", choices=["text", "json", "md"], default="md")
    triage_cmd.add_argument("--output")
    triage_cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    triage_cmd.add_argument("--pipe-args", nargs="*", help="Extra args for pipe command")
