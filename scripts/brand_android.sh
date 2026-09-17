#!/usr/bin/env bash
set -euo pipefail
: "${APP_VERSION:?APP_VERSION is required}"
: "${APP_ID:?APP_ID is required}"
: "${APP_LABEL:?APP_LABEL is required}"
ROOT='meta-openxr-sdk/Samples/XrSamples/XrPassthroughOcclusion/Projects/Android'

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
xml = xml.replace('android:label="xrpassthroughocclusion"', f'android:label="{label}"', 1)
manifest.write_text(xml)
PY

echo '--- Branding check ---'
grep -nE 'applicationId|versionName' "$ROOT/build.gradle"
grep -n 'android:label' "$ROOT/AndroidManifest.xml"
