#!/usr/bin/env python3
"""
download_gamers.py — Download profile images for 100 top world-famous gamers/e-sports players.

Uses Wikipedia API to fetch thumbnail images. Falls back to Wikimedia Commons.

Usage:
    python3 download_gamers.py
"""

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
GAMERS_DIR = SCRIPT_DIR / "gamers"
GAMERS_DIR.mkdir(exist_ok=True)

SLEEP = 1.5
HEADERS = {"User-Agent": "ActorQuiz/1.0 (educational project; soldarcompany@gmail.com) Python-urllib/3"}

TOP_100_GAMERS = [
    # Streaming / Content creators
    ("PewDiePie", "PewDiePie"),
    ("Ninja", "Ninja (streamer)"),
    ("Shroud", "Shroud (streamer)"),
    ("xQc", "xQc"),
    ("Pokimane", "Pokimane"),
    ("TimTheTatman", "TimTheTatman"),
    ("Valkyrae", "Valkyrae"),
    ("Nickmercs", "Nickmercs"),
    ("Summit1g", "Summit1g"),
    ("Sodapoppin", "Sodapoppin"),
    ("Sykkuno", "Sykkuno"),
    ("Ludwig", "Ludwig (streamer)"),
    ("Disguised Toast", "Disguised Toast"),
    ("Asmongold", "Asmongold"),
    ("DrDisrespect", "DrDisrespect"),
    ("Lirik", "LIRIK"),
    ("CouRage", "CouRage"),
    ("Myth", "Myth (streamer)"),
    ("Mizkif", "Mizkif"),
    ("HasanAbi", "HasanAbi"),

    # League of Legends
    ("Faker", "Faker (gamer)"),
    ("Uzi", "Uzi (gamer)"),
    ("Rekkles", "Rekkles"),
    ("Caps", "Caps (gamer)"),
    ("Bjergsen", "Bjergsen"),
    ("Doublelift", "Doublelift"),
    ("Perkz", "Perkz"),
    ("Ruler", "Ruler (gamer)"),
    ("Sneaky", "Sneaky (gamer)"),
    ("Imaqtpie", "Imaqtpie"),

    # CS:GO / CS2
    ("s1mple", "S1mple"),
    ("NiKo", "NiKo (gamer)"),
    ("ZywOo", "ZywOo"),
    ("dev1ce", "dev1ce"),
    ("electronic", "electronic (gamer)"),
    ("coldzera", "Coldzera"),
    ("olofmeister", "Olofmeister"),
    ("kennyS", "KennyS"),
    ("FalleN", "FalleN"),
    ("GeT_RiGhT", "GeT_RiGhT"),
    ("f0rest", "f0rest"),
    ("GuardiaN", "GuardiaN"),
    ("flusha", "Flusha"),
    ("rain", "Rain (gamer)"),
    ("Xyp9x", "Xyp9x"),
    ("dupreeh", "Dupreeh"),
    ("gla1ve", "Gla1ve"),
    ("karrigan", "Karrigan"),
    ("Twistzz", "Twistzz"),
    ("EliGE", "EliGE"),

    # Dota 2
    ("Dendi", "Dendi (gamer)"),
    ("N0tail", "N0tail"),
    ("Puppey", "Puppey"),
    ("KuroKy", "KuroKy"),
    ("Miracle-", "Miracle- (gamer)"),
    ("Sumail", "SumaiL"),
    ("Ana", "Ana (Dota 2 player)"),
    ("JerAx", "JerAx"),

    # StarCraft
    ("Flash", "Flash (gamer)"),
    ("Jaedong", "Jaedong"),
    ("Bisu", "Bisu"),
    ("Serral", "Serral"),
    ("Scarlett", "Scarlett (gamer)"),
    ("Reynor", "Reynor (gamer)"),

    # Fortnite
    ("Tfue", "Tfue"),
    ("Bugha", "Bugha"),

    # Smash Bros
    ("MKLeo", "MKLeo"),
    ("Hungrybox", "Hungrybox"),
    ("Armada", "Armada (gamer)"),
    ("Leffen", "Leffen"),
    ("Mango", "Mango (gamer)"),

    # Fighting Games
    ("SonicFox", "SonicFox"),
    ("Daigo Umehara", "Daigo Umehara"),
    ("Tokido", "Tokido"),
    ("Justin Wong", "Justin Wong"),

    # Call of Duty
    ("Scump", "Scump"),
    ("Crimsix", "Crimsix"),
    ("Karma", "Karma (Call of Duty player)"),
    ("Clayster", "Clayster"),

    # Overwatch / Valorant
    ("Sinatraa", "Sinatraa"),
    ("TenZ", "TenZ (gamer)"),
    ("ShahZaM", "ShahZaM"),
    ("ScreaM", "ScreaM"),
    ("yay", "yay (gamer)"),

    # FIFA / Sports games
    ("Tekkz", "Tekkz"),

    # Battle Royale / PUBG
    (" Dizzy", " Dizzy (gamer)"),
    ("Albralelie", "Albralelie"),

    # Rocket League
    ("jstn", "Jstn"),
    ("Jstn", "Justin Morales (gamer)"),
    ("GarrettG", "GarrettG"),

    # Other famous gamers
    ("Aphromoo", "Aphromoo"),
    ("MontanaBlack", "MontanaBlack"),
    ("Loltyler1", "Tyler1"),
    ("TSM Haunt", "TSM Haunt"),
    ("Stewie2k", "Stewie2k"),
    ("NAF", "NAF (gamer)"),
    ("autimatic", "Autimatic"),
    ("TACO", "TACO (gamer)"),
    ("fer", "fer (gamer)"),
    ("fnx", "fnx (gamer)"),
]

