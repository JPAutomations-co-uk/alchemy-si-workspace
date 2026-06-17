#!/usr/bin/env python3
"""
Follow-Up Sequence Engine

Manages time-based follow-up sequences across the sales pipeline.
Reads from the pipeline tracker sheet, checks what follow-ups are due,
and sends them via the appropriate channel (email, SMS/WhatsApp).

Sequences:
  1. Post-voicemail: auto-text immediately + 48hr follow-up
  2. Post-quick-wins: check-in at Day 3
  3. Post-proposal: reminders at 24hr, 48hr, 72hr
  4. Post-call-no-close: Day 1 Loom, Day 3 check-in, Day 7 value, Day 14 check-in, Day 30 case study
  5. Nurture (cold): monthly value touch

Usage:
    python3 .claude/skills/lead-pipeline/scripts/follow_up_engine.py --sheet-url "..."
    python3 .claude/skills/lead-pipeline/scripts/follow_up_engine.py --sheet-url "..." --dry-run
    python3 .claude/skills/lead-pipeline/scripts/follow_up_engine.py --add --name "Dave" --email "dave@example.com" --sequence post_voicemail --sheet-url "..."
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
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

# ── Follow-up sequence definitions ──────────────────────────────

SEQUENCES = {
    "post_voicemail": {
        "name": "Post-Voicemail",
        "steps": [
            {"day": 0, "channel": "sms", "template": "voicemail_immediate"},
            {"day": 2, "channel": "sms", "template": "voicemail_48hr"},
        ],
    },
    "post_quickwins": {
        "name": "Post-Quick Wins Sent",
        "steps": [
            {"day": 3, "channel": "email", "template": "quickwins_checkin"},
            {"day": 7, "channel": "email", "template": "quickwins_value"},
        ],
    },
    "post_proposal": {
        "name": "Post-Proposal",
        "steps": [
            {"day": 1, "channel": "email", "template": "proposal_24hr"},
            {"day": 2, "channel": "email", "template": "proposal_48hr"},
            {"day": 3, "channel": "email", "template": "proposal_72hr"},
        ],
    },
    "post_call_no_close": {
        "name": "Post-Call (No Close)",
        "steps": [
            {"day": 1, "channel": "email", "template": "postcall_loom"},
            {"day": 3, "channel": "email", "template": "postcall_checkin"},
            {"day": 7, "channel": "email", "template": "postcall_value"},
            {"day": 14, "channel": "sms", "template": "postcall_casual"},
            {"day": 30, "channel": "email", "template": "postcall_casestudy"},
        ],
    },
    "nurture": {
        "name": "Long-Term Nurture",
        "steps": [
            {"day": 30, "channel": "email", "template": "nurture_value"},
            {"day": 60, "channel": "email", "template": "nurture_final"},
        ],
    },
}

# ── Message templates ───────────────────────────────────────────

TEMPLATES = {
    # SMS templates (keep under 160 chars where possible)
    "voicemail_immediate": {
        "channel": "sms",
        "message": "Hey {name}, just left you a voicemail. I help {trade} businesses automate the admin that eats their evenings — invoicing, follow-ups, all of it. Happy to do a free 15-min audit if you want to see where you're leaking time. No commitment. — JP",
    },
    "voicemail_48hr": {
        "channel": "sms",
        "message": "Hi {name}, JP here again. Tried you the other day about automating your admin. I helped a {trade} business cut their invoicing time to zero and get paid in 6 days instead of 34. If that sounds useful, happy to show you how. Just reply and I'll send over some times. — JP",
    },
    "postcall_casual": {
        "channel": "sms",
        "message": "Hey {name}, JP here. Still thinking about what we discussed? No pressure — just wanted to check if anything's changed on your end. Happy to jump on a quick call if useful. — JP",
    },

    # Email templates
    "quickwins_checkin": {
        "channel": "email",
        "subject": "Did you get a chance to look at that, {name}?",
        "body": """Hi {name},

Sent over those quick wins for {business} a couple of days ago — just wanted to check you got them.

The {highlight_win} alone could save you {estimated_impact}. Happy to walk through it properly if you want — takes 15 minutes.

Thanks,
JP""",
    },
    "quickwins_value": {
        "channel": "email",
        "subject": "Quick thought for {business}",
        "body": """Hi {name},

Was looking at something for another {trade} client and thought of you.

{value_insight}

If you ever want to revisit those quick wins, the offer's still there. No expiry.

Thanks,
JP""",
    },
    "proposal_24hr": {
        "channel": "email",
        "subject": "Following up — {business} proposal",
        "body": """Hi {name},

Just checking you received the proposal I sent through yesterday. Everything we discussed is in there — the {key_system}, timeline, and guarantee.

