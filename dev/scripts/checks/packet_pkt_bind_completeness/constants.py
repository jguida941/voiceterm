"""Constants for the packet PKT-BIND completeness guard."""

try:
    from check_bootstrap import REPO_ROOT, ensure_repo_root_on_syspath
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        ensure_repo_root_on_syspath,
    )

ensure_repo_root_on_syspath(REPO_ROOT)

from dev.scripts.devctl.runtime.collaboration_packet_kinds import (
    COLLABORATION_LIFECYCLE_PACKET_KINDS,
    TASK_PRODUCED_PACKET_KIND,
    TASK_STARTED_PACKET_KIND,
)

COMMAND = "check_packet_pkt_bind_completeness"
DEFAULT_EVENT_LOG_REL = "dev/reports/review_channel/events/trace.ndjson"
DEFAULT_PLAN_INDEX_REL = "dev/state/plan_index.jsonl"
MANDATE_PACKET_ID = "rev_pkt_4017"
MANDATE_OBSERVED_AT_UTC = "2026-05-14T15:37:25Z"
DEFAULT_GRACE_MINUTES = 30
LIFECYCLE_PACKET_KINDS = COLLABORATION_LIFECYCLE_PACKET_KINDS
TASK_STARTED_KIND = TASK_STARTED_PACKET_KIND
TASK_PRODUCED_KIND = TASK_PRODUCED_PACKET_KIND
PACKET_POSTED_EVENT = "packet_posted"
TASK_STARTED_BINDING_MUTATION_OP = "task_started_packet_binding"
