#!/usr/bin/env python3
"""
final_fix.py — Targeted retries for false-positive deletions + new entries to reach 200.

For previous false positives: uses tighter Wikipedia article-images strategy,
skipping Commons name-only search (which caused wrong matches).
New entries also use the same conservative approach.
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SERIAL_DIR = SCRIPT_DIR / "serial"
SERIAL_DIR.mkdir(exist_ok=True)

SLEEP = 1.2
HEADERS = {"User-Agent": "ActorQuiz/1.0 (educational project; soldarcompany@gmail.com) Python-urllib/3"}

# ---------------------------------------------------------------------------
# Targets: false-positive retries (with exact Wikipedia titles) + new entries
# ---------------------------------------------------------------------------
TARGETS = [
    # --- False-positive retries (specific titles) ---
    ("Colin Ireland",           "Colin Ireland"),
    ("Graham Young",            "Graham Young (poisoner)"),
    ("Patrick Mackay",          "Patrick Mackay (serial killer)"),
    ("Jürgen Bartsch",          "Jürgen Bartsch"),
    ("Huang Yong",              "Huang Yong (serial killer)"),
    ("Seisaku Nakamura",        "Seisaku Nakamura"),
    ("Jeong Nam-gyu",           "Jeong Nam-gyu"),
    ("Auto Shankar",            "Auto Shankar"),
    ("Thug Behram",             "Thuggee"),
    ("Moses Sithole",           "Moses Sithole"),
    ("Stewart Wilken",          "Stewart Wilken"),
    ("John Bunting",            "John Bunting (serial killer)"),
    ("Karla Homolka",           "Karla Homolka"),
    ("Clifford Olson",          "Clifford Olson"),
    ("Lucian Staniak",          "Lucian Staniak"),

    # --- New entries to reach 200 ---
    # USA
    ("David Parker Ray",        "David Parker Ray"),
    ("Robert Berdella",         "Robert Berdella"),
    ("Herb Baumeister",         "Herb Baumeister"),
    ("Anthony Sowell",          "Anthony Sowell"),
    ("Alton Coleman",           "Alton Coleman"),
    ("Craig Price",             "Craig Price (serial killer)"),
    ("Andrew Urdiales",         "Andrew Urdiales"),
    ("Joseph Paul Franklin",    "Joseph Paul Franklin"),
    ("Gary Lewingdon",          "Gary Lewingdon"),
    ("Nathaniel Bar-Jonah",     "Nathaniel Bar-Jonah"),
    ("Robin Gecht",             "Robin Gecht"),
    ("Cleophus Prince Jr.",     "Cleophus Prince Jr."),
    ("Paul Michael Stephani",   "Paul Michael Stephani"),
    ("Michael Bruce Ross",      "Michael Bruce Ross"),
    ("Wayne Adam Ford",         "Wayne Adam Ford"),

    # UK
    ("Archibald Hall",          "Archibald Hall (serial killer)"),
    ("John Bodkin Adams",       "John Bodkin Adams"),
    ("Peter Bryan",             "Peter Bryan (murderer)"),

    # Russia
    ("Anatoly Slivko",          "Anatoly Slivko"),
    ("Sergei Golovkin",         "Sergei Golovkin"),
    ("Gennady Mikhasevich",     "Gennady Mikhasevich"),
    ("Vladimir Ionesyan",       "Vladimir Ionesyan"),
    ("Mikhail Viktorin",        "Mikhail Viktorin"),

    # Germany
    ("Georg Karl Grossmann",    "Georg Karl Grossmann"),
    ("Adolf Seefeld",           "Adolf Seefeld"),
    ("Gunter Kaufmann",         "Günter Kaufmann"),

    # Australia
    ("William Macdonald",       "William Macdonald (serial killer)"),
    ("Eric Cooke",              "Eric Edgar Cooke"),
    ("Arnold Sodeman",          "Arnold Sodeman"),

    # Colombia / Latin America
    ("Pedro Flores Jaramillo",  "Pedro Flores Jaramillo"),
    ("Gregorio Cardenas",       "Gregorio Cárdenas Hernández"),

    # Japan
    ("Kaoru Kobayashi",         "Kaoru Kobayashi (murderer)"),
    ("Hiroshi Maeue",           "Hiroshi Maeue"),

    # Other
    ("Lucía de Berk",           "Lucia de Berk"),
    ("Béatrice Cenci",          "Beatrice Cenci"),
]


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------
def api_get(base_url, params):
    params["format"] = "json"
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read())
    except Exception:
        return None


def wiki_get(params):
    return api_get("https://en.wikipedia.org/w/api.php", params)


def commons_get(params):
    return api_get("https://commons.wikimedia.org/w/api.php", params)


# ---------------------------------------------------------------------------
# Strategy 1 – Wikipedia pageimages thumbnail
# ---------------------------------------------------------------------------
def strategy_pageimages(wiki_title):
    data = wiki_get({
        "action": "query", "titles": wiki_title,
        "prop": "pageimages", "pithumbsize": 320,
        "pilimit": 1, "redirects": 1,
    })
    if not data:
        return None
    for page in data.get("query", {}).get("pages", {}).values():
        src = page.get("thumbnail", {}).get("source")
        if src:
            return src
    return None


# ---------------------------------------------------------------------------
# Strategy 2 – Wikipedia article images → resolve via Commons
# (with strict name-match filter to avoid false positives)
# ---------------------------------------------------------------------------
SKIP_WORDS = ("flag", "icon", "logo", "map", "blank", "stub",
              "commons", "wikimedia", "coat", "seal", "emblem",
              "church", "building", "cinema", "street", "gazette",
              "journal", "magazine", "book", "pdf", "ogg", "wav",
              "panoramio", "cricket", "football", "hockey", "college")

def commons_image_url(file_title):
    for fn in (commons_get, wiki_get):
        data = fn({
            "action": "query", "titles": file_title,
            "prop": "imageinfo", "iiprop": "url|mime",
            "iiurlwidth": 320, "redirects": 1,
        })
        if not data:
            continue
        for page in data.get("query", {}).get("pages", {}).values():
            info_list = page.get("imageinfo", [])
            if info_list:
                url = info_list[0].get("thumburl") or info_list[0].get("url")
                mime = info_list[0].get("mime", "")
                if url and mime.startswith("image/"):
                    return url
    return None


def strategy_article_images(wiki_title, display_name):
    data = wiki_get({
        "action": "query", "titles": wiki_title,
        "prop": "images", "imlimit": 20, "redirects": 1,
    })
    if not data:
        return None
    # Build name tokens for loose match
    name_tokens = set(display_name.lower().replace("-", " ").split())

    for page in data.get("query", {}).get("pages", {}).values():
        images = page.get("images", [])
        for img in images:
            title = img.get("title", "")
            lower = title.lower()
            if any(s in lower for s in SKIP_WORDS):
                continue
            # Prefer images whose filename contains part of the person's name
            file_stem = lower.replace("file:", "").replace(".jpg", "").replace(".png", "").replace(".jpeg", "")
            tokens_found = sum(1 for t in name_tokens if len(t) > 3 and t in file_stem)
            if tokens_found == 0 and len(name_tokens) > 1:
                continue  # Skip images with no name match
            url = commons_image_url(title)
            if url:
                return url
    return None


# ---------------------------------------------------------------------------
# Strategy 3 – Commons search with name + "killer" qualifier (tighter)
# ---------------------------------------------------------------------------
def strategy_commons_search_tight(display_name):
    for query in [f"{display_name} serial killer", f"{display_name} murderer"]:
        data = commons_get({
            "action": "query", "list": "search",
            "srsearch": query, "srnamespace": 6,
            "srlimit": 5, "redirects": 1,
        })
        if not data:
            continue
        name_tokens = set(display_name.lower().replace("-", " ").split())
        for result in data.get("query", {}).get("search", []):
            file_title = result.get("title", "")
            lower = file_title.lower()
            if any(s in lower for s in SKIP_WORDS):
                continue
            file_stem = lower.replace("file:", "")
            tokens_found = sum(1 for t in name_tokens if len(t) > 3 and t in file_stem)
            if tokens_found == 0:
                continue
            url = commons_image_url(file_title)
            if url:
                print(f"  [commons-tight] {file_title}", end=" ", flush=True)
                return url
        time.sleep(0.5)
    return None


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------
def download_image(url, dest_stem):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read()
            ext = url.split(".")[-1].split("?")[0].lower()
            if ext not in ("jpg", "jpeg", "png", "webp", "gif"):
                ext = "jpg"
            dest = SERIAL_DIR / f"{dest_stem}.{ext}"
            with open(dest, "wb") as f:
                f.write(data)
            return True, dest
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 5 * (2 ** attempt)
                print(f"  429 wait {wait}s ...", end=" ", flush=True)
                time.sleep(wait)
            else:
                return False, None
        except Exception:
            return False, None
    return False, None


def already_downloaded(name):
    for ext in ("jpg", "jpeg", "png", "webp", "gif"):
        if (SERIAL_DIR / f"{name}.{ext}").exists():
            return True
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    need = [t for t in TARGETS if not already_downloaded(t[0])]
    print(f"Already have: {len(TARGETS) - len(need)}/{len(TARGETS)}")
    print(f"Need to fetch: {len(need)}\n")

    success = 0
    failed = []

    for idx, (display_name, wiki_title) in enumerate(need, 1):
        print(f"[{idx:3}/{len(need)}] {display_name} ...", end=" ", flush=True)

        img_url = strategy_pageimages(wiki_title)
        time.sleep(SLEEP)

        if not img_url:
            img_url = strategy_article_images(wiki_title, display_name)
            time.sleep(SLEEP)

        if not img_url:
            img_url = strategy_commons_search_tight(display_name)
            time.sleep(SLEEP)

        if not img_url:
            print("FAILED")
            failed.append(display_name)
            continue

        ok, dest = download_image(img_url, display_name)
        if ok:
            print(f"OK -> {dest.name}")
            success += 1
        else:
            print("FAILED (download)")
            failed.append(display_name)

        time.sleep(SLEEP)

    total = len(list(SERIAL_DIR.iterdir()))
    print(f"\n{'='*60}")
    print(f"Images in folder: {total}")
    print(f"Newly fetched: {success}/{len(need)}")
    if failed:
        print(f"\nStill failed ({len(failed)}):")
        for n in failed:
            print(f"  - {n}")


if __name__ == "__main__":
    main()
