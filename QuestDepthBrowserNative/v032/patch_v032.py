from pathlib import Path

ROOT = Path('meta-openxr-sdk/Samples/XrSamples/XrPassthroughOcclusion')
SRC = ROOT / 'Src'
JAVA = ROOT / 'java/com/oculus/xrpassthroughocclusion'
ANDROID = ROOT / 'Projects/Android'

def rep(text, old, new, label):
    if old not in text:
        raise SystemExit(f'v0.3.2 anchor missing: {label}')
    return text.replace(old, new, 1)

# Version.
gradle_path = ANDROID / 'build.gradle'
gradle = gradle_path.read_text()
gradle = rep(gradle, 'versionCode 31', 'versionCode 32', 'versionCode')
gradle = rep(gradle, 'versionName "0.3.1"', 'versionName "0.3.2"', 'versionName')
gradle_path.write_text(gradle)

manifest_path = ANDROID / 'AndroidManifest.xml'
manifest = manifest_path.read_text()
manifest = rep(manifest, 'android:versionCode="31"', 'android:versionCode="32"', 'manifest versionCode')
manifest = rep(manifest, 'android:versionName="0.3.1"', 'android:versionName="0.3.2"', 'manifest versionName')
manifest_path.write_text(manifest)

# Restore working Presentation producer. Keep v0.3.1 class declared but unused.
bridge_path = JAVA / 'QuestDepthBrowserBridge.java'
bridge = bridge_path.read_text()

old_start = '''                Intent intent = new Intent(activity, QuestDepthBrowserSurfaceActivity.class);
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
                ActivityOptions options = ActivityOptions.makeBasic();
                options.setLaunchDisplayId(virtualDisplay.getDisplay().getDisplayId());
                activity.startActivity(intent, options.toBundle());
'''
new_start = '''                presentation = new Presentation(
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
                if (rootFrame != null) {
                    rootFrame.post(() -> {
                        requestedAspect = 16.0f / 9.0f;
                        setWindowAspect(requestedAspect);
                        if (webView != null) webView.loadUrl("https://www.wikipedia.org/");
                    });
                }
'''
bridge = rep(bridge, old_start, new_start, 'restore Presentation producer')

# Hardware keyboard should work on Presentation again.
bridge = rep(
    bridge,
    '''            if (browserActivity != null && browserActivity.getWindow() != null) {
                browserActivity.getWindow().setSoftInputMode(
                        WindowManager.LayoutParams.SOFT_INPUT_ADJUST_NOTHING |
                        WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_VISIBLE);
            }
''',
    '''            if (presentation != null && presentation.getWindow() != null) {
                presentation.getWindow().setSoftInputMode(
                        WindowManager.LayoutParams.SOFT_INPUT_ADJUST_NOTHING |
                        WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_VISIBLE);
            }
''',
    'IME back to Presentation')

# Cleanly dismiss Presentation again.
bridge = rep(
    bridge,
    '''        browserActivity = null;
        presentation = null;

        try {
            if (virtualDisplay != null) virtualDisplay.release();
''',
    '''        browserActivity = null;
        try {
            if (presentation != null) presentation.dismiss();
        } catch (Throwable ignored) {}
        presentation = null;

        try {
            if (virtualDisplay != null) virtualDisplay.release();
''',
    'dismiss Presentation')
bridge_path.write_text(bridge)

# Native producer/swapchain size: 2560x1440, avoiding the apparent ~2560-wide
# Android virtual-display/HWC ceiling seen on Quest hardware.
cpp_path = SRC / 'QuestDepthBrowserNative.cpp'
cpp = cpp_path.read_text()
cpp = rep(
    cpp,
    '''    float aspect = 1800.0f / 3200.0f;
    TextureWidth = std::min<int>(kRequestedWidth, int(maxWidth));
''',
    '''    constexpr int kQuestProducerWidth = 2560;
    constexpr int kQuestProducerHeight = 1440;
    float aspect = float(kQuestProducerHeight) / float(kQuestProducerWidth);
    TextureWidth = std::min<int>(kQuestProducerWidth, int(maxWidth));
''',
    'producer width 2560')
cpp_path.write_text(cpp)

print('Quest Depth Browser Native v0.3.2 applied')
print('Producer: Presentation restored')
print('Producer/swapchain: 2560x1440')
print('Dual controller input: preserved from v0.3.0')
print('Depth soft upsampling: preserved from v0.3.1')
print('Sharp compositor quad path: preserved')
