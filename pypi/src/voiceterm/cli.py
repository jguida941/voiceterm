"""PyPI launcher for bootstrapping and running the native VoiceTerm binary."""

from __future__ import annotations

import hashlib
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from pathlib import Path

DEFAULT_REPO_URL = "https://github.com/jguida941/voiceterm"
DEFAULT_RELEASE_OWNER_REPO = "jguida941/voiceterm"
BOOTSTRAP_MODES = {"binary-only", "binary-then-source", "source-only"}


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


def _download_file(url: str, target: Path) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        raise RuntimeError(
            f"Refusing to download non-https release asset URL: {url!r}."
        )
    request = urllib.request.Request(url, headers={"User-Agent": "voiceterm-launcher"})
    with urllib.request.urlopen(request, timeout=30) as response:  # nosec B310
        target.write_bytes(response.read())


def _sha256_hex(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _parse_checksum_file(checksum_path: Path) -> str:
    raw = checksum_path.read_text(encoding="utf-8").strip()
    if not raw:
        raise RuntimeError("Release checksum file is empty.")
    expected = raw.split()[0].strip().lower()
    if len(expected) != 64 or any(char not in "0123456789abcdef" for char in expected):
        raise RuntimeError(
            "Release checksum file did not contain a valid SHA256 digest."
        )
    return expected


def _install_binary_from_tarball(archive_path: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, mode="r:gz") as tar_handle:
        members = [
            member
            for member in tar_handle.getmembers()
            if member.isfile() and Path(member.name).name == "voiceterm"
        ]
        if not members:
            raise RuntimeError("Release archive does not contain a voiceterm binary.")
        # Prefer the shallowest path if multiple candidates exist.
        member = min(members, key=lambda item: item.name.count("/"))
        extracted = tar_handle.extractfile(member)
        if extracted is None:
            raise RuntimeError(
                "Failed to extract voiceterm binary from release archive."
            )
        tmp_destination = destination.with_suffix(".tmp")
        with tmp_destination.open("wb") as out_handle:
            shutil.copyfileobj(extracted, out_handle)
        tmp_destination.chmod(0o755)
        tmp_destination.replace(destination)


def _bootstrap_native_bin_from_release() -> Path:
    version = _launcher_version()
    if version == "unknown":
        raise RuntimeError(
            "Cannot detect installed voiceterm package version for release download."
        )
    tag = os.environ.get("VOICETERM_REPO_REF", f"v{version}")
    archive_name, checksum_name = _release_asset_names(version)
    base_url = _release_base_url()
    archive_url = f"{base_url}/{tag}/{archive_name}"
    checksum_url = f"{base_url}/{tag}/{checksum_name}"

    root = _native_root()
    root.mkdir(parents=True, exist_ok=True)
    native = _native_bin()

    with tempfile.TemporaryDirectory(prefix="voiceterm-release-bootstrap-") as tmp:
        tmp_dir = Path(tmp)
        archive_path = tmp_dir / archive_name
        checksum_path = tmp_dir / checksum_name
        try:
            _download_file(archive_url, archive_path)
            _download_file(checksum_url, checksum_path)
        except urllib.error.HTTPError as err:
            raise RuntimeError(
                f"Release asset not found for {tag}: {archive_name} (HTTP {err.code})."
            ) from err
        except urllib.error.URLError as err:
            raise RuntimeError(
                f"Failed to download release assets: {err.reason}"
            ) from err

        expected = _parse_checksum_file(checksum_path)
        actual = _sha256_hex(archive_path)
        if actual != expected:
            raise RuntimeError(
                "Release asset checksum mismatch. "
                f"expected={expected} actual={actual} asset={archive_name}"
            )
        _install_binary_from_tarball(archive_path, native)

    if not native.exists():
        raise RuntimeError(
            f"Release bootstrap completed but binary was not found at {native}."
        )
    return native


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check, text=True)


def _resolve_manifest_dir(repo_dir: Path) -> Path:
    candidates = [repo_dir / "rust", repo_dir / "src"]
    for candidate in candidates:
        if (candidate / "Cargo.toml").exists():
            return candidate
    raise RuntimeError(
        "Expected Cargo project in one of: "
        + ", ".join(str(path) for path in candidates)
        + "."
    )


def _bootstrap_native_bin_from_source() -> Path:
    cargo = shutil.which("cargo")
    git = shutil.which("git")
    if not cargo or not git:
        missing = []
        if not git:
            missing.append("git")
        if not cargo:
            missing.append("cargo")
        raise RuntimeError(
            "Missing required bootstrap tools: "
            + ", ".join(missing)
            + ". Install them or set VOICETERM_NATIVE_BIN."
        )

    root = _native_root()
    root.mkdir(parents=True, exist_ok=True)
    repo_url = os.environ.get("VOICETERM_REPO_URL", DEFAULT_REPO_URL)
    repo_ref = os.environ.get("VOICETERM_REPO_REF", _default_repo_ref())

    with tempfile.TemporaryDirectory(prefix="voiceterm-bootstrap-") as tmp:
        repo_dir = Path(tmp) / "repo"
        try:
            _run(
                [
                    git,
                    "clone",
                    "--depth",
                    "1",
                    "--branch",
                    repo_ref,
                    repo_url,
                    str(repo_dir),
                ]
            )
        except subprocess.CalledProcessError as err:
            raise RuntimeError(
                f"Failed to clone {repo_url} at ref {repo_ref}. "
                "Set VOICETERM_REPO_REF to a valid tag/commit if needed."
            ) from err
        manifest_dir = _resolve_manifest_dir(repo_dir)
        _run(
            [
                cargo,
                "install",
                "--locked",
                "--root",
                str(root),
                "--path",
                str(manifest_dir),
                "--bin",
                "voiceterm",
            ]
        )

    native = _native_bin()
    if not native.exists():
        raise RuntimeError(f"Bootstrap completed but binary was not found at {native}.")
    return native


def _bootstrap_native_bin() -> Path:
    mode = _bootstrap_mode()
    if mode == "source-only":
        return _bootstrap_native_bin_from_source()

    try:
        return _bootstrap_native_bin_from_release()
    except Exception as release_err:
        if mode == "binary-only":
            raise RuntimeError(
                "Release-binary bootstrap failed and source fallback is disabled. "
                "Set VOICETERM_BOOTSTRAP_MODE=binary-then-source to allow source fallback."
            ) from release_err
        return _bootstrap_native_bin_from_source()


def _ensure_native_bin() -> Path:
    native = _native_bin()
    if native.exists():
        return native
    return _bootstrap_native_bin()


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
        completed = subprocess.run([str(native), *sys.argv[1:]])
        return int(completed.returncode)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
