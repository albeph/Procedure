# Procedure <img src="app/resources/icon.png" align="right" width="128" height="128" />

**Procedure** is a native, independent desktop client for Linux systems, specifically designed to integrate with the **GNOME** desktop environment following the **GNOME HIG (Human Interface Guidelines)**. It acts as a minimal, fast, and secure wrapper for the Notion web service, offering a lightweight alternative to Electron focused on data privacy.

The application is identified on the system by the App ID: `io.github.albeph.Procedure`.

---

## 🚀 Key Features

*   **Native GTK4 & Libadwaita Integration**: Developed in Python and native GNOME system libraries to guarantee smooth animations, responsive layouts, and a visual appearance consistent with the host system.
*   **WebKitGTK 6.0 Engine**: Uses the native system rendering engine instead of Chromium/Electron, drastically reducing RAM and CPU utilization.
*   **Multi-Tab Navigation**:
    *   Advanced tab management using native top bars (`Adw.TabBar` and `Adw.TabView`).
    *   Open new tabs by duplicating the current URL using the `+` button or keyboard shortcuts.
    *   Independent navigation history (Back/Forward) for each tab.
*   **Advanced "Zero-Footprint" Security on Disk**:
    *   **GNOME Keyring (`libsecret`)**: Session cookies are never written in cleartext or encrypted on the hard drive. They reside solely in the WebKit RAM memory and are directly synchronized with the system's secure keyring.
    *   **RAM-disk Cache (`tmpfs`)**: Local temporary databases (IndexedDB, LocalStorage) are stored in the volatile folder `/run/user/<UID>/procedure/`, loaded entirely in a RAM-disk.
    *   **Secure Shredding**: Upon exiting the app or logging out, all volatile data is overwritten with zero bytes (`\x00`) before physical deletion to prevent forensic data recovery.
    *   **Strict Permissions**: Local configuration folders are locked with `0700` permissions (exclusive access to the owner).
*   **Automatic Theme Synchronization**: Detects GNOME color scheme preference changes (Light/Dark) via `Adw.StyleManager` and dynamically injects CSS and JavaScript to force the matching theme inside the Notion web page.
*   **Custom Icon Selection**: Allows changing the default geometric "P" icon by loading any local PNG file from the user interface. The application will resize the image to `512x512` pixels and place it in the standard user icon path.
*   **Quick Keyboard Shortcuts**:
    *   `Ctrl + T`: New tab
    *   `Ctrl + W`: Close active tab
    *   `Ctrl + Tab`: Next tab
    *   `Ctrl + Shift + Tab`: Previous tab
    *   `Ctrl + R` or `F5`: Reload active page

---

## 🔒 Security Model

Procedure implements a strict logical and technical separation to protect both your account integrity and the confidentiality of your personal data:

### 1. Session Protection (Login Credentials)
* **Goal**: Prevent the theft of session keys and subsequent hijacking of your Notion account on other devices.
* **Solution**: Sensitive authentication cookies (e.g., `token_v2`) have the `HttpOnly` security flag and **never touch the hard drive in cleartext**. They are stored solely in **GNOME Keyring**, encrypted natively with the **AES** algorithm and protected by your Linux user password.
* **Sandbox Isolation**: Thanks to the Flatpak sandbox integration, the keyring isolates credentials: only the *Procedure* application (`io.github.albeph.Procedure`) is authorized by the operating system to read the cookie, while external processes will receive an empty value (`None`).

### 2. Content Protection (Local Cache and Notes)
* **Goal**: Prevent unauthorized reading of your private documents, personal attachments, and search history when the computer is turned off or through forensic analysis of the storage drive.
* **Solution**: Notion downloads note contents locally to speed up loading (in IndexedDB/LocalStorage databases). Since web engines do not encrypt this cache at runtime, *Procedure* redirects it entirely into **volatile RAM (`tmpfs` in `/run/user/<UID>/`)**.
* **Secure Shredding**: Upon exiting the application (or clicking "Exit"), all cache files inside the volatile RAM are overwritten with zero bytes (`\x00`) before being deleted, preventing recovery of free RAM sectors (Cold-boot attacks).

