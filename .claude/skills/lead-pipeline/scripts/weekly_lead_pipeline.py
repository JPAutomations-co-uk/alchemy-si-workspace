#!/usr/bin/env python3
"""
Weekly Lead Pipeline Orchestrator

Fully automated pipeline that runs weekly (Monday 6am):
1. Scrapes Google Maps for trades businesses across target areas
2. Filters by quality gate + trades classification
3. Casualizes names for outreach
4. Pushes qualified leads to Call Sheet (for cold calling)
5. Pushes LinkedIn-ready leads to Dripify
6. Logs activity to Supabase

Usage:
    python3 .claude/skills/lead-pipeline/scripts/weekly_lead_pipeline.py
    python3 .claude/skills/lead-pipeline/scripts/weekly_lead_pipeline.py --niches "roofers,plumbers" --areas "Birmingham,Manchester,Leeds"
    python3 .claude/skills/lead-pipeline/scripts/weekly_lead_pipeline.py --sheet-url "https://docs.google.com/spreadsheets/d/..."
"""

import os
import sys
import json
import argparse
import subprocess
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Paths
WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
GMAPS_SCRIPTS = os.path.join(WORKSPACE, ".claude", "skills", "gmaps-leads", "scripts")
CASUALIZE_SCRIPTS = os.path.join(WORKSPACE, ".claude", "skills", "casualize-names", "scripts")
LINKEDIN_SCRIPTS = os.path.join(WORKSPACE, ".claude", "skills", "linkedin-outreach", "scripts")

# log_activity — fails silently
try:
    sys.path.insert(0, WORKSPACE)
    from execution.log_activity import log_activity
except Exception:
    def log_activity(*a, **kw): pass

# Default configuration — UK trades businesses
DEFAULT_NICHES = [
    "roofers",
    "plumbers",
    "electricians",
    "heating engineers",
    "builders",
    "landscapers",
]

DEFAULT_AREAS = [
    "Birmingham, UK",
    "Manchester, UK",
    "Leeds, UK",
    "Bristol, UK",
    "Sheffield, UK",
    "Liverpool, UK",
    "Nottingham, UK",
    "Leicester, UK",
    "Coventry, UK",
    "Newcastle, UK",
]

LEADS_PER_SEARCH = 25  # Per niche per area — keeps costs down while building volume


def run_gmaps_scrape(niche, area, sheet_url=None, sheet_name=None):
    """Run gmaps_lead_pipeline.py for a single niche+area combo."""
    search_query = f"{niche} in {area}"
    cmd = [
        sys.executable,
        os.path.join(GMAPS_SCRIPTS, "gmaps_lead_pipeline.py"),
        "--search", search_query,
        "--limit", str(LEADS_PER_SEARCH),
    ]
    if sheet_url:
        cmd.extend(["--sheet-url", sheet_url])
    if sheet_name:
        cmd.extend(["--sheet-name", sheet_name])

    print(f"\n{'='*60}")
    print(f"  Scraping: {search_query}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 min per search
            cwd=GMAPS_SCRIPTS,
        )
        if result.returncode == 0:
            output = result.stdout
            lead_count = 0
            captured_sheet_url = None

            for line in output.split("\n"):
                # Capture sheet URL from gmaps output
                if "sheet url:" in line.lower() or "Sheet:" in line:
                    import re as _re
                    url_match = _re.search(r'https://docs\.google\.com/spreadsheets/d/[^\s]+', line)
                    if url_match:
                        captured_sheet_url = url_match.group(0)
                # Parse lead count
                if "qualified" in line.lower() or "saved" in line.lower():
                    nums = [int(s) for s in line.split() if s.isdigit()]
                    if nums:
                        lead_count = max(nums)

            print(f"  ✓ Success — {lead_count} leads")
            if captured_sheet_url:
                print(f"  📋 Sheet: {captured_sheet_url}")
            return {"status": "success", "query": search_query, "leads": lead_count, "sheet_url": captured_sheet_url}
        else:
            print(f"  ✗ Failed: {result.stderr[:200]}")
            return {"status": "error", "query": search_query, "error": result.stderr[:200]}
    except subprocess.TimeoutExpired:
        print(f"  ✗ Timeout after 5 minutes")
        return {"status": "timeout", "query": search_query}
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return {"status": "error", "query": search_query, "error": str(e)}


