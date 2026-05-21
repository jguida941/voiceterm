"""Typed command-envelope classification for downstream render consumers.

Phase 0.6.A v4.32 (rev_pkt_4706 / plan row
``MP-GUARDIR-V4-PHASE-0-6-A-COMMAND-ENVELOPE-NORMALIZATION-S1``) extends the
v4.31 classifier to carry the full typed route through the envelope, validate
proxy authority against the active decision's authority refs, and parse
command tokens with shlex rather than substring matching.

The classifier maps a (command, executor context, decision authority refs,
runnable status) tuple to a richly-typed result that mirrors the field layout
of ``AttemptedActionReceipt`` so downstream consumers (wrapper builder,
report next-step, final-response gate, stop-gate, response shape) project the
same substrate that ``ControlDecisionObedienceGuard`` uses for packet posts.

Classification states (sum type):

  * ``same_actor_executable``        — executor == subject; safe to render
  * ``peer_lane_status_only``        — executor != subject, no bound proxy
  * ``proxy_authorized_executable``  — executor != subject, proxy_authority_ref
                                       is BOUND to the active decision
  * ``unrunnable_typed_blocker``     — repair_command_runnable=False from gate

v4.32 refinements over v4.31:

1. **Full typed envelope**: executor_actor/role/session, subject_actor/role/
   session, target_role/session, packet_id, source_ref, proxy_execution,
   proxy_authority_bound, repair_command_runnable, classification, reason.
2. **Bound proxy validation**: ``proxy_authorized_executable`` requires the
   ref to be in ``decision_authority_refs`` (decision_id / snapshot_id /
   latest_event_id). A non-empty string alone classifies as peer_lane.
3. **Robust parser**: ``parse_command_envelope_fields`` uses ``shlex.split``
   and exact-token matching, so flags like ``--actorial`` no longer collide
   with ``--actor``, and ``--actor=claude`` / ``--actor claude`` both parse.
"""

from __future__ import annotations

import re
import shlex
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from typing import Literal

# v4.41 (rev_pkt_4713): import the proxy-execution primitive from the
# neutral ``proxy_execution`` module rather than from
# ``control_decision_obedience``. This breaks the import cycle that v4.40
# triggered (classifier → obedience → action_matching → classifier).
from .proxy_execution import proxy_execution as _proxy_execution
from .value_coercion import coerce_bool, coerce_string

COMMAND_ENVELOPE_CLASSIFICATION_CONTRACT_ID = "CommandEnvelopeClassification"
COMMAND_ENVELOPE_CLASSIFICATION_SCHEMA_VERSION = 3

CommandClassification = Literal[
    "same_actor_executable",
    "peer_lane_status_only",
    "proxy_authorized_executable",
    "unrunnable_typed_blocker",
]

#: v4.39 (rev_pkt_4710): mutation-risk taxonomy. Orthogonal to the actor/proxy
#: classification — a same_actor_executable command can still carry
#: shared_worktree_state mutation risk; a peer_lane_status_only command can
#: still NAME a destructive operation without authorization to execute it.
MutationRiskClass = Literal[
    "none",
    "shared_worktree_state",
    "shared_worktree_writes",
    # v4.40 (rev_pkt_4712) — extended taxonomy for cross-consumer convergence:
    "governed_repo_state",
    "governed_review_channel_lifecycle",
    "governed_pipeline_action",
    "bypass_surface",
    # v4.42 (rev_pkt_4714) — typed-action runtime / implementation lane:
    "governed_runtime_state",
    "unclassified_mutation",
]

