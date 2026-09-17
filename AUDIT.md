# AUDIT

## 2026-09-16 — Bootstrap / v0.1

### Decisions

- Use native OpenXR reference sample rather than requiring Unity locally.
- Pin Meta OpenXR SDK to `v85` for reproducibility.
- Use `XrPassthroughOcclusion` as the Environment Depth foundation.
- Target ARM64 standalone Quest.
- Build and debug-sign through GitHub Actions.

### Hardening

- Keep Meta's Java package namespace intact.
- Brand through applicationId, label and version only.
- Verify APK signature and metadata in CI.
- Publish SHA-256 checksums.

## 2026-09-17 — Hardware bring-up accepted

Quest 3 hardware confirmed:

- passthrough works,
- Environment Depth works,
- virtual geometry is correctly hidden by real objects,
- the filtered v0.1.2 occlusion pass is the preferred visual baseline.

Decision: preserve the v0.1.2 filtered Environment Depth path through later viewer revisions.

## 2026-09-17 — Viewer / GLB / PBR phase

Implemented and iterated:

- runtime binary GLB loading with cgltf,
- Android document picker,
- transactional model replacement,
- model bounds/fit transform,
- BaseColor, Normal and Metallic/Roughness texture path,
- BaseColor sRGB correction,
- UV correction,
- lighting controls,
- labelled floating tablet UI,
- trigger-gated buttons/sliders.

Hardware testing exposed and fixed:

- wrong/patchwork PBR texture appearance,
- accidental hover activation,
- picker returning behind the immersive app,
- stale cached GLB being treated as a fresh import on startup.

## 2026-09-17 — Safe boot / import regression

Severe regression observed: launching after a prior heavy import could progressively stall tracking, controller input and Meta system UI until a hard reset was required.

Root cause class: persisted `questmr_import.glb` was eligible for native polling on process start.

Permanent rule:

- a cached GLB is ignored on cold start,
- import eligibility begins only after a fresh picker transaction,
- starting a picker transaction clears the stale app-private source file,
- the currently displayed GPU model is not affected by clearing that source.

This behavior must not be removed in future releases.

## 2026-09-17 — Import budgets corrected by hardware evidence

Two separate constraints were identified:

1. Older low-detail references use 2K BaseColor + 2K Normal + 4K Metallic/Roughness. Their mipmapped texture residency is about 128 MiB, so the old 96 MiB texture budget was too low.
2. A 3.03M-triangle reference with three 2K textures passes memory preflight but reproducibly causes severe sustained XR/system lag once rendered.

Final v1.0 safety envelope:

- file: 192 MiB
- vertices: 3,000,000
- indices: 12,000,000
- triangles: 2,000,000
- texture edge: 4096 px
- mipmapped texture estimate: 160 MiB
- total GPU estimate: 256 MiB
- CPU import estimate: 384 MiB

Decision: do not raise the 2M triangle limit without LOD, simplification, chunking or another renderer-side performance strategy.

## 2026-09-17 — Interaction finalization

Hardware confirmed:

- tablet follows full controller orientation,
- left and right controllers can independently operate the UI,
- controller squeeze/grip is exposed per hand,
- tablet can be directly grabbed with preserved hand-to-tablet offset,
- model can be directly grabbed with preserved hand-to-model offset,
- the non-grabbing hand remains available for UI interaction.

The old click-to-toggle MODEL MOVE interaction was retired in favor of direct physical manipulation.

## 2026-09-17 — v1.0 final feature pass

Added final planned v1 features:

- `REAL SCALE`: bypass automatic fit and render glTF linear units at physical metre scale,
- moving the manual SCALE slider exits real-scale mode,
- real-scale-aware model grab radius,
- visible import state text: IDLE / WAIT / READY / ERROR.

Documentation was rewritten to match the actual final architecture:

- `README.md`
- `PROJECT_STATE.md`
- `BUILD_STATE.md`
- `HANDOFF.md`
- `scripts/CONTROLS.txt`

Release policy: after CI succeeds, perform one final Quest 3 acceptance test of REAL SCALE and import status. If that passes, v1.0.0 is accepted and further features move to v1.1.
