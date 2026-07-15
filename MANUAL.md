# Manuale Tecnico e Utente: Procedure

Benvenuto nel manuale di **Procedure**, un client desktop nativo per Linux progettato secondo le linee guida **GNOME HIG (Human Interface Guidelines)**, focalizzato su performance elevate e sicurezza "zero-footprint" sul filesystem.

---

## 1. Introduzione ed Obiettivo
Procedure fornisce un'alternativa leggera ed estremamente sicura ai tradizionali client basati su Electron. È un wrapper minimale e flat per il servizio Notion che utilizza Python 3, le librerie native **GTK4/Libadwaita** e il motore di rendering **WebKitGTK 6.0**, garantendo una perfetta integrazione grafica con il desktop GNOME ed un consumo di risorse minimo.

---

## 2. Struttura del Progetto (Modularizzazione)
Il progetto è suddiviso in tre macro-cartelle per mantenere la root principale pulita e organizzata:

* **`app/`**: Contiene tutto il codice sorgente, le risorse e l'eseguibile dell'applicazione:
  * `procedure`: Launcher dell'applicazione (configura variabili e avvia il processo).
  * `install.sh`: Script per installare l'app a livello locale su sistema Linux.
  * `io.github.albeph.Procedure.desktop`: Collegamento desktop ufficiale.
  * `resources/`: Icona predefinita (`icon.png` in formato 512x512).
  * `src/`: Moduli sorgente Python (`main.py`, `window.py`, `session_manager.py`, ecc.).
* **`packaging/`**: Cartella isolata contenente le ricette e gli script di compilazione (`appimage/` e `flatpak/`).
* **`dist/`**: Cartella di output contenente i pacchetti finiti pronti per la distribuzione (`Procedure-x86_64.AppImage` e `Procedure.flatpak`).

---

## 3. Architettura di Sicurezza (Zero-Files-on-Disk)

Il client implementa requisiti di sicurezza avanzati per proteggere i tuoi dati di accesso locali da estrazioni non autorizzate:

### 3.1 Integrazione Diretta GNOME Keyring (`libsecret`)
* **Nessun database di cookie su disco**: A differenza dei browser standard che salvano i cookie in chiaro o in database locali SQLite sul disco fisso, **Procedure non crea alcun file di cookie sul filesystem** (nemmeno in modo cifrato).
* **Serializzazione in memoria**: I cookie risiedono solo nello spazio di memoria RAM privato del processo WebKit. Ogni volta che Notion modifica un cookie, l'app intercetta il cambiamento, lo serializza in formato JSON e lo invia direttamente a **GNOME Keyring** (tramite le API DBus di `libsecret`).
* **Ripristino al boot**: All'avvio dell'app, i cookie vengono recuperati direttamente dal portachiavi di sistema e reiniettati direttamente in memoria WebKit.

### 3.2 Archiviazione Dati Locali in RAM (`tmpfs`)
* I database di cache delle pagine (come IndexedDB e LocalStorage) non contengono cookie ma possono includere dati di cache delle pagine web caricate.
* Questi dati vengono direzionati nella cartella volatile `/run/user/<UID>/procedure/` (struttura in RAM disk di Linux che non scrive mai dati su supporti fisici HDD/SSD).
* **Secure Shredding**: All'uscita dell'applicazione (o tramite il pulsante "Esci"), tutti i file in RAM vengono sovrascritti con byte zero (`\x00`) prima di essere eliminati fisicamente.

### 3.4 Differenza di Protezione tra "Credenziali" e "Cache"
È importante comprendere la separazione tecnica dei canali di memorizzazione dell'applicazione:
* **Cookie di Autenticazione (Sessione)**: Il cookie critico di login (`token_v2`) ha il flag `HttpOnly` e non viene **mai** salvato nei database locali di IndexedDB/LocalStorage. Viene gestito dal portachiavi di sistema (**GNOME Keyring**) e cifrato in AES.
* **Cache di Lavoro e Note (Contenuto)**: Le tue note e gli allegati offline vengono salvati da WebKit in IndexedDB/LocalStorage per accelerare il caricamento. Non potendo cifrare questa cache dinamicamente a runtime, viene isolata interamente nel **RAM-disk volatile (`tmpfs`)** e distrutta con **secure shredding** (sovrascritta con `\x00`) alla chiusura dell'app. In questo modo, nessun dato sensibile o di testo delle note tocca mai la memoria permanente (SSD/HDD).

