# Build architecture state

Current app baseline: **v0.3.5**

The GitHub Actions workflow is intentionally thin. Build logic lives in `scripts/`:

- `patch_depth.py` - filtered Environment Depth + MSAA quality pass
- `patch_lighting.py` - lighting uniforms and controls
- `patch_android_picker.py` - Android document picker / native app bridge
- `parts/patch_glb_loader.*.pyfrag` - cgltf GLB loader and sticky viewer foundations
- `parts/patch_glb_safety.*.pyfrag` - crash-safe transactional model import
- `parts/patch_tablet_ui.*.pyfrag` - labelled room-spawned tablet UI
- `apply_patches.sh` - validates, reconstructs and applies patches in dependency order
- `brand_android.sh` - package/version/label branding
- `verify_apk.sh` - artifact collection and APK verification

The larger patch sources are split into small ordered fragments because the GitHub connector handles smaller text mutations much more reliably. `apply_patches.sh` concatenates them byte-for-byte before Python compilation/execution.

Rule: keep feature changes in the smallest relevant patch or fragment file. Do not embed Python/C++ patch payloads back into the workflow YAML.
