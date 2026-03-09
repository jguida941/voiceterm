"""Launch helpers for the optional Operator Console entrypoint."""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path
from site import addsitedir, getusersitepackages

from .logging_support import OperatorConsoleDiagnostics


def pyqt6_installed() -> bool:
    """Return whether ``PyQt6`` is importable in the current interpreter."""
    return importlib.util.find_spec("PyQt6") is not None


def running_in_virtualenv() -> bool:
    """Return whether the current interpreter is inside a virtual environment."""
    return bool(
        getattr(sys, "real_prefix", None)
        or sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    )


def build_pyqt6_install_command(
    *,
    python_executable: str | None = None,
    in_virtualenv: bool | None = None,
) -> list[str]:
    """Return the ``pip install`` command used by the launcher."""
    install_command = [
        python_executable or sys.executable,
        "-m",
        "pip",
        "install",
    ]
    if not (running_in_virtualenv() if in_virtualenv is None else in_virtualenv):
        install_command.append("--user")
    install_command.append("PyQt6")
    return install_command


def _refresh_user_site_packages() -> None:
    """Ensure newly installed user-site packages are visible in-process."""
    user_site = Path(getusersitepackages())
    if str(user_site) not in sys.path:
        addsitedir(str(user_site))


def ensure_pyqt6_installed(
    *,
    diagnostics: OperatorConsoleDiagnostics | None = None,
) -> None:
    """Install ``PyQt6`` on demand when the launcher requests it."""
    if pyqt6_installed():
        return

    install_command = build_pyqt6_install_command()
    if diagnostics is not None:
        diagnostics.log(
            level="INFO",
            event="pyqt_install_start",
            message="PyQt6 missing; attempting launcher-managed install",
            details={"command": install_command},
        )

    try:
        subprocess.run(install_command, check=True)
    except subprocess.CalledProcessError as exc:
        if diagnostics is not None:
            diagnostics.log(
                level="ERROR",
                event="pyqt_install_failed",
                message="Launcher-managed PyQt6 install failed",
                details={
                    "returncode": exc.returncode,
                    "command": install_command,
                },
            )
        raise SystemExit(
            "PyQt6 install failed. Rerun `./scripts/operator_console.sh` after "
            "fixing pip/network access, or install it manually with "
            f"`{' '.join(install_command)}`."
        ) from exc

    _refresh_user_site_packages()
    importlib.invalidate_caches()
    if not pyqt6_installed():
        raise SystemExit(
            "PyQt6 install completed but is still not importable in this "
            "interpreter. Try rerunning `./scripts/operator_console.sh`."
        )

    if diagnostics is not None:
        diagnostics.log(
            level="INFO",
            event="pyqt_install_complete",
            message="Launcher-managed PyQt6 install completed",
            details={"command": install_command},
        )
