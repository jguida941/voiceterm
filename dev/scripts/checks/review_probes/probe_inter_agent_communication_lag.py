#!/usr/bin/env python3
"""Review probe: flag stale or unacknowledged inter-agent packets."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from check_bootstrap import REPO_ROOT
    from probe_bootstrap import (
        ProbeReport,
        RiskHint,
        build_probe_parser,
        emit_probe_report,
    )
except ModuleNotFoundError:  # pragma: no cover - package-style fallback
    from dev.scripts.checks.check_bootstrap import REPO_ROOT
    from dev.scripts.checks.probe_support.bootstrap import (
        ProbeReport,
        RiskHint,
        build_probe_parser,
        emit_probe_report,
    )

from dev.scripts.devctl.runtime.provider_registry import KNOWN_AGENT_PROVIDERS

PROBE_NAME = "inter_agent_communication_lag"
REVIEW_LENS = "multi_agent_runtime_flow"
DEFAULT_LAG_SECONDS = 300
MAX_HINTS = 30
REVIEW_STATE_PATHS = (
    Path("dev/reports/review_channel/projections/latest/review_state.json"),
    Path("dev/reports/review_channel/state/latest.json"),
)


def main(argv: list[str] | None = None) -> int:
    parser = build_probe_parser(PROBE_NAME)
    parser.add_argument(
        "--lag-seconds",
        type=int,
        default=DEFAULT_LAG_SECONDS,
        help="Pending inter-agent packet age that should emit a risk hint.",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    review_state = _resolve_review_state()
    hints: list[RiskHint] = []
    if review_state is not None:
        hints = communication_lag_hints(
            review_state,
            lag_seconds=max(1, int(args.lag_seconds)),
        )
    report = ProbeReport(
        command=PROBE_NAME,
        risk_hints=hints,
        files_scanned=1 if review_state is not None else 0,
        files_with_hints=1 if hints else 0,
    )
    return emit_probe_report(report, output_format=args.format)


def communication_lag_hints(
    path: Path,
    *,
    now: datetime | None = None,
    lag_seconds: int = DEFAULT_LAG_SECONDS,
    max_hints: int = MAX_HINTS,
) -> list[RiskHint]:
    """Return stale inter-agent packet hints from one review-state projection."""
    payload = _json_file(path)
    packets = payload.get("packets") if isinstance(payload, dict) else None
    if not isinstance(packets, list):
        return []
    now_utc = now or datetime.now(timezone.utc)
    known = set(KNOWN_AGENT_PROVIDERS)
    hints: list[RiskHint] = []
    for packet in packets:
        if not isinstance(packet, dict):
            continue
        if str(packet.get("status") or "").strip().lower() != "pending":
            continue
        from_agent = str(packet.get("from_agent") or "").strip().lower()
        to_agent = str(packet.get("to_agent") or "").strip().lower()
        if from_agent == to_agent or from_agent not in known or to_agent not in known:
            continue
        posted_at = _parse_utc(str(packet.get("posted_at") or ""))
        if posted_at is None:
            continue
        age_seconds = int((now_utc - posted_at).total_seconds())
        expired = _expired(packet, now_utc)
        if age_seconds < lag_seconds and not expired:
            continue
        hints.append(_lag_hint(path, packet, age_seconds=age_seconds, expired=expired))
        if len(hints) >= max_hints:
            break
    return hints


def _lag_hint(path: Path, packet: dict[str, object], *, age_seconds: int, expired: bool) -> RiskHint:
    packet_id = str(packet.get("packet_id") or "unknown")
    from_agent = str(packet.get("from_agent") or "")
    to_agent = str(packet.get("to_agent") or "")
    return RiskHint(
        file=path.as_posix(),
        symbol=packet_id,
        risk_type="inter_agent_packet_pending_lag",
        severity="HIGH" if expired else "MEDIUM",
        signals=[
            f"packet_id={packet_id}",
            f"route={from_agent}->{to_agent}",
            f"age_seconds={age_seconds}",
            f"expired={expired}",
            f"latest_event_id={packet.get('latest_event_id') or ''}",
        ],
        ai_instruction=(
            "A peer-agent packet has remained pending long enough to slow the "
            "Codex/Claude feedback loop. ACK, apply, or dismiss it through the "
            "review channel, then decide whether packet-attention/wake routing "
            "or guard evidence requirements need to be strengthened. If the "
            "packet asserts file, registry, or guard state, require concrete "
            "evidence refs or command output before treating it as an "
            "implementation target."
        ),
        review_lens=REVIEW_LENS,
    )


def _expired(packet: dict[str, object], now: datetime) -> bool:
    expires_at = _parse_utc(str(packet.get("expires_at_utc") or ""))
    return expires_at is not None and expires_at <= now


def _parse_utc(value: str) -> datetime | None:
    text = value.strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _json_file(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _resolve_review_state() -> Path | None:
    for rel in REVIEW_STATE_PATHS:
        candidate = REPO_ROOT / rel
        if candidate.is_file():
            return candidate
    return None


if __name__ == "__main__":
    raise SystemExit(main())
