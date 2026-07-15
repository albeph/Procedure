import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

class ShortcutsManager:
    """
    Manages layout bindings for keyboard shortcuts using GTK4 ShortcutController.
    """
    @staticmethod
    def setup_shortcuts(window):
        """Sets up key triggers and maps them to respective window methods."""
        controller = Gtk.ShortcutController()
        
        # Shortcut definition list (key, method name on window)
        shortcuts = [
            ("<Control>t", "shortcut_new_tab"),
            ("<Control>w", "shortcut_close_tab"),
            ("<Control>Tab", "shortcut_next_tab"),
            ("<Control><Shift>Tab", "shortcut_prev_tab"),
            ("<Control>r", "shortcut_reload"),
            ("F5", "shortcut_reload"),
            ("<Control>z", "shortcut_undo"),
            ("<Control>y", "shortcut_redo"),
            ("<Control><Shift>z", "shortcut_redo")
        ]
        
        for keys, method_name in shortcuts:
            trigger = Gtk.ShortcutTrigger.parse_string(keys)
            # Create a callback action that calls the window's method
            callback_func = getattr(window, method_name)
            action = Gtk.CallbackAction.new(lambda w, a, m=callback_func: m(w, a))
            controller.add_shortcut(Gtk.Shortcut.new(trigger, action))
            
        window.add_controller(controller)
