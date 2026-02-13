#!/usr/bin/env python3
r"""
  /\_/\   Nyanko Protocol v1.0
 ( >w< )  Blue Protocol: Star Resonance
  > ^ <   Daily & Weekly Task Tracker
          ~nyaa!

Compile to .exe:
  pip install pyinstaller rich
  pyinstaller --onefile --console --name NyankoProtocol nyanko_protocol.py
"""

import os
import sys
import json
import time
import random
import shutil
from io import StringIO
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    from maxroll_scraper import scrape_guide
except ImportError:
    scrape_guide = None

# ── Windows check & ANSI enable ──────────────────────────────
if sys.platform != "win32":
    print("(=^・x・^=) This app is made for Windows, nya~!")
    sys.exit(1)

import msvcrt
os.system("")  # enable ANSI escape codes on Windows
# Optional: set initial size (user can resize; we read size each frame)
try:
    sz = shutil.get_terminal_size()
    if sz.columns < 80 or sz.lines < 24:
        os.system("mode con: cols=100 lines=45")
except Exception:
    os.system("mode con: cols=100 lines=45")

# ── Dependency check ─────────────────────────────────────────
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
except ImportError:
    print("(=^・ω・^=) Installing 'rich' library... hold on, nya~!")
    os.system(f'"{sys.executable}" -m pip install rich')
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box

console = Console(highlight=False)


# ╔════════════════════════════════════════════════════════════╗
# ║  🐱  NEKO THEME DATA                                      ║
# ╚════════════════════════════════════════════════════════════╝

CAT_ART = {
    "sleepy": [
        r"   /\_/\   ",
        r"  ( -.- )  ",
        r"   > ~ < z ",
    ],
    "normal": [
        r"   /\_/\   ",
        r"  ( o.o )  ",
        r"   > ^ <   ",
    ],
    "happy": [
        r"   /\_/\   ",
        r"  ( >w< )  ",
        r"   > ^ <   ",
    ],
    "love": [
        r"   /\_/\   ",
        "  ( \u2665.\u2665 )  ",
        r"   > ^ <   ",
    ],
}

NEKO_FACES = [
    "(=^\u30fb\u03c9\u30fb^=)",  # (=^・ω・^=)
    "(=^-\u03c9-^=)",            # (=^-ω-^=)
    "\u0e45^\u2022\ufe3b\u2022^\u0e45",  # ฅ^•ﻌ•^ฅ
    "(=^\u30fb^=)",              # (=^・^=)
    "~(=^\u2025^)\u30ce",       # ~(=^‥^)ノ
    "(=^\u30a7^=)",              # (=^ェ^=)
]

CAT_QUOTES = [
    "Don't furr-get your dailies, nya~!",
    "You're paw-some for doing your tasks!",
    "Meow-velous progress today!",
    "Purr-fect! Keep going~!",
    "Time to pounce on those tasks, nya!",
    "Feline good about today's progress!",
    "Whisker away those tasks, nya~!",
    "Claw-some work today!",
    "Stay paws-itive, nya~!",
    "Every task done is a little treat~!",
    "Nyan~ You're almost done!",
    "The early cat catches the quest!",
    "Believe in yourself, nya~!",
    "You've got this! Meow~!",
    "Pounce! Pounce! Get it done~!",
]

CHECK_MSGS = [
    "Nyaa~! Good job!",
    "Purr~fect!",
    "Meow~! One down!",
    "Nya~! Keep going!",
    "*purrs approvingly*",
    "Paw-some~!",
    "So productive, nya!",
    "Yatta~! Nice one!",
]

UNCHECK_MSGS = [
    "Oops, unchecked~",
    "Changed your mind, nya?",
    "Hmm, not yet?",
    "Back on the list~",
]


# ╔════════════════════════════════════════════════════════════╗
# ║  ⏰  LOCAL TIME & RESET LOGIC                              ║
# ╚════════════════════════════════════════════════════════════╝

RESET_HOUR = 5   # 5:00 AM local time
WEEKLY_DAY = 0   # Monday


def server_now():
    """Get current local time (based on user's computer timezone)"""
    return datetime.now()


def next_daily_reset():
    now = server_now()
    reset = now.replace(hour=RESET_HOUR, minute=0, second=0, microsecond=0)
    if now >= reset:
        reset += timedelta(days=1)
    return reset


