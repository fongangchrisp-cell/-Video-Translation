# Ten-creator pilot: prove value before building a movie translator

**Target:** Ten creators who own or have permission to translate their own short French-language videos, want English subtitles, and can give honest feedback. Seek variety in accents, recording quality, pace and genre. Do not process someone else's film without rights.

## Competitive reality check (read before choosing a price)

French→English captions for a short clip are already available to creators **free or cheap**. Summaries from comparison articles (several written by vendors, so treat them as marketing, and re-check the live prices yourself):

- **CapCut**: free auto-captions and translation; Pro about $19.99/month ([source](https://maestra.ai/blogs/best-subtitle-translation-software), [source](https://novascribe.ai/compare/best-subtitle-generation-tools)).
- **YouTube**: free auto-captions and auto-translate for videos already uploaded; editable, but accuracy can be poor ([source](https://www.descript.com/blog/article/best-auto-subtitle-generator)).
- **Kapwing** from about $16/month, **VEED** from about $12–18/month, **Descript** from about $16/month, all with translation and burned-in captions ([source](https://novascribe.ai/compare/best-subtitle-generation-tools), [source](https://maestra.ai/blogs/best-subtitle-translation-software)).

So a creator will not pay much for "automatic subtitles". The only thing this pilot can plausibly sell is **a better, human-checked result with the work done for them**. Test that directly: ask each creator what they use today, what they pay, and what is wrong with it. Record the answers in `pilot_data/`. If a free tool is good enough for most of the ten, say so in the decision meeting.

## Test procedure

1. Invite ten creators. Ask how they currently subtitle a clip, how long it takes, and what they would pay for a usable English-captioned version **before showing yours**.
2. Have each supply one rights-cleared French-speaking clip of 30–120 seconds. Agree on whether you may retain a copy and when to delete it. Process it on the desktop; let the creator correct captions and review the exported MP4. Never treat model output as final without review.
3. Record duration, model chosen, processing time shown in the app, minutes of human corrections, failures/retries, direct out-of-pocket costs, electricity/hardware allocation, and any refund/revision work. **Do not call the cost zero just because no API key is used.**
4. Ask the creator to rate usefulness (1–5), note specific errors, and state what they would actually pay or pay in a small real transaction. Do not confuse willingness to pay with revenue. Record repeat use a week later if possible.
5. Decide whether to improve the narrow workflow, switch to a paid translation provider for better quality, change customer segment, or stop. Do not start native mobile apps, full movies or lip-sync just because the first demo runs.

A blank [pilot scorecard](pilot_scorecard.csv) is provided. Copy it to `pilot_data/scorecard.csv` and keep real creator names, videos, quotes and financial data outside Git. Use anonymised IDs in any shared findings. This app contains **no telemetry**; it writes a local log file only (see the README).

**Never do the arithmetic by hand.** Run:

```bash
python -m cliptranslate.pilot_report pilot_data/scorecard.csv
```

It computes each clip's contribution (price paid minus cash cost, energy/hardware, payment fees, refunds, review labour and support labour), lists rows with missing or suspicious data, and states plainly whether the goal is met: ten different creators rated the result 4–5 **and** each clip paid more than its full cost. A clip with no recorded payment is flagged, because willingness to pay is not revenue.

**Run the first trials concierge-style:** one of you runs the app on your own computer and delivers the files to the creator. Do not ask ten creators to install Python. Record the hours this takes in `onboarding_support_minutes`; that is part of the true cost.

**Write the go / no-go rule before the first creator trial** and put it in `pilot_data/`. Do not change it after seeing results.

## Decision questions

- Did ten rights-holding creators finish an output they were comfortable publishing? How many would use it again?
- How many captions needed correction, and how many **human minutes per delivered video minute** were spent reviewing? How often did the app fail or need a retry?
- For the **actual selling price** (not a hypothetical price), is `price − variable processing cost − the value of correction/support time − refunds` positive per clip? Include model downloads, energy/compute rental, storage/transfer if any, and payment fees. Fixed costs and customer acquisition come **after** this contribution calculation.
- Is English text on the video what they want, or do they really need dubbed audio? Ask before building the latter.

Do not infer demand or profitability from one impressive demo. Review results after all ten tests, including failures.
