# Rights, licences and permission: checklist before taking any payment

This is a working checklist, **not legal advice**. Have someone qualified in your country review it before you charge anyone or ship an installer.

## 1. Software licences (check before distributing anything)

| Component | What we know | What to do |
| --- | --- | --- |
| **FFmpeg** (bundled by `imageio-ffmpeg`) | The Linux build we inspected was configured with `--enable-gpl` (includes libx264 and libass). A GPL build brings obligations if you **redistribute** it. Windows/macOS builds were not inspected. | Do not ship an installer containing FFmpeg until you have read the licence terms and decided how to comply, or have the user install FFmpeg themselves. Running it on your own computer for creators is a different question; ask your adviser. |
| **PySide6 (Qt)** | Generally LGPL. | Read the LGPL conditions before packaging an app (linking, replaceable libraries, notices). |
| **faster-whisper and Whisper model weights** | Believed to be MIT-licensed; **we have not verified the exact terms for the weights you download.** | Read the licence on the model page and keep a copy of the notice. |
| **Other Python dependencies** | Not audited. | Run a licence report (`pip-licenses` or similar) and keep the output. |

## 2. Permission from each creator (use before any trial)

- Written permission that they **own or may license** the video and its audio (including music and other people's voices).
- What you may do: process it, show it to reviewers, keep it for N days.
- **Deletion date**, and who confirms deletion.
- Whether you may quote their feedback, and under which name or anonymised ID.
- What they are paying for, what is included (number of fixes), and the refund rule.
- That machine translation can be wrong and the creator must review before publishing.

A tick-box in the app is **not** permission. Keep signed forms outside Git in `pilot_data/`.

## 3. People and money

- Written agreement among the eight of you: roles, weekly hours, who owns the code, how expenses are paid, what happens if someone leaves, and how any profit is shared. Friendship is not a substitute.
- Check local rules for accepting payments and for registering a business.
- If a creator's clip includes anyone's voice or face beyond the creator's own, get that person's consent too.
- Handle creator data minimally: store videos on one encrypted drive, share them with the fewest people, delete on the agreed date, and note deletions in the scorecard.

## 4. Before a public launch (not the pilot)

Licence review of every dependency, a privacy notice, terms of service, and a decision on whether you really want to process other people's content at scale.
