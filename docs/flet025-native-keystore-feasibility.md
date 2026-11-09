# Native Android Keystore bridge feasibility — Flet 0.25.2

Checked upstream Flet tag `v0.25.2` on 2026-11-09.

## Verified facts
- Flet 0.25.2's `client/pubspec.yaml` registers built-in extension packages as Flutter dependencies, including `flet_webview`.
- `packages/flet_webview/pubspec.yaml` is an example of a Flutter plugin tied to this generation of Flet.
- Modern `flet-secure-storage==1.1.2` requires `flet==1.1.2`, and BOT KING's legacy UI uses seven missing Flet 1.1.2 attributes.
- Therefore adding the modern Python extension to the existing project is **not** a supported bridge.
- Flet 0.25.2 client storage is not an Android Keystore secret store.

## Engineering route to prototype (not yet implemented)
1. Prototype a Flet 0.25.2-compatible Flutter-side service using `flutter_secure_storage` version compatible with Flutter 3.24.5; check pub resolution first.
2. Add a corresponding Flet 0.25.2 Python service/control with get/set/delete event transport and a typed adapter.
3. Confirm that `flet build apk` includes the custom plugin. A Python-only class cannot access Android Keystore by itself.
4. Test actual Keystore persistence on a device: restart, offline reconnect, explicit disconnect, signed in-place update, and restore/uninstall behavior.
5. Keep pairing key out of prefs, logs and APK; server-side Dhan token remains Oracle-only.
6. Only then connect the verified service to Settings and startup, and release a new version.

## Hard stop
If the Flet 0.25.2 APK builder cannot package a custom Flutter plugin safely, do **not** pretend that the adapter alone provides secure storage. Reassess a controlled framework migration or require manual key entry.

No Android bridge, APK, or auto-login is implemented by this document.
