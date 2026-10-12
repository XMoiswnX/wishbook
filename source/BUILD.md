# Build

Python 3.12, standard library only for the program itself. The release exe is compiled with [Nuitka](https://nuitka.net/) (on Windows it downloads a C compiler on first use).

```
pip install nuitka
cd source
python tools/build_locales.py
set PYTHONPATH=sync
python -m nuitka --onefile --windows-console-mode=disable --assume-yes-for-downloads --windows-icon-from-ico=icon.ico --include-module=game_icons --include-module=icon_data --include-module=ui_page --include-module=locale_data --output-filename=wishbook.exe sync/wishbook_sync.py
```

The program's texts are in `locales/program/*.json` (see `locales/README.md`); `tools/build_locales.py` bakes them into `sync/locale_data.py`, so the exe stays a single file.

Compiling again gives a working exe but not a byte-identical one, so the SHA-256 in the README only proves "this is the file that was published", not "it equals the source".

The program reads the gacha-history URL that each game already wrote to your own PC (logs/cache), fetches the records from the game's official API, and uploads them to your Wishbook account. `DEFAULT_SERVER` in `sync/wishbook_sync.py` is the only server it talks to besides the games' official APIs.
