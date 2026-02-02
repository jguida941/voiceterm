"""devctl mutants command wrapper."""

from typing import List

from ..common import build_env, run_cmd
from ..config import REPO_ROOT


def build_mutants_cmd(args) -> List[str]:
    """Build the mutants.py command line from args."""
    cmd = ["python3", "dev/scripts/mutants.py"]
    if args.all:
        cmd.append("--all")
    if args.module:
        cmd.extend(["--module", args.module])
    if args.timeout:
        cmd.extend(["--timeout", str(args.timeout)])
    if args.results_only:
        cmd.append("--results-only")
    if args.json:
        cmd.append("--json")
    if args.offline:
        cmd.append("--offline")
    if args.cargo_home:
        cmd.extend(["--cargo-home", args.cargo_home])
    if args.cargo_target_dir:
        cmd.extend(["--cargo-target-dir", args.cargo_target_dir])
    if args.plot:
        cmd.append("--plot")
    if args.plot_scope:
        cmd.extend(["--plot-scope", args.plot_scope])
    if args.plot_top_pct is not None:
        cmd.extend(["--plot-top-pct", str(args.plot_top_pct)])
    if args.plot_output:
        cmd.extend(["--plot-output", args.plot_output])
    if args.plot_show:
        cmd.append("--plot-show")
    if args.top:
        cmd.extend(["--top", str(args.top)])
    return cmd


def run(args) -> int:
    """Run mutation testing with the configured args."""
    cmd = build_mutants_cmd(args)
    result = run_cmd("mutants", cmd, cwd=REPO_ROOT, env=build_env(args), dry_run=args.dry_run)
    return 0 if result["returncode"] == 0 else result["returncode"]
