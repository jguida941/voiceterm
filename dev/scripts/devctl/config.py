"""Shared defaults and repo paths for devctl."""

from pathlib import Path

DEFAULT_MUTANTS_TIMEOUT = 300
DEFAULT_MEM_ITERATIONS = 20
DEFAULT_MUTATION_THRESHOLD = 0.80
DEFAULT_CI_LIMIT = 5

REPO_ROOT = Path(__file__).resolve().parents[3]
_runtime_repo_root: list[Path | None] = [None]


def resolve_src_dir(repo_root: Path) -> Path:
    """Return the Rust workspace root for Cargo-based devctl commands."""
    for candidate in (repo_root / "rust", repo_root / "src"):
        if (candidate / "Cargo.toml").exists():
            return candidate
    return repo_root / "rust"


def set_repo_root(path: Path) -> None:
    """Override the repo root at runtime for cross-repo scanning."""
    resolved_root = path.resolve()
    _runtime_repo_root[0] = resolved_root
    globals()["SRC_DIR"] = resolve_src_dir(resolved_root)


def get_repo_root() -> Path:
    """Return the effective repo root (runtime override or default)."""
    return _runtime_repo_root[0] if _runtime_repo_root[0] is not None else REPO_ROOT


SRC_DIR = resolve_src_dir(REPO_ROOT)
