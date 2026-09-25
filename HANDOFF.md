# HANDOFF — Quest3 MR Model Viewer

## Current checkpoint

Latest known green baseline before current work: **v1.5.1**, commit `db70c49d`.

Current development target: **v1.6.0 candidate**.

## Stable baseline capabilities

- Quest standalone native Android/OpenXR
- passthrough and filtered Environment Depth
- safe GLB picker/import flow
- PBR + multi-material rendering
- dual-controller UI/tablet/model grabbing
- physical SIZE controls
- skinning and live joint palette
- BONES visualization/manipulation
- two-bone IK
- GLB animation playback
- root-scale preservation
- restart-safe CPU interaction epoch
- six-model scene
- selected-model transforms
- safe deferred REMOVE MODEL

## v1.6.0 work

### Animation UI

The old PLAY label becomes PLAY/PAUSE. A progress track below it visualizes `gQuestMrAnimTime / gQuestMrAnimDuration`.

Holding Trigger on the track scrubs the clip. Scrubbing pauses playback, writes the new animation time, samples the pose immediately and rebuilds the joint palette.

Animation remains limited to the newest/live rig. Archived rigs stay frozen snapshots.

### Scene model selector

The tablet gains six SCENE MODELS rows.

- row count matches the hard scene limit
- archived models fill rows first
- newest/live model is the last loaded row
- selected row is highlighted
- live row has an additional marker
- clicking a row changes selection for transforms and REMOVE MODEL

No new deletion path was added; v1.6 reuses the deferred v1.5.1 removal mechanism.

### GLB-only picker

The Android Storage Access Framework request is now `model/gltf-binary` only. Generic `*/*`, glTF JSON and octet-stream fallback filters were removed. The returned URI is also checked for a `.glb` display name, with GLB MIME as fallback.

Provider behavior can still vary, but compliant document providers should stop showing unrelated disabled formats.

## Safety envelope

Per model: GLB 192 MiB, vertices 3M, indices 12M, triangles 2M, texture edge 4096, mipmapped textures 500 MiB estimate, per-model GPU estimate 640 MiB, CPU import estimate 384 MiB.

Scene aggregate: 768 MiB / 6 models.

## Rules to preserve

- keep the v0.1.2 filtered Environment Depth baseline unless intentionally retuned
- cached GLB must never auto-load on cold start
- never preserve raw GL names across scene/EGL recreation
- never preserve CPU grab/press ownership across scene recreation
- newest model alone owns mutable animation/IK state
- keep selected-model deletion deferred to a safe frame boundary
- do not raise the 2M triangle ceiling without a renderer performance strategy
- keep feature code in modular patch fragments, not workflow YAML

## v1.6 acceptance

Do not call v1.6 hardware accepted until Quest testing confirms scrub interaction, scene-row selection and GLB-only picker behavior in addition to the existing v1.5 restart/multi-model checks.
