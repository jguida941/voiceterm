# VoiceTerm Mobile App

SwiftUI iPhone/iPad shell over the shared `VoiceTermMobileCore` package.

This is the current runnable iOS app in the repo.

If you only need one answer:

- run `python3 dev/scripts/devctl.py mobile-app --action simulator-demo --format md`
- it builds the app, syncs real repo data, launches the simulator, and tells
  you exactly what to tap

This app does not invent a second backend. It renders the same
`devctl mobile-status` bundle the desktop Operator Console now prefers:

- `dev/reports/mobile/latest/full.json`
- `dev/reports/mobile/latest/compact.json`
- `dev/reports/mobile/latest/actions.json`

## Current Behavior

- starts in built-in sample mode so the app is usable immediately
- auto-detects a synced `Documents/LiveBundle/` and can switch to it with
  `Use Live Repo Bundle`
- imports either the emitted mobile bundle folder or its `full.json` file
- remembers the imported bundle source between launches
- renders the shared multi-agent dashboard and safe action cards
- renders typed Ralph/controller action previews from the shared mobile bundle
- includes a read-only `Terminal` section with split/combined lane views for
  Codex, Claude, and Operator
- stays read-first; device-side execution still belongs to `devctl`

## Generate Project

```bash
cd app/ios/VoiceTermMobileApp
xcodegen generate
```

Open:

```bash
open VoiceTermMobileApp.xcodeproj
```

## Build Without Signing

```bash
cd app/ios/VoiceTermMobileApp
xcodebuild -project VoiceTermMobileApp.xcodeproj \
  -scheme VoiceTermMobileApp \
  -destination generic/platform=iOS \
  CODE_SIGNING_ALLOWED=NO \
  build
```

## Run On Device

Fastest scripted path from the repo root:

```bash
python3 dev/scripts/devctl.py mobile-app --action device-install --development-team <TEAM_ID> --format md
```

That command:

- detects the plugged-in physical device
- builds a signed `iphoneos` app with `xcodebuild`
- installs it with `xcrun devicectl`
- launches it on-device
- fails honestly if signing or trust state is missing

Manual fallback:

1. Open `VoiceTermMobileApp.xcodeproj` in Xcode.
2. Set your Apple development team for `VoiceTermMobileApp`.
3. Build and run on the target iPhone or simulator.
4. Use `Import Bundle` and choose either the folder that contains the latest
   `mobile-status` projections or that folder's `full.json` file.

## Guided Simulator Demo

From the repo root:

```bash
python3 dev/scripts/devctl.py mobile-app --action simulator-demo --format md
python3 dev/scripts/devctl.py mobile-app --action simulator-demo --live-review --format md
```

What that script does:

- builds and installs `VoiceTermMobileApp`
- syncs the latest repo-backed mobile bundle into `Documents/LiveBundle/`
- launches the app in the simulator
- prints the exact manual check flow plus the current backend action preview

What `--live-review` adds:

- refreshes `review-channel --action status` first
- then syncs the current repo-backed Ralph/review bundle into the app
- prints the exact host-side `devctl` commands that still own Ralph/review
  execution while the simulator acts as the live read surface

What to do after it launches:

1. Tap `Use Live Repo Bundle`.
2. Confirm Overview, Findings, and Actions cards show real repo-backed data.
3. Confirm the Actions section includes typed Ralph/controller previews such as
   `dispatch-report-only`, `pause-loop`, and `resume-loop` when they are
   present in the live bundle.
4. Open `Terminal` and verify the split/combined lane views render.

## Sync Real Repo Data Into Simulator

From the repo root, with the app already installed in the booted simulator:

```bash
app/ios/VoiceTermMobileApp/sync_live_bundle_to_simulator.sh
```

That script emits the current `mobile-status` bundle from the live repo state,
copies it into the app sandbox under `Documents/LiveBundle/`, and makes the
`Use Live Repo Bundle` button available in the app.

The guided simulator script above is the recommended path because it performs
the build, install, sync, and launch steps together and then prints the
expected user flow.

For a real plugged-in iPhone or iPad:

```bash
python3 dev/scripts/devctl.py mobile-app --action device-wizard --format md
python3 dev/scripts/devctl.py mobile-app --action device-install --development-team <TEAM_ID> --format md
```

The wizard path is intentionally diagnostic first. The install path is real,
but it still depends on Xcode signing, a trusted device, and your Apple
development team.

Current honesty boundary:

- the app can now display real repo-backed Ralph/controller action previews
- `--live-review` ties the simulator to the current repo-backed Ralph/review
  state before launch
- the app is still read-first and does not execute those actions on-device yet
- the in-app `Tutorial` button explains the exact live-bundle test flow after
  launch
