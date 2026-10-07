# Brutal audit — ClipTranslate pilot (most to least important)

## Status after the fix pass (2026-10-07)

| # | Finding | Status |
| --- | --- | --- |
| 1 | Never run for real | **Partly fixed.** The window now builds and is smoke-tested headlessly; burned-in captions are verified to be drawn (landscape and vertical). **Still unverified:** the real speech model on real French audio, and video playback inside the window. Needs a real desktop. |
| 2 | No French text to check against | **Fixed in code.** French is transcribed and shown beside each English line (optional, default on). **Not yet measured:** whether `small` is good enough; compare models on real clips. |
| 3 | Creators can't install it | **Not fixed, by design.** Run it for creators (concierge) during the pilot; see `PILOT.md`. |
| 4 | Economics / competitors | **Researched and documented** in `PILOT.md`: free and ~$12–20/month alternatives exist, so only a human-checked, done-for-you result is sellable. Scorecard now has a report tool that does the arithmetic. |
| 5 | Licensing and consent | **Documented, not resolved.** `LEGAL_CHECKLIST.md` lists what to check. A qualified person must review it. |
| 6 | Long captions, rough timing | **Fixed for length** (auto-split into readable cues). Timing is still segment-level. |
| 7 | Burned-in style | **Fixed** for size, position and wrap on landscape and 9:16. Rotated phone clips are handled. Font choice is still the system default. Windows/macOS FFmpeg builds are untested (CI will show). |
| 8 | Cancel, unsaved prompt, progress, logs | **Fixed:** cancel button, unsaved-changes prompt, indeterminate bar for model loading, rotating local log file. No real download percentage. |
| 9 | Fragile drafts | **Fixed:** content fingerprint, and the app asks you to locate a moved video. |
| 10 | Nothing committed | **Fixed** by committing to the working branch. |
| 11 | Structure and tests | **Partly fixed:** 40 tests, headless GUI smoke tests, Ruff configured, GitHub Actions on Linux/Windows/macOS. `gui.py` is still one large file. No dependency lock file. |
| 12 | Docs overlap | **Partly fixed:** README/PILOT updated. Still several files. |
| 13 | Hyphenated repo name | **Not fixed**; rename the GitHub repository yourself if you want. |

The original audit follows, unchanged, for the record.

---

Audited on 2026-10-07 from the repository itself. I re-ran the checks: **18 tests pass, Ruff passes**. That tells you less than it sounds: the tests prove the plumbing works, not that the product works.

**Verdict:** this is a tidy, honest prototype. It is **not** evidence that the business works, and it has **never been run on real French speech or on a real desktop**. The biggest risks are the translation quality, how creators will get the app, and the economics. They are not code style.

---

## P0 — Could invalidate the whole pilot

### 1. The core promise has never been tested
- The speech model never ran here (no model download). The GUI never launched (no desktop libraries).
- `tests/test_pipeline.py` uses a **fake model**. The FFmpeg tests use a blue frame and a sine tone, and they don't check that subtitle text appears on screen.
- Unknown: real translation quality, real speed, the GUI on Windows/macOS, and whether the bundled FFmpeg can burn subtitles on those systems.
- **Fix, this week:** run three real, rights-owned French clips through the app on the creators' kind of computer. Nothing else matters until this is done.

### 2. The design makes translation errors hard to catch
- The app uses Whisper's built-in French→English `translate` task directly (`pipeline.py`). It never keeps the French text.
- Direct speech-to-English translation is a quality gamble. It is typically weaker than transcribing French first and then translating the text. That is general knowledge, not something I measured here, and the `small` model is a modest one.
- Whisper-family models are known to invent text over silence, music and noise. The VAD filter reduces this but does not remove it.
- **The reviewer can't check the work.** A French-speaking creator who is weak in English must judge English subtitles with no French transcript beside them. The README says "human review is required" but gives the reviewer nothing to compare against.
- **Fix:** also transcribe the French and show it next to the English in the editor. Then compare `small`, a larger model, and transcribe-then-translate on the same ten clips, scored by a bilingual reviewer. Choose the pipeline from that data.

### 3. Creators cannot install this
- The install is `python -m venv`, `pip install -e .`, and a model download of several hundred MB on first run. No installer, no signed build, no one-click launch.
- Non-technical creators will not do this. In practice you will run it for them. That is fine for a pilot, but then you are running a **service, not selling software**, and your hours must be in the cost.
- **Decision:** for the pilot, run it yourself on your own machine ("concierge" mode) and don't build an installer yet. Package it only if the pilot shows people will pay.

