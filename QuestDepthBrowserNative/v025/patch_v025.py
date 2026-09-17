from pathlib import Path

ROOT = Path('meta-openxr-sdk/Samples/XrSamples/XrPassthroughOcclusion')
SRC = ROOT / 'Src'
JAVA = ROOT / 'java/com/oculus/xrpassthroughocclusion'
ANDROID = ROOT / 'Projects/Android'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f'v0.2.5 anchor missing: {label}')
    return text.replace(old, new, 1)

# ---------------------------------------------------------------------------
# Version bump.
# ---------------------------------------------------------------------------
gradle_path = ANDROID / 'build.gradle'
gradle = gradle_path.read_text()
gradle = replace_once(gradle, 'versionCode 24', 'versionCode 25', 'Gradle versionCode')
gradle = replace_once(gradle, 'versionName "0.2.4"', 'versionName "0.2.5"', 'Gradle versionName')
gradle_path.write_text(gradle)

manifest_path = ANDROID / 'AndroidManifest.xml'
manifest = manifest_path.read_text()
manifest = replace_once(manifest, 'android:versionCode="24"', 'android:versionCode="25"', 'manifest versionCode')
manifest = replace_once(manifest, 'android:versionName="0.2.4"', 'android:versionName="0.2.5"', 'manifest versionName')
manifest_path.write_text(manifest)

# ---------------------------------------------------------------------------
# Keep the VirtualDisplay / SurfaceTexture geometry FIXED for its lifetime.
# Resizing the producer after attaching SurfaceTexture caused the Presentation
# and BufferQueue crop to disagree, so Android rendered a wider view than the
# sampled texture and the page/toolbar appeared stuck to the right edge.
#
# Instead, resize a centered child viewport inside the fixed backing surface.
# Chromium reflows because WebView's actual View bounds change. The native
# shader samples exactly that centered viewport and stretches it over the XR
# quad. This keeps the high-resolution producer stable and avoids BufferQueue
# crop/transform churn.
# ---------------------------------------------------------------------------
bridge_path = JAVA / 'QuestDepthBrowserBridge.java'
bridge = bridge_path.read_text()

old_aspect = '''    public static void setWindowAspect(final float requestedAspect) {
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

new_aspect = '''    public static void setWindowAspect(final float requestedAspect) {
        MAIN.post(() -> {
            if (contentFrame == null || surfaceWidth <= 0 || surfaceHeight <= 0) return;
            float aspect = Math.max(0.55f, Math.min(3.20f, requestedAspect));
            float backingAspect = (float) surfaceWidth / (float) surfaceHeight;

            int width;
            int height;
            if (aspect >= backingAspect) {
                width = surfaceWidth;
                height = Math.max(1, Math.round(surfaceWidth / aspect));
            } else {
                height = surfaceHeight;
                width = Math.max(1, Math.round(surfaceHeight * aspect));
            }

            FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(
                    width, height, Gravity.CENTER);
            contentFrame.setLayoutParams(params);
            contentFrame.requestLayout();
            contentFrame.invalidate();

            if (browserRoot != null) {
                browserRoot.setLayoutParams(new FrameLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.MATCH_PARENT));
                browserRoot.requestLayout();
            }
            if (webView != null) {
                webView.requestLayout();
                webView.invalidate();
                webView.post(() -> {
                    if (webView != null) {
                        webView.evaluateJavascript(
                                "window.dispatchEvent(new Event('resize'));", null);
                    }
                });
            }
        });
    }
'''
bridge = replace_once(bridge, old_aspect, new_aspect, 'fixed backing viewport resize')

# Overview mode can preserve a page-scale chosen for an earlier viewport and
# makes debugging layout harder. Let responsive sites use the real viewport.
bridge = replace_once(
    bridge,
    'settings.setLoadWithOverviewMode(true);',
    'settings.setLoadWithOverviewMode(false);',
    'disable overview scaling')
bridge_path.write_text(bridge)

# ---------------------------------------------------------------------------
# Native sampling: restore the centered viewport rect. The backing Surface is
# fixed 16:9; panel aspect determines which centered region contains Android UI.
# ---------------------------------------------------------------------------
cpp_path = SRC / 'QuestDepthBrowserNative.cpp'
cpp = cpp_path.read_text()
old_rect = '''    // v0.2.4: VirtualDisplay owns the requested aspect ratio. Sample the
    // complete producer buffer exactly once. No Java letterbox + shader crop.
    glUniform4f(gBrowserContentRectLocation, 0.0f, 0.0f, 1.0f, 1.0f);
'''
new_rect = '''    // v0.2.5: fixed producer surface + centered Android viewport. The Java
    // contentFrame uses the exact same aspect-fit math, so sample that region
    // once and stretch it across the XR quad. SurfaceTexture itself never
    // changes size after creation.
    const float panelAspect = PanelWidthMeters / std::max(PanelHeightMeters, 0.001f);
    const float backingAspect = static_cast<float>(TextureWidth) /
        std::max(static_cast<float>(TextureHeight), 1.0f);
    float contentOffsetX = 0.0f;
    float contentOffsetY = 0.0f;
    float contentScaleX = 1.0f;
    float contentScaleY = 1.0f;
    if (panelAspect >= backingAspect) {
        contentScaleY = backingAspect / panelAspect;
        contentOffsetY = (1.0f - contentScaleY) * 0.5f;
    } else {
        contentScaleX = panelAspect / backingAspect;
        contentOffsetX = (1.0f - contentScaleX) * 0.5f;
    }
    glUniform4f(
        gBrowserContentRectLocation,
        contentOffsetX,
        contentOffsetY,
        contentScaleX,
        contentScaleY);
'''
cpp = replace_once(cpp, old_rect, new_rect, 'centered content rect')
cpp_path.write_text(cpp)

print('Quest Depth Browser Native v0.2.5 patch applied')
print('VirtualDisplay / SurfaceTexture resizing: OFF')
print('Backing producer: fixed for lifetime')
print('Browser viewport: centered aspect-fit child view')
print('Shader: samples matching centered viewport')
print('Chromium resize event: explicit after View relayout')
print('Sharp compositor quads + Environment Depth: preserved')
