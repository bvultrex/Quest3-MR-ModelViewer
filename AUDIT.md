# AUDIT

## 2026-09-16 to 2026-09-18 — Foundation and accepted v1.0 line

- Native Android/C++ OpenXR chosen on Meta OpenXR SDK v85.
- Quest 3 hardware confirmed passthrough and `XR_META_environment_depth`; filtered v0.1.2 occlusion became the visual baseline.
- Runtime GLB import, PBR, lighting, labelled tablet, dual-controller input and direct tablet/model grab were built and hardware-tested.
- Safe-boot rule established after a persisted heavy GLB could starve XR at startup: a cached source is ignored until a fresh picker transaction.
- v1.0.0 was rejected after raw metre scaling and GL lifecycle regressions.
- v1.0.1 replaced raw scale with explicit SIZE presets and hardened UI/model GL lifecycle. Final hardware acceptance passed.

## 2026-09-18 to 2026-09-23 — Viewer expansion

The repository advanced beyond the stale v1.0 documentation.

- App icon / Android label polish.
- Texture guard raised to 500 MiB, with 640 MiB per-model estimated GPU guard.
- Multi-material GLB rendering and texture reuse.
- True controller-ray tablet interaction and further Environment Depth preservation work.
- GPU skinning / joint palette.
- Live rig visualization with BONES and joint rings.
- Direct joint posing.
- Two-bone IK for supported limb endpoints.
- GLB animation playback.
- v1.4.1 preserved external/root scale while animation clips authored in centimeters play.

Latest green pre-v1.5 checkpoint: **v1.4.1**, commit `6ac8b0c94850e65afa88a290a606bd5242946446`.

## 2026-09-25 — Repository re-audit

User reported that after restarting the app the tablet could no longer be grabbed and requested multiple models in one scene.

Audit found that GL resources were lifecycle-reset, but the interaction path still used render-local static CPU state such as tablet/model grab ownership and previous Grip/Trigger latches. Those values could survive Scene/EGL recreation and leave the tablet in a stale held/edge state.

The existing PROJECT_STATE / BUILD_STATE / README / HANDOFF files were also stale at v1.0.1 despite code reaching v1.4.1. They were rewritten to reflect the actual repository.

## 2026-09-25 — v1.5.0 candidate

### Restart-state correction

Added a scene-generation epoch:

- `Scene::Create` increments `gQuestMrSceneGeneration`.
- RenderFrame detects a generation change.
- tablet/model grab ownership is cleared,
- previous Grip/Trigger states and UI press latches are reset,
- selection and placement state are reset,
- the first frame baselines inputs already held during restart so no phantom press/grab is synthesized.

Policy: scene recreation must reset both GPU resources and CPU interaction ownership.

### Multi-model scene

Added `QuestMrSceneObject` storage.

- IMPORT GLB archives the current active model before opening the next picker transaction.
- Older models remain visible and directly grabbable.
- Grabbing an older model selects it.
- SIZE / SCALE / ROTATE / RESET target the selected object.
- Scene limit: 6 models.
- Aggregate estimated scene GPU limit: 768 MiB.
- Newest model remains the live skin/IK/animation target.
- Older rigged models archive a frozen copy of their current joint palette.

Per-model guards remain: 192 MiB file, 3M vertices, 12M indices, 2M triangles, 4096px texture edge, 500 MiB mipmapped texture estimate, 640 MiB estimated GPU, 384 MiB CPU import estimate.

The known ~3.03M-triangle reference remains outside the 2M safety ceiling because it reproducibly caused severe sustained XR/system lag.

**v1.5.0 is a candidate until CI and Quest hardware acceptance pass.**


## 2026-09-25 — v1.5.1 selected-model removal

Added a dedicated REMOVE MODEL row. Deletion is queued and processed at the beginning of the next frame so vector elements and selected-object references are never invalidated in the middle of the UI pass.

Latest green v1.5 checkpoint: **v1.5.1**, commit `db70c49dd7b1c392432dfd85fd3100e2ab8e080a`.

## 2026-09-25 — v1.6.0 UI candidate

Requested UI/import changes:

- PLAY renamed to PLAY/PAUSE while preserving toggle behavior.
- Added live animation progress track.
- Trigger-hold dragging on the track scrubs clip time, pauses playback and resamples the live rig immediately.
- Added compact six-row SCENE MODELS selector matching the existing scene limit.
- Loaded/selected/live rows receive distinct visual state.
- Row click selects a model for existing transform and REMOVE MODEL controls.
- Expanded tablet and controller-ray hit range vertically for the new controls.
- Android Storage Access Framework request tightened from `*/*` plus fallbacks to `model/gltf-binary` only.
- Returned document receives a second .glb / MIME validation before bytes are copied into the app-private import transaction.

v1.6.0 remains a candidate until CI and Quest hardware acceptance pass.
