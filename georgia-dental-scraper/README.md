# Georgia Dental Practice Sourcing

A one-time script that pulls **general and family dental practices in Georgia**
from the **Google Places API (NEW)** and writes them to a CSV for outreach.

It queries each Georgia location twice (`general dentist in ... , GA` and
`family dentist in ... , GA`), removes duplicate practices, adds two "likely
DSO" / "likely specialty-only" flag columns, and prints a summary that
**includes the total number of API calls** so you can confirm you stayed inside
the free monthly allowance.

---

## What you get

- `georgia_dental_scraper.py` — the script
- `requirements.txt` — the one dependency it needs
- `georgia_dental_practices.csv` — created when you run it (the output)

---

## Before you run anything: Google Cloud setup (do this once)

You need a Google Cloud project with a billing account and an API key. **Cost
guardrails matter here**, so follow all of these:

1. Go to <https://console.cloud.google.com/> and create (or pick) a project.
2. **Enable billing** on the project. (Google requires a billing account even
   for the free tier. You will not be charged as long as you set the quota cap
   in step 5.)
3. **Enable the "Places API (New)"** — search for it in
   *APIs & Services → Library*. Enable the one that says **(New)**; do **not**
   rely on the old/legacy "Places API". This script only calls the new one.
4. **Create an API key**: *APIs & Services → Credentials → Create credentials →
   API key*. Copy the key somewhere safe.
5. **Restrict the key** (important):
   - Under *API restrictions*, restrict it to **Places API (New)** only.
   - Optionally add an *Application restriction* (e.g. IP address) if you know
     the machine you'll run from.
6. **Set a quota cap BELOW the free monthly limit** so you *cannot* be charged:
   - Go to *APIs & Services → Places API (New) → Quotas*.
   - The relevant **Text Search** SKU includes a few **thousand** free calls per
     month. Set a daily/monthly request cap comfortably **below** that number
     (for example, a daily cap of 100–200 requests is plenty for this project).
   - With a hard cap below the free allowance, worst case the script stops
     making calls — it can't run up a bill.

> This script never hardcodes your key. It reads it from an environment
> variable, so your key does not end up saved in the code or the CSV.

---

## Running the script (step by step)

These instructions assume macOS or Linux. Windows notes are in parentheses.
You need **Python 3.8+** installed (`python3 --version` to check).

### Step 1 — Open a terminal in this folder

```bash
cd path/to/georgia-dental-scraper
```

### Step 2 — Install the one dependency

```bash
python3 -m pip install -r requirements.txt
```

(This installs `requests`, the library used to talk to Google's API.)

### Step 3 — Put your API key into an environment variable

```bash
export GOOGLE_MAPS_API_KEY='paste-your-key-here'
```

- On **Windows** (Command Prompt), use: `set GOOGLE_MAPS_API_KEY=paste-your-key-here`
  (or `setx ...` and open a new terminal to persist it).
- This only lasts for the current terminal window. If you close it, run the
  `export` line again.

### Step 4 — Do a small test run first (50 records)

```bash
python3 georgia_dental_scraper.py --limit 50
```

This stops after collecting 50 unique practices. Use it to confirm your key
works and the output looks right **before** spending more of your free calls.
Open `georgia_dental_practices.csv` (in Excel/Google Sheets) and check it.

### Step 5 — Do the full run

```bash
python3 georgia_dental_scraper.py
```

The script prints an **estimated API call count** and asks you to type `yes`
before it starts the full pull. When it finishes, it prints a summary like:

```
Total unique practices:       412
  flagged likely_DSO:         37
  flagged likely_specialty:   58
Total API calls made:         84
Output written to:            georgia_dental_practices.csv
```

Check that **"Total API calls made"** is within your free monthly allowance.

> To run the full pull without the typed confirmation (e.g. in an automated
> setting), add `--yes`.

---

## Editing what it searches

Open `georgia_dental_scraper.py` and edit the lists near the top — they are
clearly labeled with numbered comments:

- **`GEORGIA_LOCATIONS`** — the cities/ZIPs to search. Add or remove freely.
  *Every location you add increases the number of API calls (and cost).*
- **`QUERY_TEMPLATES`** — the two search phrases run per location.
- **`KNOWN_DSO_CHAINS`** — chain names that trigger the `likely_DSO` flag. A
  starter list is included (Aspen Dental, Heartland Dental, Pacific Dental
  Services, Western Dental, Sage Dental, Great Expressions, and more). Add any
  others you come across.

---

## The two flag columns (heuristics — review, don't blindly trust)

- **`likely_DSO`** — `True` when the practice name matches a known corporate
  chain (a Dental Service Organization) from `KNOWN_DSO_CHAINS`.
- **`likely_specialty_only`** — `True` when the name or Google "types" point to
  oral surgery, endodontics, orthodontics, periodontics (etc.) **and** there's
  no sign of general/family dentistry. Google's dental "types" are coarse — most
  practices just come back as `dentist` — so this leans mostly on the name.
  Treat it as a "look closer" hint, not a final answer.

---

## Cost guardrails built into the script

- **Field masking**: it requests only the specific fields you asked for. The
  field mask controls which billing SKU tier applies and keeps each call on the
  cheaper tier.
- **Call counting**: it tallies and prints every API call so you can verify you
  stayed inside the free allowance.
- **Estimate + confirmation**: before a full run it prints an estimated call
  count and waits for you to type `yes`.
- **Delays and retries**: it waits briefly between calls, waits the required
  short delay before requesting the next page of results, and retries transient
  network/server errors with exponential backoff (2s, 4s, 8s, 16s).

The single most important guardrail is on Google's side: **set the quota cap
below your free monthly limit** (setup step 6). That's what makes it impossible
to be charged.

---

## A note on completeness

Google's Places Text Search returns up to ~60 results per query (three pages of
~20). For very dense metros there may be more general/family dentists than that;
the per-city breakdown here is a strong starting list for outreach, not a
guaranteed 100% census. If you need deeper coverage in one city, add more
specific locations (e.g. individual ZIP codes within that city) to
`GEORGIA_LOCATIONS`.
