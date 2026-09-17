#!/usr/bin/env bash
set -euo pipefail
SRC_DIR='meta-openxr-sdk/Samples/XrSamples/XrPassthroughOcclusion/Src'
cp cgltf-src/cgltf.h "$SRC_DIR/cgltf.h"
cp stb-src/stb_image.h "$SRC_DIR/stb_image.h"

python3 -m py_compile \
  scripts/patch_depth.py \
  scripts/patch_lighting.py \
  scripts/patch_android_picker.py

python3 scripts/patch_depth.py
python3 scripts/patch_lighting.py
python3 scripts/patch_android_picker.py

run_fragmented_patch() {
  local name="$1"
  local tmp="/tmp/${name}.py"
  cat scripts/parts/${name}.*.pyfrag > "$tmp"
  python3 -m py_compile "$tmp"
  python3 "$tmp"
}

run_fragmented_patch patch_glb_loader
run_fragmented_patch patch_glb_safety
run_fragmented_patch patch_tablet_ui
run_fragmented_patch patch_pbr

echo '--- Modular patch verification ---'
SRC="$SRC_DIR/XrPassthroughOcclusionGl.cpp"
grep -n 'v0.1.2 filtered Environment Depth pass' "$SRC"
grep -n 'QuestMrGetAndroidApp' meta-openxr-sdk/Samples/XrSamples/XrPassthroughOcclusion/Src/XrPassthroughOcclusion.cpp
grep -n 'Quest3 MR Model Viewer v0.3.5: labelled room-spawned sticky tablet' "$SRC"
grep -n 'MODEL VIEWER' "$SRC"
grep -n 'IMPORT GLB' "$SRC"
grep -n 'HAS_BASE_COLOR_TEXTURE' "$SRC"
grep -n 'Texture1' "$SRC"
grep -n 'Texture2' "$SRC"
grep -n 'Texture3' "$SRC"
