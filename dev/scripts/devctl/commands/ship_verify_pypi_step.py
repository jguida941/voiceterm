"""PyPI verification step helper for `devctl ship`."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Dict

from .ship_common import make_step


def run_verify_pypi_step(args, context: Dict) -> Dict:
    """Check that PyPI reports the expected released version."""
    version = context["version"]
    url = f"https://pypi.org/pypi/voiceterm/{version}/json"
    if args.dry_run:
        return make_step(
            "verify-pypi",
            True,
            0,
            skipped=True,
            details={"url": url, "reason": "dry-run"},
        )

    try:
        with urllib.request.urlopen(url, timeout=30) as response:  # nosec B310
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return make_step(
            "verify-pypi", False, 1, details={"reason": str(exc), "url": url}
        )

    resolved = payload.get("info", {}).get("version")
    if resolved != version:
        return make_step(
            "verify-pypi",
            False,
            1,
            details={"url": url, "expected": version, "resolved": resolved},
        )
    return make_step("verify-pypi", True, details={"url": url, "resolved": resolved})
