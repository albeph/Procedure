import os
import json
import locale
import sys
from config import RESOURCES_DIR, VERBOSE

class LanguageManager:
    _translations = {}
    _current_lang = "en"
    _available_languages = {} # dict of code -> display name e.g. "it" -> "Italiano"
    
    @classmethod
    def initialize(cls, config_lang=None):
        """Initializes translation map and sets selected locale."""
        locales_dir = os.path.join(RESOURCES_DIR, "locales")
        
        # Mapping for display names
        display_names = {
            "en": "English",
            "it": "Italiano",
            "fr": "Français",
            "es": "Español",
            "de": "Deutsch"
        }
        
        # Scan locales directory for JSON files
        cls._available_languages = {}
        if os.path.exists(locales_dir):
            for file in os.listdir(locales_dir):
                if file.endswith(".json"):
                    code = file.split(".json")[0]
                    name = display_names.get(code, code.upper())
                    cls._available_languages[code] = name
                    
        if not cls._available_languages:
            # Fallback if no files found
            cls._available_languages = {"en": "English", "it": "Italiano"}
            
        # Determine language code to load
        if config_lang and config_lang in cls._available_languages:
            cls._current_lang = config_lang
        else:
            # Auto detect from system
            try:
                system_lang = locale.getlocale()[0]
                if system_lang:
                    code = system_lang.split("_")[0]
                    if code in cls._available_languages:
                        cls._current_lang = code
                    else:
                        cls._current_lang = "en"
                else:
                    cls._current_lang = "en"
            except Exception:
                cls._current_lang = "en"
                
        # Load translations
        cls._translations = {}
        # Load English as base fallback first
        cls._load_file("en", locales_dir)
        # Load selected language to override English
        if cls._current_lang != "en":
            cls._load_file(cls._current_lang, locales_dir)

    @classmethod
    def _load_file(cls, lang_code, locales_dir):
        file_path = os.path.join(locales_dir, f"{lang_code}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    cls._translations.update(json.load(f))
            except Exception as e:
                if VERBOSE:
                    print(f"[ERROR] Failed to load language {lang_code}: {e}", file=sys.stderr)

    @classmethod
    def get_current_language(cls):
        return cls._current_lang

    @classmethod
    def get_available_languages(cls):
        return cls._available_languages

    @classmethod
    def translate(cls, key, **kwargs):
        """Translates a key, interpolating any kwargs."""
        text = cls._translations.get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                pass
        return text

# Global translation helper function
def _t(key, **kwargs):
    return LanguageManager.translate(key, **kwargs)