Any questions at all, just reply or give me a ring.

Thanks,
JP""",
    },
    "proposal_48hr": {
        "channel": "email",
        "subject": "Quick recap for {business}",
        "body": """Hi {name},

Wanted to send a quick recap of what we discussed and why I think this is the right move for {business} right now.

I've recorded a short walkthrough — {loom_link}

The main thing: {key_pain} is costing you roughly {cost_of_inaction} every month. The system I've proposed pays for itself inside 90 days — guaranteed.

Happy to jump on a 5-minute call if anything needs clarifying.

Thanks,
JP""",
    },
    "proposal_72hr": {
        "channel": "email",
        "subject": "Last one from me, {name}",
        "body": """Hi {name},

Don't want to be a pest — this is my last follow-up on the proposal.

The offer stands whenever you're ready. If the timing's not right, no hard feelings. But if {key_pain} is still eating your evenings, the fix is ready to go.

Either way, thanks for your time on the call.

Thanks,
JP""",
    },
    "postcall_loom": {
        "channel": "email",
        "subject": "Quick recap — what we talked about",
        "body": """Hi {name},

Good chatting earlier. As promised, here's a quick walkthrough of what I'd build for {business}: {loom_link}

The three things that jumped out:
1. {win_1}
2. {win_2}
3. {win_3}

Happy to answer any questions. I'll send a proposal over shortly.

Thanks,
JP""",
    },
    "postcall_checkin": {
        "channel": "email",
        "subject": "Any questions, {name}?",
        "body": """Hi {name},

Just checking in after our call. Had a chance to think things over?

If anything's unclear or you want to discuss further, I'm around. The quick wins I spotted aren't going anywhere — but every week they're not fixed, they're costing you.

Thanks,
JP""",
    },
    "postcall_value": {
        "channel": "email",
        "subject": "Thought you'd find this useful",
        "body": """Hi {name},

{value_content}

Reminded me of what we discussed for {business}. The offer's still open whenever you're ready.

Thanks,
JP""",
    },
    "postcall_casestudy": {
        "channel": "email",
        "subject": "Just finished a project you might relate to",
        "body": """Hi {name},

Just wrapped up a project for a {case_study_trade} business — similar situation to yours.

{case_study_summary}

If you're still dealing with {key_pain}, the offer stands. Happy to pick up where we left off.

Thanks,
JP""",
    },
    "nurture_value": {
        "channel": "email",
        "subject": "Quick insight for {trade} businesses",
        "body": """Hi {name},

{nurture_insight}

If anything's changed on your end and you want to revisit automation, I'm around.

Thanks,
JP""",
    },
    "nurture_final": {
        "channel": "email",
        "subject": "Keeping the door open, {name}",
        "body": """Hi {name},

Haven't been in touch for a while — just wanted to say the offer's still there whenever the timing's right.

If {key_pain} is still a problem, I can fix it. If you've sorted it another way, genuinely happy for you.

Either way, thanks for your time back when we spoke.

