#!/usr/bin/env python3
"""
Build Manual Outreach Leads Google Sheet

Pulls:
1. All leads from Instantly campaigns who opened emails but didn't reply (warm leads)
2. All leads from CSV files in .tmp/campaign_csvs/ (cold email sequences)

Creates a Google Sheet with:
- "Manual Outreach Leads" master tab (all leads combined)
- Weekly tabs for scheduling outreach
  - Week 1 (current week): Email openers — warm, highest priority
  - Weeks 2+: CSV cold leads distributed evenly (~100/week)

Usage:
    python3 execution/build_outreach_sheet.py
"""

import os
import sys
import csv
import json
import time
import math
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

import requests
import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

load_dotenv()

INSTANTLY_API_KEY = os.getenv("INSTANTLY_API_KEY")
INSTANTLY_API_BASE = "https://api.instantly.ai/api/v2"
CSV_DIR = Path(__file__).parent.parent / ".tmp" / "campaign_csvs"
WORKSPACE_DIR = Path(__file__).parent.parent

INSTANTLY_HEADERS = {"Authorization": f"Bearer {INSTANTLY_API_KEY}"}

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Campaign CSV friendly names
CSV_CAMPAIGN_NAMES = {
    "1_plumbers_missed_calls.csv": "Plumbers - Missed Calls",
    "2_plumbers_quote_followup.csv": "Plumbers - Quote Follow-up",
    "3_roofers_late_payments.csv": "Roofers - Late Payments",
    "4_roofers_quote_followup.csv": "Roofers - Quote Follow-up",
    "5_recruitment_timesheet_friday.csv": "Recruitment - Timesheet Friday",
    "6_recruitment_awr_compliance.csv": "Recruitment - AWR Compliance",
}

# Weekly schedule starting from the current week
WEEK_SCHEDULE = [
    "Week 1 - Mar 10-14",
    "Week 2 - Mar 17-21",
    "Week 3 - Mar 24-28",
    "Week 4 - Mar 31 - Apr 4",
    "Week 5 - Apr 7-11",
    "Week 6 - Apr 14-18",
]

MASTER_COLS = [
    "First Name",
    "Last Name",
    "Company",
    "Email",
    "Website",
    "City",
    "Campaign / Source",
    "Outreach Type",
    "Priority",
    "Week",
    "Status",
    "Notes",
    "Date Added",
]


# ─── Google Auth ─────────────────────────────────────────────────────────────

def get_google_creds():
    creds = None
    token_path = WORKSPACE_DIR / "token.json"
    creds_path = WORKSPACE_DIR / "credentials.json"

    if token_path.exists():
        try:
            with open(token_path, "r") as f:
                creds = Credentials.from_authorized_user_info(json.load(f), SCOPES)
        except Exception as e:
            print(f"  Warning: could not load token.json: {e}")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return creds


# ─── Instantly ───────────────────────────────────────────────────────────────

def get_all_campaigns():
    """Fetch all campaigns from Instantly v2 API (paginated)."""
    campaigns = []
    params = {"limit": 100}

    while True:
        resp = requests.get(
            f"{INSTANTLY_API_BASE}/campaigns",
            headers=INSTANTLY_HEADERS,
            params=params,
        )
        if resp.status_code != 200:
            print(f"  ⚠ Error fetching campaigns: {resp.status_code} {resp.text[:200]}")
            break

        data = resp.json()
        items = data.get("items", [])
        campaigns.extend(items)

        next_cursor = data.get("next_starting_after")
        if not next_cursor or not items:
            break
        params["starting_after"] = next_cursor

    return campaigns


def get_leads_for_campaign(campaign_id, campaign_name):
    """Fetch ALL leads for a campaign (paginated)."""
    leads = []
    params = {"campaign_id": campaign_id, "limit": 100}

    while True:
        resp = requests.get(
            f"{INSTANTLY_API_BASE}/leads",
            headers=INSTANTLY_HEADERS,
            params=params,
        )
        if resp.status_code != 200:
            print(f"    ⚠ Could not fetch leads ({resp.status_code}): {resp.text[:100]}")
            break

        data = resp.json()
        items = data.get("items", [])
        leads.extend(items)

        next_cursor = data.get("next_starting_after")
        if not next_cursor or not items:
            break
        params["starting_after"] = next_cursor
        time.sleep(0.1)

    return leads


