import sys
import gi
gi.require_version('Adw', '1')
gi.require_version('Gio', '2.0')
from gi.repository import Adw, Gio

from window import ProcedureWindow

class ProcedureApplication(Adw.Application):
    """
    Subclassing Adw.Application to manage main thread loop events.
    """
    def __init__(self):
        super().__init__(application_id='io.github.albeph.Procedure',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
                         
    def do_activate(self):
        """Initializes and presents the main application window."""
        win = self.get_active_window()
        if not win:
            win = ProcedureWindow(application=self)
        win.present()

def run():
    """Main execution trigger."""
    import os
    import json
    from config import CONFIG_FILE
    
    # Load language settings early before GTK/WebKit initialization
    lang = None
    sync_notion = True
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                conf = json.load(f)
                lang = conf.get("language")
                sync_notion = conf.get("sync_notion_lang", True)
        except Exception:
            pass

    from language_manager import LanguageManager
    LanguageManager.initialize(lang)
    
    # If sync with Notion is enabled, override process environment variables so WebKit sends it
    if sync_notion:
        selected_lang = LanguageManager.get_current_language()
        locale_map = {
            "en": "en_US.UTF-8",
            "it": "it_IT.UTF-8"
        }
        target_locale = locale_map.get(selected_lang, f"{selected_lang}_{selected_lang.upper()}.UTF-8")
        os.environ["LANGUAGE"] = selected_lang
        os.environ["LANG"] = target_locale
        os.environ["LC_ALL"] = target_locale

    app = ProcedureApplication()
    sys.exit(app.run(sys.argv))
