"""Collaboration and review-lane state helpers for the Operator Console."""

from .context_pack_refs import (
    context_pack_ref_lines,
    context_pack_refs_payload,
    parse_context_pack_refs,
)
from .conversation_state import (
    AGENT_DISPLAY_NAMES,
    AGENT_ROLES,
    ConversationMessage,
    ConversationSnapshot,
    build_conversation_snapshot,
)
from .task_board_state import TaskBoardSnapshot, TaskTicket, build_task_board_snapshot
from .timeline_builder import TimelineEvent, build_timeline_from_snapshot