MutationActionKind = Literal[
    "none",
    # v4.39 — shared worktree state operations
    "git_stash",
    "git_reset",
    "git_checkout",
    "git_restore",
    "git_clean",
    "git_apply",
    # v4.39 — shared worktree writes (shell)
    "shell_redirect",
    "shell_heredoc",
    "shell_herestring",
    "tee_write",
    # v4.40 (rev_pkt_4712) — extended taxonomy:
    "git_add",
    "git_commit",
    "git_push",
    "devctl_commit",
    "devctl_push",
    "devctl_pipeline_action",
    "devctl_review_channel_ensure",
    "devctl_review_channel_recover",
    "devctl_review_channel_launch",
    "devctl_review_channel_stop",
    "devctl_review_channel_reset_implementer_state",
    "devctl_review_channel_post",
    "devctl_review_channel_apply",
    "devctl_review_channel_dismiss",
    "devctl_review_channel_absorb",
    "apply_patch",
    "raw_git_bypass",
    # v4.42 (rev_pkt_4714) — typed-action mutation kinds (consumed via
    # ``typed_action_mutation.classify_typed_action`` adapter):
    "runtime_recover",
    "runtime_terminate",
    "implementation_edit",
]

#: v4.39 mutation classification tables. ``git`` subcommands are exact-token
#: matched against ``git`` in argv; shell features are scanned in raw text
#: because shlex.split strips redirection operators.
_GOVERNED_GIT_SUBCOMMANDS: dict[str, MutationActionKind] = {
    # v4.39 — destructive worktree state operations
    "stash": "git_stash",
    "reset": "git_reset",
    "checkout": "git_checkout",
    "restore": "git_restore",
    "clean": "git_clean",
    "apply": "git_apply",
    # v4.40 (rev_pkt_4712) — repo-state-changing operations
    "add": "git_add",
    "commit": "git_commit",
    "push": "git_push",
}
_SHARED_WORKTREE_STATE_KINDS: frozenset[MutationActionKind] = frozenset(
    {"git_stash", "git_reset", "git_checkout", "git_restore", "git_clean", "git_apply"}
)
_SHARED_WORKTREE_WRITE_KINDS: frozenset[MutationActionKind] = frozenset(
    {"shell_redirect", "shell_heredoc", "shell_herestring", "tee_write"}
)
_GOVERNED_REPO_STATE_KINDS: frozenset[MutationActionKind] = frozenset(
    {"git_add", "git_commit", "git_push", "devctl_commit", "devctl_push"}
)

#: v4.40 — devctl subcommands following ``devctl.py`` or ``dev/scripts/devctl.py``.
_GOVERNED_DEVCTL_SUBCOMMANDS: dict[str, MutationActionKind] = {
    "commit": "devctl_commit",
    "push": "devctl_push",
}

#: v4.40 — devctl review-channel actions that mutate lifecycle / state.
_GOVERNED_REVIEW_CHANNEL_ACTIONS: dict[str, MutationActionKind] = {
    "ensure": "devctl_review_channel_ensure",
    "recover": "devctl_review_channel_recover",
    "launch": "devctl_review_channel_launch",
    "stop": "devctl_review_channel_stop",
    "reset-implementer-state": "devctl_review_channel_reset_implementer_state",
    "post": "devctl_review_channel_post",
    "apply": "devctl_review_channel_apply",
    "dismiss": "devctl_review_channel_dismiss",
    "absorb": "devctl_review_channel_absorb",
}

#: v4.40 — bypass surface markers detected via substring scan (these are
#: typed action identifiers / command flags, not full commands).
_BYPASS_SURFACE_MARKERS: dict[str, MutationActionKind] = {
    "apply_patch": "apply_patch",
    "raw-git": "raw_git_bypass",
    "raw_git": "raw_git_bypass",
}

# Tokens whose value we extract from the parsed argv. Both ``--flag value`` and
# ``--flag=value`` forms are honored by ``parse_command_envelope_fields``.
_COMMAND_ENVELOPE_VALUE_FLAGS: frozenset[str] = frozenset(
    {
        "--actor",
        "--role",
        "--actor-role",
        "--session-id",
        "--target-role",
        "--target-session-id",
        "--packet-id",
        "--proxy-authority-ref",
    }
)


