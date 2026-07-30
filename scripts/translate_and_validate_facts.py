#!/usr/bin/env python3
"""Complete and validate localized fact-pack JSON files.

The translator is intentionally limited to the three `facts` strings in each
record. Existing localized answer keys are retained; newly created files copy
the source answer key because title/name localization requires authoritative
aliases rather than literal machine translation.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import random
import time
import urllib.parse
import urllib.request
from pathlib import Path


LANGUAGES = ("am", "ar", "de", "el", "es", "fr", "he", "hi", "ja", "ko", "ru", "zh")
TRANSLATE_URL = "https://translate.googleapis.com/translate_a/single"
ROOT = Path(__file__).resolve().parents[1]
PACKS_ROOT = ROOT / "actorquiz" / "packages"


def fact_packs() -> list[Path]:
    return sorted(path for path in PACKS_ROOT.glob("facts_*") if path.is_dir())


def load(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, list):
        raise ValueError(f"{path}: top-level JSON value must be a list")
    return value


def google_translate(lines: list[str], language: str) -> list[str]:
    query = urllib.parse.urlencode(
        {
            "client": "gtx",
            "sl": "en",
            "tl": language,
            "dt": "t",
            "q": "\n".join(lines),
        }
    )
    request = urllib.request.Request(
        f"{TRANSLATE_URL}?{query}",
        headers={"User-Agent": "Mozilla/5.0 fact-pack-localizer/1.0"},
    )
    last_error: Exception | None = None
    for attempt in range(8):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                payload = json.load(response)
            translated = "".join(part[0] for part in payload[0]).splitlines()
            if len(translated) != len(lines) or any(not line.strip() for line in translated):
                raise ValueError(
                    f"expected {len(lines)} translated lines, received {len(translated)}"
                )
            return [line.strip() for line in translated]
        except Exception as error:
            last_error = error
            time.sleep(min(30, (2**attempt) + random.random()))
    raise RuntimeError(f"translation failed for {language}: {last_error}")


def batches(lines: list[str], max_chars: int = 4200) -> list[list[str]]:
    result: list[list[str]] = []
    current: list[str] = []
    size = 0
    for line in lines:
        added = len(line) + (1 if current else 0)
        if current and size + added > max_chars:
            result.append(current)
            current = []
            size = 0
        current.append(line)
        size += len(line) + (1 if len(current) > 1 else 0)
    if current:
        result.append(current)
    return result


def localize_pack(pack: Path, language: str, force: bool) -> str:
    source_path = pack / "data.json"
    target_path = pack / f"data_{language}.json"
    source = load(source_path)
    target = load(target_path) if target_path.exists() else None

    source_facts = [fact for record in source for fact in record.get("facts", [])]
    target_facts = (
        [fact for record in target for fact in record.get("facts", [])]
        if target is not None
        else []
    )
    needs_translation = (
        force
        or target is None
        or len(target) != len(source)
        or len(target_facts) != len(source_facts)
        or target_facts == source_facts
    )
    if not needs_translation:
        return f"{pack.name}/{language}: kept existing translation"

    translated: list[str] = []
    for chunk in batches(source_facts):
        translated.extend(google_translate(chunk, language))

    localized = [dict(record) for record in source]
    offset = 0
    for record in localized:
        count = len(record.get("facts", []))
        record["facts"] = translated[offset : offset + count]
        offset += count

    temporary = target_path.with_suffix(".json.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(localized, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    temporary.replace(target_path)
    return f"{pack.name}/{language}: wrote {len(translated)} translated facts"


def validate() -> list[str]:
    errors: list[str] = []
    for pack in fact_packs():
        source = load(pack / "data.json")
        source_facts = [fact for record in source for fact in record.get("facts", [])]
        if any(len(record.get("facts", [])) != 3 for record in source):
            errors.append(f"{pack.name}/en: every record must contain exactly 3 facts")
        for language in LANGUAGES:
            path = pack / f"data_{language}.json"
            if not path.exists():
                errors.append(f"{pack.name}/{language}: missing file")
                continue
            localized = load(path)
            if len(localized) != len(source):
                errors.append(
                    f"{pack.name}/{language}: {len(localized)} records; expected {len(source)}"
                )
                continue
            facts = [fact for record in localized for fact in record.get("facts", [])]
            if len(facts) != len(source_facts):
                errors.append(
                    f"{pack.name}/{language}: {len(facts)} facts; expected {len(source_facts)}"
                )
            if facts == source_facts:
                errors.append(f"{pack.name}/{language}: facts are an exact English copy")
            for index, (base, item) in enumerate(zip(source, localized)):
                if item.get("tmdb_id") != base.get("tmdb_id"):
                    errors.append(
                        f"{pack.name}/{language}[{index}]: tmdb_id differs from English"
                    )
                if item.get("gender") != base.get("gender"):
                    errors.append(
                        f"{pack.name}/{language}[{index}]: gender differs from English"
                    )
                if any(not isinstance(fact, str) or not fact.strip() for fact in item.get("facts", [])):
                    errors.append(f"{pack.name}/{language}[{index}]: blank or invalid fact")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--force", action="store_true", help="retranslate existing localized facts")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    if not args.validate_only:
        jobs = [(pack, language) for pack in fact_packs() for language in LANGUAGES]
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(localize_pack, pack, language, args.force): (pack, language)
                for pack, language in jobs
            }
            for future in concurrent.futures.as_completed(futures):
                print(future.result(), flush=True)

    errors = validate()
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print(f"Validated {len(fact_packs())} fact packs in {len(LANGUAGES) + 1} languages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
