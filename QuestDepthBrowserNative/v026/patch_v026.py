from pathlib import Path

ROOT = Path('meta-openxr-sdk/Samples/XrSamples/XrPassthroughOcclusion')
SRC = ROOT / 'Src'
JAVA = ROOT / 'java/com/oculus/xrpassthroughocclusion'
ANDROID = ROOT / 'Projects/Android'


def rep(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f'v0.2.6 anchor missing: {label}')
    return text.replace(old, new, 1)

# ---------------------------------------------------------------------------
# Version bump.
# ---------------------------------------------------------------------------
gradle_path = ANDROID / 'build.gradle'
gradle = gradle_path.read_text()
gradle = rep(gradle, 'versionCode 25', 'versionCode 26', 'Gradle versionCode')
gradle = rep(gradle, 'versionName "0.2.5"', 'versionName "0.2.6"', 'Gradle versionName')
gradle_path.write_text(gradle)

manifest_path = ANDROID / 'AndroidManifest.xml'
manifest = manifest_path.read_text()
manifest = rep(manifest, 'android:versionCode="25"', 'android:versionCode="26"', 'manifest versionCode')
manifest = rep(manifest, 'android:versionName="0.2.5"', 'android:versionName="0.2.6"', 'manifest versionName')
manifest_path.write_text(manifest)

# ---------------------------------------------------------------------------
# Per-hand trigger/grip state. The sample's bool trigger action is already bound
# to both hands; query it with subaction paths so either controller can own the
# browser interaction for that frame.
# ---------------------------------------------------------------------------
input_h_path = SRC / 'XrPassthroughOcclusionInput.h'
input_h = input_h_path.read_text()
input_h = rep(
    input_h,
    '''extern XrActionStateBoolean boolState;\nextern XrActionStateFloat rightGripState;\nextern XrActionStateVector2f rightThumbstickState;\n''',
    '''extern XrActionStateBoolean boolState;\nextern XrActionStateBoolean leftTriggerState;\nextern XrActionStateBoolean rightTriggerState;\nextern XrActionStateFloat leftGripState;\nextern XrActionStateFloat rightGripState;\nextern XrActionStateVector2f rightThumbstickState;\n''',
    'input header per-hand states')
input_h_path.write_text(input_h)

input_cpp_path = SRC / 'XrPassthroughOcclusionInput.cpp'
input_cpp = input_cpp_path.read_text()
input_cpp = rep(
    input_cpp,
    '''XrActionStateFloat GetActionStateFloat(App& app, XrAction action, XrPath subactionPath) {\n''',
    '''XrActionStateBoolean GetActionStateBoolean(App& app, XrAction action, XrPath subactionPath) {\n    XrActionStateGetInfo getInfo = {XR_TYPE_ACTION_STATE_GET_INFO};\n    getInfo.action = action;\n    getInfo.subactionPath = subactionPath;\n    XrActionStateBoolean state = {XR_TYPE_ACTION_STATE_BOOLEAN};\n    OXR(xrGetActionStateBoolean(app.Session, &getInfo, &state));\n    return state;\n}\n\nXrActionStateFloat GetActionStateFloat(App& app, XrAction action, XrPath subactionPath) {\n''',
    'per-hand boolean helper')
input_cpp = rep(
    input_cpp,
    '''XrActionStateBoolean boolState;\nXrActionStateFloat rightGripState{XR_TYPE_ACTION_STATE_FLOAT};\nXrActionStateVector2f rightThumbstickState{XR_TYPE_ACTION_STATE_VECTOR2F};\n''',
    '''XrActionStateBoolean boolState;\nXrActionStateBoolean leftTriggerState{XR_TYPE_ACTION_STATE_BOOLEAN};\nXrActionStateBoolean rightTriggerState{XR_TYPE_ACTION_STATE_BOOLEAN};\nXrActionStateFloat leftGripState{XR_TYPE_ACTION_STATE_FLOAT};\nXrActionStateFloat rightGripState{XR_TYPE_ACTION_STATE_FLOAT};\nXrActionStateVector2f rightThumbstickState{XR_TYPE_ACTION_STATE_VECTOR2F};\n''',
    'per-hand input globals')