@dataclass(frozen=True, slots=True)
class CommandEnvelopeFields:
    """Parsed argv fields extracted from a command string."""

    subject_actor: str = ""
    subject_role: str = ""
    subject_session_id: str = ""
    target_role: str = ""
    target_session_id: str = ""
    packet_id: str = ""
    proxy_authority_ref_in_command: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CommandEnvelopeClassification:
    """Typed projection of a command's executor / subject / proxy route.

    Field layout mirrors ``AttemptedActionReceipt`` so the same downstream
    obedience-guard substrate can consume either representation.
    """

    classification: CommandClassification
    # Executor (who runs the command)
    executor_actor: str
    executor_role: str
    executor_session_id: str
    # Subject (who the command targets via --actor / --role / --session-id)
    subject_actor: str
    subject_role: str
    subject_session_id: str
    # Target (the --target-role / --target-session-id route, often distinct
    # from subject when the action posts to a different recipient)
    target_role: str
    target_session_id: str
    # Identity refs
    packet_id: str
    source_ref: str
    # Proxy state
    proxy_execution: bool
    proxy_authority_ref: str
    proxy_authority_bound: bool
    # Gate state
    repair_command_runnable: bool
    # Audit
    classification_reason: str
    decision_authority_refs: tuple[str, ...] = field(default_factory=tuple)
    # v4.39 (rev_pkt_4710): mutation-risk dimension orthogonal to actor/proxy.
    # ``mutation_action_kind`` names the specific operation (e.g. ``git_stash``)
    # and ``mutation_risk_class`` classifies its safety category. Defaults
    # of ``"none"`` mean the command is read-only / non-destructive.
    mutation_action_kind: MutationActionKind = "none"
    mutation_risk_class: MutationRiskClass = "none"
    schema_version: int = COMMAND_ENVELOPE_CLASSIFICATION_SCHEMA_VERSION
    contract_id: str = COMMAND_ENVELOPE_CLASSIFICATION_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["decision_authority_refs"] = list(self.decision_authority_refs)
        return payload

    @property
    def is_executable(self) -> bool:
        return self.classification in (
            "same_actor_executable",
            "proxy_authorized_executable",
        )

    @property
    def is_peer_lane(self) -> bool:
        return self.classification == "peer_lane_status_only"

    @property
    def is_unrunnable_blocker(self) -> bool:
        return self.classification == "unrunnable_typed_blocker"

    @property
    def is_governed_mutation(self) -> bool:
        """v4.39: True if this command names a destructive operation that
        requires a typed checkpoint / governed lane / worktree-scope receipt.
        Consumers MUST refuse to render a run-this wrapper for an
        ``is_governed_mutation`` command without explicit operator override."""
        return self.mutation_risk_class != "none"

    @property
    def is_safe_to_render(self) -> bool:
        """v4.39.1 (rev_pkt_4711): composite render-safety check.

        Returns True iff the command is BOTH executable (per actor/proxy
        classification) AND not a governed mutation. Render consumers
        (operator wrappers, next_step_command, response-shape) should
        check ``is_safe_to_render`` rather than ``is_executable`` alone —
        otherwise a same-actor ``git clean -fdx`` would slip through the
        cross-actor refusal but still emit as a runnable wrapper.

        Override path: a future increment may add a typed
        ``governed_worktree_mutation_receipt_ref`` that, when present,
        flips this property True for governed mutations explicitly
        authorized by the operator. For now, this property is strictly
        default-deny on any governed mutation.
        """
        return self.is_executable and not self.is_governed_mutation


#: v4.39.1 (rev_pkt_4711): real shell-redirect lexer. Matches optional fd
#: number (``2``, ``&``) followed by ``>`` or ``>>``, optionally followed by
#: ``|`` (clobber). Examples matched:
#:   ``>file``, ``>> file``, ``2>err.log``, ``&>combined``, ``>|file``
#: Quoted strings are stripped before this regex runs so ``if 1>0:`` inside
#: ``python3 -c '...'`` is not a false positive.
_SHELL_REDIRECT_RE = re.compile(r"(?:\d+|&)?>{1,2}\|?")
_SHELL_HEREDOC_RE = re.compile(r"<<-?(?!<)")
_SHELL_HERESTRING_RE = re.compile(r"<<<")


