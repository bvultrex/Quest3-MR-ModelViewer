from pathlib import Path

ROOT = Path('meta-openxr-sdk/Samples/XrSamples/XrPassthroughOcclusion')
SRC = ROOT / 'Src'
JAVA = ROOT / 'java/com/oculus/xrpassthroughocclusion'
ANDROID = ROOT / 'Projects/Android'

def rep(text, old, new, label):
    if old not in text:
        raise SystemExit(f'v0.3.0 anchor missing: {label}')
    return text.replace(old, new, 1)

# Version reset marker.
gradle_path = ANDROID / 'build.gradle'
gradle = gradle_path.read_text()
gradle = rep(gradle, 'versionCode 27', 'versionCode 30', 'versionCode')
gradle = rep(gradle, 'versionName "0.2.7"', 'versionName "0.3.0"', 'versionName')
gradle_path.write_text(gradle)

manifest_path = ANDROID / 'AndroidManifest.xml'
manifest = manifest_path.read_text()
manifest = rep(manifest, 'android:versionCode="27"', 'android:versionCode="30"', 'manifest versionCode')
manifest = rep(manifest, 'android:versionName="0.2.7"', 'android:versionName="0.3.0"', 'manifest versionName')
manifest_path.write_text(manifest)

# ---------------------------------------------------------------------------
# INPUT: make left squeeze a real binding and keep hand ownership persistent.
# ---------------------------------------------------------------------------
input_path = SRC / 'XrPassthroughOcclusionInput.cpp'
inp = input_path.read_text()
inp = rep(
    inp,
    '''        bindings.push_back(
            ActionSuggestedBinding(app, browserGripAction, "/user/hand/right/input/squeeze/value"));
''',
    '''        bindings.push_back(
            ActionSuggestedBinding(app, browserGripAction, "/user/hand/left/input/squeeze/value"));
        bindings.push_back(
            ActionSuggestedBinding(app, browserGripAction, "/user/hand/right/input/squeeze/value"));
''',
    'left squeeze binding')
input_path.write_text(inp)

main_path = SRC / 'XrPassthroughOcclusion.cpp'
main = main_path.read_text()
old_hand = '''        const bool leftIntent =
            (leftTriggerState.currentState == XR_TRUE) || leftGripState.currentState > 0.15f;
        const bool rightIntent =
            (rightTriggerState.currentState == XR_TRUE) || rightGripState.currentState > 0.15f;
        const bool useLeftHand = leftIntent || (!rightIntent && !rightBrowserAimActive && leftBrowserAimActive);
        nativeBrowser.HandleInput(
            Env,
            useLeftHand ? leftBrowserAimPose : rightBrowserAimPose,
            useLeftHand ? leftBrowserAimActive : rightBrowserAimActive,
            useLeftHand ? (leftTriggerState.currentState == XR_TRUE)
                        : (rightTriggerState.currentState == XR_TRUE),
            useLeftHand ? leftGripState.currentState : rightGripState.currentState,
            useLeftHand ? 0.0f : rightThumbstickState.currentState.y);
'''
new_hand = '''        // v0.3.0: hand ownership persists instead of snapping back to right
        // whenever neither controller is currently squeezing. Either hand takes
        // ownership as soon as it clicks or grips, and remains the pointer hand
        // until the other controller expresses intent.
        static int browserActiveHand = 1; // 0 = left, 1 = right
        const bool leftIntent =
            (leftTriggerState.currentState == XR_TRUE) || leftGripState.currentState > 0.15f;
        const bool rightIntent =
            (rightTriggerState.currentState == XR_TRUE) || rightGripState.currentState > 0.15f;
        if (leftIntent && !rightIntent) browserActiveHand = 0;
        if (rightIntent && !leftIntent) browserActiveHand = 1;
        if (browserActiveHand == 0 && !leftBrowserAimActive && rightBrowserAimActive) {
            browserActiveHand = 1;
        } else if (browserActiveHand == 1 && !rightBrowserAimActive && leftBrowserAimActive) {
            browserActiveHand = 0;
        }
        const bool useLeftHand = browserActiveHand == 0;
        nativeBrowser.HandleInput(
            Env,
            useLeftHand ? leftBrowserAimPose : rightBrowserAimPose,
            useLeftHand ? leftBrowserAimActive : rightBrowserAimActive,
            useLeftHand ? (leftTriggerState.currentState == XR_TRUE)
                        : (rightTriggerState.currentState == XR_TRUE),
            useLeftHand ? leftGripState.currentState : rightGripState.currentState,
            useLeftHand ? 0.0f : rightThumbstickState.currentState.y);
'''
main = rep(main, old_hand, new_hand, 'persistent hand ownership')
main_path.write_text(main)

