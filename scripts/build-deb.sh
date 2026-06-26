#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTROL="$ROOT/packaging/debian/control"
VERSION="$(awk -F': ' '/^Version:/ {print $2; exit}' "$CONTROL")"
DIST="$ROOT/dist"
BUILD="$ROOT/build"
PKGROOT="$BUILD/pkgroot"

rm -rf "$PKGROOT"
mkdir -p \
  "$PKGROOT/DEBIAN" \
  "$PKGROOT/usr/bin" \
  "$PKGROOT/usr/lib/calamus" \
  "$PKGROOT/usr/share/calamus/tests" \
  "$PKGROOT/usr/share/applications" \
  "$PKGROOT/usr/share/pixmaps" \
  "$PKGROOT/usr/share/doc/calamus" \
  "$DIST"

cp -a "$CONTROL" "$PKGROOT/DEBIAN/control"
cp -a "$ROOT/bin/calamus" "$ROOT/bin/calamus-selftest" "$PKGROOT/usr/bin/"
chmod 0755 "$PKGROOT/usr/bin/calamus" "$PKGROOT/usr/bin/calamus-selftest"
cp -a "$ROOT/calamus/"*.py "$PKGROOT/usr/lib/calamus/"
cp -a "$ROOT/tests/"*.py "$PKGROOT/usr/share/calamus/tests/"
cp -a "$ROOT/share/applications/calamus.desktop" "$PKGROOT/usr/share/applications/"
cp -a "$ROOT/share/pixmaps/calamus.png" "$PKGROOT/usr/share/pixmaps/"
cp -a "$ROOT/share/doc/calamus/." "$PKGROOT/usr/share/doc/calamus/"

find "$PKGROOT" -type d -name "__pycache__" -prune -exec rm -rf {} +
find "$PKGROOT" -type f -name "*.pyc" -delete

dpkg-deb --build --root-owner-group "$PKGROOT" "$DIST/calamus_${VERSION}_all.deb"
echo "Built: $DIST/calamus_${VERSION}_all.deb"
