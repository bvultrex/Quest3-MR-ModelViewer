# PROJECT STATE

**Project:** Quest3 MR Model Viewer  
**Target:** Meta Quest 3 / Quest 3S standalone  
**Current milestone:** v1.5.0 candidate  
**Date:** 2026-09-25

## Source of truth

The repository was re-audited before v1.5 work. The latest green pre-v1.5 checkpoint is **v1.4.1**, commit `6ac8b0c94850e65afa88a290a606bd5242946446`. Older project documents had remained at v1.0.1 and were stale.

## Current capability

- passthrough + filtered Meta Environment Depth occlusion
- runtime GLB import with safe cold start
- PBR and multi-material rendering
- dual-controller tablet/model manipulation
- physical SIZE presets
- skinning and live joint palette
- BONES visualization and controller joint manipulation
- two-bone IK for supported limb endpoints
- playback of the first supported GLB animation clip
- v1.4.1 root-scale preservation for centimeter-authored animation rigs

## v1.5.0 candidate

v1.5 addresses two requested changes.

### Interaction reset after restart

A scene-generation epoch now invalidates render-local CPU interaction latches whenever Scene/Create recreates the XR/EGL scene. Tablet/model grab ownership, press-edge state and selection start cleanly. Held inputs are baselined on the first new frame so they cannot fabricate a grab press.

### Multiple models

IMPORT GLB archives the active model and loads the next model into the same scene.

- max 6 models
- 768 MiB aggregate estimated scene GPU budget
- any scene model can be grabbed and selected
- selected-model SIZE / SCALE / ROTATE / RESET
- newest model is the live animation/IK rig
- older rigs freeze their current skin-palette pose

## Current guards

Per model: 192 MiB GLB, 3M vertices, 12M indices, 2M triangles, 4096 texture edge, 500 MiB estimated mipmapped texture residency, 640 MiB estimated GPU resources, 384 MiB CPU import estimate.

Scene: maximum 6 models and 768 MiB aggregate estimated GPU resources.

## Acceptance status

v1.5.0 is **not hardware accepted yet**. Required Quest test:

1. restart app and confirm tablet can immediately be grabbed again,
2. restart while holding Grip and confirm no phantom grab,
3. import model A, place it, import B and confirm A remains,
4. grab A or B and verify controls target the selected model,
5. verify newest rig retains PLAY/BONES/IK and older rig snapshots remain visible,
6. confirm safe cold start remains intact.
