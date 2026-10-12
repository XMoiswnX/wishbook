# Wishbook

Gacha record tracker for Genshin Impact, Honkai: Star Rail, Zenless Zone Zero and Wuthering Waves.

- Website: https://wishbook.xmoiswnx.workers.dev
- Download: see **Releases** on the right

## How it works

The sync program reads the gacha history your game already saved on your own PC and uploads it to your Wishbook account. It does not modify game files, inject into the game, or ask for your game password.

Login uses Discord or Google (identify only; no e-mail is stored). Your data is private by default.

## License

The source code in `source/` is released under the MIT License (see `LICENSE`). The license covers the code only, not the game names or icons below.

## Credits

Wishbook is an unofficial fan tool and is not affiliated with HoYoverse or Kuro Games. Game names and game icons belong to their owners (HoYoverse, Kuro Games).

The page font is jf-openhuninn (justfont, SIL OFL 1.1).

## Verify the download

SHA-256 of `wishbook.exe` 0.2.0:

```
1d18c4a78bf38dd3f05eb5a46de6e46dfb233dcfaa1fa6c2028dbdcd958a5c36
```

PowerShell: `Get-FileHash .\wishbook.exe -Algorithm SHA256`

Edge / Windows SmartScreen may say "can't verify this file" because the exe is new and not code-signed. In Edge: click `...` on the download → Keep → Show more → Keep anyway. If Windows shows a blue window: More info → Run anyway.
