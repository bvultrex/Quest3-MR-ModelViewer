# AUDIT

## 2026-09-16 — Bootstrap / v0.1

### Decisions

- Use native OpenXR reference sample for the first hardware bring-up rather than requiring Unity locally.
- Pin reference SDK to Meta OpenXR SDK `v85` for reproducibility.
- Use `XrPassthroughOcclusion`, documented by Meta as the Environment Depth sample for Quest 3 and later.
- Target ARM64 only, matching Quest standalone hardware.
- Build and debug-sign through GitHub Actions.

### Hardening changes

- Do **not** rewrite Meta sample Java package declarations.
- Do **not** rewrite Meta sample manifest Activity class names.
- Change only Gradle `applicationId`, visible app label and version for branding.
- Verify the resulting APK with Android `apksigner`.
- Inspect final package/application metadata with `aapt2 dump badging`.
- Fail CI if expected package or label is missing.
- Generate SHA-256 checksum for each APK artifact.

### Known hardware dependency

The Environment Depth path cannot be accepted without a physical Quest 3/3S test. Meta's sample documentation also mentions enabling `debug.oculus.experimentalEnabled`; current Horizon OS behavior must be verified on-device.
