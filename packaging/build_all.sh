#!/usr/bin/env bash
set -e

# Change directory to the repository root
SCRIPT_DIR="$(dirname "$(readlink -f "${0}")")"
cd "$SCRIPT_DIR/.."

echo "========================================================"
echo "🌟 Starting Master Build Script: Compiling All Packages 🌟"
echo "========================================================"

# 1. Clean previous build outputs
echo "1. Cleaning up previous build outputs in dist/..."
rm -f dist/*.deb dist/*.flatpak dist/*.AppImage
echo "   - Cleanup complete."
echo ""

# 2. Build Debian package
echo "2. Compiling Debian Package (.deb)..."
./packaging/deb/build_deb.sh
echo ""

# 3. Build Flatpak package
echo "3. Compiling Flatpak Package (.flatpak)..."
./packaging/flatpak/build_flatpak.sh
echo ""

# 4. Build AppImage package
echo "4. Compiling AppImage Package (.AppImage)..."
./packaging/appimage/build_appimage.sh
echo ""

# 5. Output summary
echo "========================================================"
echo "🎉 Build Process Completed Successfully! 🎉"
echo "========================================================"
echo "The following packages are ready for distribution in dist/:"
ls -lh dist/ | grep -E "(\.deb|\.flatpak|\.AppImage)"
echo "========================================================"