### 3. Device Recognition Note (macOS / Safari)
> [!NOTE]
> Because the WebKitGTK engine presents a default Safari-based User Agent string to web servers, some identity providers (such as Google OAuth or Notion's active session manager) may mistakenly identify your active login session as a **macOS** or **Safari** client instead of Linux. This is normal behavior for WebKit-based desktop wrappers on Linux and does not affect any functionality.

---

## 📥 How to Install

Once the compiled packages are generated (located in the `dist/` directory), you can install and run them on your system using one of the following methods depending on the package type:

### 1. Debian Package (`.deb`) — *Recommended for Debian/Ubuntu systems*
Installs the application system-wide, integrates with the desktop environment launcher, and automatically configures native dependencies.
```bash
# Install the package (run from the repository root)
sudo apt install io.github.albeph.procedure_*_all.deb

# Run the application (carch it in GNOME desktop menu or run in terminal)
procedure

# Uninstall the package
sudo apt remove io.github.albeph.procedure
```

### 2. Flatpak Package (`.flatpak`) — *Recommended for sandboxed isolation*
Runs the application inside an isolated secure container, with limited filesystem access but native GNOME Keyring sharing.
```bash
# Install the package (at user level)
flatpak install --user io.github.albeph.Procedure_*.flatpak

# Run the application
flatpak run io.github.albeph.Procedure

# Uninstall the package
flatpak uninstall --user io.github.albeph.Procedure
```

### 3. AppImage Package (`.AppImage`) — *Recommended for portable, zero-install use*
A single self-contained executable that packages all dependencies and runs on any modern Linux distribution without installation.
```bash
# Make the file executable
chmod +x io.github.albeph.Procedure_*-x86_64.AppImage

# Run the application
io.github.albeph.Procedure_*-x86_64.AppImage
```

---

## 📂 Project Structure

The project is divided into isolated folders to separate application code from packaging utilities:

```
Procedure/
├── app/                      # Application source code and resources
│   ├── procedure             # Bootstrap launcher script (handles sandbox and icon paths)
│   ├── install.sh            # Script to install the app natively on the host system
│   ├── io.github.albeph.Procedure.desktop   # Desktop entry file for the application menu
│   ├── resources/            # Default icons and static resources
│   └── src/                  # Python source modules
│       ├── main.py           # Entry-point (GApplication)
│       ├── window.py         # Main UI window and tab logic
│       ├── session_manager.py# Security management (Keyring, RAM-disk, Shredding)
│       ├── dialogs.py        # Native dialog windows (About, icon selection)
│       └── config.py         # Global client constants
│
├── packaging/                # Package recipes and build scripts
│   ├── flatpak/              # Flatpak manifest and build scripts (GNOME 50)
│   ├── appimage/             # AppImage recipe and portable build scripts
│   └── deb/                  # Debian package script and metadata
│
├── dist/                     # Generated binary targets ready for distribution
│   ├── io.github.albeph.Procedure.flatpak     # Standalone portable Flatpak bundle
│   ├── io.github.albeph.Procedure-x86_64.AppImage # Standalone portable AppImage binary
│   └── io.github.albeph.procedure_*.deb # Debian installer package
│
├── README.md                 # This file (project overview)
└── MANUAL.md                 # Detailed user and developer manual
```

---

## 🛠️ Source Execution

### Prerequisites
Make sure you have installed GTK4 and WebKitGTK dependencies on your Linux system. On Debian/Ubuntu-based distributions:
```bash
sudo apt install python3 python3-gi python3-pil libadwaita-1-dev gir1.2-webkit-6.0 gir1.2-adw-1
```

### Quick Start
You can run the application in development mode directly using the launcher:
```bash
./app/procedure
```

### Verbose/Debug Mode (Show web browser logs in the terminal)
```bash
./app/procedure --verbose
```

---

## 📦 Packaging and Distribution
If you wish to compile Flatpak, AppImage, or Debian (.deb) packages ready to be installed or distributed on other Linux machines, refer to the detailed guide:
👉 `packaging/README.md`
