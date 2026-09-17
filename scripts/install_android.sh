#!/usr/bin/env bash
set -e
set +o pipefail
yes | sdkmanager --licenses >/dev/null
yes | sdkmanager --install \
  'platform-tools' \
  'platforms;android-32' \
  'build-tools;34.0.0' \
  'ndk;27.0.12077973' \
  'cmake;3.22.1'
set -o pipefail

echo '--- Installed tool versions ---'
sdkmanager --version
java -version
"$ANDROID_HOME/ndk/27.0.12077973/ndk-build" --version || true
"$ANDROID_HOME/cmake/3.22.1/bin/cmake" --version
