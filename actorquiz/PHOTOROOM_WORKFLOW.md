# PhotoRoom Batch Workflow

This workflow is for bulk background removal on people packages plus SNL, excluding
`actors-actors` / Hollywood actors.

## One-By-One Browser Automation

If bulk processing is limited, use the remove-background.com one-by-one helper:

```sh
python3 -B actorquiz/remove_background_auto.py run
```

The upload, download, and HD buttons are found from screenshot templates:

```text
actorquiz/remove_background_auto_assets/upload_image_button.png
actorquiz/remove_background_auto_assets/download_button.png
actorquiz/remove_background_auto_assets/hd_button_selected.png
actorquiz/remove_background_auto_assets/hd_button_unselected.png
```

If template matching ever fails, save fallback click points:

```sh
python3 -B actorquiz/remove_background_auto.py calibrate
```

The script will:

- Pick the next pending image from the same progress ledger (`todo` or `batched`).
- Stage it with a normal `.jpg`, `.png`, or `.webp` extension for upload.
- Find the upload button on screen and upload through the browser using PyAutoGUI.
- Find the download button on screen, click it, then find and click the HD option.
- Watch `~/Downloads` for the processed image.
- Back up the original source image.
- Replace the original source image.
- Mark the item `done`.

Avoid starting unrelated downloads while it is running; it watches `~/Downloads`
for the newest image file after clicking the download button.

Useful options:

```sh
python3 -B actorquiz/remove_background_auto.py run --limit 10
python3 -B actorquiz/remove_background_auto.py run --prompt-each
python3 -B actorquiz/remove_background_auto.py run --keep-downloads
```

## Check Progress

```sh
python3 -B actorquiz/photoroom_batches.py status --by-package
```

This refreshes:

- `actorquiz/.photoroom_progress.json`
- `actorquiz/photoroom_progress.csv`

## Create A Batch

```sh
python3 -B actorquiz/photoroom_batches.py next --size 500
```

The script creates:

```text
actorquiz/photoroom_batches/batch_0001/input
actorquiz/photoroom_batches/batch_0001/output
```

Upload or select all files from the `input` folder in PhotoRoom. The copied files
have normal `.jpg`, `.png`, or `.webp` extensions even when the originals are
extensionless.

## Automatic Session Mode

For the easier loop, run:

```sh
python3 -B actorquiz/photoroom_batches.py run
```

This defaults to 250 images per batch. To choose another size:

```sh
python3 -B actorquiz/photoroom_batches.py run --size 100
```

The script will:

- Resume the current unfinished batch, or create the next one.
- Show the PhotoRoom `input` and `output` folders.
- Wait while you upload/process/download in PhotoRoom.
- Replace originals when you press Enter.
- Move on to the next batch.

At the prompt:

- Press Enter after PhotoRoom outputs are in the `output` folder.
- Type `i` to open the current input folder.
- Type `o` to open the current output folder.
- Type `ci` to copy the current input folder path.
- Type `co` to copy the current output folder path.
- Type `s` for progress.
- Type `r` to reprint the current folders.
- Type `q` or press Ctrl-C to stop.

Stopping is safe. The current batch stays marked as `batched`, and the next
`run` resumes from that same batch.

## Finish A Batch

Put PhotoRoom's downloaded results into the batch `output` folder, then run:

```sh
python3 -B actorquiz/photoroom_batches.py complete batch_0001
```

This means the PhotoRoom outputs are approved and ready. The command replaces the
original source image files in place, while preserving the original filenames and
paths used by the app.

Before each replacement, the original is backed up to:

```text
actorquiz/photoroom_original_backups/
```

A second copy of each processed image is also written to:

```text
actorquiz/photoroom_processed/
```

The progress CSV and JSON are updated automatically.

## If A Batch Was Made By Mistake

```sh
python3 -B actorquiz/photoroom_batches.py reset-batch batch_0001
```

Only images still marked as `batched` are returned to `todo`; completed images stay
done.
