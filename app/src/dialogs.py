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


def show_preferences_dialog(parent, config, current_url, current_title, apply_icon_callback, apply_custom_icon_callback, save_callback):
    """
    Shows a custom Preferences window with a bottom bar switcher (Adw.ViewSwitcher) containing
    General Settings and Icon Customization tabs.
    """
    window = Adw.Window(
        transient_for=parent,
        modal=True,
        title="Preferenze",
        default_width=450,
        default_height=520
    )
    
    main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    window.set_content(main_box)
    
    # 1. Header Bar
    header_bar = Adw.HeaderBar()
    main_box.append(header_bar)
    
    # 2. View Stack
    view_stack = Adw.ViewStack()
    view_stack.set_vexpand(True)
    view_stack.set_hexpand(True)
    main_box.append(view_stack)
    
    def create_scroll_page(child):
        scroll = Gtk.ScrolledWindow()
        scroll.set_hscrollbar_policy(Gtk.PolicyType.NEVER)
        scroll.set_vscrollbar_policy(Gtk.PolicyType.AUTOMATIC)
        clamp = Adw.Clamp()
        clamp.set_child(child)
        clamp.set_margin_top(18)
        clamp.set_margin_bottom(18)
        clamp.set_margin_start(18)
        clamp.set_margin_end(18)
        scroll.set_child(clamp)
        return scroll

    # --- PAGE 1: GENERALE ---
    general_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
    
    # Home Page Group
    home_group = Adw.PreferencesGroup(title="Pagina Iniziale e Home")
    general_box.append(home_group)
    
    def clean_title(url, title_str):
        if not url or url in ["https://app.notion.com/home", "https://www.notion.so/home", "https://notion.so/home", "https://www.notion.com/home"]:
            return "Home default di Notion"
        if title_str:
            if " | Notion" in title_str:
                title_str = title_str.split(" | Notion")[0].strip()
            elif " | " in title_str:
                title_str = title_str.split(" | ")[0].strip()
            if title_str:
                return title_str
        return "Pagina personalizzata"

    # Current settings states
    current_settings = {
        "home_url": config.get("home_url", "https://app.notion.com/home"),
        "home_title": config.get("home_title", "Home default di Notion"),
        "icon": config.get("icon", "default")
    }

    current_home_row = Adw.ActionRow(
        title="Home Page configurata",
        subtitle=current_settings["home_title"]
    )
    current_home_row.add_prefix(Gtk.Image.new_from_icon_name("go-home-symbolic"))
    home_group.add(current_home_row)
    
    clean_curr_title = clean_title(current_url, current_title) if current_url else None
    use_current_row = Adw.ActionRow(
        title="Usa la pagina corrente",
        subtitle=f"Imposta come home: {clean_curr_title}" if clean_curr_title else "Nessuna pagina aperta"
    )
    btn_use_current = Gtk.Button.new_from_icon_name("document-save-symbolic")
    btn_use_current.set_valign(Gtk.Align.CENTER)
    btn_use_current.set_sensitive(bool(current_url))
    
    def on_use_current_clicked(btn):
        if current_url:
            current_settings["home_url"] = current_url
            current_settings["home_title"] = clean_curr_title
            current_home_row.set_subtitle(clean_curr_title)
            
    btn_use_current.connect("clicked", on_use_current_clicked)
    use_current_row.add_suffix(btn_use_current)
    home_group.add(use_current_row)
    
    reset_row = Adw.ActionRow(
        title="Ripristina predefinita",
        subtitle="Reimposta la home page predefinita di Notion"
    )
    btn_reset = Gtk.Button.new_from_icon_name("edit-clear-symbolic")
    btn_reset.set_valign(Gtk.Align.CENTER)
    
    def on_reset_clicked(btn):
        current_settings["home_url"] = "https://app.notion.com/home"
        current_settings["home_title"] = "Home default di Notion"
        current_home_row.set_subtitle("Home default di Notion")
        
    btn_reset.connect("clicked", on_reset_clicked)
    reset_row.add_suffix(btn_reset)
    home_group.add(reset_row)
    
    # Interface Group
    ui_group = Adw.PreferencesGroup(title="Interfaccia Utente")
    general_box.append(ui_group)
    
    show_home_switch = Adw.SwitchRow(
        title="Pulsante Home nella barra superiore",
        subtitle="Visualizza il tasto Home per tornare rapidamente alla pagina principale",
        active=config.get("show_home_button", True)
    )
    ui_group.add(show_home_switch)
    
    # Startup Group
    startup_group = Adw.PreferencesGroup(title="Comportamento all'Avvio")
    general_box.append(startup_group)
    
    behavior_model = Gtk.StringList.new(["Ripristina schede precedenti", "Apri la pagina Home"])
    behavior_combo = Adw.ComboRow(
        title="All'avvio di Procedure",
        model=behavior_model,
        selected=0 if config.get("startup_behavior", "restore") == "restore" else 1
    )
    startup_group.add(behavior_combo)
    
    scroll_general = create_scroll_page(general_box)
    view_stack.add_titled_with_icon(
        scroll_general,
        "general",
        "Generale",
        "preferences-system-symbolic"
    )

    # --- PAGE 2: ICONA ---
    icon_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
    
    icon_group = Adw.PreferencesGroup(title="Personalizzazione Icona")
    icon_box.append(icon_group)
    
    def get_icon_status_label(icon_type):
        if icon_type == "custom":
            return "Personalizzata (File PNG caricato)"
        return "Predefinita (Minimalista)"
        
    current_icon_row = Adw.ActionRow(
        title="Icona in uso",
        subtitle=get_icon_status_label(current_settings["icon"])
    )
    
    import os
    from config import RESOURCES_DIR
    
    icon_image = Gtk.Image()
    icon_image.set_pixel_size(48)
    
    def update_icon_preview(icon_type):
        if icon_type == "custom":
            custom_path = os.path.expanduser("~/.local/share/icons/hicolor/512x512/apps/io.github.albeph.Procedure.png")
            if os.path.exists(custom_path):
                icon_image.set_from_file(custom_path)
            else:
                icon_image.set_from_icon_name("image-missing-symbolic")
        else:
            default_path = os.path.join(RESOURCES_DIR, "icon.png")
            if os.path.exists(default_path):
                icon_image.set_from_file(default_path)
            else:
                icon_image.set_from_icon_name("io.github.albeph.Procedure")
                
    update_icon_preview(current_settings["icon"])
    current_icon_row.add_prefix(icon_image)
    icon_group.add(current_icon_row)
    
    default_icon_row = Adw.ActionRow(
        title="Icona predefinita",
        subtitle="Ripristina l'icona minimalista flat di default"
    )
    btn_apply_default = Gtk.Button.new_with_label("Applica")
    btn_apply_default.set_valign(Gtk.Align.CENTER)
    btn_apply_default.add_css_class("suggested-action")
    
    def on_apply_default_clicked(btn):
        apply_icon_callback("default")
        current_settings["icon"] = "default"
        current_icon_row.set_subtitle(get_icon_status_label("default"))
        update_icon_preview("default")
        
    btn_apply_default.connect("clicked", on_apply_default_clicked)
    default_icon_row.add_suffix(btn_apply_default)
    icon_group.add(default_icon_row)
    
    custom_icon_row = Adw.ActionRow(
        title="Icona personalizzata",
        subtitle="Seleziona un file immagine PNG dal tuo computer"
    )
    btn_upload_custom = Gtk.Button.new_from_icon_name("document-open-symbolic")
    btn_upload_custom.set_valign(Gtk.Align.CENTER)
    
    def on_icon_file_selected(file_path):
        if file_path:
            apply_custom_icon_callback(file_path)
            current_settings["icon"] = "custom"
            current_icon_row.set_subtitle(get_icon_status_label("custom"))
            update_icon_preview("custom")

    def on_upload_custom_clicked(btn):
        open_file_chooser(window, on_icon_file_selected)
        
    btn_upload_custom.connect("clicked", on_upload_custom_clicked)
    custom_icon_row.add_suffix(btn_upload_custom)
    icon_group.add(custom_icon_row)
    
    scroll_icon = create_scroll_page(icon_box)
    view_stack.add_titled_with_icon(
        scroll_icon,
        "icon",
        "Icona",
        "preferences-desktop-wallpaper-symbolic"
    )

    # 3. View Switcher Bar at the bottom
    bottom_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    bottom_bar.add_css_class("toolbar")
    
    switcher = Adw.ViewSwitcher()
    switcher.set_stack(view_stack)
    switcher.set_hexpand(True)
    switcher.set_halign(Gtk.Align.CENTER)
    
    bottom_bar.append(switcher)
    main_box.append(bottom_bar)

    def on_close_request(win):
        # Save values to config dict
        config["home_url"] = current_settings["home_url"]
        config["home_title"] = current_settings["home_title"]
        config["icon"] = current_settings["icon"]
        config["show_home_button"] = show_home_switch.get_active()
        config["startup_behavior"] = "restore" if behavior_combo.get_selected() == 0 else "home"
        save_callback()
        
    window.connect("close-request", on_close_request)
    window.present()
