---
name: pricing-strategy
description: SaaS pricing strategy — tier design, value metric selection, pricing page copy, freemium vs trial analysis, and positioning. Use when asked about pricing, designing pricing tiers, writing a pricing page, choosing a pricing model, or deciding between freemium and free trial.
---

# Pricing Strategy

Design SaaS pricing that converts — the right model, the right tiers, the right copy, the right anchoring.

## When to Use

- Designing pricing from scratch (new product)
- Redesigning pricing that's not converting
- Writing the pricing page
- Deciding freemium vs free trial vs paid-only
- Setting expansion pricing tiers

---

## Pricing Model Selection

### The five SaaS models

| Model | Best for | Avoid when |
|---|---|---|
| **Flat rate** | Simple single-persona products | Multiple ICPs with different usage |
| **Seat-based** | Collaboration tools (more users = more value) | Solo users / variable team sizes |
| **Usage-based** | API products, infra, AI tools | Users need predictable bills |
| **Tier-based (feature)** | Products with clear power users | Features aren't actually distinct needs |
| **Hybrid (seat + usage)** | Complex products with both | Simplicity is a priority |

**The value metric question:** What is the unit that most closely tracks the value your customer gets?
- Emails sent → email tool
- Contacts managed → CRM
- API calls → API product
- Team members → collaboration tool
- Revenue processed → payment tool

Charge on the value metric whenever possible. It aligns your incentives with theirs.

---

## Tier Design

### Rules

1. **3 tiers, always** — One is no choice. Two is left/right. Three creates a middle anchor. Four is confusion.

2. **Name by outcome, not size:**
   - ✅ Starter / Growth / Scale
   - ✅ Solo / Team / Business
   - ❌ Basic / Pro / Enterprise
   - ❌ Free / Plus / Premium

3. **The middle tier is the real product** — design it to be the obvious right choice for your ICP. The bottom tier should feel slightly constrained. The top tier should feel like extra room to grow.

4. **One key limit per tier** — don't gate 7 things. Pick the one most important scaling limit (seats, contacts, projects, API calls) and make that the upgrade trigger.

5. **Annual discount: 20%** — standard in SaaS. Drives cash flow. Less than 15% isn't enough to move behaviour. More than 30% signals underconfidence in value.

### Tier Design Framework

For each tier, define:
```
Name:
Price:
Who it's for (one sentence):
Core limit (the thing they'll hit):
Key feature unlocked at this tier:
CTA:
```

### The "most popular" badge

Only put it on the tier that genuinely converts the most — or the tier you want to push. Putting it on the most expensive tier looks dishonest. Putting it on the cheapest looks self-defeating. Middle tier, almost always.

---

## Freemium vs Free Trial

### Free Trial (14 days recommended)
**Best for:**
- Products where the value is obvious after one session
- ICPs who compare alternatives before buying
- B2B tools where you need buy-in from more than one person

**Don'ts:**
- Don't make the trial too long (30+ days = users lose urgency)
- Don't require credit card (conversion rate drops 50-70%)
- Don't gate the aha moment behind a paywall during trial

### Freemium
**Best for:**
- Products where casual usage creates network effects
- Tools where free users are lead generators (share links, embed widgets)
- Developer tools (build a user base, convert power users)
- Products with a natural upgrade trigger (you'll hit the limit organically)

**Don'ts:**
- Don't give away so much that paid is hard to justify
- Don't create a free tier that attracts the wrong ICP
- Don't maintain freemium if support costs exceed conversion value

**The freemium limit rule:** Free tier should be useful enough to demonstrate value, but constrained enough that growing users naturally want more. If users can achieve their entire goal on free — you have a charity, not a business.

### Paid-only
**Best for:**
- Enterprise / high-touch sales
- Products where support is intensive
- When your ICP expects to pay (signals seriousness)

---

## Pricing Psychology

### Anchoring
Put your highest tier first (left-to-right) or use it as a visual anchor. Even if no one buys it, it makes the middle tier look reasonable.

### Decoy pricing
Make the middle tier obviously better value-per-feature than the bottom. Example:
- Starter: 5 projects, $29/month
- Growth: Unlimited projects + analytics, $49/month ← make this the obvious choice
- Scale: Everything + priority support + API, $99/month

$49 is the "sweet spot" — $29 feels too limited, $99 feels like extra.

### Charm pricing
$49 not $50. $99 not $100. Works, still works, will keep working.

### Price anchoring to cost-of-not-having-it
If your tool saves someone £500/month, your £79/month price seems obvious. Build this maths into your pricing page copy.

---

## Pricing Page Structure

```
[Headline] — Simple, outcome-focused. "Pricing that grows with you" is useless. "Start free. Scale as you grow." is better.

[Toggle: Monthly / Annual] — put Annual first or highlight savings clearly

[Three tier cards, with middle card visually elevated]
  Each card:
  - Tier name
  - Price (monthly equivalent if annual)
  - One-sentence who-it's-for
  - CTA button
  - Feature list (benefits, not feature names — "Unlimited contacts" not "Contact management")
  - Key limit clearly stated

[Social proof strip] — logos or review count

[FAQ] — 5-6 questions, all real objections:
  - "Can I change plans later?"
  - "Do you offer refunds?"
  - "Is there a free trial?"
  - "What happens to my data if I cancel?"
  - "Do you support [common integration]?"
  - "What counts as a [value metric]?"

[Enterprise CTA] — "Need a custom plan? Talk to us." — just a link, not a whole section
```

---

## Pricing Copy Rules

- **Price the outcome, not the feature.** "Handle 5,000 contacts" not "Access to contact management"
- **State what's NOT included** clearly on the lower tiers — people buy up more readily when they know exactly what they're missing
- **"No credit card required"** — state this next to every trial CTA. Dramatically improves conversion.
- **"Cancel anytime"** — reduces perceived risk
- **"SOC 2 / GDPR compliant"** — include if true; enterprise buyers check

---

## Pricing Output Format

```markdown
# Pricing Strategy: [Product]

## Recommended Model
[Model] because [reason — tied to value metric]

## Value Metric
[The thing to charge on]

## Tier Structure

| | Starter | Growth (Recommended) | Scale |
|---|---|---|---|
| Price | $X/mo | $X/mo | $X/mo |
| Who it's for | ... | ... | ... |
| Core limit | ... | ... | ... |
| Key unlock | — | [feature] | [feature] |
| CTA | Start free | Start free trial | Book demo |

## Freemium vs Trial Recommendation
[Choice + rationale]

## Pricing Page Copy
[Full headline, sub, CTA, FAQ copy]

## What to A/B Test
1. [Variant A] vs [Variant B] — [hypothesis]
2. ...
```
