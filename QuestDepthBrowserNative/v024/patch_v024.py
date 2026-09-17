from pathlib import Path

ROOT = Path('meta-openxr-sdk/Samples/XrSamples/XrPassthroughOcclusion')
SRC = ROOT / 'Src'
JAVA = ROOT / 'java/com/oculus/xrpassthroughocclusion'
ANDROID = ROOT / 'Projects/Android'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f'v0.2.4 anchor missing: {label}')
    return text.replace(old, new, 1)

# ---------------------------------------------------------------------------
# Version bump.
# ---------------------------------------------------------------------------
gradle_path = ANDROID / 'build.gradle'
gradle = gradle_path.read_text()
gradle = replace_once(gradle, 'versionCode 23', 'versionCode 24', 'Gradle versionCode')
gradle = replace_once(gradle, 'versionName "0.2.3"', 'versionName "0.2.4"', 'Gradle versionName')
gradle_path.write_text(gradle)

manifest_path = ANDROID / 'AndroidManifest.xml'
manifest = manifest_path.read_text()
manifest = replace_once(manifest, 'android:versionCode="23"', 'android:versionCode="24"', 'manifest versionCode')
manifest = replace_once(manifest, 'android:versionName="0.2.3"', 'android:versionName="0.2.4"', 'manifest versionName')
manifest_path.write_text(manifest)

# ---------------------------------------------------------------------------
# Android producer surface.
# v0.2.3 placed a variable-aspect contentFrame inside a fixed 3200x2000
# VirtualDisplay and the native shader cropped that fixed surface again.
# v0.2.4 makes the VirtualDisplay itself own the requested aspect ratio.
# ---------------------------------------------------------------------------
bridge_path = JAVA / 'QuestDepthBrowserBridge.java'
bridge = bridge_path.read_text()
bridge = replace_once(
    bridge,
    '    private static Surface surface;\n',
    '    private static Surface surface;\n    private static SurfaceTexture sourceSurfaceTexture;\n',
    'SurfaceTexture field')
bridge = replace_once(
    bridge,
    '''                surfaceWidth = width;
                surfaceHeight = height;
                surface = new Surface(surfaceTexture);
''',
    '''                surfaceWidth = width;
                surfaceHeight = height;
                sourceSurfaceTexture = surfaceTexture;
                surface = new Surface(surfaceTexture);
''',
    'remember producer SurfaceTexture')

old_aspect = '''    public static void setWindowAspect(final float requestedAspect) {
        MAIN.post(() -> {
            if (contentFrame == null || surfaceWidth <= 0 || surfaceHeight <= 0) return;
            float aspect = Math.max(0.55f, Math.min(3.20f, requestedAspect));
            float textureAspect = (float) surfaceWidth / (float) surfaceHeight;
            int width;
            int height;
            if (aspect >= textureAspect) {
                width = surfaceWidth;
                height = Math.max(1, Math.round(surfaceWidth / aspect));
            } else {
                height = surfaceHeight;
                width = Math.max(1, Math.round(surfaceHeight * aspect));
            }
            FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(width, height, Gravity.CENTER);
            contentFrame.setLayoutParams(params);
            contentFrame.requestLayout();
            contentFrame.invalidate();
        });
    }
'''
new_aspect = '''    public static void setWindowAspect(final float requestedAspect) {
        MAIN.post(() -> {
            if (virtualDisplay == null || sourceSurfaceTexture == null) return;
            float aspect = Math.max(0.55f, Math.min(3.20f, requestedAspect));

            // Keep a high-resolution producer while changing the producer's real
            // dimensions. Chromium therefore reflows at the actual window aspect
            // instead of being letterboxed inside another texture.
            int width;
            int height;
            if (aspect >= (16f / 9f)) {
                width = 3200;
                height = Math.max(1000, Math.min(2400, Math.round(width / aspect)));
            } else {
                height = 1800;
                width = Math.max(1000, Math.min(3200, Math.round(height * aspect)));
            }

            if (width == surfaceWidth && height == surfaceHeight) return;
            surfaceWidth = width;
            surfaceHeight = height;
            try {
                sourceSurfaceTexture.setDefaultBufferSize(width, height);
                virtualDisplay.resize(width, height, 320);
                if (contentFrame != null) {
                    contentFrame.setLayoutParams(new FrameLayout.LayoutParams(
                            ViewGroup.LayoutParams.MATCH_PARENT,
                            ViewGroup.LayoutParams.MATCH_PARENT,
                            Gravity.CENTER));
                    contentFrame.requestLayout();
                    contentFrame.invalidate();
                }
            } catch (Throwable ignored) {}
        });
    }
'''
bridge = replace_once(bridge, old_aspect, new_aspect, 'VirtualDisplay aspect resize')
bridge = replace_once(
    bridge,
    'settings.setLoadWithOverviewMode(false);',
    'settings.setLoadWithOverviewMode(true);',
    'WebView overview mode')
