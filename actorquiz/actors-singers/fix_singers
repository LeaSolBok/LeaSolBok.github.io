#!/usr/bin/env python3
"""
fix_singers.py — Audit and fix singer image files.

Usage:
    TMDB_API_KEY=xxx python3 fix_singers.py [--audit-only]

Steps (when not --audit-only):
  1. Audit: verify each presingers/ file's embedded TMDB ID matches the named artist
  2. Fix:   for mismatches, download the correct image and remove stale Gemini toons
  3. Rename: strip TMDB ID suffix from all files in both directories

Fix logic:
  - If TMDB search by artist name returns the SAME id as already embedded → image is correct
    (stage name / legal name difference — skip download, leave as-is)
  - If TMDB search returns a DIFFERENT id → download the correct image
  - Duplicate-ID conflicts: when two files share the same TMDB id, flag the worse match
"""

import os
import re
import sys
import time
import difflib
import urllib.request
import urllib.error
import urllib.parse
import json
from pathlib import Path

# ── Config ───────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent
PRESINGERS   = SCRIPT_DIR / "presingers"
GEMINI_DIR   = SCRIPT_DIR / "Singers Gemini"
TMDB_BASE    = "https://api.themoviedb.org/3"
IMG_BASE     = "https://image.tmdb.org/t/p/h632"
SLEEP        = 0.26    # seconds between TMDB API calls
MATCH_THRESH = 0.55    # fuzzy name-similarity floor for audit

# ── Helpers ──────────────────────────────────────────────────────────────────

def get_api_key():
    key = os.environ.get("TMDB_API_KEY", "").strip()
    if not key:
        print("ERROR: TMDB_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)
    return key


def tmdb_get(path, params, api_key):
    qs  = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    url = f"{TMDB_BASE}{path}?api_key={api_key}&{qs}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  TMDB request failed ({path}): {e}")
        return None


def similarity(a, b):
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def download_image(url, dest_path):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = r.read()
        with open(dest_path, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"  Download failed ({url}): {e}")
        return False


def parse_filename(filename):
    """Return (name, tmdb_id, ext) or None."""
    m = re.match(r'^(.+?)\s+(\d+)\.(jpg|jpeg|png|webp)$', filename, re.IGNORECASE)
    if m:
        return m.group(1).strip(), m.group(2), m.group(3).lower()
    return None


def find_gemini_file(name):
    """Find file in Gemini dir whose stem name (sans ID) matches `name`."""
    for f in GEMINI_DIR.iterdir():
        if f.name.startswith('.'):
            continue
        parsed = parse_filename(f.name)
        fname  = parsed[0] if parsed else f.stem
        if fname.lower() == name.lower():
            return f
    return None


# ── Step 1: Audit ─────────────────────────────────────────────────────────────

def audit(api_key):
    results = []
    files   = sorted(PRESINGERS.iterdir())
    items   = [f for f in files if not f.name.startswith('.') and not f.is_dir()]
    total   = len(items)

    for idx, f in enumerate(items, 1):
        parsed = parse_filename(f.name)
        if not parsed:
            print(f"[{idx}/{total}] SKIP (no ID pattern): {f.name}")
            results.append({"file": f, "name": f.stem, "tmdb_id": None,
                            "ext": f.suffix.lstrip('.'), "status": "SKIP",
                            "tmdb_name": None, "score": 0.0, "dept": None})
            continue

        name, tmdb_id, ext = parsed
        print(f"[{idx}/{total}] {f.name} ...", end=" ", flush=True)

        data = tmdb_get(f"/person/{tmdb_id}", {}, api_key)
        time.sleep(SLEEP)

        if data is None or "name" not in data:
            print("NOT_FOUND")
            results.append({"file": f, "name": name, "tmdb_id": tmdb_id, "ext": ext,
                            "status": "NOT_FOUND", "tmdb_name": None, "score": 0.0,
                            "dept": None})
            continue

        tmdb_name = data.get("name", "")
        dept      = data.get("known_for_department", "")
        score     = similarity(name, tmdb_name)
        status    = "MATCH" if score >= MATCH_THRESH else "MISMATCH"
        print(f"{status} (tmdb='{tmdb_name}', score={score:.2f}, dept={dept})")

        results.append({"file": f, "name": name, "tmdb_id": tmdb_id, "ext": ext,
                        "status": status, "tmdb_name": tmdb_name, "score": score,
                        "dept": dept})

    # ── Post-process: flag duplicate-ID conflicts ──────────────────────────
    # If two files share the same TMDB ID, at most one can be correct.
    # Keep the higher-scoring match; flag the other as MISMATCH.
    id_to_results = {}
    for r in results:
        if r["tmdb_id"] is None:
            continue
        id_to_results.setdefault(r["tmdb_id"], []).append(r)

    for tid, group in id_to_results.items():
        if len(group) < 2:
            continue
        group.sort(key=lambda r: r["score"], reverse=True)
        winner = group[0]
        for loser in group[1:]:
            if loser["status"] == "MATCH":
                print(f"  [DUP-ID {tid}] Downgrading '{loser['name']}' to MISMATCH "
                      f"(shares ID with '{winner['name']}', score {loser['score']:.2f} < {winner['score']:.2f})")
                loser["status"] = "MISMATCH"

    return results


