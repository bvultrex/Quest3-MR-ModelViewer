from pathlib import Path

ROOT = Path('meta-openxr-sdk/Samples/XrSamples/XrPassthroughOcclusion')
SRC = ROOT / 'Src'
JAVA = ROOT / 'java/com/oculus/xrpassthroughocclusion'
ANDROID = ROOT / 'Projects/Android'

def rep(text, old, new, label):
    if old not in text:
        raise SystemExit(f'v0.3.3 anchor missing: {label}')
    return text.replace(old, new, 1)

# Version.
gradle_path = ANDROID / 'build.gradle'
gradle = gradle_path.read_text()
gradle = rep(gradle, 'versionCode 32', 'versionCode 33', 'versionCode')
gradle = rep(gradle, 'versionName "0.3.2"', 'versionName "0.3.3"', 'versionName')
gradle_path.write_text(gradle)

manifest_path = ANDROID / 'AndroidManifest.xml'
manifest = manifest_path.read_text()
manifest = rep(manifest, 'android:versionCode="32"', 'android:versionCode="33"', 'manifest versionCode')
manifest = rep(manifest, 'android:versionName="0.3.2"', 'android:versionName="0.3.3"', 'manifest versionName')
manifest_path.write_text(manifest)

bridge_path = JAVA / 'QuestDepthBrowserBridge.java'
bridge = bridge_path.read_text()

# Presentation/window geometry is forced to the producer coordinate system.
old_show = '''                presentation.show();
                if (rootFrame != null) {
                    rootFrame.post(() -> {
                        requestedAspect = 16.0f / 9.0f;
                        setWindowAspect(requestedAspect);
                        if (webView != null) webView.loadUrl("https://www.wikipedia.org/");
                    });
                }
'''
new_show = '''                presentation.show();
                if (window != null) {
                    window.setGravity(Gravity.TOP | Gravity.LEFT);
                    WindowManager.LayoutParams attrs = window.getAttributes();
                    attrs.width = surfaceWidth;
                    attrs.height = surfaceHeight;
                    attrs.x = 0;
                    attrs.y = 0;
                    attrs.gravity = Gravity.TOP | Gravity.LEFT;
                    window.setAttributes(attrs);
                    window.setLayout(surfaceWidth, surfaceHeight);
                    window.getDecorView().setPadding(0, 0, 0, 0);
                }
                if (rootFrame != null) {
                    ViewGroup.LayoutParams rootParams = rootFrame.getLayoutParams();
                    if (rootParams == null) {
                        rootParams = new ViewGroup.LayoutParams(surfaceWidth, surfaceHeight);
                    } else {
                        rootParams.width = surfaceWidth;
                        rootParams.height = surfaceHeight;
                    }
                    rootFrame.setLayoutParams(rootParams);
                    rootFrame.setPadding(0, 0, 0, 0);
                    rootFrame.setTranslationX(0f);
                    rootFrame.setTranslationY(0f);
                    rootFrame.post(() -> {
                        requestedAspect = 16.0f / 9.0f;
                        setWindowAspect(requestedAspect);
                        if (webView != null) webView.loadUrl("https://www.wikipedia.org/");
                    });
                }
'''
bridge = rep(bridge, old_show, new_show, 'force producer window geometry')

old_backing = '''            int backingWidth = (rootFrame != null && rootFrame.getWidth() > 0)
                    ? rootFrame.getWidth() : surfaceWidth;
            int backingHeight = (rootFrame != null && rootFrame.getHeight() > 0)
                    ? rootFrame.getHeight() : surfaceHeight;
            final float safeScale = 1.0f;
            int safeWidth = backingWidth;
            int safeHeight = backingHeight;
'''
new_backing = '''            // v0.3.3: producer pixels are the only source of truth.
            // Do not use Presentation/root measured bounds here. On Quest they
            // can be wider than the SurfaceTexture producer and caused the
            // persistent right-edge crop.
            final float safeScale = 1.0f;
            int safeWidth = surfaceWidth;
            int safeHeight = surfaceHeight;
'''
bridge = rep(bridge, old_backing, new_backing, 'producer-only aspect backing')

# Add visible producer-edge diagnostics. Left = magenta, right = cyan.
old_root_return = '''        rootFrame.addView(contentFrame, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT,
                Gravity.CENTER));
        toolbarCollapsed = false;
        return rootFrame;
'''
new_root_return = '''        rootFrame.addView(contentFrame, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT,
                Gravity.TOP | Gravity.LEFT));

        // Temporary v0.3.3 calibration rails. If both are visible in-headset,
        // the complete producer width reaches the OpenXR texture.
        View leftRail = new View(context);
        leftRail.setBackgroundColor(Color.MAGENTA);
        FrameLayout.LayoutParams leftRailParams = new FrameLayout.LayoutParams(
                dp(4, density),
                ViewGroup.LayoutParams.MATCH_PARENT,
                Gravity.TOP | Gravity.LEFT);
        rootFrame.addView(leftRail, leftRailParams);

        View rightRail = new View(context);
        rightRail.setBackgroundColor(Color.CYAN);
        FrameLayout.LayoutParams rightRailParams = new FrameLayout.LayoutParams(
                dp(4, density),
                ViewGroup.LayoutParams.MATCH_PARENT,
                Gravity.TOP | Gravity.RIGHT);
        rootFrame.addView(rightRail, rightRailParams);

        toolbarCollapsed = false;
        return rootFrame;
'''
bridge = rep(bridge, old_root_return, new_root_return, 'calibration rails')
bridge_path.write_text(bridge)

