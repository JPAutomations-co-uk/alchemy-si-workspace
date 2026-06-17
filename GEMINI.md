# Agent Instructions

> This file is mirrored across CLAUDE.md, AGENTS.md, and GEMINI.md so the same instructions load in any AI environment.

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed
- [Modal](https://modal.com/) account (for cloud webhooks)
- Google Cloud project with OAuth credentials (for Gmail/Sheets integrations)

### Setup

1. **Clone and install dependencies:**
   ```bash
   pip install -r requirements.txt
   cd execution && npm install
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and fill in your API keys. Not all keys are required — only fill in what you need:
   - `ANTHROPIC_API_KEY` — Required. Get from [console.anthropic.com](https://console.anthropic.com/)
   - `APIFY_API_TOKEN` — For lead scraping. Get from [apify.com](https://apify.com/)
   - `INSTANTLY_API_KEY` — For cold email campaigns. Get from [instantly.ai](https://instantly.ai/)
   - `PANDADOC_API_KEY` — For proposal generation. Get from [pandadoc.com](https://pandadoc.com/)
   - `OPENAI_API_KEY` — For embeddings in RAG. Get from [platform.openai.com](https://platform.openai.com/)
   - See `.env.example` for the full list.

3. **Configure Gmail (optional):**
   - Create OAuth credentials in [Google Cloud Console](https://console.cloud.google.com/) (Desktop app type)
   - Download as `credentials.json` in the root directory
   - Run any Gmail skill once to complete OAuth and generate token files

4. **Deploy to Modal (optional — for webhook automation):**
   ```bash
   modal deploy execution/modal_webhook.py
   ```
   Update the webhook URLs in `execution/webhooks.json` and relevant SKILL.md files with your Modal username.

5. **Run Claude Code:**
   ```bash
   claude
   ```
   Skills auto-activate based on your requests.

---

## The Skills Architecture

You operate using Claude Code Skills — bundled capabilities that combine instructions with deterministic scripts.

**Layer 1: Skills (Intent + Execution bundled)**
- Live in `.claude/skills/`
- Each Skill = `SKILL.md` instructions + `scripts/` folder
- Claude auto-discovers and invokes based on task context
- Self-contained: each Skill has everything it needs

**Layer 2: Orchestration (Decision making)**
- This is you. Your job: intelligent routing.
- Read SKILL.md, run bundled scripts in the right order
- Handle errors, ask for clarification, update Skills with learnings

**Layer 3: Shared Utilities**
- Common scripts in `execution/`
- Used across multiple Skills when needed

## Available Skills (52 total)

> **Foundation:** Before using any marketing skill, fill in `.claude/product-marketing.md` with your business context. All marketing skills read this first.

### Copywriting & Conversion
- `saas-copywriter` — All product/service copy: landing pages, ads, proposals
- `copy-editing` — Edit and improve existing copy
- `cro` — Conversion rate optimisation across all pages
- `marketing-psychology` — Apply psychological principles to copy and offers
- `sales-enablement` — Pitch decks, one-pagers, objection handling, demo scripts
- `ad-creative` — Generate ad copy variants at scale with A/B structure
- `create-ad-creatives` — Full creative production for ads

### Web Design & Development
- `ui-ux-pro-max` — UI/UX design across React, Next.js, Tailwind, shadcn/ui, and more
- `design-website` — Generate premium website mockups for proposals or new pages
- `site-architecture` — Plan page hierarchy, navigation, URL structure
- `schema` — Add structured data / JSON-LD markup for SEO
- `seo-audit` — Diagnose SEO issues: crawlability, technical, on-page, authority
- `programmatic-seo` — Build SEO page templates at scale

### Outbound Outreach
- `cold-email` — B2B cold outreach emails and follow-up sequences
- `instantly-campaigns` — Create cold email campaigns in Instantly with A/B testing
- `instantly-autoreply` — Auto-reply to incoming emails
- `linkedin-outreach` — LinkedIn outreach sequences and messaging
- `website-outreach` — Tailored outreach for website leads
- `gmaps-leads` — Google Maps lead scraping with deep enrichment
- `scrape-leads` — Scrape leads via Apify with verification
- `prospecting` — Build and qualify B2B prospect lists (ICP + buying signals)
- `classify-leads` — LLM-based lead classification
- `casualize-names` — Convert formal names to casual versions for personalisation
- `lead-pipeline` — Full automated lead pipeline (scrape → classify → enrich → campaign)
- `lead-nurture` — Nurture sequences for past leads and warm prospects
- `welcome-email` — Send welcome sequence to new clients
- `revops` — Lead scoring, routing, pipeline stages, CRM automation

### Marketing & Growth
- `marketing-plan` — Full marketing plan (acquisition → retention → referral)
- `marketing-ideas` — 100+ marketing ideas across all AARRR stages
- `marketing-psychology` — Apply psychological principles to marketing decisions
- `content-strategy` — Plan content pillars, clusters, and ideation
- `social` — Social media strategy (LinkedIn, Instagram, Facebook)
- `ads` — Paid advertising (Google, Meta, LinkedIn)
- `competitor-research` — Deep competitor analysis (pricing, features, positioning)
- `competitor-profiling` — Profile competitors from their URLs
- `competitors` — Build competitor comparison pages for SEO
- `public-relations` — PR strategy, media lists, journalist pitching
- `analytics` — Set up GA4, tracking, conversion events, UTMs
- `directory-submissions` — Submit to 70+ directories for SEO and discovery
- `lead-magnets` — Plan and create lead magnets for email capture
- `referrals` — Referral and partner programs
- `co-marketing` — Find partners and plan joint campaigns
- `product-launch` — Full launch playbook
- `product-marketing` — Create/update marketing context (foundation for all marketing skills)
- `pricing-strategy` — Pricing structure, positioning, proposal framing
- `generate-report` — Generate client-facing reports

### Sales & Proposals
- `create-proposal` — Generate PandaDoc proposals from client discovery notes
- `sales-enablement` — Pitch decks, one-pagers, objection handling

### Content & Creative
- `image` — AI image generation for marketing assets
- `video` — Video marketing strategy and content
- `blog-publish` — Publish blog posts
- `blog-publish` — Blog content production and publishing

### Infrastructure
- `add-webhook` — Add new Modal webhooks
- `modal-deploy` — Deploy to Modal cloud
- `local-server` — Run orchestrator locally

---

## Strategy & Context

Business context lives in `.claude/`:
- `business_context.md` — Company overview, offers, ICP, brand voice, sales process, objections
- `product-marketing.md` — Core marketing context (loaded by all marketing skills)

### When to Load Context
- Any outreach copy → load `business_context.md`
- Any marketing or content → load `product-marketing.md`
- Proposals → load `business_context.md` first
- Competitor work → load `product-marketing.md`

---

## Subagents

Subagents live in `.claude/agents/`. They're lightweight, unbiased (no parent context leakage), and keep the parent context clean.

### Available Subagents
- `code-reviewer` — Adversarial code review. Finds weaknesses, returns issues by severity + PASS/FAIL verdict.
- `qa` — Adversarial QA: generates tests (including edge cases), runs them, reports pass/fail.
- `ux-auditor` — Adversarial UX audit: finds friction, confusion, drop-off points.
- `conversion-reviewer` — Adversarial conversion review of landing pages, pricing pages, copy.
- `pipeline-verifier` — Verifies lead data quality before upload to campaigns.

### Design & Build Workflow

For any non-trivial code (scripts, features, refactors):

1. **Write/edit the code**
2. **Code Review** — Spawn `code-reviewer` subagent
3. **QA** — Spawn `qa` subagent
4. **Fix** — Parent agent applies all fixes
5. **Ship** — Only after review passes and tests pass

---

## Output Discipline

- Do not narrate steps, list files read, or explain routine actions
- Report outcomes, not process
- Lead with the answer or action, not the reasoning
- Include code snippets only when the exact text is load-bearing

## Irreversibility Gate

Before any action that is hard to reverse or affects external systems, state:
- **What** you're about to do
- **What it affects** (which account, campaign, client)
- **Wait for confirmation**

Applies to: sending emails, uploading leads to campaigns, creating proposals, any API write to production data.

## Worker Prompt Standards

Every delegated task (subagent, chained skill) must:
1. **Be self-contained** — include file paths, line numbers, error messages
2. **State what "done" looks like**
3. **Pass structured data** between steps as JSON, not prose

## Self-Annealing

When something breaks:
1. Read the error and stack trace
2. Fix the script
3. Test it again
4. Update the relevant SKILL.md with what you learned
5. The same failure should never happen twice

## Context Loading

Load business context automatically when relevant:
@.claude/business_context.md

### Conditional Rules

Skills that touch external systems load their own context:
- Instantly rules → `.claude/rules/instantly-rules.md`
- Lead pipeline rules → `.claude/rules/lead-pipeline-rules.md`
- Content generation → `.claude/rules/content-generation-rules.md`

## File Organization

- `.claude/skills/` — Skills (SKILL.md + scripts/)
- `execution/` — Shared utilities and infrastructure
- `.tmp/` — Intermediate files (never commit)
- `.env` — API keys (never commit)
- `credentials.json`, `token.json` — Google OAuth (never commit)

## Summary

You work with Skills that bundle intent (SKILL.md) with execution (scripts/). Read instructions, make decisions, run scripts, handle errors, continuously improve the system.

Be pragmatic. Be reliable. Self-anneal.
