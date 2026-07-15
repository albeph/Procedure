import gi
gi.require_version('Soup', '3.0')
from gi.repository import Soup, GLib

def cookie_to_dict(cookie):
    """
    Serializes a Soup.Cookie GObject into a standard Python dictionary.
    """
    d = {
        "name": cookie.get_name(),
        "value": cookie.get_value(),
        "domain": cookie.get_domain(),
        "path": cookie.get_path(),
        "secure": cookie.get_secure(),
        "http_only": cookie.get_http_only(),
    }
    expires = cookie.get_expires()
    if expires:
        d["expires_unix"] = expires.to_unix()
    return d


def dict_to_cookie(d):
    """
    Deserializes a Python dictionary back into a Soup.Cookie GObject.
    """
    cookie = Soup.Cookie.new(d["name"], d["value"], d["domain"], d["path"], -1)
    cookie.set_secure(d["secure"])
    cookie.set_http_only(d["http_only"])
    if "expires_unix" in d:
        dt = GLib.DateTime.new_from_unix_utc(d["expires_unix"])
        cookie.set_expires(dt)
    return cookie
