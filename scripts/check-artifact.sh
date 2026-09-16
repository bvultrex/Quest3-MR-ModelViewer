#!/usr/bin/env bash
set -euo pipefail
APK=${1:-Quest3-MR-ModelViewer-v0.1-debug.apk}
sha256sum "$APK"
file "$APK"
