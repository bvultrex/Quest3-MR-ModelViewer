#!/usr/bin/env bash
set -euo pipefail
: "${APP_VERSION:?APP_VERSION is required}"
: "${APP_ID:?APP_ID is required}"
: "${APP_LABEL:?APP_LABEL is required}"
mkdir -p dist
ROOT='meta-openxr-sdk/Samples/XrSamples/XrPassthroughOcclusion/Projects/Android'
APK=$(find "$ROOT" -type f -path '*/build/outputs/apk/*' -name '*debug.apk' | head -n 1)

if [ -z "${APK:-}" ]; then
  echo 'No debug APK found' >&2
  find "$ROOT" -maxdepth 8 -type f | sort | tail -n 200
  exit 1
fi

OUT="dist/Quest3-MR-ModelViewer-v${APP_VERSION}-debug.apk"
cp "$APK" "$OUT"

echo '--- APK signature ---'
"$ANDROID_HOME/build-tools/34.0.0/apksigner" verify --verbose --print-certs "$OUT"

echo '--- APK package / launch metadata ---'
"$ANDROID_HOME/build-tools/34.0.0/aapt2" dump badging "$OUT" | tee dist/APK-BADGING.txt

grep -q "package: name='${APP_ID}'" dist/APK-BADGING.txt
grep -Fq "application: label='${APP_LABEL}'" dist/APK-BADGING.txt
cp scripts/CONTROLS.txt dist/CONTROLS.txt
(cd dist && sha256sum "Quest3-MR-ModelViewer-v${APP_VERSION}-debug.apk" > SHA256SUMS.txt)
ls -lh dist