Thanks,
JP""",
    },
}


def get_sheets_client():
    """Get authenticated Google Sheets client."""
    token_path = os.path.join(WORKSPACE, "token.json")
    creds = Credentials.from_authorized_user_file(token_path, [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ])
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return gspread.authorize(creds)


def get_due_followups(sheet_url):
    """Read the follow-up tracker sheet and return rows where a follow-up is due."""
    gc = get_sheets_client()
    sheet_id = sheet_url.split("/d/")[1].split("/")[0]
    spreadsheet = gc.open_by_key(sheet_id)

    try:
        worksheet = spreadsheet.worksheet("Follow-Ups")
    except gspread.WorksheetNotFound:
        print("No 'Follow-Ups' worksheet found. Creating one...")
        worksheet = spreadsheet.add_worksheet("Follow-Ups", rows=1000, cols=20)
        headers = [
            "Name", "Business", "Email", "Phone", "Trade",
            "Sequence", "Current Step", "Sequence Start Date",
            "Next Follow-Up Date", "Status", "Notes",
            "Key Pain", "Estimated Impact", "Loom Link",
        ]
        worksheet.update("A1:N1", [headers])
        return [], worksheet

    records = worksheet.get_all_records()
    today = datetime.now().date()
    due = []

    for i, record in enumerate(records):
        if record.get("Status", "").lower() in ["completed", "closed", "dead"]:
            continue

        next_date_str = record.get("Next Follow-Up Date", "")
        if not next_date_str:
            continue

        try:
            next_date = datetime.strptime(next_date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue

        if next_date <= today:
            record["_row_index"] = i + 2  # +2 for header + 0-indexing
            due.append(record)

    return due, worksheet


def send_email_followup(record, template):
    """Send an email follow-up via Gmail."""
    try:
        # Build message from template
        subject = template.get("subject", "Following up").format(**{
            "name": record.get("Name", ""),
            "business": record.get("Business", ""),
            "trade": record.get("Trade", ""),
        })

        body = template.get("body", "").format(**{
            "name": record.get("Name", "there"),
            "business": record.get("Business", "your business"),
            "trade": record.get("Trade", "trade"),
            "key_pain": record.get("Key Pain", "admin overhead"),
            "estimated_impact": record.get("Estimated Impact", "significant time"),
            "highlight_win": record.get("Key Pain", "the admin automation"),
            "loom_link": record.get("Loom Link", "[Loom link to be added]"),
            "cost_of_inaction": record.get("Estimated Impact", "£X"),
            "key_system": "automation system",
            "win_1": "Invoice automation",
            "win_2": "Lead follow-up",
            "win_3": "Review collection",
            "value_insight": f"Many {record.get('Trade', 'trade')} businesses are losing £24k/year from missed calls alone.",
            "value_content": f"Just read that 81% of tradespeople are currently owed money — average of £6,200 outstanding.",
            "case_study_trade": record.get("Trade", "trade"),
            "case_study_summary": "Results: invoicing time went to zero, payments arrived in 6 days instead of 34.",
            "nurture_insight": f"UK trades businesses are losing an average of £24,000/year from missed calls. Most don't even know it's happening.",
        })

        email = record.get("Email", "")
        if not email:
            print(f"  ⚠ No email for {record.get('Name', 'Unknown')}")
            return False

        # Use Gmail API to send
        from google.oauth2.credentials import Credentials as GmailCreds
        from googleapiclient.discovery import build
        from email.mime.text import MIMEText
        import base64

        token_path = os.path.join(WORKSPACE, "token.json")
        creds = GmailCreds.from_authorized_user_file(token_path, [
            "https://www.googleapis.com/auth/gmail.send",
        ])
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

        service = build("gmail", "v1", credentials=creds)

        message = MIMEText(body)
        message["to"] = email
        message["subject"] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(
            userId="me",
            body={"raw": raw},
        ).execute()

        print(f"  ✓ Email sent to {email}: {subject}")
        return True

    except Exception as e:
        print(f"  ✗ Email failed for {record.get('Name', 'Unknown')}: {e}")
        return False


def send_sms_followup(record, template):
    """Send an SMS follow-up via Twilio."""
    phone = record.get("Phone", "")
    if not phone:
        print(f"  ⚠ No phone for {record.get('Name', 'Unknown')}")
        return False

    message = template.get("message", "").format(**{
        "name": record.get("Name", "there"),
        "business": record.get("Business", "your business"),
        "trade": record.get("Trade", "trade"),
    })

    # Try Twilio
    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_from = os.getenv("TWILIO_PHONE_NUMBER")

    if twilio_sid and twilio_token and twilio_from:
        try:
            from twilio.rest import Client
            client = Client(twilio_sid, twilio_token)
            client.messages.create(
                body=message,
                from_=twilio_from,
                to=phone,
            )
            print(f"  ✓ SMS sent to {phone}")
            return True
        except Exception as e:
            print(f"  ✗ Twilio SMS failed: {e}")
            return False
    else:
        # No Twilio — output for manual sending
        print(f"  📱 MANUAL SMS needed → {phone}")
        print(f"     Message: {message[:100]}...")
        return True  # Mark as done — user sends manually


def process_followup(record, worksheet, dry_run=False):
    """Process a single follow-up that's due."""
    name = record.get("Name", "Unknown")
    sequence_name = record.get("Sequence", "")
    current_step = int(record.get("Current Step", 0))

    sequence = SEQUENCES.get(sequence_name)
    if not sequence:
        print(f"  ⚠ Unknown sequence '{sequence_name}' for {name}")
        return

    if current_step >= len(sequence["steps"]):
        print(f"  ✓ {name}: sequence complete")
        # Update status to completed
        if not dry_run:
            row = record["_row_index"]
            worksheet.update_cell(row, 10, "completed")  # Status column
        return

    step = sequence["steps"][current_step]
    template_key = step["template"]
    template = TEMPLATES.get(template_key)

    if not template:
        print(f"  ⚠ Unknown template '{template_key}' for {name}")
        return

    print(f"\n  {name} ({record.get('Business', '')}) — {sequence['name']} Step {current_step + 1}/{len(sequence['steps'])}")

    if dry_run:
        print(f"    Would send {step['channel']}: {template_key}")
        return

    # Send the follow-up
    if step["channel"] == "email":
        success = send_email_followup(record, template)
    elif step["channel"] == "sms":
        success = send_sms_followup(record, template)
    else:
        print(f"  ⚠ Unknown channel: {step['channel']}")
        return

    if success:
        # Advance to next step
        next_step = current_step + 1
        row = record["_row_index"]

        if next_step < len(sequence["steps"]):
            next_step_def = sequence["steps"][next_step]
            start_date = datetime.strptime(record.get("Sequence Start Date", datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d")
            next_date = start_date + timedelta(days=next_step_def["day"])

            worksheet.update_cell(row, 7, str(next_step))  # Current Step
            worksheet.update_cell(row, 9, next_date.strftime("%Y-%m-%d"))  # Next Follow-Up Date
        else:
            worksheet.update_cell(row, 7, str(next_step))  # Current Step
            worksheet.update_cell(row, 9, "")  # Clear next date
            worksheet.update_cell(row, 10, "completed")  # Status


def add_to_sequence(worksheet, name, business, email, phone, trade, sequence_name, notes="", key_pain="", estimated_impact="", loom_link=""):
    """Add a new prospect to a follow-up sequence."""
    sequence = SEQUENCES.get(sequence_name)
    if not sequence:
        print(f"Unknown sequence: {sequence_name}")
        return

    today = datetime.now()
    first_step = sequence["steps"][0]
    next_date = today + timedelta(days=first_step["day"])

    row = [
        name, business, email, phone, trade,
        sequence_name, "0", today.strftime("%Y-%m-%d"),
        next_date.strftime("%Y-%m-%d"), "active", notes,
        key_pain, estimated_impact, loom_link,
    ]

    worksheet.append_row(row)
    print(f"✓ Added {name} ({business}) to {sequence['name']} sequence")
    print(f"  Next follow-up: {next_date.strftime('%Y-%m-%d')} via {first_step['channel']}")


def main():
    parser = argparse.ArgumentParser(description="Follow-Up Sequence Engine")
    parser.add_argument("--sheet-url", type=str, required=True, help="Pipeline tracker Google Sheet URL")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be sent without sending")

    # Add mode
    parser.add_argument("--add", action="store_true", help="Add a prospect to a sequence")
    parser.add_argument("--name", type=str, help="Prospect name")
    parser.add_argument("--business", type=str, help="Business name")
    parser.add_argument("--email", type=str, help="Email address")
    parser.add_argument("--phone", type=str, default="", help="Phone number")
    parser.add_argument("--trade", type=str, default="trade", help="Trade type")
    parser.add_argument("--sequence", type=str, help="Sequence name (post_voicemail, post_quickwins, post_proposal, post_call_no_close, nurture)")
    parser.add_argument("--notes", type=str, default="", help="Notes")
    parser.add_argument("--key-pain", type=str, default="", help="Key pain point")
    parser.add_argument("--estimated-impact", type=str, default="", help="Estimated impact")
    parser.add_argument("--loom-link", type=str, default="", help="Loom video link")

    args = parser.parse_args()

    if args.add:
        if not args.name or not args.sequence:
            parser.error("--add requires --name and --sequence")

        gc = get_sheets_client()
        sheet_id = args.sheet_url.split("/d/")[1].split("/")[0]
        spreadsheet = gc.open_by_key(sheet_id)

        try:
            worksheet = spreadsheet.worksheet("Follow-Ups")
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet("Follow-Ups", rows=1000, cols=20)
            headers = [
                "Name", "Business", "Email", "Phone", "Trade",
                "Sequence", "Current Step", "Sequence Start Date",
                "Next Follow-Up Date", "Status", "Notes",
                "Key Pain", "Estimated Impact", "Loom Link",
            ]
            worksheet.update("A1:N1", [headers])

        add_to_sequence(
            worksheet, args.name, args.business or "", args.email or "", args.phone,
            args.trade, args.sequence, args.notes, args.key_pain, args.estimated_impact, args.loom_link,
        )
        return

    # Process mode — check for due follow-ups and send them
    print(f"\n{'='*60}")
    print(f"  FOLLOW-UP ENGINE — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")

    due_followups, worksheet = get_due_followups(args.sheet_url)

    if not due_followups:
        print("\n  No follow-ups due today.")
        return

    print(f"\n  {len(due_followups)} follow-up(s) due today:")

    for record in due_followups:
        process_followup(record, worksheet, dry_run=args.dry_run)

    # Log
    log_activity(
        agent_id="follow_up_engine",
        event_type="followups_processed",
        message=f"Processed {len(due_followups)} follow-ups",
        metrics={"due_count": len(due_followups), "dry_run": args.dry_run},
    )

    print(f"\n{'='*60}")
    print(f"  Done. {len(due_followups)} follow-ups processed.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
