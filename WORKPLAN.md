# Work plan for 8 part-time people

**Goal (unchanged):** ten creators translate their own short French videos into English subtitles, like the result, and pay more than the full cost of producing it. Desktop, French→English, subtitles only.

## 1. Real capacity

Each person gives 2–4 hours a day, 7 days a week, so 14–28 hours a week each. Plan with **60–70% of that**, because life interrupts. That gives roughly **70–110 team hours a week**.

That is plenty of hours. The real limits are different:

- Only people who can code can change the app. Most of the other hours go to creators, reviewing, testing and records.
- With 8 people, confusion costs more than missing skills. One owner per task, written down.
- Five or six short days beat one marathon. Keep the coordination cost small.

## 2. Day 1–2: find out who can do what (no guessing)

Each person answers these in a shared document, in 10 minutes. Mark each skill 0 (none), 1 (some), 2 (can do it alone):

| Skill | 0 / 1 / 2 |
| --- | --- |
| Writes Python | |
| Fixes bugs in an existing codebase / uses Git | |
| Has built a desktop or mobile interface | |
| Speaks and writes **French** well | |
| Speaks and writes **English** well | |
| Has worked with video (editing, subtitles, FFmpeg) | |
| Knows people who make short videos (YouTube, TikTok, school, church, business) | |
| Comfortable talking to strangers / selling | |
| Keeps spreadsheets and records accurately | |
| Knows contracts, licences or business registration | |

Also record: **weekly hours**, **time zone/internet quality**, and the **computer** (Windows / macOS / Linux, RAM, free disk). We need real machines to test on, because the sandbox could not run the app.

## 3. Roles for 8 people

Assign roles from the survey scores, not from friendship. One person may hold two small roles. Nobody should hold two heavy ones.

| # | Role | Owns | Best fit |
| --- | --- | --- | --- |
| 1 | **Coordinator** | The weekly plan, the task board, the 15-minute check-in, deadlines | The most reliable person, not necessarily the most senior |
| 2 | **Engineer A: speech and translation** | `pipeline.py`, French transcript, model comparison, speed | Best Python skills |
| 3 | **Engineer B: app and export** | `gui.py`, `media.py`, cancel button, unsaved-changes prompt, log file, packaging later | Second-best Python / interface skills |
| 4 | **Bilingual reviewer A** | Scores translations, fixes them, times the correction work | Strongest French + English |
| 5 | **Bilingual reviewer B** | Scores the same clips **separately**, so we see how much reviewers disagree | Second bilingual person; or the same skill at a lower level |
| 6 | **Creator outreach lead** | Finds and talks to the ten creators, and asks what they use and pay today | Best talker |
| 7 | **Creator operations / support** | Runs each creator's trial, collects permission, tracks turnaround and complaints | Organised and patient |
| 8 | **Records, money and legal** | `pilot_scorecard.csv` as a spreadsheet, costs, permission forms, payments, licence questions | Careful with numbers and paperwork |

If you have fewer than two people who can code, **do not split the engineering**. Give it to the best one, and have the others do outreach, review and testing. If nobody codes, recruit one engineer before anything else; the other seven cannot ship the app.

If you have no bilingual person, find one before the first real test. Without one, nobody can tell whether the translations are any good.

**Everyone, week 1:** install the app on your own computer and run one test clip. This is the cheapest way to learn what breaks on Windows, macOS and Linux.

## 4. Weekly rhythm

- **Daily:** post in the group chat: done yesterday, doing today, stuck on. Three lines.
- **Twice a week (Mon, Thu), 20 min:** short call. Review the board, remove blockers. No long discussions; take those to a thread.
- **Weekly (Sun), 45 min:** demo one working clip, review the numbers, plan the next week.
- **Rules:** one owner per task. A task is "done" only when someone else has checked it. Anything not finished in a week gets split or dropped. Code changes go through a GitHub pull request, with the tests passing.
- **Honest record:** every hour spent on creators or corrections goes in the scorecard. That is how we learn the true cost.

## 5. Eight weeks, in order

| Week | Goal | Who | Exit check |
| --- | --- | --- | --- |
| **0 (2 days)** | Survey, roles, machines, rules | Everyone; Coordinator runs it | Roles named, shared board exists |
| **1** | **Real test:** 3 owned French clips, real model, real desktop | A, B, reviewers; everyone installs | Written result: does the translation make sense? What broke? |
| **2** | Fix the top blockers: French transcript beside English, cancel, unsaved-changes prompt, log file. Compare models | A, B, reviewers | Reviewers choose the pipeline from scored clips |
| **2** (parallel) | List 20 possible creators; interview 10 about current tools and price; draft a permission form | Outreach, Ops, Records/legal | Interview notes, a price range, a signed-form template |
| **3** | First 3 creator trials, run by us, with permission. Record everything | Ops, reviewers, Engineers on call | 3 full scorecard rows |
| **4–5** | Trials 4–10 with a **real price**, even a small one | Ops, Outreach, Records | 10 rows; payments received or refused (and why) |
| **6** | Analyse costs and reactions; fix only what the data points to | All | A one-page result: price, cost, satisfaction, repeat interest |
| **7** | **Decision meeting:** continue, change niche or price, or stop | All | Written go / change / no-go, using the rule set in advance |
| **8** | Next step only if "go": installer, polish, a larger test | A, B | A new plan with new numbers |

Agree the go / no-go rule **before week 3**, so the data can't be bent afterwards.

## 6. Task board: starting tasks

| Task | Owner role | Done when |
| --- | --- | --- |
| Skills and machine survey | Coordinator | 8 answers collected |
| Install and run on every machine; report problems | Everyone | 8 short reports |
| Real run on 3 owned French clips | Engineer A | Output, timings and notes saved (outside Git) |
| Show French transcript next to English | Engineer A + B | Works on real clips, tests added |
| Cancel button; unsaved-changes prompt; log file | Engineer B | Works on a real desktop |
| Score translations on the same 3 clips | Reviewers A and B | Two independent scores, with correction minutes |
| 20 creator candidates; 10 interview slots | Outreach | List and calendar |
| Permission and deletion form | Records / legal | Reviewed by someone qualified |
| Scorecard as a spreadsheet with formulas | Records / legal | Totals compute automatically |
| Licence check: FFmpeg, PySide6, model weights | Records / legal + Engineer B | Short written note and a decision |

## 7. Risks to watch

- **Someone disappears or slows down.** Keep each task's notes in the board so another person can pick it up.
- **Too many opinions.** The Coordinator and the data decide. Cut debate that has no scorecard row behind it.
- **Doing free favours.** If creators get unlimited free fixes, you learn nothing about price. Fix what is in the agreement, and log every extra minute.
- **Hurting creators' trust.** Delete their videos on the agreed date. Never share clips outside the team.
- **Friendship over agreements.** Before anyone expects a share of profit, write down roles, ownership and what happens if someone leaves. Get qualified local advice.
