# BCX ClipTranslate: how to evaluate the prototype

This is a **prototype for evaluation**, not a finished product. Read "What is real and what is not" first, so you judge it fairly.

## 1. Look first (2 minutes, nothing to install)

| What | File |
|---|---|
| The app window (demo mode) | `docs/prototype-demo.png` |
| A sample exported video with burned-in English subtitles | `docs/samples/bcx-sample-subtitled.mp4` |
| Frames from that video | `docs/samples/frame-5s.png`, `docs/samples/frame-15s.png` |
| The matching editable subtitle file | `docs/samples/bcx-sample.srt` |

The sample uses a synthetic test-pattern video and **invented** captions. It shows the editor and the export (subtitle size, position, wrapping), not translation quality.

## 2. Try the editor yourself (10 minutes, no model download)

Follow `QUICKSTART.md`, then run `python -m cliptranslate --demo`. In the window:

1. Click a row, then change its text.
2. Change a start or end time (try an invalid one; it should refuse and tell you why).
3. Use Split line, Merge next, Add line and Delete.
4. Save draft, close the app, reopen it and click Open draft.
5. Click Save .srt, then Export subtitled MP4, and play the result.

## 3. Test the real thing (30-60 minutes, needs a rights-owned French clip)

Run without `--demo`, pick a clip of 1-3 minutes that you own, tick the permission box and click Generate. The first run downloads the speech model (several hundred MB). Then fill in the report in `QUICKSTART.md`.

## 4. Score it

Give each line a mark from 1 (bad) to 5 (very good). Be harsh; a kind score hides problems.

| Question | Score | Notes |
|---|---|---|
| Install: could you get it running without help? | | |
| Editor: easy to fix a wrong line? | | |
| Translation: would you post the English as it is? | | |
| Timing: do subtitles appear when the words are spoken? | | |
| Export: does the MP4 look good on your phone? | | |
| Speed: is the wait acceptable for a 2-minute clip? | | |
| Overall: would a creator pay for the finished result? | | |

Also write down: your operating system, RAM, clip length, time taken, and any error message plus the log file (Open log folder button).

## What is real and what is not

**Real and tested here (47 automated tests):** loading a video, safety checks, the editor, draft saving, SRT writing, burning subtitles into an MP4 on 16:9 and vertical clips, the pilot report.

**Not verified yet:**

- Translation quality of the real speech model on real French (the model could not be downloaded in the build environment).
- Video playback inside the window (no playback backend in the build environment).
- Windows and macOS behaviour (CI is set up but has never run on GitHub).
- African-accent French, noisy audio and slang.
- Whether anyone will pay. That is what the ten-creator pilot in `PILOT.md` is for.
