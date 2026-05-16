"""Helper functions for governed transition typechecking."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime

from .enum_compat import StrEnum
from .session_termination_time import parse_utc


def read_field(obj: object, name: str) -> object:
    if obj is None:
        return None
    if isinstance(obj, Mapping):
        return obj.get(name)
    return getattr(obj, name, None)


def read_text(obj: object, name: str) -> str:
    value = read_field(obj, name)
    if isinstance(value, StrEnum):
        return value.value
    return str(value or "").strip()


def closure_lifecycle_id(closure: object) -> str:
    return read_text(closure, "exception_lifecycle_id") or read_text(
        closure, "lifecycle_id"
    )


def string_items(value: object) -> list[str]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def composed_refs(closure: object) -> tuple[str, ...]:
    refs = [
        read_text(closure, "validation_receipt_id"),
        read_text(closure, "action_result_id"),
        read_text(closure, "run_record_id"),
        read_text(closure, "commit_receipt_ref"),
        read_text(closure, "bypass_expiry_receipt_ref"),
    ]
    refs.extend(string_items(read_field(closure, "composed_receipt_refs")))
    refs.extend(string_items(read_field(closure, "proof_artifacts")))
    return tuple(dict.fromkeys(ref for ref in refs if ref))


def commit_ref(closure: object) -> str:
    direct = read_text(closure, "commit_sha")
    if direct:
        return direct
    for ref in composed_refs(closure):
        for prefix in ("commit:", "commit_sha:", "git_commit:"):
            if ref.startswith(prefix):
                return ref[len(prefix) :]
    return ""


def evidence_has_ref(evidence: Mapping[str, object], ref: str) -> bool:
    if ref in evidence:
        return True
    refs = evidence.get("refs")
    if isinstance(refs, Iterable) and not isinstance(refs, (str, bytes, Mapping)):
        return ref in {str(item) for item in refs}
    return False


def evidence_has_commit(evidence: Mapping[str, object], ref: str) -> bool:
    if evidence_has_ref(evidence, ref):
        return True
    for prefixed in commit_ref_variants(ref):
        if evidence_has_ref(evidence, prefixed):
            return True
    commits = evidence.get("commit_shas")
    if isinstance(commits, Iterable) and not isinstance(commits, (str, bytes, Mapping)):
        return ref in {str(item) for item in commits}
    return False


def commit_ref_variants(ref: str) -> tuple[str, str, str]:
    return (f"commit:{ref}", f"commit_sha:{ref}", f"git_commit:{ref}")


def bypass_still_active(
    *,
    bypass_lifecycle: object | None,
    bypass_expiry: object | None,
    now: datetime,
) -> bool:
    lifecycle_state = read_text(bypass_lifecycle, "state")
    if lifecycle_state:
        return lifecycle_state not in {"bypass_expired", "bypass_revoked"}
    expires_at = read_text(bypass_expiry, "expires_at_utc")
    if expires_at:
        parsed = parse_utc(expires_at)
        return parsed is None or parsed > now
    return not bool(read_text(bypass_expiry, "expired_at_utc"))


def bypass_links_to_exception(
    bypass_lifecycle: object | None,
    lifecycle_id: str,
) -> bool:
    if bypass_lifecycle is None:
        return False
    governed_exception = read_field(bypass_lifecycle, "governed_exception")
    linked_id = read_text(governed_exception, "lifecycle_id")
    if not linked_id:
        evaluation = read_field(bypass_lifecycle, "evaluation")
        linked_id = read_text(evaluation, "governed_exception_lifecycle_id")
    return bool(linked_id) and linked_id == lifecycle_id


__all__ = [
    "bypass_links_to_exception",
    "bypass_still_active",
    "closure_lifecycle_id",
    "commit_ref",
    "composed_refs",
    "evidence_has_commit",
    "evidence_has_ref",
    "read_field",
    "read_text",
]
