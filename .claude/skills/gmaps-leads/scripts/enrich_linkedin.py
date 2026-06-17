#!/usr/bin/env python3
"""
LinkedIn Profile Enrichment via Google Search (Apify)

Finds LinkedIn profiles for leads missing linkedin_url by searching
Google for 'site:linkedin.com/in "Owner Name" "Business Name" city'.

Works with:
  - Supabase (outreach-calendar leads table)
  - Google Sheets (gmaps-leads output)
  - JSON files

Usage:
    # Enrich leads in Supabase
    python3 enrich_linkedin.py --source supabase --limit 50

    # Enrich leads from Google Sheet
    python3 enrich_linkedin.py --source sheet --sheet-url "https://docs.google.com/..." --limit 50

    # Enrich from JSON file
    python3 enrich_linkedin.py --source json --input leads.json --output enriched.json

    # Dry run (show what would be searched, don't call APIs)
    python3 enrich_linkedin.py --source supabase --limit 10 --dry-run
"""

from __future__ import annotations

import os
import sys
import json
import re
import time
import argparse
from datetime import datetime
from urllib.parse import quote_plus
from typing import Optional
from dotenv import load_dotenv

import httpx

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")
APIFY_ACTOR = "apify/google-search-scraper"
APIFY_BASE = "https://api.apify.com/v2"

# Supabase config
SUPABASE_URL = os.getenv("VITE_SUPABASE_URL") or os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("VITE_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")


def build_search_query(owner_name: str, business_name: str, area: str = "") -> str:
    """Build a Google search query to find someone's LinkedIn profile."""
    parts = ['site:linkedin.com/in']

    if owner_name:
        parts.append(f'"{owner_name}"')

    if business_name:
        # Strip common suffixes for better matching
        clean_biz = re.sub(r'\b(Ltd|Limited|LLC|Inc|PLC|LLP|& Sons?|& Co)\b', '', business_name, flags=re.I).strip()
        parts.append(f'"{clean_biz}"')

    if area:
        # Just use city name, strip country/region
        city = area.split(",")[0].strip()
        if city:
            parts.append(city)

    return " ".join(parts)


def search_google_apify(queries: list[str], results_per_query: int = 3) -> list[dict]:
    """
    Run Google searches via Apify's Google Search Scraper.

    Args:
        queries: List of search query strings
        results_per_query: Max results per query (default 3)

    Returns:
        List of result dicts with 'query' and 'results' keys
    """
    if not APIFY_TOKEN:
        print("Error: APIFY_API_TOKEN not set in .env", file=sys.stderr)
        sys.exit(1)

    # Build input for the actor
    actor_input = {
        "queries": "\n".join(queries),
        "maxPagesPerQuery": 1,
        "resultsPerPage": results_per_query,
        "languageCode": "en",
        "countryCode": "gb",
        "mobileResults": False,
        "includeUnfilteredResults": False,
    }

    # Run the actor synchronously
    url = f"{APIFY_BASE}/acts/{APIFY_ACTOR}/run-sync-get-dataset-items"
    params = {"token": APIFY_TOKEN, "timeout": 120}

    print(f"  Searching Google for {len(queries)} queries via Apify...")

    try:
        with httpx.Client(timeout=180.0) as client:
            resp = client.post(url, json=actor_input, params=params)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        print(f"  Apify error: {e.response.status_code} — {e.response.text[:200]}")
        return []
    except Exception as e:
        print(f"  Apify error: {e}")
        return []


def extract_linkedin_url(results: list[dict], owner_name: str = "") -> Optional[str]:
    """
    Extract the best LinkedIn profile URL from Google search results.

    Filters for linkedin.com/in/ URLs and picks the best match.
    """
    linkedin_urls = []

    for result in results:
        url = result.get("url", "")
        if "linkedin.com/in/" not in url:
            continue
        # Skip company pages
        if "/company/" in url:
            continue
        linkedin_urls.append(url)

    if not linkedin_urls:
        return None

    # If we have an owner name, prefer URLs containing parts of the name
    if owner_name and len(linkedin_urls) > 1:
        name_parts = owner_name.lower().split()
        for url in linkedin_urls:
            url_lower = url.lower()
            if any(part in url_lower for part in name_parts if len(part) > 2):
                return url

    return linkedin_urls[0]


