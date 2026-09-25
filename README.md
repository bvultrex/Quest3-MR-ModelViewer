# Quest3 MR Model Viewer

Standalone mixed-reality GLB viewer for Meta Quest 3 / Quest 3S.

## v1.5.0 candidate

Current code is based on the hardware-confirmed viewer line through v1.4.1 and adds restart-safe interaction state plus a multi-model scene.

### Current features

- color passthrough + `XR_META_environment_depth` real-world occlusion
- filtered v0.1.2 Environment Depth edge treatment
- Android Storage Access Framework GLB picker with safe cold start
- BaseColor / Normal / Metallic-Roughness PBR, multi-material GLBs and texture reuse
- direct left/right controller UI interaction
- direct no-snap tablet and model grabbing
- FIT and physical SIZE presets: 32 / 75 / 150 / 300 mm
- rigged GLB skinning, BONES display, joint manipulation and two-bone IK
- playback of the first supported GLB animation clip
- up to 6 models in one scene in v1.5.0
- visible import state: IDLE / WAIT / READY / ERROR

## v1.5.0 changes

### Restart-safe interaction state

Every Scene/EGL recreation increments a scene generation. The render interaction state detects the generation change and clears tablet/model grab ownership, trigger/grip edge latches, current selection, placement state and UI control latches. A grip or trigger already held during restart is sampled as the new baseline instead of creating a false press.

This specifically addresses a regression where the tablet could no longer be grabbed after restarting the app because stale CPU-side grab state survived the scene lifecycle.

### Multi-model scene

Pressing IMPORT GLB archives the currently active model instead of replacing it. The selected next GLB becomes the new active model while older models remain visible and directly grabbable.

- maximum scene count: 6 models
- aggregate estimated scene GPU budget: 768 MiB
- grab an older model to select it
- SIZE / SCALE / ROTATE / RESET operate on the selected model
- the newest model remains the live rig / IK / animation target
- older rigged models keep a frozen snapshot of their current skin palette when another model is imported

## Import / safety envelope

Per imported model:

- GLB file: 192 MiB max
- vertices: 3,000,000 max
- indices: 12,000,000 max
- triangles: 2,000,000 max
- texture edge: 4096 px max
- estimated mipmapped texture residency: 500 MiB max
- estimated total GPU model resources: 640 MiB max
- estimated CPU import working set: 384 MiB max

v1.5 additionally limits the combined archived + incoming model estimate to 768 MiB. A known 3.03M-triangle reference reproducibly caused severe XR/system lag, so the 2M triangle ceiling remains deliberate.

## Build

The reproducible GitHub Actions pipeline uses Meta OpenXR SDK v85, cgltf v1.15 and pinned stb. Feature code stays in modular scripts/patch fragments; the workflow remains thin.

v1.5.0 is a release candidate until restart behavior and multi-model operation are confirmed on Quest 3 hardware.
