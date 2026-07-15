#!/usr/bin/env bash
# Script per generare e installare localmente il pacchetto Flatpak di Procedure.
set -e

# Salva la directory in cui risiede lo script
SCRIPT_DIR="$(dirname "$(readlink -f "${0}")")"
cd "$SCRIPT_DIR"

echo "=== Generazione e Installazione Pacchetto Flatpak ==="

# 1. Verifica la presenza di flatpak e flatpak-builder
if ! command -v flatpak-builder &> /dev/null || ! command -v flatpak &> /dev/null; then
    echo ""
    echo "❌ ERRORE: flatpak o flatpak-builder non sono installati sul tuo sistema!"
    echo "Per installarli, esegui il seguente comando nel tuo terminale:"
    echo "--------------------------------------------------------"
    echo "  sudo apt update && sudo apt install -y flatpak flatpak-builder"
    echo "--------------------------------------------------------"
    echo ""
    exit 1
fi

# 2. Configura il repository Flathub a livello utente se non presente
echo "1. Controllo repository Flathub..."
flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo

# 3. Verifica e installa SDK e Platform di GNOME 50
echo "2. Verifica runtime GNOME 50 (SDK e Platform)..."
if ! flatpak list | grep -q "org.gnome.Platform//50" || ! flatpak list | grep -q "org.gnome.Sdk//50"; then
    echo "   - Download e installazione delle dipendenze di GNOME 50 in corso (potrebbe richiedere tempo)..."
    flatpak install --user -y flathub org.gnome.Platform//50 org.gnome.Sdk//50
else
    echo "   - Dipendenze GNOME 50 già presenti sul sistema."
fi

# 4. Compila e installa il pacchetto Flatpak in locale
echo "3. Compilazione del pacchetto Flatpak..."
rm -rf build-dir .flatpak-builder
flatpak-builder --user --install --force-clean build-dir io.github.albeph.Procedure.yml

# 5. Genera il pacchetto portabile .flatpak per la distribuzione
echo "4. Generazione del pacchetto portabile .flatpak per la distribuzione..."
VERSION=$(python3 -c "import sys; sys.path.insert(0, '../../app/src'); from config import VERSION; print(VERSION)")
mkdir -p ../../dist
flatpak build-bundle ~/.local/share/flatpak/repo ../../dist/io.github.albeph.Procedure_${VERSION}.flatpak io.github.albeph.Procedure master

# 6. Fine
echo ""
echo "--------------------------------------------------------"
echo "🎉 Successo! Il pacchetto Flatpak è stato installato ed esportato."
echo "Puoi avviarlo in locale tramite:"
echo "👉 flatpak run io.github.albeph.Procedure"
echo ""
echo "Trovi il pacchetto portabile da copiare su altri computer in:"
echo "👉 $(readlink -f ../../dist/io.github.albeph.Procedure_${VERSION}.flatpak)"
echo "--------------------------------------------------------"
echo ""

# Pulisce la cartella temporanea del builder per liberare spazio
rm -rf build-dir .flatpak-builder
