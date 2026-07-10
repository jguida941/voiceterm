#!/usr/bin/env bash
# Launch codex review-channel session using the bootstrap BypassReceipt.
# This wrapper exists because the multi-line launch command line-wraps badly in zsh
# (the `--terminal none` and colon-containing receipt_id break paste).

set -euo pipefail

RECEIPT_ID='bypass:bootstrap-20260514T114715770073Z'
BYPASS_REASON='Resume per stop_anchor success 2026-05-14T07:37:33Z. HEAD 663147f9. 38 commits batched per rev_pkt_3982. Continue OperatorProjectionLayer feature work from 10-packet design family. Push-batch + raw-git mandates active.'

exec python3 dev/scripts/devctl.py review-channel \
  --action launch \
  --reviewer-mode single_agent \
  --execution-mode markdown-bridge \
  --terminal none \
  --dangerous \
  --bypass-receipt-id "$RECEIPT_ID" \
  --bypass-reason "$BYPASS_REASON" \
  --remote-role operator \
  --format json
