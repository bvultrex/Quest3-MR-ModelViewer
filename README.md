# Quest3 MR Model Viewer

Standalone mixed-reality GLB viewer for Meta Quest 3 / Quest 3S.

## v1.6.0 candidate

v1.6.0 builds on the green v1.5.1 multi-model line and focuses on tablet UI quality and import filtering.

### Current features

- color passthrough + `XR_META_environment_depth` real-world occlusion
- filtered v0.1.2 Environment Depth edge treatment
- Android Storage Access Framework GLB picker with safe cold start
- strict GLB-only picker request plus post-selection .glb/MIME validation
- BaseColor / Normal / Metallic-Roughness PBR, multi-material GLBs and texture reuse
- direct left/right controller UI interaction
- direct no-snap tablet and model grabbing
- FIT and physical SIZE presets: 32 / 75 / 150 / 300 mm
- rigged GLB skinning, BONES display, joint manipulation and two-bone IK
- PLAY/PAUSE control for the first supported GLB animation clip
- live animation progress track with trigger-drag scrubbing
- up to 6 models in one scene
- compact six-slot SCENE MODELS selector
- selected-model REMOVE MODEL
- visible import state: IDLE / WAIT / READY / ERROR

## v1.6.0 UI changes

The tablet now exposes a compact animation transport and scene selector.

- PLAY/PAUSE replaces the old PLAY-only label.
- The animation track shows current clip progress.
- Hold Trigger on the animation track and drag to scrub.
- Scrubbing pauses playback and samples the chosen time immediately.
- Animation controls remain bound to the newest/live rig. Archived rigs stay frozen snapshots.
- SCENE MODELS shows six slots matching the scene limit.
- Loaded slots are lit; the selected slot is highlighted.
- The newest/live model receives an additional marker.
- Trigger-clicking a loaded row selects that model for SIZE / SCALE / ROTATE / RESET / REMOVE MODEL.

The tablet was extended vertically to fit the new controls without shrinking the existing sliders.

## GLB-only document picker

The Android picker now requests only `model/gltf-binary` instead of `*/*` plus generic fallback MIME types. The selected document is also validated as a `.glb` by display name, with `model/gltf-binary` as a fallback when a provider does not expose a name.

Android document providers ultimately decide how MIME filtering is presented, but providers honoring the registered GLB MIME type should no longer show unrelated formats as disabled rows.

## Multi-model scene

- maximum scene count: 6 models
- aggregate estimated scene GPU budget: 768 MiB
- grab a model or select it from SCENE MODELS
- SIZE / SCALE / ROTATE / RESET / REMOVE MODEL target the selected model
- newest model remains the live rig / IK / animation target
- older rigged models keep a frozen snapshot of their current skin palette

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

The scene aggregate remains limited to 768 MiB. A known ~3.03M-triangle reference caused severe sustained XR/system lag, so the 2M triangle ceiling remains deliberate.

## Build

The reproducible GitHub Actions pipeline uses Meta OpenXR SDK v85, cgltf v1.15 and pinned stb. Feature code stays in modular patch fragments; the workflow remains thin.

v1.6.0 is a release candidate until the new tablet UI, scrub interaction, model list and GLB-only picker are confirmed on Quest 3 hardware.
