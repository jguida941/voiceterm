"""Release-asset helpers for the launcher bootstrap flow."""

from __future__ import annotations

import platform


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


def _release_asset_names(version: str) -> tuple[str, str]:
    os_name, arch = _target_platform_triplet()
    archive = f"voiceterm-{version}-{os_name}-{arch}.tar.gz"
    checksum = f"{archive}.sha256"
    return archive, checksum
