"""Parser wiring for `devctl security` arguments."""


def add_security_parser(sub) -> None:
    """Register the `security` command parser on the given subparser group."""
    security_cmd = sub.add_parser(
        "security",
        help="Run local security checks with scanner tiers (RustSec/core/all)",
    )
    security_cmd.add_argument(
        "--scanner-tier",
        choices=("rustsec", "core", "all"),
        default="core",
        help="Security scanner tier: rustsec baseline, core default-on, or all (core + expensive)",
    )
    security_cmd.add_argument(
        "--expensive-policy",
        choices=("advisory", "fail"),
        default="advisory",
        help="How expensive scanner failures should behave when --scanner-tier all is used",
    )
    security_cmd.add_argument(
        "--since-ref",
        help="Changed-file scope base ref for Python checks (for example origin/develop)",
    )
    security_cmd.add_argument(
        "--head-ref",
        default="HEAD",
        help="Changed-file scope head ref used with --since-ref (default: HEAD)",
    )
    security_cmd.add_argument(
        "--python-scope",
        choices=("auto", "changed", "all"),
        default="auto",
        help=(
            "Scope for Python black/isort/bandit checks: auto (changed locally, all in CI), "
            "changed (commit/worktree delta only), or all (all tracked Python files)"
        ),
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
        help="Force-enable zizmor scan even when scanner tier is rustsec",
    )
    security_cmd.add_argument(
        "--with-codeql-alerts",
        action="store_true",
        help="Force-enable CodeQL alert query even when scanner tier is rustsec",
    )
    security_cmd.add_argument(
        "--codeql-repo",
        help="Explicit GitHub repo slug for CodeQL API checks (owner/repo)",
    )
    security_cmd.add_argument(
        "--codeql-min-severity",
        choices=("low", "medium", "high", "critical"),
        default="high",
        help="Minimum CodeQL alert severity that should fail (default: high)",
    )
    security_cmd.add_argument(
        "--require-optional-tools",
        action="store_true",
        help="Fail when optional scanners (for example zizmor/codeql alerts) are requested but missing",
    )
    security_cmd.add_argument("--dry-run", action="store_true")
    security_cmd.add_argument("--offline", action="store_true")
    security_cmd.add_argument("--cargo-home")
    security_cmd.add_argument("--cargo-target-dir")
    security_cmd.add_argument("--format", choices=["text", "json", "md"], default="text")
    security_cmd.add_argument("--output")
    security_cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    security_cmd.add_argument("--pipe-args", nargs="*", help="Extra args for pipe command")
