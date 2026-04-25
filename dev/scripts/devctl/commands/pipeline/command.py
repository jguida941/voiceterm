"""Argparse dispatch entrypoint for ``devctl pipeline``.

This module stays intentionally tiny: it decides which action handler
to run based on ``args.action`` and forwards everything else to the
sibling handler modules. The actual recovery logic lives in
``status_action``, ``recover_action``, ``abandon_action``, and
``refresh_authorization_action`` so each file stays focused.
"""

from __future__ import annotations

import sys

from .abandon_action import run_abandon
from .auto_recover_action import run_auto_recover
from .local_delivery_action import run_mark_delivered_local
from .recover_action import run_recover
from .refresh_authorization_action import run_refresh_authorization
from .status_action import run_status


_ACTION_HANDLERS = {
    "status": run_status,
    "recover": run_recover,
    "abandon": run_abandon,
    "mark-delivered-local": run_mark_delivered_local,
    "refresh-authorization": run_refresh_authorization,
    "auto-recover": run_auto_recover,
}


def run(args) -> int:
    """Entry point invoked by ``devctl.py pipeline``."""
    action = str(getattr(args, "action", "") or "").strip()
    handler = _ACTION_HANDLERS.get(action)
    if handler is None:
        supported = ", ".join(sorted(_ACTION_HANDLERS))
        print(
            f"error: --action must be one of {supported}; got {action!r}",
            file=sys.stderr,
        )
        return 2
    return handler(args)
