#!/usr/bin/env bash
# Script per generare un'AppImage AUTO-CONTENUTA (self-contained) per il client Procedure.
# Questo script utilizza appimage-builder per scaricare ed includere le dipendenze di sistema (WebKit, Gtk, Secret).
set -e

# Salva la directory in cui risiede lo script
SCRIPT_DIR="$(dirname "$(readlink -f "${0}")")"
cd "$SCRIPT_DIR"

echo "=== Generazione AppImage Auto-Contenuta (fakeroot/apt) ==="

# 1. Verifica la presenza di appimage-builder nel sistema
if ! command -v appimage-builder &> /dev/null; then
    echo ""
    echo "❌ ERRORE: appimage-builder non è installato sul tuo sistema!"
    echo "Per installarlo, esegui i seguenti comandi nel tuo terminale:"
    echo "--------------------------------------------------------"
    echo "  sudo apt update"
    echo "  sudo apt install -y python3-pip patchelf desktop-file-utils appstream squashfs-tools fakeroot fakechroot"
    echo "  pip3 install --break-system-packages appimage-builder"
    echo "--------------------------------------------------------"
    echo ""
    exit 1
fi

# 2. Prepara la cartella AppDir temporanea inserendo sorgenti e risorse
echo "1. Preparazione della cartella AppDir..."
rm -rf AppDir
mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/share/applications
mkdir -p AppDir/usr/share/icons/hicolor/512x512/apps

# Copia i file dell'applicazione
cp ../../app/procedure AppDir/usr/bin/procedure
cp -r ../../app/src AppDir/usr/bin/src
cp -r ../../app/resources AppDir/usr/bin/resources
cp ../../app/io.github.albeph.Procedure.desktop AppDir/usr/share/applications/
cp ../../app/resources/icon.png AppDir/usr/share/icons/hicolor/512x512/apps/io.github.albeph.Procedure.png

# Configurazione root di AppDir (Desktop entry e Icone di avvio)
cp ../../app/resources/icon.png AppDir/io.github.albeph.Procedure.png
cp ../../app/resources/icon.png AppDir/.diricon
ln -sf usr/share/applications/io.github.albeph.Procedure.desktop AppDir/io.github.albeph.Procedure.desktop


# 4. Aggira l'assenza di apt-key e zsyncmake creando dummy script nel PATH
mkdir -p local_bin
cat << 'EOF' > local_bin/apt-key
#!/bin/sh
exit 0
EOF
chmod +x local_bin/apt-key

cat << 'EOF' > local_bin/zsyncmake
#!/bin/sh
exit 0
EOF
chmod +x local_bin/zsyncmake
ORIGINAL_PATH="$PATH"
export PATH="$PWD/local_bin:$PATH"

# 5. Avvia il processo di build di appimage-builder
echo "3. Compilazione dell'AppImage auto-contenuta (download dipendenze in corso)..."
VERSION=$(python3 -c "import sys; sys.path.insert(0, '../../app/src'); from config import VERSION; print(VERSION)")
echo "   - Versione rilevata: $VERSION"
sed "s|version: APP_VERSION|version: $VERSION|g" appimage-builder.yml > temp_appimage_recipe.yml
appimage-builder --recipe temp_appimage_recipe.yml
rm -f temp_appimage_recipe.yml

# Ripristina il PATH originale
export PATH="$ORIGINAL_PATH"
rm -rf local_bin

# 5. Sposta l'eseguibile compilato finale nella root del progetto
echo "4. Spostamento dell'eseguibile nella root del progetto..."
# Trova il file AppImage generato (es. Procedure-1.0.0-x86_64.AppImage)
GENERATED_APPIMAGE=$(find . -maxdepth 1 -name "*.AppImage" | head -n 1)

if [ -n "$GENERATED_APPIMAGE" ]; then
    mkdir -p ../../dist
    mv "$GENERATED_APPIMAGE" ../../dist/Procedure-x86_64.AppImage
    echo "--------------------------------------------------------"
    echo "🎉 Successo! AppImage creata e posizionata in:"
    echo "👉 $(readlink -f ../../dist/Procedure-x86_64.AppImage)"
    echo "--------------------------------------------------------"
else
    echo "⚠️ Attenzione: Impossibile trovare il file AppImage compilato."
fi

# 6. Pulizia dei file di log e delle cartelle temporanee
echo "5. Pulizia della directory temporanea..."
rm -rf AppDir
rm -rf appimage-builder-cache/
