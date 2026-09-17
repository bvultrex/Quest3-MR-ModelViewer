# HANDOFF — Quest3 MR Model Viewer

## Safe checkpoint

The project is **complete at v1.0.1 accepted final**.

The accepted release has passed the final Quest 3 hardware acceptance test. v1.0.0 was rejected because of raw metre-scale assumptions and GL lifecycle regressions. v1.0.1 replaces raw real-scale with explicit physical SIZE presets and hardens UI/model GL resource lifecycle handling.

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
- restart-safe UI labels
- restart-safe GL resource lifecycle

## v1.0.1 final fixes

- Removed the raw `1 glTF unit = 1 metre` interaction because imported assets do not reliably encode intended display/print units.
- SIZE sets the largest model dimension to an explicit physical millimetre target.
- Manual SCALE exits a physical preset back to FIT.
- `Scene::Create` invalidates static UI GL handles and clears imported-model GL handles rather than trusting names from a prior EGL context.
- `Scene::Destroy` explicitly releases UI text meshes and imported-model GL resources.

Final hardware testing confirmed the previous disappearing-label and white-artifact regressions are no longer observed with the accepted test set.

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

## Final hardware acceptance

Passed on Quest 3:

1. cold start with labels visible,
2. close/reopen keeps labels visible,
3. known-good small GLB reaches READY with no white artifact,
4. SIZE cycles through FIT / 32MM / 75MM / 150MM / 300MM at plausible physical sizes,
5. moving SCALE returns SIZE to FIT,
6. tablet and model gripping remain stable,
7. restart remains safe and does not auto-load cached GLB.

## Continuation policy

**v1.0.1 is frozen as the accepted v1.0 baseline.**

Future work should begin as v1.1+ from this checkpoint. Candidate future areas include Spatial Anchors, surface placement, richer multi-material glTF support, LOD/simplification for heavier meshes, and optional two-hand model manipulation. None are required for the accepted v1.0 scope.
