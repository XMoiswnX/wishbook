# Translations

`program/<lang>.json` holds the texts of the sync program. The key is the **English source text** (it is also what the code looks up, and what is shown when a translation is missing); the value is the translation.

| file | language |
|---|---|
| `zh.json` | Traditional Chinese |
| `zhs.json` | Simplified Chinese |
| `ja.json` | Japanese |
| `ko.json` | Korean |

- Keep placeholders such as `{n}` or `{name}` exactly as they are.
- Change only the value, never the key.
- After editing, run `python tools/build_locales.py` (writes `sync/locale_data.py`), then rebuild the exe (see `BUILD.md`).
- To add a language: add `<lang>.json` with the keys of `zh.json`, then add the code to `LANGS` in `tools/build_locales.py`, `sync/wishbook_sync.py` and the language menu in `sync/ui_page.py`.
- Pull requests with translation fixes are welcome.
