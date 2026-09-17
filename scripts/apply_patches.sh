#!/usr/bin/env bash
set -euo pipefail
cp cgltf-src/cgltf.h meta-openxr-sdk/Samples/XrSamples/XrPassthroughOcclusion/Src/cgltf.h

python3 scripts/patch_depth.py
python3 scripts/patch_lighting.py
python3 scripts/patch_android_picker.py
python3 scripts/patch_glb_loader.py
python3 scripts/patch_glb_safety.py
python3 scripts/patch_tablet_ui.py

echo '--- Modular patch verification ---'
SRC='meta-openxr-sdk/Samples/XrSamples/XrPassthroughOcclusion/Src/XrPassthroughOcclusionGl.cpp'
grep -n 'v0.1.2 filtered Environment Depth pass' "$SRC"
grep -n 'QuestMrGetAndroidApp' meta-openxr-sdk/Samples/XrSamples/XrPassthroughOcclusion/Src/XrPassthroughOcclusion.cpp
grep -n 'Quest3 MR Model Viewer v0.3.5: labelled room-spawned sticky tablet' "$SRC"
grep -n 'MODEL VIEWER' "$SRC"
grep -n 'IMPORT GLB' "$SRC"
