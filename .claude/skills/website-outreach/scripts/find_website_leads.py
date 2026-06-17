#!/usr/bin/env python3
"""
Website Lead Generation Pipeline

Finds local businesses with no website or weak/free-builder websites for cold outreach.

Two modes:
  no-website    — businesses with no website listed on Google Maps (pre-filtered by Apify)
  weak-website  — businesses whose website is a free builder or directory profile

Usage:
    # Find businesses with no website across multiple niches
    python3 .claude/skills/website-outreach/scripts/find_website_leads.py \
        --mode no-website \
        --searches "roofers in Birmingham" "hair salons in Birmingham" "plumbers in Birmingham" \
        --limit 50

    # Find businesses with weak/free-builder websites
    python3 .claude/skills/website-outreach/scripts/find_website_leads.py \
        --mode weak-website \
        --searches "electricians in Birmingham" "gyms in Birmingham" \
        --limit 100 \
        --sheet-url "https://docs.google.com/spreadsheets/d/..."
"""

import os
import re
import sys
import json
import argparse
import hashlib
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

from apify_client import ApifyClient
import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

load_dotenv()

ACTOR_ID = "compass/crawler-google-places"
MIN_REVIEWS = 5

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

DEFAULT_SHEET_NAME = "Website Leads"

LEAD_COLUMNS = [
    "lead_id",
    "scraped_at",
    "search_query",
    "mode",
    "business_name",
    "category",
    "city",
    "address",
    "phone",
    "website",
    "website_weakness",
    "rating",
    "review_count",
    "google_maps_url",
    "place_id",
    "outreach_status",  # left blank — fill in as you work the list
]

# URL patterns that definitively indicate a free/directory website from the URL alone
WEAK_URL_PATTERNS = [
    (r"\.wixsite\.com", "wix_free_subdomain"),
    (r"\.weebly\.com", "weebly_free_subdomain"),
    (r"\.squarespace\.com", "squarespace_free_subdomain"),
    (r"\.wordpress\.com", "wordpress_free_subdomain"),
    (r"\.godaddysites\.com", "godaddy_free"),
    (r"\.site123\.me", "site123_free"),
    (r"\.jimdo\.com", "jimdo_free"),
    (r"\.jimdosite\.com", "jimdo_free"),
    (r"\.webflow\.io", "webflow_free"),
    (r"\.framer\.website", "framer_free"),
    (r"\.cargo\.site", "cargo_free"),
    (r"\.strikingly\.com", "strikingly_free"),
    (r"\.myfreesites\.net", "myfreesites_free"),
    (r"\.1and1\.co\.uk", "1and1_free"),
    (r"yell\.com/biz/", "yell_directory"),
    (r"checkatrade\.com/trades/", "checkatrade_directory"),
    (r"^https?://(www\.)?facebook\.com/", "facebook_page_only"),
    (r"ratedpeople\.com", "ratedpeople_profile"),
    (r"mybuilder\.com", "mybuilder_profile"),
    (r"trustatrader\.com", "trustatrader_profile"),
    (r"houzz\.co\.uk", "houzz_profile"),
]

# UK city coordinates for geolocation accuracy in Apify scrape
UK_CITIES = {
    "london": {"lat": 51.5074, "lng": -0.1278},
    "manchester": {"lat": 53.4808, "lng": -2.2426},
    "birmingham": {"lat": 52.4862, "lng": -1.8904},
    "leeds": {"lat": 53.8008, "lng": -1.5491},
    "liverpool": {"lat": 53.4084, "lng": -2.9916},
    "bristol": {"lat": 51.4545, "lng": -2.5879},
    "sheffield": {"lat": 53.3811, "lng": -1.4701},
    "newcastle": {"lat": 54.9783, "lng": -1.6178},
    "coventry": {"lat": 52.4068, "lng": -1.5197},
    "nottingham": {"lat": 52.9548, "lng": -1.1581},
    "sutton coldfield": {"lat": 52.5654, "lng": -1.8221},
    "solihull": {"lat": 52.4131, "lng": -1.7779},
    "walsall": {"lat": 52.5862, "lng": -1.9826},
    "wolverhampton": {"lat": 52.5861, "lng": -2.1281},
    "wolverhampton": {"lat": 52.5861, "lng": -2.1281},
    "west bromwich": {"lat": 52.5187, "lng": -1.9950},
    "lichfield": {"lat": 52.6836, "lng": -1.8279},
    "tamworth": {"lat": 52.6336, "lng": -1.6928},
}


