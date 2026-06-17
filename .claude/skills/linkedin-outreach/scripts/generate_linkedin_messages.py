#!/usr/bin/env python3
"""
LinkedIn Message Generator

Reads leads from Google Sheet (output of gmaps-leads),
generates personalised LinkedIn connection request + 2 follow-up messages
using business_context.md for tone, results, and voice.

Usage:
    python3 ./scripts/generate_linkedin_messages.py \
        --sheet-url "https://docs.google.com/spreadsheets/d/..." \
        --output .tmp/linkedin_messages.json
"""

import os
import json
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import anthropic
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

# scripts/ -> linkedin-outreach/ -> skills/ -> .claude/ -> business_context.md
BUSINESS_CONTEXT_PATH = Path(__file__).resolve().parent.parent.parent.parent / "business_context.md"


def load_business_context() -> str:
    if BUSINESS_CONTEXT_PATH.exists():
        return BUSINESS_CONTEXT_PATH.read_text()
    raise FileNotFoundError(f"business_context.md not found at {BUSINESS_CONTEXT_PATH}")


def find_token_file() -> Path:
    """Find token.json by checking multiple locations."""
    candidates = [
        Path('token.json'),  # workspace root (when run from workspace)
        Path(__file__).resolve().parent.parent / 'token.json',  # skill root
        Path(__file__).resolve().parent.parent.parent.parent / 'token.json',  # workspace root (via path)
        Path(__file__).resolve().parent.parent.parent / 'gmaps-leads' / 'token.json',  # gmaps-leads copy
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(f"token.json not found. Checked: {[str(c) for c in candidates]}")


def get_sheets_service():
    token_path = find_token_file()
    with open(token_path, 'r') as f:
        token_data = json.load(f)
    scopes = token_data.get('scopes', [])
    creds = Credentials.from_authorized_user_file(str(token_path), scopes)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build('sheets', 'v4', credentials=creds)


def read_leads_from_sheet(sheet_url: str) -> list[dict]:
    """Read leads from Google Sheet, filter those with LinkedIn URLs."""
    sheet_id = sheet_url.split('/d/')[1].split('/')[0]
    service = get_sheets_service()

    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range='A:AZ'
    ).execute()

    rows = result.get('values', [])
    if not rows:
        return []

    headers = [h.lower().replace(' ', '_') for h in rows[0]]
    leads = []

    for row in rows[1:]:
        lead = dict(zip(headers, row + [''] * (len(headers) - len(row))))
        linkedin_url = lead.get('owner_linkedin', '').strip()
        if linkedin_url and linkedin_url.startswith('http'):
            leads.append(lead)

    print(f"Found {len(leads)} leads with LinkedIn URLs")
    return leads


def generate_messages_for_lead(lead: dict, business_context: str, client: anthropic.Anthropic) -> dict:
    """Generate 3-step LinkedIn message sequence for a single lead."""

    name = lead.get('owner_name', '').split()[0] if lead.get('owner_name') else 'there'
    company = lead.get('business_name', lead.get('casual_company_name', ''))
    industry = lead.get('category', 'service business')
    city = lead.get('city', lead.get('casual_city_name', ''))
    linkedin_url = lead.get('owner_linkedin', '')

    prompt = f"""Generate a 3-message LinkedIn outreach sequence for this prospect. Load the business context and reason against it before writing.

BUSINESS CONTEXT:
{business_context[:2500]}

PROSPECT:
- Name (first): {name}
- Company: {company}
- Industry: {industry}
- City: {city}
- LinkedIn: {linkedin_url}

Generate 3 messages:

MESSAGE 1 — Connection Request Note (HARD LIMIT: 300 characters including spaces)
- One specific observation about their type of business — name their actual situation
- No pitch. No ask. Just make them feel seen.
- Must be under 300 characters. Count carefully.

MESSAGE 2 — Follow-up after they accept (sent Day 3)
- Reference the connection briefly
- Name one specific pain point businesses like theirs face (admin, cash flow, follow-ups, owner bottleneck)
- Anchor it to a real result from the business context that matches
- Soft CTA: "Worth a quick 15-minute call this week?"
- Max 5 sentences

MESSAGE 3 — Final nudge (sent Day 7)
- One sentence. One question.
- Direct. Not desperate.

TONE: Straight-talking. Peer-to-peer. No corporate language. No em dashes. British spelling.
Use "you" not "your business". Personalise to their specific industry — don't be generic.

Output valid JSON:
{{
  "connection_request": "...",
  "follow_up": "...",
  "final_nudge": "..."
}}

Output ONLY the JSON object."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.rsplit("```", 1)[0]

    messages = json.loads(text.strip())

    # Enforce 300 char limit on connection request
    if len(messages.get("connection_request", "")) > 300:
        messages["connection_request"] = messages["connection_request"][:297] + "..."

    return {
        "owner_name": lead.get('owner_name', ''),
        "first_name": name,
        "company": company,
        "industry": industry,
        "city": city,
        "linkedin_url": linkedin_url,
        "email": lead.get('owner_email', lead.get('emails', '')),
        "messages": messages
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sheet-url", required=True, help="Google Sheet URL from gmaps-leads")
    parser.add_argument("--output", default=".tmp/linkedin_messages.json")
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--limit", type=int, default=None, help="Max leads to process")
    args = parser.parse_args()

    print("Loading business context...")
    business_context = load_business_context()
    print(f"Loaded {len(business_context)} chars of business context")

    print("Reading leads from sheet...")
    leads = read_leads_from_sheet(args.sheet_url)

    if args.limit:
        leads = leads[:args.limit]

    print(f"Generating messages for {len(leads)} leads...")
    client = anthropic.Anthropic()

    results = [None] * len(leads)
    completed = 0

    def process(idx_lead):
        idx, lead = idx_lead
        try:
            return idx, generate_messages_for_lead(lead, business_context, client), None
        except Exception as e:
            return idx, None, str(e)

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process, (i, lead)): i for i, lead in enumerate(leads)}
        for future in as_completed(futures):
            idx, result, error = future.result()
            completed += 1
            if error:
                print(f"[{completed}/{len(leads)}] ✗ {leads[idx].get('business_name', '?')}: {error[:50]}")
            else:
                results[idx] = result
                print(f"[{completed}/{len(leads)}] ✓ {result['company']} ({result['industry']})")

    results = [r for r in results if r is not None]

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nDone. {len(results)} message sets saved to {args.output}")
    print("Review messages before running create_dripify_campaign.py")


if __name__ == "__main__":
    main()
