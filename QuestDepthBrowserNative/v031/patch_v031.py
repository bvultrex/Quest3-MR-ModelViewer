from pathlib import Path
import shutil

ROOT = Path('meta-openxr-sdk/Samples/XrSamples/XrPassthroughOcclusion')
SRC = ROOT / 'Src'
JAVA = ROOT / 'java/com/oculus/xrpassthroughocclusion'
ANDROID = ROOT / 'Projects/Android'
REPO = Path('QuestDepthBrowserNative/v031')

def rep(text, old, new, label):
    if old not in text:
        raise SystemExit(f'v0.3.1 anchor missing: {label}')
    return text.replace(old, new, 1)

shutil.copy2(REPO / 'QuestDepthBrowserSurfaceActivity.java',
             JAVA / 'QuestDepthBrowserSurfaceActivity.java')

# Version.
gradle_path = ANDROID / 'build.gradle'
gradle = gradle_path.read_text()
gradle = rep(gradle, 'versionCode 30', 'versionCode 31', 'versionCode')
gradle = rep(gradle, 'versionName "0.3.0"', 'versionName "0.3.1"', 'versionName')
gradle_path.write_text(gradle)

manifest_path = ANDROID / 'AndroidManifest.xml'
manifest = manifest_path.read_text()
manifest = rep(manifest, 'android:versionCode="30"', 'android:versionCode="31"', 'manifest versionCode')
manifest = rep(manifest, 'android:versionName="0.3.0"', 'android:versionName="0.3.1"', 'manifest versionName')
activity_xml = '''    <activity
        android:name="com.oculus.xrpassthroughocclusion.QuestDepthBrowserSurfaceActivity"
        android:theme="@android:style/Theme.Material.Light.NoActionBar.Fullscreen"
        android:screenOrientation="landscape"
        android:resizeableActivity="true"
        android:excludeFromRecents="true"
        android:exported="false"
        android:launchMode="singleTop"
        android:configChanges="screenSize|smallestScreenSize|screenLayout|orientation|keyboardHidden|keyboard|navigation|uiMode|density" />
'''
if 'QuestDepthBrowserSurfaceActivity' not in manifest:
    if '</application>' not in manifest:
        raise SystemExit('v0.3.1 manifest has no application closing tag')
    manifest = manifest.replace(
        '  </application>',
        activity_xml + '  </application>',
        1)
manifest_path.write_text(manifest)

bridge_path = JAVA / 'QuestDepthBrowserBridge.java'
bridge = bridge_path.read_text()

# Imports + activity state.
bridge = rep(
    bridge,
    'import android.app.Presentation;\n',
    'import android.app.Presentation;\nimport android.app.ActivityOptions;\nimport android.content.Intent;\n',
    'activity launch imports')
bridge = rep(
    bridge,
    '    private static Presentation presentation;\n',
    '    private static Presentation presentation; // legacy, unused from v0.3.1\n'
    '    private static Activity browserActivity;\n'
    '    private static float requestedAspect = 16.0f / 9.0f;\n',
    'browser activity state')

# Replace Presentation producer with a real Activity launched on the VirtualDisplay.
old_block = '''                presentation = new Presentation(
                        activity,
                        virtualDisplay.getDisplay(),
                        android.R.style.Theme_Material_Light_NoActionBar_Fullscreen);
                presentation.requestWindowFeature(Window.FEATURE_NO_TITLE);
                presentation.setContentView(createBrowserUi(presentation.getContext()));

                Window window = presentation.getWindow();
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
                if (rootFrame != null) {
                    rootFrame.post(() -> {
                        rootFrame.requestLayout();
                        rootFrame.invalidate();
                    });
                }
                webView.loadUrl("https://www.wikipedia.org/");
'''
new_block = '''                Intent intent = new Intent(activity, QuestDepthBrowserSurfaceActivity.class);
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
                ActivityOptions options = ActivityOptions.makeBasic();
                options.setLaunchDisplayId(virtualDisplay.getDisplay().getDisplayId());
                activity.startActivity(intent, options.toBundle());
'''
bridge = rep(bridge, old_block, new_block, 'replace Presentation with display Activity')

# New activity attach/detach entry points.
anchor = '    public static void pointer(final float normalizedX, final float normalizedY, final int action) {\n'
attach = '''    public static void attachSurfaceActivity(final Activity activity) {
        MAIN.post(() -> {
            try {
                browserActivity = activity;
                Window window = activity.getWindow();
                if (window != null) {
                    window.setSoftInputMode(
                            WindowManager.LayoutParams.SOFT_INPUT_ADJUST_NOTHING);
                    window.getDecorView().setPadding(0, 0, 0, 0);
                }
                activity.setContentView(createBrowserUi(activity));
                if (rootFrame != null) {
                    rootFrame.post(() -> {
                        setWindowAspect(requestedAspect);
                        if (webView != null) webView.loadUrl("https://www.wikipedia.org/");
                    });
                }
            } catch (Throwable ignored) {}
        });
    }

    public static void detachSurfaceActivity(final Activity activity) {
        MAIN.post(() -> {
            if (browserActivity == activity) browserActivity = null;
        });
    }

''' + anchor
bridge = rep(bridge, anchor, attach, 'surface activity attach methods')

