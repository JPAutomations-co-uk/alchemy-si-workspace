#!/usr/bin/env python3
"""
Pre-Call Brief Generator

Auto-generates a one-page brief before each sales call by:
1. Pulling prospect data from the pipeline sheet
2. Scraping their Google reviews + website
3. Identifying their sub-niche and matching to the right case study
4. Generating 2-3 specific quick wins
5. Outputting a formatted brief ready for the call

Usage:
    python3 .claude/skills/lead-pipeline/scripts/precall_brief.py --business "ACE Roofing Birmingham"
    python3 .claude/skills/lead-pipeline/scripts/precall_brief.py --sheet-url "..." --row 15
    python3 .claude/skills/lead-pipeline/scripts/precall_brief.py --name "Dave Smith" --business "Smith Plumbing" --phone "07xxx" --website "smithplumbing.co.uk"
"""

import os
import sys
import json
import argparse
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# log_activity
try:
    sys.path.insert(0, WORKSPACE)
    from execution.log_activity import log_activity
except Exception:
    def log_activity(*a, **kw): pass

try:
    import anthropic
except ImportError:
    print("pip install anthropic required", file=sys.stderr)
    sys.exit(1)

try:
    import requests
except ImportError:
    print("pip install requests required", file=sys.stderr)
    sys.exit(1)

# Sub-niche → case study mapping
CASE_STUDIES = {
    "roofer": {
        "client": "3-man roofing crew in Birmingham",
        "problem": "Owed £8,400 across 6 jobs. Owner spent Sundays writing invoices.",
        "result": "Outstanding dropped from £8,400 to £320 in 8 weeks. Payment time: 34 days → 6 days.",
        "system": "Automated invoicing and collections pipeline",
    },
    "plumber": {
        "client": "Solo heating engineer in Leeds",
        "problem": "Missing 60%+ of calls. Losing 3-4 jobs/week at £180 each.",
        "result": "Missed calls → zero. Revenue up £16,800 over one winter. Google reviews 4.2 → 4.8.",
        "system": "AI call handling + qualification + instant text response",
    },
    "heating": {
        "client": "Solo heating engineer in Leeds",
        "problem": "Missing 60%+ of calls during peak season.",
        "result": "14 extra jobs/month, £16,800 additional revenue Oct-Mar.",
        "system": "AI call handling + qualification + instant text response",
    },
    "electrician": {
        "client": "NICEIC-registered 2-man team in Manchester",
        "problem": "8hrs/week on certificates, building control, CIS, VAT. Missed a notification, got a warning.",
        "result": "Admin: 8hrs → 30mins/week. Extra billable day/week = £40k/year. Zero missed notifications in 12 months.",
        "system": "End-to-end compliance and admin automation",
    },
    "builder": {
        "client": "General contractor in Bristol, 3 projects, 6 subbies",
        "problem": "WhatsApp chaos. Made £900 on a £22k job. Late CIS returns, HMRC penalty.",
        "result": "Margins: 8% → 16%. Zero late CIS returns. Subbies prefer working with him now.",
        "system": "Live job costing + subcontractor management",
    },
    "landscaper": {
        "client": "Landscaping company in Surrey, owner + 2 staff",
        "problem": "Revenue: £18k/month summer → £4k/month winter. No maintenance contracts despite 3 years of talking about it.",
        "result": "47 maintenance clients at £85/month = £3,995/month recurring. Winter revenue doubled.",
        "system": "Automated maintenance plan engine",
    },
}

# Quick win templates by sub-niche
QUICK_WIN_TEMPLATES = {
    "roofer": [
        "Invoice automation — job complete → invoice same day → auto-chase at 7/14/21 days",
        "Lead capture — missed calls get auto-text with callback booking",
        "Review requests — auto-SMS after every completed job",
    ],
    "plumber": [
        "AI call handling — every call answered, qualified, customer texted immediately",
        "Emergency flagging — push notification for urgent jobs, routine ones queued",
        "Service reminders — annual boiler service reminders to past customers = recurring revenue",
    ],
    "heating": [
        "AI call handling — pick up every call during peak season, qualify emergency vs routine",
        "Service contract engine — auto-offer annual service plans to every customer",
        "Invoice + payment automation — paid within days, not months",
    ],
    "electrician": [
        "Certificate automation — job completion triggers auto-generated EIC + building control notification",
        "CIS auto-calculation — monthly returns pre-compiled from payment records",
        "Quote follow-up — auto-reminders at 3, 7, 14 days on outstanding quotes",
    ],
    "builder": [
        "Live job costing — labour + materials tracked against budget in real-time",
        "CIS management — deductions calculated automatically, monthly returns pre-compiled",
        "Subcontractor payments — clear statements, on-time, no manual calculation",
    ],
    "landscaper": [
        "Maintenance plan engine — every completed job triggers a recurring maintenance offer",
        "Seasonal revenue smoothing — build recurring base through winter months",
        "Quote automation — site visit notes → professional quote same day",
    ],
}