# deduplicate by display name
seen = set()
GAMERS = []
for entry in TOP_100_GAMERS:
    if entry[0] not in seen:
        seen.add(entry[0])
        GAMERS.append(entry)
GAMERS = GAMERS[:100]


def wiki_get(params):
    base = "https://en.wikipedia.org/w/api.php"
    params["format"] = "json"
    qs = urllib.parse.urlencode(params)
    url = f"{base}?{qs}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  Wikipedia request failed: {e}")
        return None


def get_wiki_image(wiki_title):
    """Return a direct image URL for a Wikipedia article, or None."""
    # Use 320px — a size Wikimedia explicitly allows without rate-limiting
    data = wiki_get({
        "action": "query",
        "titles": wiki_title,
        "prop": "pageimages",
        "pithumbsize": 320,
        "pilimit": 1,
        "redirects": 1,
    })
    if not data:
        return None
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        thumb = page.get("thumbnail", {})
        src = thumb.get("source")
        if src:
            return src
    return None


def search_wiki_image(name):
    """Search Wikipedia for the person and return their image."""
    data = wiki_get({
        "action": "query",
        "list": "search",
        "srsearch": f"{name} gamer esports",
        "srlimit": 3,
        "redirects": 1,
    })
    if not data:
        return None
    results = data.get("query", {}).get("search", [])
    for result in results:
        title = result.get("title", "")
        img = get_wiki_image(title)
        if img:
            print(f"  Found via search: '{title}'")
            return img
    return None


def download_image(url, dest):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read()
            ext = url.split(".")[-1].split("?")[0].lower()
            if ext not in ("jpg", "jpeg", "png", "webp", "gif"):
                ext = "jpg"
            final_dest = dest.with_suffix(f".{ext}")
            with open(final_dest, "wb") as f:
                f.write(data)
            return True, final_dest
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 5 * (2 ** attempt)
                print(f"  429 rate-limit, waiting {wait}s ...", end=" ", flush=True)
                time.sleep(wait)
            else:
                print(f"  Download failed (HTTP {e.code}): {e}")
                return False, dest
        except Exception as e:
            print(f"  Download failed: {e}")
            return False, dest
    print(f"  Download failed after retries")
    return False, dest


def already_downloaded(name: str) -> bool:
    for ext in ("jpg", "jpeg", "png", "webp"):
        if (GAMERS_DIR / f"{name}.{ext}").exists():
            return True
    return False


def main():
    print(f"Downloading images for {len(GAMERS)} gamers...\n")
    success = 0
    failed = []

    for idx, (display_name, wiki_title) in enumerate(GAMERS, 1):
        print(f"[{idx:3}/{len(GAMERS)}] {display_name} (wiki: '{wiki_title}') ...", end=" ", flush=True)

        if already_downloaded(display_name):
            print("ALREADY EXISTS")
            success += 1
            continue

        img_url = get_wiki_image(wiki_title)
        time.sleep(SLEEP)

        if not img_url:
            print("not found via title, trying search ...", end=" ", flush=True)
            img_url = search_wiki_image(display_name)
            time.sleep(SLEEP)

        if not img_url:
            print("FAILED (no image found)")
            failed.append(display_name)
            continue

        dest = GAMERS_DIR / display_name
        ok, final_path = download_image(img_url, dest)
        if ok:
            print(f"OK -> {final_path.name}")
            success += 1
        else:
            print("FAILED (download error)")
            failed.append(display_name)

        time.sleep(SLEEP)

    print(f"\n{'='*60}")
    print(f"Done. Success: {success}/{len(GAMERS)}")
    if failed:
        print(f"Failed ({len(failed)}):")
        for name in failed:
            print(f"  - {name}")


if __name__ == "__main__":
    main()
