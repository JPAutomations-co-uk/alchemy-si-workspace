#!/usr/bin/env python3
"""
Voicemail Auto-Text

After leaving a voicemail during cold calling, immediately sends a
follow-up SMS via Twilio and adds the prospect to the follow-up sequence.

Usage:
    python3 .claude/skills/lead-pipeline/scripts/voicemail_followup.py \
        --name "Dave" --phone "+447xxx" --trade "roofer" --area "Birmingham" \
        --sheet-url "https://docs.google.com/spreadsheets/d/..."

    # Without Twilio (prints message for manual sending):
    python3 .claude/skills/lead-pipeline/scripts/voicemail_followup.py \
        --name "Dave" --phone "07xxx" --trade "roofer" --manual
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

# Sub-niche specific message variants
MESSAGES = {
    "roofer": "Hey {name}, just left you a voicemail. I help roofing businesses automate invoicing, follow-ups, and admin — one of my clients cut their outstanding invoices from £8,400 to £320 in 8 weeks. Happy to do a free 15-min audit to see where you're leaking time. No commitment. — JP",
    "plumber": "Hey {name}, just left you a voicemail. I help plumbers and heating engineers stop losing jobs to missed calls — built a system for a heating engineer in Leeds that booked 14 extra jobs/month he was previously losing. Happy to do a free 15-min audit. No commitment. — JP",
    "heating": "Hey {name}, just left you a voicemail. I help heating engineers stop losing jobs to missed calls during peak season — one client recovered £16,800 in a single winter. Happy to do a free 15-min audit. No commitment. — JP",
    "electrician": "Hey {name}, just left you a voicemail. I help electricians cut admin time — certificates, building control notifications, CIS, all automated. One client went from 8hrs/week admin to 30 minutes. Happy to do a free 15-min audit. No commitment. — JP",
    "builder": "Hey {name}, just left you a voicemail. I help builders track job costs in real-time and automate CIS returns — one client's margins went from 8% to 16% after we built their system. Happy to do a free 15-min audit. No commitment. — JP",
    "landscaper": "Hey {name}, just left you a voicemail. I help landscapers build recurring revenue — one client went from £4k winter months to £8k+ with automated maintenance plans. Happy to do a free 15-min audit. No commitment. — JP",
    "default": "Hey {name}, just left you a voicemail. I help trade businesses automate the admin that eats their evenings — invoicing, follow-ups, all of it. Happy to do a free 15-min audit to see where you're leaking time. No commitment. — JP",
}


def format_phone(phone):
    """Format UK phone number for Twilio."""
    phone = phone.strip().replace(" ", "").replace("-", "")
    if phone.startswith("0"):
        phone = "+44" + phone[1:]
    elif not phone.startswith("+"):
        phone = "+44" + phone
    return phone


def send_sms(phone, message):
    """Send SMS via Twilio."""
    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_from = os.getenv("TWILIO_PHONE_NUMBER")

    if not all([twilio_sid, twilio_token, twilio_from]):
        return False, "Twilio credentials not configured"

    try:
        from twilio.rest import Client
        client = Client(twilio_sid, twilio_token)
        msg = client.messages.create(
            body=message,
            from_=twilio_from,
            to=phone,
        )
        return True, msg.sid
    except Exception as e:
        return False, str(e)


def add_to_pipeline_sheet(sheet_url, name, phone, trade, area, business=""):
    """Add the prospect to the pipeline tracker and follow-up sequence."""
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
        sheet_id = sheet_url.split("/d/")[1].split("/")[0]
        spreadsheet = gc.open_by_key(sheet_id)

        # Add to Pipeline sheet
        try:
            pipeline = spreadsheet.worksheet("Pipeline")
        except Exception:
            pipeline = spreadsheet.add_worksheet("Pipeline", rows=1000, cols=20)
            headers = [
                "Name", "Business", "Phone", "Email", "Trade", "Area",
                "Source", "Status", "First Contact", "Last Contact",
                "Next Action", "Next Action Date", "Notes", "Deal Value",
            ]
            pipeline.update("A1:N1", [headers])

        today = datetime.now().strftime("%Y-%m-%d")
        pipeline.append_row([
            name, business, phone, "", trade, area,
            "Cold Call", "Voicemail Left", today, today,
            "Follow-up text sent, wait for reply", "", "", "",
        ])
        print(f"  ✓ Added to pipeline sheet")

        # Add to Follow-Ups sheet
        try:
            followups = spreadsheet.worksheet("Follow-Ups")
        except Exception:
            followups = spreadsheet.add_worksheet("Follow-Ups", rows=1000, cols=20)
            headers = [
                "Name", "Business", "Email", "Phone", "Trade",
                "Sequence", "Current Step", "Sequence Start Date",
                "Next Follow-Up Date", "Status", "Notes",
                "Key Pain", "Estimated Impact", "Loom Link",
            ]
            followups.update("A1:N1", [headers])

        from datetime import timedelta
        next_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        followups.append_row([
            name, business, "", phone, trade,
            "post_voicemail", "1", today,  # Step 1 = immediate text already sent
            next_date, "active", f"Cold call voicemail - {area}",
            "", "", "",
        ])
        print(f"  ✓ Added to follow-up sequence (next: {next_date})")

        return True
    except Exception as e:
        print(f"  ⚠ Sheet update failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Voicemail Auto-Text")
    parser.add_argument("--name", type=str, required=True, help="Prospect's first name")
    parser.add_argument("--phone", type=str, required=True, help="Phone number")
    parser.add_argument("--trade", type=str, default="default", help="Trade type (roofer, plumber, electrician, builder, landscaper)")
    parser.add_argument("--area", type=str, default="", help="Location/area")
    parser.add_argument("--business", type=str, default="", help="Business name")
    parser.add_argument("--sheet-url", type=str, help="Pipeline tracker sheet URL")
    parser.add_argument("--manual", action="store_true", help="Don't send SMS — just print the message")
    args = parser.parse_args()

    # Get the right message template
    trade_key = args.trade.lower()
    template = MESSAGES.get(trade_key, MESSAGES["default"])
    message = template.format(name=args.name)

    formatted_phone = format_phone(args.phone)

    print(f"\n  Voicemail Follow-Up — {args.name}")
    print(f"  Phone: {formatted_phone}")
    print(f"  Trade: {args.trade}")
    print(f"  Message: {message[:80]}...")

    if args.manual:
        print(f"\n  📱 SEND MANUALLY:")
        print(f"  To: {formatted_phone}")
        print(f"  Message:\n{message}")
    else:
        success, result = send_sms(formatted_phone, message)
        if success:
            print(f"\n  ✓ SMS sent! SID: {result}")
        else:
            print(f"\n  ✗ SMS failed: {result}")
            print(f"\n  📱 SEND MANUALLY:")
            print(f"  To: {formatted_phone}")
            print(f"  Message:\n{message}")

    # Add to pipeline sheet
    if args.sheet_url:
        add_to_pipeline_sheet(args.sheet_url, args.name, formatted_phone, args.trade, args.area, args.business)

    # Log
    log_activity(
        agent_id="voicemail_followup",
        event_type="text_sent",
        message=f"Voicemail follow-up text for {args.name} ({args.trade})",
        metrics={"trade": args.trade, "manual": args.manual},
    )


if __name__ == "__main__":
    main()
