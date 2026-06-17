---
name: gmaps-leads
description: Scrape Google Maps for B2B leads with deep website enrichment and contact extraction. Use when user asks to find local businesses, scrape Google Maps, generate contractor lists, or build local service business databases.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Google Maps Lead Generation

## Goal
Generate high-quality B2B leads from Google Maps: scrape → quality gate → enrich → score → save.

## Inputs
| Parameter | Required | Description |
|-----------|----------|-------------|
| `--search` | Yes | Search query (e.g., "plumbers in Manchester") |
| `--limit` | No | Max results (default: 10) |
| `--sheet-url` | No | Existing sheet to append to |
| `--sheet-name` | No | New sheet name |
| `--workers` | No | Parallel enrichment workers (default: 3, max 5) |

## Scripts
- `./scripts/gmaps_lead_pipeline.py` — Main pipeline (scrape → gate → enrich → sheet)
- `./scripts/gmaps_parallel_pipeline.py` — Parallel version for 100+ leads
- `./scripts/scrape_google_maps.py` — Apify `compass/crawler-google-places` wrapper
- `./scripts/extract_website_contacts.py` — Website scraper + Claude Haiku extractor
- `./scripts/enrich_linkedin.py` — Find LinkedIn profiles via Google Search (Apify)
- `./scripts/update_sheet.py` — Google Sheets sync utility

## Process

### Standard run
```bash
# New sheet
python3 ./scripts/gmaps_lead_pipeline.py \
  --search "plumbers in Manchester" \
  --limit 50 \
  --workers 5

# Append to existing sheet
python3 ./scripts/gmaps_lead_pipeline.py \
  --search "roofers in Birmingham" \
  --limit 50 \
  --sheet-url "https://docs.google.com/spreadsheets/d/..." \
  --workers 5
```

### High-volume run (100+ leads)
```bash
python3 ./scripts/gmaps_parallel_pipeline.py \
  --search "electricians in London" \
  --limit 200 \
  --workers 10 \
  --sheet-url "https://..."
```

## Pipeline Steps

1. **Scrape** — Apify `compass/crawler-google-places` fetches listings
2. **Quality gate** — Filter BEFORE enrichment. Requires: rating ≥ 4.0, reviews ≥ 15, has website. Saves cost on junk leads.
3. **Enrich** — Each qualified business: fetch main page + up to 2 contact pages, extract with Claude Haiku
4. **Score** — Claude adds `fit_score` (1-10), `fit_reason`, `has_contact_form`, `team_size_signal` at zero extra cost
5. **Save** — Append to Google Sheet, deduplicated by `lead_id` (MD5 of name|address|city)
6. **Log** — Calls `log_activity("lead_gen", ...)` → Supabase → dashboard

## Output Schema (40 fields)

**Business Basics:** business_name, category, address, city, state, zip_code, country, phone, website, rating, review_count, price_level

**Extracted Contacts:** emails, additional_phones, business_hours

**Social Media:** facebook, twitter, linkedin, instagram, youtube, tiktok

**Owner Info:** owner_name, owner_title, owner_email, owner_phone, owner_linkedin

**Team:** team_contacts (JSON array)

**Quality Signals (Claude):** fit_score (1-10), fit_reason, has_contact_form, team_size_signal (solo/small/mid/large)

**Metadata:** lead_id, scraped_at, search_query, pages_scraped, search_enriched, enrichment_status

## Dashboard Logging
Every run logs to Supabase `agent_activity`:
```json
{
  "businesses_found": 67, "businesses_qualified": 42, "businesses_disqualified": 25,
  "leads_added": 38, "emails_found": 19,
  "qualify_rate": 62.7, "enrich_rate": 50.0, "cost_gbp": 0.84,
  "city": "Manchester", "search_query": "plumbers in Manchester", "sheet_url": "..."
}
```

## Address Parsing
- **UK** — detects postcodes like `M1 2AB`, `SW1A 1AA`, extracts city correctly
- **US** — extracts 5-digit zip and 2-letter state code

## Cost
| Component | Per qualified lead |
|-----------|--------------------|
| Apify Google Maps | ~£0.008-0.015 |
| Claude Haiku extraction | ~£0.002 |
| **Total** | **~£0.010-0.020** |

Disqualified leads cost nothing — the gate pays for itself.

## LinkedIn Enrichment

After scraping, most trades leads won't have LinkedIn URLs from their websites. Use the LinkedIn enrichment script to find profiles via Google Search:

```bash
# Enrich leads in Supabase (outreach-calendar)
python3 ./scripts/enrich_linkedin.py --source supabase --limit 50

# Enrich leads in Google Sheet
python3 ./scripts/enrich_linkedin.py --source sheet --sheet-url "https://docs.google.com/..." --limit 50

# Dry run first to preview queries
python3 ./scripts/enrich_linkedin.py --source supabase --limit 10 --dry-run
```

Searches Google for `site:linkedin.com/in "Owner Name" "Business Name" city`. Typical hit rate: 30-50% for UK trades. Uses Apify's `apify/google-search-scraper` (batched, 10 queries per API call).

## Self-annealing
- **"No businesses found"**: Must include city. "plumbers" fails, "plumbers in Manchester" works.
- **403 Forbidden**: ~10-15% of sites block scrapers, handled silently.
- **Low qualify rate (<30%)**: Consider lowering MIN_REVIEWS to 10 for sparse markets.
- **Low email rate (<20%)**: Trades typically have lower email exposure. Expected for that niche.
- **Auth issues**: Delete `token.json` and re-authenticate.
- **After any bug fix**: Update this file.

## Environment
```
APIFY_API_TOKEN=your_token
ANTHROPIC_API_KEY=your_key
SUPABASE_URL=your_url
SUPABASE_SERVICE_ROLE_KEY=your_key
```
