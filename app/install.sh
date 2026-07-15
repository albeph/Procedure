#!/usr/bin/env bash
set -e
# Cambia la directory corrente in quella contenente lo script
SCRIPT_DIR="$(dirname "$(readlink -f "${0}")")"
cd "$SCRIPT_DIR"
echo "=== Installatore Client GTK4 Procedure ==="
echo "Questo script installerà Procedure a livello utente."

# Directories di destinazione
BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/512x512/apps"

echo "1. Creazione delle directory necessarie..."
mkdir -p "$BIN_DIR"
mkdir -p "$APP_DIR"
mkdir -p "$ICON_DIR"

echo "2. Copia dei file..."
# Copia la directory sorgente dei moduli
SHARE_DIR="$HOME/.local/share/procedure"
mkdir -p "$SHARE_DIR"
rm -rf "$SHARE_DIR/src"
cp -r src "$SHARE_DIR/src"
echo "   - Moduli installati in: $SHARE_DIR/src"

rm -rf "$SHARE_DIR/resources"
cp -r resources "$SHARE_DIR/resources"
echo "   - Risorse installate in: $SHARE_DIR/resources"

# Copia l'eseguibile principale launcher
cp procedure "$BIN_DIR/procedure"
chmod +x "$BIN_DIR/procedure"
echo "   - Launcher installato in: $BIN_DIR/procedure"

# Copia il file desktop
# Aggiorna il percorso assoluto all'eseguibile se necessario,
# ma usando 'procedure' in PATH è solitamente sufficiente se ~/.local/bin è nel PATH.
# Per essere sicuri, inseriamo il percorso completo assoluto dell'eseguibile nel file desktop.
sed "s|Exec=procedure|Exec=$BIN_DIR/procedure|g" io.github.albeph.Procedure.desktop > "$APP_DIR/io.github.albeph.Procedure.desktop"
chmod +x "$APP_DIR/io.github.albeph.Procedure.desktop"
echo "   - Collegamento desktop installato in: $APP_DIR/io.github.albeph.Procedure.desktop"

# Copia l'icona
cp resources/icon.png "$ICON_DIR/io.github.albeph.Procedure.png"
echo "   - Icona dell'applicazione installata in: $ICON_DIR/io.github.albeph.Procedure.png"

echo "3. Aggiornamento dei database desktop e icone..."
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$APP_DIR" || true
fi
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" || true
fi

echo "4. Verifica delle dipendenze..."
DEPENDENCY_MISSING=0

if ! dpkg -l | grep -q "gir1.2-webkit-6.0"; then
    echo "⚠️ ATTENZIONE: gir1.2-webkit-6.0 non sembra essere installato."
    DEPENDENCY_MISSING=1
fi

echo "========================================="
echo "🎉 Installazione completata con successo!"
echo "========================================="
if [ $DEPENDENCY_MISSING -eq 1 ]; then
    echo "Per far funzionare l'applicazione, esegui il seguente comando:"
    echo "👉 sudo apt install gir1.2-webkit-6.0"
    echo "========================================="
else
    echo "L'applicazione è pronta!"
    echo "Puoi avviarla cercandola nel tuo menu delle applicazioni GNOME come 'Procedure',"
    echo "oppure eseguendo da terminale: procedure"
    echo "========================================="
fi