def last_daily_reset():
    now = server_now()
    reset = now.replace(hour=RESET_HOUR, minute=0, second=0, microsecond=0)
    if now < reset:
        reset -= timedelta(days=1)
    return reset


def next_weekly_reset():
    now = server_now()
    reset = now.replace(hour=RESET_HOUR, minute=0, second=0, microsecond=0)
    days_ahead = (WEEKLY_DAY - now.weekday()) % 7
    if days_ahead == 0 and now >= reset:
        days_ahead = 7
    return reset + timedelta(days=days_ahead)


def last_weekly_reset():
    now = server_now()
    reset = now.replace(hour=RESET_HOUR, minute=0, second=0, microsecond=0)
    days_back = (now.weekday() - WEEKLY_DAY) % 7
    result = reset - timedelta(days=days_back)
    if now < result:
        result -= timedelta(days=7)
    return result


def fmt_countdown(delta):
    s = max(0, int(delta.total_seconds()))
    if s == 0:
        return "Resetting now~!"
    d, s = divmod(s, 86400)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    if d > 0:
        return f"{d}d {h:02}h {m:02}m {s:02}s"
    return f"{h:02}h {m:02}m {s:02}s"


# ╔════════════════════════════════════════════════════════════╗
# ║  📋  TASK DEFINITIONS                                     ║
# ║  Source: maxroll.gg/blue-protocol dailies & weeklies guide ║
# ║  Reset: Daily 5:00 AM UTC-2 / Weekly Monday 5:00 AM UTC-2 ║
# ╚════════════════════════════════════════════════════════════╝

DAILY_TASKS = [
    {
        "id": "unstable_space",
        "name": "Unstable Space",
        "desc": "2 runs max",
        "tip": "Luno, Honor Coins, gear drops",
    },
    {
        "id": "season_merits",
        "name": "Season Pass Merits",
        "desc": "500 merits goal",
        "tip": "Check Season Hub (O) for objectives",
    },
    {
        "id": "bureau_commissions",
        "name": "Bureau Commissions",
        "desc": "Pick 3 of 6 (Bahamar!)",
        "tip": "Lv55+, ~1 min each, rest bonus up to 9",
    },
    {
        "id": "elite_chest",
        "name": "Elite Hunt Chest",
        "desc": "2 keys daily",
        "tip": "Imagine mats, modules, stores up to 6 keys",
    },
    {
        "id": "world_boss_chest",
        "name": "World Boss Chest",
        "desc": "2 keys daily",
        "tip": "Exquisite mats, stores up to 6 keys",
    },
    {
        "id": "life_skill",
        "name": "Life Skill Focus",
        "desc": "Spend 400 focus",
        "tip": "Gather or craft, stores up to 2000",
    },
    {
        "id": "leisure",
        "name": "Leisure Activities",
        "desc": "1st clear = best rewards",
        "tip": "Friendship Pts, Luno, gear; cap 1K FP",
    },
    {
        "id": "homestead",
        "name": "Homestead Commissions",
        "desc": "1800 Homestead EXP",
        "tip": "Lv40+, rest bonus up to 9 commissions",
    },
    {
        "id": "wbc_daily",
        "name": "World Boss Crusade",
        "desc": "16:00-22:00 UTC-2",
        "tip": "20-player, 3-4x/week for 1200 weekly pts",
    },
    {
        "id": "guild_checkin",
        "name": "Guild Check-In",
        "desc": "Talk to Guild Admin",
        "tip": "10 Merits, 10 EXP, 20 Funds",
    },
    {
        "id": "guild_cargo",
        "name": "Guild Cargo",
        "desc": "20,000 volume goal",
        "tip": "18K Luno + Guild Tokens + next-day bonus",
    },
    {
        "id": "guild_hunt",
        "name": "Guild Hunt",
        "desc": "Fri-Sun 14:00-02:00, 2 clears",
        "tip": "Normal & Hard share limit; Guild Tokens",
        "days": [4, 5, 6],  # Friday, Saturday, Sunday
    },
    {
        "id": "mystery_store",
        "name": "Mystery Store",
        "desc": "Buy daily deals!",
        "tip": "Starforge Crystals, Class Books, Mech Shards",
    },
]

