"""Collaboration signal handlers for the Operator Console.

Routes ConversationPanel and TaskBoardPanel user actions into the
guarded command pipeline. Every operator instruction posted through
the chat compose area runs through ``build_review_channel_post_command``
— the same devctl guard path that AI agents use.
"""

from __future__ import annotations

from ...workflows import (
    build_review_channel_post_command,
    render_command,
)


class CollaborationMixin:
    """Conversation and task board signal handlers mixed into OperatorConsoleWindow."""

    def _on_conversation_post(
        self, to_agent: str, summary: str, body: str
    ) -> None:
        """Handle a Send Task click from the conversation panel."""
        try:
            command = build_review_channel_post_command(
                to_agent=to_agent,
                summary=summary,
                body=body,
                from_agent="operator",
                kind="instruction",
                requested_action="implement",
                policy_hint="review_only",
            )
        except ValueError as exc:
            self._append_output(f"Post validation failed: {exc}\n")
            self._record_event(
                "WARNING",
                "collaboration_post_rejected",
                f"Operator post rejected: {exc}",
            )
            return

        self._record_event(
            "INFO",
            "collaboration_post",
            f"Operator posting instruction to {to_agent}",
            details={"to_agent": to_agent, "summary": summary},
        )
        self._start_command(
            command,
            context={"flow": "collaboration_post", "to_agent": to_agent},
            busy_label="Posting...",
        )

    def _on_ticket_selected(self, ticket_id: str) -> None:
        """Handle a ticket click on the task board — log and filter."""
        self._record_event(
            "INFO",
            "ticket_selected",
            f"Operator selected ticket {ticket_id}",
            details={"ticket_id": ticket_id},
        )
        self.statusBar().showMessage(f"Selected ticket: {ticket_id}")
