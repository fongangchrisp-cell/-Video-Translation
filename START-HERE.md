# START HERE: how to open BCX ClipTranslate

*For anyone on the BCX team, including people who have never used Python or a terminal.*

You have **three ways** to open the app. Pick **one**. Way 1 is the easiest. If it fails, use Way 2.

| | What you do | Needs Python? | Needs internet? | Status |
|---|---|---|---|---|
| **Way 1: ready-made app** | Download a ZIP, unzip, double-click | No | Once, to download | Built and self-checked by GitHub. Not yet tried by a person. |
| **Way 2: launcher file** | Download the project, double-click one file | Yes (we tell you how) | 5–15 min on first run | Setup step tested on Windows, macOS and Linux. Not yet tried by a person. |
| **Way 3: VS Code** | Follow `QUICKSTART.md` | Yes | Yes | For people who will change the code |

---

## Way 1: the ready-made app (no Python)

The app is built automatically by GitHub (a free service that runs on the project's own page). Each build is self-checked: GitHub starts the built app, opens the demo, and exports a subtitled video before it is zipped.

1. Sign in to GitHub. Open: https://github.com/fongangchrisp-cell/-Video-Translation/actions/workflows/build-app.yml
2. Click the **newest run** at the top with a green tick.
3. Scroll to the bottom to **Artifacts**. Download:
   - **BCX-ClipTranslate-Windows** if you have a Windows PC.
   - **BCX-ClipTranslate-macOS** if you have a Mac with an Apple chip (M1, M2, M3, M4). Older Intel Macs: use Way 2.
4. Unzip it (right-click → Extract All on Windows; double-click on Mac).
5. **Windows:** open the folder `BCX-ClipTranslate` and double-click **`BCX-ClipTranslate.exe`**.
   **Mac:** right-click **`BCX-ClipTranslate`** → **Open** → **Open**.
6. Windows will probably say **"Windows protected your PC"**. This is because the app is not yet signed with a paid certificate. Click **More info** → **Run anyway**. On a Mac, if it is blocked, go to **System Settings → Privacy & Security** and click **Open Anyway**.

The window opens. It starts with no video. To see the editor with a sample clip, use Way 2 and choose **1 = DEMO**, or just choose your own French video.

**First real translation:** the app downloads the speech model (several hundred MB) once. Keep internet on. The window shows progress. Later runs work offline.

> The ready-made app is for **BCX testing only**. Do not give it to creators or the public yet: it contains FFmpeg, and the licence question in `LEGAL_CHECKLIST.md` must be settled first.

---

## Way 2: the launcher file (needs Python once)

### A. Download the project
Open https://github.com/fongangchrisp-cell/-Video-Translation/tree/arena/01a0ecbd-video-translation, click the green **Code** button → **Download ZIP**, and unzip it somewhere easy (for example your Documents folder).

### B. Install Python 3.12 (once)
Go to https://www.python.org/downloads/ and install **Python 3.12**.
- Not 3.13 or newer. The app does not support it yet.
- **Windows:** on the first installer screen, tick **"Add python.exe to PATH"**.

### C. Double-click the launcher
| Your computer | Double-click this file in the project folder |
|---|---|
| **Windows** | `Start-BCX.bat` |
| **Mac** | `Start-BCX.command` (first time: right-click → Open) |
| **Linux** | open a terminal in the folder and run `./start-bcx.sh` |

A black window opens and talks to you in plain English. **First time only**, it builds a private environment and downloads the app. This takes 5–15 minutes and about 1.5 GB of disk. **Do not close the black window.**

Then it asks:

```
1 = DEMO: try the editor with a sample clip (no download, invented captions)
2 = REAL: translate my own French video
```

Type **1** to look around, or **2** for real work. Next time it opens in a few seconds.

**Windows "Windows protected your PC" on the .bat file:** click **More info** → **Run anyway**.

---

## If something goes wrong

| What you see | What it means | What to do |
|---|---|---|
| "Python 3.10, 3.11 or 3.12 was not found" | Python is missing, too new, or not on PATH | Install Python 3.12 and tick "Add python.exe to PATH". Then run the launcher again. |
| The black window closes at once | Rare. Windows closed it before you could read it | Open **PowerShell** in the folder and type `.\Start-BCX.bat`. Then read the message. |
| Setup stops with red text | Usually internet or disk space | Check you have 3 GB free and internet. Run the launcher again; it continues. |
| Nothing opens after setup | Rare | Take a screenshot of the black window and send it to the team. Also click **Open log folder** in the app if it opens. |
| Translation stays at "Loading the speech model" | First-time download is slow | Wait. Several hundred MB on a slow connection can take a while. |
| Linux: "libGL" or "xcb" error | The system is missing display libraries | Ubuntu/Debian: `sudo apt install libgl1 libegl1 libxkbcommon0 libxcb-cursor0` |

---

## How this becomes a proper product (the honest roadmap)

| Level | What it is | State today |
|---|---|---|
| **1. Runs from the project** | Launcher file; needs Python | **Done** |
| **2. Ready-made app for testers** | ZIP you unzip and double-click, built by GitHub | **Done, for the BCX team's testing** |
| **3. Real installer** (`Setup.exe` / `.dmg`) | Click-next installer with an icon and Start-menu entry | **Not done.** Needs (a) a decision on the FFmpeg licence, (b) an icon and installer script, (c) code-signing certificates, which cost money every year. |
| **4. Sellable service** | Creators pay for human-checked results | **Not proven.** This is what the ten-creator pilot in `PILOT.md` tests. |

Do not spend money or time on level 3 until at least a few creators say the **results** are worth paying for. Level 4 is the real question; levels 1 and 2 are only the delivery truck.

### How to make a new ready-made app after a code change
1. Push your change to the branch.
2. On GitHub: **Actions → Build desktop app → Run workflow** (or just push a file under `packaging/`).
3. Wait about 5 minutes. Download from **Artifacts** as in Way 1.
