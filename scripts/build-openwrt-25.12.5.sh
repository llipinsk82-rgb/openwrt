#!/bin/sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
VERSION="25.12.5"
TARGET="ath79-generic"
SDK_ARCHIVE="openwrt-sdk-25.12.5-ath79-generic_gcc-14.3.0_musl.Linux-x86_64.tar.zst"
SDK_SHA256="bc4307ae2065c0c0b7c84627356e9f3d368a5a803c81552fcb77aa034a843f5a"
SDK_URL="https://downloads.openwrt.org/releases/${VERSION}/targets/ath79/generic/${SDK_ARCHIVE}"
BUILD_BASE="${BUILD_BASE:-$ROOT/.build/openwrt-${VERSION}-${TARGET}}"
CACHE_DIR="$ROOT/.build/cache"
ARCHIVE="$CACHE_DIR/$SDK_ARCHIVE"
SDK_DIR="$BUILD_BASE/sdk"
STAGE_DIR="$SDK_DIR/package/archer-custom"
DIST_DIR="$ROOT/dist"

mkdir -p "$CACHE_DIR" "$BUILD_BASE" "$DIST_DIR"

if [ ! -f "$ARCHIVE" ]; then
    wget -O "$ARCHIVE.part" "$SDK_URL"
    mv "$ARCHIVE.part" "$ARCHIVE"
fi

printf '%s  %s\n' "$SDK_SHA256" "$ARCHIVE" | sha256sum -c -

if [ ! -d "$SDK_DIR" ]; then
    EXTRACT_DIR="$BUILD_BASE/extract"
    rm -rf "$EXTRACT_DIR"
    mkdir -p "$EXTRACT_DIR"
    tar --zstd -xf "$ARCHIVE" -C "$EXTRACT_DIR"
    EXTRACTED="$(find "$EXTRACT_DIR" -mindepth 1 -maxdepth 1 -type d -name 'openwrt-sdk-*' | head -n 1)"
    [ -n "$EXTRACTED" ] || { echo "SDK extraction failed" >&2; exit 1; }
    mv "$EXTRACTED" "$SDK_DIR"
    rm -rf "$EXTRACT_DIR"
fi

cd "$SDK_DIR"

rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR"
ln -s "$ROOT/luci-theme-archer" "$STAGE_DIR/luci-theme-archer"
ln -s "$ROOT/luci-app-archer-dashboard" "$STAGE_DIR/luci-app-archer-dashboard"

make defconfig
make package/luci-theme-archer/compile V=sc
make package/luci-app-archer-dashboard/compile V=sc

THEME_APK="$(find bin/packages -type f -name 'luci-theme-archer*.apk' | head -n 1)"
DASH_APK="$(find bin/packages -type f -name 'luci-app-archer-dashboard*.apk' | head -n 1)"
[ -n "$THEME_APK" ] && [ -n "$DASH_APK" ] || { echo "Expected *.apk artifacts not found" >&2; exit 1; }

rm -f "$DIST_DIR"/luci-theme-archer*.apk "$DIST_DIR"/luci-app-archer-dashboard*.apk
cp "$THEME_APK" "$DASH_APK" "$DIST_DIR/"
sha256sum "$DIST_DIR"/*.apk > "$DIST_DIR/SHA256SUMS"

RUNTIME_BYTES="$(find "$ROOT/luci-theme-archer/htdocs" "$ROOT/luci-theme-archer/root" "$ROOT/luci-theme-archer/ucode" "$ROOT/luci-app-archer-dashboard/htdocs" "$ROOT/luci-app-archer-dashboard/root" -type f -printf '%s\n' | awk '{s+=$1} END {print s+0}')"
COMPRESSED_BYTES="$(find "$DIST_DIR" -maxdepth 1 -type f -name '*.apk' -printf '%s\n' | awk '{s+=$1} END {print s+0}')"

printf 'OpenWrt: %s\nTarget: %s\nRuntime payload bytes: %s\nAPK bytes: %s\n' "$VERSION" "$TARGET" "$RUNTIME_BYTES" "$COMPRESSED_BYTES" > "$DIST_DIR/BUILD-METRICS.txt"

if [ "$RUNTIME_BYTES" -ge 1000000 ]; then
    echo "Runtime payload exceeds 1,000,000 byte hard limit: $RUNTIME_BYTES" >&2
    exit 2
fi

printf 'Built packages:\n'
find "$DIST_DIR" -maxdepth 1 -type f -name '*.apk' -printf '  %f  %s bytes\n'
printf 'Runtime payload: %s bytes\n' "$RUNTIME_BYTES"