# ---------------------------------------------------------------------------
# ANDROID PRODUCER: exact producer-sized Presentation. Do not let decor/layout
# flags create a logical area larger than the SurfaceTexture capture.
# ---------------------------------------------------------------------------
bridge_path = JAVA / 'QuestDepthBrowserBridge.java'
bridge = bridge_path.read_text()

old_window = '''                Window window = presentation.getWindow();
                if (window != null) {
                    window.setBackgroundDrawable(new ColorDrawable(Color.TRANSPARENT));
                    window.clearFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND);
                    window.addFlags(WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS);
                    window.getDecorView().setSystemUiVisibility(
                            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY |
                            View.SYSTEM_UI_FLAG_FULLSCREEN |
                            View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
                            View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
                            View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION |
                            View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
                }

                presentation.show();
                if (window != null) {
                    window.setLayout(
                            ViewGroup.LayoutParams.MATCH_PARENT,
                            ViewGroup.LayoutParams.MATCH_PARENT);
                }
'''
new_window = '''                Window window = presentation.getWindow();
                if (window != null) {
                    window.setBackgroundDrawable(new ColorDrawable(Color.TRANSPARENT));
                    window.clearFlags(
                            WindowManager.LayoutParams.FLAG_DIM_BEHIND |
                            WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS);
                    window.getDecorView().setSystemUiVisibility(
                            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY |
                            View.SYSTEM_UI_FLAG_FULLSCREEN |
                            View.SYSTEM_UI_FLAG_HIDE_NAVIGATION);
                }

                presentation.show();
                if (window != null) {
                    // Physical producer pixels, not a decor-sized logical MATCH_PARENT.
                    window.setLayout(surfaceWidth, surfaceHeight);
                    window.getDecorView().setPadding(0, 0, 0, 0);
                }
                if (rootFrame != null) {
                    ViewGroup.LayoutParams rootParams = rootFrame.getLayoutParams();
                    if (rootParams != null) {
                        rootParams.width = surfaceWidth;
                        rootParams.height = surfaceHeight;
                        rootFrame.setLayoutParams(rootParams);
                    }
                }
'''
bridge = rep(bridge, old_window, new_window, 'exact producer window')

# Remove the emergency 84% inset. Keep the aspect-fit viewport but use all
# actual producer pixels now that the window is constrained correctly.
bridge = rep(
    bridge,
    '''            final float safeScale = 0.84f;
            int safeWidth = Math.max(1, Math.round(surfaceWidth * safeScale));
            int safeHeight = Math.max(1, Math.round(surfaceHeight * safeScale));
''',
    '''            final float safeScale = 1.0f;
            int safeWidth = surfaceWidth;
            int safeHeight = surfaceHeight;
''',
    'remove safe inset')
bridge_path.write_text(bridge)

# ---------------------------------------------------------------------------
# NATIVE BROWSER:
# 1. Do not inherit SurfaceTexture crop/translate. The producer dimensions are
#    now explicit. Apply only the Android->GL vertical flip ourselves.
# 2. Restore full centered content-rect math.
# 3. Use the same OpenGL NDC -> [0,1] depth remap as the proven GLB viewer.
# 4. Remove temporary diagnostic frame.
# ---------------------------------------------------------------------------
cpp_path = SRC / 'QuestDepthBrowserNative.cpp'
cpp = cpp_path.read_text()

