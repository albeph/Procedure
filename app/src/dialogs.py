import sys
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from config import VERSION
from language_manager import _t, LanguageManager

def show_about_dialog(parent):
    """
    Shows the native GNOME About dialog.
    """
    about = Adw.AboutWindow(
        transient_for=parent,
        application_name="Procedure",
        application_icon="io.github.albeph.Procedure",
        version=VERSION,
        comments=_t("about_comments"),
        website="https://github.com/albeph",
        license_type=Gtk.License.GPL_3_0,
        developers=["Albeph"],
    )
    about.add_credit_section(_t("about_ai_help"), ["Gemini 3.5 Flash"])
    about.present()


def show_encryption_info_dialog(parent, keyring_available):
    """
    Shows security info dialog with proper formatting.
    """
    status_key = "enc_info_active" if keyring_available else "enc_info_inactive"
    status = _t(status_key)
    body_text = _t("enc_info_body", status=status)
    dialog = Adw.MessageDialog(
        transient_for=parent,
        heading=_t("enc_info_title")
    )
    dialog.set_body_use_markup(True)
    dialog.set_body(body_text)
    dialog.add_response("close", _t("btn_close"))
    dialog.set_default_response("close")
    dialog.connect("response", lambda d, r: d.destroy())
    dialog.present()


def show_keyring_warning(parent, callback):
    """
    Shows portachiavi warning modal if libsecret service is unresponsive.
    """
    dialog = Adw.MessageDialog(
        transient_for=parent,
        heading=_t("keyring_warning_title"),
        body=_t("keyring_warning_body"),
    )
    dialog.add_response("cancel", _t("keyring_warning_cancel"))
    dialog.add_response("accept", _t("keyring_warning_accept"))
    dialog.set_response_appearance("accept", Adw.ResponseAppearance.DESTRUCTIVE)
    
    def on_response(d, response):
        d.destroy()
        callback(response == "accept")
        
    dialog.connect("response", on_response)
    dialog.present()