def _strip_shell_quoted_strings(text: str) -> str:
    """Remove single- and double-quoted substrings from a shell command.

    Used before shell-operator regex scanning so operators *inside* quoted
    strings (e.g. ``python3 -c 'if 1>0: pass'``) don't false-positive as
    redirect operators.

    Conservative: bails out on the first unbalanced quote and leaves the
    rest of the string intact so a malformed command still gets a best-
    effort scan downstream.
    """
    if not text:
        return text
    result: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == "\\" and i + 1 < n:
            # Escape sequence — skip the next char (it's literal, not an
            # operator), don't emit either to the stripped result so it
            # cannot influence the regex match.
            i += 2
            continue
        if c == "'":
            end = text.find("'", i + 1)
            if end == -1:
                # Unbalanced single quote — emit a sentinel space so the
                # regex below doesn't accidentally match unbalanced content.
                return " ".join((text[:i], text[i + 1 :]))
            i = end + 1
            continue
        if c == '"':
            j = i + 1
            while j < n:
                if text[j] == "\\" and j + 1 < n:
                    j += 2
                    continue
                if text[j] == '"':
                    break
                j += 1
            if j >= n:
                return " ".join((text[:i], text[i + 1 :]))
            i = j + 1
            continue
        result.append(c)
        i += 1
    return "".join(result)


