# Quest3 MR Model Viewer

Standalone mixed-reality GLB viewer for Meta Quest 3 / Quest 3S.

## v1.0.0

The viewer runs natively on Quest using Android + C++ OpenXR and Meta Environment Depth. It is built from Meta OpenXR SDK v85 `XrPassthroughOcclusion` through a reproducible GitHub Actions pipeline.

### Core features

- color passthrough mixed reality
- `XR_META_environment_depth` real-world occlusion
- soft filtered depth edge treatment
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
- `REAL SCALE` mode: glTF 1 linear unit is rendered as 1 real-world metre
- visible import state: `IDLE`, `WAIT`, `READY`, `ERROR`

### Hardware-tested behavior

Quest 3 hardware testing confirmed:

- passthrough and Environment Depth occlusion
- stable tablet/UI interaction
- left/right trigger control
- direct tablet grip + orientation
- GLB document picker round trip
- textured PBR GLB rendering
- direct model grip manipulation
- stable operation with the validated lower-detail reference models, including a ~100k-triangle class model

A 3.03M-triangle reference reproducibly caused severe XR/system lag in the current single-draw renderer. v1.0 therefore keeps a conservative **2,000,000 triangle import ceiling**. This is a deliberate safety limit, not a file-format limitation.

## Import envelope

Current safety guards:

- GLB file: 192 MiB max
- vertices: 3,000,000 max
- indices: 12,000,000 max
- triangles: 2,000,000 max
- texture edge: 4096 px max
- estimated mipmapped texture residency: 160 MiB max
- estimated total GPU model resources: 256 MiB max
- estimated CPU import working set: 384 MiB max

The most reliable v1.0 asset path is a binary `.glb` using triangle geometry and conventional PBR textures. Animation, skinning and advanced glTF extension support are outside the v1.0 scope.

## Controls

### Tablet

- Point with either controller and press trigger to activate buttons.
- Hold trigger while dragging sliders.
- Put either controller near the tablet and hold controller Grip/Squeeze to grab it.
- Move/rotate freely and release Grip to leave it in room space.

### Model

- Put either controller near the model and hold Grip/Squeeze to grab it.
- Position and orientation follow the controller with no snap on pickup.
- Release Grip to leave the model in room space.
- `SCALE` adjusts fitted display scale.
- `ROTATE` adjusts model yaw.
- `REAL SCALE` bypasses automatic fitting and renders glTF metres at physical 1:1 size.
- Moving the `SCALE` slider automatically exits `REAL SCALE`.
- `RESET ALL` restores default model transform and lighting state.

## Build

GitHub Actions workflow:

`.github/workflows/build-quest-apk.yml`

The pipeline installs the Android toolchain, checks out pinned dependencies, applies the modular viewer patches, builds the native Quest APK, validates it, calculates checksums and publishes an artifact.

Pinned dependencies:

- Meta OpenXR SDK v85
- cgltf v1.15
- stb image commit `2c980bb59875b0d32144a71867fbdebb2f77cd20`

Build logic deliberately lives in `scripts/` rather than giant workflow YAML payloads.

## Install

Download the latest successful `Quest3-MR-ModelViewer-v1.0.0` artifact from GitHub Actions and sideload the APK to the headset. Grant the requested spatial/environment permissions on first launch.

## Project continuity

- `PROJECT_STATE.md` - current release state and acceptance status
- `BUILD_STATE.md` - architecture, limits and build implementation notes
- `AUDIT.md` - key decisions, regressions and hardware findings
- `HANDOFF.md` - safe continuation point for a future maintainer/chat
- `scripts/CONTROLS.txt` - compact control reference included in build artifacts
