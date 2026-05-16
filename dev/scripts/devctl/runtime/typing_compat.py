"""Compatibility helpers for stdlib typing features across supported Pythons."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import NoReturn

TYPING_COMPAT_UTILITY_CONTRACT_ID = "TypingCompatUtility"
TYPING_COMPAT_UTILITY_SCHEMA_VERSION = 1

try:
    from typing import assert_never
except ImportError:  # pragma: no cover - Python < 3.11 fallback

    def assert_never(value: NoReturn, /) -> NoReturn:
        """Backport-compatible subset of ``typing.assert_never``."""

        raise AssertionError(f"Expected code to be unreachable, but got: {value!r}")


@dataclass(frozen=True, slots=True)
class TypingCompatUtility:
    exported_symbols: tuple[str, ...] = ("assert_never",)
    compatibility_target: str = "typing.assert_never"
    schema_version: int = TYPING_COMPAT_UTILITY_SCHEMA_VERSION
    contract_id: str = TYPING_COMPAT_UTILITY_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["exported_symbols"] = list(self.exported_symbols)
        return payload
