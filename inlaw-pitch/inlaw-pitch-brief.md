# Brief: Family Loan Pitch to Steve and Dawn

Build a two-part pitch that Amber and I (Matteo) will present together, in person, to her parents Steve and Dawn, asking for a formal, fully documented family loan at a rate below today's market so we can build our home on the land they're gifting us: (1) a narrated video, then (2) a short discussion deck we advance live. Work in two phases with a hard stop for my approval between them. Done when every completion check at the end of this brief passes and I approve the final version.

## The message in one line
We want to build a home across the street from Papa and Grandee. Today's bank rates make that impossible for us. A family loan at a rate below market makes it possible, and we'll do it formally, on paper, the way a bank would, so it's clear and fair for everyone.

## The situation (treat as given)
- Family: Amber and I have three boys: Lucas, Owen, and Wyatt (newborn). They call Steve and Dawn "Papa" and "Grandee."
- Land: across the street from Steve and Dawn in Flowery Branch, GA. They've offered to gift it to us.
- The build: ~$600k, hoping to build in 2027. Funded by ~$200k from selling our current home plus a family loan of ~$400k. Floor plans, main-house square footage, and construction details are NOT part of the pitch; what the home means for our family is, including the sports barn described below.
- Today: our mortgage is ~$1,000/month (principal and interest) at ~2.5%. Selling to build means giving up that rate. This is the baseline for the payment comparison.
- The "why": at today's bank rates, our payment would jump far beyond what we pay now, and the build doesn't work. A family rate closes most of that gap.
- Rate: around 3%. Present it as "a rate below market," with 3% as the example for the math. Never present 3% as fixed or final.
- Relationship: Steve and Dawn have helped before, never at this scale. They're willing to help but haven't heard this specific ask. This is help, not an investment for them. They could earn more elsewhere. Their win is family across the street.
- Our commitments: a written loan agreement, recorded against the home like a bank mortgage, with payments made through an independent loan servicer. We pay every cost of setting it up. Because the rate is below the IRS minimum rate for family loans, they may owe a small amount of tax on interest they don't actually receive; we will cover that tax every year.
- Siblings: Amber has siblings. If the loan isn't fully repaid by the time of inheritance, the unpaid balance comes out of Amber's share. This lives ONLY in the deck appendix, not in the video or main slides.

## What this home would mean for us
These are the heart of the pitch. Use them, and expand on them where it's natural, but don't invent specific facts (no made-up features, events, or details about the house beyond these):
- Building our dream home, the one we'd raise our boys in.
- Land and space for Lucas, Owen, and Wyatt to play outside and just be boys.
- Living right next to family: Papa and Grandee part of everyday life, not just holidays.
- A sports barn: its own building, attached to the main house, with about 1,000-1,500 sq ft of open space for the boys to play. Think a basketball hoop, a soccer goal, a climbing wall, a jungle gym, plus room for a home gym for Matteo. A place for the boys (and the whole family, Papa and Grandee included) to play year-round, rain or shine.
- Reasonable extensions are welcome when they follow from the above, for example room for a growing family of five, a place for family gatherings, grandparents close enough to share the small everyday moments. Keep them general and true to the spirit; never state specifics I haven't given.

## Tone
- Warm, grateful, plain English, respectful of a big request. No financial-win framing for them. Say "fully secured," never "guaranteed." No em or en dashes anywhere. Say "the home we're hoping to build," not "when we move in," so "not yet" is easy for them to say. Show honestly that our payment still rises even at the family rate.
- No jargon: no "AFR," "security deed," "Form 709," "imputed interest," or "amortization" on screen or in narration; use plain equivalents. Mention "we'll confirm the details with an attorney and CPA" once, not on every slide.

