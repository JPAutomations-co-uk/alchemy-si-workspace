# Lead Pipeline — Full Automated Sales Pipeline

## When to Use
When JP asks to run the lead pipeline, generate leads, create pipeline sheets, process follow-ups, send voicemail texts, request reviews, or generate pre-call briefs.

## Overview
End-to-end automated sales pipeline for UK trades businesses. Chains together lead scraping, qualification, outreach preparation, follow-up sequences, and client retention automation.

## Scripts

### 1. Weekly Lead Pipeline (`weekly_lead_pipeline.py`)
Automated orchestrator that runs weekly:
- Scrapes Google Maps across 6 trades niches × 10 UK cities
- Filters by quality gate (rating ≥4.0, reviews ≥15, has website)
- Casualizes names for outreach
- Pushes to pipeline sheet + Dripify for LinkedIn

```bash
# Full run (all niches, all areas)
python3 .claude/skills/lead-pipeline/scripts/weekly_lead_pipeline.py

# Specific niches and areas
python3 .claude/skills/lead-pipeline/scripts/weekly_lead_pipeline.py \
    --niches "roofers,plumbers" --areas "Birmingham,Manchester"

# Append to existing sheet
python3 .claude/skills/lead-pipeline/scripts/weekly_lead_pipeline.py \
    --sheet-url "https://docs.google.com/spreadsheets/d/..."

# Dry run (see what would execute)
python3 .claude/skills/lead-pipeline/scripts/weekly_lead_pipeline.py --dry-run
```

### 2. Pre-Call Brief Generator (`precall_brief.py`)
Generates a one-page sales brief before each call:
- Auto-detects sub-niche (roofer/plumber/electrician/builder/landscaper)
- Scrapes their website for missing features
- Matches to the right case study
- Generates 2-3 specific quick wins
- Provides opening line, objection prep, and close suggestion

```bash
# From manual input
python3 .claude/skills/lead-pipeline/scripts/precall_brief.py \
    --name "Dave" --business "ACE Roofing" --website "aceroofing.co.uk" \
    --trade "roofer" --city "Birmingham" --rating "4.6" --reviews "47"

# From pipeline sheet
python3 .claude/skills/lead-pipeline/scripts/precall_brief.py \
    --sheet-url "https://docs.google.com/spreadsheets/d/..." --row 15
```

### 3. Follow-Up Engine (`follow_up_engine.py`)
Time-based follow-up sequence manager:
- Reads from Follow-Ups tab in pipeline sheet
- Checks what's due today
- Sends via email (Gmail) or SMS (Twilio)
- Advances sequence step and schedules next

**Sequences available:**
- `post_voicemail` — immediate text + 48hr follow-up
- `post_quickwins` — Day 3 check-in + Day 7 value touch
- `post_proposal` — 24hr, 48hr, 72hr reminders
- `post_call_no_close` — Day 1 Loom, Day 3, 7, 14, 30 follow-ups
- `nurture` — Day 30 + Day 60 long-term touches

```bash
# Process all due follow-ups
python3 .claude/skills/lead-pipeline/scripts/follow_up_engine.py \
    --sheet-url "https://docs.google.com/spreadsheets/d/..."

# Dry run
python3 .claude/skills/lead-pipeline/scripts/follow_up_engine.py \
    --sheet-url "..." --dry-run

# Add prospect to a sequence
python3 .claude/skills/lead-pipeline/scripts/follow_up_engine.py \
    --sheet-url "..." --add --name "Dave" --email "dave@example.com" \
    --sequence post_proposal --trade roofer --key-pain "invoicing delays"
```

### 4. Voicemail Follow-Up (`voicemail_followup.py`)
Instant post-voicemail text with trade-specific messaging:
- Sub-niche specific templates (roofer/plumber/electrician/builder/landscaper)
- Each references the matching case study result
- Auto-adds to pipeline sheet + follow-up sequence

```bash
# With Twilio
python3 .claude/skills/lead-pipeline/scripts/voicemail_followup.py \
    --name "Dave" --phone "07xxx" --trade roofer --area "Birmingham" \
    --sheet-url "..."

# Manual mode (prints message for WhatsApp)
python3 .claude/skills/lead-pipeline/scripts/voicemail_followup.py \
    --name "Dave" --phone "07xxx" --trade roofer --manual
```

### 5. Review Request (`review_request.py`)
Post-delivery review request (Day 30 milestone):

```bash
# SMS
python3 .claude/skills/lead-pipeline/scripts/review_request.py \
    --name "Dave" --business "ACE Roofing" --phone "+447xxx"

# Email
python3 .claude/skills/lead-pipeline/scripts/review_request.py \
    --name "Dave" --business "ACE Roofing" --email "dave@aceroofing.co.uk" \
    --channel email

# Manual (copy-paste for WhatsApp)
python3 .claude/skills/lead-pipeline/scripts/review_request.py \
    --name "Dave" --business "ACE Roofing" --channel manual
```

### 6. Pipeline Sheet Creator (`create_pipeline_sheet.py`)
Creates the master pipeline Google Sheet with 5 tabs:

```bash
python3 .claude/skills/lead-pipeline/scripts/create_pipeline_sheet.py
python3 .claude/skills/lead-pipeline/scripts/create_pipeline_sheet.py --name "JP Pipeline — April 2026"
```

**Tabs created:**
1. **Pipeline** — Master CRM (name, business, phone, email, trade, status, deal value)
2. **Follow-Ups** — Sequence tracker (used by follow_up_engine.py)
3. **Call Log** — Daily cold calling outcomes
4. **Metrics** — Weekly KPI tracking
5. **Clients** — Active client management + retention milestones

## Required Environment Variables
```
ANTHROPIC_API_KEY=      # Claude (pre-call briefs, classification)
APIFY_API_TOKEN=        # Google Maps scraping
DRIPIFY_API_KEY=        # LinkedIn automation

# Optional — falls back to manual mode without these:
TWILIO_ACCOUNT_SID=     # SMS sending
TWILIO_AUTH_TOKEN=       # SMS sending
TWILIO_PHONE_NUMBER=    # SMS from number
```

## Automation Schedule

| Frequency | Script | Purpose |
|-----------|--------|---------|
| Weekly (Monday 6am) | weekly_lead_pipeline.py | Fresh leads for the week |
| Daily (7am) | follow_up_engine.py | Send due follow-ups |
| Per voicemail | voicemail_followup.py | Immediate text after voicemail |
| Per sales call | precall_brief.py | 5-min call prep |
| Day 30 post-delivery | review_request.py | Client review collection |

## Data Flow

```
weekly_lead_pipeline.py
  → gmaps-leads (scrape)
  → casualize-names (prep)
  → Pipeline Sheet (call list)
  → Dripify (LinkedIn sequences)

Cold Call → voicemail?
  → voicemail_followup.py (auto-text)
  → Pipeline Sheet (logged)
  → Follow-Up tab (sequenced)

Call Booked → precall_brief.py (prep)
  → Sales Call → close?
    YES → welcome-email + create-proposal
    NO  → follow_up_engine.py (post_call_no_close sequence)

Client Delivered → Day 30
  → review_request.py
  → Phase 2 discussion
```
