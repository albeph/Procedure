# Adding Translations to Procedure

Procedure supports multilingual translation using static JSON translation files.

To add a new translation, follow these steps:

1. Create a new JSON file named `<lang_code>.json` (where `<lang_code>` is the ISO 639-1 two-letter code, e.g., `fr.json` for French, `es.json` for Spanish) inside this directory.
2. Copy all keys from `en.json` (or `it.json`) and translate the values into the target language.
3. The application will automatically discover the new language file, load it, and display it as an option in the Preferences dialog under **Language**.

## Translation File Schema
Ensure that you preserve the JSON format and format placeholders like `{status}` or `{title}` exactly as they are used in the default templates, as the application interpolates values dynamically.
