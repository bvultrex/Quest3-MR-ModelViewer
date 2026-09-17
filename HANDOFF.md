# HANDOFF — Quest3 MR Model Viewer

## Safe checkpoint

The project is at **v1.0.1 regression-fix candidate**.

The v0.3.15 feature baseline is hardware-confirmed stable. v1.0.0 was not accepted because Quest testing exposed an unusable raw metre-scale assumption plus GL lifecycle regressions affecting UI text and producing a white import artifact.

## What works

- Quest 3 standalone Android/OpenXR launch
- passthrough + `XR_META_environment_depth`
- filtered real-world occlusion
- GLB picker via Android Storage Access Framework
- safe cold start with no persisted-model auto-load
- GLB preflight/resource guards
- BaseColor / Normal / Metallic-Roughness PBR path
- lighting controls
- dual-controller trigger UI
- direct no-snap tablet grip with full 6DoF
- direct no-snap model grip with full 6DoF
- fitted scale + yaw controls
- SIZE presets: FIT / 32MM / 75MM / 150MM / 300MM
- import state text: IDLE / WAIT / READY / ERROR

## v1.0.1 regression fixes

- Removed the raw `1 glTF unit = 1 metre` interaction because imported assets do not reliably encode their intended display/print unit.
- SIZE now sets the largest model dimension to an explicit physical millimetre target.
- Manual SCALE exits a physical preset back to FIT.
- `Scene::Create` invalidates static UI GL handles and clears imported-model GL handles rather than trusting names from a prior EGL context.
- `Scene::Destroy` now explicitly releases UI text meshes and imported-model GL resources.

This lifecycle fix targets both observed v1.0.0 graphics regressions: labels disappearing after restart and a white artifact after import.

## Build pipeline

`.github/workflows/build-quest-apk.yml` builds against Meta OpenXR SDK v85 + cgltf v1.15 + pinned stb, applies modular patches, builds ARM64, verifies APK metadata/signature/checksum and uploads artifacts.

## Rules that must survive future work

- Keep feature code in modular patch files, not workflow YAML.
- Preserve the v0.1.2 filtered Environment Depth pass unless deliberately retuning it.
- Cached GLB must never auto-load on cold start.
- Never preserve OpenGL object names across scene/EGL recreation.
- Keep the 2M triangle ceiling unless a renderer-side performance strategy is added.

## Safety envelope

GLB 192 MiB, vertices 3M, indices 12M, triangles 2M, texture edge 4096, mipmapped textures 160 MiB estimate, total GPU 256 MiB estimate, CPU import 384 MiB estimate.

## Required final hardware acceptance

1. cold start with labels visible,
2. close/reopen app and confirm labels remain visible,
3. import a known-good small GLB and confirm READY with no white artifact,
4. cycle SIZE through FIT / 32MM / 75MM / 150MM / 300MM and check physical plausibility,
5. move SCALE and confirm SIZE returns to FIT,
6. verify tablet and model gripping remain stable,
7. restart once more and confirm no cached GLB auto-load.

If all pass, mark v1.0.1 accepted/final. Future features then belong to v1.1.
