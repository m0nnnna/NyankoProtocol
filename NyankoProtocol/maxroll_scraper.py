#!/usr/bin/env python3
"""
Scrape from Maxroll Blue Protocol build guide URL:
- Gearing: only Attributes priority + Legendary Affix (no long paragraphs).
- Food and Serum.
- Interactive gear: equipment slots + image URLs when present in page (often JS-loaded).
"""

import re
import json
import urllib.request
import urllib.error
from html.parser import HTMLParser


MAXROLL_BASE = "https://maxroll.gg"
USER_AGENT = "NyankoProtocol/1.0 (Blue Protocol build tracker)"


def fetch_url(url, timeout=15):
    """Fetch URL and return decoded HTML string."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_sections_from_text(full_text):
    """
    Extract only:
    - Attributes priority list (1. Intellect 2. Luck ...)
    - Legendary Affix list (1. Cast Speed 2. MATK 3. Intellect)
    - Food and Serum.
    No long gearing paragraphs (Embeds, Modules, Emblem, Set).
    """
    text = full_text.replace("\r\n", "\n").replace("\r", "\n")
    gearing_parts = []
    food = ""
    serum = ""

    # Attributes: "1. Intellect 2. Luck ..." or after stripping tags "Intellect Luck Versatility Crit"
    attrs_m = re.search(
        r"1\.\s*(\w+)\s+2\.\s*(\w+)\s+3\.\s*(\w+)\s+4\.\s*(\w+)(?=\s|\.|Legendary|$)",
        text,
        re.IGNORECASE,
    )
    if attrs_m:
        gearing_parts.append("Attributes: 1. %s  2. %s  3. %s  4. %s" % attrs_m.groups())
    else:
        # List items may be stripped to "Intellect Luck Versatility Crit" before "Legendary"
        attrs_inline = re.search(
            r"(Intellect)\s+(Luck)\s+(Versatility)\s+(Crit)\s*(?=Legendary|$)",
            text,
            re.IGNORECASE,
        )
        if attrs_inline:
            gearing_parts.append("Attributes: 1. %s  2. %s  3. %s  4. %s" % attrs_inline.groups())

    # Legendary Affix: "For legendary affixes, focus on ..."
    leg_m = re.search(
        r"For legendary affixes, focus on\s+([^.]+?)(?=\.|Celestial|$)",
        text,
        re.IGNORECASE,
    )
    if leg_m:
        gearing_parts.append("Legendary affix: " + leg_m.group(1).strip())
    # Legendary priority: "1. Cast Speed 2. MATK 3. Intellect" or "Cast Speed , then MATK , and Intellect"
    leg_list = re.search(
        r"1\.\s*(Cast Speed|MATK|Intellect|Ranged Damage|Attack SPD)\s+2\.\s*([^.]+?)\s+3\.\s*(\w+)(?=\s|\.|Celestial|$)",
        text,
        re.IGNORECASE,
    )
    if leg_list:
        gearing_parts.append("Legendary priority: 1. %s  2. %s  3. %s" % (
            leg_list.group(1).strip(), leg_list.group(2).strip(), leg_list.group(3).strip()
        ))
    else:
        # From "focus on Cast Speed , then MATK , and Intellect" we already have the line; add explicit priority
        leg_any = re.search(r"focus on\s+([^,]+),\s*then\s+([^,]+),\s*and\s+(\w+)\s+as the last", text, re.IGNORECASE)
        if leg_any:
            gearing_parts.append("Legendary priority: 1. %s  2. %s  3. %s" % (
                leg_any.group(1).strip(), leg_any.group(2).strip(), leg_any.group(3).strip()
            ))

    gearing = "\n".join(gearing_parts) if gearing_parts else ""

    # Food and Serum
    food_m = re.search(r"Food\s*:\s*(.+?)\s*Serum\s*:", text, re.IGNORECASE)
    if food_m:
        food = food_m.group(1).strip()
    serum_m = re.search(r"Serum\s*:\s*(.+?)(?=\s*To learn|\s*Life Skills|\s*Culinary|$)", text, re.IGNORECASE)
    if serum_m:
        serum = serum_m.group(1).strip()

    return {"gearing": gearing, "food": food, "serum": serum}


def extract_planner_build_id(guide_html):
    """
    Extract the planner build ID from the guide page (class image link to planner).
    Found in: <span class="sr-planner-equipment" data-sr-id="g41si0c5"></span>
    Returns build_id string or None.
    """
    m = re.search(r'sr-planner-equipment[^>]*data-sr-id=["\']([a-zA-Z0-9]+)["\']', guide_html)
    if m:
        return m.group(1)
    m = re.search(r'data-sr-id=["\']([a-zA-Z0-9]+)["\'][^>]*sr-planner', guide_html)
    if m:
        return m.group(1)
    m = re.search(r'/planner/([a-zA-Z0-9]+)(?=["\'\s>]|$)', guide_html)
    if m:
        return m.group(1)
    return None


def extract_gear_from_html(html):
    """
    Try to extract equipment slots (name, basic/advanced attributes) from the page.
    Returns list of {"slot": str, "name": str, "basic_attributes": str, "advanced_attributes": str, "image_url": str or None}.
    """
    gear_slots = []
    # Next.js / Gatsby style embedded JSON
    m = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>([^<]+)</script>', html)
    if m:
        try:
            data = json.loads(m.group(1))
            def walk(obj, path=""):
                if isinstance(obj, dict):
                    name = obj.get("name") or obj.get("title") or ""
                    slot = obj.get("slot") or obj.get("slotType") or path.split("/")[-1] or "?"
                    basic = obj.get("basicAttributes") or obj.get("basic_attributes") or ""
                    advanced = obj.get("advancedAttributes") or obj.get("advanced_attributes") or ""
                    if isinstance(basic, dict):
                        basic = " ".join("%s %s" % (k, v) for k, v in basic.items())
                    if isinstance(advanced, dict):
                        advanced = " ".join("%s %s" % (k, v) for k, v in advanced.items())
                    if name or basic or advanced:
                        url = obj.get("imageUrl") or obj.get("image_url") or obj.get("icon")
                        gear_slots.append({
                            "slot": str(slot),
                            "name": str(name),
                            "basic_attributes": str(basic) if basic else "",
                            "advanced_attributes": str(advanced) if advanced else "",
                            "image_url": url if isinstance(url, str) else None,
                        })
                    for k, v in obj.items():
                        walk(v, path + "/" + k)
                elif isinstance(obj, list):
                    for i, v in enumerate(obj):
                        walk(v, path + "/" + str(i))
            walk(data)
        except (json.JSONDecodeError, TypeError):
            pass

    for script in re.finditer(r"<script[^>]*>([^<]{300,})</script>", html):
        content = script.group(1)
        if "equipment" in content and ("name" in content or "Intellect" in content):
            for blob in re.finditer(r'\{"[^"]*"(?:slot|name|basicAttributes|advancedAttributes)[^}]+\}', content):
                try:
                    o = json.loads(blob.group(0))
                    name = o.get("name") or o.get("title") or ""
                    if name:
                        gear_slots.append({
                            "slot": o.get("slot") or o.get("slotType") or "?",
                            "name": str(name),
                            "basic_attributes": str(o.get("basicAttributes") or o.get("basic_attributes") or ""),
                            "advanced_attributes": str(o.get("advancedAttributes") or o.get("advanced_attributes") or ""),
                            "image_url": o.get("imageUrl") or o.get("image") or None,
                        })
                except (json.JSONDecodeError, TypeError):
                    pass

    return gear_slots


def scrape_guide(url):
    """
    Fetch a Maxroll Blue Protocol build guide URL and return:
    - title: guide title
    - gearing: short string (Attributes + Legendary Affix only)
    - planner_url: link to planner page (e.g. .../planner/g41si0c5) when build ID is in guide; open for gear name + basic/advanced attributes
    - gear_slots: list of {slot, name, basic_attributes, advanced_attributes, image_url} when present
    - food, serum: recommended consumables
    - error: None or error message
    """
    if not url or "maxroll.gg" not in url:
        return {
            "title": "", "gearing": "", "planner_url": "", "gear_slots": [], "food": "", "serum": "",
            "error": "Invalid or non-Maxroll URL",
        }

    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    try:
        html = fetch_url(url)
    except urllib.error.HTTPError as e:
        return {"title": "", "gearing": "", "planner_url": "", "gear_slots": [], "food": "", "serum": "", "error": f"HTTP {e.code}"}
    except urllib.error.URLError as e:
        return {"title": "", "gearing": "", "planner_url": "", "gear_slots": [], "food": "", "serum": "", "error": str(e.reason) or "Network error"}
    except Exception as e:
        return {"title": "", "gearing": "", "planner_url": "", "gear_slots": [], "food": "", "serum": "", "error": str(e)}

    # Title
    title = ""
    tit_m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
    if tit_m:
        title = re.sub(r"\s*-\s*Blue Protocol.*$", "", tit_m.group(1), flags=re.IGNORECASE).strip()
    if not title:
        slug_m = re.search(r"maxroll\.gg/[^/]+/[^/]+/([^/?#]+)", url)
        if slug_m:
            title = slug_m.group(1).replace("-", " ").title()

    # Body text (strip scripts for gearing/food/serum)
    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&\w+;|&#\d+;", " ", text)
    text = re.sub(r"\s+", " ", text)

    sections = extract_sections_from_text(text)
    gear_slots = extract_gear_from_html(html)

    # Planner build ID (class image opens .../planner/{id}) — hover on guide shows item tooltip; full gear is on planner page
    planner_url = ""
    build_id = extract_planner_build_id(html)
    if build_id:
        planner_url = f"https://maxroll.gg/blue-protocol/planner/{build_id}"
        # Optionally fetch planner page to try to get gear name + basic/advanced attributes (often loaded by JS)
        if not gear_slots:
            try:
                planner_html = fetch_url(planner_url)
                gear_slots = extract_gear_from_html(planner_html)
            except Exception:
                pass

    return {
        "title": title,
        "gearing": sections["gearing"],
        "planner_url": planner_url,
        "gear_slots": gear_slots,
        "food": sections["food"],
        "serum": sections["serum"],
        "error": None,
    }
