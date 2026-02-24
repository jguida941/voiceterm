"""Shared defaults and repo paths for devctl."""

from pathlib import Path

DEFAULT_MUTANTS_TIMEOUT = 300
DEFAULT_MEM_ITERATIONS = 20
DEFAULT_MUTATION_THRESHOLD = 0.80
DEFAULT_CI_LIMIT = 5

REPO_ROOT = Path(__file__).resolve().parents[3]


def resolve_src_dir(repo_root: Path) -> Path:
    """Return the Rust workspace root for Cargo-based devctl commands."""
    for candidate in (repo_root / "rust", repo_root / "src"):
        if (candidate / "Cargo.toml").exists():
            return candidate
    return repo_root / "rust"


SRC_DIR = resolve_src_dir(REPO_ROOT)
