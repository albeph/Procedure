# Procedure

**Procedure** è un client desktop nativo ed indipendente per sistemi Linux, progettato specificamente per integrarsi con l'ambiente desktop **GNOME** seguendo le linee guida **GNOME HIG (Human Interface Guidelines)**. Funge da wrapper minimale, veloce e sicuro per il servizio Notion, offrendo un'alternativa leggera ad Electron e focalizzata sulla sicurezza dei dati.

L'applicazione è identificata sul sistema con l'App ID: `io.github.albeph.Procedure`.

---

## 🚀 Caratteristiche Principali (Features)

*   **Integrazione Nativa GTK4 & Libadwaita**: Sviluppata con Python e le librerie di sistema native di GNOME per garantire animazioni fluide, layout reattivi ed una resa grafica coerente con il sistema host.
*   **Motore WebKitGTK 6.0**: Utilizza il motore di rendering nativo di sistema al posto di Chromium/Electron, riducendo drasticamente l'utilizzo di memoria RAM e CPU.
*   **Navigazione Multischeda (Tab)**:
    *   Gestione avanzata delle schede tramite barra superiore nativa (`Adw.TabBar` e `Adw.TabView`).
    *   Apertura di nuove schede duplicando l'URL corrente tramite il tasto `+` o la scorciatoia da tastiera.
    *   Cronologia di navigazione (Indietro/Avanti) indipendente per ciascuna scheda.