def detect_sub_niche(business_name, category="", description=""):
    """Detect the sub-niche from business name and category."""
    text = f"{business_name} {category} {description}".lower()

    if any(w in text for w in ["roof", "gutter", "slate", "tile", "chimney"]):
        return "roofer"
    if any(w in text for w in ["plumb", "bathroom", "drainage", "pipe", "tap"]):
        return "plumber"
    if any(w in text for w in ["heat", "boiler", "gas", "hvac", "radiator", "central heating"]):
        return "heating"
    if any(w in text for w in ["electri", "wiring", "rewire", "socket", "niceic", "napit"]):
        return "electrician"
    if any(w in text for w in ["build", "construct", "extension", "renovation", "convert"]):
        return "builder"
    if any(w in text for w in ["landscap", "garden", "paving", "fencing", "deck", "turf"]):
        return "landscaper"

    return "builder"  # default fallback


def scrape_basic_info(website):
    """Scrape basic info from the business website."""
    if not website:
        return {"has_website": False}

    if not website.startswith("http"):
        website = f"https://{website}"

    try:
        resp = requests.get(website, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        html = resp.text[:5000]  # First 5k chars

        # Check for common features
        has_contact_form = any(w in html.lower() for w in ["contact form", "get in touch", "request a quote", "<form"])
        has_booking = any(w in html.lower() for w in ["book", "schedule", "calendar", "appointment"])
        has_reviews = any(w in html.lower() for w in ["review", "testimonial", "rating"])
        has_chat = any(w in html.lower() for w in ["live chat", "chatbot", "chat widget", "tawk", "tidio"])

        return {
            "has_website": True,
            "has_contact_form": has_contact_form,
            "has_booking": has_booking,
            "has_reviews_page": has_reviews,
            "has_chat": has_chat,
            "status_code": resp.status_code,
        }
    except Exception as e:
        return {"has_website": True, "error": str(e)}


def generate_brief(prospect, sub_niche, website_info):
    """Generate the pre-call brief using Claude."""
    client = anthropic.Anthropic()

    case_study = CASE_STUDIES.get(sub_niche, CASE_STUDIES["builder"])
    quick_wins = QUICK_WIN_TEMPLATES.get(sub_niche, QUICK_WIN_TEMPLATES["builder"])

    prompt = f"""Generate a concise pre-call brief for a sales call with a UK trades business.
Keep it practical and specific — this is for JP to review 5 minutes before the call.

PROSPECT:
- Name: {prospect.get('name', 'Unknown')}
- Business: {prospect.get('business', 'Unknown')}
- Trade: {sub_niche}
- Phone: {prospect.get('phone', 'Not available')}
- Website: {prospect.get('website', 'None')}
- Google Rating: {prospect.get('rating', 'Unknown')}
- Reviews: {prospect.get('review_count', 'Unknown')}
- Location: {prospect.get('city', 'Unknown')}

WEBSITE ANALYSIS:
{json.dumps(website_info, indent=2)}

RELEVANT CASE STUDY:
- Client: {case_study['client']}
- Problem: {case_study['problem']}
- Result: {case_study['result']}
- System: {case_study['system']}

QUICK WIN TEMPLATES FOR {sub_niche.upper()}S:
{chr(10).join(f'- {qw}' for qw in quick_wins)}

Generate the brief in this exact format:

---
PRE-CALL BRIEF — [Business Name]
[Date] | [Sub-niche] | [Location]
---

PROSPECT SNAPSHOT:
• [1-2 sentences about them based on available data]
• Google: [rating] stars, [count] reviews
• Website: [quick assessment — professional/basic/none, missing features]

LIKELY PAIN POINTS (based on {sub_niche} research):
1. [Most likely pain — be specific to their trade]
2. [Second pain]
3. [Third pain]

QUICK WINS TO PRESENT:
1. [Specific win with estimated impact — reference their business specifically]
2. [Second win]
3. [Third win]

CASE STUDY TO REFERENCE:
"I worked with a {case_study['client']}..."
→ {case_study['result']}

OPENING LINE:
"[Suggested opening line for this specific prospect]"

OBJECTIONS TO EXPECT:
1. [Most likely objection for this sub-niche] → [Response]
2. [Second likely objection] → [Response]

CLOSE:
"[Suggested close line]"
---"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text


def read_prospect_from_sheet(sheet_url, row):
    """Read a specific prospect row from the pipeline sheet."""
    try:
        import gspread
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request

        token_path = os.path.join(WORKSPACE, "token.json")
        creds = Credentials.from_authorized_user_file(token_path, [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ])
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

        gc = gspread.authorize(creds)

        # Extract sheet ID
        sheet_id = sheet_url.split("/d/")[1].split("/")[0]
        spreadsheet = gc.open_by_key(sheet_id)
        worksheet = spreadsheet.sheet1

        headers = worksheet.row_values(1)
        row_data = worksheet.row_values(row)

        prospect = {}
        for i, header in enumerate(headers):
            if i < len(row_data):
                key = header.lower().replace(" ", "_")
                prospect[key] = row_data[i]

        return {
            "name": prospect.get("owner_name", prospect.get("casual_first_name", prospect.get("first_name", "Unknown"))),
            "business": prospect.get("business_name", prospect.get("name", "Unknown")),
            "phone": prospect.get("phone", ""),
            "website": prospect.get("website", ""),
            "rating": prospect.get("rating", ""),
            "review_count": prospect.get("review_count", prospect.get("reviews", "")),
            "city": prospect.get("city", prospect.get("address", "")),
            "category": prospect.get("category", ""),
        }
    except Exception as e:
        print(f"Error reading sheet: {e}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(description="Pre-Call Brief Generator")
    parser.add_argument("--name", type=str, help="Prospect name")
    parser.add_argument("--business", type=str, help="Business name")
    parser.add_argument("--phone", type=str, default="", help="Phone number")
    parser.add_argument("--website", type=str, default="", help="Website URL")
    parser.add_argument("--rating", type=str, default="", help="Google rating")
    parser.add_argument("--reviews", type=str, default="", help="Review count")
    parser.add_argument("--city", type=str, default="", help="City/location")
    parser.add_argument("--category", type=str, default="", help="Business category")
    parser.add_argument("--sheet-url", type=str, help="Pipeline sheet URL")
    parser.add_argument("--row", type=int, help="Row number in sheet")
    parser.add_argument("--output", type=str, help="Save brief to file")
    args = parser.parse_args()

    # Get prospect data
    if args.sheet_url and args.row:
        prospect = read_prospect_from_sheet(args.sheet_url, args.row)
        if not prospect:
            print("Failed to read prospect from sheet", file=sys.stderr)
            sys.exit(1)
    elif args.business:
        prospect = {
            "name": args.name or "Unknown",
            "business": args.business,
            "phone": args.phone,
            "website": args.website,
            "rating": args.rating,
            "review_count": args.reviews,
            "city": args.city,
            "category": args.category,
        }
    else:
        parser.error("Either --business or --sheet-url + --row required")

    # Detect sub-niche
    sub_niche = detect_sub_niche(
        prospect.get("business", ""),
        prospect.get("category", ""),
    )
    print(f"Detected sub-niche: {sub_niche}")

    # Scrape website
    print(f"Analysing website: {prospect.get('website', 'none')}...")
    website_info = scrape_basic_info(prospect.get("website", ""))

    # Generate brief
    print("Generating pre-call brief...")
    brief = generate_brief(prospect, sub_niche, website_info)

    # Output
    if args.output:
        with open(args.output, "w") as f:
            f.write(brief)
        print(f"\nBrief saved to: {args.output}")
    else:
        print(f"\n{brief}")

    # Log
    log_activity(
        agent_id="precall_brief",
        event_type="brief_generated",
        message=f"Pre-call brief for {prospect.get('business', 'Unknown')} ({sub_niche})",
        metrics={"sub_niche": sub_niche, "has_website": website_info.get("has_website", False)},
    )


if __name__ == "__main__":
    main()