WEEKLY_TASKS = [
    {
        "id": "wbc_weekly",
        "name": "World Boss Crusade Pts",
        "desc": "1,200 pts total",
        "tip": "Asteria Rep, Rose Orb, Luno Pouch rewards",
    },
    {
        "id": "friendship",
        "name": "Friendship Points",
        "desc": "1,000 pts cap",
        "tip": "Run normal Chaotic Realm w/ AI for fast pts",
    },
    {
        "id": "guild_dance",
        "name": "Guild Dance",
        "desc": "Fri 15:30-03:30 UTC-2",
        "tip": "50 Guild Tokens, buff for Guild Hunt",
    },
    {
        "id": "guild_activity",
        "name": "Guild Activity Rewards",
        "desc": "7,000 Guild Merits",
        "tip": "5K Luno, 480 Tokens, Rose Orb, Star Chests",
    },
    {
        "id": "chaotic_reforge",
        "name": "Chaotic Realm Reforges",
        "desc": "20 runs weekly cap",
        "tip": "Normal/Hard share cap; Master separate",
    },
    {
        "id": "bane_lord",
        "name": "Bane Lord",
        "desc": "5 clears max",
        "tip": "Legendary Selector Box, Dream Crystal Dust",
    },
    {
        "id": "pioneer",
        "name": "Pioneer Rewards",
        "desc": "6 CR + 12 Elites + 1800 Focus",
        "tip": "Redeem weekly from Pioneer NPC in town",
    },
    {
        "id": "dragon_shackles",
        "name": "Dragon Shackles Raid",
        "desc": "Weekly lockout",
        "tip": "Nightmare for Glinting Stellar Core",
    },
    {
        "id": "dreambloom",
        "name": "Dreambloom Ruins Raid",
        "desc": "Per-difficulty lockout",
        "tip": "Normal/Hard/Nightmare each separate",
    },
    {
        "id": "stimen_vaults",
        "name": "Stimen Vaults",
        "desc": "Bi-weekly reset",
        "tip": "Rose Orb, Imagine mats, clear all floors",
    },
    {
        "id": "weekly_shops",
        "name": "Weekly Shop Purchases",
        "desc": "All weekly shops",
        "tip": "Season/Honor/Friendship/Rep/Guild stores",
    },
]


# ╔════════════════════════════════════════════════════════════╗
# ║  💾  SAVE / LOAD                                          ║
# ╚════════════════════════════════════════════════════════════╝

SAVE_DIR = Path(os.environ.get("APPDATA", ".")) / "NyankoProtocol"
SAVE_FILE = SAVE_DIR / "checklist.json"


def load_data():
    default = {
        "daily": [], "weekly": [], "d_mark": "", "w_mark": "",
        "build_guide_url": "", "build_guide_title": "", "build_gearing": "",
        "build_planner_url": "", "build_gear_slots": [],
        "build_food": "", "build_serum": "",
    }
    if not SAVE_FILE.exists():
        return default
    try:
        data = json.loads(SAVE_FILE.read_text("utf-8"))
    except (json.JSONDecodeError, OSError):
        return default
    for k in default:
        if k not in data:
            data[k] = default[k]

    # Auto-reset if a reset boundary has been crossed
    d_mark = last_daily_reset().isoformat()
    w_mark = last_weekly_reset().isoformat()
    if data.get("d_mark") != d_mark:
        data["daily"] = []
        data["d_mark"] = d_mark
    if data.get("w_mark") != w_mark:
        data["weekly"] = []
        data["w_mark"] = w_mark
    return data


def save_data(data):
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    data["d_mark"] = last_daily_reset().isoformat()
    data["w_mark"] = last_weekly_reset().isoformat()
    SAVE_FILE.write_text(json.dumps(data, indent=2), "utf-8")


# ╔════════════════════════════════════════════════════════════╗
# ║  🎨  UI HELPERS                                           ║
# ╚════════════════════════════════════════════════════════════╝

def pick_cat(progress):
    if progress >= 1.0:
        return CAT_ART["love"]
    if progress >= 0.5:
        return CAT_ART["happy"]
    if progress > 0:
        return CAT_ART["normal"]
    return CAT_ART["sleepy"]


