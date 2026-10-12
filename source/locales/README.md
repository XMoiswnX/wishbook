# Translations

The sync program's texts live in `program/<lang>.json`. Each file is a flat JSON object: the key is the source text (the Traditional Chinese text the program is written with), the value is the translation.

```
program/
  zh-Hant.json  Traditional Chinese
  zh-Hans.json  Simplified Chinese
  ja.json       Japanese
  ko.json       Korean
```

Language codes follow BCP 47 (`zh-Hant`, `zh-Hans`, `ja`, `ko`; `en` is the built-in English text).

- Keep placeholders such as `{n}` or `{name}` exactly as they are; change only the value, never the key.
- `tools/build_locales.py` bakes the files into `sync/locale_data.py`, so the exe stays a single file.

## Changing a text

1. Edit the value in `program/<lang>.json`.
2. Run `python tools/build_locales.py`, then rebuild the exe (see `../BUILD.md`).

## Adding a language

Add `<lang>.json` with every key of the existing files, then add the code to `tools/build_locales.py`, to `LANGS` in `sync/wishbook_sync.py` and to the language menu in `sync/ui_page.py`.
