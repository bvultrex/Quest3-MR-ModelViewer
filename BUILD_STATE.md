# Build architecture state

Current app baseline: **v0.3.5**

The GitHub Actions workflow is intentionally thin. Build logic lives in `scripts/`:

- `patch_depth.py` - filtered Environment Depth + MSAA quality pass
- `patch_lighting.py` - lighting uniforms and controls
- `patch_android_picker.py` - Android document picker / native app bridge
- `patch_glb_loader.py` - cgltf GLB loader and sticky viewer foundations
- `patch_glb_safety.py` - crash-safe transactional model import
- `patch_tablet_ui.py` - labelled room-spawned tablet UI
- `apply_patches.sh` - applies patches in dependency order
- `brand_android.sh` - package/version/label branding
- `verify_apk.sh` - artifact collection and APK verification

Rule: keep feature changes in the smallest relevant patch file. Do not embed Python or C++ patch payloads back into the workflow YAML.
