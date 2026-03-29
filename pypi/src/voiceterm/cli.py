"""PyPI launcher for bootstrapping and running the native VoiceTerm binary."""

from __future__ import annotations

import subprocess
import sys

from .bootstrap import _ensure_native_bin
from .bootstrap_support import _validated_forward_args


def main() -> int:
    try:
        native = _ensure_native_bin()
    except Exception as err:  # pragma: no cover - user-facing launcher error
        print(f"voiceterm launcher error: {err}", file=sys.stderr)
        print(
            "Install native VoiceTerm manually or set VOICETERM_NATIVE_BIN.",
            file=sys.stderr,
        )
        return 1

    try:
        forwarded_args = _validated_forward_args(sys.argv[1:])
        completed = subprocess.run([str(native), *forwarded_args], check=False)
        return int(completed.returncode)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
