#!/usr/bin/env python3
"""
Post-Delivery Review Request

Sends an automated review request to clients after job completion.
Triggered manually or via webhook at the Day 30 check-in milestone.

Supports:
  - SMS via Twilio (primary — highest open rate)
  - Email via Gmail (fallback)
  - Manual mode (prints message for WhatsApp copy-paste)

Usage:
    python3 .claude/skills/lead-pipeline/scripts/review_request.py \
        --name "Dave" --business "ACE Roofing" --phone "+447xxx" \
        --google-review-url "https://g.page/r/..."

    python3 .claude/skills/lead-pipeline/scripts/review_request.py \
        --name "Dave" --email "dave@aceroofing.co.uk" --channel email \
        --google-review-url "https://g.page/r/..."
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

# Review request templates
SMS_TEMPLATE = """Hi {name}, it's JP from JP Automations.

Hope the system's running well for {business}. Quick favour — would you mind leaving a short Google review? Just a couple of sentences on what changed would be brilliant.

Here's the link: {review_url}

Really appreciate it. Thanks, JP"""

EMAIL_SUBJECT = "Quick favour, {name}"
EMAIL_TEMPLATE = """Hi {name},

Hope everything's running smoothly with the systems we built for {business}.

I've got a quick favour to ask — would you mind leaving a short Google review? Doesn't need to be long — just a couple of sentences on what's changed since we set things up.

Here's the direct link: {review_url}

It genuinely helps other business owners in your position find me, and I'd really appreciate it.

Thanks,
JP"""

# Default Google review URL — replace with your actual Google Business Profile review link
DEFAULT_REVIEW_URL = "https://g.page/r/jpautomations/review"


def send_review_sms(phone, message):
    """Send review request via Twilio SMS."""
    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_from = os.getenv("TWILIO_PHONE_NUMBER")

    if not all([twilio_sid, twilio_token, twilio_from]):
        return False, "Twilio not configured"

    try:
        from twilio.rest import Client
        client = Client(twilio_sid, twilio_token)
        msg = client.messages.create(body=message, from_=twilio_from, to=phone)
        return True, msg.sid
    except Exception as e:
        return False, str(e)


def send_review_email(email, name, message):
    """Send review request via Gmail."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from email.mime.text import MIMEText
        import base64

        token_path = os.path.join(WORKSPACE, "token.json")
        creds = Credentials.from_authorized_user_file(token_path, [
            "https://www.googleapis.com/auth/gmail.send",
        ])
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

        service = build("gmail", "v1", credentials=creds)

        subject = EMAIL_SUBJECT.format(name=name)
        msg = MIMEText(message)
        msg["to"] = email
        msg["subject"] = subject

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return True, "sent"
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(description="Post-Delivery Review Request")
    parser.add_argument("--name", type=str, required=True, help="Client name")
    parser.add_argument("--business", type=str, default="your business", help="Business name")
    parser.add_argument("--phone", type=str, default="", help="Phone number")
    parser.add_argument("--email", type=str, default="", help="Email address")
    parser.add_argument("--channel", type=str, default="sms", choices=["sms", "email", "manual"],
                        help="Delivery channel (default: sms)")
    parser.add_argument("--google-review-url", type=str, default=DEFAULT_REVIEW_URL,
                        help="Google review URL")
    args = parser.parse_args()

    review_url = args.google_review_url

    if args.channel == "sms" or (args.channel != "email" and args.phone):
        message = SMS_TEMPLATE.format(name=args.name, business=args.business, review_url=review_url)

        if not args.phone:
            args.channel = "manual"
        else:
            # Format UK phone
            phone = args.phone.strip().replace(" ", "").replace("-", "")
            if phone.startswith("0"):
                phone = "+44" + phone[1:]

            print(f"Sending review request to {args.name} via SMS...")
            success, result = send_review_sms(phone, message)

            if success:
                print(f"✓ SMS sent! SID: {result}")
            else:
                print(f"✗ SMS failed: {result}")
                args.channel = "manual"
                print("Falling back to manual mode...")

    if args.channel == "email":
        message = EMAIL_TEMPLATE.format(name=args.name, business=args.business, review_url=review_url)

        if not args.email:
            print("No email provided — switching to manual mode")
            args.channel = "manual"
        else:
            print(f"Sending review request to {args.name} via email...")
            success, result = send_review_email(args.email, args.name, message)

            if success:
                print(f"✓ Email sent to {args.email}")
            else:
                print(f"✗ Email failed: {result}")
                args.channel = "manual"

    if args.channel == "manual":
        message = SMS_TEMPLATE.format(name=args.name, business=args.business, review_url=review_url)
        print(f"\n📱 SEND MANUALLY (WhatsApp/text):")
        print(f"To: {args.phone or args.email or '[no contact]'}")
        print(f"\n{message}")

    log_activity(
        agent_id="review_request",
        event_type="review_requested",
        message=f"Review request sent to {args.name} ({args.business}) via {args.channel}",
        metrics={"channel": args.channel, "business": args.business},
    )


if __name__ == "__main__":
    main()