input_cpp = rep(
    input_cpp,
    '''    boolState = GetActionStateBoolean(app, boolAction);\n    rightGripState = GetActionStateFloat(app, browserGripAction, rightHandPath);\n    rightThumbstickState = GetActionStateVector2f(app, browserThumbstickAction, rightHandPath);\n''',
    '''    boolState = GetActionStateBoolean(app, boolAction);\n    leftTriggerState = GetActionStateBoolean(app, boolAction, leftHandPath);\n    rightTriggerState = GetActionStateBoolean(app, boolAction, rightHandPath);\n    leftGripState = GetActionStateFloat(app, browserGripAction, leftHandPath);\n    rightGripState = GetActionStateFloat(app, browserGripAction, rightHandPath);\n    rightThumbstickState = GetActionStateVector2f(app, browserThumbstickAction, rightHandPath);\n''',
    'per-hand input sync')
input_cpp_path.write_text(input_cpp)

# ---------------------------------------------------------------------------
# Capture both aim poses, then let whichever hand has intent (trigger/grip)
# drive the browser. When idle, right is preferred for a stable single cursor.
# This keeps the proven single-pointer/resize state machine intact while making
# every operation available from either controller.
# ---------------------------------------------------------------------------
main_path = SRC / 'XrPassthroughOcclusion.cpp'
main = main_path.read_text()
old_aim = '''        XrPosef browserAimPose{};\n        browserAimPose.orientation.w = 1.0f;\n        bool browserAimActive = false;\n        if (rightControllerActive && rightControllerAimSpace != XR_NULL_HANDLE) {\n            XrSpaceLocation browserAimLocation{XR_TYPE_SPACE_LOCATION};\n            OXR(xrLocateSpace(\n                rightControllerAimSpace,\n                app.LocalSpace,\n                frameState.predictedDisplayTime,\n                &browserAimLocation));\n            const XrSpaceLocationFlags requiredFlags =\n                XR_SPACE_LOCATION_POSITION_VALID_BIT |\n                XR_SPACE_LOCATION_ORIENTATION_VALID_BIT;\n            if ((browserAimLocation.locationFlags & requiredFlags) == requiredFlags) {\n                browserAimPose = browserAimLocation.pose;\n                browserAimActive = true;\n            }\n        }\n\n'''
new_aim = '''        XrPosef leftBrowserAimPose{};\n        XrPosef rightBrowserAimPose{};\n        leftBrowserAimPose.orientation.w = 1.0f;\n        rightBrowserAimPose.orientation.w = 1.0f;\n        bool leftBrowserAimActive = false;\n        bool rightBrowserAimActive = false;\n        const XrSpaceLocationFlags requiredFlags =\n            XR_SPACE_LOCATION_POSITION_VALID_BIT |\n            XR_SPACE_LOCATION_ORIENTATION_VALID_BIT;\n\n        auto locateBrowserAim = [&](bool controllerActive, XrSpace aimSpace, XrPosef& pose, bool& active) {\n            if (!controllerActive || aimSpace == XR_NULL_HANDLE) return;\n            XrSpaceLocation location{XR_TYPE_SPACE_LOCATION};\n            OXR(xrLocateSpace(\n                aimSpace, app.LocalSpace, frameState.predictedDisplayTime, &location));\n            if ((location.locationFlags & requiredFlags) == requiredFlags) {\n                pose = location.pose;\n                active = true;\n            }\n        };\n        locateBrowserAim(leftControllerActive, leftControllerAimSpace, leftBrowserAimPose, leftBrowserAimActive);\n        locateBrowserAim(rightControllerActive, rightControllerAimSpace, rightBrowserAimPose, rightBrowserAimActive);\n\n'''
main = rep(main, old_aim, new_aim, 'dual aim capture')
old_feed = '''        nativeBrowser.HandleInput(\n            Env,\n            browserAimPose,\n            browserAimActive,\n            boolState.currentState == XR_TRUE,\n            rightGripState.currentState,\n            rightThumbstickState.currentState.y);\n'''
new_feed = '''        const bool leftIntent =\n            (leftTriggerState.currentState == XR_TRUE) || leftGripState.currentState > 0.15f;\n        const bool rightIntent =\n            (rightTriggerState.currentState == XR_TRUE) || rightGripState.currentState > 0.15f;\n        const bool useLeftHand = leftIntent || (!rightIntent && !rightBrowserAimActive && leftBrowserAimActive);\n        nativeBrowser.HandleInput(\n            Env,\n            useLeftHand ? leftBrowserAimPose : rightBrowserAimPose,\n            useLeftHand ? leftBrowserAimActive : rightBrowserAimActive,\n            useLeftHand ? (leftTriggerState.currentState == XR_TRUE)\n                        : (rightTriggerState.currentState == XR_TRUE),\n            useLeftHand ? leftGripState.currentState : rightGripState.currentState,\n            useLeftHand ? 0.0f : rightThumbstickState.currentState.y);\n'''
main = rep(main, old_feed, new_feed, 'dual hand input selection')
main_path.write_text(main)

