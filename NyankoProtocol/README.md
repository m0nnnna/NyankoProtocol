# Nyanko Protocol

A small helper tool for **Blue Protocol: Star Resonance** ? a daily & weekly task tracker with a cozy cat theme. Track your dailies, weeklies, and optional build info in the terminal.

```
   /\_/\     ?  N y a n k o   P r o t o c o l  ?
  ( >w< )    Blue Protocol: Star Resonance
   > ^ <     Daily & Weekly Task Tracker ~nyaa!
```

## Features

- **Daily & weekly checklists** ? Pre-filled from common guides (e.g. Maxroll): Unstable Space, Bureau Commissions, Guild tasks, World Boss Crusade, Bane Lord, raids, and more.
- **Reset countdowns** ? Live countdown to next daily reset (5:00 AM local) and weekly reset (Monday 5:00 AM local). Your checklist auto-clears when a reset passes.
- **Build summary (optional)** ? Import a Maxroll build guide URL to see gearing, food, and serum at a glance in a ?Build? tab. Requires the optional `maxroll_scraper` module.
- **Persistent progress** ? Checkboxes are saved to `%APPDATA%\NyankoProtocol\checklist.json` and restored when you reopen the app.
- **Windows-only** ? Uses the Windows console and keyboard input (arrow keys, Space, Tab, etc.).

## Requirements

- **Windows** (uses `msvcrt` for key input)
- **Python 3.12+** (or 3.8+)
- **rich** ? for colored terminal UI (`pip install rich`)

Optional for build import:

- **maxroll_scraper** ? place `maxroll_scraper.py` in the same folder (or on `PYTHONPATH`) to enable ?Import build? from Maxroll URLs.

## Quick start

```bash
pip install -r requirements.txt
python nyanko_protocol.py
```

If you don?t have `rich`, the script will try to install it automatically when you run it.

## Controls

| Key        | Action                    |
|-----------|---------------------------|
| **? / ?** | Move cursor               |
| **Space** | Toggle task done/undone   |
| **Tab**   | Switch section (Daily ? Weekly ? Build) |
| **I**     | Import Maxroll build guide (prompts for URL) |
| **T**     | Show/hide tips            |
| **Q**     | Quit                      |

## Building an executable

To build a single `.exe` with PyInstaller:

```bash
pip install pyinstaller rich
pyinstaller --onefile --console --name NyankoProtocol nyanko_protocol.py
```

The output will be in `dist/NyankoProtocol.exe`. You can also use the included `NyankoProtocol.spec` (e.g. if you have an icon or extra modules like `maxroll_scraper`):

```bash
pyinstaller NyankoProtocol.spec
```

## Data & reset logic

- **Save file:** `%APPDATA%\NyankoProtocol\checklist.json`
- **Daily reset:** 5:00 AM in your **local time**.
- **Weekly reset:** Monday 5:00 AM local. Task lists are cleared automatically after each daily/weekly reset.

Task list and reset times are based on common community info (e.g. Maxroll?s Blue Protocol guides). Adjust in-game if your server differs.

## License

Use and modify as you like. Have fun and don?t furr-get your dailies, nya~!