---

## 4. Guida all'Interfaccia Utente (UI)

L'interfaccia si integra con i temi scuro e chiaro di sistema di GNOME ed è strutturata in una singola barra superiore per ottimizzare lo spazio di lavoro:

### 4.1 Componenti della Barra Superiore (`Adw.HeaderBar`)
* **Pulsanti di Navigazione (Sinistra)**:
  * **Indietro**: Si attiva solo se la scheda corrente ha pagine precedenti nella cronologia (gestito dinamicamente anche su navigazioni SPA).
  * **Ricarica**: Ricarica la scheda attiva.
* **Tasto Nuova Scheda `+`**: Apre una nuova scheda duplicando l'URL di quella attualmente attiva.
* **Barra delle Schede (`Adw.TabBar`) (Centro)**: Mostra le schede aperte in modo compatto al centro della barra.
* **Menu 3 puntini (Destra)**: Offre le opzioni di informazioni e l'opzione di uscita.
* **Pulsanti di Controllo Finestra (Destra)**: Minimizza, espande e chiude l'app.

### 4.2 Menu Principale (3 Puntini)
* **Informazioni su Procedure**: Mostra la finestra dei crediti nativa di GNOME (`Adw.AboutWindow`).
* **Informazioni sulla crittografia**: Consente di verificare lo stato corrente della cifratura dei cookie (Attivo/Disattivo).
* **Esci e cancella sessione**: Cancella istantaneamente le credenziali dal GNOME Keyring, azzera i dati in RAM ed esce dal programma (equivalente a un logout totale di sicurezza).

---

## 5. Scorciatoie da Tastiera
* **`Ctrl + T`**: Apre una nuova scheda.
* **`Ctrl + W`**: Chiude la scheda attiva.
* **`Ctrl + Tab`**: Passa alla scheda successiva (a destra).
* **`Ctrl + Shift + Tab`**: Passa alla scheda precedente (a sinistra).
* **`Ctrl + R`** o **`F5`**: Ricarica la scheda corrente.

---

## 6. Parametri da Riga di Comando
* **Avvio Silenzioso (Default)**:
  ```bash
  procedure
  ```
  Non scrive nessun output a terminale e disabilita la redirezione dei log del browser.
* **Avvio Verbose (Log Attivo)**:
  ```bash
  procedure --verbose   # oppure: procedure -v
  ```
  Mostra a terminale tutti i log di caricamento, gli avvisi di sicurezza del portachiavi e redirige l'output JavaScript di WebKit su terminale.

---

## 7. Distribuzione e Compilazione (Flatpak & AppImage)
Tutte le istruzioni e i manifesti pronti all'uso sono disponibili nei seguenti file locali nella cartella del progetto:
* **Guida al packaging**: [packaging_guide.md](file:///home/user/Projects/Procedure/packaging/packaging_guide.md)
* **Manifesto Flatpak**: [io.github.albeph.Procedure.yml](file:///home/user/Projects/Procedure/packaging/flatpak/io.github.albeph.Procedure.yml)
* **Eseguibile di build AppImage**: [build_appimage.sh](file:///home/user/Projects/Procedure/packaging/appimage/build_appimage.sh)

---

## 8. Gestione e Aggiornamento della Versione

Il numero di versione dell'applicazione è gestito **centralmente** in un unico file per evitare disallineamenti tra i vari pacchetti e la GUI:

* **Configurazione Centrale**: La versione viene definita tramite la costante `VERSION` all'interno del file [config.py](file:///home/user/Projects/Procedure/app/src/config.py).
* **Funzionamento a Runtime**: All'avvio dell'applicazione, la finestra di dialogo *About* (Informazioni) carica dinamicamente questo valore importandolo da `config.py`.
* **Funzionamento in Fase di Build (AppImage)**: Lo script di compilazione [build_appimage.sh](file:///home/user/Projects/Procedure/packaging/appimage/build_appimage.sh) estrae automaticamente la versione corrente via Python e la inietta all'interno della ricetta `appimage-builder.yml` utilizzando un file temporaneo generato a runtime.

Per effettuare il bump o modificare la versione del programma, ti basta aggiornare la costante `VERSION` in `config.py`.