def is_opener_no_reply(lead: dict) -> bool:
    """
    Return True if this lead opened the email sequence but has NOT replied.
    Instantly v2 stores engagement counters: lt_opened, lt_replied, etc.
    Falls back to boolean fields if counters are absent.
    """
    # Counter-based (most reliable)
    opened = lead.get("lt_opened", 0) or 0
    replied = lead.get("lt_replied", 0) or 0
    if opened > 0 and replied == 0:
        return True

    # Boolean fallback
    opened_bool = lead.get("opened") or lead.get("is_opened") or lead.get("has_opened")
    replied_bool = lead.get("replied") or lead.get("is_replied") or lead.get("has_replied")
    if opened_bool and not replied_bool:
        return True

    return False


def get_email_openers_no_reply():
    """
    Scan every Instantly campaign for leads who opened but didn't reply.

    NOTE: Instantly's open-tracking analytics (analytics/campaign/summary, unibox/emails)
    require a v1 API key, which is a different credential from the v2 Bearer token.
    Add INSTANTLY_V1_API_KEY to .env (from Instantly Dashboard → Settings → API Keys)
    to enable this feature. Until then, this function returns an empty list and a
    dedicated 'Email Openers (Add Manually)' tab is created in the sheet.
    """
    v1_key = os.getenv("INSTANTLY_V1_API_KEY") or os.getenv("INSTANTLY_API_KEY_V1")

    if not v1_key:
        print("  ⚠ No INSTANTLY_V1_API_KEY found — skipping open tracking.")
        print("    To enable: add INSTANTLY_V1_API_KEY to .env (Instantly → Settings → API Keys)")
        return []

    print("Step 1: Fetching Instantly campaigns...")
    campaigns = get_all_campaigns()
    print(f"  Found {len(campaigns)} campaigns")

    if not campaigns:
        print("  No campaigns found — check INSTANTLY_API_KEY")
        return []

    # v1 analytics endpoint for open tracking
    v1_headers = {"Authorization": f"Bearer {v1_key}"}
    all_openers = []

    for camp in campaigns:
        cid = camp.get("id")
        cname = camp.get("name", "Unknown")
        print(f"  Scanning: {cname}")

        # Fetch lead-level analytics from v1 API
        r = requests.get(
            "https://api.instantly.ai/api/v1/analytics/campaign/summary",
            params={"id": cid, "api_key": v1_key},
        )
        if r.status_code != 200:
            print(f"    ⚠ Could not fetch analytics ({r.status_code})")
            continue

        # Get all leads for this campaign
        leads = get_leads_for_campaign(cid, cname)
        openers = [l for l in leads if is_opener_no_reply(l)]
        print(f"    → {len(openers)} opened, no reply")

        for lead in openers:
            all_openers.append({
                "first_name": lead.get("first_name") or lead.get("firstName", ""),
                "last_name": lead.get("last_name") or lead.get("lastName", ""),
                "company_name": lead.get("company_name") or lead.get("company") or lead.get("companyName", ""),
                "email": lead.get("email", ""),
                "website": lead.get("website", ""),
                "city": lead.get("city", ""),
                "_campaign_name": cname,
                "_source": "Instantly – Opened (No Reply)",
            })

        time.sleep(0.2)

    print(f"\n  Total email openers (no reply): {len(all_openers)}")
    return all_openers


# ─── CSV Leads ───────────────────────────────────────────────────────────────

