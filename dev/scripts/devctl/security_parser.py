"""Parser wiring for `devctl security` arguments."""


def add_security_parser(sub) -> None:
    """Register the `security` command parser on the given subparser group."""
    security_cmd = sub.add_parser(
        "security",
        help="Run local security checks (RustSec policy + optional workflow scanner checks)",
    )
    security_cmd.add_argument(
        "--min-cvss",
        type=float,
        default=7.0,
        help="Minimum advisory score that should fail RustSec policy checks",
    )
    security_cmd.add_argument(
        "--fail-on-kind",
        action="append",
        help="RustSec warning kind that should fail (repeatable, default: yanked + unsound)",
    )
    security_cmd.add_argument(
        "--allowlist-file",
        default="dev/security/rustsec_allowlist.md",
        help="Path to RustSec advisory allowlist file",
    )
    security_cmd.add_argument(
        "--allow-unknown-severity",
        action="store_true",
        help="Do not fail advisories that have missing severity metadata",
    )
    security_cmd.add_argument(
        "--rustsec-output",
        default="rustsec-audit.json",
        help="Where to write the raw cargo-audit JSON report",
    )
    security_cmd.add_argument(
        "--with-zizmor",
        action="store_true",
        help="Run zizmor against GitHub workflows for workflow security checks",
    )
    security_cmd.add_argument(
        "--require-optional-tools",
        action="store_true",
        help="Fail when optional scanners (for example zizmor) are requested but missing",
    )
    security_cmd.add_argument("--dry-run", action="store_true")
    security_cmd.add_argument("--offline", action="store_true")
    security_cmd.add_argument("--cargo-home")
    security_cmd.add_argument("--cargo-target-dir")
    security_cmd.add_argument("--format", choices=["text", "json", "md"], default="text")
    security_cmd.add_argument("--output")
    security_cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    security_cmd.add_argument("--pipe-args", nargs="*", help="Extra args for pipe command")
