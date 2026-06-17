---
name: linkedin-outreach
description: Automate LinkedIn outreach by generating personalised connection requests and follow-up messages using business context, then queuing them in Dripify. Use when user asks to run LinkedIn outreach, send LinkedIn messages, or build a LinkedIn campaign.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# LinkedIn Outreach Automation

## Goal
Generate personalised LinkedIn connection requests and follow-up messages — reasoned against real business context — and queue them in Dripify Pro for safe automated sending (25 requests/day).

## Inputs
- Google Sheet URL containing leads with `owner_linkedin` column (output from gmaps-leads)
- Optional: target industry or specific pain point to lead with

## Scripts
- `./scripts/generate_linkedin_messages.py` — reads leads sheet, generates personalised messages, outputs to JSON
- `./scripts/create_dripify_campaign.py` — creates campaign in Dripify and adds prospects with messages

## Process

### 0. Load Business Context
Read `.claude/business_context.md` before generating any messages.
Pull: brand voice, objection responses, real results, guarantees.

### 1. Read Leads from Sheet
```bash
python3 ./scripts/generate_linkedin_messages.py \
  --sheet-url "GOOGLE_SHEET_URL" \
  --output .tmp/linkedin_messages.json
```

Reads: `owner_name`, `owner_linkedin`, `business_name`, `category`, `city` from the sheet.
Filters out rows with no LinkedIn URL.

### 2. Review Generated Messages
Read `.tmp/linkedin_messages.json` and confirm the messages match brand voice before proceeding.

### 3. Create Dripify Campaign
```bash
python3 ./scripts/create_dripify_campaign.py \
  --input .tmp/linkedin_messages.json \
  --campaign-name "JP Automations — [Industry] — [Month Year]"
```

Creates campaign with 3-step sequence:
- Step 1 (Day 0): Connection request with note
- Step 2 (Day 3): Follow-up message to new connections
- Step 3 (Day 7): Value-add / final nudge

## Message Structure

### Connection Request (300 char limit)
- One specific observation about their business
- One relevant result that matches their situation
- No pitch. No ask. Just relevance.

### Follow-up Message (Day 3, after accept)
- Reference the connection
- Name one specific pain their industry has
- Soft CTA: "Worth a quick call this week?"

### Final Nudge (Day 7)
- Short. Direct.
- One question. One line.

## Environment
```
DRIPIFY_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

## API Notes (Dripify)
- Base URL: https://api.dripify.io/api/v1
- Auth: Bearer token in Authorization header
- Campaign endpoint: POST /campaigns
- Prospect endpoint: POST /campaigns/{id}/prospects
- Daily limit: set to 25 connection requests/day (safe threshold)
- Message personalisation: use {firstName}, {lastName}, {companyName} variables
