from pathlib import Path

ROOT = Path('meta-openxr-sdk/Samples/XrSamples/XrPassthroughOcclusion')
SRC = ROOT / 'Src'
ANDROID = ROOT / 'Projects/Android'


def rep(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f'v0.2.7 anchor missing: {label}')
    return text.replace(old, new, 1)

# Version bump only. This is a surgical crash hotfix on top of v0.2.6.
gradle_path = ANDROID / 'build.gradle'
gradle = gradle_path.read_text()
gradle = rep(gradle, 'versionCode 26', 'versionCode 27', 'Gradle versionCode')
gradle = rep(gradle, 'versionName "0.2.6"', 'versionName "0.2.7"', 'Gradle versionName')
gradle_path.write_text(gradle)

manifest_path = ANDROID / 'AndroidManifest.xml'
manifest = manifest_path.read_text()
manifest = rep(manifest, 'android:versionCode="26"', 'android:versionCode="27"', 'manifest versionCode')
manifest = rep(manifest, 'android:versionName="0.2.6"', 'android:versionName="0.2.7"', 'manifest versionName')
manifest_path.write_text(manifest)

# v0.2.6 started querying boolAction with leftHandPath/rightHandPath, but the
# original Meta sample created boolAction WITHOUT subaction paths. OpenXR can
# reject xrGetActionStateBoolean for an unsupported subaction path at runtime.
# Create the same trigger action with both hand subaction paths instead.
input_cpp_path = SRC / 'XrPassthroughOcclusionInput.cpp'
text = input_cpp_path.read_text()
text = rep(
    text,
    '    boolAction = CreateAction(runningActionSet, XR_ACTION_TYPE_BOOLEAN_INPUT, "toggle", "Toggle");\n\n    OXR(xrStringToPath(app.Instance, "/user/hand/left", &leftHandPath));',
    '    // v0.2.7: create boolAction after hand paths exist so per-hand trigger queries are legal.\n\n    OXR(xrStringToPath(app.Instance, "/user/hand/left", &leftHandPath));',
    'defer boolAction creation')
text = rep(
    text,
    '    XrPath handSubactionPaths[2] = {leftHandPath, rightHandPath};\n\n    browserGripAction = CreateAction(',
    '    XrPath handSubactionPaths[2] = {leftHandPath, rightHandPath};\n\n    boolAction = CreateAction(\n        runningActionSet,\n        XR_ACTION_TYPE_BOOLEAN_INPUT,\n        "toggle",\n        "Toggle",\n        2,\n        handSubactionPaths);\n\n    browserGripAction = CreateAction(',
    'per-hand boolAction creation')
input_cpp_path.write_text(text)

print('Quest Depth Browser Native v0.2.7 crash hotfix applied')
print('boolAction subaction paths: LEFT + RIGHT')
print('Per-hand xrGetActionStateBoolean queries are now valid')
print('v0.2.6 geometry, IME, QWERTZ and renderer otherwise unchanged')
