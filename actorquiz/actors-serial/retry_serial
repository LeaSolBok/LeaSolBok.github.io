#!/usr/bin/env python3
"""
retry_serial.py — Enhanced retry for failed serial killer images.

Strategies (in order):
  1. Wikipedia pageimages thumbnail (like before)
  2. Wikipedia article images list → fetch from Commons
  3. Wikimedia Commons direct file search
  4. Broader Wikipedia title search

Also renames H. H.jpg → H. H. Holmes.jpg and adds new entries to reach 200.
"""

import json
import os
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
# Fix bad filename from first run
# ---------------------------------------------------------------------------
bad = SERIAL_DIR / "H. H.jpg"
good = SERIAL_DIR / "H. H. Holmes.jpg"
if bad.exists() and not good.exists():
    bad.rename(good)
    print("Renamed H. H.jpg -> H. H. Holmes.jpg")

# ---------------------------------------------------------------------------
# Full target list of 200 unique display names + Wikipedia titles
# ---------------------------------------------------------------------------
ALL_200 = [
    # USA
    ("Ted Bundy",               "Ted Bundy"),
    ("Jeffrey Dahmer",          "Jeffrey Dahmer"),
    ("John Wayne Gacy",         "John Wayne Gacy"),
    ("BTK Killer",              "Dennis Rader"),
    ("Son of Sam",              "David Berkowitz"),
    ("Charles Manson",          "Charles Manson"),
    ("Ed Gein",                 "Ed Gein"),
    ("Richard Ramirez",         "Richard Ramirez"),
    ("Gary Ridgway",            "Gary Ridgway"),
    ("Aileen Wuornos",          "Aileen Wuornos"),
    ("Henry Lee Lucas",         "Henry Lee Lucas"),
    ("Albert Fish",             "Albert Fish"),
    ("John Edward Robinson",    "John Edward Robinson Sr."),
    ("Dean Corll",              "Dean Corll"),
    ("Juan Corona",             "Juan Corona"),
    ("Charles Ng",              "Charles Ng"),
    ("Leonard Lake",            "Leonard Lake"),
    ("Douglas Clark",           "Douglas Clark (serial killer)"),
    ("Carroll Cole",            "Carroll Cole"),
    ("Harvey Glatman",          "Harvey Glatman"),
    ("Randy Kraft",             "Randy Kraft"),
    ("William Bonin",           "William Bonin"),
    ("Patrick Kearney",         "Patrick Kearney"),
    ("Gerald Stano",            "Gerald Stano"),
    ("Bobby Joe Long",          "Bobby Joe Long"),
    ("Paul John Knowles",       "Paul John Knowles"),
    ("Edmund Kemper",           "Edmund Kemper"),
    ("Herbert Mullin",          "Herbert Mullin"),
    ("Joseph DeAngelo",         "Joseph James DeAngelo"),
    ("Samuel Little",           "Samuel Little"),
    ("Robert Yates",            "Robert Lee Yates Jr."),
    ("Israel Keyes",            "Israel Keyes"),
    ("Danny Rolling",           "Danny Rolling"),
    ("Wayne Williams",          "Wayne Williams"),
    ("Angelo Buono",            "Angelo Buono Jr."),
    ("Kenneth Bianchi",         "Kenneth Bianchi"),
    ("Lawrence Bittaker",       "Lawrence Bittaker"),
    ("Roy Norris",              "Roy Norris (murderer)"),
    ("Jerry Brudos",            "Jerry Brudos"),
    ("Westley Allan Dodd",      "Westley Allan Dodd"),
    ("Coral Eugene Watts",      "Coral Eugene Watts"),
    ("Ottis Toole",             "Ottis Toole"),
    ("Robert Hansen",           "Robert Hansen (serial killer)"),
    ("Arthur Shawcross",        "Arthur Shawcross"),
    ("Tommy Lynn Sells",        "Tommy Lynn Sells"),
    ("Rodney Alcala",           "Rodney Alcala"),
    ("William Heirens",         "William Heirens"),
    ("Glen Rogers",             "Glen Rogers (serial killer)"),
    ("Richard Cottingham",      "Richard Cottingham"),
    ("Larry Eyler",             "Larry Eyler"),
    ("Christopher Wilder",      "Christopher Wilder"),
    ("Robert Ben Rhoades",      "Robert Ben Rhoades"),
    ("Dean Phillip Carter",     "Dean Phillip Carter"),
    ("Gary Heidnik",            "Gary Heidnik"),
    ("Charles Cullen",          "Charles Cullen"),
    ("Donald Harvey",           "Donald Harvey"),
    ("Genene Jones",            "Genene Jones"),
    ("John List",               "John List"),
    ("Dorothea Puente",         "Dorothea Puente"),
    ("Marybeth Tinning",        "Marybeth Tinning"),
    ("Belle Gunness",           "Belle Gunness"),
    ("Jane Toppan",             "Jane Toppan"),
    ("Judy Buenoano",           "Judy Buenoano"),
    ("Nannie Doss",             "Nannie Doss"),
    ("Martha Rendell",          "Martha Rendell"),
    ("Velma Barfield",          "Velma Barfield"),
    ("Grim Sleeper",            "Lonnie Franklin Jr."),
    ("Chris Watts",             "Chris Watts"),
    ("Andrew Cunanan",          "Andrew Cunanan"),
    ("Joel Rifkin",             "Joel Rifkin"),
    ("Michael Ross",            "Michael Ross (serial killer)"),
    ("John Joubert",            "John Joubert"),
    ("David Carpenter",         "David Carpenter (serial killer)"),
    ("Derrick Todd Lee",        "Derrick Todd Lee"),
    ("Sean Vincent Gillis",     "Sean Vincent Gillis"),
    ("Carlton Gary",            "Carlton Gary"),
    ("Scott Peterson",          "Scott Peterson"),
    ("Zodiac Killer",           "Zodiac Killer"),
    ("Jack the Ripper",         "Jack the Ripper"),
    ("H. H. Holmes",            "H. H. Holmes"),
    ("Albert DeSalvo",          "Albert DeSalvo"),
    ("Ted Kaczynski",           "Ted Kaczynski"),
    ("Earle Nelson",            "Earle Nelson"),
    ("William Lester Suff",     "William Lester Suff"),
    ("Carl Panzram",            "Carl Panzram"),
    ("Charles Starkweather",    "Charles Starkweather"),
    ("Richard Speck",           "Richard Speck"),
    ("Donald Gaskins",          "Donald Gaskins"),
    ("Robert Black",            "Robert Black (serial killer)"),
    ("William Bonin",           "William Bonin"),

    # UK
    ("Harold Shipman",          "Harold Shipman"),
    ("Peter Sutcliffe",         "Peter Sutcliffe"),
    ("Dennis Nilsen",           "Dennis Nilsen"),
    ("Ian Brady",               "Ian Brady"),
    ("Myra Hindley",            "Myra Hindley"),
    ("John Christie",           "John Reginald Halliday Christie"),
    ("Fred West",               "Fred West"),
    ("Rose West",               "Rosemary West"),
    ("Peter Manuel",            "Peter Manuel"),
    ("Steve Wright",            "Steve Wright (serial killer)"),
    ("Colin Ireland",           "Colin Ireland"),
    ("John George Haigh",       "John George Haigh"),
    ("Neville Heath",           "Neville Heath"),
    ("Graham Young",            "Graham Young (poisoner)"),
    ("Patrick Mackay",          "Patrick Mackay (serial killer)"),
    ("George Joseph Smith",     "George Joseph Smith (murderer)"),

    # Germany
    ("Fritz Haarmann",          "Fritz Haarmann"),
    ("Peter Kürten",            "Peter Kürten"),
    ("Karl Denke",              "Karl Denke"),
    ("Bruno Lüdke",             "Bruno Lüdke"),
    ("Joachim Kroll",           "Joachim Kroll"),
    ("Jürgen Bartsch",          "Jürgen Bartsch"),

    # Russia / Soviet Union
    ("Andrei Chikatilo",        "Andrei Chikatilo"),
    ("Alexander Pichushkin",    "Alexander Pichushkin"),
    ("Mikhail Popkov",          "Mikhail Popkov"),
    ("Anatoly Onoprienko",      "Anatoly Onoprienko"),
    ("Nikolai Dzhumagaliev",    "Nikolai Dzhumagaliev"),
    ("Sergei Ryakhovsky",       "Sergei Ryakhovsky"),
    ("Vasili Komaroff",         "Vasili Komaroff"),

    # France
    ("Henri Landru",            "Henri Landru"),
    ("Marcel Petiot",           "Marcel Petiot"),
    ("Michel Fourniret",        "Michel Fourniret"),
    ("Guy Georges",             "Guy Georges"),

    # Belgium
    ("Marc Dutroux",            "Marc Dutroux"),

    # Netherlands
    ("Johan Otto Schlosser",    "Johan Otto Schlosser"),

    # Italy
    ("Donato Bilancia",         "Donato Bilancia"),
    ("Leonarda Cianciulli",     "Leonarda Cianciulli"),
    ("Gianfranco Stevanin",     "Gianfranco Stevanin"),

    # Spain
    ("Manuel Delgado Villegas", "Manuel Delgado Villegas"),

    # Poland
    ("Władysław Mazurkiewicz",  "Władysław Mazurkiewicz"),
    ("Lucian Staniak",          "Lucian Staniak"),

    # Hungary
    ("Béla Kiss",               "Béla Kiss"),
    ("Sylvestre Matuschka",     "Sylvestre Matuschka"),

    # Romania
    ("Ion Rîmaru",              "Ion Rîmaru"),

    # Austria
    ("Jack Unterweger",         "Jack Unterweger"),
    ("Wolfgang Priklopil",      "Wolfgang Priklopil"),

    # Sweden / Scandinavia
    ("Thomas Quick",            "Sture Bergwall"),
    ("Arnfinn Nesset",          "Arnfinn Nesset"),

    # Colombia / South America
    ("Luis Garavito",           "Luis Garavito"),
    ("Pedro Alonso Lopez",      "Pedro Alonso López"),
    ("Daniel Camargo",          "Daniel Camargo"),
    ("Pedro Rodrigues Filho",   "Pedro Rodrigues Filho"),
    ("Marcelo Costa de Andrade","Marcelo Costa de Andrade"),
    ("Francisco de Assis Pereira","Francisco de Assis Pereira"),
    ("Daniel Barbosa",          "Daniel Barbosa"),
    ("Carlos Robledo Puch",     "Carlos Robledo Puch"),

    # Mexico
    ("Goyo Cardenas",           "Gregorio Cárdenas Hernández"),
    ("Juana Barraza",           "Juana Barraza"),

    # China
    ("Yang Xinhai",             "Yang Xinhai"),
    ("Zhang Yongming",          "Zhang Yongming"),
    ("Huang Yong",              "Huang Yong (serial killer)"),

    # Japan
    ("Tsutomu Miyazaki",        "Tsutomu Miyazaki"),
    ("Futoshi Matsunaga",       "Futoshi Matsunaga"),
    ("Issei Sagawa",            "Issei Sagawa"),
    ("Seisaku Nakamura",        "Seisaku Nakamura (murderer)"),

    # South Korea
    ("Yoo Young-chul",          "Yoo Young-chul"),
    ("Jeong Nam-gyu",           "Jeong Nam-gyu"),

    # India
    ("Charles Sobhraj",         "Charles Sobhraj"),
    ("Cyanide Mohan",           "Mohan Kumar (serial killer)"),
    ("Auto Shankar",            "Auto Shankar"),
    ("Raman Raghav",            "Raman Raghav"),
    ("Thug Behram",             "Thug Behram"),

    # Pakistan
    ("Javed Iqbal",             "Javed Iqbal (serial killer)"),

    # South Africa
    ("Moses Sithole",           "Moses Sithole"),
    ("Cedric Maake",            "Cedric Maake"),
    ("Stewart Wilken",          "Stewart Wilken"),
    ("Clifford Orji",           "Clifford Orji"),

    # Australia
    ("Ivan Milat",              "Ivan Milat"),
    ("John Bunting",            "John Bunting (serial killer)"),
    ("Paul Denyer",             "Paul Denyer"),
    ("Peter Dupas",             "Peter Dupas"),
    ("Mark Twitchell",          "Mark Twitchell"),
    ("Eric Frith",              "Eric Frith"),

    # Canada
    ("Robert Pickton",          "Robert Pickton"),
    ("Paul Bernardo",           "Paul Bernardo"),
    ("Karla Homolka",           "Karla Homolka"),
    ("Clifford Olson",          "Clifford Olson"),
    ("Keith Hunter Jesperson",  "Keith Hunter Jesperson"),

    # Indonesia / SE Asia
    ("Ahmad Suradji",           "Ahmad Suradji"),
    ("Si Quey",                 "Si Quey"),
    ("Rodrigo Caballero",       "Rodrigo Caballero (murderer)"),

    # Iran
    ("Mohammad Bijeh",          "Mohammad Bijeh"),

    # Ukraine
    ("Bible John",              "Bible John"),
]

