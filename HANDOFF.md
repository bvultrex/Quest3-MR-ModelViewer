# HANDOFF — Quest3 MR Model Viewer

## Safe checkpoint

The project is at **v1.0.0 final candidate**.

The feature set is complete for v1 scope. The hardware-confirmed v0.3.15 baseline is stable on Quest 3. The final v1 additions are `REAL SCALE` and visible import status text.

## What works

- Quest 3 standalone Android/OpenXR launch
- passthrough + `XR_META_environment_depth`
- filtered real-world occlusion
- GLB picker via Android Storage Access Framework
- safe cold start with no persisted-model auto-load
- GLB preflight and resource guards
- BaseColor / Normal / Metallic-Roughness PBR path
- lighting controls
- dual-controller trigger UI
- direct no-snap tablet grip with full 6DoF
- direct no-snap model grip with full 6DoF
- fitted scale and yaw controls
- `REAL SCALE`: glTF 1 unit = 1 physical metre
- import state text: IDLE / WAIT / READY / ERROR

## Build pipeline

`.github/workflows/build-quest-apk.yml`

The workflow:

1. installs JDK 17 / Android SDK / NDK / CMake,
2. checks out Meta OpenXR SDK v85,
3. checks out cgltf v1.15 and pinned stb,
4. brands the app,
5. reconstructs and applies modular patches from `scripts/`,
6. builds the ARM64 debug APK,
7. verifies APK metadata/signature/checksum,
8. uploads the APK plus patched-source snapshots and control reference.

## Important architecture rules

- Do not rewrite Meta's Java namespace merely for branding. Keep branding at applicationId/label/version level.
- Keep the workflow thin. Feature code belongs in modular patch files.
- Fetch the current GitHub blob SHA before every update.
- Keep patch fragments small.
- Preserve the v0.1.2 filtered Environment Depth pass unless intentionally retuning occlusion.
- Preserve safe cold-start behavior. A cached GLB must never auto-load after process start.
- Do not raise the 2M triangle ceiling without a renderer-side performance strategy.

## Safety envelope

- GLB: 192 MiB
- vertices: 3M
- indices: 12M
- triangles: 2M
- texture edge: 4096
- mipmapped texture estimate: 160 MiB
- GPU estimate: 256 MiB
- CPU import estimate: 384 MiB

## Key hardware finding

A 3.03M-triangle / three-2K-map model passes memory preflight but reproducibly causes severe sustained Quest XR/system lag. Lower-detail reference models, including the ~100k-triangle class, are stable and smooth. Treat this as a render-performance limit, not an import/cache bug.

## Final acceptance test

After building v1.0.0 on main, test on Quest 3:

1. cold start is stable and does not auto-load an old GLB,
2. import a known-good small GLB,
3. confirm READY status,
4. grab tablet with either hand,
5. grab model with either hand,
6. toggle REAL SCALE and verify visible size change matches authored glTF units,
7. move SCALE and confirm REAL SCALE disengages,
8. test ERROR with an intentionally unsupported/over-budget GLB if desired,
9. restart and confirm safe empty startup again.

If those pass, v1.0.0 is the final accepted release. Future work belongs to a v1.1 branch/roadmap, not the v1.0 release.