*   **Sicurezza Avanzata "Zero-Footprint" su Disco**:
    *   **GNOME Keyring (`libsecret`)**: I cookie di sessione non vengono mai scritti in chiaro o cifrati sul disco fisso. Rimangono unicamente nella memoria RAM di WebKit e vengono sincronizzati direttamente con il portachiavi sicuro di sistema.
    *   **Cache in RAM (`tmpfs`)**: I database locali temporanei (IndexedDB, LocalStorage) vengono memorizzati nella cartella volatile `/run/user/<UID>/procedure/` caricata interamente in RAM disk.
    *   **Distruzione Sicura (Secure Shredding)**: All'uscita dell'app o al logout, tutti i dati volatili vengono sovrascritti con byte zero (`\x00`) prima della rimozione fisica per prevenire tentativi di recupero dati forense.
    *   **Permessi Rigidi**: Le cartelle di configurazione locali sono bloccate con permessi `0700` (accesso esclusivo per l'utente proprietario).
*   **Sincronizzazione Automatica del Tema**: Rileva i cambi di preferenza di colore di GNOME (Chiaro/Scuro) tramite `Adw.StyleManager` e inietta dinamicamente CSS e JavaScript per forzare il tema corrispondente all'interno della pagina web di Notion.
*   **Scelta dell'Icona Personalizzata**: Consente di modificare l'icona geometrica "P" predefinita caricando un qualsiasi file PNG locale dall'interfaccia utente. L'applicazione riscalerà l'immagine a `512x512` pixel posizionandola nel percorso standard delle icone utente.
*   **Scorciatoie da Tastiera Veloci**:
    *   `Ctrl + T`: Nuova scheda
    *   `Ctrl + W`: Chiudi scheda attiva
    *   `Ctrl + Tab`: Scheda successiva
    *   `Ctrl + Shift + Tab`: Scheda precedente
    *   `Ctrl + R` o `F5`: Ricarica la pagina attiva

---

## 🔒 Modello di Sicurezza (Security Model)

Procedure implementa una netta separazione logica e tecnica per proteggere sia l'integrità del tuo account che la riservatezza dei tuoi dati personali:

### 1. Protezione della Sessione (Credenziali di Login)
* **Obiettivo**: Impedire il furto delle chiavi di sessione e il conseguente dirottamento (hijacking) del tuo account Notion su altri dispositivi.
* **Soluzione**: I cookie sensibili di autenticazione (es. `token_v2`) hanno il flag di sicurezza `HttpOnly` e **non toccano mai il disco fisso in chiaro**. Vengono memorizzati unicamente in **GNOME Keyring**, cifrati nativamente con algoritmo **AES** e protetti dalla tua password utente di Linux.
* **Isolamento Sandbox**: Grazie all'integrazione con la sandbox Flatpak, il portachiavi isola le credenziali: solo l'applicazione *Procedure* (`io.github.albeph.Procedure`) è autorizzata dal sistema operativo a leggere il cookie, mentre processi esterni riceveranno un valore vuoto (`None`).

### 2. Protezione dei Contenuti (Cache Locale e Note)
* **Obiettivo**: Impedire la lettura non autorizzata dei tuoi documenti privati, allegati personali e cronologia delle ricerche a computer spento o tramite analisi forense del disco.
* **Soluzione**: Notion scarica localmente il testo delle note per velocizzare il caricamento (in database IndexedDB/LocalStorage). Poiché i motori web non cifrano questa cache a runtime, *Procedure* la sposta interamente all'interno della **RAM volatile (`tmpfs` in `/run/user/<UID>/`)**.
* **Distruzione Sicura (Shredding)**: All'uscita dell'applicazione (o tramite il comando "Esci"), tutti i file di cache presenti nella RAM volatile vengono sovrascritti con byte zero (`\x00`) prima di essere eliminati fisicamente, prevenendo tecniche di recupero della memoria RAM libera (Cold-boot attacks).

---

## 📂 Struttura del Progetto

Il progetto è suddiviso in cartelle isolate per separare il codice applicativo dagli strumenti di packaging:

```
Procedure/
├── app/                      # Codice sorgente e risorse dell'applicazione
│   ├── procedure             # Script bootstrap launcher (gestisce sandbox e path icone)
│   ├── install.sh            # Script per installare l'app in locale nativamente
│   ├── io.github.albeph.Procedure.desktop   # File di integrazione nel menu delle applicazioni
│   ├── resources/            # Icone predefinite e risorse statiche
│   └── src/                  # Moduli sorgente in Python
│       ├── main.py           # Entry-point (GApplication)
│       ├── window.py         # Interfaccia grafica principale e logica delle schede
│       ├── session_manager.py# Gestione della sicurezza (Keyring, RAM-disk, Shredding)
│       ├── dialogs.py        # Finestre di dialogo native (About, caricamento icone)
│       └── config.py         # Costanti globali del client
│
├── packaging/                # Ricette e script per creare i pacchetti
│   ├── flatpak/              # Manifesto e builder per pacchetto Flatpak (GNOME 50)
│   └── appimage/             # Configurazione e builder per pacchetto portabile AppImage
│
├── dist/                     # Target binari generati pronti per la distribuzione
│   ├── Procedure.flatpak     # Pacchetto Flatpak portabile autonoma
│   └── Procedure-x86_64.AppImage # Eseguibile portabile autonomo
│
├── README.md                 # Questo file (panoramica del progetto)
└── MANUAL.md                 # Manuale d'uso dettagliato per utenti e sviluppatori
```

---

## 🛠️ Esecuzione in Locale

### Prerequisiti
Assicurati di avere installato le dipendenze di GTK4 e WebKitGTK sul tuo sistema Linux. Su distribuzioni basate su Debian/Ubuntu:
```bash
sudo apt install python3 python3-gi python3-pil libadwaita-1-dev gir1.2-webkit-6.0 gir1.2-adw-1
```

### Avvio Semplice
Puoi avviare l'applicazione in modalità di sviluppo direttamente eseguendo il launcher:
```bash
./app/procedure
```

### Avvio con Debug/Verbose (Log del browser visibili a terminale)
```bash
./app/procedure --verbose
```

---

## 📦 Packaging e Distribuzione
Se desideri compilare i pacchetti Flatpak o AppImage pronti all'uso per essere installati o distribuiti su altre macchine Linux, fai riferimento alla guida dettagliata:
👉 `packaging/README.md`
