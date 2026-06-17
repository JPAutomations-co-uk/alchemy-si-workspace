#!/usr/bin/env python3
"""
Supabase Sync Adapter

Pushes leads, outreach actions, and briefs from Python scripts
into the Supabase tables used by the Outreach Calendar app.

Usage:
    from execution.supabase_sync import push_leads, push_actions, update_brief

    # Push scraped leads
    push_leads(leads_data, user_id)

    # Generate outreach actions for each lead
    generate_actions_for_lead(lead_id, user_id, trade)

    # Store a pre-call brief
    update_brief(lead_id, brief_data)
"""

import os
import json
import logging
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("supabase_sync")

SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Fall back to anon key if service role not available
if not SUPABASE_KEY:
    SUPABASE_KEY = os.getenv("VITE_SUPABASE_ANON_KEY")


def _headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _post(table, data):
    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/{table}",
        headers=_headers(),
        json=data,
        timeout=10,
    )
    if resp.status_code >= 400:
        logger.error(f"Supabase insert to {table} failed: {resp.status_code} {resp.text}")
        return None
    return resp.json()


def _patch(table, id, data):
    resp = requests.patch(
        f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{id}",
        headers=_headers(),
        json=data,
        timeout=10,
    )
    if resp.status_code >= 400:
        logger.error(f"Supabase update {table}/{id} failed: {resp.status_code} {resp.text}")
        return None
    return resp.json()


def push_lead(lead_data, user_id):
    """Insert a single lead into the leads table."""
    row = {
        "user_id": user_id,
        "business_name": lead_data.get("business_name", lead_data.get("name", "")),
        "owner_name": lead_data.get("owner_name", ""),
        "owner_first_name": lead_data.get("casual_first_name", lead_data.get("first_name", "")),
        "phone": lead_data.get("phone", ""),
        "email": lead_data.get("owner_email", lead_data.get("email", "")),
        "website": lead_data.get("website", ""),
        "linkedin_url": lead_data.get("owner_linkedin", ""),
        "trade": detect_trade(lead_data.get("category", "")),
        "area": lead_data.get("city", lead_data.get("area", "")),
        "google_rating": lead_data.get("rating"),
        "review_count": lead_data.get("review_count"),
        "source": "gmaps",
        "status": "new",
    }
    result = _post("leads", row)
    if result and len(result) > 0:
        return result[0]
    return None


def push_leads(leads_list, user_id):
    """Insert multiple leads and generate actions for each."""
    inserted = []
    for lead_data in leads_list:
        lead = push_lead(lead_data, user_id)
        if lead:
            inserted.append(lead)
            generate_actions_for_lead(lead["id"], user_id, lead.get("trade", "builder"))
    logger.info(f"Pushed {len(inserted)} leads to Supabase")
    return inserted


def generate_actions_for_lead(lead_id, user_id, trade):
    """Generate the full outreach action sequence for a lead."""
    today = datetime.now().date()
    actions = [
        {"action_type": "cold_call", "channel": "phone", "due_date": str(today), "sequence_step": 0},
        {"action_type": "connection_request", "channel": "linkedin", "due_date": str(today), "sequence_step": 0},
        {"action_type": "follow_up_email", "channel": "email", "due_date": str(today + timedelta(days=3)), "sequence_step": 1},
        {"action_type": "follow_up_dm", "channel": "linkedin", "due_date": str(today + timedelta(days=3)), "sequence_step": 1},
        {"action_type": "follow_up_email", "channel": "email", "due_date": str(today + timedelta(days=7)), "sequence_step": 2},
        {"action_type": "follow_up_email", "channel": "email", "due_date": str(today + timedelta(days=14)), "sequence_step": 3},
        {"action_type": "follow_up_email", "channel": "email", "due_date": str(today + timedelta(days=30)), "sequence_step": 4},
    ]

    rows = [
        {
            "lead_id": lead_id,
            "user_id": user_id,
            "status": "pending",
            **action,
        }
        for action in actions
    ]

    for row in rows:
        _post("outreach_actions", row)


def update_brief(lead_id, brief_data):
    """Store a pre-call brief JSON on a lead."""
    _patch("leads", lead_id, {"brief": json.dumps(brief_data) if isinstance(brief_data, dict) else brief_data})


def detect_trade(category):
    """Detect trade from business category string."""
    cat = (category or "").lower()
    if any(w in cat for w in ["roof", "gutter"]):
        return "roofer"
    if any(w in cat for w in ["plumb", "bathroom"]):
        return "plumber"
    if any(w in cat for w in ["heat", "boiler", "gas", "hvac"]):
        return "plumber"
    if any(w in cat for w in ["electri", "wiring"]):
        return "electrician"
    if any(w in cat for w in ["build", "construct", "extension"]):
        return "builder"
    if any(w in cat for w in ["landscap", "garden"]):
        return "landscaper"
    return "builder"


if __name__ == "__main__":
    # Quick test
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or VITE_SUPABASE_ANON_KEY)")
    else:
        print(f"Supabase URL: {SUPABASE_URL}")
        print("Sync adapter ready.")
