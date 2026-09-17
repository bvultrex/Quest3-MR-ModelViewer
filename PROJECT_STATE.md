# PROJECT STATE

**Project:** Quest3 MR Model Viewer  
**Target:** Meta Quest 3 / Quest 3S standalone  
**Current milestone:** v1.0.1 accepted final release  
**Date:** 2026-09-18

## Release state

**v1.0.1 is hardware-accepted on Quest 3 and is the final v1.0 release.**

The first v1.0.0 candidate was rejected after Quest testing exposed three regressions: misleading raw metre scaling, UI labels disappearing after restart, and a white rendering artifact during a later import. v1.0.1 corrected those issues and passed the final on-headset acceptance pass.

## Current architecture

- Native Android + C++ OpenXR on Meta OpenXR SDK v85 `XrPassthroughOcclusion`.
- `XR_META_environment_depth` real-world occlusion.
- cgltf GLB parsing and stb_image embedded PNG/JPEG decoding.
- OpenGL ES PBR BaseColor / Normal / Metallic-Roughness path.
- Dual-controller trigger + squeeze/grip actions.
- Android Storage Access Framework picker.
- GitHub Actions builds, debug-signs and verifies ARM64 APK artifacts.

## Hardware-confirmed features

- Quest 3 standalone launch and permissions.
- Passthrough + Environment Depth occlusion.
- Stable floating tablet interaction with both controllers.
- Direct tablet grab with full 6DoF orientation.
- GLB picker selection and return.
- Textured GLB rendering and lighting controls.
- Direct one-hand model grab without snap.
- Stable lower-detail rendering including the ~100k-triangle class.
- UI labels survive close/reopen and scene restart.
- Known-good GLBs import without the prior white artifact.
- SIZE presets behave plausibly at FIT / 32MM / 75MM / 150MM / 300MM.
- Manual SCALE returns SIZE to FIT.
- Cold restart does not auto-load a prior GLB.

## v1.0.1 final changes

- Raw `1 glTF unit = 1 metre` mode removed.
- `SIZE` cycles FIT / 32MM / 75MM / 150MM / 300MM using the model's largest dimension.
- Manual SCALE returns SIZE to FIT.
- Static UI GPU meshes are invalidated/rebuilt on Scene::Create.
- UI text and imported-model GL resources are explicitly released on Scene::Destroy.
- Import status remains IDLE / WAIT / READY / ERROR.

## Safety envelope

- 192 MiB maximum GLB file size.
- 3,000,000 vertices.
- 12,000,000 indices.
- 2,000,000 triangles.
- 4096 px maximum texture edge.
- 160 MiB estimated mipmapped texture residency.
- 256 MiB estimated total GPU resources.
- 384 MiB estimated CPU import working set.
- Persisted source GLB is never auto-loaded on cold start.

## Known performance limit

A 3.03M-triangle reference with three 2K textures reproducibly caused severe sustained XR/system lag despite passing memory preflight. Keep the 2M renderer ceiling unless a future renderer-side LOD/simplification strategy is added.

## Acceptance result

Final Quest 3 acceptance passed:

- labels remain visible across restart,
- known-good GLB import reaches READY with no white artifact,
- SIZE presets are physically plausible,
- SCALE returns SIZE to FIT,
- tablet and model grip remain stable,
- cold restart remains safe and does not auto-load cached content.

**Status: COMPLETE / ACCEPTED.** Future work belongs to v1.1 or later.
