"""devctl homebrew command wrapper."""

import os

from ..common import build_env, confirm_or_abort, run_cmd
from ..config import REPO_ROOT


def run(args) -> int:
    """Run update-homebrew.sh with confirmation."""
    if os.environ.get("CI") and not args.allow_ci and not args.dry_run:
        print("Refusing to run homebrew updates in CI. Use --allow-ci to override.")
        return 2
    confirm_or_abort(f"Run update-homebrew.sh {args.version}?", args.yes or args.dry_run)
    env = build_env(args)
    env["VOICETERM_DEVCTL_INTERNAL"] = "1"
    if args.yes or args.dry_run:
        env["VOICETERM_DEVCTL_ASSUME_YES"] = "1"
    result = run_cmd(
        "homebrew",
        ["./dev/scripts/update-homebrew.sh", args.version],
        cwd=REPO_ROOT,
        env=env,
        dry_run=args.dry_run,
    )
    return result["returncode"]
