import os
import sys
import json
import urllib.parse
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')
gi.require_version('Gio', '2.0')
from gi.repository import Gtk, Adw, WebKit, Gio, GLib

from config import CONFIG_FILE, USER_AGENT, VERBOSE
from session_manager import SessionManager
from shortcuts_manager import ShortcutsManager
from theme_manager import ThemeManager
from language_manager import _t, LanguageManager
import dialogs

class ProcedureWindow(Adw.ApplicationWindow):
    """
    Main application window subclassing Adw.ApplicationWindow.
    Draws navigation header bars, tracks WebView states, Restores config session,
    handles tabs list updates and redirects external URLs.
    """

    def __init__(self, **kwargs):
        """Initializes window states, configures files, registers cleanups, and builds UI."""
        super().__init__(**kwargs)
        self.set_title("Procedure")
        self.set_default_size(1024, 768)
        
        # Load window geometry state
        self.load_config()
        
        # Setup session path managers
        self.session_manager = SessionManager()
        self.network_session = WebKit.NetworkSession.new(
            self.session_manager.volatile_data_dir, 
            self.session_manager.cache_dir
        )
        
        # UI & Controls initialization
        self._setup_ui()
        ShortcutsManager.setup_shortcuts(self)
        self._setup_actions()
        
        # Theme observer initialization
        self.style_manager = Adw.StyleManager.get_default()
        self.style_manager.connect("notify::dark", self.on_system_theme_changed)
        
        # Restore session tabs list
        if self.session_manager.keyring_available:
            self.session_manager.load_cookies(self.network_session)
            self.open_initial_tabs()
            
            # Watch cookie manager changes to sync back to Keyring
            cookie_manager = self.network_session.get_cookie_manager()
            cookie_manager.connect("changed", self.on_cookies_changed)
        else:
            GLib.idle_add(self.show_keyring_warning)
            
        self.connect("close-request", self.on_close_request)

    def _setup_ui(self):
        """Constructs window box containers, header bars, buttons, and tab managers."""
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(self.main_box)
        
        self.header_bar = Adw.HeaderBar()
        self.main_box.append(self.header_bar)
        
        # Left navigation controls (Back, Reload)
        self.nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.nav_box.add_css_class("linked")
        
        self.btn_back = Gtk.Button.new_from_icon_name("go-previous-symbolic")
        self.btn_back.connect("clicked", self.on_back_clicked)
        self.nav_box.append(self.btn_back)
        
        self.btn_reload = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
        self.btn_reload.connect("clicked", self.on_reload_clicked)
        self.nav_box.append(self.btn_reload)
        self.header_bar.pack_start(self.nav_box)
        
        # Home button (separate, not linked to the nav_box)
        self.btn_home = Gtk.Button.new_from_icon_name("go-home-symbolic")
        self.btn_home.set_tooltip_text(_t("tooltip_home"))
        self.btn_home.connect("clicked", self.on_home_clicked)
        self.btn_home.set_visible(self.config.get("show_home_button", True))
        self.header_bar.pack_start(self.btn_home)
        
        # Add new tab (+) button
        self.btn_new_tab = Gtk.Button.new_from_icon_name("list-add-symbolic")
        self.btn_new_tab.set_tooltip_text(_t("tooltip_new_tab"))
        self.btn_new_tab.connect("clicked", lambda b: self.open_new_tab())
        self.header_bar.pack_start(self.btn_new_tab)
        
        # Dropdown options menu button
        self.menu_button = Gtk.MenuButton()
        self.menu_button.set_icon_name("view-more-symbolic")
        self.menu_button.set_tooltip_text(_t("tooltip_main_menu"))
        
        menu_model = Gio.Menu()
        menu_model.append(_t("menu_about"), "win.about")
        menu_model.append(_t("menu_encryption"), "win.encryption_info")
        menu_model.append(_t("menu_preferences"), "win.preferences")
        menu_model.append(_t("menu_logout"), "win.logout")
        self.menu_button.set_menu_model(menu_model)
        self.header_bar.pack_end(self.menu_button)
        
        # Tab view pages manager container
        self.tab_view = Adw.TabView()
        self.tab_view.set_vexpand(True)
        self.tab_view.set_hexpand(True)
        self.tab_view.connect("close-page", self.on_close_page)
        self.tab_view.connect("notify::selected-page", self.on_selected_page_changed)
        self.main_box.append(self.tab_view)
        
        # Center tabbar in header bar
        self.tab_bar = Adw.TabBar()
        self.tab_bar.set_view(self.tab_view)
        self.tab_bar.set_hexpand(True)
        self.header_bar.set_title_widget(self.tab_bar)

    def _setup_actions(self):
        """Registers SimpleAction triggers for menu buttons."""
        actions = [
            ("about", lambda a, p: dialogs.show_about_dialog(self)),
            ("encryption_info", lambda a, p: dialogs.show_encryption_info_dialog(self, self.session_manager.keyring_available)),
            ("preferences", self.on_preferences_activated),
            ("logout", self.on_logout_activated)
        ]
        for name, callback in actions:
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", callback)
            self.add_action(action)

    # --------------------------------------------------------------------------
    # Configuration and Geometry Actions
    # --------------------------------------------------------------------------

    def load_config(self):
        """Loads last width, height, and active tab lists from config.json."""
        self.config = {
            "width": 1024, 
            "height": 768, 
            "tabs": ["https://app.notion.com/home"],
            "home_url": "https://app.notion.com/home",
            "home_title": _t("home_default_title"),
            "show_home_button": True,
            "startup_behavior": "restore",
            "language": None,
            "sync_notion_lang": True
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    loaded = json.load(f)
                    self.config.update(loaded)
            except Exception:
                pass
        self.set_default_size(self.config.get("width", 1024), self.config.get("height", 768))

    def save_config(self):
        """Saves current window size and open Notion tab list to config.json."""
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        width = self.get_width()
        height = self.get_height()
        tab_uris = []
        for i in range(self.tab_view.get_n_pages()):
            page = self.tab_view.get_nth_page(i)
            webview = page.get_child()
            uri = webview.get_uri()
            if uri and uri != "about:blank" and "unsupported-browser" not in uri:
                tab_uris.append(uri)
        if not tab_uris:
            tab_uris = [self.config.get("home_url", "https://app.notion.com/home")]
        self.config["width"] = width
        self.config["height"] = height
        self.config["tabs"] = tab_uris
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f)
        except Exception as e:
            if VERBOSE:
                print(f"[ERROR] Impossibile salvare config: {e}", file=sys.stderr)

    def apply_new_icon(self, icon_type):
        """Applies chosen icon theme to system path and updates desktop environment cache."""
        self.config["icon"] = icon_type
        self.save_config()
        
        import shutil
        import subprocess
        from config import RESOURCES_DIR
        
        src_file = os.path.join(RESOURCES_DIR, "icon.png")
        if os.path.exists(src_file):
            dest_dir = os.path.expanduser("~/.local/share/icons/hicolor/512x512/apps")
            os.makedirs(dest_dir, exist_ok=True)
            dest_file = os.path.join(dest_dir, "io.github.albeph.Procedure.png")
            try:
                shutil.copy2(src_file, dest_file)
                # Update icon cache
                subprocess.Popen(
                    ["gtk-update-icon-cache", "-f", "-t", os.path.expanduser("~/.local/share/icons/hicolor")],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except Exception as e:
                if VERBOSE:
                    print(f"[ERROR] Impossibile applicare l'icona: {e}", file=sys.stderr)



    def apply_custom_png_file(self, file_path):
        """Copies custom chosen PNG file to host application icon directory."""
        if not file_path or not file_path.lower().endswith(".png"):
            return
            
        self.config["icon"] = "custom"
        self.save_config()
        
        import shutil
        import subprocess
        
        dest_dir = os.path.expanduser("~/.local/share/icons/hicolor/512x512/apps")
        os.makedirs(dest_dir, exist_ok=True)
        dest_file = os.path.join(dest_dir, "io.github.albeph.Procedure.png")
        try:
            shutil.copy2(file_path, dest_file)
            # Update icon cache
            subprocess.Popen(
                ["gtk-update-icon-cache", "-f", "-t", os.path.expanduser("~/.local/share/icons/hicolor")],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            if VERBOSE:
                print(f"[ERROR] Impossibile applicare l'icona personalizzata: {e}", file=sys.stderr)

    def on_close_request(self, window):
        """Saves session configurations and purges volatile directory paths."""
        self.save_config()
        self.session_manager.cleanup_volatile()
        return False

    # --------------------------------------------------------------------------
    # Tab View Navigation and Initialization
    # --------------------------------------------------------------------------

    def open_initial_tabs(self):
        """Restores tabs list or loads home page based on startup preferences."""
        behavior = self.config.get("startup_behavior", "restore")
        home_url = self.config.get("home_url", "https://app.notion.com/home")
        
        if behavior == "home":
            tabs = [home_url]
        else:
            tabs = self.config.get("tabs", [home_url])
            if not tabs:
                tabs = [home_url]
                
        for tab_url in tabs:
            self.open_new_tab(tab_url)
            
        if self.tab_view.get_n_pages() == 0:
            self.open_new_tab(home_url)

    def open_new_tab(self, url=None):
        """
        Creates and appends a new tab. Duplicates active tab URI if url is None.
        
        Args:
            url (str, optional): Target URI to load. Defaults to None.
            
        Returns:
            Adw.TabPage: The created Libadwaita tab page container.
        """
        home_url = self.config.get("home_url", "https://app.notion.com/home")
        if url is None:
            active_wv = self.get_active_webview()
            if active_wv:
                url = active_wv.get_uri()
            if not url or url == "about:blank" or "unsupported-browser" in url:
                url = home_url
                
        # Initialize WebKit WebView
        webview = WebKit.WebView(network_session=self.network_session)
        webview.set_vexpand(True)
        webview.set_hexpand(True)
        
        # Configure user agent signature
        settings = webview.get_settings()
        settings.set_user_agent(USER_AGENT)
        if VERBOSE:
            settings.set_enable_developer_extras(True)
            settings.set_enable_write_console_messages_to_stdout(True)
            
        # Injects default dark/light preferences
        ThemeManager.apply_theme(webview, self.style_manager.get_dark(), run_now=False)
        webview.load_uri(url)
        
        page = self.tab_view.add_page(webview, None)
        page.set_title(_t("tab_new"))
        
        # Bind page indicators using GObject notify signals
        webview.connect("notify::title", lambda w, p: page.set_title(w.get_title() or _t("app_name")))
        webview.connect("notify::is-loading", lambda w, p: page.set_loading(w.is_loading()))
        webview.connect("notify::uri", lambda w, p: self.update_nav_buttons())
        
        # Connect WebKit callbacks
        webview.connect("load-changed", self.on_webview_load_changed)
        webview.connect("decide-policy", self.on_decide_policy)
        webview.connect("create", self.on_webview_create)
        webview.connect("load-failed", self.on_webview_load_failed)
        webview.connect("load-failed-with-tls-errors", self.on_webview_load_failed_with_tls_errors)
        webview.connect("web-process-terminated", self.on_web_process_terminated)
        
        self.tab_view.set_selected_page(page)
        self.update_nav_buttons()
        return page

    def get_active_webview(self):
        """Returns the active WebView widget currently focused."""
        page = self.tab_view.get_selected_page()
        if page:
            return page.get_child()
        return None

    def on_selected_page_changed(self, tab_view, spec):
        """Triggered when tab selection switches."""
        self.update_nav_buttons()

    def update_nav_buttons(self):
        """Disables/enables Back button based on active WebView history state."""
        webview = self.get_active_webview()
        if webview:
            self.btn_back.set_sensitive(webview.can_go_back())
        else:
            self.btn_back.set_sensitive(False)

    def on_back_clicked(self, btn):
        """Goes back in history of active WebView."""
        webview = self.get_active_webview()
        if webview and webview.can_go_back():
            webview.go_back()

    def on_reload_clicked(self, btn):
        """Reloads current active WebView page."""
        webview = self.get_active_webview()
        if webview:
            webview.reload()

    def on_close_page(self, tab_view, page):
        """Closes target tab page. Closes window if it's the last page left."""
        if tab_view.get_n_pages() <= 1:
            self.close()
        else:
            tab_view.close_page_finish(page, True)
        return True

    # --------------------------------------------------------------------------
    # WebView Event and Signal Handlers
    # --------------------------------------------------------------------------

    def on_webview_load_changed(self, webview, event):
        """Fires on load status changes."""
        self.update_nav_buttons()

    def on_webview_create(self, webview, navigation_action):
        """Fires when link triggers window.open() or target='_blank'."""
        uri = navigation_action.get_request().get_uri()
        if uri and uri != "about:blank" and not self.is_internal_uri(uri):
            Gio.AppInfo.launch_default_for_uri(uri, None)
            return None
            
        new_webview = WebKit.WebView(related_view=webview)
        new_webview.set_vexpand(True)
        new_webview.set_hexpand(True)
        ThemeManager.apply_theme(new_webview, self.style_manager.get_dark(), run_now=False)
        
        page = self.tab_view.add_page(new_webview, None)
        page.set_title(_t("tab_new"))
        
        new_webview.connect("notify::title", lambda w, p: page.set_title(w.get_title() or _t("app_name")))
        new_webview.connect("notify::is-loading", lambda w, p: page.set_loading(w.is_loading()))
        new_webview.connect("notify::uri", lambda w, p: self.update_nav_buttons())
        new_webview.connect("load-changed", self.on_webview_load_changed)
        new_webview.connect("decide-policy", self.on_decide_policy)
        new_webview.connect("create", self.on_webview_create)
        new_webview.connect("load-failed", self.on_webview_load_failed)
        new_webview.connect("load-failed-with-tls-errors", self.on_webview_load_failed_with_tls_errors)
        new_webview.connect("web-process-terminated", self.on_web_process_terminated)
        
        self.tab_view.set_selected_page(page)
        return new_webview

    def on_decide_policy(self, webview, decision, decision_type):
        """Intercepts page loading policies to filter out external navigation attempts."""
        if decision_type == WebKit.PolicyDecisionType.NAVIGATION_ACTION:
            nav_action = decision.get_navigation_action()
            uri = nav_action.get_request().get_uri()
            if uri and uri != "about:blank" and not self.is_internal_uri(uri):
                Gio.AppInfo.launch_default_for_uri(uri, None)
                decision.ignore()
                # Close newly created tabs redirected to default browser
                GLib.idle_add(self.close_tab_if_empty, webview)
                return True
        return False

    def close_tab_if_empty(self, webview):
        """Closes target tab if it has no history and there are other active tabs."""
        page = self.tab_view.get_page(webview)
        if page:
            if self.tab_view.get_n_pages() > 1:
                self.tab_view.close_page(page)
        return False

    def is_internal_uri(self, uri):
        """Determines whether target URI belongs to internal Notion features or OAuth redirects."""
        if not uri:
            return False
        parsed = urllib.parse.urlparse(uri)
        domain = parsed.netloc.lower()
        
        # Allowed domains/subdomains (Notion & Captchas)
        allowed_domains = [
            ".notion.so", "notion.so", 
            ".notion.com", "notion.com", 
            ".notion.new", "notion.new",
            ".hcaptcha.com", "hcaptcha.com",
            ".recaptcha.net", "recaptcha.net"
        ]
        if any(domain.endswith(d) for d in allowed_domains):
            return True
            
        auth_domains = [
            "accounts.google.com", "appleid.apple.com", "login.microsoftonline.com",
            "github.com/login", "github.com/sessions", "google.com/recaptcha",
            "www.google.com/recaptcha"
        ]
        if any(ad in uri for ad in auth_domains):
            return True
        return False

    # --------------------------------------------------------------------------
    # Keyring Sync Trigger Callbacks
    # --------------------------------------------------------------------------

    def on_cookies_changed(self, cookie_manager):
        """Syncs cookies list changes. Debounces calls."""
        if hasattr(self, "cookie_save_timeout_id") and self.cookie_save_timeout_id:
            GLib.source_remove(self.cookie_save_timeout_id)
        self.cookie_save_timeout_id = GLib.timeout_add(2000, self.trigger_cookie_save, cookie_manager)

    def trigger_cookie_save(self, cookie_manager):
        """Asynchronously triggers the cookie manager list getter."""
        self.cookie_save_timeout_id = None
        cookie_manager.get_all_cookies(None, self.save_cookies_to_keyring, None)
        return False

    def save_cookies_to_keyring(self, cookie_manager, result, *args):
        """Passes retrieved cookies to session_manager to write into Keyring."""
        try:
            cookies = cookie_manager.get_all_cookies_finish(result)
            self.session_manager.save_cookies(cookies)
        except Exception as e:
            if VERBOSE:
                print(f"[ERROR] Fine recupero cookies per salvataggio fallito: {e}", file=sys.stderr)

    # --------------------------------------------------------------------------
    # Dark Theme Observer Callbacks
    # --------------------------------------------------------------------------

    def on_system_theme_changed(self, style_manager, pspec):
        """Fires on system theme switches. Synchronizes style properties."""
        for i in range(self.tab_view.get_n_pages()):
            page = self.tab_view.get_nth_page(i)
            webview = page.get_child()
            ThemeManager.apply_theme(webview, style_manager.get_dark(), run_now=True)

    # --------------------------------------------------------------------------
    # Warning Modal Fallback Callbacks
    # --------------------------------------------------------------------------

    def show_keyring_warning(self):
        """Shows warning modal popup."""
        dialogs.show_keyring_warning(self, self.on_keyring_warning_response)

    def on_keyring_warning_response(self, accepted):
        """Halts window launch or continues in temporal memory mode."""
        if accepted:
            self.open_initial_tabs()
        else:
            self.close()

    def on_logout_activated(self, action, parameter):
        """Wipes keyring secret data, sanitizes RAM directories, and closes client."""
        self.session_manager.clear_keyring_cookies()
        self.session_manager.cleanup_volatile()
        self.close()

    def on_home_clicked(self, button):
        """Navigates the focused tab to the configured home page."""
        webview = self.get_active_webview()
        if webview:
            home_url = self.config.get("home_url", "https://app.notion.com/home")
            webview.load_uri(home_url)

    def on_preferences_activated(self, action, param):
        """Shows the Libadwaita Preferences dialog."""
        active_wv = self.get_active_webview()
        current_url = active_wv.get_uri() if active_wv else None
        page = self.tab_view.get_selected_page()
        current_title = page.get_title() if page else None
        dialogs.show_preferences_dialog(
            self,
            self.config,
            current_url,
            current_title,
            self.apply_new_icon,
            self.apply_custom_png_file,
            self.on_preferences_saved
        )

    def on_preferences_saved(self):
        """Saves configuration and updates UI layout accordingly."""
        self.save_config()
        
        # Re-initialize translations
        LanguageManager.initialize(self.config.get("language"))
        
        # Update main window labels
        self.set_title(_t("app_name"))
        self.btn_home.set_tooltip_text(_t("tooltip_home"))
        self.btn_new_tab.set_tooltip_text(_t("tooltip_new_tab"))
        self.menu_button.set_tooltip_text(_t("tooltip_main_menu"))
        
        menu_model = Gio.Menu()
        menu_model.append(_t("menu_about"), "win.about")
        menu_model.append(_t("menu_encryption"), "win.encryption_info")
        menu_model.append(_t("menu_preferences"), "win.preferences")
        menu_model.append(_t("menu_logout"), "win.logout")
        self.menu_button.set_menu_model(menu_model)
        
        # Update WebKit default WebContext preferred languages on-the-fly
        sync_notion = self.config.get("sync_notion_lang", True)
        if sync_notion:
            selected_lang = LanguageManager.get_current_language()
            pref_langs = [f"{selected_lang}-{selected_lang.upper()}", selected_lang]
            try:
                WebKit.WebContext.get_default().set_preferred_languages(pref_langs)
            except Exception:
                pass
        
        # Reload all open web views to request with new headers
        for i in range(self.tab_view.get_n_pages()):
            page = self.tab_view.get_nth_page(i)
            webview = page.get_child()
            if webview:
                webview.reload()
                
        show_home = self.config.get("show_home_button", True)
        self.btn_home.set_visible(show_home)

    # --------------------------------------------------------------------------
    # Shortcut Delegation Handlers
    # --------------------------------------------------------------------------

    def shortcut_new_tab(self, widget, args):
        self.open_new_tab()
        return True

    def shortcut_close_tab(self, widget, args):
        page = self.tab_view.get_selected_page()
        if page:
            self.on_close_page(self.tab_view, page)
        return True

    def shortcut_next_tab(self, widget, args):
        n = self.tab_view.get_n_pages()
        if n > 1:
            idx = self.tab_view.get_page_position(self.tab_view.get_selected_page())
            next_idx = (idx + 1) % n
            self.tab_view.set_selected_page(self.tab_view.get_nth_page(next_idx))
        return True

    def shortcut_prev_tab(self, widget, args):
        n = self.tab_view.get_n_pages()
        if n > 1:
            idx = self.tab_view.get_page_position(self.tab_view.get_selected_page())
            prev_idx = (idx - 1 + n) % n
            self.tab_view.set_selected_page(self.tab_view.get_nth_page(prev_idx))
        return True

    def shortcut_reload(self, widget, args):
        webview = self.get_active_webview()
        if webview:
            webview.reload()
        return True

    def shortcut_undo(self, widget, args):
        """Triggers Undo command in active WebView."""
        webview = self.get_active_webview()
        if webview:
            webview.execute_editing_command("Undo")
        return True

    def shortcut_redo(self, widget, args):
        """Triggers Redo command in active WebView."""
        webview = self.get_active_webview()
        if webview:
            webview.execute_editing_command("Redo")
        return True

    # --------------------------------------------------------------------------
    # WebView Diagnostics Console Alerts
    # --------------------------------------------------------------------------

    def on_webview_load_failed(self, webview, load_event, failing_uri, error):
        if VERBOSE:
            print(f"[ERROR] Caricamento fallito per {failing_uri}: {error.message}", file=sys.stderr)
        return False

    def on_webview_load_failed_with_tls_errors(self, webview, failing_uri, certificate, errors):
        if VERBOSE:
            print(f"[ERROR] Errore TLS durante il caricamento di {failing_uri}", file=sys.stderr)
        return False

    def on_web_process_terminated(self, webview, reason):
        if VERBOSE:
            print(f"[ERROR] Il processo web di WebKit è terminato in modo anomalo! Motivo: {reason}", file=sys.stderr)
