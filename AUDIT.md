# Brutal audit — ClipTranslate pilot (most to least important)

## Second audit (2026-10-11, commit `fbbb958`)

**Verdict in one line:** the *delivery* is now good for a prototype (it builds, it launches, it is tested on three operating systems). The *product* is exactly as unproven as before: **nobody has put a real French video through the real model and judged the English.** Everything below follows from that.

**What I actually checked this time:** ran Ruff (clean) and the 39 non-GUI tests locally (pass); read the GitHub results for the latest commit (full suite on Linux, Windows, macOS: pass; both app builds with self-check: pass); read the translation code; checked links, line endings and the ZIP that GitHub serves; looked for secrets (none) and for what the logs record (file names only, no speech text). **What I could not check:** the real model (Hugging Face is unreachable from my environment), video playback, and the app on a real Windows or Mac screen.

### P0 — fix or decide before anything else

| # | Finding | Why it matters | What to do |
| --- | --- | --- | --- |
| A1 | **The core promise is untested.** No real clip has gone through the real model. | Translation quality, speed and memory use are all unknown. All tests use a fake model. | Run 3 rights-owned French clips on a real PC (`docs/EVALUATE.md`). Do this before more features. |
| A2 | **`main` was empty.** The app lived only on a working branch, so the GitHub front page showed nothing and a default ZIP/clone gave an empty project. | You already hit this confusion. | Merge the branch into `main` (see the pull request). |
| A3 | **No LICENSE file, and the repository is public.** Public with no licence means nobody may legally reuse the code. It also publishes your strategy: `VISION.md`, `WORKPLAN.md`, `TEAM_PLAN.md`, `PILOT.md` and `LEGAL_CHECKLIST.md` are readable by anyone, including competitors. | A business risk, and a legal one. I did not choose a licence for you; that is your decision. | Decide: **private** repo with the 8 members added (my recommendation while you validate), or public with a chosen licence. Free build minutes are smaller on private repos, and Windows and macOS builds use them faster. |
| A4 | **Nobody has run it on a real desktop.** GitHub's checks start the app offscreen; that proves it starts, not that it feels right. | Windows warnings, fonts, playback, slow disks. | One teammate on Windows, one on a Mac, screenshots of what they see. |
| A5 | **Translation method is a quality gamble.** The app asks Whisper to translate French speech straight to English, with the `small` model, on CPU. Whisper-family models can invent or repeat text over silence, music and noise. The code leaves `condition_on_previous_text` at its default, which is a known cause of repeated lines. | The product *is* this quality. | Measure first. Then run a small experiment: setting that option to off, a bigger model, and transcribe-then-translate, scored by a bilingual reviewer on the same clips. |
| A6 | **Cameroonian-accent French, slang, code-switching with English or local languages are untested.** | Likely your real audience. | Put at least 2 such clips in the first test. |

### P1 — will bite soon

| # | Finding | What to do |
| --- | --- | --- |
| B1 | **Dependencies are not pinned.** Between two of my runs `imageio-ffmpeg` changed version and the bundled FFmpeg with it. A build that works today can break next month. | Add a lock file once the first real test passes. |
| B2 | **The install is large:** about 1.2 GB for the environment (PySide6 brings Qt web and PDF parts we do not use), plus the model download (several hundred MB). On slow or expensive connections that is a real barrier. | Pre-download once and share the model folder inside the team; consider a smaller Qt install later. |
| B3 | **First-run model download comes from Hugging Face with no pinned version.** It fails on blocked or unstable networks, and the download cannot be resumed from the app screen. | Document an offline copy method after the first real test. |
| B4 | **Built apps are unsigned**, so Windows shows "Windows protected your PC" and macOS blocks them at first. Mac build is **Apple-chip only**. Downloads expire after 30 days. | Acceptable for the team. Signing costs money every year; only after creators validate. |
| B5 | **The built apps bundle a GPL build of FFmpeg.** Fine inside the team; not for creators or the public until a qualified person has reviewed `LEGAL_CHECKLIST.md`. | Keep the tester-only rule. |
| B6 | **`gui.py` is 1,237 lines**; GUI behaviour is covered only by smoke tests. Every new feature makes it harder to change safely. | Split it when you start adding features by hand (the work you are about to do in VS Code). |
| B7 | **Limits are hard-coded:** 120 s and 500 MB per clip, first audio track only. Reasonable for the pilot, but a creator with a longer or two-language clip will hit a wall. | Keep; tell creators up front. |

### P2 — tidy later

- **Documentation sprawl:** 10 Markdown files with overlap. I fixed two stale statements (install size, "CI never ran"); the "Status after the fix pass" table below is from the earlier commit and still says 40 tests.
- The hyphenated repository name (`-Video-Translation`) still trips some tools; rename on GitHub when convenient.
- GitHub Actions shows a Node 20 deprecation warning. Harmless today; bump the action versions later.
- Log files hold video **file names**, not speech text. Fine, but tell creators.

### What is genuinely good
- Safe by design: local processing, no uploads, no keys, refuses invalid or oversized files, drafts survive moves, cancel works.
- Human review is built in: the French heard is shown beside each English line.
- Launching works three ways and is checked automatically on Windows, macOS and Linux.
- Scope discipline: still FR→EN subtitles for short clips. No feature creep.

### Strategy check (unchanged, still the real risk)
The code is not what decides this project. Ten creators paying more than the full cost is. Until the first test, every extra feature is a guess.

---

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
