# Alchemy SI — Claude Code Workspace

A complete AI-powered sales and marketing system for Alchemy System Integration. Built on Claude Code Skills — each skill is a self-contained module that Claude reads, reasons against your business context, and executes.

**What this gives you:**
- Cold outreach to architects, contractors, facilities managers, and commercial businesses
- High-converting copy for proposals, landing pages, and ads
- Full website design and development capabilities
- Lead generation from Google Maps, LinkedIn, and web scraping
- Automated email campaigns via Instantly
- PandaDoc proposal generation from discovery call notes
- SEO, content strategy, and social media across all channels

---

## Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- Git
- A free [Anthropic account](https://console.anthropic.com/) for your API key

---

## Setup — Antigravity IDE on Windows

> Everything below runs inside Antigravity. Open the built-in terminal with **Ctrl+`** (backtick) and run each command — you never need to leave the IDE.

### 1. Install prerequisites via Antigravity's terminal

`winget` is built into Windows 11. If you're on Windows 10, install it from the [Microsoft Store](https://apps.microsoft.com/store/detail/app-installer/9NBLGGH4NNS1) first.

```powershell
winget install Python.Python.3.12
winget install OpenJS.NodeJS
winget install Git.Git
```

Close and reopen the terminal in Antigravity after this so the new paths register (`Ctrl+`` to reopen).

### 2. Clone the repo

```bash
git clone https://github.com/JPAutomations-co-uk/alchemy-si-workspace.git
```

Then in Antigravity: **File → Open Folder** → select the `alchemy-si-workspace` folder.

Antigravity will automatically load `AGENTS.md` into its agent context — this contains all 52 skill instructions so the AI knows exactly what it can do for your business.

### 3. Install dependencies

```bash
pip install -r requirements.txt
cd execution
npm install
cd ..
```

### 4. Set up your API keys

```powershell
copy .env.example .env
```

Open `.env` in the Antigravity editor and fill in your keys. Start with just the required one:

```
ANTHROPIC_API_KEY=your_key_here
```

