#!/usr/bin/env python3
"""
Prepare and track PhotoRoom background-removal batches for people/SNL images.

The script never edits source images while preparing a batch. Completion means
the PhotoRoom output is ready and replaces the original source image after a
backup copy is saved.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LEDGER_PATH = ROOT / ".photoroom_progress.json"
CSV_PATH = ROOT / "photoroom_progress.csv"
BATCHES_DIR = ROOT / "photoroom_batches"
PROCESSED_DIR = ROOT / "photoroom_processed"
BACKUPS_DIR = ROOT / "photoroom_original_backups"

IMAGE_EXT_BY_MAGIC = (
    (b"\xff\xd8\xff", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"RIFF", ".webp"),
)

EXCLUDED_PACKAGE_DIRS = {
    "actors-actors",  # Hollywood actors.
    "actors-mashup",
}

EXCLUDED_SOURCE_PARTS = {
    ".comparator_trash",
    "comparator trash",
    "comparator_trash",
    "deleted",
    "_deleted",
    "too old",
    "too young",
    "too white",
    "too black",
    "too asian",
    "missing as from",
    "proced",
}


@dataclass(frozen=True)
class Asset:
    asset_id: str
    source_path: Path
    package: str
    source_folder: str
    display_name: str
    extension: str


@dataclass(frozen=True)
class CompletionResult:
    batch_id: str
    replaced: int
    already_done: int
    missing: list[str]
    status: str


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def safe_part(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "item"


def image_extension(path: Path) -> str | None:
    try:
        with path.open("rb") as handle:
            header = handle.read(16)
    except OSError:
        return None

    for magic, extension in IMAGE_EXT_BY_MAGIC:
        if header.startswith(magic):
            if extension == ".webp" and header[8:12] != b"WEBP":
                continue
            return extension
    return None


def is_excluded_dir(path: Path) -> bool:
    return any(part.lower() in EXCLUDED_SOURCE_PARTS for part in path.parts)


def package_dirs() -> list[Path]:
    dirs = []
    for path in sorted(ROOT.glob("actors-*")) + [ROOT / "snl"]:
        if not path.is_dir():
            continue
        if path.name in EXCLUDED_PACKAGE_DIRS:
            continue
        dirs.append(path)
    return dirs


def discover_assets() -> list[Asset]:
    assets = []
    for package_dir in package_dirs():
        for path in sorted(package_dir.rglob("*")):
            if not path.is_file() or path.name.startswith("."):
                continue
            relative_parent = path.parent.relative_to(package_dir)
            if is_excluded_dir(relative_parent):
                continue
            extension = image_extension(path)
            if extension is None:
                continue
            source_folder = relative_parent.as_posix()
            asset_id = rel(path)
            assets.append(
                Asset(
                    asset_id=asset_id,
                    source_path=path,
                    package=package_dir.name,
                    source_folder=source_folder,
                    display_name=path.name,
                    extension=extension,
                )
            )
    return assets


def load_ledger() -> dict:
    if not LEDGER_PATH.exists():
        return {"items": {}, "batches": {}}
    with LEDGER_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_ledger(ledger: dict) -> None:
    with LEDGER_PATH.open("w", encoding="utf-8") as handle:
        json.dump(ledger, handle, indent=2, sort_keys=True)
        handle.write("\n")


def sync_ledger(ledger: dict, assets: list[Asset]) -> None:
    items = ledger.setdefault("items", {})
    seen = {asset.asset_id for asset in assets}
    for asset in assets:
        items.setdefault(
            asset.asset_id,
            {
                "status": "todo",
                "package": asset.package,
                "source_folder": asset.source_folder,
                "display_name": asset.display_name,
                "source_path": asset.asset_id,
            },
        )
    for asset_id, item in items.items():
        if asset_id not in seen and item.get("status") != "missing":
            item["status"] = "missing"
            item["missing_at"] = now()


def write_csv(ledger: dict) -> None:
    rows = []
    for asset_id, item in sorted(ledger.get("items", {}).items()):
        rows.append(
            {
                "status": item.get("status", ""),
                "package": item.get("package", ""),
                "source_folder": item.get("source_folder", ""),
                "display_name": item.get("display_name", ""),
                "batch": item.get("batch", ""),
                "source_path": asset_id,
                "processed_path": item.get("processed_path", ""),
                "backup_path": item.get("backup_path", ""),
                "replacement_format": item.get("replacement_format", ""),
            }
        )

    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "status",
                "package",
                "source_folder",
                "display_name",
                "batch",
                "source_path",
                "processed_path",
                "backup_path",
                "replacement_format",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def status(args: argparse.Namespace) -> None:
    ledger = load_ledger()
    assets = discover_assets()
    sync_ledger(ledger, assets)
    save_ledger(ledger)
    write_csv(ledger)

    counts: dict[str, int] = {}
    by_package: dict[str, dict[str, int]] = {}
    for item in ledger["items"].values():
        item_status = item.get("status", "todo")
        counts[item_status] = counts.get(item_status, 0) + 1
        package = item.get("package", "unknown")
        by_package.setdefault(package, {})
        by_package[package][item_status] = by_package[package].get(item_status, 0) + 1

    print("Overall")
    for key in sorted(counts):
        print(f"  {key}: {counts[key]}")
    print(f"\nCSV: {CSV_PATH}")

    if args.by_package:
        print("\nBy package")
        for package in sorted(by_package):
            parts = ", ".join(f"{k}: {v}" for k, v in sorted(by_package[package].items()))
            print(f"  {package}: {parts}")


def next_batch_id(ledger: dict) -> str:
    batches = ledger.setdefault("batches", {})
    number = 1
    while f"batch_{number:04d}" in batches:
        number += 1
    return f"batch_{number:04d}"


def make_batch_name(batch_index: int, asset: Asset) -> str:
    return (
        f"{batch_index:04d}__{safe_part(asset.package)}__"
        f"{safe_part(asset.source_folder)}__{safe_part(asset.display_name)}{asset.extension}"
    )


def create_next_batch(ledger: dict, assets: list[Asset], size: int, batch_id: str | None = None) -> str | None:
    item_by_id = ledger["items"]
    selected = [
        asset
        for asset in assets
        if item_by_id.get(asset.asset_id, {}).get("status") == "todo"
    ][:size]

    if not selected:
        save_ledger(ledger)
        write_csv(ledger)
        return None

    batch_id = batch_id or next_batch_id(ledger)
    batch_dir = BATCHES_DIR / batch_id
    input_dir = batch_dir / "input"
    output_dir = batch_dir / "output"
    if batch_dir.exists() and any(batch_dir.iterdir()):
        raise SystemExit(f"Batch directory already exists and is not empty: {batch_dir}")
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = []
    for index, asset in enumerate(selected, start=1):
        batch_name = make_batch_name(index, asset)
        destination = input_dir / batch_name
        shutil.copy2(asset.source_path, destination)
        item = item_by_id[asset.asset_id]
        item["status"] = "batched"
        item["batch"] = batch_id
        item["batch_file"] = batch_name
        item["batched_at"] = now()
        manifest.append(
            {
                "batch_file": batch_name,
                "source_path": asset.asset_id,
                "package": asset.package,
                "source_folder": asset.source_folder,
                "display_name": asset.display_name,
            }
        )

    ledger["batches"][batch_id] = {
        "created_at": now(),
        "size": len(selected),
        "input_dir": rel(input_dir),
        "output_dir": rel(output_dir),
        "status": "open",
    }
    with (batch_dir / "manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")

    save_ledger(ledger)
    write_csv(ledger)
    return batch_id


def create_batch(args: argparse.Namespace) -> None:
    ledger = load_ledger()
    assets = discover_assets()
    sync_ledger(ledger, assets)
    batch_id = create_next_batch(ledger, assets, args.size, args.batch_id)

    if batch_id is None:
        print("No todo images left.")
        return

    batch = ledger["batches"][batch_id]
    input_dir = ROOT / batch["input_dir"]
    output_dir = ROOT / batch["output_dir"]
    print(f"Created {batch_id} with {batch['size']} images.")
    print(f"Upload/select everything in: {input_dir}")
    print(f"Put PhotoRoom downloads in: {output_dir}")


def output_candidates(output_dir: Path) -> dict[str, Path]:
    candidates: dict[str, Path] = {}
    for path in output_dir.rglob("*"):
        if path.is_file() and not path.name.startswith("."):
            candidates[path.stem] = path
    return candidates


def unique_backup_path(batch_id: str, source_relative: Path) -> Path:
    backup_path = BACKUPS_DIR / batch_id / source_relative
    if not backup_path.exists():
        return backup_path

    counter = 2
    while True:
        candidate = backup_path.with_name(f"{backup_path.name}.backup{counter}")
        if not candidate.exists():
            return candidate
        counter += 1


def complete_batch_in_ledger(ledger: dict, batch_id: str, outputs: str | None = None) -> CompletionResult:
    batch = ledger.get("batches", {}).get(batch_id)
    if not batch:
        raise SystemExit(f"Unknown batch: {batch_id}")

    batch_dir = BATCHES_DIR / batch_id
    manifest_path = batch_dir / "manifest.json"
    output_dir = Path(outputs) if outputs else ROOT / batch["output_dir"]
    if not output_dir.exists():
        raise SystemExit(f"Output directory does not exist: {output_dir}")

    with manifest_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    candidates = output_candidates(output_dir)
    done = 0
    already_done = 0
    missing = []
    for entry in manifest:
        batch_file = entry["batch_file"]
        source_path = entry["source_path"]
        item = ledger["items"][source_path]
        if item.get("status") == "done":
            already_done += 1
            continue

        output = candidates.get(Path(batch_file).stem)
        if output is None:
            missing.append(batch_file)
            continue

        source_relative = Path(entry["source_path"])
        source_file = ROOT / source_relative
        if not source_file.exists():
            missing.append(f"{batch_file} (source missing: {source_relative})")
            continue

        replacement_format = image_extension(output) or output.suffix.lower() or "unknown"
        backup_path = unique_backup_path(batch_id, source_relative)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, backup_path)

        # Keep the original path/name stable for the app, even when it has no extension.
        shutil.copy2(output, source_file)

        processed_relative = source_relative.with_suffix(".png")
        processed_path = PROCESSED_DIR / processed_relative
        processed_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(output, processed_path)

        item["status"] = "done"
        item["completed_at"] = now()
        item["processed_path"] = rel(processed_path)
        item["backup_path"] = rel(backup_path)
        item["replacement_format"] = replacement_format
        item["replaced_source_at"] = now()
        done += 1

    remaining_batched = sum(
        1
        for item in ledger.get("items", {}).values()
        if item.get("batch") == batch_id and item.get("status") == "batched"
    )
    completed_total = sum(
        1
        for item in ledger.get("items", {}).values()
        if item.get("batch") == batch_id and item.get("status") == "done"
    )
    batch["completed_count"] = completed_total
    batch["missing_count"] = len(missing)
    batch["status"] = "done" if remaining_batched == 0 else "partial"
    batch["completed_at"] = now()

    save_ledger(ledger)
    write_csv(ledger)
    return CompletionResult(
        batch_id=batch_id,
        replaced=done,
        already_done=already_done,
        missing=missing,
        status=batch["status"],
    )


def print_completion_result(result: CompletionResult) -> None:
    print(f"Replaced {result.replaced} source images for {result.batch_id}.")
    if result.already_done:
        print(f"Already done in this batch: {result.already_done}")
    print(f"Original backups: {BACKUPS_DIR / result.batch_id}")
    print(f"Processed copies: {PROCESSED_DIR}")
    if result.missing:
        print(f"Missing {len(result.missing)} outputs. First 20:")
        for name in result.missing[:20]:
            print(f"  {name}")


def complete_batch(args: argparse.Namespace) -> None:
    ledger = load_ledger()
    result = complete_batch_in_ledger(ledger, args.batch_id, args.outputs)
    print_completion_result(result)


def active_batch_id(ledger: dict) -> str | None:
    for batch_id, batch in sorted(ledger.get("batches", {}).items()):
        if batch.get("status") not in {"open", "partial"}:
            continue
        has_batched_items = any(
            item.get("batch") == batch_id and item.get("status") == "batched"
            for item in ledger.get("items", {}).values()
        )
        if has_batched_items:
            return batch_id
    return None


def print_batch_instructions(ledger: dict, batch_id: str) -> None:
    batch = ledger["batches"][batch_id]
    remaining = sum(
        1
        for item in ledger.get("items", {}).values()
        if item.get("batch") == batch_id and item.get("status") == "batched"
    )
    done = sum(
        1
        for item in ledger.get("items", {}).values()
        if item.get("batch") == batch_id and item.get("status") == "done"
    )
    print("")
    print(f"Current batch: {batch_id}")
    print(f"Remaining in this batch: {remaining}  Done: {done}")
    print(f"PhotoRoom input:  {ROOT / batch['input_dir']}")
    print(f"PhotoRoom output: {ROOT / batch['output_dir']}")
    print("After the processed files are in output, press Enter.")
    print("Type s for status, r to reprint these folders, or q to quit.")


def print_short_status(ledger: dict) -> None:
    counts: dict[str, int] = {}
    for item in ledger.get("items", {}).values():
        item_status = item.get("status", "todo")
        counts[item_status] = counts.get(item_status, 0) + 1
    parts = ", ".join(f"{key}: {counts[key]}" for key in sorted(counts))
    print(f"Progress: {parts}")


def run_session(args: argparse.Namespace) -> None:
    ledger = load_ledger()
    assets = discover_assets()
    sync_ledger(ledger, assets)
    save_ledger(ledger)
    write_csv(ledger)

    try:
        while True:
            batch_id = active_batch_id(ledger)
            if batch_id is None:
                batch_id = create_next_batch(ledger, assets, args.size)
                if batch_id is None:
                    print("No todo images left.")
                    return
                print(f"Created {batch_id} with {ledger['batches'][batch_id]['size']} images.")
            else:
                print(f"Resuming {batch_id}.")

            print_batch_instructions(ledger, batch_id)
            while True:
                command = input("> ").strip().lower()
                if command in {"q", "quit", "exit"}:
                    print("Stopped. The current batch is saved and will resume next time.")
                    return
                if command in {"s", "status"}:
                    print_short_status(ledger)
                    continue
                if command in {"r", "repeat", "folders"}:
                    print_batch_instructions(ledger, batch_id)
                    continue
                if command == "":
                    result = complete_batch_in_ledger(ledger, batch_id)
                    print_completion_result(result)
                    if result.status == "done":
                        break
                    print("Still waiting on missing outputs for this same batch.")
                    print_batch_instructions(ledger, batch_id)
                    continue
                print("Press Enter to complete, s for status, r for folders, or q to quit.")
    except KeyboardInterrupt:
        print("\nStopped. The current batch is saved and will resume next time.")


def reset_batch(args: argparse.Namespace) -> None:
    ledger = load_ledger()
    batch = ledger.get("batches", {}).get(args.batch_id)
    if not batch:
        raise SystemExit(f"Unknown batch: {args.batch_id}")

    reset = 0
    for item in ledger.get("items", {}).values():
        if item.get("batch") == args.batch_id and item.get("status") == "batched":
            item["status"] = "todo"
            item.pop("batch", None)
            item.pop("batch_file", None)
            reset += 1
    batch["status"] = "reset"
    batch["reset_at"] = now()
    save_ledger(ledger)
    write_csv(ledger)
    print(f"Reset {reset} still-batched images back to todo.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(required=True)

    status_parser = subparsers.add_parser("status", help="Refresh and print progress.")
    status_parser.add_argument("--by-package", action="store_true")
    status_parser.set_defaults(func=status)

    next_parser = subparsers.add_parser("next", help="Create the next upload batch.")
    next_parser.add_argument("--size", type=int, default=500)
    next_parser.add_argument("--batch-id")
    next_parser.set_defaults(func=create_batch)

    run_parser = subparsers.add_parser(
        "run", help="Continuously create, wait for, and complete PhotoRoom batches."
    )
    run_parser.add_argument("--size", type=int, default=50)
    run_parser.set_defaults(func=run_session)

    complete_parser = subparsers.add_parser(
        "complete", help="Replace source images from downloaded PhotoRoom files."
    )
    complete_parser.add_argument("batch_id")
    complete_parser.add_argument("--outputs", help="PhotoRoom output folder. Defaults to batch output dir.")
    complete_parser.set_defaults(func=complete_batch)

    reset_parser = subparsers.add_parser("reset-batch", help="Return an open batch to todo.")
    reset_parser.add_argument("batch_id")
    reset_parser.set_defaults(func=reset_batch)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
