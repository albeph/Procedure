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
    app = ProcedureApplication()
    sys.exit(app.run(sys.argv))