Get it from [console.anthropic.com](https://console.anthropic.com/) — free to sign up. Add the others as you start using each capability:

| Key | What it enables | Where to get it |
|---|---|---|
| `ANTHROPIC_API_KEY` | **Required — everything** | [console.anthropic.com](https://console.anthropic.com/) |
| `APIFY_API_TOKEN` | Lead scraping (Google Maps, LinkedIn) | [apify.com](https://apify.com/) |
| `INSTANTLY_API_KEY` | Cold email campaigns | [instantly.ai](https://instantly.ai/) |
| `PANDADOC_API_KEY` | Automated proposals | [pandadoc.com](https://pandadoc.com/) |
| `FLUX_API_KEY` | AI image generation for ads | [fal.ai](https://fal.ai/) |

### 5. Fill in your business context

Open `.claude/business_context.md` directly in Antigravity and fill in every section marked `[NEEDS INPUT]`:

- Your name and direct contact details
- Average contract value (low / typical / high)
- 3–5 real project case studies (client type, brief, what you built, outcome)
- Any client testimonials or quotes

This is the most important step. The AI reads this file before generating anything — every proposal, email, and piece of copy reasons against your real data, not generic placeholders. The more detail here, the better everything else gets.

### 6. Start using it

Everything runs through Antigravity's agent chat. `AGENTS.md` has already loaded all 52 skill instructions. Just talk to it:

> "Scrape Google Maps for architects in Birmingham and build me a lead sheet."

> "Write a cold email sequence for commercial fit-out project managers, positioning around AV that doesn't fail in client meetings."

> "Generate a proposal from these discovery call notes: [paste your notes]."

For skills that run Python scripts (lead scraping, Instantly campaigns, proposals), the agent runs the scripts from `execution/` directly in Antigravity's terminal — you don't touch anything manually.

### Optional — Add Claude Code for extra power

If you want to run the full Claude Code CLI on top of Antigravity:

```bash
npm install -g @anthropic-ai/claude-code
```

Then type `claude` in the Antigravity terminal. Claude Code reads `CLAUDE.md` automatically and gives you the complete skill system powered specifically by Claude.

---

## Setup — Mac / Linux

### 1. Install prerequisites

**Mac:**
```bash
brew install python@3.12 node git
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install python3 python3-pip nodejs npm git
```

### 2. Clone and install

```bash
git clone https://github.com/JPAutomations-co-uk/alchemy-si-workspace.git
cd alchemy-si-workspace
pip install -r requirements.txt
cd execution && npm install && cd ..
```

### 3. Set up environment and run

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
npm install -g @anthropic-ai/claude-code
claude
```

---

## Your First 5 Sessions

Work through these in order to get the highest-value output fastest. Run these prompts directly in Antigravity's agent chat (or Claude Code if you installed it).

### Session 1 — Fill in business context
Say:
> "Help me fill in my business_context.md. I'll answer your questions and you write it."

Claude will interview you on your services, case studies, typical clients, and pricing approach. This powers every other skill.

### Session 2 — Generate your outreach list
> "Scrape Google Maps for architects and commercial fit-out companies in Birmingham. I want a lead sheet with contact details."

Uses: `gmaps-leads` → `classify-leads` → `casualize-names`

### Session 3 — Write your cold email sequence
> "Write a 4-email cold email sequence targeting commercial fit-out project managers. Position around avoiding AV systems that fail in client meetings."

Uses: `cold-email`

### Session 4 — Build your campaign in Instantly
> "Create a cold email campaign in Instantly using the sequence we just wrote and the lead sheet from Session 2."

Uses: `instantly-campaigns`

### Session 5 — Generate a proposal template
> "Create a PandaDoc proposal template for a multi-room corporate office AV project. Discovery call notes: [paste your notes]."

Uses: `create-proposal`

---

## What You Can Ask For

### Copywriting & Conversion
```
"Write landing page copy for our video conferencing installation service"
"Improve the copy on our homepage hero section"
"Write a one-pager for selling to construction project managers"
"Apply psychological principles to our pricing page"
"Review our website for conversion issues"
```

### Web Design & Development
```
"Design a mockup website for a prospect in the hospitality sector"
"Build a service page for our videowall installations using Tailwind"
"Plan the site architecture for a redesigned alchemysi.uk"
"Add structured data markup to our services pages"
"Run an SEO audit on alchemysi.uk"
```

### Outbound Outreach
```
"Scrape architects in Birmingham from Google Maps"
"Write LinkedIn outreach messages for facilities managers at commercial offices"
"Build a cold email campaign targeting hotel chains needing AV upgrades"
"Set up auto-replies for inbound leads in Instantly"
"Generate personalised outreach for leads with outdated websites"
```

### Marketing & Business Growth
```
"Build a full marketing plan for the next 6 months"
"Research our top 5 competitors and find positioning gaps"
"Write a content strategy targeting construction specifiers on LinkedIn"
"Plan a referral programme for our existing clients"
"Generate 20 marketing ideas for the hospitality sector"
```

### Lead Generation
```
"Run the full lead pipeline: scrape → classify → enrich → upload to campaign"
"Find and classify 200 worship venues in the UK"
"Enrich our lead list with LinkedIn data"
"Build an outreach sheet for commercial gym chains"
```

### Sales & Proposals
```
"Generate a proposal from these discovery call notes: [paste notes]"
"Write objection handling scripts for 'we already have an AV supplier'"
"Build a pitch deck for education sector AV services"
"Create a one-pager comparing us to a generic AV supplier"
```

---

## Skills Reference (52 total)

<details>
<summary><strong>Copywriting & Conversion</strong></summary>

| Skill | What it does |
|---|---|
| `saas-copywriter` | Landing pages, service pages, hero copy, CTAs |
| `copy-editing` | Improve existing copy — clarity, punch, conversion |
| `cro` | Conversion rate audits and optimisation |
| `marketing-psychology` | Apply proven psychological principles to copy and offers |
| `sales-enablement` | Pitch decks, one-pagers, objection scripts, demo flows |
| `ad-creative` | Ad copy variants with A/B structure |
| `create-ad-creatives` | Full ad creative production (images, video templates) |

</details>

<details>
<summary><strong>Web Design & Development</strong></summary>

| Skill | What it does |
|---|---|
| `ui-ux-pro-max` | UI/UX across React, Next.js, Tailwind, shadcn/ui |
| `design-website` | Generate premium website mockups for prospects or new pages |
| `site-architecture` | Page hierarchy, navigation, URL structure |
| `schema` | JSON-LD structured data for local SEO |
| `seo-audit` | Technical, on-page, and authority SEO diagnosis |
| `programmatic-seo` | SEO page templates at scale (e.g. "[City] AV installation") |

</details>

<details>
<summary><strong>Outbound Outreach</strong></summary>

| Skill | What it does |
|---|---|
| `cold-email` | B2B email sequences with follow-ups |
| `instantly-campaigns` | Create and manage Instantly campaigns |
| `instantly-autoreply` | Auto-reply logic for inbound email replies |
| `linkedin-outreach` | LinkedIn connection and message sequences |
| `website-outreach` | Personalised outreach around a pre-built website pitch |
| `gmaps-leads` | Google Maps scraping with contact enrichment |
| `scrape-leads` | Apify-based lead scraping |
| `prospecting` | Build qualified B2B prospect lists |
| `classify-leads` | LLM-based lead scoring and classification |
| `casualize-names` | Format names for personalised cold outreach |
| `lead-pipeline` | Full automated pipeline: scrape → classify → enrich → campaign |
| `lead-nurture` | Sequences for warm leads and past enquiries |
| `welcome-email` | Onboarding email sequence for new clients |
| `revops` | Lead routing, scoring, pipeline stages, CRM automation |

</details>

<details>
<summary><strong>Marketing & Growth</strong></summary>

| Skill | What it does |
|---|---|
| `marketing-plan` | Full acquisition → retention → referral plan |
| `marketing-ideas` | 100+ marketing ideas across all growth stages |
| `marketing-psychology` | Psychological frameworks applied to marketing decisions |
| `content-strategy` | Content pillars, clusters, editorial planning |
| `social` | Social media strategy (LinkedIn, Instagram, Facebook) |
| `ads` | Paid advertising (Google, Meta, LinkedIn) |
| `competitor-research` | Deep competitor analysis: pricing, positioning, gaps |
| `competitor-profiling` | Profile individual competitors from their URLs |
| `competitors` | Build competitor comparison/alternative pages for SEO |
| `public-relations` | PR strategy, media lists, press release pitching |
| `analytics` | GA4 setup, conversion tracking, UTM management |
| `directory-submissions` | Submit to 70+ directories for SEO and discovery |
| `lead-magnets` | Lead magnet planning and creation for email capture |
| `referrals` | Referral and partner programme design |
| `co-marketing` — Joint campaigns with complementary partners |
| `product-launch` | Launch playbook for new services or locations |
| `product-marketing` | Core marketing context (run this first) |
| `pricing-strategy` | Pricing structure, tiers, proposal framing |
| `generate-report` | Client-facing reports |

</details>

<details>
<summary><strong>Creative</strong></summary>

| Skill | What it does |
|---|---|
| `image` | AI image generation for ads and marketing |
| `video` | Video marketing strategy and AI video content |
| `blog-publish` | Blog content production and publishing |

</details>

<details>
<summary><strong>Infrastructure</strong></summary>

| Skill | What it does |
|---|---|
| `add-webhook` | Add Modal webhooks for event-driven automation |
| `modal-deploy` | Deploy to Modal cloud |
| `local-server` | Run the orchestrator locally |

</details>

---

## How the System Works

```
You (natural language request)
        ↓
Claude reads SKILL.md + business_context.md
        ↓
Claude makes decisions, runs scripts in execution/
        ↓
Output: Google Sheet, PandaDoc proposal, Instantly campaign, or copy
```

**Skills are living documents.** When Claude discovers a new constraint, API change, or better approach, it updates the relevant SKILL.md. The system gets smarter over time.

**Subagents** handle verification and adversarial review:
- `code-reviewer` — checks scripts before they run
- `pipeline-verifier` — spot-checks lead data before upload to campaigns
- `ux-auditor` — reviews pages for UX friction
- `conversion-reviewer` — adversarial review of landing pages and copy

---

## Key Files

| File | Purpose |
|---|---|
| `.claude/business_context.md` | **Fill this in first.** Your services, case studies, ICP, brand voice, objections |
| `.claude/product-marketing.md` | Core marketing context — read by all marketing skills |
| `.env` | Your API keys (never commit this) |
| `execution/` | Shared scripts used across multiple skills |
| `.claude/skills/` | All 52 skills — each has a SKILL.md and scripts/ folder |
| `.tmp/` | Temporary processing files — auto-cleaned, never committed |

---

## Sector-Specific Quick Starts

### Targeting architects & contractors
```
"Scrape architects in [city] from Google Maps, classify by project type, and write a cold email sequence focused on getting involved at first-fix stage."
```

### Targeting corporate offices
```
"Find commercial property management companies in Birmingham on LinkedIn. Write outreach positioning around video conferencing reliability for client-facing meetings."
```

### Targeting hospitality (hotels, bars, restaurants)
```
"Scrape hotels and hospitality venues in [city] from Google Maps. Write an outreach email sequence for background music and atmosphere systems."
```

### Winning back past enquiries
```
"I have a list of past enquiries that didn't convert. Write a re-engagement sequence for each type: corporate, hospitality, education."
```

---

## Support & Troubleshooting

If a script fails, Claude will:
1. Read the error and stack trace
2. Fix the script
3. Test it again
4. Update the SKILL.md with what it learned

You don't need to debug anything manually. Just paste the error back to Claude.

For anything else: [connect@alchemysi.uk](mailto:connect@alchemysi.uk)
