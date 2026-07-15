# Packaging Guide: Flatpak & AppImage on a Clean Machine

This guide describes the step-by-step instructions to install build dependencies and generate compiled packages of **Procedure** (`Procedure.flatpak` and `Procedure-x86_64.AppImage`) starting from a "clean/virgin" Linux installation (e.g., a fresh Ubuntu 24.04 LTS or Debian 12 install).

All packaging processes are configured to isolate temporary build files within their respective subfolders and place the final packages inside the `dist/` folder at the project root.

---

## 1. How to Compile the Flatpak Package

Flatpak is the recommended distribution format. It isolates the application inside a secure sandbox while granting access to advanced graphical libraries, the GPU, network sockets, and the host system keyring (**GNOME Keyring**).

### Step 1: Install flatpak and flatpak-builder
Open a terminal on the clean machine and run:
```bash
sudo apt update
sudo apt install -y flatpak flatpak-builder
```

### Step 2: Enable the Flathub Repository
Enable Flathub at the user level to allow downloading runtimes and SDKs:
```bash
flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
```

### Step 3: Run the Build Script
Run the script from the project root. The script will automatically check, download, and install the **GNOME 50** runtime and SDK if they are not already present on the system, and then compile and export the portable package:
```bash
# Navigate to the project directory
cd /home/user/Projects/Procedure

# Run the compilation script
./packaging/flatpak/build_flatpak.sh
```

### Step 4: Verification and Local Execution
At the end of the process, the application will be installed in the local user environment. You can start it via:
```bash
flatpak run io.github.albeph.Procedure
```

The standalone portable bundle ready to be copied and installed on other computers is located at:
👉 `dist/Procedure.flatpak`

To install it on a target machine:
```bash
flatpak install --user dist/Procedure.flatpak
```

---

## 2. How to Compile the Self-Contained AppImage Package

The AppImage bundles all the necessary dynamic libraries (including GTK, WebKitGTK, and libsecret) to allow the application to launch on any other recent Linux distribution, even if it lacks GNOME libraries.

### Step 1: Install System Prerequisites and appimage-builder
On a clean machine, install the packages required for compiling and managing compressed images:
```bash
sudo apt update
sudo apt install -y python3-pip python3-pil patchelf desktop-file-utils appstream squashfs-tools fakeroot fakechroot
```

Next, install `appimage-builder` via the Python package manager:
```bash
pip3 install --break-system-packages appimage-builder
```

*(Note: If the distribution prohibits the use of `--break-system-packages`, you can install it using `pipx` or inside a virtual environment).*

### Step 2: Run the AppImage Compilation Script
Start the script from the project root:
```bash
# Run the compilation script
./packaging/appimage/build_appimage.sh
```

This script will:
1. Create a temporary `AppDir` folder and copy the application source files into it.
2. Use `appimage-builder` to automatically download the necessary native libraries in an isolated environment (`packaging/appimage/appimage-build/`).
3. Generate and export the final standalone executable into the `dist/` folder.

### Step 3: Verification and Execution
You can find the final compiled executable at:
👉 `dist/Procedure-x86_64.AppImage`

Make it executable and run it:
```bash
chmod +x dist/Procedure-x86_64.AppImage
./dist/Procedure-x86_64.AppImage
```

---

## 💡 Troubleshooting Common Issues on Clean Machines

*   **Icons or SVG images not displayed (AppImage)**: 
    Procedure integrates a smart launcher that dynamically regenerates the `loaders.cache` at startup on any host machine. This ensures correct rendering of the graphic navigation icons even if the host computer's library paths do not match the compilation environment.
*   **White screen on startup**:
    WebKitGTK requires accelerated graphics drivers. If you run the app inside a virtual machine without 3D acceleration enabled, verify that acceleration is supported, or launch the application with `./app/procedure --verbose` to view error logs.
