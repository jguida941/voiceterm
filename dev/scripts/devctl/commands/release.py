"""devctl release command wrapper."""

import os

from ..common import build_env, confirm_or_abort, run_cmd
from ..config import REPO_ROOT


def run(args) -> int:
    """Run release.sh and optional homebrew update."""
    if os.environ.get("CI") and not args.allow_ci:
        print("Refusing to run release/homebrew in CI. Use --allow-ci to override.")
        return 2
    confirm_or_abort(f"Run release.sh {args.version}?", args.yes)
    result = run_cmd(
        "release",
        ["./dev/scripts/release.sh", args.version],
        cwd=REPO_ROOT,
        env=build_env(args),
        dry_run=args.dry_run,
    )
    if result["returncode"] != 0:
        return result["returncode"]
    if args.homebrew:
        confirm_or_abort(f"Run update-homebrew.sh {args.version}?", args.yes)
        hb = run_cmd(
            "homebrew",
            ["./dev/scripts/update-homebrew.sh", args.version],
            cwd=REPO_ROOT,
            env=build_env(args),
            dry_run=args.dry_run,
        )
        return hb["returncode"]
    return 0