# ---------------------------------------------------------------------------
# Depth edge quality: use a 13-tap soft coverage kernel at sub-depth-texel
# offsets. The final quad still receives fractional alpha.
# ---------------------------------------------------------------------------
cpp_path = SRC / 'QuestDepthBrowserNative.cpp'
cpp = cpp_path.read_text()

old_kernel = '''                float visibilitySum = 0.0;
                float weightSum = 0.0;
                float centerDepth = texture(
                    uEnvironmentDepthTexture,
                    vec3(depthUv, float(uEye))).r;

                for (int y = -1; y <= 1; ++y) {
                    for (int x = -1; x <= 1; ++x) {
                        vec2 tapUv = clamp(
                            depthUv + vec2(float(x), float(y)) * texel,
                            vec2(0.0),
                            vec2(1.0));
                        float realDepth = texture(
                            uEnvironmentDepthTexture,
                            vec3(tapUv, float(uEye))).r;
                        float wx = (x == 0) ? 2.0 : 1.0;
                        float wy = (y == 0) ? 2.0 : 1.0;
                        float weight = wx * wy;
                        float depthDelta = realDepth - virtualDepth - projectedBias;
                        float discontinuity = abs(realDepth - centerDepth);
                        float tapWidth = clamp(
                            derivativeWidth + discontinuity * 0.12,
                            0.00040,
                            0.00450);
                        float tapVisibility = smoothstep(-tapWidth, tapWidth, depthDelta);
                        visibilitySum += tapVisibility * weight;
                        weightSum += weight;
                    }
                }

                // Quad layers do not benefit from the GLB viewer's MSAA
                // alpha-to-coverage resolve. Keep fractional coverage instead of
                // re-hardening it with a second smoothstep.
                visibility = clamp(visibilitySum / max(weightSum, 0.0001), 0.0, 1.0);
'''
new_kernel = '''                float visibilitySum = 0.0;
                float weightSum = 0.0;
                float centerDepth = texture(
                    uEnvironmentDepthTexture,
                    vec3(depthUv, float(uEye))).r;

                // v0.3.3 compositor-quad coverage kernel.
                // Sample between Environment Depth texel centres as well as on
                // them. This trades a small edge feather for much less visible
                // stair stepping on furniture contours.
                const int TAP_COUNT = 13;
                vec2 offsets[TAP_COUNT] = vec2[](
                    vec2( 0.00,  0.00),
                    vec2( 0.55,  0.00), vec2(-0.55,  0.00),
                    vec2( 0.00,  0.55), vec2( 0.00, -0.55),
                    vec2( 0.55,  0.55), vec2(-0.55,  0.55),
                    vec2( 0.55, -0.55), vec2(-0.55, -0.55),
                    vec2( 1.10,  0.00), vec2(-1.10,  0.00),
                    vec2( 0.00,  1.10), vec2( 0.00, -1.10)
                );
                float weights[TAP_COUNT] = float[](
                    4.0,
                    2.0, 2.0, 2.0, 2.0,
                    1.5, 1.5, 1.5, 1.5,
                    0.75, 0.75, 0.75, 0.75
                );

                for (int i = 0; i < TAP_COUNT; ++i) {
                    vec2 tapUv = clamp(
                        depthUv + offsets[i] * texel,
                        vec2(0.0),
                        vec2(1.0));
                    float realDepth = texture(
                        uEnvironmentDepthTexture,
                        vec3(tapUv, float(uEye))).r;
                    float depthDelta = realDepth - virtualDepth - projectedBias;
                    float discontinuity = abs(realDepth - centerDepth);
                    float tapWidth = clamp(
                        derivativeWidth * 1.25 + discontinuity * 0.20,
                        0.00065,
                        0.00750);
                    float tapVisibility = smoothstep(-tapWidth, tapWidth, depthDelta);
                    visibilitySum += tapVisibility * weights[i];
                    weightSum += weights[i];
                }

                // Keep the true fractional mask for the compositor quad.
                visibility = clamp(visibilitySum / max(weightSum, 0.0001), 0.0, 1.0);
'''
cpp = rep(cpp, old_kernel, new_kernel, '13-tap soft depth kernel')
cpp_path.write_text(cpp)

print('Quest Depth Browser Native v0.3.3 applied')
print('Presentation window: fixed producer-size, top-left anchored')
print('Aspect math: producer pixels only')
print('Calibration rails: magenta left / cyan right')
print('Depth: 13-tap soft coverage kernel')
