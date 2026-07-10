"""Data models for the typed enum connectivity guard."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EnumMember:
    """One string-valued enum member declared in repo tooling code."""

    enum_name: str
    member_name: str
    value: str
    path: str
    line: int

    @property
    def key(self) -> tuple[str, str]:
        return (self.enum_name, self.member_name)

    def to_dict(self) -> dict[str, object]:
        return {
            "enum": self.enum_name,
            "member": self.member_name,
            "value": self.value,
            "path": self.path,
            "line": self.line,
        }


@dataclass(frozen=True, slots=True)
class EnumConsumer:
    """One decision-site reference to a typed enum member or raw enum value."""

    enum_name: str
    member_name: str
    value: str
    path: str
    line: int
    kind: str

    @property
    def member_key(self) -> tuple[str, str]:
        return (self.enum_name, self.member_name)

    def to_dict(self) -> dict[str, object]:
        return {
            "enum": self.enum_name,
            "member": self.member_name,
            "value": self.value,
            "path": self.path,
            "line": self.line,
            "kind": self.kind,
        }


@dataclass(frozen=True, slots=True)
class EnumConnectivityReport:
    """Connectivity report for all string enums found under scan roots."""

    ok: bool
    mode: str
    enum_count: int
    member_count: int
    connected_count: int
    disconnected_members: tuple[EnumMember, ...]
    consumers: tuple[EnumConsumer, ...]
    scan_roots: tuple[str, ...]

    @property
    def disconnected_count(self) -> int:
        return len(self.disconnected_members)

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "mode": self.mode,
            "enum_count": self.enum_count,
            "member_count": self.member_count,
            "connected_count": self.connected_count,
            "disconnected_count": self.disconnected_count,
            "disconnected_members": [
                member.to_dict() for member in self.disconnected_members
            ],
            "consumers": [consumer.to_dict() for consumer in self.consumers],
            "scan_roots": list(self.scan_roots),
        }
