# BCX (Black Cortex) — ClipTranslate: small-team plan for the ten-creator pilot

## The goal we are staffing for

Help **ten creators translate their own 30–120-second French-language videos into usable English subtitles**, then learn whether they are satisfied and will **actually pay more than the full cost of delivering each video**. The current repository is a Python desktop prototype for this narrow task. It is *not* yet a packaged product; real-model output and the GUI need testing on a normal desktop. Do not recruit a full-movie, mobile, dubbing or lip-sync team before this pilot works.

## Who should work with us?

**Core team: two or three people.** One person must own creator relationships and business decisions; one must own the working software. If there are three, split the engineering responsibilities:

| Owner | Deliverables for this pilot | Useful skills |
| --- | --- | --- |
| **Product and creator lead (you, if you want this role)** | Interview ten rights-holding creators; obtain permission for their test videos; set a test price; schedule trials; record honest feedback, payments and all costs in `pilot_scorecard.csv`; decide what to change. | Listening, communication, follow-through, basic budgeting. This role cannot be replaced by another AI model. |
| **Media / Python engineer** | Run the real speech model on diverse French clips; improve recognition/translation timing; maintain FFmpeg extraction and export; measure processing time and failure rates. Own `pipeline.py`, `media.py` and their tests. | Python, FFmpeg, debugging audio/video; AI *integration* is enough for now, not model research. |
| **Desktop / UX engineer** | Make selecting, correcting, previewing and exporting clips understandable; fix crashes; test on the creators' actual computer type; prepare a simple installable build when needed. Own `gui.py`, `project.py` and usability checks. | Python/PySide6, desktop packaging, user testing. |

**Work with, but do not necessarily hire full-time:**

- A **bilingual French–English reviewer** to score meaning, timing and readability, and to record correction time. If a core teammate can do this well, that person can cover it; otherwise pay a reviewer per clip and count that cost.
- **Ten creators who own their source videos**: for example educators, YouTubers, short-form video makers or small organizations seeking an English-speaking audience. They are design partners and potential customers, not unpaid substitute QA staff. Agree on permissions, retention/deletion, and what you may quote publicly.
- A **legal/licensing and bookkeeping adviser**, consulted when setting contributor terms and before charging for work involving other people's content. This need not be a permanent team role.

If there are **only two of you**, combine the engineering roles and use a part-time bilingual reviewer. If none of your friends can ship/debug a Python desktop app, seek **one capable generalist** rather than dividing transcription, translation and UI among several inexperienced contributors. Do **not** hire a lip-sync or cloud-scaling specialist yet.

## How the group should work

1. Agree in writing on weekly time commitments, one owner per task, spending limits, who can approve a release, and how disagreements are decided. Track work with small GitHub issues and code reviews; run automated tests before merging changes. Demo one working clip together every week.
2. Before promising equity or revenue shares, agree on code/IP ownership, expenses, compensation, what happens if someone leaves, and how ownership vests over time. **Friendship is not a substitute for an agreement.** Get locally appropriate professional advice where necessary; no split percentage is automatically fair.
3. Use only rights-cleared test clips; keep real videos and identifiable creator feedback **outside Git**. Ask permission to store footage, limit who can access it, and agree on a deletion date. Record failures and unhappy users as carefully as successes.
4. Count *all* per-clip costs: allocated processing/electricity/internet, model/service fees if added, human correction and support time at a realistic rate, payment fees, retries and refunds. `actual price paid − these costs` must be positive **before** claiming a viable unit margin. Fixed costs and finding new customers must eventually be covered too.

## Six-week experiment (a guide, not a promise)

| Period | Product lead | Engineers and reviewer | Evidence to collect |
| --- | --- | --- | --- |
| **Week 1** | Choose ten potential rights-holding creators; ask about their current workflow and price expectations **before demonstrating the app**. | Run the prototype on a real desktop with three short, owned French clips. Reviewer checks output; log crashes and corrections. | Can a creator complete an export? Is English understandable? How long and how costly is one clip? |
| **Week 2** | Agree on a test price and simple permission/deletion terms. Schedule trials. | Fix the two biggest blockers; make setup simple on **one** desktop OS first. Test export and draft reopening. | Repeatable workflow without an engineer rescuing every step. |
| **Weeks 3–4** | Supervise ten creator trials without hiding failed runs; ask for actual payment or a small paid order if appropriate. | Help with bugs but record every minute of assistance. Reviewer scores output and correction effort. | Ten complete sessions; satisfaction, real price paid, total cost, failures and support time. |
| **Weeks 5–6** | Ask whether users would return with another clip; calculate per-clip margins and decide whether to continue, change the niche, or stop. | Fix only problems supported by pilot evidence; plan the next feature **after** the decision. | Return use and a defensible cost/revenue calculation, not merely a successful demo. |

**Agree on a go/no-go rule before interviewing users.** One *example*, not a universal benchmark: ten completed trials, at least eight creators rating the output publishable after reasonable edits, some paying a real price with positive contribution per delivered clip, and evidence they want a second video. Your stated aspiration is stronger—ten happy creators at a sustainable price. If users like the demo but it takes unpaid hours to fix every clip, the business case is **not yet proved**.

An AI coding assistant can help draft code, tests, documents and analysis. It cannot sign rights agreements, recruit customers, judge every cultural nuance, or become an accountable human cofounder.
