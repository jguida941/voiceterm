"""devctl release-notes command wrapper."""

from ..common import run_cmd
from ..config import REPO_ROOT


def run(args) -> int:
    """Run generate-release-notes.sh for a target version."""
    cmd = ["./dev/scripts/generate-release-notes.sh", args.version]
    if args.output:
        cmd.extend(["--output", args.output])
    if args.end_ref:
        cmd.extend(["--end-ref", args.end_ref])
    if args.previous_tag:
        cmd.extend(["--previous-tag", args.previous_tag])

    result = run_cmd(
        "release-notes",
        cmd,
        cwd=REPO_ROOT,
        dry_run=args.dry_run,
    )
    return result["returncode"]
