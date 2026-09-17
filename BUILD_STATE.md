# Build architecture state

Current app baseline: **v1.0.0 final candidate**

The GitHub Actions workflow is intentionally thin. Build logic lives in `scripts/`:

- `patch_depth.py` - filtered Environment Depth + MSAA quality pass
- `patch_lighting.py` - lighting uniforms and controls
- `patch_android_picker.py` - Android document picker / native app bridge
- `parts/patch_glb_loader.*.pyfrag` - cgltf GLB loader and viewer foundations
- `parts/patch_glb_safety.*.pyfrag` - transactional import and baseline safety validation
- `parts/patch_tablet_ui.*.pyfrag` - labelled room-spawned tablet UI
- `parts/patch_pbr.*.pyfrag` - normals, UVs, BaseColor, Normal and Metallic/Roughness path
- `parts/patch_v037.*.pyfrag` - UV/sRGB correction plus model scale/rotate controls
- `parts/patch_v038.*.pyfrag` - trigger-gated UI, picker return and expanded import envelope
- `parts/patch_v039.*.pyfrag` - GLB preflight and CPU/GPU memory estimates
- `parts/patch_v040.*.pyfrag` - safe boot; persisted GLB never auto-loads
- `parts/patch_v041.*.pyfrag` - fresh picker transaction; stale source cleared before selection
- `parts/patch_v042.*.pyfrag` - hardware-corrected texture and triangle budgets
- `parts/patch_v043.*.pyfrag` - full controller orientation for tablet placement
- `parts/patch_v044.*.pyfrag` - independent left/right trigger and squeeze input + direct tablet grab
- `parts/patch_v045.*.pyfrag` - direct left/right one-hand model grab
- `parts/patch_v046.*.pyfrag` - v1.0 REAL SCALE + import state text
- `apply_patches.sh` - validates, reconstructs and applies patches in dependency order
- `brand_android.sh` - package/version/label branding
- `verify_apk.sh` - artifact collection, APK verification and patched-source snapshot

Pinned third-party dependencies:

- Meta OpenXR SDK v85
- cgltf v1.15
- stb commit `2c980bb59875b0d32144a71867fbdebb2f77cd20`

## Interaction model

- Either controller can point at the UI.
- Trigger click activates buttons; trigger hold + drag operates sliders.
- Either controller can Grip/Squeeze the tablet directly with no snap.
- Either controller can Grip/Squeeze the imported model directly with no snap.
- The opposite hand remains usable while one hand is grabbing an object.

## Import behavior

- A persisted `questmr_import.glb` is ignored on cold start and never auto-loaded.
- Starting a picker transaction clears only the stale app-private source file.
- A successful picker selection creates the only source eligible for the next import.
- UI import states are IDLE / WAIT / READY / ERROR.

## v1.0 scaling behavior

- Default import view fits the model to roughly 34 cm maximum extent, then applies the SCALE slider multiplier.
- `REAL SCALE` bypasses the fit transform and uses scale 1.0, matching glTF metre units to physical metres.
- Moving SCALE exits REAL SCALE automatically.
- Direct-grab hit radius accounts for actual model extent while REAL SCALE is enabled.

## Hardware findings

- Environment Depth, GLB picker, PBR rendering, dual-controller UI, direct tablet grab and direct model grab are confirmed on Quest 3.
- Lower-detail reference models including the ~100k-triangle class run smoothly.
- Older low-detail references with 2K BaseColor + 2K Normal + 4K Metallic/Roughness require about 128 MiB mipmapped texture residency and therefore need the current 160 MiB texture guard.
- A 3.03M-triangle / three-2K-texture reference passes memory preflight but reproducibly causes severe XR/system lag in the current renderer.

## v1.0 safety envelope

- 192 MiB maximum GLB file size
- 3,000,000 vertices
- 12,000,000 indices
- **2,000,000 triangles**
- 4096x4096 maximum individual texture edge
- **160 MiB** estimated mipmapped texture residency
- 256 MiB estimated total GPU model resources
- 384 MiB estimated CPU import working set

Do not raise the triangle ceiling merely because a file passes memory preflight. Future >2M support should use LOD, simplification or a renderer-side strategy.

The larger patch sources are split into small ordered fragments because the GitHub connector handles smaller text mutations more reliably. Keep future feature changes in the smallest relevant patch or fragment. Do not move Python/C++ payloads back into workflow YAML.
