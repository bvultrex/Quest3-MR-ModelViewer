# AUDIT

## 2026-09-16 — Bootstrap / v0.1

- Chose native OpenXR reference sample instead of requiring Unity locally.
- Pinned Meta OpenXR SDK v85.
- ARM64 standalone Quest target with GitHub Actions build/debug signing.
- Preserve Meta Java namespace; brand via applicationId/label/version.

## 2026-09-17 — Hardware bring-up accepted

Quest 3 confirmed passthrough, Environment Depth and correct real-world occlusion. The filtered v0.1.2 occlusion pass became the visual baseline and must be preserved unless intentionally retuned.

## 2026-09-17 — Viewer / GLB / PBR phase

Implemented runtime GLB loading, Android picker, transactional replacement, model bounds/fit, BaseColor/Normal/Metallic-Roughness PBR, sRGB/UV fixes, lighting controls, labelled tablet and trigger-gated controls.

Hardware testing exposed and fixed texture mapping, hover activation, picker foreground/return and stale cached GLB startup behavior.

## 2026-09-17 — Safe boot regression

A persisted GLB could be treated as fresh input at process startup, causing a heavy import to progressively stall tracking, controllers and system UI.

Permanent rule: cached GLB is ignored on cold start; only a fresh picker transaction makes a source eligible for import.

## 2026-09-17 — Import budgets from hardware evidence

Older low-detail references require about 128 MiB mipmapped texture residency, so texture budget was raised to 160 MiB. A 3.03M-triangle / three-2K-map model passes memory preflight but reproducibly causes severe sustained XR/system lag.

Final safety envelope: 192 MiB file, 3M vertices, 12M indices, 2M triangles, 4096px texture edge, 160 MiB textures, 256 MiB GPU estimate, 384 MiB CPU import estimate.

## 2026-09-17 — Interaction finalization

Hardware confirmed full-orientation tablet placement, independent left/right trigger input, per-hand squeeze/grip, direct no-snap tablet grip and direct no-snap model grip. Old MODEL MOVE toggle retired.

## 2026-09-17 — v1.0.0 candidate rejected on hardware

The first v1.0.0 candidate added raw `REAL SCALE` (`1 glTF unit = 1 metre`) and import status text. Quest testing immediately found:

1. raw metre scale was far too large for the user's imported Meshy/miniature assets because source coordinates did not encode intended print/display units,
2. UI labels disappeared after restarting the app,
3. a strange white rendering artifact appeared while loading a file.

Decision: v1.0.0 is **not accepted**.

## 2026-09-17 — v1.0.1 regression fix

Scaling correction:

- removed raw metre-scale interaction,
- added explicit largest-dimension presets: FIT / 32MM / 75MM / 150MM / 300MM,
- manual SCALE returns to FIT.

GL lifecycle diagnosis:

The static text mesh wrappers could retain `built=true` and numeric VAO/VBO/IBO names across a scene/EGL restart even though the underlying GL resources were no longer valid. Later allocations could reuse those same numeric names. This explains missing labels and is a plausible cause of the white artifact when stale UI state referenced unrelated newly allocated geometry.

Hardening implemented:

- invalidate all static UI mesh wrappers on `Scene::Create`,
- clear imported-model GL handles on `Scene::Create` while retaining only the safe file stamp,
- release UI text GL resources on `Scene::Destroy`,
- explicitly destroy imported-model GL resources on `Scene::Destroy`.

Policy: never carry raw OpenGL object names across an EGL/scene lifecycle boundary.

v1.0.1 remains a release candidate until the restart, import-artifact and physical SIZE behaviors pass a final Quest 3 hardware test.