## Numbers (keep it to what the ask needs)
- Look up: the current Freddie Mac 30-year mortgage rate (and a current construction-loan rate if it's notably higher), and the current IRS long-term AFR (semiannual-compounding column, IRC 7872(f)(2)(A)) for the tax estimate only. Cite each with its date in a sources note in the deck appendix.
- Compute in code into ONE figures.json that the video and deck both read:
  - At ~$400k over 30 years: monthly payment at market vs ~3%; change vs today's ~$1,000; total interest at market vs ~3%; the difference.
  - Their estimated extra tax each year from the below-market rate (interest at the AFR minus interest at ~3%, times an assumed 30% tax rate), which we cover. One rounded number, labeled an estimate.
- Sanity check: at 3% over 30 years, $400k = $1,686.42/mo, total interest $207,110.

## Part 1: Narrated video (older viewers on a TV)
Length: as long as it needs to be to deliver the message well, and no longer. Quality governs, not runtime. Every scene must earn its time; cut anything that repeats or drags. Pace narration at about 130-140 words per minute.

Scenes (in order):
1. Across the street: the land across from Papa and Grandee; picture Lucas, Owen, and Wyatt growing up right there.
2. What this home would mean: the dream home, room for the boys to run and be boys, the sports barn (hoop, soccer goal, climbing wall, jungle gym, home gym) where the whole family can play year-round, Papa and Grandee part of everyday life.
3. Thank you: gratitude for the land and everything they've done; acknowledging this is a big ask, which is why we came with a careful plan.
4. The plan: one simple visual: ~$600k home = ~$200k from selling our current home + a ~$400k family loan.
5. Why we need help: three cards: today ~$1,000/mo; a bank loan at $[X]/mo; a family rate (~3%) at $[Z]/mo. Then one card: total interest at bank rates vs ~3%, worded as "the gap a family rate closes," never "savings."
6. What we're asking: a 30-year family loan of ~$400k at a rate below market (~3% as the example); not a gift; we pay every month; they could earn more elsewhere, so this is help, not an investment.
7. Done properly: written agreement, recorded against the home like a bank mortgage, payments through an independent servicer so there are always clear records, and we cover every cost and the extra tax.
8. Let's talk: return to the opening image; "No answer needed tonight. We'd love your questions." Hold on the card; the next key or click enters the deck.

[X] and [Z] are computed values from figures.json.

Stage and style:
- Fixed 1920x1080 stage scaled to fit with letterboxing. Light warm background (#FAF8F4), dark text (#1F2A30), one warm accent. Force light mode: color-scheme: light, no dark variant, ignore the device's dark-mode setting.
- Large type for a TV (headings 64px+, key numbers 110px+). Max 12 words on screen per beat; each beat holds 6+ seconds.
- Imagery: warm, simple flat illustrations (land across a quiet street, kids playing outside, a barn attached to the house with a hoop, soccer goal, and climbing wall inside, a family table) and big-number cards. No photos, no AI-generated realistic people.
- Gentle crossfades and slow subtle motion. No flying or bouncing text. Narration only, no music. Short captions synced to narration.

Narration:
- One warm, clear ElevenLabs narrator voice in third person ("Matteo and Amber hope to..."), never speaking as us.
- creative_list_voices, pick 2 candidates, run creative_generate_speech with estimate_only and report the cost. With my OK, generate one short test clip per candidate (generations_count=1). I pick. Generate the full set, one clip per scene, generations_count=1.
- Download every clip immediately and embed it in the page. Never reference ElevenLabs URLs; they expire.

Mechanics:
- Start screen with a "Begin" button (needed for browser autoplay). Each scene advances shortly after its audio ends, with beats timed to the real clip length. Space pauses; arrows replay or skip a scene.

## Part 2: Discussion deck (short, presenter-advanced)
Main slides:
1. The ask, in one view: ~$400k, 30 years, a rate below market (~3% example), monthly payment.
2. Bank rate vs family rate side by side: monthly payment, change vs today, total interest.
3. Interactive: sliders for loan amount ($300-450k, default $400k) and rate (2.5% to market), showing our monthly payment and the difference vs a bank loan.
4. Done properly: the written agreement, recorded like a bank mortgage, independent servicer, we pay all costs and the extra tax.
5. What we're asking of you, and next steps: time to think it over, questions, then we bring in an attorney and CPA.

Appendix (only if the conversation goes there): fairness to Amber's siblings (the inheritance offset); sources for the rates.

- Short plain-English speaker notes on every slide, split between Matteo and Amber.
- Presenter tools: N opens a synced notes window on the laptop; arrow keys and clickers advance; A jumps to the appendix.

## Delivery
One self-contained HTML page: video, then deck. Published as a shareable artifact, plus a downloadable offline .html that runs with no internet.

## Time budget and phases
- 90 minutes of working time total, not counting time waiting on my approvals. The budget caps iteration; it isn't a reason to rush. Use it to make the content as good as possible, including self-critique and revision passes.
- Phase A (content): look up rates, figures.json, full narration script, storyboard, speaker notes, voice test clips (only with my OK), and a self-review pass for clarity, warmth, and anything that sounds like a sales pitch. STOP for my approval.
- Phase B (build): full narration, video, deck, QA, a final polish pass, delivery.

## Completion checks
1. I approved the Phase A script, storyboard, notes, and voice.
2. Every figure traces to figures.json; the sliders recompute correctly.
3. Layout checked at laptop and TV sizes with no overflow (screenshots if a headless browser is available; otherwise a built-in self-test on load, with results reported to me).
4. Text search finds no em or en dashes, no "guarantee," and none of the banned jargon terms in the video or main slides; the sibling topic appears only in the appendix; nothing about the home is stated beyond what this brief gives.
5. Every audio clip is embedded and plays; the offline .html has no external references.
6. I approve the final version.
