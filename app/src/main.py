import os
import sys
import json

# Define configuration directory and file path
CONFIG_DIR = os.path.expanduser("~/.config/procedure")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# Load language settings early before ANY gi/GTK/WebKit initialization
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

# Force process environment variables if sync with Notion is enabled
# This must happen before importing gi/GTK/WebKit so the process locale is correctly inherited!
if sync_notion:
    from config import local_res_dir, installed_res_dir
    res_dir = local_res_dir if os.path.exists(local_res_dir) else installed_res_dir
    locales_dir = os.path.join(res_dir, "locales")
    available_langs = []
    if os.path.exists(locales_dir):
        available_langs = [f.split(".json")[0] for f in os.listdir(locales_dir) if f.endswith(".json")]
    
    current_lang = "en"
    if lang and lang in available_langs:
        current_lang = lang
    else:
        import locale
        try:
            sys_lang = locale.getlocale()[0]
            if sys_lang:
                code = sys_lang.split("_")[0]
                if code in available_langs:
                    current_lang = code
        except Exception:
            pass
            
    locale_map = {
        "en": "en_US.UTF-8",
        "it": "it_IT.UTF-8"
    }
    target_locale = locale_map.get(current_lang, f"{current_lang}_{current_lang.upper()}.UTF-8")
    os.environ["LANGUAGE"] = current_lang
    os.environ["LANG"] = target_locale
    os.environ["LC_ALL"] = target_locale

# Now import gi and require Adw / WebKit / Gio versions safely
import gi
gi.require_version('Adw', '1')
gi.require_version('Gio', '2.0')
from gi.repository import Adw, Gio

from language_manager import LanguageManager
LanguageManager.initialize(lang)

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
    app = ProcedureApplication()
    sys.exit(app.run(sys.argv))
