# VoiceTerm Mobile

Shared Swift package for the VoiceTerm iPhone/iPad app.

This package is intentionally thin:

- PyQt6 and mobile share the same backend contract.
- The app reads the `devctl mobile-status` projection bundle.
- `ControlState`, `ReviewState`, and later typed daemon/runtime projections are
  the intended primary backend contract. `full.json`,
  `controller_payload`, and `review_payload` are still transitional
  compatibility shapes during the current migration.
- Multi-agent lane state is rendered from the same review/control payloads the
  desktop console already consumes.
- `../VoiceTermMobileApp/` is the actual iOS shell that wraps this package for
  Xcode/device use.

This package is not a second app target. If you want to launch the mobile app,
use `../VoiceTermMobileApp/`.

## Current Scope

- decode the merged `mobile-status` projection bundle
- build a human-readable dashboard model for phone UI
- render a SwiftUI dashboard with:
  - operator-console-style sidebar/workspace sections
  - control-panel hero status + metrics
  - shared approval-policy status
  - current instruction and findings cards
  - next actions
  - multi-agent lane cards
  - safe action cards from `actions.json`
  - simple/technical reading modes

## Refresh Data

From the repo root:

```bash
python3 dev/scripts/devctl.py mobile-status \
  --phone-json dev/reports/autonomy/queue/phone/latest.json \
  --review-status-dir dev/reports/review_channel/latest \
  --view full \
  --emit-projections dev/reports/mobile/latest \
  --format json \
  --output /tmp/mobile-status-report.json
```

The phone client prefers this bundle:

- `dev/reports/mobile/latest/full.json`
- `dev/reports/mobile/latest/compact.json`
- `dev/reports/mobile/latest/actions.json`

That keeps the phone UI aligned with:

- `devctl mobile-status`
- the PyQt6 Operator Console mobile relay panel, which now prefers the same
  emitted bundle before falling back to on-the-fly merging
- future notifier adapters

If the autonomy `phone-status` artifact is missing, `mobile-status` now falls
back to review-channel live data and still emits a usable phone bundle with a
warning instead of failing closed.

## Verify

```bash
cd app/ios/VoiceTermMobile
swift test
```
