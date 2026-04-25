#!/usr/bin/env python3
"""
fill_gaps.py — Add clean replacement entries to reach 200 images.
Uses only Wikipedia pageimages (most reliable, avoids wrong-person Commons matches).
"""

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SERIAL_DIR = SCRIPT_DIR / "serial"

SLEEP = 1.2
HEADERS = {"User-Agent": "ActorQuiz/1.0 (educational project; soldarcompany@gmail.com) Python-urllib/3"}

TARGETS = [
    # Replacements + extras — all have confirmed Wikipedia articles
    ("Cary Stayner",            "Cary Stayner"),
    ("Gary Gilmore",            "Gary Gilmore"),
    ("Norman Collins",          "John Norman Collins"),
    ("Michael Swango",          "Michael Swango"),
    ("Kendall Francois",        "Kendall Francois"),
    ("Charles Albright",        "Charles Albright (serial killer)"),
    ("Orville Majors",          "Orville Lynn Majors"),
    ("Robert Shulman",          "Robert Shulman (murderer)"),
    ("Richard Biegenwald",      "Richard Biegenwald"),
    ("James Koedatich",         "James Koedatich"),
    ("Cesar Barone",            "Cesar Barone"),
    ("Hadden Clark",            "Hadden Clark"),
    ("Sean Sellers",            "Sean Sellers"),
    ("Graham Young",            "Graham Young (poisoner)"),
    ("Colin Ireland",           "Colin Ireland"),
    ("Karla Homolka",           "Karla Homolka"),
    ("Clifford Olson",          "Clifford Olson"),
    ("John Bunting",            "John Justin Bunting"),
    ("Patrick Mackay",          "Patrick Mackay (serial killer)"),
    ("Archibald Hall",          "Archibald Hall (serial killer)"),
    ("Alton Coleman",           "Alton Coleman (serial killer)"),
    ("William Macdonald",       "William Macdonald (serial killer)"),
    ("Peter Bryan",             "Peter Bryan (murderer)"),
    ("Jürgen Bartsch",          "Jürgen Bartsch"),
    ("Stewart Wilken",          "Stewart Wilken"),
    ("Moses Sithole",           "Moses Sithole"),
    ("Huang Yong",              "Huang Yong (serial killer)"),
    ("Jeong Nam-gyu",           "Jeong Nam-gyu"),
    ("Auto Shankar",            "Auto Shankar"),
    ("Lucian Staniak",          "Lucian Staniak"),
]


def wiki_get(params):
    params["format"] = "json"
    url = f"https://en.wikipedia.org/w/api.php?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read())
    except Exception:
        return None


def get_thumb(wiki_title):
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


def get_article_image(wiki_title, name_tokens):
    """Try article images list, strict name match only."""
    data = wiki_get({
        "action": "query", "titles": wiki_title,
        "prop": "images", "imlimit": 20, "redirects": 1,
    })
    if not data:
        return None
    skip = ("flag", "icon", "logo", "map", "blank", "stub", "commons",
            "church", "building", "cinema", "gazette", "journal",
            "panoramio", "football", "hockey", "college", "ogg", "wav", "pdf")
    tokens = [t.lower() for t in name_tokens if len(t) > 3]
    for page in data.get("query", {}).get("pages", {}).values():
        for img in page.get("images", []):
            title = img.get("title", "")
            lower = title.lower()
            if any(s in lower for s in skip):
                continue
            stem = lower.replace("file:", "")
            # Require at least 2 name tokens OR a rare token to match
            hits = sum(1 for t in tokens if t in stem)
            if hits < 2 and not (len(tokens) == 1 and hits == 1):
                continue
            # Resolve URL
            data2 = wiki_get({
                "action": "query", "titles": title,
                "prop": "imageinfo", "iiprop": "url|mime",
                "iiurlwidth": 320, "redirects": 1,
            })
            if not data2:
                continue
            for p2 in data2.get("query", {}).get("pages", {}).values():
                iil = p2.get("imageinfo", [])
                if iil:
                    mime = iil[0].get("mime", "")
                    url = iil[0].get("thumburl") or iil[0].get("url")
                    if url and mime.startswith("image/"):
                        return url
    return None


def download(url, stem):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
        ext = url.split(".")[-1].split("?")[0].lower()
        if ext not in ("jpg", "jpeg", "png", "webp", "gif"):
            ext = "jpg"
        dest = SERIAL_DIR / f"{stem}.{ext}"
        dest.write_bytes(data)
        return dest
    except Exception:
        return None


def have(name):
    return any((SERIAL_DIR / f"{name}.{ext}").exists()
               for ext in ("jpg", "jpeg", "png", "webp", "gif"))


def main():
    need = [(n, t) for n, t in TARGETS if not have(n)]
    print(f"Currently in folder: {len(list(SERIAL_DIR.iterdir()))}")
    print(f"Need to fetch: {len(need)}\n")
    failed = []
    for i, (name, title) in enumerate(need, 1):
        tokens = name.replace(".", "").split()
        print(f"[{i:2}/{len(need)}] {name} ...", end=" ", flush=True)

        url = get_thumb(title)
        time.sleep(SLEEP)

        if not url:
            url = get_article_image(title, tokens)
            time.sleep(SLEEP)

        if not url:
            print("FAILED")
            failed.append(name)
            continue

        dest = download(url, name)
        if dest:
            print(f"OK -> {dest.name}")
        else:
            print("FAILED (download)")
            failed.append(name)
        time.sleep(SLEEP)

    total = len(list(SERIAL_DIR.iterdir()))
    print(f"\nImages in folder: {total}")
    if failed:
        print(f"Still no image ({len(failed)}): {failed}")


if __name__ == "__main__":
    main()
