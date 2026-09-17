# Build architecture state

Current app baseline: **v0.3.12**

The GitHub Actions workflow is intentionally thin. Build logic lives in `scripts/`:

- `patch_depth.py` - filtered Environment Depth + MSAA quality pass
- `patch_lighting.py` - lighting uniforms and controls
- `patch_android_picker.py` - Android document picker / native app bridge
- `parts/patch_glb_loader.*.pyfrag` - cgltf GLB loader and sticky viewer foundations
- `parts/patch_glb_safety.*.pyfrag` - transactional import and baseline safety validation
- `parts/patch_tablet_ui.*.pyfrag` - labelled room-spawned tablet UI
- `parts/patch_pbr.*.pyfrag` - authored normals, UVs, BaseColor, Normal and Metallic/Roughness material path
- `parts/patch_v037.*.pyfrag` - UV/sRGB correction plus model move/scale/rotate controls
- `parts/patch_v038.*.pyfrag` - trigger-gated UI, picker return path and larger file/geometry envelope
- `parts/patch_v039.*.pyfrag` - GLB preflight and CPU/GPU memory estimates
- `parts/patch_v040.*.pyfrag` - emergency safe boot; persisted GLB never auto-loads on process start
- `parts/patch_v041.*.pyfrag` - fresh picker transaction; stale cached source cleared before selection
- `parts/patch_v042.*.pyfrag` - hardware-corrected texture and triangle budgets
- `apply_patches.sh` - validates, reconstructs and applies patches in dependency order
- `brand_android.sh` - package/version/label branding
- `verify_apk.sh` - artifact collection, APK verification and patched-source snapshot

Pinned third-party build dependencies:

- Meta OpenXR SDK v85
- cgltf v1.15
- stb commit `2c980bb59875b0d32144a71867fbdebb2f77cd20`

Interaction rule: controller proximity is hover only. Buttons require a trigger press; sliders require trigger hold + drag.

Import behavior after v0.3.10/v0.3.11 hardware tests:

- A persisted `questmr_import.glb` is ignored on cold start and is never auto-loaded.
- Starting a picker transaction clears only the stale app-private source file; an already uploaded GPU mesh is unaffected.
- A successful picker selection creates the only source file eligible for the next import.

Hardware findings from Quest 3:

- The document-picker handshake is operational: the 3.03M-triangle reference reliably reaches native import.
- The earlier low-detail references use 2K BaseColor + 2K Normal + 4K Metallic/Roughness. With mipmaps they require about 128 MiB of texture residency and were falsely rejected by the old 96 MiB texture-only guard.
- The 3.03M-triangle / three-2K-texture reference passes memory preflight but reproducibly causes severe sustained XR/system lag after loading in the current single-draw MR/PBR renderer. This is now treated as a rendering safety limit, not a picker/cache issue.

v0.3.12 safety envelope:

- 192 MiB maximum GLB file size
- 3,000,000 vertices
- 12,000,000 indices
- **2,000,000 triangles** for the current synchronous single-draw renderer
- 4096x4096 maximum individual texture edge
- **160 MiB** estimated mipmapped texture residency
- 256 MiB estimated total GPU model resources
- 384 MiB estimated CPU import working set

The 2M triangle limit is intentionally below the reproduced 3.03M Quest failure point. Future support for the 3M class should use LOD/mesh simplification, chunked rendering or another renderer-side strategy rather than simply raising this cap again.

The larger patch sources are split into small ordered fragments because the GitHub connector handles smaller text mutations more reliably. `apply_patches.sh` concatenates them before Python compilation/execution.

Rule: keep feature changes in the smallest relevant patch or fragment file. Do not embed Python/C++ patch payloads back into the workflow YAML.
