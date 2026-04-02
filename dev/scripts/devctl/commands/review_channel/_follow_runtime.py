"""Compatibility support surface for review-channel follow runtime helpers."""

from __future__ import annotations

from ...review_channel.follow_stream import (
    build_follow_completion_report,
    build_follow_output_error_report,
    emit_follow_ndjson_frame,
    reset_follow_output,
)
from ...review_channel.heartbeat import refresh_bridge_heartbeat
from ...review_channel.lifecycle_state import (
    read_publisher_state,
    write_publisher_heartbeat,
    write_reviewer_supervisor_heartbeat,
)
from ...review_channel.peer_liveness import reviewer_mode_is_active
from ...review_channel.reviewer_state import (
    ensure_reviewer_heartbeat,
    reviewer_state_write_to_dict,
)
from ...time_utils import utc_timestamp
from . import ensure as _ensure_mod
from ._ensure_follow_runtime import run_ensure_follow_action
from ._ensure_runtime import run_ensure_action
from ._publisher import (
    ensure_reviewer_supervisor_running as _ensure_reviewer_supervisor_running,
)
from ._publisher import spawn_follow_publisher as _spawn_follow_publisher
from ._publisher import spawn_reviewer_supervisor as _spawn_reviewer_supervisor
from ._publisher import verify_detached_start as _verify_detached_start
from ._publisher import (
    verify_reviewer_supervisor_start as _verify_reviewer_supervisor_start,
)
from ._recover import run_recover_action as _run_recover_action
from ._reviewer import build_reviewer_state_report as _build_reviewer_state_report
from ._reviewer_follow_runtime import (
    run_reviewer_follow_action,
    run_reviewer_state_action,
)
from .status import _attach_reviewer_worker, _read_publisher_state_safe, _run_status_action

EnsureActionDeps = _ensure_mod.EnsureActionDeps
