# Guida al Packaging: Flatpak & AppImage su Macchina Vergine

Questa guida descrive i passaggi passo-passo per installare le dipendenze di build e generare i pacchetti compilati di **Procedure** (`Procedure.flatpak` e `Procedure-x86_64.AppImage`) partendo da un'installazione Linux "vergine" (es. Ubuntu 24.04 LTS o Debian 12 pulita).

Tutti i processi di packaging sono configurati per isolare i file temporanei all'interno delle rispettive sotto-cartelle e posizionare i pacchetti finiti nella cartella `dist/` nella root del progetto.

---

## 1. Come compilare il pacchetto Flatpak

Flatpak è il formato principale consigliato per la distribuzione. Isola l'applicazione in una sandbox protetta ma le consente di accedere alle librerie grafiche avanzate, alla GPU, alla rete e al portachiavi di sistema (**GNOME Keyring**).

### Passo 1: Installare flatpak e flatpak-builder
Apri un terminale sulla macchina vergine ed esegui:
```bash
sudo apt update
sudo apt install -y flatpak flatpak-builder
```

### Passo 2: Abilitare il repository Flathub
Abilita Flathub a livello utente per consentire il download dei runtime e degli SDK:
```bash
flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
```

### Passo 3: Eseguire lo script di build
Esegui lo script dalla root del progetto. Lo script controllerà, scaricherà e installerà automaticamente il runtime e l'SDK **GNOME 50** se non sono già presenti sul sistema, per poi compilare ed esportare il pacchetto portabile:
```bash
# Posizionati nella cartella del progetto
cd /home/user/Projects/Procedure

# Esegui lo script di compilazione
./packaging/flatpak/build_flatpak.sh
```

### Passo 4: Verifica ed esecuzione locale
Al termine del processo, l'applicazione sarà installata nel sistema locale. Puoi avviarla tramite:
```bash
flatpak run io.github.albeph.Procedure
```

Il pacchetto portabile standalone pronto per essere copiato ed installato su altri computer si trova in:
👉 `dist/Procedure.flatpak`

Per installarlo su una macchina di destinazione:
```bash
flatpak install --user dist/Procedure.flatpak
```

---

## 2. Come compilare il pacchetto AppImage Auto-Contenuto

L'AppImage raccoglie al suo interno tutte le librerie dinamiche necessarie (tra cui GTK, WebKitGTK e libsecret) per consentire all'applicazione di avviarsi su qualsiasi altra distribuzione Linux recente, anche se priva delle librerie di GNOME.

### Passo 1: Installare i prerequisiti di sistema e appimage-builder
Su una macchina vergine, installa i pacchetti necessari per la compilazione e la gestione delle immagini compresse:
```bash
sudo apt update
sudo apt install -y python3-pip python3-pil patchelf desktop-file-utils appstream squashfs-tools fakeroot fakechroot
```

Successivamente, installa `appimage-builder` tramite il gestore pacchetti Python:
```bash
pip3 install --break-system-packages appimage-builder
```

*(Nota: Se la distribuzione vieta l'uso di `--break-system-packages`, puoi installarlo usando `pipx` o all'interno di un ambiente virtuale).*

### Passo 2: Eseguire lo script di compilazione dell'AppImage
Avvia lo script dalla root del progetto:
```bash
# Esegui lo script di compilazione
./packaging/appimage/build_appimage.sh
```

Questo script:
1. Creerà una cartella temporanea `AppDir` in cui copierà i sorgenti dell'applicazione.
2. Userà `appimage-builder` per scaricare automaticamente le librerie native necessarie in un ambiente isolato (`packaging/appimage/appimage-build/`).
3. Genererà ed esporterà l'eseguibile autonomo finale nella cartella `dist/`.

### Passo 3: Verifica ed esecuzione
Trovi l'eseguibile compilato finale in:
👉 `dist/Procedure-x86_64.AppImage`

Rendilo eseguibile e avvialo:
```bash
chmod +x dist/Procedure-x86_64.AppImage
./dist/Procedure-x86_64.AppImage
```

---

## 💡 Risoluzione dei Problemi Comuni su Macchine Pulite

*   **Icone o immagini SVG non visualizzate (AppImage)**: 
    Procedure integra un launcher intelligente che rigenera dinamicamente la cache `loaders.cache` all'avvio su qualsiasi macchina host. Questo assicura il corretto rendering delle icone grafiche di navigazione anche se i path delle librerie del computer host non coincidono con quelli di compilazione.
*   **Schermo bianco all'avvio**:
    WebKitGTK richiede i driver della scheda video accelerata. Se esegui l'app all'interno di una macchina virtuale senza accelerazione 3D abilitata, assicurati che l'accelerazione sia supportata, o avvia l'applicazione con `./app/procedure --verbose` per visionare i log di errore.
