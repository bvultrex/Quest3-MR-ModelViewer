# Build architecture state

Current candidate: **v1.6.0**. Latest green checkpoint before this candidate: **v1.5.1** (`db70c49d`).

## Patch stack

The pipeline starts from Meta OpenXR SDK v85 and applies the modular patch series through `patch_v064`.

Important recent phases:

- v1.0.x: safe import, physical SIZE, GL lifecycle hardening and app polish
- v1.0.3: 500 MiB texture guard and 640 MiB per-model estimated GPU guard
- v1.1.x: multi-material/PBR expansion, controller ray and texture reuse
- v1.2.x: skin palette and GPU skinning
- v1.3.x: live joints, BONES UI and joint rings/manipulation
- v1.4.0: two-bone IK + GLB animation player
- v1.4.1: preserve external/root scale during animation sampling
- v1.5.0 / patch_v062: restart interaction epoch + multi-model scene
- v1.5.1 / patch_v063: deferred selected-model deletion
- v1.6.0 / patch_v064: PLAY/PAUSE UI, animation scrubber and six-slot scene model selector

Pinned dependencies remain Meta OpenXR SDK v85, cgltf v1.15 and stb `2c980bb59875b0d32144a71867fbdebb2f77cd20`.

## Animation UI architecture

The first supported animation clip remains represented by `gQuestMrAnimChannels`, `gQuestMrAnimDuration`, `gQuestMrAnimTime` and `gQuestMrAnimPlaying`.

The v1.6 scrubber maps controller-ray local X across the track to normalized clip time. While Trigger is held on the track:

- playback is paused,
- `gQuestMrAnimTime` is updated,
- `QuestMrSampleAnimation` runs immediately,
- the joint palette is rebuilt.

Archived rigs remain frozen and cannot be scrubbed or played.

## Scene selector architecture

The six SCENE MODELS slots directly mirror the maximum scene count. Archived objects occupy the first rows; the newest live model occupies the last loaded row. Selection only changes `selectedArchivedModel`; deletion remains deferred through the v1.5.1 pending-removal path.

## Picker rule

The generated Android helper Activity now requests `model/gltf-binary` only and validates the returned document by `.glb` display name or GLB MIME type. Safe cold-start behavior and stale-import clearing remain unchanged.

## Safety

Per model: 192 MiB file, 3M vertices, 12M indices, 2M triangles, 4096px edge, 500 MiB mipmapped textures, 640 MiB estimated GPU, 384 MiB CPU import estimate.

Scene limits: 6 models, 768 MiB aggregate estimated GPU cost.
