#!/usr/bin/env python3
"""
Georgia Dental Practice Sourcing Script
=======================================

A one-time data-sourcing tool that pulls general and family dental practices in
Georgia from the Google Places API (NEW) Text Search endpoint, for an outreach
project.

It:
  * Uses ONLY the new Places API (POST .../v1/places:searchText) with a field
    mask so you are billed on the cheapest SKU tier that still returns the
    fields you need.
  * Reads your API key from the environment variable GOOGLE_MAPS_API_KEY.
  * Loops over a list of Georgia locations you can edit at the top of this file.
  * Handles pagination, dedupes by place id, adds two heuristic flag columns,
    writes a CSV, and prints a summary including the total number of API calls.

Read the README.md next to this file first if you are not a coder -- it walks
you through setup and running, step by step.
"""

import argparse
import csv
import os
import sys
import time
from typing import Dict, List, Optional

import requests

# ---------------------------------------------------------------------------
# 1. LOCATIONS TO SEARCH  (edit this list freely)
# ---------------------------------------------------------------------------
# Each entry becomes part of a search string like:
#   "general dentist in Atlanta, GA"
#   "family dentist in Atlanta, GA"
# You can use city names or ZIP codes. Keep the list focused: every location
# adds API calls (and therefore cost). See the cost note in the README.
GEORGIA_LOCATIONS: List[str] = [
    "Atlanta",
    "Augusta",
    "Columbus",
    "Macon",
    "Savannah",
    "Athens",
    "Sandy Springs",
    "Roswell",
    "Johns Creek",
    "Albany",
    "Warner Robins",
    "Alpharetta",
    "Marietta",
    "Valdosta",
    "Smyrna",
]

# The two query templates run for each location. {loc} is filled in per location.
QUERY_TEMPLATES: List[str] = [
    "general dentist in {loc}, GA",
    "family dentist in {loc}, GA",
]

# ---------------------------------------------------------------------------
# 2. DSO / CHAIN DETECTION  (extend this list any time)
# ---------------------------------------------------------------------------
# If a practice's displayName contains one of these phrases (case-insensitive),
# we flag likely_DSO = True. DSO = Dental Service Organization (a corporate
# chain rather than an independent practice). Add more names as you find them.
KNOWN_DSO_CHAINS: List[str] = [
    "Aspen Dental",
    "Heartland Dental",
    "Pacific Dental",          # Pacific Dental Services
    "Western Dental",
    "Sage Dental",
    "Great Expressions",
    "Gentle Dental",
    "Comfort Dental",
    "Dental Care Alliance",
    "Affordable Dentures",
    "Coast Dental",
    "Smile Brands",
    "Bright Now",              # Bright Now! Dental
    "Midwest Dental",
    "North American Dental",
    "Dental Depot",
    "ClearChoice",
    "Kool Smiles",
    "DECA Dental",
    "MB2 Dental",
    "Risas Dental",
    "SmileDirectClub",
]

# ---------------------------------------------------------------------------
# 3. SPECIALTY-ONLY DETECTION
# ---------------------------------------------------------------------------
# We flag likely_specialty_only = True when the Google place types OR the name
# point to a specialty practice (oral surgery, endodontics, orthodontics,
# periodontics) AND there is no signal of general dentistry.
#
# Google's place "types" for dental businesses are fairly coarse -- most return
# just "dentist" / "doctor" -- so this is a best-effort heuristic based mostly
# on the practice name. Treat the flag as a hint to review, not gospel.
SPECIALTY_NAME_KEYWORDS: List[str] = [
    "oral surgery",
    "oral surgeon",
    "maxillofacial",
    "endodontic",
    "endodontist",
    "root canal specialist",
    "orthodontic",
    "orthodontist",
    "braces",
    "periodontic",
    "periodontist",
    "prosthodontic",
    "prosthodontist",
    "pediatric dentist",   # kids-only; not general/family
    "pediatric dentistry",
    "children's dentistry",
]

# Google place types that indicate a specialty rather than general dentistry.
SPECIALTY_TYPE_KEYWORDS: List[str] = [
    "orthodontist",
    "oral_surgeon",
    "endodontist",
    "periodontist",
    "dental_specialist",
]

# Signals that general dentistry IS offered (so we should NOT flag specialty-only).
GENERAL_DENTISTRY_KEYWORDS: List[str] = [
    "general dentist",
    "family dentist",
    "general dentistry",
    "family dentistry",
    "general & cosmetic",
    "cosmetic and general",
    "comprehensive dental",
]

# ---------------------------------------------------------------------------
# 4. API + BEHAVIOR SETTINGS
# ---------------------------------------------------------------------------
PLACES_ENDPOINT = "https://places.googleapis.com/v1/places:searchText"

# Field mask: ONLY the fields we need. This controls the billing SKU tier and
# keeps cost down. nextPageToken is required for pagination.
FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.nationalPhoneNumber",
    "places.websiteUri",
    "places.rating",
    "places.userRatingCount",
    "places.businessStatus",
    "places.primaryTypeDisplayName",
    "places.types",
    "places.location",
    "nextPageToken",
])

