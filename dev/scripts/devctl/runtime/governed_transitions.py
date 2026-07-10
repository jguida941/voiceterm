"""Decorator and manifest loader for governed lifecycle transitions."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from functools import wraps
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
    runtime_enforced: bool = False
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


PreStateResolver = Callable[..., str]
PostStateResolver = Callable[[R], str]


class TransitionStateViolation(ValueError):
    """Raised when an opted-in governed transition sees an illegal state."""

    def __init__(
        self,
        *,
        transition_id: str,
        check_kind: str,
        expected: Sequence[str],
        actual: str,
    ) -> None:
        expected_text = ", ".join(expected) or "(none)"
        super().__init__(
            f"governed transition {transition_id} {check_kind} state violation: "
            f"expected one of {expected_text}; got {actual or '(empty)'}"
        )
        self.transition_id = transition_id
        self.check_kind = check_kind
        self.expected = tuple(expected)
        self.actual = actual


def governed_transition(
    *,
    transition_id: str,
    requires: Sequence[str],
    produces: Sequence[str],
    emits: Sequence[str] = (),
    graph_path: Sequence[str] = (),
    runtime_enforced: bool = False,
    pre_state_resolver: PreStateResolver | None = None,
    post_state_resolver: PostStateResolver[R] | None = None,
    registry: list[TransitionContract] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Register lifecycle transition metadata and optionally enforce states.

    Runtime pre-state resolvers receive the wrapped function's ``*args`` and
    ``**kwargs``. Runtime post-state resolvers receive only the function result.
    """

    def decorate(func: Callable[P, R]) -> Callable[P, R]:
        target_registry = registry if registry is not None else GOVERNED_TRANSITION_REGISTRY
        transition = TransitionContract(
            transition_id=transition_id,
            requires=tuple(requires),
            produces=tuple(produces),
            emits=tuple(emits),
            graph_path=tuple(graph_path),
            runtime_enforced=runtime_enforced,
            owner_module=func.__module__,
            function_name=func.__qualname__,
        )
        _register_transition(transition, target_registry)
        if not runtime_enforced:
            setattr(func, "__governed_transition__", transition)
            return func
        if pre_state_resolver is None and post_state_resolver is None:
            raise ValueError(
                "runtime-enforced governed transitions require at least one "
                "state resolver"
            )

        @wraps(func)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            if pre_state_resolver is not None:
                _enforce_state_ref(
                    transition=transition,
                    check_kind="pre_state",
                    actual=pre_state_resolver(*args, **kwargs),
                    expected=transition.requires,
                )
            result = func(*args, **kwargs)
            if post_state_resolver is not None:
                _enforce_state_ref(
                    transition=transition,
                    check_kind="post_state",
                    actual=post_state_resolver(result),
                    expected=transition.produces,
                )
            return result

        setattr(wrapped, "__governed_transition__", transition)
        return wrapped

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
        runtime_enforced=coerce_bool(mapping.get("runtime_enforced", False)),
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


def _enforce_state_ref(
    *,
    transition: TransitionContract,
    check_kind: str,
    actual: str,
    expected: Sequence[str],
) -> None:
    if actual not in expected:
        raise TransitionStateViolation(
            transition_id=transition.transition_id,
            check_kind=check_kind,
            expected=expected,
            actual=actual,
        )


__all__ = [
    "GOVERNED_TRANSITION_REGISTRY",
    "PostStateResolver",
    "PreStateResolver",
    "TRANSITION_MODULES_STORE_REL",
    "GovernedTransitionModule",
    "TransitionContract",
    "TransitionStateViolation",
    "governed_transition",
    "governed_transition_modules_path",
    "load_governed_transition_modules",
    "load_governed_transitions",
    "load_transition_module_rows",
    "registered_governed_transitions",
    "transition_from_mapping",
]
