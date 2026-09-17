#!/usr/bin/env bash
set -euo pipefail
: "${APP_VERSION:?APP_VERSION is required}"
: "${APP_ID:?APP_ID is required}"
: "${APP_LABEL:?APP_LABEL is required}"
ROOT='meta-openxr-sdk/Samples/XrSamples/XrPassthroughOcclusion/Projects/Android'
RES='meta-openxr-sdk/Samples/XrSamples/XrPassthroughOcclusion/res'
ICON="$RES/mipmap-xxxhdpi/questmr_icon.png"

python3 scripts/generate_icon.py "$ICON"

python3 - "$ROOT/build.gradle" "$ROOT/AndroidManifest.xml" <<'PY'
from pathlib import Path
import os, sys
build_gradle = Path(sys.argv[1])
manifest = Path(sys.argv[2])
app_id = os.environ['APP_ID']
version = os.environ['APP_VERSION']
label = os.environ['APP_LABEL']

gradle = build_gradle.read_text()
gradle = gradle.replace('applicationId "com.oculus.xrpassthroughocclusion"', f'applicationId "{app_id}"', 1)
gradle = gradle.replace('versionName "1.0"', f'versionName "{version}"', 1)
build_gradle.write_text(gradle)

xml = manifest.read_text()
xml = xml.replace(
    '      android:label="xrpassthroughocclusion"\n      >',
    f'      android:label="{label}"\n'
    '      android:icon="@mipmap/questmr_icon"\n'
    '      android:roundIcon="@mipmap/questmr_icon"\n'
    '      >',
    1,
)

# Horizon OS may surface the currently running Activity/task label rather than
# only the application label. Give both VR activities explicit identity so the
# universal menu never falls back to "App name unavailable".
for activity in (
    'com.oculus.xrpassthroughocclusion.MainActivity',
    'com.oculus.xrpassthroughocclusion.MainNativeActivity',
):
    needle = f'        android:name="{activity}"\n        android:theme='
    replacement = (
        f'        android:name="{activity}"\n'
        f'        android:label="{label}"\n'
        '        android:icon="@mipmap/questmr_icon"\n'
        '        android:theme='
    )
    if needle not in xml:
        raise SystemExit(f'Activity branding anchor not found: {activity}')
    xml = xml.replace(needle, replacement, 1)

manifest.write_text(xml)
PY

echo '--- Branding check ---'
grep -nE 'applicationId|versionName' "$ROOT/build.gradle"
grep -nE 'android:label|android:icon|android:roundIcon' "$ROOT/AndroidManifest.xml"
test -s "$ICON"
file "$ICON"
