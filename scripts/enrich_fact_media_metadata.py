#!/usr/bin/env python3
"""Enrich fact packs from their canonical detail providers.

TMDB supplies IDs and localized titles for movies, TV, anime, cartoons, and
people. RAWG supplies the IDs for games because GamePage uses the RAWG API and
TMDB does not index video games. The script deliberately fails for ambiguous
or missing matches instead of silently assigning a wrong detail page.

Usage:
  TMDB_API_KEY=... RAWG_API_KEY=... python3 scripts/enrich_fact_media_metadata.py
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKS = ROOT / "actorquiz" / "packages"
LANGUAGES = ("am", "ar", "de", "el", "es", "fr", "he", "hi", "ja", "ko", "ru", "zh")
TMDB_LANGUAGES = {
    "am": "am-ET", "ar": "ar-SA", "de": "de-DE", "el": "el-GR",
    "es": "es-ES", "fr": "fr-FR", "he": "he-IL", "hi": "hi-IN",
    "ja": "ja-JP", "ko": "ko-KR", "ru": "ru-RU", "zh": "zh-CN",
}
TMDB_PACKS = {
    "facts_movies": "movie",
    "facts_tvshows": "tv",
    "facts_anime": "tv",
    "facts_cartoons": "tv",
}
# Pack labels sometimes denote a franchise or use a familiar short title rather
# than TMDB's canonical title. These are reviewed aliases, not fuzzy matches.
TMDB_SEARCH_ALIASES = {
    "Harry Potter": "Harry Potter and the Philosopher's Stone",
    "Indiana Jones": "Raiders of the Lost Ark",
    "Terminator": "The Terminator",
    "Pirates of the Caribbean": "Pirates of the Caribbean: The Curse of the Black Pearl",
    "A New Hope": "Star Wars: Episode IV - A New Hope",
    "The Force Awakens": "Star Wars: The Force Awakens",
    "Kill Bill": "Kill Bill: Vol. 1",
    "Rocky Horror Picture Show": "The Rocky Horror Picture Show",
    "School of Rock": "The School of Rock",
    "Anchorman": "Anchorman: The Legend of Ron Burgundy",
    "Borat": "Borat",
    "Ready or Not 2 Here I Come": "Ready or Not: Here I Come",
}
TMDB_ID_OVERRIDES = {
    "A New Hope": 11,
    "Borat": 496,
    "Attack on Titan Final Season": 1429,
    "Ben 10 4686": 4686,
    "Daredevil": 61889,
    "Agents of Shield": 1403,
    "Law and Order Svu": 2734,
    "Bakemonogatari": 46195,
    "When They Cry": 25760,
    "Inuyashiki Last Hero": 73946,
    "A Lull in the Sea": 61408,
    "Ben 10 68295": 68295,
    "Lilo and Stitch the Series": 2355,
    "Scooby Doo": 18123,
    "Yogi Bear": 30773,
    "Voltron": 66558,
    "The Ren and Stimpy Show": 504,
}
RAWG_ID_OVERRIDES = {
    "Call of Duty Modern Warfare": 884,
    "Warcraft Iii": 30445,
    "Pokemon Red and Blue": 23762,
    "Street Fighter Ii": 55132,
    "Sonic the Hedgehog": 283965,
    "Mega Man 2": 53939,
    "Civilization Vi": 10297,
}


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "fact-pack-enricher/1.0"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except Exception:
            if attempt == 4:
                raise
            time.sleep(1.5 * (attempt + 1))
    raise AssertionError("unreachable")


def tmdb_url(path: str, key: str, **query: str) -> str:
    return "https://api.themoviedb.org/3/" + path + "?" + urllib.parse.urlencode({"api_key": key, **query})


def match_tmdb(title: str, media_type: str, key: str) -> dict:
    canonical_title = TMDB_SEARCH_ALIASES.get(title, title)
    results = get_json(tmdb_url(f"search/{media_type}", key, query=canonical_title, language="en-US")).get("results", [])
    wanted = normalize(canonical_title)
    exact = [r for r in results if normalize(str(r.get("title") or r.get("name") or "")) == wanted]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        # The highest-popularity exact title is normally the intended work.
        return max(exact, key=lambda r: float(r.get("popularity") or 0))
    if not results:
        raise ValueError(f"TMDB: no {media_type} result for {title!r}")
    best = results[0]
    raise ValueError(f"TMDB: no exact {media_type} title for {title!r}; best was {best.get('title') or best.get('name')!r}")


def tmdb_titles(media_type: str, tmdb_id: int, key: str, english: str) -> dict[str, str]:
    payload = get_json(tmdb_url(f"{media_type}/{tmdb_id}/translations", key))
    by_language: dict[str, str] = {}
    for item in payload.get("translations", []):
        code = item.get("iso_639_1")
        data = item.get("data") or {}
        title = str(data.get("title") or data.get("name") or "").strip()
        if code and title:
            by_language[code] = title
    return {language: by_language.get(language, english) for language in LANGUAGES}


def match_rawg(title: str, key: str) -> dict:
    url = "https://api.rawg.io/api/games?" + urllib.parse.urlencode({"key": key, "search": title, "page_size": "20"})
    results = get_json(url).get("results", [])
    wanted = normalize(title)
    exact = [r for r in results if normalize(str(r.get("name") or "")) == wanted]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        return max(exact, key=lambda r: int(r.get("ratings_count") or 0))
    if not results:
        raise ValueError(f"RAWG: no game result for {title!r}")
    raise ValueError(f"RAWG: no exact game title for {title!r}; best was {results[0].get('name')!r}")


def load(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write(path: Path, data: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def enrich_tmdb_record(record: dict, media_type: str, key: str) -> None:
    tmdb_id = TMDB_ID_OVERRIDES.get(record["celebrity"])
    result = match_tmdb(record["celebrity"], media_type, key) if tmdb_id is None else None
    record["tmdb_id"] = tmdb_id or int(result["id"])
    record["media_type"] = media_type
    record["localized_titles"] = tmdb_titles(media_type, record["tmdb_id"], key, record["celebrity"])


def enrich_game_record(record: dict, key: str) -> None:
    rawg_id = RAWG_ID_OVERRIDES.get(record["celebrity"])
    result = match_rawg(record["celebrity"], key) if rawg_id is None else None
    record["rawg_id"] = rawg_id or int(result["id"])
    record["media_type"] = "game"
    # RAWG does not provide the app's supported localized answer languages.
    # Keep the canonical RAWG display name rather than machine-translating it.
    canonical_title = str(result["name"]) if result is not None else record["celebrity"]
    record["localized_titles"] = {language: canonical_title for language in LANGUAGES}


def localize_records(pack: Path, source: list[dict]) -> None:
    for language in LANGUAGES:
        path = pack / f"data_{language}.json"
        localized = load(path)
        if len(localized) != len(source):
            raise ValueError(f"{path}: record count does not match data.json")
        for base, item in zip(source, localized):
            # A sliced run only updates records it could authoritatively enrich.
            if "media_type" not in base:
                continue
            item["celebrity"] = base.get("localized_titles", {}).get(language, base["celebrity"])
            for field in ("tmdb_id", "rawg_id", "media_type"):
                item.pop(field, None)
                if field in base:
                    item[field] = base[field]
        write(path, localized)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--pack", choices=(*TMDB_PACKS, "facts_games"))
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    tmdb_key = os.environ.get("TMDB_API_KEY", "")
    rawg_key = os.environ.get("RAWG_API_KEY", "")
    if not tmdb_key or not rawg_key:
        raise SystemExit("Set TMDB_API_KEY and RAWG_API_KEY before running this script.")

    errors: list[str] = []
    selected_tmdb_packs = TMDB_PACKS.items() if args.pack is None else ((args.pack, TMDB_PACKS[args.pack]),) if args.pack in TMDB_PACKS else ()
    for pack_name, media_type in selected_tmdb_packs:
        path = PACKS / pack_name / "data.json"
        records = load(path)
        selected = records[args.offset : args.offset + args.limit if args.limit else None]
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(enrich_tmdb_record, record, media_type, tmdb_key) for record in selected]
            for record, future in zip(selected, futures):
                try:
                    future.result()
                except Exception as error:
                    errors.append(f"{pack_name}/{record['celebrity']}: {error}")
        write(path, records)
        localize_records(path.parent, records)

    if args.pack in (None, "facts_games"):
        game_path = PACKS / "facts_games" / "data.json"
        games = load(game_path)
        selected = games[args.offset : args.offset + args.limit if args.limit else None]
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(enrich_game_record, record, rawg_key) for record in selected]
            for record, future in zip(selected, futures):
                try:
                    future.result()
                except Exception as error:
                    errors.append(f"facts_games/{record['celebrity']}: {error}")
        write(game_path, games)
        localize_records(game_path.parent, games)

    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print("Enriched entertainment fact packs from TMDB and RAWG.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