bridge = replace_once(
    bridge,
    '        surface = null;\n',
    '        surface = null;\n        sourceSurfaceTexture = null;\n',
    'SurfaceTexture cleanup')
bridge_path.write_text(bridge)

# ---------------------------------------------------------------------------
# Native renderer.
# Use a real 16:9 swapchain baseline and sample the complete producer buffer.
# The VirtualDisplay now provides the active aspect, so there is no second crop.
# ---------------------------------------------------------------------------
cpp_path = SRC / 'QuestDepthBrowserNative.cpp'
cpp = cpp_path.read_text()
cpp = replace_once(
    cpp,
    '    float aspect = float(kRequestedHeight) / float(kRequestedWidth);\n',
    '    float aspect = 1800.0f / 3200.0f;\n',
    '16:9 swapchain baseline')

old_content_rect = '''    const float panelAspect = PanelWidthMeters / std::max(PanelHeightMeters, 0.001f);
    const float textureAspect = static_cast<float>(TextureWidth) /
        std::max(static_cast<float>(TextureHeight), 1.0f);
    float contentOffsetX = 0.0f;
    float contentOffsetY = 0.0f;
    float contentScaleX = 1.0f;
    float contentScaleY = 1.0f;
    if (panelAspect >= textureAspect) {
        contentScaleY = textureAspect / panelAspect;
        contentOffsetY = (1.0f - contentScaleY) * 0.5f;
    } else {
        contentScaleX = panelAspect / textureAspect;
        contentOffsetX = (1.0f - contentScaleX) * 0.5f;
    }
    glUniform4f(
        gBrowserContentRectLocation,
        contentOffsetX,
        contentOffsetY,
        contentScaleX,
        contentScaleY);
'''
new_content_rect = '''    // v0.2.4: VirtualDisplay owns the requested aspect ratio. Sample the
    // complete producer buffer exactly once. No Java letterbox + shader crop.
    glUniform4f(gBrowserContentRectLocation, 0.0f, 0.0f, 1.0f, 1.0f);
'''
cpp = replace_once(cpp, old_content_rect, new_content_rect, 'remove double crop')

shader_anchor = '''    vec4 browser = texture(uBrowserTexture, transformedUv.xy);

    float visibility = 1.0;
'''
shader_replacement = '''    vec4 browser = texture(uBrowserTexture, transformedUv.xy);

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

    float visibility = 1.0;
'''
cpp = replace_once(cpp, shader_anchor, shader_replacement, 'native diagnostic frame')
cpp_path.write_text(cpp)

print('Quest Depth Browser Native v0.2.4 patch applied')
print('Initial producer + swapchain: true 3200x1800 16:9')
print('Aspect changes: VirtualDisplay.resize + SurfaceTexture buffer resize')
print('Shader content rect: full producer, no second crop')
print('Native OpenXR frame/corner markers: ON')
print('Sharp per-eye compositor quads + Environment Depth: preserved')
