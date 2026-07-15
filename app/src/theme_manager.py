import gi
gi.require_version('WebKit', '6.0')
from gi.repository import WebKit

class ThemeManager:
    """
    Manages stylesheets and JavaScript injections to synchronize
    the internal Notion web view theme with the GNOME system-wide theme setting.
    """
    @staticmethod
    def apply_theme(webview, is_dark, run_now=False):
        """
        Injects CSS color-scheme rules and updates localStorage parameters in WebKit.
        """
        color_scheme = "dark" if is_dark else "light"
        css = f"html {{ color-scheme: {color_scheme} !important; }}"
        
        ucm = webview.get_user_content_manager()
        ucm.remove_all_style_sheets()
        ucm.remove_all_scripts()
        
        style_sheet = WebKit.UserStyleSheet.new(
            css,
            WebKit.UserContentInjectedFrames.ALL_FRAMES,
            WebKit.UserStyleLevel.USER,
            None,
            None
        )
        ucm.add_style_sheet(style_sheet)
        
        js_code = f"""
        try {{
            localStorage.setItem("theme", JSON.stringify({{"mode": "{color_scheme}"}}));
        }} catch(e) {{}}
        """
        
        user_script = WebKit.UserScript.new(
            js_code,
            WebKit.UserContentInjectedFrames.ALL_FRAMES,
            WebKit.UserScriptInjectionTime.START,
            None,
            None
        )
        ucm.add_script(user_script)
        
        if run_now:
            webview.evaluate_javascript(js_code, -1, None, None, None, lambda w, r, *d: None, None)
