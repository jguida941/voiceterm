"""Review-surface consistency implementation package."""

from __future__ import annotations

import sys

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from .command import _disk_turn_authority_parity_errors, build_report, main
