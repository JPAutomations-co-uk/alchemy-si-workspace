#!/usr/bin/env python3
"""
Google Maps Lead Generation Pipeline

End-to-end pipeline that:
1. Scrapes Google Maps for businesses matching search criteria
2. Filters by quality gate (rating, reviews, website)
3. Enriches each business by scraping their website for contact info
4. Uses Claude to extract structured contact data + fit score
5. Saves everything to a persistent Google Sheet

Usage:
    python3 .claude/skills/gmaps-leads/scripts/gmaps_lead_pipeline.py --search "plumbers in Manchester" --limit 50
    python3 .claude/skills/gmaps-leads/scripts/gmaps_lead_pipeline.py --search "roofers" --location "Birmingham, UK" --limit 25 --sheet-url "https://..."
"""

import os
import re
import sys
import json
import argparse
import hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Import our modules
from scrape_google_maps import scrape_google_maps
from extract_website_contacts import scrape_website_contacts

# log_activity — fails silently if not available
try:
    import os as _os, sys as _sys
    _ws = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))))
    _sys.path.insert(0, _ws)
    from execution.log_activity import log_activity
except Exception:
    def log_activity(*a, **kw): pass

load_dotenv()

# Google Sheets config
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Default sheet name for leads
DEFAULT_SHEET_NAME = "GMaps Lead Database"

# Qualification thresholds
MIN_RATING     = 4.0
MIN_REVIEWS    = 15

# Cost estimate per enriched lead (Claude Haiku calls)
COST_PER_LEAD_GBP = 0.02

# Lead schema - columns for the Google Sheet
LEAD_COLUMNS = [
    "lead_id",
    "scraped_at",
    "search_query",
    # Business basics from Google Maps
    "business_name",
    "category",
    "address",
    "city",
    "state",
    "zip_code",
    "country",
    "phone",
    "website",
    "google_maps_url",
    "place_id",
    # Ratings & reviews
    "rating",
    "review_count",
    "price_level",
    # Extracted contact info
    "emails",
    "additional_phones",
    "business_hours",
    # Social media
    "facebook",
    "twitter",
    "linkedin",
    "instagram",
    "youtube",
    "tiktok",
    # Owner/key person info
    "owner_name",
    "owner_title",
    "owner_email",
    "owner_phone",
    "owner_linkedin",
    # Team contacts (JSON string for multiple people)
    "team_contacts",
    # Quality signals from Claude extraction
    "fit_score",
    "fit_reason",
    "has_contact_form",
    "team_size_signal",
    # Additional data
    "additional_contact_methods",
    "pages_scraped",
    "search_enriched",
    "enrichment_status",
]


def generate_lead_id(business_name: str, address: str, city: str = "") -> str:
    """Generate a unique ID for a lead based on name, address, and city."""
    unique_string = f"{business_name}|{address}|{city}".lower()
    return hashlib.md5(unique_string.encode()).hexdigest()[:12]


