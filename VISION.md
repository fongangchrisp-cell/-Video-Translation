# BCX — Black Cortex: vision, reality check and roadmap

<img src="docs/bcx-logo.png" alt="BCX Black Cortex" width="180" align="right">

*This document records what the BCX team is trying to do, what already exists, and where BCX could genuinely be different. Parts marked **(to confirm)** are my reading of the team's intent. Please correct them.*

## 1. The vision, as I understand it **(to confirm)**

BCX wants to build a way to **translate video, eventually whole films, so that people can watch them in a language they understand**, and to do it for a market the big tools serve poorly. The team is based in Cameroon, a country where French and English are both official languages and where audiences, filmmakers and creators often sit on different sides of that language line. Film and video are how many people there learn and are entertained.

The long-term picture: **a film made in one language reaches viewers in another, with subtitles first and spoken dubbing later, and with quality that people from the community trust.**

## 2. Reality check: what already exists (researched 2026-10-08)

"Never produced" is **not accurate for the general idea**. AI video translation and dubbing are already sold today, according to comparison articles (several written by vendors, so treat the claims as marketing and verify):

| Tool | What it sells | Languages claimed | Price seen |
| --- | --- | --- | --- |
| **HeyGen** | Dubbing with voice cloning and lip-sync | 40 to 175+ (sources disagree) | from about $29/month ([source](https://vidocu.ai/blog/7-best-ai-video-translation-tools-in-2026)) |
| **Rask AI** | Dubbing, subtitles, lip-sync, bulk localisation | 130+, including Swahili ([source](https://videodubbing.com/blog/post/top-ai-video-dubbing-software-2026-ultimate-comparison/)) | from about $60/month |
| **ElevenLabs** | Voice-preserving dubbing, no native lip-sync | 29 to 90+ (sources disagree) | from about $6/month |

Free and cheap subtitle tools (CapCut, YouTube auto-translate, Kapwing, VEED) are listed in [PILOT.md](PILOT.md).

One review site says voice quality "drops for some Asian and African languages" ([source](https://toolchase.com/blog/best-ai-dubbing-tools-2026/)). That is a lead, not proof. **We have not tested any of these tools on Cameroonian content, so we do not yet know where they fail.**

**Consequence:** BCX will not win by "AI translates videos". That already exists. BCX can only win by being **better or more trusted for a specific audience** than tools built elsewhere.

## 3. Where BCX could be genuinely different (hypotheses to test, not facts)

1. **Quality for Cameroonian French, English and Pidgin, checked by people from the community.** Accent, slang and cultural references are exactly where generic tools are weakest. The "Black Cortex" is the machine brain; **the human reviewers are the moat**. *Test:* run the same ten clips through BCX and two existing tools, and have bilingual reviewers score them blind.
2. **Local languages** (for example Duala, Ewondo, Bassa, Fe'efe'e). Tool coverage here is unknown to us and likely thin. *Test:* check each tool with a native speaker before building anything. Do **not** promise a language until a native speaker has scored real output.
3. **Done-for-you service for filmmakers and creators**, priced per title and paid in ways they actually use (for example mobile money). *Test:* ask ten creators what they pay today and what they would pay for a checked result ([PILOT.md](PILOT.md)).
4. **Rights-clean pipeline.** Creators who own their work can translate it safely; BCX never handles pirated films. This is a trust feature and a legal necessity ([LEGAL_CHECKLIST.md](LEGAL_CHECKLIST.md)).

If testing shows none of these holds, BCX should say so and change direction. That is a good outcome, not a failure.

## 4. Roadmap: each step unlocks only after evidence

| Stage | What | Gate to move on |
| --- | --- | --- |
| **0 (now)** | French→English subtitles for short clips, desktop prototype | Ten creators like the result and pay more than full cost ([PILOT.md](PILOT.md)) |
| **1** | English→French, and Cameroonian Pidgin as an input accent | Reviewers score output acceptable; creators ask for it |
| **2** | Short films (5 to 30 minutes): batch processing, project management, multi-speaker handling | Stage 0 economics still positive at longer length |
| **3** | Spoken dubbing (voice synthesis) with consent for any voice used | Customers prove they need audio, not only subtitles. Dubbing carries voice and likeness rights risks |
| **4** | Local languages | Native-speaker review team in place; real demand shown |
| **5** | Feature films, distribution partnerships | Only after the above, and only with rights-holders |

**We do not build a stage until the one before it has passed its gate.** Full movies, dubbing and lip-sync are Stage 2 to 5 on purpose.

## 5. Questions the BCX team should answer together

1. Is the first audience **filmmakers**, **everyday creators**, **schools and churches**, or **viewers**? (Different customers, different prices.)
2. Which direction matters most first: French→English, English→French, or local languages?
3. Who are your first five paying customers by name, and how will you reach them?
4. What is BCX's unfair advantage: access to native reviewers, a film community, distribution, or something else?
5. What does success look like in 90 days, in numbers?
6. How much money and how many hours can the group lose before it should stop?

Answers belong in `pilot_data/` (kept out of Git) and should shape the decision meeting in [WORKPLAN.md](WORKPLAN.md).