# CSV columns, in order.
CSV_FIELDS: List[str] = [
    "place_id",
    "name",
    "formatted_address",
    "national_phone",
    "website",
    "rating",
    "user_rating_count",
    "business_status",
    "primary_type",
    "types",
    "latitude",
    "longitude",
    "source_query",
    "likely_DSO",
    "likely_specialty_only",
]

OUTPUT_CSV = "georgia_dental_practices.csv"

DELAY_BETWEEN_CALLS = 1.0        # polite delay between API calls (seconds)
NEXT_PAGE_TOKEN_DELAY = 2.0      # Google needs a short delay before a page token is valid
MAX_RETRIES = 4                  # retry attempts on transient failures
BACKOFF_BASE = 2.0               # exponential backoff base (2s, 4s, 8s, 16s)


# ---------------------------------------------------------------------------
# Heuristic helpers
# ---------------------------------------------------------------------------
def is_likely_dso(name: str) -> bool:
    """True if the practice name matches a known corporate chain."""
    lowered = name.lower()
    return any(chain.lower() in lowered for chain in KNOWN_DSO_CHAINS)


def is_likely_specialty_only(name: str, types: List[str]) -> bool:
    """
    True if the name/types indicate a specialty practice (oral surgery,
    endodontics, orthodontics, periodontics, etc.) with no sign of general
    dentistry.
    """
    lowered_name = name.lower()
    lowered_types = [t.lower() for t in types]

    # If there's an explicit general/family signal, it's not specialty-only.
    if any(kw in lowered_name for kw in GENERAL_DENTISTRY_KEYWORDS):
        return False

    name_hit = any(kw in lowered_name for kw in SPECIALTY_NAME_KEYWORDS)
    type_hit = any(kw in lowered_types for kw in SPECIALTY_TYPE_KEYWORDS)
    return name_hit or type_hit


# ---------------------------------------------------------------------------
# API call with retry / backoff
# ---------------------------------------------------------------------------
def call_places_api(
    api_key: str,
    text_query: str,
    page_token: Optional[str] = None,
) -> Dict:
    """
    Make one POST request to the Places API (NEW) Text Search endpoint.

    Returns the parsed JSON response. Raises RuntimeError if all retries fail.
    """
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
    }
    body: Dict[str, object] = {"textQuery": text_query}
    if page_token:
        body["pageToken"] = page_token

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(
                PLACES_ENDPOINT, headers=headers, json=body, timeout=30
            )
        except requests.RequestException as exc:
            last_error = f"network error: {exc}"
        else:
            if response.status_code == 200:
                return response.json()

            # 429 (rate limit) and 5xx (server) are worth retrying; others aren't.
            if response.status_code == 429 or 500 <= response.status_code < 600:
                last_error = f"HTTP {response.status_code}: {response.text[:300]}"
            else:
                # Non-retryable (bad key, bad request, API not enabled, etc.).
                raise RuntimeError(
                    f"Request failed (HTTP {response.status_code}) and will not be "
                    f"retried. Response:\n{response.text[:600]}"
                )

        if attempt < MAX_RETRIES:
            wait = BACKOFF_BASE ** attempt  # 2, 4, 8, 16 ...
            print(f"    ! {last_error} -- retrying in {wait:.0f}s "
                  f"(attempt {attempt}/{MAX_RETRIES - 1})", file=sys.stderr)
            time.sleep(wait)

    raise RuntimeError(f"All retries exhausted for query '{text_query}'. "
                       f"Last error: {last_error}")


# ---------------------------------------------------------------------------
# Result parsing
# ---------------------------------------------------------------------------
def parse_place(place: Dict, source_query: str) -> Dict:
    """Turn one raw place object from the API into a flat CSV row dict."""
    name = (place.get("displayName") or {}).get("text", "") or ""
    types = place.get("types", []) or []
    location = place.get("location") or {}

    return {
        "place_id": place.get("id", ""),
        "name": name,
        "formatted_address": place.get("formattedAddress", "") or "",
        "national_phone": place.get("nationalPhoneNumber", "") or "",
        "website": place.get("websiteUri", "") or "",
        "rating": place.get("rating", "") if place.get("rating") is not None else "",
        "user_rating_count": place.get("userRatingCount", "")
        if place.get("userRatingCount") is not None else "",
        "business_status": place.get("businessStatus", "") or "",
        "primary_type": (place.get("primaryTypeDisplayName") or {}).get("text", "") or "",
        "types": "; ".join(types),
        "latitude": location.get("latitude", ""),
        "longitude": location.get("longitude", ""),
        "source_query": source_query,
        "likely_DSO": is_likely_dso(name),
        "likely_specialty_only": is_likely_specialty_only(name, types),
    }


