# VoiceTerm Mobile

Read-first iPhone-ready client scaffold for the shared VoiceTerm control plane.

This package is intentionally thin:

- PyQt6 and mobile share the same backend contract.
- The app reads the `devctl mobile-status` projection bundle.
- Multi-agent lane state is rendered from the same review/control payloads the
  desktop console already consumes.
- `../VoiceTermMobileApp/` is the actual iOS shell that wraps this package for
  Xcode/device use.

## Current Scope

- decode the merged `mobile-status` projection bundle
- build a human-readable dashboard model for phone UI
- render a SwiftUI dashboard with:
  - sidebar/workspace sections
  - hero status + metrics
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

## Verify

```bash
cd app/ios/VoiceTermMobile
swift test
```