def classify_command_mutation(
    command: str,
) -> tuple[MutationActionKind, MutationRiskClass]:
    """v4.39 (rev_pkt_4710) + v4.39.1 (rev_pkt_4711): classify the mutation-
    risk dimension.

    Returns a ``(mutation_action_kind, mutation_risk_class)`` tuple. The
    detection is purely lexical — it observes that a command CONTAINS a
    destructive token; it does not execute or evaluate the command.

    Two scan passes:

    1. **shlex tokenization** — exact-token match for ``git <subcommand>``
       where ``<subcommand>`` is one of stash/reset/checkout/restore/clean/
       apply, and exact-token match for ``tee`` (which writes whatever stdin
       it receives).
    2. **regex scan on quote-stripped text** — shell features (``>``/``>>``
       redirect with optional fd prefix and clobber pipe, ``<<EOF`` heredoc,
       ``<<<word`` herestring) are detected on the command text AFTER
       single/double-quoted substrings are removed. This catches no-space
       redirects (``cat >file``), fd redirects (``cmd 2>err.log``), and
       clobber forms (``cmd >|file``) while avoiding false positives on
       in-string operators (``python3 -c 'if 1>0:'``).

    Precedence (highest-risk first when multiple kinds match): the first
    detected git mutation wins over shell mutation tokens, because the git
    subcommand is the load-bearing semantic; shell features are reported
    only when no git mutation is found.

    Returns ``("none", "none")`` when no destructive pattern matches.
    """
    text = coerce_string(command).strip()
    if not text:
        return ("none", "none")

    # Pass 1: tokenized scan for git/devctl subcommands and ``tee``.
    try:
        tokens = shlex.split(text)
    except ValueError:
        tokens = []
    for i, tok in enumerate(tokens):
        if tok == "git" and i + 1 < len(tokens):
            subcommand = tokens[i + 1]
            kind = _GOVERNED_GIT_SUBCOMMANDS.get(subcommand)
            if kind is not None:
                risk: MutationRiskClass = (
                    "governed_repo_state"
                    if kind in _GOVERNED_REPO_STATE_KINDS
                    else "shared_worktree_state"
                )
                return (kind, risk)
        # v4.40: ``devctl.py <subcommand>`` or
        # ``dev/scripts/devctl.py <subcommand>`` — match the script
        # token endswith ``devctl.py`` so both forms are caught.
        if tok.endswith("devctl.py") and i + 1 < len(tokens):
            subcommand = tokens[i + 1]
            devctl_kind = _GOVERNED_DEVCTL_SUBCOMMANDS.get(subcommand)
            if devctl_kind is not None:
                return (devctl_kind, "governed_repo_state")
            # ``devctl.py pipeline --action <X>`` is also a governed
            # mutation (any pipeline action mutates the pipeline state).
            if subcommand == "pipeline" and "--action" in tokens[i + 2 : i + 6]:
                return ("devctl_pipeline_action", "governed_pipeline_action")
            # ``devctl.py review-channel --action <X>`` — look up X.
            if subcommand == "review-channel":
                # Scan the remaining tokens for ``--action`` and its value.
                rest = tokens[i + 2 :]
                for j, rt in enumerate(rest):
                    if rt == "--action" and j + 1 < len(rest):
                        rc_kind = _GOVERNED_REVIEW_CHANNEL_ACTIONS.get(rest[j + 1])
                        if rc_kind is not None:
                            return (
                                rc_kind,
                                "governed_review_channel_lifecycle",
                            )
    if "tee" in tokens:
        return ("tee_write", "shared_worktree_writes")

    # Pass 2: substring scan for bypass-surface markers. These appear as
    # typed action identifiers (``apply_patch``) or command flags
    # (``raw-git``, ``raw_git``) embedded in larger command strings.
    for marker, marker_kind in _BYPASS_SURFACE_MARKERS.items():
        if marker in text:
            return (marker_kind, "bypass_surface")

    # Pass 3: regex scan on QUOTE-STRIPPED text. Strip quoted strings first
    # so in-quote operators (``python3 -c 'if 1>0:'``) don't false-positive.
    stripped = _strip_shell_quoted_strings(text)

    # Herestring (``<<<``) must be checked before heredoc (``<<``) because
    # ``<<<`` starts with ``<<``.
    if _SHELL_HERESTRING_RE.search(stripped):
        return ("shell_herestring", "shared_worktree_writes")
    if _SHELL_HEREDOC_RE.search(stripped):
        return ("shell_heredoc", "shared_worktree_writes")
    if _SHELL_REDIRECT_RE.search(stripped):
        return ("shell_redirect", "shared_worktree_writes")

    return ("none", "none")


def parse_command_envelope_fields(command: str) -> CommandEnvelopeFields:
    """Tokenize ``command`` and extract typed envelope fields.

    Uses ``shlex.split`` for proper argv tokenization, then walks tokens
    looking for exact flag matches (and ``--flag=value`` forms). This avoids
    the substring collision bug where ``--actorial`` would match a substring
    search for ``--actor``.

    Returns empty fields if the command is empty, unparseable, or lacks the
    relevant flags.
    """
    text = coerce_string(command).strip()
    if not text:
        return CommandEnvelopeFields()
    try:
        tokens = shlex.split(text)
    except ValueError:
        return CommandEnvelopeFields()

    values: dict[str, str] = {}
    i = 0
    while i < len(tokens):
        token = tokens[i]
        # ``--flag=value`` form: exact match on the prefix up to ``=``
        if "=" in token and token.startswith("--"):
            flag, _, value = token.partition("=")
            if flag in _COMMAND_ENVELOPE_VALUE_FLAGS and flag not in values:
                values[flag] = value.strip()
            i += 1
            continue
        # ``--flag value`` form: exact token match, value is next token
        if token in _COMMAND_ENVELOPE_VALUE_FLAGS and token not in values:
            if i + 1 < len(tokens):
                values[token] = tokens[i + 1].strip()
            i += 2
            continue
        i += 1

    # Subject role precedence: --actor-role > --role (--actor-role is the
    # explicit "subject's role" flag in cascade-post calls; --role can be
    # ambiguous between subject and target).
    subject_role = values.get("--actor-role") or values.get("--role") or ""

    return CommandEnvelopeFields(
        subject_actor=values.get("--actor", ""),
        subject_role=subject_role,
        subject_session_id=values.get("--session-id", ""),
        target_role=values.get("--target-role", ""),
        target_session_id=values.get("--target-session-id", ""),
        packet_id=values.get("--packet-id", ""),
        proxy_authority_ref_in_command=values.get("--proxy-authority-ref", ""),
    )