# ---------------------------------------------------------------------------
# Android capture safe area. Hardware proved the Presentation content extends
# beyond the region captured by the producer on the right. Keep the producer
# fixed, but place the browser inside a symmetric 84% safe rectangle and sample
# exactly that rectangle into the XR quad. 2688x1512 at 3200x1800 remains far
# above the angular resolution needed for a sharp compositor layer.
# ---------------------------------------------------------------------------
bridge_path = JAVA / 'QuestDepthBrowserBridge.java'
bridge = bridge_path.read_text()
bridge = rep(
    bridge,
    'import android.view.inputmethod.InputConnection;\n',
    'import android.view.inputmethod.InputConnection;\nimport android.view.inputmethod.InputMethodManager;\n',
    'InputMethodManager import')
old_aspect = '''    public static void setWindowAspect(final float requestedAspect) {\n        MAIN.post(() -> {\n            if (contentFrame == null || surfaceWidth <= 0 || surfaceHeight <= 0) return;\n            float aspect = Math.max(0.55f, Math.min(3.20f, requestedAspect));\n            float backingAspect = (float) surfaceWidth / (float) surfaceHeight;\n\n            int width;\n            int height;\n            if (aspect >= backingAspect) {\n                width = surfaceWidth;\n                height = Math.max(1, Math.round(surfaceWidth / aspect));\n            } else {\n                height = surfaceHeight;\n                width = Math.max(1, Math.round(surfaceHeight * aspect));\n            }\n\n            FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(\n                    width, height, Gravity.CENTER);\n'''
new_aspect = '''    public static void setWindowAspect(final float requestedAspect) {\n        MAIN.post(() -> {\n            if (contentFrame == null || surfaceWidth <= 0 || surfaceHeight <= 0) return;\n            float aspect = Math.max(0.55f, Math.min(3.20f, requestedAspect));\n            final float safeScale = 0.84f;\n            int safeWidth = Math.max(1, Math.round(surfaceWidth * safeScale));\n            int safeHeight = Math.max(1, Math.round(surfaceHeight * safeScale));\n            float safeAspect = (float) safeWidth / (float) safeHeight;\n\n            int width;\n            int height;\n            if (aspect >= safeAspect) {\n                width = safeWidth;\n                height = Math.max(1, Math.round(safeWidth / aspect));\n            } else {\n                height = safeHeight;\n                width = Math.max(1, Math.round(safeHeight * aspect));\n            }\n\n            FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(\n                    width, height, Gravity.CENTER);\n'''
bridge = rep(bridge, old_aspect, new_aspect, 'safe browser viewport')

# Explicit Quest/Android IME request after clicks on editable controls.
helper_anchor = '    private static View currentInputTarget() {'
ime_helpers = '''    private static void showQuestKeyboard(final View target) {\n        if (target == null) return;\n        try {\n            target.setFocusable(true);\n            target.setFocusableInTouchMode(true);\n            target.requestFocus();\n            if (presentation != null && presentation.getWindow() != null) {\n                presentation.getWindow().setSoftInputMode(\n                        WindowManager.LayoutParams.SOFT_INPUT_ADJUST_NOTHING |\n                        WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_VISIBLE);\n            }\n            MAIN.postDelayed(() -> {\n                try {\n                    InputMethodManager imm = (InputMethodManager)\n                            target.getContext().getSystemService(Context.INPUT_METHOD_SERVICE);\n                    if (imm != null) {\n                        imm.restartInput(target);\n                        imm.showSoftInput(target, InputMethodManager.SHOW_IMPLICIT);\n                    }\n                } catch (Throwable ignored) {}\n            }, 90);\n        } catch (Throwable ignored) {}\n    }\n\n    private static void maybeShowKeyboardForFocusedInput() {\n        if (addressBar != null && addressBar.hasFocus()) {\n            showQuestKeyboard(addressBar);\n            return;\n        }\n        if (webView == null) return;\n        webView.evaluateJavascript(\n                \"(function(){var e=document.activeElement;if(!e)return false;\" +\n                \"var t=(e.tagName||'').toLowerCase();\" +\n                \"var ty=(e.type||'').toLowerCase();\" +\n                \"return t==='textarea'||e.isContentEditable||(t==='input'&&\" +\n                \"ty!=='button'&&ty!=='submit'&&ty!=='checkbox'&&ty!=='radio'&&ty!=='range'&&ty!=='color');})()\",\n                value -> {\n                    if (\"true\".equals(value)) showQuestKeyboard(webView);\n                });\n    }\n\n''' + helper_anchor
bridge = rep(bridge, helper_anchor, ime_helpers, 'IME helpers')
bridge = rep(
    bridge,
    '''                contentFrame.dispatchTouchEvent(touch);\n                touch.recycle();\n                if (action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL) {\n                    pointerDownTime = 0;\n                }\n''',
    '''                contentFrame.dispatchTouchEvent(touch);\n                touch.recycle();\n                if (action == MotionEvent.ACTION_UP) {\n                    MAIN.postDelayed(QuestDepthBrowserBridge::maybeShowKeyboardForFocusedInput, 45);\n                }\n                if (action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL) {\n                    pointerDownTime = 0;\n                }\n''',
    'keyboard after pointer click')
