# Build architecture state

Current candidate: **v1.5.0**. Latest green checkpoint before this candidate: **v1.4.1**.

## Patch stack

The pipeline starts from Meta OpenXR SDK v85 and applies the modular patch series through `patch_v062`.

Important recent phases:

- v1.0.x: safe import, physical SIZE, GL lifecycle hardening and app polish
- v1.0.3: 500 MiB texture guard and 640 MiB per-model estimated GPU guard
- v1.1.x: multi-material/PBR expansion, controller ray and texture reuse
- v1.2.x: skin palette and GPU skinning
- v1.3.x: live joints, BONES UI and joint rings/manipulation
- v1.4.0: two-bone IK + GLB animation player
- v1.4.1: preserve external/root scale during animation sampling
- v1.5.0 / patch_v062: restart interaction epoch + multi-model scene

Pinned dependencies remain Meta OpenXR SDK v85, cgltf v1.15 and stb `2c980bb59875b0d32144a71867fbdebb2f77cd20`.

## Restart state rule

OpenGL lifecycle cleanup is not sufficient for interaction state. The tablet/model grab code keeps render-local static CPU variables. v1.5 introduces `gQuestMrSceneGeneration`, incremented at Scene::Create. RenderFrame detects a generation change and resets all grab owners, previous trigger/grip states, selection and placement/UI latches. The first new frame baselines currently held inputs before computing press edges.

Never carry either GL object names **or CPU grab/press ownership** across a scene lifecycle boundary.

## Multi-model architecture

The newest imported GLB remains in `gQuestMrImportedMesh` and is the live rig/animation target. Before another picker transaction, the active model is moved into `gQuestMrSceneObjects`.

Each archived scene object owns:

- mesh GPU handles/materials/draw ranges
- room-space root/default transform
- SIZE/SCALE/ROTATE state
- frozen joint-palette snapshot
- estimated GPU cost

Archived models remain rendered and directly grabbable. Grabbing selects them for transform controls. The newest model alone retains mutable rig/IK/animation state, preventing multiple heavyweight animation systems from running concurrently on Quest.

Scene limits: 6 models, 768 MiB aggregate estimated GPU cost.

## Safety

Per model: 192 MiB file, 3M vertices, 12M indices, 2M triangles, 4096px edge, 500 MiB mipmapped textures, 640 MiB estimated GPU, 384 MiB CPU import estimate.

The 2M triangle limit remains based on hardware evidence. A ~3.03M-triangle reference caused severe sustained XR/system lag.
