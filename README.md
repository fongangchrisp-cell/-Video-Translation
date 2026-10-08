# ClipTranslate — short-video subtitle pilot

A **local desktop MVP** for creators translating **their own short French-language videos into English subtitles**. Select a clip, generate timed English captions, correct the text and timing, preview alongside the video, and export both a UTF-8 `.srt` and an MP4 with burned-in captions.

This is a focused ten-creator validation experiment, **not** a service for arbitrary movies or languages. It has no dubbing, voice cloning, lip-sync, accounts, uploads, billing, or promise of professional-grade translation. Human review is required before sharing.

> **Just want to try it?** Follow [QUICKSTART.md](QUICKSTART.md) (VS Code, with a demo mode that needs no model download).

## Install and run

Requirements: Python **3.10–3.12**, a Windows/macOS/Linux **desktop with a graphical display**, adequate memory/disk for a speech model, and internet access **once** to download the model. In particular, minimal headless Linux containers may lack Qt's `libGL`/display libraries; run the GUI on a normal desktop. A CPU is sufficient but processing can take several minutes.

```bash
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
python -m pip install -e .
python -m cliptranslate
# or: cliptranslate
```

`imageio-ffmpeg` supplies FFmpeg with the app; there is no API key or paid AI service. On the first run, [faster-whisper](https://github.com/SYSTRAN/faster-whisper) downloads a multilingual Whisper model to the **user's cache directory**. **Small** is selected by default for quality; **base** starts faster and uses less space. Neither guarantees accurate captions. After the download, translation runs locally. The model is instructed to translate **French speech directly into English text**; it cannot handle every language, accent or noisy soundtrack reliably. The original video/audio are not sent to an AI API.

## Creator workflow

1. Select an **MP4, MOV or MKV of at most 2 minutes and 500 MiB** with French dialogue in its **first audio track**. Use only videos you have permission to process and share.
2. Confirm the rights checkbox and select **base** or **small**. Click **Generate English subtitles**. The first run needs internet to download model weights.
3. Play the original clip in the right-hand pane. The corresponding English line appears underneath it (the preview **does not burn it onto the video**). Correct the English text and start/end timestamps on the left; add missed dialogue, split, merge or delete lines as needed. Long or fast-to-read lines are highlighted in amber. When **Also transcribe the French** is ticked (the default; it roughly doubles processing time), the **French that was heard** appears under the editor for the selected line, so a reviewer can catch mistranslations. Long speech segments are split automatically into readable lines.
4. **Cancel job** stops a running translation or export without changing anything you already have. Closing the window with unsaved edits asks whether to save a draft.
5. Save a **draft** (`.cliptranslate.json`) if you want to continue editing later. The draft references the original video file; if you moved it, the app asks you to find it and checks it is the same video (by content, not just size). Reopening requires confirming your rights again.
6. Save an editable **`.srt`**, or **Export subtitled MP4**, which also writes a matching `.srt` next to the MP4. Export re-encodes the video to H.264 and the **first** audio track to AAC. Caption size, position and line length adapt to landscape and vertical (9:16) video. The original input is never overwritten.

The UI shows elapsed processing time so you can log it for the pilot. Keep video files, model weights, exported clips and drafts out of Git. There is **no automatic analytics or cloud storage**; measure customer satisfaction and costs using [PILOT.md](PILOT.md) and `python -m cliptranslate.pilot_report`. A local log file (timings, file names and error details, **never subtitle text**) is written to your OS log folder (`CLIPTRANSLATE_LOG_DIR` to change it); **Open log folder** in the app shows it. Send it to the team if something fails.

## Limitations and troubleshooting

- Translation is generated directly from speech by Whisper (`language="fr", task="translate"`), not by a separate text-translation engine. Music, multiple speakers, fast dialogue and specialized vocabulary can produce errors. Always review captions and timing.
- If your system cannot play the preview, **Open original in video player** uses your default player; SRT/export can still work. If export says FFmpeg lacks `subtitles/libass`, save the `.srt` or install a full FFmpeg build and set `CLIPTRANSLATE_FFMPEG` to its executable path.
- If a model download fails, check internet connectivity, free disk space and whether your network can access the model host. Downloads are stored in your OS cache (or `CLIPTRANSLATE_CACHE_DIR` if set). The first download might be large; the app does **not** download or bundle weights into this repository.
- This pilot supports **one video at a time**, one language direction and short clips only. It does not isolate speech from music/effects, identify speakers, or guarantee subtitles will be accurate or readable without edits. No voice or likeness cloning is performed.
- Before a commercial launch, verify the licenses/terms of every dependency and model, and secure rights to your customers' source content. The rights checkbox is not a substitute for legal permission.

## Project structure

- `src/cliptranslate/pipeline.py` — local speech translation; model downloads stay in the user cache.
- `src/cliptranslate/media.py` and `core.py` — FFmpeg processing and subtitle rules.
- `src/cliptranslate/gui.py` — desktop editor, review and export workflow.
- `src/cliptranslate/project.py` — reopenable local drafts.
- `src/cliptranslate/diagnostics.py` — local log file. `pilot_report.py` — scorecard arithmetic.
- `tests/` — core, media, headless GUI and report checks using synthetic video, without copyrighted samples. `.github/workflows/ci.yml` runs them on Linux, Windows and macOS.

## Develop and test

```bash
python -m pip install -e '.[dev]'
ruff check src tests && ruff format --check src tests
python -m pytest -q
```

The automated tests exercise timestamp/SRT rules, caption splitting, project persistence, the FFmpeg audio/export path (they check that burned-in captions really appear, in landscape and vertical video), cancellation, a headless GUI smoke test and the scorecard report. The transcription pipeline runs against a fake model; they do not download model weights. **Actual AI quality and video playback in the window have still never been verified**; check them on a desktop with the model installed. GUI tests skip themselves where Qt's system libraries are missing.

See [PILOT.md](PILOT.md) for the ten-creator validation plan and [TEAM_PLAN.md](TEAM_PLAN.md) for suggested group roles and working agreements, and [WORKPLAN.md](WORKPLAN.md) for the 8-person schedule, [AUDIT.md](AUDIT.md) for known risks, and [LEGAL_CHECKLIST.md](LEGAL_CHECKLIST.md) before taking any payment.
