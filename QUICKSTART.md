# Run the prototype in VS Code (about 10 minutes)

![The editor in demo mode](docs/prototype-demo.png)

*Demo mode: invented sample captions on a synthetic clip. The video pane is empty in this screenshot only because it was taken on a server without a media backend; on your computer the clip plays there.*

## 0. What you need

- A **Windows, macOS or Linux desktop** with a screen (not a remote server).
- **Python 3.10, 3.11 or 3.12.** Python 3.13 is **not** supported yet. Check with `python --version` (on Windows try `py -3.12 --version`).
- **Git** and **VS Code** with the *Python* extension (VS Code will offer to install it).
- About 1 GB of free disk space and an internet connection **for the first install**. The real speech model downloads once (several hundred MB) the first time you generate subtitles.

## 1. Get the code

```bash
git clone https://github.com/fongangchrisp-cell/-Video-Translation.git
cd ./-Video-Translation          # the leading "./" matters: the folder name starts with a hyphen
git checkout arena/01a0ecbd-video-translation
code .
```

## 2. Create the environment (VS Code terminal: Terminal → New Terminal)

**Windows (PowerShell):**
```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```
If PowerShell blocks the activation script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then try again.

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Then press **Ctrl+Shift+P** (Cmd+Shift+P on macOS) → **Python: Select Interpreter** → choose the one inside `.venv`.

## 3. Run it

Open **Run and Debug** (the play-bug icon, or Ctrl+Shift+D), pick a configuration at the top, and press **F5**:

| Configuration | What it does |
| --- | --- |
| **ClipTranslate DEMO** | Opens the editor with a sample clip and invented captions. **No model download.** Try editing, splitting, merging, saving a draft, **Save .srt** and **Export subtitled MP4**. Start here. |
| **ClipTranslate (real)** | The real app. Choose **your own** short French video you have the right to use, tick the permission box, click **Generate English subtitles**. The first run downloads the speech model. |

Or from the terminal: `python -m cliptranslate --demo` and `python -m cliptranslate`.

## 4. Try the real thing (this is the test the whole project depends on)

1. Pick a 30–90 second video of **you or a friend speaking clear French**. Do not use someone else's film or music.
2. Choose the **Small** model, leave **Also transcribe the French** ticked, click **Generate English subtitles**. Expect several minutes on a laptop CPU, plus the first-time download.
3. Select each line and compare **English** with **French heard**. Fix mistakes. Note how many lines you corrected and how many minutes it took.
4. Export the MP4 and watch it.
5. Send the team: your computer (OS, RAM), the clip length, processing time, what was wrong, and the log file (**Open log folder** button). **That report is the most valuable thing you can give the project right now.**

## Common problems

| Problem | Fix |
| --- | --- |
| `No module named PySide6` or imports fail | The environment isn't activated or the install failed. Re-run step 2 in the VS Code terminal and re-select the interpreter. |
| `Could not load the speech model` | No internet, no disk space, or a firewall blocking the model host. Try again on another network. |
| Window opens but the video won't play | Your system lacks a codec for the file. Click **Open original in video player**. Subtitles and export still work. |
| Export says FFmpeg lacks `subtitles/libass` | Save the `.srt`, or install a full FFmpeg build and set `CLIPTRANSLATE_FFMPEG` to its path. Tell us your OS; this is exactly what we need to learn. |
| Linux: Qt error about `libxcb` / `xcb-cursor` | `sudo apt install libxcb-cursor0 libgl1 libegl1 libxkbcommon0` |
| `cd -Video-Translation` fails | Use `cd ./-Video-Translation`. |

## Limits of this prototype

It is a **working prototype, not a product**. Real translation quality is unmeasured, there is no installer, and Windows and macOS have not been verified. Always review subtitles before sharing a video. See [README.md](README.md), [AUDIT.md](AUDIT.md) and [PILOT.md](PILOT.md).