def run_casualize(sheet_url):
    """Run casualize_batch.py on the lead sheet."""
    print(f"\n{'='*60}")
    print(f"  Casualizing names...")
    print(f"{'='*60}")

    cmd = [
        sys.executable,
        os.path.join(CASUALIZE_SCRIPTS, "casualize_batch.py"),
        "--sheet-url", sheet_url,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=CASUALIZE_SCRIPTS,
        )
        if result.returncode == 0:
            print("  ✓ Names casualized")
            return True
        else:
            print(f"  ✗ Failed: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return False


def run_linkedin_outreach(sheet_url):
    """Generate LinkedIn messages and queue in Dripify."""
    print(f"\n{'='*60}")
    print(f"  Generating LinkedIn outreach...")
    print(f"{'='*60}")

    output_file = os.path.join(WORKSPACE, ".tmp", "linkedin_messages.json")

    # Step 1: Generate messages
    cmd1 = [
        sys.executable,
        os.path.join(LINKEDIN_SCRIPTS, "generate_linkedin_messages.py"),
        "--sheet-url", sheet_url,
        "--output", output_file,
    ]

    try:
        result = subprocess.run(
            cmd1,
            capture_output=True,
            text=True,
            timeout=180,
            cwd=LINKEDIN_SCRIPTS,
        )
        if result.returncode != 0:
            print(f"  ✗ Message generation failed: {result.stderr[:200]}")
            return False

        # Step 2: Create Dripify campaign
        month_year = datetime.now().strftime("%B %Y")
        campaign_name = f"JP Automations — UK Trades — {month_year}"

        cmd2 = [
            sys.executable,
            os.path.join(LINKEDIN_SCRIPTS, "create_dripify_campaign.py"),
            "--input", output_file,
            "--campaign-name", campaign_name,
        ]

        result2 = subprocess.run(
            cmd2,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=LINKEDIN_SCRIPTS,
        )
        if result2.returncode == 0:
            print(f"  ✓ Dripify campaign created: {campaign_name}")
            return True
        else:
            print(f"  ✗ Dripify campaign failed: {result2.stderr[:200]}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Weekly Lead Pipeline Orchestrator")
    parser.add_argument("--niches", type=str, default=None,
                        help="Comma-separated niches (default: roofers,plumbers,electricians,heating engineers,builders,landscapers)")
    parser.add_argument("--areas", type=str, default=None,
                        help="Comma-separated areas (default: 10 UK cities)")
    parser.add_argument("--sheet-url", type=str, default=None,
                        help="Existing Google Sheet URL to append to")
    parser.add_argument("--sheet-name", type=str, default=None,
                        help="Name for new sheet (default: auto-generated)")
    parser.add_argument("--skip-linkedin", action="store_true",
                        help="Skip LinkedIn/Dripify step")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would run without executing")
    args = parser.parse_args()

    # Parse niches and areas
    niches = [n.strip() for n in args.niches.split(",")] if args.niches else DEFAULT_NICHES
    areas = [a.strip() for a in args.areas.split(",")] if args.areas else DEFAULT_AREAS

    # Generate sheet name if not provided
    if not args.sheet_name and not args.sheet_url:
        week_date = datetime.now().strftime("%Y-%m-%d")
        args.sheet_name = f"JP Leads — Week of {week_date}"

    total_searches = len(niches) * len(areas)
    print(f"\n{'='*60}")
    print(f"  JP AUTOMATIONS — WEEKLY LEAD PIPELINE")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")
    print(f"  Niches: {', '.join(niches)}")
    print(f"  Areas: {', '.join(areas)}")
    print(f"  Searches: {total_searches}")
    print(f"  Leads per search: {LEADS_PER_SEARCH}")
    print(f"  Max total leads: {total_searches * LEADS_PER_SEARCH}")
    if args.sheet_name:
        print(f"  Sheet: {args.sheet_name}")
    if args.sheet_url:
        print(f"  Appending to: {args.sheet_url}")
    print()

    if args.dry_run:
        print("DRY RUN — would execute the following searches:")
        for niche in niches:
            for area in areas:
                print(f"  • {niche} in {area}")
        return

    # ── Step 1: Scrape leads ──────────────────────────────────────
    start_time = time.time()
    results = []
    sheet_url = args.sheet_url

    for i, niche in enumerate(niches):
        for j, area in enumerate(areas):
            search_num = i * len(areas) + j + 1
            print(f"\n[{search_num}/{total_searches}]")

            result = run_gmaps_scrape(
                niche, area,
                sheet_url=sheet_url,
                sheet_name=args.sheet_name if not sheet_url else None,
            )
            results.append(result)

            # After first successful scrape, capture the sheet URL for appending
            if result["status"] == "success" and not sheet_url and result.get("sheet_url"):
                sheet_url = result["sheet_url"]
                print(f"\n  📋 Sheet URL captured: {sheet_url}")
                print(f"     All subsequent scrapes will append to this sheet.")

            # Rate limiting — don't hammer Apify
            if search_num < total_searches:
                time.sleep(2)

    # ── Step 2: Casualize names ──────────────────────────────────
    if sheet_url:
        run_casualize(sheet_url)
    else:
        print("\n  ⚠ Sheet URL not captured — run casualize-names manually")
        print("    python3 .claude/skills/casualize-names/scripts/casualize_batch.py --sheet-url YOUR_SHEET_URL")

    # ── Step 3: LinkedIn outreach ────────────────────────────────
    if not args.skip_linkedin and sheet_url:
        run_linkedin_outreach(sheet_url)
    elif not args.skip_linkedin:
        print("\n  ⚠ Sheet URL not captured — run linkedin-outreach manually")

    # ── Summary ──────────────────────────────────────────────────
    elapsed = time.time() - start_time
    successful = [r for r in results if r["status"] == "success"]
    total_leads = sum(r.get("leads", 0) for r in successful)
    failed = [r for r in results if r["status"] != "success"]

    print(f"\n{'='*60}")
    print(f"  PIPELINE COMPLETE")
    print(f"{'='*60}")
    print(f"  Time: {elapsed/60:.1f} minutes")
    print(f"  Searches: {len(successful)}/{total_searches} successful")
    print(f"  Total leads: {total_leads}")
    if failed:
        print(f"  Failed: {len(failed)}")
        for f in failed:
            print(f"    • {f['query']}: {f.get('error', f['status'])}")
    print()

    # Log to Supabase
    log_activity(
        agent_id="lead_pipeline",
        event_type="weekly_run",
        message=f"Weekly pipeline: {total_leads} leads from {len(successful)} searches across {len(niches)} niches in {len(areas)} areas",
        metrics={
            "total_leads": total_leads,
            "searches_successful": len(successful),
            "searches_failed": len(failed),
            "duration_minutes": round(elapsed / 60, 1),
            "niches": niches,
            "areas": [a.replace(", UK", "") for a in areas],
        },
        status="success" if total_leads > 0 else "warning",
    )

    # Return summary for cron/webhook callers
    return {
        "status": "success" if total_leads > 0 else "no_leads",
        "total_leads": total_leads,
        "successful_searches": len(successful),
        "failed_searches": len(failed),
        "duration_minutes": round(elapsed / 60, 1),
        "sheet_url": sheet_url,
    }


if __name__ == "__main__":
    result = main()
    if result:
        print(json.dumps(result, indent=2))