def read_csv_leads():
    """Read all leads from the campaign CSV files."""
    all_leads = []

    for csv_file in sorted(CSV_DIR.glob("*.csv")):
        campaign = CSV_CAMPAIGN_NAMES.get(csv_file.name, csv_file.stem.replace("_", " ").title())
        with open(csv_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                all_leads.append({
                    "first_name": row.get("first_name", ""),
                    "last_name": row.get("last_name", ""),
                    "company_name": row.get("company_name") or row.get("companyName", ""),
                    "email": row.get("email", ""),
                    "website": row.get("website", ""),
                    "city": row.get("city", ""),
                    "_campaign_name": campaign,
                    "_source": "Cold Email Sequence",
                })

    print(f"  Total CSV leads: {len(all_leads)}")
    return all_leads


# ─── Google Sheet Builder ─────────────────────────────────────────────────────

def build_row(lead: dict, outreach_type: str, priority: str, week: str, today: str) -> dict:
    return {
        "First Name": lead.get("first_name", "").strip(),
        "Last Name": lead.get("last_name", "").strip(),
        "Company": lead.get("company_name", "").strip(),
        "Email": lead.get("email", "").strip(),
        "Website": lead.get("website", "").strip(),
        "City": lead.get("city", "").strip(),
        "Campaign / Source": lead.get("_campaign_name", ""),
        "Outreach Type": outreach_type,
        "Priority": priority,
        "Week": week,
        "Status": "To Do",
        "Notes": "",
        "Date Added": today,
    }


def write_worksheet(ws, columns: list, rows: list):
    """Write headers + data to a worksheet in one batch update."""
    data = [columns] + [[row.get(col, "") for col in columns] for row in rows]
    ws.update(data, "A1")


def format_header_row(ws):
    """Bold + dark blue header row."""
    ws.format(
        "1:1",
        {
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
            "backgroundColor": {"red": 0.13, "green": 0.27, "blue": 0.53},
        },
    )


def create_outreach_sheet(gc, opener_leads: list, csv_leads: list) -> str:
    """Create the full Google Sheet and return its URL."""
    sheet_title = "Manual Outreach Leads — JP Automations"
    today = datetime.today().strftime("%d %b %Y")
    leads_per_week = 100

    print(f"\nStep 3: Creating Google Sheet: '{sheet_title}'")
    spreadsheet = gc.create(sheet_title)

    # ── Assign weeks ──────────────────────────────────────────────────────────
    all_rows = []

    # Email openers → Week 1 (warm, do first)
    # If no openers were fetched (no v1 key), they'll be added manually to the dedicated tab
    for lead in opener_leads:
        all_rows.append(build_row(lead, "Follow-up Call / Email", "High", WEEK_SCHEDULE[0], today))

    # CSV leads → Weeks 2+ distributed evenly
    for i, lead in enumerate(csv_leads):
        week_idx = min(1 + (i // leads_per_week), len(WEEK_SCHEDULE) - 1)
        all_rows.append(build_row(lead, "LinkedIn / Call", "Medium", WEEK_SCHEDULE[week_idx], today))

    # ── Master sheet ─────────────────────────────────────────────────────────
    master = spreadsheet.sheet1
    master.update_title("Manual Outreach Leads")
    write_worksheet(master, MASTER_COLS, all_rows)
    format_header_row(master)
    print(f"  ✓ Manual Outreach Leads — {len(all_rows)} leads total")
    time.sleep(1)

    # ── Weekly sheets ────────────────────────────────────────────────────────
    weeks = {}
    for row in all_rows:
        w = row["Week"]
        weeks.setdefault(w, []).append(row)

    for week_name in WEEK_SCHEDULE:
        week_rows = weeks.get(week_name, [])
        if not week_rows:
            continue
        ws = spreadsheet.add_worksheet(
            title=week_name,
            rows=str(len(week_rows) + 5),
            cols="15",
        )
        write_worksheet(ws, MASTER_COLS, week_rows)
        format_header_row(ws)
        print(f"  ✓ {week_name} — {len(week_rows)} leads")
        time.sleep(0.5)

    # ── Email Openers placeholder (if no v1 key) ─────────────────────────────
    if not opener_leads:
        opener_ws = spreadsheet.add_worksheet(
            title="Email Openers (Add Manually)",
            rows="200",
            cols="15",
        )
        write_worksheet(opener_ws, MASTER_COLS, [])
        format_header_row(opener_ws)
        # Add a note row explaining how to populate
        opener_ws.update(
            [["⚠ Add openers from Instantly dashboard here — leads who opened emails but didn't reply"]],
            "A2",
        )
        print(f"  ✓ Email Openers (Add Manually) — placeholder tab created")
        time.sleep(0.5)

    return spreadsheet.url


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  Manual Outreach Leads Sheet Builder")
    print("=" * 55)
    print()

    # 1. Instantly openers
    opener_leads = get_email_openers_no_reply()

    # 2. CSV cold leads
    print("\nStep 2: Reading cold email CSV leads...")
    csv_leads = read_csv_leads()

    total = len(opener_leads) + len(csv_leads)
    print(f"\n  Summary:")
    print(f"    Email openers (warm):  {len(opener_leads)}")
    print(f"    Cold email sequences:  {len(csv_leads)}")
    print(f"    Total leads:           {total}")

    # 3. Build sheet
    creds = get_google_creds()
    gc = gspread.authorize(creds)
    sheet_url = create_outreach_sheet(gc, opener_leads, csv_leads)

    print(f"\n{'=' * 55}")
    print(f"  ✅ Done!")
    print(f"  Sheet URL: {sheet_url}")
    print(f"{'=' * 55}")
    return sheet_url


if __name__ == "__main__":
    main()
