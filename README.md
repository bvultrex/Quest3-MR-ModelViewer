# Quest3 MR Model Viewer

Native Meta Quest 3 mixed-reality model viewer project.

## v0.1 hardware bring-up

The first milestone validates the platform layer before custom model importing is added:

- standalone Quest 3 / Android / OpenXR
- color passthrough
- `XR_META_environment_depth`
- real-world depth occlusion
- ARM64 APK
- reproducible cloud build via GitHub Actions

For v0.1 CI checks out Meta's official **Meta OpenXR SDK v85** and builds the official `XrPassthroughOcclusion` sample. Meta documents that sample for Quest 3 and later and specifically uses it to demonstrate Environment Depth occlusion.

The build keeps Meta's internal Java package/namespace intact and only changes the Android `applicationId`, visible label, and version. This minimizes risk to the sample's Activity/JNI wiring.

## Download the APK

Open **Actions → Build Quest APK → latest successful run → Artifacts** and download:

`Quest3-MR-ModelViewer-v0.1`

The artifact contains:

- `Quest3-MR-ModelViewer-v0.1-debug.apk`
- `SHA256SUMS.txt`
- `APK-BADGING.txt`

CI verifies the debug APK signature and confirms the expected install package and label before publishing the artifact.

## Install / test

Sideload the debug APK with your preferred Quest sideload method. On first launch grant requested spatial/environment permissions.

Expected v0.1 result: passthrough is visible and virtual sample geometry is dynamically hidden by real-world geometry using Environment Depth.

Meta's native SDK currently documents an experimental-feature system property for samples:

```bash
adb shell setprop debug.oculus.experimentalEnabled 1
```

The property resets on reboot. We will determine during the first Quest 3 hardware test whether the current Horizon OS build still needs it for Environment Depth.

## Roadmap after v0.1 passes

1. Replace the reference sample content with our own app shell.
2. GLB/glTF model loading from headset storage.
3. Controller and hand manipulation.
4. True-size and preset scaling.
5. Surface placement using live environment depth.
6. Spatial anchors and saved placements.
7. Measurement, wireframe and inspection tools.

Continuity files: `PROJECT_STATE.md`, `AUDIT.md`, `HANDOFF.md`.
