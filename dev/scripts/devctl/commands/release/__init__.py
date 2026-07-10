"""devctl release command wrapper."""

"""Internal release command implementation package."""


def run(args) -> int:
    """Dispatch the legacy release entry without eager package-import cycles."""
    from .command import run as _run

    return _run(args)
