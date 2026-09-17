# PROJECT STATE

**Project:** Quest3 MR Model Viewer  
**Target:** Meta Quest 3 / Quest 3S standalone  
**Current milestone:** v1.0.0 final candidate  
**Date:** 2026-09-17

## Release state

The project has reached feature-complete v1 scope. The previously hardware-confirmed v0.3.15 baseline is stable on Quest 3. v1.0.0 adds the final planned features: explicit physical `REAL SCALE` and visible import state text.

## Current architecture

- Native Android + C++ OpenXR.
- Meta OpenXR SDK v85 `XrPassthroughOcclusion` foundation.
- `XR_META_environment_depth` for real-world occlusion.
- cgltf for GLB parsing and stb_image for embedded PNG/JPEG texture decoding.
- OpenGL ES rendering with PBR BaseColor / Normal / Metallic-Roughness support.
- Dual-controller OpenXR trigger + squeeze/grip actions.
- Android Storage Access Framework document picker.
- GitHub Actions debug-signs and validates the ARM64 APK.

## Hardware-confirmed features

- Quest 3 standalone launch and permissions.
- Passthrough + Environment Depth occlusion.
- Stable labelled floating tablet UI.
- Left and right controller trigger interaction.
- Direct tablet grip with full 6DoF orientation.
- GLB picker selection and return to viewer.
- Textured GLB rendering and lighting controls.
- Direct one-hand model grip without snap.
- Stable operation with validated lower-detail models, including the ~100k-triangle class.

## v1.0 final additions

- `REAL SCALE`: glTF 1 linear unit renders as 1 physical metre.
- Manual SCALE automatically exits real-scale mode.
- Real-scale-aware model grab radius.
- Import status text: `IDLE`, `WAIT`, `READY`, `ERROR`.

These two final additions require the last on-headset acceptance test after the v1.0.0 APK is built.

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

## Known limit

A 3.03M-triangle reference with three 2K textures reproducibly caused severe sustained XR/system lag despite passing memory preflight. The 2M triangle ceiling therefore remains a renderer-safety limit for v1.0.

## Acceptance for v1.0.0

- CI build and APK verification succeed.
- Viewer cold-starts without automatically loading a prior model.
- Existing GLB import, PBR, tablet grab and model grab remain stable.
- `REAL SCALE` visibly switches between fitted and physical glTF scale.
- Moving SCALE exits `REAL SCALE`.
- Import status changes appropriately through IDLE / WAIT / READY or ERROR.
