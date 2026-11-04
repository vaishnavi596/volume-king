# Navigation responsiveness audit

The Android report is consistent with two code-level problems: synchronous clientStorage.set RPCs with wait_for_result=True are invoked by async refresh code, and every progress refresh rebuilds the bottom navigation while saving preferences and scheduling scroll restoration. A reproduction using Flet 0.25.2 ClientStorage and same-loop native callback delivery demonstrates sync storage starving the loop; the async storage path completes.

Prepared changes (not released):
- Native preference writes run asynchronously and are serialized/coalesced. An atomic local copy with revision-aware restore protects newer settings if the native mirror fails.
- Bottom navigation controls are created once and retain their handlers.
- Same-page background renders do not save preferences or restore scroll.
- Progress updates are coalesced and cannot reopen a page after the user has navigated elsewhere.
- Page construction errors preserve the previous page and record a diagnostic instead of clearing the body.
- A rendering lock protects UI tree mutations between navigation and refresh callbacks.

Validation: all 81 offline regression tests pass, including the real Flet storage callback reproduction, all four navigation handlers, stable buttons, coalescing, preference ordering/recovery and failed-page fallback. All Python files compile.

Limit: this does not establish the exact exception or runtime state on the user's phone; Android/device validation remains required. No new APK build was started and main was not changed.
