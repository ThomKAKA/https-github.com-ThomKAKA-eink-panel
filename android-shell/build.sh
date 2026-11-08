#!/usr/bin/env bash
# Build the minimal E-Ink WebView shell without Gradle.
# Requires a JDK 17 and the Android SDK command-line tools; see docs/P6-WEBVIEW-SHELL.md.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
TOOLCHAIN="${ANDROID_TOOLCHAIN:-D:/Codex/android-toolchain}"
SDK="${ANDROID_SDK_ROOT:-$TOOLCHAIN/sdk}"
JDK="${JAVA_HOME:-$(ls -d "$TOOLCHAIN"/jdk-* | head -1)}"
BT="$SDK/build-tools/34.0.0"
PLATFORM="$SDK/platforms/android-34/android.jar"
OUT="${OUT:-$TOOLCHAIN/build}"
CLASSES="$OUT/classes"
DEX="$OUT/dex"

for path in "$JDK/bin/javac.exe" "$BT/aapt2.exe" "$BT/d8.bat" "$BT/zipalign.exe" \
            "$BT/apksigner.bat" "$PLATFORM"; do
  [ -e "$path" ] || { echo "Missing: $path" >&2; exit 1; }
done

rm -rf "$CLASSES" "$DEX" "$OUT/eink-shell.apk"
mkdir -p "$CLASSES" "$DEX" "$OUT"

"$JDK/bin/javac.exe" -encoding UTF-8 --release 11 -classpath "$PLATFORM" \
  -d "$CLASSES" "$HERE/src/com/eink/shell/MainActivity.java"

"$BT/d8.bat" --lib "$PLATFORM" --output "$DEX" \
  "$CLASSES/com/eink/shell/MainActivity.class"

"$BT/aapt2.exe" link -o "$OUT/base.apk" --manifest "$HERE/AndroidManifest.xml" \
  -I "$PLATFORM" --min-sdk-version 24 --target-sdk-version 34 \
  --version-code 1 --version-name 1.0

"$JDK/bin/jar.exe" uf "$OUT/base.apk" -C "$DEX" classes.dex

"$BT/zipalign.exe" -f 4 "$OUT/base.apk" "$OUT/aligned.apk"

KEYSTORE="$OUT/debug.keystore"
if [ ! -f "$KEYSTORE" ]; then
  "$JDK/bin/keytool.exe" -genkeypair -keystore "$KEYSTORE" -storepass android \
    -keypass android -alias androiddebugkey -keyalg RSA -keysize 2048 \
    -validity 10000 -dname "CN=Android Debug,O=Android,C=US"
fi

"$BT/apksigner.bat" sign --ks "$KEYSTORE" --ks-pass pass:android \
  --key-pass pass:android --out "$OUT/eink-shell.apk" "$OUT/aligned.apk"
"$BT/apksigner.bat" verify --verbose "$OUT/eink-shell.apk"

echo "APK: $OUT/eink-shell.apk"
sha256sum "$OUT/eink-shell.apk"
