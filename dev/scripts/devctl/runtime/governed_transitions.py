"""Decorator and manifest loader for governed lifecycle transitions."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from importlib import import_module
from pathlib import Path
from typing import ParamSpec, TypeVar

from .state_store_authority import read_json_mappings_strict
from .value_coercion import coerce_bool, coerce_mapping, coerce_string, coerce_string_items

TRANSITION_MODULES_STORE_REL = Path("dev/state/transition_modules.jsonl")

P = ParamSpec("P")
R = TypeVar("R")


@dataclass(frozen=True, slots=True)
class TransitionContract:
    """Decorator metadata for one governed lifecycle transition."""

    transition_id: str
    requires: tuple[str, ...]
    produces: tuple[str, ...]
    emits: tuple[str, ...] = ()
    graph_path: tuple[str, ...] = ()
    owner_module: str = ""
    function_name: str = ""
    schema_version: int = 1
    contract_id: str = "TransitionContract"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GovernedTransitionModule:
    """Manifest row naming a module that registers governed transitions."""

    module: str
    required: bool = True
    schema_version: int = 1
    contract_id: str = "GovernedTransitionModule"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_mapping(cls, payload: object) -> "GovernedTransitionModule":
        mapping = coerce_mapping(payload)
        return cls(
            module=coerce_string(mapping.get("module")),
            required=coerce_bool(mapping.get("required", True)),
        )


GOVERNED_TRANSITION_REGISTRY: list[TransitionContract] = []


def governed_transition(
    *,
    transition_id: str,
    requires: Sequence[str],
    produces: Sequence[str],
    emits: Sequence[str] = (),
    graph_path: Sequence[str] = (),
    registry: list[TransitionContract] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Register lifecycle transition metadata without wrapping the function."""

    def decorate(func: Callable[P, R]) -> Callable[P, R]:
        target_registry = registry if registry is not None else GOVERNED_TRANSITION_REGISTRY
        transition = TransitionContract(
            transition_id=transition_id,
            requires=tuple(requires),
            produces=tuple(produces),
            emits=tuple(emits),
            graph_path=tuple(graph_path),
            owner_module=func.__module__,
            function_name=func.__qualname__,
        )
        _register_transition(transition, target_registry)
        setattr(func, "__governed_transition__", transition)
        return func

    return decorate


def registered_governed_transitions(
    registry: Sequence[TransitionContract] | None = None,
) -> tuple[TransitionContract, ...]:
    """Return registered transitions in deterministic order."""
    source = registry if registry is not None else GOVERNED_TRANSITION_REGISTRY
    return tuple(sorted(source, key=lambda item: item.transition_id))


def load_transition_module_rows(path: Path) -> tuple[GovernedTransitionModule, ...]:
    """Read governed-transition module manifest rows."""
    return tuple(
        GovernedTransitionModule.from_mapping(row)
        for row in read_json_mappings_strict(path)
    )


def governed_transition_modules_path(repo_root: Path) -> Path:
    """Return the repo-owned governed-transition module manifest path."""
    return repo_root / TRANSITION_MODULES_STORE_REL


def load_governed_transition_modules(
    *,
    repo_root: Path,
    path: Path | None = None,
) -> tuple[GovernedTransitionModule, ...]:
    """Import every module named by the repo-owned transition manifest."""
    manifest_path = path or governed_transition_modules_path(repo_root)
    rows = load_transition_module_rows(manifest_path)
    for row in rows:
        if not row.module:
            if row.required:
                raise ValueError("governed transition module row is missing `module`")
            continue
        try:
            import_module(row.module)
        except ModuleNotFoundError:
            if row.required:
                raise
    return rows


def load_governed_transitions(
    *,
    repo_root: Path,
    path: Path | None = None,
) -> tuple[TransitionContract, ...]:
    """Load manifest modules and return the registered transition metadata."""
    load_governed_transition_modules(repo_root=repo_root, path=path)
    return registered_governed_transitions()


def transition_from_mapping(payload: object) -> TransitionContract:
    """Rebuild a TransitionContract from serialized metadata."""
    mapping = coerce_mapping(payload)
    return TransitionContract(
        transition_id=coerce_string(mapping.get("transition_id")),
        requires=coerce_string_items(mapping.get("requires")),
        produces=coerce_string_items(mapping.get("produces")),
        emits=coerce_string_items(mapping.get("emits")),
        graph_path=coerce_string_items(mapping.get("graph_path")),
        owner_module=coerce_string(mapping.get("owner_module")),
        function_name=coerce_string(mapping.get("function_name")),
    )


def _register_transition(
    transition: TransitionContract,
    registry: list[TransitionContract],
) -> None:
    if not transition.transition_id:
        raise ValueError("governed transition requires a non-empty transition_id")
    if any(item.transition_id == transition.transition_id for item in registry):
        raise ValueError(f"duplicate governed transition id: {transition.transition_id}")
    registry.append(transition)


__all__ = [
    "GOVERNED_TRANSITION_REGISTRY",
    "TRANSITION_MODULES_STORE_REL",
    "GovernedTransitionModule",
    "TransitionContract",
    "governed_transition",
    "governed_transition_modules_path",
    "load_governed_transition_modules",
    "load_governed_transitions",
    "load_transition_module_rows",
    "registered_governed_transitions",
    "transition_from_mapping",
]