# ─── Website weakness detection ───────────────────────────────────────────────

def check_url_pattern(url: str) -> tuple:
    """Fast URL string check — catches free subdomains and directory profiles."""
    for pattern, weakness in WEAK_URL_PATTERNS:
        if re.search(pattern, url, re.IGNORECASE):
            return True, weakness
    return False, ""


def check_via_head_request(url: str) -> tuple:
    """Detect Wix/Squarespace/Weebly on custom domains via HTTP response headers."""
    try:
        r = requests.head(
            url,
            timeout=4,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        )
        h = {k.lower(): v.lower() for k, v in r.headers.items()}

        if "x-wix-request-id" in h or "x-wix-meta-site-id" in h:
            return True, "wix_custom_domain"

        served_by = h.get("x-servedby", "") + h.get("server", "")
        if "squarespace" in served_by:
            return True, "squarespace_custom_domain"

        if "x-weebly-version" in h:
            return True, "weebly_custom_domain"

        if "x-godaddy-account-protection" in h:
            return True, "godaddy_custom_domain"

    except Exception:
        pass

    return False, ""


def is_weak_website(url: str) -> tuple:
    """Return (is_weak, weakness_type) for a given website URL."""
    if not url:
        return False, ""
    flagged, weakness = check_url_pattern(url)
    if flagged:
        return True, weakness
    return check_via_head_request(url)


# ─── Apify scrape ─────────────────────────────────────────────────────────────

def scrape_google_maps(search_query: str, max_results: int, mode: str) -> list:
    api_token = os.getenv("APIFY_API_TOKEN")
    if not api_token:
        print("Error: APIFY_API_TOKEN not set", file=sys.stderr)
        return []

    client = ApifyClient(api_token)

    run_input = {
        "searchStringsArray": [search_query],
        "maxCrawledPlacesPerSearch": max_results,
        "language": "en",
        "countryCode": "gb",
        "deeperCityScrape": False,
        "oneReviewPerRow": False,
    }

    # Pre-filter at Apify level — only pay for businesses without websites
    if mode == "no-website":
        run_input["website"] = "withoutWebsite"

    # Set coordinates based on city mentioned in query
    query_lower = search_query.lower()
    for city, coords in UK_CITIES.items():
        if city in query_lower:
            run_input["lat"] = str(coords["lat"])
            run_input["lng"] = str(coords["lng"])
            run_input["zoom"] = 12
            break

    print(f"  Apify scrape: '{search_query}' (limit: {max_results})...")

    try:
        run = client.actor(ACTOR_ID).call(run_input=run_input)
        if not run:
            print(f"  Error: actor run failed", file=sys.stderr)
            return []
        results = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        print(f"  → {len(results)} raw results")
        return results
    except Exception as e:
        print(f"  Error: {e}", file=sys.stderr)
        return []


# ─── Lead processing ──────────────────────────────────────────────────────────

def parse_city(address: str) -> str:
    """Extract city from a UK address string."""
    if not address:
        return ""
    uk_pc = re.search(r"\b([A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2})\b", address)
    parts = [p.strip() for p in address.split(",")]
    if uk_pc:
        for i, part in enumerate(parts):
            if uk_pc.group(1) in part and i > 0:
                return parts[i - 1].strip()
    for seg in reversed(parts):
        seg_lower = seg.strip().lower()
        if seg_lower not in ("united kingdom", "england", "scotland", "wales", "uk"):
            if not re.search(r"\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b", seg, re.I):
                return seg.strip()
    return ""


