"""devctl mutation-score command wrapper."""

from typing import List, Optional

from ..common import find_latest_outcomes_file, run_cmd
from ..config import REPO_ROOT, DEFAULT_MUTATION_THRESHOLD
from ..script_catalog import check_script_cmd


def build_mutation_score_cmd(
    path: str,
    threshold: float,
    max_age_hours: float | None,
    warn_age_hours: float | None,
) -> List[str]:
    """Build the check_mutation_score.py command."""
    cmd = check_script_cmd("mutation_score", "--path", path, "--threshold", f"{threshold:.2f}")
    if warn_age_hours is not None:
        cmd.extend(["--warn-age-hours", str(warn_age_hours)])
    if max_age_hours is not None:
        cmd.extend(["--max-age-hours", str(max_age_hours)])
    return cmd


def resolve_outcomes_path(path_arg: Optional[str]) -> Optional[str]:
    """Resolve outcomes.json using an explicit path or the newest file."""
    if path_arg:
        return path_arg
    latest = find_latest_outcomes_file()
    if latest is None:
        return None
    return str(latest)


def run(args) -> int:
    """Run mutation score validation."""
    outcomes_path = resolve_outcomes_path(args.path)
    if outcomes_path is None:
        print("No mutation outcomes.json found under rust/mutants.out")
        return 2
    threshold = args.threshold if args.threshold is not None else DEFAULT_MUTATION_THRESHOLD
    cmd = build_mutation_score_cmd(
        outcomes_path,
        threshold,
        args.max_age_hours,
        args.warn_age_hours,
    )
    result = run_cmd("mutation-score", cmd, cwd=REPO_ROOT, env=None, dry_run=args.dry_run)
    return 0 if result["returncode"] == 0 else result["returncode"]
