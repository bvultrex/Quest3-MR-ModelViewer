# Build architecture state

Current app baseline: **v0.3.8**

The GitHub Actions workflow is intentionally thin. Build logic lives in `scripts/`:

- `patch_depth.py` - filtered Environment Depth + MSAA quality pass
- `patch_lighting.py` - lighting uniforms and controls
- `patch_android_picker.py` - Android document picker / native app bridge
- `parts/patch_glb_loader.*.pyfrag` - cgltf GLB loader and sticky viewer foundations
- `parts/patch_glb_safety.*.pyfrag` - crash-safe transactional model import
- `parts/patch_tablet_ui.*.pyfrag` - labelled room-spawned tablet UI
- `parts/patch_pbr.*.pyfrag` - authored normals, UVs, BaseColor, Normal and Metallic/Roughness material path
- `parts/patch_v037.*.pyfrag` - UV/sRGB correction plus model move/scale/rotate controls
- `parts/patch_v038.*.pyfrag` - trigger-gated UI, automatic return from Android picker, higher-detail import budget
- `apply_patches.sh` - validates, reconstructs and applies patches in dependency order
- `brand_android.sh` - package/version/label branding
- `verify_apk.sh` - artifact collection, APK verification and patched-source snapshot

Pinned third-party build dependencies:

- Meta OpenXR SDK v85
- cgltf v1.15
- stb commit `2c980bb59875b0d32144a71867fbdebb2f77cd20`

v0.3.8 interaction rule: controller proximity is hover only. Buttons require a trigger press; sliders require trigger hold + drag.

v0.3.8 import guard: 192 MiB, 3,000,000 vertices and 12,000,000 indices. These are safety limits, not performance targets.

The larger patch sources are split into small ordered fragments because the GitHub connector handles smaller text mutations more reliably. `apply_patches.sh` concatenates them before Python compilation/execution.

Rule: keep feature changes in the smallest relevant patch or fragment file. Do not embed Python/C++ patch payloads back into the workflow YAML.
