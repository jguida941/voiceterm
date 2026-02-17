"""devctl pypi command wrapper."""

import os

from ..common import build_env, confirm_or_abort, run_cmd
from ..config import REPO_ROOT


def run(args) -> int:
    """Run publish-pypi.sh with optional upload."""
    if os.environ.get("CI") and not args.allow_ci and not args.dry_run:
        print("Refusing to run PyPI publish in CI. Use --allow-ci to override.")
        return 2

    env = build_env(args)
    env["VOICETERM_DEVCTL_INTERNAL"] = "1"

    cmd = ["./dev/scripts/publish-pypi.sh"]
    if args.upload:
        confirm_or_abort("Publish package to PyPI?", args.yes or args.dry_run)
        cmd.append("--upload")

    result = run_cmd(
        "pypi",
        cmd,
        cwd=REPO_ROOT,
        env=env,
        dry_run=args.dry_run,
    )
    return result["returncode"]
