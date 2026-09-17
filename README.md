# Quest3 MR Model Viewer

Standalone mixed-reality GLB viewer for Meta Quest 3 / Quest 3S.

## v1.0.1 release candidate

The viewer runs natively on Quest using Android + C++ OpenXR and Meta Environment Depth. It is built from Meta OpenXR SDK v85 `XrPassthroughOcclusion` through a reproducible GitHub Actions pipeline.

### Core features

- color passthrough mixed reality
- `XR_META_environment_depth` real-world occlusion with filtered depth edges
- standalone ARM64 Quest APK
- Android Storage Access Framework GLB picker
- safe cold start: previously imported GLBs are never auto-loaded
- transactional GLB validation and memory/geometry guards
- BaseColor, Normal and Metallic/Roughness PBR textures
- lighting controls for ambient, key light, azimuth, elevation, warmth and exposure
- direct left/right controller UI interaction
- direct grip manipulation of the floating control tablet
- direct one-hand grip manipulation of imported models
- manual model scale and yaw controls
- physical SIZE presets based on the model's largest dimension: FIT / 32MM / 75MM / 150MM / 300MM
- visible import state: `IDLE`, `WAIT`, `READY`, `ERROR`

### Hardware-tested behavior

Quest 3 hardware testing confirmed passthrough, Environment Depth occlusion, dual-controller tablet interaction, GLB picker round trips, textured PBR rendering, direct tablet/model grip and smooth operation with validated lower-detail models including the ~100k-triangle class.

A 3.03M-triangle reference reproducibly caused severe XR/system lag in the current renderer. v1 keeps a conservative **2,000,000 triangle import ceiling**.

### v1.0.0 regression and v1.0.1 fix

The first v1.0.0 candidate exposed three hardware issues:

- raw glTF `1 unit = 1 metre` was not useful for assets whose authoring unit does not represent intended print/display size,
- tablet text could disappear after an XR/scene restart,
- stale OpenGL object names could plausibly reappear as a white rendering artifact after import.

v1.0.1 removes the raw metre toggle and replaces it with explicit physical largest-dimension presets. It also resets/rebuilds UI GPU meshes on scene creation and releases UI/imported-model GL resources on scene destruction so stale handles cannot cross an EGL/scene lifecycle boundary.

## Import envelope

- GLB file: 192 MiB max
- vertices: 3,000,000 max
- indices: 12,000,000 max
- triangles: 2,000,000 max
- texture edge: 4096 px max
- estimated mipmapped texture residency: 160 MiB max
- estimated total GPU model resources: 256 MiB max
- estimated CPU import working set: 384 MiB max

The most reliable v1 asset path is a binary `.glb` using triangle geometry and conventional PBR textures. Animation, skinning and advanced glTF extension support are outside v1 scope.

## Controls

### Tablet

- Point with either controller and press trigger to activate buttons.
- Hold trigger while dragging sliders.
- Put either controller near the tablet and hold Grip/Squeeze to grab it.
- Move/rotate freely and release Grip to leave it in room space.

### Model

- Put either controller near the model and hold Grip/Squeeze to grab it.
- Release Grip to leave the model in room space.
- `SCALE` adjusts fitted display scale.
- `ROTATE` adjusts model yaw.
- `SIZE` cycles FIT → 32MM → 75MM → 150MM → 300MM → FIT. The selected millimetre value is the model's largest displayed dimension.
- Moving `SCALE` returns SIZE to FIT.
- `RESET ALL` restores default model transform and lighting state.

## Build

GitHub Actions workflow: `.github/workflows/build-quest-apk.yml`

Pinned dependencies:

- Meta OpenXR SDK v85
- cgltf v1.15
- stb image commit `2c980bb59875b0d32144a71867fbdebb2f77cd20`

Build logic lives in `scripts/` and modular patch fragments rather than workflow YAML payloads.

## Install

Download the latest successful `Quest3-MR-ModelViewer-v1.0.1` artifact from GitHub Actions and sideload the APK. Grant requested spatial/environment permissions on first launch.

## Project continuity

- `PROJECT_STATE.md` - current release state and acceptance status
- `BUILD_STATE.md` - architecture, limits and build implementation notes
- `AUDIT.md` - key decisions, regressions and hardware findings
- `HANDOFF.md` - safe continuation point for a future maintainer/chat
- `scripts/CONTROLS.txt` - compact control reference included in build artifacts
