"""devctl homebrew command wrapper."""

import os

from ..common import build_env, confirm_or_abort, run_cmd
from ..config import REPO_ROOT


def run(args) -> int:
    """Run update-homebrew.sh with confirmation."""
    if os.environ.get("CI") and not args.allow_ci:
        print("Refusing to run homebrew updates in CI. Use --allow-ci to override.")
        return 2
    confirm_or_abort(f"Run update-homebrew.sh {args.version}?", args.yes)
    result = run_cmd(
        "homebrew",
        ["./dev/scripts/update-homebrew.sh", args.version],
        cwd=REPO_ROOT,
        env=build_env(args),
        dry_run=args.dry_run,
    )
    return result["returncode"]