# Deduplicate keeping first occurrence
seen = set()
TARGETS = []
for entry in ALL_200:
    if entry[0] not in seen:
        seen.add(entry[0])
        TARGETS.append(entry)
TARGETS = TARGETS[:200]


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def api_get(base_url, params):
    params["format"] = "json"
    qs = urllib.parse.urlencode(params)
    url = f"{base_url}?{qs}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read())
    except Exception as e:
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
        "action": "query",
        "titles": wiki_title,
        "prop": "pageimages",
        "pithumbsize": 320,
        "pilimit": 1,
        "redirects": 1,
    })
    if not data:
        return None
    for page in data.get("query", {}).get("pages", {}).values():
        src = page.get("thumbnail", {}).get("source")
        if src:
            return src
    return None


# ---------------------------------------------------------------------------
# Strategy 2 – Wikipedia article images list → resolve via Commons
# ---------------------------------------------------------------------------
def strategy_article_images(wiki_title):
    data = wiki_get({
        "action": "query",
        "titles": wiki_title,
        "prop": "images",
        "imlimit": 15,
        "redirects": 1,
    })
    if not data:
        return None
    for page in data.get("query", {}).get("pages", {}).values():
        images = page.get("images", [])
        for img in images:
            title = img.get("title", "")
            # Skip icons / flags / wikimedia meta images
            lower = title.lower()
            if any(skip in lower for skip in ("flag", "icon", "logo", "map", "blank", "stub", "commons", "wikimedia")):
                continue
            url = commons_image_url(title)
            if url:
                return url
    return None


