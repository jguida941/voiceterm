"""Internal dataclasses for bounded codeshape ingestion."""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import GraphEdge, GraphNode


@dataclass(frozen=True, slots=True)
class CodeShapeGraph:
    """Bounded codeshape subgraph over selected Python files."""

    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]
    parse_errors: tuple[dict[str, str], ...]


@dataclass(frozen=True, slots=True)
class FunctionInfo:
    rel_path: str
    qualname: str
    local_name: str
    class_name: str | None
    line: int

    @property
    def node_id(self) -> str:
        return f"func:{self.rel_path}::{self.qualname}"

    @property
    def canonical_pointer_ref(self) -> str:
        return f"{self.rel_path}::{self.qualname}"


@dataclass(frozen=True, slots=True)
class CallRecord:
    caller_id: str
    target_pointer_ref: str


@dataclass(frozen=True, slots=True)
class MutationCandidate:
    caller_id: str
    rel_path: str
    qualname: str
    line: int
    column: int
    git_verb: str
    command_source: str
    command_literal: str

    @property
    def node_id(self) -> str:
        return f"mutation:{self.rel_path}::{self.qualname}:{self.line}:{self.column}"

    @property
    def canonical_pointer_ref(self) -> str:
        return f"{self.rel_path}::{self.qualname}:{self.line}"


@dataclass(slots=True)
class ModuleIndex:
    rel_path: str
    module_name: str
    top_level_by_name: dict[str, FunctionInfo] = field(default_factory=dict)
    methods_by_name: dict[tuple[str, str], FunctionInfo] = field(default_factory=dict)
    imported_functions: dict[str, str] = field(default_factory=dict)
    imported_modules: dict[str, str] = field(default_factory=dict)
    imported_classes: dict[str, str] = field(default_factory=dict)
    functions: list[FunctionInfo] = field(default_factory=list)
    call_records: list[CallRecord] = field(default_factory=list)
    mutation_candidates: list[MutationCandidate] = field(default_factory=list)
