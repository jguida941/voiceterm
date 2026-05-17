"""Models for the typed ``devctl session`` orientation packet."""

from __future__ import annotations

from dataclasses import asdict, dataclass

DEFAULT_TIMEOUT_SECONDS = 180


@dataclass(frozen=True, slots=True)
class SessionOrientationStep:
    """One command execution within a fresh-session orientation packet."""

    name: str
    source_command: str
    exit_code: int
    ok: bool
    parsed: bool
    duration_ms: int
    error: str = ""


@dataclass(frozen=True, slots=True)
class SessionOrientationPacket:
    """Bounded reducer over startup, resume, review status, and graph context."""

    schema_version: int
    contract_id: str
    command: str
    role: str
    generated_at_utc: str
    branch: str
    head_sha: str
    steps: tuple[SessionOrientationStep, ...]
    startup: dict[str, object]
    session_resume: dict[str, object]
    review_status: dict[str, object]
    context_graph: dict[str, object]
    final: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable packet."""
        data = asdict(self)
        data["steps"] = [asdict(step) for step in self.steps]
        return data


@dataclass(frozen=True, slots=True)
class OrientationStepSpec:
    """One child command that contributes to session orientation."""

    name: str
    command: tuple[str, ...]
    suppress_artifact_writes: bool = True


def mapping(value: object) -> dict[str, object]:
    """Normalize an optional mapping-like JSON value."""
    return dict(value) if isinstance(value, dict) else {}


def text(value: object) -> str:
    """Normalize optional JSON scalars into stripped text."""
    return str(value or "").strip()