# ── Step 2: Fix mismatches ────────────────────────────────────────────────────

def fix_mismatches(results, api_key):
    to_fix = [r for r in results if r["status"] in ("MISMATCH", "NOT_FOUND")]
    if not to_fix:
        print("\nNo mismatches to fix.")
        return

    print(f"\n{'='*60}")
    print(f"Fixing {len(to_fix)} mismatche(s)...")
    print('='*60)

    for r in to_fix:
        name    = r["name"]
        ext     = r["ext"]
        f       = r["file"]
        cur_id  = r["tmdb_id"]

        print(f"\n>> {f.name}  (current TMDB: {r['tmdb_name']!r})")

        search = tmdb_get("/search/person", {"query": name, "include_adult": "false"}, api_key)
        time.sleep(SLEEP)

        if not search or not search.get("results"):
            print(f"   ERROR: No TMDB search results for '{name}' — skipping.")
            continue

        # Pick best result by name similarity
        candidates = [(res, similarity(name, res.get("name", "")))
                      for res in search["results"]]
        best_res, best_score = max(candidates, key=lambda x: x[1])

        if best_score < MATCH_THRESH:
            print(f"   WARNING: Best match '{best_res.get('name')}' score={best_score:.2f} "
                  f"< threshold — skipping.")
            continue

        correct_id   = str(best_res.get("id", ""))
        correct_name = best_res.get("name", "")
        profile_path = best_res.get("profile_path")

        print(f"   Found: '{correct_name}' (ID {correct_id}), score={best_score:.2f}")

        # Stage-name / alias check: if search returns the SAME id, image is already correct
        if correct_id == str(cur_id):
            print(f"   SKIP: same TMDB id → image is correct (stage name / alias case).")
            continue

        if not profile_path:
            print(f"   WARNING: No profile image on TMDB for '{correct_name}' — skipping.")
            continue

        img_url  = f"{IMG_BASE}{profile_path}"
        dest     = f.parent / f.name   # overwrite in-place
        print(f"   Downloading: {img_url}")
        if download_image(img_url, dest):
            print(f"   Replaced image for '{name}'")
        else:
            print(f"   ERROR: download failed — skipping Gemini removal.")
            continue

        # Remove stale Gemini toon
        gemini_file = find_gemini_file(name)
        if gemini_file:
            print(f"   Removing stale Gemini toon: {gemini_file.name}")
            gemini_file.unlink()
        else:
            print(f"   No Gemini toon found for '{name}'.")


# ── Step 3: Rename files ──────────────────────────────────────────────────────

def rename_files(directory, label):
    renamed = skipped = errors = 0

    print(f"\n{'='*60}")
    print(f"Renaming: {label}")
    print('='*60)

    for f in sorted(directory.iterdir()):
        if f.name.startswith('.') or f.is_dir():
            continue
        parsed = parse_filename(f.name)
        if not parsed:
            skipped += 1
            continue

        name, _, ext = parsed
        new_name = f"{name}.{ext}"
        new_path = f.parent / new_name

        if new_path == f:
            skipped += 1
            continue

        if new_path.exists():
            print(f"  COLLISION: '{new_name}' already exists — skipping {f.name}")
            errors += 1
            continue

        f.rename(new_path)
        print(f"  {f.name}  →  {new_name}")
        renamed += 1

    print(f"\n  Renamed: {renamed}  |  Skipped/clean: {skipped}  |  Errors: {errors}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    audit_only = "--audit-only" in sys.argv
    api_key    = get_api_key()

    print("="*60)
    print("STEP 1: AUDIT")
    print("="*60)
    results = audit(api_key)

    statuses = {}
    for r in results:
        statuses.setdefault(r["status"], []).append(r)

    print("\n" + "="*60)
    print("AUDIT SUMMARY")
    print("="*60)
    for status, items in statuses.items():
        print(f"  {status}: {len(items)}")

    mismatches = statuses.get("MISMATCH", []) + statuses.get("NOT_FOUND", [])
    if mismatches:
        print("\nMismatches:")
        for r in mismatches:
            print(f"  [{r['status']}] {r['file'].name}")
            print(f"           TMDB: {r['tmdb_name']!r}  score={r['score']:.2f}")

    if audit_only:
        print("\n--audit-only: stopping here. No files modified.")
        return

    print("\n" + "="*60)
    print("STEP 2: FIX MISMATCHES")
    print("="*60)
    fix_mismatches(results, api_key)

    print("\n" + "="*60)
    print("STEP 3: RENAME FILES")
    print("="*60)
    rename_files(PRESINGERS, "presingers/")
    rename_files(GEMINI_DIR, "Singers Gemini/")

    print("\nDone.")


if __name__ == "__main__":
    main()
