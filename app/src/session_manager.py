import os
import sys
import json
import gi
gi.require_version('Secret', '1')
gi.require_version('WebKit', '6.0')
from gi.repository import Secret, WebKit, GLib

from config import CONFIG_DIR, VERBOSE
from helpers import cookie_to_dict, dict_to_cookie

class SessionManager:
    """
    Manages directories, volatile RAM paths, cookie load/save callbacks,
    and secure shredding of volatile local data.
    """
    def __init__(self):
        self.keyring_available = False
        self._check_keyring()
        self._setup_paths()

    def _check_keyring(self):
        """Verifies if the GNOME Keyring secret service is active and responsive."""
        try:
            Secret.Schema.new(
                "io.github.albeph.Procedure.Cookies",
                Secret.SchemaFlags.NONE,
                {"app": Secret.SchemaAttributeType.STRING}
            )
            self.keyring_available = True
        except Exception as e:
            if VERBOSE:
                print(f"[WARNING] GNOME Keyring non disponibile: {e}", file=sys.stderr)

    def _setup_paths(self):
        """Creates persistent config and volatile RAM-disk storage paths."""
        uid = os.getuid()
        run_user_dir = f"/run/user/{uid}"
        
        # Select User RAM-disk directory if available, otherwise fallback to system shared memory
        if os.path.exists(run_user_dir):
            self.volatile_dir = os.path.join(run_user_dir, "procedure")
        else:
            self.volatile_dir = f"/dev/shm/procedure-{uid}"
            
        self.volatile_data_dir = os.path.join(self.volatile_dir, "data")
        self.cache_dir = os.path.join(CONFIG_DIR, "cache")
        
        # Apply secure directory permissions (0700 - owner only)
        os.makedirs(CONFIG_DIR, mode=0o700, exist_ok=True)
        os.chmod(CONFIG_DIR, 0o700)
        os.makedirs(self.volatile_dir, mode=0o700, exist_ok=True)
        os.chmod(self.volatile_dir, 0o700)
        os.makedirs(self.volatile_data_dir, mode=0o700, exist_ok=True)
        os.chmod(self.volatile_data_dir, 0o700)
        os.makedirs(self.cache_dir, mode=0o700, exist_ok=True)
        os.chmod(self.cache_dir, 0o700)

    def load_cookies(self, network_session):
        """Retrieves cookie list from GNOME Keyring and injects back to WebKit memory."""
        if not self.keyring_available:
            return
        try:
            schema = Secret.Schema.new(
                "io.github.albeph.Procedure.Cookies",
                Secret.SchemaFlags.NONE,
                {"app": Secret.SchemaAttributeType.STRING}
            )
            attrs = {"app": "procedure"}
            
            json_data = Secret.password_lookup_sync(schema, attrs, None)
            if json_data:
                serialized = json.loads(json_data)
                cookie_manager = network_session.get_cookie_manager()
                for d in serialized:
                    try:
                        cookie = dict_to_cookie(d)
                        cookie_manager.add_cookie(cookie, None, lambda *args: None, None)
                    except Exception as ex:
                        if VERBOSE:
                            print(f"[WARNING] Errore nel caricamento del cookie: {ex}", file=sys.stderr)
        except Exception as e:
            if VERBOSE:
                print(f"[ERROR] Caricamento dei cookie dal portachiavi fallito: {e}", file=sys.stderr)

    def save_cookies(self, cookies_list):
        """Serializes relevant cookies and stores them directly into GNOME Keyring."""
        if not self.keyring_available:
            return
        try:
            serialized = []
            for c in cookies_list:
                domain = c.get_domain()
                is_relevant = any(domain.endswith(d) for d in [".notion.so", "notion.so", ".notion.com", "notion.com", ".notion.new", "notion.new"])
                if not is_relevant:
                    auth_domains = ["google.com", "apple.com", "microsoftonline.com", "github.com"]
                    is_relevant = any(ad in domain for ad in auth_domains)
                if is_relevant:
                    serialized.append(cookie_to_dict(c))
            json_data = json.dumps(serialized)
            schema = Secret.Schema.new(
                "io.github.albeph.Procedure.Cookies",
                Secret.SchemaFlags.NONE,
                {"app": Secret.SchemaAttributeType.STRING}
            )
            attrs = {"app": "procedure"}
            Secret.password_store_sync(
                schema,
                attrs,
                Secret.COLLECTION_DEFAULT,
                "Procedure Saved Session Cookies",
                json_data,
                None
            )
        except Exception as e:
            if VERBOSE:
                print(f"[ERROR] Salvataggio dei cookie nel portachiavi fallito: {e}", file=sys.stderr)

    def clear_keyring_cookies(self):
        """Clears all session cookie entries from GNOME Keyring."""
        if not self.keyring_available:
            return
        try:
            schema = Secret.Schema.new(
                "io.github.albeph.Procedure.Cookies",
                Secret.SchemaFlags.NONE,
                {"app": Secret.SchemaAttributeType.STRING}
            )
            attrs = {"app": "procedure"}
            Secret.password_clear_sync(schema, attrs, None)
        except Exception as e:
            if VERBOSE:
                print(f"[ERROR] Errore nella cancellazione del portachiavi: {e}", file=sys.stderr)

    def cleanup_volatile(self):
        """Shreds (fills with zero-bytes) and deletes the active volatile data folder."""
        if os.path.exists(self.volatile_data_dir):
            try:
                for root, dirs, files in os.walk(self.volatile_data_dir):
                    for file in files:
                        fpath = os.path.join(root, file)
                        try:
                            size = os.path.getsize(fpath)
                            if size > 0:
                                with open(fpath, "ba+", buffering=0) as f:
                                    f.write(b'\x00' * size)
                        except Exception:
                            pass
                        os.remove(fpath)
                import shutil
                shutil.rmtree(self.volatile_data_dir, ignore_errors=True)
            except Exception as e:
                if VERBOSE:
                    print(f"[ERROR] Pulizia directory volatile fallita: {e}", file=sys.stderr)
