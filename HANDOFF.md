# HANDOFF — Quest3 MR Model Viewer

## Safe checkpoint

The project is at **v0.1 hardware bring-up**. The intended first APK is based on Meta OpenXR SDK v85 `XrPassthroughOcclusion`, not yet the final model viewer UI.

## Why

The immediate goal is to prove standalone Quest 3 Passthrough + `XR_META_environment_depth` + dynamic occlusion with a reproducible cloud build, so the user does not need Unity or Android Studio on the local PC.

## Build pipeline

`.github/workflows/build-quest-apk.yml`

The workflow:

1. installs JDK 17 / Android SDK / NDK 27.0.12077973 / CMake 3.22.1,
2. checks out Meta OpenXR SDK v85,
3. builds `XrPassthroughOcclusion`,
4. brands only applicationId/label/version,
5. verifies signature and APK metadata,
6. uploads the APK, checksum and badging report.

## Important constraint

Do not rewrite Meta's Java package namespace just to brand the APK. `applicationId` can differ from the Java namespace and keeps Activity/JNI wiring safer.

## Next actions

1. Push bootstrap files to `bvultrex/Quest3-MR-ModelViewer`.
2. Observe first GitHub Actions run.
3. If CI fails, inspect failing step/log and patch workflow.
4. Download successful APK artifact.
5. Hardware test on Quest 3.
6. Once depth/occlusion passes, start custom v0.2 model viewer implementation.
