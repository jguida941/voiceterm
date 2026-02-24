"""Parser wiring for `devctl cihub-setup` arguments."""


def add_cihub_setup_parser(sub) -> None:
    """Register the `cihub-setup` command parser on the given subparser group."""
    cmd = sub.add_parser(
        "cihub-setup",
        help="Preview/apply allowlisted CIHub repo-setup steps",
    )
    cmd.add_argument(
        "--steps",
        nargs="+",
        choices=("detect", "init", "update", "validate"),
        default=["detect", "init", "update", "validate"],
        help="Allowlisted CIHub setup steps to run (default: all)",
    )
    cmd.add_argument(
        "--cihub-bin",
        default="cihub",
        help="CIHub executable path (default: cihub)",
    )
    cmd.add_argument(
        "--repo",
        help="Optional owner/repo passed to CIHub setup commands",
    )
    cmd.add_argument(
        "--apply",
        action="store_true",
        help="Execute setup steps after preview + confirmation",
    )
    cmd.add_argument(
        "--strict-capabilities",
        action="store_true",
        help="Fail when requested setup steps are unsupported by the local CIHub binary",
    )
    cmd.add_argument("--yes", action="store_true", help="Skip confirmation prompt when --apply")
    cmd.add_argument("--dry-run", action="store_true")
    cmd.add_argument("--format", choices=["text", "json", "md"], default="md")
    cmd.add_argument("--output")
    cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    cmd.add_argument("--pipe-args", nargs="*", help="Extra args for pipe command")