def stringify_value(value) -> str:
    """Convert any value to a string suitable for Google Sheets."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value if v)
    if isinstance(value, dict):
        parts = []
        for k, v in value.items():
            if v:
                parts.append(f"{k}: {v}")
        return "; ".join(parts) if parts else ""
    return str(value)


def parse_address(address: str) -> dict:
    """Parse an address string into components. Handles both UK and US formats."""
    parts = {
        "city": "",
        "state": "",
        "zip_code": "",
        "country": ""
    }

    if not address:
        return parts

    # Detect UK address
    is_uk = (
        "united kingdom" in address.lower()
        or "england" in address.lower()
        or "scotland" in address.lower()
        or "wales" in address.lower()
        or re.search(r'\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b', address)
    )

    if is_uk:
        parts["country"] = "GB"
        # UK postcode: e.g. M1 2AB, SW1A 1AA, B1 1BB
        uk_pc = re.search(r'\b([A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2})\b', address)
        if uk_pc:
            parts["zip_code"] = uk_pc.group(1)

        # City: comma-separated part just before the postcode
        # e.g. "123 High St, Manchester, M1 2AB, United Kingdom"
        addr_parts = [p.strip() for p in address.split(",")]
        for i, part in enumerate(addr_parts):
            if uk_pc and uk_pc.group(1) in part:
                # City is the segment before the postcode segment
                if i > 0:
                    parts["city"] = addr_parts[i - 1].strip()
                break
        # Fallback: second-to-last non-country segment
        if not parts["city"] and len(addr_parts) >= 2:
            for seg in reversed(addr_parts):
                seg_clean = seg.strip().lower()
                if seg_clean not in ("united kingdom", "england", "scotland", "wales", "uk"):
                    if not re.search(r'\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b', seg, re.I):
                        parts["city"] = seg.strip()
                        break
    else:
        # US format
        parts["country"] = "USA"
        zip_match = re.search(r'\b(\d{5}(?:-\d{4})?)\b', address)
        if zip_match:
            parts["zip_code"] = zip_match.group(1)

        state_match = re.search(r'\b([A-Z]{2})\b', address)
        if state_match:
            parts["state"] = state_match.group(1)

        if parts["state"]:
            city_match = re.search(rf',\s*([^,]+),?\s*{parts["state"]}', address)
            if city_match:
                parts["city"] = city_match.group(1).strip()

    return parts


def qualify_business(business: dict) -> tuple:
    """
    Check if a business meets the quality gate before enrichment.

    Returns:
        (True, "") if qualified
        (False, reason) if not qualified
    """
    website = (business.get("website") or "").strip()
    if not website:
        return False, "no_website"

    try:
        rating = float(business.get("totalScore") or 0)
    except (TypeError, ValueError):
        rating = 0.0

    try:
        reviews = int(business.get("reviewsCount") or 0)
    except (TypeError, ValueError):
        reviews = 0

    if reviews < MIN_REVIEWS:
        return False, f"low_reviews_{reviews}"

    if rating < MIN_RATING:
        return False, f"low_rating_{rating}"

    return True, ""


def flatten_lead(gmaps_data: dict, contacts: dict, search_query: str) -> dict:
    """
    Flatten Google Maps data and extracted contacts into a single lead record.
    """
    address = gmaps_data.get("address", "")
    addr_parts = parse_address(address)

    social = contacts.get("social_media", {}) or {}
    owner = contacts.get("owner_info", {}) or {}
    if isinstance(owner, list):
        owner = owner[0] if owner else {}

    team = contacts.get("team_members", []) or []
    team_json = json.dumps(team) if team else ""

    emails = contacts.get("emails", []) or []
    phones = contacts.get("phone_numbers", []) or []
    additional_contacts = contacts.get("additional_contacts", []) or []

    city = addr_parts["city"] or gmaps_data.get("city", "")
    lead_id = generate_lead_id(gmaps_data.get("title", ""), address, city)

    enrichment_status = "success" if emails or owner.get("email") else "partial"
    if contacts.get("error"):
        enrichment_status = f"error: {contacts.get('error')}"

    # Quality signals from Claude extraction
    fit_score = contacts.get("fit_score")
    fit_score_str = str(int(fit_score)) if fit_score is not None else ""
    has_cf = contacts.get("has_contact_form")
    has_cf_str = "yes" if has_cf is True else ("no" if has_cf is False else "")

    return {
        "lead_id": lead_id,
        "scraped_at": datetime.now().isoformat(),
        "search_query": search_query,
        "business_name": gmaps_data.get("title", ""),
        "category": gmaps_data.get("categoryName", ""),
        "address": address,
        "city": city,
        "state": addr_parts["state"] or gmaps_data.get("state", ""),
        "zip_code": addr_parts["zip_code"] or gmaps_data.get("postalCode", ""),
        "country": addr_parts["country"] or gmaps_data.get("countryCode", ""),
        "phone": gmaps_data.get("phone", ""),
        "website": gmaps_data.get("website", ""),
        "google_maps_url": gmaps_data.get("url", ""),
        "place_id": gmaps_data.get("placeId", ""),
        "rating": gmaps_data.get("totalScore", ""),
        "review_count": gmaps_data.get("reviewsCount", ""),
        "price_level": gmaps_data.get("price", ""),
        "emails": stringify_value(emails),
        "additional_phones": stringify_value(phones),
        "business_hours": stringify_value(contacts.get("business_hours", "")),
        "facebook": stringify_value(social.get("facebook", "")),
        "twitter": stringify_value(social.get("twitter", "")),
        "linkedin": stringify_value(social.get("linkedin", "")),
        "instagram": stringify_value(social.get("instagram", "")),
        "youtube": stringify_value(social.get("youtube", "")),
        "tiktok": stringify_value(social.get("tiktok", "")),
        "owner_name": stringify_value(owner.get("name", "")),
        "owner_title": stringify_value(owner.get("title", "")),
        "owner_email": stringify_value(owner.get("email", "")),
        "owner_phone": stringify_value(owner.get("phone", "")),
        "owner_linkedin": stringify_value(owner.get("linkedin", "")),
        "team_contacts": team_json,
        "fit_score": fit_score_str,
        "fit_reason": contacts.get("fit_reason", ""),
        "has_contact_form": has_cf_str,
        "team_size_signal": contacts.get("team_size_signal", ""),
        "additional_contact_methods": stringify_value(additional_contacts),
        "pages_scraped": contacts.get("_pages_scraped", 0),
        "search_enriched": "yes" if contacts.get("_search_enriched") else "no",
        "enrichment_status": enrichment_status,
    }


def get_credentials():
    """Get OAuth2 credentials for Google Sheets API."""
    creds = None

    if os.path.exists('token.json'):
        try:
            with open('token.json', 'r') as token:
                token_data = json.load(token)
                creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        except Exception as e:
            print(f"Error loading token: {e}")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            from google_auth_oauthlib.flow import InstalledAppFlow
            creds_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds


def get_or_create_sheet(sheet_url: str = None, sheet_name: str = None) -> tuple:
    """Get existing sheet or create a new one."""
    creds = get_credentials()
    client = gspread.authorize(creds)

    if sheet_url:
        if '/d/' in sheet_url:
            sheet_id = sheet_url.split('/d/')[1].split('/')[0]
        else:
            sheet_id = sheet_url
        spreadsheet = client.open_by_key(sheet_id)
        worksheet = spreadsheet.sheet1
        is_new = False
        print(f"Opened existing sheet: {spreadsheet.title}")
    else:
        name = sheet_name or DEFAULT_SHEET_NAME
        spreadsheet = client.create(name)
        worksheet = spreadsheet.sheet1
        worksheet.update(values=[LEAD_COLUMNS], range_name='A1')
        col_letter = chr(64 + len(LEAD_COLUMNS))
        worksheet.format(f'A1:{col_letter}1', {
            "textFormat": {"bold": True},
            "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
        })
        worksheet.freeze(rows=1)
        is_new = True
        print(f"Created new sheet: {name}")
        print(f"Sheet URL: {spreadsheet.url}")

    return spreadsheet, worksheet, is_new


def get_existing_lead_ids(worksheet) -> set:
    """Get all existing lead IDs from the sheet to avoid duplicates."""
    try:
        lead_ids = worksheet.col_values(1)
        return set(lead_ids[1:])
    except Exception:
        return set()


def append_leads_to_sheet(worksheet, leads: list, existing_ids: set) -> int:
    """Append new leads to the sheet, skipping duplicates."""
    new_leads = [lead for lead in leads if lead["lead_id"] not in existing_ids]

    if not new_leads:
        print("No new leads to add (all duplicates)")
        return 0

    rows = []
    for lead in new_leads:
        row = [lead.get(col, "") for col in LEAD_COLUMNS]
        rows.append(row)

    worksheet.append_rows(rows, value_input_option='RAW')
    print(f"Added {len(new_leads)} new leads to sheet")
    return len(new_leads)


def enrich_businesses(businesses: list, max_workers: int = 3) -> list:
    """Enrich businesses with website contact information in parallel."""
    print(f"\nEnriching {len(businesses)} businesses with website data...")

    enriched = []

    # All businesses at this point already have websites (qualification gate ensures this)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_business = {
            executor.submit(
                scrape_website_contacts,
                business.get("website"),
                business.get("title")
            ): business
            for business in businesses
        }

        for i, future in enumerate(as_completed(future_to_business), 1):
            business = future_to_business[future]
            try:
                contacts = future.result()
                enriched.append({"gmaps": business, "contacts": contacts})
                print(f"  [{i}/{len(businesses)}] Enriched: {business.get('title')}")
            except Exception as e:
                print(f"  [{i}/{len(businesses)}] Error enriching {business.get('title')}: {e}")
                enriched.append({"gmaps": business, "contacts": {"error": str(e)}})

    return enriched


def run_pipeline(
    search_query: str,
    max_results: int = 10,
    location: str = None,
    sheet_url: str = None,
    sheet_name: str = None,
    workers: int = 3,
    save_intermediate: bool = True,
) -> dict:
    """
    Run the full lead generation pipeline.

    Returns:
        Dictionary with pipeline results including qualification and enrichment stats.
    """
    results = {
        "search_query": search_query,
        "started_at": datetime.now().isoformat(),
        "businesses_found": 0,
        "businesses_qualified": 0,
        "businesses_disqualified": 0,
        "qualify_rate": 0.0,
        "leads_enriched": 0,
        "leads_added": 0,
        "emails_found": 0,
        "enrich_rate": 0.0,
        "cost_gbp": 0.0,
        "sheet_url": None,
        "errors": []
    }

    # Step 1: Scrape Google Maps
    print(f"\n{'='*60}")
    print(f"STEP 1: Scraping Google Maps for '{search_query}'")
    print(f"{'='*60}")

    businesses = scrape_google_maps(
        search_query=search_query,
        max_results=max_results,
        location=location,
    )

    if not businesses:
        results["errors"].append("No businesses found on Google Maps")
        log_activity("lead_gen", "run_error", f"No businesses found for '{search_query}'",
                     metrics=results, status="error")
        return results

    results["businesses_found"] = len(businesses)
    print(f"Found {len(businesses)} businesses")

    if save_intermediate:
        os.makedirs(".tmp", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f".tmp/gmaps_raw_{timestamp}.json", "w") as f:
            json.dump(businesses, f, indent=2)

    # Step 2: Qualification gate
    print(f"\n{'='*60}")
    print(f"STEP 2: Quality gate (rating>={MIN_RATING}, reviews>={MIN_REVIEWS}, has website)")
    print(f"{'='*60}")

    qualified = []
    disqualified_reasons = {}
    for biz in businesses:
        ok, reason = qualify_business(biz)
        if ok:
            qualified.append(biz)
        else:
            results["businesses_disqualified"] += 1
            disqualified_reasons[reason] = disqualified_reasons.get(reason, 0) + 1
            print(f"  Skipped: {biz.get('title', '?')} — {reason}")

    results["businesses_qualified"] = len(qualified)
    if results["businesses_found"] > 0:
        results["qualify_rate"] = round(len(qualified) / results["businesses_found"] * 100, 1)

    print(f"\n  {len(qualified)}/{len(businesses)} qualified ({results['qualify_rate']}%)")
    if disqualified_reasons:
        for reason, count in disqualified_reasons.items():
            print(f"  — {count} skipped: {reason}")

    if not qualified:
        log_activity("lead_gen", "run_complete",
                     f"0 qualified leads for '{search_query}' — all {len(businesses)} failed gate",
                     metrics=results, status="warning")
        return results

    # Step 3: Enrich qualified businesses
    print(f"\n{'='*60}")
    print(f"STEP 3: Enriching {len(qualified)} qualified businesses")
    print(f"{'='*60}")

    enriched = enrich_businesses(qualified, max_workers=workers)
    results["leads_enriched"] = len(enriched)
    results["cost_gbp"] = round(len(enriched) * COST_PER_LEAD_GBP, 2)

    # Step 4: Flatten to lead records
    print(f"\n{'='*60}")
    print(f"STEP 4: Processing lead records")
    print(f"{'='*60}")

    leads = []
    for item in enriched:
        lead = flatten_lead(item["gmaps"], item["contacts"], search_query)
        leads.append(lead)

    # Count leads where we found an email
    results["emails_found"] = sum(
        1 for lead in leads if lead.get("emails") or lead.get("owner_email")
    )
    if results["leads_enriched"] > 0:
        results["enrich_rate"] = round(results["emails_found"] / results["leads_enriched"] * 100, 1)

    if save_intermediate:
        with open(f".tmp/leads_enriched_{timestamp}.json", "w") as f:
            json.dump(leads, f, indent=2)

    # Step 5: Save to Google Sheet
    print(f"\n{'='*60}")
    print(f"STEP 5: Saving to Google Sheet")
    print(f"{'='*60}")

    try:
        spreadsheet, worksheet, is_new = get_or_create_sheet(sheet_url, sheet_name)
        results["sheet_url"] = spreadsheet.url

        existing_ids = get_existing_lead_ids(worksheet)
        added = append_leads_to_sheet(worksheet, leads, existing_ids)
        results["leads_added"] = added

    except Exception as e:
        results["errors"].append(f"Google Sheets error: {str(e)}")
        print(f"Error saving to sheet: {e}")

    results["completed_at"] = datetime.now().isoformat()

    # Summary
    print(f"\n{'='*60}")
    print("PIPELINE COMPLETE")
    print(f"{'='*60}")
    print(f"Scraped:     {results['businesses_found']} businesses")
    print(f"Qualified:   {results['businesses_qualified']} ({results['qualify_rate']}%)")
    print(f"Enriched:    {results['leads_enriched']}")
    print(f"Emails:      {results['emails_found']} ({results['enrich_rate']}%)")
    print(f"Added:       {results['leads_added']}")
    print(f"Cost:        £{results['cost_gbp']:.2f}")
    if results["sheet_url"]:
        print(f"Sheet:       {results['sheet_url']}")
    if results["errors"]:
        print(f"Errors:      {results['errors']}")

    # Log to Supabase
    city = search_query.split(" in ", 1)[-1].strip() if " in " in search_query else ""
    log_activity(
        "lead_gen",
        "run_complete",
        f"Scraped {results['leads_added']} leads{' in ' + city if city else ''} "
        f"({results['qualify_rate']}% qualify, {results['enrich_rate']}% emails)",
        metrics={
            "businesses_found":      results["businesses_found"],
            "businesses_qualified":  results["businesses_qualified"],
            "businesses_disqualified": results["businesses_disqualified"],
            "leads_added":           results["leads_added"],
            "emails_found":          results["emails_found"],
            "qualify_rate":          results["qualify_rate"],
            "enrich_rate":           results["enrich_rate"],
            "cost_gbp":              results["cost_gbp"],
            "city":                  city,
            "search_query":          search_query,
            "sheet_url":             results.get("sheet_url", ""),
        },
        status="success" if not results["errors"] else "warning",
    )

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Google Maps Lead Generation Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/gmaps_lead_pipeline.py --search "plumbers in Manchester" --limit 50
  python3 scripts/gmaps_lead_pipeline.py --search "roofers" --location "Birmingham, UK" --limit 25
  python3 scripts/gmaps_lead_pipeline.py --search "electricians in Leeds" --limit 50 --sheet-url "https://docs.google.com/..."
        """
    )

    parser.add_argument("--search", required=True, help="Search query for Google Maps")
    parser.add_argument("--limit", type=int, default=10, help="Max results to scrape (default: 10)")
    parser.add_argument("--location", help="Location to focus search")
    parser.add_argument("--sheet-url", help="Existing Google Sheet URL to append to")
    parser.add_argument("--sheet-name", help="Name for new sheet (if not using existing)")
    parser.add_argument("--workers", type=int, default=3, help="Parallel workers for enrichment (default: 3)")
    parser.add_argument("--no-intermediate", action="store_true", help="Don't save intermediate JSON files")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    results = run_pipeline(
        search_query=args.search,
        max_results=args.limit,
        location=args.location,
        sheet_url=args.sheet_url,
        sheet_name=args.sheet_name,
        workers=args.workers,
        save_intermediate=not args.no_intermediate,
    )

    if args.json:
        print(json.dumps(results, indent=2))

    if results["leads_added"] == 0 and results["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