bridge = rep(
    bridge,
    '''        addressBar.setOnEditorActionListener((v, actionId, event) -> {\n            navigate();\n            return true;\n        });\n''',
    '''        addressBar.setOnEditorActionListener((v, actionId, event) -> {\n            navigate();\n            return true;\n        });\n        addressBar.setOnFocusChangeListener((v, hasFocus) -> {\n            if (hasFocus) showQuestKeyboard(addressBar);\n        });\n''',
    'address bar IME focus')
bridge_path.write_text(bridge)

# Native sampler must use the same 84% safe producer rectangle as Java.
cpp_path = SRC / 'QuestDepthBrowserNative.cpp'
cpp = cpp_path.read_text()
old_rect = '''    // v0.2.5: fixed producer surface + centered Android viewport. The Java\n    // contentFrame uses the exact same aspect-fit math, so sample that region\n    // once and stretch it across the XR quad. SurfaceTexture itself never\n    // changes size after creation.\n    const float panelAspect = PanelWidthMeters / std::max(PanelHeightMeters, 0.001f);\n    const float backingAspect = static_cast<float>(TextureWidth) /\n        std::max(static_cast<float>(TextureHeight), 1.0f);\n    float contentOffsetX = 0.0f;\n    float contentOffsetY = 0.0f;\n    float contentScaleX = 1.0f;\n    float contentScaleY = 1.0f;\n    if (panelAspect >= backingAspect) {\n        contentScaleY = backingAspect / panelAspect;\n        contentOffsetY = (1.0f - contentScaleY) * 0.5f;\n    } else {\n        contentScaleX = panelAspect / backingAspect;\n        contentOffsetX = (1.0f - contentScaleX) * 0.5f;\n    }\n'''
new_rect = '''    // v0.2.6: match Java's centered 84% capture-safe viewport. This avoids\n    // the Presentation/BufferQueue edge region that hardware testing showed\n    // was clipped on the right while keeping a ~2.7K browser source.\n    const float panelAspect = PanelWidthMeters / std::max(PanelHeightMeters, 0.001f);\n    const float backingAspect = static_cast<float>(TextureWidth) /\n        std::max(static_cast<float>(TextureHeight), 1.0f);\n    constexpr float safeScale = 0.84f;\n    const float safeAspect = backingAspect; // symmetric X/Y safe scaling\n    float contentScaleX = safeScale;\n    float contentScaleY = safeScale;\n    if (panelAspect >= safeAspect) {\n        contentScaleY = safeScale * safeAspect / panelAspect;\n    } else {\n        contentScaleX = safeScale * panelAspect / safeAspect;\n    }\n    const float contentOffsetX = (1.0f - contentScaleX) * 0.5f;\n    const float contentOffsetY = (1.0f - contentScaleY) * 0.5f;\n'''
cpp = rep(cpp, old_rect, new_rect, 'native safe viewport rect')
cpp_path.write_text(cpp)

print('Quest Depth Browser Native v0.2.6 patch applied')
print('Both controllers: trigger/grip browser ownership')
print('Browser capture: centered 84% safe viewport (~2688x1512 at 16:9)')
print('Quest IME: explicit showSoftInput for address bar + HTML editable fields')
print('Corner resize / grab / DE-QWERTZ / Environment Depth preserved')
