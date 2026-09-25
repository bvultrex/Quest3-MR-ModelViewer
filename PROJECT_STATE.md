# PROJECT STATE

**Project:** Quest3 MR Model Viewer  
**Target:** Meta Quest 3 / Quest 3S standalone  
**Current milestone:** v1.6.0 candidate  
**Date:** 2026-09-25

## Source of truth

Latest green checkpoint before v1.6 work: **v1.5.1**, commit `db70c49dd7b1c392432dfd85fd3100e2ab8e080a`.

v1.5.1 contains restart-safe interaction state, the six-model scene, selected-model transforms and safe REMOVE MODEL deletion.

## Current capability

- passthrough + filtered Meta Environment Depth occlusion
- runtime GLB import with safe cold start
- PBR and multi-material rendering
- dual-controller tablet/model manipulation
- physical SIZE presets
- skinning and live joint palette
- BONES visualization and controller joint manipulation
- two-bone IK for supported limb endpoints
- GLB animation playback
- root-scale preservation for centimeter-authored animation rigs
- up to six simultaneous scene models
- selected-model removal

## v1.6.0 candidate

### Animation transport

- PLAY/PAUSE label and toggle
- live progress track
- Trigger-drag scrubbing
- scrubbing pauses playback and immediately resamples the live rig pose
- animation remains intentionally restricted to the newest/live model

### Scene model window

The tablet contains six compact SCENE MODELS rows matching the scene limit.

- loaded rows are visually active
- selected row is highlighted
- newest/live row gets an extra marker
- clicking a loaded row selects that model
- transform and REMOVE MODEL controls then target that selection

### GLB-only picker

The Storage Access Framework request now uses `model/gltf-binary` instead of `*/*` and generic fallback MIME types. A second validation rejects selections that are neither named `.glb` nor reported as `model/gltf-binary`.

## Current guards

Per model: 192 MiB GLB, 3M vertices, 12M indices, 2M triangles, 4096 texture edge, 500 MiB estimated mipmapped texture residency, 640 MiB estimated GPU resources, 384 MiB CPU import estimate.

Scene: maximum 6 models and 768 MiB aggregate estimated GPU resources.

## Acceptance status

v1.6.0 requires Quest hardware acceptance:

1. verify PLAY/PAUSE toggles the live animation,
2. scrub from start to end and confirm immediate pose updates,
3. confirm scrubbing pauses playback,
4. load several models and select each from SCENE MODELS,
5. verify SIZE/SCALE/ROTATE/RESET/REMOVE target the selected row,
6. confirm the newest rig remains the only live animation/IK target,
7. open IMPORT GLB and confirm unrelated formats are no longer presented by the Quest document provider,
8. restart and re-check tablet grabbing and safe cold start.
