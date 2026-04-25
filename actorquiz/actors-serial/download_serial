#!/usr/bin/env python3
"""
download_serial.py — Download profile images for 200 world-famous serial killers / murderers.

Uses Wikipedia API to fetch thumbnail images. Falls back to search.

Usage:
    python3 download_serial.py
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

SLEEP = 1.5
HEADERS = {"User-Agent": "ActorQuiz/1.0 (educational project; soldarcompany@gmail.com) Python-urllib/3"}

TOP_200_SERIAL_KILLERS = [
    # USA
    ("Ted Bundy", "Ted Bundy"),
    ("Jeffrey Dahmer", "Jeffrey Dahmer"),
    ("John Wayne Gacy", "John Wayne Gacy"),
    ("BTK Killer", "Dennis Rader"),
    ("Son of Sam", "David Berkowitz"),
    ("Charles Manson", "Charles Manson"),
    ("Ed Gein", "Ed Gein"),
    ("Richard Ramirez", "Richard Ramirez"),
    ("Gary Ridgway", "Gary Ridgway"),
    ("Aileen Wuornos", "Aileen Wuornos"),
    ("Henry Lee Lucas", "Henry Lee Lucas"),
    ("Albert Fish", "Albert Fish"),
    ("John Edward Robinson", "John Edward Robinson Sr."),
    ("Dean Corll", "Dean Corll"),
    ("Juan Corona", "Juan Corona"),
    ("Charles Ng", "Charles Ng"),
    ("Leonard Lake", "Leonard Lake"),
    ("Douglas Clark", "Douglas Clark (serial killer)"),
    ("Carroll Cole", "Carroll Cole"),
    ("Harvey Glatman", "Harvey Glatman"),
    ("Randy Kraft", "Randy Kraft"),
    ("William Bonin", "William Bonin"),
    ("Patrick Kearney", "Patrick Kearney"),
    ("Gerald Stano", "Gerald Stano"),
    ("Bobby Joe Long", "Bobby Joe Long"),
    ("Paul John Knowles", "Paul John Knowles"),
    ("Edmund Kemper", "Edmund Kemper"),
    ("Herbert Mullin", "Herbert Mullin"),
    ("Joseph DeAngelo", "Joseph James DeAngelo"),
    ("Samuel Little", "Samuel Little"),
    ("Robert Yates", "Robert Lee Yates Jr."),
    ("Israel Keyes", "Israel Keyes"),
    ("Danny Rolling", "Danny Rolling"),
    ("Wayne Williams", "Wayne Williams"),
    ("Angelo Buono", "Angelo Buono Jr."),
    ("Kenneth Bianchi", "Kenneth Bianchi"),
    ("Lawrence Bittaker", "Lawrence Bittaker"),
    ("Roy Norris", "Roy Norris (murderer)"),
    ("Jerry Brudos", "Jerry Brudos"),
    ("Westley Allan Dodd", "Westley Allan Dodd"),
    ("Coral Eugene Watts", "Coral Eugene Watts"),
    ("Ottis Toole", "Ottis Toole"),
    ("Robert Hansen", "Robert Hansen (serial killer)"),
    ("Arthur Shawcross", "Arthur Shawcross"),
    ("Tommy Lynn Sells", "Tommy Lynn Sells"),
    ("Luis Garavito", "Luis Garavito"),
    ("Pedro Alonso Lopez", "Pedro Alonso López"),
    ("Daniel Camargo", "Daniel Camargo"),

    # UK
    ("Harold Shipman", "Harold Shipman"),
    ("Peter Sutcliffe", "Peter Sutcliffe"),
    ("Dennis Nilsen", "Dennis Nilsen"),
    ("Ian Brady", "Ian Brady"),
    ("Myra Hindley", "Myra Hindley"),
    ("John Christie", "John Reginald Halliday Christie"),
    ("Fred West", "Fred West"),
    ("Rose West", "Rosemary West"),
    ("Peter Manuel", "Peter Manuel"),
    ("Robert Black", "Robert Black (serial killer)"),
    ("Steve Wright", "Steve Wright (serial killer)"),
    ("Colin Ireland", "Colin Ireland"),

    # Germany
    ("Fritz Haarmann", "Fritz Haarmann"),
    ("Peter Kürten", "Peter Kürten"),
    ("Karl Denke", "Karl Denke"),
    ("Bruno Lüdke", "Bruno Lüdke"),
    ("Joachim Kroll", "Joachim Kroll"),
    ("Jürgen Bartsch", "Jürgen Bartsch"),

    # Russia / Soviet Union
    ("Andrei Chikatilo", "Andrei Chikatilo"),
    ("Alexander Pichushkin", "Alexander Pichushkin"),
    ("Mikhail Popkov", "Mikhail Popkov"),
    ("Anatoly Onoprienko", "Anatoly Onoprienko"),
    ("Nikolai Dzhumagaliev", "Nikolai Dzhumagaliev"),
    ("Sergei Ryakhovsky", "Sergei Ryakhovsky"),
    ("Vasili Komaroff", "Vasili Komaroff"),

    # France
    ("Henri Landru", "Henri Landru"),
    ("Marcel Petiot", "Marcel Petiot"),
    ("Michel Fourniret", "Michel Fourniret"),
    ("Guy Georges", "Guy Georges"),

    # Belgium
    ("Marc Dutroux", "Marc Dutroux"),

    # Netherlands
    ("Johan Otto Schlosser", "Johan Otto Schlosser"),

    # Italy
    ("Donato Bilancia", "Donato Bilancia"),
    ("Leonarda Cianciulli", "Leonarda Cianciulli"),
    ("Gianfranco Stevanin", "Gianfranco Stevanin"),

    # Spain
    ("Manuel Delgado Villegas", "Manuel Delgado Villegas"),

    # Poland
    ("Władysław Mazurkiewicz", "Władysław Mazurkiewicz"),
    ("Lucian Staniak", "Lucian Staniak"),

    # Hungary
    ("Béla Kiss", "Béla Kiss"),

    # Romania
    ("Ion Rîmaru", "Ion Rîmaru"),

    # Colombia
    ("Pedro Rodrigues Filho", "Pedro Rodrigues Filho"),
    ("Daniel Barbosa", "Daniel Barbosa"),

    # Brazil
    ("Marcelo Costa de Andrade", "Marcelo Costa de Andrade"),
    ("Francisco de Assis Pereira", "Francisco de Assis Pereira"),

    # Mexico
    ("Goyo Cardenas", "Gregorio Cárdenas Hernández"),
    ("Juana Barraza", "Juana Barraza"),

    # Argentina
    ("Carlos Robledo Puch", "Carlos Robledo Puch"),

    # China
    ("Yang Xinhai", "Yang Xinhai"),
    ("Zhang Yongming", "Zhang Yongming"),
    ("Huang Yong", "Huang Yong (serial killer)"),
    ("Liu Minghao", "Liu Minghao"),

    # Japan
    ("Tsutomu Miyazaki", "Tsutomu Miyazaki"),
    ("Seisaku Nakamura", "Seisaku Nakamura (murderer)"),
    ("Futoshi Matsunaga", "Futoshi Matsunaga"),
    ("Issei Sagawa", "Issei Sagawa"),
    ("Kaoru Kobayashi", "Kaoru Kobayashi (murderer)"),

    # South Korea
    ("Yoo Young-chul", "Yoo Young-chul"),
    ("Jeong Nam-gyu", "Jeong Nam-gyu"),

    # India
    ("Charles Sobhraj", "Charles Sobhraj"),
    ("Thug Behram", "Thug Behram"),
    ("Cyanide Mohan", "Mohan Kumar (serial killer)"),
    ("Auto Shankar", "Auto Shankar"),
    ("Raman Raghav", "Raman Raghav"),

    # Pakistan
    ("Javed Iqbal", "Javed Iqbal (serial killer)"),

    # South Africa
    ("Moses Sithole", "Moses Sithole"),
    ("Cedric Maake", "Cedric Maake"),
    ("Stewart Wilken", "Stewart Wilken"),

    # Nigeria
    ("Clifford Orji", "Clifford Orji"),

    # Australia
    ("Ivan Milat", "Ivan Milat"),
    ("John Bunting", "John Bunting (serial killer)"),
    ("Robert Wagner", "Robert Joe Wagner"),
    ("Eric Frith", "Eric Frith"),
    ("Paul Denyer", "Paul Denyer"),
    ("Peter Dupas", "Peter Dupas"),
    ("Mark Twitchell", "Mark Twitchell"),
    ("Snowtown murders", "John Justin Bunting"),

    # Canada
    ("Robert Pickton", "Robert Pickton"),
    ("Paul Bernardo", "Paul Bernardo"),
    ("Karla Homolka", "Karla Homolka"),
    ("Clifford Olson", "Clifford Olson"),
    ("Keith Hunter Jesperson", "Keith Hunter Jesperson"),

    # USA (continued)
    ("Grim Sleeper", "Lonnie Franklin Jr."),
    ("Chris Watts", "Chris Watts"),
    ("Scott Peterson", "Scott Peterson"),
    ("Andrew Cunanan", "Andrew Cunanan"),
    ("Joel Rifkin", "Joel Rifkin"),
    ("Michael Ross", "Michael Ross (serial killer)"),
    ("John Joubert", "John Joubert"),
    ("David Carpenter", "David Carpenter (serial killer)"),
    ("Derrick Todd Lee", "Derrick Todd Lee"),
    ("Sean Vincent Gillis", "Sean Vincent Gillis"),
    ("Rodney Alcala", "Rodney Alcala"),
    ("William Heirens", "William Heirens"),
    ("Carlton Gary", "Carlton Gary"),
    ("Glen Rogers", "Glen Rogers (serial killer)"),
    ("Richard Cottingham", "Richard Cottingham"),
    ("Joseph Fischer", "Joseph Fischer (serial killer)"),
    ("Larry Eyler", "Larry Eyler"),
    ("Christopher Wilder", "Christopher Wilder"),
    ("Robert Ben Rhoades", "Robert Ben Rhoades"),
    ("Dean Phillip Carter", "Dean Phillip Carter"),
    ("Gary Heidnik", "Gary Heidnik"),
    ("Charles Cullen", "Charles Cullen"),
    ("Donald Harvey", "Donald Harvey"),
    ("Genene Jones", "Genene Jones"),
    ("John List", "John List"),
    ("Dorothea Puente", "Dorothea Puente"),
    ("Marybeth Tinning", "Marybeth Tinning"),
    ("Belle Gunness", "Belle Gunness"),
    ("Jane Toppan", "Jane Toppan"),
    ("Judy Buenoano", "Judy Buenoano"),
    ("Nannie Doss", "Nannie Doss"),
    ("Martha Rendell", "Martha Rendell"),
    ("Velma Barfield", "Velma Barfield"),

    # Austria
    ("Jack Unterweger", "Jack Unterweger"),
    ("Wolfgang Priklopil", "Wolfgang Priklopil"),

    # Czech Republic
    ("Jaroslav Stibůrek", "Jaroslav Stibůrek"),

    # Sweden
    ("Thomas Quick", "Sture Bergwall"),

    # Finland
    ("Pentti Nousiainen", "Pentti Nousiainen"),

    # Norway
    ("Arnfinn Nesset", "Arnfinn Nesset"),

    # Scotland
    ("Bible John", "Bible John"),

    # Hungary
    ("Sylvestre Matuschka", "Sylvestre Matuschka"),

    # Indonesia
    ("Ahmad Suradji", "Ahmad Suradji"),
    ("Ryan Jombang", "Very Idham Henyansyah"),

    # Philippines
    ("Rodrigo Caballero", "Rodrigo Caballero (murderer)"),

    # Thailand
    ("Si Quey", "Si Quey"),
    ("Charles Sobhraj", "Charles Sobhraj"),

    # Iran
    ("Ali Asghar Borujerdi", "Ali Asghar Borujerdi"),
    ("Mohammad Bijeh", "Mohammad Bijeh"),

    # Ukraine
    ("Anatoly Onoprienko", "Anatoly Onoprienko"),

    # Kazakhstan
    ("Nikolai Dzhumagaliev", "Nikolai Dzhumagaliev"),

    # USA (more)
    ("Zodiac Killer", "Zodiac Killer"),
    ("Jack the Ripper", "Jack the Ripper"),
    ("H. H. Holmes", "H. H. Holmes"),
    ("Albert DeSalvo", "Albert DeSalvo"),
    ("Ted Kaczynski", "Ted Kaczynski"),
    ("Earle Nelson", "Earle Nelson"),
    ("Harvey Murray Glatman", "Harvey Glatman"),
    ("William Lester Suff", "William Lester Suff"),
    ("Robert Lee Yates", "Robert Lee Yates Jr."),
]

# Deduplicate by display name
seen = set()
KILLERS = []
for entry in TOP_200_SERIAL_KILLERS:
    if entry[0] not in seen:
        seen.add(entry[0])
        KILLERS.append(entry)
KILLERS = KILLERS[:200]


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
    data = wiki_get({
        "action": "query",
        "list": "search",
        "srsearch": f"{name} serial killer murderer",
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
        if (SERIAL_DIR / f"{name}.{ext}").exists():
            return True
    return False


def main():
    print(f"Downloading images for {len(KILLERS)} serial killers...\n")
    success = 0
    failed = []

    for idx, (display_name, wiki_title) in enumerate(KILLERS, 1):
        print(f"[{idx:3}/{len(KILLERS)}] {display_name} (wiki: '{wiki_title}') ...", end=" ", flush=True)

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

        dest = SERIAL_DIR / display_name
        ok, final_path = download_image(img_url, dest)
        if ok:
            print(f"OK -> {final_path.name}")
            success += 1
        else:
            print("FAILED (download error)")
            failed.append(display_name)

        time.sleep(SLEEP)

    print(f"\n{'='*60}")
    print(f"Done. Success: {success}/{len(KILLERS)}")
    if failed:
        print(f"Failed ({len(failed)}):")
        for name in failed:
            print(f"  - {name}")


if __name__ == "__main__":
    main()
