"""devctl release command wrapper."""

from types import SimpleNamespace

from ..common import confirm_or_abort
from . import ship


def run(args) -> int:
    """Run legacy release flow via canonical ship command."""
    confirm_or_abort(f"Run release flow for {args.version}?", args.yes or args.dry_run)
    ship_args = SimpleNamespace(
        version=args.version,
        verify=False,
        verify_docs=False,
        tag=True,
        notes=True,
        github=False,
        github_fail_on_no_commits=False,
        pypi=False,
        homebrew=args.homebrew,
        verify_pypi=False,
        notes_output=None,
        yes=args.yes,
        allow_ci=args.allow_ci,
        dry_run=args.dry_run,
        format="text",
        output=None,
        pipe_command=None,
        pipe_args=None,
    )
    return ship.run(ship_args)