# Persist requested aspect and size against the actual Activity root, not assumed decor.
bridge = rep(
    bridge,
    '''    public static void setWindowAspect(final float requestedAspect) {
        MAIN.post(() -> {
            if (contentFrame == null || surfaceWidth <= 0 || surfaceHeight <= 0) return;
            float aspect = Math.max(0.55f, Math.min(3.20f, requestedAspect));
            final float safeScale = 1.0f;
            int safeWidth = surfaceWidth;
            int safeHeight = surfaceHeight;
''',
    '''    public static void setWindowAspect(final float newAspect) {
        requestedAspect = Math.max(0.55f, Math.min(3.20f, newAspect));
        MAIN.post(() -> {
            if (contentFrame == null || surfaceWidth <= 0 || surfaceHeight <= 0) return;
            float aspect = requestedAspect;
            int backingWidth = (rootFrame != null && rootFrame.getWidth() > 0)
                    ? rootFrame.getWidth() : surfaceWidth;
            int backingHeight = (rootFrame != null && rootFrame.getHeight() > 0)
                    ? rootFrame.getHeight() : surfaceHeight;
            final float safeScale = 1.0f;
            int safeWidth = backingWidth;
            int safeHeight = backingHeight;
''',
    'aspect against activity root')

bridge = rep(
    bridge,
    '            params.leftMargin = Math.max(0, (surfaceWidth - width) / 2);\n'
    '            params.topMargin = Math.max(0, (surfaceHeight - height) / 2);\n',
    '            params.leftMargin = Math.max(0, (safeWidth - width) / 2);\n'
    '            params.topMargin = Math.max(0, (safeHeight - height) / 2);\n',
    'aspect margins against activity root')

# IME now targets the real browser Activity window.
bridge = rep(
    bridge,
    '''            if (presentation != null && presentation.getWindow() != null) {
                presentation.getWindow().setSoftInputMode(
                        WindowManager.LayoutParams.SOFT_INPUT_ADJUST_NOTHING |
                        WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_VISIBLE);
            }
''',
    '''            if (browserActivity != null && browserActivity.getWindow() != null) {
                browserActivity.getWindow().setSoftInputMode(
                        WindowManager.LayoutParams.SOFT_INPUT_ADJUST_NOTHING |
                        WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_VISIBLE);
            }
''',
    'IME surface activity window')

# Stop secondary Activity before releasing its display.
bridge = rep(
    bridge,
    '''        try {
            if (presentation != null) presentation.dismiss();
        } catch (Throwable ignored) {}
        presentation = null;

        try {
            if (virtualDisplay != null) virtualDisplay.release();
''',
    '''        try {
            if (browserActivity != null && !browserActivity.isFinishing()) {
                browserActivity.finish();
            }
        } catch (Throwable ignored) {}
        browserActivity = null;
        presentation = null;

        try {
            if (virtualDisplay != null) virtualDisplay.release();
''',
    'finish surface activity')
bridge_path.write_text(bridge)

# ---------------------------------------------------------------------------
# Browser depth softening. Keep the corrected depth space from v0.3.0 but
# interpolate the environment depth texture and preserve fractional alpha.
# ---------------------------------------------------------------------------
cpp_path = SRC / 'QuestDepthBrowserNative.cpp'
cpp = cpp_path.read_text()
cpp = rep(
    cpp,
    '''                visibility = clamp(visibilitySum / max(weightSum, 0.0001), 0.0, 1.0);
                visibility = smoothstep(0.08, 0.92, visibility);
''',
    '''                // Quad layers do not benefit from the GLB viewer's MSAA
                // alpha-to-coverage resolve. Keep fractional coverage instead of
                // re-hardening it with a second smoothstep.
                visibility = clamp(visibilitySum / max(weightSum, 0.0001), 0.0, 1.0);
''',
    'preserve fractional soft coverage')

cpp = rep(
    cpp,
    '''    glActiveTexture(GL_TEXTURE1);
    glBindTexture(GL_TEXTURE_2D_ARRAY, environmentDepthTexture);
    glUniform1i(DepthTextureLocation, 1);
''',
    '''    glActiveTexture(GL_TEXTURE1);
    glBindTexture(GL_TEXTURE_2D_ARRAY, environmentDepthTexture);
    // v0.3.1 soft upsampling for compositor quads. Meta's sample deliberately
    // uses NEAREST for hard occlusion; our browser has no MSAA/A2C projection
    // resolve, so LINEAR sampling removes the large depth-texel stair steps.
    glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glUniform1i(DepthTextureLocation, 1);
''',
    'linear depth sampling')
cpp_path.write_text(cpp)

print('Quest Depth Browser Native v0.3.1 applied')
print('Browser producer: secondary Activity on VirtualDisplay')
print('Presentation/Dialog geometry: removed from active path')
print('Depth: corrected v0.3.0 projection + LINEAR soft upsampling')
print('Quad alpha: fractional coverage preserved')
