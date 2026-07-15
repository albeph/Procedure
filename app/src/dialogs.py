import sys
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from config import VERSION

def show_about_dialog(parent):
    """
    Shows the native GNOME About dialog.
    """
    about = Adw.AboutWindow(
        transient_for=parent,
        application_name="Procedure",
        application_icon="io.github.albeph.Procedure",
        version=VERSION,
        comments="Client GTK4 nativo per il desktop GNOME (wrapper Notion).",
        website="https://github.com/albeph",
        license_type=Gtk.License.GPL_3_0,
        developers=["Albeph"],
    )
    about.add_credit_section("AI Help", ["Gemini 3.5 Flash"])
    about.present()


def show_encryption_info_dialog(parent, keyring_available):
    """
    Shows security info dialog with proper formatting.
    """
    status = "ATTIVO (Dati salvati in GNOME Keyring)" if keyring_available else "DISATTIVATO (Nessun salvataggio)"
    
    body_text = f"""Stato della crittografia: <b>{status}</b>

Questo client implementa una sicurezza di livello avanzato per proteggere la tua sessione di accesso (cookie):

1. <b>Nessun file di cookie su disco</b>: i cookie di sessione non vengono MAI scritti in nessun file del file system (né su disco fisso/SSD, né su RAM disk in chiaro o cifrati).
2. <b>GNOME Keyring nativo</b>: alla chiusura o alla modifica delle impostazioni, i cookie vengono serializzati in formato JSON cifrato e inviati direttamente a GNOME Keyring come segreto sicuro.
3. <b>Caricamento in memoria</b>: all'avvio dell'applicazione, i cookie vengono letti direttamente dal Keyring e iniettati nella memoria volatile del processo di WebKit.
4. <b>Dati temporanei in RAM</b>: i database locali temporanei delle pagine (IndexedDB/Local Storage) sono direzionati in memoria RAM (in <tt>/run/user/</tt>) e distrutti fisicamente tramite azzeramento (shredding) all'uscita.
"""
    dialog = Adw.MessageDialog(
        transient_for=parent,
        heading="Informazioni sulla crittografia"
    )
    dialog.set_body_use_markup(True)
    dialog.set_body(body_text)
    dialog.add_response("close", "Chiudi")
    dialog.set_default_response("close")
    dialog.connect("response", lambda d, r: d.destroy())
    dialog.present()


def show_keyring_warning(parent, callback):
    """
    Shows portachiavi warning modal if libsecret service is unresponsive.
    """
    dialog = Adw.MessageDialog(
        transient_for=parent,
        heading="Portachiavi non disponibile",
        body="Non è stato possibile accedere a GNOME Keyring.\n\nL'applicazione verrà avviata in modalità temporanea: i cookie di accesso verranno conservati solo in memoria e andranno persi alla chiusura (nessun dato verrà scritto sul disco).\n\nVuoi continuare comunque?",
    )
    dialog.add_response("cancel", "Annulla ed Esci")
    dialog.add_response("accept", "Continua senza salvare")
    dialog.set_response_appearance("accept", Adw.ResponseAppearance.DESTRUCTIVE)
    
    def on_response(d, response):
        d.destroy()
        callback(response == "accept")
        
    dialog.connect("response", on_response)
    dialog.present()


def show_change_icon_dialog(parent, current_icon, callback):
    """
    Shows a custom dialog with a list of previewable icons.
    """
    import os
    from config import RESOURCES_DIR

    dialog = Adw.MessageDialog(
        transient_for=parent,
        heading="Personalizza Icona Applicazione",
        body="Scegli lo stile dell'icona da applicare al lanciatore e al desktop di sistema. La modifica avrà effetto sul desktop e nella barra dock."
    )
    
    # List box of icon choices
    list_box = Gtk.ListBox()
    list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
    list_box.add_css_class("boxed-list")
    
    options = [
        ("default", "Predefinita (Minimalista)", "L'icona minimalista flat bianca e nera con la lettera 'P'."),
        ("custom_file", "Carica file PNG...", "Seleziona un'immagine PNG dal tuo computer.")
    ]
    
    rows = {}
    selected_row = None
    
    for opt_id, name, desc in options:
        row = Adw.ActionRow()
        row.set_title(name)
        row.set_subtitle(desc)
        
        # Load preview icon or default symbol
        if opt_id == "custom_file":
            img = Gtk.Image.new_from_icon_name("document-open-symbolic")
            img.set_pixel_size(32)
            row.add_prefix(img)
        else:
            img_path = os.path.join(RESOURCES_DIR, "icon.png")
            if os.path.exists(img_path):
                img = Gtk.Image.new_from_file(img_path)
                img.set_pixel_size(32)
                row.add_prefix(img)
            
        list_box.append(row)
        rows[row] = opt_id
        if opt_id == current_icon:
            selected_row = row
            
    if selected_row:
        list_box.select_row(selected_row)
        
    dialog.set_extra_child(list_box)
    
    dialog.add_response("cancel", "Annulla")
    dialog.add_response("apply", "Applica")
    dialog.set_response_appearance("apply", Adw.ResponseAppearance.SUGGESTED)
    
    def on_response(d, response):
        if response == "apply":
            sel = list_box.get_selected_row()
            if sel in rows:
                callback(rows[sel])
        d.destroy()
        
    dialog.connect("response", on_response)
    dialog.present()


def open_file_chooser(parent, file_callback):
    """
    Opens a native file chooser dialog to select a custom PNG image file.
    """
    dialog = Gtk.FileChooserNative.new(
        "Seleziona icona personalizzata (PNG)",
        parent,
        Gtk.FileChooserAction.OPEN,
        "Apri",
        "Annulla"
    )
    
    # Configure filters to only allow PNG images
    filter_png = Gtk.FileFilter.new()
    filter_png.set_name("Immagini PNG (*.png)")
    filter_png.add_pattern("*.png")
    filter_png.add_mime_type("image/png")
    dialog.add_filter(filter_png)
    
    def on_response(d, response_id):
        if response_id == Gtk.ResponseType.ACCEPT:
            file_path = d.get_file().get_path()
            file_callback(file_path)
        d.destroy()
        
    dialog.connect("response", on_response)
    dialog.show()