def progress_bar(done, total, width=22):
    if total == 0:
        return "[dim]No tasks available, nya~[/]"
    ratio = done / total
    filled = int(width * ratio)
    empty = width - filled
    pct = int(100 * ratio)

    if ratio >= 1.0:
        color = "bright_green"
        sparkle = " All done!! "
    elif ratio >= 0.5:
        color = "bright_yellow"
        sparkle = ""
    else:
        color = "bright_magenta"
        sparkle = ""

    bar = f"[{color}]{'█' * filled}[/][dim]{'░' * empty}[/]"
    return f"  {bar} [{color}]{pct}%[/] [bright_cyan]{done}/{total}[/] ~nya!{sparkle}"


# ╔════════════════════════════════════════════════════════════╗
# ║  🐾  MAIN APPLICATION                                     ║
# ╚════════════════════════════════════════════════════════════╝

class NyankoApp:
    def __init__(self):
        self.data = load_data()
        self.cursor = 0
        self.section = 0        # 0 = daily, 1 = weekly, 2 = build summary
        self.running = True
        self.show_tips = False
        self.flash = ""
        self.flash_time = 0.0
        self.quote = random.choice(CAT_QUOTES)
        self.neko_face = random.choice(NEKO_FACES)
        self.last_save_check = time.time()

    # ── Task accessors ───────────────────────────────────────

    def active_daily(self):
        dow = server_now().weekday()
        return [t for t in DAILY_TASKS if "days" not in t or dow in t["days"]]

    def tasks(self):
        if self.section == 0:
            return self.active_daily()
        if self.section == 1:
            return list(WEEKLY_TASKS)
        return []   # Build Summary has no task list

    def checked(self):
        return self.data["daily"] if self.section == 0 else self.data["weekly"]

    # ── Actions ──────────────────────────────────────────────

    def toggle(self):
        ts = self.tasks()
        if not ts or self.cursor >= len(ts):
            return
        tid = ts[self.cursor]["id"]
        key = "daily" if self.section == 0 else "weekly"
        if tid in self.data[key]:
            self.data[key].remove(tid)
            self.flash = random.choice(UNCHECK_MSGS) + " " + self.neko_face
        else:
            self.data[key].append(tid)
            self.flash = random.choice(CHECK_MSGS) + " " + self.neko_face
        self.flash_time = time.time()
        save_data(self.data)

    def switch_section(self):
        self.section = (self.section + 1) % 3
        self.cursor = 0
        self.neko_face = random.choice(NEKO_FACES)
        self.quote = random.choice(CAT_QUOTES)

    def _do_import_build(self):
        """Prompt for Maxroll URL, scrape Gearing + Food/Serum, save and show flash."""
        if scrape_guide is None:
            self.flash = "Import not available (maxroll_scraper missing), nya~"
            self.flash_time = time.time()
            return
        sys.stdout.write("\033[?25h")  # show cursor
        console.print()
        console.print("  [bold bright_yellow]Import Maxroll build guide[/]")
        console.print("  Paste URL (e.g. https://maxroll.gg/blue-protocol/build-guides/...):")
        try:
            url = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            url = ""
        sys.stdout.write("\033[?25l")  # hide cursor again
        if not url:
            self.flash = "No URL entered, nya~"
            self.flash_time = time.time()
            return
        console.print("  [dim]Fetching guide...[/]")
        result = scrape_guide(url)
        if result.get("error"):
            self.flash = f"Import failed: {result['error']} ~nya"
            self.flash_time = time.time()
            return
        self.data["build_guide_url"] = url
        self.data["build_guide_title"] = result.get("title") or "Build"
        self.data["build_gearing"] = result.get("gearing") or ""
        self.data["build_planner_url"] = result.get("planner_url") or ""
        self.data["build_gear_slots"] = result.get("gear_slots") or []
        self.data["build_food"] = result.get("food") or ""
        self.data["build_serum"] = result.get("serum") or ""
        save_data(self.data)
        self.flash = f"Build imported: {self.data['build_guide_title']} ~nya!"
        self.flash_time = time.time()

    def _render_build_summary(self, out):
        """Render Build Summary panel (Gearing + Food/Serum at a glance)."""
        title = self.data.get("build_guide_title") or "No build imported"
        url = self.data.get("build_guide_url") or ""
        planner_url = self.data.get("build_planner_url") or ""
        gearing = self.data.get("build_gearing") or ""
        gear_slots = self.data.get("build_gear_slots") or []
        food = self.data.get("build_food") or "—"
        serum = self.data.get("build_serum") or "—"

        if not url:
            out.print(
                Panel(
                    "[dim]Import a Maxroll build guide to see Gearing and Food/Serum here.[/]\n\n"
                    "  Paste a URL like:\n  [bright_cyan]https://maxroll.gg/blue-protocol/build-guides/verdant-oracle-smite-spec-guide[/]\n\n"
                    "  Press [bold bright_yellow]I[/] then Enter the URL, nya~!",
                    title="[bold bright_magenta] Build Summary [/]",
                    border_style="bright_magenta",
                    box=box.ROUNDED,
                    padding=(1, 2),
                )
            )
            return

        # Short gearing (Attributes + Legendary Affix only)
        gearing_text = gearing if gearing else "(No attributes/legendary affix extracted.)"
        gearing_block = "[bold]Gearing[/] (attributes + legendary affix):\n  " + gearing_text.replace("\n", "\n  ")

        # Planner link (class image on guide opens this — gear name, basic & advanced attributes)
        if planner_url:
            gear_block = "\n[bold]Planner[/] (gear name, basic & advanced attributes):\n  [bright_cyan]" + planner_url + "[/]"
        else:
            gear_block = ""

        # Gear slots (when we have name/attrs from planner or embed)
        if gear_slots:
            gear_lines = []
            for g in gear_slots[:14]:
                slot = g.get("slot") or "?"
                name = g.get("name") or "—"
                basic = g.get("basic_attributes") or ""
                advanced = g.get("advanced_attributes") or ""
                gear_lines.append(f"  [bold]{slot}:[/] [bright_cyan]{name}[/]")
                if basic:
                    gear_lines.append(f"    [dim]Basic:[/] {basic[:70]}{'…' if len(basic) > 70 else ''}")
                if advanced:
                    gear_lines.append(f"    [dim]Advanced:[/] {advanced[:70]}{'…' if len(advanced) > 70 else ''}")
            gear_block += "\n[bold]Gear[/]:\n" + "\n".join(gear_lines)
        elif not planner_url:
            gear_block += "\n[dim]Gear: Open the guide in a browser; hover items for tooltips or use the planner if linked.[/]"

        body = (
            f"[bold bright_cyan]{title}[/]\n"
            f"[dim]{url}[/]\n\n"
            f"{gearing_block}\n"
            f"{gear_block}\n\n"
            f"  [bold]Food:[/]  [bright_yellow]{food}[/]\n"
            f"  [bold]Serum:[/] [bright_yellow]{serum}[/]"
        )
        out.print(
            Panel(
                body,
                title="[bold bright_magenta] Build Summary [/]",
                border_style="bright_magenta",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )

    # ── Rendering ────────────────────────────────────────────

    def render(self):
        # Use current terminal size so resizing the window works
        try:
            ts = shutil.get_terminal_size()
            term_width = max(80, ts.columns)
            term_height = max(24, ts.lines)
        except Exception:
            term_width, term_height = 100, 45
        # Render entire frame into a buffer first, then paint in one shot
        buf = StringIO()
        out = Console(
            file=buf,
            highlight=False,
            width=term_width,
            height=term_height,
            force_terminal=True,
            color_system=console.color_system,
        )

        now = server_now()
        d_cd = next_daily_reset() - now
        w_cd = next_weekly_reset() - now

        ts = self.tasks()
        self.cursor = min(self.cursor, max(0, len(ts) - 1))
        chk = self.checked()
        done = sum(1 for t in ts if t["id"] in chk)
        total = len(ts)
        progress = done / total if total > 0 else 0
        cat = pick_cat(progress)

        # ── Header ──
        cat_colored = [f"[bright_magenta]{ln}[/]" for ln in cat]
        title_lines = [
            "[bold bright_magenta]★  N y a n k o   P r o t o c o l  ★[/]",
            "[dim]Blue Protocol: Star Resonance[/]",
            f"[bright_cyan]~nyaa! {self.neko_face}[/]",
        ]
        rows = []
        for i in range(max(len(cat_colored), len(title_lines))):
            c = cat_colored[i] if i < len(cat_colored) else " " * 12
            t = title_lines[i] if i < len(title_lines) else ""
            rows.append(f"    {c}     {t}")

        timer_line = (
            f"    [bright_yellow]🐾 Daily Reset :[/] [bold white]{fmt_countdown(d_cd)}[/]"
            f"      [bright_yellow]⭐ Weekly Reset:[/] [bold white]{fmt_countdown(w_cd)}[/]"
        )
        server_line = f"    [dim]Local Time: {now.strftime('%A %H:%M:%S')} ({now.strftime('%Z') or 'Local'})[/]"

        header = "\n".join(rows) + f"\n\n{timer_line}\n{server_line}"

        out.print(Panel(
            header,
            border_style="bright_magenta",
            box=box.DOUBLE_EDGE,
            padding=(0, 1),
        ))

        # ── Build at a glance (when a guide is imported) ──
        if self.data.get("build_guide_title"):
            food_s = self.data.get("build_food") or "—"
            serum_s = self.data.get("build_serum") or "—"
            out.print(
                f"  [dim]Build:[/] [bright_cyan]{self.data['build_guide_title']}[/]  "
                f"[dim]| Food:[/] [bright_yellow]{food_s}[/]  [dim]| Serum:[/] [bright_yellow]{serum_s}[/]"
            )
            out.print()

        # ── Section Tabs ──
        if self.section == 0:
            tab_text = (
                " [bold bright_magenta on grey15]  ≫ Daily ≪  [/]"
                "  [dim]Weekly[/]  [dim]Build[/]"
            )
        elif self.section == 1:
            tab_text = (
                " [dim]Daily[/]  "
                " [bold bright_magenta on grey15]  ≫ Weekly ≪  [/]"
                "  [dim]Build[/]"
            )
        else:
            tab_text = (
                " [dim]Daily[/]  [dim]Weekly[/]  "
                " [bold bright_magenta on grey15]  ≫ Build ≪  [/]"
            )
        out.print(f"{tab_text}    [dim italic](Tab switch  [I] Import guide)[/]")
        out.print()

        # ── Build Summary section (section 2) ──
        if self.section == 2:
            self._render_build_summary(out)
            out.print()
            out.print(
                f"  [dim][[/][bright_yellow]Tab[/][dim]] Back to tasks  "
                f"[[/][bright_yellow]I[/][dim]] Import guide  "
                f"[[/][bright_yellow]Q[/][dim]] Quit[/]"
            )
            frame = buf.getvalue()
            lines = frame.split("\n")
            if len(lines) > term_height:
                frame = "\n".join(lines[:term_height]) + "\033[0m"
            sys.stdout.write("\033[H\033[2J" + frame)
            sys.stdout.flush()
            return

        # ── Progress Bar ──
        out.print(progress_bar(done, total))

        if done == total and total > 0:
            section_name = "daily" if self.section == 0 else "weekly"
            out.print(
                f"  [bold bright_green]"
                f"✧ All {section_name} tasks complete! You're amazing, nya~! ✧"
                f"[/]"
            )
        out.print()

        # ── Task Table ──
        table = Table(
            box=box.ROUNDED,
            border_style="bright_magenta",
            show_header=False,
            padding=(0, 1),
            expand=True,
        )
        table.add_column("", width=2, justify="center")    # cursor
        table.add_column("", width=3, justify="center")    # checkbox
        table.add_column("Task", min_width=26, max_width=30)
        table.add_column("Details", min_width=24)
        if self.show_tips:
            table.add_column("Tip", min_width=20, style="dim italic")

        for i, task in enumerate(ts):
            is_on = task["id"] in chk
            is_cur = i == self.cursor

            ptr = "[bold bright_yellow]▸[/]" if is_cur else " "
            chk_mark = "[bold bright_green]✓[/]" if is_on else "[dim]○[/]"

            if is_on:
                name = f"[dim strikethrough]{task['name']}[/]"
                desc = f"[dim strikethrough]{task['desc']}[/]"
                tip = f"[dim]{task.get('tip', '')}[/]"
            elif is_cur:
                name = f"[bold bright_white]{task['name']}[/]"
                desc = f"[bright_cyan]{task['desc']}[/]"
                tip = f"[bright_cyan]{task.get('tip', '')}[/]"
            else:
                name = f"[white]{task['name']}[/]"
                desc = f"[dim]{task['desc']}[/]"
                tip = f"[dim]{task.get('tip', '')}[/]"

            sty = "on grey15" if is_cur else None

            row = [ptr, chk_mark, name, desc]
            if self.show_tips:
                row.append(tip)
            table.add_row(*row, style=sty)

        out.print(table)

        # ── Flash message or quote ──
        out.print()
        if self.flash and time.time() - self.flash_time < 2.5:
            out.print(f"  [bold bright_green]  {self.flash}[/]")
        else:
            out.print(f"  [italic dim]  \" {self.quote} \"[/]")

        # ── Conditional task note ──
        if self.section == 0:
            dow = server_now().weekday()
            if dow not in [4, 5, 6]:
                out.print(
                    f"\n  [dim italic]  Note: Guild Hunt is Fri-Sun only "
                    f"(hidden today) {self.neko_face}[/]"
                )

        # ── Controls ──
        out.print()
        tip_key = "Hide tips" if self.show_tips else "Show tips"
        out.print(
            f"  [dim][[/][bright_yellow]↑↓[/][dim]] Move  "
            f"[[/][bright_yellow]Space[/][dim]] Toggle  "
            f"[[/][bright_yellow]Tab[/][dim]] Switch  "
            f"[[/][bright_yellow]I[/][dim]] Import build  "
            f"[[/][bright_yellow]T[/][dim]] {tip_key}  "
            f"[[/][bright_yellow]Q[/][dim]] Quit[/]"
        )

        # Full clear then draw so no leftover from previous (larger) frame; cap height
        frame = buf.getvalue()
        lines = frame.split("\n")
        if len(lines) > term_height:
            frame = "\n".join(lines[:term_height]) + "\033[0m"
        sys.stdout.write("\033[H\033[2J" + frame)
        sys.stdout.flush()

    # ── Input handling ───────────────────────────────────────

    def handle_input(self):
        if not msvcrt.kbhit():
            return

        key = msvcrt.getch()

        # Extended keys (arrows)
        if key in (b'\xe0', b'\x00'):
            key2 = msvcrt.getch()
            if key2 == b'H':      # Up
                self.cursor = max(0, self.cursor - 1)
            elif key2 == b'P':    # Down
                self.cursor = min(len(self.tasks()) - 1, self.cursor + 1)
            elif key2 == b'G':    # Home
                self.cursor = 0
            elif key2 == b'O':    # End
                self.cursor = max(0, len(self.tasks()) - 1)
            return

        # Regular keys
        if key in (b' ', b'\r'):        # Space or Enter
            self.toggle()
        elif key == b'\t':              # Tab
            self.switch_section()
        elif key in (b'q', b'Q'):       # Quit
            self.running = False
        elif key in (b't', b'T'):       # Toggle tips
            self.show_tips = not self.show_tips
        elif key in (b'i', b'I'):       # Import Maxroll build
            self._do_import_build()
        elif key in (b'r', b'R'):       # Refresh
            self.data = load_data()
            self.flash = "Refreshed! ~nya"
            self.flash_time = time.time()

    # ── Main loop ────────────────────────────────────────────

    def run(self):
        sys.stdout.write("\033[?25l")   # hide cursor
        try:
            while self.running:
                # Periodic reset check
                if time.time() - self.last_save_check > 30:
                    old_daily = list(self.data["daily"])
                    old_weekly = list(self.data["weekly"])
                    self.data = load_data()
                    if self.data["daily"] != old_daily or self.data["weekly"] != old_weekly:
                        self.flash = "Reset happened! Fresh start, nya~!"
                        self.flash_time = time.time()
                        self.quote = random.choice(CAT_QUOTES)
                    self.last_save_check = time.time()

                self.render()

                # Poll for input, re-render every ~1 second for timer
                t0 = time.time()
                while time.time() - t0 < 1.0:
                    if msvcrt.kbhit():
                        self.handle_input()
                        break
                    time.sleep(0.05)
        except KeyboardInterrupt:
            pass
        finally:
            sys.stdout.write("\033[?25h")   # show cursor
            console.clear()
            bye_cat = random.choice(list(CAT_ART.values()))
            for line in bye_cat:
                console.print(f"  [bright_magenta]{line}[/]")
            console.print()
            console.print(
                f"  [bold bright_magenta]"
                f"Bye bye~! See you next time, nya~! {random.choice(NEKO_FACES)}"
                f"[/]"
            )
            console.print()


# ╔════════════════════════════════════════════════════════════╗
# ║  🚀  START                                                ║
# ╚════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    NyankoApp().run()
