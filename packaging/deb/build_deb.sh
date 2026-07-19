#!/usr/bin/env bash
set -e

# Change directory to the repository root
SCRIPT_DIR="$(dirname "$(readlink -f "${0}")")"
cd "$SCRIPT_DIR/../.."

echo "=== Packaging: Generating Debian (.deb) Package ==="

# 1. Retrieve the version dynamically from config.py
VERSION=$(python3 -c "import sys; sys.path.insert(0, 'app/src'); from config import VERSION; print(VERSION)")
echo "Detected Version: $VERSION"

# 2. Setup directory paths
BUILD_DIR="packaging/deb/deb-build"
DEB_PACKAGE_NAME="io.github.albeph.procedure"
DIST_DIR="dist"
DEBIAN_DIR="$BUILD_DIR/DEBIAN"

# Clean up previous builds
rm -rf "$BUILD_DIR"
mkdir -p "$DIST_DIR"

# 3. Create file structure
echo "Creating Debian package structure..."
mkdir -p "$DEBIAN_DIR"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$BUILD_DIR/usr/share/applications"
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/512x512/apps"
mkdir -p "$BUILD_DIR/usr/share/procedure"

# 4. Copy source code files and resources
echo "Copying source files..."
cp -r app/src "$BUILD_DIR/usr/share/procedure/src"
cp -r app/resources "$BUILD_DIR/usr/share/procedure/resources"

# Copy launcher to /usr/bin/procedure
cp app/procedure "$BUILD_DIR/usr/bin/procedure"
chmod 755 "$BUILD_DIR/usr/bin/procedure"

# Copy desktop file to /usr/share/applications
# Ensure it points to system-wide Exec command
cp app/io.github.albeph.Procedure.desktop "$BUILD_DIR/usr/share/applications/io.github.albeph.Procedure.desktop"
chmod 644 "$BUILD_DIR/usr/share/applications/io.github.albeph.Procedure.desktop"

# Copy application icon
cp app/resources/icon.png "$BUILD_DIR/usr/share/icons/hicolor/512x512/apps/io.github.albeph.Procedure.png"
chmod 644 "$BUILD_DIR/usr/share/icons/hicolor/512x512/apps/io.github.albeph.Procedure.png"

# 5. Create Debian control file
echo "Writing DEBIAN/control..."
cat <<EOF > "$DEBIAN_DIR/control"
Package: $DEB_PACKAGE_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-gi, python3-pil, gir1.2-webkit-6.0, gir1.2-adw-1, libsecret-1-0
Maintainer: Albeph <albeph@github.io>
Description: Native GTK4 desktop client wrapper for Notion.
 A minimal, fast, and secure desktop client wrapper for Notion with zero disk cache footprint.
 Features multi-tab support, local Keyring encryption, and automatic theme syncing.
EOF

# 6. Create post-installation and post-removal scripts
echo "Writing DEBIAN/postinst..."
cat <<'EOF' > "$DEBIAN_DIR/postinst"
#!/bin/sh
set -e
if [ "$1" = "configure" ]; then
    echo "Updating desktop and icon database caches..."
    update-desktop-database /usr/share/applications || true
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true
fi
EOF
chmod 755 "$DEBIAN_DIR/postinst"

echo "Writing DEBIAN/postrm..."
cat <<'EOF' > "$DEBIAN_DIR/postrm"
#!/bin/sh
set -e
if [ "$1" = "remove" ] || [ "$1" = "purge" ]; then
    echo "Cleaning up desktop and icon database caches..."
    update-desktop-database /usr/share/applications || true
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true
fi
EOF
chmod 755 "$DEBIAN_DIR/postrm"

# 7. Build the package
DEB_FILE_NAME="${DEB_PACKAGE_NAME}_${VERSION}_all.deb"
echo "Building package using dpkg-deb..."
dpkg-deb --root-owner-group --build "$BUILD_DIR" "$DIST_DIR/$DEB_FILE_NAME"

# Clean up build directory
rm -rf "$BUILD_DIR"

echo "--------------------------------------------------------"
echo "🎉 Success! Debian package created and located at:"
echo "👉 $DIST_DIR/$DEB_FILE_NAME"
echo "--------------------------------------------------------"
echo "You can install it on your Debian/Ubuntu machine using:"
echo "👉 sudo apt install ./$DIST_DIR/$DEB_FILE_NAME"
echo "--------------------------------------------------------"
