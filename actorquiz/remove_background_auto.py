#!/usr/bin/env python3
"""
One-by-one remove-background.com automation using PyAutoGUI.

This script uses the same progress ledger as photoroom_batches.py. It stages one
todo image with a normal extension, uploads it through the browser, waits for a
download, backs up the original, replaces the original image, and marks it done.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
import webbrowser
from dataclasses import dataclass
from pathlib import Path

import pyautogui

import photoroom_batches as tracker


URL = "https://remove-background.com/app/dashboard"
CONFIG_PATH = tracker.ROOT / ".remove_background_auto.json"
WORK_DIR = tracker.ROOT / "remove_background_auto"
STAGED_DIR = WORK_DIR / "staged"
ASSETS_DIR = tracker.ROOT / "remove_background_auto_assets"
UPLOAD_BUTTON_TEMPLATE = ASSETS_DIR / "upload_image_button.png"
DOWNLOAD_BUTTON_TEMPLATE = ASSETS_DIR / "download_button.png"
HD_BUTTON_TEMPLATES = [
    ASSETS_DIR / "hd_button_selected.png",
    ASSETS_DIR / "hd_button_unselected.png",
]
DOWNLOADS_DIR = Path.home() / "Downloads"

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.15


@dataclass(frozen=True)
class AutoResult:
    source_path: str
    downloaded_path: Path
    backup_path: Path
    staged_path: Path


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    return {
        "upload_point": None,
        "upload_button_template": str(UPLOAD_BUTTON_TEMPLATE),
        "download_button_template": str(DOWNLOAD_BUTTON_TEMPLATE),
        "hd_button_templates": [str(path) for path in HD_BUTTON_TEMPLATES],
        "upload_button_confidence": 0.82,
        "download_button_confidence": 0.82,
        "hd_button_confidence": 0.86,
        "upload_button_find_seconds": 20,
        "download_button_find_seconds": 30,
        "hd_button_find_seconds": 10,
        "download_menu_wait_seconds": 0.5,
        "upload_wait_seconds": 20,
        "download_wait_seconds": 90,
        "page_wait_seconds": 3,
    }


def save_config(config: dict) -> None:
    with CONFIG_PATH.open("w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2, sort_keys=True)
        handle.write("\n")


def copy_to_clipboard(text: str) -> None:
    subprocess.run(["pbcopy"], input=text, text=True, check=True)


def open_page() -> None:
    webbrowser.open(URL)
    time.sleep(3)


def prompt_point(label: str) -> dict[str, int]:
    input(f"Move the mouse over the {label}, then press Enter here.")
    point = pyautogui.position()
    print(f"{label}: x={point.x}, y={point.y}")
    return {"x": point.x, "y": point.y}


def calibrate(args: argparse.Namespace) -> None:
    config = load_config()
    print("Opening remove-background.com. Sign in first if the site asks.")
    open_page()
    print("Upload, Download, and HD buttons are found from screenshot templates.")
    print("If upload matching ever fails, you can still save a fallback point now.")
    answer = input("Press Enter to skip fallback upload calibration, or type p to save a point: ").strip().lower()
    if answer == "p":
        config["upload_point"] = prompt_point("Upload image / Choose File button")
    save_config(config)
    print(f"Saved calibration: {CONFIG_PATH}")
    print("Template-based automation is ready.")


def ensure_high_quality_calibration(config: dict) -> dict:
    config.setdefault("hd_button_templates", [str(path) for path in HD_BUTTON_TEMPLATES])
    config.setdefault("hd_button_confidence", 0.86)
    config.setdefault("hd_button_find_seconds", 10)
    return config


def optional_point(config: dict, key: str) -> tuple[int, int] | None:
    point = config.get(key)
    if not point:
        return None
    return int(point["x"]), int(point["y"])


def locate_single_template(
    template: Path,
    confidence: float,
    timeout_seconds: float,
    label: str,
) -> tuple[int, int]:
    if not template.exists():
        raise SystemExit(f"Missing {label} template: {template}")

    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            center = pyautogui.locateCenterOnScreen(str(template), confidence=confidence)
        except pyautogui.ImageNotFoundException:
            center = None
        except Exception as exc:
            raise SystemExit(f"Could not search screen for {label}: {exc}") from exc
        if center is not None:
            return int(center.x), int(center.y)
        time.sleep(0.5)
    raise RuntimeError(f"Could not find {label} on screen from the screenshot template.")


def locate_upload_button(config: dict) -> tuple[int, int]:
    fallback = optional_point(config, "upload_point")
    if fallback is not None:
        print("Using calibrated upload point.")
        return fallback

    template = Path(config.get("upload_button_template") or UPLOAD_BUTTON_TEMPLATE)
    try:
        return locate_single_template(
            template,
            float(config.get("upload_button_confidence", 0.82)),
            float(config.get("upload_button_find_seconds", 20)),
            "Upload image button",
        )
    except RuntimeError:
        raise


def locate_download_button(config: dict) -> tuple[int, int]:
    fallback = optional_point(config, "download_point")
    if fallback is not None:
        print("Using calibrated download point.")
        return fallback

    template = Path(config.get("download_button_template") or DOWNLOAD_BUTTON_TEMPLATE)
    try:
        return locate_single_template(
            template,
            float(config.get("download_button_confidence", 0.82)),
            float(config.get("download_button_find_seconds", 30)),
            "Download button",
        )
    except RuntimeError:
        raise


def locate_hd_button(config: dict) -> tuple[int, int]:
    fallback = optional_point(config, "high_quality_point")
    if fallback is not None:
        print("Using calibrated HD point.")
        return fallback

    template_paths = [Path(path) for path in config.get("hd_button_templates", [])]
    if not template_paths:
        template_paths = HD_BUTTON_TEMPLATES
    for path in template_paths:
        if not path.exists():
            raise SystemExit(f"Missing HD button template: {path}")

    confidence = float(config.get("hd_button_confidence", 0.86))
    deadline = time.time() + float(config.get("hd_button_find_seconds", 10))
    while time.time() < deadline:
        for template in template_paths:
            try:
                center = pyautogui.locateCenterOnScreen(str(template), confidence=confidence)
            except pyautogui.ImageNotFoundException:
                center = None
            except Exception as exc:
                raise SystemExit(f"Could not search screen for HD button: {exc}") from exc
            if center is not None:
                return int(center.x), int(center.y)
        time.sleep(0.25)
    raise RuntimeError("Could not find the HD button on screen from the screenshot templates.")


def next_pending_asset(ledger: dict, assets: list[tracker.Asset]) -> tracker.Asset | None:
    for asset in assets:
        if ledger["items"].get(asset.asset_id, {}).get("status") in {"todo", "batched"}:
            return asset
    return None


def stage_asset(asset: tracker.Asset) -> Path:
    STAGED_DIR.mkdir(parents=True, exist_ok=True)
    staged_path = STAGED_DIR / f"{tracker.safe_part(asset.package)}__{tracker.safe_part(asset.source_folder)}__{tracker.safe_part(asset.display_name)}{asset.extension}"
    shutil.copy2(asset.source_path, staged_path)
    return staged_path


def upload_file(staged_path: Path, config: dict) -> None:
    copy_to_clipboard(str(staged_path))
    upload_point = locate_upload_button(config)
    pyautogui.click(*upload_point)
    time.sleep(0.8)
    pyautogui.hotkey("command", "shift", "g")
    time.sleep(0.3)
    pyautogui.hotkey("command", "v")
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(0.8)
    pyautogui.press("enter")


def candidate_downloads(start_time: float) -> list[Path]:
    candidates = []
    for path in DOWNLOADS_DIR.iterdir():
        if not path.is_file():
            continue
        if path.name.startswith(".") or path.suffix in {".crdownload", ".download", ".part"}:
            continue
        try:
            if path.stat().st_mtime >= start_time and tracker.image_extension(path) is not None:
                candidates.append(path)
        except OSError:
            continue
    return sorted(candidates, key=lambda path: path.stat().st_mtime, reverse=True)


def stable_file(path: Path, checks: int = 3, delay: float = 0.5) -> bool:
    last_size = -1
    for _ in range(checks):
        try:
            size = path.stat().st_size
        except OSError:
            return False
        if size == 0 or size != last_size:
            last_size = size
            time.sleep(delay)
            continue
        return True
    return False


def wait_for_download(start_time: float, timeout: int) -> Path | None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        for path in candidate_downloads(start_time):
            if stable_file(path):
                return path
        time.sleep(1)
    return None


def replace_source(ledger: dict, asset: tracker.Asset, downloaded_path: Path, staged_path: Path) -> AutoResult:
    batch_id = "remove_background_auto"
    source_relative = Path(asset.asset_id)
    source_file = tracker.ROOT / source_relative
    backup_path = tracker.unique_backup_path(batch_id, source_relative)
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_file, backup_path)

    shutil.copy2(downloaded_path, source_file)

    processed_path = tracker.PROCESSED_DIR / source_relative.with_suffix(".png")
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(downloaded_path, processed_path)

    item = ledger["items"][asset.asset_id]
    item["status"] = "done"
    item["batch"] = batch_id
    item["completed_at"] = tracker.now()
    item["processed_path"] = tracker.rel(processed_path)
    item["backup_path"] = tracker.rel(backup_path)
    item["replacement_format"] = tracker.image_extension(downloaded_path) or downloaded_path.suffix.lower() or "unknown"
    item["replaced_source_at"] = tracker.now()
    item["automation"] = "remove-background.com"

    tracker.save_ledger(ledger)
    tracker.write_csv(ledger)
    return AutoResult(asset.asset_id, downloaded_path, backup_path, staged_path)


def process_one(ledger: dict, assets: list[tracker.Asset], config: dict, args: argparse.Namespace) -> AutoResult | None:
    asset = next_pending_asset(ledger, assets)
    if asset is None:
        return None

    staged_path = stage_asset(asset)

    print("")
    print(f"Next: {asset.asset_id}")
    print(f"Staged upload: {staged_path}")
    if args.prompt_each:
        answer = input("Press Enter to process this image, or q to quit: ").strip().lower()
        if answer in {"q", "quit", "exit"}:
            raise KeyboardInterrupt

    open_page()
    time.sleep(float(config.get("page_wait_seconds", 3)))
    upload_file(staged_path, config)
    print(f"Uploaded. Waiting {config.get('upload_wait_seconds', 20)} seconds for processing.")
    time.sleep(float(config.get("upload_wait_seconds", 20)))

    start_time = time.time()
    download_point = locate_download_button(config)
    pyautogui.click(*download_point)
    time.sleep(float(config.get("download_menu_wait_seconds", 0.5)))
    pyautogui.click(*locate_hd_button(config))
    print("Clicked download > HD. Waiting for a new file in Downloads...")
    downloaded_path = wait_for_download(start_time, int(config.get("download_wait_seconds", 90)))
    if downloaded_path is None:
        print("No new download detected.")
        print("If the page needs a manual click/login/subscription step, handle it, then press Enter to retry download.")
        input("> ")
        start_time = time.time()
        download_point = locate_download_button(config)
        pyautogui.click(*download_point)
        time.sleep(float(config.get("download_menu_wait_seconds", 0.5)))
        pyautogui.click(*locate_hd_button(config))
        downloaded_path = wait_for_download(start_time, int(config.get("download_wait_seconds", 90)))
    if downloaded_path is None:
        raise RuntimeError("Download did not appear. Leaving this image as todo.")

    return replace_source(ledger, asset, downloaded_path, staged_path)


def run(args: argparse.Namespace) -> None:
    config = load_config()
    ledger = tracker.load_ledger()
    assets = tracker.discover_assets()
    tracker.sync_ledger(ledger, assets)
    tracker.save_ledger(ledger)
    tracker.write_csv(ledger)

    config.setdefault("upload_button_template", str(UPLOAD_BUTTON_TEMPLATE))
    config.setdefault("upload_button_confidence", 0.82)
    config.setdefault("upload_button_find_seconds", 20)
    config = ensure_high_quality_calibration(config)

    completed = 0
    try:
        while args.limit is None or completed < args.limit:
            result = process_one(ledger, assets, config, args)
            if result is None:
                print("No todo images left.")
                return
            completed += 1
            print(f"Replaced: {result.source_path}")
            print(f"Backup:   {result.backup_path}")
            if args.keep_downloads is False:
                try:
                    result.downloaded_path.unlink()
                except OSError:
                    pass
    except KeyboardInterrupt:
        print("\nStopped. Progress is saved.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(required=True)

    calibrate_parser = subparsers.add_parser("calibrate", help="Capture a fallback upload button position.")
    calibrate_parser.set_defaults(func=calibrate)

    run_parser = subparsers.add_parser("run", help="Process todo images one by one.")
    run_parser.add_argument("--limit", type=int, help="Stop after this many images.")
    run_parser.add_argument("--prompt-each", action="store_true", help="Ask before each image.")
    run_parser.add_argument("--keep-downloads", action=argparse.BooleanOptionalAction, default=False)
    run_parser.set_defaults(func=run)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
