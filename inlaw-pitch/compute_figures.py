"""Compute every number the video and deck use. Output: figures.json (single source of truth)."""
import json, datetime

# Inputs (cited in figures.json)
LOAN = 400_000
YEARS = 30
N = YEARS * 12
TODAY_PAYMENT = 1000          # current P&I, ~2.5%
FAMILY_RATE = 0.03            # example rate, "a rate below market"
MARKET_RATE = 0.0740          # Freddie Mac PMMS 30-yr FRM, survey of 2026-10-15
MARKET_DATE = "2026-10-15"
AFR_LONG_TERM_SEMIANNUAL = 0.0515  # Rev. Rul. 2026-19, October 2026, long-term, semiannual compounding
AFR_SOURCE = "IRS Rev. Rul. 2026-19 (October 2026), Table 1, long-term AFR, semiannual column"
TAX_RATE = 0.30               # assumed combined rate for the estimate
HOME_COST = 600_000
HOME_SALE = 200_000
CONSTRUCTION_RANGE = "about 7% to 9%"  # residential construction loans, typical 2026 quotes (secondary sources)

def payment(principal, rate, n):
    r = rate / 12
    return principal * r / (1 - (1 + r) ** -n)

def first_year_interest(principal, rate, n):
    """Interest paid in the first 12 payments (used for the tax estimate)."""
    r = rate / 12
    pmt = payment(principal, rate, n)
    bal = principal
    total = 0.0
    for _ in range(12):
        i = bal * r
        total += i
        bal -= (pmt - i)
    return total

pm_market = payment(LOAN, MARKET_RATE, N)
pm_family = payment(LOAN, FAMILY_RATE, N)
ti_market = pm_market * N - LOAN
ti_family = pm_family * N - LOAN

# Sanity check from the brief
assert abs(pm_family - 1686.42) < 0.01, pm_family
assert abs(round(ti_family) - 207110) <= 1, ti_family

# Tax estimate: interest at AFR minus interest at family rate, first year, times 30%.
# Interest at AFR on the same declining balance is approximated as the year-1 interest
# if the loan carried the AFR (the IRS "foregone interest" concept, plain-English in the pitch).
int_afr_y1 = first_year_interest(LOAN, AFR_LONG_TERM_SEMIANNUAL, N)
int_fam_y1 = first_year_interest(LOAN, FAMILY_RATE, N)
# Simpler, conservative alternative: (AFR - family) * balance. Year-1 average balance ~ LOAN.
foregone_simple = (AFR_LONG_TERM_SEMIANNUAL - FAMILY_RATE) * LOAN
extra_tax_simple = foregone_simple * TAX_RATE
extra_tax_amort = (int_afr_y1 - int_fam_y1) * TAX_RATE
extra_tax_rounded = int(round(extra_tax_simple / 100.0) * 100)

int_fam_received_y1 = first_year_interest(LOAN, FAMILY_RATE, N)
GIFT_EXCLUSION = 19_000   # annual gift tax exclusion per giver per recipient; verified for 2026 before use
fig = {
    "generated": datetime.date.today().isoformat(),
    "inputs": {
        "loan_amount": LOAN,
        "term_years": YEARS,
        "home_cost": HOME_COST,
        "from_home_sale": HOME_SALE,
        "today_payment": TODAY_PAYMENT,
        "today_rate": 0.025,
        "family_rate_example": FAMILY_RATE,
        "market_rate": MARKET_RATE,
        "market_rate_source": "Freddie Mac Primary Mortgage Market Survey, 30-year fixed, week of " + MARKET_DATE,
        "market_rate_url": "https://www.freddiemac.com/pmms",
        "construction_loan_rate_note": "Residential construction loans were quoted at " + CONSTRUCTION_RANGE + " in October 2026 (secondary sources); the 30-year rate above is used for the comparison.",
        "afr_long_term_semiannual": AFR_LONG_TERM_SEMIANNUAL,
        "afr_source": AFR_SOURCE,
        "afr_url": "https://www.irs.gov/pub/irs-drop/rr-26-19.pdf",
        "gift_exclusion_source": "IRS Rev. Proc. 2025-32, annual gift tax exclusion for 2026, $19,000 per giver per recipient",
        "assumed_tax_rate": TAX_RATE
    },
    "monthly_payment_market": round(pm_market, 2),
    "monthly_payment_family": round(pm_family, 2),
    "change_vs_today_market": round(pm_market - TODAY_PAYMENT, 2),
    "change_vs_today_family": round(pm_family - TODAY_PAYMENT, 2),
    "total_interest_market": round(ti_market),
    "total_interest_family": round(ti_family),
    "interest_gap": round(ti_market - ti_family),
    "extra_tax_estimate_per_year": extra_tax_rounded,
    "foregone_interest_year1": int(round(foregone_simple / 100.0) * 100),
    "interest_received_year1_family": int(round(int_fam_received_y1 / 100.0) * 100),
    "gift_exclusion_per_person": GIFT_EXCLUSION,
    "gift_room_two_givers_two_recipients": GIFT_EXCLUSION * 4,
    "extra_tax_detail": {
        "foregone_interest_year1_simple": round(foregone_simple),
        "extra_tax_simple": round(extra_tax_simple),
        "extra_tax_amortized_year1": round(extra_tax_amort),
        "note": "Estimate. Interest at the IRS minimum family-loan rate minus interest at the example rate, times an assumed 30% tax rate. Year one is the highest; it shrinks as the balance falls."
    },
    "display": {
        "market_rate_pct": f"{MARKET_RATE*100:.2f}%",
        "family_rate_pct": "3%",
        "monthly_market": f"${pm_market:,.0f}",
        "monthly_family": f"${pm_family:,.0f}",
        "monthly_today": f"${TODAY_PAYMENT:,.0f}",
        "change_market": f"+${pm_market-TODAY_PAYMENT:,.0f}",
        "change_family": f"+${pm_family-TODAY_PAYMENT:,.0f}",
        "total_interest_market": f"${ti_market:,.0f}",
        "total_interest_family": f"${ti_family:,.0f}",
        "interest_gap": f"${ti_market-ti_family:,.0f}",
        "extra_tax": f"${extra_tax_rounded:,.0f}",
        "afr_pct": f"{AFR_LONG_TERM_SEMIANNUAL*100:.2f}%",
        "foregone_interest": f"${round(foregone_simple/100.0)*100:,.0f}",
        "interest_received_y1": f"${round(int_fam_received_y1/100.0)*100:,.0f}",
        "gift_exclusion": f"${GIFT_EXCLUSION:,.0f}",
        "gift_room": f"${GIFT_EXCLUSION*4:,.0f}",
        "total_interest_market_rounded": f"${round(ti_market/1000)*1000:,.0f}",
        "total_interest_family_rounded": f"${round(ti_family/1000)*1000:,.0f}",
        "interest_gap_rounded": f"${round((ti_market-ti_family)/1000)*1000:,.0f}",
        "home_cost_k": "$600k", "from_home_sale_k": "$200k", "loan_amount_k": "$400k", "market_date": "October 15, 2026"
    }
}
json.dump(fig, open("figures.json", "w"), indent=2)
print(json.dumps(fig["display"], indent=2))
print("extra tax simple:", round(extra_tax_simple), " amortized y1:", round(extra_tax_amort))