def fetch_leads_supabase(limit: int = 50) -> list[dict]:
    """Fetch leads from Supabase that are missing LinkedIn URLs."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: Supabase URL/Key not configured", file=sys.stderr)
        sys.exit(1)

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

    # Fetch leads without linkedin_url, that have an owner name
    url = (
        f"{SUPABASE_URL}/rest/v1/leads"
        f"?linkedin_url=is.null"
        f"&owner_name=not.is.null"
        f"&select=id,business_name,owner_name,owner_first_name,area,trade"
        f"&order=created_at.desc"
        f"&limit={limit}"
    )

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            leads = resp.json()
            print(f"  Found {len(leads)} leads missing LinkedIn URLs")
            return leads
    except Exception as e:
        print(f"  Error fetching from Supabase: {e}")
        return []


def update_lead_supabase(lead_id: str, linkedin_url: str) -> bool:
    """Update a lead's linkedin_url in Supabase."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    url = f"{SUPABASE_URL}/rest/v1/leads?id=eq.{lead_id}"

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.patch(url, json={"linkedin_url": linkedin_url}, headers=headers)
            resp.raise_for_status()
            return True
    except Exception as e:
        print(f"    Error updating lead {lead_id}: {e}")
        return False


def fetch_leads_sheet(sheet_url: str, limit: int = 50) -> list[dict]:
    """Fetch leads from Google Sheet that are missing LinkedIn URLs."""
    import gspread
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    creds = None
    if os.path.exists('token.json'):
        with open('token.json', 'r') as f:
            token_data = json.load(f)
            creds = Credentials.from_authorized_user_info(token_data, scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("Error: No valid Google credentials. Run gmaps pipeline first.", file=sys.stderr)
            sys.exit(1)

    client = gspread.authorize(creds)
    sheet_id = sheet_url.split('/d/')[1].split('/')[0]
    spreadsheet = client.open_by_key(sheet_id)
    worksheet = spreadsheet.sheet1

    records = worksheet.get_all_records()
    leads = []
    for i, row in enumerate(records):
        if len(leads) >= limit:
            break
        owner_linkedin = (row.get("owner_linkedin") or "").strip()
        owner_name = (row.get("owner_name") or "").strip()
        if not owner_linkedin and owner_name:
            leads.append({
                "row_index": i + 2,  # +2 for header row and 0-index
                "business_name": row.get("business_name", ""),
                "owner_name": owner_name,
                "area": row.get("city", "") or row.get("area", ""),
            })

    print(f"  Found {len(leads)} leads missing LinkedIn URLs in sheet")
    return leads


def update_lead_sheet(sheet_url: str, row_index: int, linkedin_url: str, col_name: str = "owner_linkedin") -> bool:
    """Update a specific cell in the Google Sheet."""
    import gspread
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    creds = None
    if os.path.exists('token.json'):
        with open('token.json', 'r') as f:
            token_data = json.load(f)
            creds = Credentials.from_authorized_user_info(token_data, scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

    client = gspread.authorize(creds)
    sheet_id = sheet_url.split('/d/')[1].split('/')[0]
    spreadsheet = client.open_by_key(sheet_id)
    worksheet = spreadsheet.sheet1

    # Find the column index for owner_linkedin
    headers = worksheet.row_values(1)
    try:
        col_index = headers.index(col_name) + 1
    except ValueError:
        print(f"    Column '{col_name}' not found in sheet")
        return False

    worksheet.update_cell(row_index, col_index, linkedin_url)
    return True


def run_enrichment(
    source: str,
    limit: int = 50,
    sheet_url: str = None,
    input_file: str = None,
    output_file: str = None,
    dry_run: bool = False,
    batch_size: int = 10,
) -> dict:
    """
    Run LinkedIn enrichment pipeline.

    Batches queries to Apify to minimize API calls and cost.
    """
    stats = {
        "total_leads": 0,
        "queries_sent": 0,
        "profiles_found": 0,
        "profiles_updated": 0,
        "not_found": 0,
        "errors": 0,
    }

    # Step 1: Fetch leads
    print(f"\n{'='*50}")
    print(f"LinkedIn Enrichment — {source}")
    print(f"{'='*50}")

    if source == "supabase":
        leads = fetch_leads_supabase(limit)
    elif source == "sheet":
        if not sheet_url:
            print("Error: --sheet-url required for sheet source", file=sys.stderr)
            sys.exit(1)
        leads = fetch_leads_sheet(sheet_url, limit)
    elif source == "json":
        if not input_file:
            print("Error: --input required for json source", file=sys.stderr)
            sys.exit(1)
        with open(input_file) as f:
            all_leads = json.load(f)
        leads = [l for l in all_leads if not l.get("linkedin_url")][:limit]
        print(f"  Found {len(leads)} leads missing LinkedIn URLs")
    else:
        print(f"Error: Unknown source '{source}'", file=sys.stderr)
        sys.exit(1)

    stats["total_leads"] = len(leads)

    if not leads:
        print("  No leads to enrich.")
        return stats

    # Step 2: Build search queries
    queries_map = {}  # query -> lead
    for lead in leads:
        owner = lead.get("owner_name") or lead.get("owner_first_name") or ""
        business = lead.get("business_name", "")
        area = lead.get("area", "")

        if not owner:
            continue

        query = build_search_query(owner, business, area)
        queries_map[query] = lead

    print(f"  Built {len(queries_map)} search queries")

    if dry_run:
        print("\n  DRY RUN — queries that would be searched:")
        for q in list(queries_map.keys())[:20]:
            lead = queries_map[q]
            print(f"    {lead.get('owner_name', '?')} @ {lead.get('business_name', '?')} → {q}")
        return stats

    # Step 3: Batch search via Apify
    query_list = list(queries_map.keys())
    all_results = []

    for i in range(0, len(query_list), batch_size):
        batch = query_list[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(query_list) + batch_size - 1) // batch_size
        print(f"\n  Batch {batch_num}/{total_batches} ({len(batch)} queries)")

        results = search_google_apify(batch)
        stats["queries_sent"] += len(batch)

        # Group results by search query
        results_by_query = {}
        for r in results:
            sq = r.get("searchQuery", {})
            q_term = sq.get("term", "") if isinstance(sq, dict) else ""
            if q_term not in results_by_query:
                results_by_query[q_term] = []
            results_by_query[q_term].append(r)

        # Process results
        for query in batch:
            lead = queries_map[query]
            owner = lead.get("owner_name", "")
            business = lead.get("business_name", "")
            query_results = results_by_query.get(query, [])

            # Extract organic results
            organic = []
            for r in query_results:
                organic.extend(r.get("organicResults", []))

            linkedin_url = extract_linkedin_url(organic, owner)

            if linkedin_url:
                stats["profiles_found"] += 1
                print(f"    ✓ {owner} @ {business} → {linkedin_url}")

                # Update the source
                updated = False
                if source == "supabase":
                    updated = update_lead_supabase(lead["id"], linkedin_url)
                elif source == "sheet":
                    updated = update_lead_sheet(sheet_url, lead["row_index"], linkedin_url)
                elif source == "json":
                    lead["linkedin_url"] = linkedin_url
                    updated = True

                if updated:
                    stats["profiles_updated"] += 1
                else:
                    stats["errors"] += 1
            else:
                stats["not_found"] += 1
                print(f"    ✗ {owner} @ {business} — not found")

        # Rate limit between batches
        if i + batch_size < len(query_list):
            time.sleep(2)

    # Save JSON output if requested
    if source == "json" and output_file:
        with open(output_file, "w") as f:
            json.dump(leads, f, indent=2)
        print(f"\n  Saved enriched leads to {output_file}")

    # Summary
    print(f"\n{'='*50}")
    print("ENRICHMENT COMPLETE")
    print(f"{'='*50}")
    print(f"  Leads processed:  {stats['total_leads']}")
    print(f"  Queries sent:     {stats['queries_sent']}")
    print(f"  Profiles found:   {stats['profiles_found']}")
    print(f"  Updated:          {stats['profiles_updated']}")
    print(f"  Not found:        {stats['not_found']}")
    hit_rate = round(stats['profiles_found'] / max(stats['queries_sent'], 1) * 100, 1)
    print(f"  Hit rate:         {hit_rate}%")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Enrich leads with LinkedIn profile URLs")
    parser.add_argument("--source", required=True, choices=["supabase", "sheet", "json"],
                        help="Where to read leads from")
    parser.add_argument("--limit", type=int, default=50, help="Max leads to enrich (default: 50)")
    parser.add_argument("--sheet-url", help="Google Sheet URL (for sheet source)")
    parser.add_argument("--input", dest="input_file", help="Input JSON file (for json source)")
    parser.add_argument("--output", dest="output_file", help="Output JSON file (for json source)")
    parser.add_argument("--batch-size", type=int, default=10, help="Queries per Apify batch (default: 10)")
    parser.add_argument("--dry-run", action="store_true", help="Show queries without calling APIs")
    parser.add_argument("--json", action="store_true", help="Output stats as JSON")

    args = parser.parse_args()

    stats = run_enrichment(
        source=args.source,
        limit=args.limit,
        sheet_url=args.sheet_url,
        input_file=args.input_file,
        output_file=args.output_file,
        dry_run=args.dry_run,
        batch_size=args.batch_size,
    )

    if args.json:
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