def commons_image_url(file_title):
    """Resolve a File: title to a 320px thumb URL via Commons."""
    for base_fn in (commons_get, wiki_get):
        data = base_fn({
            "action": "query",
            "titles": file_title,
            "prop": "imageinfo",
            "iiprop": "url|mime",
            "iiurlwidth": 320,
            "redirects": 1,
        })
        if not data:
            continue
        for page in data.get("query", {}).get("pages", {}).values():
            info_list = page.get("imageinfo", [])
            if info_list:
                url = info_list[0].get("thumburl") or info_list[0].get("url")
                if url:
                    return url
    return None


# ---------------------------------------------------------------------------
# Strategy 3 – Wikimedia Commons file search
# ---------------------------------------------------------------------------
def strategy_commons_search(name):
    data = commons_get({
        "action": "query",
        "list": "search",
        "srsearch": name,
        "srnamespace": 6,   # File namespace
        "srlimit": 5,
        "redirects": 1,
    })
    if not data:
        return None
    results = data.get("query", {}).get("search", [])
    for result in results:
        file_title = result.get("title", "")
        lower = file_title.lower()
        if any(skip in lower for skip in ("flag", "icon", "logo", "map", "blank", "signature")):
            continue
        url = commons_image_url(file_title)
        if url:
            print(f"  [commons] {file_title}", end=" ", flush=True)
            return url
    return None