cpp = rep(
    cpp,
    '''    vec2 sourceUv = uBrowserContentRect.xy + vUv * uBrowserContentRect.zw;
    vec4 transformedUv = uBrowserTextureTransform * vec4(sourceUv, 0.0, 1.0);
    vec4 browser = texture(uBrowserTexture, transformedUv.xy);

    // Native compositor-space frame. This does not come from Android/WebView,
    // so it shows the real OpenXR quad bounds even if the producer misbehaves.
    float edgeX = min(vUv.x, 1.0 - vUv.x);
    float edgeY = min(vUv.y, 1.0 - vUv.y);
    float edge = min(edgeX, edgeY);
    float frame = 1.0 - smoothstep(0.004, 0.010, edge);
    bool nearLeft = vUv.x < 0.045;
    bool nearRight = vUv.x > 0.955;
    bool nearBottom = vUv.y < 0.060;
    bool nearTop = vUv.y > 0.940;
    float corner = ((nearLeft || nearRight) && (nearBottom || nearTop)) ? 1.0 : 0.0;
    float accent = max(frame * 0.55, corner * 0.70);
    browser.rgb = mix(browser.rgb, vec3(0.80, 0.84, 0.90), accent);
    browser.a = max(browser.a, accent);
''',
    '''    vec2 sourceUv = uBrowserContentRect.xy + vUv * uBrowserContentRect.zw;
    // v0.3.0: producer geometry is explicit. SurfaceTexture's transform may
    // contain BufferQueue crop metadata from Presentation, which was causing
    // the persistent right-edge crop. Use the known full buffer and only flip Y.
    vec2 browserUv = vec2(sourceUv.x, 1.0 - sourceUv.y);
    vec4 browser = texture(uBrowserTexture, browserUv);
''',
    'raw producer UV')

cpp = rep(
    cpp,
    '''            float virtualDepth = depthCameraPosition.z / depthCameraPosition.w;
''',
    '''            float virtualDepth = depthCameraPosition.z / depthCameraPosition.w;
            // Exact Meta/GLB-viewer convention: OpenGL clip/NDC depth is [-1,+1],
            // Environment Depth texture values are [0,1].
            virtualDepth = virtualDepth * 0.5 + 0.5;
''',
    'depth range remap')

old_rect = '''    // v0.2.6: match Java's centered 84% capture-safe viewport. This avoids
    // the Presentation/BufferQueue edge region that hardware testing showed
    // was clipped on the right while keeping a ~2.7K browser source.
    const float panelAspect = PanelWidthMeters / std::max(PanelHeightMeters, 0.001f);
    const float backingAspect = static_cast<float>(TextureWidth) /
        std::max(static_cast<float>(TextureHeight), 1.0f);
    constexpr float safeScale = 0.84f;
    const float safeAspect = backingAspect; // symmetric X/Y safe scaling
    float contentScaleX = safeScale;
    float contentScaleY = safeScale;
    if (panelAspect >= safeAspect) {
        contentScaleY = safeScale * safeAspect / panelAspect;
    } else {
        contentScaleX = safeScale * panelAspect / safeAspect;
    }
    const float contentOffsetX = (1.0f - contentScaleX) * 0.5f;
    const float contentOffsetY = (1.0f - contentScaleY) * 0.5f;
'''
new_rect = '''    // v0.3.0: Java and native both use the complete fixed producer buffer.
    // Only the centered aspect-fit viewport changes when corners are dragged.
    const float panelAspect = PanelWidthMeters / std::max(PanelHeightMeters, 0.001f);
    const float backingAspect = static_cast<float>(TextureWidth) /
        std::max(static_cast<float>(TextureHeight), 1.0f);
    float contentScaleX = 1.0f;
    float contentScaleY = 1.0f;
    if (panelAspect >= backingAspect) {
        contentScaleY = backingAspect / panelAspect;
    } else {
        contentScaleX = panelAspect / backingAspect;
    }
    const float contentOffsetX = (1.0f - contentScaleX) * 0.5f;
    const float contentOffsetY = (1.0f - contentScaleY) * 0.5f;
'''
cpp = rep(cpp, old_rect, new_rect, 'full producer content rect')
cpp_path.write_text(cpp)

print('Quest Depth Browser Native v0.3.0 stability reset applied')
print('Depth NDC -> [0,1] remap: ON (matches GLB viewer)')
print('SurfaceTexture crop matrix: bypassed, explicit Y flip')
print('Presentation: exact producer pixel size, no LAYOUT_NO_LIMITS')
print('Safe-area hack: removed')
print('Left grip binding: ON')
print('Hand ownership: persistent until other hand takes over')
