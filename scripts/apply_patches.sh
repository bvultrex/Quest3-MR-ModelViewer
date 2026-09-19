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
run_fragmented_patch patch_v037
run_fragmented_patch patch_v038
run_fragmented_patch patch_v039
run_fragmented_patch patch_v040
run_fragmented_patch patch_v041
run_fragmented_patch patch_v042
run_fragmented_patch patch_v043
run_fragmented_patch patch_v044
run_fragmented_patch patch_v045
run_fragmented_patch patch_v046
run_fragmented_patch patch_v047

cat BrowserPanel/parts/patch_browser_panel.*.pyfrag > /tmp/patch_browser_panel.py
python3 -m py_compile /tmp/patch_browser_panel.py
python3 /tmp/patch_browser_panel.py

cat BrowserPanel/v02/parts/patch_browser_panel_v02.*.pyfrag > /tmp/patch_browser_panel_v02.py
python3 -m py_compile /tmp/patch_browser_panel_v02.py
python3 /tmp/patch_browser_panel_v02.py

cat BrowserPanel/v021/parts/patch_browser_panel_v021.*.pyfrag > /tmp/patch_browser_panel_v021.py
python3 -m py_compile /tmp/patch_browser_panel_v021.py
python3 /tmp/patch_browser_panel_v021.py

cat BrowserPanel/v022/parts/patch_browser_panel_v022.*.pyfrag > /tmp/patch_browser_panel_v022.py
python3 -m py_compile /tmp/patch_browser_panel_v022.py
python3 /tmp/patch_browser_panel_v022.py

cat BrowserPanel/v023/parts/patch_browser_panel_v023.*.pyfrag > /tmp/patch_browser_panel_v023.py
python3 -m py_compile /tmp/patch_browser_panel_v023.py
python3 /tmp/patch_browser_panel_v023.py

cat BrowserPanel/v024/parts/patch_browser_panel_v024.*.pyfrag > /tmp/patch_browser_panel_v024.py
python3 -m py_compile /tmp/patch_browser_panel_v024.py
python3 /tmp/patch_browser_panel_v024.py

echo '--- Modular patch verification ---'
SRC="$SRC_DIR/XrPassthroughOcclusionGl.cpp"
INPUT="$SRC_DIR/XrPassthroughOcclusionInput.cpp"
MAIN="$SRC_DIR/XrPassthroughOcclusion.cpp"
BROWSER_JAVA='meta-openxr-sdk/Samples/XrSamples/XrPassthroughOcclusion/java/com/oculus/xrpassthroughocclusion/QuestBrowserPanelBridge.java'
grep -n 'v0.1.2 filtered Environment Depth pass' "$SRC"
grep -n 'QuestMrGetAndroidApp' "$MAIN"
grep -n 'MODEL VIEWER' "$SRC"
grep -n 'QuestMrTriggerDownForHand' "$INPUT"
grep -n 'QuestMrGripDownForHand' "$INPUT"
grep -n 'BrowserPanel v0.1 live WebView draw' "$SRC"
grep -n 'samplerExternalOES BrowserTexture' "$SRC"
grep -n 'BROWSER_MODE' "$SRC"
grep -n 'browserPointerHand' "$SRC"
grep -n 'QuestBrowserPanelInitialize' "$MAIN"
grep -n 'QuestBrowserPanelUpdate' "$MAIN"
grep -n 'QuestBrowserPanelDestroy' "$MAIN"
grep -n 'wikipedia.org' "$BROWSER_JAVA"
grep -n 'createVirtualDisplay' "$BROWSER_JAVA"
grep -n 'dispatchTouchEvent' "$BROWSER_JAVA"
grep -n 'android.permission.INTERNET' meta-openxr-sdk/Samples/XrSamples/XrPassthroughOcclusion/Projects/Android/AndroidManifest.xml

grep -n 'kMinWidthMeters' "$SRC"
grep -n 'browserResizeHoverHand' "$SRC"
grep -n 'resizeFixedCorner' "$SRC"
grep -n 'addressBar' "$BROWSER_JAVA"
grep -n 'InputMethodManager' "$BROWSER_JAVA"
grep -n 'toolbarButton' "$BROWSER_JAVA"

grep -n 'custom QWERTZ URL keyboard' /tmp/patch_browser_panel_v021.py
grep -n 'urlKeyboard' "$BROWSER_JAVA"
grep -n 'Quest-style hover affordance' "$SRC"

grep -n 'oculus.software.overlay_keyboard' meta-openxr-sdk/Samples/XrSamples/XrPassthroughOcclusion/Projects/Android/AndroidManifest.xml
grep -n 'TYPE_TEXT_VARIATION_URI' "$BROWSER_JAVA"
grep -n 'evaluateJavascript' "$BROWSER_JAVA"

grep -n 'primary-Activity hidden IME proxy' /tmp/patch_browser_panel_v023.py
grep -n 'installImeProxy' "$BROWSER_JAVA"
grep -n 'imeProxy' "$BROWSER_JAVA"
grep -n 'beginWebInput' "$BROWSER_JAVA"

grep -n 'thumbstickAction' "$INPUT"
grep -n 'QuestMrThumbstickForHand' "$INPUT"
grep -n 'bridgeScroll' "$SRC"
grep -n 'adaptive controller aim stabilization' /tmp/patch_browser_panel_v024.py
grep -n 'public static void scroll' "$BROWSER_JAVA"
