#!/usr/bin/env python3
"""
Dripify Campaign Creator

Reads generated LinkedIn messages from JSON,
creates a campaign in Dripify Pro, and adds prospects
with personalised 3-step sequences.

Usage:
    python3 ./scripts/create_dripify_campaign.py \
        --input .tmp/linkedin_messages.json \
        --campaign-name "JP Automations — Plumbers — Feb 2026"
"""

import os
import json
import argparse
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

DRIPIFY_API_KEY = os.getenv("DRIPIFY_API_KEY")
BASE_URL = "https://api.dripify.io/api/v1"

HEADERS = {
    "Authorization": f"Bearer {DRIPIFY_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def create_campaign(name: str) -> str:
    """Create a new Dripify campaign and return its ID."""
    payload = {
        "name": name,
        "daily_limit": 25,
        "steps": [
            {
                "type": "CONNECT",
                "delay": 0,
            },
            {
                "type": "MESSAGE",
                "delay": 3,  # days after connection accepted
            },
            {
                "type": "MESSAGE",
                "delay": 7,  # days after connection accepted
            },
        ],
    }

    resp = requests.post(f"{BASE_URL}/campaigns", headers=HEADERS, json=payload)

    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Failed to create campaign: {resp.status_code} {resp.text}")

    data = resp.json()
    campaign_id = data.get("id") or data.get("data", {}).get("id")
    print(f"Created campaign '{name}' — ID: {campaign_id}")
    return str(campaign_id)


def add_prospect(campaign_id: str, lead: dict) -> bool:
    """Add a single prospect to the campaign with personalised messages."""
    messages = lead.get("messages", {})

    payload = {
        "linkedin_url": lead["linkedin_url"],
        "first_name": lead.get("first_name", ""),
        "last_name": "",
        "company_name": lead.get("company", ""),
        "steps": [
            {
                "step": 1,
                "message": messages.get("connection_request", ""),
            },
            {
                "step": 2,
                "message": messages.get("follow_up", ""),
            },
            {
                "step": 3,
                "message": messages.get("final_nudge", ""),
            },
        ],
    }

    resp = requests.post(
        f"{BASE_URL}/campaigns/{campaign_id}/prospects",
        headers=HEADERS,
        json=payload,
    )

    if resp.status_code in (200, 201):
        return True
    else:
        print(f"  ✗ {lead.get('company', '?')}: {resp.status_code} {resp.text[:80]}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=".tmp/linkedin_messages.json")
    parser.add_argument("--campaign-name", required=True)
    parser.add_argument("--dry-run", action="store_true", help="Print prospects without creating campaign")
    args = parser.parse_args()

    if not DRIPIFY_API_KEY:
        raise SystemExit("DRIPIFY_API_KEY not set in environment")

    with open(args.input) as f:
        leads = json.load(f)

    print(f"Loaded {len(leads)} leads from {args.input}")

    if args.dry_run:
        print("\n--- DRY RUN ---")
        for lead in leads:
            msgs = lead.get("messages", {})
            print(f"\n{lead.get('company', '?')} ({lead.get('industry', '?')}) — {lead.get('linkedin_url', '')}")
            print(f"  [Connect] {msgs.get('connection_request', '')[:80]}...")
            print(f"  [Day 3]   {msgs.get('follow_up', '')[:80]}...")
            print(f"  [Day 7]   {msgs.get('final_nudge', '')}")
        return

    campaign_id = create_campaign(args.campaign_name)

    added = 0
    failed = 0

    for i, lead in enumerate(leads, 1):
        print(f"[{i}/{len(leads)}] Adding {lead.get('company', '?')}...")
        success = add_prospect(campaign_id, lead)
        if success:
            added += 1
        else:
            failed += 1
        # Rate limit: avoid hammering the API
        time.sleep(0.5)

    print(f"\nDone. {added} prospects added, {failed} failed.")
    print(f"Campaign ID: {campaign_id}")
    print("Activate the campaign in Dripify dashboard to start sending.")


if __name__ == "__main__":
    main()
