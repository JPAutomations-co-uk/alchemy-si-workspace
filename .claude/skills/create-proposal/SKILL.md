---
name: create-proposal
description: Generate PandaDoc proposals from client information or sales call transcripts. Use when user asks to create a proposal, generate a quote, draft a contract, or prepare a client document.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Proposal Generation

## Goal
Create PandaDoc proposals for clients, either from structured information or by extracting details from sales call transcripts.

The output must read like your best salesperson wrote it on their sharpest day — not like professional filler. This is achieved by loading business context and reasoning against it before writing a single word.

## Inputs (One of the following)

**Option A: Structured Data**
- Client First Name, Last Name, Email, Company
- Project Title
- 4 Key Problems (brief)
- 4 Key Benefits (brief)
- Project Duration
- Investment Breakdown (Month 1, Month 2, Month 3+)

**Option B: Call Transcript**
- Sales call transcript to extract all details from

## Scripts
- `./scripts/create_proposal.py` - Creates PandaDoc proposal via API
- `./scripts/read_sheet.py` - Read client data from sheets if needed

## Process

### 0. Load Business Context
Before doing anything else, read `.claude/business_context.md`.
This is not optional. Every proposal must be reasoned against real offers, real pricing, real objection data, and real brand voice.
If the file is empty or missing sections, flag what's needed and stop until it's filled.

### 0b. Analysis Scratchpad
Before writing any proposal content, reason in `<analysis>` tags:
```
<analysis>
- Offer tier match: Based on budget signals and needs, which tier? Pull exact pricing from business_context.md.
- "Do they understand my business?" moment: What one thing about this prospect, if named precisely, makes them feel seen?
- Top objection prediction: Based on industry and budget, what objection? Pull matching response from business_context.md.
- Proof selection: Which testimonial or case study is most relevant by industry/problem/outcome?
- Brand voice check: Using business_context.md voice — straight-talking, no fluff, peer-to-peer, pragmatic.
</analysis>
```
Strip the analysis block from the final proposal — it's for reasoning only.

### 1. Gather Information
- If user provides structured data, use directly
- If user provides transcript, extract:
  - Client info (name, company, email)
  - Project context and title
  - 4 main problems/pain points
  - 4 proposed solutions/benefits
  - Financial terms (duration, value, costs)
- Ask for any missing critical information

### 2. Reason Before Writing (do this explicitly, show your reasoning)

Using the lead data + loaded business context, work through:

**Offer tier match:**
- Based on their budget signals and stated needs, which tier fits?
- Pull the exact pricing from business context — never fabricate
- If budget is unclear, note it and default to Tier 2 with a note

**The "do they understand my business?" moment:**
- What is the one thing about this prospect's situation that, if named precisely, makes them feel seen in the first 60 seconds?
- Draw from their industry, company size, conversation notes, or specific language they used

**Top objection prediction:**
- Based on their industry and budget signals, what objection will they raise?
- Pull the matching response from business context objection data
- Bake the answer into the proposal before they ask — don't save it for a call

**Proof selection:**
- Which testimonial or past result from business context is most relevant to this prospect?
- Match by industry, problem type, or outcome

### 3. Generate Content
Write the 4 problems and 4 benefits using the reasoning from Step 2:

**Problem Expansion Guidelines:**
- Use direct "you" language (not third-person)
- Name their specific situation — not a generic version of it
- Focus on revenue impact and dollar amounts
- Pull language from their conversation notes where possible
- Example: "Right now, your top-of-funnel is converting very poorly to booked meetings..."

**Benefit Expansion Guidelines:**
- Address the client directly
- Tie each benefit back to the offer tier selected in Step 2
- Emphasize ROI and payback period
- Use brand voice from business context — not "professional" filler language

**Also generate:**
- Slide Footer: "Confidential | [Company] Strategic Initiative | [Date]"
- Contract Footer: "[Company]-[ProjectTitle]-[YYYY-MM]"
- Created Date: Current date (YYYY-MM-DD)

**Rule:** If lead data is too thin to reason meaningfully, flag what's missing and ask — do not fill gaps with assumptions.

### 3. Execute Proposal Creation
```bash
python3 ./scripts/create_proposal.py <<'EOF'
{
  "client": {
    "firstName": "...",
    "lastName": "...",
    "email": "...",
    "company": "..."
  },
  "project": {
    "title": "...",
    "problems": {
      "problem01": "[Expanded Problem 1]",
      "problem02": "[Expanded Problem 2]",
      "problem03": "[Expanded Problem 3]",
      "problem04": "[Expanded Problem 4]"
    },
    "benefits": {
      "benefit01": "[Expanded Benefit 1]",
      "benefit02": "[Expanded Benefit 2]",
      "benefit03": "[Expanded Benefit 3]",
      "benefit04": "[Expanded Benefit 4]"
    },
    "monthOneInvestment": "...",
    "monthTwoInvestment": "...",
    "monthThreeInvestment": "..."
  },
  "generated": {
    "slideFooter": "...",
    "contractFooterSlug": "...",
    "createdDate": "..."
  }
}
EOF
```

### 4. Send Follow-Up Email
Use Gmail to send HTML follow-up email:
- Subject: "Re: [Brief Project Context] Discussion"
- Opening: Thank them for discussing challenges
- Body: 2-4 numbered sections with bold headers
- Each section: Description + "Steps:" bullet points
- Closing: "I'll send you a full proposal shortly..."
- Signature: "Thanks, Nick"

### 5. Notify User
- Provide the PandaDoc "internalLink" for review
- Confirm follow-up email was sent

## Output
- PandaDoc proposal URL (for editing/review)
- Follow-up email sent to client

## Environment
Requires in `.env`:
```
PANDADOC_API_KEY=your_key
```