### 4. The economics are untested, and the likely winner is a free tool
- The success test (ten creators who like it and pay more than cost) is the right one. Nothing here proves it yet.
- **I did not research competitors in this project.** That is a gap. Creators can already caption and translate videos with free or cheap tools. Before charging, find out what ten creators use now and what that costs them. Then your price has a reference point.
- Per clip, your time dominates. A 2-minute clip that needs 15 minutes of correction costs more than most creators will pay unless your hourly cost is very low. Track it in minutes, not hope.
- Selection bias: friends say yes. A real payment, even a small one, is the only reliable signal.

### 5. Licensing and consent are unresolved
- The FFmpeg that `imageio-ffmpeg` supplies is a **GPL** build (I checked its configuration: `--enable-gpl`, libx264, libass). **If you ship an installer that includes it, you take on GPL obligations.** That is a lawyer-level question.
- PySide6 is LGPL and has its own conditions. Check the licence terms of the Whisper model weights you use. The README says to verify, but nobody has.
- The "I have rights" checkbox is a statement by the user. It protects nobody. Get written permission from each pilot creator, covering retention and deletion.

---

## P1 — Defects the pilot will probably hit

### 6. Caption quality
- Captions are whole Whisper segments, which can be long. Long lines are only highlighted amber, not split automatically. There are no word-level timestamps, so timing is rough.
- Overlap handling moves a caption's start later (`max(previous_end, start)`), which can make a subtitle appear after the speech starts.
- Only the first audio track is used. Music, several speakers, accents and fast speech are not handled.

### 7. The burned-in MP4 may look bad or fail
- No control over font, size, position, background or vertical (9:16) video. It uses libass defaults. Creators posting short videos care a lot about this.
- libass needs fonts. A static FFmpeg on a system without fontconfig may show missing glyphs. The app checks the filter exists, but then the main deliverable simply fails.
- Export always re-encodes to H.264. Rotated phone video, HDR, variable frame rate and 10-bit video are untested.

### 8. User-facing gaps in the GUI
- **No cancel button** for translation or export. A multi-minute CPU job can only be waited out.
- **No unsaved-changes prompt on close.** A creator can lose 20 minutes of corrections. (`closeEvent` only blocks closing during a running job.)
- First-run model download shows no real progress. The bar sits at ~12% for a long time and looks frozen.
- **No log file.** When a creator says "it broke", you have nothing to look at. Error text is truncated to 250–300 characters.

### 9. Drafts are fragile
- A draft stores the **absolute path** to the video and checks only the file size. Moving the file breaks it, and a different video of the same size would be accepted.

---

## P2 — Engineering hygiene

### 10. Nothing is committed
- `git log` shows only `Initial commit`. Every file I wrote is **untracked**. One lost workspace and the project is gone. Commit and push soon.

### 11. Structure, tests, tooling
- `gui.py` is a 1,038-line single file and has **zero automated tests**. All GUI logic is verified only by reading it.
- Dependencies are version ranges with no lock file, so a fresh install next month may behave differently. No CI. No Windows/macOS test runs.
- The project venv was missing from the checkout this session. I rebuilt one in `/tmp` to re-run the checks. Nothing in the repo depends on it, but anyone cloning will need to create their own.

---

## P3 — Documentation and housekeeping

### 12. Docs
- `README.md`, `PILOT.md` and `TEAM_PLAN.md` overlap and are heavily hedged. The reader has to hunt for the three things to do first.
- `TEAM_PLAN.md`'s six-week schedule and its "8 of 10" go/no-go example are illustrations I wrote, not validated numbers. Set your own thresholds before you start interviewing.
- `pilot_scorecard.csv` expects a hand-calculated `contribution_after_variable_cost`. That invites mistakes; use a spreadsheet formula. It also has no columns for the quoted price versus the paid price, onboarding/support time, or turnaround time.

### 13. A small annoyance
- The repository is named `-Video-Translation` (leading hyphen). Many command-line tools read it as an option, so `cd -Video-Translation` and similar commands misbehave (use `./-Video-Translation`). Consider renaming it.

---

## What is actually solid
- Scope is tight and matches your chosen goal: French→English, short clips, desktop, subtitles only.
- Local processing: no video leaves the machine, and no API key or recurring AI bill.
- Safe file handling: atomic saves, no overwriting the original, FFmpeg paths with spaces and quotes handled, timestamps validated.
- Honest documentation: it does not promise accuracy or profit.

## If you do only five things
1. **Run three real clips on a real desktop** (P0.1).
2. **Show the French transcript beside the English** and compare models on those clips (P0.2).
3. **Ask ten creators what they use and pay today**, then run the pilot concierge-style yourself (P0.3, P0.4).
4. **Resolve licensing and written permission** before taking any money (P0.5).
5. **Commit and push**, then add cancel, an unsaved-changes prompt and a log file (P2.10, P1.8).
