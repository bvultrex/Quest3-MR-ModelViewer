from pathlib import Path
import re
import shutil

ROOT = Path('meta-openxr-sdk/Samples/XrSamples/XrPassthroughOcclusion')
REPO = Path('QuestDepthBrowserNative')

src_dir = ROOT / 'Src'
java_dir = ROOT / 'java/com/oculus/xrpassthroughocclusion'
android_dir = ROOT / 'Projects/Android'

src_dir.mkdir(parents=True, exist_ok=True)
java_dir.mkdir(parents=True, exist_ok=True)

cpp_parts = sorted((REPO / 'parts').glob('QuestDepthBrowserNative.*.cppfrag'))
if not cpp_parts:
    raise SystemExit('native browser C++ fragments missing')
(src_dir / 'QuestDepthBrowserNative.cpp').write_text(''.join(part.read_text() for part in cpp_parts))
shutil.copy2(REPO / 'src/QuestDepthBrowserNative.h', src_dir / 'QuestDepthBrowserNative.h')
shutil.copy2(
    REPO / 'java/com/oculus/xrpassthroughocclusion/QuestDepthBrowserBridge.java',
    java_dir / 'QuestDepthBrowserBridge.java')

# ---------------------------------------------------------------------------
# Android branding + internet access.
# ---------------------------------------------------------------------------
gradle_path = android_dir / 'build.gradle'
gradle = gradle_path.read_text()
gradle = gradle.replace(
    'applicationId "com.oculus.xrpassthroughocclusion"',
    'applicationId "com.bvultrex.questdepthbrowser.native"', 1)
gradle = gradle.replace('versionCode 1', 'versionCode 20', 1)
gradle = gradle.replace('versionName "1.0"', 'versionName "0.2.0"', 1)
gradle_path.write_text(gradle)

manifest_path = android_dir / 'AndroidManifest.xml'
manifest = manifest_path.read_text()
manifest = manifest.replace('android:versionCode="1"', 'android:versionCode="20"', 1)
manifest = manifest.replace('android:versionName="1.0"', 'android:versionName="0.2.0"', 1)
manifest = manifest.replace(
    '<uses-permission android:name="com.oculus.permission.USE_SCENE" />',
    '<uses-permission android:name="android.permission.INTERNET" />\n'
    '  <uses-permission android:name="com.oculus.permission.USE_SCENE" />',
    1)
manifest = manifest.replace(
    'android:label="xrpassthroughocclusion"',
    'android:label="Quest Depth Browser Native"\n'
    '      android:hardwareAccelerated="true"',
    1)
manifest_path.write_text(manifest)

# ---------------------------------------------------------------------------
# Native OpenXR integration.
# ---------------------------------------------------------------------------
main_path = src_dir / 'XrPassthroughOcclusion.cpp'
text = main_path.read_text()

include_anchor = '#include "XrPassthroughOcclusionGl.h"\n'
if '#include "QuestDepthBrowserNative.h"' not in text:
    if include_anchor not in text:
        raise SystemExit('native browser include anchor not found')
    text = text.replace(
        include_anchor,
        include_anchor + '#include "QuestDepthBrowserNative.h"\n',
        1)

app_anchor = '    App app;\n'
if 'QuestDepthBrowserNative nativeBrowser;' not in text:
    if app_anchor not in text:
        raise SystemExit('App app anchor not found')
    text = text.replace(
        app_anchor,
        app_anchor + '    QuestDepthBrowserNative nativeBrowser;\n',
        1)

start_depth_anchor = '    OXR(xrStartEnvironmentDepthProviderMETA(app.EnvironmentDepthProvider));\n'
if 'nativeBrowser.Initialize(' not in text:
    if start_depth_anchor not in text:
        raise SystemExit('environment depth start anchor not found')
    browser_init = r'''

#if defined(XR_USE_PLATFORM_ANDROID)
    if (!nativeBrowser.Initialize(
            Env,
            androidApp->activity->clazz,
            app.Session,
            systemProperties.graphicsProperties.maxSwapchainImageWidth,
            systemProperties.graphicsProperties.maxSwapchainImageHeight)) {
        ALOGE("Quest Depth Browser Native v0.2.0 failed to initialize");
    } else {
        ALOGV("Quest Depth Browser Native v0.2.0 initialized");
    }
#endif
'''
    text = text.replace(start_depth_anchor, start_depth_anchor + browser_init, 1)

render_anchor = '        app.appRenderer.RenderFrame(frameIn);\n'
if 'nativeBrowser.Render(' not in text:
    if render_anchor not in text:
        raise SystemExit('RenderFrame anchor not found')
    browser_render = r'''
#if defined(XR_USE_PLATFORM_ANDROID)
        nativeBrowser.Render(
            Env,
            frameIn.HasDepth,
            frameIn.DepthTexture,
            &frameIn.DepthViewMatrices[0].M[0][0],
            &frameIn.DepthProjectionMatrices[0].M[0][0],
            &frameIn.DepthViewMatrices[1].M[0][0],
            &frameIn.DepthProjectionMatrices[1].M[0][0]);
#endif

'''
    text = text.replace(render_anchor, browser_render + render_anchor, 1)

projection_submit = '        app.Layers[app.LayerCount++].Projection = proj_layer;\n'
if 'nativeBrowser.MakeLayer' not in text:
    if projection_submit not in text:
        raise SystemExit('projection submission anchor not found')
    replacement = r'''        // v0.2.0: do not submit the conventional projection layer. The browser is
        // submitted as two eye-specific, alpha-masked compositor quads instead.
#if defined(XR_USE_PLATFORM_ANDROID)
        if (nativeBrowser.IsReady()) {
            app.Layers[app.LayerCount++].Quad = nativeBrowser.MakeLayer(0, app.LocalSpace);
            app.Layers[app.LayerCount++].Quad = nativeBrowser.MakeLayer(1, app.LocalSpace);
        }
#endif
'''
    text = text.replace(projection_submit, replacement, 1)

cleanup_anchor = '    app.appRenderer.Destroy();\n'
if 'nativeBrowser.Destroy(Env);' not in text:
    if cleanup_anchor not in text:
        raise SystemExit('renderer cleanup anchor not found')
    text = text.replace(
        cleanup_anchor,
        '#if defined(XR_USE_PLATFORM_ANDROID)\n'
        '    nativeBrowser.Destroy(Env);\n'
        '#endif\n\n' + cleanup_anchor,
        1)

# Rename OpenXR app metadata for captures/logs.
text = text.replace(
    'strcpy(appInfo.applicationName, "XrPassthroughOcclusion");',
    'strcpy(appInfo.applicationName, "QuestDepthBrowserNative");',
    1)
main_path.write_text(text)

print('Quest Depth Browser Native v0.2.0 patch applied')
print('WebView source texture: virtual display -> SurfaceTexture -> GL_TEXTURE_EXTERNAL_OES')
print('Browser source target: 3200x2000 (clamped to runtime max)')
print('Compositor: LEFT + RIGHT XrCompositionLayerQuad')
print('Environment depth: per-eye 3x3 soft alpha mask')
print('Projection layer submission: disabled')
