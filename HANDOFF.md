# HANDOFF — Quest3 MR Model Viewer

## Current checkpoint

Repository re-audit on 2026-09-25 found the real code baseline at **v1.4.1**, not the stale v1.0.1 documentation. v1.4.1 is the last green CI checkpoint before the current **v1.5.0 candidate**.

## v1.4.1 capabilities

- Quest standalone native Android/OpenXR
- passthrough and filtered Environment Depth
- safe GLB picker/import flow
- PBR + multi-material rendering
- dual-controller UI/tablet/model grabbing
- physical SIZE controls
- skinning and live joint palette
- BONES visualization/manipulation
- two-bone IK
- first GLB animation playback
- preservation of character root scale during animation

## v1.5.0 work

### Restart regression

Symptom: after app restart the tablet could become ungrabbable.

Cause class: render-local static CPU interaction state survived Scene/EGL recreation even though GL resource state was reset.

Fix: scene-generation epoch. Scene::Create increments the generation; RenderFrame clears grab ownership, input-edge latches, selection and placement state on mismatch. Currently held controls are baselined for one frame to prevent phantom grabs.

### Multi-model scene

IMPORT GLB now archives the active model instead of deleting it, then loads the selected GLB as the new active model.

- max 6 models
- aggregate estimated scene GPU cap 768 MiB
- older models remain rendered and grabbable
- grabbing a model selects it for SIZE/SCALE/ROTATE/RESET
- newest model remains the live animation/IK target
- older rigged models freeze their current joint palette when archived

## Safety envelope

Per model: GLB 192 MiB, vertices 3M, indices 12M, triangles 2M, texture edge 4096, mipmapped textures 500 MiB estimate, per-model GPU estimate 640 MiB, CPU import estimate 384 MiB. Scene aggregate: 768 MiB / 6 models.

## Rules to preserve

- keep the v0.1.2 filtered Environment Depth baseline unless intentionally retuned
- cached GLB must never auto-load on cold start
- never preserve raw GL names across scene/EGL recreation
- never preserve CPU grab/press ownership across scene recreation
- do not raise the 2M triangle ceiling without a renderer performance strategy
- keep feature code in modular patch fragments, not workflow YAML

## v1.5 acceptance

Do not call v1.5 hardware accepted until Quest testing confirms restart grabbing and multi-model behavior.