def open_file_chooser(parent, file_callback):
    """
    Opens a native file chooser dialog to select a custom PNG image file.
    """
    dialog = Gtk.FileChooserNative.new(
        _t("file_chooser_title"),
        parent,
        Gtk.FileChooserAction.OPEN,
        _t("file_chooser_open"),
        _t("file_chooser_cancel")
    )
    
    # Configure filters to only allow PNG images
    filter_png = Gtk.FileFilter.new()
    filter_png.set_name(_t("file_chooser_filter"))
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
        title=_t("pref_title"),
        default_width=450,
        default_height=540
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
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        clamp = Adw.Clamp()
        clamp.set_child(child)
        clamp.set_margin_top(18)
        clamp.set_margin_bottom(18)
        clamp.set_margin_start(18)
        clamp.set_margin_end(18)
        scroll.set_child(clamp)
        return scroll

    # --- PAGE 1: HOME PAGE ---
    home_page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
    
    # Home Page Group
    home_group = Adw.PreferencesGroup(title=_t("pref_group_home"))
    home_page_box.append(home_group)
    
    def clean_title(url, title_str):
        if not url or url in ["https://app.notion.com/home", "https://www.notion.so/home", "https://notion.so/home", "https://www.notion.com/home"]:
            return _t("home_default_title")
        if title_str:
            if " | Notion" in title_str:
                title_str = title_str.split(" | Notion")[0].strip()
            elif " | " in title_str:
                title_str = title_str.split(" | ")[0].strip()
            if title_str:
                return title_str
        return _t("custom_page_title")

    # Current settings states
    current_settings = {
        "home_url": config.get("home_url", "https://app.notion.com/home"),
        "home_title": config.get("home_title", _t("home_default_title")),
        "icon": config.get("icon", "default")
    }

    current_home_row = Adw.ActionRow(
        title=_t("pref_row_home_config"),
        subtitle=current_settings["home_title"]
    )
    current_home_row.add_prefix(Gtk.Image.new_from_icon_name("go-home-symbolic"))
    home_group.add(current_home_row)
    
    clean_curr_title = clean_title(current_url, current_title) if current_url else None
    use_current_row = Adw.ActionRow(
        title=_t("pref_row_use_current"),
        subtitle=_t("pref_sub_use_current", title=clean_curr_title) if clean_curr_title else _t("pref_sub_no_page")
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
        title=_t("pref_row_reset_default"),
        subtitle=_t("pref_sub_reset_default")
    )
    btn_reset = Gtk.Button.new_from_icon_name("edit-clear-symbolic")
    btn_reset.set_valign(Gtk.Align.CENTER)
    
    def on_reset_clicked(btn):
        current_settings["home_url"] = "https://app.notion.com/home"
        current_settings["home_title"] = _t("home_default_title")
        current_home_row.set_subtitle(_t("home_default_title"))
        
    btn_reset.connect("clicked", on_reset_clicked)
    reset_row.add_suffix(btn_reset)
    home_group.add(reset_row)
    
    # Interface Group
    ui_group = Adw.PreferencesGroup(title=_t("pref_group_ui"))
    home_page_box.append(ui_group)
    
    show_home_switch = Adw.SwitchRow(
        title=_t("pref_row_show_home"),
        subtitle=_t("pref_sub_show_home"),
        active=config.get("show_home_button", True)
    )
    ui_group.add(show_home_switch)
    
    # Startup Group
    startup_group = Adw.PreferencesGroup(title=_t("pref_group_startup"))
    home_page_box.append(startup_group)
    
    behavior_model = Gtk.StringList.new([_t("pref_opt_restore"), _t("pref_opt_home")])
    behavior_combo = Adw.ComboRow(
        title=_t("pref_row_startup_action"),
        model=behavior_model,
        selected=0 if config.get("startup_behavior", "restore") == "restore" else 1
    )
    startup_group.add(behavior_combo)
    
    scroll_home_page = create_scroll_page(home_page_box)
    view_stack.add_titled_with_icon(
        scroll_home_page,
        "home_page",
        _t("tab_home_page"),
        "go-home-symbolic"
    )

    # --- PAGE 2: LINGUA ---
    language_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
    
    lang_group = Adw.PreferencesGroup(title=_t("pref_group_language"))
    language_box.append(lang_group)
    
    langs = LanguageManager.get_available_languages()
    lang_codes = list(langs.keys())
    lang_names = list(langs.values())
    lang_model = Gtk.StringList.new(lang_names)
    current_lang_code = LanguageManager.get_current_language()
    selected_idx = lang_codes.index(current_lang_code) if current_lang_code in lang_codes else 0
    
    lang_combo = Adw.ComboRow(
        title=_t("pref_row_language"),
        model=lang_model,
        selected=selected_idx
    )
    lang_group.add(lang_combo)
    
    sync_notion_switch = Adw.SwitchRow(
        title=_t("pref_row_sync_notion_lang"),
        subtitle=_t("pref_sub_sync_notion_lang"),
        active=config.get("sync_notion_lang", True)
    )
    lang_group.add(sync_notion_switch)
    
    scroll_language = create_scroll_page(language_box)
    view_stack.add_titled_with_icon(
        scroll_language,
        "language",
        _t("tab_language"),
        "preferences-desktop-locale-symbolic"
    )

    # --- PAGE 3: ICONA ---
    icon_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
    
    icon_group = Adw.PreferencesGroup(title=_t("pref_group_icon"))
    icon_box.append(icon_group)
    
    def get_icon_status_label(icon_type):
        if icon_type == "custom":
            return _t("pref_status_custom_icon")
        return _t("pref_status_default_icon")
        
    current_icon_row = Adw.ActionRow(
        title=_t("pref_row_icon_in_use"),
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
        title=_t("pref_row_icon_default"),
        subtitle=_t("pref_sub_icon_default")
    )
    btn_apply_default = Gtk.Button.new_with_label(_t("pref_btn_apply"))
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
        title=_t("pref_row_icon_custom"),
        subtitle=_t("pref_sub_icon_custom")
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
        _t("tab_icon"),
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

    # --- DYNAMIC TRANSLATION UPDATE HANDLER ---
    def update_ui_labels():
        window.set_title(_t("pref_title"))
        home_group.set_title(_t("pref_group_home"))
        current_home_row.set_title(_t("pref_row_home_config"))
        
        c_title = clean_title(current_url, current_title) if current_url else None
        use_current_row.set_title(_t("pref_row_use_current"))
        use_current_row.set_subtitle(_t("pref_sub_use_current", title=c_title) if c_title else _t("pref_sub_no_page"))
        
        reset_row.set_title(_t("pref_row_reset_default"))
        reset_row.set_subtitle(_t("pref_sub_reset_default"))
        
        ui_group.set_title(_t("pref_group_ui"))
        show_home_switch.set_title(_t("pref_row_show_home"))
        show_home_switch.set_subtitle(_t("pref_sub_show_home"))
        
        startup_group.set_title(_t("pref_group_startup"))
        behavior_combo.set_title(_t("pref_row_startup_action"))
        
        sel_startup = behavior_combo.get_selected()
        behavior_combo.set_model(Gtk.StringList.new([_t("pref_opt_restore"), _t("pref_opt_home")]))
        behavior_combo.set_selected(sel_startup)
        
        page_home = view_stack.get_page(scroll_home_page)
        page_home.set_title(_t("tab_home_page"))
        
        lang_group.set_title(_t("pref_group_language"))
        lang_combo.set_title(_t("pref_row_language"))
        sync_notion_switch.set_title(_t("pref_row_sync_notion_lang"))
        sync_notion_switch.set_subtitle(_t("pref_sub_sync_notion_lang"))
        
        page_lang = view_stack.get_page(scroll_language)
        page_lang.set_title(_t("tab_language"))
        
        icon_group.set_title(_t("pref_group_icon"))
        current_icon_row.set_title(_t("pref_row_icon_in_use"))
        current_icon_row.set_subtitle(get_icon_status_label(current_settings["icon"]))
        
        default_icon_row.set_title(_t("pref_row_icon_default"))
        default_icon_row.set_subtitle(_t("pref_sub_icon_default"))
        btn_apply_default.set_label(_t("pref_btn_apply"))
        
        custom_icon_row.set_title(_t("pref_row_icon_custom"))
        custom_icon_row.set_subtitle(_t("pref_sub_icon_custom"))
        
        page_icon = view_stack.get_page(scroll_icon)
        page_icon.set_title(_t("tab_icon"))

    def on_lang_changed(combo, pspec):
        sel_idx = combo.get_selected()
        selected_lang_code = lang_codes[sel_idx]
        LanguageManager.initialize(selected_lang_code)
        
        # Save temporary changes to config dictionary so they apply to window
        config["language"] = selected_lang_code
        config["sync_notion_lang"] = sync_notion_switch.get_active()
        
        # Dynamic label updates
        update_ui_labels()
        
        # Notify the parent window
        save_callback()

    lang_combo.connect("notify::selected", on_lang_changed)

    def on_close_request(win):
        # Save values to config dict
        config["home_url"] = current_settings["home_url"]
        config["home_title"] = current_settings["home_title"]
        config["icon"] = current_settings["icon"]
        config["show_home_button"] = show_home_switch.get_active()
        config["startup_behavior"] = "restore" if behavior_combo.get_selected() == 0 else "home"
        
        # Save language configuration
        selected_lang_code = lang_codes[lang_combo.get_selected()]
        config["language"] = selected_lang_code
        config["sync_notion_lang"] = sync_notion_switch.get_active()
        
        save_callback()
        
    window.connect("close-request", on_close_request)
    window.present()
