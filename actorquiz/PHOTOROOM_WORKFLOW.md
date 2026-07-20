# PhotoRoom Batch Workflow

This workflow is for bulk background removal on people packages plus SNL, excluding
`actors-actors` / Hollywood actors.

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

This defaults to 50 images per batch. To choose another size:

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