def parse_subject_actor(command: str) -> str:
    """Return the subject actor parsed from ``command``'s ``--actor`` flag.

    Thin wrapper around ``parse_command_envelope_fields`` preserved for
    callers that only need the actor token. Uses shlex-based tokenization;
    does not substring-match against ``--actorial`` or similar.
    """
    return parse_command_envelope_fields(command).subject_actor


def classify_command_envelope(
    *,
    command: str,
    current_actor: str = "",
    current_role: str = "",
    current_session_id: str = "",
    proxy_authority_ref: str = "",
    decision_authority_refs: Iterable[str] = (),
    repair_command_runnable: object = True,
    source_ref: str = "",
) -> CommandEnvelopeClassification:
    """Classify a command for downstream render consumers.

    Precedence:

    1. ``repair_command_runnable`` False → ``unrunnable_typed_blocker``
       (typed BlockerSnapshot stop wins over everything else).
    2. No ``current_actor`` plumbed → ``same_actor_executable`` (backwards-
       compatible "render everything" for legacy call sites).
    3. Command has no ``--actor`` token → ``same_actor_executable``.
    4. ``--actor`` token matches ``current_actor`` (and roles/sessions are
       consistent with same-lane execution) → ``same_actor_executable``.
    5. Cross-actor command with ``proxy_authority_ref`` BOUND to a member of
       ``decision_authority_refs`` → ``proxy_authorized_executable``.
    6. Otherwise (cross-actor with no proxy or unbound proxy) →
       ``peer_lane_status_only``.

    ``decision_authority_refs`` should be the active decision's authority
    refs: ``receipt_id`` / ``source_decision_id`` / ``source_snapshot_id`` /
    ``source_latest_event_id`` collected via
    ``_decision_proxy_authority_refs`` in ``control_decision_obedience.py``.
    """
    runnable = (
        coerce_bool(repair_command_runnable)
        if repair_command_runnable is not None
        else True
    )
    command_text = coerce_string(command).strip()
    fields = parse_command_envelope_fields(command_text)
    executor_actor = coerce_string(current_actor).strip()
    executor_role = coerce_string(current_role).strip()
    executor_session_id = coerce_string(current_session_id).strip()
    proxy_ref = coerce_string(proxy_authority_ref).strip()
    bound_refs = tuple(
        coerce_string(value).strip()
        for value in decision_authority_refs
        if coerce_string(value).strip()
    )
    source_ref_value = coerce_string(source_ref).strip()
    # v4.39 (rev_pkt_4710): mutation-risk classification is orthogonal to
    # the actor/proxy dimensions. Compute it once and attach to every
    # ``_build`` result.
    mutation_kind, mutation_risk = classify_command_mutation(command_text)

    def _build(
        *,
        classification: CommandClassification,
        reason: str,
        proxy_execution_flag: bool,
        proxy_ref_value: str,
        proxy_bound_flag: bool,
        runnable_flag: bool,
    ) -> CommandEnvelopeClassification:
        return CommandEnvelopeClassification(
            classification=classification,
            executor_actor=executor_actor,
            executor_role=executor_role,
            executor_session_id=executor_session_id,
            subject_actor=fields.subject_actor,
            subject_role=fields.subject_role,
            subject_session_id=fields.subject_session_id,
            target_role=fields.target_role,
            target_session_id=fields.target_session_id,
            packet_id=fields.packet_id,
            source_ref=source_ref_value,
            proxy_execution=proxy_execution_flag,
            proxy_authority_ref=proxy_ref_value,
            proxy_authority_bound=proxy_bound_flag,
            repair_command_runnable=runnable_flag,
            classification_reason=reason,
            decision_authority_refs=bound_refs,
            mutation_action_kind=mutation_kind,
            mutation_risk_class=mutation_risk,
        )

    # Layer 1: typed blocker stops everything
    if not runnable:
        return _build(
            classification="unrunnable_typed_blocker",
            reason="repair_command_runnable=False from upstream BlockerSnapshot",
            proxy_execution_flag=False,
            proxy_ref_value="",
            proxy_bound_flag=False,
            runnable_flag=False,
        )

    # Layer 2: backwards-compat for callers without actor context
    if not executor_actor:
        return _build(
            classification="same_actor_executable",
            reason=(
                "no current_actor plumbed; preserve backwards-compatible "
                "executable rendering"
            ),
            proxy_execution_flag=False,
            proxy_ref_value="",
            proxy_bound_flag=False,
            runnable_flag=True,
        )

    # Layer 3: command lacks --actor scoping → not actor-bound
    if not fields.subject_actor:
        return _build(
            classification="same_actor_executable",
            reason="command has no --actor scoping; runnable as same-lane",
            proxy_execution_flag=False,
            proxy_ref_value="",
            proxy_bound_flag=False,
            runnable_flag=True,
        )

    # Use the typed substrate primitive (_proxy_execution) for cross-actor
    # detection so this classification stays consistent with how
    # ControlDecisionObedienceGuard validates packet posts.
    proxy_execution_flag = _proxy_execution(
        executor_actor=executor_actor,
        executor_role=executor_role,
        executor_session_id=executor_session_id,
        subject_actor=fields.subject_actor,
        subject_role=fields.subject_role,
        subject_session_id=fields.subject_session_id,
    )

    # Layer 4: subject matches executor → same-lane execution
    if not proxy_execution_flag:
        return _build(
            classification="same_actor_executable",
            reason="subject_actor matches executor_actor",
            proxy_execution_flag=False,
            proxy_ref_value="",
            proxy_bound_flag=False,
            runnable_flag=True,
        )

    # Layer 5: cross-actor command. Proxy authority must be BOUND.
    proxy_bound = bool(proxy_ref) and proxy_ref in bound_refs
    if proxy_bound:
        return _build(
            classification="proxy_authorized_executable",
            reason=(
                "cross-actor command with bound proxy_authority_ref "
                f"(matched member of decision_authority_refs={list(bound_refs)})"
            ),
            proxy_execution_flag=True,
            proxy_ref_value=proxy_ref,
            proxy_bound_flag=True,
            runnable_flag=True,
        )

    # Layer 6: cross-actor without a bound proxy ref → peer lane
    if proxy_ref and not bound_refs:
        reason = (
            "cross-actor command with proxy_authority_ref present but no "
            "decision_authority_refs supplied (cannot bind); status only"
        )
    elif proxy_ref:
        reason = (
            "cross-actor command with proxy_authority_ref NOT in "
            f"decision_authority_refs={list(bound_refs)}; status only"
        )
    else:
        reason = "cross-actor command without proxy_authority_ref; status only"

    return _build(
        classification="peer_lane_status_only",
        reason=reason,
        proxy_execution_flag=True,
        proxy_ref_value="",
        proxy_bound_flag=False,
        runnable_flag=True,
    )


__all__ = [
    "COMMAND_ENVELOPE_CLASSIFICATION_CONTRACT_ID",
    "COMMAND_ENVELOPE_CLASSIFICATION_SCHEMA_VERSION",
    "CommandClassification",
    "CommandEnvelopeClassification",
    "CommandEnvelopeFields",
    "MutationActionKind",
    "MutationRiskClass",
    "classify_command_envelope",
    "classify_command_mutation",
    "parse_command_envelope_fields",
    "parse_subject_actor",
]