# ---------------------------------------------------------------------------
# Query runner (handles pagination for a single text query)
# ---------------------------------------------------------------------------
def run_query(
    api_key: str,
    text_query: str,
    results: Dict[str, Dict],
    limit: Optional[int],
    stats: Dict[str, int],
) -> None:
    """
    Run one text query, following nextPageToken through all pages.
    New (deduped) places are added to `results` keyed by place id.
    `stats['api_calls']` is incremented for every API call made.
    Stops early if `limit` unique results have been collected overall.
    """
    page_token = None
    page_num = 1
    while True:
        if limit is not None and len(results) >= limit:
            return

        print(f"  -> '{text_query}' (page {page_num})")
        data = call_places_api(api_key, text_query, page_token)
        stats["api_calls"] += 1

        for place in data.get("places", []):
            place_id = place.get("id")
            if not place_id or place_id in results:
                continue
            results[place_id] = parse_place(place, text_query)
            if limit is not None and len(results) >= limit:
                print(f"    reached --limit of {limit}; stopping early.")
                return

        page_token = data.get("nextPageToken")
        if not page_token:
            return  # no more pages

        page_num += 1
        # Google requires a short delay before a nextPageToken becomes valid.
        time.sleep(NEXT_PAGE_TOKEN_DELAY)
        # Also a small polite delay between calls generally.
        time.sleep(DELAY_BETWEEN_CALLS)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def build_query_list() -> List[str]:
    """All (template x location) query strings we intend to run."""
    queries = []
    for loc in GEORGIA_LOCATIONS:
        for template in QUERY_TEMPLATES:
            queries.append(template.format(loc=loc))
    return queries


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pull GA general/family dental practices from Google Places API (NEW)."
    )
    parser.add_argument(
        "--limit", type=int, default=None, metavar="N",
        help="Stop after collecting N unique practices (for a small test run, "
             "e.g. --limit 50). Omit for the full pull.",
    )
    parser.add_argument(
        "--yes", action="store_true",
        help="Skip the confirmation prompt before a full run (non-interactive).",
    )
    args = parser.parse_args()

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("ERROR: environment variable GOOGLE_MAPS_API_KEY is not set.\n"
              "Set it first, e.g.:\n"
              "    export GOOGLE_MAPS_API_KEY='your-key-here'   (macOS/Linux)\n"
              "    setx GOOGLE_MAPS_API_KEY \"your-key-here\"      (Windows, new terminal)\n",
              file=sys.stderr)
        return 1

    queries = build_query_list()

    # ---- Cost estimate + confirmation -------------------------------------
    # Each query is at least 1 API call. With pagination it can be up to 3
    # (Text Search returns up to ~60 results across 3 pages of 20). So the true
    # call count lands between len(queries) and len(queries) * 3.
    min_calls = len(queries)
    max_calls = len(queries) * 3
    print("=" * 68)
    print("Georgia Dental Practice Sourcing -- Google Places API (NEW)")
    print("=" * 68)
    print(f"Locations:            {len(GEORGIA_LOCATIONS)}")
    print(f"Queries per location: {len(QUERY_TEMPLATES)}")
    print(f"Total queries:        {len(queries)}")
    print(f"Estimated API calls:  {min_calls} (min) to {max_calls} (max, with pagination)")
    if args.limit is not None:
        print(f"Mode:                 TEST RUN, stopping at {args.limit} unique practices")
    else:
        print("Mode:                 FULL RUN")
    print("-" * 68)
    print("Reminder: the relevant Text Search SKU includes a few thousand free "
          "calls\nper month. Keep a quota cap set BELOW that limit in Google "
          "Cloud so you\ncannot be charged. See README.md.")
    print("=" * 68)

    if args.limit is None and not args.yes:
        try:
            answer = input("Proceed with the FULL run? Type 'yes' to continue: ").strip().lower()
        except EOFError:
            answer = ""
        if answer != "yes":
            print("Aborted. (Tip: use --limit 50 for a small test run first.)")
            return 0

    # ---- Run --------------------------------------------------------------
    results: Dict[str, Dict] = {}
    stats: Dict[str, int] = {"api_calls": 0}

    print("\nStarting queries...\n")
    try:
        for text_query in queries:
            if args.limit is not None and len(results) >= args.limit:
                print(f"Reached --limit of {args.limit}; skipping remaining queries.")
                break
            run_query(api_key, text_query, results, args.limit, stats)
            time.sleep(DELAY_BETWEEN_CALLS)
    except RuntimeError as exc:
        print(f"\nERROR during API calls: {exc}", file=sys.stderr)
        print("Writing whatever was collected so far before exiting...", file=sys.stderr)

    # ---- Write CSV --------------------------------------------------------
    rows = list(results.values())
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    # ---- Summary ----------------------------------------------------------
    dso_count = sum(1 for r in rows if r["likely_DSO"])
    specialty_count = sum(1 for r in rows if r["likely_specialty_only"])

    print("\n" + "=" * 68)
    print("SUMMARY")
    print("=" * 68)
    print(f"Total unique practices:       {len(rows)}")
    print(f"  flagged likely_DSO:         {dso_count}")
    print(f"  flagged likely_specialty:   {specialty_count}")
    print(f"Total API calls made:         {stats['api_calls']}")
    print(f"Output written to:            {OUTPUT_CSV}")
    print("=" * 68)
    print("Confirm 'Total API calls made' is within your free monthly allowance.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
