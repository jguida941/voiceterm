"""Shared launcher bootstrap helpers and validation."""

from __future__ import annotations

import os
import platform
import re
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from pathlib import Path

DEFAULT_REPO_URL = "https://github.com/jguida941/voiceterm"
DEFAULT_RELEASE_OWNER_REPO = "jguida941/voiceterm"
BOOTSTRAP_MODES = {"binary-only", "binary-then-source", "source-only"}
GITHUB_REPO_URL_RE = re.compile(
    r"^https://github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)
GIT_REF_RE = re.compile(r"^[A-Za-z0-9._/-]+$")


def _launcher_version() -> str:
    try:
        return package_version("voiceterm")
    except PackageNotFoundError:
        try:
            from . import __version__

            return __version__
        except Exception:
            return "unknown"


def _default_repo_ref() -> str:
    version = _launcher_version()
    if version == "unknown":
        raise RuntimeError(
            "Cannot detect installed voiceterm package version. "
            "Set VOICETERM_REPO_REF to an explicit tag/commit."
        )
    return f"v{version}"


def _native_root() -> Path:
    configured = os.environ.get("VOICETERM_PY_NATIVE_ROOT")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".local" / "share" / "voiceterm" / "native"


def _native_bin() -> Path:
    configured = os.environ.get("VOICETERM_NATIVE_BIN")
    if configured:
        return Path(configured).expanduser()
    return _native_root() / "bin" / "voiceterm"


def _bootstrap_mode() -> str:
    mode = os.environ.get("VOICETERM_BOOTSTRAP_MODE", "binary-only").strip().lower()
    if mode not in BOOTSTRAP_MODES:
        raise RuntimeError(
            "Invalid VOICETERM_BOOTSTRAP_MODE. "
            "Use one of: binary-only, binary-then-source, source-only."
        )
    return mode


def _target_platform_triplet() -> tuple[str, str]:
    system = platform.system().lower()
    machine = platform.machine().lower()
    os_name_map = {"linux": "linux", "darwin": "darwin"}
    arch_map = {
        "x86_64": "amd64",
        "amd64": "amd64",
        "aarch64": "arm64",
        "arm64": "arm64",
    }
    os_name = os_name_map.get(system)
    arch = arch_map.get(machine)
    if os_name is None or arch is None:
        raise RuntimeError(
            "Unsupported platform for release binary bootstrap: "
            f"{platform.system()}/{platform.machine()}. "
            "Set VOICETERM_NATIVE_BIN or VOICETERM_BOOTSTRAP_MODE=source-only."
        )
    return os_name, arch


def _release_base_url() -> str:
    configured = os.environ.get("VOICETERM_RELEASE_BASE_URL")
    if configured:
        return configured.rstrip("/")
    owner_repo = os.environ.get(
        "VOICETERM_RELEASE_OWNER_REPO", DEFAULT_RELEASE_OWNER_REPO
    )
    return f"https://github.com/{owner_repo}/releases/download"


def _release_asset_names(version: str) -> tuple[str, str]:
    os_name, arch = _target_platform_triplet()
    archive = f"voiceterm-{version}-{os_name}-{arch}.tar.gz"
    checksum = f"{archive}.sha256"
    return archive, checksum


def _validated_repo_url(raw_value: str) -> str:
    value = raw_value.strip()
    match = GITHUB_REPO_URL_RE.fullmatch(value)
    if match is None:
        raise RuntimeError(
            "VOICETERM_REPO_URL must be an https://github.com/<owner>/<repo>[.git] URL."
        )
    owner = match.group("owner")
    repo = match.group("repo")
    return f"https://github.com/{owner}/{repo}"


def _validated_repo_ref(raw_value: str) -> str:
    value = raw_value.strip()
    if not value:
        raise RuntimeError("VOICETERM_REPO_REF must not be empty.")
    if value.startswith("-") or value.endswith("/") or value.endswith(".lock"):
        raise RuntimeError("VOICETERM_REPO_REF must be a normal tag, branch, or commit-like ref.")
    if (
        ".." in value
        or "//" in value
        or "@{" in value
        or any(char.isspace() for char in value)
        or not GIT_REF_RE.fullmatch(value)
    ):
        raise RuntimeError("VOICETERM_REPO_REF contains unsupported characters.")
    return value


def _validated_forward_args(argv: list[str]) -> list[str]:
    forwarded: list[str] = []
    for value in argv:
        if "\x00" in value:
            raise RuntimeError("Launcher arguments must not contain NUL bytes.")
        forwarded.append(value)
    return forwarded