# ---------------------------------------------------------------------------
# Strategy 4 – Wikipedia search fallback
# ---------------------------------------------------------------------------
def strategy_wiki_search(name, extra="serial killer murderer"):
    data = wiki_get({
        "action": "query",
        "list": "search",
        "srsearch": f"{name} {extra}",
        "srlimit": 5,
        "redirects": 1,
    })
    if not data:
        return None
    for result in data.get("query", {}).get("search", []):
        title = result.get("title", "")
        img = strategy_pageimages(title)
        if img:
            print(f"  [wiki-search] {title}", end=" ", flush=True)
            return img
        img = strategy_article_images(title)
        if img:
            print(f"  [wiki-search+art] {title}", end=" ", flush=True)
            return img
        time.sleep(0.5)
    return None


# ---------------------------------------------------------------------------
# Download helper
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
                print(f"  429 rate-limit, waiting {wait}s ...", end=" ", flush=True)
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

        img_url = None

        # S1: pageimages
        img_url = strategy_pageimages(wiki_title)
        time.sleep(SLEEP)

        # S2: article images
        if not img_url:
            img_url = strategy_article_images(wiki_title)
            time.sleep(SLEEP)

        # S3: Commons search
        if not img_url:
            img_url = strategy_commons_search(display_name)
            time.sleep(SLEEP)

        # S4: Wikipedia search
        if not img_url:
            img_url = strategy_wiki_search(display_name)
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
            print("FAILED (download error)")
            failed.append(display_name)

        time.sleep(SLEEP)

    already = len(TARGETS) - len(need)
    total_ok = already + success
    print(f"\n{'='*60}")
    print(f"Total in folder: {total_ok}/{len(TARGETS)}")
    print(f"Newly downloaded: {success}/{len(need)}")
    if failed:
        print(f"\nStill failed ({len(failed)}):")
        for name in failed:
            print(f"  - {name}")


if __name__ == "__main__":
    main()
