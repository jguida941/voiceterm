"""Shared defaults and repo paths for devctl."""

from pathlib import Path

DEFAULT_MUTANTS_TIMEOUT = 300
DEFAULT_MEM_ITERATIONS = 20
DEFAULT_MUTATION_THRESHOLD = 0.80
DEFAULT_CI_LIMIT = 5

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "src"
