---
name: competitor-research
description: Deep competitor analysis for SaaS products — features, pricing, positioning, messaging, weaknesses, and gaps. Use when asked to research competitors, analyse the market, find gaps, compare products, or understand positioning.
allowed-tools: Bash, Read, Write, WebFetch, WebSearch, Glob, Grep
---

# Competitor Research

Systematic intelligence gathering on direct and indirect competitors. The output is always actionable: what to position against, what gaps to exploit, what not to build (because they own it), and where the market is underserved.

## When to Use

- Pre-launch market validation
- Positioning decisions ("how are we different?")
- Pricing calibration
- Feature roadmap prioritisation
- Landing page / copy decisions

---

## Input

User provides:
- Product name and one-sentence description
- 1-3 known competitors (or "find them" if unknown)
- What they want to know: pricing, features, positioning, all-of-the-above

---

## Research Process

### Phase 1: Identify the Competitive Set

Classify competitors into three tiers:
- **Direct:** Same ICP, same core use case, same price point
- **Indirect:** Same ICP, adjacent use case (or different deployment e.g. enterprise vs SMB)
- **Category substitutes:** What the prospect uses *instead* — often a spreadsheet, agency, or manual process

For each, find:
- Homepage + pricing page (scrape both)
- G2 / Capterra / Trustpilot reviews (search for these)
- Recent news, funding, product updates (search "[competitor] 2024 OR 2025")
- Job postings — what roles they're hiring reveals what they're building

### Phase 2: Feature Mapping

Build a feature matrix:
```
| Feature | Our Product | Competitor A | Competitor B | Competitor C |
|---------|-------------|--------------|--------------|--------------|
| ...     | ✅ / ❌ / 🔜 | ✅ / ❌       | ✅ / ❌       | ✅ / ❌       |
```

Pull features from:
1. Their features/pricing page
2. G2 review mentions ("I wish it had X", "Unlike X, this does Y")
3. Their changelog / blog (shows what they've been building)

### Phase 3: Pricing Intelligence

For each competitor, capture:
- Pricing model: seat-based / usage-based / flat / freemium / custom
- Tiers and names
- Entry price (first paid tier)
- Enterprise price (if public)
- Free tier or trial: yes/no + limitations
- What's gated behind higher tiers
- Annual discount (if any)

### Phase 4: Messaging & Positioning

For each competitor:
- **Headline:** Exact hero headline (copy it verbatim)
- **ICP signal:** Who they're writing for (extract from copy)
- **Primary CTA:** What they're pushing (trial / demo / free / contact)
- **Key claims:** The 3 things they say make them best
- **Proof:** How they back it up (reviews count, case studies, logos, metrics)
- **What they're NOT saying:** Gaps in their positioning = your opportunity

### Phase 5: Review Mining (Voice of Customer)

Search G2, Capterra, Reddit, and Twitter/X for:
- Most praised features ("Pros")
- Most complained about ("Cons", "I wish")
- Reasons for switching to them
- Reasons for churning from them

Quote verbatim where possible — these exact phrases belong in your copy.

### Phase 6: Weakness Identification

Flag for each competitor:
- Features customers keep asking for (from reviews) that don't exist
- Pricing complaints (too expensive, too rigid, seat-based friction)
- Support / reliability complaints
- Onboarding friction
- Integrations missing
- Use cases they explicitly don't serve

---

## Output Format

```markdown
# Competitive Analysis: [Product Name]

## Market Map
[Direct / Indirect / Substitute grid]

## Feature Matrix
[Table]

## Pricing Comparison
[Table: model / entry / top tier / trial]

## Competitor Profiles (one per competitor)

### [Competitor Name]
- **Headline:** "exact headline from their site"
- **ICP:** Who they target
- **Key claims:** 1) ... 2) ... 3) ...
- **Pricing:** [model + entry price + gating]
- **Strengths:** (from reviews and product)
- **Weaknesses:** (from reviews and product)
- **What they avoid saying:** [gaps in positioning]

## Voice of Customer (Review Mining)
### What customers love about [Category]
- "direct quote" (G2/Capterra, date)

### What customers hate / wish existed
- "direct quote"

## Gap Analysis
### Pricing gaps
- ...
### Feature gaps
- ...
### Positioning gaps (angles nobody is owning)
- ...

## Strategic Implications
### Position against
[How to frame your product vs. the market]

### Win on
[Where you're better — be honest, not aspirational]

### Avoid competing on
[Where they're unbeatable or it's a race to zero]

### Copy angles to test
[3-5 specific claims to test on your landing page based on gaps found]
```

---

## Research Tools

Use WebSearch with these queries:
- `[competitor] pricing 2025`
- `[competitor] vs [competitor] review`
- `[competitor] alternatives`
- `site:g2.com [competitor]`
- `site:reddit.com [competitor] review`
- `[competitor] changelog`
- `[category] best tools 2025`
- `[competitor] funding announcement`

Scrape with WebFetch:
- Homepage
- /pricing page
- /features or /product page
- G2 profile page
