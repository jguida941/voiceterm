# iOS Mobile Scaffold Language Retired

Date: 2026-03-09
Status: archived clarification

## Summary

Older docs used "client scaffold" and similar wording for the iOS work.
That wording is now retired.

## Current Canonical Split

- `app/ios/VoiceTermMobileApp/` is the runnable iPhone/iPad app.
- `app/ios/VoiceTermMobile/` is the shared Swift package used by that app.

The package is not an archived old app. It remains part of the live mobile
surface and should stay in active use.

## Why This Was Archived

The old wording made it sound like:

- there were two competing iOS apps, or
- the shared package was a stale prototype that should be deleted

Neither was true. This archive note exists so future docs can point to one
clear interpretation instead of reusing the older language.