def make_lead_id(name: str, address: str) -> str:
    return hashlib.md5(f"{name}|{address}".lower().encode()).hexdigest()[:12]


def build_lead(biz: dict, search_query: str, mode: str, website: str, weakness: str) -> dict:
    address = biz.get("address", "")
    return {
        "lead_id": make_lead_id(biz.get("title", ""), address),
        "scraped_at": datetime.now().isoformat(),
        "search_query": search_query,
        "mode": mode,
        "business_name": biz.get("title", ""),
        "category": biz.get("categoryName", ""),
        "city": parse_city(address),
        "address": address,
        "phone": biz.get("phone", ""),
        "website": website,
        "website_weakness": weakness,
        "rating": str(biz.get("totalScore", "")),
        "review_count": str(int(biz.get("reviewsCount") or 0)),
        "google_maps_url": biz.get("url", ""),
        "place_id": biz.get("placeId", ""),
        "outreach_status": "",
    }


def process_no_website(businesses: list, search_query: str) -> list:
    """All results already have no website (Apify pre-filtered). Apply review gate only."""
    leads = []
    skipped = 0
    for biz in businesses:
        reviews = int(biz.get("reviewsCount") or 0)
        if reviews < MIN_REVIEWS:
            skipped += 1
            continue
        leads.append(build_lead(biz, search_query, "no-website", "", "none"))
    if skipped:
        print(f"  Skipped {skipped} businesses with <{MIN_REVIEWS} reviews")
    return leads


def process_weak_website(businesses: list, search_query: str, workers: int) -> list:
    """Filter businesses to those with free-builder or directory-profile websites."""
    candidates = [
        biz for biz in businesses
        if biz.get("website") and int(biz.get("reviewsCount") or 0) >= MIN_REVIEWS
    ]

    if not candidates:
        print(f"  No candidates with website + {MIN_REVIEWS}+ reviews")
        return []

    print(f"  Checking {len(candidates)} websites (URL pattern + HEAD request)...")

    results = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_biz = {
            executor.submit(is_weak_website, biz.get("website", "")): biz
            for biz in candidates
        }
        done = 0
        for future in as_completed(future_to_biz):
            biz = future_to_biz[future]
            done += 1
            try:
                flagged, weakness = future.result()
                results.append((biz, flagged, weakness))
                status = f"WEAK ({weakness})" if flagged else "clean"
                print(f"  [{done}/{len(candidates)}] {biz.get('title', '?')[:45]:<45} {status}")
            except Exception as e:
                results.append((biz, False, ""))
                print(f"  [{done}/{len(candidates)}] {biz.get('title', '?')[:45]:<45} error: {e}")

    leads = []
    for biz, flagged, weakness in results:
        if flagged:
            leads.append(build_lead(biz, search_query, "weak-website", biz.get("website", ""), weakness))

    print(f"  → {len(leads)} weak websites found out of {len(candidates)} checked")
    return leads


# ─── Google Sheets ────────────────────────────────────────────────────────────

def get_credentials():
    creds = None
    if os.path.exists("token.json"):
        try:
            with open("token.json") as f:
                creds = Credentials.from_authorized_user_info(json.load(f), SCOPES)
        except Exception:
            pass
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            from google_auth_oauthlib.flow import InstalledAppFlow
            creds_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return creds


def get_or_create_sheet(sheet_url: str = None, sheet_name: str = None):
    client = gspread.authorize(get_credentials())
    if sheet_url:
        sheet_id = sheet_url.split("/d/")[1].split("/")[0]
        spreadsheet = client.open_by_key(sheet_id)
        worksheet = spreadsheet.sheet1
        print(f"Opened existing sheet: {spreadsheet.title}")
    else:
        name = sheet_name or DEFAULT_SHEET_NAME
        spreadsheet = client.create(name)
        worksheet = spreadsheet.sheet1
        worksheet.update(values=[LEAD_COLUMNS], range_name="A1")
        col_letter = chr(64 + len(LEAD_COLUMNS))
        worksheet.format(
            f"A1:{col_letter}1",
            {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}},
        )
        worksheet.freeze(rows=1)
        print(f"Created sheet: {name}")
        print(f"Sheet URL: {spreadsheet.url}")
    return spreadsheet, worksheet


