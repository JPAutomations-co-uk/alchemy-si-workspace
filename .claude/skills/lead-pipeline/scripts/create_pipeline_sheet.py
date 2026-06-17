#!/usr/bin/env python3
"""
Pipeline Tracker Sheet Creator

Creates a structured Google Sheet with all necessary tabs for
managing the full sales pipeline:

  1. Pipeline — Master CRM view of all prospects
  2. Follow-Ups — Automated follow-up sequence tracker
  3. Call Log — Daily cold calling log
  4. Metrics — Weekly/monthly KPI dashboard
  5. Clients — Active client management

Usage:
    python3 .claude/skills/lead-pipeline/scripts/create_pipeline_sheet.py
    python3 .claude/skills/lead-pipeline/scripts/create_pipeline_sheet.py --name "JP Pipeline — March 2026"
"""

import os
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

try:
    sys.path.insert(0, WORKSPACE)
    from execution.log_activity import log_activity
except Exception:
    def log_activity(*a, **kw): pass

try:
    import gspread
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
except ImportError:
    print("pip install gspread google-auth required", file=sys.stderr)
    sys.exit(1)


def get_sheets_client():
    token_path = os.path.join(WORKSPACE, "token.json")
    creds = Credentials.from_authorized_user_file(token_path, [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ])
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return gspread.authorize(creds)


def create_pipeline_sheet(name=None):
    gc = get_sheets_client()

    if not name:
        name = f"JP Pipeline — {datetime.now().strftime('%B %Y')}"

    print(f"Creating pipeline sheet: {name}")
    spreadsheet = gc.create(name)

    # ── Tab 1: Pipeline (Master CRM) ──────────────────────────
    pipeline = spreadsheet.sheet1
    pipeline.update_title("Pipeline")
    pipeline_headers = [[
        "Name", "Business", "Phone", "Email", "Trade", "Area",
        "Source", "Status", "First Contact", "Last Contact",
        "Next Action", "Next Action Date", "Deal Value",
        "Sub-Niche", "Google Rating", "Reviews", "Website", "Notes",
    ]]
    pipeline.update(values=pipeline_headers, range_name="A1:R1")

    # Status values for reference
    # cold | voicemail_left | contacted | call_booked | call_completed |
    # proposal_sent | negotiating | closed_won | closed_lost | nurture

    # ── Tab 2: Follow-Ups ─────────────────────────────────────
    followups = spreadsheet.add_worksheet("Follow-Ups", rows=1000, cols=20)
    followup_headers = [[
        "Name", "Business", "Email", "Phone", "Trade",
        "Sequence", "Current Step", "Sequence Start Date",
        "Next Follow-Up Date", "Status", "Notes",
        "Key Pain", "Estimated Impact", "Loom Link",
    ]]
    followups.update(values=followup_headers, range_name="A1:N1")

    # ── Tab 3: Call Log ───────────────────────────────────────
    call_log = spreadsheet.add_worksheet("Call Log", rows=1000, cols=15)
    calllog_headers = [[
        "Date", "Name", "Business", "Phone", "Trade", "Area",
        "Outcome", "Notes", "Follow-Up Action", "Callback Date", "Added to Pipeline",
    ]]
    call_log.update(values=calllog_headers, range_name="A1:K1")
    # Outcome values: answered_interested | answered_not_interested |
    # voicemail | no_answer | gatekeeper | wrong_number | callback_requested

    # ── Tab 4: Metrics ────────────────────────────────────────
    metrics = spreadsheet.add_worksheet("Metrics", rows=100, cols=15)
    metrics_headers = [[
        "Week Starting", "Calls Made", "Conversations", "Voicemails",
        "Calls Booked", "Sales Calls Done", "Proposals Sent",
        "Deals Closed", "Revenue Closed", "LinkedIn Requests",
        "LinkedIn DMs", "Content Posted",
    ]]
    metrics.update(values=metrics_headers, range_name="A1:L1")

    # Add Week 1 template row
    from datetime import timedelta
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    metrics.update(values=[[
        monday.strftime("%Y-%m-%d"), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    ]], range_name="A2:L2")

    # ── Tab 5: Clients ────────────────────────────────────────
    clients = spreadsheet.add_worksheet("Clients", rows=100, cols=20)
    client_headers = [[
        "Client Name", "Business", "Email", "Phone", "Trade",
        "Deal Value", "Start Date", "Delivery Status",
        "Day 7 Check-In", "Day 30 Check-In", "Testimonial Collected",
        "Review Requested", "Phase 2 Discussed", "Retainer Offered",
        "Referral Asked", "Notes",
    ]]
    clients.update(values=client_headers, range_name="A1:P1")
    # Delivery Status: onboarding | building | testing | delivered | active | churned

    # Make sheet accessible
    spreadsheet.share(None, perm_type="anyone", role="writer")
    sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}"

    print(f"\n✓ Pipeline sheet created!")
    print(f"  URL: {sheet_url}")
    print(f"\n  Tabs:")
    print(f"    1. Pipeline — Track all prospects and their status")
    print(f"    2. Follow-Ups — Automated follow-up sequence management")
    print(f"    3. Call Log — Log every cold call outcome")
    print(f"    4. Metrics — Weekly KPI tracking")
    print(f"    5. Clients — Active client management and retention")

    log_activity(
        agent_id="pipeline_tracker",
        event_type="sheet_created",
        message=f"Pipeline tracker created: {name}",
        metrics={"sheet_url": sheet_url},
    )

    return sheet_url


def main():
    parser = argparse.ArgumentParser(description="Create Pipeline Tracker Sheet")
    parser.add_argument("--name", type=str, default=None, help="Sheet name")
    args = parser.parse_args()

    url = create_pipeline_sheet(args.name)
    print(f"\n{url}")


if __name__ == "__main__":
    main()