def get_existing_lead_ids(worksheet) -> set:
    try:
        return set(worksheet.col_values(1)[1:])
    except Exception:
        return set()


def append_leads(worksheet, leads: list, existing_ids: set) -> int:
    new = [lead for lead in leads if lead["lead_id"] not in existing_ids]
    if not new:
        print("No new leads to add (all duplicates of existing sheet rows)")
        return 0
    rows = [[lead.get(col, "") for col in LEAD_COLUMNS] for lead in new]
    worksheet.append_rows(rows, value_input_option="RAW")
    print(f"Added {len(new)} new leads")
    return len(new)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Find local businesses with no or weak websites",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # No website — multiple niches, new sheet
  python3 scripts/find_website_leads.py \\
      --mode no-website \\
      --searches "roofers in Birmingham" "hair salons in Birmingham" "plumbers in Birmingham" \\
      --limit 50

  # Weak website — append to existing sheet
  python3 scripts/find_website_leads.py \\
      --mode weak-website \\
      --searches "electricians in Birmingham" "gyms in Birmingham" \\
      --limit 100 \\
      --sheet-url "https://docs.google.com/spreadsheets/d/..."
        """,
    )
    parser.add_argument(
        "--mode", required=True, choices=["no-website", "weak-website"],
        help="no-website: businesses with no GMaps website | weak-website: free builder/directory sites",
    )
    parser.add_argument(
        "--searches", nargs="+", required=True,
        help='One or more search queries e.g. "roofers in Birmingham" "salons in Leeds"',
    )
    parser.add_argument("--limit", type=int, default=50, help="Max results per search query (default: 50)")
    parser.add_argument("--sheet-url", help="Existing Google Sheet URL to append leads to")
    parser.add_argument("--sheet-name", help="Name for a new sheet (ignored if --sheet-url is set)")
    parser.add_argument(
        "--workers", type=int, default=5,
        help="Parallel workers for HEAD request checks in weak-website mode (default: 5)",
    )
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"Website Lead Finder")
    print(f"Mode:     {args.mode}")
    print(f"Searches: {args.searches}")
    print(f"Limit:    {args.limit} per search")
    print(f"{'='*60}")

    all_leads = []

    for query in args.searches:
        print(f"\n{'─'*50}")
        print(f"Query: {query}")
        print(f"{'─'*50}")

        businesses = scrape_google_maps(query, args.limit, args.mode)
        if not businesses:
            print(f"  No results returned — skipping")
            continue

        if args.mode == "no-website":
            leads = process_no_website(businesses, query)
        else:
            leads = process_weak_website(businesses, query, args.workers)

        print(f"  Qualified leads: {len(leads)}")
        all_leads.extend(leads)

    if not all_leads:
        print("\nNo leads found. Try broader search queries or lower --limit.")
        sys.exit(0)

    # Cross-query deduplication
    seen_ids: set = set()
    unique_leads = []
    for lead in all_leads:
        if lead["lead_id"] not in seen_ids:
            seen_ids.add(lead["lead_id"])
            unique_leads.append(lead)

    dupes = len(all_leads) - len(unique_leads)

    print(f"\n{'='*60}")
    print(f"SAVING TO GOOGLE SHEET")
    print(f"{'='*60}")

    spreadsheet, worksheet = get_or_create_sheet(args.sheet_url, args.sheet_name)
    existing_ids = get_existing_lead_ids(worksheet)
    added = append_leads(worksheet, unique_leads, existing_ids)

    print(f"\n{'='*60}")
    print(f"COMPLETE")
    print(f"  Found:      {len(all_leads)} leads across {len(args.searches)} searches")
    if dupes:
        print(f"  Deduped:    {dupes} cross-query duplicates removed")
    print(f"  Added:      {added} new leads")
    print(f"  Sheet:      {spreadsheet.url}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
